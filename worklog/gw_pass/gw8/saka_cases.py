"""worklog/gw_pass/gw8/saka_cases.py - Saka's two cases for Friday's GW8 deadline pass (Boris, Thu 22 Oct;
information only, read-only; no tool change, s8c-wip d9071b8 stays the bundle commit). Standard library only.

    python saka_cases.py --code DIR --bb FILE --data DIR --hist DIR --ban FILE [--csv FILE] --out DIR [--beam M1 M2]

  --code   a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --bb     bb_timing.py as committed (worklog/gw_pass/gw8): its plan search is reused unchanged
  --ban    W3's ban-risk lines (fpl_squad.ban_risk) on the same data
  --csv    the bundle's xp_v2_all.csv, checked against the matrix's GW8 column

matrix   the planner's xp_v2 horizon matrix GW8-13 (builder.live_matrix, as planner_live and bb_timing use it)
cases    (a) Saka 0 in every week: the matrix as built (the gate drops a player whose status is not 'a')
         (b) Saka 0 in GW8-9; in GW10-13 his values as an available player: the same matrix built with his export
             row set to status 'a' and chance_next_round 100, in memory only (nothing written); every other
             player's value must be unchanged in all six weeks, or the run stops
planner  planner_live's run on each case's matrix (S8's rank_plans: no hits, 1 FT, decay 0.85, Boris's schedule; no
         ban adjustment, as the planner runs): its default, the best single transfer for GW8, the best with Saka out
plans    bb_timing's A (Bench Boost GW8: the best single transfer now) and C (Bench Boost GW10: the best use of
         transfers GW8-10, a beam at two widths), each followed by the planner's default; Thiago's GW9 value
         x (1 - P(ban)) from W3's ban-risk line, as in bb_timing
"""
import argparse
import copy
import csv
import importlib.util
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
BB_PATH = os.path.abspath(_arg(sys.argv[1:], "--bb"))
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(CODE, "tools"))
import builder as B                                               # noqa: E402
import chips as CH                                                # noqa: E402
import fpl_edge as E                                              # noqa: E402
import planner as PL                                              # noqa: E402
import planner_live as PLV                                        # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run, sha256_of                             # noqa: E402

_spec = importlib.util.spec_from_file_location("bb_timing", BB_PATH)
BB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BB)

SAKA = ("Saka", "ARS")
FROM_WEEK = 2                       # case (b): available from GW10 = the matrix's third week


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def matrix_with(data, hist, edit):
    """builder.live_matrix on the newest export with `edit` applied to an in-memory copy of it."""
    orig = CH.newest_export

    def patched(data_dir):
        d, path = orig(data_dir)
        d = copy.deepcopy(d)
        edit(d)
        return d, path
    CH.newest_export = patched
    try:
        return B.live_matrix(data, hist, PL.HORIZON)
    finally:
        CH.newest_export = orig


def set_row(pid, **kw):
    def edit(d):
        rows = [p for p in d["all_players"] if p["id"] == pid]
        if len(rows) != 1:
            raise MissingInput(f"player {pid} is not once in all_players")
        rows[0].update(kw)
    return edit


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--bb", "--data", "--hist", "--ban", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--csv")
    ap.add_argument("--beam", type=int, nargs=2, default=(50, 100))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw8/saka_cases.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    def note(s):
        print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {s}", file=sys.stderr, flush=True)

    note("matrices")
    d, path, target, XP0, srcs, p_start, snap = PLV.live_inputs(a.data, a.hist)
    squad = CH.my_squad(d)
    sk = [r for r in squad if (r["name"], r["team"]) == SAKA]
    if len(sk) != 1:
        raise MissingInput("Saka (ARS) is not one player of our 15")
    sid = sk[0]["id"]
    row = next(p for p in d["all_players"] if p["id"] == sid)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise MissingInput(f"no budget: {why}")
    bank = budget - sum(r["selling"] for r in squad)
    market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
               "status": p["status"]} for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    weeks = list(range(target, target + len(XP0)))
    if len(weeks) != 6:
        raise MissingInput(f"the matrix covers GW{weeks[0]}-{weeks[-1]}, not six weeks")
    _, _, t_av, XP_av, _ = matrix_with(a.data, a.hist, set_row(sid, status="a", chance_next_round=100))
    _, _, t_lift, XP_lift, _ = matrix_with(a.data, a.hist, set_row(sid, status="a"))
    if t_av != target or t_lift != target:
        raise MissingInput("the edited matrices are for another gameweek")
    for t in range(6):
        for M, label in ((XP_av, "available"), (XP_lift, "gate lifted")):
            ids = (set(M[t]) | set(XP0[t])) - {sid}
            moved = [pid for pid in ids if M[t].get(pid) != XP0[t].get(pid)]
            if moved:
                raise MissingInput(f"GW{weeks[t]}: the '{label}' matrix moves {len(moved)} other players")
    if any(sid in XP0[t] for t in range(6)):
        raise MissingInput("Saka has a value in the matrix as built: case (a) is not the gate's 0")
    XP_b = [dict(w) for w in XP0]
    for t in range(FROM_WEEK, 6):
        XP_b[t][sid] = XP_av[t].get(sid, 0.0)
    data_commit = subprocess.run(["git", "-C", a.data, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    bb_commit = subprocess.run(["git", "-C", os.path.dirname(BB_PATH), "log", "-1", "--format=%h", "--", os.path.basename(BB_PATH)],
                               capture_output=True, text=True).stdout.strip() or "not in git"

    # Thiago's GW9 value x (1 - P(ban)), from W3's line, for the plans (as bb_timing)
    ban_lines = [ln.rstrip("\n") for ln in open(a.ban, encoding="utf-8")]
    bans = [(m, ln) for ln in ban_lines for m in [BB.BAN_RE.match(ln)] if m]
    th = [(m, ln) for m, ln in bans if m.group(1) == "Thiago"]
    if len(th) != 1:
        raise MissingInput(f"W3's ban-risk lines hold {len(th)} lines for Thiago, not 1")
    m, ban_line = th[0]
    p_ban = float(m.group(8))
    tid = [r["id"] for r in squad if r["name"] == "Thiago" and r["team"] == m.group(2)]
    if len(tid) != 1:
        raise MissingInput("Thiago of W3's line is not one player of our 15")
    tid = tid[0]
    src_line = next((ln[1:].strip() for ln in ban_lines if ln.startswith("#")), "source not stated")

    def with_ban(XP):
        X = [dict(w) for w in XP]
        X[1][tid] = XP[1].get(tid, 0.0) * (1 - p_ban)
        return X

    out(f"SAKA CASES  GW{target}, information for Friday's deadline pass (Boris, Thu 22 Oct); read-only, no tool change")
    out(f"  data {data_commit[:7]}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {sha256_of(os.path.abspath(__file__))}; bb_timing.py {bb_commit} sha256 {sha256_of(BB_PATH)}; "
        f"generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  matrix: the planner's xp_v2 horizon matrix GW{weeks[0]}-{weeks[-1]} (builder.live_matrix; odds "
        f"{snap or 'none before the deadline'} where they price the fixture, else the fallback)")
    if a.csv:
        csv_rows = list(csv.DictReader(open(a.csv, encoding="utf-8", newline="")))
        bad = [r["id"] for r in csv_rows if abs(float(r["xp_v2"]) - XP0[0].get(int(r["id"]), 0.0)) > 1e-9]
        out(f"  check: the GW{target} column against the bundle's {os.path.basename(a.csv)}: {len(csv_rows) - len(bad)} of "
            f"{len(csv_rows)} players equal" + ("" if not bad else f"; differ: {', '.join(bad[:10])}"))
    out(f"  Saka (ARS MID, id {sid}) in the export: status {row['status']}, chance_next_round {row.get('chance_next_round')}, "
        f"news \"{row.get('news', '')}\"; in the matrix as built: no value in any week (the gate)")
    out(f"  Saka as available (his row in memory: status 'a', chance 100; every other player unchanged in all six weeks): "
        + ", ".join(f"GW{u} {XP_av[t].get(sid, 0.0):.2f}" for t, u in enumerate(weeks)))
    out(f"  information, only the gate lifted (chance {row.get('chance_next_round')} kept, as the bundle's 'if he plays'): "
        + ", ".join(f"GW{u} {XP_lift[t].get(sid, 0.0):.2f}" for t, u in enumerate(weeks)))
    out(f"  (a) Saka 0 in every week; (b) Saka 0 in GW{weeks[0]}-{weeks[FROM_WEEK - 1]}, from GW{weeks[FROM_WEEK]} his values as available")
    out(f"  planner rows: planner_live's run on the case's matrix ({BB.K0} free transfer, no hits, decay {BB.DECAY}, Boris's "
        f"schedule; no ban adjustment); A and C: bb_timing.py's search, Thiago's GW{target + 1} x (1 - {p_ban:.3f}) from W3's "
        f"line ({src_line}): {ban_line.strip()}")
    out()

    res = {}
    for case, XP in (("a", XP0), ("b", XP_b)):
        note(f"case ({case}): the planner")
        scored, _ = PL.rank_plans(squad, bank, market, XP, BB.K0, p_start, BB.DECAY, BB.SCHED, hits_allowed=False)
        if not scored:
            raise MissingInput(f"case ({case}): no plan scored")
        singles = [(i, ev) for i, ev in enumerate(scored, 1) if len(ev["outs"]) == 1]
        best_single = singles[0]
        saka_out = [(i, ev) for i, ev in singles if ev["outs"][0]["id"] == sid]
        XB = with_ban(XP)
        root = {"rows": squad, "bank": bank, "k": BB.K0, "W": [], "H": 0.0, "moves": [], "ks": []}
        note(f"case ({case}): A")
        plan_a = BB.follow_default(BB.expand([root], 0, 0, XB, market, only=1)[0], 0, XB, market, p_start)
        cs = {}
        for mw in a.beam:
            note(f"case ({case}): C, width {mw}")
            c0 = BB.expand([root], 0, 2, XB, market)
            c1 = BB.prune(BB.expand(c0, 1, 2, XB, market), mw)
            c2 = BB.expand(c1, 2, 2, XB, market)
            cs[mw] = c2[0]
        same_c = len({BB.key_of(v) for v in cs.values()}) == 1
        plan_c = BB.follow_default(cs[max(a.beam)], 2, XB, market, p_start)
        res[case] = (scored, best_single, saka_out, plan_a, plan_c, same_c)

    def move(ev):
        return BB.plan_text(ev["outs"], ev["ins"])

    def moves(st):
        return "; ".join(f"GW{weeks[t]} {BB.plan_text(o, i)}" for t, (_, o, i) in enumerate(st["moves"]))

    title = {"a": f"(a) SAKA 0 IN EVERY WEEK (the bundle's gate)",
             "b": f"(b) SAKA 0 IN GW{weeks[0]}-{weeks[FROM_WEEK - 1]}, AVAILABLE FROM GW{weeks[FROM_WEEK]}"}
    for case in ("a", "b"):
        scored, (ri, bs), saka_out, plan_a, plan_c, same_c = res[case]
        out(title[case])
        out(f"  the planner: default {move(scored[0])} {scored[0]['score']:.2f}; best single transfer for GW{target}: "
            f"{move(bs)} {bs['score']:.2f} (rank {ri} of {len(scored)})")
        if saka_out:
            si, se = saka_out[0]
            out(f"  best with Saka out: {move(se)} {se['score']:.2f} (rank {si} of {len(scored)}; weekly dxP "
                + " ".join(f"{g:+.1f}" for g in se["gains"]) + ")")
        else:
            out("  best with Saka out: none scored (no legal swap from the pool)")
        tot = {}
        for name, st in (("A", plan_a), ("C", plan_c)):
            sc, dec, lost, raw = BB.total(st)
            tot[name] = (sc, raw)
            out(f"  {name}  BB GW{weeks[0 if name == 'A' else 2]:<3} score {sc:7.2f}  undiscounted xP {raw:7.2f}   {moves(st)}")
        out(f"  A - C: score {tot['A'][0] - tot['C'][0]:+.2f}, undiscounted {tot['A'][1] - tot['C'][1]:+.2f}; C's beam, widths "
            f"{a.beam[0]} and {a.beam[1]}: the same moves {'yes' if same_c else 'NO - the wider is reported'}")
        out()
    path_out = os.path.join(a.out, "saka_cases.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines).rstrip("\n") + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (MissingInput, BB.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
