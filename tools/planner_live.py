"""tools/planner_live.py - S8c, the live transfer planner on xp_v2 with no
hits (prereg/S8c.md; Ruling, Tue 20 Oct, point 1). Offline; standard
library only; the nightly never imports it. From GW8 it is the default
transfer suggestion; hits stay a manual call.

  matrix   xp_v2 as tested for the next six gameweeks (S15's
           builder.live_matrix: the Odds API snapshot where it prices the
           fixture, else the fallback fitted on results before the
           deadline); every fixture's source is printed
  planner  S8's rank_plans unchanged: our 15 at selling prices, 1 free
           transfer, hits forbidden, decay 0.85, Boris's schedule
  beside   the simple rule (S8's baseline_plan on the same matrix: the best
           one-week move when its gain > 0, else roll)
  BB       information: every plan re-scored with week t's value = all 15
           + the captain (a Bench Boost in week t), re-ranked

    python tools/planner_live.py [--data DIR] [--hist ROOT] [--out DIR]
"""
import argparse
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import builder as B                                               # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import planner as PL                                              # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

FREE_TRANSFERS = 1                  # the ruling: 1 FT
DECAY = PL.DECAY                    # 0.85
SCHEDULE = "boris"
TOP = 5
TOP_BB = 3


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted."""


def fixture_sources(d, target, weeks_n, book, model):
    """[(week, home, away, source)] for the matrix's fixtures, the same
    lambda rule as builder.live_matrix (the book where it prices the
    fixture, else the fallback)."""
    out = []
    for u in range(target, target + weeks_n):
        for fid, f in sorted(XL.target_fixtures(d, u).items()):
            _, src = OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"])
            out.append((u, f["home"], f["away"], src))
    return out


def live_inputs(data_dir, hist_root, weeks_n=PL.HORIZON):
    """(d, path, target, weeks_xp, per-fixture sources, p_start) at the live origin."""
    from datetime import datetime, timezone
    d, path, target, weeks_xp, _ = B.live_matrix(data_dir, hist_root, weeks_n)
    _, deadlines, fixtures, _, _ = OL.sqlite_tables(data_dir)
    dl = deadlines[target]
    snap = OL.newest_snapshot(data_dir, dl)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    srcs = fixture_sources(d, target, weeks_n, book, XL._model(fixtures, dl))
    c = E.canonical_through(E.canonical_from_export(d), d["gameweek"])
    inp = E.reliability_inputs(c, gws_played=d["gameweek"])
    p_start = {pid: p["p_start"] for pid, p in inp["players"].items()}
    return d, path, target, weeks_xp, srcs, p_start, (os.path.basename(snap[0]) if snap else None)


def bb_value(rows, xp):
    """Week t's value under a Bench Boost: all 15 by xP + the captain (S8's
    rule: the highest top of a position)."""
    by = PL.squad_by_pos(rows, xp)
    cap = max(by[1][0] if by.get(1) else 0.0, max((by[p][0] for p in (2, 3, 4) if by.get(p)), default=0.0))
    return sum(sum(v) for v in by.values()) + cap


def bb_rescore(scored, squad, xp0):
    """Every plan with week t's gain replaced by the Bench Boost gain; re-ranked as S8 ranks."""
    base = bb_value(squad, xp0)
    out = []
    for ev in scored:
        rows = [r for r in squad if r["id"] not in {o["id"] for o in ev["outs"]}] + list(ev["ins"])
        g0 = bb_value(rows, xp0) - base
        out.append(dict(ev, score=ev["score"] - ev["gains"][0] + g0, gain=ev["gain"] - ev["gains"][0] + g0,
                        gains=[g0] + list(ev["gains"][1:])))
    out.sort(key=lambda e: (-e["score"], e["used"], tuple(sorted(i["id"] for i in e["ins"]))))
    return out


def plan_text(ev):
    return "roll" if not ev["outs"] else "; ".join(f"{o['name']} -> {n['name']} ({n['team']}, {n['price']:.1f})"
                                                   for o, n in zip(ev["outs"], ev["ins"]))


def plan(data_dir, hist_root, out=print):
    d, path, target, weeks_xp, srcs, p_start, snap = live_inputs(data_dir, hist_root)
    squad = CH.my_squad(d)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise MissingInput(f"no budget: {why}")
    bank = budget - sum(r["selling"] for r in squad)
    market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
               "status": p["status"]} for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    scored, pool = PL.rank_plans(squad, bank, market, weeks_xp, FREE_TRANSFERS, p_start, DECAY, PL.SCHEDULES[SCHEDULE],
                                 hits_allowed=False)
    if not scored:
        raise MissingInput("no plan scored")
    simple = PL.baseline_plan(squad, bank, pool, weeks_xp[0], FREE_TRANSFERS)
    simple_ev = next((ev for ev in scored if PL.plan_key(ev) == PL.plan_key({"outs": simple[0], "ins": simple[1]})), None)
    bb = bb_rescore(scored, squad, weeks_xp[0])
    weeks = list(range(target, target + len(weeks_xp)))
    out(f"TRANSFER PLANNER ON XP_V2  GW{weeks[0]}-{weeks[-1]} from {os.path.basename(path)}; xp_v2 as tested (odds "
        f"{snap or 'none before the deadline'}, else the fallback); {FREE_TRANSFERS} free transfer, no hits (a hit stays a manual "
        f"call), decay {DECAY}, schedule {SCHEDULE} {PL.SCHEDULES[SCHEDULE]}; bank {bank:.1f}; the default from GW8 (Ruling, Tue 20 Oct, "
        f"point 1)")
    by_week = defaultdict(list)
    for u, h, a, s in srcs:
        by_week[u].append(f"{h}-{a} {s}")
    for u in weeks:
        out(f"  lambdas GW{u}: " + ", ".join(by_week.get(u, ["no fixtures"])))
    out(f"  {'#':>2} {'score':>7} {'gain':>7} {'lostFT':>7}  {'weekly dxP':<36} plan")
    for i, ev in enumerate(scored[:TOP], 1):
        weekly = " ".join(f"{g:+5.1f}" for g in ev["gains"])
        out(f"  {i:>2} {ev['score']:7.2f} {ev['gain']:7.2f} {ev['lost']:7.2f}  {weekly:<36} {plan_text(ev)}")
    out(f"  DEFAULT: {plan_text(scored[0])}")
    out(f"  the simple rule beside it (best one-week move when its gain > 0, else roll): {plan_text({'outs': simple[0], 'ins': simple[1]})}"
        + (f"; on the planner's score {simple_ev['score']:.2f}, week-t gain {simple_ev['gains'][0]:+.2f}" if simple_ev else ""))
    out(f"  information, a Bench Boost in GW{target} (week t's bench at full weight), top {TOP_BB}:")
    for i, ev in enumerate(bb[:TOP_BB], 1):
        out(f"    {i} {ev['score']:7.2f}  week-t gain {ev['gains'][0]:+5.2f}  {plan_text(ev)}")
    return {"target": target, "scored": scored, "simple": simple, "bb": bb, "sources": srcs, "bank": bank}


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "planner_live"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("tools/planner_live.py", a.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        res = plan(a.data, a.hist, out)
    except (MissingInput, XR.MissingInput, OL.MissingInput, CH.MissingInput, SH.MissingInput, PL.MissingInput, B.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        return 2
    path = os.path.join(a.out, f"planner_live_gw{res['target']}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path)
    print(f"written: {path}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
