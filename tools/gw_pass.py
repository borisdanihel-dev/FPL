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
  5. own v xp_v2 as tested (S6d, tools/xp_v2_live.py): our XI, bench
     order and captain by each, side by side; from GW8 xp_v2 as tested is
     the default for XI and captain (RULING S6b acceptance point 1), own
     printed beside it. Without the live forecast: own picks GW8.
  6. The keeper line: own's P(start) beside S12's keeper lock (not
     adopted, information) and each keeper's xp_v2 as tested.
  7. S14's captain table (tools/points_pmf.py): for our 15, the mean,
     P(>=10), P(>=15) and p90 of xp_v2 as tested's points distribution;
     information only until S14 passes and Boris accepts.

A section whose input is missing prints "missing input: ..." and the
bundle continues; nothing is substituted.

    python tools/gw_pass.py [--data DIR] [--hist ROOT] [--out DIR]
"""
import argparse
import os
import sqlite3
import sys
import unicodedata
from collections import Counter
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
import xp_v2_live as XL                                           # noqa: E402
import points_pmf as PM                                           # noqa: E402
import minutes_v2 as MV                                           # noqa: E402
import planner as PL                                              # noqa: E402
import planner_live as PLV                                        # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

MISSING = tuple(c for c in (getattr(m, "MissingInput", None) for m in (E, BT, CH, OL, LG, XV, XL, PM, MV, PL, PLV)) if c is not None)
SECTIONS = ("S5 ODDS CLEAN SHEETS", "S7 CHIPS", "TRANSFER PLANNER: THE XP_V2 NO-HIT DEFAULT, S8 AND THE BASELINE", "S9 LEAGUE, CAPTAIN AND EFFECTIVE OWNERSHIP",
            "OWN v XP_V2 AS TESTED: XI, BENCH AND CAPTAIN", "KEEPER LINE: OWN P(START) AND THE S12 KEEPER LOCK",
            "CAPTAIN TABLE: S14 POINTS DISTRIBUTIONS (INFORMATION ONLY)")


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


def sqlite_deadline(data_dir, event):
    """events.deadline_time of `event` from fpl.sqlite, as the runner reads
    it (UTC); None when the database or the row is missing."""
    db = os.path.join(data_dir, "fpl.sqlite")
    if not os.path.exists(db):
        return None
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = c.execute("select deadline_time from events where id = ?", (event,)).fetchone()
    except sqlite3.OperationalError:
        return None
    finally:
        c.close()
    if not row or not row[0]:
        return None
    return datetime.fromisoformat(row[0].replace("Z", "+00:00"))


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


CONFIRMED_FT = {8: 1}                      # Boris, 19 Oct: 1 free transfer for GW8 (the planner's estimate was right)
NAMED_SWAP = ("Thiago", "Joao Pedro")      # bundle amendment 1, row (1)


def norm_name(s):
    """Accents and case stripped, so 'Joao Pedro' finds 'João Pedro'."""
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower().strip()


def find_player(rows, name, where):
    hits = [r for r in rows if norm_name(r["name"]) == norm_name(name)]
    if not hits:
        raise MissingInput(f"{where}: no player named {name}")
    if len(hits) > 1:
        raise MissingInput(f"{where}: {len(hits)} players named {name} ({', '.join(f'{r['name']} {r['team']}' for r in hits)})")
    return hits[0]


def why_illegal(rows15, bank_after):
    """The reason a 15 is not allowed, or None."""
    if bank_after < -1e-9:
        return f"over budget by £{-bank_after:.1f}m"
    clubs = Counter(r["team"] for r in rows15)
    club, n = clubs.most_common(1)[0]
    if n > PL.CLUB_MAX:
        return f"{n} from {club} (cap {PL.CLUB_MAX})"
    gkdef = Counter(r["team"] for r in rows15 if r["pos"] in (1, 2))
    if gkdef and max(gkdef.values()) > PL.GKDEF_CLUB_MAX:
        club, n = gkdef.most_common(1)[0]
        return f"{n} GK/DEF from {club} (cap {PL.GKDEF_CLUB_MAX})"
    return None


def value_bb(rows15, xp):
    """GW value with Bench Boost: all 15 count, plus the captain (the highest)."""
    projs = [xp.get(r["id"], 0.0) for r in rows15]
    return sum(projs) + max(projs)


def evaluate_bb(plan, squad, xp_weeks, decay, schedule, k, p_start):
    """planner.evaluate with the first week valued under Bench Boost."""
    ev = PL.evaluate(plan, squad, xp_weeks, decay, schedule, k, p_start)
    if ev is None:
        return None
    outs, ins = plan
    rows = [r for r in squad if r["id"] not in {o["id"] for o in outs}] + list(ins)
    g0 = value_bb(rows, xp_weeks[0]) - value_bb(squad, xp_weeks[0])
    gains = [g0] + list(ev["gains"][1:])
    gain = sum(decay ** t * g for t, g in enumerate(gains))
    return dict(ev, gains=gains, gain=gain, score=gain - PL.HIT * ev["hits"] - ev["lost"])


def named_plans(inp, p_start, k, decay=PL.DECAY, schedule=PL.SCHEDULES["boris"], swap=NAMED_SWAP):
    """Bundle amendment 1: [(label, evaluation or None, note)] for (1) the
    named swap, (2) the roll, (3) the best single bench upgrade under
    Bench Boost in the first week (outgoing = one of the four bench slots
    of the first week's XI by the same xP; incoming = any affordable
    same-position market player)."""
    squad, bank, market, xp_weeks = inp["squad"], inp["bank"], inp["market"], inp["xp_weeks"]
    ids = {r["id"] for r in squad}
    rows = []
    label = f"{swap[0]} -> {swap[1]}"
    try:
        out = find_player(squad, swap[0], "our squad")
        inc = find_player(market, swap[1], "the market")
        new15 = [r for r in squad if r["id"] != out["id"]] + [inc]
        why = why_illegal(new15, bank + out["selling"] - inc["price"])
        if why:
            rows.append((label, None, f"not allowed: {why}"))
        else:
            ev = PL.evaluate(((out,), (inc,)), squad, xp_weeks, decay, schedule, k, p_start)
            rows.append((label, ev, None if ev else "not allowed by the hit rule (the gain, one fixture or an incoming P(start) < 0.8)"))
    except MissingInput as e:
        rows.append((label, None, f"missing input: {e}"))
    ev = PL.evaluate(((), ()), squad, xp_weeks, decay, schedule, k, p_start)
    rows.append(("roll", ev, None if ev else f"not allowed: {k} banked, never sit on {PL.MAX_FT}"))
    xi, bench, gk = CH.xi_and_bench([dict(r) for r in squad], xp_weeks[0])
    bench_ids = {gk["id"]} | {r["id"] for r in bench}
    best = None
    for out in [r for r in squad if r["id"] in bench_ids]:
        for inc in market:
            if inc["pos"] != out["pos"] or inc["id"] in ids:
                continue
            new15 = [r for r in squad if r["id"] != out["id"]] + [inc]
            if why_illegal(new15, bank + out["selling"] - inc["price"]):
                continue
            ev = evaluate_bb(((out,), (inc,)), squad, xp_weeks, decay, schedule, k, p_start)
            if ev and (best is None or (ev["score"], -inc["id"]) > (best["score"], -best["ins"][0]["id"])):
                best = ev
    rows.append(("best single bench upgrade under Bench Boost (the first week's term values all 15)", best,
                 None if best else "no legal single bench upgrade"))
    return rows


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


def captain_band(sbs, sums):
    """(xp_v2 as tested's captain, the options within 0.3 xP of him in xp_v2's
    XI): section 5's side-by-side, its xp_v2 column (S14 amendment 1)."""
    cap = sbs["captain"][1]["id"]
    xi = [b["id"] for _, _, b in sbs["rows"][:11]]
    return cap, PM.captain_options(xi, cap, {pid: s["xp"] for pid, s in sums.items()})


def keeper_line(keepers, own_ps, lock):
    """[(name, team, own P(start) or None, keeper lock or None)] for our keepers."""
    return [(r["name"], r["team"], own_ps.get(r["id"]), lock.get(r["id"])) for r in keepers]


def bundle(data_dir, out=print, now=None, hist_root=None):
    hist_root = hist_root or os.path.join(ROOT, "historical")
    d, path = CH.newest_export(data_dir)
    log_rows = E.read_log(os.path.join(data_dir, E.LOG_PATH))
    target = d["gameweek"] + 1
    now = now or datetime.now(timezone.utc)
    dl = sqlite_deadline(data_dir, target)                   # RULING landing + S11 item 3: fpl.sqlite events.deadline_time, as the runner reads it
    out(f"GW PASS  GW{target} (deadline {f'{dl:%Y-%m-%d %H:%M} UTC' if dl else 'not in fpl.sqlite events'}) from {os.path.basename(path)}; generated {now:%Y-%m-%d %H:%M} UTC; "
        f"information only - no section here is recorded; the transfer default from GW8 is the no-hit planner on xp_v2 (section 3, "
        f"Ruling, Tue 20 Oct, point 1), the simple rule beside it")
    section(out, SECTIONS[0], lambda: OL.live(data_dir, out, now=now))
    section(out, SECTIONS[1], lambda: CH.live(data_dir, out))

    def planner():
        try:
            PLV.plan(data_dir, hist_root, out)
            out("")
            out("  below, information: S8's planner on own xP, its baseline and the named plans (the default is the xp_v2 planner above)")
        except Exception as e:                   # missing or failed: said, and the ruling's fallback; nothing substituted
            out(f"  the xp_v2 planner: {'missing input' if isinstance(e, MISSING + (PLV.MissingInput,)) else 'failed: ' + type(e).__name__}: {e}")
            out("  the ruling's fallback (Ruling, Tue 20 Oct, point 1): S8's planner and the simple rule below, and the decision by hand")
        results = PL.live(data_dir, out)
        inp = planner_inputs(d, log_rows)
        b_text, p_text, n_text, default = baseline_note(results, inp)
        out("")
        out(f"  BASELINE (best one-week move with a free transfer when its gain > 0, else roll; never a hit): {b_text}")
        out(f"  planner top plan: {p_text}")
        out(f"  planner, no hits: {n_text}")
        out(f"  {default}")
        k = CONFIRMED_FT.get(target, inp["k"])
        d_ev = {"events": d.get("events") or []}
        p_start = {int(r["player_id"]): float(r["predicted"]) for r in E.forecasts(log_rows, d_ev)
                   if r["source"] == "minutes" and int(r["event"]) == target}
        out("")
        out(f"  NAMED PLANS (bundle amendment 1): free transfers {k}" + (" confirmed by Boris" if target in CONFIRMED_FT else " (the planner's estimate)")
            + f", planner estimate {inp['k']}" + ("" if k == inp["k"] else "  [DIFFERS]")
            + f"; score = decayed gain - 4 x hits - lost FT value, Boris's schedule, decay {PL.DECAY}")
        out(f"  {'#':>2} {'score':>7} {'gain':>7} {'hits':>5} {'lostFT':>7}  {'weekly dxP':<36} plan")
        for i, (label, ev, note) in enumerate(named_plans(inp, p_start, k), 1):
            if ev is None:
                out(f"  {i:>2} {'-':>7} {'-':>7} {'-':>5} {'-':>7}  {'':<36} {label}: {note}")
                continue
            plan = plan_text(ev["outs"], ev["ins"]) if ev["outs"] else "roll"
            weekly = " ".join(f"{g:+5.1f}" for g in ev["gains"])
            out(f"  {i:>2} {ev['score']:7.2f} {ev['gain']:7.2f} {ev['hits']:5d} {ev['lost']:7.2f}  {weekly:<36} {label}: {plan}"
                + ("   (GW term 1 under Bench Boost)" if label.startswith("best single bench") else ""))
        return results
    section(out, SECTIONS[2], planner)
    section(out, SECTIONS[3], lambda: LG.report(data_dir, out, now))

    v2_live, live_res = {}, {}

    def own_v_xp():
        try:
            res = XL.live(data_dir, hist_root, now)
            if res["target"] != target:
                raise MissingInput(f"the live forecast is for GW{res['target']}, the export's next gameweek is GW{target}")
        except Exception as e:                   # missing or failed: said, and own picks (ruling point 1); nothing substituted
            out(f"  {'missing input' if isinstance(e, MISSING + (MissingInput,)) else 'section failed: ' + type(e).__name__}: {e}")
            out(f"  own picks GW{target} (RULING S6b acceptance point 1: without the live xp_v2 as tested, own picks); nothing is substituted")
            return None
        v2 = res["xp"]
        v2_live.update(v2)
        live_res["res"] = res
        weeks, pts, src = CH.own_week_points(d, log_rows)
        if not weeks or weeks[0] != target:
            raise MissingInput(f"own has no GW{target} projections in the log")
        squad = CH.my_squad(d)
        missing = [r["name"] for r in squad if r["id"] not in v2]
        sbs = side_by_side(squad, pts[target], v2)
        live_res["sbs"] = sbs
        snap = res["snapshot"]
        n_odds = sum(1 for s_ in res["sources"].values() if s_ == "odds")
        out(f"  GW{target}: from GW8 xp_v2 as tested picks the XI and captain (RULING S6b acceptance point 1); own is printed beside it; "
            f"vetoes on hard facts only")
        out(f"  own = the recorded row where the log holds one ({sum(1 for r in squad if src[target].get(r['id']) == 'own')} of 15); "
            f"xp_v2 as tested = tools/xp_v2_live.py (not recorded) from {res['export']}, odds "
            + (f"{snap[0]} ({n_odds} of {len(res['sources'])} fixtures from odds)" if snap else "none before the deadline (every fixture on the fallback)")
            + f", priors 2025/26 (S11)" + (f"; no xp_v2 for {', '.join(missing)} (0 in the choice: status not a, under 45 minutes in the last four, or no fixture)" if missing else ""))
        out(f"  {'slot':>4}  {'own':<34}{'xp_v2 as tested':<34}")
        for slot, a, b in sbs["rows"]:
            tag = "   " if a["id"] == b["id"] else " * "
            out(f"  {slot:>4}{tag}{a['name']:<16}{BT.POS_NAME.get(a['pos'], '?'):>4} {a['proj']:5.2f}       {b['name']:<16}{BT.POS_NAME.get(b['pos'], '?'):>4} {b['proj']:5.2f}")
        co, cv = sbs["captain"]
        out(f"  captain: own {co['name']} ({co['proj']:.2f})  |  xp_v2 as tested {cv['name']} ({cv['proj']:.2f})" + ("" if co["id"] == cv["id"] else "   *"))
        out(f"  {sbs['changed']} slots differ; the XI {'differs' if sbs['xi_differs'] else 'is the same set'}; DEFAULT = xp_v2 as tested "
            f"(slots 1-11, the bench order and the captain)")
        return sbs
    section(out, SECTIONS[4], own_v_xp)

    def keepers():
        mv = MV.live(data_dir, out=lambda s: None, now=now)
        d_ev = {"events": d.get("events") or []}
        own_ps = {int(r["player_id"]): float(r["predicted"]) for r in E.forecasts(log_rows, d_ev)
                  if r["source"] == "minutes" and int(r["event"]) == target}
        squad = CH.my_squad(d)
        ks = keeper_line([r for r in squad if r["pos"] == 1], own_ps, mv["v2"])
        out(f"  GW{target}: own P(start) = the recorded minutes row; keeper lock = S12 minutes v2 (not adopted; 0.95 / 0.05 / 0 by starts in the club's last 3); "
            f"xp_v2 = xp_v2 as tested (section 5)")
        ids = [r["id"] for r in squad if r["pos"] == 1]
        for (name, team, ps, lk), pid in zip(ks, ids):
            v = v2_live.get(pid)
            out(f"  {name:<16}{team:>5}  own P(start) {'n/a' if ps is None else f'{ps:.2f}':>5}   keeper lock {'n/a' if lk is None else f'{lk:.2f}':>5}"
                f"   xp_v2 {'n/a' if v is None else f'{v:.2f}':>5}")
        return ks
    section(out, SECTIONS[5], keepers)

    def captains():
        res = live_res.get("res")
        if res is None:
            raise MissingInput("xp_v2 as tested is not available (section 5): no distribution to print")
        out(f"  GW{target}: the points distribution of xp_v2 as tested (S14, option (a): its mean is xp_v2; no saves term); "
            f"information only until S14 passes and Boris accepts")
        sums = PM.live_pmfs(res)
        rows = PM.captain_table(CH.my_squad(d), sums, out)
        sbs = live_res.get("sbs")
        if sbs is not None:                      # amendment 1: the options within 0.3 xP beside xp_v2's captain
            cap, options = captain_band(sbs, sums)
            names = {r["id"]: r["name"] for r in CH.my_squad(d)}
            PM.print_options(cap, options, sums, names, out)
        return rows
    section(out, SECTIONS[6], captains)
    return target


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"), help="xp_v2 as tested: the root holding 2025-26/ and 2026-27/")
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "gw_pass"))
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    run = Run("tools/gw_pass.py", args.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        target = bundle(args.data, out, hist_root=args.hist)
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
