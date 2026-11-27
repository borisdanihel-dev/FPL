"""worklog/gw_pass/gw11/refresh_extra.py - the GW11 refresh's information items 3-5 (Boris, point e of Fri 20 Nov,
verbatim in prereg/bundle.md with the reading pinned before this code). Information only, read-only, no tool change.
Standard library only.

    python -I refresh_extra.py --code DIR --data DIR --hist DIR --out DIR

3  Calafiori at P(start) 1.0 in every week GW11-16 (nothing else changed): the no-BB tables on the lifted matrix
   (bb_moves.py's: Thiago from GW14, Thomas at his chance in GW11, then normal) and the gated one; the best pair and
   the named options.
4  Clean-sheet sensitivity: each of those moves' decayed six-week gain (the planner's evaluate, no BB) as is and with
   every team's P(cs) in GW11-16 flattened - only the clean-sheet probability, in both xp_v2 blends; the goals-conceded
   deduction, attack, DEFCON and minutes keep their fixture values. (A) the team's realised 2026/27 clean-sheet rate
   before the deadline; (B) the mean of the model's own P(cs) over the team's GW11-16 fixtures. The clean-sheet
   share = (gain - gain with every P(cs) = 0) / gain, XIs re-chosen in each (not additive).
5  The captain tie: the recorded GW11 xg and bottomup rows for Gabriel and Haaland; Newcastle's and Fulham's goals
   scored and conceded in finished 2026/27 league fixtures, all and by venue.
"""
import argparse
import importlib.util
import math
import os
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(f"gw11_{name}", os.path.join(HERE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BM = _load("bb_moves")                  # lifted_matrix and the --code imports
B, CH, E, PL, PLV = BM.B, BM.CH, BM.E, BM.PL, BM.PLV
OL_MOD = sys.modules[B.OL.__name__]
XL = B.XL
assert XL.OL is OL_MOD, "xp_v2_live and builder must share odds_lambda"
EXP_CS = OL_MOD.p_clean_sheet


class TLam(float):
    """lambda_opp carrying the player's team, so the clean-sheet probability alone can be replaced."""
    def __new__(cls, v, team):
        o = float.__new__(cls, v)
        o.team = team
        return o


def matrix(data_dir, hist_root, weeks_n, lifts, pstart=None, cs=None):
    """bb_moves.lifted_matrix with two information switches: pstart {pid: P(start)} in every week; cs None (as is),
    ("flat", {team: P(cs)}) or ("zero", None) - the clean-sheet probability only. Returns (weeks, model P(cs) per team
    and week)."""
    now = datetime.now(timezone.utc)
    OL, SH, XV = B.OL, B.SH, B.XV
    _, deadlines, fixtures, _, _ = OL.sqlite_tables(data_dir)
    dl, target = sorted((dl, ev) for ev, dl in deadlines.items() if dl > now)[0]
    d, path = CH.newest_export(data_dir)
    snap = OL.newest_snapshot(data_dir, dl)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    model = XL._model(fixtures, dl)
    prior = XL.load_prior(hist_root)
    names, _ = XL.prior_names(os.path.join(data_dir, "fpl.sqlite"), os.path.join(hist_root, "2026-27", "elements_positions.csv"),
                              os.path.join(hist_root, XL.PRIOR_SEASON))
    c = E.canonical_through(E.canonical_from_export(d), d["gameweek"])
    gws = d["gameweek"]
    inp = E.reliability_inputs(c, gws_played=gws)
    starts4 = Counter()
    for r in c["rows"]:
        if gws - min(4, gws) < r["event"] <= gws:
            starts4[r["player_id"]] += r["starts"] or 0
    by_round, rows = XL.export_rows(d)
    tot = SH.team_totals(rows, {})
    gate0 = {int(p["id"]): p["status"] == "a" for p in d["all_players"]}
    chance0 = XV.chance_scale(d)
    weeks, pcs = [], []

    def patched(lam):
        if isinstance(lam, TLam) and cs is not None:
            return 0.0 if cs[0] == "zero" else cs[1][lam.team]
        return EXP_CS(lam)
    OL_MOD.p_clean_sheet = patched
    try:
        for u in range(target, target + weeks_n):
            fx = XL.target_fixtures(d, u)
            lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}
            wk = {}
            for fid, f in fx.items():
                wk.setdefault(f["home"], []).append(EXP_CS(lam[fid][0]["lambda_away"]))
                wk.setdefault(f["away"], []).append(EXP_CS(lam[fid][0]["lambda_home"]))
            pcs.append(wk)

            def fixtures_of(team, fx=fx):
                return [(fid, f) for fid, f in fx.items() if team in (f["home"], f["away"])]

            def lam_team(fid, team, fx=fx, lam=lam):
                return lam[fid][0]["lambda_home"] if team == fx[fid]["home"] else lam[fid][0]["lambda_away"]

            def lam_opp(fid, team, fx=fx, lam=lam):
                return TLam(lam[fid][0]["lambda_away"] if team == fx[fid]["home"] else lam[fid][0]["lambda_home"], team)
            gate, chance, players = dict(gate0), dict(chance0), dict(inp["players"])
            for pid, (first, normal_from) in lifts.items():
                if first is not None and u < first:
                    continue
                gate[pid] = True
                if normal_from is not None and u >= normal_from and pid in players:
                    players[pid] = dict(players[pid], p_start=min(1.0, starts4[pid] / max(1, min(4, gws))))
                    chance[pid] = 1.0
            for pid, v in (pstart or {}).items():
                if pid in players:
                    players[pid] = dict(players[pid], p_start=v)
            xp, _ = XL.core(dict(inp, players=players), names, by_round, target, rows, {}, tot, prior, fixtures_of,
                            lam_team, lam_opp, ict=XL.ict_live(d), chance=chance, gate=gate)
            weeks.append(xp)
    finally:
        OL_MOD.p_clean_sheet = EXP_CS
    return weeks, pcs


def realised_cs(data_dir, before):
    """{short_name: (clean sheets, matches, goals for, goals against, by venue)} from finished league fixtures."""
    con = sqlite3.connect(os.path.join(data_dir, "fpl.sqlite"))
    short = dict(con.execute("select id, short_name from teams"))
    out = {}
    for h, a, hs, as_, ko in con.execute("select team_h, team_a, team_h_score, team_a_score, kickoff_time from fixtures "
                                         "where finished = 1"):
        if datetime.fromisoformat(ko.replace("Z", "+00:00")) >= before:
            continue
        for team, gf, ga, venue in ((short[h], hs, as_, "home"), (short[a], as_, hs, "away")):
            r = out.setdefault(team, {"cs": 0, "n": 0, "gf": 0, "ga": 0, "home": [0, 0, 0], "away": [0, 0, 0]})
            r["cs"] += ga == 0
            r["n"] += 1
            r["gf"] += gf
            r["ga"] += ga
            r[venue][0] += 1
            r[venue][1] += gf
            r[venue][2] += ga
    con.close()
    return out


def main(argv=None):
    BM.utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = BM.Run("worklog/gw_pass/gw11/refresh_extra.py", a.out, argv if argv is not None else sys.argv[1:], root=BM.CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    d, path, target, XP, srcs, p_start, snap = PLV.live_inputs(a.data, a.hist)
    n = len(XP)
    weeks = list(range(target, target + n))
    squad = CH.my_squad(d)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise BM.MissingInput(f"no budget: {why}")
    bank = budget - sum(r["selling"] for r in squad)
    market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
               "status": p["status"]} for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    by_name = {}
    for p in d["all_players"]:
        by_name.setdefault((p["web_name"], p["team"]), []).append(p)

    def ours(name):
        m = [r for r in squad if r["name"] == name]
        if len(m) != 1:
            raise BM.MissingInput(f"{name} is not one player of our 15")
        return m[0]

    def market_row(name, team):
        m = [r for r in market if r["name"] == name and r["team"] == team]
        if len(m) != 1:
            raise BM.MissingInput(f"{name} ({team}) is not one available market player")
        return m[0]
    data_commit = subprocess.run(["git", "-C", a.data, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    deadline = B.OL.sqlite_tables(a.data)[1].get(target)
    out(f"GW{target} REFRESH, INFORMATION ITEMS 3-5 (Boris, point e of Fri 20 Nov; reading pinned in prereg/bundle.md); "
        f"read-only, no tool change")
    out(f"  data {data_commit[:7]}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {BM.sha256_of(os.path.abspath(__file__))}; generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    thiago, thomas, cala = ours("Thiago"), ours("Thomas"), ours("Calafiori")
    lifts = {thiago["id"]: (BM.THIAGO_FROM, BM.THIAGO_FROM), thomas["id"]: (None, target + 1)}
    XL_ref, _, _ = BM.lifted_matrix(a.data, a.hist, n, lifts)
    L0, pcs = matrix(a.data, a.hist, n, lifts)
    out(f"  check: this script's lifted matrix, no switch, equals bb_moves.lifted_matrix: {all(L0[t] == XL_ref[t] for t in range(n))}")
    G0, _ = matrix(a.data, a.hist, n, {})
    out(f"  check: this script's gated matrix, no switch, equals the planner's: {all(G0[t] == XP[t] for t in range(n))}")
    L1, _ = matrix(a.data, a.hist, n, lifts, pstart={cala["id"]: 1.0})
    G1, _ = matrix(a.data, a.hist, n, {}, pstart={cala["id"]: 1.0})
    moved = [(t, pid) for M, R in ((L1, L0), (G1, G0)) for t in range(n) for pid in set(M[t]) | set(R[t])
             if pid != cala["id"] and M[t].get(pid) != R[t].get(pid)]
    out(f"  check: Calafiori's P(start) 1.0 moves no other player's value: {not moved}")
    cala_in = next(p for p in d["all_players"] if p["id"] == cala["id"])
    out(f"  Calafiori (ARS DEF, status {cala_in['status']}, chance {cala_in.get('chance_next_round')}): model P(start) "
        f"{p_start.get(cala['id'], 0.0):.2f}; xp_v2 by week as is (lifted) " + ", ".join(f"GW{u} {L0[t].get(cala['id'], 0.0):.2f}" for t, u in enumerate(weeks))
        + "; at P(start) 1.0 " + ", ".join(f"GW{u} {L1[t].get(cala['id'], 0.0):.2f}" for t, u in enumerate(weeks)))

    dec, sched, fts = BM.DECAY, BM.SCHED, BM.FTS
    dc, vh = market_row("De Cuyper", "BHA"), market_row("Van Hecke", "TOT")
    named = [("Calafiori -> De Cuyper + Thomas -> Van Hecke", ((cala, thomas), (dc, vh))),
             ("Calafiori -> De Cuyper alone + roll one", ((cala,), (dc,))),
             ("Thomas -> Van Hecke alone + roll one", ((thomas,), (vh,)))]

    def why_not(plan):
        outs, ins = plan
        rows = [r for r in squad if r["id"] not in {o["id"] for o in outs}] + list(ins)
        left = bank + sum(o["selling"] for o in outs) - sum(i["price"] for i in ins)
        return None if PL.legal(rows, left) else f"not legal: bank after {left:.1f} (or a club over 3)"

    def ev_of(plan, M):
        return None if why_not(plan) else PL.evaluate(plan, squad, M, dec, sched, fts, p_start, hits_allowed=False)

    def show(tag, e, rank=None, plan=None):
        if e is None:
            out(f"    {tag:<46} " + ((why_not(plan) if plan else None) or "not allowed (unscored)"))
            return
        out(f"    {tag:<46} {e['score']:6.2f} {e['gain']:6.2f} {e['lost']:6.2f} {'' if rank is None else rank:>6}   "
            + " ".join(f"{g:+5.1f}" for g in e["gains"]) + f"   {PLV.plan_text(e)}")
    out()
    out(f"ITEM 3  CALAFIORI AT P(START) 1.0, NO BENCH BOOST ({fts} free transfers, bank {bank:.1f}, no hits, decay {dec}, "
        f"Boris's schedule {sched})")
    best_pairs = {}
    for label, M, R in (("LIFTED (Thiago from GW14; Thomas at his chance in GW11, then normal)", L1, L0),
                        ("GATED (Thiago, Thomas 0)", G1, G0)):
        scored, _ = PL.rank_plans(squad, bank, market, M, fts, p_start, dec, sched, hits_allowed=False)
        rank = {PL.plan_key(e): i for i, e in enumerate(scored, 1)}
        out(f"  {label}: {len(scored)} plans")
        out(f"    {'':<46} {'score':>6} {'gain':>6} {'lostFT':>6} {'rank':>6}   weekly dxP GW{weeks[0]}-{weeks[-1]}")
        top = scored[0]
        pair = next(e for e in scored if e["used"] == 2)
        best_pairs[label] = pair
        show("best (P(start) 1.0)", top, 1)
        show("best pair (P(start) 1.0)", pair, rank[PL.plan_key(pair)])
        for tag, plan in named:
            e = ev_of(plan, M)
            show(tag, e, rank.get(PL.plan_key(e)) if e else None, plan)
        r0, _ = PL.rank_plans(squad, bank, market, R, fts, p_start, dec, sched, hits_allowed=False)
        rk0 = {PL.plan_key(e): i for i, e in enumerate(r0, 1)}
        out(f"    beside it, Calafiori as the model has him (P(start) {p_start.get(cala['id'], 0.0):.2f}):")
        show("best pair (model P(start))", next(e for e in r0 if e["used"] == 2), rk0[PL.plan_key(next(e for e in r0 if e["used"] == 2))])
        for tag, plan in named:
            e = ev_of(plan, R)
            show(tag, e, rk0.get(PL.plan_key(e)) if e else None, plan)

    out()
    rc = realised_cs(a.data, deadline) if deadline else None
    if rc is None:
        raise BM.MissingInput("no GW deadline in the export's events")
    flat_a = {t: r["cs"] / r["n"] for t, r in rc.items() if r["n"]}
    teams = sorted({t for wk in pcs for t in wk})
    missing = [t for t in teams if t not in flat_a]
    if missing:
        raise BM.MissingInput(f"no finished league match for {', '.join(missing)}")
    flat_b = {t: sum(v for wk in pcs for v in wk.get(t, [])) / sum(len(wk.get(t, [])) for wk in pcs) for t in teams}
    out(f"ITEM 4  CLEAN-SHEET SENSITIVITY (only P(cs) flattened, GW{weeks[0]}-{weeks[-1]}, every team; goals-conceded, attack, "
        f"DEFCON and minutes unchanged)")
    out(f"  (A) the realised 2026/27 clean-sheet rate before the deadline; (B) the mean of the model's own P(cs) over the "
        f"team's GW{weeks[0]}-{weeks[-1]} fixtures")
    out(f"  the four clubs of the moves: model P(cs) by week, (A), (B)")
    for t in ("ARS", "BHA", "COV", "TOT"):
        out(f"    {t}  " + " ".join(f"{sum(pcs[k].get(t, [])):.2f}" if len(pcs[k].get(t, [])) == 1 else
                                  ("  -  " if not pcs[k].get(t) else "+".join(f"{v:.2f}" for v in pcs[k][t])) for k in range(n))
            + f"   (A) {flat_a[t]:.2f} ({rc[t]['cs']} of {rc[t]['n']})   (B) {flat_b[t]:.2f}")
    out(f"  every club (A): " + ", ".join(f"{t} {flat_a[t]:.1f}" for t in teams))
    for label, lf, ps in (("LIFTED, Calafiori at P(start) 1.0 (item 3's matrix)", lifts, {cala["id"]: 1.0}),
                          ("LIFTED, Calafiori as the model has him", lifts, None)):
        M0, _ = matrix(a.data, a.hist, n, lf, pstart=ps)
        MA, _ = matrix(a.data, a.hist, n, lf, pstart=ps, cs=("flat", flat_a))
        MB, _ = matrix(a.data, a.hist, n, lf, pstart=ps, cs=("flat", flat_b))
        MZ, _ = matrix(a.data, a.hist, n, lf, pstart=ps, cs=("zero", None))
        fwd = {p["id"] for p in d["all_players"] if p["pos"] in (4, "FWD")}
        fmoved = [pid for M in (MA, MB, MZ) for t in range(n) for pid in fwd if M[t].get(pid) != M0[t].get(pid)]
        r_bp, _ = PL.rank_plans(squad, bank, market, M0, fts, p_start, dec, sched, hits_allowed=False)
        bp = next(e for e in r_bp if e["used"] == 2)
        out(f"  {label}  (check: no forward's value moves under any switch: {not fmoved}); this matrix's best pair: "
            f"{PLV.plan_text(bp)}")
        out(f"    {'move':<46} {'gain':>7} {'flat A':>7} {'flat B':>7} {'no CS':>7}  {'CS share':>8}")
        plans = list(named)
        if PL.plan_key(bp) not in {PL.plan_key(ev_of(p, M0)) for _, p in named if ev_of(p, M0)}:
            plans.insert(0, ("this matrix's best pair (above)", (bp["outs"], bp["ins"])))
        for tag, plan in plans:
            g = [ev_of(plan, M) for M in (M0, MA, MB, MZ)]
            if any(e is None for e in g):
                out(f"    {tag:<46} {why_not(plan) or 'not allowed'}")
                continue
            g0, ga, gb, gz = (e["gain"] for e in g)
            share = f"{(g0 - gz) / g0:8.0%}" if abs(g0) > 1e-9 else "       -"
            out(f"    {tag:<46} {g0:7.2f} {ga:7.2f} {gb:7.2f} {gz:7.2f}  {share}")
    out(f"  gain = the planner's decayed gain over GW{weeks[0]}-{weeks[-1]} (no BB, before the lost-FT value); CS share = "
        f"(gain - no CS) / gain")

    out()
    out(f"ITEM 5  THE CAPTAIN TIE (own: Gabriel v Haaland)")
    log = E.read_log(os.path.join(a.data, E.LOG_PATH))
    fc = E.forecasts(log, d)
    for name, team in (("Gabriel", "ARS"), ("Haaland", "MCI")):
        r = ours(name)
        vals = {src: next((float(x["predicted"]) for x in fc if x["source"] == src and int(x["event"]) == target
                           and int(x["player_id"]) == r["id"]), None) for src in ("own", "xg", "bottomup", "bottomup_lambda", "xp_v2")}
        out(f"  {name:<8} {team}  recorded GW{target}: " + "   ".join(f"{s} {'-' if v is None else f'{v:.2f}'}" for s, v in vals.items()))
    for opp, venue, note in (("NEW", "home", "Newcastle, at home to Arsenal"), ("FUL", "away", "Fulham, away at City")):
        r = rc[opp]
        v = r[venue]
        out(f"  {note}: all {r['n']} matches GF {r['gf']} ({r['gf'] / r['n']:.2f}/m) GA {r['ga']} ({r['ga'] / r['n']:.2f}/m), "
            f"clean sheets {r['cs']}; {venue} {v[0]} matches GF {v[1]} ({v[1] / v[0]:.2f}/m) GA {v[2]} ({v[2] / v[0]:.2f}/m)")
    path_out = os.path.join(a.out, "refresh_extra.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines).rstrip("\n") + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BM.MissingInput as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
