"""S8c - the live transfer planner on xp_v2, no hits, and the bundle's planner
section (tools/planner_live.py, tools/gw_pass.py; prereg/S8c.md, Ruling Tue
20 Oct point 1). Hermetic: S6d's toy 2026/27 data folder and toy history
root in temporary folders; no real data."""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import builder as B                                               # noqa: E402
import chips as CH                                                # noqa: E402
import gw_pass as G                                               # noqa: E402
import planner as PL                                              # noqa: E402
import planner_live as PLV                                        # noqa: E402
from tests.test_S6d import toy_live, toy_hist_root, gw9_snapshot, NOW9   # noqa: E402


class Toy(unittest.TestCase):
    def setUp(self):
        self.tmp, self.hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        toy_live(self.tmp); toy_hist_root(self.hist)
        gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        self.budget = mock.patch.object(PLV.E, "selling_budget", return_value=(100.0, ""))
        self.budget.start()

    def tearDown(self):
        self.budget.stop()
        shutil.rmtree(self.tmp, ignore_errors=True); shutil.rmtree(self.hist, ignore_errors=True)

    def test_the_matrix_is_s15s_with_every_source(self):
        d, path, target, weeks_xp, srcs, p_start, snap = PLV.live_inputs(self.tmp, self.hist)
        want = B.live_matrix(self.tmp, self.hist, PL.HORIZON)
        self.assertEqual(weeks_xp, want[3]); self.assertEqual(target, want[2])
        self.assertEqual(Counter(("week t" if u == target else "later weeks", s) for u, _, _, s in srcs), want[4])
        self.assertEqual(snap, "odds_2098-12-31T10-00-00Z.json.gz")
        self.assertTrue(srcs and all(s in ("odds", "fallback") for *_, s in srcs))

    def test_the_plans_are_s8s_with_no_hits_and_one_ft(self):
        lines = []
        res = PLV.plan(self.tmp, self.hist, lines.append)
        d, path, target, weeks_xp, srcs, p_start, snap = PLV.live_inputs(self.tmp, self.hist)
        squad = CH.my_squad(d)
        bank = 100.0 - sum(r["selling"] for r in squad)
        market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"], "status": p["status"]}
                  for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
        want, pool = PL.rank_plans(squad, bank, market, weeks_xp, 1, p_start, 0.85, PL.SCHEDULES["boris"], hits_allowed=False)
        self.assertEqual(res["scored"], want)
        self.assertTrue(all(ev["hits"] == 0 and ev["used"] <= 1 for ev in res["scored"]))      # no hit, one free transfer
        self.assertEqual(res["simple"], PL.baseline_plan(squad, bank, pool, weeks_xp[0], 1))
        self.assertTrue(lines[0].startswith("TRANSFER PLANNER ON XP_V2  GW9-14")); self.assertIn("no hits", lines[0])
        self.assertTrue(any(l.startswith("  DEFAULT: ") for l in lines))
        self.assertTrue(any(l.startswith("  the simple rule beside it") for l in lines))
        self.assertTrue(any(l.startswith("  lambdas GW9: ") and "odds" in l for l in lines))
        with mock.patch.object(PLV.PL, "baseline_plan", wraps=PL.baseline_plan) as bp:
            PLV.plan(self.tmp, self.hist, lambda s: None)
        self.assertEqual(bp.call_args.args[3], weeks_xp[0]); self.assertNotEqual(weeks_xp[0], weeks_xp[1])   # the simple rule on week t
        with mock.patch.object(PLV.PL, "rank_plans", wraps=PL.rank_plans) as rp:
            PLV.plan(self.tmp, self.hist, lambda s: None)
        args, kw = rp.call_args
        self.assertEqual((args[4], args[6], kw["hits_allowed"]), (1, 0.85, False)); self.assertEqual(args[7], PL.SCHEDULES["boris"])

    def test_the_bundle_section_and_its_fallback(self):
        buf = io.StringIO()
        G.bundle(self.tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=self.hist)
        text = buf.getvalue()
        sec = text.split("TRANSFER PLANNER: THE XP_V2 NO-HIT DEFAULT, S8 AND THE BASELINE")[1].split("S9 LEAGUE")[0]
        self.assertIn("TRANSFER PLANNER ON XP_V2", sec); self.assertIn("below, information: S8's planner on own xP", sec)
        self.assertIn("the transfer default from GW8 is the no-hit planner on xp_v2", text.splitlines()[0])
        shutil.rmtree(os.path.join(self.hist, "2025-26"))
        buf = io.StringIO()
        G.bundle(self.tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=self.hist)
        sec = buf.getvalue().split("TRANSFER PLANNER: THE XP_V2 NO-HIT DEFAULT, S8 AND THE BASELINE")[1].split("S9 LEAGUE")[0]
        self.assertIn("the xp_v2 planner: missing input", sec); self.assertIn("the ruling's fallback", sec)
        self.assertNotIn("TRANSFER PLANNER ON XP_V2", sec)
        self.assertIn("TRANSFER PLANNER  export", sec)                                         # S8's own planner still printed


class BenchBoost(unittest.TestCase):
    def rows(self):
        return [{"id": i, "pos": pos, "name": f"P{i}", "team": f"T{i}", "price": 5.0}
                for i, pos in enumerate((1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4), 1)]

    def test_by_hand(self):
        rows = self.rows()
        xp = {i: float(i) for i in range(1, 16)}
        self.assertAlmostEqual(PLV.bb_value(rows, xp), sum(range(1, 16)) + 15.0)              # all 15 + the captain (15)
        inc = {"id": 99, "pos": 2, "name": "N", "team": "TN", "price": 5.0}
        ev = {"score": 2.0, "gain": 3.0, "gains": [1.0, 2.0], "used": 1, "outs": [rows[2]], "ins": [inc], "hits": 0, "lost": 1.0}
        out = PLV.bb_rescore([ev], rows, {**xp, 99: 10.0})
        g0 = 10.0 - 3.0                                                                         # out 3, in 10; the captain stays 15
        self.assertAlmostEqual(out[0]["gains"][0], g0); self.assertAlmostEqual(out[0]["score"], 2.0 - 1.0 + g0)
        self.assertEqual(out[0]["gains"][1:], [2.0])


class Isolation(unittest.TestCase):
    def test_the_nightly_imports_nothing_here(self):
        code = ("import sys; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "print([m for m in sys.modules if m.split('.')[0] in ('planner_live', 'gw_pass', 'builder')])")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
