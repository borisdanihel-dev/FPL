"""
fpl_edge.py  —  turns fpl_export_gwN.json into decision output.

Standard library only. Offline: reads the export, prints nothing it can't prove
from the data.

Usage:
    python fpl_edge.py                        # auto-picks the newest export here
    python fpl_edge.py --horizon 5
    python fpl_edge.py --section eo,defcon
    python fpl_edge.py --out report.txt       # also write to a file
    python fpl_edge.py fpl_export_gw3.json    # or name one explicitly
    python fpl_edge.py --brief                # 20-line pre-deadline summary
    python fpl_edge.py --diff                 # vs the previous export
    python fpl_edge.py --diff fpl_export_gw2.json
    python fpl_edge.py --section wildcard --horizon 6
"""

import argparse
import csv
import glob
import math
import json
import os
import re
import sys
import time
from collections import defaultdict

POS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
DEFCON_THRESHOLD = {2: 10, 3: 12}          # DEF needs 10 CBIT, MID needs 12 CBIRT
FIRST_HALF_CHIPS = ["wildcard", "freehit", "bboost", "3xc"]
CHIP_LABEL = {"wildcard": "WC", "freehit": "FH", "bboost": "BB", "3xc": "TC"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def newest_export(folder="."):
    """Highest-numbered fpl_export_gwN.json in `folder`, else newest by mtime."""
    files = glob.glob(os.path.join(folder, "fpl_export_gw*.json"))
    if not files:
        return None
    def gw_of(f):
        m = re.search(r"gw(\d+)", os.path.basename(f))
        return int(m.group(1)) if m else -1
    return max(files, key=lambda f: (gw_of(f), os.path.getmtime(f)))


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def my_name(d):
    """My entry name. Uses entry_id when the export carries it, else infers
    from the i_own flags in league_ownership."""
    my_id = d.get("my_entry")
    for row in d.get("squads", []):
        if my_id is not None and row.get("entry_id") == my_id:
            return row["entry_name"]

    mine = {p["web_name"] for p in d.get("league_ownership", []) if p.get("i_own")}
    counts = defaultdict(int)
    for row in d.get("squads", []):
        if row["web_name"] in mine:
            counts[row["entry_name"]] += 1
    if not counts:
        return None
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        print(f"  ! cannot identify your entry: {ranked[0][0]} and {ranked[1][0]} "
              f"match equally. Re-run fpl_sync.py to export entry_id.")
    return ranked[0][0]


def previous_export(current, folder="."):
    """The export one gameweek older than `current`, if it is sitting here."""
    files = glob.glob(os.path.join(folder, "fpl_export_gw*.json"))
    def gw_of(f):
        m = re.search(r"gw(\d+)", os.path.basename(f))
        return int(m.group(1)) if m else -1
    cur = gw_of(current)
    older = [f for f in files if -1 < gw_of(f) < cur]
    return max(older, key=gw_of) if older else None


def estimate_free_transfers(d):
    """Reconstruct the FT balance from the transfer + chip log.

    1 FT per GW, banked to a max of 5. Wildcard/Free Hit consume that
    gameweek's own FT but preserve anything banked before it.
    Estimate only - confirm in the app before acting.
    """
    me = my_name(d)
    gw = d["gameweek"]
    made = defaultdict(int)
    for t in d["transfers"]:
        if t["entry_name"] == me:
            made[t["event"]] += 1
    chip_at = {c["event"]: c["name"] for c in d["chips_used"]
               if c["entry_name"] == me}

    ft = 1
    for g in range(2, gw + 1):
        if g > 2:
            ft = min(5, ft + 1)
        if chip_at.get(g) in ("wildcard", "freehit"):
            ft = min(5, ft - 1) if ft > 0 else 0
        else:
            ft = max(0, ft - made.get(g, 0))
    return min(5, ft + 1)          # the transfer granted for the upcoming GW


def build_ticker(d, horizon):
    """team -> [(gw, 'OPP (H)', fdr), ...] for the next `horizon` gameweeks."""
    tick = defaultdict(list)
    gws = sorted({f["event"] for f in d["fixtures_next6"]})[:horizon]
    for f in d["fixtures_next6"]:
        if f["event"] not in gws:
            continue
        tick[f["home"]].append((f["event"], f"{f['away']} (H)", f["h_fdr"]))
        tick[f["away"]].append((f["event"], f"{f['home']} (A)", f["a_fdr"]))
    for t in tick:
        tick[t].sort()
    return tick, gws


def fdr_avg(tick, team):
    fx = tick.get(team, [])
    return sum(x[2] for x in fx) / len(fx) if fx else 0.0


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------

def sec_league(d):
    print("=" * 78)
    print(f"LEAGUE  (after GW{d['gameweek']})")
    print("=" * 78)
    me = my_name(d)

    used = defaultdict(set)
    for c in d["chips_used"]:
        if c["event"] <= 19:
            used[c["entry_name"]].add(c["name"])

    lead = d["standings"][0]["total"]
    print(f"{'':2s} {'team':22s} {'GW':>4} {'tot':>5} {'gap':>5} {'val':>6} "
          f"{'bench':>5}  chips left (1st half)")
    for s in d["standings"]:
        left = [CHIP_LABEL[c] for c in FIRST_HALF_CHIPS if c not in used[s["entry_name"]]]
        flag = ">>" if s["entry_name"] == me else "  "
        print(f"{flag} {s['entry_name'][:22]:22s} {s['event_total']:>4} {s['total']:>5} "
              f"{s['total']-lead:>5} {s['value']/10:>6.1f} {s['points_on_bench']:>5}  "
              f"{' '.join(left) if left else '-none-'}")
    print()


def sec_eo(d, top=12):
    """Ownership gap (forward-looking) + last GW's captaincy effect (historical)."""
    print("=" * 78)
    print("MINI-LEAGUE OWNERSHIP")
    print("=" * 78)
    me = my_name(d)
    gw = d["gameweek"]
    entries = sorted({r["entry_name"] for r in d["squads"]})
    n_rivals = len(entries) - 1
    if n_rivals < 1:
        print("\n  Only one entry in the league - no rivals to compare against.\n")
        return
    chip_at = {c["entry_name"]: c["name"] for c in d["chips_used"] if c["event"] == gw}

    owns = defaultdict(dict)      # player -> entry -> multiplier
    meta = {}
    for r in d["squads"]:
        owns[r["web_name"]][r["entry_name"]] = r["multiplier"]
        meta[r["web_name"]] = (r["team"], r["pos"], r["price"])

    rows = []
    for name, by_entry in owns.items():
        mine_own = 1 if me in by_entry else 0
        rival_own = sum(1 for k in by_entry if k != me)
        my_mult = by_entry.get(me, 0)
        rival_mult = [by_entry[k] for k in by_entry if k != me]
        chipped = sum(1 for k in by_entry
                      if k != me and by_entry[k] >= 3 and chip_at.get(k) == "3xc")
        rows.append({
            "name": name, "team": meta[name][0], "pos": POS[meta[name][1]],
            "price": meta[name][2],
            "mine_own": mine_own, "rival_own": rival_own,
            "own_gap": mine_own - rival_own / n_rivals,
            "mult_gap": my_mult - sum(rival_mult) / n_rivals,
            "chipped": chipped,
        })

    print(f"\n  YOU DON'T OWN, THEY DO   (forward-looking: every point is a loss)")
    print(f"  {'player':15s}{'team':5s}{'pos':4s}{'£':>6}{'rivals':>8}{'gap/pt':>8}")
    for r in sorted(rows, key=lambda x: x["own_gap"])[:top]:
        if r["own_gap"] >= 0:
            break
        print(f"  {r['name'][:15]:15s}{r['team']:5s}{r['pos']:4s}{r['price']:>6.1f}"
              f"{r['rival_own']:>5}/{n_rivals}{r['own_gap']:>+8.2f}")

    print(f"\n  YOU OWN, THEY MOSTLY DON'T   (your differentials)")
    print(f"  {'player':15s}{'team':5s}{'pos':4s}{'£':>6}{'rivals':>8}{'gap/pt':>8}")
    for r in sorted(rows, key=lambda x: -x["own_gap"])[:top]:
        if r["own_gap"] <= 0:
            break
        print(f"  {r['name'][:15]:15s}{r['team']:5s}{r['pos']:4s}{r['price']:>6.1f}"
              f"{r['rival_own']:>5}/{n_rivals}{r['own_gap']:>+8.2f}")

    capt = [r for r in rows if abs(r["mult_gap"]) > 0.01 and r["mine_own"]]
    if capt:
        print(f"\n  CAPTAINCY EFFECT IN GW{gw}   (historical - not a transfer signal)")
        print(f"  {'player':15s}{'team':5s}{'mult gap':>10}  note")
        for r in sorted(capt, key=lambda x: x["mult_gap"])[:top]:
            note = ""
            if r["chipped"]:
                note = (f"{r['chipped']} rival(s) played Triple Captain - "
                        f"spent, cannot recur")
            print(f"  {r['name'][:15]:15s}{r['team']:5s}{r['mult_gap']:>+10.2f}  {note}")

    print("\n  gap/pt = net points gained on the average rival per point that player")
    print("  scores. Ownership gap is what transfers change. The captaincy block")
    print("  reflects one past gameweek only.\n")


def bench_vs_xi(d):
    """The bench-vs-XI check for the next gameweek. Each bench player of my
    current 15 (slots 12-15) against the lowest-projecting XI player of his
    own position, both in one unit - project_reliability with all terms - with
    P(start) and the frozen minutes-share flag beside them. Same-position
    swaps only: the formation is never chosen on the sums (review D), and a
    second swap in the same position is not chained. A blank XI player is the
    lowest by construction. Returns (week, rows, flagged_xi); week is None
    when the export has no upcoming fixtures."""
    me = my_name(d)
    gw = d["gameweek"]
    weeks = sorted({f["event"] for f in d.get("fixtures_next6") or []})
    if not weeks:
        return None, [], []
    week = weeks[0]
    by_key = {}
    for p in d["all_players"]:
        by_key.setdefault((p["web_name"], p["team"]), p)
    inp = reliability_inputs(canonical_from_export(d), gws_played=gw)
    fx = week_fixtures(d)
    window = range(gw - min(4, gw) + 1, gw + 1)
    played = defaultdict(int)
    for f in d.get("fixtures_played") or []:
        if f["event"] in window:
            played[f["home"]] += 1
            played[f["away"]] += 1

    def view(r):
        p = by_key.get((r["web_name"], r["team"]))
        if p is None:
            return None
        share = minutes_share(p, played)
        return {"name": r["web_name"], "team": r["team"], "pos": r["pos"], "slot": r["slot"],
                "proj": project_week(p["id"], p, inp, fx, week, ALL_TERMS),
                "p_start": inp["players"].get(p["id"], {}).get("p_start", 0.0),
                "share": share, "flag": share is not None and share <= FLAG_SHARE_MAX,
                "fixtures": fx[p["team"]].get(week, [])}

    mine = sorted((r for r in d["squads"] if r["entry_name"] == me), key=lambda r: r["slot"])
    mine = [v for v in (view(r) for r in mine) if v]
    xi = [v for v in mine if v["slot"] <= 11]
    bench = [v for v in mine if v["slot"] > 11]
    rows = []
    for b in bench:
        same = [x for x in xi if x["pos"] == b["pos"]]
        if not same:
            rows.append({"bench": b, "xi": None, "delta": None,
                         "verdict": "hold (no XI player of this position)"})
            continue
        low = min(same, key=lambda x: -1.0 if x["proj"] is None else x["proj"])
        bp = 0.0 if b["proj"] is None else b["proj"]
        xp = 0.0 if low["proj"] is None else low["proj"]
        if b["proj"] is None:
            verdict = "hold (bench blank)"
        elif low["proj"] is None:
            verdict = "SWAP (XI blank)"
        else:
            verdict = "SWAP" if bp > xp else "hold"
        rows.append({"bench": b, "xi": low, "delta": bp - xp, "verdict": verdict})
    return week, rows, [x for x in xi if x["flag"]]


def sec_squad(d, horizon):
    print("=" * 78)
    print(f"YOUR SQUAD  (form, flags, next {horizon} fixtures)")
    print("=" * 78)
    me = my_name(d)
    tick, _ = build_ticker(d, horizon)
    by_name = {p["web_name"]: p for p in d["all_players"]}

    mine = [r for r in d["squads"] if r["entry_name"] == me]
    mine.sort(key=lambda r: r["slot"])
    for r in mine:
        p = by_name.get(r["web_name"], {})
        fx = tick.get(r["team"], [])
        run = " ".join(f"{o.split()[0]}{o.split()[1][1]}{f}" for _, o, f in fx)
        flag = ""
        if p.get("status") and p["status"] != "a":
            flag = f"  !! {p['status']} {p.get('news','')[:40]}"
        loc = "XI " if r["slot"] <= 11 else "BEN"
        print(f"{loc} {POS[r['pos']]:4s}{r['web_name'][:14]:15s}{r['team']:5s}{r['price']:>5.1f} "
              f"pts{p.get('total_points',0):>3} L4:{p.get('pts_last4',0):>3} "
              f"m{p.get('mins_last4',0):>4} fdr{fdr_avg(tick, r['team']):>4.1f}  {run}{flag}")
    print()

    week, rows, flagged = bench_vs_xi(d)
    if week is None:
        print("  BENCH vs XI: no upcoming fixtures in the export\n")
        return
    print(f"  BENCH vs XI  GW{week}   proj = full model, all terms (one unit); each bench player")
    print("  against the lowest-projecting XI player of his own position. Same-position swaps")
    print("  only - the formation is not chosen on the sums. Picks as of the last deadline.")
    print(f"    {'bench':19s}{'proj':>6}{'P(st)':>6}{'share':>6}   {'lowest XI':19s}"
          f"{'proj':>6}{'P(st)':>6}{'share':>6}{'delta':>7}  verdict")

    def cells(v):
        proj = f"{'BLANK':>6}" if v["proj"] is None else f"{v['proj']:>6.2f}"
        share = f"{'-':>6}" if v["share"] is None else f"{v['share']:>6.2f}"
        return f"{POS[v['pos']]:4s}{v['name'][:14]:15s}{proj}{v['p_start']:>6.2f}{share}"

    for r in rows:
        b, x = r["bench"], r["xi"]
        if x is None:
            print(f"    {cells(b)}   {'-':19s}{'':25s}  {r['verdict']}")
            continue
        print(f"    {cells(b)}   {cells(x)}{r['delta']:>+7.2f}  {r['verdict']}")
    print(f"    XI under the frozen flag (minutes share <= {FLAG_SHARE_MAX}): "
          + (", ".join(f"{x['name']} ({x['share']:.2f})" for x in flagged) or "none"))
    print()


def sec_ticker(d, horizon):
    print("=" * 78)
    print(f"FIXTURE TICKER  (next {horizon}, sorted by average difficulty)")
    print("=" * 78)
    tick, gws = build_ticker(d, horizon)
    for team in sorted(tick, key=lambda t: fdr_avg(tick, t)):
        fx = tick[team]
        cells = " ".join(f"{o:>10}{f}" for _, o, f in fx)
        print(f"  {team:5s} {fdr_avg(tick, team):>4.2f}  {cells}")
    print()


def gw_index(d):
    """web_name -> list of per-gameweek rows, newest last. Empty if not exported."""
    idx = defaultdict(list)
    for r in d.get("player_gw_recent", []):
        idx[r["web_name"]].append(r)
    for k in idx:
        idx[k].sort(key=lambda r: r["event"])
    return idx


def fixtures_by_team_event(d):
    """(team, event) -> FDRs of that team's finished fixtures that gameweek.

    Grading needs it to tell a benched player from a blank. No row for a player
    whose team played means no minutes and 0 points - that forecast must be
    graded, or a model is never penalised for backing someone who did not
    feature. No fixture at all is a blank or a postponement: nothing to grade.
    """
    out = defaultdict(list)
    for f in d.get("fixtures_played") or []:
        out[(f["home"], f["event"])].append(f["h_fdr"])
        out[(f["away"], f["event"])].append(f["a_fdr"])
    return out


def _player_key(d):
    """Key for joining forecasts to results. web_name is not unique - 17 names
    are shared this season - so use the element id when the export carries it.
    Older exports have names only and fall back to them."""
    rows = d.get("player_gw_recent") or []
    if rows and "player_id" in rows[0]:
        return lambda r: int(r["player_id"] if "player_id" in r else r["id"])
    return lambda r: r["web_name"]


def sec_defcon(d, min_mins=180, top=15):
    """Per-90 defensive contribution vs threshold, plus real hit rate."""
    idx = gw_index(d)
    print("=" * 78)
    print("DEFCON RATE  (per 90 vs threshold: DEF 10, MID 12)")
    if not idx:
        print("  hit rate unavailable - re-run fpl_sync.py to export per-gameweek rows")
    print("=" * 78)
    for pos in (2, 3):
        rows = []
        for p in d["all_players"]:
            if p["pos"] != pos or p["mins_last4"] < min_mins:
                continue
            per90 = p["defcon_last4"] / p["mins_last4"] * 90
            rows.append((per90, p))
        rows.sort(key=lambda x: -x[0])
        thr = DEFCON_THRESHOLD[pos]
        print(f"\n  {POS[pos]} (threshold {thr}/match)")
        print(f"    {'player':15s}{'team':5s}{'£':>5}  {'/90':>6} {'margin':>7} "
              f"{'hit':>7} {'per game':>12}  {'own%':>5}")
        for per90, p in rows[:top]:
            gws = [g for g in idx.get(p["web_name"], []) if g["mins"] >= 60]
            if gws:
                hits = sum(1 for g in gws if (g["defcon"] or 0) >= thr)
                rate = f"{hits}/{len(gws)}"
                seq = " ".join(str(g["defcon"] or 0) for g in gws[-6:])
            else:
                rate, seq = "-", "-"
            print(f"    {p['web_name'][:15]:15s}{p['team']:5s}{p['price']:>5.1f}  "
                  f"{per90:>6.1f} {per90-thr:>+7.1f} {rate:>7} {seq:>12}  "
                  f"{p['owned_pct']:>5.1f}")
    print("\n  hit = gameweeks at or above the threshold, out of starts.")
    print("  per game = raw actions per gameweek, oldest first. A player at 10.0/90")
    print("  who went 4-16-10 is a coin flip; one who went 10-10-10 is an asset.\n")


def sec_value(d, horizon, min_mins=135, top=12):
    print("=" * 78)
    print(f"FORM x FIXTURES  (last-4 pts per £m, weighted by next-{horizon} difficulty)")
    print("=" * 78)
    tick, _ = build_ticker(d, horizon)
    for pos in (1, 2, 3, 4):
        rows = []
        for p in d["all_players"]:
            if p["pos"] != pos or p["mins_last4"] < min_mins:
                continue
            if p["status"] != "a":
                continue
            fdr = fdr_avg(tick, p["team"])
            if not fdr:
                continue
            ppm = p["pts_last4"] / p["price"]
            score = ppm * (5.0 - fdr) / 2.0
            rows.append((score, ppm, fdr, p))
        rows.sort(key=lambda x: -x[0])
        print(f"\n  {POS[pos]}")
        print(f"    {'player':15s}{'team':5s}{'£':>5} {'L4':>4} {'pts/£m':>7} "
              f"{'fdr':>5} {'score':>6} {'own%':>6}")
        for score, ppm, fdr, p in rows[:top]:
            print(f"    {p['web_name'][:15]:15s}{p['team']:5s}{p['price']:>5.1f} "
                  f"{p['pts_last4']:>4} {ppm:>7.2f} {fdr:>5.2f} {score:>6.2f} "
                  f"{p['owned_pct']:>6.1f}")
    print()


def sec_bench(d):
    print("=" * 78)
    print("BENCH AUDIT")
    print("=" * 78)
    me = my_name(d)
    for entry in sorted({r["entry_name"] for r in d["squads"]}):
        rows = [r for r in d["squads"] if r["entry_name"] == entry]
        bench = [r for r in rows if r["slot"] > 11]
        xi = [r for r in rows if r["slot"] <= 11 and r["pos"] != 1]
        lost = sum((r["gw_points"] or 0) for r in bench if r["pos"] != 1)
        worst = min(((r["gw_points"] or 0), r["web_name"]) for r in xi) if xi else (0, "-")
        best = max(((r["gw_points"] or 0), r["web_name"]) for r in bench
                   if r["pos"] != 1) if bench else (0, "-")
        flag = ">>" if entry == me else "  "
        gain = max(0, best[0] - worst[0])
        print(f"{flag} {entry[:22]:22s} bench={lost:>3}  best benched {best[1][:12]:12s}"
              f"({best[0]:>2})  worst XI {worst[1][:12]:12s}({worst[0]:>2})  "
              f"perfect-XI gain +{gain}")
    print()


def days_since_last_pl_match(d, team, event):
    """Days from the team's previous Premier League kickoff to its first
    kickoff in `event`. A calendar fact, not a signal: whether short rest costs
    points has never been tested, and cup and European matches are invisible to
    the FPL API, so this is not a fatigue measure. None when either is unknown.
    """
    from datetime import datetime

    def when(f):
        k = f.get("kickoff_time")
        return datetime.fromisoformat(k.replace("Z", "+00:00")) if k else None

    fx = (d.get("fixtures_played") or []) + (d.get("fixtures_next6") or [])
    ours = [(f["event"], when(f)) for f in fx if team in (f["home"], f["away"])]
    upcoming = [t for ev, t in ours if ev == event and t]
    if not upcoming:
        return None
    start = min(upcoming)
    before = [t for _, t in ours if t and t < start]
    if not before:
        return None
    return (start - max(before)).days


def sec_brief(d, horizon):
    me = my_name(d)
    gw = d["gameweek"]
    nxt = gw + 1
    tick, _ = build_ticker(d, horizon)
    by_name = {p["web_name"]: p for p in d["all_players"]}
    mine = sorted([r for r in d["squads"] if r["entry_name"] == me],
                  key=lambda r: r["slot"])
    stand = next(s for s in d["standings"] if s["entry_name"] == me)
    lead = d["standings"][0]

    used = {c["name"] for c in d["chips_used"]
            if c["entry_name"] == me and c["event"] <= 19}
    left = [CHIP_LABEL[c] for c in FIRST_HALF_CHIPS if c not in used]
    ft = estimate_free_transfers(d)

    print("=" * 78)
    print(f"BRIEF  ->  GW{nxt}     rank {stand['rank']}/{len(d['standings'])}   "
          f"{stand['total']} pts   {stand['total']-lead['total']:+d} on leader")
    print(f"         bank £{stand['bank']/10:.1f}m   ~{ft} free transfer(s)   "
          f"chips: {' '.join(left) if left else 'none'}")
    print("=" * 78)

    def nextfx(team):
        """Fixtures for gameweek `nxt` specifically - blank teams report BLANK,
        double gameweeks report both."""
        fx = [f for f in tick.get(team, []) if f[0] == nxt]
        if not fx:
            return (nxt, "BLANK", 5)
        if len(fx) > 1:
            return (nxt, " + ".join(f[1].split()[0] for f in fx),
                    min(f[2] for f in fx))
        return fx[0]

    alerts = []
    for r in mine:
        p = by_name.get(r["web_name"], {})
        if p.get("status", "a") != "a":
            alerts.append(f"{r['web_name']} ({p.get('status')}, "
                          f"{p.get('chance_next_round')}%) {p.get('news','')[:45]}")
    if alerts:
        print("\n  FLAGGED")
        for a in alerts:
            print(f"    !! {a}")
    else:
        print("\n  FLAGGED: none - all 15 available")

    xi = [r for r in mine if r["slot"] <= 11]
    print(f"\n  XI, GW{nxt} fixture (weakest last)")
    rows = sorted(xi, key=lambda r: -nextfx(r["team"])[2])
    for r in rows:
        _, opp, fdr = nextfx(r["team"])
        p = by_name.get(r["web_name"], {})
        mark = "  <-- soft spot" if fdr >= 4 else ""
        rest = days_since_last_pl_match(d, r["team"], nxt)
        rest = f"{rest:>2}d" if rest is not None else "  -"
        print(f"    {POS[r['pos']]:4s}{r['web_name'][:14]:15s}{opp:>10} "
              f"fdr{fdr}  L4:{p.get('pts_last4',0):>3}  rest {rest}{mark}")
    print("    rest = days since the team's previous PL match. A calendar fact,")
    print("    not a signal: its effect on points is untested, and cup and")
    print("    European minutes are invisible to the FPL API - not a fatigue measure.")

    print(f"\n  BENCH")
    for r in [x for x in mine if x["slot"] > 11]:
        _, opp, fdr = nextfx(r["team"])
        print(f"    {POS[r['pos']]:4s}{r['web_name'][:14]:15s}{opp:>10} fdr{fdr}")

    weak = [r for r in xi if nextfx(r["team"])[2] >= 4]
    if weak:
        budget = stand["bank"] / 10
        print(f"\n  UPGRADE SHORTLIST  (fdr>=4 spots, budget £{budget:.1f}m + sale)")
        for r in weak:
            cash = budget + r["price"]
            pool = [p for p in d["all_players"]
                    if p["pos"] == r["pos"] and p["price"] <= cash
                    and p["status"] == "a" and p["mins_last4"] >= 135
                    and p["web_name"] not in {m["web_name"] for m in mine}]
            pool.sort(key=lambda p: -(p["pts_last4"] / p["price"]
                                      * (5.0 - fdr_avg(tick, p["team"])) / 2.0))
            names = ", ".join(f"{p['web_name']} {p['team']} £{p['price']:.1f}"
                              for p in pool[:3])
            print(f"    out {r['web_name'][:14]:15s}(£{cash:.1f}m to spend) -> {names}")
    print()


def sec_diff(d, prev, horizon):
    print("=" * 78)
    print(f"DIFF  GW{prev.get('gameweek','?')} -> GW{d['gameweek']}")
    print("=" * 78)
    me = my_name(d)

    missing = [k for k in ("standings", "all_players", "chips_used", "squads")
               if k not in prev]
    if missing:
        print(f"\n  ! older export is missing: {', '.join(missing)}")
        print("    It was written by an earlier version of fpl_sync.py.")
        print("    Those blocks are skipped; the rest still runs.")

    if prev.get("gameweek") == d["gameweek"]:
        print(f"\n  ! both exports are GW{d['gameweek']} - the comparison is")
        print("    against itself. Delete the stale file and diff from the next GW.")

    a = {s["entry_name"]: s for s in prev.get("standings", [])}
    if not a:
        print("\n  TABLE: no comparable standings in the older export")
    if a:
        print("\n  TABLE")
    for s in (d["standings"] if a else []):
        o = a.get(s["entry_name"])
        if not o:
            continue
        dr = o["rank"] - s["rank"]
        arrow = f"{dr:+d}" if dr else " ="
        flag = ">>" if s["entry_name"] == me else "  "
        print(f"{flag} {s['entry_name'][:22]:22s} {s['rank']}({arrow})  "
              f"{s['total']:>4} ({s['total']-o['total']:+d})  "
              f"val {s['value']/10:>5.1f} ({(s['value']-o['value'])/10:+.1f})")

    pa = {p["web_name"]: p for p in prev.get("all_players", [])}
    mine = {r["web_name"] for r in d["squads"] if r["entry_name"] == me}

    if not pa:
        print("\n  price moves / new flags / form movers: need 'all_players' in "
              "both exports - skipped")
        _diff_chips(d, prev)
        return

    print("\n  YOUR SQUAD: price moves")
    moved = False
    for n in sorted(mine):
        p, o = next((x for x in d["all_players"] if x["web_name"] == n), None), pa.get(n)
        if p and o and p["price"] != o["price"]:
            moved = True
            print(f"    {n[:15]:15s}{p['team']:5s} £{o['price']:.1f} -> "
                  f"£{p['price']:.1f}  ({p['price']-o['price']:+.1f})")
    if not moved:
        print("    none")

    print("\n  NEW FLAGS (owned by anyone in the league)")
    league = {r["web_name"] for r in d["squads"]}
    newflag = False
    for p in d["all_players"]:
        if p["web_name"] not in league or p["status"] == "a":
            continue
        o = pa.get(p["web_name"])
        if o and o["status"] == "a":
            newflag = True
            print(f"    !! {p['web_name'][:15]:15s}{p['team']:5s}{p['status']} "
                  f"{p.get('chance_next_round')}%  {p['news'][:45]}")
    if not newflag:
        print("    none")

    print("\n  FORM MOVERS  (last-4 points, biggest gains, 60+ mins)")
    rows = []
    for p in d["all_players"]:
        o = pa.get(p["web_name"])
        if not o or p["mins_last4"] < 60 or p["status"] != "a":
            continue
        rows.append((p["pts_last4"] - o["pts_last4"], p))
    rows.sort(key=lambda x: -x[0])
    for delta, p in rows[:10]:
        own = " *YOURS*" if p["web_name"] in mine else ""
        print(f"    {p['web_name'][:15]:15s}{p['team']:5s}£{p['price']:>5.1f} "
              f"L4 {p['pts_last4']:>3} ({delta:+d})  own {p['owned_pct']:>5.1f}%{own}")

    _diff_chips(d, prev)


def _diff_chips(d, prev):
    if "chips_used" not in prev:
        print("\n  CHIPS PLAYED SINCE: not comparable (older export lacks the data)\n")
        return
    ca = {(c["entry_name"], c["name"]) for c in prev["chips_used"]}
    fresh = [c for c in d["chips_used"] if (c["entry_name"], c["name"]) not in ca]
    print("\n  CHIPS PLAYED SINCE")
    if fresh:
        for c in fresh:
            print(f"    {c['entry_name'][:22]:22s} {CHIP_LABEL.get(c['name'], c['name'])} "
                  f"GW{c['event']}")
    else:
        print("    none")
    print()


# ---------------------------------------------------------------------------
# canonical season slice - one shape, several sources
# ---------------------------------------------------------------------------

CANONICAL_FIELDS = frozenset({"source", "season", "through_gw", "players",
                              "rows", "team_matches", "notes"})
CANONICAL_PLAYER_FIELDS = frozenset({"player_id", "name", "pos", "team",
                                     "chance_next_round"})
CANONICAL_ROW_FIELDS = frozenset({"player_id", "event", "minutes", "starts",
                                  "pts", "xg", "xa", "bps", "defcon",
                                  "n_fixtures", "fixtures"})
CANONICAL_FIXTURE_FIELDS = frozenset({"opponent", "was_home", "fixture_id"})
CANONICAL_MATCH_FIELDS = frozenset({"event", "team", "opponent", "was_home",
                                    "goals_for", "goals_against", "fixture_id"})


def check_canonical(c):
    """Raise unless `c` matches the canonical contract exactly.

    The harness reads one shape; the live export and the historical CSVs are
    adapted into it. If one adapter emitted `expected_goals` where the other
    emits `xg`, the model would read zeros from that source and report a
    finding rather than fail, so the field sets are asserted, not duck-typed.
    """
    def same(got, want, what):
        got = set(got)
        if got != set(want):
            raise ValueError(f"canonical {what}: missing {sorted(set(want) - got)}, "
                             f"unexpected {sorted(got - set(want))}")
    same(c, CANONICAL_FIELDS, "keys")
    for p in c["players"].values():
        same(p, CANONICAL_PLAYER_FIELDS, "player")
    for r in c["rows"]:
        same(r, CANONICAL_ROW_FIELDS, "row")
        for f in r["fixtures"]:
            same(f, CANONICAL_FIXTURE_FIELDS, "row fixture")
    for m in c["team_matches"]:
        same(m, CANONICAL_MATCH_FIELDS, "team match")
    return c


def canonical_through(c, gw):
    """The same slice truncated at gameweek `gw` - training windows for the
    rolling-origin backtest, so nothing after `gw` can reach a prediction."""
    return check_canonical(dict(
        c, through_gw=gw,
        rows=[r for r in c["rows"] if r["event"] <= gw],
        team_matches=[m for m in c["team_matches"] if m["event"] <= gw]))


def canonical_from_export(d, season="2026/27"):
    """Adapter: the live fpl_export_gwN.json bundle -> canonical."""
    rows_in = d.get("player_gw_recent") or []
    if rows_in and "player_id" not in rows_in[0]:
        raise ValueError("export has no player_id in player_gw_recent - web_names "
                         "are not unique. Re-export with the current fpl_sync.py.")
    players = {int(p["id"]): {"player_id": int(p["id"]), "name": p["web_name"],
                              "pos": p["pos"], "team": p["team"],
                              "chance_next_round": p.get("chance_next_round")}
               for p in d.get("all_players", [])}
    rows = []
    for r in rows_in:
        fx = []
        if r.get("opp") is not None:          # NULL for a double: not attributable
            fx = [{"opponent": r["opp"], "was_home": r.get("venue") == "H",
                   "fixture_id": None}]
        rows.append({"player_id": int(r["player_id"]), "event": int(r["event"]),
                     "minutes": r.get("mins") or 0, "starts": r.get("starts") or 0,
                     "pts": r.get("pts") or 0, "xg": float(r.get("xg") or 0),
                     "xa": float(r.get("xa") or 0), "bps": r.get("bps") or 0,
                     "defcon": r.get("defcon") or 0,
                     "n_fixtures": r.get("n_fixtures") or 1, "fixtures": fx})
    matches = []
    for f in d.get("fixtures_played") or []:
        matches.append({"event": f["event"], "team": f["home"], "opponent": f["away"],
                        "was_home": True, "goals_for": f["h_goals"],
                        "goals_against": f["a_goals"], "fixture_id": None})
        matches.append({"event": f["event"], "team": f["away"], "opponent": f["home"],
                        "was_home": False, "goals_for": f["a_goals"],
                        "goals_against": f["h_goals"], "fixture_id": None})
    return check_canonical({"source": "export", "season": season,
                            "through_gw": d.get("gameweek", 0), "players": players,
                            "rows": rows, "team_matches": matches, "notes": []})


# ---------------------------------------------------------------------------
# reliability - does a metric agree with itself?
# ---------------------------------------------------------------------------

RELIABILITY_METRICS = ("pts", "xg", "xa", "xgi", "bps", "defcon", "minutes")


def measure_reliability(c, metrics=RELIABILITY_METRICS, min_mins=45,
                        population="appeared"):
    """Split-half reliability per metric, on a canonical slice.

    Odd gameweeks against even, not first half against second: that removes
    trend, form drift and fixture runs, which would otherwise be measured as
    reliability. Per-90 rates, tie-corrected Spearman across players, then
    Spearman-Brown up to the full sample, r_full = 2r / (1 + r).

    `minutes` must be handled separately and is: per 90 it divides minutes by
    minutes, which is the same constant for everyone and measures nothing. It
    is totalled per half across the whole population, with players who did not
    feature counted as zero.

    A metric with no variance in either half is reported `undefined`, never as
    a correlation of zero - that would read as a finding.

    `population` decides who counts for `minutes`: "appeared" (default) is
    everyone with at least one appearance in the window; "all" is every player
    in the game. The choice is not cosmetic - on GW1-4 it moves r_half from
    0.777 to 0.873, because a few hundred players who never feature are a block
    of identical zeros that agrees perfectly with itself. Players who appeared
    in one half and not the other are counted as zero in that half either way,
    which is the part that matters.
    """
    if population not in ("appeared", "all"):
        raise ValueError(f"population must be 'appeared' or 'all', got {population!r}")
    half = defaultdict(lambda: {0: defaultdict(float), 1: defaultdict(float)})
    for r in c["rows"]:
        h = half[r["player_id"]][r["event"] % 2]
        h["minutes"] += r["minutes"] or 0
        for k in ("pts", "xg", "xa", "bps", "defcon"):
            h[k] += r[k] or 0
        h["xgi"] += (r["xg"] or 0) + (r["xa"] or 0)
    out = {}
    for m in metrics:
        a, b = [], []
        if m == "minutes":
            appeared = {r["player_id"] for r in c["rows"] if (r["minutes"] or 0) > 0}
            pool = sorted(c["players"] if population == "all" else appeared)
            for pid in pool:
                h = half.get(pid)
                a.append(h[1]["minutes"] if h else 0.0)
                b.append(h[0]["minutes"] if h else 0.0)
        else:
            for h in half.values():
                if h[1]["minutes"] >= min_mins and h[0]["minutes"] >= min_mins:
                    a.append(h[1][m] / h[1]["minutes"] * 90)
                    b.append(h[0][m] / h[0]["minutes"] * 90)
        n = len(a)
        if n < 3 or len(set(a)) < 2 or len(set(b)) < 2:
            out[m] = {"n": n, "r_half": None, "r_full": None, "ci": None,
                      "weight": None, "undefined": True}
            continue
        r_half = _spearman(a, b)
        r_full = 2 * r_half / (1 + r_half) if r_half > -1 else None
        out[m] = {"n": n, "r_half": r_half, "r_full": r_full,
                  "ci": 1.96 / (n - 1) ** 0.5,
                  "weight": min(1.0, max(0.0, r_full)) if r_full is not None else 0.0,
                  "undefined": False}
    return out


def reliability_table(rel, title="RELIABILITY  (split-half, odd vs even gameweeks)"):
    lines = ["=" * 78, title, "=" * 78,
             f"  {'metric':10s}{'n':>6}{'r_half':>9}{'r_full':>9}{'95% CI':>18}{'weight':>9}"]
    for m, v in rel.items():
        if v["undefined"]:
            lines.append(f"  {m:10s}{v['n']:>6}{'undefined - no variance in a half':>45}")
            continue
        lo = max(-1.0, v['r_half'] - v['ci'])      # the normal approximation is
        hi = min(1.0, v['r_half'] + v['ci'])       # unbounded; a correlation is not
        lines.append(f"  {m:10s}{v['n']:>6}{v['r_half']:>9.3f}{v['r_full']:>9.3f}"
                     f"{lo:>10.3f} ..{hi:>6.3f}{v['weight']:>9.0%}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# reliability-weighted projection (BUILD_SPEC 2) - reads the canonical slice
# ---------------------------------------------------------------------------

XGI_GOAL_SHARE = 0.62          # BUILD_SPEC 2: xGI split between goals and assists
ALL_TERMS = frozenset({"xgi", "cs", "defcon"})
ABLATION = (("p_start", frozenset()), ("+xgi", frozenset({"xgi"})),
            ("+cs", frozenset({"xgi", "cs"})), ("+defcon", ALL_TERMS))


def reliability_inputs(c, gws_played=None, min_mins=45, prior_mins=180):
    """Everything project_reliability() needs, computed once from a TRAINING
    slice: measured weights, positional priors, per-player rates and P(start),
    team rates. Nothing here may come from the target gameweek - callers pass
    canonical_through(c, t - 1), and the leakage test holds them to it.
    """
    gws = c["through_gw"] if gws_played is None else gws_played
    rel = measure_reliability(c, metrics=("xgi", "defcon"), min_mins=min_mins)
    weights = {m: (0.0 if rel[m]["undefined"] else rel[m]["weight"])
               for m in ("xgi", "defcon")}

    lo = gws - min(4, gws)
    tot = defaultdict(lambda: defaultdict(float))
    team_xg, team_ev = defaultdict(float), defaultdict(set)
    for r in c["rows"]:
        t = tot[r["player_id"]]
        t["minutes"] += r["minutes"] or 0
        t["xgi"] += (r["xg"] or 0) + (r["xa"] or 0)
        t["defcon"] += r["defcon"] or 0
        if lo < r["event"] <= gws:
            t["starts_last4"] += r["starts"] or 0
            t["mins_last4"] += r["minutes"] or 0
        team = c["players"].get(r["player_id"], {}).get("team")
        if team is not None:
            team_xg[team] += r["xg"] or 0
            team_ev[team].add(r["event"])

    players = {}
    for pid, p in c["players"].items():
        t = tot.get(pid)
        m = t["minutes"] if t else 0.0
        players[pid] = {
            "pos": p["pos"], "team": p["team"], "minutes": m,
            "mins_last4": t["mins_last4"] if t else 0.0,
            "xgi90": (t["xgi"] / m * 90) if m else None,
            "defcon90": (t["defcon"] / m * 90) if m else None,
            "p_start": start_probability(
                {"starts_last4": t["starts_last4"] if t else 0,
                 "chance_next_round": p["chance_next_round"]}, gws),
        }

    priors = {}
    for pos in (1, 2, 3, 4):
        for k in ("xgi90", "defcon90"):
            vals = sorted(v[k] for v in players.values()
                          if v["pos"] == pos and v["minutes"] >= prior_mins
                          and v[k] is not None)
            priors[(pos, k)] = vals[len(vals) // 2] if vals else 0.0

    played = defaultdict(lambda: {"n": 0, "ga": 0.0})
    for mt in c["team_matches"]:
        played[mt["team"]]["n"] += 1
        played[mt["team"]]["ga"] += mt["goals_against"] or 0
    teams = {}
    for team in set(played) | set(team_xg):
        n = played[team]["n"] if team in played else len(team_ev[team])
        teams[team] = {
            "gc_per_match": played[team]["ga"] / n if team in played and n else None,
            "xg_per_match": team_xg[team] / n if team in team_xg and n else None}
    gcs = [v["gc_per_match"] for v in teams.values() if v["gc_per_match"] is not None]
    xgs = [v["xg_per_match"] for v in teams.values() if v["xg_per_match"] is not None]
    return {"gws": gws, "weights": weights, "reliability": rel, "priors": priors,
            "players": players, "teams": teams,
            "league_gc": sum(gcs) / len(gcs) if gcs else 1.3,
            "league_xg": sum(xgs) / len(xgs) if xgs else 1.3}


def project_reliability(pid, inputs, fixtures, terms=ALL_TERMS):
    """Expected points for one player over `fixtures`, a list of
    (opponent, was_home) for the target gameweek. Every term is a scoring rule
    times a measured probability - no fitted weights, no points term.

        xP = 2 * P(start)
           + xGI * 0.62 * GOAL_VALUE[pos] * P(start)
           + xGI * 0.38 * 3               * P(start)
           + P(clean sheet) * CS_VALUE[pos] * P(start)
           + 2 * P(DEFCON threshold)        * P(start)

    Rates are shrunk toward the positional prior by the measured reliability
    (BUILD_SPEC 2.1) - components, never the output. Clean sheet is Poisson on
    measured team rates (2.2). DEFCON is logistic on the threshold (2.3).
    No fixture -> None: a blank gets no forecast. Double -> summed (2.5).
    `terms` switches components off for the ablation; P(start) always stays.
    """
    if not fixtures:
        return None
    p = inputs["players"].get(pid)
    if p is None:
        return None
    ps = p["p_start"]
    if ps <= 0:
        return 0.0
    pos, w = p["pos"], inputs["weights"]

    def shrunk(key, metric):
        prior = inputs["priors"].get((pos, key), 0.0)
        obs = p[key]
        return prior if obs is None else obs * w[metric] + prior * (1 - w[metric])

    xgi = shrunk("xgi90", "xgi")
    dc = shrunk("defcon90", "defcon")
    gc = inputs["teams"].get(p["team"], {}).get("gc_per_match")
    gc = inputs["league_gc"] if gc is None else gc

    total = 0.0
    for opp, _home in fixtures:
        xp = 2.0 * ps
        if "xgi" in terms:
            xp += xgi * XGI_GOAL_SHARE * GOAL_VALUE.get(pos, 5) * ps
            xp += xgi * (1 - XGI_GOAL_SHARE) * 3.0 * ps
        if "cs" in terms and CS_VALUE.get(pos, 0):
            oxg = inputs["teams"].get(opp, {}).get("xg_per_match")
            oxg = inputs["league_xg"] if oxg is None else oxg
            lam = gc * (oxg / inputs["league_xg"]) if inputs["league_xg"] else gc
            xp += math.exp(-lam) * CS_VALUE[pos] * ps
        if "defcon" in terms and pos in DEFCON_THRESHOLD:
            xp += 2.0 / (1.0 + math.exp(-(dc - DEFCON_THRESHOLD[pos]) / 2.0)) * ps
        total += xp
    return total


# ---------------------------------------------------------------------------
# rolling-origin backtest (HISTORICAL_VALIDATION 3-5) - same functions as live
# ---------------------------------------------------------------------------

BASELINES = ("minutes", "points", "xgi", "bottomup")


def backtest_week(c, t, gate_mins=45):
    """Train on GW1..t-1, predict GW t, for every baseline and every ablation
    stage at once. Leak-free by construction: inputs come from
    canonical_through(c, t-1); the target week contributes only the fixture
    pairing before the fact and the actual points after it.

    Population: at least `gate_mins` minutes over the last four training
    gameweeks (the live recording gate) and a fixture in GW t. A player with
    no row in GW t was benched and scores 0 - graded, not dropped.
    """
    train = canonical_through(c, t - 1)
    inp = reliability_inputs(train, gws_played=t - 1)
    fx = defaultdict(list)
    for m in c["team_matches"]:
        if m["event"] == t:
            fx[m["team"]].append((m["opponent"], m["was_home"]))
    actual, mins_t = defaultdict(float), defaultdict(float)
    for r in c["rows"]:
        if r["event"] == t:
            actual[r["player_id"]] += r["pts"] or 0
            mins_t[r["player_id"]] += r["minutes"] or 0
    lo = t - 1 - min(4, t - 1)
    recent = defaultdict(lambda: [0.0, 0.0])
    for r in train["rows"]:
        if r["event"] > lo:
            recent[r["player_id"]][0] += r["pts"] or 0
            recent[r["player_id"]][1] += r["minutes"] or 0

    out = []
    for pid, p in inp["players"].items():
        if p["mins_last4"] < gate_mins:
            continue
        f = fx.get(p["team"])
        if not f:
            continue
        pts4, min4 = recent[pid]
        preds = {"minutes": p["p_start"] * len(f),
                 "points": pts4 / min4 * 90 if min4 else 0.0,
                 "xgi": p["xgi90"] or 0.0}
        for label, terms in ABLATION:
            preds[label] = project_reliability(pid, inp, f, terms)
        preds["bottomup"] = preds["+defcon"]
        out.append({"pid": pid, "pos": p["pos"], "event": t,
                    "actual": actual.get(pid, 0.0),
                    "featured": mins_t.get(pid, 0.0) >= 60, "preds": preds})
    return out


def score_rows(rows, source, featured_only=False):
    """Tie-corrected rho with interval, MAE, and the constant-predictor MAE,
    for one source over a pooled set of backtest rows."""
    sel = [r for r in rows if not featured_only or r["featured"]]
    n = len(sel)
    if n < 3:
        return {"n": n, "rho": None, "ci": None, "mae": None, "const": None}
    pred = [r["preds"][source] for r in sel]
    act = [r["actual"] for r in sel]
    mean = sum(act) / n
    return {"n": n, "rho": _spearman(pred, act), "ci": 1.96 / (n - 1) ** 0.5,
            "mae": sum(abs(p - a) for p, a in zip(pred, act)) / n,
            "const": sum(abs(mean - a) for a in act) / n}


SHRINK = 4.0        # prior weight, in matches


def positional_priors(players):
    """Median points per 90 among established starters, per position."""
    priors = {}
    for pos in (1, 2, 3, 4):
        vals = sorted(p["pts_last4"] / p["mins_last4"] * 90
                      for p in players
                      if p["pos"] == pos and p["mins_last4"] >= 180)
        priors[pos] = vals[len(vals) // 2] if vals else 3.0
    return priors


def personal_priors(d):
    """web_name -> that player's own points per 90 last season.

    A much stronger anchor than a positional median: it stops Haaland and a
    rotation striker being shrunk toward the same number. Empty if the export
    has no history (run: python fpl_sync.py --history).
    """
    best = {}
    for h in d.get("player_history", []):
        if h["minutes"] < 450:
            continue
        cur = best.get(h["web_name"])
        if cur is None or h["season"] > cur["season"]:
            best[h["web_name"]] = h
    return {k: v["pts"] / v["minutes"] * 90 for k, v in best.items()}


def project(p, tick, horizon, gws_played, priors, personal=None):
    """Per-gameweek projection: form shrunk toward a positional prior,
    scaled by minutes reliability, adjusted for fixtures."""
    mins = p.get("mins_last4", 0)
    if mins < 45:
        return 0.0, 0.0, 0.0
    raw90 = p["pts_last4"] / mins * 90
    matches = mins / 90.0
    prior = ((personal or {}).get(p.get("web_name"))
             or priors.get(p["pos"], 3.0))
    per90 = (raw90 * matches + prior * SHRINK) / (matches + SHRINK)
    reliability = min(1.0, mins / (90.0 * max(1, gws_played)))
    fdr = fdr_avg(tick, p["team"]) or 3.0
    fdr_adj = 1.0 + (3.0 - fdr) * 0.12
    return per90 * reliability * fdr_adj, per90, fdr


# ---------------------------------------------------------------------------
# wildcard draft - the frozen three-layer rule (CHANGELOG 2026-09-14 16:10),
# scored on the six-week sum (horizon test, 9b43a78)
# ---------------------------------------------------------------------------

ROLE_DEFCON_RATE = 0.5      # DEFCON hit rate that counts as a role edge (2+ starts)
CLUB_MAX = 3


def role_edges(d):
    """pid -> set of rules-level edges: layer 2 of the frozen rule, no model.
    pens / corners / fk: first choice. defcon: hit rate >= ROLE_DEFCON_RATE over
    2+ starts of 60 minutes. arb: a DEF whose xGI/90 reaches the MID median
    (position arbitrage - paid as a defender, plays like a midfielder)."""
    rows = defaultdict(list)
    for r in d.get("player_gw_recent") or []:
        if "player_id" in r:
            rows[int(r["player_id"])].append(r)
    xgi90 = lambda p: ((p.get("xg") or 0) + (p.get("xa") or 0)) / p["minutes"] * 90
    mids = sorted(xgi90(p) for p in d["all_players"]
                  if p["pos"] == 3 and (p.get("minutes") or 0) >= 180)
    mid_median = mids[len(mids) // 2] if mids else float("inf")
    edges = {}
    for p in d["all_players"]:
        tags = set()
        if p.get("pens_order") == 1:
            tags.add("pens")
        if p.get("corners_order") == 1:
            tags.add("corners")
        if p.get("fk_order") == 1:
            tags.add("fk")
        thr = DEFCON_THRESHOLD.get(p["pos"])
        if thr:
            starts = [r for r in rows.get(p["id"], []) if (r.get("mins") or 0) >= 60]
            if len(starts) >= 2 and (sum(1 for r in starts if (r.get("defcon") or 0) >= thr)
                                     / len(starts) >= ROLE_DEFCON_RATE):
                tags.add("defcon")
        if p["pos"] == 2 and (p.get("minutes") or 0) >= 180 and xgi90(p) >= mid_median:
            tags.add("arb")
        edges[p["id"]] = tags
    return edges


def wildcard_candidates(d, horizon=6):
    """Layers 1-3, per position. Returns ({pos: [cand, ...] ordered}, weeks,
    {reason: excluded count}). Each cand carries the six-week sum in one unit
    (the full model, every term, for every position - so the fifteen add up),
    the role edges, P(start) x fixtures and xGI/90, the fixture count in the
    horizon's later weeks (the bench tie-break), its ordering key and rank.
    For GK/DEF the full sum is the bottomup sum: the ordering is unchanged."""
    gw = d["gameweek"]
    inp = reliability_inputs(canonical_from_export(d), gws_played=gw)
    fx = week_fixtures(d)
    weeks = sorted({f["event"] for f in d.get("fixtures_next6") or []})[:horizon]
    window = range(gw - min(4, gw) + 1, gw + 1)
    played = defaultdict(int)
    for f in d.get("fixtures_played") or []:
        if f["event"] in window:
            played[f["home"]] += 1
            played[f["away"]] += 1
    roles = role_edges(d)
    cands = {1: [], 2: [], 3: [], 4: []}
    excluded = defaultdict(int)
    for p in d["all_players"]:
        if p["status"] != "a":
            excluded["status not 'a'"] += 1
            continue
        if (p.get("mins_last4") or 0) < 45:
            excluded["under 45 min in the last four"] += 1
            continue
        share = minutes_share(p, played)
        if share is None or share <= FLAG_SHARE_MAX:            # layer 1
            excluded[f"minutes share <= {FLAG_SHARE_MAX}"] += 1
            continue
        pid = p["id"]
        nfix = sum(len(fx[p["team"]].get(w, ())) for w in weeks)
        if nfix == 0:
            excluded["no fixture in the horizon"] += 1
            continue
        sum6 = sum(x for x in (project_week(pid, p, inp, fx, w, ALL_TERMS) for w in weeks)
                   if x is not None)
        nfix_later = sum(len(fx[p["team"]].get(w, ())) for w in weeks[2:])
        ip = inp["players"].get(pid, {})
        p_start, xgi90 = ip.get("p_start", 0.0), ip.get("xgi90") or 0.0
        tier = len(roles.get(pid, ()))                              # layer 2
        key = ((tier, sum6) if p["pos"] in (1, 2)                   # layer 3
               else (tier, p_start * nfix, xgi90))
        cands[p["pos"]].append({
            "id": pid, "name": p["web_name"], "team": p["team"], "pos": p["pos"],
            "price": p["price"], "roles": sorted(roles.get(pid, ())), "sum6": sum6,
            "nfix": nfix, "nfix_later": nfix_later, "p_start": p_start, "xgi90": xgi90,
            "share": share, "key": key})
    for pos in cands:
        cands[pos].sort(key=lambda c: c["key"], reverse=True)
        for i, c in enumerate(cands[pos]):
            c["rank"] = i
    return cands, weeks, dict(excluded)


def budget_split(d, budget, quota=None, given=None):
    """Money per position. `given` (--split GK,DEF,MID,FWD, any four positive
    numbers) is scaled to the budget; otherwise the current squad's shape
    scaled to the budget when it is known, else proportional to the quota.
    Never a value-per-million comparison across positions (the 16:10
    amendment)."""
    quota = quota or FULL_QUOTA
    if given:
        total = sum(given.values())
        return {k: budget * given[k] / total for k in quota}
    me = my_name(d)
    spend = defaultdict(float)
    for r in d.get("squads", []):
        if r["entry_name"] == me:
            spend[r["pos"]] += r["price"]
    if sum(spend.values()) <= 0:
        total = sum(quota.values())
        return {k: budget * n / total for k, n in quota.items()}
    total = sum(spend.values())
    return {k: budget * spend[k] / total for k in quota}


def parse_formation(s):
    """'4-3-3' -> (4, 3, 3): DEF 3-5, MID 2-5, FWD 1-3, ten outfield."""
    try:
        ndef, nmid, nfwd = (int(x) for x in str(s).split("-"))
    except ValueError:
        raise ValueError(f"formation {s!r}: want DEF-MID-FWD, e.g. 4-3-3") from None
    if not (3 <= ndef <= 5 and 2 <= nmid <= 5 and 1 <= nfwd <= 3 and ndef + nmid + nfwd == 10):
        raise ValueError(f"formation {s!r} is not legal (DEF 3-5, MID 2-5, FWD 1-3, ten outfield)")
    return ndef, nmid, nfwd


def parse_split(s):
    """'9.3,26.8,36,28.2' -> {1: 9.3, 2: 26.8, 3: 36.0, 4: 28.2}. Any four
    positive numbers; budget_split scales them to the budget."""
    try:
        parts = [float(x) for x in str(s).split(",")]
    except ValueError:
        parts = []
    if len(parts) != 4 or min(parts) <= 0:
        raise ValueError(f"split {s!r}: want four positive numbers GK,DEF,MID,FWD")
    return dict(zip((1, 2, 3, 4), parts))


def xi_shape(formation):
    """XI slots per position for a DEF-MID-FWD formation."""
    ndef, nmid, nfwd = formation
    return {1: 1, 2: ndef, 3: nmid, 4: nfwd}


def bench_key(c):
    """Cheapest first; GK/DEF ties broken by the fixture count in the horizon's
    later weeks (GW8-11 from a GW5 export - a bench body who plays in the Bench
    Boost window); then the frozen order."""
    return (c["price"], -(c["nfix_later"] if c["pos"] in (1, 2) else 0), c["rank"])


def fill_position(cands, n_xi, n_bench, share, club, club_max=CLUB_MAX):
    """XI first: walk the ordered list, taking a candidate when he fits the
    position's money with enough left for the cheapest fill of every remaining
    slot, XI and bench. The order is the whole ranking: a role edge outranks
    the model. Then the bench: the cheapest remaining candidates who passed
    layer 1, by bench_key - never the leftovers of the XI walk.
    Returns (xi, bench, spent)."""
    xi, bench, spent = [], [], 0.0
    ids = set()

    def cheapest(k):
        prices = sorted(c["price"] for c in cands
                        if c["id"] not in ids and club[c["team"]] < club_max)
        return sum(prices[:k]) if len(prices) >= k else float("inf")

    def take(c, into):
        into.append(c)
        ids.add(c["id"])
        club[c["team"]] += 1
        return c["price"]

    for c in cands:
        if len(xi) == n_xi:
            break
        if club[c["team"]] >= club_max or c["id"] in ids:
            continue
        ids.add(c["id"])
        if spent + c["price"] + cheapest(n_xi - len(xi) - 1 + n_bench) <= share + 1e-9:
            ids.discard(c["id"])
            spent += take(c, xi)
        else:
            ids.discard(c["id"])
    for c in sorted(cands, key=bench_key):           # share too small: cheapest XI fill
        if len(xi) == n_xi:
            break
        if c["id"] not in ids and club[c["team"]] < club_max:
            spent += take(c, xi)
    for c in sorted(cands, key=bench_key):           # the bench: cheapest who pass layer 1
        if len(bench) == n_bench:
            break
        if c["id"] not in ids and club[c["team"]] < club_max:
            spent += take(c, bench)
    return xi, bench, spent


def repair_split(cands, split, quota):
    """A position whose share cannot buy its cheapest legal fill is raised to
    that fill; the others give up the difference in proportion to their slack.
    Returns (split, floor): floor is each position's cheapest fill. A split
    that still cannot fill every position is left short - the build then
    overruns and the section refuses to print it as a draft."""
    floor = {pos: sum(sorted(c["price"] for c in cands[pos])[:quota[pos]]) for pos in quota}
    fixed = dict(split)
    for _ in range(len(quota)):
        short = {pos: floor[pos] - fixed[pos] for pos in quota if fixed[pos] < floor[pos] - 1e-9}
        if not short:
            break
        for pos in short:
            fixed[pos] = floor[pos]
        slack = {pos: fixed[pos] - floor[pos] for pos in quota
                 if pos not in short and fixed[pos] > floor[pos] + 1e-9}
        if not slack:
            break
        need, total = sum(short.values()), sum(slack.values())
        for pos in slack:
            fixed[pos] -= need * slack[pos] / total
    return fixed, floor


def build_three_layer_squad(cands, budget, split, formation=(4, 3, 3), quota=None):
    """Fill each position's XI slots from its own ordered shortlist within its
    share - the formation is a parameter, never a projection-driven choice -
    and its bench slots with the cheapest who pass layer 1. Then spend what is
    left by upgrading the lowest-ranked XI pick of a position to a
    higher-ranked affordable candidate, position by position, until nothing
    moves. Returns (squad, spent, split) with the split as used (repaired if
    a share could not buy its cheapest fill); each pick carries "xi"."""
    quota = quota or FULL_QUOTA
    shape = xi_shape(formation)
    split, _ = repair_split(cands, split, quota)
    club = defaultdict(int)
    picks, benches, spent = {}, {}, 0.0
    for pos in (1, 2, 3, 4):
        xi, bench, cost = fill_position(cands[pos], shape[pos], quota[pos] - shape[pos],
                                        split[pos], club)
        picks[pos], benches[pos], spent = xi, bench, spent + cost
    taken = {c["id"] for pos in picks for c in picks[pos] + benches[pos]}

    def cost():
        return sum(c["price"] for pos in picks for c in picks[pos] + benches[pos])

    def upgrade():
        spent, improved = cost(), True
        while improved:
            improved = False
            for pos in (4, 3, 2, 1):
                worst = max(picks[pos], key=lambda c: c["rank"], default=None)
                if worst is None:
                    continue
                for c in cands[pos]:
                    if c["rank"] >= worst["rank"]:
                        break
                    if c["id"] in taken or (c["team"] != worst["team"]
                                            and club[c["team"]] >= CLUB_MAX):
                        continue
                    if spent - worst["price"] + c["price"] <= budget + 1e-9:
                        picks[pos].remove(worst)
                        picks[pos].append(c)
                        taken.discard(worst["id"])
                        taken.add(c["id"])
                        spent += c["price"] - worst["price"]
                        club[worst["team"]] -= 1
                        club[c["team"]] += 1
                        improved = True
                        break

    def rebench():
        """Re-draw the bench for the XI as it now stands: the cheapest who
        pass layer 1, by bench_key - an upgrade may have freed a cheaper body."""
        moved = False
        for pos in (1, 2, 3, 4):
            for c in benches[pos]:
                club[c["team"]] -= 1
                taken.discard(c["id"])
            new = []
            for c in sorted(cands[pos], key=bench_key):
                if len(new) == quota[pos] - shape[pos]:
                    break
                if c["id"] not in taken and club[c["team"]] < CLUB_MAX:
                    new.append(c)
                    taken.add(c["id"])
                    club[c["team"]] += 1
            moved |= [c["id"] for c in new] != [c["id"] for c in benches[pos]]
            benches[pos] = new
        return moved

    for _ in range(20):                 # upgrades free bench money and vice versa
        upgrade()
        if not rebench():
            break
    spent = cost()
    squad = ([dict(c, xi=True) for pos in (1, 2, 3, 4) for c in picks[pos]]
             + [dict(c, xi=False) for pos in (1, 2, 3, 4) for c in benches[pos]])
    return squad, spent, split


WC_FORMATION = "4-3-3"      # --formation DEF-MID-FWD: the XI shape is a parameter
WC_SPLIT = None             # --split GK,DEF,MID,FWD: money per position, scaled to the budget


def sec_wildcard(d, horizon, formation=None, split=None):
    """The frozen three-layer rule, scored on the six-week sum. No
    cross-position choice is made on the sums: the formation is a parameter,
    the captain and vice are the best MID/FWD, until the DEF calibration is
    addressed (~GW10)."""
    form = parse_formation(formation or WC_FORMATION)
    given = parse_split(split) if split else None
    cands, weeks, excluded = wildcard_candidates(d, horizon)
    me = my_name(d)
    stand = next((s for s in d["standings"] if s["entry_name"] == me), None)
    budget = stand["value"] / 10.0 if stand else 100.0   # value includes the bank
    split_used = budget_split(d, budget, given=given)
    form_str = "-".join(str(n) for n in form)
    print("=" * 78)
    print(f"WILDCARD DRAFT  (frozen three-layer rule, six-week sum GW{weeks[0]}-{weeks[-1]})"
          if weeks else "WILDCARD DRAFT  (no upcoming fixtures in the export)")
    print("=" * 78)
    if not weeks:
        return
    print(f"  budget £{budget:.1f}m = team value"
          + (f" (bank £{stand['bank']/10:.1f}m included)" if stand else ""))
    print(f"  formation {form_str} (--formation): the XI is the top of each position's "
          "ordered list, never a choice on the sums")
    print("  split by position, " + ("--split scaled to the budget" if given else "current squad shape")
          + ": " + "  ".join(f"{POS[k]} £{v:.1f}m" for k, v in split_used.items()))
    print("  layer 1  excluded: " + ", ".join(f"{v} {k}" for k, v in sorted(excluded.items())))
    print("  layer 2  role edges: pens / corners / fk = first choice; defcon = hit rate "
          f">= {ROLE_DEFCON_RATE:.0%} over 2+ starts; arb = DEF with xGI/90 >= MID median")
    print("  layer 3  within position: GK/DEF by six-week bottomup; MID/FWD by P(start) x")
    print("           fixtures, then xGI/90. A role edge outranks the model.")
    print(f"\n  SHORTLISTS  (top 8 per position; 6wk = full model, all terms, GW{weeks[0]}-{weeks[-1]}:")
    print("               one unit for every position, next to the ordering metric)")
    for pos in (1, 2, 3, 4):
        print(f"    {POS[pos]}   {'player':15s}{'team':5s}{'£':>5}  {'roles':16s}{'6wk':>6}"
              f"{'P(st)xfix':>10}{'xGI/90':>8}")
        for c in cands[pos][:8]:
            print(f"         {c['name'][:14]:15s}{c['team']:5s}{c['price']:>5.1f}  "
                  f"{','.join(c['roles'])[:15]:16s}{c['sum6']:>6.1f}"
                  f"{c['p_start'] * c['nfix']:>10.2f}{c['xgi90']:>8.2f}")
    squad, spent, split_built = build_three_layer_squad(cands, budget, split_used, form)
    if any(abs(split_built[k] - split_used[k]) > 0.05 for k in split_used):
        print("\n  split repaired so every position can buy its cheapest fill: "
              + "  ".join(f"{POS[k]} £{v:.1f}m" for k, v in split_built.items()))
    if len(squad) < sum(FULL_QUOTA.values()) or spent > budget + 1e-9:
        print(f"\n  Could not assemble a legal 15 within £{budget:.1f}m from the candidates"
              f" (this fill costs £{spent:.1f}m).\n")
        return
    xi = [c for c in squad if c["xi"]]
    bench = [c for c in squad if not c["xi"]]
    ranked = sorted((c for c in xi if c["pos"] in (3, 4)), key=lambda c: -c["sum6"])
    captain = ranked[0] if ranked else None
    vice = ranked[1] if len(ranked) > 1 else None
    mine = {(r["web_name"], r["team"]) for r in d["squads"] if r["entry_name"] == me}
    keeps = sorted(c["name"] for c in squad if (c["name"], c["team"]) in mine)
    print(f"\n  SQUAD  £{spent:.1f}m of £{budget:.1f}m   keeps from your current 15 ({len(keeps)}): "
          f"{', '.join(keeps) or '-'}")
    print(f"    XI ({form_str}, --formation)   sums = full model, all terms   by = the frozen ordering metric")
    for c in sorted(xi, key=lambda c: (c["pos"], c["rank"])):
        metric = (f"bottomup {c['sum6']:.1f}" if c["pos"] in (1, 2)
                  else f"P(st)xfix {c['p_start'] * c['nfix']:.2f} xGI/90 {c['xgi90']:.2f}")
        mark = ("  (C)" if captain and c["id"] == captain["id"]
                else "  (V)" if vice and c["id"] == vice["id"] else "")
        print(f"      {POS[c['pos']]:4s}{c['name'][:14]:15s}{c['team']:5s}{c['price']:>5.1f}"
              f"  6wk {c['sum6']:>5.1f}  by {metric:31s}{','.join(c['roles'])}{mark}")
    print("    captain restricted to MID/FWD: DEF over-spread")
    fx = week_fixtures(d)
    later = weeks[2:]                                   # the bench's GW8-11 from a GW5 export
    print("    BENCH  cheapest who pass layer 1 per remaining slot"
          + (f" (GK/DEF ties: GW{later[0]}-{later[-1]} fixture count)"
             f"{'':6s}fixtures GW{later[0]}-{later[-1]}" if later else ""))
    for c in sorted(bench, key=lambda c: (c["pos"], c["price"], c["rank"])):
        cells = []
        for w in later:
            f = fx[c["team"]].get(w, [])
            cells.append(" + ".join(f"{o} ({'H' if h else 'A'}) {fdr}" for o, h, fdr in f) or "BLANK")
        print(f"      {POS[c['pos']]:4s}{c['name'][:14]:15s}{c['team']:5s}{c['price']:>5.1f}"
              f"  6wk {c['sum6']:>5.1f}   {' | '.join(cells)}")
    xi_sum, bench_sum = sum(c["sum6"] for c in xi), sum(c["sum6"] for c in bench)
    print(f"    XI six-week sum {xi_sum:.1f}   bench six-week sum {bench_sum:.1f}   "
          f"fifteen {xi_sum + bench_sum:.1f}   (one unit: full model, all terms)")
    print()


def _build_squad(pool, budget, quota=None):
    """Greedy by value-per-million, then hill-climb swaps to spend the rest.
    `quota` is players per position; the default is a full 15."""
    quota = quota or {1: 2, 2: 5, 3: 5, 4: 3}
    picked, spent = [], 0.0
    club = defaultdict(int)
    filled = defaultdict(int)

    for p in sorted(pool, key=lambda x: -x["vpm"]):
        if filled[p["pos"]] >= quota[p["pos"]] or club[p["team"]] >= 3:
            continue
        if spent + p["price"] > budget:
            continue
        picked.append(p)
        spent += p["price"]
        filled[p["pos"]] += 1
        club[p["team"]] += 1
    if sum(filled.values()) < sum(quota.values()):
        return None

    for _ in range(400):
        best = None
        for out in picked:
            for inn in pool:
                if inn["pos"] != out["pos"] or inn in picked:
                    continue
                if spent - out["price"] + inn["price"] > budget:
                    continue
                if inn["team"] != out["team"] and club[inn["team"]] >= 3:
                    continue
                gain = inn["proj"] - out["proj"]
                if gain > 0 and (best is None or gain > best[0]):
                    best = (gain, out, inn)
        if not best:
            break
        _, out, inn = best
        picked.remove(out)
        picked.append(inn)
        spent += inn["price"] - out["price"]
        club[out["team"]] -= 1
        club[inn["team"]] += 1
    return picked


def _best_xi(squad):
    """Highest-projecting legal XI: 1 GK, 3-5 DEF, 2-5 MID, 1-3 FWD."""
    by = {k: sorted([p for p in squad if p["pos"] == k], key=lambda x: -x["proj"])
          for k in (1, 2, 3, 4)}
    best, best_pts = None, -1
    for ndef in range(3, 6):
        for nmid in range(2, 6):
            nfwd = 10 - ndef - nmid
            if not 1 <= nfwd <= 3:
                continue
            xi = by[1][:1] + by[2][:ndef] + by[3][:nmid] + by[4][:nfwd]
            if len(xi) != 11:
                continue
            pts = sum(p["proj"] for p in xi)
            if pts > best_pts:
                best, best_pts = xi, pts
    return best or []


def _spearman(a, b):
    """Rank correlation, tied values sharing their average rank.

    Ties are the norm here - most players score 1 or 2 in a week. Ranking them
    in input order made the answer depend on row order, and the export's row
    order (points DESC) is correlated with any form-based prediction, which
    pushed those correlations negative by construction.
    """
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2.0
            i = j + 1
        return r
    n = len(a)
    if n < 3:
        return 0.0
    ra, rb = rank(a), rank(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    den = (sum((ra[i] - ma) ** 2 for i in range(n))
           * sum((rb[i] - mb) ** 2 for i in range(n))) ** 0.5
    return num / den if den else 0.0


def _rho_verdict(rho, n):
    """Read a rank correlation against the project's bar: +0.20, with a 95%
    interval clear of zero. The interval decides whether it is real at all -
    +0.15 on 224 players is real; +0.30 on 20 players is not."""
    half = 1.96 / (n - 1) ** 0.5 if n > 2 else float("inf")
    if rho - half <= 0 <= rho + half:
        return "indistinguishable from zero"
    if rho < 0:
        return "inverted - actively misleading"
    if rho < 0.20:
        return "real but weak - below the +0.20 bar"
    return "clears +0.20 this week - needs three graded weeks"


def backtest_population(d, train, target):
    """Everyone with 90+ training minutes whose team played the target week.

    A player with no target-week row was benched and scored 0; he is graded,
    not dropped - dropping him removes exactly the cases a minutes signal
    exists to catch. Grouped by element id where the export has it: two players
    sharing a web_name are two players.
    """
    key = _player_key(d)
    fx = fixtures_by_team_event(d)
    by = defaultdict(list)
    for r in d.get("player_gw_recent", []):
        by[key(r)].append(r)
    built = []
    for rows in by.values():
        tr = [r for r in rows if r["event"] in train]
        te = [r for r in rows if r["event"] == target]
        if not tr:
            continue
        team = tr[0]["team"]
        if not te and (team, target) not in fx:
            continue                      # blank or postponed: nothing to grade
        mins = sum(r["mins"] for r in tr)
        if mins < 90:
            continue
        built.append({
            "web_name": tr[0]["web_name"], "team": team, "pos": tr[0]["pos"],
            "pts_last4": sum(r["pts"] for r in tr), "mins_last4": mins,
            "actual": sum(r["pts"] for r in te),          # 0 when benched
            "target_fdr": te[0].get("fdr") if te else min(fx[(team, target)]),
            "benched": not te,
        })
    return built


def sec_backtest(d, horizon):
    """Score the projection model against a gameweek it did not see."""
    idx = gw_index(d)
    print("=" * 78)
    print("BACKTEST  (projection vs what actually happened)")
    print("=" * 78)
    if not idx:
        print("\n  Needs per-gameweek rows. Run:  python fpl_sync.py --refetch\n")
        return

    events = sorted({r["event"] for r in d.get("player_gw_recent", [])})
    if len(events) < 3:
        print(f"\n  Only {len(events)} gameweek(s) of history. Needs 3+ to hold one out.\n")
        return

    target = events[-1]
    train = events[:-1]
    built = backtest_population(d, train, target)

    priors = positional_priors(built)
    personal = personal_priors(d)
    have_fdr = any(r.get("fdr") is not None
                   for rows in idx.values() for r in rows)
    scored = []
    for p in built:
        tick = {p["team"]: [(target, "x", p["target_fdr"])]} if p.get("target_fdr") else {}
        proj, _, _ = project(p, tick, horizon, len(train), priors, personal)
        scored.append((proj, p["actual"], p))

    n = len(scored)
    mean_actual = sum(ac for _, ac, _ in scored) / n
    mae = sum(abs(pr - ac) for pr, ac, _ in scored) / n
    bias = sum(pr - ac for pr, ac, _ in scored) / n
    mae_base = sum(abs(p["pts_last4"] / max(1, len(train)) - ac)
                   for _, ac, p in scored) / n
    mae_const = sum(abs(mean_actual - ac) for _, ac, _ in scored) / n
    rho = _spearman([pr for pr, _, _ in scored], [ac for _, ac, _ in scored])

    print(f"\n  trained on GW{train[0]}-{train[-1]}, tested on GW{target}, "
          f"{n} players ({sum(p['benched'] for p in built)} benched that week, "
          f"graded as 0)")
    print(f"  priors: {len(personal)} players anchored to their own last season, "
          f"rest to positional median")
    print("  (fixture adjustment ON - using each player's actual FDR that week)"
          if have_fdr else
          "  (fixture adjustment OFF - re-export to include per-match FDR)")
    print(f"    model                  MAE {mae:>5.2f}   bias {bias:>+5.2f}")
    print(f"    flat average of training MAE {mae_base:>5.2f}")
    print(f"    CONSTANT ({mean_actual:.2f} for all)  MAE {mae_const:>5.2f}"
          f"   <- the bar that matters")
    if mae < mae_const:
        print(f"    PASS: beats a constant guess by {mae_const-mae:.2f} pts/player")
    else:
        print(f"    FAIL: WORSE than guessing the mean, by {mae-mae_const:.2f} "
              f"pts/player")
    print(f"\n    Spearman rank correlation {rho:>+6.3f}   "
          f"({_rho_verdict(rho, n)})")
    print("    Ordering is what a squad picker needs. Below about +0.20 the")
    print("    projection is not usable for ranking players.")

    print("\n  BIAS BY PROJECTION QUINTILE  (is it overconfident at the top?)")
    ordered = sorted(scored, key=lambda x: x[0])
    k = max(1, n // 5)
    for i in range(5):
        grp = ordered[i * k:(i + 1) * k] if i < 4 else ordered[4 * k:]
        if not grp:
            continue
        mp = sum(x[0] for x in grp) / len(grp)
        ma = sum(x[1] for x in grp) / len(grp)
        print(f"    Q{i+1}  proj {grp[0][0]:>4.1f}-{grp[-1][0]:<4.1f} n={len(grp):>3}"
              f"  projected {mp:>5.2f}  actual {ma:>5.2f}  bias {mp-ma:>+5.2f}")
    print("    A rising bias down this column means the model is reading noise")
    print("    as signal: the players it likes least outscore the ones it likes most.")

    print("\n  BIAS BY POSITION")
    for pos in (1, 2, 3, 4):
        grp = [x for x in scored if x[2]["pos"] == pos]
        if not grp:
            continue
        print(f"    {POS[pos]:4s} n={len(grp):>3}  "
              f"MAE {sum(abs(a - b) for a, b, _ in grp)/len(grp):>5.2f}  "
              f"bias {sum(a - b for a, b, _ in grp)/len(grp):>+5.2f}")

    scored.sort(key=lambda x: x[0] - x[1])
    print("\n  WORST UNDER-CALLS  (it said low, they hauled)")
    for pr, ac, p in scored[:6]:
        print(f"    {p['web_name'][:15]:15s}{p['team']:5s} proj {pr:>5.2f}  "
              f"actual {ac:>3}")
    print("\n  WORST OVER-CALLS  (it said high, they blanked)")
    for pr, ac, p in scored[-6:][::-1]:
        print(f"    {p['web_name'][:15]:15s}{p['team']:5s} proj {pr:>5.2f}  "
              f"actual {ac:>3}")
    print("\n  One gameweek is noise. Read the trend across several runs, not this.\n")


def sec_fdr(d, horizon):
    """Does FPL's difficulty rating actually predict what happened?"""
    print("=" * 78)
    print("FDR AUDIT  (rating vs result, all finished fixtures)")
    print("=" * 78)
    played = d.get("fixtures_played")
    if not played:
        print("\n  Needs finished fixtures with scores. Run:  python fpl_sync.py")
        print("  (re-export with the current fpl_sync.py to include them)\n")
        return

    # one row per team-match: the difficulty they were given, what they did
    obs = []
    for f in played:
        if f["h_goals"] is None or f["a_goals"] is None:
            continue
        obs.append((f["h_fdr"], f["h_goals"], f["a_goals"], f["home"], "H", f["event"]))
        obs.append((f["a_fdr"], f["a_goals"], f["h_goals"], f["away"], "A", f["event"]))
    if not obs:
        print("\n  No finished fixtures with scores yet.\n")
        return

    print(f"\n  {len(obs)//2} matches, {len(obs)} team-performances\n")
    print(f"  {'FDR':>4}{'n':>5}{'goals for':>11}{'conceded':>10}"
          f"{'clean sheets':>14}{'win rate':>10}")
    buckets = defaultdict(list)
    for fdr, gf, ga, *_ in obs:
        buckets[fdr].append((gf, ga))
    for fdr in sorted(buckets):
        rows = buckets[fdr]
        n = len(rows)
        gf = sum(r[0] for r in rows) / n
        ga = sum(r[1] for r in rows) / n
        cs = sum(1 for r in rows if r[1] == 0) / n
        wr = sum(1 for r in rows if r[0] > r[1]) / n
        print(f"  {fdr:>4}{n:>5}{gf:>11.2f}{ga:>10.2f}{cs:>13.0%}{wr:>10.0%}")

    lo = [r for f, *r in [(f, gf, ga) for f, gf, ga, *_ in obs] if f <= 2]
    hi = [r for f, *r in [(f, gf, ga) for f, gf, ga, *_ in obs] if f >= 4]
    if lo and hi:
        gf_lo = sum(r[0] for r in lo) / len(lo)
        gf_hi = sum(r[0] for r in hi) / len(hi)
        cs_lo = sum(1 for r in lo if r[1] == 0) / len(lo)
        cs_hi = sum(1 for r in hi if r[1] == 0) / len(hi)
        print(f"\n  easy (FDR<=2) vs hard (FDR>=4)")
        print(f"    goals scored   {gf_lo:.2f}  vs  {gf_hi:.2f}   "
              f"gap {gf_lo-gf_hi:+.2f}")
        print(f"    clean sheets   {cs_lo:>4.0%}  vs  {cs_hi:>4.0%}   "
              f"gap {cs_lo-cs_hi:+.0%}")
        if gf_lo - gf_hi < 0.3:
            print("    The rating is barely separating attacking output. Weight it lightly.")
        if abs(cs_lo - cs_hi) < 0.10:
            print("    The rating is not separating clean sheets at all.")

    print("\n  BIGGEST UPSETS  (favourite by 2+ difficulty points, lost or drew)")
    ups = []
    for f in played:
        if f["h_goals"] is None:
            continue
        gap = f["a_fdr"] - f["h_fdr"]
        if gap >= 2 and f["h_goals"] <= f["a_goals"]:
            ups.append((abs(gap), f, f["home"], f["away"]))
        elif gap <= -2 and f["a_goals"] <= f["h_goals"]:
            ups.append((abs(gap), f, f["away"], f["home"]))
    if not ups:
        print("    none - the ratings held up")
    for gap, f, fav, dog in sorted(ups, key=lambda x: -x[0]):
        print(f"    GW{f['event']}  {f['home']} {f['h_goals']}-{f['a_goals']} "
              f"{f['away']}   {fav} was favoured by {gap}")
    print()


def _mean_sd(v):
    n = len(v)
    if not n:
        return 0, 0.0, 0.0
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5 if n > 1 else 0.0
    return n, m, sd


def _gap_ci(a, b):
    """Difference in means and its 95% interval. Returns (gap, halfwidth)."""
    n1, m1, s1 = _mean_sd(a)
    n2, m2, s2 = _mean_sd(b)
    if not n1 or not n2:
        return 0.0, float("inf")
    se = (s1 ** 2 / n1 + s2 ** 2 / n2) ** 0.5
    return m1 - m2, 1.96 * se


def sec_sensitivity(d, horizon):
    """Does fixture difficulty move returns - and is the move bigger than noise?"""
    print("=" * 78)
    print("FIXTURE SENSITIVITY  (per player-match, with 95% intervals)")
    print("=" * 78)
    rows = [r for r in d.get("player_gw_recent", [])
            if r.get("fdr") is not None and r["mins"] >= 60]
    if not rows:
        print("\n  Needs per-match FDR. Re-export with the current fpl_sync.py\n")
        return

    print(f"\n  {len(rows)} player-matches of 60+ minutes\n")
    print(f"  {'':5s}{'easy FDR<=2':>16}{'hard FDR>=4':>16}{'gap':>8}"
          f"{'95% interval':>20}  verdict")
    real = []
    for pos in (1, 2, 3, 4):
        e = [r["pts"] for r in rows if r["pos"] == pos and r["fdr"] <= 2]
        h = [r["pts"] for r in rows if r["pos"] == pos and r["fdr"] >= 4]
        if not e or not h:
            continue
        n1, m1, _ = _mean_sd(e)
        n2, m2, _ = _mean_sd(h)
        gap, ci = _gap_ci(e, h)
        sig = abs(gap) > ci
        if sig:
            real.append(POS[pos])
        print(f"  {POS[pos]:5s}{m1:>8.2f} (n={n1:>3}){m2:>8.2f} (n={n2:>3})"
              f"{gap:>8.2f}{gap-ci:>11.2f} to {gap+ci:<6.2f}  "
              f"{'REAL' if sig else 'noise'}")

    print("\n  CHASING EASY vs AVOIDING HARD")
    for pos in (1, 2, 3, 4):
        a = [r["pts"] for r in rows if r["pos"] == pos and r["fdr"] <= 2]
        b = [r["pts"] for r in rows if r["pos"] == pos and r["fdr"] == 3]
        c = [r["pts"] for r in rows if r["pos"] == pos and r["fdr"] >= 4]
        if not (a and b and c):
            continue
        g1, c1 = _gap_ci(a, b)
        g2, c2 = _gap_ci(b, c)
        print(f"    {POS[pos]:5s} FDR2 over FDR3 {g1:>+6.2f} (+-{c1:.2f})"
              f"    FDR3 over FDR4+ {g2:>+6.2f} (+-{c2:.2f})")

    print("\n  HOME vs AWAY")
    for pos in (1, 2, 3, 4):
        h = [r["pts"] for r in rows if r["pos"] == pos and r["venue"] == "H"]
        a = [r["pts"] for r in rows if r["pos"] == pos and r["venue"] == "A"]
        if not (h and a):
            continue
        gap, ci = _gap_ci(h, a)
        print(f"    {POS[pos]:5s} gap {gap:>+5.2f}  +-{ci:.2f}   "
              f"{'REAL' if abs(gap) > ci else 'noise'}")

    print("\n  Only rows marked REAL survive the sample size. Everything else is")
    print("  a difference this data cannot distinguish from chance - do not spend")
    print("  transfers on it. Re-run as gameweeks accumulate and the intervals")
    print("  will narrow.")
    if real:
        print(f"  Currently real: {', '.join(real)}.\n")
    else:
        print("  Nothing is currently distinguishable from noise.\n")


def sec_arbitrage(d, horizon):
    """Players whose FPL position is worth more than the role they actually play."""
    print("=" * 78)
    print("POSITION ARBITRAGE  (the scoring system is wrong about these players)")
    print("=" * 78)
    ap = [p for p in d["all_players"] if p["minutes"] >= 180 and p["status"] == "a"]
    if not ap:
        print("\n  Not enough minutes played yet.\n")
        return
    tick, _ = build_ticker(d, horizon)

    print("\n  A defender who plays forward earns 6 for a goal AND 4 for a clean")
    print("  sheet. FPL fixes position in July and rarely changes it.\n")

    for pos, label in ((2, "DEFENDERS with attacking output"),
                       (3, "MIDFIELDERS carrying defensive load (DEFCON + goals)")):
        rows = []
        for p in ap:
            if p["pos"] != pos:
                continue
            per90 = (p["xg"] + p["xa"]) / p["minutes"] * 90
            dc90 = p["defcon_last4"] / max(1, p["mins_last4"]) * 90
            score = per90 if pos == 2 else per90 + dc90 / 12.0
            rows.append((score, per90, dc90, p))
        rows.sort(key=lambda x: -x[0])
        print(f"  {label}")
        print(f"    {'player':15s}{'team':5s}{'£':>5}{'xG+xA/90':>10}{'DEFCON/90':>11}"
              f"{'own%':>7}{'fdr':>6}")
        for score, per90, dc90, p in rows[:8]:
            print(f"    {p['web_name'][:15]:15s}{p['team']:5s}{p['price']:>5.1f}"
                  f"{per90:>10.2f}{dc90:>11.1f}{p['owned_pct']:>7.1f}"
                  f"{fdr_avg(tick, p['team']):>6.2f}")
        print()

    thr = [p for p in ap if p.get("threat") is not None and p["pos"] in (3, 4)]
    if thr:
        print("  CHANCE QUALITY vs FINISHING  (threat is FPL's shot-danger index)")
        print("  High threat, few returns = chances are coming, goals have not.\n")
        rows = []
        for p in thr:
            t90 = p["threat"] / p["minutes"] * 90
            ret = p["goals"] + p["assists"]
            rows.append((t90, ret, p))
        rows.sort(key=lambda x: -x[0])
        print(f"    {'player':15s}{'team':5s}{'£':>5}{'threat/90':>11}"
              f"{'G+A':>6}{'xG+xA':>8}{'own%':>7}")
        for t90, ret, p in rows[:10]:
            flag = "  <-- due" if t90 > 40 and ret <= 1 else ""
            print(f"    {p['web_name'][:15]:15s}{p['team']:5s}{p['price']:>5.1f}"
                  f"{t90:>11.1f}{ret:>6}{p['xg']+p['xa']:>8.2f}"
                  f"{p['owned_pct']:>7.1f}{flag}")
        print()
    else:
        print("  threat unavailable - re-export with the current fpl_sync.py\n")


def sec_consistency(d, horizon):
    """Floor vs ceiling: who delivers every week, who is all-or-nothing."""
    print("=" * 78)
    print("CONSISTENCY  (delivery pattern, not total)")
    print("=" * 78)
    idx = gw_index(d)
    if not idx:
        print("\n  Needs per-gameweek rows. Run:  python fpl_sync.py --refetch\n")
        return

    rows = []
    for name, gws in idx.items():
        played = [g for g in gws if g["mins"] >= 60]
        if len(played) < 3:
            continue
        pts = [g["pts"] for g in played]
        n = len(pts)
        mean = sum(pts) / n
        sd = (sum((x - mean) ** 2 for x in pts) / (n - 1)) ** 0.5
        blanks = sum(1 for x in pts if x <= 2)
        rows.append({"name": name, "team": played[0]["team"],
                     "pos": played[0]["pos"], "pts": pts, "mean": mean,
                     "sd": sd, "blanks": blanks, "floor": min(pts),
                     "ceiling": max(pts), "n": n})

    if not rows:
        print("\n  Not enough full appearances yet.\n")
        return

    good = [r for r in rows if r["mean"] >= 3.0]
    print(f"\n  {len(rows)} players with 3+ full appearances, "
          f"{len(good)} averaging 3.0+\n")

    print("  METRONOMES  (good average, small swing - captain and bench-boost picks)")
    print(f"    {'player':15s}{'team':5s}{'pos':4s}{'mean':>6}{'swing':>7}"
          f"{'floor':>6}{'blanks':>7}   per game")
    for r in sorted(good, key=lambda x: (x["sd"], -x["mean"]))[:10]:
        seq = " ".join(str(x) for x in r["pts"][-6:])
        print(f"    {r['name'][:15]:15s}{r['team']:5s}{POS[r['pos']]:4s}"
              f"{r['mean']:>6.1f}{r['sd']:>7.1f}{r['floor']:>6}{r['blanks']:>7}"
              f"   {seq}")

    print("\n  LOTTERY TICKETS  (same average, huge swing - differentials, not anchors)")
    for r in sorted(good, key=lambda x: -x["sd"])[:8]:
        seq = " ".join(str(x) for x in r["pts"][-6:])
        print(f"    {r['name'][:15]:15s}{r['team']:5s}{POS[r['pos']]:4s}"
              f"{r['mean']:>6.1f}{r['sd']:>7.1f}{r['floor']:>6}{r['blanks']:>7}"
              f"   {seq}")

    me = my_name(d)
    mine = {r["web_name"] for r in d["squads"] if r["entry_name"] == me}
    ours = [r for r in rows if r["name"] in mine]
    if ours:
        print("\n  YOUR SQUAD")
        for r in sorted(ours, key=lambda x: -x["mean"]):
            seq = " ".join(str(x) for x in r["pts"][-6:])
            tag = ""
            if r["mean"] >= 3 and r["sd"] <= 2:
                tag = "  steady"
            elif r["sd"] >= 4:
                tag = "  volatile"
            print(f"    {r['name'][:15]:15s}{r['team']:5s}{POS[r['pos']]:4s}"
                  f"{r['mean']:>6.1f}{r['sd']:>7.1f}{r['floor']:>6}"
                  f"{r['blanks']:>7}   {seq}{tag}")

    print("\n  swing is the standard deviation of gameweek scores. Three matches is")
    print("  far too few to trust an individual figure - read it again at GW8.\n")


def load_projections(path):
    """Read an external projections CSV. Tolerant about column names.

    Wants a player identifier and a predicted-points column. Recognised:
      id / element / element_id / player_id      -> FPL element id
      name / web_name / player / Player          -> player name
      xPts / pred / points / prediction / proj    -> forecast
      gw / event / gameweek                      -> optional gameweek
    """
    import csv
    ID_COLS = ("id", "element", "element_id", "player_id")
    NAME_COLS = ("web_name", "name", "player", "player_name")
    PTS_COLS = ("xpts", "pred", "prediction", "points", "proj", "predicted_points",
                "xp", "forecast")
    GW_COLS = ("gw", "event", "gameweek", "round")

    out = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return out, "empty file"
        low = {c.lower().strip(): c for c in reader.fieldnames}
        id_c = next((low[c] for c in ID_COLS if c in low), None)
        name_c = next((low[c] for c in NAME_COLS if c in low), None)
        pts_c = next((low[c] for c in PTS_COLS if c in low), None)
        gw_c = next((low[c] for c in GW_COLS if c in low), None)
        if pts_c is None:
            return out, f"no forecast column found in: {', '.join(reader.fieldnames)}"
        if id_c is None and name_c is None:
            return out, "no player id or name column found"
        for row in reader:
            try:
                val = float(row[pts_c])
            except (TypeError, ValueError):
                continue
            key = None
            if id_c and row.get(id_c, "").strip():
                try:
                    key = ("id", int(float(row[id_c])))
                except ValueError:
                    key = None
            if key is None and name_c:
                key = ("name", row[name_c].strip())
            if key is None:
                continue
            gw = None
            if gw_c and row.get(gw_c, "").strip():
                try:
                    gw = int(float(row[gw_c]))
                except ValueError:
                    gw = None
            out.setdefault(key, {})[gw] = val
    return out, None


def defcon_expectation(d):
    """web_name -> expected DEFCON points per start, from measured hit rate.

    Models trained before 2025/26 have never seen this scoring category, so
    their forecasts are missing up to 2 points per match for defensive players.
    This estimates the gap without touching the model.
    """
    idx = gw_index(d)
    out = {}
    for name, rows in idx.items():
        starts = [r for r in rows if r["mins"] >= 60 and r.get("defcon") is not None]
        if not starts:
            continue
        thr = DEFCON_THRESHOLD.get(starts[0]["pos"])
        if not thr:                       # GK and FWD have no threshold
            out[name] = 0.0
            continue
        hits = sum(1 for r in starts if (r["defcon"] or 0) >= thr)
        out[name] = 2.0 * hits / len(starts)
    return out


def sec_compare(d, horizon, proj_path=None):
    """Score an external projection against the same bar our own model failed."""
    print("=" * 78)
    print("EXTERNAL PROJECTION  (scored against the same bar)")
    print("=" * 78)
    if not proj_path:
        print("\n  Pass one:  python fpl_edge.py --section compare "
              "--projections openfpl.csv\n")
        return
    if not os.path.exists(proj_path):
        print(f"\n  Not found: {proj_path}\n")
        return

    ext, err = load_projections(proj_path)
    if err:
        print(f"\n  Could not read {os.path.basename(proj_path)}: {err}\n")
        return
    print(f"\n  {len(ext)} players loaded from {os.path.basename(proj_path)}")

    idx = gw_index(d)
    events = sorted({r["event"] for r in d.get("player_gw_recent", [])})
    if len(events) < 2:
        print("  Need at least 2 gameweeks of results to score against.\n")
        return
    target = events[-1]

    by_name = {p["web_name"]: p for p in d["all_players"]}
    pairs, unmatched = [], 0
    for name, rows in idx.items():
        te = [r for r in rows if r["event"] == target]
        if not te:
            continue
        actual = sum(r["pts"] for r in te)
        pid = by_name.get(name, {}).get("id")
        vals = ext.get(("id", pid)) if pid is not None else None
        if vals is None:
            vals = ext.get(("name", name))
        if vals is None:
            unmatched += 1
            continue
        pred = vals.get(target, vals.get(None))
        if pred is None:
            pred = next(iter(vals.values()))
        pairs.append((pred, actual, name))

    if len(pairs) < 20:
        print(f"  Only matched {len(pairs)} players ({unmatched} unmatched).")
        print("  Check the CSV uses FPL element ids or matching web_names.\n")
        return

    n = len(pairs)
    mean_actual = sum(a for _, a, _ in pairs) / n
    mae = sum(abs(p - a) for p, a, _ in pairs) / n
    mae_const = sum(abs(mean_actual - a) for _, a, _ in pairs) / n
    rho = _spearman([p for p, _, _ in pairs], [a for _, a, _ in pairs])
    bias = sum(p - a for p, a, _ in pairs) / n

    # DEFCON did not exist before 2025/26. Add it back for models that predate it.
    dc = defcon_expectation(d)
    adj = [(p + dc.get(nm, 0.0), a, nm) for p, a, nm in pairs]
    mae_adj = sum(abs(p - a) for p, a, _ in adj) / n
    rho_adj = _spearman([p for p, _, _ in adj], [a for _, a, _ in adj])
    bias_adj = sum(p - a for p, a, _ in adj) / n
    added = sum(dc.get(nm, 0.0) for _, _, nm in pairs) / n

    print(f"  matched {n}, unmatched {unmatched}, scored on GW{target}\n")
    print(f"    external               MAE {mae:>5.2f}   bias {bias:>+5.2f}")
    print(f"    CONSTANT ({mean_actual:.2f} for all)  MAE {mae_const:>5.2f}")
    print(f"    {'PASS' if mae < mae_const else 'FAIL'}: "
          f"{'beats' if mae < mae_const else 'worse than'} a constant guess by "
          f"{abs(mae_const-mae):.2f}")
    print(f"\n    Spearman rank correlation {rho:>+6.3f}   ({_rho_verdict(rho, n)})")

    print(f"\n  DEFCON-CORRECTED  (adds 2 x measured hit rate; +{added:.2f} "
          f"pts/player on average)")
    print(f"    corrected              MAE {mae_adj:>5.2f}   bias {bias_adj:>+5.2f}")
    print(f"    Spearman rank correlation {rho_adj:>+6.3f}   "
          f"({_rho_verdict(rho_adj, n)})")
    better = "helps" if mae_adj < mae else "hurts"
    print(f"    the correction {better}: MAE {mae-mae_adj:>+.2f}, "
          f"rho {rho_adj-rho:>+.3f}")
    print("    Apply this to any model trained before 2025/26 - the scoring")
    print("    category did not exist when it was fitted.")

    print("\n  Our own model ranks at about +0.15 (GW3, re-measured 2026-09-11):")
    print("  real but below the +0.20 bar. Anything clearing +0.20 over three")
    print("  graded weeks is a real improvement and may drive the wildcard.")
    print("  Below that, it is no better than what we already discarded.\n")

    pairs.sort(key=lambda x: x[0] - x[1])
    print("  WORST UNDER-CALLS")
    for pr, ac, nm in pairs[:5]:
        print(f"    {nm[:18]:18s} predicted {pr:>6.2f}  actual {ac:>3}")
    print("  WORST OVER-CALLS")
    for pr, ac, nm in pairs[-5:][::-1]:
        print(f"    {nm[:18]:18s} predicted {pr:>6.2f}  actual {ac:>3}")
    print()


GOAL_VALUE = {1: 6, 2: 6, 3: 5, 4: 4}
CS_VALUE = {1: 4, 2: 4, 3: 1, 4: 0}


def cs_rate_by_fdr(d):
    """Measured clean-sheet rate per difficulty bucket, from finished fixtures.
    Falls back to a flat prior when the export has no results yet."""
    played = d.get("fixtures_played") or []
    buckets = defaultdict(list)
    for f in played:
        if f.get("h_goals") is None or f.get("a_goals") is None:
            continue
        buckets[f["h_fdr"]].append(1 if f["a_goals"] == 0 else 0)
        buckets[f["a_fdr"]].append(1 if f["h_goals"] == 0 else 0)
    out = {}
    for fdr in (2, 3, 4, 5):
        v = buckets.get(fdr, [])
        out[fdr] = sum(v) / len(v) if len(v) >= 6 else None
    known = [x for x in out.values() if x is not None]
    default = sum(known) / len(known) if known else 0.28
    return {k: (v if v is not None else default) for k, v in out.items()}, default


def history_rates(d):
    """web_name -> last season's xG and xA per 90, for shrinking components."""
    best = {}
    for h in d.get("player_history", []):
        if h["minutes"] < 900:
            continue
        cur = best.get(h["web_name"])
        if cur is None or h["season"] > cur["season"]:
            best[h["web_name"]] = h
    return {k: ((v.get("xg") or 0) / v["minutes"] * 90,
                (v.get("xa") or 0) / v["minutes"] * 90)
            for k, v in best.items()}


def start_probability(p, gws_played):
    """P(start) for the coming gameweek, scaled by any injury doubt.

    starts_last4 counts a four-gameweek window, so the denominator must too:
    uncapped, a nailed starter reads 0.4 by GW10. `is None` rather than `or`,
    because a genuine zero is information - a player who has stopped starting
    must not fall back to his season starts and read as half-nailed.

    One implementation: project_xg() and the `minutes` baseline both call this,
    so the baseline cannot drift from the model's own notion of starting.
    """
    starts = p.get("starts_last4")
    if starts is None:
        starts, window = p.get("starts") or 0, gws_played
    else:
        window = min(4, gws_played)
    p_start = min(1.0, (starts or 0) / max(1, window))
    chance = p.get("chance_next_round")
    if chance is not None:
        p_start *= float(chance) / 100.0
    return p_start


def project_xg(p, fdr, gws_played, cs_table, cs_default, hist, ict_pct=0.5):
    """Bottom-up expected points. Every term is a scoring rule, not a fitted
    weight, so it can be read and argued with line by line."""
    pos = p["pos"]
    if p.get("mins_last4", 0) < 45:          # recent-activity gate
        return 0.0
    # xG and xA are SEASON totals, so the rate must use season minutes.
    # Before GW5 these are identical; after it they diverge badly.
    mins = p.get("minutes") or p.get("mins_last4", 0)

    p_start = start_probability(p, gws_played)
    if p_start <= 0:
        return 0.0
    exp_mins = 90.0 * p_start

    # attacking: this season's rate shrunk toward last season's, weight decaying
    xg90 = (p.get("xg") or 0) / mins * 90
    xa90 = (p.get("xa") or 0) / mins * 90
    prior_w = max(2.0, 8.0 - gws_played)
    hx, ha = hist.get(p["web_name"], (None, None))
    matches = mins / 90.0
    if hx is not None:
        xg90 = (xg90 * matches + hx * prior_w) / (matches + prior_w)
        xa90 = (xa90 * matches + ha * prior_w) / (matches + prior_w)

    goals = xg90 * (exp_mins / 90.0) * GOAL_VALUE.get(pos, 5)
    assists = xa90 * (exp_mins / 90.0) * 3.0

    p_cs = cs_table.get(fdr, cs_default)
    clean = p_cs * CS_VALUE.get(pos, 0) * p_start

    appearance = 2.0 * p_start
    defcon = p.get("_defcon_pts", 0.0) * p_start
    bonus = 0.8 * ict_pct * p_start          # top ICT ~0.8 bonus/gw, bottom ~0

    return appearance + goals + assists + clean + defcon + bonus


LOG_PATH = "projection_log.csv"
LOG_FIELDS = ["made_at", "source", "event", "player_id", "web_name", "predicted"]


def next_deadline(d, event):
    """UTC deadline for a gameweek: 90 minutes before its first kickoff.
    None if the export has no fixtures for it."""
    from datetime import datetime, timedelta, timezone
    kos = [f["kickoff_time"] for f in d.get("fixtures_next6", [])
           if f["event"] == event and f.get("kickoff_time")]
    if not kos:
        return None
    first = min(kos)
    try:
        dt = datetime.fromisoformat(first.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt - timedelta(minutes=90)


def read_log(path=None):
    import csv
    path = path or LOG_PATH
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh)]


WRITE_RETRIES = 3           # after the first attempt
WRITE_WAIT = 5.0            # seconds between attempts
_sleep = time.sleep         # tests replace this so they do not really wait


def _replace_with_retry(src, dst, retries=WRITE_RETRIES, wait=WRITE_WAIT):
    """os.replace(src, dst), retried while dst is locked. Raises after the last
    attempt; the caller decides what a failure means."""
    for attempt in range(retries + 1):
        try:
            os.replace(src, dst)
            return attempt
        except OSError as e:
            if attempt == retries:
                raise
            print(f"  {os.path.basename(dst)} is locked ({e.strerror or e}) - "
                  f"retry {attempt + 1}/{retries} in {wait:.0f}s")
            _sleep(wait)


def recover_stranded_log(path, retries=WRITE_RETRIES, wait=WRITE_WAIT):
    """Promote <path>.tmp into place when it is newer than the log.

    A pre-deadline write that failed (log locked) leaves that week's frozen
    forecasts in the .tmp - the only copy. The next run is after the deadline
    and records nothing for that week, so unless the .tmp goes first, a later
    successful write builds on the stale log and overwrites it.

    Returns (state, n_rows): "none" (no .tmp), "recovered", "stale" (.tmp older
    than the log - left alone), "refused" (unreadable or incomplete - moved
    aside as <tmp>.refused-<stamp>, never promoted, never deleted), or
    "locked" (could not be promoted - left alone; the caller must not write).
    """
    tmp = path + ".tmp"
    name = os.path.basename(tmp)
    if not os.path.exists(tmp):
        return "none", 0
    if os.path.exists(path) and os.path.getmtime(tmp) <= os.path.getmtime(path):
        print(f"  ignoring {name}: older than the log")
        return "stale", 0
    try:
        rows = read_log(tmp)
        bad = [r for r in rows if set(r) != set(LOG_FIELDS)
               or any(v in (None, "") for v in r.values())]
    except (OSError, csv.Error, UnicodeDecodeError) as e:
        rows, bad = [], [str(e)]
    groups = lambda rs: {(r["source"], r["event"]) for r in rs}
    missing = (groups(read_log(path)) if os.path.exists(path) else set()) - groups(rows)
    if bad or missing:
        why = ("unreadable or truncated rows" if bad
               else f"it lacks {sorted(missing)}, which the log has")
        from datetime import datetime, timezone
        aside = f"{tmp}.refused-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}"
        os.replace(tmp, aside)
        print(f"  refusing to promote {name}: {why}; kept as {os.path.basename(aside)}")
        return "refused", len(rows)
    try:
        _replace_with_retry(tmp, path, retries, wait)
    except OSError as e:
        print(f"  could not promote {name} ({e.strerror or e})")
        return "locked", len(rows)
    print(f"  RECOVERED {len(rows)} rows from {name}")
    return "recovered", len(rows)


def write_log_atomic(path, rows, retries=WRITE_RETRIES, wait=WRITE_WAIT):
    """Write the whole log to <path>.tmp, then os.replace() it over <path>.

    The log is never opened for writing, so a crash or a lock cannot leave it
    truncated or half-written: it is either the old file or the new one. If the
    target is locked (Excel takes an exclusive lock on an open CSV - 19 Sep,
    four sources lost to it), retry `retries` times, `wait` seconds apart, then
    raise. The .tmp is left in place on failure: it holds that run's forecasts
    with their pre-deadline timestamps.
    """
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return _replace_with_retry(tmp, path, retries, wait)


def record_status(d, horizon, source="own", proj_path=None, path=None):
    """Store this model's forecast for the NEXT gameweek, before it is played.

    Returns (ok, n, reason). ok is False only when a forecast SHOULD have been
    written and was not: the deadline is still open and nothing was produced,
    or the log could not be written. A passed deadline is ok with n = 0 -
    that is the guard working, and it happens after every deadline.

    Point-in-time discipline: refuses to write once the deadline has passed, so
    the log can never contain a forecast made with knowledge of the result.
    Re-running before the deadline replaces the entry with fresher data.
    """
    import csv
    from datetime import datetime, timezone
    path = path or LOG_PATH
    state, held = recover_stranded_log(path)
    if state == "locked":
        # writing now would rebuild the log without those rows and overwrite
        # the .tmp that holds them
        return False, 0, (f"{os.path.basename(path)}.tmp holds {held} unpromoted "
                          f"rows and the log is locked - close it and re-run")
    target = d["gameweek"] + 1
    dl = next_deadline(d, target)
    now = datetime.now(timezone.utc)
    if dl is None:
        print(f"  no fixtures for GW{target} in this export - nothing recorded")
        return True, 0, f"no fixtures for GW{target} in this export"
    if now > dl:
        print(f"  GW{target} deadline passed ({dl:%Y-%m-%d %H:%M} UTC). "
              f"Refusing to record - it would not be a genuine forecast.")
        return True, 0, f"GW{target} deadline passed - nothing to record"

    rows = []
    if proj_path:
        ext, err = load_projections(proj_path)
        if err:
            print(f"  could not read {proj_path}: {err}")
            return False, 0, f"could not read {proj_path}: {err}"
        by_id = {p["id"]: p for p in d["all_players"]}
        by_nm = {p["web_name"]: p for p in d["all_players"]}
        for key, vals in ext.items():
            p = by_id.get(key[1]) if key[0] == "id" else by_nm.get(key[1])
            if not p:
                continue
            v = vals.get(target, vals.get(None))
            if v is None:
                v = next(iter(vals.values()))
            rows.append((p["id"], p["web_name"], v))
    elif source == "minutes":
        # The bar: P(start) alone, no model. BUILD_SPEC 3.1 - anything that
        # cannot beat this is not earning its complexity. Summed over a double
        # gameweek like every other source, and silent on a blank like them.
        tick, _ = build_ticker(d, horizon)
        for p in d["all_players"]:
            if p["status"] != "a" or p["mins_last4"] < 45:
                continue
            fx = [f for f in tick.get(p["team"], []) if f[0] == target]
            if not fx:
                continue
            proj = start_probability(p, d["gameweek"]) * len(fx)
            if proj > 0:
                rows.append((p["id"], p["web_name"], round(proj, 3)))
    elif source == "bottomup":
        # BUILD_SPEC 2 on the live export. The canonical slice carries the
        # export's rows - the whole season since 2026-09-24 (the last six
        # gameweeks before that) - so weights and rates use every gameweek.
        tick, _ = build_ticker(d, horizon)
        inp = reliability_inputs(canonical_from_export(d), gws_played=d["gameweek"])
        for p in d["all_players"]:
            if p["status"] != "a" or p["mins_last4"] < 45:
                continue
            fx = [(f[1].split()[0], f[1].endswith("(H)"))
                  for f in tick.get(p["team"], []) if f[0] == target]
            proj = project_reliability(p["id"], inp, fx)   # None on a blank
            if proj:
                rows.append((p["id"], p["web_name"], round(proj, 3)))
    elif source == "xg":
        tick, _ = build_ticker(d, horizon)
        cs_table, cs_default = cs_rate_by_fdr(d)
        hist = history_rates(d)
        dc = defcon_expectation(d)
        icts = sorted(p.get("influence", 0) + p.get("creativity", 0)
                      + p.get("threat", 0) for p in d["all_players"])
        for p in d["all_players"]:
            if p["status"] != "a" or p["mins_last4"] < 45:
                continue
            fx = [f for f in tick.get(p["team"], []) if f[0] == target]
            if not fx:
                continue                  # blank gameweek: no fixture, no forecast
            ict = (p.get("influence", 0) + p.get("creativity", 0)
                   + p.get("threat", 0))
            pct = (sum(1 for x in icts if x < ict) / len(icts)) if icts else 0.5
            q = dict(p, _defcon_pts=dc.get(p["web_name"], 0.0))
            # double gameweek: two matches, so two lots of everything
            proj = sum(project_xg(q, f[2], d["gameweek"], cs_table, cs_default,
                                  hist, pct) for f in fx)
            if proj > 0:
                rows.append((p["id"], p["web_name"], round(proj, 3)))
    else:
        tick, _ = build_ticker(d, horizon)
        priors = positional_priors(d["all_players"])
        personal = personal_priors(d)
        for p in d["all_players"]:
            if p["status"] != "a" or p["mins_last4"] < 45:
                continue
            fx = [f for f in tick.get(p["team"], []) if f[0] == target]
            if not fx:
                continue                  # blank gameweek: no fixture, no forecast
            # double gameweek: two matches, so two forecasts - as the xg branch
            proj = sum(project(p, {p["team"]: [f]}, horizon, d["gameweek"],
                               priors, personal)[0] for f in fx)
            if proj > 0:
                rows.append((p["id"], p["web_name"], round(proj, 3)))

    if not rows:
        print("  nothing to record")
        return False, 0, (f"no forecasts produced for GW{target} although its "
                          f"deadline has not passed")

    existing = read_log(path)
    keep = [r for r in existing
            if not (r["source"] == source and int(r["event"]) == target)]
    stamp = now.isoformat(timespec="seconds")
    for pid, nm, val in rows:
        keep.append({"made_at": stamp, "source": source, "event": str(target),
                     "player_id": str(pid), "web_name": nm,
                     "predicted": str(val)})
    try:
        write_log_atomic(path, keep)
    except OSError as e:
        name = os.path.basename(path)
        return False, 0, (f"{name} still locked after {WRITE_RETRIES + 1} attempts "
                          f"({e.strerror or e}) - close it; this run's forecasts "
                          f"are kept in {name}.tmp")
    print(f"  recorded {len(rows)} forecasts for GW{target} as '{source}' "
          f"({dl - now} before deadline)")
    return True, len(rows), ""


def record_projections(d, horizon, source="own", proj_path=None, path=None):
    """record_status() for callers that only want the row count."""
    return record_status(d, horizon, source, proj_path, path)[1]


STARTER_MINUTES = 60


def gameweek_settled(d, event):
    """(ok, blockers). A gameweek may be graded only when its points are final:
    the event has data_checked = 1 AND every one of its fixtures has
    finished = 1. `data_checked` is the API's "points and bonus are final"
    flag and exists on events only; a fixture carries `finished`, which flips
    earlier (observed GW5: fixtures 10/10 finished while the event was still
    data_checked = 0). Grading before both hold records provisional points.
    """
    if "events" not in d or "fixtures_status" not in d:
        return False, ["export has no events / fixtures_status section - "
                       "re-run fpl_sync.py to write one"]
    blockers = []
    ev = next((e for e in d["events"] if e["event"] == event), None)
    if ev is None:
        blockers.append(f"GW{event} is not in the export's events section")
    elif not ev.get("data_checked"):
        blockers.append(f"event data_checked = 0 (points and bonus not final; "
                        f"event finished = {int(bool(ev.get('finished')))})")
    fixtures = [f for f in d["fixtures_status"] if f["event"] == event]
    if not fixtures:
        blockers.append(f"no fixtures listed for GW{event}")
    for f in fixtures:
        if not f.get("finished"):
            blockers.append(f"{f['home']} v {f['away']} ({f.get('kickoff_time')}) "
                            f"finished = 0")
    return not blockers, blockers


def grade_forecasts(d, log, detail=False):
    """Pair every logged forecast with what the player actually scored.

    Returns ({(source, event): [(predicted, actual), ...]},
             {(source, event): count still pending}).
    A player whose team played but who has no row got no minutes and is graded
    against 0. Only a blank or postponed fixture goes ungraded. With
    `detail`, each pair gains a third item: did he play STARTER_MINUTES or more.
    """
    key = _player_key(d)
    actual = defaultdict(dict)
    minutes = defaultdict(dict)
    for r in d.get("player_gw_recent", []):
        k = key(r)
        actual[r["event"]][k] = actual[r["event"]].get(k, 0) + r["pts"]
        minutes[r["event"]][k] = minutes[r["event"]].get(k, 0) + (r.get("mins") or 0)
    fx = fixtures_by_team_event(d)
    team_of = {key(p): p["team"] for p in d.get("all_players", [])}

    graded = defaultdict(list)
    pending = defaultdict(int)
    for r in log:
        ev = int(r["event"])
        if ev not in actual:
            pending[(r["source"], ev)] += 1
            continue
        k = key(r)
        a = actual[ev].get(k)
        if a is None:
            if (team_of.get(k), ev) not in fx:
                continue                  # blank or postponed: nothing to grade
            a = 0                         # team played, he did not: scored 0
        row = (float(r["predicted"]), a)
        if detail:
            row += (minutes[ev].get(k, 0) >= STARTER_MINUTES,)
        graded[(r["source"], ev)].append(row)
    return graded, pending


def sec_calibration(d, horizon, path=None):
    """Rolling accuracy across every gameweek we forecast in advance."""
    print("=" * 78)
    print("CALIBRATION  (accumulated forecast record)")
    print("=" * 78)
    log = read_log(path)
    if not log:
        print("\n  No forecasts recorded yet. Run before each deadline:")
        print("    python fpl_edge.py --record\n")
        return

    graded, pending = grade_forecasts(d, log, detail=True)

    print("""
  DEFINITIONS
    n        forecasts graded for that source and gameweek. Population = every
             logged forecast whose team played; counts are per source below.
    rho      Spearman rank correlation, tie-corrected (tied values share their
             average rank). whole = everyone graded; starters = players with
             %d+ minutes that gameweek (n_st of them).
    MAE      mean |predicted - actual|. const = MAE of predicting the mean
             actual for everyone: the bar. bias = mean(predicted - actual).
    blanks   logged player, team played, no row -> graded as 0 points.
             Team had no finished fixture -> excluded, not graded.
    settled  a gameweek is graded only when its event has data_checked = 1
             and every one of its fixtures has finished = 1.""" % STARTER_MINUTES)

    refused = {}
    for ev in sorted({e for _, e in graded}):
        ok, blockers = gameweek_settled(d, ev)
        if not ok:
            refused[ev] = blockers
    for ev, blockers in refused.items():
        print(f"\n  REFUSED GW{ev} - not settled; grading it now would record "
              f"provisional points:")
        for b in blockers:
            print(f"    - {b}")
    graded = {k: v for k, v in graded.items() if k[1] not in refused}

    if not graded:
        weeks = sorted({e for _, e in pending})
        if weeks:
            print(f"\n  {len(log)} forecasts recorded for GW{weeks} - "
                  f"not played yet.")
        print()
        return

    print(f"\n  {'source':10s}{'GW':>4}{'n':>6}{'MAE':>7}{'const':>7}"
          f"{'rho':>8}{'starters':>10}{'n_st':>6}{'bias':>7}   verdict")
    by_source = defaultdict(list)
    for (src, ev), rows in sorted(graded.items()):
        pairs = [(p, a) for p, a, _ in rows]
        st = [(p, a) for p, a, f in rows if f]
        n = len(pairs)
        mean = sum(a for _, a in pairs) / n
        mae = sum(abs(p - a) for p, a in pairs) / n
        const = sum(abs(mean - a) for _, a in pairs) / n
        rho = _spearman([p for p, _ in pairs], [a for _, a in pairs])
        rho_st = _spearman([p for p, _ in st], [a for _, a in st])
        bias = sum(p - a for p, a in pairs) / n
        by_source[src].extend(pairs)
        if src == "minutes":
            print(f"  {src[:10]:10s}{ev:>4}{n:>6}{'-':>7}{'-':>7}"
                  f"{rho:>8.3f}{rho_st:>10.3f}{len(st):>6}{'-':>7}   rho only")
        else:
            print(f"  {src[:10]:10s}{ev:>4}{n:>6}{mae:>7.2f}{const:>7.2f}"
                  f"{rho:>8.3f}{rho_st:>10.3f}{len(st):>6}{bias:>+7.2f}   "
                  f"{'beats const' if mae < const else 'loses'}")
    if any(src == "minutes" for src, _ in graded):
        print("  minutes is a start probability, not a points forecast: its MAE, const "
              "and bias are undefined, so only rho is shown.")

    print()
    for src, pairs in sorted(by_source.items()):
        n = len(pairs)
        weeks = len({e for s, e in graded if s == src})
        mean = sum(a for _, a in pairs) / n
        mae = sum(abs(p - a) for p, a in pairs) / n
        const = sum(abs(mean - a) for _, a in pairs) / n
        rho = _spearman([p for p, _ in pairs], [a for _, a in pairs])
        se = (1.0 / (n - 1)) ** 0.5 if n > 2 else 1.0
        print(f"  {src.upper()} over {weeks} gameweek(s), {n} forecasts")
        if src == "minutes":
            print(f"    rho {rho:+.3f} +-{1.96*se:.3f}   (start probability: rho only)")
        else:
            print(f"    MAE {mae:.3f} vs constant {const:.3f}   "
                  f"rho {rho:+.3f} +-{1.96*se:.3f}")
        verdict = ("real signal" if rho - 1.96 * se > 0.10
                   else "still indistinguishable from noise")
        print(f"    {verdict}")
        if weeks < 3:
            print(f"    {3-weeks} more gameweek(s) before this is worth acting on.")
        print()

    for (src, ev), cnt in sorted(pending.items()):
        print(f"  {cnt} forecasts pending for {src} GW{ev}")
    if pending:
        print()


# ---------------------------------------------------------------------------
# bench boost screen - the frozen three-layer rule applied to one 15
# ---------------------------------------------------------------------------

FLAG_SHARE_MAX = 0.667      # the frozen P1 flag (CHANGELOG 2026-09-11 22:04); inclusive
SQUAD_IDS = None            # --squad 1,2,3,...   None = my current 15
FULL_QUOTA = {1: 2, 2: 5, 3: 5, 4: 3}


def three_layer_terms(pos):
    """The frozen wildcard rule (CHANGELOG 2026-09-14 16:10): bottomup for GK
    and DEF; bare xGI for MID and FWD. "Bare xGI" is project_reliability with
    the xGI term only - P(start) plus xGI-per-90 x P(start), in points - so the
    fifteen sum in one unit. No fixture term reaches a MID or FWD."""
    return ALL_TERMS if pos in (1, 2) else frozenset({"xgi"})


def week_fixtures(d):
    """team -> event -> [(opponent, was_home, fdr)] for the upcoming gameweeks."""
    fx = defaultdict(lambda: defaultdict(list))
    for f in d.get("fixtures_next6") or []:
        fx[f["home"]][f["event"]].append((f["away"], True, f["h_fdr"]))
        fx[f["away"]][f["event"]].append((f["home"], False, f["a_fdr"]))
    return fx


def project_week(pid, p, inp, fx, week, terms=None):
    """One player, one gameweek. None on a blank - no fixture, no forecast. A
    double is two fixtures in the list and project_reliability sums them.
    `terms` defaults to the frozen three-layer terms for the position."""
    f = fx[p["team"]].get(week, [])
    if not f:
        return None
    pairs = [(opp, home) for opp, home, _ in f]
    return project_reliability(pid, inp, pairs,
                               three_layer_terms(p["pos"]) if terms is None else terms)


def minutes_share(p, played):
    """The frozen P1 predictor: minutes over the last min(4, gws) gameweeks
    over 90 x the fixtures the team played in that window. None if unknown."""
    n = played.get(p["team"], 0)
    return (p.get("mins_last4") or 0) / (90.0 * n) if n else None


def my_squad_ids(d):
    """The 15 in my current squad, as element ids (web_name + team -> id)."""
    me = my_name(d)
    by_key = {}
    for p in d["all_players"]:
        by_key.setdefault((p["web_name"], p["team"]), p["id"])
    rows = sorted((r for r in d["squads"] if r["entry_name"] == me), key=lambda r: r["slot"])
    ids = [by_key.get((r["web_name"], r["team"])) for r in rows]
    return [i for i in ids if i is not None]


def bench_boost_table(d, squad_ids=None, horizon=6):
    """Everything the section prints, as data. Per candidate week: each of the
    fifteen with fixtures, projection (None = blank), P(start), minutes share
    and flag; the fifteen's total; GK/DEF at FDR 4+; the best XI from this 15
    and its points; the best XI the same budget buys around a fodder bench,
    same formation, and its points."""
    gw = d["gameweek"]
    by_id = {p["id"]: p for p in d["all_players"]}
    ids = list(squad_ids) if squad_ids else my_squad_ids(d)
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise ValueError(f"player ids not in the export: {missing}")
    inp = reliability_inputs(canonical_from_export(d), gws_played=gw)
    fx = week_fixtures(d)
    weeks = sorted({f["event"] for f in d.get("fixtures_next6") or []})[:horizon]
    window = range(gw - min(4, gw) + 1, gw + 1)
    played = defaultdict(int)
    for f in d.get("fixtures_played") or []:
        if f["event"] in window:
            played[f["home"]] += 1
            played[f["away"]] += 1
    stand = next((s for s in d["standings"] if s["entry_name"] == my_name(d)), None)
    # the API's value = squad prices at the deadline + bank: it IS the budget
    budget = (stand["value"] / 10.0 if stand
              else sum(by_id[i]["price"] for i in ids))
    available = [p for p in d["all_players"]
                 if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]

    out = {"ids": ids, "budget": budget, "weeks": []}
    for week in weeks:
        rows = []
        for pid in ids:
            p = by_id[pid]
            share = minutes_share(p, played)
            rows.append({
                "id": pid, "name": p["web_name"], "team": p["team"], "pos": p["pos"],
                "price": p["price"], "fixtures": fx[p["team"]].get(week, []),
                "proj": project_week(pid, p, inp, fx, week),
                "p_start": inp["players"][pid]["p_start"] if pid in inp["players"] else 0.0,
                "share": share,
                "flag": share is not None and share <= FLAG_SHARE_MAX,
            })
        total = sum(r["proj"] for r in rows if r["proj"] is not None)
        hard = sum(1 for r in rows if r["pos"] in (1, 2) and r["fixtures"]
                   and max(f[2] for f in r["fixtures"]) >= 4)

        xi = _best_xi([dict(r, proj=r["proj"] or 0.0) for r in rows])
        xi_pts = sum(r["proj"] for r in xi)
        formation = {k: sum(1 for r in xi if r["pos"] == k) for k in FULL_QUOTA}

        # the same money, spent on the XI only: cheapest legal fillers on the
        # bench, then the best XI of the same shape the remainder buys
        fodder, fodder_cost = [], 0.0
        for pos, need in FULL_QUOTA.items():
            for p in sorted((p for p in d["all_players"] if p["pos"] == pos
                             and p["status"] == "a"),
                            key=lambda p: (p["price"], p["id"]))[:need - formation[pos]]:
                fodder.append(p)
                fodder_cost += p["price"]
        taken = {p["id"] for p in fodder}
        market = []
        for p in available:
            if p["id"] in taken:
                continue
            pr = project_week(p["id"], p, inp, fx, week)
            if pr:
                market.append({"id": p["id"], "web_name": p["web_name"], "team": p["team"],
                               "pos": p["pos"], "price": p["price"], "proj": pr,
                               "vpm": pr / p["price"]})
        alt = _build_squad(market, budget - fodder_cost, quota=formation) if xi else None
        out["weeks"].append({
            "event": week, "rows": rows, "total": total, "gk_def_fdr4": hard,
            "xi": xi, "xi_pts": xi_pts, "formation": formation,
            "fodder": fodder, "fodder_cost": fodder_cost,
            "alt_xi": alt, "alt_pts": sum(r["proj"] for r in alt) if alt else None,
        })
    return out


def sec_bench_boost(d, horizon, squad_ids=None):
    t = bench_boost_table(d, squad_ids, horizon)
    print("=" * 78)
    print(f"BENCH BOOST SCREEN  (frozen three-layer rule, next {len(t['weeks'])} gameweeks)")
    print("=" * 78)
    print(f"  squad: {len(t['ids'])} players ({'--squad' if squad_ids else 'my current 15'})"
          f"   budget £{t['budget']:.1f}m = team value (bank included)")
    print("  proj  GK/DEF: bottomup (P(start), xGI, Poisson clean sheet, DEFCON)")
    print("        MID/FWD: P(start) + xGI-per-90 x P(start), in points - bare xGI, no")
    print(f"        fixture term.  FLAG: minutes share <= {FLAG_SHARE_MAX} over the last four")
    print("        gameweeks, the frozen P1 predictor.  BLANK: no fixture, no forecast.")
    for w in t["weeks"]:
        print(f"\n  GW{w['event']}")
        print(f"    {'pos':4s}{'player':15s}{'team':5s}{'fixture':15s}{'P(st)':>6}{'share':>7}{'proj':>7}")
        for r in w["rows"]:
            fixt = " + ".join(f"{o} ({'H' if h else 'A'}) {fdr}" for o, h, fdr in r["fixtures"]) or "BLANK"
            proj = f"{r['proj']:>7.2f}" if r["proj"] is not None else f"{'-':>7}"
            share = f"{r['share']:>7.2f}" if r["share"] is not None else f"{'-':>7}"
            print(f"    {POS[r['pos']]:4s}{r['name'][:14]:15s}{r['team']:5s}{fixt[:14]:15s}"
                  f"{r['p_start']:>6.2f}{share}{proj}{'  FLAG' if r['flag'] else ''}")
        blanks = sum(1 for r in w["rows"] if r["proj"] is None)
        print(f"    all 15 projected: {w['total']:.1f} pts   GK/DEF at FDR 4+: {w['gk_def_fdr4']}"
              f"   blanks: {blanks}   flagged: {sum(1 for r in w['rows'] if r['flag'])}")
        form = "-".join(str(w["formation"][k]) for k in (2, 3, 4))
        print(f"    XI from this 15 ({form}):                             {w['xi_pts']:6.1f} pts")
        if w["alt_pts"] is None:
            print(f"    best XI, same budget, fodder bench ({form}): could not be filled inside the budget")
        else:
            print(f"    best XI, same budget, fodder bench ({form}, fodder £{w['fodder_cost']:.1f}m): "
                  f"{w['alt_pts']:6.1f} pts")
    print()


SECTIONS = {
    "league": lambda d, h: sec_league(d),
    "eo": lambda d, h: sec_eo(d),
    "squad": sec_squad,
    "ticker": sec_ticker,
    "defcon": lambda d, h: sec_defcon(d),
    "value": sec_value,
    "bench": lambda d, h: sec_bench(d),
    "brief": sec_brief,
    "wildcard": lambda d, h: sec_wildcard(d, h, WC_FORMATION, WC_SPLIT),
    "backtest": sec_backtest,
    "fdr": sec_fdr,
    "sensitivity": sec_sensitivity,
    "arbitrage": sec_arbitrage,
    "consistency": sec_consistency,
    "compare": lambda d, h: sec_compare(d, h, PROJECTIONS_PATH),
    "calibration": lambda d, h: sec_calibration(d, h),
    "bench_boost": lambda d, h: sec_bench_boost(d, h, SQUAD_IDS),
}

PROJECTIONS_PATH = None


def force_utf8():
    """Windows consoles default to cp1252 and choke on names like Muharemovic.
    Re-encode our own streams as UTF-8, replacing anything that still fails."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for st in self.streams:
            try:
                st.write(data)
            except UnicodeEncodeError:
                enc = getattr(st, "encoding", None) or "ascii"
                st.write(data.encode(enc, "replace").decode(enc, "replace"))

    def flush(self):
        for st in self.streams:
            try:
                st.flush()
            except Exception:
                pass


def main():
    force_utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("export", nargs="?", default=None,
                    help="fpl_export_gwN.json (default: newest in this folder)")
    ap.add_argument("--out", help="also write the report to this file")
    ap.add_argument("--record", action="store_true",
                    help="store this model's forecast for the next gameweek "
                         "(refuses once the deadline has passed)")
    ap.add_argument("--source", default="own",
                    help="label for --record, e.g. openfpl")
    ap.add_argument("--status",
                    help="with --record: append the RECORD OK/FAIL line to this file")
    ap.add_argument("--squad",
                    help="comma-separated player ids for --section bench_boost "
                         "(default: my current 15)")
    ap.add_argument("--projections",
                    help="external projections CSV to score (use with "
                         "--section compare)")
    ap.add_argument("--brief", action="store_true",
                    help="short pre-deadline summary only")
    ap.add_argument("--diff", nargs="?", const="auto", default=None,
                    help="compare against an older export (default: previous GW)")
    ap.add_argument("--formation", default="4-3-3",
                    help="XI shape for --section wildcard, DEF-MID-FWD (default 4-3-3; "
                         "a parameter, never chosen on the projections)")
    ap.add_argument("--split",
                    help="money per position for --section wildcard, GK,DEF,MID,FWD, "
                         "scaled to the budget (default: the current squad's shape)")
    ap.add_argument("--horizon", type=int, default=6, help="fixtures to look ahead")
    ap.add_argument("--section", default="all",
                    help="comma list: " + ",".join(SECTIONS))
    args = ap.parse_args()

    global PROJECTIONS_PATH, SQUAD_IDS, WC_FORMATION, WC_SPLIT
    PROJECTIONS_PATH = args.projections
    SQUAD_IDS = [int(x) for x in args.squad.split(",")] if args.squad else None
    try:
        parse_formation(args.formation)
        if args.split:
            parse_split(args.split)
    except ValueError as e:
        sys.exit(str(e))
    WC_FORMATION, WC_SPLIT = args.formation, args.split

    path = args.export or newest_export()
    if not path:
        sys.exit("No fpl_export_gw*.json found here. Run fpl_sync.py first, "
                 "or pass the filename: python fpl_edge.py fpl_export_gw3.json")
    if not os.path.exists(path):
        sys.exit(f"Not found: {path}")
    print(f"[reading {os.path.basename(path)}]\n")

    d = load(path)
    if args.record:
        try:
            ok, n, reason = record_status(d, args.horizon, args.source,
                                          args.projections)
        except Exception as e:                                  # noqa: BLE001
            import traceback
            traceback.print_exc()
            ok, n, reason = False, 0, f"{type(e).__name__}: {e}"
        line = (f"RECORD OK {args.source} {n}" + (f" ({reason})" if reason else "")
                if ok else f"RECORD FAIL {args.source} {reason}")
        print(line)
        if args.status:
            with open(args.status, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        if not ok:
            sys.exit(1)
        if args.section == "all":
            return
    if args.brief:
        args.section = "brief"
    if args.section == "all":
        want = [w for w in SECTIONS
                if w not in ("brief", "wildcard", "backtest", "compare",
                             "calibration", "bench_boost")]
    else:
        want = args.section.split(",")

    prev = None
    if args.diff:
        ppath = previous_export(path) if args.diff == "auto" else args.diff
        if not ppath or not os.path.exists(ppath):
            print("[no earlier export found to diff against - skipping]\n")
        else:
            prev = load(ppath)
            print(f"[diffing against {os.path.basename(ppath)}]\n")

    sink = open(args.out, "w", encoding="utf-8") if args.out else None
    real = sys.stdout
    try:
        if sink:
            sys.stdout = _Tee(real, sink)
        if prev:
            sec_diff(d, prev, args.horizon)
        for s in want:
            if s not in SECTIONS:
                continue
            SECTIONS[s](d, args.horizon)
    finally:
        sys.stdout = real
        if sink:
            sink.close()
            print(f"[written to {args.out}]")


if __name__ == "__main__":
    main()
