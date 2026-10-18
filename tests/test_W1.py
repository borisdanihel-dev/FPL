"""W1 (RULING FAST-TRACK item 3): FPL's ep_next recorded nightly as source
fpl_ep (BUILD_PLAN.md Step 4 item 2), and the Odds API collector storing every
snapshot with its fetch time (Step 5 item 1, the collector only), with
ODDS_API_KEY reaching the runner under S1 amendment 1 item 1.
"""

import io
import json
import os
import secrets
import shutil
import sqlite3
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import checks as C          # noqa: E402
import fpl_edge as E        # noqa: E402
import fpl_gate as G        # noqa: E402
import fpl_nightly as N     # noqa: E402
import fpl_odds as O        # noqa: E402
import fpl_sync as S        # noqa: E402
from test_fpl import _recordable_export, _s2_element, _s2_event, UK_SUMMER   # noqa: E402

NOW = datetime(2026, 10, 18, 21, 41, tzinfo=timezone.utc)


def fake_key():
    """A key-shaped value built at run time: no key-like literal in any file."""
    return "k" + secrets.token_hex(16)


def _db():
    con = sqlite3.connect(":memory:")
    con.executescript(S.SCHEMA)
    S.migrate(con)
    return con


class FplEp(unittest.TestCase):
    """Step 4 item 2: FPL's ep_next, stored by the sync, exported, recorded as
    source fpl_ep - point-in-time like every source, the frozen four untouched."""

    def _boot(self, elements):
        db = _db()
        events = [_s2_event(7, "2026-10-17T10:00:00Z", cur=True), _s2_event(8, "2026-10-23T17:30:00Z", nxt=True)]
        saved = S.get, S.london_tz
        S.get = lambda path: {"teams": [], "elements": elements, "events": events}
        S.london_tz = lambda: UK_SUMMER
        try:
            with redirect_stdout(io.StringIO()):
                S.sync_bootstrap(db)
        finally:
            S.get, S.london_tz = saved
        return db

    def test_the_sync_stores_ep_next_as_a_number_and_a_missing_one_as_null(self):
        db = self._boot([_s2_element(1, ep_next="4.5"), _s2_element(2, ep_next=None),
                         _s2_element(3, ep_next=""), _s2_element(4)])
        got = dict(db.execute("SELECT id, ep_next FROM players"))
        self.assertEqual(got, {1: 4.5, 2: None, 3: None, 4: None})

    def test_an_old_players_table_gets_the_column_and_its_rows_keep_null(self):
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE players (id INTEGER PRIMARY KEY, web_name TEXT)")
        db.execute("INSERT INTO players VALUES (1, 'Old')")
        db.executescript(S.SCHEMA)                 # every other table, as the sync makes them
        with redirect_stdout(io.StringIO()):
            S.migrate(db)
        cols = [r[1] for r in db.execute("PRAGMA table_info(players)")]
        self.assertIn("ep_next", cols)
        self.assertEqual(db.execute("SELECT ep_next FROM players WHERE id = 1").fetchone(), (None,))

    def test_the_export_carries_ep_next(self):
        with open(os.path.join(HERE, "fpl_sync.py"), encoding="utf-8") as fh:
            src = fh.read()
        query = src.split('out["all_players"] = q(db,')[1].split("GROUP BY")[0]
        self.assertIn("pl.ep_next", query)

    def _record(self, d, source):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        log = os.path.join(tmp, "log.csv")
        with redirect_stdout(io.StringIO()):
            ok, n, why = E.record_status(d, 6, source, None, log)
        return ok, n, why, E.read_log(log)

    def test_fpl_ep_records_ep_next_for_the_next_gameweek(self):
        d = _recordable_export()
        d["all_players"][0]["ep_next"] = None
        ok, n, _, rows = self._record(d, "fpl_ep")
        want = [(str(p["id"]), str(round(float(p["ep_next"]), 3))) for p in d["all_players"]
                if p.get("ep_next") is not None]
        self.assertTrue(ok)
        self.assertEqual(n, len(want))
        self.assertEqual([(r["player_id"], r["predicted"]) for r in rows], want)
        self.assertEqual({r["source"] for r in rows}, {"fpl_ep"})
        self.assertEqual({r["event"] for r in rows}, {str(d["gameweek"] + 1)})

    def test_fpl_ep_is_refused_at_the_deadline_like_every_source(self):
        d = _recordable_export()
        passed = (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        d["events"].append({"event": d["gameweek"] + 1, "finished": 0, "data_checked": 0,
                            "deadline_time": passed})
        ok, n, why, rows = self._record(d, "fpl_ep")
        self.assertEqual((ok, n, rows), (True, 0, []))

    def test_a_missing_ep_next_is_a_skip_never_a_lost_night(self):
        """RULING W1 decisions, point 3: absent, or null for every player."""
        for how in ("absent", "null"):
            with self.subTest(how=how):
                d = _recordable_export()
                for p in d["all_players"]:
                    if how == "absent":
                        p.pop("ep_next", None)
                    else:
                        p["ep_next"] = None
                ok, n, why, rows = self._record(d, "fpl_ep")
                self.assertEqual((ok, n, rows), (E.RECORD_SKIP, 0, []))
                self.assertEqual(why, "the export has no ep_next for any player")

    def test_some_null_players_are_counted_and_the_rest_recorded(self):
        d = _recordable_export()
        for p in d["all_players"][:3]:
            p["ep_next"] = None
        ok, n, why, rows = self._record(d, "fpl_ep")
        self.assertIs(ok, True)
        self.assertEqual(n, len(d["all_players"]) - 3)
        self.assertEqual(why, "3 without ep_next")

    def test_the_cli_writes_record_skip_and_exits_zero(self):
        import subprocess
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        d = _recordable_export()
        for p in d["all_players"]:
            p.pop("ep_next", None)
        with open(os.path.join(tmp, f"fpl_export_gw{d['gameweek']}.json"), "w", encoding="utf-8") as fh:
            json.dump(d, fh)
        r = subprocess.run([sys.executable, os.path.join(HERE, "fpl_edge.py"), "--record", "--source",
                            "fpl_ep", "--status", "st.txt"], cwd=tmp, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-500:] + r.stderr[-500:])
        with open(os.path.join(tmp, "st.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "RECORD SKIP fpl_ep the export has no ep_next for any player\n")

    def test_the_frozen_four_stay_strict(self):
        d = _recordable_export()
        d["all_players"] = []
        for source in ("own", "xg", "minutes", "bottomup"):
            ok, n, why, rows = self._record(d, source)
            self.assertIs(ok, False, source)

    def test_ep_next_is_not_a_required_field(self):
        self.assertNotIn("ep_next", S.REQUIRED_ELEMENT)
        self.assertNotIn("ep_next", S.REQUIRED_EVENT)

    def test_the_frozen_four_record_the_same_with_or_without_ep_next(self):
        with_ep, without = _recordable_export(), _recordable_export()
        for p in without["all_players"]:
            p.pop("ep_next", None)
        for source in ("own", "xg", "minutes", "bottomup"):
            a = [(r["player_id"], r["predicted"]) for r in self._record(with_ep, source)[3]]
            b = [(r["player_id"], r["predicted"]) for r in self._record(without, source)[3]]
            self.assertEqual(a, b, source)
            self.assertGreater(len(a), 0, source)

    def test_the_nightly_and_the_checks_know_the_fifth_source(self):
        self.assertEqual(N.SOURCES, ("own", "xg", "minutes", "bottomup", "fpl_ep"))
        self.assertEqual(C.SOURCES, N.SOURCES)


EVENTS = [
    {"id": "e1", "commence_time": "2026-10-24T14:00:00Z", "home_team": "Arsenal",
     "away_team": "Everton", "bookmakers": [
         {"key": "bet365", "last_update": "2026-10-18T21:00:00Z", "markets": [
             {"key": "h2h", "last_update": "2026-10-18T21:00:01Z", "outcomes": [
                 {"name": "Arsenal", "price": 1.5}, {"name": "Everton", "price": 7.0},
                 {"name": "Draw", "price": 4.2}]},
             {"key": "totals", "outcomes": [
                 {"name": "Over", "price": 1.8, "point": 2.5},
                 {"name": "Under", "price": 2.0, "point": 2.5}]}]}]},
    {"id": "e2", "commence_time": "2026-10-24T16:30:00Z", "home_team": "Leeds",
     "away_team": "Burnley", "bookmakers": [
         {"key": "unibet_eu", "last_update": "2026-10-18T20:55:00Z", "markets": [
             {"key": "h2h", "outcomes": [{"name": "Leeds", "price": 2.1},
                                         {"name": "Burnley", "price": 3.6},
                                         {"name": "Draw", "price": 3.3}]}]}]}]


class Reply(io.BytesIO):
    def __init__(self, payload, headers):
        super().__init__(json.dumps(payload).encode("utf-8"))
        self.headers = headers


class OddsCollector(unittest.TestCase):
    """Step 5 item 1, the collector: every snapshot stored with its fetch time,
    the credits logged, the key never printed, logged or stored."""

    HEADERS = {"x-requests-used": "12", "x-requests-remaining": "488", "x-requests-last": "4"}

    def _opener(self, seen, payload=EVENTS, error=None):
        def opener(req, timeout=30):
            seen.append(req)
            if error is not None:
                raise error
            return Reply(payload, self.HEADERS)
        return opener

    def test_one_row_per_price_with_its_fetch_time(self):
        got = O.rows(EVENTS, "2026-10-18T21:41:00+00:00")
        self.assertEqual(len(got), 8)
        self.assertIn(("2026-10-18T21:41:00+00:00", "e1", "2026-10-24T14:00:00Z", "Arsenal", "Everton",
                       "bet365", "2026-10-18T21:00:00Z", "totals", "Over", "2.5", 1.8), got)
        self.assertIn(("2026-10-18T21:41:00+00:00", "e2", "2026-10-24T16:30:00Z", "Leeds", "Burnley",
                       "unibet_eu", "2026-10-18T20:55:00Z", "h2h", "Draw", "", 3.3), got)

    def test_the_snapshot_is_stored_and_the_credits_logged(self):
        db, seen = _db(), []
        line = O.collect(db, fake_key(), NOW, self._opener(seen))
        self.assertEqual(line, "ODDS OK      2 events (1 with totals), 8 prices fetched "
                               "2026-10-18T21:41:00+00:00; credits used 12, remaining 488, this request 4")
        self.assertEqual(db.execute("SELECT COUNT(*), MIN(fetched_at_utc), MAX(fetched_at_utc) "
                                    "FROM odds_snapshots").fetchone(),
                         (8, "2026-10-18T21:41:00+00:00", "2026-10-18T21:41:00+00:00"))
        url = seen[0].full_url
        self.assertTrue(url.startswith(O.API + "/soccer_epl/odds/?"))
        for part in ("regions=uk%2Ceu", "markets=h2h%2Ctotals", "oddsFormat=decimal"):
            self.assertIn(part, url)

    def test_a_second_night_adds_a_snapshot_and_keeps_the_first(self):
        db = _db()
        O.collect(db, fake_key(), NOW, self._opener([]))
        O.collect(db, fake_key(), NOW + timedelta(days=1), self._opener([]))
        self.assertEqual(db.execute("SELECT COUNT(DISTINCT fetched_at_utc), COUNT(*) FROM odds_snapshots").fetchone(),
                         (2, 16))

    def test_the_key_goes_to_the_api_and_nowhere_else(self):
        key, seen, db = fake_key(), [], _db()
        line = O.collect(db, key, NOW, self._opener(seen))
        self.assertIn(key, seen[0].full_url)                    # sent ...
        self.assertNotIn(key, line)                             # ... never shown
        stored = "".join(map(str, db.execute("SELECT * FROM odds_snapshots").fetchall()))
        self.assertNotIn(key, stored)
        out = io.StringIO()
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        with redirect_stdout(out):
            self.assertEqual(O.main({"ODDS_API_KEY": key}, db_path=os.path.join(tmp, "fpl.sqlite"),
                                    opener=self._opener([])), 0)
        self.assertNotIn(key, out.getvalue())

    def test_a_failure_never_shows_the_url_or_the_key(self):
        key = fake_key()
        url = O.request(key).full_url
        cases = ((urllib.error.HTTPError(url, 401, "Unauthorized " + url, {}, io.BytesIO(b"")),
                  "ODDS FAILED  HTTP 401 - no snapshot tonight"),
                 (urllib.error.URLError("no route to " + url), "ODDS FAILED  network (URLError) - no snapshot tonight"))
        for error, want in cases:
            with self.subTest(want=want):
                db = _db()
                line = O.collect(db, key, NOW, self._opener([], error=error))
                self.assertEqual(line, want)
                self.assertNotIn(key, line)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM odds_snapshots").fetchone(), (0,))

    def test_no_key_no_request(self):
        seen = []
        self.assertEqual(O.collect(_db(), "", NOW, self._opener(seen)),
                         "ODDS SKIPPED no ODDS_API_KEY in this run - no snapshot tonight")
        self.assertEqual(seen, [])

    def test_a_dry_run_calls_the_api_only_with_odds_live(self):
        """RULING W1 decisions, point 1."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        for env, calls in (({"GITHUB_REF": "refs/heads/w1-wip"}, 0),
                           ({"GITHUB_REF": "refs/heads/master", "FPL_DRY_RUN": "true"}, 0),
                           ({"GITHUB_REF": "refs/heads/w1-wip", "FPL_ODDS_LIVE": "false"}, 0),
                           ({"GITHUB_REF": "refs/heads/w1-wip", "FPL_ODDS_LIVE": "true"}, 1),
                           ({"GITHUB_REF": "refs/heads/master", "GITHUB_EVENT_NAME": "schedule"}, 1)):
            with self.subTest(env=env):
                seen, lines = [], []
                env = dict(env, ODDS_API_KEY=fake_key())
                O.main(env, say=lines.append, db_path=os.path.join(tmp, "f.sqlite"), opener=self._opener(seen))
                self.assertEqual(len(seen), calls)
                if not calls:
                    self.assertEqual(lines, ["ODDS SKIPPED (dry run): odds_live not ticked - no Odds API call"])

    def test_the_workflow_input_odds_live(self):
        with open(os.path.join(HERE, ".github", "workflows", "nightly.yml"), encoding="utf-8") as fh:
            y = fh.read()
        block = y[y.index("      odds_live:\n"):y.index("      force_backup:")]
        self.assertIn("        type: boolean\n", block)
        self.assertIn("        default: false\n", block)
        step = y[y.index("name: Nightly run"):y.index("name: Commit outputs")]
        self.assertIn("FPL_ODDS_LIVE: ${{ inputs.odds_live }}", step)

    def test_a_body_that_is_not_a_list_is_a_failure(self):
        self.assertTrue(O.collect(_db(), fake_key(), NOW, self._opener([], payload={"message": "x"}))
                        .startswith("ODDS FAILED  the answer is not a list"))

    def test_the_table_is_grow_only_and_the_gate_knows_it(self):
        self.assertIn("odds_snapshots", G.EXPECTED_TABLES)
        self.assertIn("odds_snapshots", G.GROW_ONLY)
        with open(os.path.join(HERE, "fpl_odds.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotRegex(src, r"(?i)\b(delete\s+from|drop\s+table|truncate|vacuum)\b")


class OddsCheck(unittest.TestCase):
    """Check 30 (W1): tonight's odds line; missing, skipped or failed is a WARN."""

    def _level(self, text):
        return C.c30(C.Ctx(run_log=text))

    def test_ok_skipped_failed_missing(self):
        self.assertEqual(self._level("collecting odds ...\nODDS OK      20 events (20 with totals), 1200 prices")[0], C.OK)
        self.assertEqual(self._level("ODDS SKIPPED no ODDS_API_KEY in this run")[0], C.WARN)
        self.assertEqual(self._level("ODDS FAILED  HTTP 401 - no snapshot tonight")[0], C.WARN)
        self.assertEqual(self._level("collecting odds ...\n")[0], C.WARN)
        self.assertEqual(C.NAMES[30], "odds snapshot")
        self.assertEqual(C.SEVERITY[30], C.WARN)

    def test_a_skipped_fpl_ep_is_a_warn_and_a_skipped_frozen_source_a_fail(self):
        base = ("record summary:\nRECORD OK own 5\nRECORD OK xg 5\nRECORD OK minutes 5\n"
                "RECORD OK bottomup 5\n")
        skip = base + "RECORD SKIP fpl_ep the export has no ep_next for any player\narchiving ...\n"
        self.assertEqual(C.c29(C.Ctx(run_log=skip)),
                         (C.WARN, "fpl_ep skipped: the export has no ep_next for any player; the four recorded"))
        frozen = skip.replace("RECORD OK xg 5", "RECORD SKIP xg no reason")
        self.assertEqual(C.c29(C.Ctx(run_log=frozen))[0], C.FAIL)

    def test_credits_below_60_are_a_warn(self):
        line = "ODDS OK      20 events (20 with totals), 1200 prices fetched x; credits used 441, remaining {}, this request 4"
        self.assertEqual(C.c30(C.Ctx(run_log=line.format(59)))[0], C.WARN)
        self.assertIn("credits remaining 59 (< 60)", C.c30(C.Ctx(run_log=line.format(59)))[1])
        self.assertEqual(C.c30(C.Ctx(run_log=line.format(60)))[0], C.OK)

    def test_a_missing_fpl_ep_record_fails_check_29(self):
        text = ("record summary:\nRECORD OK own 5\nRECORD OK xg 5\nRECORD OK minutes 5\n"
                "RECORD OK bottomup 5\narchiving the export ...\n")
        self.assertEqual(C.c29(C.Ctx(run_log=text)), (C.FAIL, "fpl_ep missing"))


class OddsNeverCostsTheNight(unittest.TestCase):
    """RULING W1 decisions, point 2: fpl_odds.py raising mid-run is a WARN only -
    the night is green, the data commits, the failure issue stays shut."""

    def test_a_crashing_collector_and_the_night_still_commits(self):
        import subprocess
        # the commit's identity comes from this test, never the machine (S3
        # amendment 1): fpl_publish.py's git inherits os.environ
        ident = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        saved = {k: os.environ.get(k) for k in ident}
        os.environ.update(ident)
        self.addCleanup(lambda: [os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
                                 for k, v in saved.items()])
        import fpl_alert as A
        import fpl_publish as PUB
        from test_fpl import NIGHTLY_EDGE_STUB
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        git = lambda repo, *a: subprocess.run(["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t",
                                               "-c", "core.autocrlf=false", *a], capture_output=True, text=True)
        remote, seed, data, code = (os.path.join(tmp, n) for n in ("remote.git", "seed", "data", "code"))
        subprocess.run(["git", "init", "-q", "--bare", remote], check=True)
        subprocess.run(["git", "init", "-q", seed], check=True)
        con = sqlite3.connect(os.path.join(seed, "fpl.sqlite"))
        con.executescript("CREATE TABLE price_history (player_id INTEGER, date TEXT, now_cost INTEGER);"
                          "CREATE TABLE events (id INTEGER PRIMARY KEY, deadline_time TEXT);"
                          "INSERT INTO price_history VALUES (1, '2026-10-17', 50);")
        con.commit()
        con.close()
        with open(os.path.join(seed, "projection_log.csv"), "w", encoding="utf-8", newline="") as fh:
            fh.write("made_at,source,event,player_id,web_name,predicted\n")
        with open(os.path.join(seed, ".gitignore"), "w", encoding="utf-8", newline="") as fh:
            fh.write("/fpl_export_gw*.json\nreports/record_status.tmp\n")
        git(seed, "add", "-A")
        git(seed, "commit", "-q", "-m", "first")
        git(seed, "push", "-q", remote, "HEAD:refs/heads/data")
        subprocess.run(["git", "clone", "-q", "--branch", "data", "file://" + remote.replace("\\", "/"), data],
                       check=True)
        before = git(remote, "rev-parse", "data").stdout.strip()
        os.makedirs(code)
        stubs = {"test_fpl.py": "import unittest\n\n\nclass T(unittest.TestCase):\n    def test(self):\n        pass\n",
                 "fpl_sync.py": "print('sync')\n",
                 "fpl_odds.py": "print('collecting ...')\nraise RuntimeError('planted mid-run')\n",
                 "fpl_edge.py": NIGHTLY_EDGE_STUB, "MODE": "clean",
                 "checks.py": ("import os\nos.makedirs('reports', exist_ok=True)\n"
                               "open(os.path.join('reports', 'status.txt'), 'w').write("
                               "'STATUS WARN | generated 2026-10-18T21:50:00Z | x\\n30 WARN odds snapshot: x\\n')\n")}
        for name, body in stubs.items():
            with open(os.path.join(code, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        with open(os.path.join(data, "fpl_export_gw3.json"), "w", encoding="utf-8") as fh:
            fh.write("{}")
        shutil.copy(os.path.join(code, "MODE"), os.path.join(data, "MODE"))
        lines = []
        code_rc = N.nightly(root=code, data=data, stamp="2026-10-18", echo=lines.append)
        self.assertEqual(code_rc, 0, lines[-5:])                       # never red
        self.assertIn("ODDS FAILED  fpl_odds.py exited 1 - no snapshot tonight", lines)
        x = C.Ctx(run_log="\n".join(lines))
        self.assertEqual(C.c30(x)[0], C.WARN)
        out = []
        with redirect_stdout(io.StringIO()):
            self.assertEqual(PUB.main([data], sleep=lambda s: None, say=out.append,
                                      env={}), 0)
        self.assertNotEqual(git(remote, "rev-parse", "data").stdout.strip(), before, "the night did not commit")

        class NoCalls:
            def open_issues(self):
                return []

            def call(self, *a):
                raise AssertionError("a green night touched the issue API")
        said = []
        A.main([data], env={"RUN_OUTCOMES": "nightly=success publish=success backup=skipped",
                            "GITHUB_REPOSITORY": "o/r"}, say=said.append, gh=NoCalls())
        self.assertEqual(said, ["ALERT none: the run is green and no issue is open"])


class NightlyOrder(unittest.TestCase):
    """The odds step runs after the sync and before the record; the suite runs
    without the odds key and the token, the collector with the key."""

    def test_the_odds_step_has_the_key_and_the_suite_does_not(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        stubs = {
            "test_fpl.py": ("import os, unittest\n\n\nclass T(unittest.TestCase):\n"
                            "    def test_no_secret(self):\n"
                            "        for k in ('ODDS_API_KEY', 'GH_TOKEN', 'GITHUB_TOKEN'):\n"
                            "            self.assertNotIn(k, os.environ)\n"),
            "fpl_sync.py": "print('sync')\n", "fpl_export_gw3.json": "{}",
            "fpl_odds.py": "import os\nprint('ODDS OK stub key' if os.environ.get('ODDS_API_KEY') else 'ODDS SKIPPED stub')\n",
            "fpl_edge.py": "import sys\nprint('edge', sys.argv[1:])\n", "checks.py": "print('checks')\n"}
        for name, body in stubs.items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        saved = {k: os.environ.get(k) for k in ("ODDS_API_KEY", "GH_TOKEN", "GITHUB_TOKEN")}
        os.environ.update(ODDS_API_KEY=fake_key(), GH_TOKEN="t" + secrets.token_hex(8),
                          GITHUB_TOKEN="t" + secrets.token_hex(8))
        lines = []
        try:
            N.nightly(root=tmp, stamp="2026-10-18", echo=lines.append)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        self.assertIn("TESTS OK", lines)
        self.assertIn("ODDS OK stub key", lines)
        order = [lines.index(x) for x in ("syncing FPL API ...", "collecting odds ...",
                                          "recording forecasts for next GW ...")]
        self.assertEqual(order, sorted(order))


if __name__ == "__main__":
    unittest.main(verbosity=2)
