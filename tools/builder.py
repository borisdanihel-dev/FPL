"""tools/builder.py - S15, the unified squad builder (BUILD_PLAN.md Step 15;
Part F item F-G; prereg/S15.md). Offline; standard library only; the
nightly never imports it. Accepted (Ruling, Tue 20 Oct, point 2): the
default for Free Hit and Wildcard builds, the cap on live with its cost, the
three-layer rule's squad printed beside it (prereg/S15.md amendment 2); not
used for GW8. --bb stays information.

One objective: the decayed six-week value of a 15, sum over k of
0.85^k x V_k, V_k = the best legal XI by week k's xP (any of the 7
formations) + the captain (the highest XI xP again, any position) + S7's
bench weights (0.30 / 0.10 / 0.03 outfield in forecast order, 0.03 the sub
keeper). Constraints: the budget, the quota 2/5/5/3, 3 per club, and the
2-per-club GK+DEF cap as a toggle whose cost is always reported. The
solver: a greedy start (decayed xP per million) and local search over S8's
pool (25 per position): single swaps by best improvement, then pairs by
first improvement; the A/B also starts from the rule's squad.

The A/B (--test): every gameweek 5-38 of 2025/26 and 2024/25 a hypothetical
wildcard at that gameweek's prices with 100.0; the same xp_v2 matrix for
both sides (S8b's horizon season: week t S5's lambdas, weeks t+1..t+5 the
origin's fallback); the frozen three-layer rule (fpl_edge's
build_three_layer_squad, unchanged, 4-3-3, the quota-proportional split)
on its candidates ported to history (layer 1 and layer 3; the GK/DEF
six-week sum is the shared matrix). Realised points over the window with
rule_autosubs and the captain the highest xp_v2 in the XI.

    python tools/builder.py --test [--hist ROOT] [--out DIR]
    python tools/builder.py --wildcard | --freehit | --bb [--data DIR] [--hist ROOT] [--out DIR]
"""
import argparse
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import planner as PL                                              # noqa: E402
import planner_2425 as P                                          # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2 as XV                                                # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_2425 as F                                            # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

DECAY = 0.85
HORIZON = 6
BUDGET = 100.0
QUOTA = dict(E.FULL_QUOTA)
CLUB_MAX = 3
GKDEF_CLUB_MAX = 2
BENCH_W, SUBGK_W = CH.BENCH_W, CH.SUBGK_W
POOL = PL.POOL
EPS = 1e-9
FIRST, LAST = 5, 38
RULE_FORMATION = (4, 3, 3)
PASS_SHARE = 0.60
SEASONS = (("2025-26", "2024-25"), ("2024-25", "2023-24"))     # (test season, prior season)


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# the objective
# ---------------------------------------------------------------------------

def week_value(squad, xp, bench_full=False, formation=None):
    """(V, XI, formation) of a 15 in one week: the best legal XI by xp (as
    fpl_edge._best_xi; or the given formation), the captain = the highest XI
    xp again, the bench by S7's weights (bench_full: every bench player at
    1.0, a Bench Boost week). A player without xp scores 0."""
    def v(p):
        return xp.get(p["id"], 0.0)
    by = {k: sorted((p for p in squad if p["pos"] == k), key=lambda p: -v(p)) for k in (1, 2, 3, 4)}
    best = None
    for ndef in range(3, 6):
        for nmid in range(2, 6):
            nfwd = 10 - ndef - nmid
            if not 1 <= nfwd <= 3 or (formation is not None and (ndef, nmid, nfwd) != tuple(formation)):
                continue
            xi = by[1][:1] + by[2][:ndef] + by[3][:nmid] + by[4][:nfwd]
            if len(xi) != 11:
                continue
            pts = sum(v(p) for p in xi)
            if best is None or pts > best[0]:
                best = (pts, xi, (ndef, nmid, nfwd))
    if best is None:
        return float("-inf"), [], None
    pts, xi, form = best
    ids = {p["id"] for p in xi}
    rest = [p for p in squad if p["id"] not in ids]
    if bench_full:
        bench = sum(v(p) for p in rest)
    else:
        out = sorted((p for p in rest if p["pos"] != 1), key=lambda p: (-v(p), p["id"]))
        bench = sum(w * v(p) for w, p in zip(BENCH_W, out)) + SUBGK_W * sum(v(p) for p in rest if p["pos"] == 1)
    return pts + max(v(p) for p in xi) + bench, xi, form


def objective(squad, weeks_xp, decay=DECAY, bench_full=False):
    return sum(decay ** k * week_value(squad, xp, bench_full)[0] for k, xp in enumerate(weeks_xp))


def decayed(weeks_xp, pid, decay=DECAY):
    return sum(decay ** k * xp.get(pid, 0.0) for k, xp in enumerate(weeks_xp))


# ---------------------------------------------------------------------------
# constraints, greedy start, local search
# ---------------------------------------------------------------------------

def legal(squad, budget, gkdef_cap):
    """The quota, distinct players, the budget, 3 per club and (if on) 2 GK+DEF per club."""
    if len({p["id"] for p in squad}) != len(squad) or Counter(p["pos"] for p in squad) != Counter(QUOTA):
        return False
    if sum(p["price"] for p in squad) > budget + EPS:
        return False
    if max(Counter(p["team"] for p in squad).values()) > CLUB_MAX:
        return False
    if gkdef_cap and Counter(p["team"] for p in squad if p["pos"] in (1, 2)) and \
            max(Counter(p["team"] for p in squad if p["pos"] in (1, 2)).values()) > GKDEF_CLUB_MAX:
        return False
    return True


def greedy(market, weeks_xp, budget, gkdef_cap, decay=DECAY):
    """The best decayed xP per million into each slot while the cheapest fill
    of the remaining slots still fits, then the cheapest legal fill."""
    dec = {r["id"]: decayed(weeks_xp, r["id"], decay) for r in market}
    order = sorted(market, key=lambda r: (-(dec[r["id"]] / r["price"]) if r["price"] > 0 else 0.0, r["id"]))
    squad, need = [], dict(QUOTA)

    def fits(p):
        if need[p["pos"]] == 0 or any(q["id"] == p["id"] for q in squad):
            return False
        trial = squad + [p]
        if max(Counter(q["team"] for q in trial).values()) > CLUB_MAX:
            return False
        if gkdef_cap and p["pos"] in (1, 2) and \
                sum(1 for q in trial if q["pos"] in (1, 2) and q["team"] == p["team"]) > GKDEF_CLUB_MAX:
            return False
        return True

    def cheapest_rest(after):
        taken, total = {q["id"] for q in after}, 0.0
        left = dict(QUOTA)
        for q in after:
            left[q["pos"]] -= 1
        for pos, n in left.items():
            prices = sorted(r["price"] for r in market if r["pos"] == pos and r["id"] not in taken)
            if len(prices) < n:
                return float("inf")
            total += sum(prices[:n])
        return total

    for r in order:
        if not fits(r):
            continue
        if sum(q["price"] for q in squad) + r["price"] + cheapest_rest(squad + [r]) <= budget + EPS:
            squad.append(r)
            need[r["pos"]] -= 1
    for r in sorted(market, key=lambda r: (r["price"], -dec[r["id"]], r["id"])):
        if sum(need.values()) == 0:
            break
        if fits(r) and sum(q["price"] for q in squad) + r["price"] <= budget + EPS:
            squad.append(r)
            need[r["pos"]] -= 1
    return squad if legal(squad, budget, gkdef_cap) else None


def build_pool(market, weeks_xp, squad_ids, n=POOL, decay=DECAY):
    """S8's pool: the top n per position by decayed six-week xP, outside the 15."""
    by = defaultdict(list)
    for r in market:
        if r["id"] not in squad_ids:
            by[r["pos"]].append(r)
    return {pos: sorted(v, key=lambda r: (-decayed(weeks_xp, r["id"], decay), r["id"]))[:n] for pos, v in by.items()}


def local_search(squad, market, weeks_xp, budget, gkdef_cap, decay=DECAY, bench_full=False, pool_n=POOL):
    """Single swaps by best improvement until none improves; then pairs by
    first improvement in a fixed order, back to singles after one; stops
    when nothing improves by more than EPS. Never worsens."""
    cur = objective(squad, weeks_xp, decay, bench_full)
    while True:
        ids = {p["id"] for p in squad}
        pool = build_pool(market, weeks_xp, ids, pool_n, decay)     # S8's pool: the top n per position outside the 15
        singles = [(o, i) for o in squad for i in pool.get(o["pos"], []) if i["id"] not in ids]
        best = None
        for o, i in singles:
            new = [p for p in squad if p["id"] != o["id"]] + [i]
            if not legal(new, budget, gkdef_cap):
                continue
            val = objective(new, weeks_xp, decay, bench_full)
            if val > cur + EPS and (best is None or val > best[0]):
                best = (val, new)
        if best is not None:
            cur, squad = best
            continue
        moved = False
        for a in range(len(singles)):
            o1, i1 = singles[a]
            for b in range(a + 1, len(singles)):
                o2, i2 = singles[b]
                if o1["id"] == o2["id"] or i1["id"] == i2["id"]:
                    continue
                new = [p for p in squad if p["id"] not in (o1["id"], o2["id"])] + [i1, i2]
                if not legal(new, budget, gkdef_cap):
                    continue
                val = objective(new, weeks_xp, decay, bench_full)
                if val > cur + EPS:
                    cur, squad, moved = val, new, True
                    break
            if moved:
                break
        if not moved:
            return squad, cur


def build(market, weeks_xp, budget, gkdef_cap, starts=(), decay=DECAY, bench_full=False):
    """The builder's 15 and its objective: local search from the greedy start
    and from every given start that is legal under the builder's rules; the
    best end point (ties to the first)."""
    begins = []
    g = greedy(market, weeks_xp, budget, gkdef_cap, decay)
    if g is not None:
        begins.append(g)
    begins += [s for s in starts if s and legal(s, budget, gkdef_cap)]
    if not begins:
        raise MissingInput("no legal 15 within the budget")
    best = None
    for s in begins:
        sq, val = local_search([dict(p) for p in s], market, weeks_xp, budget, gkdef_cap, decay, bench_full)
        if best is None or val > best[1] + EPS:
            best = (sq, val)
    return best


# ---------------------------------------------------------------------------
# the frozen three-layer rule on history
# ---------------------------------------------------------------------------

def rule_candidates(players, inp, pairings, weeks, played, matrix):
    """fpl_edge.wildcard_candidates' layers 1 and 3 on given inputs: players
    [{id, name, team, pos, price, status, mins_last4}] in the export's order,
    the reliability inputs, pairings {week: {team: [fixture, ...]}}, the
    horizon weeks, played {team: matches in the last four gameweeks} and the
    xP matrix {week: {pid: xP}} (the GK/DEF six-week sum). Layer 2's role
    edges never rank or admit (frozen code) and are left out."""
    cands = {1: [], 2: [], 3: [], 4: []}
    excluded = defaultdict(int)
    for p in players:
        if p["status"] != "a":
            excluded["status not 'a'"] += 1
            continue
        if (p.get("mins_last4") or 0) < 45:
            excluded["under 45 min in the last four"] += 1
            continue
        share = E.minutes_share(p, played)
        if share is None or share <= E.FLAG_SHARE_MAX:
            excluded[f"minutes share <= {E.FLAG_SHARE_MAX}"] += 1
            continue
        pid = p["id"]
        nfix = sum(len(pairings.get(w, {}).get(p["team"], ())) for w in weeks)
        if nfix == 0:
            excluded["no fixture in the horizon"] += 1
            continue
        sum6 = sum(matrix.get(w, {}).get(pid, 0.0) for w in weeks if pairings.get(w, {}).get(p["team"]))
        nfix_later = sum(len(pairings.get(w, {}).get(p["team"], ())) for w in weeks[2:])
        ip = inp["players"].get(pid, {})
        p_start, xgi90 = ip.get("p_start", 0.0), ip.get("xgi90") or 0.0
        key = (sum6,) if p["pos"] in (1, 2) else (p_start * nfix, xgi90)
        cands[p["pos"]].append({"id": pid, "name": p["name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
                                "roles": [], "sum6": sum6, "nfix": nfix, "nfix_later": nfix_later, "p_start": p_start,
                                "xgi90": xgi90, "share": share, "key": key, "var": None})
    for pos in cands:
        cands[pos].sort(key=lambda c: c["key"], reverse=True)
        for i, c in enumerate(cands[pos]):
            c["rank"] = i
    return cands, dict(excluded)


def quota_split(budget, quota=None):
    """fpl_edge.budget_split without a current squad: proportional to the quota."""
    quota = quota or QUOTA
    total = sum(quota.values())
    return {k: budget * n / total for k, n in quota.items()}


def rule_squad(cands, budget=BUDGET):
    squad, spent, split = E.build_three_layer_squad(cands, budget, quota_split(budget), RULE_FORMATION, QUOTA)
    return [{"id": c["id"], "team": c["team"], "pos": c["pos"], "price": c["price"]} for c in squad], spent


# ---------------------------------------------------------------------------
# the A/B on 2025/26 and 2024/25
# ---------------------------------------------------------------------------

class Origin:
    """One date of one season: the matrix, the market and the rule's inputs."""

    def __init__(self, season, t):
        self.t = t
        fc, p_start, pos = season.forecasts(t)
        self.weeks = sorted(fc)
        self.weeks_xp = [fc[u] for u in self.weeks]
        self.fc = fc
        self.market = sorted((r for r in season.market(t, pos) if r["pos"] in QUOTA), key=lambda r: r["id"])   # 2024/25's assistant managers (AM, from GW23) are no players
        c = BT.canonical_at(season.hist, t)
        self.inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        window = range((t - 1) - min(4, t - 1) + 1, t)
        mins, pts = defaultdict(float), defaultdict(float)
        for r in c["rows"]:
            if r["event"] in window:
                mins[r["player_id"]] += r["minutes"] or 0
            if r["event"] < t:
                pts[r["player_id"]] += r.get("pts") or 0
        played = Counter()
        for f in season.s5.fixtures.values():
            if f["event"] in window:
                played[f["home"]] += 1
                played[f["away"]] += 1
        self.played = dict(played)
        pairings = {u: {team: list(v) for team, v in season.rp.pairings[u].items()} for u in self.weeks}
        self.pairings = pairings
        self.players = [{"id": r["id"], "name": r["name"], "team": r["team"], "pos": r["pos"], "price": r["price"],
                         "status": "a", "mins_last4": mins.get(r["id"], 0.0)}
                        for r in sorted(self.market, key=lambda r: (r["pos"], -pts.get(r["id"], 0.0), r["id"]))]


def realised(season, squad, origin):
    """Window points of a fixed 15: each week the XI by the origin's matrix,
    the captain doubled, rule_autosubs on realised minutes (S8's realised)."""
    rows = [{"id": p["id"], "pos": p["pos"], "team": p["team"], "name": str(p["id"])} for p in squad]
    return sum(season.realised(rows, u, origin.fc[u]) for u in origin.weeks)


def bench_points(season, squad, origin):
    """Realised points of the four bench players in the window's first week (a Bench Boost there)."""
    t = origin.weeks[0]
    xi = {p["id"] for p in week_value(squad, origin.fc[t])[1]}
    return sum(season.rp.actual[t].get(p["id"], (0.0, 0))[0] for p in squad if p["id"] not in xi)


def one_date(season, t):
    o = Origin(season, t)
    cands, excluded = rule_candidates(o.players, o.inp, o.pairings, o.weeks, o.played, o.fc)
    rsq, rspent = rule_squad(cands)
    r_obj = objective(rsq, o.weeks_xp)
    bsq, b_obj = build(o.market, o.weeks_xp, BUDGET, False, starts=[rsq])
    csq, c_obj = build(o.market, o.weeks_xp, BUDGET, True)
    t_xp = o.fc[o.weeks[0]]
    best_v, _, form = week_value(bsq, t_xp)
    v433 = week_value(bsq, t_xp, formation=RULE_FORMATION)[0]
    return {"gw": t, "rule_proj": r_obj, "builder_proj": b_obj, "cap_proj": c_obj, "rule_spent": rspent,
            "rule": realised(season, rsq, o), "builder": realised(season, bsq, o), "cap": realised(season, csq, o),
            "form": form, "cost_433": best_v - v433, "bench_rule": bench_points(season, rsq, o),
            "bench_builder": bench_points(season, bsq, o), "window": len(o.weeks), "excluded": excluded,
            "rule_ids": sorted(p["id"] for p in rsq), "builder_ids": sorted(p["id"] for p in bsq)}


def season_dates(hist_root, season_name, prior_name, out_csv, first=FIRST, last=LAST, say=lambda s: None):
    """[one_date records] for one season (its own harness and re-score)."""
    hist_dir, prior_dir = os.path.join(hist_root, season_name), os.path.join(hist_root, prior_name)
    odds = F.ODDS if season_name == F.SEASON else OL.odds_path(season_name)
    for p in (odds, os.path.join(prior_dir, "merged_gw.csv"), os.path.join(prior_dir, "teams.csv")):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing")
    if season_name == F.SEASON:
        F.check_no_counts(hist_dir)
        rescored = F.rescore(hist_root, out_csv, season_name, say=say)
    else:
        rescored = XR.rescore(hist_root, out_csv, say=say)
    with F.season_names(season_name):
        season = P.Season2425(hist_dir, prior_dir, odds, rescored)
    last = min(last, season.through)
    return [one_date(season, t) for t in range(first, last + 1)], season


def verdict(recs, seed=XR.SEED):
    diffs = [r["builder"] - r["rule"] for r in recs]
    boot = BT.bootstrap_mean(diffs, seed=seed)
    share = sum(1 for d in diffs if d >= 0) / len(diffs)
    proj_ok = all(r["builder_proj"] >= r["rule_proj"] - EPS for r in recs)
    ok = boot["mean"] > 0 and boot["lo"] > 0 and share >= PASS_SHARE and proj_ok
    return {"boot": boot, "share": share, "proj_ok": proj_ok, "pass": ok, "n": len(diffs)}


def test(hist_root, out=print, out_dir=None, first=FIRST, last=LAST, seasons=SEASONS, seed=XR.SEED):
    per, notes, sources = {}, [], {}
    for name, prior in seasons:
        recs, season = season_dates(hist_root, name, prior, os.path.join(out_dir or ".", f"rescored_{name}.csv"), first, last,
                                    say=notes.append)
        per[name] = recs
        sources[name] = Counter(("week t" if o == u else "weeks t+1..t+5", src) for o, u, _, _, _, src in season.sources)
    pooled = [r for name, _ in seasons for r in per[name]]
    res = {"per": per, "verdict": verdict(pooled, seed), "by_season": {n: verdict(per[n], seed) for n, _ in seasons},
           "every6": verdict([r for n, _ in seasons for r in per[n] if (r["gw"] - first) % 6 == 0], seed),
           "notes": notes, "sources": sources, "seed": seed, "first": first}
    report(res, out, seasons)
    return res


def report(res, out, seasons):
    v = res["verdict"]
    pooled = [r for n, _ in seasons for r in res["per"][n]]
    n = len(pooled)
    out(f"S15 TEST  the unified squad builder against the frozen three-layer rule: every gameweek {res['first']}-38 of "
        + " and ".join(F.label(s) for s, _ in seasons) + f" a hypothetical wildcard at that gameweek's prices with {BUDGET:.1f}; "
        f"the same xp_v2 matrix for both (week t S5's lambdas, weeks t+1..t+5 the origin's fallback); realised points over "
        f"weeks t..t+5 with rule_autosubs and the captain the highest xp_v2 in the XI; bootstrap over dates B={BT.B}, 90%, "
        f"seed {res['seed']}")
    out(f"  builder: decay {DECAY}, S7's bench weights {BENCH_W} + {SUBGK_W}, greedy + local search over S8's pool of {POOL} "
        f"(single swaps best, pairs first), also from the rule's squad; the GK+DEF 2-per-club cap off in the A/B (its cost below)")
    out(f"  rule: fpl_edge.build_three_layer_squad unchanged, {'-'.join(map(str, RULE_FORMATION))}, the quota-proportional "
        f"split; layer 1 and layer 3 ported to history, the GK/DEF six-week sum = the shared matrix; layer 2 never ranks")
    for note in res["notes"]:
        out(f"  re-score: {note}")
    for name, cnt in res["sources"].items():
        out(f"  {F.label(name)} lambda sources: " + ", ".join(f"{k[0]} {k[1]} {c}" for k, c in sorted(cnt.items())))
    out(f"  {'season':>8} {'GW':>3} {'rule':>7} {'builder':>8} {'diff':>7} {'proj rule':>10} {'proj bld':>9} {'cap':>7} "
        f"{'form':>6} {'433 cost':>9}")
    for name, _ in seasons:
        for r in res["per"][name]:
            out(f"  {F.label(name):>8} {r['gw']:>3} {r['rule']:7.1f} {r['builder']:8.1f} {r['builder'] - r['rule']:+7.1f} "
                f"{r['rule_proj']:10.2f} {r['builder_proj']:9.2f} {r['cap']:7.1f} {'-'.join(map(str, r['form'])):>6} "
                f"{r['cost_433']:9.2f}")
    b = v["boot"]
    out(f"  primary (pooled, {n} dates): builder - rule {b['mean']:+.2f} window points per date, 90% CI [{b['lo']:+.2f}, "
        f"{b['hi']:+.2f}]; builder >= rule on {v['share']:.2f} of dates; projected builder >= rule on every date: "
        f"{'yes' if v['proj_ok'] else 'NO'}")
    for name, _ in seasons:
        s = res["by_season"][name]
        out(f"  {F.label(name)} (information): {s['boot']['mean']:+.2f} [{s['boot']['lo']:+.2f}, {s['boot']['hi']:+.2f}] over "
            f"{s['n']} dates, builder >= rule on {s['share']:.2f}")
    e6 = res["every6"]
    out(f"  every sixth date (non-overlapping windows, information): {e6['boot']['mean']:+.2f} [{e6['boot']['lo']:+.2f}, "
        f"{e6['boot']['hi']:+.2f}] over {e6['n']} dates")
    not433 = [r for r in pooled if tuple(r["form"]) != RULE_FORMATION]
    out(f"  secondary: the builder's week-t formation is not 4-3-3 on {len(not433)} of {n} dates (mean projected cost of 4-3-3 "
        f"there {sum(r['cost_433'] for r in not433) / len(not433) if not433 else 0.0:.2f}); bench points in a first-week Bench "
        f"Boost: builder {sum(r['bench_builder'] for r in pooled) / n:.2f}, rule {sum(r['bench_rule'] for r in pooled) / n:.2f}")
    out(f"  the GK+DEF 2-per-club cap: projected cost {sum(r['builder_proj'] - r['cap_proj'] for r in pooled) / n:.2f}, realised "
        f"cost {sum(r['builder'] - r['cap'] for r in pooled) / n:+.2f} window points per date (builder without the cap - with it)")
    out("  pre-registered bar: mean > 0 with the 90% CI excluding 0, builder >= rule on >= 60% of dates, projected builder >= "
        "rule on every date: " + ("PASS (information only until Boris accepts)" if v["pass"] else "FAIL - the frozen rule stays"))


# ---------------------------------------------------------------------------
# live: --wildcard / --freehit (the default, Ruling, Tue 20 Oct, point 2) / --bb (information)
# ---------------------------------------------------------------------------

def live_matrix(data_dir, hist_root, weeks_n):
    """xp_v2 as tested at the live origin for weeks target..target+weeks_n-1:
    the newest export before the deadline; per fixture the Odds API snapshot
    where it prices the fixture, else the fallback fitted on results before
    the deadline (the night ruling, point 5). Returns (d, path, target,
    [{pid: xP}], sources Counter)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    name_to_short, deadlines, fixtures, settled, _ = OL.sqlite_tables(data_dir)
    upcoming = sorted((dl, ev) for ev, dl in deadlines.items() if dl > now)
    if not upcoming:
        raise MissingInput("no deadline after now in events")
    dl, target = upcoming[0]
    d, path = CH.newest_export(data_dir)
    if datetime.fromisoformat(d["generated"]) >= dl or d["gameweek"] + 1 != target:
        raise MissingInput(f"{os.path.basename(path)} is not the export before the GW{target} deadline")
    snap = OL.newest_snapshot(data_dir, dl)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    model = XL._model(fixtures, dl)
    prior = XL.load_prior(hist_root)
    names, _ = XL.prior_names(os.path.join(data_dir, "fpl.sqlite"), os.path.join(hist_root, "2026-27", "elements_positions.csv"),
                              os.path.join(hist_root, XL.PRIOR_SEASON))
    c = E.canonical_through(E.canonical_from_export(d), d["gameweek"])
    inp = E.reliability_inputs(c, gws_played=d["gameweek"])
    by_round, rows = XL.export_rows(d)
    tot = SH.team_totals(rows, {})
    gate = {int(p["id"]): p["status"] == "a" for p in d["all_players"]}
    weeks, srcs = [], Counter()
    for u in range(target, target + weeks_n):
        fx = XL.target_fixtures(d, u)
        lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}
        srcs.update(("week t" if u == target else "later weeks", s) for _, s in lam.values())

        def fixtures_of(team, fx=fx):
            return [(fid, f) for fid, f in fx.items() if team in (f["home"], f["away"])]

        def lam_team(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_home"] if team == fx[fid]["home"] else lam[fid][0]["lambda_away"]

        def lam_opp(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_away"] if team == fx[fid]["home"] else lam[fid][0]["lambda_home"]
        xp, _ = XL.core(inp, names, by_round, target, rows, {}, tot, prior, fixtures_of, lam_team, lam_opp,
                        ict=XL.ict_live(d), chance=XV.chance_scale(d), gate=gate)
        weeks.append(xp)
    return d, path, target, weeks, srcs


def live_rule(d, weeks_xp, target, budget):
    """The frozen three-layer rule's squad on the live export (amendment 2):
    rule_candidates with the live xp_v2 matrix as the GK/DEF six-week sum,
    then fpl_edge.build_three_layer_squad unchanged (4-3-3, the quota
    split), at current prices within the live budget."""
    fx = E.week_fixtures(d)
    weeks = list(range(target, target + len(weeks_xp)))
    pairings = {w: {team: fx[team].get(w, []) for team in fx} for w in weeks}
    gw = d["gameweek"]
    window = range(gw - min(4, gw) + 1, gw + 1)
    played = Counter()
    for f in d.get("fixtures_played") or []:
        if f["event"] in window:
            played[f["home"]] += 1
            played[f["away"]] += 1
    inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=gw)
    players = [{"id": int(p["id"]), "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
                "status": p.get("status"), "mins_last4": p.get("mins_last4")} for p in d["all_players"]]
    cands, _ = rule_candidates(players, inp, pairings, weeks, dict(played), {w: weeks_xp[i] for i, w in enumerate(weeks)})
    sq, spent = rule_squad(cands, budget)
    names = {p["id"]: p["name"] for p in players}
    return [dict(p, name=names.get(p["id"], str(p["id"]))) for p in sq], spent


def live(data_dir, hist_root, mode, out=print):
    weeks_n = HORIZON if mode == "wildcard" else 1
    d, path, target, weeks_xp, srcs = live_matrix(data_dir, hist_root, weeks_n)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise MissingInput(f"no budget: {why}")
    mine = {r["id"]: r for r in CH.my_squad(d)}
    market = [{"id": int(p["id"]), "name": p["web_name"], "team": p["team"], "pos": p["pos"],
               "price": mine[int(p["id"])]["selling"] if int(p["id"]) in mine else p["price"]}
              for p in d["all_players"] if p.get("status") == "a" or int(p["id"]) in mine]
    decay = DECAY if mode == "wildcard" else 1.0
    bench_full = mode == "bb"
    rsq, rspent = live_rule(d, weeks_xp, target, budget)
    full = len(rsq) == sum(QUOTA.values())
    r_obj = objective(rsq, weeks_xp, decay, bench_full) if full else None
    starts = [list(mine.values())] + ([rsq] if full else [])
    sq_on, v_on = build(market, weeks_xp, budget, True, starts=starts, decay=decay, bench_full=bench_full)
    sq_off, v_off = build(market, weeks_xp, budget, False, starts=starts, decay=decay, bench_full=bench_full)
    t_xp = weeks_xp[0]
    _, xi, form = week_value(sq_on, t_xp, bench_full)
    cap = max(xi, key=lambda p: (t_xp.get(p["id"], 0.0), -p["id"]))
    out(f"BUILDER  --{mode}  GW{target}" + (f"-{target + weeks_n - 1}" if weeks_n > 1 else "") + f" from {os.path.basename(path)}; "
        f"budget {budget:.1f} = bank + selling prices; xp_v2 as tested (" + ", ".join(f"{k[0]} {k[1]} {c}" for k, c in sorted(srcs.items()))
        + ("); the default for Free Hit and Wildcard builds (Ruling, Tue 20 Oct, point 2; not used for GW8)"
           if mode != "bb" else "); information only (the ruling makes the builder the default for Free Hit and Wildcard only)"))
    out(f"  the GK+DEF 2-per-club cap ON (Boris's choice): objective {v_on:.2f}; without it {v_off:.2f}; the cap costs "
        f"{v_off - v_on:.2f}")
    out(f"  {'player':<16}{'pos':>4}{'team':>5}{'price':>7}{'xP GW' + str(target):>9}  {'XI' if not bench_full else ''}")
    xi_ids = {p["id"] for p in xi}
    for p in sorted(sq_on, key=lambda p: (p["id"] not in xi_ids, p["pos"], -t_xp.get(p["id"], 0.0))):
        tag = ("C" if p["id"] == cap["id"] else "XI") if p["id"] in xi_ids else "bench"
        out(f"  {p['name']:<16}{BT.POS_NAME.get(p['pos'], '?'):>4}{p['team']:>5}{p['price']:7.1f}{t_xp.get(p['id'], 0.0):9.2f}  {tag}")
    out(f"  formation {'-'.join(map(str, form))}; spent {sum(p['price'] for p in sq_on):.1f} of {budget:.1f}")
    if not full:
        out(f"  beside it, the three-layer rule (frozen, 4-3-3, the quota split, the same matrix): no full squad ({len(rsq)} "
            f"players passed its layers); nothing is substituted")
    else:
        out(f"  beside it, the three-layer rule (frozen, 4-3-3, the quota split, the same matrix): objective {r_obj:.2f}, spent "
            f"{rspent:.1f}; builder - rule {v_on - r_obj:+.2f}")
        for pos in (1, 2, 3, 4):
            out(f"    {BT.POS_NAME.get(pos, '?'):>3}: " + ", ".join(f"{p['name']} ({p['team']}, {p['price']:.1f})"
                                                           for p in sorted(rsq, key=lambda p: (-t_xp.get(p["id"], 0.0), p["id"]))
                                                           if p["pos"] == pos))
    return {"squad": sq_on, "value": v_on, "value_off": v_off, "target": target, "rule": rsq, "rule_value": r_obj}


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--test", action="store_true")
    g.add_argument("--wildcard", action="store_true")
    g.add_argument("--freehit", action="store_true")
    g.add_argument("--bb", action="store_true")
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"))
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "builder"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("tools/builder.py", a.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    mode = "test" if a.test else "wildcard" if a.wildcard else "freehit" if a.freehit else "bb"
    try:
        if a.test:
            test(a.hist, out, a.out)
        else:
            live(a.data, a.hist, mode, out)
    except (MissingInput, XR.MissingInput, OL.MissingInput, BT.MissingInput, CH.MissingInput, SH.MissingInput,
            PL.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        return 2
    path = os.path.join(a.out, f"builder_{mode}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path)
    print(f"written: {path}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
