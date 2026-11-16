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
    for g in origins:
        d, path, dl, book, model, snap = G.origin(data_dir, g, exports)
        sus, unknown = G.suspensions([x for x in exports if x[0] < dl], deadlines, d["gameweek"])
        weeks_n = 6
        v1, _ = G.matrix(d, g, weeks_n, book, model, prior, names, "v1")
        v2, modes = G.matrix(d, g, weeks_n, book, model, prior, names, "v2", sus)
        flagged = [p for p in d["all_players"] if p["status"] in FLAGGED and (p.get("mins_last4") or 0) >= 45]
        s, n, no_row = 0.0, 0, 0
        for i, u in enumerate(range(g, g + weeks_n)):
            if u > last or u not in locked:
                continue
            playing = {t for f in XL.target_fixtures(d, u).values() for t in (f["home"], f["away"])}
            for p in flagged:
                if p["team"] not in playing:
                    continue
                pid = p["id"]
                r = realised.get((pid, u))
                if r is None:
                    no_row += 1
                    r = 0.0
                a, b = v1[i].get(pid, 0.0), v2[i].get(pid, 0.0)
                e = abs(a - r) - abs(b - r)
                rows.append({"origin": g, "week": u, "id": pid, "name": p["web_name"], "status": p["status"],
                             "mode": modes.get(pid, ["?"] * weeks_n)[i], "v1": a, "v2": b, "r": r, "e": e})
                s += e
                n += 1
        per_origin.append({"origin": g, "export": os.path.basename(path), "snapshot": snap, "sum": s, "n": n,
                           "no_row": no_row, "flagged": len(flagged), "unknown": sorted(unknown & set(range(1, d["gameweek"] + 1)))})
    return rows, per_origin


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    a = ap.parse_args(argv)
    run_ = Run("tools/gate_v2_check.py", a.out, argv if argv is not None else sys.argv[1:])
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)
    rows, per = check(a.data, a.hist, out)
    out("STATUS GATE V2 (xp_v2_g2): THE RETROSPECTIVE CHECK, GW4-10 (prereg/FM.md; Boris's answer 4, Thu 12 Nov night)")
    out(f"  code {run_.commit[:7]} (modified tracked files {run_.dirty})")
    out(f"  {'origin':<7}{'export':<36}{'odds':<30}{'flagged':>8}{'n':>5}{'mean e':>9}  unknown GWs (point 5)")
    for o in per:
        out(f"  GW{o['origin']:<5}{o['export']:<36}{(o['snapshot'] or 'fallback'):<30}{o['flagged']:>8}{o['n']:>5}"
            f"{(o['sum'] / o['n'] if o['n'] else float('nan')):>9.3f}  {o['unknown'] or '-'}")
    boot = cluster_bootstrap([(o["sum"], o["n"]) for o in per])
    out("")
    out(f"  PRIMARY: e = |v1 - r| - |v2 - r| over {boot['n']} flagged player-weeks in {boot['n_clusters']} origins: "
        f"mean {boot['mean']:+.3f}, 90% [{boot['lo']:+.3f}, {boot['hi']:+.3f}] (origins resampled, B {FB.B}, seed {FB.SEED}"
        f"{'; ' + str(boot['dropped']) + ' empty resamples dropped' if boot['dropped'] else ''})")
    out(f"  bar: the 90% lower bound above 0 - {'PASS' if passes(boot) else 'not passed'}. Reported only; Boris decides.")
    by_status = defaultdict(list)
    for r in rows:
        by_status[r["status"]].append(r["e"])
    out("  by status (information): " + ", ".join(f"{st} n={len(v)} mean {sum(v) / len(v):+.3f}" for st, v in sorted(by_status.items())))
    out(f"  no player_gw row (counted 0): {sum(o['no_row'] for o in per)}")
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "gate_v2_check.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path)
    csv_path = os.path.join(a.out, "gate_v2_rows.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        import csv
        w = csv.DictWriter(fh, fieldnames=["origin", "week", "id", "name", "status", "mode", "v1", "v2", "r", "e"])
        w.writeheader()
        w.writerows(rows)
    run_.wrote(csv_path)
    print(f"written: {path}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except G.MissingInput as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
