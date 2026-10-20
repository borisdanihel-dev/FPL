"""S2b (RULING S2b, 19 Oct): the final re-fetch until data_checked.

events.data_checked_seen_utc is set the first time a sync sees data_checked = 1
and never changed after. A player_gw, entry_gw or picks row is final only when
its fetched_at_utc is later than that time; anything else - provisional rows,
rows with no fetch time, gameweeks whose data_checked was never seen - is
fetched again. Check 22 reconciles every locked-down gameweek and lists each
mismatch.
"""

import io
import os
import sqlite3
import sys
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import checks as C          # noqa: E402
import fpl_sync as S        # noqa: E402
from test_fpl import _s2_event, _s2_sync_ns   # noqa: E402
from tests import test_S3 as T3               # noqa: E402

T0 = "2026-10-19T21:40:05+00:00"      # the night the sync first sees data_checked
T1 = "2026-10-19T21:40:09+00:00"      # the same night, a few seconds later
T2 = "2026-10-20T21:40:05+00:00"      # the next night
EARLY = "2026-10-12T21:40:00+00:00"   # a fetch before data_checked was seen

DEADLINES = {g: (datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc) + timedelta(days=7 * (g - 1)))
             .strftime("%Y-%m-%dT%H:%M:%SZ") for g in range(1, 9)}


def _ns(now):
    return _s2_sync_ns(now)


def _db(ns):
    db = sqlite3.connect(":memory:")
    db.executescript(ns["SCHEMA"])
    with redirect_stdout(io.StringIO()):
        ns["migrate"](db)
    return db


def _boot(ns, db, checked, finished=None, last=7):
    """One bootstrap: events 1..8, data_checked for the ids in `checked`."""
    finished = checked if finished is None else finished
    evs = [_s2_event(g, DEADLINES[g], cur=g == last, nxt=g == last + 1, fin=g in finished,
                     chk=g in checked) for g in range(1, 9)]
    ns["get"] = lambda path: {"teams": [], "elements": [], "events": evs}
    with redirect_stdout(io.StringIO()):
        ns["sync_bootstrap"](db)


def _seen(db):
    return dict(db.execute("SELECT id, data_checked_seen_utc FROM events ORDER BY id").fetchall())


STATS = {"minutes": 90, "total_points": 6, "goals_scored": 0, "assists": 1, "clean_sheets": 0,
         "goals_conceded": 1, "bonus": 1, "bps": 22, "saves": 0, "yellow_cards": 0,
         "red_cards": 0, "expected_goals": "0.2", "expected_assists": "0.3",
         "defensive_contribution": 4, "starts": 1}


def _live(n=320, points=6):
    return {"elements": [{"id": i, "stats": dict(STATS, total_points=points)} for i in range(1, n + 1)]}


def _store_player_gw(db, gw, fetched, n=320, points=5):
    db.executemany("INSERT OR REPLACE INTO player_gw (player_id, event, minutes, total_points, "
                   "fetched_at_utc, ruleset) VALUES (?,?,90,?,?,'2026-27')",
                   [(i, gw, points, fetched) for i in range(1, n + 1)])


def _sync_gw(ns, db, last_gw, refetch=False, live=None):
    calls = []

    def get(path):
        calls.append(path)
        return live or _live()
    ns["get"] = get
    with redirect_stdout(io.StringIO()):
        ns["sync_player_gw"](db, last_gw, refetch=refetch)
    return calls


class SeenTime(unittest.TestCase):
    """Point 1: data_checked_seen_utc - first sight, never changed after."""

    def test_the_column_is_added_and_stored_rows_keep_null(self):
        db = sqlite3.connect(":memory:")
        db.executescript("""
            CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT, deadline_time TEXT,
                finished INTEGER, average_score INTEGER, highest_score INTEGER,
                most_captained INTEGER, data_checked INTEGER);
            CREATE TABLE picks (entry_id INTEGER, event INTEGER, player_id INTEGER,
                position INTEGER, multiplier INTEGER, is_captain INTEGER, is_vice INTEGER,
                PRIMARY KEY (entry_id, event, player_id));
            INSERT INTO events VALUES (3, 'GW3', '2026-09-12T10:00:00Z', 1, 50, 90, 7, 1);
            INSERT INTO picks VALUES (99, 3, 7, 1, 2, 1, 0);""")
        ns = _ns(T0)
        db.executescript(ns["SCHEMA"])
        out = io.StringIO()
        with redirect_stdout(out):
            ns["migrate"](db)
        self.assertIn("+ events.data_checked_seen_utc", out.getvalue())
        self.assertIn("+ picks.fetched_at_utc", out.getvalue())
        self.assertEqual(db.execute("SELECT data_checked, data_checked_seen_utc FROM events").fetchall(),
                         [(1, None)])
        self.assertEqual(db.execute("SELECT fetched_at_utc FROM picks").fetchall(), [(None,)])

    def test_set_at_first_sight_and_never_changed(self):
        db = _db(_ns(T0))
        _boot(_ns(T0), db, checked={1, 2, 3, 4, 5, 6})
        seen = _seen(db)
        self.assertEqual({g: seen[g] for g in range(1, 7)}, {g: T0 for g in range(1, 7)})
        self.assertIsNone(seen[7])
        _boot(_ns(T2), db, checked={1, 2, 3, 4, 5, 6, 7})         # GW7 locks down the next night
        seen = _seen(db)
        self.assertEqual(seen[6], T0, "a later sync must never move the first sight")
        self.assertEqual(seen[7], T2)
        _boot(_ns("2026-10-21T21:40:05+00:00"), db, checked={1, 2, 3, 4, 5, 6})   # GW7 reads 0 again
        self.assertEqual(_seen(db)[7], T2)
        self.assertEqual(db.execute("SELECT data_checked FROM events WHERE id = 7").fetchone(), (0,))

    def test_the_nightly_rewrite_keeps_every_other_column_current(self):
        db = _db(_ns(T0))
        _boot(_ns(T0), db, checked={1}, finished={1})
        _boot(_ns(T2), db, checked={1, 2}, finished={1, 2, 3})
        self.assertEqual(db.execute("SELECT id, finished, data_checked FROM events WHERE id <= 4 "
                                    "ORDER BY id").fetchall(),
                         [(1, 1, 1), (2, 1, 1), (3, 1, 0), (4, 0, 0)])
        self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone(), (8,))


class PlayerGwFinality(unittest.TestCase):
    """Point 1 for player_gw: re-fetched until every row is later than the
    first sight of data_checked."""

    def setUp(self):
        self.db = _db(_ns(T0))
        _boot(_ns(T0), self.db, checked={1, 2, 3, 4, 5, 6})

    def test_a_row_fetched_before_data_checked_is_fetched_again(self):
        for g in range(1, 7):
            _store_player_gw(self.db, g, T1)           # final
        _store_player_gw(self.db, 4, EARLY)            # GW4 provisional
        calls = _sync_gw(_ns(T2), self.db, 6)
        self.assertEqual(calls, ["event/4/live/"])
        self.assertEqual(self.db.execute("SELECT DISTINCT total_points, fetched_at_utc FROM player_gw "
                                         "WHERE event = 4").fetchall(), [(6, T2)])

    def test_one_provisional_row_is_enough(self):
        for g in range(1, 7):
            _store_player_gw(self.db, g, T1)
        self.db.execute("UPDATE player_gw SET fetched_at_utc = ? WHERE event = 5 AND player_id = 77", (EARLY,))
        self.assertEqual(_sync_gw(_ns(T2), self.db, 6), ["event/5/live/"])

    def test_a_null_fetch_time_is_never_final(self):
        for g in range(1, 7):
            _store_player_gw(self.db, g, T1)
        self.db.execute("UPDATE player_gw SET fetched_at_utc = NULL WHERE event = 2")
        self.assertEqual(_sync_gw(_ns(T2), self.db, 6), ["event/2/live/"])

    def test_the_same_second_is_not_later(self):
        for g in range(1, 7):
            _store_player_gw(self.db, g, T1)
        _store_player_gw(self.db, 3, T0)
        self.assertEqual(_sync_gw(_ns(T2), self.db, 6), ["event/3/live/"])

    def test_a_finished_gameweek_never_seen_data_checked_is_fetched_again(self):
        """The finding: finished = 1 while data_checked = 0 stopped the re-fetch."""
        for g in range(1, 8):
            _store_player_gw(self.db, g, T1)
        _boot(_ns(T1), self.db, checked={1, 2, 3, 4, 5, 6}, finished={1, 2, 3, 4, 5, 6, 7})
        self.assertEqual(_sync_gw(_ns(T2), self.db, 7), ["event/7/live/"])

    def test_final_gameweeks_are_not_fetched_again(self):
        for g in range(1, 7):
            _store_player_gw(self.db, g, T1)
        self.assertEqual(_sync_gw(_ns(T2), self.db, 6), [])

    def test_the_old_guards_stay(self):
        for g in range(1, 7):
            _store_player_gw(self.db, g, T1)
        self.assertEqual(_sync_gw(_ns(T2), self.db, 6, refetch=True),
                         [f"event/{g}/live/" for g in range(1, 7)])
        self.db.execute("DELETE FROM player_gw WHERE event = 6 AND player_id > 300")
        self.assertEqual(_sync_gw(_ns(T2), self.db, 6)[-1:], ["event/6/live/"])


HIST = {"points": 61, "total_points": 400, "overall_rank": 1, "bank": 5, "value": 1000,
        "event_transfers": 0, "event_transfers_cost": 0, "points_on_bench": 3}
PICKS = [{"element": i, "position": i, "multiplier": 1 if i <= 11 else 0,
          "is_captain": i == 1, "is_vice_captain": i == 2} for i in range(1, 16)]


def _store_entry(db, eid, gw, fetched, picks_fetched="same", points=50):
    picks_fetched = fetched if picks_fetched == "same" else picks_fetched
    db.execute("INSERT OR REPLACE INTO entry_gw (entry_id, event, points, fetched_at_utc) "
               "VALUES (?,?,?,?)", (eid, gw, points, fetched))
    db.executemany("INSERT OR REPLACE INTO picks (entry_id, event, player_id, position, multiplier, "
                   "is_captain, is_vice, fetched_at_utc) VALUES (?,?,?,?,1,0,0,?)",
                   [(eid, gw, i, i, picks_fetched) for i in range(1, 16)])


def _sync_entries(ns, db, eids, last_gw, subs=()):
    calls = []

    def get(path):
        calls.append(path)
        if "history" in path:
            return {"chips": []}
        if "transfers" in path:
            return []
        return {"entry_history": HIST, "active_chip": None, "picks": PICKS,
                "automatic_subs": [{"element_in": a, "element_out": b} for a, b in subs]}
    ns["get"] = get
    with redirect_stdout(io.StringIO()):
        ns["sync_entries"](db, eids, last_gw)
    return [c for c in calls if c.endswith("/picks/")]


class EntryFinality(unittest.TestCase):
    """Point 1 for entry_gw and picks."""

    def setUp(self):
        self.db = _db(_ns(T0))
        _boot(_ns(T0), self.db, checked={1, 2, 3, 4, 5, 6})

    def test_provisional_entry_rows_are_fetched_again_and_replaced(self):
        for g in range(1, 7):
            _store_entry(self.db, 99, g, T1)
        _store_entry(self.db, 99, 3, EARLY, points=40)
        self.assertEqual(_sync_entries(_ns(T2), self.db, [99], 6), ["entry/99/event/3/picks/"])
        self.assertEqual(self.db.execute("SELECT points, fetched_at_utc FROM entry_gw WHERE event = 3")
                         .fetchall(), [(61, T2)])
        self.assertEqual(self.db.execute("SELECT DISTINCT fetched_at_utc FROM picks WHERE event = 3")
                         .fetchall(), [(T2,)])

    def test_a_null_fetch_time_on_either_table_is_never_final(self):
        for g in range(1, 7):
            _store_entry(self.db, 99, g, T1)
        _store_entry(self.db, 99, 2, None)                       # entry_gw from before S2
        _store_entry(self.db, 99, 5, T1, picks_fetched=None)     # picks from before S2b
        self.assertEqual(_sync_entries(_ns(T2), self.db, [99], 6),
                         ["entry/99/event/2/picks/", "entry/99/event/5/picks/"])

    def test_final_entries_are_not_fetched_again_and_each_entry_stands_alone(self):
        for g in range(1, 7):
            _store_entry(self.db, 99, g, T1)
            _store_entry(self.db, 98, g, T1)
        _store_entry(self.db, 98, 6, EARLY)
        self.assertEqual(_sync_entries(_ns(T2), self.db, [99, 98], 6), ["entry/98/event/6/picks/"])

    def test_an_entry_never_stored_is_fetched(self):
        for g in range(1, 7):
            _store_entry(self.db, 99, g, T1)
        self.assertEqual(_sync_entries(_ns(T2), self.db, [99, 97], 6),
                         [f"entry/97/event/{g}/picks/" for g in range(1, 7)])

    def test_a_finished_gameweek_never_seen_data_checked_is_fetched_again(self):
        for g in range(1, 8):
            _store_entry(self.db, 99, g, T1)
        _boot(_ns(T1), self.db, checked={1, 2, 3, 4, 5, 6}, finished={1, 2, 3, 4, 5, 6, 7})
        self.assertEqual(_sync_entries(_ns(T2), self.db, [99], 7), ["entry/99/event/7/picks/"])


class FirstRun(unittest.TestCase):
    """Point 1, last sentence: on today's data the first run re-fetches GW1-6
    once and the run after it none; the calls are counted in SYNC STATS."""

    def test_once_then_never(self):
        db = _db(_ns(EARLY))
        for g in range(1, 7):
            _store_player_gw(db, g, EARLY)
            for eid in (91, 92, 93):
                _store_entry(db, eid, g, EARLY if g > 2 else None, picks_fetched=None)
        # tonight: the sync sees data_checked for GW1-6 at bootstrap (T0) and
        # fetches the gameweeks a few seconds later (T1)
        _boot(_ns(T0), db, checked={1, 2, 3, 4, 5, 6}, last=6)
        first = _sync_gw(_ns(T1), db, 6) + _sync_entries(_ns(T1), db, [91, 92, 93], 6)
        self.assertEqual(len(first), 6 + 6 * 3)
        _boot(_ns(T2), db, checked={1, 2, 3, 4, 5, 6}, last=6)
        second = _sync_gw(_ns(T2), db, 6) + _sync_entries(_ns(T2), db, [91, 92, 93], 6)
        self.assertEqual(second, [])

    def test_the_calls_are_counted(self):
        db = _db(_ns(T0))
        S_STATS = {"calls": []}
        ns = _ns(T1)
        ns["STATS"] = S_STATS
        _boot(_ns(T0), db, checked={1, 2}, last=2)

        class Reply(io.BytesIO):
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        import json
        ns["_urlopen"] = lambda req, timeout=30: Reply(json.dumps(_live(3)).encode())
        ns["_sleep"] = lambda s: None
        with redirect_stdout(io.StringIO()):
            ns["sync_player_gw"](db, 2)
        self.assertEqual([c[0] for c in S_STATS["calls"]], ["event/1/live/", "event/2/live/"])


def _ctx(db, export, now):
    return C.Ctx(db=db, export=export, now=now)


class EveryLockedGameweek(unittest.TestCase):
    """Point 2: check 22 over every locked-down gameweek, each mismatch listed."""

    def _world(self, fpl_points, locked=(5, 6), last=7):
        db = T3._db()
        export = {"events": [], "fixtures_status": []}
        for g in range(1, last + 1):
            settled = g in locked
            db.execute("INSERT INTO events (id, name, deadline_time, finished, data_checked) "
                       "VALUES (?,?,?,?,?)", (g, f"GW{g}", T3.iso(T3.deadline(g)), int(settled), int(settled)))
            export["events"].append({"event": g, "finished": int(settled), "data_checked": int(settled),
                                     "deadline_time": T3.iso(T3.deadline(g))})
            export["fixtures_status"].append({"event": g, "home": "T1", "away": "T2",
                                              "kickoff_time": T3.iso(T3.deadline(g) + timedelta(hours=2)),
                                              "finished": int(settled), "started": 1})
        for (eid, g), fpl in fpl_points.items():
            for p in range(1, 16):
                db.execute("INSERT INTO picks (entry_id, event, player_id, position, multiplier, "
                           "is_captain, is_vice, fetched_at_utc) VALUES (?,?,?,?,?,?,?,'x')",
                           (eid, g, p, p, (2 if p == 10 else 1) if p <= 11 else 0, int(p == 10), int(p == 11)))
                db.execute("INSERT OR IGNORE INTO player_gw (player_id, event, minutes, total_points) "
                           "VALUES (?,?,90,?)", (p, g, p))
            db.execute("INSERT INTO entry_gw (entry_id, event, points, fetched_at_utc) VALUES (?,?,?,'x')",
                       (eid, g, fpl))
        return _ctx(db, export, T3.deadline(last) + timedelta(days=1))

    RIGHT = sum(range(1, 12)) + 10

    def test_an_earlier_gameweek_is_reconciled_too(self):
        x = self._world({(1, 5): self.RIGHT - 3, (1, 6): self.RIGHT})
        level, detail = C.c22(x)
        self.assertEqual(level, C.WARN, detail)
        self.assertIn(f"GW5 1: FPL {self.RIGHT - 3}, computed {self.RIGHT}", detail)

    def test_every_mismatch_is_listed(self):
        pts = {(e, g): self.RIGHT - e for e in range(1, 5) for g in (5, 6)}       # 8 mismatches
        level, detail = C.c22(self._world(pts))
        self.assertEqual(level, C.WARN)
        for e in range(1, 5):
            for g in (5, 6):
                self.assertIn(f"GW{g} {e}: FPL {self.RIGHT - e}, computed {self.RIGHT}", detail)
        self.assertNotIn("more)", detail)

    def test_all_equal_is_ok_and_names_the_gameweeks(self):
        level, detail = C.c22(self._world({(1, 5): self.RIGHT, (1, 6): self.RIGHT, (2, 6): self.RIGHT}))
        self.assertEqual(level, C.OK, detail)
        self.assertIn("3 entry-gameweeks", detail)
        self.assertIn("GW5-GW6", detail)

    def test_the_gameweek_in_progress_stays_silent(self):
        x = self._world({(1, 6): self.RIGHT, (1, 7): self.RIGHT - 9}, locked=(6,))
        level, detail = C.c22(x)
        self.assertEqual(level, C.OK, detail)
        self.assertIn("GW7 not locked down: silent mid-gameweek", detail)


if __name__ == "__main__":
    unittest.main(verbosity=2)
