"""
tools/chips.py - the first-half chip calculator and Free Hit screen
(BUILD_PLAN.md Step 7, item S7, offline). Standard library only; the nightly
never imports it (wiring is lane A's W2).

    python tools/chips.py                      # live: V table, continuation values, PLAY/HOLD, FH screen, bench prep
    python tools/chips.py --replay             # the pre-registered 2025/26 replay (50 synthetic squads, seed 7)

Definitions, as pre-registered in prereg/S7.md (with amendment 1):
  xP source   `own`: the recorded row for the next gameweek (projection log,
              S2 reader rule), and for every later gameweek through GW19
              fpl_edge.project() from the same export on that gameweek's real
              fixture(s) from fpl.sqlite's fixtures table (RULING S7 result,
              point 2: no proxy weeks) - the recording formula.
  V_BB,t      sum over the four bench players of xP_t x (1 - w), w = 0.30 /
              0.10 / 0.03 for the outfield bench in forecast order, 0.03 for
              the sub keeper: the bench points a Bench Boost adds beyond the
              automatic substitutions that happen anyway.
  V_FH,t      the best legal one-week XI the selling budget buys (fpl_edge's
              item N solver) minus our best XI from the current 15, both by
              the week's xP. No transfers assumed (amendment 1 point 4): our
              squad is held fixed, so V_FH is an upper bound.
  Induction   V(t, S) = max(hold, play BB, play FH) over t = next .. 19,
              chips S left, one chip a week, FH never in GW19, V(20, .) = 0.
  Replay      2025/26 GW5-19 on 50 squads sampled from GW1 ownership (seed 7),
              point-in-time `bottomup` forecasts from the S4 harness (the only
              source rebuildable for 2025/26), squads held fixed, clubs from
              tools/hist_pit.py; realised chip points; paired bootstrap over
              squads (B = 10,000, 90%, seed 20261018) against the heuristic.
"""

import argparse
import glob
import gzip
import json
import math
import os
import random
import sqlite3
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import hist_pit as PIT                                            # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

BENCH_W = (0.30, 0.10, 0.03)      # outfield bench, in forecast order
SUBGK_W = 0.03
LAST_GW = 19                      # both first-half chips are worth 0 after it
CHIPS = ("BB", "FH")
CHIP_API = {"bboost": "BB", "freehit": "FH"}
SQUAD_SEED = 7
N_SQUADS = 50
REPLAY_FIRST = 5                  # GW1-4 have no training window
RESAMPLES = 1000
SEED = BT.SEED
QUOTA = {1: 2, 2: 5, 3: 5, 4: 3}
CLUB_MAX = 3
BUDGET_TENTHS = 1000
GATE_MINS = 45
PASS_LOWER = -3.0


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# the export and the xP source (live)
# ---------------------------------------------------------------------------

def newest_export(data_dir):
    """The newest dated export under exports/ (the data worktree, read-only)."""
    files = glob.glob(os.path.join(data_dir, "exports", "fpl_export_gw*_*.json.gz"))
    if not files:
        raise MissingInput(f"no dated export under {os.path.join(data_dir, 'exports')}")

    def key(f):
        base = os.path.basename(f)
        gw = int(base.split("_gw")[1].split("_")[0])
        return (gw, base.split("_")[-1])
    path = max(files, key=key)
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh), path


def fixtures_ticker(data_dir, first, last=LAST_GW):
    """team -> [(gw, 'OPP (H)', fdr), ...] for gameweeks first..last from
    fpl.sqlite's fixtures table (all 380), the shape fpl_edge.build_ticker
    gives for the export's six. A gameweek with no fixture rows stops the
    run (reported, never substituted)."""
    db = os.path.join(data_dir, "fpl.sqlite")
    if not os.path.exists(db):
        raise MissingInput(f"{db} is missing")
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    teams = {i: short for i, short in c.execute("select id, short_name from teams")}
    tick, seen = defaultdict(list), set()
    for ev, h, a, hd, ad in c.execute(
            "select event, team_h, team_a, team_h_difficulty, team_a_difficulty from fixtures "
            "where event between ? and ? and team_h is not null and team_a is not null", (first, last)):
        if h not in teams or a not in teams:
            raise MissingInput(f"fixture in GW{ev} names a team id not in teams: {h}, {a}")
        tick[teams[h]].append((ev, f"{teams[a]} (H)", hd))
        tick[teams[a]].append((ev, f"{teams[h]} (A)", ad))
        seen.add(ev)
    c.close()
    missing = [w for w in range(first, last + 1) if w not in seen]
    if missing:
        raise MissingInput(f"the fixtures table has no fixture for GW{missing}")
    for t in tick:
        tick[t].sort()
    return tick, list(range(first, last + 1))


def own_week_points(d, log_rows, tick=None, weeks=None):
    """(weeks, pts, src): pts[w][pid] by the `own` source for every gameweek
    in `weeks` (default: the export's upcoming six): the recorded row where
    the log holds one for that event (the S2 reader rule), else
    fpl_edge.project() on that week's fixture(s) from `tick` - the formula
    record_status uses - for players through the recording gate (status 'a',
    45+ minutes in the last four); a blank or a gated-out player scores 0.
    src is 'own', 'own-model', 'blank' or 'gate'."""
    if tick is None or weeks is None:
        tick, weeks = E.build_ticker(d, 6)
    own = defaultdict(dict)
    for r in E.forecasts(log_rows, d):
        if r["source"] == "own":
            own[int(r["event"])][int(r["player_id"])] = float(r["predicted"])
    priors = E.positional_priors(d["all_players"])
    personal = E.personal_priors(d)
    pts, src = {}, {}
    for w in weeks:
        pts[w], src[w] = {}, {}
        for p in d["all_players"]:
            pid = p["id"]
            if pid in own[w]:
                pts[w][pid], src[w][pid] = own[w][pid], "own"
                continue
            fx = [f for f in tick.get(p["team"], []) if f[0] == w]
            if not fx:
                pts[w][pid], src[w][pid] = 0.0, "blank"
            elif p["status"] != "a" or (p.get("mins_last4") or 0) < 45:
                pts[w][pid], src[w][pid] = 0.0, "gate"
            else:
                v = sum(E.project(p, {p["team"]: [f]}, 6, d["gameweek"], priors, personal)[0] for f in fx)
                pts[w][pid], src[w][pid] = max(0.0, v), "own-model"
    return weeks, pts, src


def my_squad(d):
    """Our 15 as rows {id, name, team, pos, price, selling, status} from the
    export's squads (player_id and selling_price, S2); refused without them."""
    me = d["my_entry"]
    by_id = {p["id"]: p for p in d["all_players"]}
    rows = sorted((r for r in d["squads"] if r["entry_id"] == me), key=lambda r: r["slot"])
    if len(rows) != 15:
        raise MissingInput(f"the export holds {len(rows)} squad rows for entry {me}, not 15")
    out = []
    for r in rows:
        if r.get("player_id") is None or r.get("selling_price") is None:
            raise MissingInput("the export has no player_id or selling_price for my squad (pre-S2 export)")
        p = by_id.get(r["player_id"])
        if p is None:
            raise MissingInput(f"squad player {r['player_id']} is not in all_players")
        out.append({"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"],
                    "price": p["price"], "selling": r["selling_price"], "status": p["status"]})
    return out


def chips_left(d):
    me_name = next(r["entry_name"] for r in d["squads"] if r["entry_id"] == d["my_entry"])
    used = {CHIP_API[c["name"]] for c in d.get("chips_used", [])
            if c["entry_name"] == me_name and c["name"] in CHIP_API}
    return frozenset(c for c in CHIPS if c not in used)


# ---------------------------------------------------------------------------
# chip values
# ---------------------------------------------------------------------------

def xi_and_bench(squad, pts):
    """(xi, bench_outfield in forecast order, sub keeper) from a 15 by the
    week's xP: fpl_edge._best_xi, then the rest; a missing forecast is 0."""
    rows = [dict(r, proj=pts.get(r["id"], 0.0)) for r in squad]
    xi = E._best_xi(rows)
    if len(xi) != 11:
        raise MissingInput("no legal XI from the 15")
    in_xi = {r["id"] for r in xi}
    rest = [r for r in rows if r["id"] not in in_xi]
    sub_gk = [r for r in rest if r["pos"] == 1]
    outfield = sorted((r for r in rest if r["pos"] != 1), key=lambda r: (-r["proj"], r["id"]))
    if len(sub_gk) != 1 or len(outfield) != 3:
        raise MissingInput("the bench is not one keeper and three outfield players")
    return xi, outfield, sub_gk[0]


def bench_boost_value(outfield, sub_gk):
    """V_BB = sum of bench xP x (1 - w): what a Bench Boost adds beyond the
    automatic substitutions that would happen anyway."""
    return (sum(r["proj"] * (1 - w) for r, w in zip(outfield, BENCH_W))
            + sub_gk["proj"] * (1 - SUBGK_W))


def market_rows(d, pts_w):
    """The item N solver's inputs for one week: market = the gate (status
    'a', 45+ minutes), fodder = every status-'a' player; pts = the week's xP."""
    def row(p):
        return {"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"],
                "price": p["price"], "status": p["status"], "pts": pts_w.get(p["id"], 0.0)}
    market = [row(p) for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    fodder = [row(p) for p in d["all_players"] if p["status"] == "a"]
    return market, fodder


def free_hit_value(market, fodder, budget, squad, pts_w):
    """(V_FH, fh, ours_xi): the best legal one-week XI the budget buys minus
    our best XI by the same xP. No transfers assumed (amendment 1 point 4)."""
    fh = E.best_one_week_xi(market, fodder, budget)
    xi, _, _ = xi_and_bench(squad, pts_w)
    ours = sum(r["proj"] for r in xi)
    if fh is None:
        return None, None, xi
    return fh["pts"] - ours, fh, xi


# ---------------------------------------------------------------------------
# backward induction
# ---------------------------------------------------------------------------

def induction(v_bb, v_fh, first, last=LAST_GW, chips=frozenset(CHIPS)):
    """V(t, S) for t = first..last and every S subset of `chips`: the value of
    holding the chips in S from t on. One chip a week; FH never in GW19;
    V(last + 1, .) = 0. Returns {"V": {(t, S): value}, "action": {(t, S):
    'HOLD' | 'PLAY BB' | 'PLAY FH'}, "next": the action at (first, chips)}.
    A tie goes to playing (the chip is worth 0 after `last`, so holding at
    equal value only risks losing it); BB before FH on a tie between them."""
    subsets = []
    for k in range(len(chips) + 1):
        from itertools import combinations
        subsets += [frozenset(c) for c in combinations(sorted(chips), k)]
    V, action = {}, {}
    for S in subsets:
        V[(last + 1, S)] = 0.0
    for t in range(last, first - 1, -1):
        for S in subsets:
            best, act = V[(t + 1, S)], "HOLD"
            if "BB" in S and v_bb.get(t) is not None:
                v = v_bb[t] + V[(t + 1, S - {"BB"})]
                if v >= best - 1e-12:
                    best, act = v, "PLAY BB"
            if "FH" in S and t != last and v_fh.get(t) is not None:
                v = v_fh[t] + V[(t + 1, S - {"FH"})]
                if v > best + 1e-12:
                    best, act = v, "PLAY FH"
            V[(t, S)], action[(t, S)] = best, act
    return {"V": V, "action": action, "next": action[(first, frozenset(chips))], "subsets": subsets}


def action_values(v_bb, v_fh, ind, t, chips, last=LAST_GW):
    """{action: value} at (t, chips): hold, and each chip still held."""
    S = frozenset(chips)
    vals = {"HOLD": ind["V"][(t + 1, S)]}
    if "BB" in S and v_bb.get(t) is not None:
        vals["PLAY BB"] = v_bb[t] + ind["V"][(t + 1, S - {"BB"})]
    if "FH" in S and t != last and v_fh.get(t) is not None:
        vals["PLAY FH"] = v_fh[t] + ind["V"][(t + 1, S - {"FH"})]
    return vals


def margin(v_bb, v_fh, ind, t, chips, action=None):
    """The margin of `action` (default: the induction's choice at t) over the
    best other action at (t, chips); negative when a resample prefers
    another action."""
    vals = action_values(v_bb, v_fh, ind, t, chips)
    action = action or ind["action"][(t, frozenset(chips))]
    others = [v for a, v in vals.items() if a != action]
    return vals[action] - max(others) if others else 0.0


# ---------------------------------------------------------------------------
# the live calculator
# ---------------------------------------------------------------------------

def residual_pools(data_dir, source="own"):
    """Residuals (realised minus forecast) by position from every gameweek the
    S4 harness has graded for `source` in 2026/27; counts printed by the caller."""
    h = BT.Harness("2026-27", data_dir=data_dir)
    pools = defaultdict(list)
    for ev in h.weeks(source):
        for pid, pred, a in h.rows(ev, source, "all"):
            pos = h.data["pos"].get(pid)
            if pos is not None:
                pools[pos].append(float(a["pts"]) - pred)
    return pools


def live(data_dir, out=print, resamples=RESAMPLES, seed=SEED):
    d, path = newest_export(data_dir)
    log_rows = E.read_log(os.path.join(data_dir, E.LOG_PATH))
    first = d["gameweek"] + 1
    if first > LAST_GW:
        raise MissingInput(f"GW{first} is past GW{LAST_GW}: the first-half chips are worth 0")
    tick, weeks = fixtures_ticker(data_dir, first, LAST_GW)
    weeks, pts, src = own_week_points(d, log_rows, tick, weeks)
    squad = my_squad(d)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise MissingInput(f"no budget: {why}")
    chips = chips_left(d)
    first = weeks[0]
    out(f"CHIP CALCULATOR  export {os.path.basename(path)} (GW{d['gameweek']} played), "
        f"next GW{first}, chips left: {', '.join(sorted(chips)) or 'none'}; budget £{budget:.1f}m = bank + selling prices")
    out(f"  xP source: own - the recorded row for GW{first} where the log holds one, else the own")
    out(f"  formula on each week's real fixtures from the fixtures table, GW{first}-GW{LAST_GW} (no proxy weeks).")
    out("  Every Free Hit value: no transfers assumed (our 15 held fixed; an upper bound).")
    v_bb, v_fh, detail = {}, {}, {}
    for w in weeks:
        xi, outfield, gk = xi_and_bench(squad, pts[w])
        v_bb[w] = bench_boost_value(outfield, gk)
        market, fodder = market_rows(d, pts[w])
        v, fh, _ = free_hit_value(market, fodder, budget, squad, pts[w])
        v_fh[w] = v
        n_own = sum(1 for r in squad if src[w].get(r["id"]) == "own")
        detail[w] = {"xi": xi, "bench": outfield, "gk": gk, "fh": fh, "ours": sum(r["proj"] for r in xi),
                     "metric": "own" if n_own else "own-model"}
    ind = induction(v_bb, v_fh, first, LAST_GW, chips)
    out("")
    out(f"  {'GW':>4} {'metric':>10} {'V_BB':>7} {'V_FH':>7} {'ours XI':>8} {'FH XI':>7}   "
        + "  ".join(f"V({'+'.join(sorted(S)) or 'none'})" for S in ind["subsets"]) + "   action with all chips")
    for w in range(first, LAST_GW + 1):
        dw = detail[w]
        cont = "  ".join(f"{ind['V'][(w, S)]:9.2f}" for S in ind["subsets"])
        out(f"  {w:>4} {dw['metric']:>10} {v_bb[w]:7.2f} "
            f"{(v_fh[w] if v_fh[w] is not None else float('nan')):7.2f} {dw['ours']:8.2f} "
            f"{(dw['fh']['pts'] if dw['fh'] else float('nan')):7.2f}   {cont}   {ind['action'][(w, chips)]}")
    out("")
    nxt = ind["next"]
    m = margin(v_bb, v_fh, ind, first, chips)
    out(f"  NEXT GAMEWEEK GW{first}: {nxt}   (margin over the best other action {m:+.2f} xP)")
    # uncertainty: residuals by position, the XIs held fixed under resampling
    pools = residual_pools(data_dir)
    out("  residuals by position (2026/27 own, graded gameweeks): "
        + ", ".join(f"{BT.POS_NAME[p]} n={len(v)}" for p, v in sorted(pools.items())))
    if all(pools.get(p) for p in (1, 2, 3, 4)):
        rng = random.Random(seed)
        same, margins = 0, []
        pos_of = {r["id"]: r["pos"] for r in squad}
        for _ in range(resamples):
            rb, rf = {}, {}
            for w in weeks:
                dw = detail[w]
                noise = {r["id"]: rng.choice(pools[r["pos"]]) for r in squad}
                rb[w] = (sum((r["proj"] + noise[r["id"]]) * (1 - wt) for r, wt in zip(dw["bench"], BENCH_W))
                         + (dw["gk"]["proj"] + noise[dw["gk"]["id"]]) * (1 - SUBGK_W))
                if dw["fh"] is not None:
                    fh_pts = sum(p["pts"] + rng.choice(pools[p["pos"]]) for p in dw["fh"]["xi"])
                    ours = sum(r["proj"] + noise[r["id"]] for r in dw["xi"])
                    rf[w] = fh_pts - ours
                else:
                    rf[w] = None
            ri = induction(rb, rf, first, LAST_GW, chips)
            same += ri["next"] == nxt
            margins.append(margin(rb, rf, ri, first, chips, action=nxt))
        margins.sort()
        lo, hi = margins[int(0.05 * resamples)], margins[int(0.95 * resamples) - 1]
        out(f"  uncertainty: {resamples} residual resamples by position (XIs held fixed): "
            f"margin of {nxt} over the best other action 90% [{lo:+.2f}, {hi:+.2f}], same action in {same / resamples:.0%}")
    else:
        out("  uncertainty: no graded own gameweek for every position yet - no interval")
    # bench prep for the planned BB week
    bb_week = next((w for w in range(first, LAST_GW + 1)
                    if ind["action"][(w, chips)] == "PLAY BB"), None)
    if bb_week is None and "BB" in chips:
        bb_week = max(range(first, LAST_GW + 1), key=lambda w: v_bb[w])
    if bb_week is not None and "BB" in chips:
        out("")
        out(f"  BENCH PREP for GW{bb_week}: "
            "one transfer per bench slot, same position, within bank + selling price (bench counts 1.0 in a BB week)")
        for line in bench_prep(d, squad, pts[bb_week], detail[bb_week], budget):
            out(line)
    # the Free Hit screen (item N, selling budget)
    out("")
    out("  FREE HIT SCREEN (item N: own where recorded, else bottomup; budget = bank + selling prices)")
    fh_table = E.free_hit_table(d, E.forecasts(log_rows, d))
    for line in E.free_hit_lines(fh_table):
        out(line)
    return {"weeks": weeks, "v_bb": v_bb, "v_fh": v_fh, "induction": ind, "next": nxt, "chips": chips,
            "budget": budget, "detail": detail}


def bench_prep(d, squad, pts_w, dw, budget):
    """For each bench slot of the planned BB week, the best same-position
    replacement by that week's xP within bank + selling price, club cap kept;
    information only."""
    bank = budget - sum(r["selling"] for r in squad)
    clubs = Counter(r["team"] for r in squad)
    ids = {r["id"] for r in squad}
    lines = []
    for r in list(dw["bench"]) + [dw["gk"]]:
        cands = [p for p in d["all_players"]
                 if p["pos"] == r["pos"] and p["status"] == "a" and p["id"] not in ids
                 and (p.get("mins_last4") or 0) >= 45
                 and p["price"] <= r["selling"] + bank + 1e-9
                 and clubs[p["team"]] - (1 if p["team"] == r["team"] else 0) < CLUB_MAX]
        best = max(cands, key=lambda p: (pts_w.get(p["id"], 0.0), -p["price"]), default=None)
        if best is None:
            lines.append(f"    {r['name']:<16} {r['proj']:5.2f}  no affordable replacement")
            continue
        gain = pts_w.get(best["id"], 0.0) - r["proj"]
        lines.append(f"    {r['name']:<16} {r['proj']:5.2f} -> {best['web_name']:<16} {pts_w.get(best['id'], 0.0):5.2f} "
                     f"(£{best['price']:.1f}m, {best['team']})  gain {gain:+.2f}")
    return lines


# ---------------------------------------------------------------------------
# the 2025/26 replay (pre-registered test)
# ---------------------------------------------------------------------------

def gw1_candidates(hist):
    """[{id, pos, team, price (tenths), selected}] from the GW1 rows."""
    c, cm = hist["c"], hist["cm"]
    out = {}
    for r in hist["raw"].get(1, []):
        pid = int(r["element"])
        if pid in out:
            continue
        out[pid] = {"id": pid, "pos": c["players"][pid]["pos"], "team": PIT.club_at(cm, pid, 1),
                    "price": int(round(H._num(r["value"]))), "selected": H._num(r.get("selected"))}
    return list(out.values())


def sample_squads(cands, n=N_SQUADS, seed=SQUAD_SEED, budget=BUDGET_TENTHS):
    """n legal squads: players drawn without replacement with probability
    proportional to `selected`, position quotas filled in draw order, club
    cap 3; a draw whose 15 cost more than the budget is rejected and redrawn."""
    rng = random.Random(seed)
    pool = [p for p in cands if p["selected"] > 0]
    squads, tries = [], 0
    while len(squads) < n:
        tries += 1
        if tries > 100000:
            raise MissingInput("could not sample a legal squad within the budget")
        avail = list(pool)
        weights = [p["selected"] for p in avail]
        picked, filled, clubs = [], Counter(), Counter()
        while len(picked) < 15 and avail:
            i = rng.choices(range(len(avail)), weights=weights, k=1)[0]
            p = avail.pop(i); weights.pop(i)
            if filled[p["pos"]] >= QUOTA[p["pos"]] or clubs[p["team"]] >= CLUB_MAX:
                continue
            picked.append(p); filled[p["pos"]] += 1; clubs[p["team"]] += 1
        if len(picked) == 15 and sum(p["price"] for p in picked) <= budget:
            squads.append(sorted(picked, key=lambda p: (p["pos"], p["id"])))
    return squads


class Replay:
    """2025/26 point-in-time replay on the S4 harness: forecasts at origin t
    for weeks u >= t use rounds < t (training) and the fixture pairings of u;
    clubs as of t (hist_pit); prices of round t."""

    def __init__(self, hist_dir, last=LAST_GW):
        self.last = last
        self.hist = BT.load_2526(hist_dir)
        self.c, self.cm = self.hist["c"], self.hist["cm"]
        self.through = self.hist["through"]
        self.pairings = defaultdict(lambda: defaultdict(list))     # event -> team -> [(opp, home)]
        for m in self.c["team_matches"]:
            self.pairings[m["event"]][m["team"]].append((m["opponent"], m["was_home"]))
        self.actual = defaultdict(dict)                             # event -> pid -> (pts, minutes)
        for r in self.c["rows"]:
            self.actual[r["event"]][r["player_id"]] = (float(r["pts"] or 0), float(r["minutes"] or 0))
        self.price = defaultdict(dict)                              # round -> pid -> tenths
        for rnd, rows in self.hist["raw"].items():
            for r in rows:
                self.price[rnd].setdefault(int(r["element"]), int(round(H._num(r["value"]))))
        self._fc = {}

    def forecasts(self, t):
        """{u: {pid: xP}} for u = t..last at origin t, from rounds < t."""
        if t in self._fc:
            return self._fc[t]
        c_t = BT.canonical_at(self.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c_t, t - 1), gws_played=t - 1)
        out = {}
        for u in range(t, self.last + 1):
            out[u] = {}
            for pid, p in inp["players"].items():
                if p["mins_last4"] < GATE_MINS:
                    continue
                fx = self.pairings[u].get(p["team"], [])
                v = E.project_reliability(pid, inp, fx) if fx else None
                if v:
                    out[u][pid] = v
        self._fc[t] = (out, {pid: p["pos"] for pid, p in inp["players"].items()})
        return self._fc[t]

    def price_at(self, pid, t):
        for rnd in range(t, 0, -1):
            if pid in self.price.get(rnd, {}):
                return self.price[rnd][pid]
        return None

    def squad_rows(self, squad, t):
        rows = []
        for p in squad:
            now = self.price_at(p["id"], t)
            now = p["price"] if now is None else now
            rows.append({"id": p["id"], "name": str(p["id"]), "team": PIT.club_at(self.cm, p["id"], t) or p["team"],
                         "pos": p["pos"], "price": now / 10, "selling": E.selling_price(p["price"], now) / 10,
                         "status": "a"})
        return rows

    def budget(self, squad, t):
        bank = (BUDGET_TENTHS - sum(p["price"] for p in squad)) / 10
        return bank + sum(r["selling"] for r in self.squad_rows(squad, t))

    def values(self, squad, t):
        """(v_bb, v_fh, detail) for weeks t..19 from the origin-t forecasts."""
        fc, pos_of = self.forecasts(t)
        rows = self.squad_rows(squad, t)
        budget = self.budget(squad, t)
        v_bb, v_fh, detail = {}, {}, {}
        for u in range(t, self.last + 1):
            pts = fc[u]
            xi, outfield, gk = xi_and_bench(rows, pts)
            v_bb[u] = bench_boost_value(outfield, gk)
            market = []
            for pid, v in pts.items():
                price = self.price_at(pid, t)
                if price is None:
                    continue
                club = PIT.club_at(self.cm, pid, t)
                market.append({"id": pid, "name": str(pid), "team": club, "pos": pos_of[pid],
                               "price": price / 10, "status": "a", "pts": v})
            fodder = []
            for pid, price in self.price.get(t, {}).items():
                club = PIT.club_at(self.cm, pid, t)
                if club is None:
                    continue
                fodder.append({"id": pid, "name": str(pid), "team": club, "pos": self.c["players"][pid]["pos"],
                               "price": price / 10, "status": "a", "pts": pts.get(pid, 0.0)})
            v, fh, _ = free_hit_value(market, fodder, budget, rows, pts)
            v_fh[u] = v
            detail[u] = {"xi": xi, "bench": outfield, "gk": gk, "fh": fh, "bench_sum": sum(r["proj"] for r in outfield) + gk["proj"]}
        return v_bb, v_fh, detail

    def realised_xi(self, xi_rows, t):
        """Realised points of an XI with its captain (highest forecast) doubled."""
        cap = max(xi_rows, key=lambda r: (r.get("proj", r.get("pts", 0.0)), -r["id"]))
        return sum(self.actual[t].get(r["id"], (0.0, 0.0))[0] for r in xi_rows) + self.actual[t].get(cap["id"], (0.0, 0.0))[0]

    def bb_gain(self, detail_t, t):
        """Realised bench points minus the automatic substitutions that would
        have come on without the chip (fpl_edge.rule_autosubs on realised
        minutes, bench in forecast order)."""
        xi, bench, gk = detail_t["xi"], detail_t["bench"], detail_t["gk"]
        rows = []
        for slot, r in enumerate(xi, 1):
            rows.append({"slot": slot, "pos": r["pos"], "id": r["id"], "minutes": self.actual[t].get(r["id"], (0, 0))[1]})
        for slot, r in enumerate([gk] + list(bench), 12):
            rows.append({"slot": slot, "pos": r["pos"], "id": r["id"], "minutes": self.actual[t].get(r["id"], (0, 0))[1]})
        autosub = sum(self.actual[t].get(cand["id"], (0.0, 0.0))[0] for cand, _ in E.rule_autosubs(rows))
        bench_pts = sum(self.actual[t].get(r["id"], (0.0, 0.0))[0] for r in [gk] + list(bench))
        return bench_pts - autosub

    def fh_gain(self, detail_t, t):
        if detail_t["fh"] is None:
            return 0.0
        return self.realised_xi(detail_t["fh"]["xi"], t) - self.realised_xi(detail_t["xi"], t)


def heuristic_action(t, chips, v_bench_sum, v_gap, last=LAST_GW):
    """BB when the forecast bench xP at t is the highest of the remaining
    weeks; else FH when the forecast gap at t is the highest, t != last."""
    if "BB" in chips and v_bench_sum[t] >= max(v_bench_sum[u] for u in v_bench_sum if u >= t):
        return "PLAY BB"
    if "FH" in chips and t != last:
        gaps = {u: g for u, g in v_gap.items() if u >= t and g is not None}
        if gaps and v_gap.get(t) is not None and v_gap[t] >= max(gaps.values()):
            return "PLAY FH"
    return "HOLD"


def replay(hist_dir, n_squads=N_SQUADS, seed=SQUAD_SEED, out=print, boot_seed=SEED, first=REPLAY_FIRST,
           last=LAST_GW):
    rp = Replay(hist_dir, last)
    if rp.through < last:
        raise MissingInput(f"the season copy ends at GW{rp.through}, before GW{last}")
    squads = sample_squads(gw1_candidates(rp.hist), n_squads, seed)
    out(f"REPLAY 2025/26 GW{first}-{last}: {len(squads)} synthetic squads from GW1 ownership (seed {seed}), "
        f"held fixed; point-in-time bottomup forecasts (S4 harness, clubs from hist_pit); chips BB and FH")
    results = []
    for si, squad in enumerate(squads):
        policies = {name: {"chips": set(CHIPS), "pts": 0.0, "played": {}, "split": {"BB": 0.0, "FH": 0.0}}
                    for name in ("calculator", "heuristic", "early", "late", "bb_first_fh_heur")}
        for t in range(first, last + 1):
            v_bb, v_fh, detail = rp.values(squad, t)
            bench_sum = {u: detail[u]["bench_sum"] for u in detail}
            acts = {}
            P = policies["calculator"]
            acts["calculator"] = induction(v_bb, v_fh, t, last, frozenset(P["chips"]))["next"] if P["chips"] else "HOLD"
            P = policies["heuristic"]
            acts["heuristic"] = heuristic_action(t, P["chips"], bench_sum, v_fh, last)
            P = policies["early"]
            acts["early"] = "PLAY BB" if "BB" in P["chips"] else ("PLAY FH" if "FH" in P["chips"] and t != last else "HOLD")
            P = policies["late"]                      # both-late: FH in the week before the last, BB in the last
            acts["late"] = ("PLAY FH" if t == last - 1 and "FH" in P["chips"]
                            else "PLAY BB" if t == last and "BB" in P["chips"] else "HOLD")
            P = policies["bb_first_fh_heur"]          # BB in the first week, FH by the heuristic
            acts["bb_first_fh_heur"] = ("PLAY BB" if t == first and "BB" in P["chips"]
                                        else heuristic_action(t, P["chips"] & {"FH"}, bench_sum, v_fh, last))
            for name, act in acts.items():
                P = policies[name]
                if act == "PLAY BB" and "BB" in P["chips"]:
                    g = rp.bb_gain(detail[t], t)
                    P["chips"].discard("BB"); P["pts"] += g; P["played"]["BB"] = t; P["split"]["BB"] = g
                elif act == "PLAY FH" and "FH" in P["chips"] and t != last:
                    g = rp.fh_gain(detail[t], t)
                    P["chips"].discard("FH"); P["pts"] += g; P["played"]["FH"] = t; P["split"]["FH"] = g
        results.append({k: (v["pts"], dict(v["played"]), dict(v["split"])) for k, v in policies.items()})
    calc = [r["calculator"][0] for r in results]
    heur = [r["heuristic"][0] for r in results]
    early = [r["early"][0] for r in results]
    diff = [a - b for a, b in zip(calc, heur)]
    diff_e = [a - b for a, b in zip(calc, early)]
    b1 = BT.bootstrap_mean(diff, seed=boot_seed)
    b2 = BT.bootstrap_mean(diff_e, seed=boot_seed)
    out(f"  realised chip points per squad (mean): calculator {sum(calc) / len(calc):.2f}, "
        f"heuristic {sum(heur) / len(heur):.2f}, both-early {sum(early) / len(early):.2f}")
    out(f"  paired gain calculator - heuristic: mean {b1['mean']:+.2f}, 90% CI [{b1['lo']:+.2f}, {b1['hi']:+.2f}] "
        f"(bootstrap over {b1['n']} squads, B={BT.B}, seed {boot_seed})")
    ok = b1["mean"] >= 0 and b1["lo"] > PASS_LOWER
    out(f"  pre-registered bar: mean >= 0 and CI lower bound > {PASS_LOWER:g}: {'PASS' if ok else 'FAIL'}")
    out(f"  information only - calculator - both-early: mean {b2['mean']:+.2f}, 90% CI [{b2['lo']:+.2f}, {b2['hi']:+.2f}]")
    for name in ("calculator", "heuristic", "early"):
        bb = Counter(r[name][1].get("BB") for r in results)
        fh = Counter(r[name][1].get("FH") for r in results)
        sb = sum(r[name][2]["BB"] for r in results) / len(results)
        sf = sum(r[name][2]["FH"] for r in results) / len(results)
        out(f"  {name:<10} mean BB gain {sb:+.2f}, mean FH gain {sf:+.2f};  BB weeks "
            f"{dict(sorted(bb.items(), key=lambda kv: (kv[0] is None, kv[0])))}  "
            f"FH weeks {dict(sorted(fh.items(), key=lambda kv: (kv[0] is None, kv[0])))}")
    # RULING S7 result, point 3: two more comparators, information only, same squads
    out(f"  information only (RULING S7 result point 3), same replay, seed and squads:")
    extra = {}
    for name, label in (("late", f"both-late (FH GW{last - 1}, BB GW{last})"),
                        ("bb_first_fh_heur", f"BB GW{first} + FH by the heuristic")):
        pts = [r[name][0] for r in results]
        d_calc = BT.bootstrap_mean([a - b for a, b in zip(calc, pts)], seed=boot_seed)
        d_heur = BT.bootstrap_mean([a - b for a, b in zip(heur, pts)], seed=boot_seed)
        sb = sum(r[name][2]["BB"] for r in results) / len(results)
        sf = sum(r[name][2]["FH"] for r in results) / len(results)
        out(f"  {label}: mean {sum(pts) / len(pts):.2f} per squad (BB {sb:+.2f}, FH {sf:+.2f}); "
            f"calculator - it {d_calc['mean']:+.2f} [{d_calc['lo']:+.2f}, {d_calc['hi']:+.2f}]; "
            f"heuristic - it {d_heur['mean']:+.2f} [{d_heur['lo']:+.2f}, {d_heur['hi']:+.2f}]")
        extra[name] = {"mean": sum(pts) / len(pts), "vs_calc": d_calc, "vs_heur": d_heur}
    return {"results": results, "boot": b1, "boot_early": b2, "pass": ok, "extra": extra}


def main(argv=None):
    utf8_console()                       # RULING S5 amendment fix: never stop on a console code page
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--squads", type=int, default=N_SQUADS)
    ap.add_argument("--resamples", type=int, default=RESAMPLES)
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    run = Run("tools/chips.py", args.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        if args.replay:
            replay(args.hist, n_squads=args.squads, out=out)
            name = "chips_replay_2025-26.txt"
        else:
            live(args.data, out=out, resamples=args.resamples)
            name = "chips_live.txt"
    except MissingInput as e:
        print(f"MISSING INPUT: {e} - stopping; nothing is substituted")
        return 2
    path = os.path.join(args.out, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    run.wrote(path)
    run.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
