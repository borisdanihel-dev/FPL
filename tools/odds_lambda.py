"""
tools/odds_lambda.py - the odds-implied fixture lambda (BUILD_PLAN.md Step 5,
item S5, offline). Standard library only; the nightly never imports it. The
live Odds API collector is lane A's W1; this module reads football-data.co.uk
CSVs (tools/odds/E0_<season>_fetched_<date>.csv, pre-closing columns only).

    python tools/odds_lambda.py --season 2025-26 --test        # the pre-registered primary test
    python tools/odds_lambda.py --season 2026-27 --condition   # the 2026/27 condition + its power
    python tools/odds_lambda.py --fixture ARS CHE               # lambda, source, P(cs) for one pairing

Definitions, as pre-registered in prereg/S5.md (with amendment 1):
  odds       AvgH/AvgD/AvgA, Avg>2.5/Avg<2.5; where a row lacks them, B365.
             Never a closing column (any *C* column), never Pinnacle.
  de-margin  proportional (p_i = q_i / sum q) and power (p_i = q_i^k, k by
             bisection so sum p = 1); the forecast uses the power method.
  lambda     total goals from P(under 2.5) by bisection on the Poisson CDF
             at 2; home/away split by bisection on P(home win) under
             independent Poisson; P(clean sheet for a team) = exp(-lambda_opp).
  fallback   a time-decayed Poisson team model on results before the
             deadline (weights exp(-0.0065 x days), league average for a
             team with fewer than 4 weighted matches); which source fired is
             printed per fixture.
  source     bottomup_lambda = bottomup with the GK/DEF clean-sheet term's
             lambda replaced by lambda_opp and a goals-conceded term
             -P(start) x E[floor(GC/2)] under Poisson(lambda_opp); MID and
             FWD unchanged.
  primary    2025/26 GW5-38, GK/DEF with 60+ minutes in the fixture: Brier of
             P(clean sheet), bottomup minus bottomup_lambda per gameweek,
             paired bootstrap (B = 10,000, 90%, seed 20261018); pass if the
             mean improvement >= 0.005 with the CI lower bound > 0; AND the
             2026/27 condition: starters-only DEF/GK Spearman does not fall
             (the 90% CI upper bound of lambda - bottomup >= 0), its power
             printed from the S4 calculator.
"""

import argparse
import csv
import glob
import gzip
import json
import math
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402

XI = 0.0065                 # Dixon-Coles decay per day
MIN_WEIGHTED = 4.0          # below this weighted match count the fallback uses the league average
MAX_GOALS = 15
PASS_BRIER = 0.005
POWER_DELTA = 0.02
STARTER_P = BT.STARTER_P
SEED = BT.SEED
ODDS_DIR = os.path.join(ROOT, "tools", "odds")
# football-data.co.uk names that differ from the FPL / vaastav team names
FD_ALIASES = {"Man United": "Man Utd", "Tottenham": "Spurs", "Coventry": "Coventry City",
              "Hull": "Hull City", "Ipswich": "Ipswich Town", "Nott'm Forest": "Nott'm Forest"}
PRE_CLOSING = (("AvgH", "AvgD", "AvgA", "Avg>2.5", "Avg<2.5"),
               ("B365H", "B365D", "B365A", "B365>2.5", "B365<2.5"))


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# odds -> probabilities -> lambda
# ---------------------------------------------------------------------------

def demargin_proportional(odds):
    q = [1.0 / o for o in odds]
    s = sum(q)
    return [x / s for x in q]


def demargin_power(odds, tol=1e-12):
    """p_i = q_i^k with k solved by bisection so that sum p_i = 1."""
    q = [1.0 / o for o in odds]
    lo, hi = 0.5, 3.0
    for _ in range(200):
        k = (lo + hi) / 2
        s = sum(x ** k for x in q)
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            lo = k
        else:
            hi = k
    return [x ** k for x in q]


def poisson_pmf(lam, k):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_cdf(lam, k):
    return sum(poisson_pmf(lam, i) for i in range(k + 1))


def lambda_total(p_under, tol=1e-10):
    """Total goals lambda with P(0, 1 or 2 goals) = p_under, by bisection."""
    if not 0.0 < p_under < 1.0:
        raise ValueError(f"P(under 2.5) must be in (0, 1), got {p_under}")
    lo, hi = 1e-6, 15.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if poisson_cdf(mid, 2) > p_under:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def p_home_win(lam_h, lam_a, n=MAX_GOALS):
    ph = [poisson_pmf(lam_h, i) for i in range(n + 1)]
    pa = [poisson_pmf(lam_a, j) for j in range(n + 1)]
    return sum(ph[i] * pa[j] for i in range(n + 1) for j in range(i))


def split_lambda(total, p_home, tol=1e-10):
    """(lambda_home, lambda_away) with lambda_home + lambda_away = total and
    P(home win) = p_home under independent Poisson, by bisection."""
    lo, hi = 1e-6, total - 1e-6
    for _ in range(200):
        mid = (lo + hi) / 2
        if p_home_win(mid, total - mid) < p_home:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    lh = (lo + hi) / 2
    return lh, total - lh


def lambdas_from_odds(o_h, o_d, o_a, o_over, o_under, method="power"):
    """{lambda_home, lambda_away, p_home, p_under, method} from five odds."""
    dm = demargin_power if method == "power" else demargin_proportional
    p_h, _, _ = dm([o_h, o_d, o_a])
    _, p_under = dm([o_over, o_under])
    total = lambda_total(p_under)
    lh, la = split_lambda(total, p_h)
    return {"lambda_home": lh, "lambda_away": la, "p_home": p_h, "p_under": p_under, "method": method}


def p_clean_sheet(lam_opp):
    return math.exp(-lam_opp)


def expected_gc_penalty(lam_opp, n=MAX_GOALS):
    """E[floor(GC / 2)] under Poisson(lambda_opp): the goals-conceded points a
    GK or DEF loses, in expectation."""
    return sum(poisson_pmf(lam_opp, k) * (k // 2) for k in range(n + 1))


# ---------------------------------------------------------------------------
# the odds files and the fixture join
# ---------------------------------------------------------------------------

def odds_path(season, folder=ODDS_DIR):
    files = sorted(glob.glob(os.path.join(folder, f"E0_{season}_fetched_*.csv")))
    if not files:
        raise MissingInput(f"no odds file for {season} under {folder}")
    return files[-1]


def _fd_date(s):
    d, m, y = s.split("/")
    y = int(y) if len(y) == 4 else 2000 + int(y)
    return date(y, int(m), int(d))


def load_odds(path, name_to_short):
    """[{date, home, away, odds (H, D, A, over, under), cols ('Avg' | 'B365')}]
    reading pre-closing columns only. An unmapped team name stops the run."""
    out = []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if not r.get("Date"):
                continue
            teams = []
            for name in (r["HomeTeam"], r["AwayTeam"]):
                short = name_to_short.get(FD_ALIASES.get(name, name))
                if short is None:
                    raise MissingInput(f"odds row {r['Date']} {r['HomeTeam']} v {r['AwayTeam']}: "
                                       f"team {name!r} is not in the team table")
                teams.append(short)
            vals = None
            for cols in PRE_CLOSING:
                try:
                    vals = [float(r[c]) for c in cols]
                    tag = cols[0][:-1]
                    break
                except (KeyError, ValueError, TypeError):
                    continue
            if vals is None:
                continue
            out.append({"date": _fd_date(r["Date"]), "home": teams[0], "away": teams[1],
                        "odds": dict(zip(("H", "D", "A", "over", "under"), vals)), "cols": tag})
    return out


class OddsBook:
    """Odds by (date, home, away), matched to a fixture by its kickoff date
    (the same day, else the day before or after)."""

    def __init__(self, rows):
        self.by_key = {(r["date"], r["home"], r["away"]): r for r in rows}

    def find(self, kickoff, home, away):
        d0 = kickoff.date() if isinstance(kickoff, datetime) else kickoff
        for delta in (0, -1, 1):
            r = self.by_key.get((d0 + timedelta(days=delta), home, away))
            if r is not None:
                return r
        return None


# ---------------------------------------------------------------------------
# the fallback: a time-decayed Poisson team model
# ---------------------------------------------------------------------------

def fit_fallback(results, deadline, xi=XI, iters=20):
    """results: [(kickoff datetime/date, home, away, home_goals, away_goals)];
    only results with kickoff before `deadline` are used, weighted
    exp(-xi x days before the deadline). Returns {"m", "hf", "att", "def",
    "n"} - multiplicative strengths by alternating weighted updates; a team
    with fewer than MIN_WEIGHTED weighted matches keeps strength 1."""
    dl = deadline.date() if isinstance(deadline, datetime) else deadline
    used = []
    for ko, h, a, hg, ag in results:
        kd = ko.date() if isinstance(ko, datetime) else ko
        if kd < dl and hg is not None and ag is not None:
            used.append((math.exp(-xi * (dl - kd).days), h, a, float(hg), float(ag)))
    if not used:
        return {"m": 1.3, "hf": 1.0, "att": {}, "def": {}, "n": {}}
    wsum = sum(w for w, *_ in used)
    m = sum(w * (hg + ag) for w, _, _, hg, ag in used) / (2 * wsum)
    home_goals = sum(w * hg for w, _, _, hg, _ in used)
    away_goals = sum(w * ag for w, _, _, _, ag in used)
    hf = home_goals / away_goals if away_goals > 0 else 1.0
    teams = {t for _, h, a, _, _ in used for t in (h, a)}
    n = {t: sum(w for w, h, a, _, _ in used if t in (h, a)) for t in teams}
    att = {t: 1.0 for t in teams}
    dfc = {t: 1.0 for t in teams}
    sh, sa = math.sqrt(hf), 1 / math.sqrt(hf)
    for _ in range(iters):
        new_att = {}
        for t in teams:
            if n[t] < MIN_WEIGHTED:
                new_att[t] = 1.0
                continue
            num = sum(w * (hg if h == t else ag) for w, h, a, hg, ag in used if t in (h, a))
            den = sum(w * m * (dfc[a] * sh if h == t else dfc[h] * sa) for w, h, a, _, _ in used if t in (h, a))
            new_att[t] = num / den if den else 1.0
        att = new_att
        new_def = {}
        for t in teams:
            if n[t] < MIN_WEIGHTED:
                new_def[t] = 1.0
                continue
            num = sum(w * (ag if h == t else hg) for w, h, a, hg, ag in used if t in (h, a))
            den = sum(w * m * (att[a] * sa if h == t else att[h] * sh) for w, h, a, _, _ in used if t in (h, a))
            new_def[t] = num / den if den else 1.0
        dfc = new_def
    return {"m": m, "hf": hf, "att": att, "def": dfc, "n": n}


def fallback_lambdas(model, home, away):
    m, hf = model["m"], model["hf"]
    att, dfc = model["att"], model["def"]
    lh = m * att.get(home, 1.0) * dfc.get(away, 1.0) * math.sqrt(hf)
    la = m * att.get(away, 1.0) * dfc.get(home, 1.0) / math.sqrt(hf)
    return {"lambda_home": lh, "lambda_away": la, "method": "fallback"}


def fixture_lambdas(book, model, kickoff, home, away, method="power"):
    """(lambdas, source): the odds row's lambdas, else the fallback's."""
    r = book.find(kickoff, home, away) if book is not None else None
    if r is not None:
        o = r["odds"]
        return lambdas_from_odds(o["H"], o["D"], o["A"], o["over"], o["under"], method), "odds"
    return fallback_lambdas(model, home, away), "fallback"


# ---------------------------------------------------------------------------
# the source: bottomup_lambda
# ---------------------------------------------------------------------------

def lambda_terms(pos, ps, lam_opp):
    """The GK/DEF clean-sheet and goals-conceded terms under lambda_opp, in
    points; None for MID/FWD (their terms are bottomup's own)."""
    if pos not in (1, 2) or ps <= 0:
        return None
    return ps * (p_clean_sheet(lam_opp) * E.CS_VALUE[pos] - expected_gc_penalty(lam_opp))


def forecast_lambda(pid, inp, fixtures):
    """bottomup_lambda for one player: fixtures = [(opp, was_home, lambda_opp)].
    MID/FWD: project_reliability unchanged. GK/DEF: every term but the
    clean sheet, plus lambda_terms per fixture."""
    if not fixtures:
        return None
    p = inp["players"].get(pid)
    if p is None:
        return None
    pairs = [(opp, home) for opp, home, _ in fixtures]
    if p["pos"] not in (1, 2):
        return E.project_reliability(pid, inp, pairs, E.ALL_TERMS)
    base = E.project_reliability(pid, inp, pairs, E.ALL_TERMS - {"cs"})
    if not base:
        return base
    return base + sum(lambda_terms(p["pos"], p["p_start"], lam) or 0.0 for _, _, lam in fixtures)


# ---------------------------------------------------------------------------
# 2025/26: the pre-registered primary test
# ---------------------------------------------------------------------------

def vaastav_tables(hist_dir):
    """teams (id -> short, name -> short) and fixtures (id -> {kickoff, home,
    away, hg, ag, event, fdr_h, fdr_a})."""
    with open(os.path.join(hist_dir, "teams.csv"), encoding="utf-8", newline="") as fh:
        teams = list(csv.DictReader(fh))
    short_by_id = {t["id"]: t["short_name"] for t in teams}
    name_to_short = {t["name"]: t["short_name"] for t in teams}
    fixtures = {}
    with open(os.path.join(hist_dir, "fixtures.csv"), encoding="utf-8", newline="") as fh:
        for f in csv.DictReader(fh):
            if not f.get("kickoff_time") or not f.get("event"):
                continue
            ko = datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
            fixtures[f["id"]] = {"kickoff": ko, "home": short_by_id[f["team_h"]], "away": short_by_id[f["team_a"]],
                                 "hg": H._num(f["team_h_score"], None) if f.get("team_h_score") not in (None, "") else None,
                                 "ag": H._num(f["team_a_score"], None) if f.get("team_a_score") not in (None, "") else None,
                                 "event": int(f["event"]),
                                 "fdr_h": H._num(f.get("team_h_difficulty"), None), "fdr_a": H._num(f.get("team_a_difficulty"), None)}
    return short_by_id, name_to_short, fixtures


class Season2526:
    def __init__(self, hist_dir, odds_file=None, method="power"):
        self.hist = BT.load_2526(hist_dir)
        self.short_by_id, self.name_to_short, self.fixtures = vaastav_tables(hist_dir)
        self.book = OddsBook(load_odds(odds_file or odds_path("2025-26"), self.name_to_short))
        self.method = method
        self.first_kick = {}
        for f in self.fixtures.values():
            ev = f["event"]
            if ev not in self.first_kick or f["kickoff"] < self.first_kick[ev]:
                self.first_kick[ev] = f["kickoff"]
        self._lam = {}

    def deadline(self, g):
        """2025/26 has no recorded deadlines: results of rounds < g are the
        training set, so the fallback's cut is the round's first kickoff."""
        return self.first_kick[g]

    def lambdas(self, g):
        """{fixture id: (lambdas, source)} for round g."""
        if g in self._lam:
            return self._lam[g]
        results = [(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in self.fixtures.values()
                   if f["event"] < g]
        model = fit_fallback(results, self.deadline(g))
        out = {}
        for fid, f in self.fixtures.items():
            if f["event"] == g:
                out[fid] = fixture_lambdas(self.book, model, f["kickoff"], f["home"], f["away"], self.method)
        self._lam[g] = out
        return out

    def lam_opp(self, fid, team):
        lam, src = self.lambdas(self.fixtures[fid]["event"])[fid]
        f = self.fixtures[fid]
        return (lam["lambda_away"] if team == f["home"] else lam["lambda_home"]), src

    def week(self, g):
        """Per-fixture rows for round g: GK/DEF with 60+ minutes: (pid, pos,
        p_model, p_lambda, outcome, source, lam_opp, fdr); plus the full
        forecasts of both sources for every gated player (for Spearman) and
        p_start."""
        c = BT.canonical_at(self.hist, g)
        inp = E.reliability_inputs(E.canonical_through(c, g - 1), gws_played=g - 1)
        rows, fc_model, fc_lambda, p_start, pos_of = [], {}, {}, {}, {}
        per_player = defaultdict(list)
        for r in self.hist["raw"].get(g, []):
            per_player[int(r["element"])].append(r)
        actual = {r["player_id"]: float(r["pts"] or 0) for r in self.hist["c"]["rows"] if r["event"] == g}
        for pid, p in inp["players"].items():
            raw = per_player.get(pid, [])
            if p["mins_last4"] < 45 or not raw:              # the recording gate
                continue
            fx = []
            for r in raw:
                fid = str(r["fixture"])
                if fid not in self.fixtures:
                    raise MissingInput(f"round {g}: fixture {fid} of element {pid} is not in fixtures.csv")
                f = self.fixtures[fid]
                home = p["team"] == f["home"]
                opp = f["away"] if home else f["home"]
                lam, src = self.lam_opp(fid, p["team"])
                fx.append((opp, home, lam))
                if p["pos"] in (1, 2) and H._num(r["minutes"]) >= 60:
                    rows.append({"pid": pid, "pos": p["pos"], "p_model": BT._p_cs(inp, p, opp),
                                 "p_lambda": p_clean_sheet(lam), "outcome": 1 if H._num(r.get("clean_sheets")) >= 1 else 0,
                                 "source": src, "lam_opp": lam, "fdr": f["fdr_a"] if home else f["fdr_h"],
                                 "pts": float(H._num(r.get("total_points"))), "fid": fid})
            pairs = [(o, h) for o, h, _ in fx]
            fc_model[pid] = E.project_reliability(pid, inp, pairs, E.ALL_TERMS)
            fc_lambda[pid] = forecast_lambda(pid, inp, fx)
            p_start[pid] = p["p_start"]
            pos_of[pid] = p["pos"]
        return {"rows": rows, "model": fc_model, "lambda": fc_lambda, "p_start": p_start, "pos": pos_of,
                "actual": actual}


def brier_of(rows, key):
    return BT.brier([r[key] for r in rows], [r["outcome"] for r in rows]) if rows else None


def logloss_of(rows, key):
    return BT.log_loss([r[key] for r in rows], [r["outcome"] for r in rows]) if rows else None


def primary_test(hist_dir, out=print, first=5, last=None, odds_file=None, seed=SEED):
    s = Season2526(hist_dir, odds_file)
    s_prop = Season2526(hist_dir, odds_file, method="proportional")
    last = last or s.hist["through"]
    weeks = list(range(first, last + 1))
    per = []
    out(f"S5 PRIMARY TEST  2025/26 GW{first}-{last}: Brier of P(clean sheet), GK/DEF with 60+ minutes in the fixture; "
        f"bottomup (team-rate Poisson) vs bottomup_lambda (odds, power de-margin); paired bootstrap over gameweeks "
        f"(B={BT.B}, 90%, seed {seed})")
    out(f"  {'GW':>4} {'n':>5} {'Brier model':>12} {'Brier lambda':>13} {'diff':>8} {'odds':>5} {'fallback':>9} {'Friday':>7}")
    rows_all = []
    for g in weeks:
        w = s.week(g)
        rows = w["rows"]
        if not rows:
            raise MissingInput(f"GW{g}: no GK/DEF with 60+ minutes")
        bm, bl = brier_of(rows, "p_model"), brier_of(rows, "p_lambda")
        n_odds = sum(1 for r in rows if r["source"] == "odds")
        friday = s.first_kick[g].weekday() == 4
        wp = s_prop.week(g)
        bp = brier_of(wp["rows"], "p_lambda")
        per.append({"gw": g, "n": len(rows), "model": bm, "lambda": bl, "diff": bm - bl, "friday": friday,
                    "odds": n_odds, "fallback": len(rows) - n_odds,
                    "ll_model": logloss_of(rows, "p_model"), "ll_lambda": logloss_of(rows, "p_lambda"),
                    "prop": bp, "week": w})
        rows_all.extend(dict(r, gw=g) for r in rows)
        out(f"  {g:>4} {len(rows):>5} {bm:12.4f} {bl:13.4f} {bm - bl:+8.4f} {n_odds:>5} {len(rows) - n_odds:>9} {'yes' if friday else '':>7}")
    diffs = [p["diff"] for p in per]
    b = BT.bootstrap_mean(diffs, seed=seed)
    ok = b["mean"] >= PASS_BRIER and b["lo"] > 0
    out(f"  mean Brier improvement (model - lambda): {b['mean']:+.4f}, 90% CI [{b['lo']:+.4f}, {b['hi']:+.4f}], n={b['n']}")
    out(f"  pre-registered bar (a): improvement >= {PASS_BRIER} and CI lower bound > 0: {'PASS' if ok else 'FAIL'}")
    # amendment 1 point 2: with and without Friday-kickoff gameweeks (information only)
    nf = [p["diff"] for p in per if not p["friday"]]
    bf = BT.bootstrap_mean(nf, seed=seed) if nf else None
    out(f"  sensitivity (information only): without the {sum(1 for p in per if p['friday'])} gameweeks whose first kickoff is a Friday: "
        + (f"{bf['mean']:+.4f} [{bf['lo']:+.4f}, {bf['hi']:+.4f}], n={bf['n']}" if bf else "n/a"))
    # secondaries
    ll = BT.bootstrap_mean([p["ll_model"] - p["ll_lambda"] for p in per], seed=seed)
    out(f"  secondary: log-loss improvement {ll['mean']:+.4f} [{ll['lo']:+.4f}, {ll['hi']:+.4f}]; "
        f"proportional de-margin Brier mean {sum(p['prop'] for p in per) / len(per):.4f} vs power {sum(p['lambda'] for p in per) / len(per):.4f} "
        f"(model {sum(p['model'] for p in per) / len(per):.4f})")
    out(f"  fallback fired for {sum(p['fallback'] for p in per)} of {sum(p['n'] for p in per)} player-fixtures")
    # DEF spread by lambda_opp quintile and by FDR, starters (p_start >= 0.8), DEF only
    starters = [r for p in per for r in p["week"]["rows"] if r["pos"] == 2 and p["week"]["p_start"].get(r["pid"], 0) >= STARTER_P]
    spread = quintile_spread(starters, "lam_opp", reverse=False)
    spread_fdr = quintile_spread([r for r in starters if r["fdr"] is not None], "fdr", reverse=False)
    out(f"  secondary: DEF starters' realised points, easiest minus hardest quintile: by lambda_opp {spread[0]:+.2f} "
        f"(quintile means {', '.join(f'{v:.2f}' for v in spread[1])}, n={len(starters)}); by FDR {spread_fdr[0]:+.2f} "
        f"(FDR is the file's undated value)")
    # starters DEF/GK Spearman of both sources, per gameweek, and s_d for the 2026/27 condition's power
    rhos = []
    for p in per:
        w = p["week"]
        ids = [pid for pid in w["model"] if w["pos"][pid] in (1, 2) and w["p_start"][pid] >= STARTER_P
               and w["model"][pid] is not None and w["lambda"][pid] is not None]
        act = [w["actual"].get(pid, 0.0) for pid in ids]
        rhos.append((BT.spearman([w["model"][pid] for pid in ids], act), BT.spearman([w["lambda"][pid] for pid in ids], act), len(ids)))
    d_rho = [l - m for m, l, _ in rhos]
    br = BT.bootstrap_mean(d_rho, seed=seed)
    s_d = BT.sd(d_rho)
    out(f"  secondary: 2025/26 DEF/GK starters Spearman, mean model {sum(m for m, _, _ in rhos) / len(rhos):+.4f}, "
        f"lambda {sum(l for _, l, _ in rhos) / len(rhos):+.4f}, lambda - model {br['mean']:+.4f} [{br['lo']:+.4f}, {br['hi']:+.4f}], "
        f"s_d = {s_d:.4f} -> G at delta {POWER_DELTA}: {BT.power_gameweeks(s_d, POWER_DELTA):.1f} gameweeks")
    return {"per": per, "boot": b, "pass_a": ok, "s_d": s_d, "spread": spread, "rhos": rhos}


def quintile_spread(rows, key, reverse=False):
    """(easiest minus hardest quintile mean points, [quintile means]) with
    quintiles of `key` ascending (low lambda / low FDR = easiest)."""
    if len(rows) < 5:
        return 0.0, []
    srt = sorted(rows, key=lambda r: (r[key], r["pid"]), reverse=reverse)
    n = len(srt)
    means = []
    for q in range(5):
        chunk = srt[q * n // 5:(q + 1) * n // 5]
        means.append(sum(r["pts"] for r in chunk) / len(chunk) if chunk else 0.0)
    return means[0] - means[4], means


# ---------------------------------------------------------------------------
# 2026/27: the condition on starters-only DEF/GK Spearman
# ---------------------------------------------------------------------------

def dated_exports(data_dir):
    """[(generated datetime, path)] for every dated export."""
    out = []
    for f in glob.glob(os.path.join(data_dir, "exports", "fpl_export_gw*_*.json*")):
        op = gzip.open if f.endswith(".gz") else open
        with op(f, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        out.append((datetime.fromisoformat(d["generated"]), f, d))
    return sorted(out, key=lambda x: x[0])


def pre_deadline_export(exports, deadline, target):
    """The newest export generated before `deadline` whose next gameweek is
    `target` (export gameweek = target - 1); None if there is none."""
    best = None
    for gen, path, d in exports:
        if gen < deadline and d["gameweek"] == target - 1:
            best = (gen, path, d)
    return best


def sqlite_tables(data_dir):
    db = os.path.join(data_dir, "fpl.sqlite")
    if not os.path.exists(db):
        raise MissingInput(f"{db} is missing")
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    short = {i: s for i, s in c.execute("select id, short_name from teams")}
    name_to_short = {n: s for n, s in c.execute("select name, short_name from teams")}
    deadlines = {ev: datetime.fromisoformat(dl.replace("Z", "+00:00")) for ev, dl in c.execute("select id, deadline_time from events")}
    fixtures = []
    for ev, ko, h, a, hs, as_, fin in c.execute("select event, kickoff_time, team_h, team_a, team_h_score, team_a_score, finished from fixtures where event is not null"):
        fixtures.append({"event": ev, "kickoff": datetime.fromisoformat(ko.replace("Z", "+00:00")), "home": short[h], "away": short[a],
                         "hg": hs, "ag": as_, "finished": fin})
    settled = BT.load_2627(data_dir)["settled"]
    actual = defaultdict(dict)
    for pid, ev, pts in c.execute("select player_id, event, total_points from player_gw"):
        actual[ev][pid] = float(pts or 0)
    c.close()
    return name_to_short, deadlines, fixtures, settled, actual


def rebuild_2627(d, target, book, model, method="power"):
    """bottomup (as record_status builds it) and bottomup_lambda from one
    pre-deadline export, for the next gameweek `target`. Returns
    {pid: (bottomup, lambda, p_start, pos, source)}; a blank gives no row."""
    tick, _ = E.build_ticker(d, 6)
    inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=d["gameweek"])
    out = {}
    for p in d["all_players"]:
        if p["status"] != "a" or (p.get("mins_last4") or 0) < 45:
            continue
        fx = []
        for f in tick.get(p["team"], []):
            if f[0] != target:
                continue
            opp, home = f[1].split()[0], f[1].endswith("(H)")
            ko = kickoff_of(d, target, p["team"], opp, home)
            lam, src = fixture_lambdas(book, model, ko, p["team"] if home else opp, opp if home else p["team"], method)
            fx.append((opp, home, lam["lambda_away"] if home else lam["lambda_home"], src))
        if not fx:
            continue
        pairs = [(o, h) for o, h, _, _ in fx]
        proj = E.project_reliability(p["id"], inp, pairs)
        if not proj:
            continue
        lam_proj = forecast_lambda(p["id"], inp, [(o, h, l) for o, h, l, _ in fx])
        pp = inp["players"][p["id"]]
        out[p["id"]] = (proj, lam_proj, pp["p_start"], pp["pos"], ",".join(s for _, _, _, s in fx))
    return out


def kickoff_of(d, event, team, opp, home):
    for f in d.get("fixtures_next6") or []:
        if f["event"] == event and ((home and f["home"] == team and f["away"] == opp) or (not home and f["away"] == team and f["home"] == opp)):
            return datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
    raise MissingInput(f"GW{event}: no kickoff for {team} v {opp} in the export")


def condition_2627(data_dir, s_d, out=print, odds_file=None, seed=SEED):
    name_to_short, deadlines, fixtures, settled, actual = sqlite_tables(data_dir)
    book = OddsBook(load_odds(odds_file or odds_path("2026-27"), name_to_short))
    exports = dated_exports(data_dir)
    log_rows = E.read_log(os.path.join(data_dir, E.LOG_PATH))
    d_events = {"events": [{"event": ev, "deadline_time": dl.isoformat()} for ev, dl in deadlines.items()]}
    recorded = defaultdict(dict)
    for r in E.forecasts(log_rows, d_events):
        if r["source"] == "bottomup":
            recorded[int(r["event"])][int(r["player_id"])] = float(r["predicted"])
    out(f"S5 CONDITION  2026/27: starters-only (P(start) >= {STARTER_P}) DEF/GK Spearman, bottomup_lambda vs bottomup, "
        f"rebuilt from the newest export before each deadline; settled gameweeks only")
    out(f"  {'GW':>4} {'export':>28} {'n':>4} {'rho model':>10} {'rho lambda':>11} {'diff':>8} {'odds/fallback':>14} {'rebuilt = log':>14}")
    diffs, used = [], []
    for g in sorted(settled):
        dl = deadlines.get(g)
        ex = pre_deadline_export(exports, dl, g) if dl else None
        if ex is None:
            out(f"  {g:>4} {'no pre-deadline export':>28}")
            continue
        gen, path, d = ex
        results = [(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in fixtures if f["finished"] and f["kickoff"] < dl]
        model = fit_fallback(results, dl)
        try:
            reb = rebuild_2627(d, g, book, model)
        except ValueError as e:                       # the frozen adapter refuses an export without player_id
            out(f"  {g:>4} {os.path.basename(path):>28}  excluded: {e}")
            continue
        ids = [pid for pid, v in reb.items() if v[3] in (1, 2) and v[2] >= STARTER_P and pid in actual[g]]
        act = [actual[g][pid] for pid in ids]
        rm = BT.spearman([reb[pid][0] for pid in ids], act)
        rl = BT.spearman([reb[pid][1] for pid in ids], act)
        srcs = [reb[pid][4] for pid in reb]
        n_odds = sum(1 for s in srcs if s == "odds")
        rec = recorded.get(g)
        if rec:
            common = [pid for pid in reb if pid in rec]
            worst = max((abs(reb[pid][0] - rec[pid]) for pid in common), default=None)
            match = f"{len(common)} rows, max |diff| {worst:.3f}" if worst is not None else "no common rows"
        else:
            match = "not recorded"
        diffs.append(rl - rm)
        used.append(g)
        out(f"  {g:>4} {os.path.basename(path):>28} {len(ids):>4} {rm:+10.4f} {rl:+11.4f} {rl - rm:+8.4f} {n_odds:>6}/{len(srcs) - n_odds:<7} {match:>14}")
    if not diffs:
        raise MissingInput("no settled 2026/27 gameweek with a pre-deadline export")
    b = BT.bootstrap_mean(diffs, seed=seed)
    ok = b["hi"] >= 0
    g_needed = BT.power_gameweeks(s_d, POWER_DELTA) if s_d else float("nan")
    out(f"  mean per-gameweek difference lambda - model: {b['mean']:+.4f}, 90% CI [{b['lo']:+.4f}, {b['hi']:+.4f}], n={b['n']}"
        + ("   (fewer than 5 gameweeks: the interval is not meaningful)" if b["n"] < 5 else ""))
    out(f"  pre-registered condition (b): 'does not fall' = CI upper bound >= 0: {'PASS' if ok else 'FAIL'}; "
        f"power: s_d {s_d:.4f} on 2025/26 -> {g_needed:.1f} gameweeks needed to detect a fall of {POWER_DELTA} at 80% (have {b['n']})")
    return {"diffs": diffs, "boot": b, "pass_b": ok, "weeks": used, "g_needed": g_needed}


def fixture_report(data_dir, home, away, out=print, odds_file=None):
    name_to_short, deadlines, fixtures, settled, _ = sqlite_tables(data_dir)
    book = OddsBook(load_odds(odds_file or odds_path("2026-27"), name_to_short))
    f = next((f for f in fixtures if f["home"] == home and f["away"] == away), None)
    if f is None:
        raise MissingInput(f"no 2026/27 fixture {home} v {away}")
    dl = deadlines[f["event"]]
    results = [(x["kickoff"], x["home"], x["away"], x["hg"], x["ag"]) for x in fixtures if x["finished"] and x["kickoff"] < dl]
    lam, src = fixture_lambdas(book, fit_fallback(results, dl), f["kickoff"], home, away)
    out(f"{home} v {away} GW{f['event']} ({f['kickoff']:%Y-%m-%d}): source {src}; lambda home {lam['lambda_home']:.3f}, "
        f"away {lam['lambda_away']:.3f}; P(cs {home}) {p_clean_sheet(lam['lambda_away']):.3f}, P(cs {away}) {p_clean_sheet(lam['lambda_home']):.3f}")
    return lam, src


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--odds", default=None, help="an odds CSV (default: the newest tools/odds file for the season)")
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    ap.add_argument("--season", default="2025-26", choices=("2025-26", "2026-27"))
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--condition", action="store_true")
    ap.add_argument("--s_d", type=float, default=None, help="s_d for the condition's power (default: measured by --test)")
    ap.add_argument("--fixture", nargs=2, metavar=("HOME", "AWAY"))
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        if args.test:
            primary_test(args.hist, out, odds_file=args.odds)
            name = "odds_lambda_test_2025-26.txt"
        elif args.condition:
            s_d = args.s_d
            if s_d is None:
                buf = []
                s_d = primary_test(args.hist, buf.append)["s_d"]
                out(f"  (s_d {s_d:.4f} measured on 2025/26 by the primary test)")
            condition_2627(args.data, s_d, out, odds_file=args.odds)
            name = "odds_lambda_condition_2026-27.txt"
        elif args.fixture:
            fixture_report(args.data, args.fixture[0], args.fixture[1], out, odds_file=args.odds)
            name = f"odds_lambda_fixture_{args.fixture[0]}_{args.fixture[1]}.txt"
        else:
            ap.print_help()
            return 0
    except MissingInput as e:
        print(f"MISSING INPUT: {e} - stopping; nothing is substituted")
        return 2
    with open(os.path.join(args.out, name), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
