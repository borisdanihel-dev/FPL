"""S11 - share-of-team allocation with 2024/25 priors (tools/shares.py).
Hermetic: the toy seasons of the S4/S5 tests in temporary folders; no
network, no C:\\GIT\\FPL-data."""
import csv
import io
import math
import os
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
import shares as S                                                # noqa: E402
from tests.test_S4 import toy_hist, MERGED_COLS, TEAMS            # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402


def toy_prior(folder, seed=2, rename=None, drop_club=None):
    """A toy 2024/25: toy_hist with player-linked xG and xA (so the split-half
    reliability is positive); `rename` = {pid: new name}; `drop_club` = a team
    index whose rows are removed (a club without 2024/25 rows)."""
    toy_hist(folder, rounds=6, seed=seed)
    p = os.path.join(folder, "merged_gw.csv")
    with open(p, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out = []
    for r in rows:
        pid = int(r["element"]); mins = float(r["minutes"])
        r["expected_goals"] = f"{(0.05 + 0.5 * ((pid * 7) % 10) / 10) * mins / 90:.3f}"
        r["expected_assists"] = f"{(0.03 + 0.3 * ((pid * 3) % 10) / 10) * mins / 90:.3f}"
        if rename and pid in rename:
            r["name"] = rename[pid]
        if drop_club and r["team"] == TEAMS[drop_club - 1][0]:
            continue
        out.append(r)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=MERGED_COLS); w.writeheader(); w.writerows(out)


def hand_rows(spec, team="Alpha"):
    """Raw rows from {element: [(round, minutes, xg, xa)]}, one fixture per round."""
    rows = []
    for pid, items in spec.items():
        for rnd, mins, xg, xa in items:
            rows.append({"element": pid, "name": f"N{pid}", "team": team, "position": "MID", "fixture": rnd, "round": rnd,
                         "minutes": mins, "starts": 1 if mins >= 60 else 0, "expected_goals": xg, "expected_assists": xa})
    return rows


class Hand(unittest.TestCase):
    def test_shares_and_team_totals(self):
        rows = hand_rows({1: [(1, 90, 0.5, 0.1), (2, 90, 0.5, 0.3)], 2: [(1, 90, 1.5, 0.3), (2, 0, 0.0, 0.0)]})
        n2s = {"Alpha": "ALP"}
        tot = S.team_totals(rows, n2s)
        self.assertAlmostEqual(tot[("1", "ALP")]["xg"], 2.0); self.assertAlmostEqual(tot[("2", "ALP")]["xa"], 0.3)
        agg = S.player_sums(rows, n2s, {1, 2}, tot)
        self.assertAlmostEqual(S.share_of(agg[1], "xg"), 1.0 / 2.5)                  # own 1.0 over team 2.0 + 0.5 (the fixtures he appeared in)
        self.assertAlmostEqual(S.share_of(agg[2], "xg"), 1.5 / 2.0)                  # round 2 (0 minutes) does not count
        self.assertEqual(agg[1]["starts"], 2); self.assertAlmostEqual(agg[1]["start_minutes"], 180)
        self.assertAlmostEqual(S.share_of({"xg": 0.0, "team_xg": 0.0}, "xg"), 0.0)    # no appearance: 0

    def test_credibility_k_by_hand(self):
        # three players, rounds 1-4, 90 minutes each; shares ordered 1 < 2 < 3 in odd rounds and 1 < 3 < 2 in even:
        # tie-free Spearman = 1 - 6 x 2 / (3 x 8) = 0.5; n = 2 matches per half; k = n (1 - r) / r = 2
        spec = {1: [], 2: [], 3: []}
        for rnd in (1, 2, 3, 4):
            xg = (0.1, 0.2, 0.3) if rnd % 2 else (0.1, 0.3, 0.2)
            for i, pid in enumerate((1, 2, 3)):
                spec[pid].append((rnd, 90, xg[i], xg[i] / 2))
        rows = hand_rows(spec); n2s = {"Alpha": "ALP"}
        tot = S.team_totals(rows, n2s)
        k, rel = S.credibility_k(rows, n2s, tot, {1, 2, 3, 4}, "xg")
        self.assertAlmostEqual(rel["r"], 0.5); self.assertAlmostEqual(rel["n"], 2.0); self.assertAlmostEqual(k, 2.0)
        self.assertEqual(rel["players"], 3)
        spec[3] = [(rnd, 20, 0.1, 0.0) for rnd in (1, 2, 3, 4)]                      # 40 minutes a half, under 45: out of the population
        rows = hand_rows(spec); tot = S.team_totals(rows, n2s)
        with self.assertRaises(S.MissingInput):
            S.credibility_k(rows, n2s, tot, {1, 2, 3, 4}, "xg")                       # fewer than 3 players
        # a perfectly consistent share gives k = 0; a reversed one is refused (r <= 0), never fabricated
        spec = {pid: [(rnd, 90, 0.1 * pid, 0.0) for rnd in (1, 2, 3, 4)] for pid in (1, 2, 3)}
        rows = hand_rows(spec); tot = S.team_totals(rows, n2s)
        self.assertAlmostEqual(S.credibility_k(rows, n2s, tot, {1, 2, 3, 4}, "xg")[0], 0.0)
        spec = {pid: [(rnd, 90, (0.1 * pid if rnd % 2 else 0.4 - 0.1 * pid), 0.0) for rnd in (1, 2, 3, 4)] for pid in (1, 2, 3)}
        rows = hand_rows(spec); tot = S.team_totals(rows, n2s)
        with self.assertRaises(S.MissingInput):
            S.credibility_k(rows, n2s, tot, {1, 2, 3, 4}, "xg")
        self.assertEqual((S.HALF_MINUTES, S.PRIOR_MINS, S.STARTER_P, S.HOLM_ALPHA), (45, 180, 0.8, 0.10))

    def test_prior_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "teams.csv"), "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=["id", "name", "short_name"]); w.writeheader()
                w.writerow({"id": 1, "name": "Alpha", "short_name": "ALP"}); w.writerow({"id": 2, "name": "Beta", "short_name": "BET"})
            rows = []
            # Alpha: Ann (0.5 of team xG, 180 minutes), Bob (0.3, 180), Cy (0.2, 180); Beta: Dee (0.6, 180), Eve (0.4, 100 - under 180)
            for rnd in (1, 2):
                for pid, name, team, xg in ((1, "Ann", "Alpha", 0.5), (2, "Bob", "Alpha", 0.3), (3, "Cy", "Alpha", 0.2), (4, "Dee", "Beta", 0.6)):
                    rows.append({"element": pid, "name": name, "team": team, "position": "MID", "fixture": rnd * 10 + (1 if team == "Alpha" else 2),
                                 "round": rnd, "minutes": 90, "starts": 1, "expected_goals": xg, "expected_assists": xg / 2})
                rows.append({"element": 5, "name": "Eve", "team": "Beta", "position": "MID", "fixture": rnd * 10 + 2, "round": rnd,
                             "minutes": 50, "starts": 0, "expected_goals": 0.4, "expected_assists": 0.2})
                rows.append({"element": 6, "name": "Pep", "team": "Alpha", "position": "AM", "fixture": rnd * 10 + 1, "round": rnd,
                             "minutes": 90, "starts": 1, "expected_goals": 0, "expected_assists": 0})
            cols = list(rows[0].keys())
            with open(os.path.join(tmp, "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
            pr = S.Prior(tmp)
            self.assertAlmostEqual(pr.prior("Ann", 3, "ALP", "xg")[0], 0.5)                          # own 2024/25 at the club
            self.assertEqual(pr.prior("Ann", 3, "ALP", "xg")[1], "own 2024/25 at the club")
            s, how = pr.prior("Ann", 3, "BET", "xg")                                                 # a club change: Beta's MID mean
            self.assertAlmostEqual(s, 0.6); self.assertEqual(how, "club-position mean")               # Dee only: Eve has 100 minutes, under 180
            self.assertAlmostEqual(pr.prior("Zed", 3, "ALP", "xg")[0], (0.5 + 0.3 + 0.2) / 3)       # no 2024/25 minutes: Alpha's MID mean
            s, how = pr.prior("Zed", 3, "SUN", "xg")                                                 # a club without 2024/25 rows
            self.assertAlmostEqual(s, (0.5 + 0.3 + 0.2 + 0.6) / 4); self.assertIn("league-position mean", how)
            with self.assertRaises(S.MissingInput):
                pr.prior("Zed", 1, "SUN", "xg")                                                      # no keeper at all in the toy: nothing to fabricate
            self.assertNotIn(("Pep", "ALP"), pr.by_name_club)                                        # manager rows out
            self.assertAlmostEqual(pr.k["xg"], 0.0)                                                  # consistent shares: r = 1

    def test_logloss_and_holm_by_hand(self):
        rows = [{"xg": 1.0, "goals": 1}, {"xg": 0.0, "goals": 0}]
        self.assertAlmostEqual(S.logloss_goal(rows, "xg"), (-math.log(1 - math.exp(-1.0)) - math.log(1 - 1e-6)) / 2)
        pos = [0.05] * 20                                                                            # surely positive: p = 1 / (B + 1)
        mixed = [0.5, -0.4] * 10                                                                     # mean +0.05, an interval through 0
        zero = [0.1, -0.1] * 10
        h = S.holm_intervals({"a": pos, "b": zero})
        self.assertEqual((h["a"]["level"], h["b"]["level"]), (0.95, 0.90))                          # the smaller p first, at 95%
        self.assertTrue(h["a"]["adopt"]); self.assertTrue(h["b"]["tested"]); self.assertFalse(h["b"]["adopt"])
        h = S.holm_intervals({"a": mixed, "b": zero})
        self.assertFalse(h["a"]["adopt"]); self.assertFalse(h["b"]["tested"]); self.assertFalse(h["b"]["adopt"])   # Holm stops
        # the stop bites: `first` fails at 95% (its 90% bound is positive); `second` would pass at 90% alone but is not tested
        first = [-0.02, 0.003, 0.051, 0.016, 0.153, -0.036, 0.208, -0.045, 0.135, -0.027, 0.187, 0.053, 0.076, 0.107, -0.015, -0.05, -0.137, 0.149, -0.02, -0.011]
        second = [0.067, -0.047, -0.0, 0.152, -0.127, 0.007, -0.073, 0.225, 0.122, 0.112, 0.099, 0.087, 0.087, -0.119, 0.084, 0.12, -0.101, 0.146, 0.128, -0.112]
        self.assertGreater(BT.bootstrap_mean(first)["lo"], 0); self.assertLessEqual(BT.bootstrap_mean(first, ci=0.95)["lo"], 0)
        self.assertGreater(BT.bootstrap_mean(second)["lo"], 0); self.assertLess(BT.bootstrap_mean(first)["p"], BT.bootstrap_mean(second)["p"])
        h = S.holm_intervals({"first": first, "second": second})
        self.assertEqual(h["first"]["level"], 0.95); self.assertFalse(h["first"]["adopt"]); self.assertTrue(h["first"]["tested"])
        self.assertFalse(h["second"]["tested"]); self.assertFalse(h["second"]["adopt"])
        h = S.holm_intervals({"a": zero, "b": pos})
        self.assertEqual(h["b"]["level"], 0.95); self.assertTrue(h["b"]["adopt"]); self.assertFalse(h["a"]["adopt"])
        b95 = BT.bootstrap_mean(pos, ci=0.95)
        self.assertAlmostEqual(h["b"]["lo"], b95["lo"])                                             # the Holm interval is the bootstrap at that level


class Season(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); cls.tmp24 = tempfile.TemporaryDirectory()
        cls.odds = toy_season(cls.tmp.name, skip_fixture=13)
        toy_prior(cls.tmp24.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup(); cls.tmp24.cleanup()

    def test_sample_forecast_and_comparator(self):
        s = S.Season(self.tmp.name, self.tmp24.name, self.odds)
        o = s.origin(5)
        c5 = BT.canonical_at(s.hist, 5)
        inp = E.reliability_inputs(E.canonical_through(c5, 4), gws_played=4)
        want = sorted(pid for pid, p in inp["players"].items() if p["p_start"] >= 0.8 and p["pos"])
        self.assertEqual(sorted(r["pid"] for r in o["rows"]), want)                               # every club plays every toy round
        self.assertTrue(any(p["p_start"] < 0.8 for p in inp["players"].values()))
        agg = S.player_sums(s.rows, s.n2s, {1, 2, 3, 4}, s.tot)
        for r in o["rows"]:
            p = inp["players"][r["pid"]]; a = agg.get(r["pid"])
            m_start = a["start_minutes"] / a["starts"] if a and a["starts"] else None
            if m_start is not None:
                self.assertAlmostEqual(r["ms"], p["p_start"] * m_start / 90.0)                    # expected minutes share
            self.assertLessEqual(r["ms"], p["p_start"] + 1e-9)
            lams = [s.lambda_team(fid, p["team"])[0] for fid, f in s.club_fixtures(p["team"], 5)]
            for key in ("xg", "xa"):
                z = r["m"] / (r["m"] + s.prior.k[key])
                self.assertAlmostEqual(r["z_" + key], z)
                shrunk = z * r["s_" + key] + (1 - z) * r["s0_" + key]
                self.assertAlmostEqual(r[key], sum(lam * shrunk * r["ms"] for lam in lams))         # lambda x shrunk share x minutes share
                self.assertAlmostEqual(r[key + "_cmp"], sum(lam * r["s_" + key] * r["ms"] for lam in lams))   # the comparator: Z = 1
                self.assertAlmostEqual(r["s_" + key], S.share_of(a, key) if a else 0.0)
                self.assertEqual(r["prior_" + key], "own 2024/25 at the club")                      # the toy keeps every player at his club
            self.assertEqual(r["goals"], sum(float(x.get("goals_scored") or 0) for x in s.hist["raw"][5] if int(x["element"]) == r["pid"]))
        self.assertTrue(any(r["xg"] != r["xg_cmp"] for r in o["rows"]))
        self.assertTrue(any("fallback" in r["sources"] for r in o["rows"]))
        # the minutes share: a starter who plays 70 minutes a start gets 70/90 of his P(start) (the toy's starters play 90)
        pid0 = o["rows"][0]["pid"]
        s70 = S.Season(self.tmp.name, self.tmp24.name, self.odds)
        for r in s70.rows:
            if int(r["element"]) == pid0 and int(r["round"]) < 5 and float(r["minutes"]) >= 60:
                r["minutes"] = "70"
        r70 = next(r for r in s70.origin(5)["rows"] if r["pid"] == pid0)
        self.assertAlmostEqual(r70["ms"], inp["players"][pid0]["p_start"] * 70 / 90.0)
        self.assertLess(r70["ms"], o["rows"][0]["ms"])

    def test_name_match_club_change_and_promoted(self):
        base = S.Season(self.tmp.name, self.tmp24.name, self.odds).origin(5)["rows"]
        c5 = BT.canonical_at(S.Season(self.tmp.name, self.tmp24.name, self.odds).hist, 5)
        pid0 = next(r["pid"] for r in base if r["team"] != TEAMS[1][1])                          # a sampled player outside Beta
        with tempfile.TemporaryDirectory() as tmp24:
            toy_prior(tmp24, rename={pid0: "Somebody Else"}, drop_club=2)                       # pid0 unmatched; team 2 (Beta) absent in 2024/25
            s = S.Season(self.tmp.name, tmp24, self.odds)
            o = s.origin(5)
            by = {r["pid"]: r for r in o["rows"]}
            for pid, r in by.items():
                club = c5["players"][pid]["team"]
                if pid == pid0:
                    self.assertEqual(r["prior_xg"], "club-position mean")
                elif club == TEAMS[1][1]:
                    self.assertIn("league-position mean", r["prior_xg"])
                else:
                    self.assertEqual(r["prior_xg"], "own 2024/25 at the club")
            self.assertIn(pid0, by); self.assertTrue(any(c5["players"][pid]["team"] == TEAMS[1][1] for pid in by))

    def test_point_in_time(self):
        s = S.Season(self.tmp.name, self.tmp24.name, self.odds)
        o = s.origin(5)
        key = lambda o: [(r["pid"], round(r["xg"], 12), round(r["xa"], 12), round(r["xg_cmp"], 12), round(r["z_xg"], 12)) for r in o["rows"]]
        s2 = S.Season(self.tmp.name, self.tmp24.name, self.odds)
        for r in s2.rows:
            if int(r["round"]) >= 5:
                r["expected_goals"] = "9"; r["expected_assists"] = "9"; r["minutes"] = "90"; r["starts"] = "1"
        for g in range(5, s2.hist["through"] + 1):
            for r in s2.hist["raw"][g]:
                r["goals_scored"] = "9"; r["minutes"] = "90"
        for r in s2.hist["c"]["rows"]:
            if r["event"] >= 5:
                r["xg"] = 9.0; r["minutes"] = 90; r["starts"] = 1
        for f in s2.fixtures.values():
            if f["event"] >= 5:
                f["hg"], f["ag"] = 9, 9
        for k, r in s2.s.book.by_key.items():
            if k[0] >= date(2025, 8, 20):
                r["odds"] = {kk: v * 3 for kk, v in r["odds"].items()}
        s2.tot = S.team_totals(s2.rows, s2.n2s)
        o2 = s2.origin(5)
        self.assertEqual(key(o2), key(o))                                                        # nothing of round >= 5 reaches origin 5 ...
        self.assertTrue(all(r["goals"] == 9 * sum(1 for x in s2.hist["raw"][5] if int(x["element"]) == r["pid"]) for r in o2["rows"]))   # ... but the outcomes
        # 2024/25 altered: the priors move, the current shares do not
        with tempfile.TemporaryDirectory() as tmp24:
            toy_prior(tmp24, seed=5)
            s3 = S.Season(self.tmp.name, tmp24, self.odds)
            o3 = s3.origin(5)
            self.assertEqual([r["s_xg"] for r in o3["rows"]], [r["s_xg"] for r in o["rows"]])
            self.assertEqual([r["xg_cmp"] for r in o3["rows"]], [r["xg_cmp"] for r in o["rows"]])
            self.assertNotEqual([r["s0_xg"] for r in o3["rows"]], [r["s0_xg"] for r in o["rows"]])
        buf = io.StringIO()
        res = S.test_2526(self.tmp.name, self.tmp24.name, out=lambda t: buf.write(t + chr(10)), first=5, last=6, odds_file=self.odds)
        text = buf.getvalue()
        self.assertEqual([r["gw"] for r in res["per"]], [5, 6])
        self.assertIn(S.MANAGER_LINE, text); self.assertIn("manager changes: not modelled", text)
        self.assertIn("pre-registered result: goals", text); self.assertIn("Holm level 95%", text)
        with self.assertRaises(S.MissingInput):
            s.origin(1)


class CLI(unittest.TestCase):
    def test_cli_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tmp24:
            odds = toy_season(tmp); toy_prior(tmp24)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = S.main(["--test", "--hist", tmp, "--prior", tmp24, "--odds", odds, "--out", out, "--last", "6"])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "shares_test_2025-26.txt"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("pre-registered result", text); self.assertIn("not modelled", text)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(S.main(["--test", "--hist", tmp, "--prior", os.path.join(tmp, "nowhere"), "--out", out]), 2)   # a missing prior folder: refused
                self.assertEqual(S.main(["--hist", tmp]), 2)
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'shares')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
