"""worklog/gw_pass/gw8/gibbs_white.py - the named move Saka -> Gibbs-White beside Saka -> Rogers, for Friday's GW8
deadline pass (Boris, Fri 23 Oct; information only, read-only; no tool change, s8c-wip d9071b8 stays the bundle
commit). Standard library only.

    python gibbs_white.py --code DIR --data DIR --hist DIR [--csv FILE] --out DIR

  --code   a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --csv    the bundle's xp_v2_all.csv, checked against the matrix's GW8 column

matrix   the planner's xp_v2 horizon matrix GW8-13 (builder.live_matrix), Saka 0 in every week (case (a): the gate
         drops him)
twice    1. as the matrix has Gibbs-White
         2. his P(start) in the reliability inputs set to 1.0 (in memory only) for GW8-13, every term of his xp_v2
            recomputed by the same code; every other player's value must be unchanged, or the run stops
score    S8's evaluate exactly as planner_live runs it (1 free transfer, no hits, decay 0.85, Boris's schedule), and
         the move's rank among the planner's plans on the same matrix
"""
import argparse
import csv
import os
import subprocess
import sys
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
K0 = PLV.FREE_TRANSFERS
OUT_P = ("Saka", "ARS")
INS = (("Gibbs-White", "NFO"), ("Rogers", "CHE"))


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def matrix_p_start(data, hist, pid, value):
    """builder.live_matrix with player pid's P(start) in the reliability inputs set to `value`, in memory."""
    orig = E.reliability_inputs

    def patched(*a, **kw):
        inp = orig(*a, **kw)
        if pid not in inp["players"]:
            raise MissingInput(f"player {pid} is not in the reliability inputs")
        inp["players"][pid]["p_start"] = value
        return inp
    E.reliability_inputs = patched
    try:
        return B.live_matrix(data, hist, PL.HORIZON)
    finally:
        E.reliability_inputs = orig


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--csv")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw8/gibbs_white.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
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
    sk = [r for r in squad if (r["name"], r["team"]) == OUT_P]
    if len(sk) != 1:
        raise MissingInput("Saka (ARS) is not one player of our 15")
    saka = sk[0]
    if any(saka["id"] in XP[t] for t in range(len(XP))):
        raise MissingInput("Saka has a value in the matrix as built: not case (a)")
    ins = {}
    for name, team in INS:
        m = [r for r in market if (r["name"], r["team"]) == (name, team)]
        if len(m) != 1:
            raise MissingInput(f"{name} ({team}) is not once in the planner's market (status 'a', 45+ minutes in the last four)")
        ins[name] = m[0]
    gw = ins["Gibbs-White"]
    gw_row = next(p for p in d["all_players"] if p["id"] == gw["id"])
    inp = E.reliability_inputs(E.canonical_through(E.canonical_from_export(d), d["gameweek"]), gws_played=d["gameweek"])
    gw_ps = inp["players"][gw["id"]]["p_start"]
    _, _, t1, XP1, _ = matrix_p_start(a.data, a.hist, gw["id"], 1.0)
    if t1 != target:
        raise MissingInput("the edited matrix is for another gameweek")
    for t in range(len(XP)):
        ids = (set(XP1[t]) | set(XP[t])) - {gw["id"]}
        moved = [pid for pid in ids if XP1[t].get(pid) != XP[t].get(pid)]
        if moved:
            raise MissingInput(f"GW{weeks[t]}: setting Gibbs-White's P(start) moves {len(moved)} other players")
    data_commit = subprocess.run(["git", "-C", a.data, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    out(f"NAMED MOVE  Saka -> Gibbs-White beside Saka -> Rogers, GW{target} (Boris, Fri 23 Oct); information, read-only, no tool change")
    out(f"  data {data_commit[:7]}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {sha256_of(os.path.abspath(__file__))}; generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  matrix: the planner's xp_v2 horizon matrix GW{weeks[0]}-{weeks[-1]} (builder.live_matrix; odds "
        f"{snap or 'none before the deadline'} where they price the fixture, else the fallback); Saka 0 in every week (the gate; "
        f"export status {next(p for p in d['all_players'] if p['id'] == saka['id'])['status']})")
    if a.csv:
        csv_rows = list(csv.DictReader(open(a.csv, encoding="utf-8", newline="")))
        bad = [r["id"] for r in csv_rows if abs(float(r["xp_v2"]) - XP[0].get(int(r["id"]), 0.0)) > 1e-9]
        out(f"  check: the GW{target} column against the bundle's {os.path.basename(a.csv)}: {len(csv_rows) - len(bad)} of "
            f"{len(csv_rows)} players equal" + ("" if not bad else f"; differ: {', '.join(bad[:10])}"))
    out(f"  Gibbs-White (NFO MID, id {gw['id']}, {gw['price']:.1f}): export status {gw_row['status']}, chance_next_round "
        f"{gw_row.get('chance_next_round')}, starts_last4 {gw_row.get('starts_last4')}, mins_last4 {gw_row.get('mins_last4')}; "
        f"the matrix's P(start) {gw_ps:.2f}")
    out(f"  score: S8's evaluate as planner_live runs it ({K0} free transfer, no hits, decay {DECAY}, Boris's schedule {SCHED}); "
        f"Saka's selling price {saka['selling']:.1f}, bank {bank:.1f}")
    out()
    for label, M in (("1. as the matrix has him", XP), (f"2. Gibbs-White's P(start) 1.0 from GW{target} (in memory; every other player unchanged)", XP1)):
        out(label)
        out(f"  Gibbs-White xp_v2: " + ", ".join(f"GW{u} {M[t].get(gw['id'], 0.0):.2f}" for t, u in enumerate(weeks)))
        scored, pool = PL.rank_plans(squad, bank, market, M, K0, p_start, DECAY, SCHED, hits_allowed=False)
        keys = {PL.plan_key(ev): i for i, ev in enumerate(scored, 1)}
        out(f"  the planner's default on this matrix: {PLV.plan_text(scored[0])} {scored[0]['score']:.2f}")
        for name, _ in INS:
            inc = ins[name]
            plan = ((saka,), (inc,))
            rows = [r for r in squad if r["id"] != saka["id"]] + [inc]
            legal = PL.legal(rows, bank + saka["selling"] - inc["price"])
            ev = PL.evaluate(plan, squad, M, DECAY, SCHED, K0, p_start, hits_allowed=False) if legal else None
            if ev is None:
                out(f"  Saka -> {name}: not a legal plan (budget, club cap or GK+DEF cap)")
                continue
            rank = keys.get(PL.plan_key(ev))
            out(f"  Saka -> {name} ({inc['team']}, {inc['price']:.1f}): score {ev['score']:6.2f}  gain {ev['gain']:6.2f}  lostFT "
                f"{ev['lost']:.2f}  weekly dxP " + " ".join(f"{g:+5.2f}" for g in ev["gains"])
                + (f"  rank {rank} of the planner's {len(scored)} plans" if rank else f"  not among the planner's {len(scored)} plans "
                   f"(outside its pool, the top {PL.POOL} per position by decayed xP)") + CF.move_flag(squad, (saka,), (inc,)))
        out()
    path_out = os.path.join(a.out, "gibbs_white.txt")
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
