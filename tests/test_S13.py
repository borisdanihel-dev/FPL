"""S13 - P(DEFCON) v2 (tools/defcon.py). Hermetic: the toy season of the
S4/S5 tests in a temporary folder; no network, no C:\\GIT\\FPL-data."""
import io
import math
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import defcon as D                                                # noqa: E402
from tests.test_S4 import plant_transfer, TEAMS                   # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402


def poisson_tail(mu, k):
    return 1.0 - sum(math.exp(-mu) * mu ** x / math.factorial(x) for x in range(k))


class Maths(unittest.TestCase):
    def test_nb_tail_against_hand_sums_and_the_poisson_limit(self):
        self.assertAlmostEqual(D.nb_tail(2.0, 1.0, 3), (2 / 3) ** 3)              # r = 1 is geometric: P(X >= k) = (mu / (1 + mu))^k
        mu, r = 1.5, 2.0
        p0 = (r / (r + mu)) ** r
        p1 = r * (r / (r + mu)) ** r * (mu / (r + mu))
        self.assertAlmostEqual(D.nb_tail(mu, r, 2), 1 - p0 - p1)
        self.assertAlmostEqual(D.nb_tail(3.0, None, 4), poisson_tail(3.0, 4))     # the Poisson limit
        self.assertAlmostEqual(D.nb_tail(3.0, 1e6, 4), poisson_tail(3.0, 4), places=4)
        self.assertGreater(abs(D.nb_tail(3.0, 1.0, 4) - poisson_tail(3.0, 4)), 0.02)   # r = 1 is not Poisson
        self.assertEqual(D.nb_tail(3.0, 2.0, 0), 1.0)
        self.assertEqual(D.nb_tail(0.0, 2.0, 1), 0.0)
        self.assertLess(D.nb_tail(8.0, 5.0, 10), D.nb_tail(9.0, 5.0, 10))           # a larger mean raises P
        self.assertAlmostEqual(sum(math.exp(D.nb_logpmf(2.5, 3.0, x)) for x in range(200)), 1.0)

    def test_dispersion_by_moments_with_the_clip_and_the_poisson_limit(self):
        self.assertAlmostEqual(D.fit_dispersion([(0, 2.0), (4, 2.0)]), 2.0)        # 8 / (8 - 4)
        self.assertEqual(D.fit_dispersion([(0, 1.0), (100, 1.0)]), D.R_LO)          # 2 / 9800 -> clipped up
        self.assertEqual(D.fit_dispersion([(90, 100.5), (111, 100.5)]), D.R_HI)     # 20200.5 / 19.5 -> clipped down
        self.assertIsNone(D.fit_dispersion([(2, 2.0), (2, 2.0)]))                   # variance below the mean: Poisson
        self.assertIsNone(D.fit_dispersion([(0, 1.0), (2, 1.0), (0, 1.0), (2, 1.0)]))   # variance equal to the mean: Poisson
        with self.assertRaises(D.MissingInput):
            D.fit_dispersion([])
        self.assertEqual((D.R_LO, D.R_HI), (0.5, 1000.0))

    def test_scores_and_calibration_on_hand_cases(self):
        rows = [{"pid": 1, "p": 0.0, "hit": 1}, {"pid": 2, "p": 1.0, "hit": 1}]
        self.assertAlmostEqual(D.brier(rows, "p"), 0.5)
        self.assertAlmostEqual(D.logloss(rows, "p"), (-math.log(D.EPS) - math.log(1 - D.EPS)) / 2)   # the comparator's 0 against a hit is clipped, never infinite
        rows = []
        for i in range(10):
            p = 0.05 + 0.1 * i
            hits = (1, 0) if i in (4, 5) else ((1, 1) if i == 9 else (0, 0))
            rows += [{"pid": 2 * i, "p": p, "hit": hits[0]}, {"pid": 2 * i + 1, "p": p, "hit": hits[1]}]
        cal = D.calibration(rows, "p")
        self.assertEqual([n for n, _, _ in cal], [2] * 10)
        self.assertAlmostEqual(cal[4][1], 0.45); self.assertAlmostEqual(cal[4][2], 0.5)
        self.assertAlmostEqual(cal[9][1], 0.95); self.assertAlmostEqual(cal[9][2], 1.0)
        self.assertEqual(D.within(cal), 4)                                          # deciles 1 (0.05 v 0), 5, 6 (0.45 / 0.55 v 0.5) and 10 (0.95 v 1)
        self.assertEqual(D.within(cal, tol=0.0), 0)
        self.assertEqual((D.DECILES, D.CAL_TOL, D.CAL_MIN, D.PASS_BRIER, D.MIN_MINUTES), (10, 0.05, 8, 0.005, 60))


class Season(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.odds = toy_season(cls.tmp.name, skip_fixture=13)                         # one round-5 fixture on the fallback

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_thresholds_sample_and_the_opponent_factor(self):
        self.assertEqual(D.THRESHOLDS, {2: 10, 3: 12, 4: 12})
        self.assertIs(D.COMPARATOR, E.DEFCON_THRESHOLD)
        self.assertEqual(D.COMPARATOR, {2: 10, 3: 12})
        s = D.Season(self.tmp.name, self.odds)
        o = s.origin(5)
        c5 = BT.canonical_at(s.hist, 5)
        want = [int(r["element"]) for r in s.hist["raw"][5]
                if float(r["minutes"]) >= 60 and c5["players"][int(r["element"])]["pos"] in D.THRESHOLDS]
        self.assertEqual(sorted(r["pid"] for r in o["rows"]), sorted(want))
        self.assertTrue(all(c5["players"][r["pid"]]["pos"] != 1 for r in o["rows"]))   # no keepers
        self.assertTrue(any(r["pos"] == 4 for r in o["rows"]))                      # forwards are in v2 ...
        self.assertTrue(all(r["p_cmp"] == 0.0 for r in o["rows"] if r["pos"] == 4))  # ... and 0 for the comparator
        self.assertTrue(any(r["source"] == "fallback" for r in o["rows"]))
        self.assertTrue(any(r["source"] == "odds" for r in o["rows"]))
        # the factor averages 1 over the round's team-fixtures and is larger against the stronger attack
        facs = []
        for fid, f in s.fixtures.items():
            if f["event"] == 5:
                fh, _ = D.opponent_factor(s.s, fid, f["home"])
                fa, _ = D.opponent_factor(s.s, fid, f["away"])
                lam, _ = s.s.lambdas(5)[fid]
                self.assertEqual(fh > fa, lam["lambda_away"] > lam["lambda_home"])
                facs += [fh, fa]
        self.assertAlmostEqual(sum(facs) / len(facs), 1.0)
        self.assertGreater(max(facs), 1.05); self.assertLess(min(facs), 0.95)        # the factor varies across the round
        # the 60-minute edge: a 59-minute row is out, a 60-minute row is in (the toy has only 90 / 0 / 15 / 30)
        s59 = D.Season(self.tmp.name, self.odds)
        edge = [r for r in s59.hist["raw"][5] if float(r["minutes"]) == 90 and c5["players"][int(r["element"])]["pos"] == 2][:2]
        edge[0]["minutes"] = "59"; edge[1]["minutes"] = "60"
        pids = [r["pid"] for r in s59.origin(5)["rows"]]
        self.assertNotIn(int(edge[0]["element"]), pids); self.assertIn(int(edge[1]["element"]), pids)
        # mu = shrunk rate x factor; P rises with the factor at a fixed rate
        inp = E.reliability_inputs(E.canonical_through(c5, 4), gws_played=4)
        for r in o["rows"]:
            self.assertAlmostEqual(r["mu"], D.shrunk_rate90(inp, inp["players"][r["pid"]]) * r["factor"])
            self.assertAlmostEqual(r["p_v2"], D.nb_tail(r["mu"], o["r"][r["pos"]], D.THRESHOLDS[r["pos"]]))
            self.assertEqual(r["hit"], 1 if r["x"] >= D.THRESHOLDS[r["pos"]] else 0)
        for pos in D.THRESHOLDS:
            self.assertGreater(o["n_train"][pos], 0)
            if o["r"][pos] is not None:
                self.assertTrue(D.R_LO <= o["r"][pos] <= D.R_HI)
        # the shrink, by hand: own x w + prior x (1 - w); the prior alone without a rate
        toy = {"priors": {(2, "defcon90"): 8.0}, "weights": {"defcon": 0.25}}
        self.assertAlmostEqual(D.shrunk_rate90(toy, {"pos": 2, "defcon90": 12.0}), 9.0)
        self.assertAlmostEqual(D.shrunk_rate90(toy, {"pos": 2, "defcon90": None}), 8.0)
        # the shrink: the rate sits between the player's own and the positional prior
        for pid, p in inp["players"].items():
            if p["defcon90"] is not None and p["pos"] in D.THRESHOLDS:
                lo, hi = sorted((p["defcon90"], inp["priors"][(p["pos"], "defcon90")]))
                self.assertTrue(lo - 1e-9 <= D.shrunk_rate90(inp, p) <= hi + 1e-9)

    def test_comparator_reproduces_defcon_expectation(self):
        s = D.Season(self.tmp.name, self.odds)
        o = s.origin(5)
        c5 = BT.canonical_at(s.hist, 5)
        recent = []
        for g in range(1, 5):
            for r in s.hist["raw"][g]:
                pid = int(r["element"])
                recent.append({"web_name": f"P{pid}", "event": g, "mins": float(r["minutes"]),
                               "defcon": int(float(r["defensive_contribution"])), "pos": c5["players"][pid]["pos"]})
        want = E.defcon_expectation({"player_gw_recent": recent})
        checked = 0
        for r in o["rows"]:
            self.assertAlmostEqual(2 * r["p_cmp"], want.get(f"P{r['pid']}", 0.0))
            checked += 1
        self.assertGreater(checked, 10)
        self.assertTrue(any(0 < r["p_cmp"] < 1 for r in o["rows"]))
        self.assertEqual(D.comparator_rate([10, 9, 12], 2), 2 / 3)
        self.assertEqual(D.comparator_rate([12, 9], 3), 0.5)
        self.assertEqual(D.comparator_rate([20, 20], 4), 0.0)                        # forwards: no threshold in the current code
        self.assertEqual(D.comparator_rate([], 2), 0.0)                              # no 60+ match: 0, as the code does

    def test_point_in_time(self):
        s = D.Season(self.tmp.name, self.odds)
        o = s.origin(5)
        key = lambda o: [(r["pid"], round(r["p_v2"], 12), round(r["p_cmp"], 12), round(r["factor"], 12)) for r in o["rows"]]
        # rows of rounds > 5, results of rounds >= 5 and odds from round 6 on altered: origin 5 unchanged
        s2 = D.Season(self.tmp.name, self.odds)
        for g in range(6, s2.hist["through"] + 1):
            for r in s2.hist["raw"][g]:
                r["minutes"] = "90"; r["defensive_contribution"] = "99"
        for r in s2.hist["c"]["rows"]:
            if r["event"] >= 5:
                r["defcon"] = 99; r["minutes"] = 90; r["pts"] = 50
        for f in s2.fixtures.values():
            if f["event"] >= 5:
                f["hg"], f["ag"] = 9, 9
        for k, r in s2.s.book.by_key.items():
            if k[0] >= date(2025, 8, 20):
                r["odds"] = {kk: v * 3 for kk, v in r["odds"].items()}
        o2 = s2.origin(5)
        self.assertEqual(key(o2), key(o)); self.assertEqual(o2["r"], o["r"])
        # the outcomes of round 5 itself move the hits only, never a probability or r
        s3 = D.Season(self.tmp.name, self.odds)
        for r in s3.hist["raw"][5]:
            r["defensive_contribution"] = "99"
        o3 = s3.origin(5)
        self.assertEqual(key(o3), key(o)); self.assertEqual(o3["r"], o["r"])
        self.assertTrue(all(r["hit"] == 1 for r in o3["rows"]))
        self.assertFalse(all(r["hit"] == 1 for r in o["rows"]))
        # the test runs on the toy and reports both bars
        buf = io.StringIO()
        res = D.test_2526(self.tmp.name, out=lambda t: buf.write(t + chr(10)), first=5, last=6, odds_file=self.odds)
        self.assertEqual([r["gw"] for r in res["per"]], [5, 6])
        self.assertIn("pre-registered result", buf.getvalue())
        self.assertIn("(b) calibration", buf.getvalue())
        self.assertEqual(res["pass"], res["boot"]["mean"] >= 0.005 and res["boot"]["lo"] > 0 and res["within"] >= 8)
        with self.assertRaises(D.MissingInput):
            s.origin(1)
        # a transfer planted after t: the club of the origin agrees with the row; the end-of-season club would not
        with tempfile.TemporaryDirectory() as tmp:
            odds = toy_season(tmp)
            plant_transfer(tmp, 3, 6, 2)
            s4 = D.Season(tmp, odds)
            self.assertEqual(s4.hist["c"]["players"][3]["team"], TEAMS[1][1])      # the adapter's end-of-season club
            self.assertEqual(BT.canonical_at(s4.hist, 5)["players"][3]["team"], TEAMS[0][1])
            o4 = s4.origin(5)
            self.assertIn(3, [r["pid"] for r in o4["rows"]] + [None])              # runs; player 3's round-5 row is at his old club
            s4.hist["c"]["players"][3]["team"] = TEAMS[1][1]
            s4.hist["cm"]["by_gw"][5][3] = TEAMS[1][1]                             # a wrong club map for round 5
            with self.assertRaises(D.MissingInput):
                s4.origin(5)


class CLI(unittest.TestCase):
    def test_cli_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            odds = toy_season(tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = D.main(["--test", "--hist", tmp, "--odds", odds, "--out", out, "--last", "6"])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "defcon_test_2025-26.txt"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("pre-registered result", text)
            self.assertIn("thresholds DEF 10 CBIT, MID 12 CBIRT", text)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(D.main(["--hist", tmp]), 2)                        # nothing asked: help, refused
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'defcon')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
