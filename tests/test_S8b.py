"""S8b - S8's planner without hits on xp_v2, 2024/25 (tools/planner_2425.py;
prereg/S8b.md, Part F item F-F, the night ruling point 5). Hermetic: S6b's
toy season (S5/S11 toys) laid out as a 2024-25 / 2023-24 history root in a
temporary folder; no network, no real data."""
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
import odds_lambda as OL                                          # noqa: E402
import planner as PL                                              # noqa: E402
import planner_2425 as P                                          # noqa: E402
import xp_v2_replay as X                                          # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402
from tests.test_S6b import toy_rules_root                         # noqa: E402
from tests.test_S6c import add_s6c_inputs                         # noqa: E402
from tests.test_S6f import zero_counts                            # noqa: E402


class Toy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.rules = tempfile.mkdtemp(), tempfile.mkdtemp()
        cls.hist, cls.prior = os.path.join(cls.root, "2024-25"), os.path.join(cls.root, "2023-24")
        os.makedirs(cls.hist); os.makedirs(cls.prior)
        cls.odds = toy_season(cls.hist, skip_fixture=13)
        add_s6c_inputs(cls.hist)
        toy_prior(cls.prior)
        toy_rules_root(cls.rules, cls.hist)
        cls.rescored = X.rescore(cls.rules, os.path.join(cls.rules, "rescored.csv"))
        zero_counts(cls.hist)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True); shutil.rmtree(cls.rules, ignore_errors=True)

    def season(self):
        return P.Season2425(self.hist, self.prior, self.odds, self.rescored)

    def run_tool(self, **kw):
        lines = []
        through = self.season().through
        with mock.patch.object(P.F, "rescore", return_value=self.rescored):
            res = P.run(self.root, lines.append, odds_file=self.odds, out_csv=os.path.join(self.root, "r.csv"),
                        sources_csv=os.path.join(self.root, "src.csv"), n_squads=3, first=2, last=through, check_decays=False, **kw)
        return res, lines

    def test_week_t_is_s6b_and_later_weeks_the_origin_fallback(self):
        s = self.season()
        rp = X.Replay(self.hist, self.prior, self.odds)
        t = 3
        fc, p_start, pos = s.forecasts(t)
        want, _ = rp.xp_v2(t)
        self.assertEqual(fc[t], {k: v for k, v in want.items() if v})                      # week t: S6b's xp_v2 as tested
        self.assertEqual(sorted(fc), list(range(t, min(t + 5, PL.REPLAY_LAST) + 1)))                # six weeks from the origin
        results = [(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in s.s5.fixtures.values() if f["event"] < t]
        model = OL.fit_fallback(results, s.s5.deadline(t))
        seen_odds_week, checked = False, 0
        for u in sorted(fc):
            lam = s.horizon_lambdas(t, u)
            for fid, (l, src) in lam.items():
                f = s.s5.fixtures[fid]
                if u == t:
                    self.assertEqual((l, src), s.s5.lambdas(t)[fid])
                    continue
                self.assertEqual(src, "fallback")
                self.assertEqual(l, OL.fallback_lambdas(model, f["home"], f["away"]))   # fitted on results before the origin
                seen_odds_week |= s.s5.lambdas(u)[fid][1] == "odds"                        # its own week had odds: never read
                checked += 1
        self.assertGreater(checked, 0); self.assertTrue(seen_odds_week)
        self.assertTrue(all(len(r) == 6 for r in s.sources))
        self.assertEqual({r[5] for r in s.sources if r[0] != r[1]}, {"fallback"})

    def test_the_outcomes_are_the_rescore(self):
        s = self.season()
        want = X.actuals_from(self.rescored)
        for g in range(2, s.through + 1):
            self.assertEqual(dict(s.rp.actual[g]), dict(want[g]), g)                       # S10b's re-score, never the official points
        lifted = {k: (v[0] + 30.0, v[1]) if k[1] == 3 else v for k, v in self.rescored.items()}
        s2 = P.Season2425(self.hist, self.prior, self.odds, lifted)
        rows = s2.squad_rows(P.CH.sample_squads(P.CH.gw1_candidates(s2.rp.hist), 1, 7)[0], 3)
        xp = s2.forecasts(3)[0][3]
        self.assertGreater(s2.realised(rows, 3, xp), s.realised(rows, 3, xp) + 300)

    def test_rows_of_the_origin_and_later_never_move_a_forecast(self):
        s1 = self.season()
        before = s1.forecasts(3)[0]
        s2 = self.season()
        for g in range(3, s2.through + 1):
            for r in s2.hist["raw"][g]:
                r["minutes"], r["starts"], r["expected_goals"], r["expected_assists"], r["total_points"] = "90", "1", "3.0", "2.0", "30"
        for f in s2.s5.fixtures.values():
            if f["event"] >= 3:
                f["hg"], f["ag"] = 9, 0
        self.assertEqual(s2.forecasts(3)[0], before)

    def test_s8_loop_unchanged_with_hits_forbidden(self):
        res, lines = self.run_tool()
        through = self.season().through
        with P.F.season_names("2024-25"), P.season_2425(self.prior, self.odds, self.rescored):
            want = PL.replay(self.hist, n_squads=3, seed=7, out=lambda s: None, decay=0.85, schedule_name="boris", first=2,
                             last=through, check_decays=False, hits_allowed=False)
        self.assertEqual(res["results"], want["results"]); self.assertEqual(res["boot"], want["boot"])
        self.assertTrue(all(r["planner"]["hits"] == 0 and r["baseline"]["hits"] == 0 for r in res["results"]))
        self.assertIsInstance(PL.Replay, type); self.assertFalse(issubclass(PL.Replay, P.Season2425))     # S8's, restored
        self.assertTrue(lines[0].startswith("S8B TEST  2024/25 GW2-")); self.assertIn("decay 0.85, schedule boris", lines[0])
        with open(os.path.join(self.root, "src.csv"), encoding="utf-8") as fh:
            head = fh.readline().strip()
        self.assertEqual(head, "origin,week,fixture,home,away,source")
        with mock.patch.object(P.PL, "replay", wraps=PL.replay) as rep:
            self.run_tool()
        self.assertFalse(rep.call_args.kwargs["hits_allowed"]); self.assertEqual(rep.call_args.kwargs["decay"], 0.85)
        self.assertEqual(rep.call_args.kwargs["schedule_name"], "boris")

    def test_the_bar(self):
        base, _ = self.run_tool()
        for mean, lo, want in ((5.0, 0.1, True), (4.99, 1.0, False), (6.0, 0.0, False), (7.0, -2.0, False)):
            fake = dict(base, boot=dict(base["boot"], mean=mean, lo=lo, hi=mean + 3))
            with mock.patch.object(P.PL, "replay", side_effect=lambda *a, **k: P.Season2425(self.hist, self.prior, self.odds,
                                                                                               self.rescored) and fake):
                res, lines = self.run_tool()
            self.assertEqual(res["pass_"], want, (mean, lo))
            self.assertEqual(lines[-1].endswith("PASS (adoption needs Boris)"), want)

    def test_restored_after_an_error_and_isolation(self):
        saved = PL.Replay
        with self.assertRaises(RuntimeError):
            with P.season_2425(self.prior, self.odds, self.rescored):
                raise RuntimeError("boom")
        self.assertIs(PL.Replay, saved)
        out = tempfile.mkdtemp()
        try:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(P.main(["--test", "--hist", os.path.join(out, "none"), "--out", out]), 2)
        finally:
            shutil.rmtree(out, ignore_errors=True)
        code = ("import sys; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "print([m for m in sys.modules if m.split('.')[0] in ('planner_2425', 'planner', 'xp_v2_2425')])")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
