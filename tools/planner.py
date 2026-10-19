"""
tools/planner.py - the rolling-horizon transfer planner (BUILD_PLAN.md Step 8,
item S8, offline). Standard library only; the nightly never imports it.

    python tools/planner.py                 # live: the top 5 plans for the next gameweek -> tools/out/planner_live.txt
    python tools/planner.py --replay        # the pre-registered 2025/26 replay (50 synthetic squads, seed 7)

Definitions, as pre-registered in prereg/S8.md:
  xP          own: the recorded row for the next gameweek, fpl_edge.project() on each later
              fixture-known gameweek (as S7); a blank or gated-out player scores 0
  pool        the top 25 per position by decayed six-week xP (sum of 0.85^t xP_t), outside our 15
  candidates  0 transfers; every single swap (out, in) at the same position; every pair of swaps -
              exhaustive over the pool - within the selling budget (bank + selling prices), the club
              cap of 3 and the 2 GK+DEF per club cap; the best legal XI and captain re-optimised per
              gameweek (captain = the highest xP in the XI, doubled)
  score       sum_{t=0..5} decay^t dxP_t - 4 x hits - lost banked-FT value, dxP_t = candidate XI+C xP
              minus the current 15's XI+C xP in gameweek t; the FT stock value V(k) = sum of the
              schedule's first k values (Boris 1.5/1.0/0.6/0.3; solver 2.1/1.8/1.5/1.1; a fifth is 0);
              lost = V(min(5, k+1)) - V(k'), k' the stock after the plan; rolling at k = 5 is not allowed
  hit         only if the decayed gain >= 5.5, not resting on one fixture (the gain without its
              largest single-gameweek term stays > 0), and every incoming P(start) >= 0.8
  robustness  the choice re-run at decay 0.80 and 0.90; a flag where it differs
  price line  "price predictor: no source" - never invented
  replay      2025/26 GW2-38, S7's 50 squads (seed 7), 1 FT a week, bank to 5, no chips; forecasts
              project_reliability point-in-time with clubs of the origin (hist_pit); XI and captain by
              forecast, autosubs by fpl_edge.rule_autosubs, hits -4; primary decay 0.85, Boris's
              schedule, buffer 1.5; baseline = the best one-week move with the FT when its gain > 0,
              else roll, never a hit; pass: mean gain >= +10 season points per squad net of hits with
              the 90% bootstrap lower bound > 0 (B = 10,000, seed 20261018, unit = squad)
"""

import argparse
import itertools
import math
import os
import random
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import hist_pit as PIT                                            # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402

DECAY = 0.85
DECAYS_CHECK = (0.80, 0.90)
HORIZON = 6
POOL = 25
HIT = 4.0
HIT_BUFFER = 1.5
HIT_MIN_GAIN = HIT + HIT_BUFFER
EXPLORATORY = (("no hits", {"hits_allowed": False}), ("hit buffer 3.0", {"buffer": 3.0}))   # RULING morning 19 Oct item 2
HIT_MIN_PSTART = 0.8
MAX_FT = 5
CLUB_MAX = 3
GKDEF_CLUB_MAX = 2
SCHEDULES = {"boris": (1.5, 1.0, 0.6, 0.3), "solver": (2.1, 1.8, 1.5, 1.1)}
FORMATIONS = [(d, m, 10 - d - m) for d in (3, 4, 5) for m in (2, 3, 4, 5) if 1 <= 10 - d - m <= 3]
SEED = BT.SEED
PASS_GAIN = 10.0
REPLAY_FIRST, REPLAY_LAST = 2, 38
TOP_PLANS = 5


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# the XI value of a 15, fast: sorted projections per position, formations
# ---------------------------------------------------------------------------

def xi_value(by_pos):
    """by_pos: {pos: sorted descending list of xP of the 15's players at that
    position}. The best legal XI's xP plus the captain (the highest xP in
    the XI: every formation takes the top of each position, so it is the
    highest top). None when no legal XI exists."""
    gk = by_pos.get(1, [])
    if not gk:
        return None
    best = None
    pre = {p: [0.0] for p in (2, 3, 4)}
    for p in (2, 3, 4):
        acc = 0.0
        for v in by_pos.get(p, []):
            acc += v
            pre[p].append(acc)
    for d, m, f in FORMATIONS:
        if len(by_pos.get(2, [])) < d or len(by_pos.get(3, [])) < m or len(by_pos.get(4, [])) < f:
            continue
        v = gk[0] + pre[2][d] + pre[3][m] + pre[4][f]
        if best is None or v > best:
            best = v
    if best is None:
        return None
    cap = max(gk[0], max((by_pos[p][0] for p in (2, 3, 4) if by_pos.get(p)), default=0.0))
    return best + cap


def squad_by_pos(squad, xp):
    out = defaultdict(list)
    for r in squad:
        out[r["pos"]].append(xp.get(r["id"], 0.0))
    for p in out:
        out[p].sort(reverse=True)
    return out


def stock_value(schedule, k):
    return sum(schedule[:max(0, min(k, len(schedule)))])


def lost_ft_value(schedule, k, used):
    """The banked-FT value a plan gives up against rolling: V(min(5, k+1)) -
    V(k'), k' = the stock after the plan (1 when the plan uses more than it
    has)."""
    after = max(k - used, 0) + 1
    after = min(MAX_FT, after)
    return stock_value(schedule, min(MAX_FT, k + 1)) - stock_value(schedule, after)


# ---------------------------------------------------------------------------
# candidates
# ---------------------------------------------------------------------------

def legal(squad_rows, bank):
    """Budget (cost of the incoming players against bank + selling prices
    of the outgoing), club cap 3, and 2 GK+DEF per club."""
    if bank < -1e-9:
        return False
    clubs = Counter(r["team"] for r in squad_rows)
    if clubs and max(clubs.values()) > CLUB_MAX:
        return False
    gkdef = Counter(r["team"] for r in squad_rows if r["pos"] in (1, 2))
    return not gkdef or max(gkdef.values()) <= GKDEF_CLUB_MAX


def decayed(xp_weeks, pid, decay):
    return sum(decay ** t * xp_weeks[t].get(pid, 0.0) for t in range(len(xp_weeks)))


def build_pool(market, squad_ids, xp_weeks, decay=DECAY, n=POOL):
    """The top `n` per position by decayed xP among `market` rows
    ({id, name, team, pos, price, p_start}) outside our 15."""
    pool = defaultdict(list)
    for r in market:
        if r["id"] in squad_ids:
            continue
        pool[r["pos"]].append((decayed(xp_weeks, r["id"], decay), r))
    return {p: [r for _, r in sorted(v, key=lambda x: (-x[0], x[1]["id"]))[:n]] for p, v in pool.items()}


def plan_candidates(squad, bank, pool):
    """Every 0-, 1- and 2-transfer plan over the pool, legal ones only:
    [(outs, ins)] with outs/ins lists of rows. Exhaustive."""
    singles = []
    for out in squad:
        for inc in pool.get(out["pos"], []):
            singles.append((out, inc))
    plans = [((), ())]
    for out, inc in singles:
        rows = [r for r in squad if r["id"] != out["id"]] + [inc]
        if legal(rows, bank + out["selling"] - inc["price"]):
            plans.append(((out,), (inc,)))
    seen = set()
    for (o1, i1), (o2, i2) in itertools.combinations(singles, 2):
        if o1["id"] == o2["id"] or i1["id"] == i2["id"]:
            continue
        key = (tuple(sorted((o1["id"], o2["id"]))), tuple(sorted((i1["id"], i2["id"]))))
        if key in seen:
            continue                                  # the same 15 reached by swapping the pairing: once
        seen.add(key)
        rows = [r for r in squad if r["id"] not in (o1["id"], o2["id"])] + [i1, i2]
        if legal(rows, bank + o1["selling"] + o2["selling"] - i1["price"] - i2["price"]):
            plans.append(((o1, o2), (i1, i2)))
    return plans


def evaluate(plan, squad, xp_weeks, decay, schedule, k_banked, p_start, hits_allowed=True, buffer=HIT_BUFFER):
    """The plan's score and its parts. None when the plan is not allowed
    (a hit outside the rule, or rolling at the cap). `hits_allowed` False
    and `buffer` are the exploratory variants of RULING morning 19 Oct item
    2 (no hits; the hit buffer at 3.0): no bar, no adoption."""
    outs, ins = plan
    used = len(outs)
    if used == 0 and k_banked >= MAX_FT:
        return None
    rows = [r for r in squad if r["id"] not in {o["id"] for o in outs}] + list(ins)
    base_rows = squad
    gains = []
    for t, xp in enumerate(xp_weeks):
        v_new = xi_value(squad_by_pos(rows, xp))
        v_old = xi_value(squad_by_pos(base_rows, xp))
        if v_new is None or v_old is None:
            return None
        gains.append(v_new - v_old)
    decayed_gain = sum(decay ** t * g for t, g in enumerate(gains))
    hits = max(0, used - k_banked)
    if hits:
        if not hits_allowed:
            return None
        largest = max(decay ** t * g for t, g in enumerate(gains))
        if decayed_gain < HIT + buffer or decayed_gain - largest <= 0:
            return None
        if any(p_start.get(i["id"], 0.0) < HIT_MIN_PSTART for i in ins):
            return None
    lost = lost_ft_value(schedule, k_banked, used)
    score = decayed_gain - HIT * hits - lost
    return {"score": score, "gain": decayed_gain, "gains": gains, "hits": hits, "lost": lost, "used": used,
            "outs": outs, "ins": ins}


def rank_plans(squad, bank, market, xp_weeks, k_banked, p_start, decay=DECAY, schedule=SCHEDULES["boris"], pool=None,
               hits_allowed=True, buffer=HIT_BUFFER):
    pool = pool or build_pool(market, {r["id"] for r in squad}, xp_weeks, decay)
    scored = []
    for plan in plan_candidates(squad, bank, pool):
        ev = evaluate(plan, squad, xp_weeks, decay, schedule, k_banked, p_start, hits_allowed, buffer)
        if ev is not None:
            scored.append(ev)
    scored.sort(key=lambda e: (-e["score"], e["used"], tuple(sorted(i["id"] for i in e["ins"]))))
    return scored, pool


def plan_key(ev):
    return (tuple(sorted(o["id"] for o in ev["outs"])), tuple(sorted(i["id"] for i in ev["ins"])))


# ---------------------------------------------------------------------------
# live
# ---------------------------------------------------------------------------

def live(data_dir, out=print):
    d, path = CH.newest_export(data_dir)
    log_rows = E.read_log(os.path.join(data_dir, E.LOG_PATH))
    weeks, pts, src = CH.own_week_points(d, log_rows)
    if not weeks:
        raise MissingInput("the export has no upcoming fixtures")
    xp_weeks = [pts[w] for w in weeks[:HORIZON]]
    squad = CH.my_squad(d)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise MissingInput(f"no budget: {why}")
    bank = budget - sum(r["selling"] for r in squad)
    k = E.estimate_free_transfers(d)
    target = weeks[0]
    d_ev = {"events": d.get("events") or []}
    p_start = {int(r["player_id"]): float(r["predicted"]) for r in E.forecasts(log_rows, d_ev)
               if r["source"] == "minutes" and int(r["event"]) == target}
    market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
               "status": p["status"]} for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    out(f"TRANSFER PLANNER  export {os.path.basename(path)}, next GW{target}, horizon GW{weeks[0]}-{weeks[-1]}; "
        f"bank £{bank:.1f}m, free transfers {k} (estimated from the transfer log; confirm in the app); xP = own; "
        f"pool = top {POOL} per position by decayed xP; information only")
    out("  price predictor: no source")
    results = {}
    for decay in (DECAY,) + DECAYS_CHECK:
        for name, schedule in SCHEDULES.items():
            scored, pool = rank_plans(squad, bank, market, xp_weeks, k, p_start, decay, schedule)
            results[(decay, name)] = scored
    for name, schedule in SCHEDULES.items():
        scored = results[(DECAY, name)]
        out("")
        out(f"  TOP {TOP_PLANS} PLANS  decay {DECAY}, schedule {name} {schedule}: score = decayed gain - 4 x hits - lost FT value")
        out(f"  {'#':>2} {'score':>7} {'gain':>7} {'hits':>5} {'lostFT':>7}  {'weekly dxP':<36} plan")
        for i, ev in enumerate(scored[:TOP_PLANS], 1):
            plan = "roll" if not ev["outs"] else "; ".join(f"{o['name']} -> {n['name']} ({n['team']}, £{n['price']:.1f}m)" for o, n in zip(ev["outs"], ev["ins"]))
            weekly = " ".join(f"{g:+5.1f}" for g in ev["gains"])
            flags = []
            for dc in DECAYS_CHECK:
                alt = results[(dc, name)]
                if alt and plan_key(alt[0]) != plan_key(scored[0]) and i == 1:
                    flags.append(f"decay {dc} prefers "
                                 + ("roll" if not alt[0]["outs"] else "; ".join(f"{o['name']} -> {n['name']}" for o, n in zip(alt[0]["outs"], alt[0]["ins"]))))
            out(f"  {i:>2} {ev['score']:7.2f} {ev['gain']:7.2f} {ev['hits']:5d} {ev['lost']:7.2f}  {weekly:<36} {plan}"
                + (f"   [{'; '.join(flags)}]" if flags else ""))
    # exploratory lines (RULING morning 19 Oct item 2): the same ranking with no hits, and with the buffer at 3.0
    out("")
    for label, kw in EXPLORATORY:
        scored, _ = rank_plans(squad, bank, market, xp_weeks, k, p_start, DECAY, SCHEDULES["boris"], **kw)
        results[(label, "boris")] = scored
        ev = scored[0] if scored else None
        plan = "none" if ev is None else ("roll" if not ev["outs"] else "; ".join(f"{o['name']} -> {n['name']}" for o, n in zip(ev["outs"], ev["ins"])))
        out(f"  exploratory, {label} (Boris's schedule, no bar): top plan {plan}" + (f"  score {ev['score']:.2f}, gain {ev['gain']:.2f}, hits {ev['hits']}" if ev else ""))
    return results


# ---------------------------------------------------------------------------
# the replay (pre-registered test)
# ---------------------------------------------------------------------------

class Replay:
    """2025/26 on the S7 machinery: forecasts at origin t for weeks t..t+5
    from rounds < t, clubs and prices of the origin."""

    def __init__(self, hist_dir):
        self.rp = CH.Replay(hist_dir, last=REPLAY_LAST)
        self.c, self.cm = self.rp.c, self.rp.cm
        self.through = self.rp.through
        self._fc = {}

    def forecasts(self, t):
        """{u: {pid: xP}} for u = t..min(t+5, 38) at origin t; and p_start, pos."""
        if t in self._fc:
            return self._fc[t]
        c_t = BT.canonical_at(self.rp.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c_t, t - 1), gws_played=t - 1)
        out = {}
        for u in range(t, min(t + HORIZON - 1, REPLAY_LAST) + 1):
            out[u] = {}
            for pid, p in inp["players"].items():
                if p["mins_last4"] < 45:
                    continue
                fx = self.rp.pairings[u].get(p["team"], [])
                v = E.project_reliability(pid, inp, fx) if fx else None
                if v:
                    out[u][pid] = v
        self._fc[t] = (out, {pid: p["p_start"] for pid, p in inp["players"].items()},
                       {pid: p["pos"] for pid, p in inp["players"].items()})
        return self._fc[t]

    def market(self, t, pos_of):
        rows = []
        for pid, price in self.rp.price.get(t, {}).items():
            club = PIT.club_at(self.cm, pid, t)
            if club is None:
                continue
            rows.append({"id": pid, "name": str(pid), "team": club, "pos": pos_of.get(pid) or self.c["players"][pid]["pos"],
                         "price": price / 10, "status": "a"})
        return rows

    def squad_rows(self, squad, t):
        return self.rp.squad_rows(squad, t)

    def realised(self, rows, t, xp):
        """Realised points of the week: the XI by forecast with the captain
        doubled, automatic substitutions by rule_autosubs on realised
        minutes (bench in forecast order)."""
        proj = {r["id"]: xp.get(r["id"], 0.0) for r in rows}
        xi, bench, gk = CH.xi_and_bench([dict(r) for r in rows], proj)
        actual = self.rp.actual[t]
        lineup = []
        for slot, r in enumerate(xi, 1):
            lineup.append({"slot": slot, "pos": r["pos"], "id": r["id"], "minutes": actual.get(r["id"], (0, 0))[1]})
        for slot, r in enumerate([gk] + list(bench), 12):
            lineup.append({"slot": slot, "pos": r["pos"], "id": r["id"], "minutes": actual.get(r["id"], (0, 0))[1]})
        pts = sum(actual.get(r["id"], (0.0, 0))[0] for r in xi)
        for cand, out in E.rule_autosubs(lineup):
            pts += actual.get(cand["id"], (0.0, 0))[0] - actual.get(out["id"], (0.0, 0))[0]
        cap = max(xi, key=lambda r: (r["proj"], -r["id"]))
        pts += actual.get(cap["id"], (0.0, 0))[0]
        return pts


def baseline_plan(squad, bank, pool, xp_now, k_banked):
    """The best one-week move with a free transfer when its gain > 0, else
    roll; never a hit."""
    if k_banked < 1:
        return ((), ())
    base = xi_value(squad_by_pos(squad, xp_now))
    best, best_gain = ((), ()), 0.0
    for out in squad:
        for inc in pool.get(out["pos"], []):
            rows = [r for r in squad if r["id"] != out["id"]] + [inc]
            if not legal(rows, bank + out["selling"] - inc["price"]):
                continue
            v = xi_value(squad_by_pos(rows, xp_now))
            if v is not None and v - base > best_gain:
                best, best_gain = ((out,), (inc,)), v - base
    return best


def replay(hist_dir, n_squads=50, seed=CH.SQUAD_SEED, out=print, decay=DECAY, schedule_name="boris",
           boot_seed=SEED, first=REPLAY_FIRST, last=REPLAY_LAST, check_decays=True, hits_allowed=True, buffer=HIT_BUFFER):
    rp = Replay(hist_dir)
    if rp.through < last:
        raise MissingInput(f"the season copy ends at GW{rp.through}, before GW{last}")
    schedule = SCHEDULES[schedule_name]
    squads = CH.sample_squads(CH.gw1_candidates(rp.rp.hist), n_squads, seed)
    out(f"REPLAY 2025/26 GW{first}-{last}: {len(squads)} synthetic squads (seed {seed}), 1 FT a week, bank to {MAX_FT}, no chips; "
        f"planner decay {decay}, schedule {schedule_name} {schedule}, " + ("no hits" if not hits_allowed else f"hit buffer {buffer}")
        + "; baseline = best one-week move or roll, never a hit"
        + ("" if (hits_allowed and buffer == HIT_BUFFER) else "; EXPLORATORY (RULING morning 19 Oct item 2): no bar, no adoption"))
    pre_registered = hits_allowed and buffer == HIT_BUFFER
    results = []
    for si, squad0 in enumerate(squads):
        state = {}
        for name in ("planner", "baseline"):
            state[name] = {"squad": [dict(p) for p in squad0], "bank": (CH.BUDGET_TENTHS - sum(p["price"] for p in squad0)) / 10,
                           "k": 1, "pts": 0.0, "hits": 0, "transfers": 0, "disagree": 0}
        for t in range(first, last + 1):
            fc, p_start, pos_of = rp.forecasts(t)
            weeks = sorted(fc)
            xp_weeks = [fc[u] for u in weeks]
            market = rp.market(t, pos_of)
            for name, st in state.items():
                rows = rp.squad_rows(st["squad"], t)
                pool = build_pool(market, {r["id"] for r in rows}, xp_weeks, decay)
                if name == "planner":
                    scored, _ = rank_plans(rows, st["bank"], market, xp_weeks, st["k"], p_start, decay, schedule, pool, hits_allowed, buffer)
                    plan = (scored[0]["outs"], scored[0]["ins"]) if scored else ((), ())
                    if check_decays and si < 5:
                        for dc in DECAYS_CHECK:
                            alt, _ = rank_plans(rows, st["bank"], market, xp_weeks, st["k"], p_start, dc, schedule, pool, hits_allowed, buffer)
                            if alt and scored and plan_key(alt[0]) != plan_key(scored[0]):
                                st["disagree"] += 1
                else:
                    plan = baseline_plan(rows, st["bank"], pool, xp_weeks[0], st["k"])
                outs, ins = plan
                used = len(outs)
                hits = max(0, used - st["k"])
                # apply: the new 15 keeps GW1 buy prices for continuing players; incoming at the origin price
                keep = [p for p in st["squad"] if p["id"] not in {o["id"] for o in outs}]
                for o, i in zip(outs, ins):
                    keep.append({"id": i["id"], "pos": i["pos"], "team": i["team"], "price": int(round(i["price"] * 10)), "selected": 0})
                st["bank"] = st["bank"] + sum(o["selling"] for o in outs) - sum(i["price"] for i in ins)
                st["squad"] = keep
                st["k"] = min(MAX_FT, max(st["k"] - used, 0) + 1)
                st["hits"] += hits
                st["transfers"] += used
                rows_after = rp.squad_rows(st["squad"], t)
                st["pts"] += rp.realised(rows_after, t, xp_weeks[0]) - HIT * hits
        results.append({name: dict(pts=st["pts"], hits=st["hits"], transfers=st["transfers"], disagree=st["disagree"])
                        for name, st in state.items()})
    gains = [r["planner"]["pts"] - r["baseline"]["pts"] for r in results]
    b = BT.bootstrap_mean(gains, seed=boot_seed)
    ok = b["mean"] >= PASS_GAIN and b["lo"] > 0
    out(f"  season points per squad net of hits (mean): planner {sum(r['planner']['pts'] for r in results) / len(results):.1f} "
        f"(hits {sum(r['planner']['hits'] for r in results) / len(results):.1f}, transfers {sum(r['planner']['transfers'] for r in results) / len(results):.1f}), "
        f"baseline {sum(r['baseline']['pts'] for r in results) / len(results):.1f} (transfers {sum(r['baseline']['transfers'] for r in results) / len(results):.1f})")
    out(f"  paired gain planner - baseline: mean {b['mean']:+.2f}, 90% CI [{b['lo']:+.2f}, {b['hi']:+.2f}] (bootstrap over {b['n']} squads, B={BT.B}, seed {boot_seed})")
    if pre_registered:
        out(f"  pre-registered bar: mean >= +{PASS_GAIN:g} and CI lower bound > 0: {'PASS' if ok else 'FAIL'}")
    else:
        out("  exploratory line: no bar, no adoption")
    if check_decays:
        dis = [r["planner"]["disagree"] for r in results[:5]]
        out(f"  robustness (first 5 squads): weeks where decay 0.80 or 0.90 chose a different plan: {dis} of {last - first + 1} each")
    return {"results": results, "boot": b, "pass": ok if pre_registered else None}


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--squads", type=int, default=50)
    ap.add_argument("--schedule", default="boris", choices=tuple(SCHEDULES))
    ap.add_argument("--decay", type=float, default=DECAY)
    ap.add_argument("--no-hits", action="store_true", help="exploratory: the planner never takes a hit")
    ap.add_argument("--buffer", type=float, default=HIT_BUFFER, help="exploratory: the hit buffer (pre-registered 1.5)")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        if args.replay:
            replay(args.hist, n_squads=args.squads, out=out, decay=args.decay, schedule_name=args.schedule,
                   hits_allowed=not args.no_hits, buffer=args.buffer)
            name = "planner_replay_2025-26.txt" if (args.decay == DECAY and args.schedule == "boris") else f"planner_replay_2025-26_{args.schedule}_{args.decay}.txt"
            if args.no_hits:
                name = name.replace(".txt", "_nohits.txt")                    # the exploratory lines never overwrite the pre-registered file
            elif args.buffer != HIT_BUFFER:
                name = name.replace(".txt", f"_buffer{args.buffer:g}.txt")
        else:
            live(args.data, out)
            name = "planner_live.txt"
    except MissingInput as e:
        print(f"MISSING INPUT: {e} - stopping; nothing is substituted")
        return 2
    with open(os.path.join(args.out, name), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
