"""tools/gate_v2_check.py - the retrospective check of status gate v2, xp_v2_g2's test (prereg/FM.md; Boris's answer
4 of Thu 12 Nov night: "the retrospective check (GW4-10 from our archived nightly exports) as its test and the bar
as drafted (90% lower bound of the paired |error| difference above 0)"). Offline; standard library only; the
nightly never imports it.

    python tools/gate_v2_check.py --data DIR --hist ROOT --out DIR

method (pinned in prereg/FM.md before this code)
  - origins: the deadlines of GW4-GW10; at each, the newest dated export generated before it, the newest Odds API
    snapshot before it where it prices the fixture, else the fallback fitted on results before it;
    v1 = builder.live_matrix's computation at that origin, v2 = the same under tools/gate_v2's rule;
  - weeks scored: u = g .. g+5, u <= 10, locked down (data_checked 1, every fixture finished), the club playing;
  - population: every flagged player-week - status d, s or i in the origin's export, 45+ minutes in its last four;
  - realised: player_gw.total_points summed over the week (no row: 0, counted);
  - e = |v1 - r| - |v2 - r|; the mean over player-weeks; bootstrap with the origin as the unit (the origins
    resampled with replacement, the pooled mean recomputed), B 10000, seed 20261018, 90%;
  - bar: the 90% lower bound above 0.
"""
import argparse
import os
import random
import sqlite3
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_bt as FB                                               # noqa: E402
import gate_v2 as G                                               # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

ORIGINS = tuple(range(4, 11))
LAST = 10
FLAGGED = ("d", "s", "i")


def cluster_bootstrap(clusters, b=FB.B, seed=FB.SEED, ci=FB.CI):
    """Percentile bootstrap of the pooled mean, the cluster (origin) as the unit: clusters = [(sum, n)]. Returns
    {mean, lo, hi, n_clusters, n}; resamples whose clusters hold no player-week are dropped (and counted)."""
    clusters = [c for c in clusters]
    tot_n = sum(n for _, n in clusters)
    if not tot_n:
        return {"mean": None, "lo": None, "hi": None, "n_clusters": len(clusters), "n": 0, "dropped": 0}
    rng = random.Random(seed)
    means, dropped = [], 0
    for _ in range(b):
        pick = rng.choices(clusters, k=len(clusters))
        n = sum(x[1] for x in pick)
        if not n:
            dropped += 1
            continue
        means.append(sum(x[0] for x in pick) / n)
    means.sort()
    tail = (1 - ci) / 2
    k = len(means)
    return {"mean": sum(s for s, _ in clusters) / tot_n, "lo": means[int(round(tail * k))],
            "hi": means[int(round((1 - tail) * k)) - 1], "n_clusters": len(clusters), "n": tot_n, "dropped": dropped}


def passes(boot):
    """The bar, stated before any number was seen: the 90% lower bound above 0."""
    return boot["lo"] is not None and boot["lo"] > 0


def locked_weeks(db_path):
    c = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    ok = set()
    for ev, chk in c.execute("select id, data_checked from events"):
        n, fin = c.execute("select count(*), coalesce(sum(finished = 1), 0) from fixtures where event = ?", (ev,)).fetchone()
        if chk == 1 and n and n == fin:
            ok.add(ev)
    pts = defaultdict(float)
    for pid, ev, tp in c.execute("select player_id, event, total_points from player_gw"):
        pts[(pid, ev)] += tp or 0
    c.close()
    return ok, pts


def check(data_dir, hist_root, out=print, origins=ORIGINS, last=LAST):
    """Everything the check prints, as data: per origin the flagged player-weeks with v1, v2, r and e."""
    _, deadlines, _, _, _ = OL.sqlite_tables(data_dir)
    exports = OL.dated_exports(data_dir)
    prior = XL.load_prior(hist_root)
    names, _ = XL.prior_names(os.path.join(data_dir, "fpl.sqlite"), os.path.join(hist_root, "2026-27", "elements_positions.csv"),
                              os.path.join(hist_root, XL.PRIOR_SEASON))
    locked, realised = locked_weeks(os.path.join(data_dir, "fpl.sqlite"))
    rows, per_origin = [], []
    name_matched = 0
    for g in origins:
        weeks_n = 6
        try:
            d, path, dl, book, model, snap = G.origin(data_dir, g, exports)
            sus, unknown = G.suspensions([x for x in exports if x[0] < dl], deadlines, d["gameweek"])
            v1, _ = G.matrix(d, g, weeks_n, book, model, prior, names, "v1")
            v2, modes = G.matrix(d, g, weeks_n, book, model, prior, names, "v2", sus)
        except (G.MissingInput, ValueError) as e:              # reported, never substituted: the origin is not scored
            per_origin.append({"origin": g, "missing": f"{type(e).__name__}: {e}", "sum": 0.0, "n": 0})
            continue
        flagged = [p for p in d["all_players"] if p["status"] in FLAGGED and (p.get("mins_last4") or 0) >= 45]
        mine = [r for r in d.get("squads") or [] if r.get("entry_id") == d.get("my_entry")]
        ours = {r["player_id"] for r in mine if r.get("player_id") is not None}
        key = {}                                    # older exports' squad rows carry no player_id: name, club, position
        for p in d["all_players"]:
            key.setdefault((p["web_name"], p["team"], p["pos"]), []).append(p["id"])
        by_name = [key.get((r["web_name"], r["team"], r["pos"]), []) for r in mine if r.get("player_id") is None]
        ours |= {ids[0] for ids in by_name if len(ids) == 1}
        name_matched += sum(1 for ids in by_name if len(ids) == 1)
        # information (Boris, answers on FM of Thu 19 Nov late, point 3): status-a players whose plain last-four window
        # holds a suspended gameweek - the players v2 moves through point 5 alone
        plain = set(range(max(1, d["gameweek"] - 3), d["gameweek"] + 1))
        p5 = [p for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45
              and sus.get(p["id"], set()) & plain]
        s, n, no_row = 0.0, 0, 0
        for i, u in enumerate(range(g, g + weeks_n)):
            if u > last or u not in locked:
                continue
            playing = {t for f in XL.target_fixtures(d, u).values() for t in (f["home"], f["away"])}
            for p in flagged + p5:
                if p["team"] not in playing:
                    continue
                pid = p["id"]
                r = realised.get((pid, u))
                if r is None and p["status"] in FLAGGED:
                    no_row += 1
                r = 0.0 if r is None else r
                a, b = v1[i].get(pid, 0.0), v2[i].get(pid, 0.0)
                e = abs(a - r) - abs(b - r)
                group = "flagged" if p["status"] in FLAGGED else "point5"
                rows.append({"origin": g, "week": u, "id": pid, "name": p["web_name"], "status": p["status"],
                             "mode": modes.get(pid, ["?"] * weeks_n)[i], "v1": a, "v2": b, "r": r, "e": e,
                             "group": group, "ours": pid in ours})
                if group == "flagged":
                    s += e
                    n += 1
        touch = sum(1 for p in flagged if set(G.window_weeks(d["gameweek"], sus.get(p["id"], set()))) & unknown)
        per_origin.append({"origin": g, "export": os.path.basename(path), "snapshot": snap, "sum": s, "n": n,
                           "no_row": no_row, "flagged": len(flagged), "touch": touch, "unknown": sorted(unknown)})
    if per_origin:
        per_origin[-1]["name_matched"] = name_matched
    return rows, per_origin


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--origins", default=f"{ORIGINS[0]}-{ORIGINS[-1]}", help="the origins' gameweeks, e.g. 4-10 (the default)")
    ap.add_argument("--last", type=int, default=LAST, help="the last gameweek scored (default 10)")
    a = ap.parse_args(argv)
    lo_, _, hi_ = a.origins.partition("-")
    origins = tuple(range(int(lo_), int(hi_ or lo_) + 1))
    run_ = Run("tools/gate_v2_check.py", a.out, argv if argv is not None else sys.argv[1:])
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)
    rows, per = check(a.data, a.hist, out, origins=origins, last=a.last)
    out(f"STATUS GATE V2 (xp_v2_g2): THE RETROSPECTIVE CHECK, GW{origins[0]}-{origins[-1]} scored through GW{a.last} "
        "(prereg/FM.md; Boris's answer 4, Thu 12 Nov night)")
    out(f"  code {run_.commit[:7]} (modified tracked files {run_.dirty})")
    out(f"  {'origin':<7}{'export':<36}{'odds':<30}{'flagged':>8}{'n':>5}{'mean e':>9}  point 5: flagged windows touching a GW with no archive")
    for o in per:
        if "missing" in o:
            out(f"  GW{o['origin']:<5}missing input, not scored: {o['missing']}")
            continue
        out(f"  GW{o['origin']:<5}{o['export']:<36}{(o['snapshot'] or 'fallback'):<30}{o['flagged']:>8}{o['n']:>5}"
            f"{(o['sum'] / o['n'] if o['n'] else float('nan')):>9.3f}  {o['touch']} of {o['flagged']}"
            + (f" (GW{', GW'.join(map(str, o['unknown']))} taken as unsuspended)" if o['touch'] else ""))
    scored = [o for o in per if "missing" not in o]
    boot = cluster_bootstrap([(o["sum"], o["n"]) for o in scored])
    out("")
    if not boot["n"]:
        out(f"  PRIMARY: e = |v1 - r| - |v2 - r| over 0 flagged player-weeks in {boot['n_clusters']} origins: no result")
    else:
        out(f"  PRIMARY: e = |v1 - r| - |v2 - r| over {boot['n']} flagged player-weeks in {boot['n_clusters']} origins: "
            f"mean {boot['mean']:+.3f}, 90% [{boot['lo']:+.3f}, {boot['hi']:+.3f}] (origins resampled, B {FB.B}, seed {FB.SEED}"
            f"{'; ' + str(boot['dropped']) + ' empty resamples dropped' if boot['dropped'] else ''})")
    out(f"  bar: the 90% lower bound above 0 - {'PASS' if passes(boot) else 'not passed'}. Reported only; Boris decides.")
    by_status = defaultdict(list)
    for r in rows:
        if r["group"] == "flagged":
            by_status[r["status"]].append(r["e"])
    out("  by status (information): " + ", ".join(f"{st} n={len(v)} mean {sum(v) / len(v):+.3f}" for st, v in sorted(by_status.items())))
    out(f"  no player_gw row (counted 0): {sum(o.get('no_row', 0) for o in per)}")
    for label, sel in (("point 5 alone (status a, a suspended gameweek in the plain last-four window; information)",
                        [r for r in rows if r["group"] == "point5"]),
                       (f"our own flagged players (in our 15 at the origin; {sum(o.get('name_matched', 0) for o in per)} squad rows "
                        f"without player_id matched by name, club and position; information)",
                        [r for r in rows if r["group"] == "flagged" and r["ours"]])):
        mean = f"{sum(r['e'] for r in sel) / len(sel):+.3f}" if sel else "-"
        out(f"  {label}: n={len(sel)} mean e {mean}")
    for r in (r for r in rows if r["group"] == "flagged" and r["ours"]):
        out(f"    GW{r['origin']} -> GW{r['week']}  {r['name']:<16} {r['status']}  v1 {r['v1']:.2f}  v2 {r['v2']:.2f}  "
            f"realised {r['r']:.0f}  e {r['e']:+.2f}")
    if len(scored) < len(per):
        out(f"  NOT SCORED: {', '.join('GW' + str(o['origin']) for o in per if 'missing' in o)} (missing input above); the primary "
            f"line covers {len(scored)} of {len(per)} origins")
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "gate_v2_check.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path)
    csv_path = os.path.join(a.out, "gate_v2_rows.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        import csv
        w = csv.DictWriter(fh, fieldnames=["origin", "week", "id", "name", "status", "mode", "v1", "v2", "r", "e", "group", "ours"])
        w.writeheader()
        w.writerows(rows)
    run_.wrote(csv_path)
    print(f"written: {path}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (G.MissingInput, XL.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
