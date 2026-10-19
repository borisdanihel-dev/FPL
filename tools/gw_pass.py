"""tools/gw_pass.py - the Thursday deadline-pass bundle (prereg/bundle.md;
RULING morning 19 Oct items 3 and 6, RULING S8 verifier FAIL item (d)).
Offline, information only; standard library only; the nightly never
imports it. It composes the live outputs of the lane-B tools from the
newest snapshot in the data folder into one file, tools/out/gw_pass/
gw<N>_pass.txt, with run.txt beside it:

  1. S5 --live: the fixtures' odds-implied lambdas and clean-sheet
     probabilities, our GK/DEF lines (odds_lambda.live).
  2. S7: the chip table and the next-gameweek call (chips.live).
  3. S8: the top 5 plans and the two exploratory lines (planner.live)
     beside the baseline's choice (best one-week move or roll, never a
     hit); where they differ the baseline is the default and the planner
     the note.
  4. S9: the league report with the captain and effective-ownership
     tables (league.report).
  5. own v xp_v2: our XI, bench order and captain by each, side by side.
  6. The keeper line: own's P(start) beside S12's keeper lock (not
     adopted, information).

A section whose input is missing prints "missing input: ..." and the
bundle continues; nothing is substituted.

    python tools/gw_pass.py [--data DIR] [--out DIR]
"""
import argparse
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import league as LG                                               # noqa: E402
import xp_v2 as XV                                                # noqa: E402
import minutes_v2 as MV                                           # noqa: E402
import planner as PL                                              # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

MISSING = tuple(c for c in (getattr(m, "MissingInput", None) for m in (E, BT, CH, OL, LG, XV, MV, PL)) if c is not None)
SECTIONS = ("S5 ODDS CLEAN SHEETS", "S7 CHIPS", "S8 TRANSFER PLANNER AND THE BASELINE", "S9 LEAGUE, CAPTAIN AND EFFECTIVE OWNERSHIP",
            "OWN v XP_V2: XI, BENCH AND CAPTAIN", "KEEPER LINE: OWN P(START) AND THE S12 KEEPER LOCK")


class MissingInput(Exception):
    pass


def section(out, title, fn):
    out("")
    out("=" * 78)
    out(title)
    out("=" * 78)
    try:
        return fn()
    except MISSING + (MissingInput,) as e:
        out(f"  missing input: {e}")
        return None
    except Exception as e:                       # a section's tool failed: said, never substituted; the pass goes on
        out(f"  section failed: {type(e).__name__}: {e}")
        return None


def plan_text(outs, ins):
    if not outs:
        return "roll"
    return "; ".join(f"{o['name']} -> {n['name']} ({n['team']}, £{n['price']:.1f}m)" for o, n in zip(outs, ins))


def planner_inputs(d, log_rows):
    """The planner's live inputs, as planner.live builds them."""
    weeks, pts, src = CH.own_week_points(d, log_rows)
    if not weeks:
        raise MissingInput("the export has no upcoming fixtures")
    xp_weeks = [pts[w] for w in weeks[:PL.HORIZON]]
    squad = CH.my_squad(d)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise MissingInput(f"no budget: {why}")
    bank = budget - sum(r["selling"] for r in squad)
    k = E.estimate_free_transfers(d)
    market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
               "status": p["status"]} for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    return {"weeks": weeks, "xp_weeks": xp_weeks, "squad": squad, "bank": bank, "k": k, "market": market}


def baseline_note(results, inp):
    """(baseline plan text, planner top plan text, no-hit top plan text,
    the default line): the baseline is the default, the planner the note."""
    pool = PL.build_pool(inp["market"], {r["id"] for r in inp["squad"]}, inp["xp_weeks"], PL.DECAY)
    b_outs, b_ins = PL.baseline_plan(inp["squad"], inp["bank"], pool, inp["xp_weeks"][0], inp["k"])
    top = results.get((PL.DECAY, "boris")) or []
    nohit = results.get(("no hits", "boris")) or []
    base_key = (tuple(sorted(o["id"] for o in b_outs)), tuple(sorted(i["id"] for i in b_ins)))
    p_text = plan_text(top[0]["outs"], top[0]["ins"]) if top else "none"
    n_text = plan_text(nohit[0]["outs"], nohit[0]["ins"]) if nohit else "none"
    agree = bool(top) and PL.plan_key(top[0]) == base_key
    default = ("the planner agrees with the baseline" if agree
               else "DEFAULT = the baseline; the planner's top plan is the note (RULING S8 verifier FAIL item d)")
    return plan_text(b_outs, b_ins), p_text, n_text, default


def side_by_side(squad, own_pts, v2_pts):
    """[(slot, own row, xp_v2 row)] for the XI (1-11), the bench (12-15:
    the sub keeper then the outfield bench) and the captains; rows carry
    name, pos and proj under each projection."""
    xi_o, bench_o, gk_o = CH.xi_and_bench([dict(r) for r in squad], own_pts)
    xi_v, bench_v, gk_v = CH.xi_and_bench([dict(r) for r in squad], v2_pts)
    cap_o = max(xi_o, key=lambda r: (r["proj"], -r["id"]))
    cap_v = max(xi_v, key=lambda r: (r["proj"], -r["id"]))
    rows = []
    for slot, (a, b) in enumerate(zip(xi_o + [gk_o] + list(bench_o), xi_v + [gk_v] + list(bench_v)), 1):
        rows.append((slot, a, b))
    changed = sum(1 for _, a, b in rows if a["id"] != b["id"])
    return {"rows": rows, "captain": (cap_o, cap_v), "changed": changed,
            "xi_differs": {r["id"] for r in xi_o} != {r["id"] for r in xi_v}}


def keeper_line(keepers, own_ps, lock):
    """[(name, team, own P(start) or None, keeper lock or None)] for our keepers."""
    return [(r["name"], r["team"], own_ps.get(r["id"]), lock.get(r["id"])) for r in keepers]


def bundle(data_dir, out=print, now=None):
    d, path = CH.newest_export(data_dir)
    log_rows = E.read_log(os.path.join(data_dir, E.LOG_PATH))
    target = d["gameweek"] + 1
    now = now or datetime.now(timezone.utc)
    dl = E.event_deadline(d, target)
    out(f"GW PASS  GW{target} (deadline {f'{dl:%Y-%m-%d %H:%M} UTC' if dl else 'unknown'}) from {os.path.basename(path)}; generated {now:%Y-%m-%d %H:%M} UTC; "
        f"information only - no section here is adopted or recorded; the baseline is the default where the planner differs")
    section(out, SECTIONS[0], lambda: OL.live(data_dir, out, now=now))
    section(out, SECTIONS[1], lambda: CH.live(data_dir, out))

    def planner():
        results = PL.live(data_dir, out)
        inp = planner_inputs(d, log_rows)
        b_text, p_text, n_text, default = baseline_note(results, inp)
        out("")
        out(f"  BASELINE (best one-week move with a free transfer when its gain > 0, else roll; never a hit): {b_text}")
        out(f"  planner top plan: {p_text}")
        out(f"  planner, no hits: {n_text}")
        out(f"  {default}")
        return results
    section(out, SECTIONS[2], planner)
    section(out, SECTIONS[3], lambda: LG.report(data_dir, out, now))

    def own_v_xp():
        rows = XV.forecast(data_dir, out=lambda s: None, now=now)
        v2 = {pid: v for pid, v, *_ in rows}
        weeks, pts, src = CH.own_week_points(d, log_rows)
        if not weeks:
            raise MissingInput("the export has no upcoming fixtures")
        squad = CH.my_squad(d)
        missing = [r["name"] for r in squad if r["id"] not in v2]
        sbs = side_by_side(squad, pts[weeks[0]], v2)
        out(f"  GW{weeks[0]}: own = the recorded row where the log holds one ({sum(1 for r in squad if src[weeks[0]].get(r['id']) == 'own')} of 15), "
            f"xp_v2 = the S6 forecast (not recorded)" + (f"; no xp_v2 for {', '.join(missing)} (0 assumed)" if missing else ""))
        out(f"  {'slot':>4}  {'own':<34}{'xp_v2':<34}")
        for slot, a, b in sbs["rows"]:
            tag = "   " if a["id"] == b["id"] else " * "
            out(f"  {slot:>4}{tag}{a['name']:<16}{BT.POS_NAME.get(a['pos'], '?'):>4} {a['proj']:5.2f}       {b['name']:<16}{BT.POS_NAME.get(b['pos'], '?'):>4} {b['proj']:5.2f}")
        co, cv = sbs["captain"]
        out(f"  captain: own {co['name']} ({co['proj']:.2f})  |  xp_v2 {cv['name']} ({cv['proj']:.2f})" + ("" if co["id"] == cv["id"] else "   *"))
        out(f"  {sbs['changed']} slots differ; the XI {'differs' if sbs['xi_differs'] else 'is the same set'} (slots 1-11 by own are the default: Part C rule 2)")
        return sbs
    section(out, SECTIONS[4], own_v_xp)

    def keepers():
        mv = MV.live(data_dir, out=lambda s: None, now=now)
        d_ev = {"events": d.get("events") or []}
        own_ps = {int(r["player_id"]): float(r["predicted"]) for r in E.forecasts(log_rows, d_ev)
                  if r["source"] == "minutes" and int(r["event"]) == target}
        squad = CH.my_squad(d)
        ks = keeper_line([r for r in squad if r["pos"] == 1], own_ps, mv["v2"])
        out(f"  GW{target}: own P(start) = the recorded minutes row; keeper lock = S12 minutes v2 (not adopted; 0.95 / 0.05 / 0 by starts in the club's last 3)")
        for name, team, ps, lk in ks:
            out(f"  {name:<16}{team:>5}  own P(start) {'n/a' if ps is None else f'{ps:.2f}':>5}   keeper lock {'n/a' if lk is None else f'{lk:.2f}':>5}")
        return ks
    section(out, SECTIONS[5], keepers)
    return target


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "gw_pass"))
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    run = Run("tools/gw_pass.py", args.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        target = bundle(args.data, out)
    except MISSING + (MissingInput,) as e:
        print(f"MISSING INPUT: {e} - stopping; nothing is substituted")
        return 2
    path = os.path.join(args.out, f"gw{target}_pass.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    run.wrote(path)
    run.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
