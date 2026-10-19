"""
tools/xp_v2.py - the xP rebuild and blend (BUILD_PLAN.md Step 6, item S6,
offline). Standard library only; the nightly never imports it. Recording
xp_v2 nightly under its own source name is a later wiring item; this tool
never writes the projection log.

    python tools/xp_v2.py --develop --cut 6      # the development set: GW5..cut (settled, all sources recorded)
    python tools/xp_v2.py --validate --cut 6     # the validation set: gameweeks settled after the cut
    python tools/xp_v2.py --forecast             # xp_v2 for the next gameweek from the newest export and log

Definitions, as pre-registered in prereg/S6.md (with amendment 1):
  xp_v2 = P(start) x mean(E_xg[pts | start], E_bl[pts | start]) + P(sub) x E[pts | sub]
    P(start)         the recorded `minutes` row (the minutes model; never averaged in as points)
    E_xg[pts|start]  the recorded `xg` row / P(start)   (every term of the model scales with P(start))
    E_bl[pts|start]  bottomup_lambda / P(start), rebuilt from the newest export before the deadline
                     (S5, adopted by RULING S5 result; the bottomup half of xp_v2)
    P(sub)           (appearances - starts) over the same four-gameweek window as P(start), from
                     player_gw rows before the deadline, scaled by chance_next_round
    E[pts|sub]       the mean realised points of sub appearances (minutes > 0, starts = 0) by position
                     over the gameweeks before the deadline - measured, never assumed
  candidates   equal-weight blend (primary) and the best single model, chosen on the development set
               (amendment 1 point 5b; no fitted weights). No penalty term (5a).
  primary      mean per-gameweek Spearman among predicted starters (P(start) >= 0.8), xp_v2 - own,
               on the validation set; decision metric XI + captain from our 15 (S4).
  pass         xp_v2 beats own with the 90% CI lower bound > 0 on a validation set of at least G
               gameweeks (the S4 calculator at delta 0.02, s_d from the development set); otherwise
               "inconclusive" and nothing is adopted (re-run at the GW10 and GW19 checkpoints).
"""

import argparse
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import chips as CH                                                # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402

FIRST = 5                      # the first gameweek with every source recorded
STARTER_P = BT.STARTER_P
SEED = BT.SEED
DELTA = 0.02
WINDOW = 4
CANDIDATES = ("blend", "xg_only", "bl_only")
SOURCES_NEEDED = ("own", "xg", "bottomup", "minutes")


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# the components, per gameweek, point-in-time
# ---------------------------------------------------------------------------

def sub_inputs(db_path, g, window=WINDOW):
    """From player_gw rows of events < g: P(sub) per player over the last
    min(window, g-1) gameweeks (appearances without a start / window) and
    E[pts | sub] per position over every event < g (mean points of
    appearances without a start; 0.0 with a printed count when a position
    has none)."""
    c = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    pos = {pid: p for pid, p in c.execute("select id, position from players")}
    lo = g - 1 - min(window, g - 1)
    apps = defaultdict(lambda: [0, 0])
    sub_pts = defaultdict(list)
    for pid, ev, pts, mins, starts in c.execute(
            "select player_id, event, total_points, minutes, starts from player_gw where event < ?", (g,)):
        if (mins or 0) > 0 and not starts:
            sub_pts[pos.get(pid)].append(float(pts or 0))
        if lo < ev <= g - 1:
            apps[pid][0] += 1 if (mins or 0) > 0 else 0
            apps[pid][1] += 1 if starts else 0
    c.close()
    n_window = min(window, g - 1)
    p_sub = {pid: (a - s) / n_window for pid, (a, s) in apps.items()} if n_window else {}
    e_sub = {p: (sum(v) / len(v) if v else 0.0) for p in (1, 2, 3, 4) for v in [sub_pts.get(p, [])]}
    counts = {p: len(sub_pts.get(p, [])) for p in (1, 2, 3, 4)}
    return p_sub, e_sub, counts, pos


def chance_scale(d):
    """player id -> chance_next_round / 100 from the export (None = 100)."""
    return {p["id"]: E.chance_of_playing(p) / 100.0 for p in d.get("all_players", [])}


def xp_candidates(p_start, e_xg, e_bl, p_sub, e_sub):
    """{candidate: xP} for one player from the conditional forecasts."""
    sub_term = p_sub * e_sub
    out = {"blend": p_start * (e_xg + e_bl) / 2 + sub_term,
           "xg_only": p_start * e_xg + sub_term,
           "bl_only": p_start * e_bl + sub_term}
    return out


class Season:
    """2026/27 through the S4 harness (the S2 reader rule, lockdown) plus the
    pre-deadline exports and odds (S5) for bottomup_lambda."""

    def __init__(self, data_dir, odds_file=None):
        self.data_dir = data_dir
        self.h = BT.Harness("2026-27", data_dir=data_dir)
        self.name_to_short, self.deadlines, self.fixtures, self.settled, self.actual = OL.sqlite_tables(data_dir)
        self.book = OL.OddsBook(OL.load_odds(odds_file or OL.odds_path("2026-27"), self.name_to_short))
        self.exports = OL.dated_exports(data_dir)
        self.db = os.path.join(data_dir, "fpl.sqlite")
        self._week = {}

    def weeks_with_sources(self):
        return sorted(ev for ev in self.settled if ev >= FIRST
                      and all((ev, s) in self.h.data["forecasts"] for s in SOURCES_NEEDED))

    def week(self, g):
        """Per player: P(start), E_xg, E_bl, P(sub), the candidates' xP, own,
        actual; plus notes. Every input is from before g's deadline."""
        if g in self._week:
            return self._week[g]
        if g not in self.settled:
            raise MissingInput(f"GW{g} is not settled - not graded")
        fc = self.h.data["forecasts"]
        for s in SOURCES_NEEDED:
            if (g, s) not in fc:
                raise MissingInput(f"GW{g}: no pre-deadline {s} snapshot")
        dl = self.deadlines.get(g)
        ex = OL.pre_deadline_export(self.exports, dl, g) if dl else None
        if ex is None:
            raise MissingInput(f"GW{g}: no export generated before its deadline")
        gen, path, d = ex
        results = [(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in self.fixtures
                   if f["finished"] and f["kickoff"] < dl]
        model = OL.fit_fallback(results, dl)
        try:
            reb = OL.rebuild_2627(d, g, self.book, model)
        except ValueError as e:
            raise MissingInput(f"GW{g}: export {os.path.basename(path)} unusable: {e}")
        p_sub_all, e_sub, sub_counts, pos_db = sub_inputs(self.db, g)
        chance = chance_scale(d)
        minutes, xg, own, bottomup = fc[(g, "minutes")], fc[(g, "xg")], fc[(g, "own")], fc[(g, "bottomup")]
        rows, drift = {}, []
        for pid, ps in minutes.items():
            if pid not in xg or pid not in reb:
                continue
            ps = min(1.0, ps)
            e_xg = xg[pid] / ps if ps > 0 else 0.0
            e_bl = reb[pid][1] / ps if ps > 0 else 0.0
            drift.append(abs(reb[pid][2] - ps))
            p_sub = min(1.0, p_sub_all.get(pid, 0.0) * chance.get(pid, 1.0))
            pos = pos_db.get(pid) or reb[pid][3]
            cands = xp_candidates(ps, e_xg, e_bl, p_sub, e_sub.get(pos, 0.0))
            rows[pid] = {"p_start": ps, "e_xg": e_xg, "e_bl": e_bl, "p_sub": p_sub, "pos": pos,
                         "own": own.get(pid), "bottomup": bottomup.get(pid), "bl": reb[pid][1],
                         "actual": float(self.actual[g].get(pid, 0.0)), **cands}
        out = {"rows": rows, "export": os.path.basename(path), "e_sub": e_sub, "sub_counts": sub_counts,
               "p_start_drift": max(drift) if drift else None, "n_minutes": len(minutes), "n_xg": len(xg),
               "n_reb": len(reb)}
        self._week[g] = out
        return out

    def metrics(self, g, cand):
        """(spearman among starters, decision points, n starters) for one
        candidate and for own, paired on the same players."""
        w = self.week(g)
        starters = [pid for pid, r in w["rows"].items() if r["p_start"] >= STARTER_P and r["own"] is not None]
        act = [w["rows"][pid]["actual"] for pid in starters]
        rho_c = BT.spearman([w["rows"][pid][cand] for pid in starters], act)
        rho_o = BT.spearman([w["rows"][pid]["own"] for pid in starters], act)
        squad, _ = self.h.squad(g)
        pos = dict(self.h.data["pos"])
        act_all = {pid: float(a["pts"]) for pid, a in self.h.data["actual"][g].items()}
        dec_c = BT.decision_points(squad, {pid: r[cand] for pid, r in w["rows"].items()}, act_all, pos)
        dec_o = BT.decision_points(squad, {pid: r["own"] for pid, r in w["rows"].items() if r["own"] is not None}, act_all, pos)
        return {"rho": rho_c, "rho_own": rho_o, "dec": dec_c, "dec_own": dec_o, "n": len(starters)}


def develop(data_dir, cut, out=print, odds_file=None, seed=SEED):
    """The development set GW5..cut: every candidate's per-gameweek metrics,
    the best single model chosen here, s_d and G for the validation."""
    s = Season(data_dir, odds_file)
    weeks = [g for g in s.weeks_with_sources() if g <= cut]
    if not weeks:
        raise MissingInput(f"no settled gameweek from GW{FIRST} to GW{cut} with every source recorded")
    out(f"XP_V2 DEVELOP  2026/27 GW{weeks[0]}-{weeks[-1]} (cut GW{cut}): {len(weeks)} gameweeks; candidates equal-weight blend "
        f"(primary) and the single models; metric Spearman among starters (P(start) >= {STARTER_P}); in-sample")
    per = defaultdict(list)
    for g in weeks:
        w = s.week(g)
        out(f"  GW{g}: export {w['export']}, {len(w['rows'])} players with every input (minutes {w['n_minutes']}, xg {w['n_xg']}, "
            f"rebuilt {w['n_reb']}); E[pts|sub] by position "
            + ", ".join(f"{BT.POS_NAME[p]} {w['e_sub'][p]:.2f} (n={w['sub_counts'][p]})" for p in (1, 2, 3, 4))
            + f"; P(start) export vs minutes row max |diff| {w['p_start_drift']:.3f}")
        line = []
        for cand in CANDIDATES:
            m = s.metrics(g, cand)
            per[cand].append(m)
            line.append(f"{cand} rho {m['rho']:+.3f} XI+C {m['dec']:.0f}")
        out(f"        own rho {m['rho_own']:+.3f} XI+C {m['dec_own']:.0f} (n starters {m['n']}); " + "; ".join(line))
    out("  candidate means over the development set (in-sample):")
    best, best_val = None, None
    for cand in CANDIDATES:
        rhos = [m["rho"] for m in per[cand]]
        d_rho = [m["rho"] - m["rho_own"] for m in per[cand]]
        decs = [m["dec"] - m["dec_own"] for m in per[cand]]
        mean_rho, mean_d = sum(rhos) / len(rhos), sum(d_rho) / len(d_rho)
        out(f"    {cand:<8} rho {mean_rho:+.4f}; rho - own {mean_d:+.4f}; XI+C - own {sum(decs) / len(decs):+.2f}")
        if cand != "blend" and (best_val is None or mean_rho > best_val):
            best, best_val = cand, mean_rho
    d_blend = [m["rho"] - m["rho_own"] for m in per["blend"]]
    s_d = BT.sd(d_blend)
    g_needed = BT.power_gameweeks(s_d, DELTA) if s_d else None
    out(f"  best single model on the development set: {best} (chosen here, frozen for validation)")
    out(f"  s_d of (blend - own) over {len(d_blend)} development gameweeks: "
        + (f"{s_d:.4f} -> G at delta {DELTA}: {g_needed:.1f} gameweeks" if s_d is not None else "undefined (fewer than 2 gameweeks)"))
    out("  fpl_ep: " + ("recorded" if any(k[1] == "fpl_ep" for k in s.h.data["forecasts"]) else "not recorded yet (W1)"))
    return {"weeks": weeks, "per": per, "best_single": best, "s_d": s_d, "g_needed": g_needed, "season": s}


def validate(data_dir, cut, out=print, odds_file=None, seed=SEED):
    """The validation set: gameweeks settled after the cut. The candidate
    weights are frozen (equal; the best single model as chosen on the
    development set). Inconclusive below G gameweeks."""
    dev = develop(data_dir, cut, out=lambda s: None, odds_file=odds_file, seed=seed)
    s = dev["season"]
    weeks = [g for g in s.weeks_with_sources() if g > cut]
    out(f"XP_V2 VALIDATE  2026/27 after the cut GW{cut}: {len(weeks)} settled gameweeks with every source "
        f"({', '.join('GW' + str(g) for g in weeks) if weeks else 'none'}); "
        f"needed: G = {dev['g_needed']:.1f} at delta {DELTA}" if dev["g_needed"] else
        f"XP_V2 VALIDATE  2026/27 after the cut GW{cut}: {len(weeks)} settled gameweeks; G undefined (development s_d needs 2+ gameweeks)")
    result = {"weeks": weeks, "g_needed": dev["g_needed"], "best_single": dev["best_single"]}
    if not weeks:
        out("  result: INCONCLUSIVE - no validation gameweek yet; nothing adopted; re-run at the GW10 and GW19 checkpoints")
        result["verdict"] = "inconclusive"
        return result
    per = defaultdict(list)
    for g in weeks:
        for cand in ("blend", dev["best_single"]):
            per[cand].append(s.metrics(g, cand))
    for cand in ("blend", dev["best_single"]):
        d_rho = [m["rho"] - m["rho_own"] for m in per[cand]]
        d_dec = [m["dec"] - m["dec_own"] for m in per[cand]]
        br, bd = BT.bootstrap_mean(d_rho, seed=seed), BT.bootstrap_mean(d_dec, seed=seed)
        out(f"  {cand:<8} rho - own {br['mean']:+.4f} [{br['lo']:+.4f}, {br['hi']:+.4f}]; XI+C - own {bd['mean']:+.2f} "
            f"[{bd['lo']:+.2f}, {bd['hi']:+.2f}]; n={br['n']}")
        result[cand] = {"rho": br, "dec": bd}
    # the blend is replaced only if the single model wins validation by >= 0.02 on rho AND on decision points
    b, sgl = result["blend"], result[dev["best_single"]]
    chosen = dev["best_single"] if (sgl["rho"]["mean"] - b["rho"]["mean"] >= 0.02 and sgl["dec"]["mean"] > b["dec"]["mean"]) else "blend"
    out(f"  xp_v2 = {chosen} (the blend is replaced only if the single model wins by >= 0.02 on rho and on decision points)")
    powered = dev["g_needed"] is not None and len(weeks) >= dev["g_needed"]
    r = result[chosen]["rho"]
    if not powered:
        out(f"  result: INCONCLUSIVE - {len(weeks)} validation gameweeks against G = "
            + (f"{dev['g_needed']:.1f}" if dev["g_needed"] else "undefined") + "; nothing adopted; re-run at the GW10 and GW19 checkpoints")
        result["verdict"] = "inconclusive"
    elif r["lo"] > 0:
        out(f"  result: PASS - xp_v2 ({chosen}) beats own on the primary metric with the CI lower bound > 0; adoption needs Boris's acceptance in chat")
        result["verdict"] = "pass"
    else:
        out(f"  result: FAIL - the CI lower bound is not above 0")
        result["verdict"] = "fail"
    result["chosen"] = chosen
    return result


def forecast(data_dir, out=print, odds_file=None, now=None):
    """xp_v2 for the next gameweek from the newest export and the recorded
    xg and minutes rows for it; bottomup_lambda live (S5); never written to
    the log."""
    now = now or datetime.now(timezone.utc)
    name_to_short, deadlines, fixtures, settled, _ = OL.sqlite_tables(data_dir)
    upcoming = sorted((dl, ev) for ev, dl in deadlines.items() if dl > now)
    if not upcoming:
        raise MissingInput("no deadline after now")
    dl, target = upcoming[0]
    d, path = CH.newest_export(data_dir)
    if d["gameweek"] + 1 != target:
        raise MissingInput(f"the newest export is for GW{d['gameweek'] + 1}, not GW{target}")
    log_rows = E.read_log(os.path.join(data_dir, E.LOG_PATH))
    d_events = {"events": [{"event": ev, "deadline_time": x.isoformat()} for ev, x in deadlines.items()]}
    fc = defaultdict(dict)
    for r in E.forecasts(log_rows, d_events):
        if int(r["event"]) == target:
            fc[r["source"]][int(r["player_id"])] = float(r["predicted"])
    for s in ("xg", "minutes"):
        if not fc[s]:
            raise MissingInput(f"GW{target}: no recorded {s} snapshot yet")
    snap = OL.newest_snapshot(data_dir, dl)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    results = [(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in fixtures if f["finished"] and f["kickoff"] < dl]
    reb = OL.rebuild_2627(d, target, book, OL.fit_fallback(results, dl))
    p_sub_all, e_sub, counts, pos_db = sub_inputs(os.path.join(data_dir, "fpl.sqlite"), target)
    chance = chance_scale(d)
    out(f"XP_V2 FORECAST  GW{target} (deadline {dl:%Y-%m-%d %H:%M} UTC) from {os.path.basename(path)}, the recorded xg and minutes rows, "
        f"bottomup_lambda {'from the odds snapshot' if snap else 'on the fallback (no snapshot)'}; information only, not recorded")
    out("  E[pts|sub] by position: " + ", ".join(f"{BT.POS_NAME[p]} {e_sub[p]:.2f} (n={counts[p]})" for p in (1, 2, 3, 4)))
    rows = []
    for pid, ps in fc["minutes"].items():
        if pid not in fc["xg"] or pid not in reb:
            continue
        ps = min(1.0, ps)
        c = xp_candidates(ps, fc["xg"][pid] / ps if ps else 0.0, reb[pid][1] / ps if ps else 0.0,
                          min(1.0, p_sub_all.get(pid, 0.0) * chance.get(pid, 1.0)), e_sub.get(pos_db.get(pid) or reb[pid][3], 0.0))
        rows.append((pid, c["blend"], ps, fc["xg"][pid], reb[pid][1]))
    by_id = {p["id"]: p for p in d["all_players"]}
    rows.sort(key=lambda r: -r[1])
    out(f"  {'player':<18}{'team':>5}{'pos':>4}{'xp_v2':>7}{'P(start)':>9}{'xg':>6}{'bl':>6}")
    for pid, v, ps, xg, bl in rows[:25]:
        p = by_id.get(pid, {})
        out(f"  {p.get('web_name', pid):<18}{p.get('team', '?'):>5}{BT.POS_NAME.get(p.get('pos'), '?'):>4}{v:7.2f}{ps:9.2f}{xg:6.2f}{bl:6.2f}")
    out(f"  {len(rows)} players forecast")
    return rows


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--odds", default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    ap.add_argument("--cut", type=int, default=None, help="the development cut (the last settled gameweek on the day of the first S6 code commit)")
    ap.add_argument("--develop", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--forecast", action="store_true")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        if args.develop or args.validate:
            if args.cut is None:
                raise MissingInput("--cut is required: the development cut is a frozen argument, never read from the data")
            if args.develop:
                develop(args.data, args.cut, out, odds_file=args.odds)
                name = f"xp_v2_develop_cut{args.cut}.txt"
            else:
                validate(args.data, args.cut, out, odds_file=args.odds)
                name = f"xp_v2_validate_cut{args.cut}.txt"
        elif args.forecast:
            forecast(args.data, out, odds_file=args.odds)
            name = "xp_v2_forecast.txt"
        else:
            ap.print_help()
            return 0
    except MissingInput as e:
        print(f"MISSING INPUT: {e} - stopping; nothing is substituted")
        return 2
    with open(os.path.join(args.out, name), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
