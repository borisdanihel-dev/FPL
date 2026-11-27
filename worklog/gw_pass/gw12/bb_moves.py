"""worklog/gw_pass/gw12/bb_moves.py - the GW12 transfer tables, the clean-sheet sensitivity and the captain block
(Boris, GW12 deadline pass of Fri 27 Nov, points 2-3, verbatim in prereg/bundle.md with the reading pinned before this
code). Information only, read-only; no tool change, master stays the bundle commit. Standard library only. Built from
worklog/gw_pass/gw11/bb_moves.py (lifted_matrix) and gw11/refresh_extra.py (the switches).

    python -I bb_moves.py --code DIR --data DIR --hist DIR [--csv FILE] --out DIR

  --code   a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --csv    the bundle's xp_v2_all.csv, checked against the gated matrix's first column

matrix   the planner's xp_v2 horizon matrix GW12-17 (builder.live_matrix, as planner_live runs it), four cases:
           gated            as the bundle: a player whose status is not 'a' has no value (Thiago s: 0)
           lifted           Thiago's gate lifted from GW14 (Boris: "banned until GW14"), taken as available
                            (chance 100): P(start) = his starts in the last four / 4, P(sub) unscaled
           + Calafiori 1.0  each of the two with Calafiori's P(start) at 1.0 in every week (Boris: "his GW8 cameo is
                            still in the window"), nothing else changed
score    S8's rank_plans and evaluate as planner_live runs them: 1 free transfer, no hits (so single moves and roll),
         decay 0.85, Boris's schedule, bank as the export; top five single moves and roll, with ranks
cs       the clean-sheet probability alone flattened in GW12-17, every team, both xp_v2 blends (goals-conceded, attack,
         DEFCON and minutes keep their fixture values): (A) the team's realised 2026/27 clean-sheet rate before the
         deadline; (B) the mean of the model's own P(cs) over the team's GW12-17 fixtures. CS share = (gain - gain with
         every P(cs) = 0) / gain, XIs re-chosen in each (not additive). Top three single moves of the lifted matrix and
         of the lifted + Calafiori matrix.
captain  the top four of our 15 by xp_v2 (the gated GW12 column, the captain rule's input) with own, xg, bottomup,
         bottomup_lambda and xp_v2 as recorded for GW12; the ARS-MCI odds (each side's lambda and P(cs))
"""
import argparse
import csv
import os
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone


def _arg(argv, name):
    for i, x in enumerate(argv):
        if x == name and i + 1 < len(argv):
            return argv[i + 1]
        if x.startswith(name + "="):
            return x.split("=", 1)[1]
    sys.exit(f"{name} is required")


CODE = os.path.abspath(_arg(sys.argv[1:], "--code"))
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(CODE, "tools"))
import builder as B                                               # noqa: E402
import capflag as CF                                              # noqa: E402
import chips as CH                                                # noqa: E402
import fpl_edge as E                                              # noqa: E402
import planner as PL                                              # noqa: E402
import planner_live as PLV                                        # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run, sha256_of                             # noqa: E402

DECAY = PLV.DECAY
SCHED = PL.SCHEDULES[PLV.SCHEDULE]
FTS = 1                                   # Boris: 1 free transfer
THIAGO_FROM = 14                         # Boris: "Thiago banned until GW14"
TOPN = 5
OL_MOD = sys.modules[B.OL.__name__]
XL = B.XL
assert XL.OL is OL_MOD, "xp_v2_live and builder must share odds_lambda"
EXP_CS = OL_MOD.p_clean_sheet


class MissingInput(Exception):
    pass


class TLam(float):
    """lambda_opp carrying the player's team, so the clean-sheet probability alone can be replaced."""
    def __new__(cls, v, team):
        o = float.__new__(cls, v)
        o.team = team
        return o


def matrix(data_dir, hist_root, weeks_n, lifts, pstart=None, cs=None):
    """builder.live_matrix with status gates lifted per player and week (lifts {pid: (first, normal_from)}, as
    gw11/bb_moves.lifted_matrix), pstart {pid: P(start)} in every week, and cs None (as is), ("flat", {team: P(cs)})
    or ("zero", None) - the clean-sheet probability only. Returns (weeks, model P(cs) per team and week, lambdas of
    the first week {fid: (lambda_home, lambda_away, source)}, the export d)."""
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
    weeks, pcs, lam0 = [], [], {}

    def patched(lam):
        if isinstance(lam, TLam) and cs is not None:
            return 0.0 if cs[0] == "zero" else cs[1][lam.team]
        return EXP_CS(lam)
    OL_MOD.p_clean_sheet = patched
    try:
        for u in range(target, target + weeks_n):
            fx = XL.target_fixtures(d, u)
            lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}
            if u == target:
                lam0 = {fid: (v[0]["lambda_home"], v[0]["lambda_away"], v[1] if len(v) > 1 else "?") for fid, v in lam.items()}
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
    return weeks, pcs, lam0, d


def lifted_matrix(data_dir, hist_root, weeks_n, lifts):
    """gw11/bb_moves.lifted_matrix's interface for bb_timing: (weeks, None, d)."""
    w, _, _, d = matrix(data_dir, hist_root, weeks_n, lifts)
    return w, None, d


def realised_cs(data_dir, before):
    """{short_name: {cs, n}} from finished league fixtures kicked off before `before`."""
    con = sqlite3.connect(os.path.join(data_dir, "fpl.sqlite"))
    short = dict(con.execute("select id, short_name from teams"))
    out = {}
    for h, a, hs, as_, ko in con.execute("select team_h, team_a, team_h_score, team_a_score, kickoff_time from fixtures "
                                         "where finished = 1"):
        if datetime.fromisoformat(ko.replace("Z", "+00:00")) >= before:
            continue
        for team, ga in ((short[h], as_), (short[a], hs)):
            r = out.setdefault(team, {"cs": 0, "n": 0})
            r["cs"] += ga == 0
            r["n"] += 1
    con.close()
    return out


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--csv")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw12/bb_moves.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
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
        raise MissingInput(f"no budget: {why}")
    bank = budget - sum(r["selling"] for r in squad)
    market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
               "status": p["status"]} for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    by_id = {p["id"]: p for p in d["all_players"]}

    def ours(name):
        m = [r for r in squad if r["name"] == name]
        if len(m) != 1:
            raise MissingInput(f"{name} is not one player of our 15")
        return m[0]
    data_commit = subprocess.run(["git", "-C", a.data, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    deadline = B.OL.sqlite_tables(a.data)[1].get(target)
    out(f"TRANSFER TABLES, CLEAN-SHEET SENSITIVITY AND CAPTAIN  GW{target} (Boris, GW12 pass of Fri 27 Nov, points 2-3); "
        f"information, read-only, no tool change")
    out(f"  data {data_commit[:7]}, export {os.path.basename(path)} (generated {d.get('generated', '?')}); code {run_.commit[:7]} "
        f"(modified tracked files {run_.dirty}); script sha256 {sha256_of(os.path.abspath(__file__))}; "
        f"generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  matrix: the planner's xp_v2 horizon matrix GW{weeks[0]}-{weeks[-1]} (builder.live_matrix; odds "
        f"{snap or 'none before the deadline'} where they price the fixture, else the fallback)")
    if a.csv:
        csv_rows = list(csv.DictReader(open(a.csv, encoding="utf-8", newline="")))
        bad = [r["id"] for r in csv_rows if abs(float(r["xp_v2"]) - XP[0].get(int(r["id"]), 0.0)) > 1e-9]
        out(f"  check: the GW{target} column against the bundle's {os.path.basename(a.csv)}: {len(csv_rows) - len(bad)} of "
            f"{len(csv_rows)} players equal" + ("" if not bad else f"; differ: {', '.join(bad[:10])}"))
    thiago, cala = ours("Thiago"), ours("Calafiori")
    lifts = {thiago["id"]: (THIAGO_FROM, THIAGO_FROM)}
    G0, _, _, _ = matrix(a.data, a.hist, n, {})
    out(f"  check: this script's matrix, no switch, equals the planner's: {all(G0[t] == XP[t] for t in range(n))}")
    L0, pcs, lam0, _ = matrix(a.data, a.hist, n, lifts)
    G1, _, _, _ = matrix(a.data, a.hist, n, {}, pstart={cala["id"]: 1.0})
    L1, _, _, _ = matrix(a.data, a.hist, n, lifts, pstart={cala["id"]: 1.0})
    moved = [(t, pid) for M, R, keep in ((L0, G0, thiago["id"]), (G1, G0, cala["id"]), (L1, L0, cala["id"]))
             for t in range(n) for pid in set(M[t]) | set(R[t]) if pid != keep and M[t].get(pid) != R[t].get(pid)]
    out(f"  check: the Thiago lift and Calafiori's P(start) 1.0 each move no other player's value: {not moved}")
    tp = by_id[thiago["id"]]
    out(f"  Thiago ({thiago['team']}, selling {thiago['selling']:.1f}): status {tp['status']}, chance {tp.get('chance_next_round')}, "
        f"news \"{tp.get('news', '')}\"; gated: no value; lifted: " + ", ".join(f"GW{u} {L0[t].get(thiago['id'], 0.0):.2f}" for t, u in enumerate(weeks)))
    cp = by_id[cala["id"]]
    out(f"  Calafiori ({cala['team']}, selling {cala['selling']:.1f}): status {cp['status']}, chance {cp.get('chance_next_round')}; "
        f"model P(start) {p_start.get(cala['id'], 0.0):.2f}; xp_v2 " + ", ".join(f"GW{u} {G0[t].get(cala['id'], 0.0):.2f}" for t, u in enumerate(weeks))
        + "; at P(start) 1.0 " + ", ".join(f"GW{u} {G1[t].get(cala['id'], 0.0):.2f}" for t, u in enumerate(weeks)))
    out(f"  score: S8's rank_plans and evaluate ({FTS} free transfer, no hits: single moves and roll; decay {DECAY}, Boris's "
        f"schedule {SCHED}); bank {bank:.1f}")

    best = {}
    for key, label, M in (("G0", "GATED (Thiago 0)", G0),
                          ("L0", f"LIFTED (Thiago from GW{THIAGO_FROM} at chance 100)", L0),
                          ("G1", "GATED, Calafiori at P(start) 1.0", G1),
                          ("L1", f"LIFTED (Thiago from GW{THIAGO_FROM}), Calafiori at P(start) 1.0", L1)):
        scored, _ = PL.rank_plans(squad, bank, market, M, FTS, p_start, DECAY, SCHED, hits_allowed=False)
        if not scored:
            raise MissingInput("no plan scored")
        best[key] = scored
        out()
        out(f"  {label}: {len(scored)} plans")
        out(f"    {'#':>4} {'score':>6} {'gain':>6} {'lostFT':>6}   weekly dxP GW{weeks[0]}-{weeks[-1]}            plan")
        roll_i = next(i for i, e in enumerate(scored, 1) if not e["outs"])
        for i, e in enumerate(scored, 1):
            if i <= TOPN or i == roll_i:
                out(f"    {i:>4} {e['score']:6.2f} {e['gain']:6.2f} {e['lost']:6.2f}   "
                    + " ".join(f"{g:+5.1f}" for g in e["gains"]) + f"   {PLV.plan_text(e)}" + CF.move_flag(squad, e["outs"], e["ins"]))

    out()
    if deadline is None:
        raise MissingInput("no deadline for the target in fpl.sqlite")
    rc = realised_cs(a.data, deadline)
    teams = sorted({t for wk in pcs for t in wk})
    missing = [t for t in teams if not rc.get(t, {}).get("n")]
    if missing:
        raise MissingInput(f"no finished league match for {', '.join(missing)}")
    flat_a = {t: rc[t]["cs"] / rc[t]["n"] for t in teams}
    flat_b = {t: sum(v for wk in pcs for v in wk.get(t, [])) / sum(len(wk.get(t, [])) for wk in pcs) for t in teams}
    out(f"CLEAN-SHEET SENSITIVITY (only P(cs) flattened, GW{weeks[0]}-{weeks[-1]}, every team; goals-conceded, attack, DEFCON and "
        f"minutes unchanged; the reading of 'season-average' is open: both printed)")
    out(f"  (A) the realised 2026/27 clean-sheet rate before the deadline; (B) the mean of the model's own P(cs) over the team's "
        f"GW{weeks[0]}-{weeks[-1]} fixtures")
    for label, lf, ps, key in ((f"LIFTED (Thiago from GW{THIAGO_FROM})", lifts, None, "L0"),
                               (f"LIFTED, Calafiori at P(start) 1.0", lifts, {cala["id"]: 1.0}, "L1")):
        M0 = L0 if key == "L0" else L1
        MA, _, _, _ = matrix(a.data, a.hist, n, lf, pstart=ps, cs=("flat", flat_a))
        MB, _, _, _ = matrix(a.data, a.hist, n, lf, pstart=ps, cs=("flat", flat_b))
        MZ, _, _, _ = matrix(a.data, a.hist, n, lf, pstart=ps, cs=("zero", None))
        fwd = {p["id"] for p in d["all_players"] if p["pos"] in (4, "FWD")}
        fmoved = [pid for M in (MA, MB, MZ) for t in range(n) for pid in fwd if M[t].get(pid) != M0[t].get(pid)]
        top = [e for e in best[key] if e["outs"]][:3]
        clubs = sorted({r["team"] for e in top for r in list(e["outs"]) + list(e["ins"])})
        out(f"  {label}  (check: no forward's value moves under any switch: {not fmoved})")
        out(f"    clubs of the moves: model P(cs) GW{weeks[0]}-{weeks[-1]}, (A), (B)")
        for t in clubs:
            out(f"      {t}  " + " ".join(("+".join(f"{v:.2f}" for v in pcs[k][t]) if pcs[k].get(t) else "  -  ") for k in range(n))
                + f"   (A) {flat_a[t]:.2f} ({rc[t]['cs']} of {rc[t]['n']})   (B) {flat_b[t]:.2f}")
        out(f"    {'move':<44} {'gain':>7} {'flat A':>7} {'flat B':>7} {'no CS':>7}  {'CS share':>8}")
        for e in top:
            plan = (e["outs"], e["ins"])
            g = [PL.evaluate(plan, squad, M, DECAY, SCHED, FTS, p_start, hits_allowed=False) for M in (M0, MA, MB, MZ)]
            if any(x is None for x in g):
                out(f"    {PLV.plan_text(e):<44} not scored")
                continue
            g0, ga, gb, gz = (x["gain"] for x in g)
            share = f"{(g0 - gz) / g0:8.0%}" if abs(g0) > 1e-9 else "       -"
            out(f"    {PLV.plan_text(e):<44} {g0:7.2f} {ga:7.2f} {gb:7.2f} {gz:7.2f}  {share}")
    out(f"  every club (A): " + ", ".join(f"{t} {flat_a[t]:.2f}" for t in teams))
    out(f"  gain = the planner's decayed gain over GW{weeks[0]}-{weeks[-1]} (before the lost-FT value); CS share = (gain - no CS) / gain")

    out()
    log = E.read_log(os.path.join(a.data, E.LOG_PATH))
    fc = E.forecasts(log, d)
    srcs_ = ("own", "xg", "bottomup", "bottomup_lambda", "xp_v2")
    rec = {r["id"]: {s: next((float(x["predicted"]) for x in fc if x["source"] == s and int(x["event"]) == target
                              and int(x["player_id"]) == r["id"]), None) for s in srcs_} for r in squad}
    top_x = sorted((r for r in squad if XP[0].get(r["id"])), key=lambda r: -XP[0][r["id"]])[:4]
    top_o = sorted((r for r in squad if rec[r["id"]]["own"] is not None), key=lambda r: -rec[r["id"]]["own"])[:4]
    am_ids = [ours(nm) for nm in ("Gabriel", "Calafiori", "Haaland")]       # Boris: plus Gabriel, Calafiori and Haaland
    rows_c = sorted({r["id"]: r for r in top_x + top_o + am_ids}.values(), key=lambda r: -XP[0].get(r["id"], 0.0))
    out(f"CAPTAIN (GW{target}): the top four of our 15 by xp_v2 (the gated column, the captain rule's input) and by own, and "
        f"Gabriel, Calafiori and Haaland (ARS-MCI), with the recorded GW{target} rows")
    out(f"    {'player':<14} {'club':<4} {'pos':<3}  {'xp_v2 live':>10}  " + "  ".join(f"{s:>15}" for s in srcs_) + "   why listed")
    for r in rows_c:
        why_ = [w for w, grp in (("xp_v2 top 4", top_x), ("own top 4", top_o), ("ARS-MCI", am_ids)) if r in grp]
        out(f"    {r['name']:<14} {r['team']:<4} {str(r['pos']):<3}  {XP[0].get(r['id'], 0.0):10.2f}  "
            + "  ".join(f"{('-' if v is None else f'{v:.2f}'):>15}" for v in rec[r["id"]].values()) + "   " + ", ".join(why_))
    am = [(fid, v) for fid, v in lam0.items() if fid in ("ARS-MCI", "MCI-ARS")]
    if not am:
        out("  ARS-MCI: no such GW12 fixture in the export - missing input")
    for fid, (lh, la, src) in am:
        h, aw = fid.split("-")
        out(f"  odds {fid} (GW{target}, {src}): lambda {h} {lh:.2f}, lambda {aw} {la:.2f}; P(cs) {h} {EXP_CS(la):.3f}, "
            f"P(cs) {aw} {EXP_CS(lh):.3f}")
    path_out = os.path.join(a.out, "bb_moves.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines).rstrip("\n") + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MissingInput as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
