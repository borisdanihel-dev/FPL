"""worklog/gw_pass/gw10/bb_moves.py - Bench Boost transfers on the planner's score for the GW10 deadline pass (Boris,
Fri 6 Nov, step 4; information only, read-only; no tool change, s8c-wip d9071b8 stays the bundle commit). Standard
library only.

    python -I bb_moves.py --code DIR --data DIR --hist DIR [--csv FILE] --out DIR

  --code   a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --csv    the bundle's xp_v2_all.csv, checked against the gated matrix's first column

matrix     the planner's xp_v2 horizon matrix (builder.live_matrix, as planner_live runs it). Two cases:
           gate     as the bundle: a player whose status is not 'a' has no value in any week (Thomas d 50%,
                    Branthwaite d 75%: 0)
           lifted   the same, with Branthwaite's status gate lifted in every week (his own model numbers, as the
                    bundle's "if he plays" line computes them) and his GW10 P(start) set to 0.75 (cramp; Moyes
                    hopeful): xp_v2 = 0.75 x (e_xg + e_bl) / 2 + P(sub) x e_sub, xp_v2's own blend
score      S8's rank_plans and evaluate as planner_live runs them (no hits, decay 0.85, Boris's schedule), with Boris's
           2 free transfers; the Bench Boost score is planner_live.bb_rescore: week t's gain is all 15 by xP plus the
           captain (the bench at full weight)
"""
import argparse
import csv
import os
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
FTS = 2                                   # Boris: 2 free transfers this week
LIFT_NAME, LIFT_P_START = "Branthwaite", 0.75
NAMED = (("Thomas", "Slater"), ("Thomas", "Branthwaite"), ("Thomas",))


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def lifted_matrix(data_dir, hist_root, weeks_n, lift_id):
    """builder.live_matrix with one player's status gate lifted (and nothing else changed); also week 0's detail."""
    now = datetime.now(timezone.utc)
    OL, XL, SH, XV = B.OL, B.XL, B.SH, B.XV
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
    inp = E.reliability_inputs(c, gws_played=d["gameweek"])
    by_round, rows = XL.export_rows(d)
    tot = SH.team_totals(rows, {})
    gate = {int(p["id"]): p["status"] == "a" for p in d["all_players"]}
    if lift_id is not None:
        gate[lift_id] = True
    weeks, details = [], []
    for u in range(target, target + weeks_n):
        fx = XL.target_fixtures(d, u)
        lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}

        def fixtures_of(team, fx=fx):
            return [(fid, f) for fid, f in fx.items() if team in (f["home"], f["away"])]

        def lam_team(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_home"] if team == fx[fid]["home"] else lam[fid][0]["lambda_away"]

        def lam_opp(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_away"] if team == fx[fid]["home"] else lam[fid][0]["lambda_home"]
        xp, det = XL.core(inp, names, by_round, target, rows, {}, tot, prior, fixtures_of, lam_team, lam_opp,
                          ict=XL.ict_live(d), chance=XV.chance_scale(d), gate=gate)
        weeks.append(xp)
        details.append(det)
    return weeks, details


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--csv")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw10/bb_moves.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    d, path, target, XP, srcs, p_start, snap = PLV.live_inputs(a.data, a.hist)
    weeks = list(range(target, target + len(XP)))
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
    out(f"BENCH BOOST TRANSFERS  GW{target} (Boris, Fri 6 Nov, step 4); information, read-only, no tool change")
    out(f"  data {data_commit[:7]}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {sha256_of(os.path.abspath(__file__))}; generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  matrix: the planner's xp_v2 horizon matrix GW{weeks[0]}-{weeks[-1]} (builder.live_matrix; odds "
        f"{snap or 'none before the deadline'} where they price the fixture, else the fallback)")
    if a.csv:
        csv_rows = list(csv.DictReader(open(a.csv, encoding="utf-8", newline="")))
        bad = [r["id"] for r in csv_rows if abs(float(r["xp_v2"]) - XP[0].get(int(r["id"]), 0.0)) > 1e-9]
        out(f"  check: the GW{target} column against the bundle's {os.path.basename(a.csv)}: {len(csv_rows) - len(bad)} of "
            f"{len(csv_rows)} players equal" + ("" if not bad else f"; differ: {', '.join(bad[:10])}"))
    lift = ours(LIFT_NAME)
    same, _ = lifted_matrix(a.data, a.hist, len(XP), None)
    out(f"  check: this script's copy of the matrix, no gate lifted, equals the planner's: "
        f"{all(same[t] == XP[t] for t in range(len(XP)))}")
    XL_, det = lifted_matrix(a.data, a.hist, len(XP), lift["id"])
    moved = [(t, pid) for t in range(len(XP)) for pid in set(XP[t]) | set(XL_[t]) if pid != lift["id"] and XP[t].get(pid) != XL_[t].get(pid)]
    out(f"  check: lifting {LIFT_NAME}'s gate moves no other player's value: {not moved}")
    if lift["id"] not in det[0]:
        raise MissingInput(f"{LIFT_NAME} has no xp_v2 with the gate lifted (minutes or fixture)")
    d0 = det[0][lift["id"]]
    x0 = LIFT_P_START * (d0["e_xg"] + d0["e_bl"]) / 2 + d0["p_sub"] * d0["e_sub"]
    XL_[0] = {**XL_[0], lift["id"]: x0}
    for name in ("Thomas", "Branthwaite", "Slater"):
        r = ours(name)
        p = by_id[r["id"]]
        out(f"  {name} ({r['team']}, selling {r['selling']:.1f}): status {p['status']}, chance_next_round {p.get('chance_next_round')}, "
            f"news \"{p.get('news', '')}\"; gate: " + (", ".join(f"GW{u} {XP[t][r['id']]:.2f}" for t, u in enumerate(weeks) if r["id"] in XP[t])
                                                      or "no value in any week"))
    out(f"  {LIFT_NAME} lifted: GW{target} {x0:.2f} at P(start) {LIFT_P_START} (the model's {d0['p_start']:.2f}, scaled by chance, gives "
        f"{det[0][lift['id']]['p_start'] * (d0['e_xg'] + d0['e_bl']) / 2 + d0['p_sub'] * d0['e_sub']:.2f}; P(sub) {d0['p_sub']:.2f}); "
        f"later weeks his own model numbers: " + ", ".join(f"GW{u} {XL_[t].get(lift['id'], 0.0):.2f}" for t, u in enumerate(weeks) if t))
    out(f"  score: S8's rank_plans and evaluate ({FTS} free transfers, no hits, decay {DECAY}, Boris's schedule {SCHED}); bank {bank:.1f}; "
        f"Bench Boost = planner_live.bb_rescore (GW{target}'s gain: all 15 by xP + the captain)")
    for label, M in (("UNDER THE GATE (Thomas, Branthwaite 0)", XP), (f"WITH {LIFT_NAME.upper()} LIFTED (GW{target} P(start) {LIFT_P_START})", XL_)):
        scored, _ = PL.rank_plans(squad, bank, market, M, FTS, p_start, DECAY, SCHED, hits_allowed=False)
        if not scored:
            raise MissingInput("no plan scored")
        bb = PLV.bb_rescore(scored, squad, M[0])
        plain = {PL.plan_key(ev): (i, ev) for i, ev in enumerate(scored, 1)}
        boost = {PL.plan_key(ev): (i, ev) for i, ev in enumerate(bb, 1)}
        out()
        out(f"  {label}: {len(scored)} plans")
        out(f"    {'':<40} {'BB score':>8} {'GW' + str(target) + ' gain':>9} {'rank':>5}   {'no-BB':>6} {'rank':>5}   plan")

        def row(tag, key):
            if key is None:
                out(f"    {tag:<40} none scored (outside the pool of the top {PL.POOL} per position, or illegal)")
                return
            (ib, eb), (ip, ep) = boost[key], plain[key]
            out(f"    {tag:<40} {eb['score']:8.2f} {eb['gains'][0]:+9.2f} {ib:>5}   {ep['score']:6.2f} {ip:>5}   {PLV.plan_text(ep)}"
                + CF.move_flag(squad, ep["outs"], ep["ins"]))

        def best(evs, test):
            ev = next((e for e in evs if test(e)), None)
            return PL.plan_key(ev) if ev else None
        row("best with a Bench Boost", best(bb, lambda e: True))
        row("best pair with a Bench Boost", best(bb, lambda e: e["used"] == 2))
        row("best without a Bench Boost", best(scored, lambda e: True))
        row("best pair without a Bench Boost", best(scored, lambda e: e["used"] == 2))
        for names in NAMED:
            ids = {ours(n)["id"] for n in names}
            tag = " + ".join(names) + (" out" if len(names) > 1 else " out only (roll one)")
            row(f"{tag}, best under BB", best(bb, lambda e, ids=ids: {o["id"] for o in e["outs"]} == ids))
            row(f"{tag}, best without BB", best(scored, lambda e, ids=ids: {o["id"] for o in e["outs"]} == ids))
        row("roll both", best(scored, lambda e: not e["outs"]))
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
