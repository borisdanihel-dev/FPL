"""
tests/test_S5.py - the odds-implied lambda model (prereg/S5.md acceptance tests).

    python -m unittest tests.test_S5
"""

import csv
import io
import math
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import odds_lambda as OL                                          # noqa: E402
from tests.test_S4 import toy_hist, TEAMS                         # noqa: E402

FD_NAMES = {"Alpha": "Alpha", "Beta": "Beta", "Gamma": "Gamma", "Delta": "Delta", "Eps": "Eps", "Zeta": "Zeta"}


def odds_for(lam_h, lam_a, margin=1.05):
    """Five odds that imply (lam_h, lam_a) under the model, with a margin."""
    p_h = OL.p_home_win(lam_h, lam_a)
    p_a = OL.p_home_win(lam_a, lam_h)
    p_d = 1 - p_h - p_a
    p_u = OL.poisson_cdf(lam_h + lam_a, 2)
    return [margin / p_h, margin / p_d, margin / p_a, margin / (1 - p_u), margin / p_u]


def toy_season(tmp, skip_fixture=None):
    """toy_hist plus kickoff times in fixtures.csv and an odds CSV covering
    every fixture except `skip_fixture` (its lambdas come from the fallback)."""
    toy_hist(tmp)
    path = os.path.join(tmp, "fixtures.csv")
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["kickoff_time"] = f"2025-08-{14 + int(r['event']):02d}T14:00:00Z"
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    odds = os.path.join(tmp, "E0_toy_fetched_2026-10-18.csv")
    cols = ["Div", "Date", "Time", "HomeTeam", "AwayTeam", "AvgH", "AvgD", "AvgA", "Avg>2.5", "Avg<2.5",
            "AvgCH", "AvgCD", "AvgCA", "PSH", "PSD", "PSA"]
    with open(odds, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        skip = next((r for r in rows if r["id"] == str(skip_fixture)), None)
        for r in rows:
            if skip is not None and (r["team_h"], r["team_a"]) == (skip["team_h"], skip["team_a"]):
                continue                                  # no odds for that pairing anywhere (adjacent toy days)
            lam_h = 1.0 + 0.3 * (int(r["team_h"]) % 3)
            lam_a = 0.8 + 0.2 * (int(r["team_a"]) % 2)
            o = odds_for(lam_h, lam_a)
            d = date(2025, 8, 14 + int(r["event"]))
            w.writerow({"Div": "E0", "Date": d.strftime("%d/%m/%Y"), "Time": "15:00",
                        "HomeTeam": TEAMS[int(r["team_h"]) - 1][0], "AwayTeam": TEAMS[int(r["team_a"]) - 1][0],
                        "AvgH": f"{o[0]:.3f}", "AvgD": f"{o[1]:.3f}", "AvgA": f"{o[2]:.3f}",
                        "Avg>2.5": f"{o[3]:.3f}", "Avg<2.5": f"{o[4]:.3f}",
                        "AvgCH": "9.99", "AvgCD": "9.99", "AvgCA": "9.99", "PSH": "9.99", "PSD": "9.99", "PSA": "9.99"})
    return odds


class Maths(unittest.TestCase):
    def test_demargin(self):
        for odds in ([2.0, 3.0, 6.0], [1.9, 3.4, 4.2], [1.85, 2.05]):
            for f in (OL.demargin_proportional, OL.demargin_power):
                p = f(odds)
                self.assertAlmostEqual(sum(p), 1.0, places=9)
                self.assertEqual(sorted(range(len(p)), key=lambda i: -p[i]), sorted(range(len(odds)), key=lambda i: odds[i]))
        self.assertEqual([round(x, 9) for x in OL.demargin_proportional([2.0, 3.0, 6.0])], [0.5, round(1 / 3, 9), round(1 / 6, 9)])
        self.assertNotEqual(OL.demargin_power([1.9, 3.4, 4.2]), OL.demargin_proportional([1.9, 3.4, 4.2]))

    def test_lambda_total_and_split(self):
        self.assertAlmostEqual(OL.lambda_total(OL.poisson_cdf(2.0, 2)), 2.0, places=6)
        lh, la = OL.split_lambda(2.0, OL.p_home_win(1.0, 1.0))
        self.assertAlmostEqual(lh, 1.0, places=6); self.assertAlmostEqual(la, 1.0, places=6)
        lh, la = OL.split_lambda(3.0, OL.p_home_win(2.0, 1.0))
        self.assertAlmostEqual(lh, 2.0, places=5)
        r = OL.lambdas_from_odds(*odds_for(1.6, 0.9, margin=1.0))
        self.assertAlmostEqual(r["lambda_home"], 1.6, places=4); self.assertAlmostEqual(r["lambda_away"], 0.9, places=4)

    def test_clean_sheet_moves_with_opponent_strength(self):
        weak = OL.lambdas_from_odds(*odds_for(1.0, 0.6))          # home v a weak attack
        strong = OL.lambdas_from_odds(*odds_for(1.0, 1.8))        # home v a strong attack
        self.assertGreater(OL.p_clean_sheet(weak["lambda_away"]), OL.p_clean_sheet(strong["lambda_away"]))
        self.assertAlmostEqual(OL.p_clean_sheet(0.0), 1.0)
        self.assertAlmostEqual(OL.expected_gc_penalty(0.0), 0.0)
        self.assertLess(OL.expected_gc_penalty(1.0), OL.expected_gc_penalty(2.0))
        self.assertAlmostEqual(OL.expected_gc_penalty(2.0), sum(OL.poisson_pmf(2.0, k) * (k // 2) for k in range(16)))

    def test_lambda_terms_and_forecast(self):
        self.assertIsNone(OL.lambda_terms(3, 0.9, 1.0))
        self.assertAlmostEqual(OL.lambda_terms(2, 0.5, 1.0), 0.5 * (math.exp(-1) * 4 - OL.expected_gc_penalty(1.0)))
        with tempfile.TemporaryDirectory() as tmp:
            toy_season(tmp)
            hist = BT.load_2526(tmp)
            c = BT.canonical_at(hist, 5)
            inp = E.reliability_inputs(E.canonical_through(c, 4), gws_played=4)
            seen = set()
            for pid, p in inp["players"].items():
                if p["p_start"] <= 0 or p["pos"] in seen:
                    continue
                if p["pos"] == 2:
                    model = E.project_reliability(pid, inp, [("BET", True)])
                    no_cs = E.project_reliability(pid, inp, [("BET", True)], E.ALL_TERMS - {"cs"})
                    lam = OL.forecast_lambda(pid, inp, [("BET", True, 1.0)])
                    self.assertAlmostEqual(lam, no_cs + OL.lambda_terms(2, p["p_start"], 1.0))
                    self.assertNotAlmostEqual(lam, model)
                    seen.add(2)
                elif p["pos"] in (3, 4):                              # MID and FWD: bottomup unchanged
                    self.assertAlmostEqual(OL.forecast_lambda(pid, inp, [("BET", True, 1.0)]),
                                           E.project_reliability(pid, inp, [("BET", True)]))
                    seen.add(p["pos"])
            self.assertEqual(seen, {2, 3, 4})


class Fallback(unittest.TestCase):
    def results(self):
        d = lambda n: datetime(2025, 9, n, 15, tzinfo=timezone.utc)   # noqa: E731
        return [(d(1), "A", "B", 2, 0), (d(1), "C", "D", 1, 1), (d(8), "B", "C", 0, 3), (d(8), "D", "A", 1, 2),
                (d(15), "A", "C", 3, 1), (d(15), "B", "D", 1, 1), (d(22), "C", "A", 0, 2), (d(22), "D", "B", 2, 2),
                (d(29), "A", "D", 2, 1), (d(29), "C", "B", 1, 0)]

    def test_fit_uses_only_results_before_the_deadline(self):
        res = self.results()
        dl = datetime(2025, 9, 20, 12, tzinfo=timezone.utc)
        m1 = OL.fit_fallback(res, dl)
        m2 = OL.fit_fallback([r for r in res if r[0] < dl], dl)
        self.assertEqual(m1, m2)
        later = [(r[0], r[1], r[2], 9, 9) if r[0] >= dl else r for r in res]
        self.assertEqual(OL.fit_fallback(later, dl), m1)
        self.assertNotEqual(OL.fit_fallback(res, datetime(2025, 10, 1, tzinfo=timezone.utc)), m1)

    def test_strengths_and_decay(self):
        m = OL.fit_fallback(self.results(), datetime(2025, 10, 1, tzinfo=timezone.utc))
        self.assertGreater(m["att"]["A"], m["att"]["B"])          # A scores, B does not
        self.assertGreater(m["hf"], 0)
        lam = OL.fallback_lambdas(m, "A", "B")
        self.assertGreater(lam["lambda_home"], lam["lambda_away"])
        # fewer than 4 weighted matches: league average
        few = OL.fit_fallback(self.results()[:2], datetime(2025, 9, 2, tzinfo=timezone.utc))
        self.assertEqual((few["att"]["A"], few["def"]["A"]), (1.0, 1.0))
        heavy = OL.fit_fallback(self.results(), datetime(2025, 10, 1, tzinfo=timezone.utc), xi=0.5)
        self.assertNotEqual(heavy["att"]["A"], m["att"]["A"])     # the decay weights matter


class OddsFiles(unittest.TestCase):
    def test_pre_closing_columns_only_and_team_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            odds = toy_season(tmp)
            rows = OL.load_odds(odds, FD_NAMES | {n: s for n, s in TEAMS})
            self.assertTrue(rows)
            self.assertTrue(all(r["cols"] == "Avg" for r in rows))
            self.assertTrue(all(r["odds"]["H"] != 9.99 for r in rows))        # closing and Pinnacle never read
            with self.assertRaises(OL.MissingInput):
                OL.load_odds(odds, {"Alpha": "ALP"})                            # an unmapped team stops the run
            book = OL.OddsBook(rows)
            r = rows[0]
            self.assertIs(book.find(datetime(r["date"].year, r["date"].month, r["date"].day, 20, tzinfo=timezone.utc), r["home"], r["away"]), r)
            self.assertIs(book.find(r["date"].replace(day=r["date"].day + 1), r["home"], r["away"]), r)   # the day after still matches
            self.assertIsNone(book.find(r["date"], r["home"], r["home"]))
            self.assertIsNone(book.find(r["date"].replace(month=12), r["home"], r["away"]))

    @unittest.skipUnless(os.path.isdir(OL.ODDS_DIR), "no odds folder")
    def test_real_files_map_every_team(self):
        _, name_to_short, _ = OL.vaastav_tables(os.path.join(ROOT, "historical", "2025-26")) if os.path.isdir(os.path.join(ROOT, "historical", "2025-26")) else (None, None, None)
        if name_to_short:
            rows = OL.load_odds(OL.odds_path("2025-26"), name_to_short)
            self.assertEqual(len(rows), 380)
            self.assertEqual(sum(1 for r in rows if r["cols"] == "B365"), 0)


class Primary(unittest.TestCase):
    def test_primary_test_runs_and_is_point_in_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            odds = toy_season(tmp, skip_fixture=13)                 # one round-5 fixture without odds -> fallback
            buf = io.StringIO()
            res = OL.primary_test(tmp, lambda s: buf.write(s + chr(10)), first=5, last=6, odds_file=odds)
            self.assertEqual([p["gw"] for p in res["per"]], [5, 6])
            self.assertIn("pre-registered bar (a)", buf.getvalue())
            self.assertGreater(res["per"][0]["fallback"], 0)
            s = OL.Season2526(tmp, odds)
            w5 = s.week(5)
            # the sample is GK/DEF with 60+ minutes in the fixture, among players through the gate
            c5 = BT.canonical_at(s.hist, 5)
            inp = E.reliability_inputs(E.canonical_through(c5, 4), gws_played=4)
            want = sum(1 for r in s.hist["raw"][5]
                       if int(r["element"]) in inp["players"] and inp["players"][int(r["element"])]["mins_last4"] >= 45
                       and inp["players"][int(r["element"])]["pos"] in (1, 2) and float(r["minutes"]) >= 60)
            self.assertEqual(len(w5["rows"]), want)
            self.assertGreater(len(s.hist["raw"][5]), want)
            # altering every round >= 5 result leaves round 5's lambdas and forecasts unchanged (fallback trains on rounds < 5)
            s2 = OL.Season2526(tmp, odds)
            for f in s2.fixtures.values():
                if f["event"] >= 5:
                    f["hg"], f["ag"] = 9, 9
            for r in s2.hist["c"]["rows"]:
                if r["event"] >= 5:
                    r["pts"] = 50; r["xg"] = 9.0
            w5b = s2.week(5)
            self.assertEqual(w5["model"], w5b["model"]); self.assertEqual(w5["lambda"], w5b["lambda"])
            self.assertEqual([r["p_lambda"] for r in w5["rows"]], [r["p_lambda"] for r in w5b["rows"]])
            # odds of a later round do not reach round 5
            s3 = OL.Season2526(tmp, odds)
            for key, r in s3.book.by_key.items():
                if key[0] >= date(2025, 8, 20):
                    r["odds"] = {k: v * 3 for k, v in r["odds"].items()}
            self.assertEqual(s3.week(5)["lambda"], w5["lambda"])
            # the Friday flag: the toy kicks off on 2025-08-19 (Tuesday) for round 5
            self.assertFalse(res["per"][0]["friday"])
            self.assertEqual(OL.PASS_BRIER, 0.005)
            self.assertEqual(res["pass_a"], res["boot"]["mean"] >= 0.005 and res["boot"]["lo"] > 0)


class CLI(unittest.TestCase):
    def test_cli_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            odds = toy_season(tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = OL.main(["--season", "2025-26", "--test", "--hist", tmp, "--odds", odds, "--out", out])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(out, "odds_lambda_test_2025-26.txt")))
            with redirect_stdout(io.StringIO()):
                rc = OL.main(["--season", "2026-27", "--condition", "--data", tmp, "--hist", tmp, "--odds", odds, "--out", out, "--s_d", "0.1"])
            self.assertEqual(rc, 2)                                   # no fpl.sqlite in the toy: refused
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'odds_lambda', 'chips', 'backtest', 'hist_pit')]; "
                "print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
