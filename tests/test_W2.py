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


class SixthSource(unittest.TestCase):
    """bottomup_lambda recorded as a sixth source (prereg/W2.md acceptance 2):
    the runner's copy gives tools/odds_lambda.py's numbers on the same
    snapshot and export; no snapshot before the deadline is a RECORD SKIP."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        sys.path.insert(0, os.path.join(HERE, "tools"))
        from tests.test_S5 import toy_2627
        toy_2627(self.tmp, post_deadline_export=False, export_gw=8)
        import gzip, json, sqlite3
        path = os.path.join(self.tmp, "exports", "fpl_export_gw8_2026-10-17.json.gz")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            self.d = json.load(fh)
        # the export's finished results, as the sync exports them from fpl.sqlite (fixtures_played)
        c = sqlite3.connect(os.path.join(self.tmp, "fpl.sqlite"))
        short = dict(c.execute("select id, short_name from teams"))
        self.d["fixtures_played"] = [{"event": ev, "home": short[h], "away": short[a], "h_goals": hs, "a_goals": as_,
                                      "kickoff_time": ko}
                                     for ev, ko, h, a, hs, as_, fin in c.execute(
                                         "select event, kickoff_time, team_h, team_a, team_h_score, team_a_score, finished "
                                         "from fixtures where finished = 1 and event <= 8")]
        c.close()
        import fpl_edge as E
        self.dl = E.event_deadline(self.d, 9)

    def snapshot(self, name, fetched):
        from tests.test_S5 import toy_snapshot, api_event
        import odds_lambda as OL
        _, _, fixtures, _, _ = OL.sqlite_tables(self.tmp)
        events = [api_event(f["home"], f["away"], f["kickoff"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                            [("b1", 2.0, 3.4, 3.8, 1.9, 1.9, False), ("b2", 2.2, 3.6, 3.4, 2.1, 1.7, True)])
                  for f in fixtures if f["event"] == 9][:2]                    # the third fixture has no odds: the fallback
        toy_snapshot(self.tmp, name, events, fetched_at=fetched)

    def test_the_numbers_are_the_tools(self):
        import fpl_lambda as L
        import odds_lambda as OL
        self.snapshot("odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        snap = OL.newest_snapshot(self.tmp, self.dl)
        self.assertEqual(L.newest_snapshot(self.tmp, self.dl)[0], snap[0])
        _, _, fixtures, _, _ = OL.sqlite_tables(self.tmp)
        tool_results = [(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in fixtures if f["finished"] and f["kickoff"] < self.dl]
        self.assertEqual(sorted(L.results_before(self.d, self.dl)), sorted(tool_results))   # the export's results are the database's
        late = dict(self.d["fixtures_played"][0], kickoff_time="2099-02-01T15:00:00Z")      # kicked off after the deadline
        d_late = dict(self.d, fixtures_played=self.d["fixtures_played"] + [late])
        self.assertEqual(L.results_before(d_late, self.dl), L.results_before(self.d, self.dl))   # never read
        book_t, book_r = OL.snapshot_book(snap[1])[0], L.snapshot_book(snap[1])[0]
        model_t, model_r = OL.fit_fallback(tool_results, self.dl), L.fit_fallback(L.results_before(self.d, self.dl), self.dl)
        want = OL.rebuild_2627(self.d, 9, book_t, model_t)
        got = L.rebuild_2627(self.d, 9, book_r, model_r)
        self.assertTrue(want)
        self.assertEqual(got, want)                                                   # byte-identical, sources included
        self.assertEqual({v[4] for v in want.values()} >= {"odds"}, True)
        self.assertTrue(any("fallback" in v[4] for v in want.values()))               # both paths exercised
        rows, note, skipped = L.bottomup_lambda(self.d, 9, self.dl, self.tmp)
        self.assertFalse(skipped)
        self.assertEqual(rows, [(pid, next(p["web_name"] for p in self.d["all_players"] if p["id"] == pid), round(v[1], 3))
                                for pid, v in want.items() if v[1]])
        self.assertIn("odds_2098-12-31T10-00-00Z.json.gz", note)

    def test_the_record_and_the_skip(self):
        import fpl_edge as E
        log = os.path.join(self.tmp, "projection_log.csv")
        with redirect_stdout(io.StringIO()):
            ok, n, why = E.record_status(self.d, 6, source="bottomup_lambda", path=log)
        self.assertEqual((ok, n), (E.RECORD_SKIP, 0))                                  # no odds/ yet
        self.assertIn("no odds snapshot before the GW9 deadline", why)
        self.snapshot("odds_2099-01-03T10-00-00Z.json.gz", "2099-01-03T10:00:00Z")     # after the deadline: never used
        with redirect_stdout(io.StringIO()):
            ok, n, why = E.record_status(self.d, 6, source="bottomup_lambda", path=log)
        self.assertEqual(ok, E.RECORD_SKIP)
        self.snapshot("odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        with redirect_stdout(io.StringIO()):
            ok, n, why = E.record_status(self.d, 6, source="bottomup_lambda", path=log)
        self.assertIs(ok, True); self.assertGreater(n, 0)
        every = E.read_log(log)
        rows = [r for r in every if r["source"] == "bottomup_lambda"]
        self.assertEqual(len([r for r in every if r["source"] == "bottomup"]), 5)       # the toy's earlier rows untouched
        self.assertEqual({r["event"] for r in rows}, {"9"})
        import fpl_lambda as L
        want, _, _ = L.bottomup_lambda(self.d, 9, self.dl, self.tmp)
        self.assertEqual([(int(r["player_id"]), float(r["predicted"])) for r in rows], [(p, v) for p, _, v in want])

    def test_check_29_learns_the_sixth_source(self):
        import checks as C
        self.assertEqual(C.SOURCES[-1], "bottomup_lambda")
        nl = chr(10)
        base = "".join(f"RECORD OK {s} 5" + nl for s in C.SOURCES[:-1])
        head, tail = "record summary:" + nl, "archiving ..." + nl
        ok = head + base + "RECORD OK bottomup_lambda 5" + nl + tail
        self.assertEqual(C.c29(C.Ctx(run_log=ok))[0], C.OK)
        skip = head + base + "RECORD SKIP bottomup_lambda no odds snapshot before the GW9 deadline" + nl + tail
        self.assertEqual(C.c29(C.Ctx(run_log=skip)),
                         (C.WARN, "bottomup_lambda skipped: no odds snapshot before the GW9 deadline; the other 5 recorded"))
        fail = head + base + "RECORD FAIL bottomup_lambda boom" + nl + tail
        self.assertEqual(C.c29(C.Ctx(run_log=fail))[0], C.FAIL)
        missing = head + base + tail
        self.assertEqual(C.c29(C.Ctx(run_log=missing)), (C.FAIL, "bottomup_lambda missing"))

    def test_the_record_never_imports_tools_or_opens_the_database(self):
        import ast
        tree = ast.parse(open(os.path.join(HERE, "fpl_lambda.py"), encoding="utf-8").read())
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertNotIn("sqlite3", names)
        self.assertFalse(names & {"odds_lambda", "tools", "backtest", "chips", "league"})


class ReportSections(unittest.TestCase):
    """The CHIPS and LEAGUE sections (prereg/W2.md acceptance 1): byte-identical
    to tools/chips.py and tools/league.py on the same data folder; a missing
    input is one SKIPPED line; check 31 WARNs and never fails the night."""

    def tools(self):
        sys.path.insert(0, os.path.join(HERE, "tools"))
        import chips as CHt
        import league as LGt
        return CHt, LGt

    def test_byte_identical_to_the_tools(self):
        import shutil, tempfile
        from datetime import datetime, timezone
        import fpl_chips, fpl_league, fpl_sections as FS
        CHt, LGt = self.tools()
        from tests.test_S4 import toy_data
        from tests.test_S7 import toy_export
        from tests.test_S9 import toy_league
        a, b = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_data(a); toy_export(a)
            ta, tb = [], []
            CHt.live(a, out=ta.append); fpl_chips.live(a, out=tb.append)
            self.assertGreater(len(ta), 10)
            self.assertEqual(tb, ta)                                                       # same data, seed and resamples
            toy_league(b)
            today = datetime(2026, 9, 16, tzinfo=timezone.utc)
            la, lb = [], []
            LGt.report(b, out=la.append, today=today); fpl_league.report(b, out=lb.append, today=today)
            self.assertGreater(len(la), 10)
            self.assertEqual(lb, la)
            res = dict((t, (lines, st)) for t, lines, st in FS.sections(b, now=today))
            self.assertEqual(res["LEAGUE"][0], la)
            self.assertEqual(res["LEAGUE"][1], f"LEAGUE OK {len(la)} lines")
            self.assertTrue(res["CHIPS"][1].startswith("CHIPS SKIPPED: "))                # the league toy has no chip inputs
        finally:
            shutil.rmtree(a, ignore_errors=True); shutil.rmtree(b, ignore_errors=True)

    def test_a_missing_input_is_one_skipped_line_and_the_report_is_appended(self):
        import shutil, tempfile
        import fpl_sections as FS
        tmp = tempfile.mkdtemp()
        try:
            report = os.path.join(tmp, "fpl_x.txt")
            with open(report, "w", encoding="utf-8", newline="") as fh:
                fh.write("THE REPORT\n")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = FS.main(["--report", report, "--data", tmp])
            self.assertEqual(rc, 0)
            printed = buf.getvalue().splitlines()
            self.assertEqual([l.split(":")[0] for l in printed], ["CHIPS SKIPPED", "LEAGUE SKIPPED"])
            with open(report, encoding="utf-8", newline="") as fh:
                text = fh.read()
            self.assertTrue(text.startswith("THE REPORT\n"))
            self.assertIn("CHIPS (W2: S7 chip calculator)", text); self.assertIn("LEAGUE (W2: S9 league)", text)
            self.assertEqual(sum(1 for l in text.splitlines() if " SKIPPED: " in l), 2)
            self.assertNotIn(chr(13), text)
            self.assertFalse([f for f in os.listdir(tmp) if "sqlite" in f])               # read-only: no database created
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_check_31_warns_and_never_fails(self):
        import checks as C
        nl = chr(10)
        ok = "adding the report sections ..." + nl + "CHIPS OK 37 lines" + nl + "LEAGUE OK 69 lines" + nl
        self.assertEqual(C.c31(C.Ctx(run_log=ok)), (C.OK, "CHIPS 37 lines, LEAGUE 69 lines"))
        skip = ok.replace("LEAGUE OK 69 lines", "LEAGUE SKIPPED: no fpl.sqlite")
        self.assertEqual(C.c31(C.Ctx(run_log=skip)), (C.WARN, "LEAGUE SKIPPED: no fpl.sqlite"))
        self.assertEqual(C.c31(C.Ctx(run_log="nothing" + nl))[0], C.WARN)                  # no lines: a WARN
        crash = "SECTIONS FAILED  fpl_sections.py exited 1 - the report has no CHIPS or LEAGUE section tonight" + nl
        self.assertEqual(C.c31(C.Ctx(run_log=crash)), (C.WARN, crash.strip()))
        self.assertEqual((C.NAMES[31], C.SEVERITY[31], len(C.CHECKS)), ("report sections", C.WARN, 31))

    def test_a_crash_never_reddens_the_night(self):
        import shutil, tempfile
        import fpl_nightly as N
        from test_fpl import NIGHTLY_EDGE_STUB
        tmp = tempfile.mkdtemp()
        try:
            stubs = {"test_fpl.py": "import unittest" + chr(10) * 3 + "class Stub(unittest.TestCase):" + chr(10)
                                    + "    def test_stub(self):" + chr(10) + "        pass" + chr(10),
                     "fpl_sync.py": "print('sync ran')" + chr(10),
                     "checks.py": "print('CHECKS stub')" + chr(10),
                     "fpl_odds.py": "print('ODDS SKIPPED stub')" + chr(10),
                     "fpl_edge.py": NIGHTLY_EDGE_STUB, "MODE": "clean",
                     "fpl_sections.py": "raise SystemExit(3)" + chr(10),
                     "fpl_export_gw3.json": "{}"}
            for name, body in stubs.items():
                with open(os.path.join(tmp, name), "w", encoding="utf-8", newline="") as fh:
                    fh.write(body)
            os.makedirs(os.path.join(tmp, "reports"))
            with open(os.path.join(tmp, "reports", "fpl_2026-10-05.txt"), "w", encoding="utf-8", newline="") as fh:
                fh.write("THE REPORT" + chr(10))                                          # the stub edge writes none
            log = []
            code = N.nightly(root=tmp, stamp="2026-10-05", echo=log.append)
            text = chr(10).join(log)
            self.assertIn("SECTIONS FAILED  fpl_sections.py exited 3", text)
            self.assertNotIn("sections", " ".join(l for l in log if l.startswith("FINISHED WITH ERRORS")))
            import checks as C
            self.assertEqual(C.c31(C.Ctx(run_log=text))[0], C.WARN)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
