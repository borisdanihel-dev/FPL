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
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone

LEAGUE_ID = 455565          # VAR Wars: Revenge of the Ref
MY_ENTRY = 3073318          # 1. FC Kiripolcz
DB_PATH = "fpl.sqlite"
BASE = "https://fantasy.premierleague.com/api"
PAUSE = 0.4                 # seconds between requests, be polite to the API

# ----------------------------------------------------------------------------
# HTTP
# ----------------------------------------------------------------------------

def get(path):
    url = f"{BASE}/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 fpl_sync"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            time.sleep(PAUSE)
            return data
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                print(f"  ! failed {url}: {e}")
                return None
            time.sleep(2)

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
    influence REAL, creativity REAL, threat REAL);

CREATE TABLE IF NOT EXISTS player_history (
    player_id INTEGER, season TEXT, minutes INTEGER, total_points INTEGER,
    goals INTEGER, assists INTEGER, clean_sheets INTEGER, bonus INTEGER,
    expected_goals REAL, expected_assists REAL, starts INTEGER,
    PRIMARY KEY (player_id, season));

CREATE TABLE IF NOT EXISTS price_history (
    player_id INTEGER, date TEXT, now_cost INTEGER,
    PRIMARY KEY (player_id, date));

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY, name TEXT, deadline_time TEXT, finished INTEGER,
    average_score INTEGER, highest_score INTEGER, most_captained INTEGER,
    data_checked INTEGER);

CREATE TABLE IF NOT EXISTS fixtures (
    id INTEGER PRIMARY KEY, event INTEGER, kickoff_time TEXT,
    team_h INTEGER, team_a INTEGER, team_h_difficulty INTEGER,
    team_a_difficulty INTEGER, team_h_score INTEGER, team_a_score INTEGER,
    finished INTEGER);

CREATE TABLE IF NOT EXISTS player_gw (
    player_id INTEGER, event INTEGER, minutes INTEGER, total_points INTEGER,
    goals INTEGER, assists INTEGER, clean_sheets INTEGER, goals_conceded INTEGER,
    bonus INTEGER, bps INTEGER, saves INTEGER, yellow INTEGER, red INTEGER,
    expected_goals REAL, expected_assists REAL, defensive_contribution INTEGER,
    starts INTEGER,
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
"""

MIGRATIONS = {
    "players": ["starts INTEGER", "pens_order INTEGER", "corners_order INTEGER",
                "fk_order INTEGER", "xgc REAL", "tin_event INTEGER",
                "tout_event INTEGER", "form REAL", "ppg REAL",
                "influence REAL", "creativity REAL", "threat REAL"],
    "teams": ["att_h INTEGER", "att_a INTEGER", "def_h INTEGER", "def_a INTEGER"],
    "player_gw": ["starts INTEGER"],
    "events": ["data_checked INTEGER"],
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
    today = datetime.now(timezone.utc).date().isoformat()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    db.executemany("INSERT OR REPLACE INTO teams VALUES (?,?,?,?,?,?,?,?)",
                   [(t["id"], t["name"], t["short_name"], t["strength"],
                     t.get("strength_attack_home"), t.get("strength_attack_away"),
                     t.get("strength_defence_home"), t.get("strength_defence_away"))
                    for t in bs["teams"]])

    rows = []
    for p in bs["elements"]:
        rows.append((p["id"], p["web_name"], p["first_name"], p["second_name"],
                     p["team"], p["element_type"], p["now_cost"], p["cost_change_start"],
                     float(p["selected_by_percent"]), p["total_points"], p["minutes"],
                     p["goals_scored"], p["assists"], p["clean_sheets"], p["bonus"],
                     float(p.get("expected_goals") or 0), float(p.get("expected_assists") or 0),
                     float(p.get("ict_index") or 0), p["status"],
                     p.get("chance_of_playing_next_round"), p.get("news", ""), now,
                     p.get("starts") or 0,
                     p.get("penalties_order"),
                     p.get("corners_and_indirect_freekicks_order"),
                     p.get("direct_freekicks_order"),
                     float(p.get("expected_goals_conceded") or 0),
                     p.get("transfers_in_event") or 0,
                     p.get("transfers_out_event") or 0,
                     float(p.get("form") or 0),
                     float(p.get("points_per_game") or 0),
                     float(p.get("influence") or 0),
                     float(p.get("creativity") or 0),
                     float(p.get("threat") or 0)))
        db.execute("INSERT OR REPLACE INTO price_history VALUES (?,?,?)",
                   (p["id"], today, p["now_cost"]))
    db.executemany("INSERT OR REPLACE INTO players VALUES (%s)" % ",".join("?" * 34), rows)

    # data_checked = points and bonus are final. `finished` only means the
    # matches ended; grading keys on data_checked.
    db.executemany("INSERT OR REPLACE INTO events VALUES (?,?,?,?,?,?,?,?)",
                   [(e["id"], e["name"], e["deadline_time"], int(e["finished"]),
                     e.get("average_entry_score"), e.get("highest_score"),
                     e.get("most_captained"), int(bool(e.get("data_checked"))))
                    for e in bs["events"]])
    db.commit()
    # latest gameweek that has started (finished OR currently in progress)
    started = [e["id"] for e in bs["events"] if e["finished"] or e.get("is_current")]
    return max(started) if started else 0


def sync_fixtures(db):
    print("fixtures ...")
    fx = get("fixtures/") or []
    db.executemany("INSERT OR REPLACE INTO fixtures VALUES (?,?,?,?,?,?,?,?,?,?)",
                   [(f["id"], f.get("event"), f.get("kickoff_time"), f["team_h"], f["team_a"],
                     f["team_h_difficulty"], f["team_a_difficulty"],
                     f.get("team_h_score"), f.get("team_a_score"), int(f["finished"]))
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
        for el in live["elements"]:
            s = el["stats"]
            rows.append((el["id"], gw, s["minutes"], s["total_points"], s["goals_scored"],
                         s["assists"], s["clean_sheets"], s["goals_conceded"], s["bonus"],
                         s["bps"], s["saves"], s["yellow_cards"], s["red_cards"],
                         float(s.get("expected_goals") or 0), float(s.get("expected_assists") or 0),
                         s.get("defensive_contribution", 0),
                         s.get("starts", 0)))
        db.executemany("INSERT OR REPLACE INTO player_gw VALUES (%s)" % ",".join("?" * 17), rows)
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
            db.execute("INSERT OR REPLACE INTO entry_gw VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (eid, gw, h["points"], h["total_points"], h["overall_rank"], h["bank"],
                        h["value"], h["event_transfers"], h["event_transfers_cost"],
                        h["points_on_bench"], pk.get("active_chip")))
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
        SELECT e.id AS entry_id, e.entry_name, p.position AS slot, pl.web_name, t.short_name AS team,
               pl.position AS pos, pl.now_cost/10.0 AS price, p.multiplier,
               p.is_captain, p.is_vice, g.total_points AS gw_points, g.minutes
        FROM picks p JOIN entries e ON e.id=p.entry_id
        JOIN players pl ON pl.id=p.player_id JOIN teams t ON t.id=pl.team_id
        LEFT JOIN player_gw g ON g.player_id=p.player_id AND g.event=p.event
        WHERE p.event=? ORDER BY e.entry_name, p.position""", (gw,))

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
               (pl.tin_event - pl.tout_event) AS net_transfers,
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
        WHERE g.event BETWEEN ?-5 AND ? AND g.minutes>0
        -- one row per player per gameweek. player_gw holds a GW TOTAL, so the
        -- fixtures join must not fan a double out into two copies of it, and
        -- the per-match columns stay NULL when there is more than one match.
        GROUP BY g.player_id, g.event
        ORDER BY g.event, g.total_points DESC""", (gw, gw))

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

    # what grading needs to know before it trusts a gameweek's points
    out["events"] = q(db, """
        SELECT id AS event, finished, data_checked FROM events
        WHERE id<=? ORDER BY id""", (gw,))

    out["fixtures_status"] = q(db, """
        SELECT f.event, th.short_name AS home, ta.short_name AS away,
               f.kickoff_time, f.finished
        FROM fixtures f JOIN teams th ON th.id=f.team_h JOIN teams ta ON ta.id=f.team_a
        WHERE f.event BETWEEN ?-5 AND ? ORDER BY f.event, f.kickoff_time""", (gw, gw))

    out["price_changes_7d"] = q(db, """
        SELECT pl.web_name, t.short_name AS team, a.now_cost/10.0 AS price_now,
               b.now_cost/10.0 AS price_7d_ago, (a.now_cost-b.now_cost)/10.0 AS change
        FROM price_history a JOIN price_history b ON b.player_id=a.player_id
        JOIN players pl ON pl.id=a.player_id JOIN teams t ON t.id=pl.team_id
        WHERE a.date=(SELECT MAX(date) FROM price_history)
          AND b.date=(SELECT MIN(date) FROM price_history WHERE date>=date('now','-7 day'))
          AND a.now_cost<>b.now_cost ORDER BY change DESC""")

    fname = f"fpl_export_gw{gw}.json"
    with open(fname, "w", encoding="utf-8") as f:
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
    db.close()


if __name__ == "__main__":
    main()
