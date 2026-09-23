"""
fpl_hist.py  -  historical validation entry point (HISTORICAL_VALIDATION.md).

Adapts a season of github.com/vaastav/Fantasy-Premier-League CSVs into the
canonical slice that `fpl_edge.py` reads, then calls **the same functions the
live pipeline calls**. There is no second implementation of the measurement or
the model here: if the historical run passes, it is our code that passed.

    python fpl_hist.py historical/2025-26 --season 2025/26
    python fpl_hist.py historical/2025-26 --windows 4,8,12,20,38
    python fpl_hist.py historical/2025-26 --backtest          # Steps 3-5
    python fpl_hist.py historical/2025-26 --horizon           # pre-registered 9b43a78

Two things this adapter owns, because they are properties of the source and not
of the model:

* **De-duplication.** `merged_gw.csv` repeats some (element, fixture) rows
  verbatim. De-duplicating on that pair removes exactly the repeats; doing it on
  (element, round) would delete genuine double gameweeks instead. Every removal
  is reported - a silent de-dup that began dropping real rows after an upstream
  data change would be invisible.
* **Per-fixture to per-gameweek.** The source has one row per match; the
  canonical row is one per player per gameweek, with `n_fixtures` and the
  fixtures listed, matching what the live export carries.
"""

import argparse
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402

POS = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def dedup_rows(rows, key=("element", "fixture")):
    """Drop repeated source rows. Returns (kept, note). The note names the
    count and the players, so a change upstream cannot pass unnoticed."""
    seen, kept, dropped = set(), [], defaultdict(int)
    for r in rows:
        k = tuple(r[f] for f in key)
        if k in seen:
            dropped[(r["element"], r.get("name", "?"))] += 1
            continue
        seen.add(k)
        kept.append(r)
    n = sum(dropped.values())
    if not n:
        return kept, "de-duplication on (element, fixture): no repeated rows"
    who = ", ".join(f"{name} (element {el}) x{c}"
                    for (el, name), c in sorted(dropped.items(), key=lambda kv: -kv[1]))
    return kept, (f"de-duplication on (element, fixture): removed {n} repeated "
                  f"row(s) from {len(dropped)} player(s) - {who}")


def canonical_from_vaastav(folder, season=None):
    """Adapter: a vaastav season folder -> canonical slice."""
    def read(name):
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} is missing - this adapter will not "
                                    f"substitute for it")
        with open(path, encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    teams = read("teams.csv")
    short_by_id = {t["id"]: t["short_name"] for t in teams}
    short_by_name = {t["name"]: t["short_name"] for t in teams}
    fixtures = {f["id"]: f for f in read("fixtures.csv")}
    raw = read(os.path.join("gws", "merged_gw.csv")
               if os.path.exists(os.path.join(folder, "gws", "merged_gw.csv"))
               else "merged_gw.csv")

    rows_in, note = dedup_rows(raw)
    notes = [note]

    players, by_key = {}, defaultdict(list)
    for r in rows_in:
        by_key[(int(r["element"]), int(r["round"]))].append(r)
        pid = int(r["element"])
        players[pid] = {"player_id": pid, "name": r["name"],
                        "pos": POS.get(r["position"], 0),
                        "team": short_by_name.get(r["team"], r["team"]),
                        "chance_next_round": None}

    rows = []
    for (pid, event), group in sorted(by_key.items()):
        fx = []
        for r in group:
            opp = short_by_id.get(r.get("opponent_team"), r.get("opponent_team"))
            fx.append({"opponent": opp,
                       "was_home": str(r.get("was_home")).lower() == "true",
                       "fixture_id": r.get("fixture")})
        rows.append({
            "player_id": pid, "event": event,
            "minutes": sum(_num(r["minutes"]) for r in group),
            "starts": sum(_num(r.get("starts")) for r in group),
            "pts": sum(_num(r["total_points"]) for r in group),
            "xg": sum(_num(r.get("expected_goals")) for r in group),
            "xa": sum(_num(r.get("expected_assists")) for r in group),
            "bps": sum(_num(r.get("bps")) for r in group),
            "defcon": sum(_num(r.get("defensive_contribution")) for r in group),
            "n_fixtures": len(group), "fixtures": fx})

    matches = []
    for f in fixtures.values():
        if f.get("team_h_score") in (None, "") or f.get("event") in (None, ""):
            continue
        h, a = short_by_id.get(f["team_h"]), short_by_id.get(f["team_a"])
        hs, as_ = _num(f["team_h_score"]), _num(f["team_a_score"])
        ev = int(f["event"])
        matches.append({"event": ev, "team": h, "opponent": a, "was_home": True,
                        "goals_for": hs, "goals_against": as_, "fixture_id": f["id"]})
        matches.append({"event": ev, "team": a, "opponent": h, "was_home": False,
                        "goals_for": as_, "goals_against": hs, "fixture_id": f["id"]})

    doubles = sum(1 for r in rows if r["n_fixtures"] > 1)
    notes.append(f"{len(rows)} player-gameweeks from {len(rows_in)} source rows; "
                 f"{doubles} of them cover more than one fixture")
    return E.check_canonical({
        "source": "vaastav", "season": season or os.path.basename(folder.rstrip("/\\")),
        "through_gw": max((r["event"] for r in rows), default=0),
        "players": players, "rows": rows, "team_matches": matches, "notes": notes})


WINDOWS = ((4, 7), (8, 11), (12, 19), (20, 37))      # training gameweeks
POSN = {0: "ALL", 1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def _fmt(sc):
    if sc["rho"] is None:
        return f"{'-':>7} {'(n<3)':>16}"
    lo, hi = max(-1.0, sc["rho"] - sc["ci"]), min(1.0, sc["rho"] + sc["ci"])
    return f"{sc['rho']:>+7.3f} {lo:>+7.3f}..{hi:<+7.3f}"


HORIZONS = (1, 2, 4, 6, 8, 12)
HORIZON_DEFINITION = """\
  Pre-registered 2026-09-14 (commit 9b43a78), run without change:
    For H in {1, 2, 4, 6, 8, 12}, on 2025/26 with the rolling-origin harness:
    train on GW1..t-1; predict the SUM of points over GW t..t+H-1 with the SUM
    of per-fixture bottomup projections over the same gameweeks, fixture
    pairings taken as known in advance and results not; minutes-H = P(start)
    times the number of fixtures in the horizon. Whole population with blanks
    as 0, per position, tie-corrected Spearman with intervals, pooled by
    training window as in Steps 3-5. A player is in the population if he
    passes the usual gate at t and his team has at least one fixture in the
    horizon.
  Implementation detail, not a redefinition: an origin t is used for a given H
  only when t+H-1 <= GW38, so every graded horizon is complete."""


def horizon_rows(c, t, hs=HORIZONS, gate_mins=45):
    """One origin t: train once on GW1..t-1 (the same reliability_inputs the
    single-week backtest uses), then for each H sum per-fixture bottomup
    projections and actual points over GW t..t+H-1."""
    train = E.canonical_through(c, t - 1)
    inp = E.reliability_inputs(train, gws_played=t - 1)
    last, span = c["through_gw"], t + max(hs) - 1
    fx = defaultdict(lambda: defaultdict(list))
    for m in c["team_matches"]:
        if t <= m["event"] <= span:
            fx[m["team"]][m["event"]].append((m["opponent"], m["was_home"]))
    pts = defaultdict(float)
    for r in c["rows"]:
        if t <= r["event"] <= span:
            pts[(r["player_id"], r["event"])] += r["pts"] or 0
    out = []
    for pid, p in inp["players"].items():
        if p["mins_last4"] < gate_mins:
            continue
        row = {"pid": pid, "pos": p["pos"], "origin": t, "H": {}}
        for H in hs:
            if t + H - 1 > last:
                continue                              # incomplete horizon
            events = range(t, t + H)
            nfix = sum(len(fx[p["team"]].get(e, ())) for e in events)
            if nfix == 0:
                continue                              # no fixture in the horizon
            bottomup = 0.0
            for e in events:
                f = fx[p["team"]].get(e)
                if f:
                    bottomup += E.project_reliability(pid, inp, f) or 0.0
            row["H"][H] = {"bottomup": bottomup,
                           "minutes": p["p_start"] * nfix,
                           "actual": sum(pts.get((pid, e), 0.0) for e in events)}
        if row["H"]:
            out.append(row)
    return out


def _rho_cell(pred, act):
    n = len(pred)
    if n < 3:
        return f"{'-':>22}"
    rho = E._spearman(pred, act)
    ci = 1.96 / (n - 1) ** 0.5
    return f"{rho:>+7.3f} {max(-1, rho - ci):>+6.3f}..{min(1, rho + ci):<+6.3f}"


def horizon_report(c, hs=HORIZONS, first=5):
    last = c["through_gw"]
    by_origin = {t: horizon_rows(c, t, hs) for t in range(first, last + 1)}
    out = [f"HORIZON TEST  {c['season']}  origins GW{first}-{last}", HORIZON_DEFINITION, ""]
    windows = list(WINDOWS) + [(WINDOWS[0][0], WINDOWS[-1][1])]
    for H in hs:
        origins = [t for t in by_origin if t + H - 1 <= last]
        out += ["=" * 78,
                f"H = {H:<3} sum over GW t..t+{H - 1}   origins GW{origins[0]}-{origins[-1]} "
                f"({len(origins)})",
                "=" * 78,
                f"  {'training':12s}{'pos':5s}{'n':>6}{'bottomup-H rho, 95%':>24}"
                f"{'minutes-H rho, 95%':>24}"]
        for lo, hi in windows:
            label = f"GW{lo:>2}-{hi:<3}" + ("all" if (lo, hi) == windows[-1] else "   ")
            for pos in (0, 1, 2, 3, 4):
                sel = [r["H"][H] for t in origins if lo <= t - 1 <= hi
                       for r in by_origin[t] if H in r["H"] and (pos == 0 or r["pos"] == pos)]
                act = [s["actual"] for s in sel]
                out.append(f"  {label:12s}{POSN[pos]:5s}{len(sel):>6}"
                           f"  {_rho_cell([s['bottomup'] for s in sel], act)}"
                           f"  {_rho_cell([s['minutes'] for s in sel], act)}")
            out.append("")
    return "\n".join(out)


def backtest_report(c, first=5, last=None):
    """Steps 3-5. Rolling origin GW `first`..`last`; rows pooled by training
    window; every figure per position with its interval; the crossover named
    per position or its absence stated."""
    last = last or c["through_gw"]
    rows = []
    for t in range(first, last + 1):
        rows.extend(E.backtest_week(c, t))
    out = [f"ROLLING-ORIGIN BACKTEST  {c['season']}  GW{first}-{last}, "
           f"{len(rows)} player-gameweeks graded, blanks counted as 0"]

    def pool(lo, hi, pos):
        return [r for r in rows if lo <= r["event"] - 1 <= hi
                and (pos == 0 or r["pos"] == pos)]

    for featured in (False, True):
        out += ["", "=" * 78,
                ("RHO, PLAYERS WHO FEATURED (60+ min) - how well do the starters do"
                 if featured else
                 "RHO, WHOLE POPULATION - who blanks and who scores"),
                "=" * 78]
        for pos in (0, 1, 2, 3, 4):
            out.append(f"\n  {POSN[pos]}   (rho, 95% interval)")
            out.append(f"  {'training':10s}{'n':>5}" + "".join(f"{s:>24}" for s in E.BASELINES))
            for lo, hi in WINDOWS:
                sel = pool(lo, hi, pos)
                scs = {s: E.score_rows(sel, s, featured) for s in E.BASELINES}
                n = scs["minutes"]["n"]
                out.append(f"  GW{lo:>2}-{hi:<5}{n:>5}" + "".join(f"{_fmt(scs[s]):>24}" for s in E.BASELINES))
        if not featured:
            out += ["", "  CROSSOVER - first window where bottomup's rho exceeds minutes' (whole population)"]
            for pos in (1, 2, 3, 4):
                found = None
                for lo, hi in WINDOWS:
                    sel = pool(lo, hi, pos)
                    b, m = E.score_rows(sel, "bottomup"), E.score_rows(sel, "minutes")
                    if b["rho"] is not None and m["rho"] is not None and b["rho"] > m["rho"]:
                        clear = b["rho"] - b["ci"] > m["rho"]
                        found = (lo, hi, b["rho"], m["rho"], clear)
                        break
                if found:
                    lo, hi, b, m, clear = found
                    out.append(f"    {POSN[pos]:4s} GW{lo}-{hi}: bottomup {b:+.3f} vs minutes {m:+.3f}"
                               + ("  (bottomup's lower bound clears minutes)" if clear
                                  else "  (inside the interval - not separable)"))
                else:
                    out.append(f"    {POSN[pos]:4s} no crossover: minutes is never beaten")

    out += ["", "=" * 78, "MAE vs CONSTANT, whole population, per position, 20-37 GWs training", "=" * 78]
    for pos in (0, 1, 2, 3, 4):
        sel = pool(20, 37, pos)
        cells = []
        for s in E.BASELINES:
            sc = E.score_rows(sel, s)
            cells.append(f"{sc['mae']:>6.2f}" if sc["mae"] is not None else f"{'-':>6}")
        const = E.score_rows(sel, "minutes")["const"]
        out.append(f"  {POSN[pos]:4s} n={len(sel):>5}  " + "  ".join(f"{s} {v}" for s, v in zip(E.BASELINES, cells))
                   + (f"   constant {const:.2f}" if const is not None else ""))

    out += ["", "=" * 78, "ABLATION - rho after each term, whole population (featured in brackets)", "=" * 78]
    out.append(f"  {'window':10s}{'pos':5s}" + "".join(f"{lbl:>20}" for lbl, _ in E.ABLATION) + f"{'minutes':>20}")
    for lo, hi in WINDOWS:
        for pos in (0, 1, 2, 3, 4):
            sel = pool(lo, hi, pos)
            cells = []
            for lbl, _ in list(E.ABLATION) + [("minutes", None)]:
                a, f = E.score_rows(sel, lbl), E.score_rows(sel, lbl, True)
                cells.append("-" if a["rho"] is None else
                             f"{a['rho']:+.3f} ({f['rho']:+.3f})" if f["rho"] is not None else f"{a['rho']:+.3f}")
            out.append(f"  GW{lo:>2}-{hi:<5}{POSN[pos]:5s}" + "".join(f"{x:>20}" for x in cells))
    out.append("\n  A term that does not move rho is decoration. Read per position: the")
    out.append("  clean-sheet term should matter for GK/DEF and not for FWD.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="a vaastav season folder, e.g. historical/2025-26")
    ap.add_argument("--season", default=None)
    ap.add_argument("--windows", default="",
                    help="comma-separated training windows, e.g. 4,8,12,20,38")
    ap.add_argument("--backtest", action="store_true",
                    help="rolling-origin backtest, four baselines, ablation (Steps 3-5)")
    ap.add_argument("--horizon", action="store_true",
                    help="the pre-registered horizon test (commit 9b43a78)")
    ap.add_argument("--out", help="also write the output to this file")
    args = ap.parse_args()
    E.force_utf8()
    c = canonical_from_vaastav(args.folder, args.season)
    print(f"[{c['source']} {c['season']}: {len(c['players'])} players, "
          f"{len(c['rows'])} player-gameweeks, GW1-{c['through_gw']}]")
    for n in c["notes"]:
        print(f"  ! {n}")
    print()
    if args.horizon:
        text = horizon_report(c)
        print(text)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        return
    if args.backtest:
        text = backtest_report(c)
        print(text)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text + "\n")
        return
    if not args.windows:
        print(E.reliability_table(E.measure_reliability(c),
                                  f"RELIABILITY  {c['season']}  (odd vs even gameweeks)"))
        return
    for w in [int(x) for x in args.windows.split(",")]:
        sl = E.canonical_through(c, w)
        print(E.reliability_table(
            E.measure_reliability(sl),
            f"RELIABILITY  {c['season']}  through GW{w}  (odd vs even)"))
        print()


if __name__ == "__main__":
    main()
