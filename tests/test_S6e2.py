"""S6e2 - xp_v2 + the discretised save points, on 2024/25 (tools/xp_v2_saves2.py;
prereg/S6e2.md, RULING 19 Oct evening point 2). Hermetic: S6e's toy season
(S6b's toy with saves) laid out as a 2024-25 / 2023-24 history root in a
temporary folder; no network, no real data."""
import io
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_saves as SV                                          # noqa: E402
import xp_v2_saves2 as T                                          # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402
from tests.test_S6b import toy_rules_root                         # noqa: E402
from tests.test_S6e import add_saves                              # noqa: E402
from tests.test_S6f import zero_counts                            # noqa: E402


def direct(mu, per=3, n=400):
    """E[floor(S/per)] by the direct sum over k of floor(k/per) P(S = k)."""
    if mu <= 0:
        return 0.0
    return sum((k // per) * math.exp(-mu + k * math.log(mu) - math.lgamma(k + 1)) for k in range(n))


class ByHand(unittest.TestCase):
    def test_floor_points(self):
        self.assertEqual(T.floor_points(0.0), 0.0); self.assertEqual(T.floor_points(-1.0), 0.0)
        mu = 1.2
        p0, p1, p2 = math.exp(-mu), mu * math.exp(-mu), mu * mu / 2 * math.exp(-mu)
        self.assertAlmostEqual(T.floor_points(mu), direct(mu), places=13)
        self.assertGreater(T.floor_points(mu), 1 - (p0 + p1 + p2))                       # P(S >= 3) and more
        for mu in (0.3, 2.0, 3.0, 4.7, 9.0, 25.0, 60.0):
            self.assertAlmostEqual(T.floor_points(mu), direct(mu), places=11)
            self.assertLess(T.floor_points(mu), mu / 3)                                   # the floor: below E[S]/3
            self.assertGreater(T.floor_points(mu), mu / 3 - 1)                            # and within one point of it
        self.assertAlmostEqual(T.floor_points(5.0, per=1), 5.0, places=10)               # per 1: the mean itself


class Toy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.rules = tempfile.mkdtemp(), tempfile.mkdtemp()
        cls.hist, cls.prior = os.path.join(cls.root, "2024-25"), os.path.join(cls.root, "2023-24")
        os.makedirs(cls.hist); os.makedirs(cls.prior)
        cls.odds = toy_season(cls.hist, skip_fixture=13)
        toy_prior(cls.prior)
        for folder in (cls.hist, cls.prior):
            add_saves(folder)
        toy_rules_root(cls.rules, cls.hist)
        cls.rescored = XR.rescore(cls.rules, os.path.join(cls.rules, "rescored.csv"))
        zero_counts(cls.hist)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True); shutil.rmtree(cls.rules, ignore_errors=True)

    def run_tool(self, **kw):
        lines = []
        with mock.patch.object(T.F, "rescore", return_value=self.rescored):
            res = T.run(self.root, lines.append, odds_file=self.odds, out_csv=os.path.join(self.root, "r.csv"), first=5, last=6,
                        n_squads=3, **kw)
        return res, lines

    def test_only_the_keeper_term_changes(self):
        s6e, s2 = SV.Season(self.hist, self.prior, self.odds), T.Season2(self.hist, self.prior, self.odds)
        self.assertEqual(s2.k, s6e.k)                                                     # k: S6e's rule on the prior folder
        for t in (5, 6):
            xp, plus, es, p_start, pos = s6e.forecasts(t)
            xp2, plus2, es2, p_start2, pos2 = s2.forecasts(t)
            self.assertEqual((xp2, es2, p_start2, pos2), (xp, es, p_start, pos))         # xp_v2 and E[saves] are S6e's
            rp = s2.rp
            c = __import__("backtest").canonical_at(rp.hist, t)
            inp = __import__("fpl_edge").reliability_inputs(__import__("fpl_edge").canonical_through(c, t - 1), gws_played=t - 1)
            lams = [v for l, _ in rp.s5.lambdas(t).values() for v in (l["lambda_home"], l["lambda_away"])]
            lam_bar = sum(lams) / len(lams)
            rates, mean90 = SV.keeper_rates(rp.by_round, t)
            starts = [a[3] / a[2] for a in rates.values() if a[2]]
            pms = sum(starts) / len(starts)
            for pid in xp:
                if pos[pid] != 1:
                    self.assertEqual(plus2[pid], xp[pid])
                    continue
                fx = rp.s11.club_fixtures(inp["players"][pid]["team"], t)
                mus = [SV.expected_saves(rates.get(pid), mean90, s2.k, [rp.s5.lam_opp(fid, inp["players"][pid]["team"])[0]], lam_bar, pms)
                       for fid, _ in fx]
                self.assertAlmostEqual(sum(mus), es[pid])
                self.assertAlmostEqual(plus2[pid], xp[pid] + p_start[pid] * sum(direct(m) for m in mus), places=10)
                self.assertLess(plus2[pid], plus[pid] + 1e-12)                            # below S6e's E[S]/3 term
        self.assertTrue(s2.sizes and all(b < a for a, b in s2.sizes if a > 0))

    def test_a_double_gameweek_sums_two_floors(self):
        s2 = T.Season2(self.hist, self.prior, self.odds)
        with mock.patch.object(T.SV, "expected_saves", side_effect=lambda a, m, k, fx, lb, pms: 2.0 * len(fx)):
            fake = {"p_start": 1.0, "fixtures": [{"lam_opp": 1.0}, {"lam_opp": 1.0}]}
            with mock.patch.object(T.XL, "core", side_effect=lambda *a, **k: ({1: 3.0}, {1: fake})):
                with mock.patch.object(T.E, "reliability_inputs", return_value={"players": {1: {"pos": 1, "p_start": 1.0}}}):
                    _, plus, es, _, _ = s2.forecasts(5)
        self.assertAlmostEqual(es[1], 4.0)
        self.assertAlmostEqual(plus[1], 3.0 + 2 * direct(2.0), places=10)                  # two floors, not one floor of 4
        self.assertNotAlmostEqual(plus[1], 3.0 + direct(4.0), places=3)

    def test_the_run_is_s6e_loop_and_the_bar(self):
        res, lines = self.run_tool()
        with T.discretised():
            want = SV.test_2526(self.hist, self.prior, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=3,
                                rescored=self.rescored)
        for key in ("per", "boot", "mae", "pass", "k"):
            self.assertEqual(res[key], want[key], key)
        plain = SV.test_2526(self.hist, self.prior, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=3,
                             rescored=self.rescored)
        self.assertEqual([r["base"] for r in res["per"]], [r["base"] for r in plain["per"]])   # the xp_v2 side is S6e's
        self.assertIs(SV.Season, SV.Season.__mro__[0]); self.assertIsNot(SV.Season, T.Season2)  # restored after the run
        self.assertTrue(lines[0].startswith("S6E2 TEST  2024/25 GW5-6")); self.assertIn("2023/24 split-half", lines[0])
        self.assertIn("E[floor(S/3)]", lines[0])
        for lo, word in ((0.01, "PASS"), (0.0, "FAIL"), (-0.3, "FAIL")):
            with mock.patch.object(SV.BT, "bootstrap_mean", return_value={"mean": 0.1, "lo": lo, "hi": 0.4, "n": 2, "p": 0.2}):
                r2, l2 = self.run_tool()
            self.assertEqual(r2["pass"], lo > 0); self.assertIn(word, l2[-1])
        with self.assertRaises(RuntimeError):
            with T.discretised():
                raise RuntimeError("boom")
        self.assertIsNot(SV.Season, T.Season2)
        with mock.patch.object(T.F, "season_names", wraps=T.F.season_names) as names:
            self.run_tool()
        names.assert_called_once_with("2024-25")                                           # S6f's harness: the 2024/25 names
        with mock.patch.object(T.F, "check_no_counts", side_effect=T.F.MissingInput("counts")), self.assertRaises(XR.MissingInput):
            self.run_tool()                                                                   # DEFCON refused as in S6f

    def test_cli_and_isolation(self):
        out = tempfile.mkdtemp()
        try:
            with mock.patch.object(T.F, "rescore", return_value=self.rescored), redirect_stdout(io.StringIO()):
                rc = T.main(["--test", "--hist", self.root, "--odds", self.odds, "--out", out])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(out, "s6e2_2024-25.txt")))
            with open(os.path.join(out, "run.txt"), encoding="utf-8") as fh:
                self.assertIn("tools/xp_v2_saves2.py", fh.read())
            with redirect_stdout(io.StringIO()):
                self.assertEqual(T.main(["--test", "--hist", os.path.join(out, "none"), "--out", out]), 2)
        finally:
            shutil.rmtree(out, ignore_errors=True)
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m in sys.modules if m.split('.')[0] in ('xp_v2_saves2', 'xp_v2_saves', 'xp_v2_2425')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
