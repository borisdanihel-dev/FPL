"""worklog/gw_pass/gw9/named_moves.py - named moves on the planner's score for the GW9 deadline pass (Boris, Fri 30 Oct;
information only, read-only; no tool change, s8c-wip d9071b8 stays the bundle commit). Standard library only.

    python named_moves.py --code DIR --data DIR --hist DIR [--csv FILE] --out DIR

  --code   a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --csv    the bundle's xp_v2_all.csv, checked against the matrix's first column

matrix   the planner's xp_v2 horizon matrix (builder.live_matrix, as planner_live runs it); a player whose status is not
         'a' has no value in any week (the gate)
moves    Thomas -> De Cuyper; the best single move with Thomas out; the best single move with Calafiori out; roll
score    S8's rank_plans and evaluate exactly as planner_live runs them (1 free transfer, no hits, decay 0.85, Boris's
         schedule): each move's score, its parts and its rank among the planner's plans
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
NAMED = (("Thomas", None), ("De Cuyper", "BHA"))     # out (our 15), in (the market)
OUTS = ("Thomas", "Calafiori")


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--csv")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw9/named_moves.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
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
    out(f"NAMED MOVES  GW{target} (Boris, Fri 30 Oct); information, read-only, no tool change")
    out(f"  data {data_commit[:7]}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {sha256_of(os.path.abspath(__file__))}; generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  matrix: the planner's xp_v2 horizon matrix GW{weeks[0]}-{weeks[-1]} (builder.live_matrix; odds "
        f"{snap or 'none before the deadline'} where they price the fixture, else the fallback)")
    if a.csv:
        csv_rows = list(csv.DictReader(open(a.csv, encoding="utf-8", newline="")))
        bad = [r["id"] for r in csv_rows if abs(float(r["xp_v2"]) - XP[0].get(int(r["id"]), 0.0)) > 1e-9]
        out(f"  check: the GW{target} column against the bundle's {os.path.basename(a.csv)}: {len(csv_rows) - len(bad)} of "
            f"{len(csv_rows)} players equal" + ("" if not bad else f"; differ: {', '.join(bad[:10])}"))
    for name in OUTS:
        r = ours(name)
        p = by_id[r["id"]]
        out(f"  {name} ({r['team']} DEF, selling {r['selling']:.1f}): export status {p['status']}, chance_next_round "
            f"{p.get('chance_next_round')}, news \"{p.get('news', '')}\"; in the matrix: "
            + (", ".join(f"GW{u} {XP[t][r['id']]:.2f}" for t, u in enumerate(weeks) if r["id"] in XP[t]) or "no value in any week (the gate)"))
    out(f"  score: S8's rank_plans as planner_live runs it ({K0} free transfer, no hits, decay {DECAY}, Boris's schedule {SCHED}); "
        f"bank {bank:.1f}")
    scored, pool = PL.rank_plans(squad, bank, market, XP, K0, p_start, DECAY, SCHED, hits_allowed=False)
    if not scored:
        raise MissingInput("no plan scored")
    rank = {PL.plan_key(ev): i for i, ev in enumerate(scored, 1)}

    def line(label, ev):
        if ev is None:
            out(f"  {label}: none scored")
            return
        i = rank.get(PL.plan_key(ev))
        out(f"  {label}: {PLV.plan_text(ev)}  score {ev['score']:6.2f}  gain {ev['gain']:6.2f}  lostFT {ev['lost']:.2f}  weekly dxP "
            + " ".join(f"{g:+5.2f}" for g in ev["gains"])
            + (f"  rank {i} of the planner's {len(scored)} plans" if i else f"  not among the planner's {len(scored)} plans "
               f"(outside its pool, the top {PL.POOL} per position by decayed xP)") + CF.move_flag(squad, ev["outs"], ev["ins"]))
    out()
    out(f"  the planner's default: {PLV.plan_text(scored[0])} {scored[0]['score']:.2f}")
    o = ours(NAMED[0][0])
    inc = [r for r in market if r["name"] == NAMED[1][0] and r["team"] == NAMED[1][1]]
    if len(inc) != 1:
        raise MissingInput(f"{NAMED[1][0]} ({NAMED[1][1]}) is not once in the planner's market")
    rows = [r for r in squad if r["id"] != o["id"]] + inc
    named = None
    if PL.legal(rows, bank + o["selling"] - inc[0]["price"]):
        named = PL.evaluate(((o,), (inc[0],)), squad, XP, DECAY, SCHED, K0, p_start, hits_allowed=False)
    line(f"Thomas -> De Cuyper (named)", named)
    for name in OUTS:
        oid = ours(name)["id"]
        best = next((ev for ev in scored if len(ev["outs"]) == 1 and ev["outs"][0]["id"] == oid), None)
        line(f"best with {name} out", best)
    roll = next((ev for ev in scored if not ev["outs"]), None)
    line("roll", roll)
    path_out = os.path.join(a.out, "named_moves.txt")
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
