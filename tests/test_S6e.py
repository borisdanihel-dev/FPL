"""S6e - xp_v2 + saves (tools/xp_v2_saves.py; prereg/S6e.md). Hermetic:
S6b's toy season and Step 10 root in temporary folders; no network."""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_saves as SV                                          # noqa: E402
import provenance as PV                                           # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402
from tests.test_S6b import toy_rules_root                         # noqa: E402


def gk(el, rnd, mins, saves, starts=1):
    return {"element": el, "round": rnd, "position": "GK", "minutes": mins, "saves": saves, "starts": starts}


def add_saves(folder):
    """The toy merged_gw gains a saves column: a keeper who played saves
    element mod 5 + 1 (+1 in odd rounds), everyone else 0."""
    import csv
    p = os.path.join(folder, "merged_gw.csv")
    with open(p, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["saves"] = str(int(r["element"]) % 5 + 1 + int(r["round"]) % 2 if r["position"] == "GK" and float(r["minutes"]) > 0 else 0)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


class ByHand(unittest.TestCase):
    def test_expected_saves_and_k(self):
        by_round = {1: [gk(1, 1, 90, 6), gk(2, 1, 90, 2), {"element": 9, "round": 1, "position": "DEF", "minutes": 90, "saves": 9}],
                    2: [gk(1, 2, 45, 3, starts=0)], 3: [gk(1, 3, 90, 99)]}
        rates, mean90 = SV.keeper_rates(by_round, 3)
        self.assertEqual(rates[1], [9.0, 135.0, 1, 90.0])                                  # round 3 unseen; a DEF never counted
        self.assertAlmostEqual(mean90, (9 + 2) / (135 + 90) * 90)
        k = 2.0
        es = SV.expected_saves(rates[1], mean90, k, [1.5, 1.0], 1.25, 90.0)
        z = 1.5 / (1.5 + k)
        rate = z * (9 / 135 * 90) + (1 - z) * mean90
        self.assertAlmostEqual(es, rate * (90 / 90) * (1.5 / 1.25) + rate * (1.0 / 1.25))
        self.assertAlmostEqual(SV.expected_saves(None, mean90, k, [1.25], 1.25, 80.0), mean90 * 80 / 90)   # no rows: the mean
        rows = []
        for pid, rate90 in ((1, 2.0), (2, 3.0), (3, 4.0), (4, 5.0)):
            for rnd in range(1, 9):
                rows.append(gk(pid, rnd, 90, rate90 + (0.5 if rnd % 2 else 0.0)))
        kk, det = SV.saves_k(rows, half_minutes=90)
        self.assertEqual(det["keepers"], 4); self.assertAlmostEqual(det["r"], 1.0)
        self.assertAlmostEqual(kk, 0.0)                                                    # perfectly reliable: k = 0
        with self.assertRaises(SV.MissingInput):
            SV.saves_k(rows[:8], half_minutes=90)                                          # one keeper: k undefined

    def test_choice_and_the_substitution(self):
        self.assertEqual(SV.choose_keeper([3, 7], {3: 4.0, 7: 4.5}), 7)
        self.assertEqual(SV.choose_keeper([3, 7], {3: 4.0, 7: 4.0}), 3)                    # ties: the lower id
        act = {3: (6.0, 90.0), 7: (0.0, 0.0)}
        self.assertEqual(SV.keeper_points(7, [3, 7], act), 6.0)                            # the other keeper came on
        self.assertEqual(SV.keeper_points(3, [3, 7], act), 6.0)
        self.assertEqual(SV.keeper_points(7, [3, 7], {}), 0.0)


class Toy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.tmp24, cls.rules = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        cls.odds = toy_season(cls.tmp, skip_fixture=13)
        toy_prior(cls.tmp24)
        for folder in (cls.tmp, cls.tmp24):
            add_saves(folder)
        toy_rules_root(cls.rules, cls.tmp)
        cls.rescored = XR.rescore(cls.rules, os.path.join(cls.rules, "rescored.csv"))

    @classmethod
    def tearDownClass(cls):
        for d in (cls.tmp, cls.tmp24, cls.rules):
            shutil.rmtree(d, ignore_errors=True)

    def season(self):
        return SV.Season(self.tmp, self.tmp24, self.odds)

    def test_only_keepers_change_and_point_in_time(self):
        s = self.season()
        xp, plus, es, p_start, pos = s.forecasts(5)
        want, _ = s.rp.xp_v2(5)
        self.assertEqual(xp, want)                                                          # xp_v2 as tested, unchanged
        for pid in xp:
            if pos[pid] != 1:
                self.assertEqual(plus[pid], xp[pid])
            else:
                self.assertAlmostEqual(plus[pid], xp[pid] + p_start[pid] * es[pid] / 3)
        self.assertTrue(any(es[p] > 0 for p in es))                                         # keepers gain save points
        s2 = self.season()
        for g in range(5, s2.rp.hist["through"] + 1):
            for r in s2.rp.hist["raw"][g]:
                r["saves"] = "30"; r["minutes"] = "90"; r["starts"] = "1"
        xp2, plus2, es2, _, _ = s2.forecasts(5)
        self.assertEqual(es2, es)                                                            # rows of rounds >= 5 unread
        s3 = self.season()
        for r in s3.rp.hist["raw"][4]:
            if r["position"] == "GK":
                r["saves"] = "30"
        self.assertNotEqual(s3.forecasts(5)[2], es)                                           # round 4 is read

    def test_the_run_and_the_bar(self):
        s = None
        try:
            buf = io.StringIO()
            res = SV.test_2526(self.tmp, self.tmp24, out=lambda x: buf.write(x + chr(10)), odds_file=self.odds, first=5, last=6,
                               n_squads=3, rescored=self.rescored)
        except SV.MissingInput as e:
            self.fail(f"missing input on the toy: {e}")
        self.assertEqual([r["gw"] for r in res["per"]], [5, 6])
        self.assertEqual(res["pass"], res["boot"]["lo"] > 0)
        self.assertIn("pre-registered bar: 90% lower bound > 0", buf.getvalue())
        with self.assertRaises(XR.MissingInput):
            SV.test_2526(self.tmp, self.tmp24, out=lambda x: None, odds_file=self.odds, first=5, last=6, n_squads=3)


class Isolation(unittest.TestCase):
    def test_the_nightly_imports_nothing_here(self):
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'xp_v2_saves')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
