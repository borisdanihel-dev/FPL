"""tools/league_sim.py - S17, the mini-league win simulator (BUILD_PLAN.md
Step 17; Part F item F-H; prereg/S17.md). Offline; standard library only;
the nightly never imports it. Information only.

The simulator: joint draws from the Step 14 PMFs (tools/points_pmf.py) at an
origin, one draw per player-week per simulation shared by every manager who
owns him, the captain's draw counted twice; each manager's XI and captain
by the origin's xp_v2 matrix (week T on S5's lambdas, later weeks on the
origin's fallback - the night ruling, point 5). P(win) = the share of
simulations in which a manager's final total is the league's highest (ties
split).

The test (--test): 200 synthetic leagues of 10 managers from the 2025/26
replay (S7's sampler with style weights: 4 template ~ selected, 3 mixed ~
selected^0.5, 3 differential ~ 1/selected; fixed squads, no chips); the
truth replays GW2-38 with S6b's point-in-time xp_v2 choices, rule_autosubs
and the re-scored points; P(win) from GW20, 26 and 32 against the replayed
winner. Pass: Brier skill >= 0.05 v "the current leader wins", plus the
decile calibration table.

Live (--live): league 455565, 100,000 simulations, remaining Triple Captain
and Bench Boost in each manager's best projected week, P(win) and dP(win)
for our captain options and the builder's top three single transfers.

    python tools/league_sim.py --test [--hist ROOT] [--out DIR]
    python tools/league_sim.py --live [--data DIR] [--hist ROOT] [--out DIR]
"""
import argparse
import bisect
import os
import random
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import builder as B                                               # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import planner_2425 as P                                          # noqa: E402
import points_pmf as PM                                           # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2 as XV                                                # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

SEASON, PRIOR = "2025-26", "2024-25"
N_LEAGUES, ORIGINS, LAST = 200, (20, 26, 32), 38
STYLES = (("template", 4, lambda s: s), ("mixed", 3, lambda s: s ** 0.5), ("differential", 3, lambda s: 1.0 / s))
N_SIM, N_SIM_LIVE = 2000, 100000
SEED = BT.SEED
SQUAD_SEED = CH.SQUAD_SEED
PASS_SKILL = 0.05
LEAGUE_ID = 455565
FIRST_COUNTED = 2                   # GW1 has no forecast: no one's GW1 counts (pinned)
HALF_END = 19                       # the first-half chips (live)


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# managers
# ---------------------------------------------------------------------------

def sample_style(cands, n, seed, weight, budget=CH.BUDGET_TENTHS):
    """chips.sample_squads with `weight(selected)` in place of selected
    (players with selected > 0); weight = identity is S7's sampler."""
    rng = random.Random(seed)
    pool = [p for p in cands if p["selected"] > 0]
    squads, tries = [], 0
    while len(squads) < n:
        tries += 1
        if tries > 100000:
            raise MissingInput("could not sample a legal squad within the budget")
        avail = list(pool)
        weights = [weight(p["selected"]) for p in avail]
        picked, filled, clubs = [], Counter(), Counter()
        while len(picked) < 15 and avail:
            i = rng.choices(range(len(avail)), weights=weights, k=1)[0]
            p = avail.pop(i); weights.pop(i)
            if filled[p["pos"]] >= CH.QUOTA[p["pos"]] or clubs[p["team"]] >= CH.CLUB_MAX:
                continue
            picked.append(p); filled[p["pos"]] += 1; clubs[p["team"]] += 1
        if len(picked) == 15 and sum(p["price"] for p in picked) <= budget:
            squads.append(sorted(picked, key=lambda p: (p["pos"], p["id"])))
    return squads


def leagues(cands, n_leagues=N_LEAGUES, styles=STYLES, seed=SQUAD_SEED):
    """[[(style, squad), ...]] per league; league i, style j: seed*100000 + 10 i + j."""
    out = []
    for i in range(n_leagues):
        lg = []
        for j, (name, k, w) in enumerate(styles):
            lg += [(name, sq) for sq in sample_style(cands, k, seed * 100000 + 10 * i + j, w)]
        out.append(lg)
    return out


# ---------------------------------------------------------------------------
# the season: point-in-time choices, the horizon matrix and PMFs
# ---------------------------------------------------------------------------

class SimSeason(P.Season2425):
    """S8b's season with the detail kept: xp_v2 and its detail for any week u
    at origin t (week t: S5's lambdas; later weeks: the origin's fallback)."""

    def week_detail(self, t, u, inp, names):
        lam = self.horizon_lambdas(t, u)

        def lam_team(fid, team):
            l, f = lam[fid][0], self.fixtures[fid]
            return l["lambda_home"] if team == f["home"] else l["lambda_away"]

        def lam_opp(fid, team):
            l, f = lam[fid][0], self.fixtures[fid]
            return l["lambda_away"] if team == f["home"] else l["lambda_home"]
        for fid in sorted(lam, key=str):
            f = self.fixtures[fid]
            self.sources.append((t, u, fid, f["home"], f["away"], lam[fid][1]))
        return XL.core(inp, names, self.by_round, t, self.s11.rows, self.s11.n2s, self.s11.tot, self.s11.prior,
                       lambda team: self.s11.club_fixtures(team, u), lam_team, lam_opp)

    def origin_inputs(self, t):
        c = BT.canonical_at(self.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        return c, inp, {pid: c["players"][pid]["name"] for pid in inp["players"]}

    def point_in_time(self, u):
        """S6b's xp_v2(u) from rounds < u (the truth's choices)."""
        return self.forecasts(u)[0][u]

    def horizon(self, t, last=LAST):
        """({u: {pid: xp}}, {u: {pid: pmf}}) for u = t..last at origin t."""
        c, inp, names = self.origin_inputs(t)
        pos_of = {pid: p["pos"] for pid, p in inp["players"].items()}
        train = [r for rnd in range(1, t) for r in self.by_round.get(rnd, [])]
        subs = PM.sub_pmfs(train, pos_of)
        table = PM.bonus_table([(pos_of.get(int(r["element"])) or H.POS.get(r.get("position"), 0),
                                 H._num(r.get("goals_scored")) + H._num(r.get("assists")), H._num(r.get("clean_sheets")) > 0,
                                 H._num(r.get("bonus"))) for r in train if H._num(r.get("starts")) >= 1])
        xps, pmfs = {}, {}
        for u in range(t, last + 1):
            xp, detail = self.week_detail(t, u, inp, names)
            xps[u], pmfs[u] = xp, {}
            for pid, x in detail.items():
                pos = inp["players"][pid]["pos"]
                terms = PM.bottomup_terms(pid, inp, [(f["opp"], f["home"], f["lam_opp"]) for f in x["fixtures"]])
                pmfs[u][pid] = PM.player_pmf(x, terms, pos, subs[pos], table)[0]
        return xps, pmfs


def choice(squad, xp):
    """(XI ids, captain id) by xp: chips.xi_and_bench, the captain the highest in the XI (ties to the lower id)."""
    xi, _, _ = CH.xi_and_bench([dict(p) for p in squad], xp)
    cap = max(xi, key=lambda r: (r["proj"], -r["id"]))
    return [r["id"] for r in xi], cap["id"]


# ---------------------------------------------------------------------------
# the simulator
# ---------------------------------------------------------------------------

def cdf_of(pmf):
    vals = sorted(pmf)
    cum, acc = [], 0.0
    for v in vals:
        acc += pmf[v]
        cum.append(acc)
    cum[-1] = max(cum[-1], 1.0)                    # rounding: the last bin takes the remainder
    return vals, cum


def plan(manager_weeks):
    """manager_weeks: per manager [(week, XI ids, captain, multiplier)] ->
    (keys [(pid, week)], per manager [key index ...] with the captain's
    index repeated multiplier - 1 more times)."""
    index, keys, idx = {}, [], []
    for weeks in manager_weeks:
        mine = []
        for u, xi, cap, mult in weeks:
            for pid in xi:
                k = index.setdefault((pid, u), len(keys))
                if k == len(keys):
                    keys.append((pid, u))
                mine.append(k)
            k = index[(cap, u)]
            mine += [k] * (mult - 1)
        idx.append(mine)
    return keys, idx


def simulate(keys, pmfs, idx, base, groups, n_sim, seed, extra=None):
    """P(win) per manager: draws shared by key, totals = base + sum over
    indices; groups: [[manager index, ...]] per league. extra: {name:
    (manager index, [key index ...])} alternative totals for one manager
    (common random numbers). Returns (p_win list, {name: p_win})."""
    tables = [cdf_of(pmfs.get(u, {}).get(pid, {0: 1.0})) for pid, u in keys]
    rng = random.Random(seed)
    wins = [0.0] * len(idx)
    ex_wins = {name: 0.0 for name in (extra or {})}
    for _ in range(n_sim):
        d = []
        for vals, cum in tables:
            j = bisect.bisect_left(cum, rng.random())
            d.append(vals[min(j, len(vals) - 1)])
        tot = [base[m] + sum(map(d.__getitem__, ix)) for m, ix in enumerate(idx)]
        for g in groups:
            top = max(tot[m] for m in g)
            lead = [m for m in g if tot[m] == top]
            for m in lead:
                wins[m] += 1.0 / len(lead)
        for name, (m, ix) in (extra or {}).items():
            g = next(gr for gr in groups if m in gr)
            mine = base[m] + sum(map(d.__getitem__, ix))
            top = max([tot[o] for o in g if o != m] + [mine])
            if mine == top:
                ex_wins[name] += 1.0 / (1 + sum(1 for o in g if o != m and tot[o] == top))
    return [w / n_sim for w in wins], {k: v / n_sim for k, v in ex_wins.items()}


def leader_p(totals):
    top = max(totals)
    lead = [i for i, t in enumerate(totals) if t == top]
    return [1.0 / len(lead) if i in lead else 0.0 for i in range(len(totals))]


def brier(pairs):
    return sum((p - w) ** 2 for p, w in pairs) / len(pairs)


def deciles(pairs, n=10):
    s = sorted(pairs, key=lambda x: x[0])
    out = []
    for k in range(n):
        part = s[k * len(s) // n:(k + 1) * len(s) // n]
        if part:
            out.append((sum(p for p, _ in part) / len(part), sum(w for _, w in part) / len(part), len(part)))
    return out


def skill_ci(per_league, b=BT.B, seed=SEED):
    """Brier skill and its 90% bootstrap interval over leagues: per_league =
    [(sum sq err sim, sum sq err leader, n)]."""
    def sk(rows):
        s, l = sum(r[0] for r in rows), sum(r[1] for r in rows)
        return 1.0 - s / l if l > 0 else float("nan")
    rng = random.Random(seed)
    boots = sorted(sk([per_league[rng.randrange(len(per_league))] for _ in per_league]) for _ in range(b))
    return sk(per_league), boots[int(0.05 * b)], boots[int(0.95 * b) - 1]


# ---------------------------------------------------------------------------
# the test on 2025/26
# ---------------------------------------------------------------------------

def test(hist_root, out=print, out_dir=None, n_leagues=N_LEAGUES, origins=ORIGINS, n_sim=N_SIM, seed=SEED, styles=STYLES,
         last=LAST, season_name=SEASON, prior_name=PRIOR, odds_file=None, rescored=None):
    hist_dir, prior_dir = os.path.join(hist_root, season_name), os.path.join(hist_root, prior_name)
    odds_file = odds_file or OL.odds_path(season_name)
    for p in (odds_file, os.path.join(prior_dir, "merged_gw.csv")):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing")
    notes = []
    if rescored is None:
        rescored = XR.rescore(hist_root, os.path.join(out_dir or ".", f"rescored_{season_name}.csv"), say=notes.append)
    season = SimSeason(hist_dir, prior_dir, odds_file, rescored)
    last = min(last, season.through)
    lgs = leagues(CH.gw1_candidates(season.rp.hist), n_leagues, styles)
    managers = [sq for lg in lgs for _, sq in lg]
    groups, k = [], 0
    for lg in lgs:
        groups.append(list(range(k, k + len(lg))))
        k += len(lg)
    weekly = {}                                                   # the truth: points per manager per week
    for u in range(FIRST_COUNTED, last + 1):
        xp = season.point_in_time(u)
        weekly[u] = [season.realised([{"id": p["id"], "pos": p["pos"], "team": p["team"], "name": str(p["id"])} for p in sq], u, xp)
                     for sq in managers]
    final = [sum(weekly[u][m] for u in weekly) for m in range(len(managers))]
    won = [0.0] * len(managers)
    for g in groups:
        for m, p in zip(g, leader_p([final[m] for m in g])):
            won[m] = p
    per_origin, per_league = {}, defaultdict(lambda: [0.0, 0.0, 0])
    pairs_all = []
    for T in origins:
        if T > last:
            continue
        base = [sum(weekly[u][m] for u in weekly if u < T) for m in range(len(managers))]
        xps, pmfs = season.horizon(T, last)
        mweeks = []
        for sq in managers:
            ws = []
            for u in range(T, last + 1):
                xi, cap = choice(sq, xps[u])
                ws.append((u, xi, cap, 2))
            mweeks.append(ws)
        keys, idx = plan(mweeks)
        p_win, _ = simulate(keys, pmfs, idx, base, groups, n_sim, seed)
        pairs = []
        for li, g in enumerate(groups):
            lead = leader_p([base[m] for m in g])
            for m, pl in zip(g, lead):
                pairs.append((p_win[m], won[m]))
                per_league[li][0] += (p_win[m] - won[m]) ** 2
                per_league[li][1] += (pl - won[m]) ** 2
                per_league[li][2] += 1
        lead_pairs = [(pl, won[m]) for g in groups for m, pl in zip(g, leader_p([base[m] for m in g]))]
        per_origin[T] = {"sim": brier(pairs), "leader": brier(lead_pairs)}
        pairs_all += pairs
    skill, lo, hi = skill_ci(list(per_league.values()), seed=seed)
    res = {"styles": [(n_, k_) for n_, k_, _ in styles], "skill": skill, "lo": lo, "hi": hi, "per_origin": per_origin, "deciles": deciles(pairs_all), "pass": skill >= PASS_SKILL,
           "notes": notes, "n_leagues": n_leagues, "n_sim": n_sim, "origins": [T for T in origins if T <= last], "last": last,
           "sources": Counter(("week T" if o == u else "later weeks", s) for o, u, _, _, _, s in season.sources if o in origins),
           "final": final, "won": won, "seed": seed}
    report(res, out)
    return res


def report(res, out):
    comp = ", ".join(f"{k} {n}" for n, k in res["styles"])
    out(f"S17 TEST  {res['n_leagues']} synthetic leagues of {sum(k for _, k in res['styles'])} from the 2025/26 replay (S7's sampler "
        f"with style weights: {comp}; template ~ selected, mixed ~ selected^0.5, differential ~ 1/selected; fixed squads, no chips); "
        f"the truth GW"
        f"{FIRST_COUNTED}-{res['last']} with S6b's point-in-time xp_v2 choices, rule_autosubs and the re-scored points; P(win) from GW"
        + ", ".join(map(str, res["origins"])) + f" by {res['n_sim']} joint simulations from Step 14's PMFs (shared players one draw, "
        f"the captain doubled, no autosubs inside); seed {res['seed']}")
    for n in res["notes"]:
        out(f"  re-score: {n}")
    out("  lambda sources at the origins: " + ", ".join(f"{k[0]} {k[1]} {v}" for k, v in sorted(res["sources"].items())))
    for T, b in sorted(res["per_origin"].items()):
        out(f"  GW{T}: Brier simulator {b['sim']:.4f}, leader {b['leader']:.4f}, skill {1 - b['sim'] / b['leader'] if b['leader'] else float('nan'):+.3f}")
    out(f"  primary: Brier skill v the current leader {res['skill']:+.4f}, 90% CI over leagues [{res['lo']:+.4f}, {res['hi']:+.4f}]")
    out("  decile calibration (mean P(win), observed win rate, n):")
    for p, w, n in res["deciles"]:
        out(f"    {p:.3f}  {w:.3f}  {n}")
    out(f"  pre-registered bar: Brier skill >= {PASS_SKILL}: " + ("PASS (information only; live use needs Boris)" if res["pass"] else "FAIL"))


# ---------------------------------------------------------------------------
# live: league 455565 (information only)
# ---------------------------------------------------------------------------

def live_horizon(data_dir, hist_root):
    """The live xp_v2 matrix and Step 14 PMFs for target..38 (the Odds API
    snapshot where it prices the fixture, else the fallback)."""
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
    pos_of = {pid: p["pos"] for pid, p in inp["players"].items()}
    subs = PM.sub_pmfs(rows, pos_of)
    table = PM.bonus_table([(pos_of.get(int(r["player_id"])), (r.get("g_") or 0) + (r.get("a_") or 0), (r.get("cs") or 0) > 0,
                             r.get("bonus") or 0) for r in d.get("player_gw_recent") or []
                            if (r.get("starts") or 0) >= 1 and int(r["event"]) <= d["gameweek"]])
    xps, pmfs, srcs = {}, {}, Counter()
    for u in range(target, LAST + 1):
        fx = XL.target_fixtures(d, u)
        lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}
        srcs.update(("week t" if u == target else "later weeks", s) for _, s in lam.values())

        def fixtures_of(team, fx=fx):
            return [(fid, f) for fid, f in fx.items() if team in (f["home"], f["away"])]

        def lam_team(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_home"] if team == fx[fid]["home"] else lam[fid][0]["lambda_away"]

        def lam_opp(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_away"] if team == fx[fid]["home"] else lam[fid][0]["lambda_home"]
        xp, detail = XL.core(inp, names, by_round, target, rows, {}, tot, prior, fixtures_of, lam_team, lam_opp,
                             ict=XL.ict_live(d), chance=XV.chance_scale(d), gate=gate)
        xps[u], pmfs[u] = xp, {}
        for pid, x in detail.items():
            terms = PM.bottomup_terms(pid, inp, [(f["opp"], f["home"], f["lam_opp"]) for f in x["fixtures"]])
            pmfs[u][pid] = PM.player_pmf(x, terms, pos_of[pid], subs[pos_of[pid]], table)[0]
    return d, path, target, xps, pmfs, srcs


def chip_weeks(squad, xps, target, has_tc, has_bb):
    """(TC week, BB week): the remaining chip in the manager's best projected
    week of the current half (the highest captain xP; the highest bench xP)."""
    weeks = [u for u in sorted(xps) if u <= HALF_END] or []
    tc = bb = None
    if has_tc and weeks:
        tc = max(weeks, key=lambda u: (max(xps[u].get(i, 0.0) for i in choice(squad, xps[u])[0]), -u))
    if has_bb and weeks:
        def bench(u):
            xi = set(choice(squad, xps[u])[0])
            return sum(xps[u].get(p["id"], 0.0) for p in squad if p["id"] not in xi)
        bb = max(weeks, key=lambda u: (bench(u), -u))
    return tc, bb


def manager_weeks(squad, xps, target, tc=None, bb=None, captain=None):
    out = []
    for u in sorted(xps):
        xi, cap = choice(squad, xps[u])
        if u == target and captain is not None:
            cap = captain
        if u == bb:
            xi = [p["id"] for p in squad]
        out.append((u, xi, cap, 3 if u == tc else 2))
    return out


def live(data_dir, hist_root, out=print, n_sim=N_SIM_LIVE, seed=SEED):
    d, path, target, xps, pmfs, srcs = live_horizon(data_dir, hist_root)
    by_entry = defaultdict(list)
    players = {int(p["id"]): p for p in d["all_players"]}
    for r in d["squads"]:
        p = players.get(r["player_id"])
        if p is None:
            raise MissingInput(f"squad player {r['player_id']} is not in all_players")
        by_entry[r["entry_id"]].append({"id": p["id"], "pos": p["pos"], "team": p["team"], "name": p["web_name"]})
    stand = {s["entry_id"]: s for s in d["standings"]}
    entries = sorted(e for e in by_entry if e in stand)
    if len(entries) < 2 or any(len(by_entry[e]) != 15 for e in entries):
        raise MissingInput("the export holds fewer than two entries with 15 picks and a standing")
    used = defaultdict(set)
    for ch in d.get("chips_used") or []:
        if ch.get("event") is not None and ch["event"] <= HALF_END:
            used[ch["entry_name"]].add(ch["name"])
    me = d["my_entry"]
    names = {e: stand[e]["entry_name"] for e in entries}
    mweeks, chips_note = [], []
    for e in entries:
        tc, bb = chip_weeks(by_entry[e], xps, target, "3xc" not in used[names[e]], "bboost" not in used[names[e]])
        chips_note.append(f"{names[e]}: TC {'GW' + str(tc) if tc else '-'}, BB {'GW' + str(bb) if bb else '-'}")
        mweeks.append(manager_weeks(by_entry[e], xps, target, tc, bb))
    m_me = entries.index(me)
    sq_me = by_entry[me]
    tc_me, bb_me = chip_weeks(sq_me, xps, target, "3xc" not in used[names[me]], "bboost" not in used[names[me]])
    xi_t, cap_t = choice(sq_me, xps[target])
    caps = sorted(xi_t, key=lambda i: (-xps[target].get(i, 0.0), i))[:3]
    alts = {f"captain {players[c]['web_name']}": manager_weeks(sq_me, xps, target, tc_me, bb_me, captain=c) for c in caps}
    budget, why = E.selling_budget(d)
    if budget is not None:
        mine = {r["id"]: r for r in CH.my_squad(d)}
        bank = budget - sum(r["selling"] for r in mine.values())
        market = [{"id": int(p["id"]), "name": p["web_name"], "team": p["team"], "pos": p["pos"],
                   "price": mine[int(p["id"])]["selling"] if int(p["id"]) in mine else p["price"]}
                  for p in d["all_players"] if p.get("status") == "a" or int(p["id"]) in mine]
        weeks6 = [xps[u] for u in sorted(xps)[:B.HORIZON]]
        cur = [dict(m, price=m["selling"]) for m in mine.values()]
        pool = B.build_pool(market, weeks6, {p["id"] for p in cur})
        moves = []
        for o in cur:
            for i in pool.get(o["pos"], []):
                new = [p for p in cur if p["id"] != o["id"]] + [i]
                if B.legal(new, bank + sum(p["price"] for p in cur), True):
                    moves.append((B.objective(new, weeks6) - B.objective(cur, weeks6), o, i, new))
        for gain, o, i, new in sorted(moves, key=lambda m: (-m[0], m[1]["id"], m[2]["id"]))[:3]:
            sq = [{"id": p["id"], "pos": p["pos"], "team": p["team"], "name": p.get("name", str(p["id"]))} for p in new]
            alts[f"{players[o['id']]['web_name']} -> {i['name']} ({gain:+.2f} decayed xP)"] = manager_weeks(sq, xps, target, tc_me, bb_me)
    keys, idx = plan(mweeks + list(alts.values()))
    base = [stand[e]["total"] for e in entries] + [stand[me]["total"]] * len(alts)
    extra = {name: (m_me, idx[len(entries) + k]) for k, name in enumerate(alts)}
    p_win, p_alt = simulate(keys, pmfs, idx[:len(entries)], base[:len(entries)], [list(range(len(entries)))], n_sim, seed, extra)
    out(f"LEAGUE SIMULATOR  league {LEAGUE_ID}, GW{target}-{LAST} from {os.path.basename(path)}: {n_sim} joint simulations from "
        f"Step 14's PMFs of xp_v2 as tested (" + ", ".join(f"{k[0]} {k[1]} {v}" for k, v in sorted(srcs.items()))
        + "); information only (S17's test decides any use)")
    out("  chips: played chips are in the totals; a remaining TC / BB in the manager's best projected week of the half; FH and WC "
        "not modelled (their squads are unknown): " + "; ".join(chips_note))
    for e, p in sorted(zip(entries, p_win), key=lambda x: -x[1]):
        out(f"  {names[e]:<24} total {stand[e]['total']:>5}  P(win) {p:.3f}" + ("   <- us" if e == me else ""))
    out(f"  dP(win) for us (common random numbers; our default: captain {players[cap_t]['web_name']}, no transfer, P(win) "
        f"{p_win[m_me]:.3f}):")
    for name, p in p_alt.items():
        out(f"    {name:<52} P(win) {p:.3f}  dP {p - p_win[m_me]:+.3f}")
    return {"p_win": dict(zip(entries, p_win)), "alts": p_alt, "target": target}


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--test", action="store_true")
    g.add_argument("--live", action="store_true")
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"))
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "league_sim"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("tools/league_sim.py", a.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        if a.test:
            test(a.hist, out, a.out)
        else:
            live(a.data, a.hist, out)
    except (MissingInput, XR.MissingInput, OL.MissingInput, BT.MissingInput, CH.MissingInput, SH.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        return 2
    path = os.path.join(a.out, f"league_sim_{'test' if a.test else 'live'}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path)
    print(f"written: {path}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
