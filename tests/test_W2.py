"""W2 (prereg/W2.md): the wiring of the sync columns (fetched_at_utc on
transfers, chips, standings and player_history; players.code; the seven
mislabelled standings rows flagged, never rewritten), bottomup_lambda as a
sixth source, and the CHIPS and LEAGUE report sections. Hermetic: in-memory
or temporary databases, a fake API; no network, no real data."""
import io
import os
import sqlite3
import sys
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fpl_sync as S        # noqa: E402
from test_fpl import _s2_element, _s2_event, UK_SUMMER   # noqa: E402

OLD_SCHEMA = """
CREATE TABLE players (id INTEGER PRIMARY KEY, web_name TEXT);
CREATE TABLE standings (entry_id INTEGER, event INTEGER, rank INTEGER, event_total INTEGER,
    total INTEGER, PRIMARY KEY (entry_id, event));
CREATE TABLE transfers (entry_id INTEGER, event INTEGER, time TEXT, player_in INTEGER,
    player_out INTEGER, cost_in INTEGER, cost_out INTEGER, PRIMARY KEY (entry_id, time, player_in, player_out));
CREATE TABLE chips (entry_id INTEGER, name TEXT, event INTEGER, time TEXT, PRIMARY KEY (entry_id, name, event));
CREATE TABLE player_history (player_id INTEGER, season TEXT, minutes INTEGER, total_points INTEGER,
    goals INTEGER, assists INTEGER, clean_sheets INTEGER, bonus INTEGER, expected_goals REAL,
    expected_assists REAL, starts INTEGER, PRIMARY KEY (player_id, season));
"""


def old_db():
    """A database as the sync made it before W2, with standings and entry_gw:
    entry 1's and entry 2's event-2 rows hold later totals (a GW3 snapshot),
    entry 3's event-2 row is its true GW2 total."""
    db = sqlite3.connect(":memory:")
    db.executescript(OLD_SCHEMA)
    db.executescript(S.SCHEMA)                       # every other table, as the sync makes them
    db.executemany("INSERT INTO standings VALUES (?,?,?,?,?)",
                   [(1, 2, 1, 60, 200), (2, 2, 2, 50, 180), (3, 2, 3, 40, 150),
                    (1, 3, 1, 60, 200), (2, 3, 2, 50, 180), (3, 3, 3, 44, 194)])
    db.executemany("INSERT INTO entry_gw (entry_id, event, points, total_points) VALUES (?,?,?,?)",
                   [(1, 2, 70, 140), (2, 2, 65, 130), (3, 2, 40, 150), (1, 3, 60, 200), (2, 3, 50, 180), (3, 3, 44, 194)])
    db.execute("INSERT INTO transfers VALUES (1, 2, '2026-08-20T10:00:00Z', 5, 6, 50, 55)")
    db.execute("INSERT INTO chips VALUES (1, 'wildcard', 2, '2026-08-20T10:00:00Z')")
    db.execute("INSERT INTO player_history VALUES (5, '2025/26', 900, 80, 3, 2, 4, 5, 2.5, 1.5, 10)")
    db.commit()
    return db


class SyncColumns(unittest.TestCase):
    def test_migration_flags_the_mislabelled_rows_and_keeps_every_row(self):
        db = old_db()
        before = db.execute("SELECT entry_id, event, rank, event_total, total FROM standings ORDER BY 1, 2").fetchall()
        buf = io.StringIO()
        with redirect_stdout(buf):
            S.migrate(db)
        text = buf.getvalue()
        for col in ("players.code", "transfers.fetched_at_utc", "chips.fetched_at_utc",
                    "player_history.fetched_at_utc", "standings.fetched_at_utc", "standings.label_error"):
            self.assertIn(f"+ {col}", text)
        flags = dict(((e, ev), f) for e, ev, f in db.execute("SELECT entry_id, event, label_error FROM standings"))
        self.assertEqual(flags, {(1, 2): 1, (2, 2): 1, (3, 2): 0, (1, 3): 0, (2, 3): 0, (3, 3): 0})   # only event 2, only off the chain
        self.assertIn("standings entry 1 event 2: total 200 is not the GW2 chain's 140 - label_error = 1, row kept", text)
        self.assertEqual(text.count("label_error = 1, row kept"), 2)
        after = db.execute("SELECT entry_id, event, rank, event_total, total FROM standings ORDER BY 1, 2").fetchall()
        self.assertEqual(after, before)                                                  # byte for byte, nothing removed
        for t in ("transfers", "chips", "player_history"):
            self.assertEqual(db.execute(f"SELECT fetched_at_utc FROM {t}").fetchall(), [(None,)])   # stored rows keep NULL
        db.execute("UPDATE standings SET label_error = 0 WHERE entry_id = 2")            # a later migrate never re-flags
        with redirect_stdout(io.StringIO()):
            S.migrate(db)
        self.assertEqual(db.execute("SELECT label_error FROM standings WHERE entry_id = 2 AND event = 2").fetchone(), (0,))

    def test_every_write_sets_the_fetch_time_and_the_code(self):
        db = sqlite3.connect(":memory:")
        db.executescript(S.SCHEMA)
        with redirect_stdout(io.StringIO()):
            S.migrate(db)
        answers = {
            "bootstrap-static/": {"teams": [], "elements": [_s2_element(1, code=111), _s2_element(2)],
                                  "events": [_s2_event(7, "2026-10-17T10:00:00Z", cur=True),
                                             _s2_event(8, "2026-10-23T17:30:00Z", nxt=True)]},
            f"leagues-classic/{S.LEAGUE_ID}/standings/": {"standings": {"results": [
                {"entry": 9, "entry_name": "Us", "player_name": "B", "rank": 1, "event_total": 50, "total": 400}]}},
            "entry/9/history/": {"chips": [{"name": "wildcard", "event": 6, "time": "2026-10-02T17:23:24Z"}]},
            "entry/9/transfers/": [{"event": 7, "time": "2026-10-15T10:00:00Z", "element_in": 1, "element_out": 2,
                                    "element_in_cost": 55, "element_out_cost": 50}],
            "element-summary/1/": {"history_past": [{"season_name": "2025/26", "minutes": 900, "total_points": 80,
                                                     "goals_scored": 3, "assists": 2, "clean_sheets": 4, "bonus": 5,
                                                     "expected_goals": "2.5", "expected_assists": "1.5", "starts": 10}]},
        }
        saved = S.get, S.london_tz
        S.get = lambda path: answers.get(path)
        S.london_tz = lambda: UK_SUMMER
        try:
            with redirect_stdout(io.StringIO()):
                S.sync_bootstrap(db)
                entries = S.sync_league(db, 7)
                S.sync_entries(db, entries, 0)
                S.sync_history(db, only_relevant=False)
        finally:
            S.get, S.london_tz = saved
        self.assertEqual(dict(db.execute("SELECT id, code FROM players")), {1: 111, 2: None})
        for t in ("standings", "chips", "transfers", "player_history"):
            got = db.execute(f"SELECT fetched_at_utc FROM {t}").fetchall()
            self.assertEqual(len(got), 1, t)
            self.assertRegex(got[0][0], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00$", t)
        self.assertEqual(db.execute("SELECT label_error FROM standings").fetchall(), [(0,)])

    def test_the_export_skips_a_flagged_row(self):
        db = sqlite3.connect(":memory:")
        db.executescript(S.SCHEMA)
        with redirect_stdout(io.StringIO()):
            S.migrate(db)
        db.executemany("INSERT INTO entries VALUES (?,?,?)", [(1, "A", "a"), (2, "B", "b")])
        db.executemany("INSERT INTO standings (entry_id, event, rank, event_total, total, label_error) VALUES (?,?,?,?,?,?)",
                       [(1, 7, 1, 60, 400, 0), (2, 7, 2, 50, 390, 1)])
        db.commit()
        import json, shutil, tempfile
        cwd, tmp = os.getcwd(), tempfile.mkdtemp()
        try:
            os.chdir(tmp)                                                                 # the export writes its file here
            with redirect_stdout(io.StringIO()):
                S.export(db, 7)
            with open(os.path.join(tmp, "fpl_export_gw7.json"), encoding="utf-8") as fh:
                d = json.load(fh)
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual([s["entry_id"] for s in d["standings"]], [1])                      # entry 2's flagged row is not read


if __name__ == "__main__":
    unittest.main()
