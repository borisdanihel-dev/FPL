"""S6b - the xp_v2 past-season test (tools/xp_v2_replay.py; prereg/S6b.md).
Hermetic: the toy seasons of the S4/S5/S11 tests plus a toy Step 10 root
(a merged_gw with every scoring column, players_raw, elements_positions,
game_config) in temporary folders; no network, no real data."""
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import xp_v2 as XV                                                # noqa: E402
import xp_v2_replay as X                                          # noqa: E402
from tests.test_S4 import MERGED_COLS                             # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S10 import SCORING                                # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402

SCORE_COLS = ("goals_conceded", "saves", "penalties_saved", "penalties_missed", "own_goals", "yellow_cards", "red_cards",
              "clearances_blocks_interceptions", "tackles", "recoveries", "assists", "ict_index")


def toy_rules_root(root, hist_2526, reclassify=None):
    """Step 10's root from the toy 2025/26: 2025-26/merged_gw.csv with every
    scoring column (zeros where the toy has none, the DEFCON components from
    the toy's defensive_contribution), players_raw (code = 1000 + id,
    the toy position), 2026-27/elements_positions (the same positions, or
    `reclassify` = {id: element_type}) and game_config (the S10 toy table)."""
    for d in ("2025-26", "2026-27"):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    with open(os.path.join(hist_2526, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    pos_code = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}
    cols = list(rows[0].keys()) + [c for c in SCORE_COLS if c not in rows[0]]
    seen = {}
    with open(os.path.join(root, "2025-26", "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        for r in rows:
            r = dict(r)
            for c in SCORE_COLS:
                r.setdefault(c, "0")
            dc = int(float(r.get("defensive_contribution") or 0))
            r["clearances_blocks_interceptions"] = str(dc); r["tackles"] = "0"; r["recoveries"] = "0"
            r["ict_index"] = f"{(int(r['element']) % 7) * 1.5:.1f}"
            seen[int(r["element"])] = pos_code[r["position"]]
            w.writerow(r)
    with open(os.path.join(root, "2025-26", "players_raw.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("id,code,element_type\n")
        for pid, et in sorted(seen.items()):
            fh.write(f"{pid},{1000 + pid},{et}\n")
    with open(os.path.join(root, "2026-27", "elements_positions.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("id,code,element_type,web_name\n")
        for pid, et in sorted(seen.items()):
            fh.write(f"{pid},{1000 + pid},{(reclassify or {}).get(pid, et)},P{pid}\n")
    with open(os.path.join(root, "2026-27", "game_config.json"), "w", encoding="utf-8") as fh:
        json.dump({"scoring": SCORING}, fh)
    return root


class Toys(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(); cls.tmp24 = tempfile.mkdtemp(); cls.rules = tempfile.mkdtemp()
        cls.odds = toy_season(cls.tmp, skip_fixture=13)
        toy_prior(cls.tmp24)
        toy_rules_root(cls.rules, cls.tmp, reclassify={10: 3})                     # player 10 (a DEF in the toy) is a MID in 2026/27
        cls.rescored = X.rescore(cls.rules, os.path.join(cls.rules, "rescored.csv"))

    @classmethod
    def tearDownClass(cls):
        for d in (cls.tmp, cls.tmp24, cls.rules):
            shutil.rmtree(d, ignore_errors=True)

    def test_rescored_outcomes_and_the_official_points(self):
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        official = {(pid, ev): v for ev, d in rp.pl.rp.actual.items() for pid, v in d.items()}
        self.assertEqual(set(self.rescored), set(official))                                   # one unit per player-gameweek
        changed = [k for k in official if official[k][0] != self.rescored[k][0]]
        self.assertTrue(changed)                                                              # the 2026/27 table scores differently
        self.assertTrue(all(official[k][1] == self.rescored[k][1] for k in official))          # minutes untouched
        self.assertTrue(any(k[0] == 10 for k in changed))                                     # the reclassified player among them
        with self.assertRaises(X.MissingInput):
            X.rescore(self.tmp, os.path.join(self.rules, "x.csv"))                           # not a Step 10 root: refused

    def test_xp_v2_terms_blend_and_own_proxy(self):
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        v2, detail = rp.xp_v2(5)
        own, p_start = rp.own_proxy(5)
        self.assertTrue(v2)
        c5 = BT.canonical_at(rp.hist, 5)
        inp = E.reliability_inputs(E.canonical_through(c5, 4), gws_played=4)
        for pid, d in detail.items():
            p = inp["players"][pid]
            self.assertAlmostEqual(d["e_xg"], X.xg_half(p["pos"], d["xg"], d["xa"], d["cs"], d["defcon"], d["ict"]))
            self.assertAlmostEqual(v2[pid], XV.xp_candidates(d["p_start"], d["e_xg"], d["e_bl"], d["p_sub"], d["e_sub"])["blend"])
            self.assertAlmostEqual(v2[pid], d["p_start"] * (d["e_xg"] + d["e_bl"]) / 2 + d["p_sub"] * d["e_sub"])   # the equal blend
            self.assertEqual(d["p_start"], p["p_start"])                                       # the current minutes model
            self.assertGreaterEqual(p["mins_last4"], X.GATE_MINS)
            fx = rp.s11.club_fixtures(p["team"], 5)
            want_cs = sum(__import__("odds_lambda").p_clean_sheet(rp.s5.lam_opp(fid, p["team"])[0]) * E.CS_VALUE.get(p["pos"], 0) for fid, f in fx)
            self.assertAlmostEqual(d["cs"], want_cs)                                          # the clean sheet by position: forwards 0, midfielders 1
        self.assertTrue(any(inp["players"][pid]["pos"] == 4 and d["cs"] == 0.0 for pid, d in detail.items()))
        self.assertTrue(any(inp["players"][pid]["pos"] == 2 and d["cs"] > 0.0 for pid, d in detail.items()))
        # the recording gate both models share: a player under 45 minutes in the last four gets no xp_v2 (and no own_proxy)
        gated = X.Replay(self.tmp, self.tmp24, self.odds)
        pid0 = next(iter(v2))
        for r in gated.hist["c"]["rows"]:
            if r["player_id"] == pid0 and r["event"] <= 4:
                r["minutes"] = 10; r["starts"] = 0
        v2g, _ = gated.xp_v2(5); owng, _ = gated.own_proxy(5)
        self.assertNotIn(pid0, v2g); self.assertNotIn(pid0, owng); self.assertIn(pid0, v2)
        # own_proxy is project_reliability on the same training inputs, exactly
        pairings = {m["team"]: [] for m in c5["team_matches"] if m["event"] == 5}
        for m in c5["team_matches"]:
            if m["event"] == 5:
                pairings[m["team"]].append((m["opponent"], m["was_home"]))
        for pid, v in own.items():
            p = inp["players"][pid]
            self.assertAlmostEqual(v, E.project_reliability(pid, inp, pairings[p["team"]]))
        self.assertAlmostEqual(X.xg_half(4, 0.5, 0.2, 0.0, 0.0, 1.0), 2.0 + 0.5 * 4 + 0.2 * 3 + 0.8)   # a forward: goals 4, assists 3, top ICT bonus
        self.assertAlmostEqual(X.xg_half(2, 0.1, 0.1, 0.4 * 4, 2 * 0.5, 0.0), 2.0 + 0.6 + 0.3 + 1.6 + 1.0)
        self.assertEqual(X.OWN_PROXY_LACKS[:14], "own_proxy = pr")
        self.assertIn("form term", X.OWN_PROXY_LACKS); self.assertIn("FDR", X.OWN_PROXY_LACKS); self.assertIn("chance_next_round", X.OWN_PROXY_LACKS)

    def test_sub_inputs_ict_and_defcon_by_hand(self):
        by_round = {1: [{"element": 1, "minutes": 20, "starts": 0, "total_points": 1, "ict_index": 2.0, "defensive_contribution": 12},
                        {"element": 2, "minutes": 90, "starts": 1, "total_points": 6, "ict_index": 9.0, "defensive_contribution": 12}],
                    2: [{"element": 1, "minutes": 90, "starts": 1, "total_points": 2, "ict_index": 4.0, "defensive_contribution": 3},
                        {"element": 2, "minutes": 0, "starts": 0, "total_points": 0, "ict_index": 0.0, "defensive_contribution": 0}],
                    3: [{"element": 1, "minutes": 99, "starts": 0, "total_points": 99, "ict_index": 99.0, "defensive_contribution": 99}]}
        pos = {1: 3, 2: 3}
        p_sub, e_sub = X.sub_inputs_2526(by_round, 3, pos)
        self.assertAlmostEqual(p_sub[1], 0.5); self.assertAlmostEqual(p_sub[2], 0.0)       # 1: one sub appearance in 2 rounds; 2: none
        self.assertAlmostEqual(e_sub[3], 1.0)                                               # the one sub appearance scored 1 (round 3, a sub too, unseen)
        ict = X.ict_percentile(by_round, 3)
        self.assertEqual((ict[1], ict[2]), (0.0, 1.0))                                      # 6.0 against 9.0; round 3 unseen
        by_round[2].append({"element": 3, "minutes": 50, "starts": 1, "total_points": 2, "ict_index": 0.0, "defensive_contribution": 12})
        pos[3] = 3
        dc = X.defcon_rates(by_round, 3, pos)
        self.assertAlmostEqual(dc[1], 2.0 * 0.0 / 1)                                        # 1: one 60+ match, 3 < 12
        self.assertAlmostEqual(dc[2], 2.0 * 1.0 / 1)                                        # 2: one 60+ match, a hit
        self.assertNotIn(3, dc)                                                             # 3: 50 minutes, under 60: no match counted
        self.assertEqual(X.defcon_rates(by_round, 3, {1: 1, 2: 1}), {})                     # keepers: no threshold
        self.assertEqual((X.SUB_WINDOW, X.BONUS_TOP, X.GATE_MINS, X.STARTER_P, X.FIRST, X.LAST), (4, 0.8, 45, 0.8, 5, 38))

    def test_pick_realised_and_the_rescored_actuals(self):
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        rp.pl.rp.actual = X.actuals_from(self.rescored)
        squad = CH.sample_squads(CH.gw1_candidates(rp.hist), 1, 7)[0]
        rows = rp.pl.squad_rows(squad, 5)
        own, _ = rp.own_proxy(5)
        top = max(own.get(r["id"], 0.0) for r in rows)
        flipped = {r["id"]: top - own.get(r["id"], 0.0) for r in rows}                     # the reverse ranking: another XI
        xi_a, cap_a = X.pick(rows, own); xi_b, cap_b = X.pick(rows, flipped)
        self.assertEqual(len(xi_a), 11); self.assertNotEqual(xi_a, xi_b)
        self.assertIn(cap_a, xi_a); self.assertEqual(cap_a, max(xi_a, key=lambda i: (own.get(i, 0.0), -i)))
        tied = {r["id"]: 1.0 for r in rows}                                               # every projection equal: the lowest id captains
        xi_t, cap_t = X.pick(rows, tied)
        self.assertEqual(cap_t, min(xi_t))
        r_a = rp.pl.realised(rows, 5, own)
        # the outcomes are the re-scored points: lifting one XI player's re-scored points lifts the realised total by that much
        pid = next(iter(xi_a))
        pts, mins = rp.pl.rp.actual[5].get(pid, (0.0, 0.0))
        rp.pl.rp.actual[5][pid] = (pts + 50.0, mins if mins else 90.0)
        self.assertGreater(rp.pl.realised(rows, 5, own), r_a)
        rp.pl.rp.actual = X.actuals_from(self.rescored)
        self.assertEqual(rp.pl.realised(rows, 5, own), r_a)

    def test_point_in_time_and_the_output(self):
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        v2, _ = rp.xp_v2(5); own, _ = rp.own_proxy(5)
        rp2 = X.Replay(self.tmp, self.tmp24, self.odds)
        for g in range(5, rp2.hist["through"] + 1):
            for r in rp2.hist["raw"][g]:
                r["minutes"] = "90"; r["starts"] = "1"; r["total_points"] = "50"; r["ict_index"] = "99"; r["defensive_contribution"] = "99"
                r["expected_goals"] = "9"; r["expected_assists"] = "9"
        for r in rp2.hist["c"]["rows"]:
            if r["event"] >= 5:
                r["pts"] = 50; r["xg"] = 9.0; r["minutes"] = 90; r["starts"] = 1
        for f in rp2.fixtures.values():
            if f["event"] >= 5:
                f["hg"], f["ag"] = 9, 9
        for k, r in rp2.s5.book.by_key.items():
            if k[0] >= date(2025, 8, 20):
                r["odds"] = {kk: v * 3 for kk, v in r["odds"].items()}
        for r in rp2.s11.rows:
            if int(r["round"]) >= 5:
                r["expected_goals"] = "9"; r["expected_assists"] = "9"
        rp2.s11.tot = __import__("shares").team_totals(rp2.s11.rows, rp2.s11.n2s)
        v2b, _ = rp2.xp_v2(5); ownb, _ = rp2.own_proxy(5)
        self.assertEqual({p: round(v, 12) for p, v in v2b.items()}, {p: round(v, 12) for p, v in v2.items()})   # nothing of round >= 5 reaches origin 5
        self.assertEqual(ownb, own)
        buf = io.StringIO()
        res = X.test_2526(self.tmp, self.tmp24, self.rules, out=lambda s: buf.write(s + chr(10)), odds_file=self.odds,
                          first=5, last=6, n_squads=3, rescored=self.rescored)
        text = buf.getvalue()
        self.assertEqual([r["gw"] for r in res["per"]], [5, 6])
        self.assertIn("pre-registered bar: 90% lower bound > 0:", text); self.assertIn(X.OWN_PROXY_LACKS, text)
        self.assertIn("season (GW5-6)", text); self.assertIn("secondary (information only)", text)
        self.assertEqual(res["pass"], res["boot"]["lo"] > 0)
        self.assertAlmostEqual(res["season"], sum(r["diff"] for r in res["per"]))
        self.assertEqual(res["squads"], [sorted(p["id"] for p in s) for s in CH.sample_squads(CH.gw1_candidates(rp.hist), 3, 7)])   # S7's squads, seed 7
        # the bar is the 90% lower bound, not the mean
        from unittest import mock
        with mock.patch.object(X.BT, "bootstrap_mean", return_value={"mean": 1.0, "lo": -0.5, "hi": 2.5, "n": 2, "p": 0.5}):
            res_bar = X.test_2526(self.tmp, self.tmp24, self.rules, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=2, rescored=self.rescored)
        self.assertFalse(res_bar["pass"])
        # the outcomes are the re-scored points: lifting every GW5 re-scored total lifts both models' GW5 realised means
        lifted = {k: (v[0] + 30.0, v[1]) if k[1] == 5 else v for k, v in self.rescored.items()}
        res_l = X.test_2526(self.tmp, self.tmp24, self.rules, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=3, rescored=lifted)
        self.assertGreater(res_l["per"][0]["own"], res["per"][0]["own"] + 100)
        self.assertGreater(res_l["per"][0]["v2"], res["per"][0]["v2"] + 100)
        self.assertAlmostEqual(res_l["per"][1]["own"], res["per"][1]["own"])
        with self.assertRaises(X.MissingInput):
            X.test_2526(self.tmp, self.tmp24, self.rules, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=3)   # no re-scored season: refused


class CLI(unittest.TestCase):
    def test_cli_and_isolation(self):
        tmp, tmp24, rules = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            odds = toy_season(tmp); toy_prior(tmp24); toy_rules_root(rules, tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = X.main(["--test", "--hist", tmp, "--prior", tmp24, "--rules", rules, "--odds", odds, "--out", out,
                             "--last", "6", "--squads", "2"])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(out, "rescored_2025-26.csv")))
            with open(os.path.join(out, "xp_v2_replay_2025-26.txt"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("pre-registered bar", text)
            with open(os.path.join(out, "run.txt"), encoding="utf-8") as fh:
                run = fh.read()
            self.assertIn("rescored_2025-26.csv", run); self.assertIn("xp_v2_replay_2025-26.txt", run)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(X.main(["--test", "--hist", tmp, "--prior", tmp24, "--rules", tmp, "--odds", odds, "--out", out]), 2)   # no Step 10 root
                self.assertEqual(X.main(["--hist", tmp]), 2)
        finally:
            for d in (tmp, tmp24, rules):
                shutil.rmtree(d, ignore_errors=True)
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'xp_v2_replay')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
