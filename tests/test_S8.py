"""
tests/test_S8.py - the rolling-horizon transfer planner (prereg/S8.md).

    python -m unittest tests.test_S8
"""

import io
import itertools
import os
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
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import planner as P                                               # noqa: E402
from tests.test_S4 import toy_hist, toy_data, plant_transfer      # noqa: E402
from tests.test_S7 import toy_export                              # noqa: E402

CLUBS = ["ARS", "BOU", "BRE", "BHA", "CHE", "EVE"]


def toy_squad():
    """Our 15: 2 GK (ids 1, 2), 5 DEF (3-7), 5 MID (8-12), 3 FWD (13-15)."""
    rows = []
    for pid in range(1, 16):
        pos = 1 if pid <= 2 else 2 if pid <= 7 else 3 if pid <= 12 else 4
        rows.append({"id": pid, "name": f"P{pid}", "team": CLUBS[pid % 6], "pos": pos, "price": 5.0, "selling": 5.0, "status": "a"})
    return rows


def toy_market(n_extra=4):
    """Pool players 100+: a few per position, priced 4.0-7.0."""
    rows = []
    pid = 100
    for pos in (1, 2, 3, 4):
        for k in range(n_extra):
            pid += 1
            rows.append({"id": pid, "name": f"M{pid}", "team": CLUBS[pid % 6], "pos": pos, "price": 4.0 + k, "status": "a"})
    return rows


def toy_xp(squad, market, weeks=6):
    """xP per week: squad players 2.0 + id/100; market players 3.0 + k, varied by week."""
    out = []
    for t in range(weeks):
        xp = {r["id"]: 2.0 + r["id"] / 100 + 0.1 * t for r in squad}
        for r in market:
            xp[r["id"]] = r["price"] - 1.0 + 0.2 * ((r["id"] + t) % 3)
        out.append(xp)
    return out


def brute_force(squad, bank, pool, xp_weeks, decay, schedule, k, p_start):
    """Every 0/1/2-transfer combination, evaluated by P.evaluate, the best score."""
    singles = [(o, i) for o in squad for i in pool.get(o["pos"], [])]
    best = None
    plans = [((), ())] + [((o,), (i,)) for o, i in singles]
    for (o1, i1), (o2, i2) in itertools.combinations(singles, 2):
        if o1["id"] == o2["id"] or i1["id"] == i2["id"]:
            continue
        plans.append(((o1, o2), (i1, i2)))
    for plan in plans:
        outs, ins = plan
        rows = [r for r in squad if r["id"] not in {o["id"] for o in outs}] + list(ins)
        if not P.legal(rows, bank + sum(o["selling"] for o in outs) - sum(i["price"] for i in ins)):
            continue
        ev = P.evaluate(plan, squad, xp_weeks, decay, schedule, k, p_start)
        if ev is not None and (best is None or ev["score"] > best["score"]):
            best = ev
    return best


class Score(unittest.TestCase):
    def test_xi_value_and_captain(self):
        by_pos = {1: [3.0, 1.0], 2: [5.0, 4.0, 3.0, 2.0, 1.0], 3: [6.0, 5.0, 4.0, 3.0, 2.0], 4: [7.0, 2.0, 1.0]}
        # best formation: 3-4-3? DEF 12, MID 18, FWD 10 = 40; 3-5-2: 12+20+9=41; 4-4-2: 14+18+9=41; 4-5-1: 14+20+7=41; 5-4-1: 15+18+7=40; 5-3-2: 15+15+9=39 -> 41 + GK 3 + captain 7 = 51
        self.assertAlmostEqual(P.xi_value(by_pos), 51.0)
        self.assertIsNone(P.xi_value({2: [1.0] * 5, 3: [1.0] * 5, 4: [1.0] * 3}))        # no keeper
        self.assertIsNone(P.xi_value({1: [1.0], 2: [1.0, 1.0], 3: [1.0] * 5, 4: [1.0] * 3}))   # two defenders: no legal XI

    def test_score_hand_case_and_ft_values(self):
        self.assertAlmostEqual(P.stock_value(P.SCHEDULES["boris"], 2), 2.5)
        self.assertAlmostEqual(P.stock_value(P.SCHEDULES["boris"], 5), 3.4)                 # a fifth is worth 0
        self.assertAlmostEqual(P.lost_ft_value(P.SCHEDULES["boris"], 1, 1), 1.0)             # use 1 of 1: stock 1 instead of 2
        self.assertAlmostEqual(P.lost_ft_value(P.SCHEDULES["boris"], 1, 2), 1.0)             # a hit: the stock is 1 again
        self.assertAlmostEqual(P.lost_ft_value(P.SCHEDULES["boris"], 1, 0), 0.0)             # rolling loses nothing
        self.assertAlmostEqual(P.lost_ft_value(P.SCHEDULES["boris"], 4, 1), 0.0)             # 4 banked: the fifth is worth 0
        squad, market = toy_squad(), toy_market()
        xp = toy_xp(squad, market)
        out, inc = squad[13], next(r for r in market if r["pos"] == 4 and r["price"] == 7.0)
        ev = P.evaluate(((out,), (inc,)), squad, xp, 0.85, P.SCHEDULES["boris"], 1, {inc["id"]: 1.0})
        gains = [P.xi_value(P.squad_by_pos([r for r in squad if r is not out] + [inc], w)) - P.xi_value(P.squad_by_pos(squad, w)) for w in xp]
        self.assertAlmostEqual(ev["gain"], sum(0.85 ** t * g for t, g in enumerate(gains)))
        self.assertAlmostEqual(ev["score"], ev["gain"] - 0 - 1.0)
        self.assertEqual(P.evaluate(((), ()), squad, xp, 0.85, P.SCHEDULES["boris"], 1, {})["score"], 0.0)
        self.assertIsNone(P.evaluate(((), ()), squad, xp, 0.85, P.SCHEDULES["boris"], 5, {}))     # never leave 5 banked
        # the five verifier gaps (RULING S8 verifier FAIL item c), 1 and 2: the score charges 4 per hit; the club cap is exactly 3
        o1, o2 = squad[13], squad[14]
        i1 = next(r for r in market if r["pos"] == 4 and r["price"] == 7.0)
        i2 = next(r for r in market if r["pos"] == 4 and r["price"] == 6.0)
        hit = P.evaluate(((o1, o2), (i1, i2)), squad, xp, 0.85, P.SCHEDULES["boris"], 1, {i1["id"]: 1.0, i2["id"]: 1.0})
        self.assertEqual(hit["hits"], 1)
        self.assertAlmostEqual(hit["score"], hit["gain"] - 4.0 * 1 - hit["lost"])                      # - 4 x hits, exactly
        free = P.evaluate(((o1, o2), (i1, i2)), squad, xp, 0.85, P.SCHEDULES["boris"], 2, {})
        self.assertAlmostEqual(free["score"], free["gain"] - free["lost"]); self.assertEqual(free["hits"], 0)
        self.assertAlmostEqual(hit["gain"], free["gain"])
        self.assertEqual(P.HIT, 4.0)
        gkdef = [r for r in squad if r["pos"] in (1, 2)]; others = [r for r in squad if r["pos"] in (3, 4)]
        spread = ["ARS", "BRE", "BHA", "CHE", "EVE"]
        capped = ([dict(r, team=spread[i % 5]) for i, r in enumerate(gkdef)]                      # at most two GK/DEF per club
                  + [dict(r, team="BOU") for r in others[:4]]                                       # exactly four BOU midfielders/forwards
                  + [dict(r, team=spread[i % 4]) for i, r in enumerate(others[4:])])               # at most three per club elsewhere
        self.assertEqual(sum(1 for r in capped if r["team"] == "BOU"), 4)
        self.assertTrue(all(sum(1 for r in capped if r["team"] == c) <= 3 for c in spread))
        self.assertFalse(P.legal(capped, 1.0))                                                       # four from one club: illegal
        three = [dict(r) for r in capped]
        bou = [i for i, r in enumerate(three) if r["team"] == "BOU"]
        three[bou[-1]] = dict(three[bou[-1]], team="EVE")
        self.assertEqual(sum(1 for r in three if r["team"] == "BOU"), 3)
        self.assertTrue(P.legal(three, 1.0))                                                         # three: legal (so the cap is 3, not 4 or 5)
        self.assertEqual(P.CLUB_MAX, 3)

    def test_hit_rule(self):
        squad, market = toy_squad(), toy_market()
        xp = toy_xp(squad, market)
        o1, o2 = squad[13], squad[14]
        i1 = next(r for r in market if r["pos"] == 4 and r["price"] == 7.0)
        i2 = next(r for r in market if r["pos"] == 4 and r["price"] == 6.0)
        plan = ((o1, o2), (i1, i2))
        ev = P.evaluate(plan, squad, xp, 0.85, P.SCHEDULES["boris"], 1, {i1["id"]: 1.0, i2["id"]: 0.9})
        self.assertIsNotNone(ev); self.assertEqual(ev["hits"], 1); self.assertGreaterEqual(ev["gain"], P.HIT_MIN_GAIN)
        self.assertIsNone(P.evaluate(plan, squad, xp, 0.85, P.SCHEDULES["boris"], 1, {i1["id"]: 1.0, i2["id"]: 0.7}))   # an incoming P(start) < 0.8
        tiny = [{k: (v if k not in (i1["id"], i2["id"]) else 2.3) for k, v in w.items()} for w in xp]          # gain below 4
        self.assertIsNone(P.evaluate(plan, squad, tiny, 0.85, P.SCHEDULES["boris"], 1, {i1["id"]: 1.0, i2["id"]: 1.0}))
        # a gain between 4 and 5.5 is refused: the buffer, not the bare hit, is the bar
        for step in range(1, 200):
            lift = 0.05 * step
            mid = [{k: (v if k not in (i1["id"], i2["id"]) else w[squad[13]["id"]] + lift) for k, v in w.items()} for w in xp]
            ev_mid = P.evaluate(plan, squad, mid, 0.85, P.SCHEDULES["boris"], 2, {})       # no hit: read the gain
            if ev_mid and 4.0 <= ev_mid["gain"] < P.HIT_MIN_GAIN:
                break
        else:
            self.fail("no toy gain between 4 and 5.5")
        self.assertIsNone(P.evaluate(plan, squad, mid, 0.85, P.SCHEDULES["boris"], 1, {i1["id"]: 1.0, i2["id"]: 1.0}))
        one = [{**w, i1["id"]: 2.0, i2["id"]: 2.0} for w in xp]                                                  # all the gain in one fixture
        one[0][i1["id"]] = 20.0
        self.assertIsNone(P.evaluate(plan, squad, one, 0.85, P.SCHEDULES["boris"], 1, {i1["id"]: 1.0, i2["id"]: 1.0}))
        self.assertIsNotNone(P.evaluate(plan, squad, xp, 0.85, P.SCHEDULES["boris"], 2, {}))                     # two banked: no hit, no P(start) rule
        # exploratory variants (RULING morning 19 Oct item 2): no hits; the buffer at 3.0
        ps = {i1["id"]: 1.0, i2["id"]: 1.0}
        self.assertIsNone(P.evaluate(plan, squad, xp, 0.85, P.SCHEDULES["boris"], 1, ps, hits_allowed=False))   # a hit: refused outright
        self.assertIsNotNone(P.evaluate(plan, squad, xp, 0.85, P.SCHEDULES["boris"], 2, {}, hits_allowed=False))  # no hit needed: allowed
        for step in range(1, 400):
            lift = 0.05 * step
            band = [{k: (v if k not in (i1["id"], i2["id"]) else w[squad[13]["id"]] + lift) for k, v in w.items()} for w in xp]
            ev_band = P.evaluate(plan, squad, band, 0.85, P.SCHEDULES["boris"], 2, {})
            if ev_band and P.HIT_MIN_GAIN <= ev_band["gain"] < P.HIT + 3.0:
                break
        else:
            self.fail("no toy gain between 5.5 and 7.0")
        self.assertIsNotNone(P.evaluate(plan, squad, band, 0.85, P.SCHEDULES["boris"], 1, ps))                  # buffer 1.5: a hit
        self.assertIsNone(P.evaluate(plan, squad, band, 0.85, P.SCHEDULES["boris"], 1, ps, buffer=3.0))          # buffer 3.0: refused
        big = [{k: (v if k not in (i1["id"], i2["id"]) else v + 10.0) for k, v in w.items()} for w in xp]
        self.assertIsNotNone(P.evaluate(plan, squad, big, 0.85, P.SCHEDULES["boris"], 1, ps, buffer=3.0))        # a large gain clears 7.0
        scored, _ = P.rank_plans(squad, 0.0, market, xp, 1, ps, hits_allowed=False)
        self.assertTrue(all(ev["hits"] == 0 for ev in scored))
        self.assertEqual(P.EXPLORATORY, (("no hits", {"hits_allowed": False}), ("hit buffer 3.0", {"buffer": 3.0})))

    def test_exhaustive_equals_brute_force_and_caps(self):
        squad, market = toy_squad(), toy_market()
        xp = toy_xp(squad, market)
        p_start = {r["id"]: 1.0 for r in market}
        pool = P.build_pool(market, {r["id"] for r in squad}, xp, 0.85, n=P.POOL)
        singles = [(o, i) for o in squad for i in pool.get(o["pos"], [])]
        for bank in (0.0, 2.0, 10.0):
            scored, _ = P.rank_plans(squad, bank, market, xp, 1, p_start, 0.85, P.SCHEDULES["boris"], pool)
            want = brute_force(squad, bank, pool, xp, 0.85, P.SCHEDULES["boris"], 1, p_start)
            self.assertAlmostEqual(scored[0]["score"], want["score"])
            # the candidate set is exactly the legal 0/1/2-transfer combinations (each unordered pair once)
            keys = set()
            for outs, ins in P.plan_candidates(squad, bank, pool):
                keys.add((tuple(sorted(o["id"] for o in outs)), tuple(sorted(i["id"] for i in ins))))
            want_keys = {((), ())}
            for o, i in singles:
                if P.legal([r for r in squad if r["id"] != o["id"]] + [i], bank + o["selling"] - i["price"]):
                    want_keys.add(((o["id"],), (i["id"],)))
            for (o1, i1), (o2, i2) in itertools.combinations(singles, 2):
                if o1["id"] == o2["id"] or i1["id"] == i2["id"]:
                    continue
                rows = [r for r in squad if r["id"] not in (o1["id"], o2["id"])] + [i1, i2]
                if P.legal(rows, bank + o1["selling"] + o2["selling"] - i1["price"] - i2["price"]):
                    want_keys.add((tuple(sorted((o1["id"], o2["id"]))), tuple(sorted((i1["id"], i2["id"])))))
            self.assertEqual(keys, want_keys)
            self.assertEqual(len(keys), len(P.plan_candidates(squad, bank, pool)))
        # caps: a candidate over budget; a fourth from one club (four midfielders: the GK+DEF cap untouched);
        # a third GK+DEF from one club (one keeper, two defenders: the club cap untouched)
        self.assertFalse(P.legal(squad, -0.1))
        four_mid = squad[:7] + [dict(r, team="ARS") for r in squad[7:11]] + squad[11:]
        self.assertFalse(P.legal(four_mid, 1.0))
        three_gkdef = ([dict(squad[0], team="CHE"), squad[1], dict(squad[2], team="CHE"), dict(squad[3], team="CHE")]
                       + [dict(r, team="ARS") if r["team"] == "CHE" else r for r in squad[4:]])   # exactly three CHE, all GK/DEF
        self.assertFalse(P.legal(three_gkdef, 1.0))
        self.assertTrue(P.legal(squad, 0.0))
        # the pool is the top 25 per position by decayed xP
        big = [{"id": 1000 + k, "name": f"B{k}", "team": CLUBS[k % 6], "pos": 1 + k % 4, "price": 5.0, "status": "a"} for k in range(160)]
        xp_big = [{r["id"]: (r["id"] % 37) / 10 + 0.1 * t for r in big} for t in range(6)]
        pool_big = P.build_pool(big, set(), xp_big, 0.85)
        for pos in (1, 2, 3, 4):
            self.assertEqual(len(pool_big[pos]), P.POOL)
            self.assertEqual(P.POOL, 25)
            ranked = sorted((r for r in big if r["pos"] == pos), key=lambda r: (-P.decayed(xp_big, r["id"], 0.85), r["id"]))
            self.assertEqual([r["id"] for r in pool_big[pos]], [r["id"] for r in ranked[:25]])


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        toy_hist(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_point_in_time_and_baseline_never_hits(self):
        with mock.patch.object(P, "REPLAY_LAST", 6):
            rp = P.Replay(self.tmp.name)
            fc5, ps, pos = rp.forecasts(5)
            self.assertEqual(sorted(fc5), [5, 6])
            rp2 = P.Replay(self.tmp.name)
            for r in rp2.c["rows"]:
                if r["event"] >= 5:
                    r["pts"] = 50; r["xg"] = 9.0
            self.assertEqual(rp2.forecasts(5)[0], fc5)
            with mock.patch.object(E, "canonical_through", lambda c, gw: E.check_canonical(dict(c, through_gw=gw))):
                self.assertNotEqual(P.Replay(self.tmp.name).forecasts(5)[0], fc5)
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            with mock.patch.object(P, "REPLAY_LAST", 6):
                base = P.Replay(tmp).forecasts(5)[0]
                plant_transfer(tmp, 3, 6, 2)                                   # a club change in round 6: invisible at origin 5
                self.assertEqual(P.Replay(tmp).forecasts(5)[0], base)
        squad, market = toy_squad(), toy_market()
        xp = toy_xp(squad, market)
        pool = P.build_pool(market, {r["id"] for r in squad}, xp, 0.85)
        plan = P.baseline_plan(squad, 10.0, pool, xp[0], 1)
        self.assertEqual(len(plan[0]), 1)                                      # one move, no hit
        self.assertEqual(P.baseline_plan(squad, 10.0, pool, xp[0], 0), ((), ()))
        worse = [{**w, **{r["id"]: 0.0 for r in market}} for w in xp]
        self.assertEqual(P.baseline_plan(squad, 10.0, pool, worse[0], 1), ((), ()))   # no positive gain: roll

    def test_replay_runs_and_scores(self):
        buf = io.StringIO()
        with mock.patch.object(P, "REPLAY_LAST", 6):
            res = P.replay(self.tmp.name, n_squads=2, seed=7, out=lambda s: buf.write(s + chr(10)), first=5, last=6, check_decays=True)
        self.assertEqual(len(res["results"]), 2)
        for r in res["results"]:
            self.assertEqual(r["baseline"]["hits"], 0)
            self.assertGreaterEqual(r["planner"]["transfers"], r["planner"]["hits"])
        self.assertIn("pre-registered bar", buf.getvalue())
        self.assertIn("robustness", buf.getvalue())
        self.assertNotIn("EXPLORATORY", buf.getvalue())
        buf2 = io.StringIO()
        with mock.patch.object(P, "REPLAY_LAST", 6):
            res2 = P.replay(self.tmp.name, n_squads=2, seed=7, out=lambda s: buf2.write(s + chr(10)), first=5, last=6,
                            check_decays=False, hits_allowed=False)
            res3 = P.replay(self.tmp.name, n_squads=2, seed=7, out=print if False else (lambda s: None), first=5, last=6,
                            check_decays=False, buffer=3.0)
        self.assertTrue(all(r["planner"]["hits"] == 0 for r in res2["results"]))      # no hits: never a hit
        with mock.patch.object(P, "REPLAY_LAST", 6), mock.patch.object(P, "rank_plans", wraps=P.rank_plans) as rp:
            P.replay(self.tmp.name, n_squads=1, seed=7, out=lambda s: None, first=5, last=5, check_decays=False, hits_allowed=False, buffer=2.5)
        self.assertTrue(rp.call_args_list)
        self.assertTrue(all(c.args[9] is False and c.args[10] == 2.5 for c in rp.call_args_list))   # the variants reach every ranking
        # gaps 3-4: the replay reads the realised points of round t itself and charges 4 per hit; a forced two-transfer plan each week
        def forced(rows, bank, market, xp_weeks, k, p_start, decay, schedule, pool, *rest):
            mids = [r for r in rows if r["pos"] == 3][:2]
            ins = [r for r in pool[3] if r["id"] not in {x["id"] for x in rows}][:2]
            return ([{"outs": tuple(mids), "ins": tuple(ins), "score": 1.0, "gain": 1.0, "gains": [0.0] * len(xp_weeks),
                      "hits": max(0, 2 - k), "lost": 0.0, "used": 2}], pool)
        seen_t = []

        def realised(self_, rows, t, xp):
            seen_t.append(t)
            return 100.0
        with mock.patch.object(P, "REPLAY_LAST", 6), mock.patch.object(P, "rank_plans", side_effect=forced), \
                mock.patch.object(P.Replay, "realised", realised):
            res4 = P.replay(self.tmp.name, n_squads=1, seed=7, out=lambda s: None, first=5, last=6, check_decays=False)
        pl = res4["results"][0]["planner"]
        self.assertEqual((pl["hits"], pl["transfers"]), (2, 4))                                     # 1 FT a week, two moves: a hit each week
        self.assertAlmostEqual(pl["pts"], 2 * 100.0 - 4.0 * 2)                                     # realised minus 4 per hit
        self.assertEqual(sorted(seen_t), [5, 5, 6, 6])                                              # round t, for the planner and the baseline
        self.assertEqual(res4["results"][0]["baseline"]["hits"], 0)
        # gap 4, inside realised(): the points come from round t's actuals, not round t + 1's
        rp = P.Replay(self.tmp.name)
        squad0 = CH.sample_squads(CH.gw1_candidates(rp.rp.hist), 1, 7)[0]
        rows5 = rp.squad_rows(squad0, 5)
        fc, _, _ = rp.forecasts(5)
        xp5 = fc[min(fc)]
        base = rp.realised(rows5, 5, xp5)
        saved6 = dict(rp.rp.actual[6])
        rp.rp.actual[6] = {pid: (99.0, 90) for pid in rp.rp.actual[6]}
        self.assertEqual(rp.realised(rows5, 5, xp5), base)                                          # round 6 altered: unchanged
        rp.rp.actual[6] = saved6
        rp.rp.actual[5] = {pid: (99.0, 90) for pid in rp.rp.actual[5]}
        self.assertNotEqual(rp.realised(rows5, 5, xp5), base)                                       # round 5 altered: moves
        self.assertIsNone(res2["pass"]); self.assertIsNone(res3["pass"])                 # exploratory: no bar
        self.assertIn("no hits; baseline", buf2.getvalue()); self.assertIn("EXPLORATORY", buf2.getvalue())
        self.assertIn("exploratory line: no bar, no adoption", buf2.getvalue())
        self.assertNotIn("pre-registered bar", buf2.getvalue())
        self.assertEqual([r["baseline"] for r in res2["results"]], [r["baseline"] for r in res["results"]])   # the baseline is untouched


class CLI(unittest.TestCase):
    def test_live_cli_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_data(tmp); toy_export(tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = P.main(["--data", tmp, "--out", out])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "planner_live.txt"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("price predictor: no source", text)
            self.assertIn("TOP 5 PLANS  decay 0.85, schedule boris", text)
            self.assertIn("schedule solver", text)
            self.assertIn("exploratory, no hits (Boris's schedule, no bar): top plan", text)
            self.assertIn("exploratory, hit buffer 3.0 (Boris's schedule, no bar): top plan", text)
            # the toy export yields no hit plan at all, so the variants are checked on what the ranking is asked for
            with mock.patch.object(P, "rank_plans", wraps=P.rank_plans) as rp:
                res = P.live(tmp, out=lambda s: None)
            kws = [c.kwargs for c in rp.call_args_list]
            self.assertEqual(sum(1 for k in kws if k.get("hits_allowed") is False), 1)               # the no-hit line
            self.assertEqual(sum(1 for k in kws if k.get("buffer") == 3.0), 1)                       # the buffer-3.0 line
            self.assertEqual(len(res[("no hits", "boris")]), len([e for e in res[(P.DECAY, "boris")] if e["hits"] == 0]))
            self.assertEqual(P.HORIZON, 6)                                                           # gap 5: six weeks reach every ranking
            real_weeks = P.CH.own_week_points

            def eight_weeks(d, log_rows, *a, **kw):                                                 # the toy offers three weeks: offer eight
                weeks, pts, src = real_weeks(d, log_rows, *a, **kw)
                extra = [weeks[-1] + i for i in range(1, 6)]
                return weeks + extra, {**pts, **{w: dict(pts[weeks[-1]]) for w in extra}}, src
            with mock.patch.object(P.CH, "own_week_points", side_effect=eight_weeks), \
                    mock.patch.object(P, "rank_plans", wraps=P.rank_plans) as rp8:
                P.live(tmp, out=lambda s: None)
            self.assertTrue(rp8.call_args_list)
            self.assertTrue(all(len(c.args[3]) == 6 for c in rp8.call_args_list))                  # the ranking sees six weeks, no more
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'planner')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
