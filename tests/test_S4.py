"""
tests/test_S4.py - the backtest harness (prereg/S4.md acceptance tests).

    python -m unittest tests.test_S4
    python -m unittest discover -s tests -t .
"""

import csv
import io
import itertools
import math
import os
import random
import sqlite3
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
import hist_pit as PIT                                            # noqa: E402

TEAMS = [("Alpha", "ALP"), ("Beta", "BET"), ("Gamma", "GAM"), ("Delta", "DEL"),
         ("Eps", "EPS"), ("Zeta", "ZET")]
POSN = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
SHAPE = {1: 1, 2: 3, 3: 3, 4: 2}        # players per team per position (9 a team, 54 in all)
MERGED_COLS = ["name", "position", "team", "element", "fixture", "round", "kickoff_time",
               "minutes", "starts", "total_points", "expected_goals", "expected_assists",
               "bps", "defensive_contribution", "opponent_team", "was_home", "selected",
               "value", "clean_sheets", "goals_scored", "bonus"]


def toy_hist(folder, rounds=6, seed=1):
    """A six-team vaastav-shaped season: every team plays every round."""
    rng = random.Random(seed)
    with open(os.path.join(folder, "teams.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "name", "short_name"])
        w.writeheader()
        for i, (name, short) in enumerate(TEAMS, 1):
            w.writerow({"id": i, "name": name, "short_name": short})
    players, pid = [], 0
    for ti, (name, short) in enumerate(TEAMS, 1):
        for pos, n in SHAPE.items():
            for k in range(n):
                pid += 1
                players.append({"id": pid, "team": ti, "pos": pos, "price": rng.choice([40, 45, 50, 60, 75, 90, 120]),
                                "quality": rng.random()})
    fixtures, rows, fid = [], [], 0
    for r in range(1, rounds + 1):
        order = list(range(1, 7))
        rng.shuffle(order)
        for h, a in zip(order[::2], order[1::2]):
            fid += 1
            hs, as_ = rng.choice([0, 1, 2, 3]), rng.choice([0, 1, 2])
            fixtures.append({"id": fid, "event": r, "team_h": h, "team_a": a, "team_h_score": hs, "team_a_score": as_})
            for p in players:
                if p["team"] not in (h, a):
                    continue
                home = p["team"] == h
                conceded = as_ if home else hs
                starts = 1 if rng.random() < 0.6 + 0.35 * p["quality"] else 0
                mins = 90 if starts else (rng.choice([0, 0, 15, 30]))
                goals = 1 if (mins and p["pos"] >= 3 and rng.random() < 0.25 * p["quality"]) else 0
                cs = 1 if (mins >= 60 and conceded == 0) else 0
                dc = rng.choice([4, 8, 10, 12, 14]) if mins else 0
                bonus = rng.choice([0, 0, 0, 1, 2, 3]) if mins else 0
                pts = (2 if mins >= 60 else (1 if mins else 0)) + goals * E.GOAL_VALUE[p["pos"]] \
                    + cs * E.CS_VALUE[p["pos"]] + bonus + (2 if p["pos"] in E.DEFCON_THRESHOLD and dc >= E.DEFCON_THRESHOLD[p["pos"]] else 0)
                rows.append({"name": f"P{p['id']}", "position": POSN[p["pos"]], "team": TEAMS[p["team"] - 1][0],
                             "element": p["id"], "fixture": fid, "round": r,
                             "kickoff_time": f"2025-08-{14 + r:02d}T14:00:00Z",
                             "minutes": mins, "starts": starts, "total_points": pts,
                             "expected_goals": round(rng.random() * 0.6 * p["quality"], 2) if mins else 0,
                             "expected_assists": round(rng.random() * 0.3, 2) if mins else 0,
                             "bps": rng.randint(0, 30) if mins else 0, "defensive_contribution": dc,
                             "opponent_team": a if home else h, "was_home": home,
                             "selected": int(1000 * p["quality"] + 100 * r), "value": p["price"] + (r if r % 2 else 0),
                             "clean_sheets": cs, "goals_scored": goals, "bonus": bonus})
    with open(os.path.join(folder, "fixtures.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "event", "team_h", "team_a", "team_h_score", "team_a_score"])
        w.writeheader(); w.writerows(fixtures)
    with open(os.path.join(folder, "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MERGED_COLS)
        w.writeheader(); w.writerows(rows)
    return players, rows


def plant_transfer(folder, pid, from_round, new_team):
    """Rewrite the toy so player `pid` plays for team id `new_team` from
    `from_round` on: his rows move to that team's fixture of each round."""
    with open(os.path.join(folder, "fixtures.csv"), encoding="utf-8", newline="") as fh:
        fixtures = list(csv.DictReader(fh))
    with open(os.path.join(folder, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if int(r["element"]) != pid or int(r["round"]) < from_round:
            continue
        f = next(f for f in fixtures if int(f["event"]) == int(r["round"])
                 and new_team in (int(f["team_h"]), int(f["team_a"])))
        home = int(f["team_h"]) == new_team
        r.update({"team": TEAMS[new_team - 1][0], "fixture": f["id"], "was_home": home,
                  "opponent_team": f["team_a"] if home else f["team_h"]})
    with open(os.path.join(folder, "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MERGED_COLS)
        w.writeheader(); w.writerows(rows)


def truncate_rounds(src, dst, g):
    """Copy the toy keeping only merged rows with round <= g."""
    os.makedirs(dst, exist_ok=True)
    for name in ("teams.csv", "fixtures.csv"):
        with open(os.path.join(src, name), encoding="utf-8") as a, open(os.path.join(dst, name), "w", encoding="utf-8") as b:
            b.write(a.read())
    with open(os.path.join(src, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if int(r["round"]) <= g]
    with open(os.path.join(dst, "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MERGED_COLS)
        w.writeheader(); w.writerows(rows)


def toy_data(folder, deadline5="2026-09-18T17:30:00+00:00"):
    """A 2026/27 data folder: fpl.sqlite with events 4-6 (5 settled, 6 not
    data_checked, 4 one fixture unfinished) and a projection log with two
    pre-deadline snapshots, one post-deadline snapshot and a tie for GW5."""
    db = os.path.join(folder, "fpl.sqlite")
    c = sqlite3.connect(db)
    c.executescript("""
      create table events(id integer, deadline_time text, finished integer, data_checked integer);
      create table fixtures(id integer, event integer, finished integer);
      create table players(id integer, position integer);
      create table player_gw(player_id integer, event integer, total_points integer, minutes integer,
        starts integer, clean_sheets integer, goals integer, bonus integer, defensive_contribution integer);
      create table picks(entry_id integer, event integer, player_id integer, position integer);
    """)
    c.executemany("insert into events values (?,?,?,?)",
                  [(4, "2026-09-12T12:30:00Z", 1, 1), (5, "2026-09-18T17:30:00Z", 1, 1), (6, "2026-10-10T10:00:00Z", 1, 0)])
    c.executemany("insert into fixtures values (?,?,?)",
                  [(1, 4, 1), (2, 4, 0), (3, 5, 1), (4, 5, 1), (5, 6, 1)])
    pos = {pid: (1 if pid <= 2 else 2 if pid <= 7 else 3 if pid <= 12 else 4) for pid in range(1, 16)}
    c.executemany("insert into players values (?,?)", list(pos.items()))
    rng = random.Random(3)
    for ev in (4, 5, 6):
        for pid in range(1, 16):
            mins = rng.choice([0, 90, 90, 60])
            c.execute("insert into player_gw values (?,?,?,?,?,?,?,?,?)",
                      (pid, ev, rng.randint(0, 12) if mins else 0, mins, 1 if mins == 90 else 0,
                       rng.choice([0, 1]) if mins >= 60 else 0, rng.choice([0, 0, 1]) if mins else 0,
                       rng.choice([0, 0, 1, 3]) if mins else 0, rng.choice([5, 10, 13]) if mins else 0))
        for slot, pid in enumerate(range(1, 16), 1):
            c.execute("insert into picks values (?,?,?,?)", (BT.MY_ENTRY, ev, pid, slot))
    c.commit(); c.close()
    log = os.path.join(folder, E.LOG_PATH)
    with open(log, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=E.LOG_FIELDS)
        w.writeheader()
        for src in ("own", "bottomup", "minutes"):
            for pid in range(1, 15):            # player 15 is never forecast
                w.writerow({"made_at": "2026-09-16T21:55:00+00:00", "source": src, "event": 5,
                            "player_id": pid, "web_name": f"P{pid}", "predicted": 1.0})
            for pid in range(1, 14):            # the last pre-deadline snapshot drops player 14
                val = {"own": 2.0 + pid / 10, "bottomup": 3.0 - pid / 10, "minutes": 0.9 if pid % 3 else 0.5}[src]
                w.writerow({"made_at": "2026-09-17T21:55:00+00:00", "source": src, "event": 5,
                            "player_id": pid, "web_name": f"P{pid}", "predicted": val})
            w.writerow({"made_at": "2026-09-17T21:55:00+00:00", "source": src, "event": 5,
                        "player_id": 1, "web_name": "P1", "predicted": 9.0})       # the tie: later row wins
            for pid in range(1, 14):            # post-deadline: never read
                w.writerow({"made_at": "2026-09-18T18:00:00+00:00", "source": src, "event": 5,
                            "player_id": pid, "web_name": f"P{pid}", "predicted": 99.0})
            for ev in (4, 6):
                for pid in range(1, 14):
                    w.writerow({"made_at": "2026-09-11T21:55:00+00:00" if ev == 4 else "2026-10-09T21:55:00+00:00",
                                "source": src, "event": ev, "player_id": pid, "web_name": f"P{pid}",
                                "predicted": 1.0 + pid / 10})
    return db, log


class Metrics(unittest.TestCase):
    def test_spearman_is_the_repo_ruler(self):
        a, b = [1, 2, 2, 3, 5], [2, 1, 3, 3, 4]
        self.assertEqual(BT.spearman(a, b), E._spearman(a, b))

    def test_kendall_tau_b_with_ties(self):
        self.assertAlmostEqual(BT.kendall_tau_b([1, 2, 3, 4], [1, 3, 2, 4]), 4 / 6)
        self.assertAlmostEqual(BT.kendall_tau_b([1, 1, 2, 3], [1, 2, 2, 3]), 0.8)
        self.assertAlmostEqual(BT.kendall_tau_b([1, 2, 3], [3, 2, 1]), -1.0)

    def test_topk_regret_and_tie_break(self):
        self.assertEqual(BT.topk_regret([1, 2, 3], [3, 2, 1], [1, 5, 2], 1), 4)
        self.assertEqual(BT.topk_regret([1, 2, 3], [3, 2, 1], [1, 5, 2], 3), 0)
        self.assertEqual(BT.topk_regret([2, 1, 3], [2, 2, 1], [5, 1, 2], 1), 4)   # tie -> lower id (1) first
        self.assertIsNone(BT.topk_regret([1, 2], [1, 2], [1, 2], 11))

    def test_mae_brier_logloss(self):
        self.assertAlmostEqual(BT.mae([1, 2], [2, 4]), 1.5)
        self.assertAlmostEqual(BT.brier([0.8, 0.3], [1, 0]), (0.04 + 0.09) / 2)
        self.assertAlmostEqual(BT.log_loss([0.5, 0.5], [1, 0]), math.log(2))
        self.assertAlmostEqual(BT.log_loss([0.0], [1]), -math.log(BT.CLIP))

    def test_decision_points(self):
        pos = {pid: (1 if pid <= 2 else 2 if pid <= 7 else 3 if pid <= 12 else 4) for pid in range(1, 16)}
        pred = {pid: float(pid) for pid in range(1, 15)}          # 15 has no forecast -> counts as 0
        pred[13] = 0.5                                              # so a forecast of 5 for player 15 would change the XI
        act = {pid: float(pid) for pid in range(1, 16)}            # distinct, so any XI change shows
        # best legal XI by pred is 4-5-1: GK 2, DEF 4-7, MID 8-12, FWD 14 (86.0); captain 14, doubled
        v = BT.decision_points(list(range(1, 16)), pred, act, pos)
        xi = [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14]
        self.assertEqual(v, sum(act[p] for p in xi) + act[14])
        self.assertEqual(v, 102.0)
        self.assertIsNone(BT.decision_points([1, 2, 3], pred, act, pos))

    def test_holm_and_bh(self):
        pv = [("a", 0.001), ("b", 0.04), ("c", 0.06), ("d", 0.2)]
        self.assertEqual(BT.holm(pv), {"a": True, "b": False, "c": False, "d": False})
        self.assertEqual(BT.benjamini_hochberg(pv), {"a": True, "b": True, "c": True, "d": False})
        pv = [("a", 0.001), ("b", 0.03), ("c", 0.2), ("d", 0.3)]        # Holm rejects b, Bonferroni would not
        self.assertEqual(BT.holm(pv), {"a": True, "b": True, "c": False, "d": False})
        self.assertEqual(BT.benjamini_hochberg(pv), {"a": True, "b": True, "c": False, "d": False})

    def test_power_formula(self):
        self.assertAlmostEqual(BT.power_gameweeks(0.10, 0.03), ((1.645 + 0.842) * 0.10 / 0.03) ** 2)
        self.assertAlmostEqual(BT.sd([1, 2, 3, 4]), math.sqrt(5 / 3))

    def test_bootstrap_hand_cases(self):
        r = BT.bootstrap_mean([2.0, 2.0, 2.0], b=200, seed=1)
        self.assertEqual((r["mean"], r["lo"], r["hi"], r["n"]), (2.0, 2.0, 2.0, 3))
        self.assertAlmostEqual(r["p"], 1 / 201)
        r = BT.bootstrap_mean([-1.0, 1.0] * 10, b=2000, seed=1)
        self.assertLess(r["lo"], 0); self.assertGreater(r["hi"], 0); self.assertGreater(r["p"], 0.5)
        self.assertEqual(BT.bootstrap_mean([], b=10)["n"], 0)
        a = BT.bootstrap_mean([0.1, 0.3, -0.2, 0.4], b=500, seed=7)
        self.assertEqual(a, BT.bootstrap_mean([0.1, 0.3, -0.2, 0.4], b=500, seed=7))   # reproducible

    def test_selftest_runs_through_the_rule(self):
        buf = io.StringIO()
        power, fp, n = BT.selftest(reps=20, b=200, out=lambda s: buf.write(s + "\n"))
        self.assertEqual(n, math.ceil(BT.power_gameweeks(0.10, 0.03)))
        self.assertTrue(0 <= fp <= power <= 1)
        self.assertIn("bar 0.80 +/- 0.05", buf.getvalue())


class Squad(unittest.TestCase):
    def small_world(self, rng, n=(3, 6, 6, 4), clubs=5):
        cands, pid = [], 0
        for pos, k in zip((1, 2, 3, 4), n):
            for _ in range(k):
                pid += 1
                cands.append({"id": pid, "pos": pos, "team": f"C{rng.randrange(clubs)}",
                              "price": rng.choice([40, 45, 50, 60, 80, 100, 125]), "metric": rng.randint(1, 1000)})
        return cands

    def brute(self, cands, budget):
        by = {p: [c for c in cands if c["pos"] == p] for p in (1, 2, 3, 4)}
        best = None
        for g in itertools.combinations(by[1], 2):
            for d in itertools.combinations(by[2], 5):
                for m in itertools.combinations(by[3], 5):
                    for f in itertools.combinations(by[4], 3):
                        sq = g + d + m + f
                        if sum(p["price"] for p in sq) > budget:
                            continue
                        if max(sum(1 for p in sq if p["team"] == t) for t in {p["team"] for p in sq}) > 3:
                            continue
                        v = sum(p["metric"] for p in sq)
                        if best is None or v > best:
                            best = v
        return best

    def test_best_fifteen_equals_brute_force(self):
        rng = random.Random(11)
        binding = 0
        for world in range(4):
            cands = self.small_world(rng, clubs=4 if world % 2 else 5)
            budget = rng.choice([900, 1000, 1100])
            want = self.brute(cands, budget)
            got = BT.best_fifteen(cands, budget)
            if want is None:
                self.assertIsNone(got)
                continue
            self.assertEqual(got["metric"], want, f"world {world}")
            self.assertTrue(got["exact"])
            self.assertLessEqual(got["cost"], budget)
            self.assertEqual(sorted(p["pos"] for p in got["squad"]), [1, 1] + [2] * 5 + [3] * 5 + [4] * 3)
            if got["nodes"] > 1:
                binding += 1
            if world == 0:                                   # pruning never changes the answer
                self.assertEqual(BT.best_fifteen(cands, budget, prune=False)["metric"], want)
        self.assertGreaterEqual(binding, 1, "no world had the club limit bind")

    def test_candidates_use_previous_gameweek_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            hist = BT.load_2526(tmp)
            c3 = {p["id"]: p for p in BT.squad_candidates(hist, 3)}
            c1 = {p["id"]: p for p in BT.squad_candidates(hist, 1)}
            sel = {(int(r["element"]), int(r["round"])): (float(r["selected"]), float(r["value"]))
                   for r in sum(hist["raw"].values(), [])}
            pid = next(iter(c3))
            self.assertEqual(c3[pid]["metric"], sel[(pid, 2)][0])      # selected of GW2 for GW3
            self.assertEqual(c3[pid]["price"], sel[(pid, 3)][1])       # value of GW3
            self.assertEqual(c1[pid]["metric"], sel[(pid, 1)][0])      # GW1 uses GW1's


class Season2526(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        toy_hist(cls.tmp.name)
        cls.h = BT.Harness("2025-26", hist_dir=cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_rebuilt_equals_backtest_week(self):
        reb = self.h.rebuilt(5)
        bt = {b["pid"]: b["preds"] for b in E.backtest_week(self.h.hist["c"], 5)}
        self.assertEqual(len(reb["rows"]["bottomup"]), len(bt))
        for src in ("bottomup", "minutes"):
            for pid, pred, a in reb["rows"][src]:
                self.assertAlmostEqual(pred, bt[pid][src], places=9)

    def test_components_are_the_models_own_terms(self):
        c = self.h.hist["c"]
        inp = E.reliability_inputs(E.canonical_through(c, 4), gws_played=4)
        for pid, p in inp["players"].items():
            if p["p_start"] <= 0 or p["pos"] not in (2, 3):
                continue
            opp = "BET" if p["team"] != "BET" else "ALP"
            base = E.project_reliability(pid, inp, [(opp, True)], frozenset())
            cs = E.project_reliability(pid, inp, [(opp, True)], frozenset({"cs"}))
            dc = E.project_reliability(pid, inp, [(opp, True)], frozenset({"defcon"}))
            self.assertAlmostEqual(cs - base, BT._p_cs(inp, p, opp) * E.CS_VALUE[p["pos"]] * p["p_start"], places=9)
            self.assertAlmostEqual(dc - base, 2.0 * BT._p_defcon(inp, p) * p["p_start"], places=9)
            break
        else:
            self.fail("no DEF/MID with P(start) > 0 in the toy")

    def test_leak_free_and_mutation_red(self):
        before = {pid: pred for pid, pred, _ in self.h.rebuilt(5)["rows"]["bottomup"]}
        hist2 = BT.load_2526(self.tmp.name)
        for r in hist2["c"]["rows"]:
            if r["event"] >= 5:
                r["pts"] = (r["pts"] or 0) + 50; r["xg"] = (r["xg"] or 0) + 3.0; r["minutes"] = 90
        after = {pid: pred for pid, pred, _ in BT.rebuild_2526(hist2, 5)["rows"]["bottomup"]}
        self.assertEqual(before, after)
        # mutation: a training slice that keeps the target week -> the forecast moves
        with mock.patch.object(E, "canonical_through", lambda c, gw: E.check_canonical(dict(c, through_gw=gw))):
            leaked = {pid: pred for pid, pred, _ in BT.rebuild_2526(hist2, 5)["rows"]["bottomup"]}
        self.assertNotEqual(before, leaked)

    def test_not_rebuildable_sources_refuse(self):
        for s in ("own", "xg", "fpl_ep"):
            with self.assertRaises(BT.MissingInput):
                self.h.rows(5, s)
            with self.assertRaises(BT.MissingInput):
                self.h.compare(s, "bottomup")
        self.assertEqual(self.h.weeks("own"), [])

    def test_starters_filter_is_forecast_p_start(self):
        rows = self.h.rows(5, "bottomup", "starters")
        ps = self.h.rebuilt(5)["p_start"]
        self.assertTrue(rows)
        self.assertTrue(all(ps[pid] >= BT.STARTER_P for pid, _, _ in rows))
        self.assertLess(len(rows), len(self.h.rows(5, "bottomup", "all")))

    def test_compare_and_decision(self):
        res = self.h.compare("bottomup", "minutes", "all")
        self.assertEqual(res["weeks"], [5, 6])
        self.assertEqual(set(res["boot"]), {"spearman", "kendall", "mae", "decision", "regret1", "regret3", "regret11"})
        d, missing, note = self.h.decision(5, "bottomup")
        self.assertIsInstance(d, float)
        self.assertIn("selected of GW4", note)
        out = io.StringIO()
        BT.print_compare(res, lambda s: out.write(s + "\n"))
        self.assertIn("COMPARE bottomup vs minutes", out.getvalue())

    def test_rebuild_uses_the_club_of_that_gameweek(self):
        """The team-column leak test: a transfer planted in round 6 leaves
        every gameweek-5 number unchanged, and gameweek 6 sees the new club."""
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            base = BT.load_2526(tmp)
            pid = 3                                      # an Alpha defender
            reb5 = BT.rebuild_2526(base, 5)
            cands5 = BT.squad_candidates(base, 5)
            plant_transfer(tmp, pid, 6, 2)
            hist = BT.load_2526(tmp)
            self.assertEqual(hist["c"]["players"][pid]["team"], "BET")     # the frozen adapter: end-of-season club
            reb5b = BT.rebuild_2526(hist, 5)
            self.assertEqual(reb5["rows"], reb5b["rows"])
            self.assertEqual(reb5["components"], reb5b["components"])
            self.assertEqual(reb5["p_start"], reb5b["p_start"])
            self.assertEqual(cands5, BT.squad_candidates(hist, 5))
            self.assertEqual(next(c for c in BT.squad_candidates(hist, 6) if c["id"] == pid)["team"], "BET")
            self.assertEqual(BT.canonical_at(hist, 5)["players"][pid]["team"], "ALP")
            self.assertEqual(BT.canonical_at(hist, 6)["players"][pid]["team"], "BET")

    def test_components_leak_free_and_mutation_red(self):
        """P(start), P(cs) and P(DEFCON) for gameweek 5 read nothing from
        round 5 onward; training through the target week moves them."""
        def probs(reb):
            return (reb["p_start"], [p for p, _ in reb["components"]["bottomup"]["cs"]],
                    [p for p, _ in reb["components"]["bottomup"]["defcon"]])
        before = probs(self.h.rebuilt(5))
        hist2 = BT.load_2526(self.tmp.name)
        for r in hist2["c"]["rows"]:
            if r["event"] >= 5:
                r["starts"] = 0; r["minutes"] = 1; r["xg"] = (r["xg"] or 0) + 2.0; r["defcon"] = 40
        for m in hist2["c"]["team_matches"]:
            if m["event"] >= 5:
                m["goals_against"] = 9
        self.assertEqual(probs(BT.rebuild_2526(hist2, 5)), before)
        no_cut = lambda c, gw: E.check_canonical(dict(c, through_gw=gw))      # noqa: E731
        with mock.patch.object(E, "canonical_through", no_cut):              # the verifier's mutation:
            leaked = probs(BT.rebuild_2526(hist2, 5))                        # slice keeps the target week
        self.assertEqual(leaked[0], before[0])        # P(start)'s window is bounded by gws_played, not the slice
        self.assertNotEqual(leaked[1], before[1])     # team rates and season totals move P(cs) ...
        self.assertNotEqual(leaked[2], before[2])     # ... and P(DEFCON)
        orig = E.reliability_inputs
        with mock.patch.object(E, "canonical_through", no_cut),              mock.patch.object(E, "reliability_inputs", lambda c, gws_played=None, **k: orig(c, gws_played=gws_played + 1, **k)):
            leaked = probs(BT.rebuild_2526(hist2, 5))                        # training through the target week
        self.assertNotEqual(leaked[0], before[0])


class ClubMap(unittest.TestCase):
    """prereg/S4.md amendment 2: the point-in-time club map."""

    def test_every_row_club_is_one_of_its_fixture_teams(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            cm = PIT.club_map(tmp)
            with open(os.path.join(tmp, "fixtures.csv"), newline="") as fh:
                fx = {f["id"]: f for f in csv.DictReader(fh)}
            with open(os.path.join(tmp, "merged_gw.csv"), newline="") as fh:
                rows = list(csv.DictReader(fh))
            short = {str(i): s for i, (_, s) in enumerate(TEAMS, 1)}
            self.assertEqual(len(rows), len(cm["rows"]))
            for r in rows:
                f = fx[r["fixture"]]
                self.assertIn(cm["rows"][(int(r["element"]), int(r["round"]))],
                              {short[f["team_h"]], short[f["team_a"]]})
            self.assertEqual(PIT.changes(cm), [])

    @unittest.skipUnless(os.path.isdir(os.path.join(ROOT, "historical", "2025-26")), "no 2025/26 copy")
    def test_real_season_rows_match_their_fixtures(self):
        folder = os.path.join(ROOT, "historical", "2025-26")
        cm = PIT.club_map(folder)            # derive_clubs raises on any mismatch
        self.assertEqual((len(cm["first"]), cm["through"]), (841, 38))
        self.assertGreater(len(PIT.changes(cm)), 0)

    def test_planted_transfer_changes_club_in_exactly_that_gameweek(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            cm0 = PIT.club_map(tmp)
            pid = 1                           # Alpha's keeper
            self.assertEqual(PIT.club_at(cm0, pid, 6), "ALP")
            plant_transfer(tmp, pid, 4, 2)    # to Beta from round 4
            cm = PIT.club_map(tmp)
            self.assertEqual([PIT.club_at(cm, pid, g) for g in range(1, 7)],
                             ["ALP", "ALP", "ALP", "BET", "BET", "BET"])
            self.assertEqual(PIT.changes(cm), [(pid, 4, "ALP", "BET")])
            self.assertEqual(PIT.club_at(cm, pid, 0), None)
            self.assertEqual(PIT.club_at(cm, pid, 99), "BET")   # beyond the data: the last known club

    def test_look_ahead_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "full"); os.makedirs(src); toy_hist(src)
            plant_transfer(src, 1, 4, 2)
            full = PIT.club_map(src)
            for g in range(1, 7):
                cut = os.path.join(tmp, f"upto{g}")
                truncate_rounds(src, cut, g)
                self.assertEqual(PIT.club_map(cut)["by_gw"][g], full["by_gw"][g], f"gameweek {g}")
            self.assertEqual(PIT.club_at(full, 1, 3), "ALP")     # the round-4 move is invisible at 3

    def test_cross_check_and_unknown_fixture_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            path = os.path.join(tmp, "merged_gw.csv")
            with open(path, newline="") as fh:
                rows = list(csv.DictReader(fh))
            rows[0]["team"] = TEAMS[1][0] if rows[0]["team"] != TEAMS[1][0] else TEAMS[2][0]
            with open(path, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=MERGED_COLS); w.writeheader(); w.writerows(rows)
            with self.assertRaises(ValueError):
                PIT.club_map(tmp)
            toy_hist(tmp)
            with open(path, newline="") as fh:
                rows = list(csv.DictReader(fh))
            rows[0]["fixture"] = "999"
            with open(path, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=MERGED_COLS); w.writeheader(); w.writerows(rows)
            with self.assertRaises(ValueError):
                PIT.club_map(tmp)

    def test_blank_carries_forward_and_no_backfill(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            path = os.path.join(tmp, "merged_gw.csv")
            with open(path, newline="") as fh:
                rows = [r for r in csv.DictReader(fh) if not (int(r["element"]) == 1 and int(r["round"]) in (1, 2, 4))]
            with open(path, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=MERGED_COLS); w.writeheader(); w.writerows(rows)
            cm = PIT.club_map(tmp)
            self.assertEqual([PIT.club_at(cm, 1, g) for g in range(1, 7)], [None, None, "ALP", "ALP", "ALP", "ALP"])
            c = BT.load_2526(tmp)["c"]
            self.assertNotIn(1, PIT.players_at(c, cm, 2))
            self.assertEqual(PIT.players_at(c, cm, 3)[1]["team"], "ALP")
            self.assertEqual(PIT.players_at(c, cm, 3)[1]["pos"], c["players"][1]["pos"])


class Season2627(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        toy_data(cls.tmp.name)
        cls.h = BT.Harness("2026-27", data_dir=cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_reader_is_the_s2_rule(self):
        d = {"events": [{"event": ev, "deadline_time": e["deadline_time"]} for ev, e in self.h.data["events"].items()]}
        rows = E.read_log(os.path.join(self.tmp.name, E.LOG_PATH))
        want = {(int(r["event"]), r["source"], int(r["player_id"])): float(r["predicted"]) for r in E.forecasts(rows, d)}
        got = {(ev, s, pid): v for (ev, s), fc in self.h.data["forecasts"].items() for pid, v in fc.items()}
        self.assertEqual(got, want)
        fc = self.h.data["forecasts"][(5, "own")]
        self.assertEqual(len(fc), 13)                 # the last pre-deadline snapshot, player 14 dropped
        self.assertEqual(fc[1], 9.0)                  # the tie: later row wins
        self.assertNotIn(99.0, fc.values())           # post-deadline never read
        self.assertEqual(self.h.data["dropped"][(5, "own")], 1)

    def test_lockdown_guard(self):
        self.assertEqual(self.h.data["settled"], {5})
        for ev in (4, 6):                              # 4: one fixture unfinished; 6: data_checked = 0
            with self.assertRaises(BT.MissingInput):
                self.h.rows(ev, "own")
        self.assertEqual(self.h.weeks("own"), [5])

    def test_starters_and_components(self):
        rows = self.h.rows(5, "own", "starters")
        self.assertEqual(sorted(pid for pid, _, _ in rows), [p for p in range(1, 14) if p % 3])
        comps = self.h.components(5, "minutes", self.h.rows(5, "minutes"))
        self.assertEqual((len(comps["start"]), comps["_skipped"]), (12, 1))   # the tie row (9.0) is not a probability
        self.assertEqual(self.h.components(5, "own", rows), {})

    def test_decision_uses_our_picks_and_missing_forecast_is_zero(self):
        d, missing, note = self.h.decision(5, "own")
        self.assertEqual(missing, 2)                  # players 14 and 15 have no forecast in the last snapshot
        self.assertEqual(note, "our 15 (picks)")
        pred = self.h.data["forecasts"][(5, "own")]
        act = {pid: float(a["pts"]) for pid, a in self.h.data["actual"][5].items()}
        self.assertEqual(d, BT.decision_points(list(range(1, 16)), pred, act, self.h.data["pos"]))

    def test_compare_needs_a_common_graded_week(self):
        res = self.h.compare("own", "bottomup", "starters")
        self.assertEqual(res["weeks"], [5])
        with self.assertRaises(BT.MissingInput):
            self.h.compare("own", "fpl_ep")


class CLI(unittest.TestCase):
    def test_cli_refuses_not_rebuildable_and_writes_only_under_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            hist = os.path.join(tmp, "hist"); os.makedirs(hist); toy_hist(hist)
            data = os.path.join(tmp, "data"); os.makedirs(data); toy_data(data)
            out = os.path.join(tmp, "out")

            def listing(folder):
                return {f: os.path.getmtime(os.path.join(folder, f)) for f in os.listdir(folder)}
            before = (listing(hist), listing(data))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = BT.main(["--compare", "own", "bottomup", "--season", "2025-26", "--filter", "starters",
                              "--hist", hist, "--data", data, "--out", out])
            self.assertEqual(rc, 2)
            self.assertIn("cannot be rebuilt for 2025/26", buf.getvalue())
            for argv in (["--compare", "bottomup", "minutes", "--season", "2025-26", "--filter", "starters"],
                         ["--compare", "own", "minutes", "--season", "2026-27"],
                         ["--report"], ["--power"], ["--selftest", "--reps", "2"]):
                with redirect_stdout(io.StringIO()):
                    rc = BT.main(argv + ["--hist", hist, "--data", data, "--out", out])
                self.assertEqual(rc, 0, argv)
            self.assertEqual(before, (listing(hist), listing(data)))
            self.assertTrue({"report.txt", "power.txt", "selftest.txt"} <= set(os.listdir(out)))

    def test_nightly_imports_nothing_under_tools_or_analysis(self):
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/analysis/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'backtest')]; "
                "print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "[]")


if __name__ == "__main__":
    unittest.main()
