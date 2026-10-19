"""tools/points_pmf.py - S14, points distributions (prereg/S14.md; RULING
Step 14 and RULING 19 Oct afternoon point 1, option (a)). Offline; standard
library only; the nightly never imports it. Information only until it
passes and Boris accepts.

The PMF of a player-gameweek is the distribution of xp_v2 as tested itself
(its mean is xp_v2 by construction):

    P(start) x (1/2 X + 1/2 L) + P(sub) x U + (1 - P(start) - P(sub)) x 0

  X  the xg half given a start: 2 + sum over fixtures of GOAL_VALUE x
     Poisson(xG_f) + 3 x Poisson(xA_f) + CS_VALUE x Bernoulli(exp(-lambda_opp))
     + 2 x Bernoulli(DEFCON hit rate) + bonus, the bonus drawn from the
     empirical distribution of its returns cell, tilted to the half's bonus
     mean (0.8 x the ICT percentile);
  L  the bottomup half given a start: per fixture 2 + GOAL_VALUE x
     Poisson(0.62 xgi) + 3 x Poisson(0.38 xgi) + the clean sheet and goals
     conceded from one Poisson(lambda_opp) count (GK/DEF; MID its own
     team-rate clean sheet) + 2 x Bernoulli(logistic DEFCON);
  U  the empirical points of sub appearances per position.

Independence: within a half the components are independent of each other
and across fixtures; the bonus depends on the returns only; start, sub and
no appearance exclude each other. No saves term (xp_v2 has none; the GW10
item "xp_v2 + saves").

    python tools/points_pmf.py --test [--hist DIR] [--prior DIR] [--rules ROOT] [--odds FILE] [--out DIR]
    python tools/points_pmf.py --captain [--data DIR] [--hist ROOT] [--out DIR]
"""
import argparse
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

TAIL = OL.MAX_GOALS                 # Poisson counts cut at 15, as S5's expected_gc_penalty
EPS = 1e-13                         # a Poisson goal count stops when its tail is this small
BONUS_MIN_ROWS = 30                 # a returns cell with fewer rows backs off
HAUL, BIG = 10, 15
FIRST, LAST = 5, 38
SEED = BT.SEED
MEAN_BAR = 0.05                     # the ruling: the PMF mean within 0.05 of xp_v2
COUNT_BAR = 0.15                    # the ruling: predicted hauls within +/-15% of the actual count


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# PMF algebra: {points: probability}
# ---------------------------------------------------------------------------

def conv(a, b):
    out = defaultdict(float)
    for x, p in a.items():
        for y, q in b.items():
            out[x + y] += p * q
    return dict(out)


def mix(parts):
    """sum of w x pmf over [(w, pmf)]."""
    out = defaultdict(float)
    for w, pmf in parts:
        if w:
            for x, p in pmf.items():
                out[x] += w * p
    return dict(out)


def mean(pmf):
    return sum(x * p for x, p in pmf.items())


def p_at_least(pmf, k):
    return sum(p for x, p in pmf.items() if x >= k)


def quantile(pmf, q=0.9):
    """The smallest k with P(points <= k) >= q."""
    acc = 0.0
    for x in sorted(pmf):
        acc += pmf[x]
        if acc >= q - 1e-12:
            return x
    return max(pmf)


def poisson_counts(lam):
    """[(k, p)] for k = 0..K: Poisson(lam), stopped where the tail is below
    EPS or at TAIL; the residual sits on the last count."""
    out, acc = [], 0.0
    for k in range(TAIL + 1):
        p = OL.poisson_pmf(lam, k)
        out.append([k, p])
        acc += p
        if 1.0 - acc < EPS:
            break
    out[-1][1] += max(0.0, 1.0 - acc)
    return [(k, p) for k, p in out]


def scaled_poisson(lam, value):
    return {k * value: p for k, p in poisson_counts(lam)} if lam > 0 else {0: 1.0}


def bern(p, value):
    if p <= 0:
        return {0: 1.0}
    if p >= 1:
        return {value: 1.0}
    return {0: 1.0 - p, value: p}


def cs_and_gc(lam_opp, pos):
    """GK/DEF: one goals-conceded count GC ~ Poisson(lam_opp) gives the clean
    sheet and the penalty: CS_VALUE x 1{GC = 0} - floor(GC / 2), GC to 15 as
    S5's expected_gc_penalty sums it; the mass beyond 15 scores 0 here, so the
    mean is exactly lambda_terms' P(cs) x CS_VALUE - E[floor(GC / 2)]."""
    out, acc = defaultdict(float), 0.0
    for k in range(TAIL + 1):
        p = OL.poisson_pmf(lam_opp, k)
        acc += p
        out[(E.CS_VALUE[pos] if k == 0 else 0) - k // 2] += p
    out[0] += max(0.0, 1.0 - acc)
    return dict(out)


# ---------------------------------------------------------------------------
# the halves
# ---------------------------------------------------------------------------

def bottomup_terms(pid, inp, fixtures):
    """project_reliability's and forecast_lambda's terms per fixture, given a
    start: [{'xgi', 'k', 'p_dc'}] with k the clean-sheet input ('lam_opp' for
    GK/DEF, 'lam_own' for MID) and the per-start mean of each fixture."""
    p = inp["players"][pid]
    pos, w = p["pos"], inp["weights"]

    def shrunk(key, metric):
        prior = inp["priors"].get((pos, key), 0.0)
        obs = p[key]
        return prior if obs is None else obs * w[metric] + prior * (1 - w[metric])
    xgi, dc = shrunk("xgi90", "xgi"), shrunk("defcon90", "defcon")
    gc = inp["teams"].get(p["team"], {}).get("gc_per_match")
    gc = inp["league_gc"] if gc is None else gc
    p_dc = (1.0 / (1.0 + math.exp(-(dc - E.DEFCON_THRESHOLD[pos]) / 2.0))) if pos in E.DEFCON_THRESHOLD else 0.0
    out = []
    for opp, _home, lam_opp in fixtures:
        t = {"xgi": xgi, "p_dc": p_dc, "pos": pos}
        m = 2.0 + xgi * E.XGI_GOAL_SHARE * E.GOAL_VALUE.get(pos, 5) + xgi * (1 - E.XGI_GOAL_SHARE) * 3.0 + 2.0 * p_dc
        if pos in (1, 2):
            t["lam_opp"] = lam_opp
            m += OL.p_clean_sheet(lam_opp) * E.CS_VALUE[pos] - OL.expected_gc_penalty(lam_opp)
        elif E.CS_VALUE.get(pos, 0):
            oxg = inp["teams"].get(opp, {}).get("xg_per_match")
            oxg = inp["league_xg"] if oxg is None else oxg
            t["lam_own"] = gc * (oxg / inp["league_xg"]) if inp["league_xg"] else gc
            m += math.exp(-t["lam_own"]) * E.CS_VALUE[pos]
        t["mean"] = m
        out.append(t)
    return out


def bl_half(terms):
    """L, the bottomup half given a start: the fixtures summed."""
    pmf = {0: 1.0}
    for t in terms:
        pos = t["pos"]
        f = {2: 1.0}
        f = conv(f, scaled_poisson(t["xgi"] * E.XGI_GOAL_SHARE, E.GOAL_VALUE.get(pos, 5)))
        f = conv(f, scaled_poisson(t["xgi"] * (1 - E.XGI_GOAL_SHARE), 3))
        if "lam_opp" in t:
            f = conv(f, cs_and_gc(t["lam_opp"], pos))
        elif "lam_own" in t:
            f = conv(f, bern(math.exp(-t["lam_own"]), E.CS_VALUE[pos]))
        f = conv(f, bern(t["p_dc"], 2))
        pmf = conv(pmf, f)
    return pmf


def group_of(pos):
    return "def" if pos in (1, 2) else "att"


def cell_key(pos, gi, cs):
    return (group_of(pos), min(int(gi), 2), (1 if cs else 0) if pos in (1, 2) else 0)


def bonus_table(rows, min_rows=BONUS_MIN_ROWS):
    """rows: [(pos, goal involvements, clean sheet 0/1, bonus)] of starts.
    Returns cell -> {b: share}, every cell of the grid filled by the
    back-off: the cell, then the cell with the clean sheet pooled, then the
    involvements over both groups, then all rows."""
    counts = defaultdict(lambda: defaultdict(int))
    for pos, gi, cs, b in rows:
        if pos not in (1, 2, 3, 4):
            continue
        g, i, c = cell_key(pos, gi, cs)
        b = max(0, min(3, int(b)))
        for key in ((g, i, c), (g, i, "*"), ("*", i, "*"), ("*", "*", "*")):
            counts[key][b] += 1
    table = {}
    for g in ("def", "att"):
        for i in (0, 1, 2):
            for c in ((0, 1) if g == "def" else (0,)):
                for key in ((g, i, c), (g, i, "*"), ("*", i, "*"), ("*", "*", "*")):
                    n = sum(counts[key].values())
                    if n >= min_rows or key == ("*", "*", "*"):
                        table[(g, i, c)] = {b: counts[key][b] / n for b in range(4)} if n else {0: 1.0}
                        break
    return table


def tilt(dist, theta):
    w = {b: p * math.exp(theta * b) for b, p in dist.items() if p > 0}
    z = sum(w.values())
    return {b: v / z for b, v in w.items()}


def solve_theta(cells, target, lo=-60.0, hi=60.0, iters=200):
    """cells: [(weight, dist)]; theta with sum weight x mean(tilt(dist,
    theta)) = target, by bisection (the mean rises with theta); None when the
    target is out of reach."""
    def m(th):
        return sum(w * sum(b * p for b, p in tilt(d, th).items()) for w, d in cells)
    if target <= m(lo) + 1e-15 or target >= m(hi) - 1e-15:
        return None
    for _ in range(iters):
        mid = (lo + hi) / 2
        if m(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def xg_half(pos, fixtures, h, bonus_target, table):
    """X, the xg half given a start, and how the bonus was set ('tilted',
    'none' for a zero target, 'flat' for the unreachable fallback)."""
    state = {(0, 0, 0): 1.0}                   # (points from goals, assists and clean sheets, involvements capped at 2, clean sheet)
    for f in fixtures:
        g = poisson_counts(f["xg"]) if f["xg"] > 0 else [(0, 1.0)]
        a = poisson_counts(f["xa"]) if f["xa"] > 0 else [(0, 1.0)]
        pcs = OL.p_clean_sheet(f["lam_opp"]) if E.CS_VALUE.get(pos, 0) else 0.0
        cs = [(0, 1.0 - pcs), (1, pcs)] if pcs > 0 else [(0, 1.0)]
        new = defaultdict(float)
        for (pts, gi, c), p in state.items():
            for kg, pg in g:
                for ka, pa in a:
                    for kc, pc in cs:
                        key = (pts + kg * E.GOAL_VALUE.get(pos, 5) + ka * 3 + kc * E.CS_VALUE.get(pos, 0),
                               min(2, gi + kg + ka), max(c, kc))
                        new[key] += p * pg * pa * pc
        state = dict(new)
    cells = defaultdict(float)
    for (pts, gi, c), p in state.items():
        cells[cell_key(pos, gi, c)] += p
    how = "none"
    if bonus_target > 0:
        theta = solve_theta([(w, table[k]) for k, w in cells.items()], bonus_target)
        how = "tilted" if theta is not None else "flat"
    out = defaultdict(float)
    for (pts, gi, c), p in state.items():
        if how == "tilted":
            bd = tilt(table[cell_key(pos, gi, c)], theta)
        elif how == "flat":
            bd = bern(bonus_target, 1)
        else:
            bd = {0: 1.0}
        for b, q in bd.items():
            out[pts + b] += p * q
    pmf = conv(conv(dict(out), {2: 1.0}), bern(h, 2))
    return pmf, how


def sub_pmfs(rows, pos_of):
    """position -> the empirical PMF of official points of sub appearances
    (minutes > 0, no start); rows: raw rows of the training rounds."""
    pts = defaultdict(list)
    for r in rows:
        if H._num(r.get("minutes")) > 0 and not H._num(r.get("starts")):
            pts[pos_of.get(int(r["element"]))].append(int(round(H._num(r.get("total_points")))))
    out = {}
    for pos in (1, 2, 3, 4):
        v = pts.get(pos, [])
        out[pos] = {x: v.count(x) / len(v) for x in set(v)} if v else {0: 1.0}
    return out


def player_pmf(x, terms, pos, sub_pmf, table):
    """The player-gameweek PMF from core's detail x, bottomup_terms and the
    sub PMF; returns (pmf, notes)."""
    ps, psub = x["p_start"], x["p_sub"]
    notes = {}
    start = None
    if ps > 0:
        X, notes["bonus"] = xg_half(pos, x["fixtures"], x["defcon"] / 2.0, XR.BONUS_TOP * x["ict"], table)
        L = bl_half(terms)
        start = mix([(0.5, X), (0.5, L)])
    if ps + psub <= 1.0 + 1e-12:
        parts = [(psub, sub_pmf)]
        if start is not None:
            parts.append((ps, start))
        parts.append((max(0.0, 1.0 - ps - psub), {0: 1.0}))
        return mix(parts), notes
    notes["independent"] = True                 # P(start) + P(sub) > 1: the two parts added as independent events
    a = mix([(ps, start), (1.0 - ps, {0: 1.0})]) if start is not None else {0: 1.0}
    return conv(a, mix([(psub, sub_pmf), (1.0 - psub, {0: 1.0})])), notes


def summary(pmf):
    return {"mean": mean(pmf), "p10": p_at_least(pmf, HAUL), "p15": p_at_least(pmf, BIG), "p90": quantile(pmf, 0.9)}


# ---------------------------------------------------------------------------
# 2025/26: the pre-registered test
# ---------------------------------------------------------------------------

class Season:
    """S6b's replay with xp_v2's core kept open: per origin t the PMFs of
    every forecast player-gameweek."""

    def __init__(self, hist_dir, prior_dir, odds_file=None):
        self.rp = XR.Replay(hist_dir, prior_dir, odds_file)
        self.hist = self.rp.hist
        self.by_round = self.rp.by_round

    def inputs(self, t):
        c = BT.canonical_at(self.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        return c, inp

    def pmfs(self, t):
        """{pid: (pmf, xp_v2, notes)} at origin t from rounds < t."""
        rp = self.rp
        c, inp = self.inputs(t)
        names = {pid: c["players"][pid]["name"] for pid in inp["players"]}
        xp, detail = XL.core(inp, names, rp.by_round, t, rp.s11.rows, rp.s11.n2s, rp.s11.tot, rp.s11.prior,
                             lambda team: rp.s11.club_fixtures(team, t), lambda fid, team: rp.s11.lambda_team(fid, team)[0],
                             lambda fid, team: rp.s5.lam_opp(fid, team)[0])
        pos_of = {pid: p["pos"] for pid, p in inp["players"].items()}
        train = [r for rnd in range(1, t) for r in self.by_round.get(rnd, [])]
        subs = sub_pmfs(train, pos_of)
        table = bonus_table([(pos_of.get(int(r["element"])) or H.POS.get(r.get("position"), 0),
                              H._num(r.get("goals_scored")) + H._num(r.get("assists")), H._num(r.get("clean_sheets")) > 0,
                              H._num(r.get("bonus"))) for r in train if H._num(r.get("starts")) >= 1])
        out = {}
        for pid, x in detail.items():
            pos = inp["players"][pid]["pos"]
            terms = bottomup_terms(pid, inp, [(f["opp"], f["home"], f["lam_opp"]) for f in x["fixtures"]])
            pmf, notes = player_pmf(x, terms, pos, subs[pos], table)
            out[pid] = (pmf, xp[pid], notes)
        return out, pos_of


def gate_rounds(season, rescored, last):
    """{round r: {pos: (hauls 10+, hauls 15+, n)}} over the forecast gate at r
    (45+ minutes in the previous four rounds, a fixture), outcomes the
    re-scored points of r."""
    out = {}
    for r in range(2, last + 1):
        c, inp = season.inputs(r)
        acc = defaultdict(lambda: [0, 0, 0])
        for pid, p in inp["players"].items():
            if p["mins_last4"] < XR.GATE_MINS or not season.rp.s11.club_fixtures(p["team"], r):
                continue
            pts = rescored.get((pid, r), (0.0, 0.0))[0]
            a = acc[p["pos"]]
            a[0] += pts >= HAUL; a[1] += pts >= BIG; a[2] += 1
        out[r] = dict(acc)
    return out


def baseline(gates, t, pos, idx):
    """The haul rate of `pos` over rounds 2..t-1 (idx 0: 10+, 1: 15+)."""
    h = n = 0
    for r in range(2, t):
        a = gates.get(r, {}).get(pos)
        if a:
            h += a[idx]; n += a[2]
    return h / n if n else 0.0


def test_2526(hist_dir, prior_dir, out=print, odds_file=None, first=FIRST, last=LAST, seed=SEED, rescored=None):
    if rescored is None:
        raise MissingInput("the re-scored season is required (xp_v2_replay.rescore)")
    s = Season(hist_dir, prior_dir, odds_file)
    last = min(last, s.hist["through"])
    gates = gate_rounds(s, rescored, last)
    out(f"S14 TEST  2025/26 GW{first}-{last} re-scored under the 2026/27 rules (Step 10): the PMF of xp_v2 as tested (S6b), "
        f"P(>= {HAUL}) against the per-position haul rate (rounds 2..t-1, the same gate); Brier per gameweek, bootstrap B={BT.B}, 90%, "
        f"seed {seed}; no saves term (the GW10 item)")
    out(f"  {'GW':>4} {'n':>5} {'hauls':>6} {'E pmf':>7} {'E base':>7} {'Brier base':>11} {'Brier pmf':>10} {'diff':>8} "
        f"{'15+':>4} {'E15 pmf':>8} {'max|mean-xp|':>13}")
    per, pairs, worst, n_indep, bonus_how = [], [], 0.0, 0, defaultdict(int)
    for t in range(first, last + 1):
        pm, pos_of = s.pmfs(t)
        bb = bp = b15b = b15p = 0.0
        hauls = big = 0
        e_pmf = e_base = e15 = 0.0
        for pid, (pmf, xp, notes) in pm.items():
            pos = pos_of[pid]
            y = rescored.get((pid, t), (0.0, 0.0))[0]
            y10, y15 = float(y >= HAUL), float(y >= BIG)
            p10, p15 = p_at_least(pmf, HAUL), p_at_least(pmf, BIG)
            q10, q15 = baseline(gates, t, pos, 0), baseline(gates, t, pos, 1)
            bb += (q10 - y10) ** 2; bp += (p10 - y10) ** 2
            b15b += (q15 - y15) ** 2; b15p += (p15 - y15) ** 2
            hauls += y10; big += y15; e_pmf += p10; e_base += q10; e15 += p15
            worst = max(worst, abs(mean(pmf) - xp))
            n_indep += bool(notes.get("independent")); bonus_how[notes.get("bonus", "no start")] += 1
            pairs.append((p10, y10))
        n = len(pm)
        rec = {"gw": t, "n": n, "hauls": hauls, "big": big, "e_pmf": e_pmf, "e_base": e_base, "e15": e15,
               "brier_base": bb / n, "brier_pmf": bp / n, "diff": (bb - bp) / n, "diff15": (b15b - b15p) / n}
        per.append(rec)
        out(f"  {t:>4} {n:>5} {hauls:>6.0f} {e_pmf:7.1f} {e_base:7.1f} {rec['brier_base']:11.5f} {rec['brier_pmf']:10.5f} "
            f"{rec['diff']:+8.5f} {big:>4.0f} {e15:8.1f} {worst:13.2e}")
    boot = BT.bootstrap_mean([r["diff"] for r in per], seed=seed)
    boot15 = BT.bootstrap_mean([r["diff15"] for r in per], seed=seed)
    actual = sum(r["hauls"] for r in per)
    pred = sum(r["e_pmf"] for r in per)
    count_ok = actual > 0 and abs(pred - actual) <= COUNT_BAR * actual
    ok = boot["lo"] > 0 and count_ok
    out(f"  primary: mean per-gameweek Brier(baseline) - Brier(PMF), P(>= {HAUL}): {boot['mean']:+.5f}, 90% CI "
        f"[{boot['lo']:+.5f}, {boot['hi']:+.5f}] (n={boot['n']} gameweeks, p={boot['p']:.4f})")
    out(f"  count: predicted 10+ hauls {pred:.1f} against {actual:.0f} actual ({(pred - actual) / actual * 100 if actual else float('nan'):+.1f}%; "
        f"bar +/-{COUNT_BAR * 100:.0f}%): {'within' if count_ok else 'OUTSIDE'}; the baseline predicts {sum(r['e_base'] for r in per):.1f}")
    out(f"  secondary (information only): P(>= {BIG}) Brier(baseline) - Brier(PMF) {boot15['mean']:+.5f} [{boot15['lo']:+.5f}, "
        f"{boot15['hi']:+.5f}]; 15+ predicted {sum(r['e15'] for r in per):.1f} against {sum(r['big'] for r in per):.0f}")
    out(f"  mean check: max |E[PMF] - xp_v2| = {worst:.2e} over every player-gameweek (bar {MEAN_BAR}): "
        f"{'within' if worst <= MEAN_BAR else 'OUTSIDE'}; P(start) + P(sub) > 1 (independent parts): {n_indep}; "
        f"bonus: " + ", ".join(f"{k} {v}" for k, v in sorted(bonus_how.items())))
    deciles = calibration(pairs)
    out("  reliability of P(>= 10) by decile (information): " + "; ".join(f"{a:.3f}->{b:.3f} (n={n})" for a, b, n in deciles))
    out(f"  pre-registered bar (both): 90% lower bound > 0 and the count within +/-15%: {'PASS' if ok else 'FAIL'}"
        + (" (information only until Boris accepts)" if ok else ""))
    return {"per": per, "boot": boot, "boot15": boot15, "pred": pred, "actual": actual, "count_ok": count_ok, "pass": ok,
            "worst": worst, "independent": n_indep, "bonus": dict(bonus_how), "deciles": deciles}


def calibration(pairs, bins=10):
    """[(mean predicted, observed rate, n)] by decile of the prediction."""
    ps = sorted(pairs)
    n = len(ps)
    out = []
    for i in range(bins):
        chunk = ps[i * n // bins:(i + 1) * n // bins]
        if chunk:
            out.append((sum(p for p, _ in chunk) / len(chunk), sum(y for _, y in chunk) / len(chunk), len(chunk)))
    return out


# ---------------------------------------------------------------------------
# live: the captain table
# ---------------------------------------------------------------------------

def live_pmfs(res):
    """{pid: summary} for the live forecast (xp_v2_live.live's result)."""
    d = res["d"]
    c = E.canonical_through(E.canonical_from_export(d), d["gameweek"])
    inp = E.reliability_inputs(c, gws_played=d["gameweek"])
    by_round, rows = XL.export_rows(d)
    pos_of = {pid: p["pos"] for pid, p in inp["players"].items()}
    subs = sub_pmfs(rows, pos_of)
    table = bonus_table([(pos_of.get(int(r["player_id"])), (r.get("g_") or 0) + (r.get("a_") or 0), (r.get("cs") or 0) > 0,
                          r.get("bonus") or 0) for r in d.get("player_gw_recent") or []
                         if (r.get("starts") or 0) >= 1 and int(r["event"]) <= d["gameweek"]])
    out = {}
    for pid, x in res["detail"].items():
        pos = inp["players"][pid]["pos"]
        terms = bottomup_terms(pid, inp, [(f["opp"], f["home"], f["lam_opp"]) for f in x["fixtures"]])
        pmf, notes = player_pmf(x, terms, pos, subs[pos], table)
        out[pid] = dict(summary(pmf), xp=res["xp"][pid])
    return out


def captain_table(squad, sums, out=print):
    """Our 15 sorted by mean: mean, P(>=10), P(>=15), p90; a player without
    an xp_v2 forecast is listed as such."""
    out(f"  {'player':<16}{'pos':>4} {'mean':>6} {'P>=10':>7} {'P>=15':>7} {'p90':>4}")
    rows = sorted(squad, key=lambda r: -(sums[r["id"]]["mean"] if r["id"] in sums else -1))
    for r in rows:
        s = sums.get(r["id"])
        if s is None:
            out(f"  {r['name']:<16}{BT.POS_NAME.get(r['pos'], '?'):>4}  no xp_v2 forecast")
            continue
        out(f"  {r['name']:<16}{BT.POS_NAME.get(r['pos'], '?'):>4} {s['mean']:6.2f} {s['p10']:7.3f} {s['p15']:7.3f} {s['p90']:>4}")
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hist", default=None, help="--test: historical/2025-26; --captain: the root holding 2025-26/ and 2026-27/")
    ap.add_argument("--prior", default=os.path.join(ROOT, "historical", "2024-25"))
    ap.add_argument("--rules", default=os.path.join(ROOT, "historical"))
    ap.add_argument("--odds", default=None)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "points_pmf"))
    ap.add_argument("--first", type=int, default=FIRST)
    ap.add_argument("--last", type=int, default=LAST)
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--captain", action="store_true")
    a = ap.parse_args(argv)
    if not (a.test or a.captain):
        ap.print_help()
        return 2
    os.makedirs(a.out, exist_ok=True)
    run = Run("tools/points_pmf.py", a.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    missing = (MissingInput, XR.MissingInput, OL.MissingInput, BT.MissingInput, SH.MissingInput, CH.MissingInput)
    try:
        if a.test:
            rescored_csv = os.path.join(a.out, "rescored_2025-26.csv")
            rescored = XR.rescore(a.rules, rescored_csv, say=out)
            test_2526(a.hist or os.path.join(ROOT, "historical", "2025-26"), a.prior, out, odds_file=a.odds, first=a.first,
                      last=a.last, rescored=rescored)
            name = "points_pmf_2025-26.txt"
            run.wrote(rescored_csv)
        else:
            res = XL.live(a.data, a.hist or os.path.join(ROOT, "historical"))
            out(f"CAPTAIN TABLE  GW{res['target']} (S14, information only): the PMF of xp_v2 as tested for our 15")
            captain_table(CH.my_squad(res["d"]), live_pmfs(res), out)
            name = f"captain_gw{res['target']}.txt"
    except missing as e:
        print(f"missing input: {e}")
        return 2
    path = os.path.join(a.out, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run.wrote(path)
    print(f"written: {path}; provenance: {run.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
