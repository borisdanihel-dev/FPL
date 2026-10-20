"""S17 - the mini-league win simulator (tools/league_sim.py; prereg/S17.md,
Part F item F-H). Hermetic: S6b's toy season as a 2025-26 / 2024-25 root,
S6d's toy 2026/27 folder, hand-made PMFs and leagues, all in temporary
folders; no real data."""
import io
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
import chips as CH                                                # noqa: E402
import league_sim as LS                                           # noqa: E402
import points_pmf as PM                                           # noqa: E402
import xp_v2_replay as X                                          # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402
from tests.test_S6b import toy_rules_root                         # noqa: E402
from tests.test_S6c import add_s6c_inputs                         # noqa: E402

SMALL = (("template", 2, lambda s: s), ("mixed", 1, lambda s: s ** 0.5), ("differential", 1, lambda s: 1.0 / s))


class ByHand(unittest.TestCase):
    def test_shared_draws_captain_and_p_win(self):
        pmfs = {3: {1: {0: 0.5, 10: 0.5}, 2: {2: 1.0}, 3: {5: 1.0}}}
        mw = [[(3, [1, 2], 1, 2)], [(3, [1, 3], 3, 2)], [(3, [2, 3], 3, 2)]]
        keys, idx = LS.plan(mw)
        self.assertEqual(sorted(keys), [(1, 3), (2, 3), (3, 3)])
        self.assertEqual(sorted(idx[0]), sorted([keys.index((1, 3)), keys.index((2, 3)), keys.index((1, 3))]))   # captain twice
        p, _ = LS.simulate(keys, pmfs, idx, [0, 0, 0], [[0, 1, 2]], 4000, 1)
        # player 1 scores 10 (half the time): A = 22, B = 20, C = 12 -> A wins; else A = 2, B = 10, C = 12 -> C wins
        self.assertAlmostEqual(p[0], 0.5, delta=0.03); self.assertAlmostEqual(p[2], 0.5, delta=0.03); self.assertEqual(p[1], 0.0)
        self.assertAlmostEqual(sum(p), 1.0)
        p2, _ = LS.simulate(keys, {3: {1: {10: 1.0}, 2: {0: 1.0}, 3: {5: 1.0}}}, idx, [0, 0, 0], [[0, 1, 2]], 50, 1)
        self.assertEqual(p2, [0.5, 0.5, 0.0])                                               # A 2x10+0, B 10+2x5, C 0+2x5: a tie shares
        keys2, idx2 = LS.plan([[(3, [1], 1, 3)]])
        p3, alt = LS.simulate(keys2, {3: {1: {4: 1.0}}}, idx2, [10], [[0]], 5, 1, extra={"x": (0, [0])})
        self.assertEqual((p3, alt), ([1.0], {"x": 1.0}))
        self.assertEqual(LS.leader_p([10, 12, 12]), [0.0, 0.5, 0.5])
        self.assertAlmostEqual(LS.brier([(0.5, 1.0), (0.5, 0.0)]), 0.25)
        dec = LS.deciles([(i / 100, i % 2) for i in range(100)])
        self.assertEqual(len(dec), 10); self.assertTrue(all(n == 10 for _, _, n in dec))
        self.assertAlmostEqual(dec[0][0], 0.045)
        per = [(1.0, 2.0, 10), (1.0, 2.0, 10)]
        sk, lo, hi = LS.skill_ci(per, b=200)
        self.assertAlmostEqual(sk, 0.5); self.assertAlmostEqual(lo, 0.5); self.assertAlmostEqual(hi, 0.5)

    def test_cdf_draws_follow_the_pmf(self):
        vals, cum = LS.cdf_of({0: 0.2, 2: 0.3, 9: 0.5 - 1e-15})
        self.assertEqual(vals, [0, 2, 9]); self.assertEqual(cum[-1], 1.0)
        keys, idx = LS.plan([[(1, [7], 7, 1)]])
        p, _ = LS.simulate(keys, {1: {7: {0: 0.2, 2: 0.3, 9: 0.5}}}, idx, [0], [[0]], 10, 1)
        self.assertEqual(p, [1.0])


class Styles(unittest.TestCase):
    def test_template_is_s7_and_the_weights(self):
        cands = [{"id": i, "pos": (1, 2, 2, 3, 3, 4)[i % 6], "team": f"T{i % 8}", "price": 40 + i % 30, "selected": 1.0 + (i * 37) % 900}
                 for i in range(1, 200)]
        self.assertEqual(LS.sample_style(cands, 3, 7, lambda s: s), CH.sample_squads(cands, 3, 7))
        for w in (lambda s: 1.0 / s, lambda s: s ** 0.5):                                 # the weight replaces selected, nothing else
            moved = [dict(p, selected=w(p["selected"])) for p in cands]
            ids = lambda sqs: [[p["id"] for p in sq] for sq in sqs]
            self.assertEqual(ids(LS.sample_style(cands, 2, 11, w)), ids(CH.sample_squads(moved, 2, 11)))
        lg = LS.leagues(cands, 2, SMALL)
        self.assertEqual([s for s, _ in lg[0]], ["template", "template", "mixed", "differential"])
        self.assertEqual(lg[1][0][1], LS.sample_style(cands, 2, 7 * 100000 + 10 * 1 + 0, lambda s: s)[0])   # seed 7 x 100000 + 10 i + j
        self.assertEqual([s for s, _, _ in LS.STYLES], ["template", "mixed", "differential"])
        self.assertEqual([k for _, k, _ in LS.STYLES], [4, 3, 3])


class Toy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.rules = tempfile.mkdtemp(), tempfile.mkdtemp()
        cls.hist, cls.prior = os.path.join(cls.root, "2025-26"), os.path.join(cls.root, "2024-25")
        os.makedirs(cls.hist); os.makedirs(cls.prior)
        cls.odds = toy_season(cls.hist, skip_fixture=13)
        add_s6c_inputs(cls.hist)
        toy_prior(cls.prior)
        toy_rules_root(cls.rules, cls.hist)
        cls.rescored = X.rescore(cls.rules, os.path.join(cls.rules, "rescored.csv"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True); shutil.rmtree(cls.rules, ignore_errors=True)

    def season(self):
        return LS.SimSeason(self.hist, self.prior, self.odds, self.rescored)

    def run_test(self, **kw):
        lines = []
        res = LS.test(self.root, lines.append, self.root, n_leagues=3, origins=(4, 5), n_sim=200, odds_file=self.odds,
                      rescored=self.rescored, styles=SMALL, **kw)
        return res, lines

    def test_the_horizon_pmfs_are_step_14s(self):
        s = self.season()
        xps, pmfs = s.horizon(4, s.through)
        want = PM.Season(self.hist, self.prior, self.odds).pmfs(4)[0]
        self.assertEqual(set(pmfs[4]), set(want))
        for pid in want:
            self.assertEqual(pmfs[4][pid], want[pid][0])                                   # week T: S14's PMF exactly
            self.assertAlmostEqual(xps[4][pid], want[pid][1])
        self.assertEqual(sorted(xps), list(range(4, s.through + 1)))
        self.assertEqual({src for o, u, _, _, _, src in s.sources if u > o}, {"fallback"})
        want4 = X.Replay(self.hist, self.prior, self.odds).xp_v2(4)[0]
        self.assertEqual(s.point_in_time(4), {k: v for k, v in want4.items() if v})            # the truth's choices: S6b's xp_v2(u)

    def test_the_run_the_truth_and_the_bar(self):
        res, lines = self.run_test()
        s = self.season()
        lgs = LS.leagues(CH.gw1_candidates(s.rp.hist), 3, SMALL)
        sq = lgs[0][0][1]
        truth = sum(s.realised([{"id": p["id"], "pos": p["pos"], "team": p["team"], "name": "x"} for p in sq], u, s.point_in_time(u))
                    for u in range(2, s.through + 1))
        self.assertAlmostEqual(res["final"][0], truth)                                        # GW2..last, S6b's choices
        self.assertTrue(lines[0].startswith("S17 TEST  3 synthetic leagues of 4")); self.assertIn("GW4, 5", lines[0])
        self.assertEqual(res["pass"], res["skill"] >= 0.05)
        for skill, want in ((0.05, True), (0.0499, False)):
            with mock.patch.object(LS, "skill_ci", return_value=(skill, -1.0, 1.0)):
                r2, l2 = self.run_test()
            self.assertEqual(r2["pass"], want); self.assertEqual(l2[-1].endswith("FAIL"), not want)

    def test_rows_of_the_origin_and_later_never_move_the_simulation(self):
        s1 = self.season()
        x1, p1 = s1.horizon(4, s1.through)
        s2 = self.season()
        for g in range(4, s2.through + 1):
            for r in s2.by_round[g]:
                r["minutes"], r["starts"], r["total_points"], r["expected_goals"], r["bonus"] = "90", "1", "30", "3.0", "3"
        for f in s2.s5.fixtures.values():
            if f["event"] >= 4:
                f["hg"], f["ag"] = 9, 0
        x2, p2 = s2.horizon(4, s2.through)
        self.assertEqual((x2, p2), (x1, p1))


class Live(unittest.TestCase):
    def test_live_league(self):
        from tests.test_S6d import toy_live, toy_hist_root, gw9_snapshot
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_live(tmp); toy_hist_root(hist)
            gw9_snapshot(tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
            import gzip, json
            path = os.path.join(tmp, "exports", sorted(os.listdir(os.path.join(tmp, "exports")))[-1])
            with gzip.open(path, "rt", encoding="utf-8") as fh:
                d = json.load(fh)
            mine = [r for r in d["squads"] if r["entry_id"] == d["my_entry"]]
            rival = [dict(r, entry_id=2, entry_name="Them") for r in mine]                    # the same legal 15
            d["squads"] = mine + rival
            d["standings"] = [{"entry_id": d["my_entry"], "entry_name": mine[0]["entry_name"], "total": 400, "bank": 5},
                              {"entry_id": 2, "entry_name": "Them", "total": 410, "bank": 0}]
            d["chips_used"] = [{"entry_name": "Them", "name": "3xc", "event": 3}]
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                json.dump(d, fh)
            lines = []
            with mock.patch.object(LS.E, "selling_budget", return_value=(100.0, "")):
                res = LS.live(tmp, hist, lines.append, n_sim=300)
            self.assertAlmostEqual(sum(res["p_win"].values()), 1.0)
            self.assertTrue(lines[0].startswith("LEAGUE SIMULATOR  league 455565, GW9-38")); self.assertIn("information only", lines[0])
            self.assertIn("Them: TC -, BB GW9", lines[1])                                    # TC used, BB in its best week
            self.assertTrue(any(l.strip().startswith("captain ") for l in lines))
            self.assertTrue(all(0.0 <= p <= 1.0 for p in res["alts"].values()))
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)


class Isolation(unittest.TestCase):
    def test_cli_and_isolation(self):
        out = tempfile.mkdtemp()
        try:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(LS.main(["--test", "--hist", os.path.join(out, "none"), "--out", out]), 2)
        finally:
            shutil.rmtree(out, ignore_errors=True)
        code = ("import sys; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "print([m for m in sys.modules if m.split('.')[0] in ('league_sim', 'builder', 'points_pmf')])")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
