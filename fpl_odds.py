"""
fpl_odds.py  -  the Odds API collector (W1; BUILD_PLAN.md Step 5 item 1, the
collector only; RULING FAST-TRACK item 3; RULING W1 odds storage).

    python fpl_odds.py        run in DATA_DIR by fpl_nightly.py, after the sync

One request a night: GET /v4/sports/soccer_epl/odds/ with markets h2h,totals,
regions uk,eu, decimal odds. The answer's body is written byte for byte as
gzip (no name, mtime 0: the same body always gives the same bytes) to

    odds/odds_<fetched UTC, YYYY-MM-DDTHHMMZ>.json.gz

on the data branch. Append-only: a file is never rewritten or deleted -
fpl_gate.py checks that every odds file of the previous data commit is still
there, byte-identical. No odds table in fpl.sqlite (at +0.84 MB a night it
would pass GitHub's 100 MB file limit around February). rows() is the reader
of these files; forecasts may only use snapshots fetched before a deadline
(Step 5). A compact derived table comes with the step that uses the odds.

The key comes from ODDS_API_KEY (a GitHub Actions secret; S1 amendment 1,
item 1) and is never printed, logged or written: the request URL carries it,
so the URL is never shown, and a failure is reported by its kind and HTTP
status only. Without a key, or when the request fails, it says so in one line
- ODDS SKIPPED or ODDS FAILED - and exits 0: tonight's other data still
commits, and checks.py (check 30) turns the line into a WARN.

A dry run (fpl_publish.run_mode) never calls the API unless its dispatch
ticked odds_live (FPL_ODDS_LIVE=true): otherwise ODDS SKIPPED (dry run). A
real run always calls it (RULING W1 decisions, point 1).

The ODDS OK line gives the events, how many carry a totals market (Step 5:
"confirm totals coverage"), the prices, the file and its size, and the
x-requests-used / -remaining / -last headers (Step 5: "log the credits used").

Standard library only.
"""

import gzip
import io
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SPORT, REGIONS, MARKETS = "soccer_epl", "uk,eu", "h2h,totals"
API = "https://api.the-odds-api.com/v4/sports"
ODDS_DIR = "odds"
LAY = "h2h_lay"             # exchange lay prices: kept in the file, skipped by readers unless asked
_urlopen = urllib.request.urlopen


def request(key):
    """The one request. Its URL holds the key: never print or log it."""
    query = urllib.parse.urlencode({"apiKey": key, "regions": REGIONS, "markets": MARKETS,
                                    "oddsFormat": "decimal", "dateFormat": "iso"})
    return urllib.request.Request(f"{API}/{SPORT}/odds/?{query}",
                                  headers={"Accept": "application/json", "User-Agent": "fpl-odds"})


def file_name(fetched):
    """odds_<fetched UTC, YYYY-MM-DDTHHMMZ>.json.gz"""
    return f"odds_{fetched.astimezone(timezone.utc):%Y-%m-%dT%H%M}Z.json.gz"


def gz(body):
    """The body as gzip with no name and mtime 0: the same body, the same bytes."""
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as fh:
        fh.write(body)
    return out.getvalue()


def read_snapshot(path):
    """(fetched UTC from the file name, the events) of one odds file."""
    name = os.path.basename(path)
    fetched = datetime.strptime(name[len("odds_"):-len("Z.json.gz")], "%Y-%m-%dT%H%M")
    with gzip.open(path, "rb") as fh:
        return fetched.replace(tzinfo=timezone.utc), json.loads(fh.read())


def rows(events, fetched, lay=False):
    """One row per price: (fetched_at_utc, event_id, commence_time, home_team,
    away_team, bookmaker, last_update, market, outcome, point, price). point is
    the line of a totals price ("2.5"), "" for a market without one. The
    exchanges' h2h_lay prices are skipped unless `lay`."""
    out = []
    for ev in events:
        for bm in ev.get("bookmakers") or []:
            for mk in bm.get("markets") or []:
                if mk.get("key") == LAY and not lay:
                    continue
                for oc in mk.get("outcomes") or []:
                    point = oc.get("point")
                    out.append((fetched, ev["id"], ev.get("commence_time"), ev.get("home_team"),
                                ev.get("away_team"), bm.get("key"),
                                mk.get("last_update") or bm.get("last_update"), mk.get("key"),
                                oc.get("name"), "" if point is None else str(point),
                                float(oc["price"])))
    return out


def collect(data_dir, key, now=None, opener=None):
    """Fetch tonight's answer and write it to odds/. Returns the one line to
    print."""
    if not key:
        return "ODDS SKIPPED no ODDS_API_KEY in this run - no snapshot tonight"
    opener = opener or _urlopen
    fetched = now or datetime.now(timezone.utc)
    try:
        with opener(request(key), timeout=30) as r:
            body = r.read()
            used = r.headers.get("x-requests-used")
            left = r.headers.get("x-requests-remaining")
            last = r.headers.get("x-requests-last")
    except urllib.error.HTTPError as e:
        code = e.code
        e.close()
        return f"ODDS FAILED  HTTP {code} - no snapshot tonight"
    except OSError as e:
        return f"ODDS FAILED  network ({type(e).__name__}) - no snapshot tonight"
    try:
        events = json.loads(body)
    except ValueError:
        return "ODDS FAILED  the answer is not JSON - no snapshot tonight"
    if not isinstance(events, list):
        return "ODDS FAILED  the answer is not a list of events - no snapshot tonight"
    name = file_name(fetched)
    folder = os.path.join(data_dir, ODDS_DIR)
    os.makedirs(folder, exist_ok=True)
    data = gz(body)
    try:
        with open(os.path.join(folder, name), "xb") as fh:     # never over an existing file
            fh.write(data)
    except FileExistsError:
        return f"ODDS FAILED  {ODDS_DIR}/{name} exists - a snapshot is never rewritten"
    stamp = fetched.astimezone(timezone.utc).isoformat(timespec="seconds")
    prices = len(rows(events, stamp, lay=True))
    totals = sum(1 for ev in events if any(m.get("key") == "totals"
                                           for b in ev.get("bookmakers") or []
                                           for m in b.get("markets") or []))
    return (f"ODDS OK      {len(events)} events ({totals} with totals), {prices} prices, "
            f"{ODDS_DIR}/{name} {len(data)} bytes; credits used {used}, remaining {left}, "
            f"this request {last}")


def main(env=None, say=print, data_dir=".", opener=None):
    import fpl_publish
    env = os.environ if env is None else env
    mode, _ = fpl_publish.run_mode(env)
    if mode == "dry" and (env.get("FPL_ODDS_LIVE") or "").strip().lower() != "true":
        say("ODDS SKIPPED (dry run): odds_live not ticked - no Odds API call")
        return 0
    say(collect(data_dir, env.get("ODDS_API_KEY", ""), opener=opener))
    return 0


if __name__ == "__main__":
    sys.exit(main())
