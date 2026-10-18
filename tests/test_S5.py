"""
tests/test_S5.py - the odds-implied lambda model (prereg/S5.md acceptance tests).

    python -m unittest tests.test_S5
"""

import csv
import gzip
import io
import json
import math
import os
import random
import sqlite3
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


API_NAMES = {"ARS": "Arsenal", "BOU": "Bournemouth", "BRE": "Brentford", "BHA": "Brighton and Hove Albion",
             "CHE": "Chelsea", "EVE": "Everton"}
CLUBS = list(API_NAMES)


def toy_2627(tmp, post_deadline_export=True, export_gw=7, rename=None):
    """A small 2026/27 data folder: six clubs, 30 players, GW4-7 played
    (results before the GW8 deadline), GW8 settled with points, GW9 far in
    the future; exports of gameweek 7 generated before and (optionally)
    after the GW8 deadline, with different stats; a log with bottomup rows
    for GW8; an odds CSV for GW8's fixtures. Returns the GW8 fixtures."""
    rng = random.Random(5)
    db = os.path.join(tmp, "fpl.sqlite")
    c = sqlite3.connect(db)
    c.executescript("""
      create table teams(id integer, name text, short_name text);
      create table events(id integer, deadline_time text, finished integer, data_checked integer);
      create table fixtures(id integer, event integer, kickoff_time text, team_h integer, team_a integer,
        team_h_difficulty integer, team_a_difficulty integer, team_h_score integer, team_a_score integer, finished integer);
      create table players(id integer, position integer);
      create table player_gw(player_id integer, event integer, total_points integer, minutes integer, starts integer,
        clean_sheets integer, goals integer, bonus integer, defensive_contribution integer);
      create table picks(entry_id integer, event integer, player_id integer, position integer);
    """)
    c.executemany("insert into teams values (?,?,?)", [(i, API_NAMES[s], s) for i, s in enumerate(CLUBS, 1)])
    c.executemany("insert into events values (?,?,?,?)",
                  [(ev, f"2026-10-{ev + 10:02d}T11:00:00Z", 1, 1) for ev in range(4, 9)] + [(9, "2099-01-01T12:00:00Z", 0, 0)])
    fid, fixtures, gw8 = 0, [], []
    for ev in range(4, 10):
        pairs = [(1, 2), (3, 4), (5, 6)] if ev % 2 == 0 else [(2, 3), (4, 5), (6, 1)]
        for h, a in pairs:
            fid += 1
            ko = f"2026-10-{ev + 10:02d}T14:00:00Z" if ev < 9 else "2099-01-02T14:00:00Z"
            hs, as_ = (rng.choice([0, 1, 2, 3]), rng.choice([0, 1, 2])) if ev < 9 else (None, None)
            fixtures.append((fid, ev, ko, h, a, 3, 3, hs, as_, 1 if ev < 9 else 0))
            if ev == 8:
                gw8.append({"id": fid, "home": CLUBS[h - 1], "away": CLUBS[a - 1], "hg": hs, "ag": as_})
    c.executemany("insert into fixtures values (?,?,?,?,?,?,?,?,?,?)", fixtures)
    players = []
    pid = 0
    for ti, club in enumerate(CLUBS, 1):
        for pos, n in ((1, 1), (2, 2), (3, 1), (4, 1)):
            for _ in range(n):
                pid += 1
                players.append({"id": pid, "web_name": (rename or {}).get(pid, f"P{pid}"), "team": club, "pos": pos,
                                "price": 4.5 + (pid % 4) * 0.5, "status": "a", "chance_next_round": None})
    c.executemany("insert into players values (?,?)", [(p["id"], p["pos"]) for p in players])
    for p in players:
        for ev in range(4, 9):
            mins = 90 if rng.random() < 0.8 else 0
            c.execute("insert into player_gw values (?,?,?,?,?,?,?,?,?)",
                      (p["id"], ev, rng.randint(0, 10) if mins else 0, mins, 1 if mins else 0,
                       rng.choice([0, 1]) if mins else 0, 0, 0, rng.choice([5, 10, 13]) if mins else 0))
    c.commit(); c.close()
    # exports of gameweek 7: player_gw_recent GW4-7 with player_id; fixtures_next6 = GW8
    def export(generated, boost):
        rows = []
        for p in players:
            for ev in range(4, export_gw + 1):
                mins = 90 if rng.random() < 0.85 else 0
                f = next(x for x in fixtures if x[1] == ev and (x[3] == CLUBS.index(p["team"]) + 1 or x[4] == CLUBS.index(p["team"]) + 1))
                home = f[3] == CLUBS.index(p["team"]) + 1
                rows.append({"event": ev, "player_id": p["id"], "web_name": p["web_name"], "team": p["team"], "pos": p["pos"],
                             "pts": (rng.randint(1, 8) + boost) if mins else 0, "mins": mins, "starts": 1 if mins else 0,
                             "g_": 0, "a_": 0, "cs": rng.choice([0, 1]) if mins else 0, "gc": 1, "bonus": 0, "bps": 10,
                             "defcon": rng.choice([5, 11]) if mins else 0, "xg": round(rng.random() * 0.5 + boost * 0.1, 2) if mins else 0,
                             "xa": 0.1 if mins else 0, "n_fixtures": 1, "opp": CLUBS[(f[4] if home else f[3]) - 1],
                             "venue": "H" if home else "A", "fdr": 3, "opp_goals": 1})
        allp = []
        for p in players:
            mine = [r for r in rows if r["player_id"] == p["id"]]
            allp.append(dict(p, mins_last4=sum(r["mins"] for r in mine), starts_last4=sum(r["starts"] for r in mine),
                             pts_last4=sum(r["pts"] for r in mine), minutes=sum(r["mins"] for r in mine),
                             xg=sum(r["xg"] for r in mine), xa=sum(r["xa"] for r in mine), starts=sum(r["starts"] for r in mine)))
        if export_gw == 7:
            fx = [{"event": 8, "home": g["home"], "away": g["away"], "h_fdr": 3, "a_fdr": 3, "kickoff_time": "2026-10-18T14:00:00Z"} for g in gw8]
        else:
            fx = [{"event": 9, "home": CLUBS[f[3] - 1], "away": CLUBS[f[4] - 1], "h_fdr": 3, "a_fdr": 3, "kickoff_time": f[2]}
                  for f in fixtures if f[1] == 9]
        squads = [{"entry_id": 1, "entry_name": "Us", "slot": i + 1, "player_id": p["id"], "web_name": p["web_name"], "team": p["team"],
                   "pos": p["pos"], "price": p["price"], "multiplier": 1, "is_captain": 0, "is_vice": 0, "gw_points": 0, "minutes": 0,
                   "purchase_price": p["price"], "selling_price": p["price"]}
                  for i, p in enumerate([players[0], players[5], players[1], players[2], players[6], players[11], players[16],
                                         players[3], players[8], players[13], players[18], players[23], players[4], players[9], players[14]])]
        return {"schema": 2, "generated": generated, "league_id": 1, "my_entry": 1, "gameweek": export_gw,
                "standings": [{"entry_id": 1, "entry_name": "Us", "bank": 10, "value": 1000}], "chips_used": [],
                "squads": squads, "all_players": allp, "player_history": [], "fixtures_played": [], "fixtures_next6": fx,
                "player_gw_recent": rows, "events": [], "fixtures_status": [], "teams": [], "league_ownership": [], "transfers": []}
    os.makedirs(os.path.join(tmp, "exports"))
    with gzip.open(os.path.join(tmp, "exports", f"fpl_export_gw{export_gw}_2026-10-17.json.gz"), "wt", encoding="utf-8") as fh:
        json.dump(export("2026-10-17T21:55:00+00:00", 0), fh)
    if post_deadline_export:
        with gzip.open(os.path.join(tmp, "exports", "fpl_export_gw7_2026-10-18.json.gz"), "wt", encoding="utf-8") as fh:
            json.dump(export("2026-10-18T12:00:00+00:00", 3), fh)        # after the GW8 deadline: must never be used
    with open(os.path.join(tmp, E.LOG_PATH), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=E.LOG_FIELDS); w.writeheader()
        for p in players[:5]:
            w.writerow({"made_at": "2026-10-17T21:56:00+00:00", "source": "bottomup", "event": 8, "player_id": p["id"],
                        "web_name": p["web_name"], "predicted": 2.5})
    odds = os.path.join(tmp, "E0_toy27_fetched_2026-10-18.csv")
    with open(odds, "w", newline="") as fh:
        cols = ["Div", "Date", "Time", "HomeTeam", "AwayTeam", "AvgH", "AvgD", "AvgA", "Avg>2.5", "Avg<2.5"]
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        for g in gw8:
            o = odds_for(1.4, 1.0)
            w.writerow({"Div": "E0", "Date": "18/10/2026", "Time": "15:00", "HomeTeam": API_NAMES[g["home"]], "AwayTeam": API_NAMES[g["away"]],
                        "AvgH": f"{o[0]:.3f}", "AvgD": f"{o[1]:.3f}", "AvgA": f"{o[2]:.3f}", "Avg>2.5": f"{o[3]:.3f}", "Avg<2.5": f"{o[4]:.3f}"})
    return gw8, odds


def toy_snapshot(tmp, name, events, fetched_at=None):
    os.makedirs(os.path.join(tmp, "odds"), exist_ok=True)
    payload = {"fetched_at": fetched_at, "events": events} if fetched_at else events
    with gzip.open(os.path.join(tmp, "odds", name), "wt", encoding="utf-8") as fh:
        json.dump(payload, fh)


def api_event(home, away, commence, books):
    """books: [(key, h, d, a, over, under, lay)] - prices per bookmaker; None skips a market."""
    ev = {"id": "x", "sport_key": "soccer_epl", "commence_time": commence, "home_team": API_NAMES[home],
          "away_team": API_NAMES[away], "bookmakers": []}
    for key, h, d, a, over, under, lay in books:
        markets = []
        if h is not None:
            markets.append({"key": "h2h", "outcomes": [{"name": API_NAMES[home], "price": h}, {"name": API_NAMES[away], "price": a},
                                                      {"name": "Draw", "price": d}]})
        if lay:
            markets.append({"key": "h2h_lay", "outcomes": [{"name": API_NAMES[home], "price": 50.0}, {"name": API_NAMES[away], "price": 50.0},
                                                          {"name": "Draw", "price": 50.0}]})
        if over is not None:
            markets.append({"key": "totals", "outcomes": [{"name": "Over", "price": over, "point": 2.5}, {"name": "Under", "price": under, "point": 2.5},
                                                         {"name": "Over", "price": 9.0, "point": 3.5}, {"name": "Under", "price": 1.1, "point": 3.5}]})
        ev["bookmakers"].append({"key": key, "title": key, "markets": markets})
    return ev


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


class Condition(unittest.TestCase):
    def test_condition_uses_the_pre_deadline_export_and_the_starters_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            gw8, odds = toy_2627(tmp)
            exports = OL.dated_exports(tmp)
            name_to_short, deadlines, fixtures, settled, actual = OL.sqlite_tables(tmp)
            self.assertEqual(settled, {4, 5, 6, 7, 8})
            ex = OL.pre_deadline_export(exports, deadlines[8], 8)
            self.assertTrue(ex[1].endswith("fpl_export_gw7_2026-10-17.json.gz"))      # the post-deadline export is never chosen
            self.assertIsNone(OL.pre_deadline_export(exports, datetime(2026, 10, 17, 12, tzinfo=timezone.utc), 8))
            buf = io.StringIO()
            res = OL.condition_2627(tmp, 0.1, lambda s: buf.write(s + chr(10)), odds_file=odds)
            self.assertEqual(res["weeks"], [8])
            text = buf.getvalue()
            self.assertIn("fpl_export_gw7_2026-10-17.json.gz", text)
            self.assertNotIn("2026-10-18.json.gz", text)
            # the starters threshold: n equals the count of rebuilt DEF/GK with P(start) >= 0.8, below the full count
            book = OL.OddsBook(OL.load_odds(odds, name_to_short))
            reb = OL.rebuild_2627(ex[2], 8, book, OL.fit_fallback([], deadlines[8]))
            want = sum(1 for pid, v in reb.items() if v[3] in (1, 2) and v[2] >= OL.STARTER_P and pid in actual[8])
            all_gkdef = sum(1 for v in reb.values() if v[3] in (1, 2))
            self.assertLess(want, all_gkdef)
            line = next(l for l in text.splitlines() if "fpl_export_gw7_2026-10-17" in l)
            self.assertEqual(int(line.split()[2]), want)
            self.assertIn("rows, max |diff|", text)
            # without any pre-deadline export the condition refuses
            for f in os.listdir(os.path.join(tmp, "exports")):
                os.remove(os.path.join(tmp, "exports", f))
            with self.assertRaises(OL.MissingInput):
                OL.condition_2627(tmp, 0.1, lambda s: None, odds_file=odds)


class LiveMode(unittest.TestCase):
    def test_aggregation_means_counts_and_exclusions(self):
        ev = api_event("ARS", "CHE", "2099-01-02T14:00:00Z", [
            ("b1", 2.0, 3.4, 3.8, 1.9, 1.9, True), ("b2", 2.2, 3.6, 3.4, 2.1, 1.7, False), ("b3", None, None, None, 2.0, 1.8, False)])
        agg = OL.aggregate_event(ev)
        self.assertEqual((agg["home"], agg["away"], agg["n_h2h"], agg["n_totals"]), ("ARS", "CHE", 2, 3))
        self.assertAlmostEqual(agg["odds"]["H"], 2.1); self.assertAlmostEqual(agg["odds"]["D"], 3.5); self.assertAlmostEqual(agg["odds"]["A"], 3.6)
        self.assertAlmostEqual(agg["odds"]["over"], 2.0); self.assertAlmostEqual(agg["odds"]["under"], 1.8)   # the 3.5 line and the lay market ignored
        self.assertIsNone(OL.aggregate_event(api_event("ARS", "CHE", "2099-01-02T14:00:00Z", [("b1", 2.0, 3.4, 3.8, None, None, False)])))
        bad = api_event("ARS", "CHE", "2099-01-02T14:00:00Z", [("b1", 2.0, 3.4, 3.8, 1.9, 1.9, False)])
        bad["home_team"] = "Nowhere FC"
        with self.assertRaises(OL.MissingInput):
            OL.aggregate_event(bad)

    def test_snapshot_time_and_selection(self):
        self.assertEqual(OL.snapshot_time("odds_2026-10-22T21-50-00Z.json.gz", []), datetime(2026, 10, 22, 21, 50, tzinfo=timezone.utc))
        self.assertEqual(OL.snapshot_time("odds_2026-10-22.json.gz", []), datetime(2026, 10, 22, 23, 59, 59, tzinfo=timezone.utc))
        self.assertEqual(OL.snapshot_time("x.json.gz", {"fetched_at": "2026-10-22T10:00:00Z"}), datetime(2026, 10, 22, 10, tzinfo=timezone.utc))
        self.assertIsNone(OL.snapshot_time("x.json.gz", []))
        with tempfile.TemporaryDirectory() as tmp:
            dl = datetime(2099, 1, 1, 12, tzinfo=timezone.utc)
            e = [api_event("ARS", "CHE", "2099-01-02T14:00:00Z", [("b1", 2.0, 3.4, 3.8, 1.9, 1.9, False)])]
            toy_snapshot(tmp, "odds_2098-12-30T10-00-00Z.json.gz", e)
            toy_snapshot(tmp, "odds_2098-12-31T10-00-00Z.json.gz", e)
            toy_snapshot(tmp, "odds_2099-01-01T13-00-00Z.json.gz", e)           # after the deadline: ignored
            path, payload, taken = OL.newest_snapshot(tmp, dl)
            self.assertTrue(path.endswith("odds_2098-12-31T10-00-00Z.json.gz"))
            self.assertIsNone(OL.newest_snapshot(tmp, datetime(2098, 1, 1, tzinfo=timezone.utc)))

    def test_live_with_and_without_a_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            gw8, _ = toy_2627(tmp, post_deadline_export=False)
            now = datetime(2098, 12, 1, tzinfo=timezone.utc)
            buf = io.StringIO()
            res = OL.live(tmp, lambda s: buf.write(s + chr(10)), now=now)
            self.assertEqual(res["target"], 9)
            self.assertFalse(res["snapshot"])
            self.assertIn("NO SNAPSHOT", buf.getvalue())
            self.assertTrue(all(src == "fallback" for _, src in res["fixtures"].values()))
            name_to_short, deadlines, fixtures, _, _ = OL.sqlite_tables(tmp)
            gw9 = [f for f in fixtures if f["event"] == 9]
            events = [api_event(f["home"], f["away"], f["kickoff"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                                [("b1", 2.0, 3.4, 3.8, 1.9, 1.9, True), ("b2", 2.2, 3.6, 3.4, 2.1, 1.7, False)]) for f in gw9[:2]]
            toy_snapshot(tmp, "odds_2098-12-31T10-00-00Z.json.gz", events, fetched_at="2098-12-31T10:00:00Z")
            buf = io.StringIO()
            res = OL.live(tmp, lambda s: buf.write(s + chr(10)), now=now)
            self.assertTrue(res["snapshot"])
            srcs = {pair: src for pair, (_, src) in res["fixtures"].items()}
            self.assertEqual(sorted(srcs.values()), ["fallback", "odds", "odds"])          # the third fixture is not in the snapshot
            lam = res["fixtures"][(gw9[0]["home"], gw9[0]["away"])][0]
            want = OL.lambdas_from_odds(2.1, 3.5, 3.6, 2.0, 1.8)
            self.assertAlmostEqual(lam["lambda_home"], want["lambda_home"]); self.assertAlmostEqual(lam["lambda_away"], want["lambda_away"])
            self.assertIn("2/2", buf.getvalue())                                            # bookmaker counts printed
            self.assertIn("is for GW8, not GW9", buf.getvalue())                           # the toy export is a gameweek behind: no squad lines


NON_CP1252 = "\u0106aleta-Car"
CP1252_ENV = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")


def read_utf8(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


def run_cli(module, argv, cwd):
    """One tool's CLI in a subprocess on a cp1252 console."""
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", module + ".py")] + argv,
                          cwd=cwd, capture_output=True, env=CP1252_ENV)


class ConsoleEncoding(unittest.TestCase):
    """RULING S5 amendment fix: each CLI exits 0 on a cp1252 console with a
    non-cp1252 name in play, and its output file holds the name byte-exact."""

    def test_helper_reconfigures_the_console(self):
        code = "import sys; sys.path.insert(0, r'%s'); from console_utf8 import utf8_console; utf8_console(); print('%s')" % (
            os.path.join(ROOT, "tools"), NON_CP1252)
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, env=CP1252_ENV)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.decode("utf-8").strip(), NON_CP1252)
        code = "import sys; print('%s')" % NON_CP1252                   # without the helper the console cannot print it
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, env=CP1252_ENV)
        self.assertNotEqual(r.returncode, 0)

    def test_odds_lambda_live_on_cp1252(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_2627(tmp, post_deadline_export=False, export_gw=8, rename={1: NON_CP1252})   # player 1: our keeper
            out = os.path.join(tmp, "out")
            r = run_cli("odds_lambda", ["--live", "--data", tmp, "--out", out], tmp)
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
            text = read_utf8(os.path.join(out, "odds_lambda_live.txt"))
            self.assertIn(NON_CP1252, text)
            self.assertIn("our GK/DEF for GW9", text)

    def test_chips_live_on_cp1252(self):
        from tests.test_S7 import toy_export
        from tests.test_S4 import toy_data
        with tempfile.TemporaryDirectory() as tmp:
            toy_data(tmp); toy_export(tmp, rename={1: NON_CP1252})         # player 1: our sub keeper, printed by bench prep
            out = os.path.join(tmp, "out")
            r = run_cli("chips", ["--data", tmp, "--out", out, "--resamples", "5"], tmp)
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
            text = read_utf8(os.path.join(out, "chips_live.txt"))
            self.assertIn(NON_CP1252, text)

    def test_backtest_report_on_cp1252(self):
        from tests.test_S4 import toy_hist, toy_data
        with tempfile.TemporaryDirectory() as tmp:
            hist = os.path.join(tmp, "hist"); os.makedirs(hist); toy_hist(hist)
            data = os.path.join(tmp, "data"); os.makedirs(data); toy_data(data)
            out = os.path.join(tmp, "out")
            r = run_cli("backtest", ["--report", "--hist", hist, "--data", data, "--out", out], tmp)
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
            text = read_utf8(os.path.join(out, "report.txt"))   # valid UTF-8; the report prints no names
            self.assertIn("REPORT 2025-26", text)


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
        with tempfile.TemporaryDirectory() as tmp:
            gw8, odds27 = toy_2627(tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = OL.main(["--season", "2026-27", "--condition", "--data", tmp, "--odds", odds27, "--out", out, "--s_d", "0.1"])
            self.assertEqual(rc, 0)
            self.assertTrue(os.path.exists(os.path.join(out, "odds_lambda_condition_2026-27.txt")))
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'odds_lambda', 'chips', 'backtest', 'hist_pit')]; "
                "print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
