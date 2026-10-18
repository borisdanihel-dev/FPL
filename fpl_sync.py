"""
fpl_sync.py  —  pulls the public FPL API into a local SQLite database
and exports a compact analysis bundle (fpl_export_gwN.json) to upload.

Standard library only: no pip installs needed.

Usage:
    python fpl_sync.py            # sync everything, export latest finished GW
    python fpl_sync.py --gw 3     # export a specific gameweek instead

Edit LEAGUE_ID / MY_ENTRY below if they ever change.
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

LEAGUE_ID = 455565          # VAR Wars: Revenge of the Ref
MY_ENTRY = 3073318          # 1. FC Kiripolcz
DB_PATH = "fpl.sqlite"
BASE = "https://fantasy.premierleague.com/api"
PAUSE = 0.4                 # seconds between requests, be polite to the API
# The API turns scripts away from cloud addresses; ask the way a browser does.
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
RETRIES = 3                 # after the first attempt
BACKOFF = 2.0               # seconds before the first retry, doubling: 2, 4, 8
FAILED = []                 # urls that still failed after every retry
# What tonight's sync saw, printed as one "SYNC STATS {json}" line at the end
# of every sync, finished or not; checks.py reads it from the run log (S3,
# Step 3 checks 1-5, 8 and 9). calls: [path, final status] per request -
# 200, an HTTP code, "network" or "bad-json".
STATS = {"calls": []}
STATS_PREFIX = "SYNC STATS "
# Step 3 check 8: the fields every element and event must carry, and their type
REQUIRED_ELEMENT = {"id": int, "code": int, "team": int, "element_type": int,
                    "now_cost": int, "status": str, "minutes": int, "total_points": int,
                    "defensive_contribution": int}
REQUIRED_EVENT = {"deadline_time": str, "data_checked": bool}
RULESET = "2026-27"         # the scoring rules of the season this sync pulls (Step 2.7)
LONDON = "Europe/London"    # FPL prices change at 00:00 UK time (Step 2.4)
EARLY_HOURS = 12            # a fetch before 12:00 London time came after that day's
                            # 00:00 UK price change: flagged (Step 2.4)
PRICE_GAPS_FILE = "price_gaps_known.txt"   # days known to have no price snapshot, with
                                           # their reason; next to this file (S2 amendment 1.3)
_urlopen = urllib.request.urlopen
_sleep = time.sleep

# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------

def get(path):
    """One API path as JSON, with a browser-style User-Agent. Retried with
    doubling backoff, up to RETRIES times, only on HTTP 429, a 5xx or a
    network error; a 403 at most once; any other HTTP error, or a body that is
    not JSON, not at all (Step 3, check 2). A request that never succeeds is
    recorded in FAILED and returns None - the sync saves what it can, and
    main() then exits non-zero so a partial sync is never mistaken for a clean
    one. Every request's final status goes into STATS. PAUSE follows each
    success: 0.4 s, inside the 0.3-0.5 s the check asks for between calls."""
    url = f"{BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"})
    forbidden = 0
    for attempt in range(RETRIES + 1):
        try:
            with _urlopen(req, timeout=30) as r:
                data = json.load(r)
            _sleep(PAUSE)
            STATS["calls"].append([path, 200])
            return data
        except urllib.error.HTTPError as e:
            status, why = e.code, str(e)
            e.close()
            if e.code == 403:
                forbidden += 1
            again = e.code == 429 or e.code >= 500 or (e.code == 403 and forbidden == 1)
        except ValueError as e:                      # a body that is not JSON
            status, why, again = "bad-json", str(e), False
        except OSError as e:                         # URLError, timeouts, resets
            status, why, again = "network", str(e), True
        if not again or attempt == RETRIES:
            print(f"  ! failed {path}: {why}")    # the path, never the full URL
            FAILED.append(url)
            STATS["calls"].append([path, status])
            return None
        wait = BACKOFF * 2 ** attempt
        print(f"  retry {attempt + 1}/{RETRIES} in {wait:.0f}s - {path}: {why}")
        _sleep(wait)


def ep_next(p):
    """FPL's expected points for the next gameweek (W1: source fpl_ep), as a
    number; None when the API gives none - never a 0."""
    v = p.get("ep_next")
    return None if v in (None, "") else float(v)


def field_problems(items, spec, what):
    """Every missing or mistyped required field in `items` (Step 3, check 8):
    a list of "<what> <id>: <field> ..." strings. bool is not an int here."""
    out = []
    for it in items:
        for field, kind in spec.items():
            v = it.get(field)
            ok = (isinstance(v, kind) and not (kind is int and isinstance(v, bool)))
            if not ok:
                out.append(f"{what} {it.get('id')}: {field} "
                           f"{'missing' if v is None else 'is ' + type(v).__name__}")
    return out

def num(value, field):
    """A numeric API field as float. Many arrive as strings ("0.00"); each is
    cast explicitly, and a missing value is an error, never a silent 0
    (Step 2.6)."""
    if value is None:
        raise ValueError(f"required numeric field {field!r} is missing")
    return float(value)


def required(obj, field):
    """obj[field], or an error naming it: a required field never defaults to 0
    (Step 2.6)."""
    if obj.get(field) is None:
        raise ValueError(f"required field {field!r} is missing")
    return obj[field]


def london_tz():
    """Europe/London from zoneinfo. Windows ships no time-zone database: there
    the tzdata package is required, and without it the sync stops with a clear
    error rather than label a day wrongly (Step 2.4)."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        return ZoneInfo(LONDON)
    except ZoneInfoNotFoundError:
        sys.exit("TIME ZONE MISSING: Europe/London is not available. On Windows "
                 "install the tzdata package (python -m pip install tzdata) - price "
                 "snapshots are labelled with the London calendar day.")


def price_labels(fetched_utc, tz):
    """(UTC date, London date, early) for a price fetch. The London date is the
    day whose prices the snapshot holds: prices change at 00:00 UK. `early`
    flags a fetch made after that midnight and before noon London time - it
    holds the new day's prices, so the evening snapshot of the day before is
    missing unless another run took it (Step 2.4)."""
    local = fetched_utc.astimezone(tz)
    return (fetched_utc.date().isoformat(), local.date().isoformat(),
            local.hour < EARLY_HOURS)


def missing_dates(dates):
    """Calendar dates absent between the first and the last of `dates`."""
    from datetime import date, timedelta
    have = sorted({date.fromisoformat(d) for d in dates if d})
    if not have:
        return []
    have_set = set(have)
    return [str(have[0] + timedelta(n)) for n in range((have[-1] - have[0]).days + 1)
            if have[0] + timedelta(n) not in have_set]


def known_price_gaps(path=None):
    """({date: reason}, problem) from the committed list of days known to
    have no price snapshot (S2 amendment 1, point 3): one "YYYY-MM-DD reason"
    per line; a line starting with "#" is a comment. PRICE DATES MISSING warns
    only on a gap that is not listed. A list that cannot be read, or a line
    without a date or a reason, is returned as `problem` with nothing listed,
    so every gap is warned - never fewer."""
    from datetime import date
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), PRICE_GAPS_FILE)
    name = os.path.basename(path)
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            lines = fh.read().splitlines()
    except OSError as e:
        return {}, f"cannot read {name}: {e.strerror}"
    known = {}
    for n, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        day, _, reason = line.strip().partition(" ")
        try:
            day = date.fromisoformat(day).isoformat()
        except ValueError:
            return {}, f"{name} line {n}: {day!r} is not a date"
        if not reason.strip():
            return {}, f"{name} line {n}: {day} has no reason"
        known[day] = reason.strip()
    return known, None


def deadline_gameweeks(events, now):
    """(current, next) by deadline_time alone (Step 2.5): current = the last
    event whose deadline has passed (0 before GW1), next = the first event
    whose deadline is still ahead (None after GW38). The API's is_current and
    is_next flags are never used for this."""
    passed, ahead = [], []
    for e in events:
        dl = datetime.fromisoformat(required(e, "deadline_time").replace("Z", "+00:00"))
        (passed if dl <= now else ahead).append(e["id"])
    return (max(passed) if passed else 0), (min(ahead) if ahead else None)

# ----------------------------------------------------------------------------
# Schema
# ----------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY, name TEXT, short_name TEXT, strength INTEGER,
    att_h INTEGER, att_a INTEGER, def_h INTEGER, def_a INTEGER);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY, web_name TEXT, first_name TEXT, second_name TEXT,
    team_id INTEGER, position INTEGER, now_cost INTEGER, cost_change_start INTEGER,
    selected_by_percent REAL, total_points INTEGER, minutes INTEGER,
    goals INTEGER, assists INTEGER, clean_sheets INTEGER, bonus INTEGER,
    expected_goals REAL, expected_assists REAL, ict_index REAL,
    status TEXT, chance_next_round INTEGER, news TEXT, updated_at TEXT,
    starts INTEGER, pens_order INTEGER, corners_order INTEGER, fk_order INTEGER,
    xgc REAL, tin_event INTEGER, tout_event INTEGER, form REAL, ppg REAL,
    influence REAL, creativity REAL, threat REAL, ep_next REAL);

CREATE TABLE IF NOT EXISTS player_history (
    player_id INTEGER, season TEXT, minutes INTEGER, total_points INTEGER,
    goals INTEGER, assists INTEGER, clean_sheets INTEGER, bonus INTEGER,
    expected_goals REAL, expected_assists REAL, starts INTEGER,
    PRIMARY KEY (player_id, season));

CREATE TABLE IF NOT EXISTS price_history (
    player_id INTEGER, date TEXT, now_cost INTEGER,
    fetched_at_utc TEXT, london_date TEXT,
    PRIMARY KEY (player_id, date));

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY, name TEXT, deadline_time TEXT, finished INTEGER,
    average_score INTEGER, highest_score INTEGER, most_captained INTEGER,
    data_checked INTEGER);

CREATE TABLE IF NOT EXISTS fixtures (
    id INTEGER PRIMARY KEY, event INTEGER, kickoff_time TEXT,
    team_h INTEGER, team_a INTEGER, team_h_difficulty INTEGER,
    team_a_difficulty INTEGER, team_h_score INTEGER, team_a_score INTEGER,
    finished INTEGER, started INTEGER, fetched_at_utc TEXT);

CREATE TABLE IF NOT EXISTS player_gw (
    player_id INTEGER, event INTEGER, minutes INTEGER, total_points INTEGER,
    goals INTEGER, assists INTEGER, clean_sheets INTEGER, goals_conceded INTEGER,
    bonus INTEGER, bps INTEGER, saves INTEGER, yellow INTEGER, red INTEGER,
    expected_goals REAL, expected_assists REAL, defensive_contribution INTEGER,
    starts INTEGER, fetched_at_utc TEXT, ruleset TEXT,
    PRIMARY KEY (player_id, event));

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY, entry_name TEXT, player_name TEXT);

CREATE TABLE IF NOT EXISTS standings (
    entry_id INTEGER, event INTEGER, rank INTEGER, event_total INTEGER,
    total INTEGER, PRIMARY KEY (entry_id, event));

CREATE TABLE IF NOT EXISTS entry_gw (
    entry_id INTEGER, event INTEGER, points INTEGER, total_points INTEGER,
    overall_rank INTEGER, bank INTEGER, value INTEGER, transfers INTEGER,
    transfers_cost INTEGER, points_on_bench INTEGER, active_chip TEXT,
    fetched_at_utc TEXT,
    PRIMARY KEY (entry_id, event));

CREATE TABLE IF NOT EXISTS picks (
    entry_id INTEGER, event INTEGER, player_id INTEGER, position INTEGER,
    multiplier INTEGER, is_captain INTEGER, is_vice INTEGER,
    PRIMARY KEY (entry_id, event, player_id));

CREATE TABLE IF NOT EXISTS transfers (
    entry_id INTEGER, event INTEGER, time TEXT, player_in INTEGER,
    player_out INTEGER, cost_in INTEGER, cost_out INTEGER,
    PRIMARY KEY (entry_id, time, player_in, player_out));

CREATE TABLE IF NOT EXISTS chips (
    entry_id INTEGER, name TEXT, event INTEGER, time TEXT,
    PRIMARY KEY (entry_id, name, event));

CREATE TABLE IF NOT EXISTS automatic_subs (
    entry_id INTEGER, event INTEGER, element_in INTEGER, element_out INTEGER,
    fetched_at_utc TEXT,
    PRIMARY KEY (entry_id, event, element_in, element_out));
"""

MIGRATIONS = {
    "players": ["starts INTEGER", "pens_order INTEGER", "corners_order INTEGER",
                "fk_order INTEGER", "xgc REAL", "tin_event INTEGER",
                "tout_event INTEGER", "form REAL", "ppg REAL",
                "influence REAL", "creativity REAL", "threat REAL",
                "ep_next REAL"],                 # W1: FPL's ep_next, recorded as fpl_ep
    "teams": ["att_h INTEGER", "att_a INTEGER", "def_h INTEGER", "def_a INTEGER"],
    "player_gw": ["starts INTEGER", "fetched_at_utc TEXT", "ruleset TEXT"],
    "events": ["data_checked INTEGER"],
    # S2: added with ALTER TABLE; rows already stored keep NULL - their fetch
    # time was never recorded (S2 ruling 3)
    "price_history": ["fetched_at_utc TEXT", "london_date TEXT"],
    "fixtures": ["started INTEGER", "fetched_at_utc TEXT"],
    "entry_gw": ["fetched_at_utc TEXT"],
}


def migrate(db):
    """Add columns to a database created by an earlier version."""
    for table, cols in MIGRATIONS.items():
        have = {r[1] for r in db.execute(f"PRAGMA table_info({table})")}
        for col in cols:
            name = col.split()[0]
            if name not in have:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
                print(f"  + {table}.{name}")
    db.commit()


# ----------------------------------------------------------------------------
# Sync steps
# ----------------------------------------------------------------------------

def sync_bootstrap(db):
    print("bootstrap-static ...")
    bs = get("bootstrap-static/")
    if not bs:
        sys.exit("cannot reach FPL API")
    # what checks 3, 4, 8 and 9 need, taken before anything can raise
    elements = bs.get("elements") or []
    STATS["elements"] = len(elements)
    STATS["element_ids"] = sorted(e.get("id") for e in elements if isinstance(e.get("id"), int))
    STATS["element_keys"] = sorted(set().union(*(e.keys() for e in elements))) if elements else []
    STATS["teams"] = len(bs.get("teams") or [])
    STATS["field_problems"] = (field_problems(elements, REQUIRED_ELEMENT, "element")
                               + field_problems(bs.get("events") or [], REQUIRED_EVENT, "event"))
    fetched = datetime.now(timezone.utc)
    now = fetched.isoformat(timespec="seconds")
    today, london_day, early = price_labels(fetched, london_tz())

    db.executemany("INSERT OR REPLACE INTO teams VALUES (?,?,?,?,?,?,?,?)",
                   [(t["id"], t["name"], t["short_name"], t["strength"],
                     t.get("strength_attack_home"), t.get("strength_attack_away"),
                     t.get("strength_defence_home"), t.get("strength_defence_away"))
                    for t in bs["teams"]])

    rows = []
    for p in bs["elements"]:
        rows.append((p["id"], p["web_name"], p["first_name"], p["second_name"],
                     p["team"], p["element_type"], p["now_cost"], p["cost_change_start"],
                     num(p["selected_by_percent"], "selected_by_percent"),
                     required(p, "total_points"), required(p, "minutes"),
                     p["goals_scored"], p["assists"], p["clean_sheets"], p["bonus"],
                     num(p.get("expected_goals"), "expected_goals"),
                     num(p.get("expected_assists"), "expected_assists"),
                     num(p.get("ict_index"), "ict_index"), required(p, "status"),
                     p.get("chance_of_playing_next_round"), p.get("news", ""), now,
                     p.get("starts") or 0,
                     p.get("penalties_order"),
                     p.get("corners_and_indirect_freekicks_order"),
                     p.get("direct_freekicks_order"),
                     num(p.get("expected_goals_conceded"), "expected_goals_conceded"),
                     p.get("transfers_in_event") or 0,
                     p.get("transfers_out_event") or 0,
                     num(p.get("form"), "form"),
                     num(p.get("points_per_game"), "points_per_game"),
                     num(p.get("influence"), "influence"),
                     num(p.get("creativity"), "creativity"),
                     num(p.get("threat"), "threat"),
                     ep_next(p)))
        db.execute("INSERT OR REPLACE INTO price_history "
                   "(player_id, date, now_cost, fetched_at_utc, london_date) VALUES (?,?,?,?,?)",
                   (required(p, "id"), today, required(p, "now_cost"), now, london_day))
    db.executemany("INSERT OR REPLACE INTO players VALUES (%s)" % ",".join("?" * 35), rows)

    # data_checked = points and bonus are final. `finished` only means the
    # matches ended; grading keys on data_checked.
    db.executemany("INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?,?,?)",
                   [(e["id"], e["name"], required(e, "deadline_time"), int(e["finished"]),
                     e.get("average_entry_score"), e.get("highest_score"),
                     e.get("most_captained"), int(required(e, "data_checked") is True))
                    for e in bs["events"]])
    db.commit()
    if early:
        print(f"PRICE DATE FLAG: fetched {now} = after 00:00 UK - this snapshot holds "
              f"the prices of London day {london_day}, not of the evening before")
    # warned only for a day not on the committed known-gaps list (S2 amendment 1.3)
    known, problem = known_price_gaps()
    if problem:
        print(f"PRICE GAPS LIST UNREADABLE: {problem} - every gap is warned")
    gaps = [g for g in missing_dates(r[0] for r in db.execute("SELECT DISTINCT date FROM price_history"))
            if g not in known]
    if gaps:
        print(f"PRICE DATES MISSING: {len(gaps)} day(s) without a snapshot: {', '.join(gaps)}")
    # the gameweek that has started = the last one whose deadline has passed;
    # the target of the forecasts = the next one (Step 2.5). The flags only
    # get compared, and a disagreement is logged.
    current, nxt = deadline_gameweeks(bs["events"], fetched)
    flag_cur = next((e["id"] for e in bs["events"] if e.get("is_current")), 0)
    flag_next = next((e["id"] for e in bs["events"] if e.get("is_next")), None)
    if (flag_cur, flag_next) != (current, nxt):
        print(f"GAMEWEEK FLAGS DISAGREE: by deadline_time current GW{current}, next "
              f"GW{nxt}; the API flags say is_current GW{flag_cur}, is_next GW{flag_next}"
              f" - using deadline_time")
    return current


def sync_fixtures(db):
    print("fixtures ...")
    fx = get("fixtures/") or []
    STATS["fixtures"] = len(fx)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db.executemany("INSERT OR REPLACE INTO fixtures (id, event, kickoff_time, team_h, team_a, "
                   "team_h_difficulty, team_a_difficulty, team_h_score, team_a_score, "
                   "finished, started, fetched_at_utc) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                   [(f["id"], f.get("event"), f.get("kickoff_time"), f["team_h"], f["team_a"],
                     f["team_h_difficulty"], f["team_a_difficulty"],
                     f.get("team_h_score"), f.get("team_a_score"), int(f["finished"]),
                     int(required(f, "started") is True), now)
                    for f in fx])
    db.commit()


def sync_player_gw(db, last_gw, refetch=False):
    for gw in range(1, last_gw + 1):
        finished = db.execute("SELECT finished FROM events WHERE id=?", (gw,)).fetchone()
        done = db.execute("SELECT COUNT(*) FROM player_gw WHERE event=?", (gw,)).fetchone()[0]
        if done > 300 and finished and finished[0] and not refetch:
            continue          # stored and final, skip (unless --refetch)
        print(f"live stats GW{gw} ...")
        live = get(f"event/{gw}/live/")
        if not live:
            continue
        rows = []
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for el in live["elements"]:
            s = el["stats"]
            # one row per (player, gameweek): the live endpoint's stats are the
            # gameweek total over all of a double's fixtures (Step 2.6)
            rows.append((el["id"], gw, required(s, "minutes"), required(s, "total_points"),
                         s["goals_scored"],
                         s["assists"], s["clean_sheets"], s["goals_conceded"], s["bonus"],
                         s["bps"], s["saves"], s["yellow_cards"], s["red_cards"],
                         num(s.get("expected_goals"), "expected_goals"),
                         num(s.get("expected_assists"), "expected_assists"),
                         required(s, "defensive_contribution"),
                         s.get("starts", 0), now, RULESET))
        db.executemany("INSERT OR REPLACE INTO player_gw (player_id, event, minutes, total_points, "
                       "goals, assists, clean_sheets, goals_conceded, bonus, bps, saves, yellow, "
                       "red, expected_goals, expected_assists, defensive_contribution, starts, "
                       "fetched_at_utc, ruleset) VALUES (%s)" % ",".join("?" * 19), rows)
        db.commit()


def sync_history(db, only_relevant=True):
    """element-summary/{id}/ -> history_past. One request per player, so this is
    opt-in (--history) and cached: it only refetches players it has never seen."""
    ids = [r[0] for r in db.execute(
        "SELECT id FROM players WHERE minutes>0 OR now_cost>=45 ORDER BY id")] \
        if only_relevant else [r[0] for r in db.execute("SELECT id FROM players")]
    have = {r[0] for r in db.execute("SELECT DISTINCT player_id FROM player_history")}
    todo = [i for i in ids if i not in have]
    if not todo:
        print("player history already cached")
        return
    print(f"player history: fetching {len(todo)} players (cached after this) ...")
    rows = []
    for n, pid in enumerate(todo, 1):
        if n % 100 == 0:
            print(f"  {n}/{len(todo)} ...")
        summary = get(f"element-summary/{pid}/")
        if not summary:
            continue
        for h in summary.get("history_past", []):
            rows.append((pid, h["season_name"], h["minutes"], h["total_points"],
                         h["goals_scored"], h["assists"], h["clean_sheets"],
                         h["bonus"], float(h.get("expected_goals") or 0),
                         float(h.get("expected_assists") or 0),
                         h.get("starts") or 0))
    if rows:
        db.executemany(
            "INSERT OR REPLACE INTO player_history VALUES (%s)" % ",".join("?" * 11),
            rows)
        db.commit()
    print(f"  stored {len(rows)} season rows")


def sync_league(db, last_gw):
    print("league standings ...")
    lg = get(f"leagues-classic/{LEAGUE_ID}/standings/")
    if not lg:
        return []
    entries = []
    for r in lg["standings"]["results"]:
        entries.append(r["entry"])
        db.execute("INSERT OR REPLACE INTO entries VALUES (?,?,?)",
                   (r["entry"], r["entry_name"], r["player_name"]))
        db.execute("INSERT OR REPLACE INTO standings VALUES (?,?,?,?,?)",
                   (r["entry"], last_gw, r["rank"], r["event_total"], r["total"]))
    db.commit()
    return entries


def sync_entries(db, entries, last_gw):
    for eid in entries:
        print(f"entry {eid} ...")
        hist = get(f"entry/{eid}/history/")
        if hist:
            for c in hist.get("chips", []):
                db.execute("INSERT OR REPLACE INTO chips VALUES (?,?,?,?)",
                           (eid, c["name"], c["event"], c["time"]))
        tr = get(f"entry/{eid}/transfers/") or []
        for t in tr:
            db.execute("INSERT OR REPLACE INTO transfers VALUES (?,?,?,?,?,?,?)",
                       (eid, t["event"], t["time"], t["element_in"], t["element_out"],
                        t["element_in_cost"], t["element_out_cost"]))
        for gw in range(1, last_gw + 1):
            have = db.execute("SELECT 1 FROM entry_gw WHERE entry_id=? AND event=?",
                              (eid, gw)).fetchone()
            final = db.execute("SELECT finished FROM events WHERE id=?", (gw,)).fetchone()
            if have and final and final[0]:
                continue
            pk = get(f"entry/{eid}/event/{gw}/picks/")
            if not pk:
                continue
            h = pk["entry_history"]
            fetched = datetime.now(timezone.utc).isoformat(timespec="seconds")
            # fetched_at_utc set = this gameweek's automatic_subs are known (S2,
            # Step 2.10); a row stored before S2 has NULL and its subs unknown
            db.execute("INSERT OR REPLACE INTO entry_gw (entry_id, event, points, total_points, "
                       "overall_rank, bank, value, transfers, transfers_cost, points_on_bench, "
                       "active_chip, fetched_at_utc) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                       (eid, gw, h["points"], h["total_points"], h["overall_rank"], h["bank"],
                        h["value"], h["event_transfers"], h["event_transfers_cost"],
                        h["points_on_bench"], pk.get("active_chip"), fetched))
            db.executemany("INSERT OR REPLACE INTO automatic_subs (entry_id, event, element_in, "
                           "element_out, fetched_at_utc) VALUES (?,?,?,?,?)",
                           [(eid, gw, a["element_in"], a["element_out"], fetched)
                            for a in pk["automatic_subs"]])
            db.executemany("INSERT OR REPLACE INTO picks VALUES (?,?,?,?,?,?,?)",
                           [(eid, gw, p["element"], p["position"], p["multiplier"],
                             int(p["is_captain"]), int(p["is_vice_captain"])) for p in pk["picks"]])
        db.commit()

# ----------------------------------------------------------------------------
# Export bundle (what you upload for analysis)
# ----------------------------------------------------------------------------

def q(db, sql, args=()):
    cur = db.execute(sql, args)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def selling_price(buy, now):
    """FPL's selling price in tenths (Step 2.8): half of any rise, rounded
    down; all of any fall. Bought at 7.5, now 7.8 -> sells for 7.6."""
    return buy + (now - buy) // 2 if now > buy else now


def purchase_prices(db, entry, gw):
    """{player_id: purchase price in tenths, or None} for `entry`'s squad in
    gameweek `gw` (Step 2.8). A player's purchase price is the cost of his
    last transfer in up to `gw` - wildcard moves included, the moves of a
    Free Hit week not, as that squad reverted - else, for a squad picked
    before GW1, his season-start price (now_cost - cost_change_start: prices
    do not move before the GW1 deadline). An entry that joined later has no
    recorded price for its first squad: None, never a guess."""
    fh = {ev for (ev,) in db.execute(
        "SELECT event FROM entry_gw WHERE entry_id=? AND active_chip='freehit'", (entry,))}
    fh.discard(gw)                       # in a Free Hit week its own squad is the one shown
    first = db.execute("SELECT MIN(event) FROM picks WHERE entry_id=?", (entry,)).fetchone()[0]
    out = {}
    for (pid,) in db.execute("SELECT player_id FROM picks WHERE entry_id=? AND event=?",
                             (entry, gw)):
        bought = [c for ev, c in db.execute(
            "SELECT event, cost_in FROM transfers WHERE entry_id=? AND player_in=? AND event<=? "
            "ORDER BY time DESC", (entry, pid, gw)) if ev not in fh]
        if bought:
            out[pid] = bought[0]
        elif first == 1:
            row = db.execute("SELECT now_cost - cost_change_start FROM players WHERE id=?",
                             (pid,)).fetchone()
            out[pid] = row[0] if row else None
        else:
            out[pid] = None
    return out


def export(db, gw):
    out = {"schema": 2,
           "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "league_id": LEAGUE_ID, "my_entry": MY_ENTRY, "gameweek": gw}

    out["standings"] = q(db, """
        SELECT e.id AS entry_id, e.entry_name, e.player_name, s.rank, s.event_total, s.total,
               g.value, g.bank, g.points_on_bench, g.transfers, g.transfers_cost, g.active_chip
        FROM standings s JOIN entries e ON e.id=s.entry_id
        LEFT JOIN entry_gw g ON g.entry_id=s.entry_id AND g.event=s.event
        WHERE s.event=? ORDER BY s.rank""", (gw,))

    out["chips_used"] = q(db, """
        SELECT e.entry_name, c.name, c.event FROM chips c JOIN entries e ON e.id=c.entry_id
        ORDER BY e.entry_name, c.event""")

    out["squads"] = q(db, """
        SELECT e.id AS entry_id, e.entry_name, p.position AS slot, p.player_id,
               pl.web_name, t.short_name AS team,
               pl.position AS pos, pl.now_cost/10.0 AS price, p.multiplier,
               p.is_captain, p.is_vice, g.total_points AS gw_points, g.minutes
        FROM picks p JOIN entries e ON e.id=p.entry_id
        JOIN players pl ON pl.id=p.player_id JOIN teams t ON t.id=pl.team_id
        LEFT JOIN player_gw g ON g.player_id=p.player_id AND g.event=p.event
        WHERE p.event=? ORDER BY e.entry_name, p.position""", (gw,))
    # selling prices, never `value`, for every budget (Step 2.8)
    now_cost = dict(db.execute("SELECT id, now_cost FROM players"))
    bought = {}
    for r in out["squads"]:
        if r["entry_id"] not in bought:
            bought[r["entry_id"]] = purchase_prices(db, r["entry_id"], gw)
        buy = bought[r["entry_id"]].get(r["player_id"])
        now = now_cost.get(r["player_id"])
        r["purchase_price"] = buy / 10.0 if buy is not None else None
        r["selling_price"] = (selling_price(buy, now) / 10.0
                              if buy is not None and now is not None else None)

    out["transfers"] = q(db, """
        SELECT e.entry_name, tr.event, pi.web_name AS player_in, po.web_name AS player_out,
               tr.cost_in/10.0 AS cost_in, tr.cost_out/10.0 AS cost_out
        FROM transfers tr JOIN entries e ON e.id=tr.entry_id
        JOIN players pi ON pi.id=tr.player_in JOIN players po ON po.id=tr.player_out
        ORDER BY tr.event, e.entry_name""")

    out["league_ownership"] = q(db, """
        SELECT pl.web_name, t.short_name AS team, pl.now_cost/10.0 AS price,
               COUNT(DISTINCT p.entry_id) AS owners,
               SUM(CASE WHEN p.entry_id=? THEN 1 ELSE 0 END) AS i_own,
               pl.total_points, pl.selected_by_percent
        FROM picks p JOIN players pl ON pl.id=p.player_id JOIN teams t ON t.id=pl.team_id
        WHERE p.event=? GROUP BY pl.id ORDER BY owners DESC, pl.total_points DESC""",
        (MY_ENTRY, gw))

    out["top_players_recent"] = q(db, """
        SELECT pl.web_name, t.short_name AS team, pl.position AS pos, pl.now_cost/10.0 AS price,
               pl.selected_by_percent, pl.status, pl.news,
               SUM(g.total_points) AS pts_last4, SUM(g.minutes) AS mins_last4,
               ROUND(SUM(g.expected_goals),2) AS xg_last4, ROUND(SUM(g.expected_assists),2) AS xa_last4
        FROM players pl JOIN teams t ON t.id=pl.team_id
        JOIN player_gw g ON g.player_id=pl.id AND g.event BETWEEN ?-3 AND ?
        GROUP BY pl.id HAVING mins_last4>0 ORDER BY pts_last4 DESC LIMIT 150""", (gw, gw))

    # every player in the game: season totals + last-4 form, for wildcard drafting
    out["all_players"] = q(db, """
        SELECT pl.id, pl.web_name, t.short_name AS team, pl.position AS pos,
               pl.now_cost/10.0 AS price, pl.cost_change_start/10.0 AS price_change_season,
               pl.selected_by_percent AS owned_pct, pl.status, pl.chance_next_round, pl.news,
               pl.total_points, pl.minutes, pl.goals, pl.assists, pl.clean_sheets, pl.bonus,
               ROUND(pl.expected_goals,2) AS xg, ROUND(pl.expected_assists,2) AS xa,
               pl.starts, pl.pens_order, pl.corners_order, pl.fk_order,
               ROUND(pl.xgc,2) AS xgc, pl.form, pl.ppg,
               ROUND(pl.threat,1) AS threat, ROUND(pl.creativity,1) AS creativity,
               ROUND(pl.influence,1) AS influence,
               pl.tin_event, pl.tout_event,
               (pl.tin_event - pl.tout_event) AS net_transfers, pl.ep_next,
               COALESCE(SUM(g.total_points),0) AS pts_last4,
               COALESCE(SUM(g.minutes),0) AS mins_last4,
               COALESCE(SUM(g.defensive_contribution),0) AS defcon_last4,
               COALESCE(SUM(g.starts),0) AS starts_last4
        FROM players pl JOIN teams t ON t.id=pl.team_id
        LEFT JOIN player_gw g ON g.player_id=pl.id AND g.event BETWEEN ?-3 AND ?
        GROUP BY pl.id ORDER BY pl.position, pl.total_points DESC""", (gw, gw))

    out["player_gw_recent"] = q(db, """
        SELECT g.event, g.player_id, pl.web_name, t.short_name AS team,
               pl.position AS pos,
               g.total_points AS pts, g.minutes AS mins, g.starts,
               g.goals AS g_, g.assists AS a_, g.clean_sheets AS cs,
               g.goals_conceded AS gc, g.bonus, g.bps,
               g.defensive_contribution AS defcon,
               ROUND(g.expected_goals,2) AS xg, ROUND(g.expected_assists,2) AS xa,
               COUNT(f.id) AS n_fixtures,
               CASE WHEN COUNT(f.id)=1 THEN MAX(CASE WHEN f.team_h=pl.team_id
                    THEN ta.short_name ELSE th.short_name END) END AS opp,
               CASE WHEN COUNT(f.id)=1 THEN MAX(CASE WHEN f.team_h=pl.team_id
                    THEN 'H' ELSE 'A' END) END AS venue,
               CASE WHEN COUNT(f.id)=1 THEN MAX(CASE WHEN f.team_h=pl.team_id
                    THEN f.team_h_difficulty ELSE f.team_a_difficulty END) END AS fdr,
               CASE WHEN COUNT(f.id)=1 THEN MAX(CASE WHEN f.team_h=pl.team_id
                    THEN f.team_a_score ELSE f.team_h_score END) END AS opp_goals
        FROM player_gw g
        JOIN players pl ON pl.id=g.player_id
        JOIN teams t ON t.id=pl.team_id
        LEFT JOIN fixtures f ON f.event=g.event
             AND (f.team_h=pl.team_id OR f.team_a=pl.team_id)
        LEFT JOIN teams th ON th.id=f.team_h
        LEFT JOIN teams ta ON ta.id=f.team_a
        WHERE g.event<=? AND g.minutes>0
        -- the whole season, not a window: the canonical slice, the measured
        -- weights and the rates need every gameweek (CHANGELOG 2026-09-24).
        -- one row per player per gameweek. player_gw holds a GW TOTAL, so the
        -- fixtures join must not fan a double out into two copies of it, and
        -- the per-match columns stay NULL when there is more than one match.
        GROUP BY g.player_id, g.event
        ORDER BY g.event, g.total_points DESC""", (gw,))

    out["fixtures_played"] = q(db, """
        SELECT f.event, th.short_name AS home, ta.short_name AS away,
               f.team_h_score AS h_goals, f.team_a_score AS a_goals,
               f.team_h_difficulty AS h_fdr, f.team_a_difficulty AS a_fdr,
               f.kickoff_time
        FROM fixtures f JOIN teams th ON th.id=f.team_h JOIN teams ta ON ta.id=f.team_a
        WHERE f.finished=1 AND f.event<=? AND f.team_h_score IS NOT NULL
        ORDER BY f.event, f.kickoff_time""", (gw,))

    out["player_history"] = q(db, """
        SELECT pl.web_name, t.short_name AS team, pl.position AS pos,
               h.season, h.minutes, h.total_points AS pts, h.starts,
               h.goals, h.assists, h.clean_sheets AS cs,
               ROUND(h.expected_goals,2) AS xg, ROUND(h.expected_assists,2) AS xa
        FROM player_history h
        JOIN players pl ON pl.id=h.player_id
        JOIN teams t ON t.id=pl.team_id
        WHERE h.minutes>=450
        ORDER BY pl.id, h.season""")

    out["teams"] = q(db, """
        SELECT short_name AS team, name, strength,
               att_h, att_a, def_h, def_a
        FROM teams ORDER BY short_name""")

    out["fixtures_next6"] = q(db, """
        SELECT f.event, th.short_name AS home, ta.short_name AS away,
               f.team_h_difficulty AS h_fdr, f.team_a_difficulty AS a_fdr, f.kickoff_time
        FROM fixtures f JOIN teams th ON th.id=f.team_h JOIN teams ta ON ta.id=f.team_a
        WHERE f.event BETWEEN ?+1 AND ?+6 ORDER BY f.event, f.kickoff_time""", (gw, gw))

    # what grading needs to know before it trusts a gameweek's points, and every
    # event's deadline: the forecast target and its cut-off (Step 2.2, 2.5)
    out["events"] = q(db, """
        SELECT id AS event, finished, data_checked, deadline_time FROM events
        ORDER BY id""")

    out["fixtures_status"] = q(db, """
        SELECT f.event, th.short_name AS home, ta.short_name AS away,
               f.kickoff_time, f.finished, f.started
        FROM fixtures f JOIN teams th ON th.id=f.team_h JOIN teams ta ON ta.id=f.team_a
        WHERE f.event<=? ORDER BY f.event, f.kickoff_time""", (gw,))

    # automatic substitutions as FPL applied them, where known (Step 2.10)
    out["automatic_subs"] = q(db, """
        SELECT a.entry_id, a.event, a.element_in, a.element_out
        FROM automatic_subs a WHERE a.event=? ORDER BY a.entry_id""", (gw,))
    out["autosubs_known"] = q(db, """
        SELECT entry_id, event FROM entry_gw
        WHERE event=? AND fetched_at_utc IS NOT NULL ORDER BY entry_id""", (gw,))

    out["price_changes_7d"] = q(db, """
        SELECT pl.web_name, t.short_name AS team, a.now_cost/10.0 AS price_now,
               b.now_cost/10.0 AS price_7d_ago, (a.now_cost-b.now_cost)/10.0 AS change
        FROM price_history a JOIN price_history b ON b.player_id=a.player_id
        JOIN players pl ON pl.id=a.player_id JOIN teams t ON t.id=pl.team_id
        WHERE a.date=(SELECT MAX(date) FROM price_history)
          AND b.date=(SELECT MIN(date) FROM price_history WHERE date>=date('now','-7 day'))
          AND a.now_cost<>b.now_cost ORDER BY change DESC""")

    fname = f"fpl_export_gw{gw}.json"
    with open(fname, "w", encoding="utf-8", newline="") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nexported -> {fname}  (upload this file to Claude)")

# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gw", type=int, help="gameweek to export (default: last finished)")
    ap.add_argument("--history", action="store_true",
                    help="fetch previous-season baselines (slow, one call per "
                         "player, cached afterwards)")
    ap.add_argument("--refetch", action="store_true",
                    help="re-pull finished gameweeks; backfills newly added columns")
    args = ap.parse_args()

    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    migrate(db)

    try:
        last_gw = sync_bootstrap(db)
        sync_fixtures(db)
        if last_gw == 0:
            print("no finished gameweek yet")
            return
        sync_player_gw(db, last_gw, refetch=args.refetch)
        if args.history:
            sync_history(db)
        entries = sync_league(db, last_gw)
        sync_entries(db, entries, last_gw)
        export(db, args.gw or last_gw)
        STATS["finished"] = True
    finally:
        # one line, whatever happened above: what the checks read (S3)
        STATS.setdefault("finished", False)
        print(STATS_PREFIX + json.dumps(STATS, separators=(",", ":"), sort_keys=True))
    db.close()
    if FAILED:
        # the export above holds what was fetched; the exit code says it is partial
        sys.exit(f"SYNC INCOMPLETE: {len(FAILED)} request(s) still failed after "
                 f"{RETRIES} retries each")


if __name__ == "__main__":
    main()
