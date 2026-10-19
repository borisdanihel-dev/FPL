"""tools/shares.py - S11 (BUILD_PLAN.md Step 11, item H2): share-of-team
allocation with 2024/25 priors, offline. Standard library only; the nightly
never imports it.

Player xG(t) = sum over his club's round-t fixtures of lambda_team (S5's
odds-implied lambda, the fallback labelled) x shrunk share x expected
minutes share; xA the same with the xA shares. Share s = own xG / team xG
over the fixtures the player appeared in (training rounds < t); prior s0 =
his 2024/25 share at the same club, else the 2024/25 mean share of his
position at his club, else the league-wide position mean; shrunk share =
Z s + (1 - Z) s0 with Z = m / (m + k), m = minutes / 90 this season and
k = n (1 - r) / r from split-half reliability of the share on 2024/25.
Expected minutes share = P(start) x mean minutes per start / 90. Goals
forecast = xG, assists forecast = xA (finishing shrunk to 0). Comparator =
the same with Z = 1 (the current-season share alone). Manager changes: not
modelled (no dated source in the repo).

The pre-registered test (prereg/S11.md): 2025/26 GW5-38 point-in-time
(canonical_at, rounds < t, clubs of the origin), predicted starters
(P(start) >= 0.8) with a fixture; per-gameweek tie-corrected Spearman of
forecast against realised goals, and against realised assists, each v2 -
comparator; bootstrap over gameweeks (B = 10000, seed 20261018); Holm
across the two at 90% (the smaller p at 95%, then the other at 90%); each
metric adopted separately only if its Holm-adjusted lower bound > 0.

    python tools/shares.py --test [--hist DIR] [--prior DIR] [--odds FILE] [--out DIR]
"""
import argparse
import csv
import math
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import odds_lambda as OL                                          # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402

STARTER_P = BT.STARTER_P                  # predicted starters: P(start) >= 0.8
HALF_MINUTES = 45                         # split-half population: 45+ minutes in each half
PRIOR_MINS = 180                          # the club-position mean prior: players with 180+ minutes there
HOLM_ALPHA = 0.10
METRICS = (("goals", "xg", "expected_goals", "goals_scored"), ("assists", "xa", "expected_assists", "assists"))
MANAGER_LINE = "manager changes: not modelled (no dated source in the repo)"
SEED = BT.SEED


class MissingInput(Exception):
    pass


# ---------------------------------------------------------------------------
# shares from raw rows
# ---------------------------------------------------------------------------

def read_raw(folder):
    """De-duplicated vaastav rows and the club-name -> short map."""
    with open(os.path.join(folder, "teams.csv"), encoding="utf-8", newline="") as fh:
        name_to_short = {t["name"]: t["short_name"] for t in csv.DictReader(fh)}
    with open(os.path.join(folder, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        rows, _ = H.dedup_rows(list(csv.DictReader(fh)))
    for r in rows:
        if "expected_goals" not in r or "expected_assists" not in r:
            raise MissingInput(f"{folder}: no expected_goals / expected_assists column")
    return rows, name_to_short


def team_totals(rows, name_to_short):
    """(fixture, club) -> {xg, xa} summed over the club's rows in that fixture."""
    tot = defaultdict(lambda: {"xg": 0.0, "xa": 0.0})
    for r in rows:
        club = name_to_short.get(r["team"], r["team"])
        t = tot[(str(r["fixture"]), club)]
        t["xg"] += H._num(r.get("expected_goals")); t["xa"] += H._num(r.get("expected_assists"))
    return tot


def player_sums(rows, name_to_short, rounds, tot, by="element"):
    """Per key (element id, or name): own and team xG/xA over the fixtures
    the player appeared in (minutes > 0) within `rounds`, his minutes,
    starts and minutes in starts, and his club per fixture count."""
    out = {}
    for r in rows:
        rnd = int(r["round"])
        if rnd not in rounds:
            continue
        mins = H._num(r.get("minutes"))
        if mins <= 0:
            continue
        key = int(r["element"]) if by == "element" else r["name"]
        club = name_to_short.get(r["team"], r["team"])
        a = out.setdefault(key, {"xg": 0.0, "xa": 0.0, "team_xg": 0.0, "team_xa": 0.0, "minutes": 0.0, "starts": 0,
                                 "start_minutes": 0.0, "clubs": defaultdict(float), "pos": H.POS.get(r.get("position"), 0)})
        t = tot[(str(r["fixture"]), club)]
        a["xg"] += H._num(r.get("expected_goals")); a["xa"] += H._num(r.get("expected_assists"))
        a["team_xg"] += t["xg"]; a["team_xa"] += t["xa"]
        a["minutes"] += mins
        if H._num(r.get("starts")) >= 1:
            a["starts"] += 1; a["start_minutes"] += mins
        a["clubs"][club] += mins
    return out


def share_of(a, metric):
    team = a["team_" + metric]
    return a[metric] / team if team > 0 else 0.0


# ---------------------------------------------------------------------------
# 2024/25: the priors and the credibility constants
# ---------------------------------------------------------------------------

class Prior:
    """2024/25 shares per (name, club), the club-position and league-position
    means (players with PRIOR_MINS+ minutes), and k per metric."""

    def __init__(self, folder):
        rows, n2s = read_raw(folder)
        rows = [r for r in rows if H.POS.get(r.get("position"), 0)]        # manager rows (AM) out
        if not rows:
            raise MissingInput(f"{folder}: no player rows")
        self.folder = folder
        tot = team_totals(rows, n2s)
        rounds = {int(r["round"]) for r in rows}
        per_name_club = {}
        for r in rows:
            if H._num(r.get("minutes")) <= 0:
                continue
            club = n2s.get(r["team"], r["team"])
            key = (r["name"], club)
            a = per_name_club.setdefault(key, {"xg": 0.0, "xa": 0.0, "team_xg": 0.0, "team_xa": 0.0, "minutes": 0.0,
                                               "pos": H.POS.get(r.get("position"), 0)})
            t = tot[(str(r["fixture"]), club)]
            a["xg"] += H._num(r.get("expected_goals")); a["xa"] += H._num(r.get("expected_assists"))
            a["team_xg"] += t["xg"]; a["team_xa"] += t["xa"]; a["minutes"] += H._num(r.get("minutes"))
        self.by_name_club = per_name_club
        self.club_pos = defaultdict(list)
        self.league_pos = defaultdict(list)
        for (name, club), a in per_name_club.items():
            if a["minutes"] >= PRIOR_MINS:
                pair = (share_of(a, "xg"), share_of(a, "xa"))
                self.club_pos[(club, a["pos"])].append(pair)
                self.league_pos[a["pos"]].append(pair)
        self.clubs = {club for _, club in per_name_club}
        self.k, self.rel = {}, {}
        for metric, key, _, _ in METRICS:
            self.k[key], self.rel[key] = credibility_k(rows, n2s, tot, rounds, key)

    def prior(self, name, pos, club, metric):
        """(prior share, source) for a 2025/26 player at `club`."""
        a = self.by_name_club.get((name, club))
        if a is not None and a["minutes"] > 0 and a["team_" + metric] > 0:
            return share_of(a, metric), "own 2024/25 at the club"
        i = 0 if metric == "xg" else 1
        vals = self.club_pos.get((club, pos))
        if vals:
            return sum(v[i] for v in vals) / len(vals), "club-position mean"
        vals = self.league_pos.get(pos)
        if not vals:
            raise MissingInput(f"no 2024/25 share for position {pos}")
        return sum(v[i] for v in vals) / len(vals), "league-position mean (club without 2024/25 rows)"


def credibility_k(rows, n2s, tot, rounds, metric):
    """k = n (1 - r) / r: r = tie-corrected Spearman of the share in odd
    against even rounds among players with HALF_MINUTES+ in each half, n =
    their mean minutes / 90 per half. Returns (k, {r, n, players, ci})."""
    odd = player_sums(rows, n2s, {g for g in rounds if g % 2 == 1}, tot)
    even = player_sums(rows, n2s, {g for g in rounds if g % 2 == 0}, tot)
    a, b, mins = [], [], []
    for pid in sorted(set(odd) & set(even)):
        if odd[pid]["minutes"] >= HALF_MINUTES and even[pid]["minutes"] >= HALF_MINUTES:
            a.append(share_of(odd[pid], metric)); b.append(share_of(even[pid], metric))
            mins.append((odd[pid]["minutes"] + even[pid]["minutes"]) / 2 / 90.0)
    if len(a) < 3:
        raise MissingInput(f"split-half {metric}: fewer than 3 players with {HALF_MINUTES}+ minutes in each half")
    r = E._spearman(a, b)
    if r <= 0:
        raise MissingInput(f"split-half {metric}: reliability {r:.3f} is not positive; k is undefined")
    n = sum(mins) / len(mins)
    return n * (1 - r) / r, {"r": r, "n": n, "players": len(a), "ci": 1.96 / (len(a) - 1) ** 0.5}


# ---------------------------------------------------------------------------
# 2025/26, point-in-time
# ---------------------------------------------------------------------------

class Season:
    def __init__(self, hist_dir, prior_dir, odds_file=None):
        self.s = OL.Season2526(hist_dir, odds_file)
        self.hist = self.s.hist
        self.fixtures = self.s.fixtures
        self.rows, self.n2s = read_raw(hist_dir)
        self.tot = team_totals(self.rows, self.n2s)
        self.prior = Prior(prior_dir)

    def club_fixtures(self, club, t):
        return [(fid, f) for fid, f in self.fixtures.items() if f["event"] == t and club in (f["home"], f["away"])]

    def lambda_team(self, fid, club):
        lam, src = self.s.lambdas(self.fixtures[fid]["event"])[fid]
        f = self.fixtures[fid]
        return (lam["lambda_home"] if club == f["home"] else lam["lambda_away"]), src

    def origin(self, t):
        """Round t from rounds < t: per predicted starter the v2 and comparator
        forecasts of xG and xA, Z, the prior source, and the realised goals
        and assists of round t."""
        if t < 2 or t > self.hist["through"]:
            raise MissingInput(f"GW{t} is outside the rebuildable range 2..{self.hist['through']}")
        c = BT.canonical_at(self.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        train = set(range(1, t))
        agg = player_sums(self.rows, self.n2s, train, self.tot)
        pos_start = defaultdict(list)
        for pid, a in agg.items():
            p = inp["players"].get(pid)
            if p is not None and a["starts"]:
                pos_start[p["pos"]].append(a["start_minutes"] / a["starts"])
        pos_mean_start = {pos: sum(v) / len(v) for pos, v in pos_start.items()}
        realised = defaultdict(lambda: {"goals": 0.0, "assists": 0.0})
        for r in self.hist["raw"].get(t, []):
            pid = int(r["element"])
            realised[pid]["goals"] += H._num(r.get("goals_scored")); realised[pid]["assists"] += H._num(r.get("assists"))
        rows = []
        for pid, p in inp["players"].items():
            if p["p_start"] < STARTER_P or not p["pos"]:
                continue
            fx = self.club_fixtures(p["team"], t)
            if not fx:
                continue
            a = agg.get(pid)
            m = (a["minutes"] / 90.0) if a else 0.0
            m_start = (a["start_minutes"] / a["starts"]) if a and a["starts"] else pos_mean_start.get(p["pos"], 90.0)
            ms = p["p_start"] * m_start / 90.0
            row = {"pid": pid, "pos": p["pos"], "team": p["team"], "m": m, "ms": ms,
                   "goals": realised[pid]["goals"], "assists": realised[pid]["assists"], "sources": set()}
            lams = []
            for fid, f in fx:
                lam, src = self.lambda_team(fid, p["team"])
                lams.append(lam); row["sources"].add(src)
            for metric, key, _, _ in METRICS:
                s = share_of(a, key) if a else 0.0
                s0, how = self.prior.prior(c["players"][pid]["name"], p["pos"], p["team"], key)
                z = m / (m + self.prior.k[key])
                shrunk = z * s + (1 - z) * s0
                row[key] = sum(lam * shrunk * ms for lam in lams)
                row[key + "_cmp"] = sum(lam * s * ms for lam in lams)
                row["z_" + key] = z; row["s_" + key] = s; row["s0_" + key] = s0; row["prior_" + key] = how
            rows.append(row)
        return {"gw": t, "rows": rows}


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------

def logloss_goal(rows, key):
    tot = 0.0
    for r in rows:
        p = min(1 - 1e-6, max(1e-6, 1 - math.exp(-r[key])))
        tot -= math.log(p) if r["goals"] >= 1 else math.log(1 - p)
    return tot / len(rows) if rows else None


def holm_intervals(diffs, seed=SEED, alpha=HOLM_ALPHA):
    """Holm step-down over the metric family: the metric with the smaller
    two-sided bootstrap p is tested at 1 - alpha/2, the next at 1 - alpha;
    stop at the first failure. {metric: {mean, lo, hi, level, p, tested,
    adopt}}, adopt = tested and lo > 0."""
    base = {m: BT.bootstrap_mean(v, seed=seed) for m, v in diffs.items()}
    order = sorted(base, key=lambda m: (base[m]["p"], m))
    out, stop = {}, False
    for i, m in enumerate(order):
        level = 1 - alpha / (len(order) - i)
        b = BT.bootstrap_mean(diffs[m], seed=seed, ci=level)
        ok = (not stop) and b["lo"] > 0
        out[m] = {"mean": b["mean"], "lo": b["lo"], "hi": b["hi"], "level": level, "p": base[m]["p"],
                  "tested": not stop, "adopt": ok, "lo90": base[m]["lo"], "hi90": base[m]["hi"]}
        if not ok:
            stop = True
    return out


def test_2526(hist_dir, prior_dir, out=print, first=5, last=None, odds_file=None, seed=SEED):
    season = Season(hist_dir, prior_dir, odds_file)
    last = last or season.hist["through"]
    pr = season.prior
    out(f"S11 TEST  2025/26 GW{first}-{last}: share-of-team allocation with 2024/25 priors (v2) against the current-season-only "
        f"share (comparator), predicted starters (P(start) >= {STARTER_P}), per-gameweek Spearman of forecast v realised goals and "
        f"assists; bootstrap over gameweeks B={BT.B}, seed {seed}; Holm across the two at {1 - HOLM_ALPHA:.0%}")
    for metric, key, _, _ in METRICS:
        rel = pr.rel[key]
        out(f"  credibility {metric} ({key} share, 2024/25 split-half odd v even, {rel['players']} players with {HALF_MINUTES}+ minutes in each half): "
            f"r = {rel['r']:.3f} +/- {rel['ci']:.3f}, n = {rel['n']:.2f} matches per half, k = {pr.k[key]:.2f}")
    out(f"  priors: 2024/25 from {os.path.basename(os.path.normpath(prior_dir))}; clubs without 2024/25 rows take the league-position mean")
    out(f"  {MANAGER_LINE}")
    out(f"  {'GW':>4} {'n':>4} {'rho_g v2':>9} {'rho_g cmp':>10} {'diff':>7} {'rho_a v2':>9} {'rho_a cmp':>10} {'diff':>7} {'LL v2':>6} {'LL cmp':>7} "
        f"{'Z xg':>5} {'own/club/league':>16} {'fallback':>9}")
    per = []
    for t in range(first, last + 1):
        o = season.origin(t)
        rows = o["rows"]
        if len(rows) < 3:
            raise MissingInput(f"GW{t}: fewer than 3 predicted starters with a fixture")
        rec = {"gw": t, "n": len(rows)}
        for metric, key, _, _ in METRICS:
            real = [r[metric] for r in rows]
            rec["rho_" + key] = E._spearman([r[key] for r in rows], real)
            rec["rho_" + key + "_cmp"] = E._spearman([r[key + "_cmp"] for r in rows], real)
        rec["ll"] = logloss_goal(rows, "xg"); rec["ll_cmp"] = logloss_goal(rows, "xg_cmp")
        rec["z"] = sum(r["z_xg"] for r in rows) / len(rows)
        srcs = [r["prior_xg"] for r in rows]
        rec["prior"] = (sum(1 for s in srcs if s.startswith("own")), sum(1 for s in srcs if s.startswith("club")), sum(1 for s in srcs if s.startswith("league")))
        rec["fallback"] = sum(1 for r in rows if "fallback" in r["sources"]) / len(rows)
        per.append(rec)
        out(f"  {t:>4} {rec['n']:>4} {rec['rho_xg']:9.3f} {rec['rho_xg_cmp']:10.3f} {rec['rho_xg'] - rec['rho_xg_cmp']:+7.3f} "
            f"{rec['rho_xa']:9.3f} {rec['rho_xa_cmp']:10.3f} {rec['rho_xa'] - rec['rho_xa_cmp']:+7.3f} {rec['ll']:6.3f} {rec['ll_cmp']:7.3f} "
            f"{rec['z']:5.2f} {rec['prior'][0]:>6}/{rec['prior'][1]}/{rec['prior'][2]} {rec['fallback']:9.2f}")
    diffs = {metric: [r["rho_" + key] - r["rho_" + key + "_cmp"] for r in per] for metric, key, _, _ in METRICS}
    holm = holm_intervals(diffs, seed=seed)
    ll = BT.bootstrap_mean([r["ll_cmp"] - r["ll"] for r in per], seed=seed)
    out(f"  secondary: log loss of P(goal) = 1 - exp(-xG), comparator - v2: {ll['mean']:+.4f} [{ll['lo']:+.4f}, {ll['hi']:+.4f}]")
    for metric in [m for m, *_ in METRICS]:
        h = holm[metric]
        out(f"  {metric}: Spearman v2 - comparator mean {h['mean']:+.4f}, 90% [{h['lo90']:+.4f}, {h['hi90']:+.4f}], p = {h['p']:.4f}; "
            f"Holm level {h['level']:.0%}: [{h['lo']:+.4f}, {h['hi']:+.4f}] -> "
            + ("ADOPTABLE (lower bound > 0)" if h["adopt"] else ("FAIL (lower bound <= 0)" if h["tested"] else "FAIL (Holm stopped at the earlier metric)")))
    out(f"  pre-registered result: goals {'PASS' if holm['goals']['adopt'] else 'FAIL'}, assists {'PASS' if holm['assists']['adopt'] else 'FAIL'} "
        f"(each adopted separately; adoption needs Boris)")
    return {"per": per, "holm": holm, "ll": ll, "k": dict(pr.k), "rel": dict(pr.rel)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--prior", default=os.path.join(ROOT, "historical", "2024-25"))
    ap.add_argument("--odds", default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    ap.add_argument("--first", type=int, default=5)
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    if not a.test:
        ap.print_help()
        return 2
    lines = []

    def out(s):
        print(s)
        lines.append(s)
    try:
        for name in ("merged_gw.csv", "fixtures.csv", "teams.csv"):
            for folder in (a.hist, a.prior):
                if not os.path.exists(os.path.join(folder, name)):
                    raise MissingInput(f"{os.path.join(folder, name)} is missing")
        test_2526(a.hist, a.prior, out, first=a.first, last=a.last, odds_file=a.odds)
    except (MissingInput, OL.MissingInput, BT.MissingInput) as e:
        print(f"missing input: {e}")
        return 2
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "shares_test_2025-26.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"written: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
