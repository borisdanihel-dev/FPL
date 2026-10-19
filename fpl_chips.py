"""fpl_chips.py - the runner's copy of tools/chips.py, the part that
the CHIPS and LEAGUE report sections need (W2 piece c; prereg/W2.md acceptance 1).

Every definition below is copied verbatim from tools/chips.py by its syntax
tree, so the runner never imports tools/; tests/test_W2.py holds the
sections byte-identical to the tools' output. Standard library only.
"""
import fpl_bt as BT
import fpl_edge as E
import glob
import gzip
import json
import os
import random
import sqlite3
from collections import Counter, defaultdict


BENCH_W = (0.30, 0.10, 0.03)      # outfield bench, in forecast order


SUBGK_W = 0.03


LAST_GW = 19                      # both first-half chips are worth 0 after it


CHIPS = ("BB", "FH")


CHIP_API = {"bboost": "BB", "freehit": "FH"}


RESAMPLES = 1000


SEED = BT.SEED


CLUB_MAX = 3


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


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
