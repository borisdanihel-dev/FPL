"""tests/test_runcommit.py - runcommit (prereg/runcommit.md): real and dry runs record their code commit in the log,
the status header and (real runs) the data commit message; the addendum's price-moves fix (players matched by id) and
the calibration RMSE columns (report only). Hermetic: temporary folders only, the environment passed explicitly."""
import io
import os
import re
import sys
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import checks as C                                                # noqa: E402
import fpl_edge as E                                              # noqa: E402
import fpl_nightly as N                                           # noqa: E402
import test_fpl as TF                                             # noqa: E402

SHA = "0123456789abcdef0123456789abcdef01234567"

# Publish's world (a bare remote and a runner clone) without its own tests, which test_fpl runs
PublishWorld = type("PublishWorld", (unittest.TestCase,),
                    {k: v for k, v in vars(TF.Publish).items() if not k.startswith("test") and k not in ("__dict__", "__weakref__")})


class LogLine(unittest.TestCase):
    """The run header of logs/run_<date>.log names the code commit, after `using:`."""

    def _log(self, env):
        tmp = TF.NightlyRunner._world(self)
        real_ship, real_backup = TF.SHIP.ship, TF.SHIP.backup_db
        TF.SHIP.ship = lambda *a, **k: 0
        TF.SHIP.backup_db = lambda *a, **k: ("", [])
        try:
            with mock.patch.dict(os.environ, env, clear=False):
                if "GITHUB_SHA" not in env:
                    os.environ.pop("GITHUB_SHA", None)
                code, log, _ = TF.NightlyRunner._run(self, tmp)
        finally:
            TF.SHIP.ship, TF.SHIP.backup_db = real_ship, real_backup
        return log

    _get = staticmethod(TF.NightlyRunner._get)
    _put = staticmethod(TF.NightlyRunner._put)
    STAMP = TF.NightlyRunner.STAMP

    def test_with_github_sha(self):
        log = self._log({"GITHUB_SHA": SHA})
        i = next(k for k, s in enumerate(log) if s.startswith("using: "))
        self.assertEqual(log[i + 1], "code commit: 0123456")

    def test_without_github_sha_no_substitute(self):
        log = self._log({})
        i = next(k for k, s in enumerate(log) if s.startswith("using: "))
        self.assertEqual(log[i + 1], "code commit: unknown (no GITHUB_SHA)")


class StatusField(unittest.TestCase):
    """The last field of the status line; status_time and the publisher's STATUS FAIL test read the longer line."""

    def test_the_field_and_its_absence(self):
        res = C.run_all(TF_world())
        now = datetime(2026, 10, 18, 21, 50, tzinfo=timezone.utc)
        line = C.status_line(res, now, None, 120 * 1024, timezone.utc, code=C.code_commit({"GITHUB_SHA": SHA}))
        self.assertTrue(line.endswith(" | repo 120 MB | code 0123456"), line)
        self.assertTrue(C.status_line(res, now, None, 120 * 1024, timezone.utc).endswith(" | code ?"))
        self.assertEqual(C.status_time(line + "\n"), now)

    def test_the_commit_comes_from_github_sha_only(self):
        self.assertEqual(C.code_commit({"GITHUB_SHA": SHA}), "0123456")
        for env in ({}, {"GITHUB_SHA": ""}, {"GIT_COMMIT": SHA, "GITHUB_REF_NAME": "master"}, None):
            self.assertIsNone(C.code_commit(env), env)

    def test_the_publisher_still_sees_a_failed_night(self):
        import fpl_publish as PUB
        import tempfile
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "reports"))
            with open(os.path.join(tmp, "reports", "status.txt"), "w", encoding="utf-8", newline="\n") as fh:
                fh.write("STATUS FAIL | generated 2026-10-18T21:50:00Z | next deadline none | checks 1/2 | repo ? MB | code 0123456\n")
            self.assertTrue(PUB.checks_failed(tmp, "real"))
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)


def TF_world():
    from tests.test_S3 import world
    return world()


class CommitMessage(PublishWorld):
    """A real run's data commit message carries the code commit; without GITHUB_SHA the field is left out."""

    def test_a_real_run_names_its_commit(self):
        code, out = self._publish({"GITHUB_SHA": SHA})
        self.assertEqual(code, 0, out)
        msg = self._git(self.remote, "log", "-1", "--format=%s", "data").stdout.strip()
        self.assertRegex(msg, r"^nightly \d{4}-\d{2}-\d{2} 0123456 \[skip ci\]$")

    def test_without_github_sha_the_field_is_left_out(self):
        code, out = self._publish({})
        self.assertEqual(code, 0, out)
        msg = self._git(self.remote, "log", "-1", "--format=%s", "data").stdout.strip()
        self.assertRegex(msg, r"^nightly \d{4}-\d{2}-\d{2} \[skip ci\]$")


class PriceMovesById(unittest.TestCase):
    """Two players named Thomas at two clubs: ours did not move, the other did and is newly flagged. The diff matches
    players by id (Coventry's Thomas showed Hull's price move)."""

    def setUp(self):
        import copy
        prev = TF.make_export()
        me = E.my_name(prev)
        ours = [r for r in prev["squads"] if r["entry_name"] == me]
        owned = {(r["web_name"], r["team"]) for r in prev["squads"]}
        mine = next(p for p in prev["all_players"] if (p["web_name"], p["team"]) == (ours[3]["web_name"], ours[3]["team"]))
        other = next(p for p in prev["all_players"] if (p["web_name"], p["team"]) not in owned
                     and p["team"] != mine["team"] and p["status"] == "a")
        for ex in (prev,):
            for r in ex["squads"]:
                if (r["web_name"], r["team"]) == (mine["web_name"], mine["team"]):
                    r["web_name"] = "Thomas"
        mine["web_name"] = other["web_name"] = "Thomas"
        prev["all_players"].remove(other)
        prev["all_players"].insert(0, other)                 # the other Thomas first: a name match finds him
        by = {(p["web_name"], p["team"]): p["id"] for p in prev["all_players"]}
        for r in prev["squads"]:
            r["player_id"] = by[(r["web_name"], r["team"])]
        d = copy.deepcopy(prev)
        o = next(p for p in d["all_players"] if p["id"] == other["id"])
        o["price"] = round(o["price"] - 1.5, 1)
        o["status"], o["chance_next_round"], o["news"] = "d", 50, "Calf injury - 50% chance of playing"
        self.d, self.prev, self.mine, self.other = d, prev, mine, other

    def _blocks(self, d=None):
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_diff(d or self.d, self.prev, 6)
        text = buf.getvalue()
        block = lambda head: text.split(head)[1].split("\n\n")[0].strip("\n").splitlines()
        return text, block

    def test_our_price_moves_follow_the_id(self):
        _, block = self._blocks()
        self.assertEqual([s.strip() for s in block("YOUR SQUAD: price moves")], ["none"])

    def test_new_flags_follow_the_id(self):
        _, block = self._blocks()
        self.assertEqual([s.strip() for s in block("NEW FLAGS (owned by anyone in the league)")], ["none"])

    def test_our_own_move_still_shows(self):
        import copy
        d = copy.deepcopy(self.d)
        m = next(p for p in d["all_players"] if p["id"] == self.mine["id"])
        m["price"] = round(m["price"] + 0.1, 1)
        _, block = self._blocks(d)
        rows = block("YOUR SQUAD: price moves")
        self.assertEqual(len(rows), 1)
        self.assertIn(f"Thomas         {self.mine['team']:5s}", rows[0])

    def test_squads_without_player_id_is_one_line(self):
        import copy
        d = copy.deepcopy(self.d)
        for r in d["squads"]:
            r.pop("player_id", None)
        text, _ = self._blocks(d)
        self.assertIn("not comparable: squads rows without player_id", text)
        self.assertNotIn("YOUR SQUAD: price moves", text)


class CalibrationRmse(unittest.TestCase):
    """RMSE and RMSE against the constant beside MAE; report only - the verdicts are unchanged."""

    def test_the_formulas(self):
        pairs = [(2.0, 0.0), (1.0, 4.0), (3.0, 3.0)]
        rmse, rconst = E._rmse(pairs, 7.0 / 3)
        self.assertAlmostEqual(rmse, ((4 + 9 + 0) / 3) ** 0.5)
        self.assertAlmostEqual(rconst, (((7 / 3) ** 2 + (5 / 3) ** 2 + (2 / 3) ** 2) / 3) ** 0.5)

    def test_the_columns_and_the_unchanged_verdicts(self):
        d, gw, log = TF._graded_world()
        out = TF._calibration(d, log)
        self.assertRegex(out, r"(?m)^  source\s+GW\s+n\s+MAE\s+const\s+RMSE\s+rconst\s+rho\s+starters\s+n_st\s+bias\s+verdict$")
        row = re.search(r"(?m)^  xg\s+\d+\s+\d+\s+(\d+\.\d{2})\s+(\d+\.\d{2})\s+(\d+\.\d{2})\s+(\d+\.\d{2})\s+.*\s{3}(beats const|loses)$", out)
        self.assertIsNotNone(row, out)
        mae, const, rmse, rconst = (float(row.group(k)) for k in (1, 2, 3, 4))
        self.assertGreaterEqual(rmse + 0.005, mae)                          # RMSE >= MAE, always
        self.assertGreaterEqual(rconst + 0.005, const)
        self.assertEqual(row.group(5), "beats const" if mae < const else "loses")   # the verdict still reads MAE
        self.assertRegex(out, r"XG over 1 gameweek\(s\), \d+ forecasts\n    MAE \d\.\d{3} vs constant \d\.\d{3}   "
                              r"RMSE \d\.\d{3} vs constant \d\.\d{3}   rho ")

    def test_the_verdict_reads_mae_where_rmse_disagrees(self):
        d, gw, log = TF._graded_world()
        pairs = [(float(i % 5), float(i % 5), False) for i in range(40)]
        pairs[7] = (pairs[7][1] + 40.0, pairs[7][1], False)             # exact but one large miss
        with mock.patch.object(E, "grade_forecasts", return_value=({("xg", gw): pairs}, {})):
            out = TF._calibration(d, log)
        row = re.search(r"(?m)^  xg\s+\d+\s+40\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+.*\s{3}(beats const|loses)$", out)
        self.assertIsNotNone(row, out)
        self.assertEqual([row.group(k) for k in (1, 2, 3, 4)], ["1.00", "1.20", "6.32", "1.41"])
        self.assertEqual(row.group(5), "beats const")                    # MAE beats the constant; RMSE would lose


if __name__ == "__main__":
    unittest.main()
