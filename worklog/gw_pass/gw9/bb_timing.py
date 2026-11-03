"""worklog/gw_pass/gw9/bb_timing.py - Bench Boost timing (Boris, Wed 21 Oct; re-run for GW9, Fri 30 Oct: the GW8
script with its labels taken from the data, the calculation unchanged; information only, read-only; no tool change,
s8c-wip d9071b8 stays the bundle commit). Boris's rule: the Bench Boost is played before the international break.
Plans A, B and C put it in the target gameweek, the next and the one after. Standard library only.

    python bb_timing.py --code DIR --data DIR --hist DIR --ban FILE [--csv FILE] --out DIR [--beam M1 M2]

  --code   a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --ban    W3's ban-risk lines (fpl_squad.ban_risk) on the same data
  --csv    the bundle's xp_v2_all.csv, checked against the matrix's first column

matrix   the planner's xp_v2 horizon matrix, six weeks from the target t (planner_live.live_inputs: builder.live_matrix, the odds
         snapshot where it prices the fixture, else the fallback); Thiago's week t+1 value x (1 - P(ban)), P(ban) from
         W3's ban-risk line
1        the Bench Boost value each week on our 15 held: the four outside xp_v2's best XI (S8's xi_value, the best
         legal formation)
2        three plans, no hits: 1 free transfer now, +1 a week, rolled transfers carry up to 5 (S8's MAX_FT), Boris's
         FT schedule (1.5, 1.0, 0.6, 0.3)
           A  BB in t:    the best single transfer now
           B  BB in t+1:  the best use of transfers for t to t+1 (rolling allowed)
           C  BB in t+2:  the best use of transfers for t to t+2 (rolling allowed)
         after the BB week, each week the planner's default (S8's rank_plans as planner_live runs it: no hits, decay
         0.85, Boris's schedule) on the weeks left of the same matrix
score    the planner's score over the six weeks: sum_t 0.85^t W_t - lost FT value; W_t = the XI + captain xP of the
         squad held in week t, all 15 + the captain in the BB week; lost = V(5) - V(FTs after the six weeks), V = S8's stock
         value (rolling every week ends at 5)
search   the moves up to the BB week maximise that score with the squad after the BB week held to the sixth week (for A it is
         the planner's score with week t's bench at full weight); each week 0, 1 or 2 transfers within the banked FTs,
         S8's candidates (same-position swaps from the top 25 per position by decayed xP over the weeks left, budget
         at selling prices, club cap 3, 2 GK+DEF per club; a player bought in the horizon sells at his price); A and
         B exhaustive; C by a beam (after t+1, the best M states for each FT stock), run at two widths
"""
import argparse
import csv
import hashlib
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone


def _code_dir(argv):
    for i, x in enumerate(argv):
        if x == "--code" and i + 1 < len(argv):
            return argv[i + 1]
        if x.startswith("--code="):
            return x.split("=", 1)[1]
    sys.exit("--code DIR is required (a clean worktree of the bundle commit)")


CODE = os.path.abspath(_code_dir(sys.argv[1:]))
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(CODE, "tools"))
import fpl_edge as E                                              # noqa: E402
import capflag as CF                                              # noqa: E402
import chips as CH                                                # noqa: E402
import planner as PL                                              # noqa: E402
import planner_live as PLV                                        # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run, sha256_of                             # noqa: E402

DECAY = PLV.DECAY                   # 0.85
SCHED = PL.SCHEDULES[PLV.SCHEDULE]  # Boris's (1.5, 1.0, 0.6, 0.3)
K0 = PLV.FREE_TRANSFERS             # 1 free transfer now
MAX_FT = PL.MAX_FT                  # 5
PLANS = (("A", 0), ("B", 1), ("C", 2))
BAN_RE = re.compile(r"^\s+(.+?)\s+([A-Z]{3})\s+(GK|DEF|MID|FWD)\s+cautions (\d+), club match (\d+) next\s+rate90 ([\d.]+)"
                    r"\s+P\(start\) ([\d.]+)\s+P\(ban\) ([\d.]+)")


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def V(k):
    return PL.stock_value(SCHED, k)


def week_value(rows, xp, bb):
    """W_t: the best XI + captain (S8's xi_value), or all 15 + the captain in a Bench Boost week (planner_live's bb_value)."""
    return PLV.bb_value(rows, xp) if bb else PL.xi_value(PL.squad_by_pos(rows, xp))


def xi_bench(rows, xp):
    """(XI, bench) of S8's xi_value: GK = the top keeper; the first formation reaching the best value; ties by id."""
    by = defaultdict(list)
    for r in rows:
        by[r["pos"]].append(r)
    for p in by:
        by[p].sort(key=lambda r: (-xp.get(r["id"], 0.0), r["id"]))
    best = None
    for d_, m, f in PL.FORMATIONS:
        if len(by[2]) < d_ or len(by[3]) < m or len(by[4]) < f:
            continue
        v = sum(xp.get(r["id"], 0.0) for r in [by[1][0]] + by[2][:d_] + by[3][:m] + by[4][:f])
        if best is None or v > best[0]:
            best = (v, (d_, m, f))
    d_, m, f = best[1]
    xi = [by[1][0]] + by[2][:d_] + by[3][:m] + by[4][:f]
    ids = {r["id"] for r in xi}
    bench = sorted((r for r in rows if r["id"] not in ids), key=lambda r: (r["pos"] != 1, -xp.get(r["id"], 0.0), r["id"]))
    return xi, bench


def apply(rows, bank, outs, ins):
    gone = {o["id"] for o in outs}
    new = [r for r in rows if r["id"] not in gone] + [dict(i, selling=i.get("selling", i["price"])) for i in ins]
    return new, bank + sum(o["selling"] for o in outs) - sum(i["price"] for i in ins)


def candidates(rows, bank, xp_left, market, max_u):
    """S8's candidates with at most max_u transfers (pool: the top 25 per position by decayed xP over the weeks left)."""
    pool = PL.build_pool(market, {r["id"] for r in rows}, xp_left, DECAY)
    if max_u >= 2:
        return PL.plan_candidates(rows, bank, pool)
    out = [((), ())]
    if max_u >= 1:
        for o in rows:
            for i in pool.get(o["pos"], []):
                new = [r for r in rows if r["id"] != o["id"]] + [i]
                if PL.legal(new, bank + o["selling"] - i["price"]):
                    out.append(((o,), (i,)))
    return out


def plan_text(outs, ins):
    return PLV.plan_text({"outs": outs, "ins": ins})


def key_of(st):
    return tuple((s, tuple(sorted(o["id"] for o in outs)), tuple(sorted(i["id"] for i in ins))) for s, outs, ins in st["moves"])


def expand(states, s, b, XP, market, only=None):
    """Every child of every state at week s: the held score H (the squad after week s held to GW13, the BB in week b,
    lost = V(min(5, K0 + s + 1)) - V(FTs into week s + 1)); `only` = an exact transfer count."""
    out = []
    for st in states:
        k = st["k"]
        for outs, ins in candidates(st["rows"], st["bank"], XP[s:], market, min(2, k)):
            u = len(outs)
            if only is not None and u != only:
                continue
            if u == 0 and k >= MAX_FT:
                continue
            rows, bank = apply(st["rows"], st["bank"], outs, ins)
            vals = [week_value(rows, XP[t], t == b) for t in range(s, len(XP))]
            k2 = min(MAX_FT, k - u + 1)
            past = sum(DECAY ** t * w for t, w in enumerate(st["W"]))
            H = past + sum(DECAY ** (s + j) * w for j, w in enumerate(vals)) - (V(min(MAX_FT, K0 + s + 1)) - V(k2))
            out.append({"rows": rows, "bank": bank, "k": k2, "W": st["W"] + [vals[0]], "H": H,
                        "moves": st["moves"] + [(s, outs, ins)], "ks": st["ks"] + [(k, k2)]})
    out.sort(key=lambda c: (-round(c["H"], 9), sum(len(m[1]) for m in c["moves"]), key_of(c)))
    return out


def prune(states, m):
    """The best m states for each FT stock (states sorted best first)."""
    kept, n = [], defaultdict(int)
    for st in states:
        if n[st["k"]] < m:
            kept.append(st)
            n[st["k"]] += 1
    return kept


def follow_default(st, b, XP, market, p_start):
    """After the BB week: each week the planner's default (rank_plans, no hits) on the weeks left."""
    st = dict(st)
    for t in range(b + 1, len(XP)):
        scored, _ = PL.rank_plans(st["rows"], st["bank"], market, XP[t:], st["k"], p_start, DECAY, SCHED, hits_allowed=False)
        if not scored:
            raise MissingInput(f"no plan scored at GW{t}")
        ev = scored[0]
        rows, bank = apply(st["rows"], st["bank"], ev["outs"], ev["ins"])
        k2 = min(MAX_FT, st["k"] - len(ev["outs"]) + 1)
        st = {"rows": rows, "bank": bank, "k": k2, "W": st["W"] + [week_value(rows, XP[t], False)],
              "moves": st["moves"] + [(t, ev["outs"], ev["ins"])], "ks": st["ks"] + [(st["k"], k2)], "H": st["H"]}
    return st


def total(st):
    dec = sum(DECAY ** t * w for t, w in enumerate(st["W"]))
    lost = V(MAX_FT) - V(st["k"])
    return dec - lost, dec, lost, sum(st["W"])


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--code", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--hist", required=True)
    ap.add_argument("--ban", required=True)
    ap.add_argument("--csv")
    ap.add_argument("--out", required=True)
    ap.add_argument("--beam", type=int, nargs=2, default=(50, 100))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw9/bb_timing.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    def note(s):
        print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {s}", file=sys.stderr, flush=True)

    d, path, target, XP_raw, srcs, p_start, snap = PLV.live_inputs(a.data, a.hist)
    squad = CH.my_squad(d)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise MissingInput(f"no budget: {why}")
    bank = budget - sum(r["selling"] for r in squad)
    market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
               "status": p["status"]} for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    weeks = list(range(target, target + len(XP_raw)))
    if weeks[:3] != [target, target + 1, target + 2] or len(weeks) != 6:
        raise MissingInput(f"the matrix covers GW{weeks[0]}-{weeks[-1]}, not six weeks")
    data_commit = subprocess.run(["git", "-C", a.data, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    # P(ban) from W3's line; Thiago's GW9 value x (1 - P(ban))
    ban_lines = [ln.rstrip("\n") for ln in open(a.ban, encoding="utf-8")]
    bans = [(m, ln) for ln in ban_lines for m in [BAN_RE.match(ln)] if m]
    thiago = [(m, ln) for m, ln in bans if m.group(1) == "Thiago"]
    if len(thiago) != 1:
        raise MissingInput(f"W3's ban-risk lines hold {len(thiago)} lines for Thiago, not 1")
    m, ban_line = thiago[0]
    p_ban = float(m.group(8))
    tid = [r["id"] for r in squad if r["name"] == "Thiago" and r["team"] == m.group(2)]
    if len(tid) != 1:
        raise MissingInput("Thiago of W3's line is not one player of our 15")
    tid = tid[0]
    XP = [dict(w) for w in XP_raw]
    XP[1][tid] = XP_raw[1].get(tid, 0.0) * (1 - p_ban)

    out(f"BENCH BOOST TIMING  A, B, C = a Bench Boost in GW{target}, GW{target + 1}, GW{target + 2} (Boris's rule: before the "
        f"international break); information for the GW{target} deadline pass, read-only, no tool change")
    out(f"  data {data_commit[:7]}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {sha256_of(os.path.abspath(__file__))}; generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  matrix: the planner's xp_v2 horizon matrix GW{weeks[0]}-{weeks[-1]} (planner_live.live_inputs; odds "
        f"{snap or 'none before the deadline'} where they price the fixture, else the fallback)")
    if a.csv:
        csv_rows = list(csv.DictReader(open(a.csv, encoding="utf-8", newline="")))
        bad = [r["id"] for r in csv_rows if abs(float(r["xp_v2"]) - XP_raw[0].get(int(r["id"]), 0.0)) > 1e-9]
        out(f"  check: the GW{target} column against the bundle's {os.path.basename(a.csv)}: {len(csv_rows) - len(bad)} of "
            f"{len(csv_rows)} players equal" + ("" if not bad else f"; differ: {', '.join(bad[:10])}"))
    src_line = next((ln[1:].strip() for ln in ban_lines if ln.startswith("#")), "source not stated")
    out(f"  W3's ban-risk line ({src_line}): {ban_line.strip()}")
    others = [mm.group(1) for mm, _ in bans if mm.group(1) != "Thiago"]
    out(f"  Thiago's GW{target + 1} xp_v2 {XP_raw[1].get(tid, 0.0):.2f} x (1 - {p_ban:.3f}) = {XP[1][tid]:.2f} in every "
        f"section below" + (f"; also on W3's line, not adjusted (the request names Thiago): "
                                                  f"{', '.join(others)}" if others else ""))
    out(f"  free transfers: {K0} now (planner_live's FREE_TRANSFERS, the ruling), +1 a week, up to {MAX_FT}; no hits; bank "
        f"{bank:.1f}; decay {DECAY}; Boris's FT schedule {SCHED}")
    out()

    # 1. the Bench Boost value each week on our 15
    out(f"1. BENCH BOOST VALUE ON XP_V2, our 15 held (the four outside xp_v2's best XI; S8's xi_value)" + CF.flag(squad))
    for t, u in enumerate(weeks):
        xi, bench = xi_bench(squad, XP[t])
        bv = sum(XP[t].get(r["id"], 0.0) for r in bench)
        check = week_value(squad, XP[t], True) - week_value(squad, XP[t], False)
        if abs(bv - check) > 1e-9:
            raise MissingInput(f"GW{u}: the bench {bv:.6f} is not bb_value - xi_value {check:.6f}")
        out(f"  GW{u:<3} {bv:6.2f}   bench: " + ", ".join(f"{r['name']} {XP[t].get(r['id'], 0.0):.2f}" for r in bench)
            + ("   (Thiago x (1 - P(ban)))" if t == 1 and tid in {r['id'] for r in bench} else ""))
    out()

    # consistency with the bundle: the planner's default and its BB GW8 rescore, on the unadjusted matrix
    note("the planner on the unadjusted matrix")
    scored, _ = PL.rank_plans(squad, bank, market, XP_raw, K0, p_start, DECAY, SCHED, hits_allowed=False)
    bb0 = PLV.bb_rescore(scored, squad, XP_raw[0])
    root_raw = {"rows": squad, "bank": bank, "k": K0, "W": [], "H": 0.0, "moves": [], "ks": []}
    a_raw = expand([root_raw], 0, 0, XP_raw, market, only=1)[0]
    a_rel = a_raw["H"] - sum(DECAY ** t * week_value(squad, XP_raw[t], t == 0) for t in range(6))
    bb0_single = next(ev for ev in bb0 if ev["outs"])
    out(f"  check, the unadjusted matrix: the planner's default {plan_text(scored[0]['outs'], scored[0]['ins'])} "
        f"{scored[0]['score']:.2f}; its BB GW{target} rescore, best transfer {plan_text(bb0_single['outs'], bb0_single['ins'])} "
        f"{bb0_single['score']:.2f} (the bundle's planner section prints both); this script's held score for that step: "
        f"{plan_text(a_raw['moves'][0][1], a_raw['moves'][0][2])} {a_rel:.2f}")

    # 2. the plans
    root = {"rows": squad, "bank": bank, "k": K0, "W": [], "H": 0.0, "moves": [], "ks": []}
    results = {}
    note("A")
    singles = expand([root], 0, 0, XP, market, only=1)
    roll_a = expand([root], 0, 0, XP, market, only=0)[0]
    results["A"] = follow_default(singles[0], 0, XP, market, p_start)
    note("B")
    s0 = expand([root], 0, 1, XP, market)
    s1 = expand(s0, 1, 1, XP, market)
    results["B"] = follow_default(s1[0], 1, XP, market, p_start)
    nb = len(s1)
    cs = {}
    for mw in a.beam:
        note(f"C, width {mw}")
        c0 = expand([root], 0, 2, XP, market)
        c1 = prune(expand(c0, 1, 2, XP, market), mw)
        c2 = expand(c1, 2, 2, XP, market)
        cs[mw] = (c2[0], len(c1), len(c2))
    same_c = len({key_of(v[0]) for v in cs.values()}) == 1
    wide = max(a.beam)
    results["C"] = follow_default(cs[wide][0], 2, XP, market, p_start)
    note("done")

    base = sum(DECAY ** t * week_value(squad, XP[t], False) for t in range(6))
    out(f"2. THREE PLANS GW{weeks[0]}-{weeks[-1]}, no hits; the planner's score = sum 0.85^t W_t - lost FT value (lost = V(5) - V(FTs "
        f"into GW{weeks[-1] + 1})); W_t = XI + captain, all 15 + captain in the BB week; after the BB week the planner's default each week")
    out(f"  search: A exhaustive over {len(singles)} single transfers (rolling instead: {roll_a['H'] - singles[0]['H']:+.2f} on the held "
        f"score); B exhaustive over {nb} GW{weeks[0]}-{weeks[1]} move sequences; C a beam: after GW{weeks[1]} the best M per FT stock, M = {a.beam[0]} and {a.beam[1]} "
        f"({cs[a.beam[0]][2]} and {cs[a.beam[1]][2]} GW{weeks[0]}-{weeks[2]} sequences scored): the same best moves at both widths: "
        f"{'yes' if same_c else 'NO - the wider is reported'}")
    out(f"  (our 15 held, no Bench Boost, for scale: {base:.2f})")
    out(f"  {'plan':<12} {'score':>8} {'decayed xP':>11} {'FTs GW' + str(weeks[-1] + 1):>9} {'lost FT':>8} {'undecayed xP':>13}")
    tot = {}
    for name, b in PLANS:
        sc, dec, lost, raw = total(results[name])
        tot[name] = (sc, raw)
        out(f"  {name}  BB GW{weeks[b]:<4} {sc:8.2f} {dec:11.2f} {results[name]['k']:>9} {lost:8.2f} {raw:13.2f}")
    out(f"  differences on the score: A - B {tot['A'][0] - tot['B'][0]:+.2f}, A - C {tot['A'][0] - tot['C'][0]:+.2f}, "
        f"B - C {tot['B'][0] - tot['C'][0]:+.2f}; undecayed xP, information: A - B {tot['A'][1] - tot['B'][1]:+.2f}, "
        f"A - C {tot['A'][1] - tot['C'][1]:+.2f}, B - C {tot['B'][1] - tot['C'][1]:+.2f}")
    for name, b in PLANS:
        st = results[name]
        out(f"  {name}, week by week (FTs before -> into the next week; W = the week's XI + captain xP, BB = all 15 + captain):")
        rows_t = squad
        for t, u in enumerate(weeks):
            s_, outs, ins = st["moves"][t]
            k1, k2 = st["ks"][t]
            rows_t, _ = apply(rows_t, 0.0, outs, ins)
            out(f"    GW{u:<3} {'BB' if t == b else '  '}  FT {k1} -> {k2}  W {st['W'][t]:6.2f}  "
                f"{'default: ' if t > b else ''}{plan_text(outs, ins)}" + (CF.flag(rows_t) if outs else ""))
        out(f"    after GW{weeks[-1]}: bank {st['bank']:.1f}")
    path_out = os.path.join(a.out, "bb_timing.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MissingInput as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
