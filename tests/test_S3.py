"""S3 (BUILD_PLAN.md Step 3, D3; ruling S3) and RULING FAST-TRACK items 1 and 5.

Every one of the 27 checks with a test that plants its failure; the status
line on both sides of the 25 Oct clock change; the 03:17 backup run's due rule
(it writes nothing when the status file exists); both paths of the failure
issue; the dry run's status file; the retry policy of check 2; the pinned
actions; the nightly imports nothing under tools/ or analysis/; discovery
finds tests/.
"""

import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone, tzinfo

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import checks as C          # noqa: E402
import fpl_alert as A       # noqa: E402
import fpl_nightly as N     # noqa: E402
import fpl_publish as PUB   # noqa: E402
import fpl_sync as S        # noqa: E402

UTC = timezone.utc
NOW = datetime(2026, 10, 18, 21, 50, tzinfo=UTC)
GW1 = datetime(2026, 9, 5, 10, 0, tzinfo=UTC)       # GW g's deadline: GW1 + 7 days x (g - 1)
STAMP = "2026-10-18"
ELEMENTS = 600


def deadline(g):
    return GW1 + timedelta(days=7 * (g - 1))


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def round_robin(n=20):
    """38 gameweeks of 10 fixtures, every team once a gameweek."""
    teams, rounds = list(range(1, n + 1)), []
    for _ in range(n - 1):
        rounds.append([(teams[i], teams[n - 1 - i]) for i in range(n // 2)])
        teams = [teams[0], teams[-1]] + teams[1:-1]
    return rounds + [[(a, h) for h, a in r] for r in rounds]


class EUZone(tzinfo):
    """A stand-in Europe/Prague: CET, CEST from the last Sunday of March to the
    last Sunday of October at 01:00 UTC - no time-zone database needed."""

    @staticmethod
    def _last_sunday(year, month):
        d = datetime(year, month + 1, 1, 1, tzinfo=UTC) - timedelta(days=1)
        while d.weekday() != 6:
            d -= timedelta(days=1)
        return d

    def utcoffset(self, dt):
        u = dt.replace(tzinfo=None)
        start = self._last_sunday(u.year, 3).replace(tzinfo=None)
        end = self._last_sunday(u.year, 10).replace(tzinfo=None)
        return timedelta(hours=2 if start <= u < end else 1)

    def dst(self, dt):
        return self.utcoffset(dt) - timedelta(hours=1)

    def tzname(self, dt):
        return "CEST" if self.dst(dt) else "CET"

    def fromutc(self, dt):
        return dt + self.utcoffset(dt.replace(tzinfo=None))


PRAGUE = EUZone()


_OPEN = []                       # every in-memory database, closed after the module


def tearDownModule():
    for con in _OPEN:
        con.close()


def _db():
    con = sqlite3.connect(":memory:")
    con.executescript(S.SCHEMA)
    S.migrate(con)
    _OPEN.append(con)
    return con


def _fill(con, nights, updated):
    con.executemany("INSERT INTO teams (id, name, short_name, strength) VALUES (?,?,?,3)",
                    [(t, f"T{t}", f"T{t}") for t in range(1, 21)])
    fid = 0
    for g, pairs in enumerate(round_robin(), 1):
        for h, a in pairs:
            fid += 1
            ko = deadline(g) + timedelta(hours=2)
            con.execute("INSERT INTO fixtures (id, event, kickoff_time, team_h, team_a, finished, "
                        "started) VALUES (?,?,?,?,?,?,?)", (fid, g, iso(ko), h, a, int(g < 7), int(g <= 7)))
    con.executemany("INSERT INTO events (id, name, deadline_time, finished, data_checked) "
                    "VALUES (?,?,?,?,?)", [(g, f"GW{g}", iso(deadline(g)), int(g < 7), int(g < 7))
                                           for g in range(1, 39)])
    con.executemany("INSERT INTO players (id, web_name, team_id, position, now_cost, "
                    "chance_next_round, updated_at) VALUES (?,?,?,?,?,?,?)",
                    [(i, f"P{i}", i % 20 + 1, i % 4 + 1, 40 + i % 60, None, updated)
                     for i in range(1, ELEMENTS + 1)])
    for day in nights:
        con.executemany("INSERT INTO price_history (player_id, date, now_cost) VALUES (?,?,?)",
                        [(i, day, 40 + i % 60) for i in range(1, ELEMENTS + 1)])
    con.commit()


def _row(made, source, event, pid, val=1.0):
    return {"made_at": made, "source": source, "event": str(event), "player_id": str(pid),
            "web_name": f"P{pid}", "predicted": str(val)}


def _export(locked=False, now=NOW):
    """The two sections the stuck and lockdown checks read."""
    events = [{"event": g, "finished": int(g < 7 or locked), "data_checked": int(g < 7 or locked),
               "deadline_time": iso(deadline(g))} for g in range(1, 39)]
    fx = [{"event": 7, "home": f"T{h}", "away": f"T{a}",
           "kickoff_time": iso(deadline(7) + timedelta(hours=2 + i)), "finished": int(locked),
           "started": 1} for i, (h, a) in enumerate(round_robin()[6])]
    return {"gameweek": 7, "events": events, "fixtures_status": fx}


KEYS = sorted(["id", "code", "team", "element_type", "now_cost", "status", "minutes",
               "total_points", "defensive_contribution", "web_name"])


def world():
    """A healthy night: every check OK (27 is manual, 9 and 22 skip-free here)."""
    prev, db = _db(), _db()
    _fill(prev, ["2026-10-15", "2026-10-16", "2026-10-17"], "2026-10-17T21:40:00+00:00")
    _fill(db, ["2026-10-15", "2026-10-16", "2026-10-17", "2026-10-18"], "2026-10-18T21:40:00+00:00")
    old = [_row("2026-10-16T22:00:00+00:00", "own", 7, p) for p in range(1, 51)]
    new = [_row("2026-10-18T21:45:00+00:00", s, 8, p) for s in ("own", "xg", "minutes", "bottomup")
           for p in range(1, 51)]
    stats = {"calls": [["bootstrap-static/", 200], ["fixtures/", 200], ["event/7/live/", 200],
                       ["leagues-classic/455565/standings/", 200]],
             "elements": ELEMENTS, "element_ids": list(range(1, ELEMENTS + 1)), "element_keys": KEYS,
             "teams": 20, "fixtures": 380, "field_problems": [], "finished": True}
    return C.Ctx(db=db, prev=prev, stats=stats, prev_stats=json.loads(json.dumps(stats)),
                 log=old + new, prev_log=list(old), export=_export(), now=NOW,
                 started=NOW - timedelta(minutes=8),
                 prev_status=f"STATUS OK | generated {iso(NOW - timedelta(hours=24))} | x",
                 changed=[("reports/fpl_2026-10-18.txt", b"report")], repo_kb=120 * 1024,
                 repo_why="", key="", known_gaps={}, run_log=GOOD_RUN)


GOOD_RUN = ("running tests ...\nRan 454 tests in 9.1s\n\nOK (skipped=11)\nTESTS OK\n"
            "syncing FPL API ...\ncollecting odds ...\nODDS OK      20 events (20 with totals), "
            "1200 prices fetched 2026-10-18T21:41:00+00:00; credits used 4, remaining 496, this "
            "request 4\nrecord summary:\nRECORD OK own 275\nRECORD OK xg 260\n"
            "RECORD OK minutes 260\nRECORD OK bottomup 260\nRECORD OK fpl_ep 600\n"
            "archiving the export ...\n")
RED_RUN = ("running tests ...\nRan 454 tests in 9.5s\n\nFAILED (failures=3, skipped=11)\n"
           "TESTS FAILED - see logs/run_2026-10-18.log\nsyncing FPL API ...\n"
           "SKIPPED --record: test suite is red, no forecasts written\nrecord summary:\n"
           + "".join(f"RECORD FAIL {s} skipped - test suite is red\n" for s in C.SOURCES)
           + "archiving the export ...\n")

# git commits made by the code under test (fpl_publish.py) get their identity
# from the environment, never from the machine (S3 amendment 1, point 1)
IDENTITY = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def with_identity(test):
    saved = {k: os.environ.get(k) for k in IDENTITY}
    os.environ.update(IDENTITY)

    def restore():
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    test.addCleanup(restore)


def level(x, n):
    return C.CHECKS[n - 1](x)[0]


class TheChecks(unittest.TestCase):
    """Step 3: the table, every check with a planted failure."""

    def test_a_healthy_night_has_no_warn_and_no_fail(self):
        res = C.run_all(world())
        self.assertEqual([r for r in res if r.level in (C.WARN, C.FAIL)], [])
        self.assertEqual([r.n for r in res if r.level == C.SKIP], [22, 27])
        self.assertEqual(len(res), 30)

    def test_01_core_endpoints(self):
        x = world()
        x.stats["calls"][1] = ["fixtures/", 503]
        self.assertEqual(level(x, 1), C.FAIL)
        x.stats = None
        self.assertEqual(level(x, 1), C.FAIL)
        x = world()
        x.stats["calls"] = [c for c in x.stats["calls"] if "standings" not in c[0]]
        self.assertEqual(level(x, 1), C.FAIL)

    def test_02_element_summary_failures(self):
        x = world()
        x.stats["calls"] += [[f"element-summary/{i}/", 200] for i in range(98)]
        x.stats["calls"] += [["element-summary/98/", 404], ["element-summary/99/", "network"]]
        self.assertEqual(level(x, 2), C.OK)                 # 2 of 100
        x.stats["calls"].append(["element-summary/100/", 503])
        self.assertEqual(level(x, 2), C.FAIL)               # 3 of 101

    def test_03_player_count(self):
        for n, want in ((540, C.FAIL), (550, C.OK), (900, C.OK), (905, C.FAIL)):
            x = world()
            x.prev = None                                   # the range alone, no last night
            x.stats["elements"] = n
            self.assertEqual(level(x, 3), want, n)
        x = world()
        x.stats["elements"] = 640                           # +6.7% on last night
        self.assertEqual(level(x, 3), C.FAIL)
        x = world()
        x.stats["element_ids"].append(601)
        self.assertEqual(level(x, 3), C.WARN)

    def test_04_teams(self):
        x = world()
        x.stats["teams"] = 19
        self.assertEqual(level(x, 4), C.FAIL)

    def test_05_fixtures(self):
        x = world()
        x.stats["fixtures"] = 379
        self.assertEqual(level(x, 5), C.FAIL)

    def test_06_fixtures_per_gameweek(self):
        x = world()
        x.db.execute("UPDATE fixtures SET event = NULL WHERE id = (SELECT MIN(id) FROM fixtures WHERE event = 9)")
        self.assertEqual(level(x, 6), C.WARN)

    def test_07_team_appearances(self):
        x = world()
        h, a = x.db.execute("SELECT team_h, team_a FROM fixtures WHERE event = 10 ORDER BY id LIMIT 2").fetchall()[1]
        first = x.db.execute("SELECT id, team_h FROM fixtures WHERE event = 10 ORDER BY id LIMIT 1").fetchone()
        x.db.execute("UPDATE fixtures SET team_a = ? WHERE id = ?", (h, first[0]))   # h twice, one team none
        self.assertEqual(level(x, 7), C.WARN)

    def test_08_required_fields(self):
        x = world()
        x.stats["field_problems"] = ["element 7: code missing"]
        self.assertEqual(level(x, 8), C.FAIL)

    def test_09_element_key_set(self):
        x = world()
        x.stats["element_keys"] = KEYS + ["new_field"]
        self.assertEqual(level(x, 9), C.WARN)
        x.prev_stats = None
        self.assertEqual(level(x, 9), C.SKIP)

    def test_10_distinct_prices(self):
        x = world()
        x.db.execute("UPDATE players SET now_cost = 50 + id % 10")
        self.assertEqual(level(x, 10), C.FAIL)

    def test_11_price_step(self):
        x = world()
        x.db.execute("UPDATE price_history SET now_cost = now_cost + 3 WHERE player_id = 1 AND date = '2026-10-18'")
        self.assertEqual(level(x, 11), C.FAIL)
        x = world()
        x.db.execute("DELETE FROM price_history WHERE player_id = 1 AND date = '2026-10-17'")
        x.db.execute("UPDATE price_history SET now_cost = now_cost + 2 WHERE player_id = 1 AND date = '2026-10-18'")
        self.assertEqual(level(x, 11), C.OK)                # two nights, 0.2 allowed

    def test_12_price_changes(self):
        x = world()
        x.db.execute("UPDATE price_history SET now_cost = now_cost + 1 WHERE player_id <= 61 AND date = '2026-10-18'")
        self.assertEqual(level(x, 12), C.WARN)

    def test_13_chance_of_playing_zero(self):
        x = world()
        x.db.execute("UPDATE players SET chance_next_round = 0 WHERE id <= 240")
        self.assertEqual(level(x, 13), C.FAIL)               # 40%
        x.db.execute("UPDATE players SET chance_next_round = NULL WHERE id = 240")
        self.assertEqual(level(x, 13), C.OK)

    def test_14_position_changes(self):
        x = world()
        x.db.execute("UPDATE players SET position = 4 WHERE id = 1")
        self.assertEqual(level(x, 14), C.WARN)

    def test_15_sqlite_integrity(self):
        class Broken:
            def __init__(self, con):
                self.con = con

            def execute(self, sql, args=()):
                if sql.startswith("PRAGMA integrity_check"):
                    return self.con.execute("SELECT '*** in database main ***'")
                return self.con.execute(sql, args)
        x = world()
        x.db = Broken(x.db)
        self.assertEqual(level(x, 15), C.FAIL)
        x.db = None
        self.assertEqual(level(x, 15), C.FAIL)

    def test_15_a_real_corrupt_file_is_a_fail(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "x.sqlite")
        con = sqlite3.connect(path)
        con.execute("CREATE TABLE t (a INTEGER PRIMARY KEY, b TEXT)")
        con.executemany("INSERT INTO t VALUES (?, ?)", [(i, "x" * 300) for i in range(400)])
        con.execute("CREATE INDEX tb ON t (b)")
        con.commit()
        con.close()
        with open(path, "r+b") as fh:                      # zero a page of the index
            fh.seek(4096 * 6)
            fh.write(b"\x00" * 4096)
        x = world()
        x.db = sqlite3.connect(path)
        self.addCleanup(x.db.close)
        try:
            got = level(x, 15)
        except sqlite3.DatabaseError:
            got = C.FAIL
        self.assertEqual(got, C.FAIL)

    def test_16_price_history_rows(self):
        x = world()
        x.db.execute("DELETE FROM price_history WHERE date IN ('2026-10-15', '2026-10-16')")
        self.assertEqual(level(x, 16), C.FAIL)               # 1800 -> 1200 rows
        x = world()
        x.db.execute("DELETE FROM price_history WHERE date = '2026-10-18' AND player_id > 300")
        self.assertEqual(level(x, 16), C.WARN)               # +300 against about +600

    def test_17_price_date_gaps(self):
        x = world()
        x.db.execute("DELETE FROM price_history WHERE date = '2026-10-16'")
        self.assertEqual(level(x, 17), C.WARN)
        x.known_gaps = {"2026-10-16": "known"}
        self.assertEqual(level(x, 17), C.OK)

    def test_18_projection_log_growth(self):
        x = world()
        x.log += [_row("2026-10-18T21:45:00+00:00", "own", 9, p) for p in range(1, 700)]
        self.assertEqual(level(x, 18), C.FAIL)                # 749 > 1.2 x 600

    def test_19_duplicate_keys(self):
        x = world()
        x.log.append(dict(x.log[-1], predicted="2.0"))
        self.assertEqual(level(x, 19), C.WARN)

    def test_20_rows_after_the_deadline(self):
        x = world()
        x.log.append(_row(iso(deadline(8) + timedelta(minutes=1)).replace("Z", "+00:00"), "own", 8, 99))
        self.assertEqual(level(x, 20), C.FAIL)               # a new late row
        x.prev_log.append(x.log[-1])
        self.assertEqual(level(x, 20), C.WARN)               # one already committed

    def test_21_stuck_gameweek(self):
        x = world()
        x.now = deadline(7) + timedelta(hours=2 + 9 + 80)    # 80 h after the last kickoff
        self.assertEqual(level(x, 21), C.WARN)

    def test_23_secret_in_the_files_to_commit(self):
        import gzip
        x = world()
        x.changed = [("logs/run.log", b"GET /odds?" + b"api" + b"Key=" + b"x" * 3)]
        self.assertEqual(level(x, 23), C.FAIL)
        x.key = "s3cr" + "etvalue"
        x.changed = [("exports/e.json.gz", gzip.compress(b"... " + x.key.encode() + b" ..."))]
        self.assertEqual(level(x, 23), C.FAIL)

    def test_24_repo_size(self):
        x = world()
        x.repo_kb = 600 * 1024
        self.assertEqual(level(x, 24), C.WARN)
        x.repo_kb = 950 * 1024
        self.assertEqual(level(x, 24), C.FAIL)
        x.repo_kb = None
        self.assertEqual(level(x, 24), C.SKIP)

    def test_25_run_duration(self):
        x = world()
        x.started = NOW - timedelta(minutes=16)
        self.assertEqual(level(x, 25), C.WARN)

    def test_26_heartbeat(self):
        x = world()
        x.prev_status = f"STATUS OK | generated {iso(NOW - timedelta(hours=31))} | x"
        self.assertEqual(level(x, 26), C.WARN)
        x.prev_status = None
        self.assertEqual(level(x, 26), C.SKIP)

    def test_27_workflow_state_is_manual(self):
        self.assertEqual(level(world(), 27), C.SKIP)

    def test_28_test_gate(self):
        """S3 amendment 1, point 3: a red suite fails the night."""
        x = world()
        self.assertEqual(C.c28(x), (C.OK, "454 tests green"))
        x.run_log = RED_RUN
        self.assertEqual(C.c28(x), (C.FAIL, "the suite is red: FAILED (failures=3, skipped=11)"))
        x.run_log = "syncing FPL API ...\n"
        self.assertEqual(level(x, 28), C.FAIL)               # the suite never ran

    def test_29_record(self):
        x = world()
        self.assertEqual(level(x, 29), C.OK)
        x.run_log = GOOD_RUN.replace("RECORD OK minutes 260", "RECORD FAIL minutes locked")
        self.assertEqual(C.c29(x), (C.FAIL, "minutes locked"))
        x.run_log = RED_RUN                                  # skipped: the suite was red
        self.assertEqual(level(x, 29), C.FAIL)
        self.assertIn("own skipped - test suite is red", C.c29(x)[1])
        x.run_log = GOOD_RUN.replace("RECORD OK xg 260\n", "")
        self.assertEqual(C.c29(x), (C.FAIL, "xg missing"))
        x.run_log = GOOD_RUN.replace("record summary:", "no summary")
        self.assertEqual(level(x, 29), C.FAIL)

    def test_a_night_with_a_red_suite_never_reads_ok(self):
        """The dry run of 18 Oct said STATUS OK, 23/23, while three tests failed;
        that must be impossible (S3 amendment 1, point 3)."""
        x = world()
        x.run_log = RED_RUN
        res = C.run_all(x)
        line = C.status_line(res, NOW, None, x.repo_kb, PRAGUE)
        self.assertTrue(line.startswith("STATUS FAIL |"), line)
        self.assertEqual(sorted(r.n for r in res if r.level == C.FAIL), [28, 29])

    def test_a_check_that_raises_is_a_warn_never_a_crash(self):
        x = world()
        x.stats = {"calls": "not a list"}
        res = {r.n: r for r in C.run_all(x)}
        self.assertEqual(res[1].level, C.WARN)
        self.assertIn("the check itself failed", res[1].detail)


class Reconciliation(unittest.TestCase):
    """Check 22: computed = entry_history.points, after lockdown only (ruling
    S3, point 6)."""

    def _gw(self, picks, points, fpl, subs=(), minutes=None):
        x = world()
        x.export = _export(locked=True)
        x.now = deadline(7) + timedelta(days=3)
        for pid, pos, mult, cap, vice in picks:
            x.db.execute("INSERT INTO picks VALUES (1, 7, ?, ?, ?, ?, ?)", (pid, pos, mult, cap, vice))
            x.db.execute("INSERT INTO player_gw (player_id, event, minutes, total_points) VALUES (?,7,?,?)",
                         (pid, (minutes or {}).get(pid, 90), points[pid]))
        for inn, out in subs:
            x.db.execute("INSERT INTO automatic_subs VALUES (1, 7, ?, ?, 'x')", (inn, out))
        x.db.execute("INSERT INTO entry_gw (entry_id, event, points, fetched_at_utc) VALUES (1, 7, ?, 'x')", (fpl,))
        return x

    def _squad(self, cap=10, vice=11, mult=2, bench_mult=0):
        return [(p, p, (mult if p == cap else 1) if p <= 11 else bench_mult,
                 int(p == cap), int(p == vice)) for p in range(1, 16)]

    def test_silent_mid_gameweek(self):
        x = world()                                          # GW7 not locked
        self.assertEqual(C.c22(x)[0], C.SKIP)
        self.assertIn("silent mid-gameweek", C.c22(x)[1])

    def test_equal_after_lockdown_is_ok_and_a_difference_is_a_warn(self):
        pts = {p: p for p in range(1, 16)}
        right = sum(range(1, 12)) + 10                       # captain 10 doubled
        self.assertEqual(C.c22(self._gw(self._squad(), pts, right))[0], C.OK)
        self.assertEqual(C.c22(self._gw(self._squad(), pts, right - 2))[0], C.WARN)

    def test_the_vice_takes_the_armband_when_the_captain_does_not_play(self):
        pts = {p: (0 if p == 10 else p) for p in range(1, 16)}
        right = sum(range(1, 12)) - 10 + 11                  # vice 11 doubled
        x = self._gw(self._squad(), pts, right, minutes={10: 0})
        self.assertEqual(C.entry_points(x.db, 1, 7), (right, right))

    def test_automatic_subs_bench_boost_and_triple_captain(self):
        pts = {p: p for p in range(1, 16)}
        subbed = sum(range(1, 12)) - 5 + 12 + 10             # 12 for 5, captain 10 doubled
        x = self._gw(self._squad(), pts, subbed, subs=[(12, 5)], minutes={5: 0})
        self.assertEqual(C.entry_points(x.db, 1, 7)[0], subbed)
        boost = sum(range(1, 16)) + 10
        x = self._gw(self._squad(bench_mult=1), pts, boost)
        self.assertEqual(C.entry_points(x.db, 1, 7)[0], boost)
        triple = sum(range(1, 12)) + 20
        x = self._gw(self._squad(mult=3), pts, triple)
        self.assertEqual(C.entry_points(x.db, 1, 7)[0], triple)


class StatusLine(unittest.TestCase):
    """Step 3.2 and ruling S3, point 5: UTC and Prague, right on both sides of
    the 25 Oct clock change."""

    def _line(self, when, results=None):
        res = results or C.run_all(world())
        return C.status_line(res, NOW, (8, when), 120 * 1024, PRAGUE)

    def test_the_line_and_its_fields(self):
        line = self._line(datetime(2026, 10, 23, 17, 30, tzinfo=UTC))
        self.assertEqual(line, "STATUS OK | generated 2026-10-18T21:50:00Z | next deadline GW8 "
                               "2026-10-23 17:30 UTC / 2026-10-23 19:30 Prague | checks 28/28 | repo 120 MB")

    def test_both_sides_of_the_25_october_change(self):
        before = self._line(datetime(2026, 10, 25, 0, 30, tzinfo=UTC))
        after = self._line(datetime(2026, 10, 25, 1, 30, tzinfo=UTC))
        self.assertIn("2026-10-25 00:30 UTC / 2026-10-25 02:30 Prague", before)   # CEST, +2
        self.assertIn("2026-10-25 01:30 UTC / 2026-10-25 02:30 Prague", after)    # CET, +1
        self.assertIn("2026-10-31 11:00 UTC / 2026-10-31 12:00 Prague",
                      self._line(datetime(2026, 10, 31, 11, 0, tzinfo=UTC)))

    def test_the_real_prague_zone_where_installed(self):
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo("Europe/Prague")
        except zoneinfo.ZoneInfoNotFoundError:
            self.skipTest("no time-zone database here (Windows without tzdata)")
        res = C.run_all(world())
        for when, local in ((datetime(2026, 10, 25, 0, 30, tzinfo=UTC), "02:30"),
                            (datetime(2026, 10, 25, 1, 30, tzinfo=UTC), "02:30"),
                            (datetime(2027, 3, 28, 1, 30, tzinfo=UTC), "03:30")):
            self.assertIn(f"{local} Prague", C.status_line(res, NOW, (8, when), None, tz))

    def test_warn_and_fail_and_the_counts(self):
        x = world()
        x.started = NOW - timedelta(minutes=20)              # 25 WARN
        line = C.status_line(C.run_all(x), NOW, None, None, PRAGUE)
        self.assertTrue(line.startswith("STATUS WARN |"), line)
        self.assertIn("| next deadline none | checks 27/28 | repo ? MB", line)
        x.stats["teams"] = 19                                # 4 FAIL
        self.assertTrue(C.status_line(C.run_all(x), NOW, None, None, PRAGUE).startswith("STATUS FAIL"))

    def test_the_status_time_reads_back(self):
        line = self._line(datetime(2026, 10, 23, 17, 30, tzinfo=UTC))
        self.assertEqual(C.status_time(line), NOW)


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t",
                           "-c", "core.autocrlf=false", *args],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")


class ChecksMain(unittest.TestCase):
    """checks.main on a data folder with a last commit: the status file, the
    report's first line, and the dry run's own file (ruling S3, point 7)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        d = self.tmp
        subprocess.run(["git", "init", "-q", d], check=True)
        for sub in ("reports", "logs"):
            os.makedirs(os.path.join(d, sub))
        self._db(os.path.join(d, "fpl.sqlite"), ["2026-10-16", "2026-10-17"], "2026-10-17T21:40:00+00:00")
        self._put("projection_log.csv", "made_at,source,event,player_id,web_name,predicted\n")
        self._put("reports/status.txt", f"STATUS OK | generated {iso(NOW - timedelta(hours=24))} | x\n")
        self._put("logs/run_2026-10-17.log", "==== run x ====\n" + C.STATS_PREFIX + json.dumps({"element_keys": KEYS}) + "\n")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "last night")
        os.remove(os.path.join(d, "fpl.sqlite"))
        self._db(os.path.join(d, "fpl.sqlite"), ["2026-10-16", "2026-10-17", "2026-10-18"],
                 "2026-10-18T21:40:00+00:00")
        stats = world().stats
        self._put(f"logs/run_{STAMP}.log", f"==== run {STAMP} UTC, started 2026-10-18 21:42:00 UTC ====\n"
                  + GOOD_RUN + C.STATS_PREFIX + json.dumps(stats) + "\n")
        self._put(f"reports/fpl_{STAMP}.txt", "THE REPORT\n")
        with open(os.path.join(d, "fpl_export_gw7.json"), "w", encoding="utf-8") as fh:
            json.dump(_export(), fh)

    @staticmethod
    def _db(path, nights, updated):
        con = sqlite3.connect(path)
        con.executescript(S.SCHEMA)
        S.migrate(con)
        _fill(con, nights, updated)
        con.close()

    def _put(self, name, text):
        with open(os.path.join(self.tmp, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    def _get(self, name):
        with open(os.path.join(self.tmp, name), encoding="utf-8", newline="") as fh:
            return fh.read()

    def _main(self, env):
        out = io.StringIO()
        with redirect_stdout(out):
            code = C.main(["--stamp", STAMP, "--data", self.tmp], env=env, tz=PRAGUE, now=NOW)
        return code, out.getvalue()

    def test_a_real_run_writes_status_txt_and_heads_the_report(self):
        code, out = self._main({})
        self.assertEqual(code, 0, out)
        status = self._get("reports/status.txt")
        self.assertTrue(status.startswith("STATUS OK | generated 2026-10-18T21:50:00Z | next deadline GW8 "
                                          "2026-10-24 10:00 UTC / 2026-10-24 12:00 Prague"), status)
        self.assertEqual(len(status.splitlines()), 31)
        self.assertEqual(self._get(f"reports/fpl_{STAMP}.txt"), status.splitlines()[0] + "\n\nTHE REPORT\n")
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "reports", "status_dryrun.txt")))

    def test_a_dry_run_never_writes_status_txt(self):
        before = self._get("reports/status.txt")
        code, out = self._main({"GITHUB_REF": "refs/heads/s3-wip", "FPL_DRY_RUN": "true"})
        self.assertEqual(self._get("reports/status.txt"), before)
        self.assertTrue(self._get("reports/status_dryrun.txt").startswith("STATUS "))

    def test_a_fail_exits_one(self):
        self._put(f"logs/run_{STAMP}.log", f"==== run {STAMP} UTC, started 2026-10-18 21:42:00 UTC ====\n")
        code, out = self._main({})
        self.assertEqual(code, 1)
        self.assertTrue(self._get("reports/status.txt").startswith("STATUS FAIL |"))


class PublishOnAFail(unittest.TestCase):
    """Step 3.1: FAIL = no data commit; a dry run still reports to data-dryrun."""

    def setUp(self):
        with_identity(self)                  # fpl_publish.py commits: no machine identity
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.remote = os.path.join(self.tmp, "remote.git")
        subprocess.run(["git", "init", "-q", "--bare", self.remote], check=True)
        seed = os.path.join(self.tmp, "seed")
        subprocess.run(["git", "init", "-q", seed], check=True)
        con = sqlite3.connect(os.path.join(seed, "fpl.sqlite"))
        con.executescript("CREATE TABLE price_history (player_id INTEGER, date TEXT, price REAL);"
                          "CREATE TABLE events (id INTEGER PRIMARY KEY, deadline_time TEXT);")
        con.execute("INSERT INTO price_history VALUES (1, '2026-10-17', 5.0)")
        con.commit()
        con.close()
        os.makedirs(os.path.join(seed, "reports"))
        for name, body in (("projection_log.csv", "made_at,source,event,player_id,web_name,predicted\n"),
                           ("reports/status.txt", "STATUS FAIL | generated 2026-10-17T21:50:00Z | old\n")):
            with open(os.path.join(seed, name), "w", encoding="utf-8", newline="") as fh:
                fh.write(body)
        _git(seed, "add", "-A")
        _git(seed, "commit", "-q", "-m", "first")
        _git(seed, "push", "-q", self.remote, "HEAD:refs/heads/data")
        self.run_dir = os.path.join(self.tmp, "run")
        subprocess.run(["git", "clone", "-q", "--branch", "data", "file://" + self.remote.replace("\\", "/"),
                        self.run_dir], check=True)

    def _status(self, name, text):
        with open(os.path.join(self.run_dir, "reports", name), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)

    def _publish(self, env):
        lines = []
        with redirect_stdout(io.StringIO()):
            code = PUB.main([self.run_dir], sleep=lambda s: None, say=lines.append, env=env)
        return code, lines

    def _head(self, branch):
        r = _git(self.remote, "rev-parse", "--verify", "-q", f"refs/heads/{branch}")
        return r.stdout.strip() if r.returncode == 0 else None

    def test_a_fresh_fail_commits_nothing(self):
        before = self._head("data")
        self._status("status.txt", "STATUS FAIL | generated 2026-10-18T21:50:00Z | x\n 4 FAIL teams: 19 teams, not 20\n")
        code, lines = self._publish({})
        self.assertEqual(code, 1, lines)
        self.assertIn("CHECKS FAIL  4 FAIL teams: 19 teams, not 20", lines)
        self.assertEqual(self._head("data"), before)

    def test_a_status_not_written_tonight_does_not_block(self):
        code, lines = self._publish({})                     # the committed FAIL of last night
        self.assertEqual(code, 0, lines)
        self.assertFalse(any(l.startswith("CHECKS FAIL") for l in lines))

    def test_a_fresh_ok_is_committed(self):
        self._status("status.txt", "STATUS OK | generated 2026-10-18T21:50:00Z | x\n")
        code, lines = self._publish({})
        self.assertEqual(code, 0, lines)
        self.assertIn("PUSH OK      origin data", lines)

    def test_a_dry_run_with_a_fail_still_reports_to_data_dryrun(self):
        before = self._head("data")
        self._status("status_dryrun.txt", "STATUS FAIL | generated 2026-10-18T21:50:00Z | x\n 4 FAIL teams: x\n")
        code, lines = self._publish({"GITHUB_REF": "refs/heads/s3-wip"})
        self.assertEqual(code, 0, lines)
        self.assertIn("CHECKS FAIL  a real run would commit nothing; the dry run still reports to data-dryrun", lines)
        self.assertEqual(self._head("data"), before)
        self.assertIsNotNone(self._head("data-dryrun"))


class BackupRun(unittest.TestCase):
    """Ruling S3, point 4: the 03:17 cron runs only when the nightly left no
    status.txt, and writes nothing when it exists."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        os.makedirs(os.path.join(self.tmp, "reports"))
        self.at = datetime(2026, 10, 19, 3, 17, tzinfo=UTC)

    def _status(self, generated):
        with open(os.path.join(self.tmp, "reports", "status.txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write(f"STATUS OK | generated {iso(generated)} | next deadline x | checks 1/1 | repo 1 MB\n")

    def _snapshot(self):
        out = {}
        for root, _, files in os.walk(self.tmp):
            for f in files:
                p = os.path.join(root, f)
                with open(p, "rb") as fh:
                    out[p] = (fh.read(), os.path.getmtime(p))
        return out

    def test_it_exits_without_writing_when_the_status_file_exists(self):
        self._status(datetime(2026, 10, 18, 21, 52, tzinfo=UTC))
        before = self._snapshot()
        due, why = N.backup_due(self.tmp, self.at, N.BACKUP_CRON)
        self.assertFalse(due, why)
        out = os.path.join(tempfile.mkdtemp(), "github_output")
        self.addCleanup(shutil.rmtree, os.path.dirname(out), True)
        lines = []
        self.assertEqual(N.due_main(self.tmp, {"FPL_SCHEDULE": N.BACKUP_CRON, "GITHUB_OUTPUT": out},
                                    self.at, lines.append), 0)
        self.assertTrue(lines[0].startswith("NOT DUE      backup run skipped:"), lines)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "run=false\n")
        self.assertEqual(self._snapshot(), before, "the backup run wrote into the data folder")

    def test_it_runs_when_the_status_file_is_missing_or_older_than_the_nightly(self):
        self.assertTrue(N.backup_due(self.tmp, self.at, N.BACKUP_CRON)[0])
        self._status(datetime(2026, 10, 17, 21, 50, tzinfo=UTC))
        self.assertTrue(N.backup_due(self.tmp, self.at, N.BACKUP_CRON)[0])
        self._status(datetime(2026, 10, 18, 13, 0, tzinfo=UTC))     # a day-time dispatch only
        self.assertTrue(N.backup_due(self.tmp, self.at, N.BACKUP_CRON)[0])

    def test_the_nightly_and_a_dispatch_are_always_due(self):
        self._status(datetime(2026, 10, 18, 21, 52, tzinfo=UTC))
        self.assertTrue(N.backup_due(self.tmp, self.at, "40 21 * * *")[0])
        self.assertTrue(N.backup_due(self.tmp, self.at, "")[0])

    def test_the_workflow_runs_every_step_only_when_due_in_the_one_group(self):
        y = _yml("nightly.yml")
        self.assertIn('    - cron: "17 3 * * *"\n', y)
        self.assertIn('    - cron: "40 21 * * *"\n', y)
        self.assertIn("    timeout-minutes: 30\n", y)
        steps = y[y.index("    steps:"):].split("\n      - ")[1:]
        due = next(i for i, s in enumerate(steps) if "id: due" in s)
        self.assertIn("FPL_SCHEDULE: ${{ github.event.schedule }}", steps[due])
        self.assertIn("run: python fpl_nightly.py --due", steps[due])
        for s in steps[due + 1:]:
            cond = next((l for l in s.splitlines() if l.strip().startswith("if:")), "")
            self.assertIn("steps.due.outputs.run == 'true'", cond, s[:50])
        group = next(l for l in y.splitlines() if l.startswith("  group:"))
        self.assertNotIn("schedule", group, "the backup cron must share the nightly's group")


def _yml(name):
    with open(os.path.join(HERE, ".github", "workflows", name), encoding="utf-8") as fh:
        return fh.read()


class FakeGitHub:
    def __init__(self, open_issues=(), fail=False):
        self.issues, self.calls, self.fail = list(open_issues), [], fail

    def open_issues(self):
        if self.fail:
            raise OSError("API down")
        return list(self.issues)

    def call(self, method, path, body=None):
        self.calls.append((method, path, body))
        if method == "POST" and path == "/issues":
            return {"number": 9}
        return {}


class FailureIssue(unittest.TestCase):
    """Step 3.3 and ruling S3, points 3 and 7: one open issue, opened or updated
    on a red run, closed on the next green one, never touched by a dry run."""

    RED = {"RUN_OUTCOMES": "nightly=failure publish=failure backup=skipped",
           "GITHUB_REPOSITORY": "o/r", "GITHUB_RUN_ID": "5"}
    GREEN = {"RUN_OUTCOMES": "nightly=success publish=success backup=skipped",
             "GITHUB_REPOSITORY": "o/r", "GITHUB_RUN_ID": "6"}

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        os.makedirs(os.path.join(self.tmp, "reports"))
        with open(os.path.join(self.tmp, "reports", "status.txt"), "w", encoding="utf-8", newline="") as fh:
            fh.write("STATUS FAIL | generated x | y\n 1 OK   core endpoints: fine\n 4 FAIL teams: 19 teams, not 20\n")

    def _run(self, env, gh):
        lines = []
        code = A.main([self.tmp], env=env, say=lines.append, gh=gh)
        return code, lines

    def test_a_planted_failure_opens_the_issue_and_the_next_green_run_closes_it(self):
        gh = FakeGitHub()
        code, lines = self._run(self.RED, gh)
        self.assertEqual(code, 0, lines)
        method, path, body = gh.calls[0]
        self.assertEqual((method, path, body["title"]), ("POST", "/issues", A.TITLE))
        self.assertIn("4 FAIL teams: 19 teams, not 20", body["body"])
        self.assertIn("nightly (failure)", body["body"])
        self.assertNotIn("core endpoints", body["body"])
        gh = FakeGitHub([{"number": 9, "title": A.TITLE}])
        code, lines = self._run(self.GREEN, gh)
        self.assertEqual([c[:2] for c in gh.calls], [("POST", "/issues/9/comments"), ("PATCH", "/issues/9")])
        self.assertEqual(gh.calls[1][2], {"state": "closed"})
        self.assertIn("ALERT CLOSED issue #9: the run is green", lines)

    def test_an_open_issue_is_updated_never_a_second_one(self):
        gh = FakeGitHub([{"number": 4, "title": A.TITLE}])
        self._run(self.RED, gh)
        self.assertEqual([c[:2] for c in gh.calls], [("PATCH", "/issues/4"), ("POST", "/issues/4/comments")])

    def test_a_second_open_issue_is_closed_as_a_duplicate(self):
        gh = FakeGitHub([{"number": 4, "title": A.TITLE}, {"number": 7, "title": A.TITLE}])
        self._run(self.RED, gh)
        self.assertIn(("PATCH", "/issues/7", {"state": "closed"}), gh.calls)
        self.assertNotIn(("POST", "/issues"), [c[:2] for c in gh.calls])

    def test_a_dry_run_never_opens_or_closes_it(self):
        gh = FakeGitHub([{"number": 4, "title": A.TITLE}])
        for env in (dict(self.RED, GITHUB_REF="refs/heads/s3-wip"),
                    dict(self.GREEN, GITHUB_REF="refs/heads/master", FPL_DRY_RUN="true")):
            code, lines = self._run(env, gh)
            self.assertEqual(code, 0)
            self.assertTrue(lines[0].startswith("ALERT skipped: dry run"), lines)
        self.assertEqual(gh.calls, [])

    def test_a_green_run_with_no_issue_does_nothing(self):
        gh = FakeGitHub()
        self._run(self.GREEN, gh)
        self.assertEqual(gh.calls, [])

    def test_an_api_failure_turns_a_red_run_red_and_leaves_a_green_one_green(self):
        self.assertEqual(self._run(self.RED, FakeGitHub(fail=True))[0], 1)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(self._run(self.GREEN, FakeGitHub(fail=True))[0], 0)

    def test_the_workflow_grants_issues_write_and_contents_write_only(self):
        y = _yml("nightly.yml")
        job = y[y.index("    permissions:"):y.index("    env:")]
        self.assertEqual([l.split("#")[0].strip() for l in job.splitlines()[1:] if l.strip()],
                         ["contents: write", "issues: write"])
        step = y[y.index("name: Failure issue"):]
        self.assertIn("if: always() && steps.due.outputs.run == 'true' && env.FPL_DRY_RUN != 'true'", step)
        self.assertIn("run: python fpl_alert.py data", step)
        self.assertIn('RUN_OUTCOMES: "nightly=${{ steps.nightly.outcome }} publish=${{ steps.publish.outcome }} '
                      'backup=${{ steps.backup.outcome }}"', step)


class RetryPolicy(unittest.TestCase):
    """Step 3, check 2: retry only 429, 5xx and network errors; a 403 at most
    once; the final status of every request in SYNC STATS."""

    def setUp(self):
        self.sleeps = []
        self.saved = (S._urlopen, S._sleep, list(S.FAILED), dict(S.STATS))
        S._sleep = self.sleeps.append
        S.FAILED[:] = []
        S.STATS.clear()
        S.STATS["calls"] = []

    def tearDown(self):
        S._urlopen, S._sleep = self.saved[0], self.saved[1]
        S.FAILED[:] = self.saved[2]
        S.STATS.clear()
        S.STATS.update(self.saved[3])

    def _get(self, *errors):
        seq, calls = list(errors), []

        def opener(req, timeout=30):
            calls.append(req.full_url)
            e = seq.pop(0) if seq else None
            if isinstance(e, int):
                raise urllib.error.HTTPError(req.full_url, e, "x", {}, io.BytesIO(b""))
            if e == "net":
                raise urllib.error.URLError("reset")
            if e == "json":
                return io.BytesIO(b"<html>")
            return io.BytesIO(b'{"ok": 1}')
        S._urlopen = opener
        with redirect_stdout(io.StringIO()):
            got = S.get("fixtures/")
        return got, len(calls)

    def test_404_is_not_retried(self):
        self.assertEqual(self._get(404, 404), (None, 1))
        self.assertEqual(S.STATS["calls"], [["fixtures/", 404]])

    def test_403_is_retried_once(self):
        self.assertEqual(self._get(403, 403, 403), (None, 2))
        self.assertEqual(self._get(403), ({"ok": 1}, 2))

    def test_429_5xx_and_network_errors_are_retried(self):
        self.assertEqual(self._get(429, 503, "net"), ({"ok": 1}, 4))
        self.assertEqual(self._get(500, 502, 503, 504), (None, 4))

    def test_a_body_that_is_not_json_is_not_retried(self):
        self.assertEqual(self._get("json"), (None, 1))
        self.assertEqual(S.STATS["calls"][-1], ["fixtures/", "bad-json"])

    def test_the_pause_between_calls_is_inside_0_3_to_0_5_seconds(self):
        self.assertTrue(0.3 <= S.PAUSE <= 0.5)

    def test_field_problems_finds_missing_and_mistyped_fields(self):
        good = {k: 1 for k in S.REQUIRED_ELEMENT}
        good["status"] = "a"
        self.assertEqual(S.field_problems([good], S.REQUIRED_ELEMENT, "element"), [])
        bad = dict(good, code=None, minutes=True, now_cost="55")
        self.assertEqual(S.field_problems([bad], S.REQUIRED_ELEMENT, "element"),
                         ["element 1: code missing", "element 1: now_cost is str",
                          "element 1: minutes is bool"])
        self.assertEqual(S.field_problems([{"id": 3, "deadline_time": "x", "data_checked": 1}],
                                          S.REQUIRED_EVENT, "event"), ["event 3: data_checked is int"])

    def test_the_sync_prints_its_stats_even_when_it_stops_early(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        here, argv, get, tz = os.getcwd(), sys.argv, S.get, S.london_tz
        boot = {"teams": [], "elements": [{"id": 1}], "events": []}
        S.get = lambda path: boot if path.startswith("bootstrap") else None
        S.london_tz = lambda: timezone.utc
        out = io.StringIO()
        try:
            os.chdir(tmp)
            sys.argv = ["fpl_sync.py"]
            with redirect_stdout(out):
                with self.assertRaises(Exception):
                    S.main()
        finally:
            os.chdir(here)
            sys.argv, S.get, S.london_tz = argv, get, tz
        stats = C.sync_stats(out.getvalue())
        self.assertIsNotNone(stats, out.getvalue()[-300:])
        self.assertFalse(stats["finished"])
        self.assertEqual(stats["elements"], 1)
        self.assertTrue(any("element 1: code missing" == p for p in stats["field_problems"]))


class PinnedActions(unittest.TestCase):
    """Ruling S3, point 2: checkout and setup-python at their current major
    versions, pinned to full commit SHAs, in every workflow."""

    CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1"
    SETUP = "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97  # v7.0.0"

    def test_every_action_is_pinned_to_a_full_sha(self):
        import re
        for name in os.listdir(os.path.join(HERE, ".github", "workflows")):
            for line in _yml(name).splitlines():
                if line.strip().startswith(("- uses:", "uses:")):
                    self.assertRegex(line, r"uses: [\w.-]+/[\w.-]+@[0-9a-f]{40}  # v\d", f"{name}: {line}")

    def test_the_versions(self):
        y = _yml("nightly.yml")
        self.assertEqual(y.count(self.CHECKOUT), 2)
        self.assertEqual(y.count(self.SETUP), 1)
        self.assertIn(self.CHECKOUT.split("  #")[0], _yml("secret-scan.yml"))
        for old in ("@v4", "@v5"):
            self.assertNotIn(old, y)


class Hermetic(unittest.TestCase):
    """S3 amendment 1, points 1 and 2: every test that runs git sets its own
    identity and never relies on machine config. The proof, kept: every test
    class that runs git (found in the sources) runs again in a child process
    whose home is an empty folder and whose git reads no system or global
    config, and with no git identity in its environment."""

    # every test file: test_fpl.py and each tests/test_<item>.py (W1: a new
    # file is covered the day it lands)
    FILES = ("test_fpl.py",) + tuple(sorted(
        os.path.join("tests", f) for f in os.listdir(os.path.join(HERE, "tests"))
        if f.startswith("test_") and f.endswith(".py")))

    def _git_classes(self):
        import ast
        import re
        found = []
        for name in self.FILES:
            module = name[:-3].replace(os.sep, ".")
            with open(os.path.join(HERE, name), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            helpers = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)
                       and re.search(r"[\"']git[\"']", ast.unparse(n))}
            for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
                src = ast.unparse(cls)
                calls = {c.func.id for c in ast.walk(cls) if isinstance(c, ast.Call)
                         and isinstance(c.func, ast.Name)}
                if (re.search(r"[\"']git[\"']", src) or "PUB.main" in src or calls & helpers) \
                        and cls.name != "Hermetic":
                    found.append(f"{module}.{cls.name}")
        return found

    def test_the_git_using_tests_pass_with_an_empty_home(self):
        classes = self._git_classes()
        for must in ("test_fpl.Publish", "test_fpl.PrePush", "test_fpl.DataGate",
                     "tests.test_S3.PublishOnAFail", "tests.test_S3.ChecksMain"):
            self.assertIn(must, classes)
        home = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, home, True)
        empty = os.path.join(home, "empty.gitconfig")
        open(empty, "w").close()
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("GIT_AUTHOR_", "GIT_COMMITTER_", "EMAIL"))}
        env.update(HOME=home, USERPROFILE=home, XDG_CONFIG_HOME=home, GIT_CONFIG_NOSYSTEM="1",
                   GIT_CONFIG_GLOBAL=empty, PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", *classes], cwd=HERE,
                           env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout[-3000:])


class FastTrack(unittest.TestCase):
    """RULING FAST-TRACK: item 1 (the nightly imports nothing under tools/ or
    analysis/) and item 5 (the suite runs by discovery, tests/ included)."""

    def test_the_nightly_imports_nothing_under_tools_or_analysis(self):
        import ast
        offline = {"tools", "analysis"}
        for folder in ("tools", "analysis"):
            if os.path.isdir(os.path.join(HERE, folder)):
                offline |= {f[:-3] for f in os.listdir(os.path.join(HERE, folder)) if f.endswith(".py")}
        for name in sorted(f for f in os.listdir(HERE) if f.endswith(".py")):
            with open(os.path.join(HERE, name), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module]
                for m in mods:
                    self.assertNotIn(m.split(".")[0], offline, f"{name} imports {m}")
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ("insert", "append")
                        and "path" in ast.unparse(node.func.value)):
                    self.assertNotRegex(ast.unparse(node), r"tools|analysis", f"{name}: {ast.unparse(node)}")
        y = _yml("nightly.yml")
        for line in y.splitlines():
            if "python " in line and not line.strip().startswith("#"):
                self.assertNotRegex(line, r"tools[/\\]|analysis[/\\]", line)

    def test_the_suite_runs_by_discovery_with_tests_included(self):
        self.assertIn("discover", N.TEST_ARGS)
        self.assertIn("test*.py", N.TEST_ARGS)
        suite = unittest.TestLoader().discover(HERE, pattern="test*.py", top_level_dir=HERE)

        def ids(s):
            for t in s:
                if isinstance(t, unittest.TestSuite):
                    yield from ids(t)
                else:
                    yield t.id()
        found = set(ids(suite))
        self.assertTrue(any(i.startswith("tests.test_S3.") for i in found))
        self.assertTrue(any(i.startswith("test_fpl.") for i in found))

    def test_the_nightly_runs_the_checks_last_and_a_fail_turns_it_red(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        stubs = {"test_fpl.py": "import unittest\n\n\nclass T(unittest.TestCase):\n    def test(self):\n        pass\n",
                 "fpl_sync.py": "print('sync')\n", "fpl_export_gw3.json": "{}",
                 "fpl_edge.py": "import sys\nprint('edge', sys.argv[1:])\n",
                 "checks.py": "import sys\nprint('CHECKS FAIL stub')\nsys.exit(1)\n"}
        for name, body in stubs.items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        lines = []
        code = N.nightly(root=tmp, stamp=STAMP, echo=lines.append)
        self.assertEqual(code, 1)
        self.assertLess(lines.index("archiving the export ..."), lines.index("running the checks ..."))
        self.assertIn("CHECKS FAIL stub", lines)
        self.assertTrue(lines[-1].startswith("FINISHED WITH ERRORS:") and "checks" in lines[-1], lines[-1])
        self.assertFalse(os.path.exists(os.path.join(tmp, "__pycache__")), "the suite left bytecode behind")
        self.assertIn("TESTS OK", lines)

    def test_the_nightly_says_tests_ok_only_on_a_green_suite(self):
        """Check 28 reads these lines (S3 amendment 1, point 3)."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        stubs = {"test_fpl.py": "import unittest\n\n\nclass T(unittest.TestCase):\n    def test(self):\n        self.fail('planted')\n",
                 "fpl_sync.py": "print('sync')\n", "fpl_export_gw3.json": "{}",
                 "fpl_edge.py": "import sys\nprint('edge', sys.argv[1:])\n", "checks.py": "print('checks')\n"}
        for name, body in stubs.items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        lines = []
        self.assertEqual(N.nightly(root=tmp, stamp=STAMP, echo=lines.append), 1)
        self.assertNotIn("TESTS OK", lines)
        self.assertTrue(any(l.startswith("TESTS FAILED") for l in lines))
        x = world()
        x.run_log = "\n".join(lines)
        self.assertEqual(level(x, 28), C.FAIL)
        self.assertEqual(level(x, 29), C.FAIL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
