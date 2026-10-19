"""fpl_bt.py - the runner's copy of tools/backtest.py, the part that
the report sections need (W2 piece c; prereg/W2.md acceptance 1).

Every definition below is copied verbatim from tools/backtest.py by its syntax
tree, so the runner never imports tools/; tests/test_W2.py holds the
sections byte-identical to the tools' output. Standard library only.
"""
import csv
import fpl_edge as E
import fpl_hist as H
import fpl_pit as PIT
import math
import os
import random
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime


SEED = 20261018            # the bootstrap seed (prereg)


B = 10000                  # resamples


CI = 0.90                  # interval


STARTER_P = 0.8            # starters = forecast P(start) >= 0.8, never realised minutes


TOPK = (1, 3, 11)


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


POS_NAME = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


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


def sd(values):
    n = len(values)
    if n < 2:
        return None
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1))


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
