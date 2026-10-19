"""
tools/league.py - league variance, relative xP and the captain table
(BUILD_PLAN.md Step 9, item S9, offline part). Standard library only; the
nightly never imports it (the LEAGUE ODDS section is lane A's W2).

    python tools/league.py                 # -> tools/out/league_<date>.txt (descriptive, information only)

Definitions, as pre-registered in prereg/S9.md:
  points      a manager's gameweek points net of hits, settled gameweeks only (lockdown rule),
              read from the totals chain (RULING S9 decisions, point 2): net_g = final_total_g -
              final_total_{g-1}, final_total_g = the next row's total_points - its net points
              (a row's own total and points are fetched together, so the pair is consistent even
              when provisional). The stored entry_gw.points - transfers_cost is compared with it:
              a difference is printed as "provisional" (a WARN once lane A's S2b lands); a row
              without a later row cannot be corrected and is excluded and counted.
  sigma_i     sample SD of i's net points; d_j = ours - j's; sigma_d,j = SD of d_j; rho_ij Pearson
  sigma_d     pooled = root mean square of sigma_d,j over every rival (primary); per pair as information;
              without chip weeks (either side's active_chip set) as information
  P(above j)  Phi(-gap_j / (sigma_d sqrt(n))), gap_j = j's total - ours, n = 38 - last settled gameweek,
              zero drift (primary); the drift version over the next six gameweeks as information
  line        "beyond the line" when gap_j > sigma_d sqrt(n), else "inside"
  threat set  rivals ahead of us; if we lead, rivals with P(j above us) >= 0.05; weights
              w_j = P(j above us), normalised
  EO          league effective ownership per player = sum of w_j x multiplier_j from each rival's
              last settled picks (starter 1, captain 2, triple captain 3, bench 0, bench 1 under
              Bench Boost); the coming gameweek's picks are hidden until its deadline - said so
  relative xP (our multiplier - EO) x xP, xP = the recorded own row for the next gameweek;
              "free variance" when two options' xP differ by less than 0.3
  captain     every player of our XI ranked by own xP, any position; the differential allowance
              <= 0.5 xP before GW25, <= 1.0 from GW25, against the threat-set EO; a running count
              of how often a DEF or GK topped the table on settled gameweeks
  intervals   bootstrap over gameweeks, B = 10,000, 90%, seed 20261018, for every sigma and every P
  flags       "allowed differential" = cost <= the allowance AND a lower threat-set EO than the top
              (Part C rule 3); "free variance" = cost < 0.3 AND a lower EO (the ruling's reading)
"""

import argparse
import math
import os
import random
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

MY_ENTRY = BT.MY_ENTRY
LAST_GW = 38
SEED = BT.SEED
B = BT.B
THREAT_MIN_P = 0.05
FREE_VARIANCE = 0.3
ALLOWANCE_EARLY, ALLOWANCE_LATE, ALLOWANCE_SWITCH = 0.5, 1.0, 25
DRIFT_WEEKS = 6
CHIP_MULT = {"3xc": 3}


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------

def phi(x):
    """The standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def sd(values):
    return BT.sd(values)


def pearson(a, b):
    n = len(a)
    if n < 2:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else 0.0


def line_label(gap, line):
    """The variance line: "beyond the line" when the gap exceeds sigma_d
    sqrt(n), else "inside" (a gap exactly on the line is inside)."""
    return "beyond the line" if gap > line else "inside"


def pooled_sigma_d(diffs_by_rival):
    """Root mean square of sigma_d,j over the rivals (each from its own
    gameweek list); None when no pair has two gameweeks."""
    sds = [sd(v) for v in diffs_by_rival.values() if len(v) >= 2]
    return math.sqrt(sum(s * s for s in sds) / len(sds)) if sds else None


def bootstrap_stat(values_by_gw, stat, b=B, seed=SEED, ci=0.90):
    """Percentile bootstrap over gameweeks of a statistic of a per-gameweek
    table: values_by_gw = {gw: row}; stat(rows) -> float or None."""
    gws = sorted(values_by_gw)
    n = len(gws)
    if n == 0:
        return None, None
    rng = random.Random(seed)
    out = []
    for _ in range(b):
        sample = [values_by_gw[g] for g in rng.choices(gws, k=n)]
        v = stat(sample)
        if v is not None:
            out.append(v)
    if not out:
        return None, None
    out.sort()
    tail = (1 - ci) / 2
    return out[int(round(tail * len(out)))], out[max(0, int(round((1 - tail) * len(out))) - 1)]


# ---------------------------------------------------------------------------
# the database, point-in-time
# ---------------------------------------------------------------------------

def load(data_dir):
    db = os.path.join(data_dir, "fpl.sqlite")
    if not os.path.exists(db):
        raise MissingInput(f"{db} is missing")
    settled = BT.load_2627(data_dir)["settled"]
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    entries = {i: (name, player) for i, name, player in c.execute("select id, entry_name, player_name from entries")}
    if MY_ENTRY not in entries:
        raise MissingInput(f"entry {MY_ENTRY} is not in entries")
    stored = defaultdict(dict)             # entry -> event -> {net, total, chip} as fetched (every event)
    for eid, ev, pts, total, cost, chip in c.execute(
            "select entry_id, event, points, total_points, transfers_cost, active_chip from entry_gw"):
        stored[eid][ev] = {"net": (pts or 0) - (cost or 0), "gross": pts or 0, "total": total, "chip": chip}
    gw, provisional, excluded = totals_chain(stored, settled)
    picks = defaultdict(lambda: defaultdict(list))   # entry -> event -> [(pid, position, multiplier, is_captain)]
    for eid, ev, pid, pos, mult, cap in c.execute("select entry_id, event, player_id, position, multiplier, is_captain from picks"):
        if ev in settled:
            picks[eid][ev].append((pid, pos, mult, cap))
    players = {pid: (name, team, pos) for pid, name, team, pos in c.execute(
        "select p.id, p.web_name, t.short_name, p.position from players p join teams t on t.id = p.team_id")}
    deadlines = {ev: dl for ev, dl in c.execute("select id, deadline_time from events")}
    c.close()
    log_rows = E.read_log(os.path.join(data_dir, E.LOG_PATH))
    d_events = {"events": [{"event": ev, "deadline_time": dl} for ev, dl in deadlines.items()]}
    own = defaultdict(dict)
    for r in E.forecasts(log_rows, d_events):
        if r["source"] == "own":
            own[int(r["event"])][int(r["player_id"])] = float(r["predicted"])
    check_multipliers(gw, picks)
    return {"entries": entries, "gw": gw, "picks": picks, "players": players, "own": own,
            "settled": sorted(settled), "deadlines": deadlines, "provisional": provisional, "excluded": excluded}


def totals_chain(stored, settled):
    """Settled gameweek scores from the totals chain. For entry e and
    settled gameweek g: final_total[g] = stored[g+1].total - stored[g+1].net
    (the next row, settled or not); final_total[g-1] likewise from row g
    (0 before GW1); net[g] = final_total[g] - final_total[g-1]. Returns
    (gw, provisional, excluded): gw[e][g] = {net, total, chip}; provisional
    = [(e, g, stored net, chain net)] where they differ; excluded = [(e, g)]
    rows the chain cannot correct (no later row)."""
    gw = defaultdict(dict)
    provisional, excluded = [], []
    for eid, rows in stored.items():
        def final_total(g):
            nxt = rows.get(g + 1)
            if nxt is None or nxt["total"] is None:
                return None
            return nxt["total"] - nxt["net"]
        for ev in sorted(rows):
            if ev not in settled:
                continue
            ft = final_total(ev)
            if ft is None:
                excluded.append((eid, ev))
                continue
            prev = 0 if ev == 1 else (rows[ev]["total"] - rows[ev]["net"] if rows[ev]["total"] is not None else None)
            if prev is None:
                excluded.append((eid, ev))
                continue
            net = ft - prev
            if net != rows[ev]["net"]:
                provisional.append((eid, ev, rows[ev]["net"], net))
            gw[eid][ev] = {"net": net, "gross": net + (rows[ev]["gross"] - rows[ev]["net"]), "total": ft, "chip": rows[ev]["chip"]}
    return gw, provisional, excluded


def expected_multiplier(position, is_captain, chip):
    """The pre-registered multiplier from the pick's slot and the chip."""
    if position > 11:
        return 1 if chip == "bboost" else 0
    if is_captain:
        return CHIP_MULT.get(chip, 2)
    return 1


def check_multipliers(gw, picks):
    """The picks' multiplier field must equal the rule on every settled
    gameweek; a mismatch stops the run."""
    for eid, by_ev in picks.items():
        for ev, rows in by_ev.items():
            chip = gw.get(eid, {}).get(ev, {}).get("chip")
            for pid, pos, mult, cap in rows:
                want = expected_multiplier(pos, cap, chip)
                if mult != want:
                    raise MissingInput(f"entry {eid} GW{ev} player {pid}: multiplier {mult} but the rule says {want} (chip {chip})")


# ---------------------------------------------------------------------------
# the measurements
# ---------------------------------------------------------------------------

def variance_table(data):
    gw, entries = data["gw"], data["entries"]
    ours = gw[MY_ENTRY]
    if not ours:
        raise MissingInput("no settled gameweek for our entry")
    rivals = sorted(e for e in entries if e != MY_ENTRY)
    common = {}
    for j in rivals:
        common[j] = sorted(ev for ev in ours if ev in gw.get(j, {}))
    last = max(ours)
    n_left = LAST_GW - last
    diffs = {j: [ours[ev]["net"] - gw[j][ev]["net"] for ev in common[j]] for j in rivals}
    diffs_nochip = {j: [ours[ev]["net"] - gw[j][ev]["net"] for ev in common[j]
                        if not ours[ev]["chip"] and not gw[j][ev]["chip"]] for j in rivals}
    sigma_d = pooled_sigma_d(diffs)
    if sigma_d is None:
        raise MissingInput("fewer than two settled gameweeks: sigma_d undefined")
    # bootstrap over gameweeks: resample the gameweek list, recompute the pooled statistic
    all_gws = sorted(ours)

    def pooled_of(sample):
        return pooled_sigma_d({j: [ours[ev]["net"] - gw[j][ev]["net"] for ev in sample if ev in gw.get(j, {})] for j in rivals})
    lo, hi = bootstrap_stat({ev: ev for ev in all_gws}, pooled_of)
    sigma_d_nochip = pooled_sigma_d(diffs_nochip)
    rows = []
    for j in rivals:
        pts_j = [gw[j][ev]["net"] for ev in common[j]]
        pts_me = [ours[ev]["net"] for ev in common[j]]
        s_j, s_dj = sd(pts_j), sd(diffs[j])
        lo_j, hi_j = bootstrap_stat({ev: ours[ev]["net"] - gw[j][ev]["net"] for ev in common[j]}, lambda smp: sd(smp))
        lo_sj, hi_sj = bootstrap_stat({ev: gw[j][ev]["net"] for ev in common[j]}, lambda smp: sd(smp))
        gap = gw[j][last]["total"] - ours[last]["total"] if last in gw[j] else None
        p_above = phi(-gap / (sigma_d * math.sqrt(n_left))) if gap is not None and n_left > 0 else (1.0 if gap is not None and gap < 0 else 0.0)
        if gap is not None and n_left > 0:          # the interval of P follows the resampled pooled sigma_d
            lo_p, hi_p = bootstrap_stat({ev: ev for ev in all_gws},
                                        lambda smp, g=gap: (phi(-g / (pooled_of(smp) * math.sqrt(n_left))) if pooled_of(smp) else None))
        else:
            lo_p, hi_p = p_above, p_above
        rows.append({"entry": j, "name": entries[j][0], "n": len(common[j]), "sigma_j": s_j, "sigma_j_ci": (lo_sj, hi_sj),
                     "sigma_dj": s_dj, "sigma_dj_ci": (lo_j, hi_j), "rho": pearson(pts_me, pts_j),
                     "gap": gap, "p_above": p_above, "p_above_ci": (lo_p, hi_p),
                     "line": None if gap is None else line_label(gap, sigma_d * math.sqrt(n_left)),
                     "sigma_dj_nochip": sd(diffs_nochip[j]) if len(diffs_nochip[j]) >= 2 else None})
    sigma_me = sd([ours[ev]["net"] for ev in all_gws])
    lo_me, hi_me = bootstrap_stat({ev: ours[ev]["net"] for ev in all_gws}, lambda smp: sd(smp))

    def pooled_nochip_of(sample):
        return pooled_sigma_d({j: [ours[ev]["net"] - gw[j][ev]["net"] for ev in sample
                                   if ev in gw.get(j, {}) and not ours[ev]["chip"] and not gw[j][ev]["chip"]] for j in rivals})
    lo_nc, hi_nc = bootstrap_stat({ev: ev for ev in all_gws}, pooled_nochip_of) if sigma_d_nochip is not None else (None, None)
    return {"last": last, "n_left": n_left, "sigma_d": sigma_d, "sigma_d_ci": (lo, hi), "sigma_d_nochip": sigma_d_nochip,
            "sigma_d_nochip_ci": (lo_nc, hi_nc), "sigma_me": sigma_me, "sigma_me_ci": (lo_me, hi_me), "rows": rows,
            "our_total": ours[last]["total"]}


def threat_set(var):
    """(threat rivals, weights) per the pre-registered rule."""
    ahead = [r for r in var["rows"] if r["gap"] is not None and r["gap"] > 0]
    if ahead:
        threats = ahead
    else:
        threats = [r for r in var["rows"] if r["gap"] is not None and 1 - r["p_above"] >= THREAT_MIN_P]
    # w_j = P(j finishes above us) = 1 - P(we finish above j), normalised
    raw = {r["entry"]: 1 - r["p_above"] for r in threats}
    tot = sum(raw.values())
    weights = {j: (v / tot if tot else 0.0) for j, v in raw.items()}
    return threats, weights


def last_settled_picks(data, entry):
    by_ev = data["picks"].get(entry, {})
    if not by_ev:
        return None, None
    ev = max(by_ev)
    return ev, by_ev[ev]


def league_eo(data, weights):
    """player -> EO from each threat rival's last settled picks."""
    eo = defaultdict(float)
    used = {}
    for j, w in weights.items():
        ev, rows = last_settled_picks(data, j)
        if rows is None:
            continue
        used[j] = ev
        for pid, pos, mult, cap in rows:
            eo[pid] += w * mult
    return eo, used


def our_xi(data, next_gw):
    """Our best XI by own xP for the next gameweek from our last settled 15
    (any formation), with the multiplier we would hold (captain 2)."""
    ev, rows = last_settled_picks(data, MY_ENTRY)
    if rows is None:
        raise MissingInput("no settled picks for our entry")
    own = data["own"].get(next_gw, {})
    squad = [{"id": pid, "pos": data["players"].get(pid, ("?", "?", 0))[2], "proj": own.get(pid, 0.0)} for pid, _, _, _ in rows]
    xi = E._best_xi(squad)
    cap = max(xi, key=lambda r: (r["proj"], -r["id"])) if xi else None
    mult = {r["id"]: (2 if cap and r["id"] == cap["id"] else 1) for r in xi}
    for pid, _, _, _ in rows:
        mult.setdefault(pid, 0)
    return ev, xi, mult, own


def captain_history(data):
    """(count DEF/GK topped, gameweeks counted): on every settled gameweek
    with our picks and own rows, the top own-xP player of our XI-by-own."""
    top_defgk, counted = 0, 0
    for ev in data["settled"]:
        rows = data["picks"].get(MY_ENTRY, {}).get(ev)
        own = data["own"].get(ev)
        if not rows or not own:
            continue
        squad = [{"id": pid, "pos": data["players"].get(pid, ("?", "?", 0))[2], "proj": own.get(pid, 0.0)} for pid, _, _, _ in rows]
        xi = E._best_xi(squad)
        if len(xi) != 11:
            continue
        top = max(xi, key=lambda r: (r["proj"], -r["id"]))
        counted += 1
        top_defgk += 1 if top["pos"] in (1, 2) else 0
    return top_defgk, counted


def allowance(next_gw):
    return ALLOWANCE_EARLY if next_gw < ALLOWANCE_SWITCH else ALLOWANCE_LATE


def report(data_dir, out=print, today=None):
    data = load(data_dir)
    var = variance_table(data)
    last, n_left = var["last"], var["n_left"]
    today = today or datetime.now(timezone.utc)
    coming = sorted(ev for ev, dl in data["deadlines"].items()
                    if dl and datetime.fromisoformat(dl.replace("Z", "+00:00")) > today)
    next_gw = coming[0] if coming else last + 1          # the coming deadline: xP, EO and the captain table are for it
    out(f"LEAGUE  {today:%Y-%m-%d}: settled through GW{last}, {n_left} gameweeks left; coming deadline GW{next_gw}"
        + (f" (GW{', GW'.join(str(g) for g in range(last + 1, next_gw))} played, not yet settled)" if next_gw > last + 1 else "")
        + f"; points net of hits; B={B}, 90% CI, seed {SEED}; information only")
    lo, hi = var["sigma_d_ci"]
    out("  scores from the totals chain (RULING S9 decisions, point 2): "
        + (f"{len(data['provisional'])} stored rows were provisional" if data["provisional"] else "every stored row equals the chain")
        + (f"; {len(data['excluded'])} rows the chain cannot correct, excluded" if data["excluded"] else ""))
    for eid, ev, stored_net, chain_net in data["provisional"]:
        out(f"    WARN provisional: {data['entries'][eid][0]} GW{ev} stored {stored_net}, chain {chain_net} ({chain_net - stored_net:+d})")
    for eid, ev in data["excluded"]:
        out(f"    excluded: {data['entries'][eid][0]} GW{ev} (no later row to correct it)")
    nc = var["sigma_d_nochip"]
    out(f"  pooled sigma_d = {var['sigma_d']:.2f} [{lo:.2f}, {hi:.2f}] points a gameweek (root mean square over rivals); "
        f"our sigma = {var['sigma_me']:.2f} [{var['sigma_me_ci'][0]:.2f}, {var['sigma_me_ci'][1]:.2f}]; without chip weeks sigma_d = "
        + (f"{nc:.2f} [{var['sigma_d_nochip_ci'][0]:.2f}, {var['sigma_d_nochip_ci'][1]:.2f}]" if nc is not None and var["sigma_d_nochip_ci"][0] is not None else (f"{nc:.2f}" if nc is not None else "n/a")))
    out(f"  variance line = sigma_d x sqrt(n) = {var['sigma_d'] * math.sqrt(n_left):.1f} points")
    out("")
    out(f"  {'rival':<22}{'n':>3}{'sigma_j [90%]':>22}{'sigma_dj [90%]':>22}{'rho':>7}{'gap':>6}{'P(above j) [90%]':>24}  line")
    for r in var["rows"]:
        ci = f"{r['sigma_dj']:.2f} [{r['sigma_dj_ci'][0]:.1f}, {r['sigma_dj_ci'][1]:.1f}]" if r["sigma_dj_ci"][0] is not None else f"{r['sigma_dj']:.2f}"
        cj = f"{r['sigma_j']:.2f} [{r['sigma_j_ci'][0]:.1f}, {r['sigma_j_ci'][1]:.1f}]" if r["sigma_j_ci"][0] is not None else f"{r['sigma_j']:.2f}"
        cp = f"{r['p_above']:.3f} [{r['p_above_ci'][0]:.3f}, {r['p_above_ci'][1]:.3f}]" if r["p_above_ci"][0] is not None else f"{r['p_above']:.3f}"
        out(f"  {r['name']:<22}{r['n']:>3}{cj:>22}{ci:>22}{(r['rho'] if r['rho'] is not None else float('nan')):7.2f}"
            f"{(r['gap'] if r['gap'] is not None else 0):6d}{cp:>24}  {r['line']}")
    threats, weights = threat_set(var)
    out("")
    out("  threat set (" + ("rivals ahead of us" if any(r["gap"] is not None and r["gap"] > 0 for r in var["rows"]) else f"we lead: rivals with P(j above us) >= {THREAT_MIN_P}") + "): "
        + ", ".join(f"{r['name']} w={weights[r['entry']]:.3f}" for r in threats))
    # drift version, information only
    ev_me, xi, mult_me, own = our_xi(data, next_gw)
    xp_me = sum(r["proj"] * mult_me[r["id"]] for r in xi)
    out(f"  drift version (information only): our XI by own for GW{next_gw} from GW{ev_me} picks = {xp_me:.1f} xP")
    for r in var["rows"]:
        ev_j, rows_j = last_settled_picks(data, r["entry"])
        if rows_j is None or r["gap"] is None:
            continue
        xp_j = sum(own.get(pid, 0.0) * mult for pid, pos, mult, cap in rows_j)
        missing_j = sum(1 for pid, pos, mult, cap in rows_j if mult and pid not in own)
        drift = xp_me - xp_j
        p_drift = phi(-(r["gap"] - drift * min(n_left, DRIFT_WEEKS)) / (var["sigma_d"] * math.sqrt(n_left))) if n_left > 0 else r["p_above"]
        out(f"    {r['name']:<22} their XI (GW{ev_j} picks) {xp_j:5.1f} xP"
            + (f" ({missing_j} starters without an own row)" if missing_j else "")
            + f", drift {drift:+5.1f}/GW over {min(n_left, DRIFT_WEEKS)} -> P(above) {p_drift:.3f} (zero drift {r['p_above']:.3f})")
    eo, used = league_eo(data, weights)
    out("")
    out(f"  league EO from the threat set's last settled picks ({', '.join(f'{data['entries'][j][0]} GW{ev}' for j, ev in used.items())}); "
        f"the coming gameweek's picks are hidden until its deadline")
    out(f"  our 15 (GW{ev_me} picks) for GW{next_gw}: relative xP = (our multiplier - EO) x own")
    out(f"  {'player':<16}{'pos':>4}{'own':>6}{'mult':>5}{'EO':>6}{'rel xP':>8}")
    allow = allowance(next_gw)
    for r in sorted(xi, key=lambda r: -r["proj"]):
        name, team, pos = data["players"].get(r["id"], ("?", "?", 0))
        rel = (mult_me[r["id"]] - eo.get(r["id"], 0.0)) * r["proj"]
        note = "" if r["id"] in own else "  no own forecast"
        out(f"  {name:<16}{BT.POS_NAME.get(pos, '?'):>4}{r['proj']:6.2f}{mult_me[r['id']]:5d}{eo.get(r['id'], 0.0):6.2f}{rel:8.2f}{note}")
    # captain table
    out("")
    out(f"  CAPTAIN TABLE GW{next_gw}: our XI by own xP, any position; allowed differential = cost <= {allow:.1f} xP (" +
        ("before" if next_gw < ALLOWANCE_SWITCH else "from") + f" GW{ALLOWANCE_SWITCH}) and a lower threat-set EO than the top; "
        f"free variance = cost < {FREE_VARIANCE} and a lower EO")
    ranked = sorted(xi, key=lambda r: (-r["proj"], r["id"]))
    top = ranked[0]["proj"] if ranked else 0.0
    out(f"  {'rank':>4} {'player':<16}{'pos':>4}{'own':>6}{'EO':>6}{'cost':>6}  flags")
    for i, r in enumerate(ranked, 1):
        name, team, pos = data["players"].get(r["id"], ("?", "?", 0))
        cost = top - r["proj"]
        flags = []
        if i > 1 and cost <= allow and eo.get(r["id"], 0.0) < eo.get(ranked[0]["id"], 0.0):
            flags.append("allowed differential")
        if i > 1 and cost < FREE_VARIANCE and eo.get(r["id"], 0.0) < eo.get(ranked[0]["id"], 0.0):
            flags.append("free variance")
        out(f"  {i:>4} {name:<16}{BT.POS_NAME.get(pos, '?'):>4}{r['proj']:6.2f}{eo.get(r['id'], 0.0):6.2f}{cost:6.2f}  {', '.join(flags)}")
    k, n_hist = captain_history(data)
    out(f"  a DEF or GK topped our XI's own xP in {k} of {n_hist} settled gameweeks with own rows")
    return {"var": var, "threats": threats, "weights": weights, "eo": eo, "xi": xi, "next_gw": next_gw}


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    run = Run("tools/league.py", args.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    today = datetime.now(timezone.utc)
    try:
        report(args.data, out, today)
    except MissingInput as e:
        print(f"MISSING INPUT: {e} - stopping; nothing is substituted")
        return 2
    path = os.path.join(args.out, f"league_{today:%Y-%m-%d}.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    run.wrote(path)
    run.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
