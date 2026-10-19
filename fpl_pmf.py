"""fpl_pmf.py - the runner's copy of tools/points_pmf.py, the part W3 needs:
Step 14's points distributions and the captain table (W3; prereg/W3.md, Part F item F-B).

Every definition below is copied verbatim from tools/points_pmf.py by its syntax
tree, module aliases kept and pointed at the runner's copies, so the
runner never imports tools/; tests/test_W3.py holds the copies to the
tools. Standard library only.
"""
import fpl_bt as BT
import fpl_edge as E
import fpl_hist as H
import fpl_lambda as OL
import fpl_xpr as XR
import fpl_xpv2 as XL
import math
from collections import defaultdict


TAIL = OL.MAX_GOALS                 # Poisson counts cut at 15, as S5's expected_gc_penalty


EPS = 1e-13                         # a Poisson goal count stops when its tail is this small


BONUS_MIN_ROWS = 30                 # a returns cell with fewer rows backs off


HAUL, BIG = 10, 15


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted."""


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


CAPTAIN_BAND = 0.3                  # RULING S14 acceptance point 1: options within 0.3 xP of the captain


def captain_options(xi, cap_id, xp, band=CAPTAIN_BAND):
    """The XI players other than the captain whose xp_v2 is at least the
    captain's minus `band` (inclusive), highest first (ties by the lower id).
    The captain stays the highest xp_v2 in the XI: no tie-break here."""
    top = xp[cap_id]
    return sorted((pid for pid in xi if pid != cap_id and pid in xp and xp[pid] >= top - band - 1e-12),
                  key=lambda pid: (-xp[pid], pid))


def print_options(cap, options, sums, names, out=print, band=CAPTAIN_BAND):
    """Section 7's lines beside the captain (amendment 1): the captain and
    each option with xp_v2, mean, P(>=10), P(>=15) and p90."""
    if not options:
        out(f"  captain {names[cap]} (xp_v2 {sums[cap]['xp']:.2f}): no option within {band} xP; the captain rule is unchanged "
            f"(highest xp_v2 in the XI)")
        return
    out(f"  within {band} xP of the captain (information; the captain rule is unchanged - highest xp_v2 in the XI - and there is "
        f"no tie-break):")
    for pid, tag in [(cap, "captain")] + [(o, "option") for o in options]:
        s = sums[pid]
        out(f"    {tag:<8}{names[pid]:<16} xp_v2 {s['xp']:5.2f}  mean {s['mean']:5.2f}  P>=10 {s['p10']:.3f}  P>=15 {s['p15']:.3f}  "
            f"p90 {s['p90']}")


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
