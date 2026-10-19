"""The Thursday deadline-pass bundle (tools/gw_pass.py; prereg/bundle.md).
Hermetic: the S4/S7 toy export in a temporary folder; sections whose
inputs the toy lacks are reported, never substituted."""
import gc
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
import gw_pass as G                                               # noqa: E402
import planner as P                                               # noqa: E402
import provenance as PV                                           # noqa: E402
from tests.test_S4 import toy_data                                # noqa: E402
from tests.test_S7 import toy_export                              # noqa: E402


def squad15():
    """Two keepers, five defenders, five midfielders, three forwards."""
    pos = [1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4]
    clubs = ["CHE", "ARS", "BRE", "BHA", "EVE", "LIV"]                               # at most 3 per club, 2 GK/DEF per club: legal
    return [{"id": i + 1, "name": f"N{i + 1}", "team": clubs[i % 6], "pos": p, "price": 5.0, "selling": 5.0}
            for i, p in enumerate(pos)]


class Hand(unittest.TestCase):
    def test_side_by_side_two_projections(self):
        squad = squad15()
        own = {r["id"]: 2.0 + (15 - r["id"]) * 0.1 for r in squad}            # low ids high: keeper 1, defenders 3-7 ...
        v2 = dict(own); v2[15] = 9.0; v2[2] = 8.0                                 # xp_v2 loves forward 15 and keeper 2
        sbs = G.side_by_side(squad, own, v2)
        self.assertEqual(len(sbs["rows"]), 15)
        self.assertEqual([slot for slot, _, _ in sbs["rows"]], list(range(1, 16)))
        own_xi = {a["id"] for slot, a, _ in sbs["rows"] if slot <= 11}
        v2_xi = {b["id"] for slot, _, b in sbs["rows"] if slot <= 11}
        self.assertIn(1, own_xi); self.assertNotIn(2, own_xi)                      # own: keeper 1 starts
        self.assertIn(2, v2_xi); self.assertNotIn(1, v2_xi)                        # xp_v2: keeper 2 starts
        self.assertIn(15, v2_xi)
        self.assertEqual(sbs["captain"][0]["id"], 1 if own[1] == max(own[i] for i in own_xi) else sbs["captain"][0]["id"])
        self.assertEqual(sbs["captain"][1]["id"], 15)                              # the highest projection in the XI
        self.assertTrue(sbs["xi_differs"]); self.assertGreater(sbs["changed"], 0)
        same = G.side_by_side(squad, own, dict(own))
        self.assertEqual(same["changed"], 0); self.assertFalse(same["xi_differs"])
        self.assertEqual(same["captain"][0]["id"], same["captain"][1]["id"])
        for slot, a, b in same["rows"]:
            self.assertEqual(a["id"], b["id"])
        self.assertEqual(same["rows"][11][1]["pos"], 1)                            # slot 12 is the sub keeper

    def test_keeper_line_and_plan_text(self):
        ks = [r for r in squad15() if r["pos"] == 1]
        line = G.keeper_line(ks, {1: 1.0}, {1: 0.95, 2: 0.05})
        self.assertEqual(line, [("N1", "CHE", 1.0, 0.95), ("N2", "ARS", None, 0.05)])   # no recorded row: None, never 0
        o, n = {"name": "A", "id": 1}, {"name": "B", "team": "BHA", "price": 5.2, "id": 2}
        self.assertEqual(G.plan_text((), ()), "roll")
        self.assertEqual(G.plan_text((o,), (n,)), "A -> B (BHA, £5.2m)")

    def test_baseline_note_default_and_agreement(self):
        squad = squad15()
        market = [dict(r, status="a") for r in squad] + [{"id": 100 + i, "name": f"M{i}", "team": "BOU", "pos": 1 + i % 4, "price": 4.5, "status": "a"} for i in range(8)]
        xp = [{r["id"]: 1.0 for r in market} for _ in range(6)]
        for w in xp:
            w[101] = 9.0                                                            # a defender worth a free move
        inp = {"squad": squad, "bank": 10.0, "k": 1, "market": market, "xp_weeks": xp, "weeks": [8, 9, 10, 11, 12, 13]}
        pool = P.build_pool(market, {r["id"] for r in squad}, xp, P.DECAY)
        b_outs, b_ins = P.baseline_plan(squad, 10.0, pool, xp[0], 1)
        self.assertEqual([i["id"] for i in b_ins], [101])
        top = {"outs": b_outs, "ins": b_ins, "hits": 0}
        b_text, p_text, n_text, default = G.baseline_note({(P.DECAY, "boris"): [top], ("no hits", "boris"): [top]}, inp)
        self.assertIn("M1 (BOU", b_text); self.assertEqual(p_text, b_text); self.assertEqual(n_text, b_text)
        self.assertIn("agrees", default)
        other = {"outs": (squad[2], squad[3]), "ins": (market[-1], market[-2]), "hits": 1}
        _, p_text, _, default = G.baseline_note({(P.DECAY, "boris"): [other]}, inp)
        self.assertNotEqual(p_text, b_text); self.assertIn("DEFAULT = the baseline", default)   # the baseline is the default, the planner the note
        _, p_text, n_text, _ = G.baseline_note({}, inp)
        self.assertEqual((p_text, n_text), ("none", "none"))
        # a different plan without a hit still differs: agreement is the same 15, not the hit count
        free_other = {"outs": (squad[2],), "ins": (market[-1],), "hits": 0}
        _, p_text, _, default = G.baseline_note({(P.DECAY, "boris"): [free_other]}, inp)
        self.assertNotEqual(p_text, b_text); self.assertIn("DEFAULT = the baseline", default)
        # with no free transfer the baseline rolls (never a hit), whatever the planner says
        b_text0, _, _, _ = G.baseline_note({(P.DECAY, "boris"): [top]}, dict(inp, k=0))
        self.assertEqual(b_text0, "roll")


class NamedPlans(unittest.TestCase):
    def setUp(self):
        self.squad = squad15()
        self.squad[13]["name"] = "Thiago"                                                 # forward 14 is Thiago
        self.market = [dict(r, status="a") for r in self.squad] + [
            {"id": 201, "name": "João Pedro", "team": "TOT", "pos": 4, "price": 7.8, "status": "a"},
            {"id": 202, "name": "Cheap Mid", "team": "BOU", "pos": 3, "price": 4.5, "status": "a"},
            {"id": 203, "name": "Star Fwd", "team": "BOU", "pos": 4, "price": 7.5, "status": "a"},   # affordable, but only for an XI forward
            {"id": 204, "name": "Keeper", "team": "BOU", "pos": 1, "price": 4.5, "status": "a"}]
        # XI players 2.0, the four bench slots (keeper 2, defender 7, midfielders 11 and 12) 1.0; week 0 only differs for the incomings
        xp0 = {r["id"]: (1.0 if r["id"] in (2, 7, 11, 12) else 2.0) for r in self.squad}
        xp0.update({201: 2.1, 202: 1.5, 203: 9.0, 204: 1.2})
        later = {**{r["id"]: 2.0 for r in self.squad}, 201: 2.0, 202: 1.0, 203: 2.0, 204: 1.0}
        self.xp = [xp0] + [dict(later) for _ in range(5)]
        self.inp = {"squad": self.squad, "bank": 3.0, "k": 1, "market": self.market, "xp_weeks": self.xp, "weeks": list(range(8, 14))}   # 3.0 + 5.0 - 7.8 = 0.2 left

    def test_named_swap_roll_and_the_bench_boost_upgrade(self):
        rows = G.named_plans(self.inp, {}, 1)
        self.assertEqual([r[0][:6] for r in rows], ["Thiago", "roll", "best s"])
        label, ev, note = rows[0]
        self.assertIsNone(note); self.assertEqual([i["id"] for i in ev["ins"]], [201])          # 'Joao Pedro' finds 'João Pedro'
        want = P.evaluate(((self.squad[13],), (self.market[-4],)), self.squad, self.xp, P.DECAY, P.SCHEDULES["boris"], 1, {})
        self.assertEqual(ev["score"], want["score"]); self.assertEqual(ev["gains"], want["gains"])  # the planner's own scorer
        self.assertAlmostEqual(ev["gains"][0], 0.2)                                                 # 2.1 replaces a 2.0 forward in the XI (+0.1) and becomes the captain (+0.1)
        _, roll, note = rows[1]
        self.assertIsNone(note); self.assertEqual((roll["score"], roll["gain"], roll["hits"], roll["lost"]), (0.0, 0.0, 0, 0.0))
        label, bb, note = rows[2]
        self.assertIsNone(note); self.assertIn("Bench Boost", label)
        self.assertIn(bb["outs"][0]["id"], (2, 7, 11, 12))                                          # a bench slot goes out ...
        self.assertEqual(bb["ins"][0]["id"], 202)                                                   # ... for the cheap midfielder: 1.5 for a 1.0
        self.assertAlmostEqual(bb["gains"][0], 0.5)                                                 # counts under Bench Boost ...
        xi_based = P.evaluate(((bb["outs"][0],), (bb["ins"][0],)), self.squad, self.xp, P.DECAY, P.SCHEDULES["boris"], 1, {})
        self.assertAlmostEqual(xi_based["gains"][0], 0.0)                                           # ... and not in the planner's XI valuation
        self.assertNotEqual(bb["ins"][0]["id"], 203)                                                # the 9.0 forward would need an XI forward out: not a bench upgrade
        # the roll is refused at the cap; a missing name and an unaffordable swap are reported, never scored
        rows5 = G.named_plans(self.inp, {}, 5)
        self.assertIsNone(rows5[1][1]); self.assertIn("never sit on 5", rows5[1][2])
        rows_x = G.named_plans(self.inp, {}, 1, swap=("Thiago", "Nobody"))
        self.assertIsNone(rows_x[0][1]); self.assertIn("missing input", rows_x[0][2]); self.assertIn("Nobody", rows_x[0][2])
        dear = dict(self.inp, bank=-5.0)
        rows_d = G.named_plans(dear, {}, 1)
        self.assertIsNone(rows_d[0][1]); self.assertIn("over budget", rows_d[0][2])
        two = [dict(r) for r in self.squad]; two[12]["name"] = "Thiago"
        rows_2 = G.named_plans(dict(self.inp, squad=two), {}, 1)
        self.assertIn("2 players named Thiago", rows_2[0][2])
        self.assertEqual(G.norm_name("JOÃO Pedro "), "joao pedro"); self.assertEqual(G.CONFIRMED_FT, {8: 1})
        self.assertIsNone(G.why_illegal(self.squad, 0.0))
        self.assertIn("from CHE", G.why_illegal(self.squad[:14] + [dict(self.squad[14], id=99, team="CHE", pos=1)], 0.0))   # a fourth from CHE
        bha3 = self.squad[:9] + [dict(self.squad[9], pos=2)] + self.squad[10:14] + [dict(self.squad[14], id=99, team="BHA", pos=2)]   # BHA: three defenders, three in all
        self.assertIn("3 GK/DEF from BHA", G.why_illegal(bha3, 0.0))
        self.assertIn("over budget", G.why_illegal(self.squad, -0.1))


class Toy(unittest.TestCase):
    def test_bundle_on_the_toy_export_reports_missing_sections(self):
        tmp = tempfile.mkdtemp()
        try:
            toy_data(tmp); toy_export(tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = G.main(["--data", tmp, "--out", out])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "gw8_pass.txt"), encoding="utf-8") as fh:
                text = fh.read()
            for title in G.SECTIONS:
                self.assertIn(title, text)                                         # every section is announced ...
            self.assertIn("BASELINE (best one-week move", text)                     # ... S7 and S8 run on the toy ...
            self.assertIn("NEXT GAMEWEEK GW8", text)
            self.assertIn("DEFAULT = the baseline", text + "the planner agrees")
            self.assertIn("section failed", text)                                  # ... and the sections the toy cannot feed say so (its sqlite lacks the real schema)
            self.assertIn("missing input: our squad: no player named Thiago", text)   # the named swap on a toy without him
            self.assertNotIn("Traceback", text)
            rec = PV.read_run(out)
            self.assertEqual(rec["tool"], "tools/gw_pass.py"); self.assertIn("gw8_pass.txt", rec["outputs"])
            with redirect_stdout(io.StringIO()):
                self.assertEqual(G.main(["--data", os.path.join(tmp, "nowhere"), "--out", out]), 2)   # no export at all: refused
        finally:
            gc.collect()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_isolation(self):
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'gw_pass')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
