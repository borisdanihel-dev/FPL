"""
fpl_odds.py  -  the Odds API collector (W1; BUILD_PLAN.md Step 5 item 1, the
collector only; RULING FAST-TRACK item 3).

    python fpl_odds.py        run in DATA_DIR by fpl_nightly.py, after the sync

One request a night: GET /v4/sports/soccer_epl/odds/ with markets h2h,totals,
regions uk,eu, decimal odds. Every price it returns goes into the table
odds_snapshots of fpl.sqlite (the schema is fpl_sync.py's), one row per
(event, bookmaker, market, outcome, line), with the fetch time - forecasts may
only use snapshots fetched before a deadline (Step 5). Nothing is fitted or
used here; the models come later, offline.

The key comes from ODDS_API_KEY (a GitHub Actions secret; S1 amendment 1,
item 1) and is never printed, logged or written: the request URL carries it,
so the URL is never shown, and a failure is reported by its kind and HTTP
status only. Without a key, or when the request fails, it says so in one line
- ODDS SKIPPED or ODDS FAILED - and exits 0: tonight's other data still
commits, and checks.py (check 30) turns the line into a WARN.

Credits: the x-requests-used / -remaining / -last headers of the response go
into the ODDS OK line (Step 5: "log the credits used"), with the number of
events that carry a totals market (Step 5: "confirm totals coverage").

Standard library only.
"""

import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SPORT, REGIONS, MARKETS = "soccer_epl", "uk,eu", "h2h,totals"
API = "https://api.the-odds-api.com/v4/sports"
DB_PATH = "fpl.sqlite"
_urlopen = urllib.request.urlopen


def request(key):
    """The one request. Its URL holds the key: never print or log it."""
    query = urllib.parse.urlencode({"apiKey": key, "regions": REGIONS, "markets": MARKETS,
                                    "oddsFormat": "decimal", "dateFormat": "iso"})
    return urllib.request.Request(f"{API}/{SPORT}/odds/?{query}",
                                  headers={"Accept": "application/json", "User-Agent": "fpl-odds"})


def rows(events, fetched):
    """One row per price: (fetched_at_utc, event_id, commence_time, home_team,
    away_team, bookmaker, last_update, market, outcome, point, price). point is
    the line of a totals price ("2.5"), "" for a market without one."""
    out = []
    for ev in events:
        for bm in ev.get("bookmakers") or []:
            for mk in bm.get("markets") or []:
                for oc in mk.get("outcomes") or []:
                    point = oc.get("point")
                    out.append((fetched, ev["id"], ev.get("commence_time"), ev.get("home_team"),
                                ev.get("away_team"), bm.get("key"),
                                mk.get("last_update") or bm.get("last_update"), mk.get("key"),
                                oc.get("name"), "" if point is None else str(point),
                                float(oc["price"])))
    return out


def collect(db, key, now=None, opener=None):
    """Fetch and store tonight's snapshot. Returns the one line to print."""
    if not key:
        return "ODDS SKIPPED no ODDS_API_KEY in this run - no snapshot tonight"
    opener = opener or _urlopen
    fetched = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    try:
        with opener(request(key), timeout=30) as r:
            events = json.load(r)
            used = r.headers.get("x-requests-used")
            left = r.headers.get("x-requests-remaining")
            last = r.headers.get("x-requests-last")
    except urllib.error.HTTPError as e:
        code = e.code
        e.close()
        return f"ODDS FAILED  HTTP {code} - no snapshot tonight"
    except ValueError:
        return "ODDS FAILED  the answer is not JSON - no snapshot tonight"
    except OSError as e:
        return f"ODDS FAILED  network ({type(e).__name__}) - no snapshot tonight"
    if not isinstance(events, list):
        return "ODDS FAILED  the answer is not a list of events - no snapshot tonight"
    got = rows(events, fetched)
    db.executemany("INSERT OR REPLACE INTO odds_snapshots VALUES (?,?,?,?,?,?,?,?,?,?,?)", got)
    db.commit()
    totals = sum(1 for ev in events if any(m.get("key") == "totals"
                                           for b in ev.get("bookmakers") or []
                                           for m in b.get("markets") or []))
    return (f"ODDS OK      {len(events)} events ({totals} with totals), {len(got)} prices "
            f"fetched {fetched}; credits used {used}, remaining {left}, this request {last}")


def main(env=None, say=print, db_path=DB_PATH, opener=None):
    import fpl_sync
    env = os.environ if env is None else env
    db = sqlite3.connect(db_path)
    try:
        db.executescript(fpl_sync.SCHEMA)
        say(collect(db, env.get("ODDS_API_KEY", ""), opener=opener))
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
