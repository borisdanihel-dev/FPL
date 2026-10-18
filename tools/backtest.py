"""
tools/backtest.py - the walk-forward backtest harness (BUILD_PLAN.md Step 4,
item S4, offline part). Standard library only; the nightly never imports it.

    python tools/backtest.py --compare own bottomup --season 2026-27 --filter starters
    python tools/backtest.py --compare bottomup minutes --season 2025-26 --filter all
    python tools/backtest.py --report                 # the Step 4 item 8 table
    python tools/backtest.py --power                  # s_d on 2025/26, G for 0.01/0.02/0.03
    python tools/backtest.py --selftest               # 400 replications, the two bars

Data (read-only): --data (the FPL-data worktree: the forecast log and fpl.sqlite)
and --hist (historical/2025-26, the vaastav CSVs). Everything written goes
under --out (tools/out by default, gitignored).

Point-in-time, as pre-registered in prereg/S4.md:
  2026/27  forecasts through fpl_edge.forecasts() - the whole last snapshot
           per (event, source) made before events.deadline_time; actuals from
           player_gw; a gameweek is graded only when settled (data_checked = 1
           and every fixture finished = 1).
  2025/26  only sources that can be rebuilt from rows with round < g:
           bottomup and minutes, through fpl_edge.backtest_week (the frozen
           rolling-origin rebuild) on players at their point-in-time club
           (tools/hist_pit.py, amendment 2). own, xg and fpl_ep are excluded,
           never approximated (ruling 2, amendment 1 point 3).
"""

import argparse
import csv
import math
import os
import random
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
import hist_pit as PIT                                            # noqa: E402

SEED = 20261018            # the bootstrap seed (prereg)
SELFTEST_SEED = 4          # the self-test seed (prereg)
B = 10000                  # resamples
CI = 0.90                  # interval
Z_ALPHA = 1.645            # alpha = 0.10 two-sided, the "90% CI lower bound > 0" rule
Z_BETA = 0.842             # beta = 0.20
DELTAS = (0.01, 0.02, 0.03)
STARTER_P = 0.8            # starters = forecast P(start) >= 0.8, never realised minutes
TOPK = (1, 3, 11)
CLIP = 1e-6
QUOTA = {1: 2, 2: 5, 3: 5, 4: 3}
CLUB_MAX = 3
BUDGET_TENTHS = 1000       # 100.0m for the 2025/26 most-selected squad
NODE_LIMIT = 3000
MY_ENTRY = 3073318         # Boris's entry (CLAUDE.md)
SOURCES_2627 = ("own", "xg", "bottomup", "minutes", "fpl_ep")
SOURCES_2526 = ("bottomup", "minutes")
NOT_REBUILDABLE = {
    "own": "project() needs the pre-deadline FDR, chance_next_round and status; 2025/26 has none",
    "xg": "project_xg() needs the pre-deadline FDR and chance_next_round; 2025/26 has none",
    "fpl_ep": "not recorded in 2025/26; merged_gw.csv's xP has no documented fetch time",
}
COMPONENTS = ("start", "cs", "goal", "defcon", "bonus")
POS_NAME = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# metrics - each on one gameweek's paired lists
# ---------------------------------------------------------------------------

def spearman(pred, act):
    return E._spearman(list(pred), list(act))


def kendall_tau_b(x, y):
    """Kendall's tau-b (ties corrected), O(n^2) - n is a few hundred."""
    n = len(x)
    if n < 2:
        return 0.0
    conc = disc = tx = ty = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = (x[i] > x[j]) - (x[i] < x[j])
            dy = (y[i] > y[j]) - (y[i] < y[j])
            if dx == 0 and dy == 0:
                continue
            if dx == 0:
                tx += 1
            elif dy == 0:
                ty += 1
            elif dx == dy:
                conc += 1
            else:
                disc += 1
    den = math.sqrt((conc + disc + tx) * (conc + disc + ty))
    return (conc - disc) / den if den else 0.0


def topk_regret(pids, pred, act, k):
    """(sum of realised points of the true top k) - (sum of realised points
    of the forecast's top k); forecast ties broken by ascending player id."""
    if len(pids) < k:
        return None
    true_top = sorted(act, reverse=True)[:k]
    order = sorted(range(len(pids)), key=lambda i: (-pred[i], pids[i]))
    return sum(true_top) - sum(act[i] for i in order[:k])


def mae(pred, act):
    return sum(abs(p - a) for p, a in zip(pred, act)) / len(pred) if pred else None


def brier(prob, outcome):
    return sum((p - o) ** 2 for p, o in zip(prob, outcome)) / len(prob) if prob else None


def log_loss(prob, outcome):
    if not prob:
        return None
    tot = 0.0
    for p, o in zip(prob, outcome):
        p = min(1 - CLIP, max(CLIP, p))
        tot += -(math.log(p) if o else math.log(1 - p))
    return tot / len(prob)


def decision_points(squad, pred, act, pos):
    """XI plus captain from a fixed 15: the best legal XI by `pred`
    (fpl_edge._best_xi: 1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD), captain = the
    highest forecast in it, doubled; realised points of that XI; no automatic
    substitutions, no vice-captain transfer; a squad member without a forecast
    counts as forecast 0 and a non-player scores 0."""
    rows = [{"id": pid, "pos": pos[pid], "proj": pred.get(pid, 0.0)} for pid in squad]
    xi = E._best_xi(rows)
    if len(xi) != 11:
        return None
    cap = max(xi, key=lambda r: (r["proj"], -r["id"]))
    return sum(act.get(r["id"], 0.0) for r in xi) + act.get(cap["id"], 0.0)


# ---------------------------------------------------------------------------
# paired bootstrap, Holm, Benjamini-Hochberg, power
# ---------------------------------------------------------------------------

def bootstrap_mean(values, b=B, seed=SEED, ci=CI):
    """Percentile bootstrap of the mean over `values` (one per gameweek):
    resample with replacement b times. Returns {mean, lo, hi, n, p} where
    p is the two-sided bootstrap p-value, 2 * min(share of resample means
    <= 0, share >= 0), floored at 1/(b+1) and capped at 1."""
    n = len(values)
    if n == 0:
        return {"mean": None, "lo": None, "hi": None, "n": 0, "p": None}
    rng = random.Random(seed)
    means = []
    choices, s = rng.choices, sum
    for _ in range(b):
        means.append(s(choices(values, k=n)) / n)
    means.sort()
    tail = (1 - ci) / 2
    lo = means[int(round(tail * b))]
    hi = means[int(round((1 - tail) * b)) - 1]
    le = sum(1 for m in means if m <= 0) / b
    ge = sum(1 for m in means if m >= 0) / b
    p = min(1.0, max(1.0 / (b + 1), 2 * min(le, ge)))
    return {"mean": sum(values) / n, "lo": lo, "hi": hi, "n": n, "p": p}


def holm(pvals, alpha=0.10):
    """Holm step-down: {label: rejected}. pvals = [(label, p)]."""
    m = len(pvals)
    order = sorted(pvals, key=lambda lp: lp[1])
    out, stop = {}, False
    for i, (label, p) in enumerate(order):
        if not stop and p <= alpha / (m - i):
            out[label] = True
        else:
            stop = True
            out[label] = False
    return out


def benjamini_hochberg(pvals, q=0.10):
    """BH step-up at FDR q: {label: rejected}."""
    m = len(pvals)
    order = sorted(pvals, key=lambda lp: lp[1])
    k = 0
    for i, (label, p) in enumerate(order, 1):
        if p <= q * i / m:
            k = i
    return {label: i <= k for i, (label, p) in enumerate(order, 1)}


def power_gameweeks(s_d, delta, z_alpha=Z_ALPHA, z_beta=Z_BETA):
    """G = ((z_alpha + z_beta) * s_d / delta)^2 gameweeks."""
    return ((z_alpha + z_beta) * s_d / delta) ** 2


def sd(values):
    n = len(values)
    if n < 2:
        return None
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1))


# ---------------------------------------------------------------------------
# the self-test (prereg acceptance test 1)
# ---------------------------------------------------------------------------

def selftest(reps=400, seed=SELFTEST_SEED, s=0.10, delta=0.03, b=B, out=print):
    """Synthetic per-gameweek differences Normal(delta, s), n = ceil(G)
    gameweeks, judged by the same rule the harness applies to real data:
    the 90% bootstrap CI lower bound > 0. Returns (power, false_positive, n)."""
    n = math.ceil(power_gameweeks(s, delta))
    rng = random.Random(seed)
    rates = {}
    for true_delta in (delta, 0.0):
        hits = 0
        for _ in range(reps):
            diffs = [rng.gauss(true_delta, s) for _ in range(n)]
            r = bootstrap_mean(diffs, b=b, seed=rng.randrange(1 << 31))
            hits += r["lo"] > 0
        rates[true_delta] = hits / reps
    power, fp = rates[delta], rates[0.0]
    out(f"SELF-TEST  {reps} replications, seed {seed}, s = {s}, delta = {delta}, "
        f"n = ceil(G) = {n} gameweeks, B = {b}")
    out(f"  true effect detected: {power:.3f}   bar 0.80 +/- 0.05  "
        f"{'PASS' if abs(power - 0.80) <= 0.05 else 'FAIL'}")
    out(f"  false positives:      {fp:.3f}   bar 0.05 +/- 0.02  "
        f"{'PASS' if abs(fp - 0.05) <= 0.02 else 'FAIL'}")
    return power, fp, n


# ---------------------------------------------------------------------------
# 2026/27 - the projection log and the database, point-in-time
# ---------------------------------------------------------------------------

def load_2627(data_dir):
    """{"events", "deadline", "settled", "forecasts", "actual", "pos",
    "squads", "dropped"}. Forecasts come through fpl_edge.forecasts() - the
    S2 reader rule. A gameweek is settled when its event has data_checked = 1
    and every one of its fixtures is finished = 1 (and it has fixtures)."""
    db = os.path.join(data_dir, "fpl.sqlite")
    log = os.path.join(data_dir, E.LOG_PATH)          # the forecast log, read through forecasts()
    for p in (db, log):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing")
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    events = {}
    for ev, dl, fin, chk in c.execute("select id, deadline_time, finished, data_checked from events"):
        events[ev] = {"deadline_time": dl, "finished": fin, "data_checked": chk}
    fx = defaultdict(list)
    for ev, fin in c.execute("select event, finished from fixtures where event is not null"):
        fx[ev].append(fin)
    settled = {ev for ev, e in events.items()
               if e["data_checked"] == 1 and fx.get(ev) and all(f == 1 for f in fx[ev])}
    pos = {pid: p for pid, p in c.execute("select id, position from players")}
    actual = defaultdict(dict)
    for row in c.execute("select player_id, event, total_points, minutes, starts, clean_sheets, "
                         "goals, bonus, defensive_contribution from player_gw"):
        pid, ev, pts, mins, starts, cs, goals, bonus, dc = row
        actual[ev][pid] = {"pts": pts or 0, "mins": mins or 0, "starts": starts or 0,
                           "cs": cs or 0, "goals": goals or 0, "bonus": bonus or 0,
                           "defcon": dc or 0}
    squads = defaultdict(list)
    for ev, pid, slot in c.execute("select event, player_id, position from picks "
                                   "where entry_id = ? order by event, position", (MY_ENTRY,)):
        squads[ev].append(pid)
    c.close()
    d = {"events": [{"event": ev, "deadline_time": e["deadline_time"]} for ev, e in events.items()]}
    rows = E.read_log(log)
    kept = E.forecasts(rows, d)
    forecasts = defaultdict(dict)
    for r in kept:
        forecasts[(int(r["event"]), r["source"])][int(r["player_id"])] = float(r["predicted"])
    return {"events": events, "settled": settled, "forecasts": forecasts, "actual": actual,
            "pos": pos, "squads": squads,
            "dropped": {(int(ev), src): n for (ev, src), n in E.dropped_players(rows, d).items()},
            "deadline": {ev: e["deadline_time"] for ev, e in events.items()}}


def weeks_2627(data, source):
    return sorted(ev for (ev, s) in data["forecasts"] if s == source and ev in data["settled"])


def rows_2627(data, ev, source, filt="all"):
    """[(pid, pred, actual dict)] for one settled gameweek and source; the
    starters filter reads the `minutes` snapshot of the same event."""
    if ev not in data["settled"]:
        raise MissingInput(f"GW{ev} is not settled - not graded")
    fc = data["forecasts"].get((ev, source))
    if not fc:
        raise MissingInput(f"no pre-deadline {source} snapshot for GW{ev}")
    out = []
    starters = data["forecasts"].get((ev, "minutes")) if filt == "starters" else None
    if filt == "starters" and not starters:
        raise MissingInput(f"GW{ev} has no minutes snapshot - the starters filter is undefined")
    for pid, pred in fc.items():
        if filt == "starters" and starters.get(pid, 0.0) < STARTER_P:
            continue
        a = data["actual"][ev].get(pid, {"pts": 0, "mins": 0, "starts": 0, "cs": 0,
                                         "goals": 0, "bonus": 0, "defcon": 0})
        out.append((pid, pred, a))
    return out


def components_2627(data, ev, source, rows):
    """{component: [(prob, outcome)]} - only components the source itself
    outputs: `minutes` is P(start) (a double gives > 1, which is skipped and
    counted). Every other 2026/27 source records one number."""
    if source != "minutes":
        return {}
    pairs, skipped = [], 0
    for pid, pred, a in rows:
        if pred > 1.0:
            skipped += 1
            continue
        pairs.append((pred, 1 if a["starts"] >= 1 else 0))
    return {"start": pairs, "_skipped": skipped}


# ---------------------------------------------------------------------------
# 2025/26 - rebuilt from rows with round < g (bottomup, minutes only)
# ---------------------------------------------------------------------------

def load_2526(hist_dir):
    """The canonical slice plus the raw de-duplicated rows per round (for
    per-fixture outcomes, `selected` and `value`)."""
    for name in ("merged_gw.csv", "fixtures.csv", "teams.csv"):
        if not os.path.exists(os.path.join(hist_dir, name)):
            raise MissingInput(f"{os.path.join(hist_dir, name)} is missing")
    c = H.canonical_from_vaastav(hist_dir, "2025/26")
    with open(os.path.join(hist_dir, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        raw, _ = H.dedup_rows(list(csv.DictReader(fh)))
    by_round = defaultdict(list)
    for r in raw:
        by_round[int(r["round"])].append(r)
    with open(os.path.join(hist_dir, "teams.csv"), encoding="utf-8", newline="") as fh:
        short = {t["id"]: t["short_name"] for t in csv.DictReader(fh)}
    # the point-in-time club map (amendment 2): the adapter's players carry
    # end-of-season clubs; every rebuild replaces them with club_at(g)
    return {"c": c, "raw": by_round, "through": c["through_gw"], "short": short,
            "cm": PIT.club_map(hist_dir)}


def canonical_at(hist, g):
    """The canonical slice with players as of gameweek g (amendment 2):
    only players who exist by g, each at his club of rounds <= g. Rows and
    team matches are untouched; callers still truncate to g-1 for training
    (fpl_edge.backtest_week does)."""
    return dict(hist["c"], players=PIT.players_at(hist["c"], hist["cm"], g))


def _p_cs(inp, p, opp):
    """P(clean sheet) for one fixture, the model's own Poisson: lambda =
    team GC/match x (opponent xG/match / league xG). Tied to
    project_reliability by a test (the cs term equals p_cs * CS_VALUE * ps)."""
    gc = inp["teams"].get(p["team"], {}).get("gc_per_match")
    gc = inp["league_gc"] if gc is None else gc
    oxg = inp["teams"].get(opp, {}).get("xg_per_match")
    oxg = inp["league_xg"] if oxg is None else oxg
    lam = gc * (oxg / inp["league_xg"]) if inp["league_xg"] else gc
    return math.exp(-lam)


def _p_defcon(inp, p):
    pos = p["pos"]
    if pos not in E.DEFCON_THRESHOLD:
        return None
    prior = inp["priors"].get((pos, "defcon90"), 0.0)
    w = inp["weights"]["defcon"]
    dc = prior if p["defcon90"] is None else p["defcon90"] * w + prior * (1 - w)
    return 1.0 / (1.0 + math.exp(-(dc - E.DEFCON_THRESHOLD[pos]) / 2.0))


def rebuild_2526(hist, t):
    """Gameweek t rebuilt from rounds < t: fpl_edge.backtest_week (the frozen
    rolling-origin rebuild) plus the components bottomup exposes per fixture.
    Returns {"rows": {source: [(pid, pred, actual)]}, "components":
    {source: {component: [(prob, outcome)]}}, "p_start": {pid: p}}."""
    if t < 2 or t > hist["through"]:
        raise MissingInput(f"GW{t} is outside the rebuildable range 2..{hist['through']}")
    c = canonical_at(hist, t)                 # clubs as of gameweek t (rounds <= t)
    bt = E.backtest_week(c, t)
    train = E.canonical_through(c, t - 1)
    inp = E.reliability_inputs(train, gws_played=t - 1)
    per_fixture = defaultdict(list)          # pid -> [raw row] in round t
    for r in hist["raw"].get(t, []):
        per_fixture[int(r["element"])].append(r)
    rows = {s: [] for s in SOURCES_2526}
    comps = {"bottomup": {"cs": [], "defcon": []}, "minutes": {"start": []}}
    p_start = {}
    for b in bt:
        pid = b["pid"]
        a = {"pts": b["actual"], "mins": 0, "starts": 0, "cs": 0, "goals": 0, "bonus": 0, "defcon": 0}
        for r in per_fixture.get(pid, []):
            a["mins"] += H._num(r["minutes"]); a["starts"] += H._num(r.get("starts"))
            a["cs"] += H._num(r.get("clean_sheets")); a["goals"] += H._num(r.get("goals_scored"))
            a["bonus"] += H._num(r.get("bonus")); a["defcon"] += H._num(r.get("defensive_contribution"))
        for s in SOURCES_2526:
            rows[s].append((pid, b["preds"][s], a))
        p = inp["players"][pid]
        p_start[pid] = p["p_start"]
        comps["minutes"]["start"].append((p["p_start"], 1 if a["starts"] >= 1 else 0))
        for r in per_fixture.get(pid, []):              # per fixture: a clean sheet needs 60+ minutes
            if H._num(r["minutes"]) >= 60 and E.CS_VALUE.get(p["pos"], 0):
                opp = hist["short"].get(r.get("opponent_team"), r.get("opponent_team"))
                comps["bottomup"]["cs"].append((_p_cs(inp, p, opp), 1 if H._num(r.get("clean_sheets")) >= 1 else 0))
        pd = _p_defcon(inp, p)
        if pd is not None and a["mins"] > 0:
            thr = E.DEFCON_THRESHOLD[p["pos"]]
            comps["bottomup"]["defcon"].append((pd, 1 if a["defcon"] >= thr else 0))
    return {"rows": rows, "components": comps, "p_start": p_start, "pos": {b["pid"]: b["pos"] for b in bt}}


def rows_2526(reb, source, filt="all"):
    if source in NOT_REBUILDABLE:
        raise MissingInput(f"{source} cannot be rebuilt for 2025/26: {NOT_REBUILDABLE[source]}")
    rows = reb["rows"][source]
    if filt == "starters":
        rows = [r for r in rows if reb["p_start"].get(r[0], 0.0) >= STARTER_P]
    return rows


# ---------------------------------------------------------------------------
# the 2025/26 decision squad: the legal 15 maximising `selected` (amendment 1:
# gameweek g uses the `selected` of gameweek g-1's rows, GW1 its own) at
# gameweek g's `value`, within 100.0m, 2/5/5/3, at most 3 per club - exact
# ---------------------------------------------------------------------------

def squad_candidates(hist, g):
    """[{id, pos, team, price (tenths), metric}] for gameweek g."""
    c = hist["c"]
    sel_round = g - 1 if g > 1 else 1
    latest = {}
    for r in hist["raw"].get(sel_round, []):
        latest[int(r["element"])] = H._num(r.get("selected"))
    cands = {}
    for r in hist["raw"].get(g, []):
        pid = int(r["element"])
        if pid not in latest or pid in cands:
            continue
        p = c["players"][pid]
        club = PIT.club_at(hist["cm"], pid, g)       # the club of gameweek g's own row
        cands[pid] = {"id": pid, "pos": p["pos"], "team": club,
                      "price": int(round(H._num(r["value"]))), "metric": latest[pid]}
    return list(cands.values())


def _prune(cands, quota, club_max=CLUB_MAX):
    """Drop a player dominated (cheaper-or-equal, metric higher-or-equal) by
    players from at least quota + club_max + 2 distinct clubs: at most
    quota - 1 of them can already be in the squad and at most 15 // club_max
    clubs can be full, so a free swap always exists."""
    out = []
    for pos, q in quota.items():
        pool = [p for p in cands if p["pos"] == pos]
        need = q + 15 // club_max + 1
        for p in pool:
            clubs = {d["team"] for d in pool if d is not p and d["price"] <= p["price"]
                     and d["metric"] >= p["metric"]}
            if len(clubs) < need:
                out.append(p)
    return out


def _knapsack(pool, k, budget):
    """f[c] = best metric choosing exactly k of `pool` with cost <= c, with
    reconstruction. Returns (f, chooser) where chooser(c) -> the players."""
    n = len(pool)
    NEG = float("-inf")
    f = [[NEG] * (budget + 1) for _ in range(k + 1)]
    f[0] = [0.0] * (budget + 1)
    take = [[[False] * (budget + 1) for _ in range(k + 1)] for _ in range(n)]
    for i, p in enumerate(pool):
        cost, v = p["price"], p["metric"]
        for j in range(min(k, i + 1), 0, -1):
            fj, fjm = f[j], f[j - 1]
            tj = take[i][j]
            for c in range(budget, cost - 1, -1):
                cand = fjm[c - cost] + v
                if cand > fj[c]:
                    fj[c] = cand
                    tj[c] = True

    def chooser(c):
        chosen, j = [], k
        for i in range(n - 1, -1, -1):
            if j and take[i][j][c]:
                chosen.append(pool[i]); c -= pool[i]["price"]; j -= 1
        return chosen
    return f[k], chooser


def _solve_clubfree(cands, quota, budget):
    parts = []
    for pos in (1, 2, 3, 4):
        pool = [p for p in cands if p["pos"] == pos]
        if len(pool) < quota[pos]:
            return None
        parts.append(_knapsack(pool, quota[pos], budget))
    # combine over cost
    g = parts[0][0]
    splits = []
    for f, _ in parts[1:]:
        h = [float("-inf")] * (budget + 1)
        arg = [None] * (budget + 1)
        for c1 in range(budget + 1):
            if g[c1] == float("-inf"):
                continue
            for c2 in range(budget + 1 - c1):
                if f[c2] == float("-inf"):
                    continue
                v = g[c1] + f[c2]
                if v > h[c1 + c2]:
                    h[c1 + c2] = v; arg[c1 + c2] = (c1, c2)
        splits.append(arg)
        g = h
    best_c = max(range(budget + 1), key=lambda c: g[c])
    if g[best_c] == float("-inf"):
        return None
    costs = [None] * 4
    c = best_c
    for idx in range(3, 0, -1):
        c1, c2 = splits[idx - 1][c]
        costs[idx] = c2; c = c1
    costs[0] = c
    chosen = []
    for (f, chooser), cc in zip(parts, costs):
        chosen.extend(chooser(cc))
    return {"metric": g[best_c], "squad": chosen, "cost": sum(p["price"] for p in chosen)}


def best_fifteen(cands, budget=BUDGET_TENTHS, quota=QUOTA, club_max=CLUB_MAX,
                 node_limit=NODE_LIMIT, prune=True):
    """The legal 15 maximising the metric: a club-free knapsack per position
    combined over cost, then branch and bound on the club limit (a node whose
    club-free optimum has too many of one club branches on which of them to
    drop). Returns {metric, squad, cost, exact, nodes} or None."""
    pool = _prune(cands, quota, club_max) if prune else list(cands)
    best, nodes = None, 0
    stack = [frozenset()]
    seen = set()
    while stack and nodes < node_limit:
        banned = stack.pop()
        if banned in seen:
            continue
        seen.add(banned); nodes += 1
        sol = _solve_clubfree([p for p in pool if p["id"] not in banned], quota, budget)
        if sol is None or (best and sol["metric"] <= best["metric"]):
            continue
        over = [t for t, n in Counter(p["team"] for p in sol["squad"]).items() if n > club_max]
        if not over:
            best = sol
            continue
        club = max(over, key=lambda t: sum(1 for p in sol["squad"] if p["team"] == t))
        for p in sol["squad"]:
            if p["team"] == club:
                stack.append(banned | {p["id"]})
    if best is None:
        return None
    best["exact"] = nodes < node_limit
    best["nodes"] = nodes
    return best


# ---------------------------------------------------------------------------
# per-gameweek evaluation and comparisons
# ---------------------------------------------------------------------------

def week_metrics(rows, pos=None):
    """Every per-gameweek metric on [(pid, pred, actual)] rows."""
    pids = [r[0] for r in rows]
    pred = [r[1] for r in rows]
    act = [float(r[2]["pts"]) for r in rows]
    out = {"n": len(rows), "spearman": spearman(pred, act), "kendall": kendall_tau_b(pred, act),
           "mae": mae(pred, act)}
    for k in TOPK:
        out[f"regret{k}"] = topk_regret(pids, pred, act, k)
    if pos:
        out["by_pos"] = {}
        for p in (1, 2, 3, 4):
            sub = [r for r in rows if pos.get(r[0]) == p]
            if len(sub) >= 3:
                out["by_pos"][p] = {"n": len(sub),
                                    "spearman": spearman([r[1] for r in sub], [float(r[2]["pts"]) for r in sub]),
                                    "mae": mae([r[1] for r in sub], [float(r[2]["pts"]) for r in sub])}
    return out


def component_metrics(comps):
    out = {}
    for comp in COMPONENTS:
        pairs = comps.get(comp)
        if not pairs:
            out[comp] = None
            continue
        out[comp] = {"n": len(pairs), "brier": brier([p for p, _ in pairs], [o for _, o in pairs]),
                     "logloss": log_loss([p for p, _ in pairs], [o for _, o in pairs])}
    return out


class Harness:
    """One season's graded weeks, loaded once."""

    def __init__(self, season, data_dir=None, hist_dir=None, log=print):
        self.season, self.log = season, log
        if season == "2026-27":
            self.data = load_2627(data_dir)
            self.sources = SOURCES_2627
        elif season == "2025-26":
            self.hist = load_2526(hist_dir)
            self.sources = SOURCES_2526
            self._reb, self._squad = {}, {}
        else:
            raise MissingInput(f"unknown season {season}")

    def weeks(self, source):
        if self.season == "2026-27":
            return weeks_2627(self.data, source)
        if source in NOT_REBUILDABLE:
            return []
        return list(range(5, self.hist["through"] + 1))

    def rebuilt(self, t):
        if t not in self._reb:
            self._reb[t] = rebuild_2526(self.hist, t)
        return self._reb[t]

    def rows(self, ev, source, filt="all"):
        if self.season == "2026-27":
            return rows_2627(self.data, ev, source, filt)
        return rows_2526(self.rebuilt(ev), source, filt)

    def positions(self, ev):
        if self.season == "2026-27":
            return self.data["pos"]
        return self.rebuilt(ev)["pos"]

    def components(self, ev, source, rows):
        if self.season == "2026-27":
            return components_2627(self.data, ev, source, rows)
        return self.rebuilt(ev)["components"].get(source, {})

    def squad(self, ev):
        """The fixed 15 for the decision metric, and a note."""
        if self.season == "2026-27":
            s = self.data["squads"].get(ev)
            if len(s or []) != 15:
                raise MissingInput(f"picks hold {len(s or [])} players for GW{ev}, not 15")
            return s, "our 15 (picks)"
        if ev not in self._squad:
            sol = best_fifteen(squad_candidates(self.hist, ev))
            if sol is None:
                raise MissingInput(f"no legal most-selected 15 for GW{ev}")
            self._squad[ev] = ([p["id"] for p in sol["squad"]],
                               f"most-selected 15 (selected of GW{ev - 1 if ev > 1 else 1}, "
                               f"cost {sol['cost'] / 10:.1f}m, {'exact' if sol['exact'] else 'NOT exact'}, "
                               f"{sol['nodes']} nodes)")
        return self._squad[ev]

    def decision(self, ev, source):
        rows = self.rows(ev, source, "all")
        squad, note = self.squad(ev)
        pred = {pid: p for pid, p, _ in rows}
        if self.season == "2026-27":
            act = {pid: float(a["pts"]) for pid, a in self.data["actual"][ev].items()}
        else:
            act = {r["player_id"]: float(r["pts"] or 0) for r in self.hist["c"]["rows"] if r["event"] == ev}
        pos = dict(self.positions(ev))
        for pid in squad:                       # a squad member outside the gate still has a position
            if pos.get(pid) is None:
                pos[pid] = self.hist["c"]["players"][pid]["pos"] if self.season == "2025-26" else None
        if any(pos.get(pid) is None for pid in squad):
            raise MissingInput(f"GW{ev}: a squad member has no position")
        missing = sum(1 for pid in squad if pid not in pred)
        return decision_points(squad, pred, act, pos), missing, note

    def compare(self, a, b, filt="all", seed=SEED):
        """Paired comparison of two sources over the gameweeks both have:
        per-gameweek differences (a - b) of every metric, then the bootstrap."""
        for s in (a, b):
            if self.season == "2025-26" and s in NOT_REBUILDABLE:
                raise MissingInput(f"{s} cannot be rebuilt for 2025/26: {NOT_REBUILDABLE[s]}")
        weeks = sorted(set(self.weeks(a)) & set(self.weeks(b)))
        if filt == "starters" and self.season == "2026-27":
            weeks = [w for w in weeks if (w, "minutes") in self.data["forecasts"]]
        if not weeks:
            raise MissingInput(f"no graded gameweek holds both {a} and {b}" +
                               (" with a minutes snapshot" if filt == "starters" else ""))
        per_week, diffs = [], defaultdict(list)
        for w in weeks:
            ra = {r[0]: r for r in self.rows(w, a, filt)}
            rb = {r[0]: r for r in self.rows(w, b, filt)}
            common = sorted(set(ra) & set(rb))
            ma = week_metrics([ra[p] for p in common])
            mb = week_metrics([rb[p] for p in common])
            da, _, _ = self.decision(w, a)
            db, _, _ = self.decision(w, b)
            ma["decision"], mb["decision"] = da, db
            per_week.append((w, len(common), ma, mb))
            for k in ("spearman", "kendall", "mae", "decision") + tuple(f"regret{k}" for k in TOPK):
                if ma.get(k) is not None and mb.get(k) is not None:
                    diffs[k].append(ma[k] - mb[k])
        boots = {k: bootstrap_mean(v, seed=seed) for k, v in diffs.items()}
        return {"a": a, "b": b, "filter": filt, "weeks": weeks, "per_week": per_week,
                "diffs": dict(diffs), "boot": boots}


# ---------------------------------------------------------------------------
# printing
# ---------------------------------------------------------------------------

def fmt(v, w=7, d=3):
    return f"{v:+{w}.{d}f}" if isinstance(v, float) else (f"{v!s:>{w}}" if v is not None else " " * (w - 3) + "n/a")


def print_compare(res, out=print):
    a, b = res["a"], res["b"]
    out(f"COMPARE {a} vs {b}   filter = {res['filter']}   gameweeks {res['weeks'][0]}-{res['weeks'][-1]} "
        f"({len(res['weeks'])} graded)   paired bootstrap B={B}, {int(CI * 100)}% CI, seed {SEED}")
    out(f"  {'GW':>4} {'n':>5} {'rho ' + a:>12} {'rho ' + b:>12} {'tau ' + a:>10} {'tau ' + b:>10} "
        f"{'MAE ' + a:>9} {'MAE ' + b:>9} {'XI+C ' + a:>10} {'XI+C ' + b:>10}")
    for w, n, ma, mb in res["per_week"]:
        out(f"  {w:>4} {n:>5} {fmt(ma['spearman'], 12)} {fmt(mb['spearman'], 12)} {fmt(ma['kendall'], 10)} "
            f"{fmt(mb['kendall'], 10)} {fmt(ma['mae'], 9, 2)} {fmt(mb['mae'], 9, 2)} "
            f"{fmt(ma['decision'], 10, 1)} {fmt(mb['decision'], 10, 1)}")
    out(f"  mean difference {a} - {b} over gameweeks, with its {int(CI * 100)}% interval:"
        + ("   (fewer than 5 gameweeks: the interval is not meaningful)" if len(res["weeks"]) < 5 else ""))
    for k, r in res["boot"].items():
        if r["n"]:
            out(f"    {k:<10} {r['mean']:+.4f}  [{r['lo']:+.4f}, {r['hi']:+.4f}]  n={r['n']}  p={r['p']:.3f}")


def report(data_dir, hist_dir, out=print, seasons=("2025-26", "2026-27")):
    """Step 4 item 8: own vs xg vs bottomup vs minutes vs fpl_ep, per season.
    Mean per-gameweek metric, each with its bootstrap interval; cells without
    a source print why."""
    for season in seasons:
        try:
            h = Harness(season, data_dir, hist_dir)
        except MissingInput as e:
            out(f"REPORT {season}: {e}")
            continue
        out(f"\nREPORT {season}   mean over graded gameweeks, {int(CI * 100)}% bootstrap CI (B={B}, seed {SEED})"
            + ("   (fewer than 5 settled gameweeks: intervals are not meaningful)"
               if season == "2026-27" and len(h.data["settled"]) < 5 else ""))
        srcs = SOURCES_2627
        for filt in ("all", "starters"):
            out(f"  filter = {filt}")
            out(f"  {'source':<10}{'GWs':>5}{'n/GW':>7}{'Spearman':>24}{'Kendall':>24}{'MAE':>20}"
                f"{'regret1':>10}{'regret3':>10}{'regret11':>10}{'XI+C pts':>22}")
            for s in srcs:
                if season == "2025-26" and s in NOT_REBUILDABLE:
                    out(f"  {s:<10}  not rebuildable: {NOT_REBUILDABLE[s]}")
                    continue
                weeks = h.weeks(s)
                if filt == "starters" and season == "2026-27":
                    weeks = [w for w in weeks if (w, "minutes") in h.data["forecasts"]]
                if not weeks:
                    out(f"  {s:<10}  not recorded for any settled gameweek" +
                        (" with a minutes snapshot" if filt == "starters" else ""))
                    continue
                per = defaultdict(list)
                ns = []
                for w in weeks:
                    rows = h.rows(w, s, filt)
                    m = week_metrics(rows)
                    ns.append(m["n"])
                    for k in ("spearman", "kendall", "mae", "regret1", "regret3", "regret11"):
                        if m.get(k) is not None:
                            per[k].append(m[k])
                    d, _, _ = h.decision(w, s)
                    if d is not None:
                        per["decision"].append(d)
                cells = []
                for k, wd in (("spearman", 24), ("kendall", 24), ("mae", 20), ("regret1", 10),
                              ("regret3", 10), ("regret11", 10), ("decision", 22)):
                    r = bootstrap_mean(per[k]) if per[k] else None
                    if r is None:
                        cells.append(f"{'n/a':>{wd}}")
                    elif wd >= 20:
                        cells.append(f"{r['mean']:+.3f} [{r['lo']:+.3f},{r['hi']:+.3f}]".rjust(wd))
                    else:
                        cells.append(f"{r['mean']:.2f}".rjust(wd))
                out(f"  {s:<10}{len(weeks):>5}{sum(ns) / len(ns):>7.0f}" + "".join(cells))
        # components
        out("  binary components (Brier / log loss), where a source exposes the probability itself:")
        for s in srcs:
            if season == "2025-26" and s in NOT_REBUILDABLE:
                continue
            weeks = h.weeks(s)
            if not weeks:
                continue
            agg = defaultdict(list)
            skipped = 0
            for w in weeks:
                rows = h.rows(w, s, "all")
                comps = h.components(w, s, rows)
                skipped += comps.get("_skipped", 0)
                for comp, pairs in comps.items():
                    if comp.startswith("_") or not pairs:
                        continue
                    agg[comp].append(pairs)
            line = []
            if season == "2026-27" and s != "minutes":
                out(f"    {s:<10}records one number per player: no component exposed")
                continue
            for comp in COMPONENTS:
                if comp not in agg:
                    line.append(f"{comp}: n/a (no source exposes it)")
                    continue
                bs = [brier([p for p, _ in pairs], [o for _, o in pairs]) for pairs in agg[comp]]
                ls = [log_loss([p for p, _ in pairs], [o for _, o in pairs]) for pairs in agg[comp]]
                rb, rl = bootstrap_mean(bs), bootstrap_mean(ls)
                n = sum(len(pairs) for pairs in agg[comp])
                line.append(f"{comp}: Brier {rb['mean']:.4f} [{rb['lo']:.4f},{rb['hi']:.4f}] "
                            f"logloss {rl['mean']:.4f} (n={n})")
            out(f"    {s:<10}" + "; ".join(line) + (f"; {skipped} double-gameweek P(start) > 1 skipped" if skipped else ""))
        if season == "2026-27" and h.data["dropped"]:
            out("  players dropped between snapshots (not graded on the older forecast): "
                + ", ".join(f"GW{ev} {s}: {n}" for (ev, s), n in sorted(h.data["dropped"].items())))
        if season == "2025-26":
            out("  2025/26 points are under 2025/26 rules (Step 10 has not landed); DEF/GK figures sit on superseded BPS rules.")
            ws = h.weeks("bottomup")
            for w in sorted({ws[0], ws[len(ws) // 2], ws[-1]}):
                _, note = h.squad(w)
                out(f"  decision squad GW{w}: {note}")


def power_report(hist_dir, out=print):
    """s_d measured on 2025/26 for bottomup - minutes, GW5-38, and G for the
    pre-registered deltas, for starters Spearman, all Spearman and the
    decision metric."""
    h = Harness("2025-26", hist_dir=hist_dir)
    out(f"POWER  G = ((z_alpha + z_beta) * s_d / delta)^2, z_alpha = {Z_ALPHA} (alpha 0.10 two-sided, "
        f"the 90% CI rule), z_beta = {Z_BETA} (beta 0.20); s_d from 2025/26 bottomup - minutes, GW5-{h.hist['through']}")
    rows = []
    for label, filt, key in (("Spearman, starters", "starters", "spearman"),
                             ("Spearman, all", "all", "spearman"),
                             ("decision (XI+C points), all", "all", "decision")):
        res = h.compare("bottomup", "minutes", filt)
        s = sd(res["diffs"][key])
        rows.append((label, s, len(res["diffs"][key])))
        out(f"  {label:<30} s_d = {s:.4f} over {len(res['diffs'][key])} gameweeks  "
            + "  ".join(f"delta {d}: G = {power_gameweeks(s, d):7.1f}" for d in DELTAS))
        if key == "decision":                 # information only: the pre-registered deltas are in rho units
            out(f"  {'':<30} (in points, information only)  "
                + "  ".join(f"delta {d}: G = {power_gameweeks(s, d):7.1f}" for d in (1.0, 2.0, 3.0)))
    return rows


def main(argv=None):
    utf8_console()                       # RULING S5 amendment fix: never stop on a console code page
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"),
                    help="the data branch worktree (read-only)")
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    ap.add_argument("--season", default="2026-27", choices=("2025-26", "2026-27"))
    ap.add_argument("--filter", default="all", choices=("all", "starters"))
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"))
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--reps", type=int, default=400)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        if args.compare:
            h = Harness(args.season, args.data, args.hist)
            print_compare(h.compare(args.compare[0], args.compare[1], args.filter), out)
            name = f"compare_{args.season}_{args.compare[0]}_{args.compare[1]}_{args.filter}.txt"
        elif args.report:
            report(args.data, args.hist, out)
            name = "report.txt"
        elif args.power:
            power_report(args.hist, out)
            name = "power.txt"
        elif args.selftest:
            selftest(reps=args.reps, out=out)
            name = "selftest.txt"
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
