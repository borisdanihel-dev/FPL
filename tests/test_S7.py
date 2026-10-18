"""
tests/test_S7.py - the first-half chip calculator (prereg/S7.md acceptance tests).

    python -m unittest tests.test_S7
"""

import csv
import gzip
import io
import json
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
import chips as C                                                 # noqa: E402
from tests.test_S4 import toy_hist, toy_data, plant_transfer, TEAMS, MERGED_COLS   # noqa: E402

CLUBS = ["ARS", "BOU", "BRE", "BHA", "CHE", "EVE"]


def toy_export(tmp, own_rows=True, selling=True):
    """A small live world: 30 players over six clubs, our 15, selling prices,
    GW8-10 fixtures, deadlines, and a log with own rows for GW8."""
    players, pid = [], 0
    for ci, club in enumerate(CLUBS):
        for pos, n in ((1, 1), (2, 2), (3, 1), (4, 1)):
            for k in range(n):
                pid += 1
                players.append({"id": pid, "web_name": f"P{pid}", "team": club, "pos": pos,
                                "price": 4.0 + 0.5 * (pid % 5), "status": "a", "mins_last4": 360,
                                "pts_last4": 4 + (pid % 7), "chance_next_round": None, "starts_last4": 4})
    players[1]["status"] = "d"                 # a doubtful player: outside the gate
    mine = [1, 11, 2, 7, 12, 17, 22, 4, 9, 14, 19, 24, 10, 20, 25]   # 2 GK, 5 DEF, 5 MID, 3 FWD, 3 per club
    pos_of = {p["id"]: p["pos"] for p in players}
    assert sorted(pos_of[i] for i in mine) == [1, 1] + [2] * 5 + [3] * 5 + [4] * 3, sorted(pos_of[i] for i in mine)
    squads = []
    for slot, i in enumerate(mine, 1):
        p = next(q for q in players if q["id"] == i)
        row = {"entry_id": 1, "entry_name": "Us", "slot": slot, "player_id": i, "web_name": p["web_name"],
               "team": p["team"], "pos": p["pos"], "price": p["price"], "multiplier": 1,
               "is_captain": 0, "is_vice": 0, "gw_points": 0, "minutes": 0}
        if selling:
            row.update({"purchase_price": p["price"], "selling_price": p["price"]})
        squads.append(row)
    fixtures = []
    for ev in (8, 9, 10):
        pairs = [(0, 1), (2, 3), (4, 5)] if ev % 2 == 0 else [(1, 2), (3, 4), (5, 0)]
        for h, a in pairs:
            fixtures.append({"event": ev, "home": CLUBS[h], "away": CLUBS[a], "h_fdr": 3, "a_fdr": 3,
                             "kickoff_time": f"2026-10-{20 + ev}T14:00:00Z"})
    if not selling:
        pass
    d = {"schema": 2, "generated": "2026-10-18T18:00:00+00:00", "league_id": 1, "my_entry": 1, "gameweek": 7,
         "standings": [{"entry_id": 1, "entry_name": "Us", "bank": 15, "value": 1000}],
         "chips_used": [{"entry_name": "Us", "name": "wildcard", "event": 6}],
         "squads": squads, "all_players": players, "player_history": [], "fixtures_played": [],
         "fixtures_next6": fixtures, "player_gw_recent": [],
         "events": [{"event": ev, "finished": 0, "data_checked": 0, "deadline_time": f"2026-10-{20 + ev}T11:00:00Z"}
                    for ev in (7, 8, 9, 10)],
         "fixtures_status": [], "teams": [], "league_ownership": [], "transfers": []}
    os.makedirs(os.path.join(tmp, "exports"), exist_ok=True)
    with gzip.open(os.path.join(tmp, "exports", "fpl_export_gw7_2026-10-18.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump(d, fh)
    log = os.path.join(tmp, E.LOG_PATH)
    new = not os.path.exists(log)
    with open(log, "a", encoding="utf-8", newline="") as fh:        # appends to toy_data's log when present
        w = csv.DictWriter(fh, fieldnames=E.LOG_FIELDS)
        if new:
            w.writeheader()
        if own_rows:
            for p in players:
                w.writerow({"made_at": "2026-10-27T21:00:00+00:00", "source": "own", "event": 8,
                            "player_id": p["id"], "web_name": p["web_name"], "predicted": 2.0 + p["id"] / 10})
    return d


class Induction(unittest.TestCase):
    def test_three_week_toy_with_known_optimum(self):
        v_bb = {17: 1.0, 18: 5.0, 19: 2.0}
        v_fh = {17: 4.0, 18: 3.0, 19: 9.0}
        ind = C.induction(v_bb, v_fh, 17, 19)
        both = frozenset(C.CHIPS)
        self.assertAlmostEqual(ind["V"][(17, both)], 9.0)              # FH at 17, BB at 18
        self.assertEqual(ind["next"], "PLAY FH")
        self.assertEqual(ind["action"][(18, frozenset({"BB"}))], "PLAY BB")
        self.assertEqual(ind["V"][(19, frozenset({"FH"}))], 0.0)       # FH is never played in GW19
        self.assertEqual(ind["action"][(19, frozenset({"FH"}))], "HOLD")
        self.assertAlmostEqual(ind["V"][(19, frozenset({"BB"}))], 2.0)
        self.assertEqual(ind["V"][(20, both)], 0.0)                     # worth 0 after GW19
        # one chip a week: V with both is never above the best split
        self.assertLessEqual(ind["V"][(17, both)], max(v_fh[17] + v_bb[18], v_fh[17] + v_bb[19], v_bb[17] + v_fh[18]))
        self.assertAlmostEqual(C.margin(v_bb, v_fh, ind, 17, both), 9.0 - 5.0)   # PLAY FH 9 vs HOLD 5 (BB 4)

    def test_tie_goes_to_playing_and_last_week_plays(self):
        ind = C.induction({19: 0.0}, {19: 5.0}, 19, 19)
        self.assertEqual(ind["next"], "PLAY BB")                        # 0 = holding 0: play, do not lose it
        ind = C.induction({18: 2.0, 19: 2.0}, {18: 0.0, 19: 0.0}, 18, 19, frozenset({"BB"}))
        self.assertEqual(ind["next"], "PLAY BB")                        # equal weeks: the earlier one

    def test_hand_values(self):
        out = [{"proj": 3.0}, {"proj": 2.0}, {"proj": 1.0}]
        self.assertAlmostEqual(C.bench_boost_value(out, {"proj": 1.0}), 3 * 0.7 + 2 * 0.9 + 1 * 0.97 + 1 * 0.97)
        self.assertEqual(C.heuristic_action(5, {"BB", "FH"}, {5: 7.0, 6: 6.0}, {5: 1.0, 6: 2.0}), "PLAY BB")
        self.assertEqual(C.heuristic_action(5, {"FH"}, {5: 7.0, 6: 6.0}, {5: 1.0, 6: 2.0}), "HOLD")
        self.assertEqual(C.heuristic_action(6, {"FH"}, {5: 7.0, 6: 6.0}, {5: 1.0, 6: 2.0}), "PLAY FH")
        self.assertEqual(C.heuristic_action(19, {"FH"}, {19: 1.0}, {19: 9.0}), "HOLD")


class Live(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        toy_data(cls.tmp.name)                                    # fpl.sqlite and graded own rows for the residual pools
        cls.d = toy_export(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_own_week_points_recorded_then_formula(self):
        d, _ = C.newest_export(self.tmp.name)
        log = E.read_log(os.path.join(self.tmp.name, E.LOG_PATH))
        weeks, pts, src = C.own_week_points(d, log)
        self.assertEqual(weeks, [8, 9, 10])
        self.assertEqual(pts[8][5], 2.5)                            # the recorded own row for the next gameweek
        self.assertEqual(src[8][5], "own")
        # later weeks: the recording formula on that week's fixture
        tick, _ = E.build_ticker(d, 6)
        priors, personal = E.positional_priors(d["all_players"]), E.personal_priors(d)
        p = next(q for q in d["all_players"] if q["id"] == 5)
        fx = [f for f in tick[p["team"]] if f[0] == 9]
        want = sum(E.project(p, {p["team"]: [f]}, 6, d["gameweek"], priors, personal)[0] for f in fx)
        self.assertAlmostEqual(pts[9][5], want)
        self.assertEqual(src[9][5], "own-model")
        self.assertEqual((pts[9][2], src[9][2]), (0.0, "gate"))         # status 'd': outside the gate
        d2 = dict(d, fixtures_next6=[f for f in d["fixtures_next6"] if not (f["event"] == 9 and "ARS" in (f["home"], f["away"]))])
        _, pts2, src2 = C.own_week_points(d2, log)
        self.assertEqual((pts2[9][1], src2[9][1]), (0.0, "blank"))

    def test_squad_budget_and_chips(self):
        d, _ = C.newest_export(self.tmp.name)
        squad = C.my_squad(d)
        self.assertEqual(len(squad), 15)
        self.assertEqual(sorted(r["pos"] for r in squad), [1, 1] + [2] * 5 + [3] * 5 + [4] * 3)
        self.assertEqual(C.chips_left(d), frozenset({"BB", "FH"}))
        d3 = dict(d, chips_used=d["chips_used"] + [{"entry_name": "Us", "name": "bboost", "event": 3}])
        self.assertEqual(C.chips_left(d3), frozenset({"FH"}))
        d4 = dict(d, squads=[{k: v for k, v in r.items() if k != "selling_price"} for r in d["squads"]])
        with self.assertRaises(C.MissingInput):
            C.my_squad(d4)

    def test_xi_bench_and_values(self):
        d, _ = C.newest_export(self.tmp.name)
        squad = C.my_squad(d)
        pts = {r["id"]: float(r["id"]) for r in squad}
        xi, outfield, gk = C.xi_and_bench(squad, pts)
        self.assertEqual(len(xi), 11)
        self.assertEqual(gk["pos"], 1)
        self.assertEqual([r["proj"] for r in outfield], sorted((r["proj"] for r in outfield), reverse=True))
        self.assertEqual(len({r["id"] for r in xi} | {r["id"] for r in outfield} | {gk["id"]}), 15)
        v = C.bench_boost_value(outfield, gk)
        self.assertAlmostEqual(v, sum(r["proj"] * (1 - w) for r, w in zip(outfield, C.BENCH_W)) + gk["proj"] * 0.97)
        market, fodder = C.market_rows(d, pts)
        self.assertTrue(all(p["status"] == "a" for p in market))
        budget, _ = E.selling_budget(d)
        vfh, fh, ours = C.free_hit_value(market, fodder, budget, squad, pts)
        self.assertAlmostEqual(vfh, fh["pts"] - sum(r["proj"] for r in ours))
        self.assertLessEqual(fh["cost"], budget + 1e-9)

    def test_live_runs_and_labels(self):
        buf = io.StringIO()
        res = C.live(self.tmp.name, out=lambda s: buf.write(s + "\n"), resamples=20)
        text = buf.getvalue()
        self.assertIn("no transfers assumed", text)
        self.assertIn("NEXT GAMEWEEK GW8:", text)
        self.assertIn("FREE HIT SCREEN", text)
        self.assertIn("BENCH PREP", text)
        self.assertEqual(res["weeks"], [8, 9, 10])
        self.assertTrue(all(w in res["v_bb"] for w in range(8, 20)))        # proxies to GW19
        self.assertIn("proxy", text)
        self.assertEqual(res["induction"]["V"][(20, frozenset({"BB", "FH"}))], 0.0)


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        toy_hist(cls.tmp.name)
        cls.rp = C.Replay(cls.tmp.name, last=6)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_squads_are_legal_and_reproducible(self):
        cands = C.gw1_candidates(self.rp.hist)
        a = C.sample_squads(cands, n=5, seed=7, budget=1100)
        b = C.sample_squads(cands, n=5, seed=7, budget=1100)
        self.assertEqual(a, b)
        for sq in a:
            self.assertEqual(sorted(p["pos"] for p in sq), [1, 1] + [2] * 5 + [3] * 5 + [4] * 3)
            self.assertLessEqual(sum(p["price"] for p in sq), 1100)
            self.assertLessEqual(max(sum(1 for p in sq if p["team"] == t) for t in {p["team"] for p in sq}), 3)
        self.assertNotEqual(a, C.sample_squads(cands, n=5, seed=8, budget=1100))

    def test_forecasts_point_in_time(self):
        fc5, _ = self.rp.forecasts(5)
        self.assertEqual(sorted(fc5), [5, 6])
        rp2 = C.Replay(self.tmp.name, last=6)
        for r in rp2.c["rows"]:
            if r["event"] >= 5:
                r["pts"] = 50; r["xg"] = 9.0
        self.assertEqual(rp2.forecasts(5)[0], fc5)
        with mock.patch.object(E, "canonical_through", lambda c, gw: E.check_canonical(dict(c, through_gw=gw))):
            leaked = C.Replay(self.tmp.name, last=6).forecasts(5)[0]
        self.assertNotEqual(leaked, fc5)

    def test_club_of_the_origin_is_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            base = C.Replay(tmp, last=6).forecasts(5)[0]
            plant_transfer(tmp, 3, 6, 2)                           # moves in round 6: invisible at origin 5
            self.assertEqual(C.Replay(tmp, last=6).forecasts(5)[0], base)

    def test_realised_gains_hand_cases(self):
        rp = self.rp
        t = 5
        rows = [{"id": pid, "pos": pos, "proj": 1.0} for pid, pos in [(1, 1), (2, 2), (3, 2), (4, 2), (5, 3), (6, 3), (7, 3), (8, 4), (9, 4), (10, 2), (11, 3)]]
        bench = [{"id": 12, "pos": 2, "proj": 0.5}, {"id": 13, "pos": 3, "proj": 0.4}, {"id": 14, "pos": 4, "proj": 0.3}]
        gk = {"id": 15, "pos": 1, "proj": 0.2}
        rp.actual[t] = {i: (float(i), 90.0) for i in range(1, 16)}
        rp.actual[t][2] = (0.0, 0.0)                                   # a starter who did not play: 12 comes on
        detail = {"xi": rows, "bench": bench, "gk": gk, "fh": None}
        self.assertAlmostEqual(rp.bb_gain(detail, t), (15 + 12 + 13 + 14) - 12)
        self.assertEqual(rp.fh_gain(detail, t), 0.0)
        fh_xi = [dict(r, pts=r["proj"]) for r in rows[:10]] + [{"id": 16, "pos": 4, "pts": 9.0}]
        rp.actual[t][16] = (20.0, 90.0)
        detail["fh"] = {"xi": fh_xi}
        ours = sum(float(i) for i in range(1, 12)) - 2 + 1.0            # captain 1 (highest proj, lowest id) doubled
        theirs = sum(float(i) for i in range(1, 11)) - 2 + 20 + 20     # captain 16 doubled
        self.assertAlmostEqual(rp.fh_gain(detail, t), theirs - ours)
        del rp.actual[t]
        rp.actual[t] = {r["player_id"]: (float(r["pts"] or 0), float(r["minutes"] or 0)) for r in rp.c["rows"] if r["event"] == t}

    def test_replay_runs_and_scores_every_policy(self):
        buf = io.StringIO()
        res = C.replay(self.tmp.name, n_squads=3, seed=7, out=lambda s: buf.write(s + "\n"), first=5, last=6)
        self.assertEqual(len(res["results"]), 3)
        for r in res["results"]:
            self.assertEqual(set(r), {"calculator", "heuristic", "early"})
            for name, (pts, played, split) in r.items():
                self.assertTrue(set(played) <= {"BB", "FH"})
                self.assertNotIn(6, [played.get("FH")])                # FH never in the last week
                self.assertAlmostEqual(pts, split["BB"] + split["FH"])
        self.assertIn("pre-registered bar", buf.getvalue())
        self.assertEqual(res["results"][0]["early"][1], {"BB": 5})       # FH cannot follow in the last week


class CLI(unittest.TestCase):
    def test_cli_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            hist = os.path.join(tmp, "hist"); os.makedirs(hist); toy_hist(hist)
            data = os.path.join(tmp, "data"); os.makedirs(data); toy_data(data); toy_export(data)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = C.main(["--data", data, "--hist", hist, "--out", out, "--resamples", "5"])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(out, "chips_live.txt")))
            with redirect_stdout(io.StringIO()):
                rc = C.main(["--replay", "--data", data, "--hist", hist, "--out", out, "--squads", "1"])
            self.assertEqual(rc, 2)                                   # the toy ends at GW6: refused, not substituted
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'chips', 'backtest', 'hist_pit')]; "
                "print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
