"""worklog/gw_pass/gw12/bb_timing.py - Bench Boost timing, GW14 v GW15 (Boris, GW12 deadline pass of Fri 27 Nov,
point 4: "bb_timing for GW14 v GW15 (the Bench Boost plan is GW14)"; information only, read-only; no tool change,
master stays the bundle commit). Copied from worklog/gw_pass/gw11/bb_timing.py. Standard library only.

    python -I bb_timing.py --code DIR --data DIR --hist DIR --out DIR --squad TAG=MOVES [--squad ...]

  --code   a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --squad  as worklog/gw_pass/gw12/s7_post_transfer.py, e.g. "(a) best single move=Calafiori:ARS>Senesi:BOU"

matrix   the planner's xp_v2 horizon matrix GW12-17 (planner_live.live_inputs: builder.live_matrix), and the same with
         Thiago lifted from GW14 (worklog/gw_pass/gw12/bb_moves.py's matrix, the transfer tables' lifted case)
value    the Bench Boost value each week with the squad held: the four outside xp_v2's best XI (planner_live.bb_value
         minus S8's xi_value), for the current 15 and each candidate squad after GW12's transfer; GW14 - GW15 printed
not      later transfers: the squad is held from GW12 to GW17 (an upper bound on doing nothing, not a plan). The S7
         calculator's own-xP V_BB for GW12-19 is in s7_post_transfer.txt.
"""
import argparse
import importlib.util
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(f"gw12_{name}", os.path.join(HERE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BM = _load("bb_moves")                  # lifted_matrix, and the --code imports (builder, chips, planner, ...)
S7 = _load("s7_post_transfer")          # post_squad, parse_squad
CH, E, PL, PLV = BM.CH, BM.E, BM.PL, BM.PLV
from console_utf8 import utf8_console   # noqa: E402  (on the path through --code)
from provenance import Run, sha256_of   # noqa: E402


def bench_value(rows, xp):
    """The four outside xp_v2's best XI: bb_value (all 15 + captain) minus xi_value (best XI + captain)."""
    return PLV.bb_value(rows, xp) - PL.xi_value(PL.squad_by_pos(rows, xp))


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--squad", action="append", required=True)
    a = ap.parse_args(argv)
    run_ = Run("worklog/gw_pass/gw12/bb_timing.py", a.out, argv if argv is not None else sys.argv[1:], root=BM.CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    d, path, target, XP, srcs, p_start, snap = PLV.live_inputs(a.data, a.hist)
    weeks = list(range(target, target + len(XP)))
    cur = CH.my_squad(d)
    names = {r["name"]: r for r in cur}
    if "Thiago" not in names:
        raise BM.MissingInput("Thiago is not in our 15")
    lifts = {names["Thiago"]["id"]: (BM.THIAGO_FROM, BM.THIAGO_FROM)}
    XL_, _, _ = BM.lifted_matrix(a.data, a.hist, len(XP), lifts)
    same, _, _ = BM.lifted_matrix(a.data, a.hist, len(XP), {})
    data_head = subprocess.run(["git", "-C", a.data, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    out(f"BENCH BOOST TIMING ON THE POST-TRANSFER SQUADS  GW{target}-{weeks[-1]} (Boris, GW12 pass of Fri 27 Nov, point 4); information, "
        f"read-only, no tool change")
    out(f"  data {data_head}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {sha256_of(os.path.abspath(__file__))}; generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  check: bb_moves' copy of the matrix, no gate lifted, equals the planner's: {all(same[t] == XP[t] for t in range(len(XP)))}")
    out(f"  value: the four outside xp_v2's best XI, the squad held GW{target}-{weeks[-1]} (no later transfers); BB = that week's bench at full weight")
    squads = [("current 15", "", cur)]
    for text in a.squad:
        tag, label, moves = S7.parse_squad(text)
        rows, bank_after, _ = S7.post_squad(d, cur, moves)
        squads.append((tag, f"{label} (bank after {bank_after:.1f})", rows))
    i14, i15 = weeks.index(14), weeks.index(15)
    for label, M in (("UNDER THE GATE (Thiago 0)", XP),
                     (f"LIFTED (Thiago from GW{BM.THIAGO_FROM} at chance 100)", XL_)):
        out()
        out(f"  {label}")
        out(f"    {'squad':<12}" + "".join(f"{'GW' + str(u):>7}" for u in weeks) + f"  GW14-GW15   best week   GW{target} rank   GW14 bench")
        for tag, desc, rows in squads:
            vals = [bench_value(rows, M[t]) for t in range(len(weeks))]
            order = sorted(range(len(weeks)), key=lambda t: -vals[t])
            _, outfield, gk = CH.xi_and_bench(rows, M[0])
            bench0 = [gk] + list(outfield)
            if abs(sum(M[0].get(r["id"], 0.0) for r in bench0) - vals[0]) > 1e-9:
                raise BM.MissingInput(f"{tag}: the GW{target} bench differs from bb_value - xi_value")
            _, of14, gk14 = CH.xi_and_bench(rows, M[i14])
            out(f"    {tag:<12}" + "".join(f"{v:7.2f}" for v in vals) + f"  {vals[i14] - vals[i15]:+9.2f}   GW{weeks[order[0]]:<8} "
                f"{order.index(0) + 1:>5} of {len(weeks)}   " + ", ".join(f"{r['name']} {M[i14].get(r['id'], 0.0):.2f}" for r in [gk14] + list(of14)))
        for tag, desc, rows in squads[1:]:
            out(f"    {tag}: {desc}")
    path_out = os.path.join(a.out, "bb_timing.txt")
    os.makedirs(a.out, exist_ok=True)
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines).rstrip("\n") + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (BM.MissingInput, S7.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
