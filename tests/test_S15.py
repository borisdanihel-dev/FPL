"""S15 - the unified squad builder and its A/B against the frozen three-layer
rule (tools/builder.py; prereg/S15.md, Part F item F-G). Hermetic: synthetic
markets, test_fpl's synthetic export, S6b's toy season as a 2024-25 root
and S6d's toy 2026/27 folder, all in temporary folders; no real data."""
import io
import os
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import builder as B                                               # noqa: E402
import xp_v2_replay as X                                          # noqa: E402
from test_fpl import make_export                                  # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402
from tests.test_S6b import toy_rules_root                         # noqa: E402
from tests.test_S6c import add_s6c_inputs                         # noqa: E402
from tests.test_S6f import zero_counts                            # noqa: E402

TEAMS = ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH")


def market(n_per=(6, 14, 14, 9), seed=3):
    """A synthetic market: ids 1.., positions by n_per, eight clubs, prices 4.0-12.0."""
    rng, out, pid = random.Random(seed), [], 0
    for pos, n in zip((1, 2, 3, 4), n_per):
        for _ in range(n):
            pid += 1
            out.append({"id": pid, "name": f"P{pid}", "team": TEAMS[pid % len(TEAMS)], "pos": pos,
                        "price": round(4.0 + rng.random() * 8.0, 1)})
    return out


def matrix(mk, weeks=6, seed=5):
    rng = random.Random(seed)
    return [{p["id"]: round(rng.random() * (2.0 + p["price"] / 2), 3) for p in mk if rng.random() > 0.1} for _ in range(weeks)]


class Objective(unittest.TestCase):
    def test_week_value_by_hand(self):
        mk = market()
        sq = B.greedy(mk, matrix(mk), 100.0, False)
        xp = matrix(mk, 1)[0]
        v, xi, form = B.week_value(sq, xp)
        rows = [dict(p, proj=xp.get(p["id"], 0.0)) for p in sq]
        best = E._best_xi(rows)
        self.assertAlmostEqual(sum(p["proj"] for p in best), sum(xp.get(p["id"], 0.0) for p in xi))   # fpl_edge's best XI
        ids = {p["id"] for p in xi}
        bench = sorted((p for p in sq if p["id"] not in ids and p["pos"] != 1), key=lambda p: (-xp.get(p["id"], 0.0), p["id"]))
        gk = [p for p in sq if p["id"] not in ids and p["pos"] == 1]
        want = (sum(xp.get(p["id"], 0.0) for p in xi) + max(xp.get(p["id"], 0.0) for p in xi)
                + 0.30 * xp.get(bench[0]["id"], 0.0) + 0.10 * xp.get(bench[1]["id"], 0.0) + 0.03 * xp.get(bench[2]["id"], 0.0)
                + 0.03 * xp.get(gk[0]["id"], 0.0))
        self.assertAlmostEqual(v, want)
        self.assertEqual(sum(form), 10); self.assertEqual(Counter(p["pos"] for p in xi)[1], 1)
        full = B.week_value(sq, xp, bench_full=True)[0]
        self.assertAlmostEqual(full, sum(xp.get(p["id"], 0.0) for p in sq) + max(xp.get(p["id"], 0.0) for p in xi))
        forced = B.week_value(sq, xp, formation=(4, 3, 3))
        self.assertEqual(forced[2], (4, 3, 3)); self.assertLessEqual(forced[0], v + 1e-12)
        weeks = matrix(mk)
        self.assertAlmostEqual(B.objective(sq, weeks), sum(0.85 ** k * B.week_value(sq, w)[0] for k, w in enumerate(weeks)))

    def test_legal(self):
        mk = market()
        sq = B.greedy(mk, matrix(mk), 100.0, False)
        self.assertTrue(B.legal(sq, 100.0, False))
        self.assertFalse(B.legal(sq[:-1], 100.0, False))                                   # the quota
        self.assertFalse(B.legal(sq[:-1] + [sq[0]], 100.0, False))                         # distinct
        self.assertFalse(B.legal(sq, sum(p["price"] for p in sq) - 0.1, False))            # the budget
        same = [dict(p, team="AAA") for p in sq]
        self.assertFalse(B.legal(same, 100.0, False))                                      # 3 per club
        spread = [dict(p, team=f"T{i}") for i, p in enumerate(sq)]
        three = [dict(p, team="AAA") if i < 3 else p for i, p in enumerate(spread)]
        four = [dict(p, team="AAA") if i < 4 else p for i, p in enumerate(spread)]
        self.assertTrue(B.legal(three, 100.0, False)); self.assertFalse(B.legal(four, 100.0, False))   # exactly 3, never 4
        gd = [dict(p, team="AAA" if p["pos"] in (1, 2) and i < 3 else f"Z{i}") for i, p in enumerate(sorted(sq, key=lambda p: p["pos"]))]
        self.assertTrue(B.legal(gd, 100.0, False)); self.assertFalse(B.legal(gd, 100.0, True))   # the GK+DEF cap toggle


class Search(unittest.TestCase):
    def test_greedy_local_search_and_build(self):
        mk, weeks = market(), matrix(market())
        g = B.greedy(mk, weeks, 100.0, False)
        self.assertIsNotNone(g)
        sq, v = B.local_search(g, mk, weeks, 100.0, False)
        self.assertGreaterEqual(v, B.objective(g, weeks) - 1e-12)                          # never worsens
        self.assertTrue(B.legal(sq, 100.0, False)); self.assertAlmostEqual(v, B.objective(sq, weeks))
        ids = {p["id"] for p in sq}
        pool = B.build_pool(mk, weeks, ids)
        for o in sq:                                                                        # a local optimum: no single swap improves
            for i in pool.get(o["pos"], []):
                new = [p for p in sq if p["id"] != o["id"]] + [i]
                if B.legal(new, 100.0, False):
                    self.assertLessEqual(B.objective(new, weeks), v + 1e-9)
        other = B.greedy(mk, weeks, 90.0, False)
        best, bv = B.build(mk, weeks, 100.0, False, starts=[other])
        self.assertGreaterEqual(bv, B.local_search(other, mk, weeks, 100.0, False)[1] - 1e-9)   # at least every start's end
        capped, cv = B.build(mk, weeks, 100.0, True)
        self.assertTrue(B.legal(capped, 100.0, True)); self.assertLessEqual(cv, bv + 1e-9)
        self.assertEqual(B.build_pool(mk, weeks, ids).keys(), {1, 2, 3, 4})
        self.assertTrue(all(len(v) <= B.POOL and not ({p["id"] for p in v} & ids) for v in pool.values()))   # S8's pool, outside the 15


class Gaps(unittest.TestCase):
    """Cases built so that one rule alone decides the answer."""

    def squad15(self):
        out, pid = [], 0
        for pos, n in ((1, 2), (2, 5), (3, 5), (4, 3)):
            for _ in range(n):
                pid += 1
                out.append({"id": pid, "name": f"S{pid}", "team": f"C{pid}", "pos": pos, "price": 5.0})
        return out

    def test_only_a_pair_improves(self):
        sq = self.squad15()
        xp = {p["id"]: 1.0 for p in sq}
        a = {"id": 101, "name": "A", "team": "CA", "pos": 3, "price": 6.0}                  # better, one more
        b = {"id": 102, "name": "B", "team": "CB", "pos": 2, "price": 4.0}                  # a little worse, one less
        xp.update({101: 5.0, 102: 0.9})
        mk, weeks = sq + [a, b], [xp]
        for o in sq:                                                                        # no single swap improves
            for i in (a, b):
                if i["pos"] == o["pos"]:
                    new = [p for p in sq if p["id"] != o["id"]] + [i]
                    self.assertFalse(B.legal(new, 75.0, False) and B.objective(new, weeks) > B.objective(sq, weeks) + 1e-9)
        out, v = B.local_search(sq, mk, weeks, 75.0, False)
        self.assertEqual({101, 102} <= {p["id"] for p in out}, True)                         # the pair found
        self.assertGreater(v, B.objective(sq, weeks))

    def test_the_pool_is_outside_the_15(self):
        sq = self.squad15()
        xp = {p["id"]: 2.0 for p in sq}
        fw = [p["id"] for p in sq if p["pos"] == 4]
        xp.update({fw[0]: 3.0, fw[1]: 3.0, fw[2]: 1.0})
        c = {"id": 201, "name": "C", "team": "CC", "pos": 4, "price": 5.0}
        xp[201] = 2.5
        out, v = B.local_search(sq, sq + [c], [xp], 75.0, False, pool_n=2)
        self.assertIn(201, {p["id"] for p in out})                                         # the top 2 outside the 15 hold C

    def test_layer_one_at_the_frozen_share(self):
        players = [{"id": 1, "name": "A", "team": "T1", "pos": 3, "price": 5.0, "status": "a", "mins_last4": 216.0},   # 0.600
                   {"id": 2, "name": "B", "team": "T1", "pos": 3, "price": 5.0, "status": "a", "mins_last4": 252.0}]   # 0.700
        cands, exc = B.rule_candidates(players, {"players": {}}, {6: {"T1": [("T2", True)]}}, [6], {"T1": 4}, {6: {1: 1.0, 2: 1.0}})
        self.assertEqual([c["id"] for c in cands[3]], [2]); self.assertEqual(exc, {f"minutes share <= {E.FLAG_SHARE_MAX}": 1})

    def test_the_share_bar_is_60_percent(self):
        recs = [{"builder": 10.0, "rule": 0.0, "builder_proj": 1.0, "rule_proj": 0.0} for _ in range(11)] + \
               [{"builder": 0.0, "rule": 0.1, "builder_proj": 1.0, "rule_proj": 0.0} for _ in range(9)]
        v = B.verdict(recs)
        self.assertGreater(v["boot"]["lo"], 0); self.assertAlmostEqual(v["share"], 0.55); self.assertFalse(v["pass"])


class RulePort(unittest.TestCase):
    def test_equals_wildcard_candidates_and_the_frozen_build(self):
        d = make_export(gw=5)
        want, weeks, exc = E.wildcard_candidates(d)
        canon = E.canonical_from_export(d)
        inp = E.reliability_inputs(canon, gws_played=d["gameweek"])
        fx = E.week_fixtures(d)
        played = defaultdict(int)
        for f in d.get("fixtures_played") or []:
            if f["event"] in range(5 - 4 + 1, 6):
                played[f["home"]] += 1; played[f["away"]] += 1
        pairings = {w: {team: fx[team].get(w, []) for team in fx} for w in weeks}
        mat = {w: {} for w in weeks}
        for p in d["all_players"]:
            for w in weeks:
                v = E.project_week(p["id"], p, inp, fx, w, E.ALL_TERMS)
                if v is not None:
                    mat[w][p["id"]] = v
        players = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
                    "status": p["status"], "mins_last4": p.get("mins_last4")} for p in d["all_players"]]
        got, gexc = B.rule_candidates(players, inp, pairings, weeks, dict(played), mat)
        keys = ("id", "sum6", "nfix", "nfix_later", "p_start", "xgi90", "key", "rank", "price", "team", "share")
        for pos in (1, 2, 3, 4):
            self.assertEqual([{k: c[k] for k in keys} for c in got[pos]], [{k: c[k] for k in keys} for c in want[pos]], pos)
        self.assertEqual(gexc, exc)
        self.assertEqual(B.quota_split(100.0), E.budget_split(dict(d, squads=[]), 100.0))   # no squad: the quota's shares
        with mock.patch.object(B.E, "build_three_layer_squad", wraps=E.build_three_layer_squad) as frozen:
            sq, spent = B.rule_squad(got)
        frozen.assert_called_once()
        self.assertEqual(frozen.call_args.args[3], (4, 3, 3)); self.assertEqual(frozen.call_args.args[1], 100.0)
        w_sq, w_spent, _ = E.build_three_layer_squad(want, 100.0, B.quota_split(100.0), (4, 3, 3), B.QUOTA)
        self.assertEqual([p["id"] for p in sq], [c["id"] for c in w_sq]); self.assertEqual(spent, w_spent)


class Bar(unittest.TestCase):
    def rec(self, b, r, bp=10.0, rp=9.0):
        return {"builder": b, "rule": r, "builder_proj": bp, "rule_proj": rp}

    def test_the_three_conditions(self):
        ok = [self.rec(10 + i % 3, 9) for i in range(20)]
        self.assertTrue(B.verdict(ok)["pass"])
        self.assertFalse(B.verdict(ok[:-1] + [self.rec(10, 9, bp=8.0)])["pass"])            # projected below the rule once
        mixed = [self.rec(30, 0) for _ in range(5)] + [self.rec(0, 1) for _ in range(15)]   # mean > 0, share 0.25
        v = B.verdict(mixed)
        self.assertGreater(v["boot"]["mean"], 0); self.assertFalse(v["pass"]); self.assertEqual(v["share"], 0.25)
        with mock.patch.object(B.BT, "bootstrap_mean", return_value={"mean": 1.0, "lo": -0.1, "hi": 2.0, "n": 20, "p": 0.1}):
            self.assertFalse(B.verdict(ok)["pass"])                                           # the CI must exclude 0
        self.assertEqual(B.verdict([self.rec(9, 9)] * 3)["share"], 1.0)                     # ties count as >=


class Season(unittest.TestCase):
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
        return B.P.Season2425(self.hist, self.prior, self.odds, self.rescored)

    def test_a_date_and_point_in_time(self):
        s = self.season()
        with mock.patch.object(B, "build", wraps=B.build) as bld:
            r = B.one_date(s, 5)
        first = bld.call_args_list[0]
        self.assertEqual(sorted(p["id"] for p in first.kwargs["starts"][0]), r["rule_ids"])   # the rule's squad is a start
        self.assertEqual([c.args[3] for c in bld.call_args_list], [False, True])            # the A/B without the cap; its cost with it
        self.assertGreaterEqual(r["builder_proj"], r["rule_proj"] - 1e-9)                    # the rule's squad is a start
        self.assertGreaterEqual(r["builder_proj"], r["cap_proj"] - 1e-9)
        self.assertEqual(len(r["builder_ids"]), 15); self.assertEqual(len(r["rule_ids"]), 15)
        o = B.Origin(s, 5)
        real_market = s.market
        with mock.patch.object(s, "market", side_effect=lambda t, pos: real_market(t, pos) + [{"id": 9999, "name": "AM", "team": "AAA",
                                                                                              "pos": 0, "price": 1.0, "status": "a"}]):
            self.assertNotIn(9999, {p["id"] for p in B.Origin(s, 5).market})                # no assistant manager in the market
        want = B.realised(s, [p for p in o.market if p["id"] in set(r["builder_ids"])], o)
        self.assertAlmostEqual(want, r["builder"])
        self.assertAlmostEqual(r["builder"], sum(s.realised([{"id": p["id"], "pos": p["pos"], "team": p["team"], "name": "x"}
                                                                for p in o.market if p["id"] in set(r["builder_ids"])], u, o.fc[u])
                                                 for u in o.weeks))
        s2 = self.season()
        for g in range(5, s2.through + 1):
            for row in s2.hist["c"]["rows"]:
                if row["event"] == g:
                    row["minutes"], row["pts"] = 90, 30
        o2 = B.Origin(s2, 5)
        self.assertEqual(o2.players, o.players); self.assertEqual(o2.played, o.played)       # rows of rounds >= t never read
        self.assertEqual([p["mins_last4"] for p in o.players],
                         [sum(row["minutes"] or 0 for row in s.hist["c"]["rows"]
                              if row["player_id"] == p["id"] and 1 <= row["event"] <= 4) for p in o.players])


class Live(unittest.TestCase):
    def test_wildcard_freehit_bb(self):
        from tests.test_S6d import toy_live, toy_hist_root, gw9_snapshot
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_live(tmp); toy_hist_root(hist)
            gw9_snapshot(tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
            from datetime import datetime, timezone
            with mock.patch.object(B.E, "selling_budget", return_value=(100.0, "")):
                outs = {}
                for mode in ("wildcard", "freehit", "bb"):
                    lines = []
                    with mock.patch.object(B, "build", wraps=B.build) as bld:
                        res = B.live(tmp, hist, mode, lines.append)
                    self.assertEqual([c.args[3] for c in bld.call_args_list], [True, False])     # live: the cap on, its cost off
                    outs[mode] = (res, lines)
                    self.assertTrue(lines[0].startswith(f"BUILDER  --{mode}  GW9")); self.assertIn("information only", lines[0])
                    self.assertIn("the GK+DEF 2-per-club cap ON", lines[1])
                    self.assertTrue(B.legal(res["squad"], 100.0, True)); self.assertLessEqual(res["value"], res["value_off"] + 1e-9)
            self.assertIn("GW9-14", outs["wildcard"][1][0])
            for mode in ("freehit", "bb"):
                self.assertIn("GW9 from", outs[mode][1][0])                                    # one week, no decay
            self.assertIn("odds", outs["freehit"][1][0])
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)


class Isolation(unittest.TestCase):
    def test_cli_and_isolation(self):
        out = tempfile.mkdtemp()
        try:
            with redirect_stdout(io.StringIO()):
                self.assertEqual(B.main(["--test", "--hist", os.path.join(out, "none"), "--out", out]), 2)
        finally:
            shutil.rmtree(out, ignore_errors=True)
        code = ("import sys; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "print([m for m in sys.modules if m.split('.')[0] in ('builder', 'planner_2425', 'planner')])")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
