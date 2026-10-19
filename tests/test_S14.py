"""S14 - points distributions (tools/points_pmf.py, the bundle's captain
table; prereg/S14.md, option (a)). Hermetic: S6b's toy 2025/26 and Step 10
root, S6d's toy 2026/27 folder and history root, in temporary folders; no
network, no real data."""
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
import fpl_edge as E                                              # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import points_pmf as PM                                           # noqa: E402
import gw_pass as G                                               # noqa: E402
import provenance as PV                                           # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402
from tests.test_S6b import toy_rules_root                         # noqa: E402
from tests.test_S6d import toy_live, toy_hist_root, gw9_snapshot, NOW9   # noqa: E402


class Algebra(unittest.TestCase):
    def test_summaries_on_a_hand_pmf(self):
        pmf = {0: 0.3, 2: 0.3, 6: 0.2, 10: 0.1, 13: 0.05, 15: 0.03, 20: 0.02}
        self.assertAlmostEqual(PM.p_at_least(pmf, 10), 0.2)
        self.assertAlmostEqual(PM.p_at_least(pmf, 15), 0.05)
        self.assertEqual(PM.quantile(pmf, 0.9), 10)                                          # P(<= 6) 0.8, P(<= 10) 0.9
        self.assertAlmostEqual(PM.mean(pmf), 0.6 + 1.2 + 1.0 + 0.65 + 0.45 + 0.4)
        s = PM.summary(pmf)
        self.assertEqual((s["p90"], round(s["p10"], 9), round(s["p15"], 9)), (10, 0.2, 0.05))

    def test_poisson_and_the_goals_conceded_count(self):
        for lam, places in ((0.0, 12), (0.3, 12), (1.4, 9), (3.2, 4)):                         # the cut at 15 costs ~2e-6 at 3.2 goals a match
            g = PM.scaled_poisson(lam, 5)
            self.assertAlmostEqual(sum(g.values()), 1.0, places=12)
            self.assertAlmostEqual(PM.mean(g), 5 * lam, places=places)
        for pos in (1, 2):
            k = PM.cs_and_gc(1.3, pos)
            self.assertAlmostEqual(sum(k.values()), 1.0, places=12)
            self.assertAlmostEqual(k[E.CS_VALUE[pos]], math.exp(-1.3))                          # the clean sheet is GC = 0 ...
            self.assertNotIn(E.CS_VALUE[pos] - 1, k)                                              # ... never with a penalty
            self.assertAlmostEqual(k[-1], OL.poisson_pmf(1.3, 2) + OL.poisson_pmf(1.3, 3))         # GC 2 or 3: -1
            self.assertAlmostEqual(PM.mean(k), math.exp(-1.3) * E.CS_VALUE[pos] - OL.expected_gc_penalty(1.3), places=12)

    def test_bonus_table_back_off_and_the_tilt(self):
        rows = [(2, 0, 1, 3)] * 40 + [(2, 0, 0, 0)] * 40 + [(3, 1, 0, 2)] * 5 + [(4, 1, 0, 0)] * 5 + [(3, 1, 0, 1)] * 25 \
            + [(3, 0, 0, 0)] * 100 + [(1, 2, 1, 1)] * 3 + [(4, 2, 0, 3)] * 10
        t = PM.bonus_table(rows)
        n = len(rows)
        overall = {k: sum(1 for r in rows if r[3] == k) / n for k in range(4)}
        self.assertEqual(t[("def", 2, 1)], overall)                                             # 3 rows, 3 pooled, 13 over groups: all rows
        self.assertEqual(t[("att", 2, 0)], overall)                                             # 10 rows: all rows too
        self.assertEqual(t[("def", 0, 1)], {0: 0.0, 1: 0.0, 2: 0.0, 3: 1.0})                    # a full cell: its own rows
        self.assertEqual(t[("att", 1, 0)], {0: 5 / 35, 1: 25 / 35, 2: 5 / 35, 3: 0.0})           # 35 rows: its own
        self.assertAlmostEqual(sum(t[("def", 2, 1)].values()), 1.0)
        self.assertEqual(len(t), 9)                                                             # every cell of the grid filled
        cells = [(0.7, {0: 1.0, 1: 0.0}), (0.3, {0: 0.5, 2: 0.5})]
        th = PM.solve_theta(cells, 0.2)
        self.assertAlmostEqual(sum(w * PM.mean(PM.tilt(d, th)) for w, d in cells), 0.2, places=9)
        self.assertEqual(PM.tilt({0: 1.0, 1: 0.0}, th), {0: 1.0})                               # a zero cell stays at zero
        self.assertIsNone(PM.solve_theta([(1.0, {0: 1.0})], 0.3))                                # unreachable
        pmf, how = PM.xg_half(3, [{"xg": 0.0, "xa": 0.0, "lam_opp": 1.0}], 0.0, 0.3, {k: {0: 1.0} for k in t})
        self.assertEqual(how, "flat"); self.assertAlmostEqual(PM.mean(pmf), 2 + 1 * math.exp(-1.0) + 0.3)

    def test_the_halves_by_hand_and_a_double(self):
        table = {k: {0: 0.6, 1: 0.2, 2: 0.1, 3: 0.1} for k in PM.bonus_table([])}
        f1 = {"xg": 0.4, "xa": 0.2, "lam_opp": 1.1}
        f2 = {"xg": 0.3, "xa": 0.1, "lam_opp": 0.8}
        for pos in (1, 2, 3, 4):
            x1, _ = PM.xg_half(pos, [f1], 0.3, 0.5, table)
            want = 2 + 0.4 * E.GOAL_VALUE[pos] + 0.2 * 3 + math.exp(-1.1) * E.CS_VALUE[pos] + 2 * 0.3 + 0.5
            self.assertAlmostEqual(PM.mean(x1), want, places=9)
            x2, _ = PM.xg_half(pos, [f1, f2], 0.3, 0.5, table)                                   # a double: appearance, DEFCON and bonus once
            want2 = want + 0.3 * E.GOAL_VALUE[pos] + 0.1 * 3 + math.exp(-0.8) * E.CS_VALUE[pos]
            self.assertAlmostEqual(PM.mean(x2), want2, places=9)
            self.assertAlmostEqual(sum(x2.values()), 1.0, places=12)
        t1 = {"xgi": 0.5, "p_dc": 0.4, "pos": 2, "lam_opp": 1.2}
        t2 = {"xgi": 0.5, "p_dc": 0.4, "pos": 2, "lam_opp": 0.9}
        self.assertEqual(PM.bl_half([t1, t2]), PM.conv(PM.bl_half([t1]), PM.bl_half([t2])))       # the fixtures summed
        m1 = 2 + 0.5 * 0.62 * 6 + 0.5 * 0.38 * 3 + math.exp(-1.2) * 4 - OL.expected_gc_penalty(1.2) + 2 * 0.4
        self.assertAlmostEqual(PM.mean(PM.bl_half([t1])), m1, places=9)

    def test_mixture_and_the_independent_fallback(self):
        x = {"p_start": 0.6, "p_sub": 0.3, "e_sub": 1.5, "defcon": 0.4, "ict": 0.5,
             "fixtures": [{"opp": "B", "home": True, "lam_opp": 1.0, "xg": 0.2, "xa": 0.1}]}
        terms = [{"xgi": 0.3, "p_dc": 0.2, "pos": 3, "lam_own": 1.1}]
        table = {k: {0: 0.7, 1: 0.2, 3: 0.1} for k in PM.bonus_table([])}
        sub = {1: 0.5, 2: 0.5}
        pmf, notes = PM.player_pmf(x, terms, 3, sub, table)
        X, _ = PM.xg_half(3, x["fixtures"], 0.2, 0.4, table)
        L = PM.bl_half(terms)
        self.assertAlmostEqual(sum(pmf.values()), 1.0, places=12)
        self.assertAlmostEqual(PM.mean(pmf), 0.6 * (PM.mean(X) + PM.mean(L)) / 2 + 0.3 * 1.5, places=12)
        self.assertAlmostEqual(pmf.get(0, 0.0), 0.1 + 0.6 * (0.5 * X.get(0, 0) + 0.5 * L.get(0, 0)), places=12)   # 10% no appearance
        self.assertNotIn("independent", notes)
        y = dict(x, p_start=0.8, p_sub=0.5)
        pmf2, notes2 = PM.player_pmf(y, terms, 3, sub, table)
        self.assertTrue(notes2["independent"])
        self.assertAlmostEqual(PM.mean(pmf2), 0.8 * (PM.mean(X) + PM.mean(L)) / 2 + 0.5 * 1.5, places=12)
        z = dict(x, p_start=0.0, p_sub=0.4)
        pmf3, _ = PM.player_pmf(z, terms, 3, sub, table)
        self.assertEqual(pmf3, {1: 0.2, 2: 0.2, 0: 0.6})


class Toy2526(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.tmp24, cls.rules = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        cls.odds = toy_season(cls.tmp, skip_fixture=13)
        toy_prior(cls.tmp24); toy_rules_root(cls.rules, cls.tmp)
        cls.rescored = XR.rescore(cls.rules, os.path.join(cls.rules, "rescored.csv"))

    @classmethod
    def tearDownClass(cls):
        for d in (cls.tmp, cls.tmp24, cls.rules):
            shutil.rmtree(d, ignore_errors=True)

    def test_every_pmf_is_xp_v2s_distribution(self):
        s = PM.Season(self.tmp, self.tmp24, self.odds)
        for t in (5, 6):
            pm, pos_of = s.pmfs(t)
            want, _ = s.rp.xp_v2(t)
            self.assertEqual(set(pm), set(want))                                                  # S6b's population
            for pid, (pmf, xp, notes) in pm.items():
                self.assertAlmostEqual(sum(pmf.values()), 1.0, places=12)
                self.assertAlmostEqual(xp, want[pid], places=12)
                self.assertLess(abs(PM.mean(pmf) - xp), 1e-6)                                     # the mean is xp_v2

    def test_point_in_time_and_the_baseline(self):
        s = PM.Season(self.tmp, self.tmp24, self.odds)
        pm5, _ = s.pmfs(5)
        s2 = PM.Season(self.tmp, self.tmp24, self.odds)
        for r in s2.hist["c"]["rows"]:
            if r["event"] >= 5:
                r["pts"] = 50; r["minutes"] = 90; r["starts"] = 1; r["xg"] = 9.0
        for g in range(5, s2.hist["through"] + 1):
            for r in s2.hist["raw"][g]:
                r["minutes"] = "90"; r["starts"] = "1"; r["total_points"] = "50"; r["bonus"] = "3"; r["goals_scored"] = "4"
        pm5b, _ = s2.pmfs(5)
        self.assertEqual({k: v[0] for k, v in pm5b.items()}, {k: v[0] for k, v in pm5.items()})   # nothing of round >= 5
        gates = PM.gate_rounds(s, self.rescored, 6)
        base = {pos: PM.baseline(gates, 5, pos, 0) for pos in (1, 2, 3, 4)}
        late = {k: ((v[0] + 40.0) if k[1] >= 5 else v[0], v[1]) for k, v in self.rescored.items()}
        gates_late = PM.gate_rounds(s, late, 6)
        self.assertEqual({pos: PM.baseline(gates_late, 5, pos, 0) for pos in (1, 2, 3, 4)}, base)   # outcomes of rounds >= t unread
        early = {k: ((v[0] + 40.0) if k[1] == 4 else v[0], v[1]) for k, v in self.rescored.items()}
        gates_early = PM.gate_rounds(s, early, 6)
        self.assertNotEqual({pos: PM.baseline(gates_early, 5, pos, 0) for pos in (1, 2, 3, 4)}, base)   # round t-1 is read

    def test_the_run_and_both_pass_conditions(self):
        buf = io.StringIO()
        res = PM.test_2526(self.tmp, self.tmp24, out=lambda s: buf.write(s + chr(10)), odds_file=self.odds, first=5, last=6,
                           rescored=self.rescored)
        text = buf.getvalue()
        self.assertEqual([r["gw"] for r in res["per"]], [5, 6])
        self.assertLess(res["worst"], 1e-6)
        self.assertIn("pre-registered bar (both)", text); self.assertIn("mean check", text)
        for r in res["per"]:
            self.assertAlmostEqual(r["diff"], r["brier_base"] - r["brier_pmf"])
        self.assertAlmostEqual(res["actual"], sum(r["hauls"] for r in res["per"]))
        lifted = {k: (v[0] + 30.0, v[1]) if k[1] == 6 else v for k, v in self.rescored.items()}
        res_l = PM.test_2526(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6, rescored=lifted)
        self.assertGreater(res_l["actual"], res["actual"])                                       # the outcomes are the re-scored points
        good = {"mean": 0.01, "lo": 0.005, "hi": 0.02, "n": 2, "p": 0.01}
        bad = {"mean": 0.01, "lo": -0.005, "hi": 0.02, "n": 2, "p": 0.2}
        with mock.patch.object(PM, "calibration", return_value=[]):
            with mock.patch.object(PM.BT, "bootstrap_mean", return_value=good):
                r1 = PM.test_2526(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6, rescored=self.rescored)
            self.assertEqual(r1["pass"], r1["count_ok"])                                          # a good bound alone is not enough
            with mock.patch.object(PM.BT, "bootstrap_mean", return_value=bad):
                r2 = PM.test_2526(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6, rescored=self.rescored)
            self.assertFalse(r2["pass"])                                                          # nor a count alone
        with mock.patch.object(PM.BT, "bootstrap_mean", return_value=good), mock.patch.object(PM, "p_at_least", return_value=0.0):
            r3 = PM.test_2526(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6, rescored=lifted)
        self.assertFalse(r3["count_ok"]); self.assertFalse(r3["pass"])                            # predicted 0 against real hauls
        with self.assertRaises(XR.MissingInput):
            PM.test_2526(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6)


class LiveAndBundle(unittest.TestCase):
    def test_captain_table_live_and_in_the_bundle(self):
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_live(tmp); toy_hist_root(hist)
            gw9_snapshot(tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
            res = XL.live(tmp, hist, now=NOW9)
            sums = PM.live_pmfs(res)
            self.assertEqual(set(sums), set(res["xp"]))
            for pid, s in sums.items():
                self.assertAlmostEqual(s["mean"], res["xp"][pid], places=9)                       # the live PMF's mean is the live xp_v2
                self.assertTrue(0.0 <= s["p15"] <= s["p10"] <= 1.0)
            buf = io.StringIO()
            G.bundle(tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=hist)
            sec7 = buf.getvalue().split("CAPTAIN TABLE: S14 POINTS DISTRIBUTIONS (INFORMATION ONLY)")[1]
            self.assertIn("information only until S14 passes and Boris accepts", sec7)
            squad = G.CH.my_squad(res["d"])
            lines = [ln for ln in sec7.splitlines() if ln.strip() and ln.split()[0] in {r["name"] for r in squad}]
            self.assertEqual(len(lines), 15)
            top = max((r for r in squad if r["id"] in sums), key=lambda r: sums[r["id"]]["mean"])
            self.assertTrue(lines[0].split()[0] == top["name"])                                   # sorted by mean
            s = sums[top["id"]]
            self.assertIn(f"{s['mean']:6.2f} {s['p10']:7.3f} {s['p15']:7.3f} {s['p90']:>4}", lines[0])
            shutil.rmtree(os.path.join(hist, "2025-26"))                                          # no live xp_v2: the table says so
            buf = io.StringIO()
            G.bundle(tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=hist)
            sec7 = buf.getvalue().split("CAPTAIN TABLE: S14 POINTS DISTRIBUTIONS (INFORMATION ONLY)")[1]
            self.assertIn("missing input: xp_v2 as tested is not available", sec7)
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)


class CLI(unittest.TestCase):
    def test_cli_run_txt_and_isolation(self):
        tmp, tmp24, rules = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        live, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            odds = toy_season(tmp); toy_prior(tmp24); toy_rules_root(rules, tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = PM.main(["--test", "--hist", tmp, "--prior", tmp24, "--rules", rules, "--odds", odds, "--out", out, "--last", "6"])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "points_pmf_2025-26.txt"), encoding="utf-8") as fh:
                self.assertIn("S14 TEST", fh.read())
            rec = PV.read_run(out)
            self.assertEqual(rec["tool"], "tools/points_pmf.py"); self.assertIn("points_pmf_2025-26.txt", rec["outputs"])
            toy_live(live); toy_hist_root(hist)
            out2 = os.path.join(live, "out")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(PM.main(["--captain", "--data", live, "--hist", hist, "--out", out2]), 0)
            with open(os.path.join(out2, "captain_gw9.txt"), encoding="utf-8") as fh:
                self.assertIn("CAPTAIN TABLE  GW9", fh.read())
            with redirect_stdout(io.StringIO()):
                self.assertEqual(PM.main(["--test", "--hist", tmp, "--prior", tmp24, "--rules", tmp, "--out", out]), 2)   # no Step 10 root
                self.assertEqual(PM.main([]), 2)
        finally:
            for d in (tmp, tmp24, rules, live, hist):
                shutil.rmtree(d, ignore_errors=True)
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'points_pmf')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
