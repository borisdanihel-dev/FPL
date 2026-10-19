"""tools/xp_v2_saves.py - S6e, xp_v2 + saves (prereg/S6e.md; RULINGS PART
F, item F-E). Offline; standard library only; the nightly never imports
it. Adoption at the GW10 checkpoint at the earliest, with Boris.

For goalkeepers, xp_v2 + saves = xp_v2 as tested + P(start) x E[save points
| start], E[save points | start] = E[saves | start] / 3 and

    E[saves | start] = sum over the round's fixtures of
        (Z x his saves per 90 + (1 - Z) x the keepers' mean saves per 90)
        x (minutes per start / 90) x (lambda_opp / the round's mean lambda)

with Z = m / (m + k) (S11's credibility method; k by split-half on the prior
season's keepers). The test: on S7's 50 squads, the starting keeper chosen
by xp_v2 against by xp_v2 + saves, the realised (re-scored) keeper points
paired per squad-gameweek, block bootstrap over gameweeks; pass: the 90%
lower bound > 0.

    python tools/xp_v2_saves.py --test [--hist DIR] [--prior DIR] [--rules ROOT] [--odds FILE] [--out DIR]
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

SAVES_PER_POINT = 3
FIRST, LAST = 5, 38
SEED = BT.SEED
STARTER_P = BT.STARTER_P


class MissingInput(XR.MissingInput):
    pass


def keeper_rows(rows):
    """The goalkeeper rows of raw vaastav rows."""
    return [r for r in rows if r.get("position") in ("GK", "GKP")]


def saves_k(prior_rows, half_minutes=SH.HALF_MINUTES):
    """k = n (1 - r) / r for keepers' saves per 90 (S11's rule): r = the
    tie-corrected Spearman of saves per 90 in odd against even rounds among
    keepers with half_minutes+ in each half, n = their mean minutes / 90 per
    half. Returns (k, detail)."""
    half = {0: defaultdict(lambda: [0.0, 0.0]), 1: defaultdict(lambda: [0.0, 0.0])}
    for r in keeper_rows(prior_rows):
        h = half[int(r["round"]) % 2][int(r["element"])]
        h[0] += H._num(r.get("saves")); h[1] += H._num(r.get("minutes"))
    a, b, mins = [], [], []
    for pid in sorted(set(half[0]) & set(half[1])):
        (s0, m0), (s1, m1) = half[1][pid], half[0][pid]
        if m0 >= half_minutes and m1 >= half_minutes:
            a.append(s0 / m0 * 90); b.append(s1 / m1 * 90); mins.append((m0 + m1) / 2 / 90.0)
    if len(a) < 3:
        raise MissingInput(f"split-half saves: fewer than 3 keepers with {half_minutes}+ minutes in each half")
    r = E._spearman(a, b)
    if r <= 0:
        raise MissingInput(f"split-half saves: reliability {r:.3f} is not positive; k is undefined")
    n = sum(mins) / len(mins)
    return n * (1 - r) / r, {"r": r, "n": n, "keepers": len(a)}


def keeper_rates(by_round, t):
    """From rounds < t: per keeper (saves, minutes, starts, minutes in starts)
    and the keepers' minutes-weighted mean saves per 90."""
    per = defaultdict(lambda: [0.0, 0.0, 0, 0.0])
    for rnd in range(1, t):
        for r in keeper_rows(by_round.get(rnd, [])):
            m = H._num(r.get("minutes"))
            if m <= 0:
                continue
            a = per[int(r["element"])]
            a[0] += H._num(r.get("saves")); a[1] += m
            if H._num(r.get("starts")) >= 1:
                a[2] += 1; a[3] += m
    tot_s, tot_m = sum(a[0] for a in per.values()), sum(a[1] for a in per.values())
    return dict(per), (tot_s / tot_m * 90 if tot_m else 0.0)


def expected_saves(a, mean90, k, fixtures, lam_bar, pos_mean_start):
    """E[saves | start] for one keeper: a = (saves, minutes, starts, start
    minutes) or None; fixtures = [lambda_opp]; the round's mean lambda."""
    s, m, starts, sm = a if a else (0.0, 0.0, 0, 0.0)
    own90 = s / m * 90 if m else 0.0
    mm = m / 90.0
    z = mm / (mm + k) if (mm + k) > 0 else 0.0
    rate = z * own90 + (1 - z) * mean90
    m_start = sm / starts if starts else pos_mean_start
    return sum(rate * (m_start / 90.0) * (lo / lam_bar) for lo in fixtures) if lam_bar > 0 else 0.0


class Season:
    def __init__(self, hist_dir, prior_dir, odds_file=None):
        self.rp = XR.Replay(hist_dir, prior_dir, odds_file)
        with open(os.path.join(prior_dir, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
            prior_rows, _ = H.dedup_rows(list(csv.DictReader(fh)))
        self.k, self.k_detail = saves_k(prior_rows)

    def forecasts(self, t):
        """({pid: xp_v2}, {pid: xp_v2 + saves}, {pid: E[saves | start]},
        p_start, pos) at origin t from rounds < t."""
        rp = self.rp
        c = BT.canonical_at(rp.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        names = {pid: c["players"][pid]["name"] for pid in inp["players"]}
        xp, detail = XL.core(inp, names, rp.by_round, t, rp.s11.rows, rp.s11.n2s, rp.s11.tot, rp.s11.prior,
                             lambda team: rp.s11.club_fixtures(team, t), lambda fid, team: rp.s11.lambda_team(fid, team)[0],
                             lambda fid, team: rp.s5.lam_opp(fid, team)[0])
        lams = [v for lam, _ in rp.s5.lambdas(t).values() for v in (lam["lambda_home"], lam["lambda_away"])]
        lam_bar = sum(lams) / len(lams) if lams else 0.0
        rates, mean90 = keeper_rates(rp.by_round, t)
        starts = [a[3] / a[2] for a in rates.values() if a[2]]
        pos_mean_start = sum(starts) / len(starts) if starts else 90.0
        plus, esaves = dict(xp), {}
        for pid, x in detail.items():
            if inp["players"][pid]["pos"] != 1:
                continue
            es = expected_saves(rates.get(pid), mean90, self.k, [f["lam_opp"] for f in x["fixtures"]], lam_bar, pos_mean_start)
            esaves[pid] = es
            plus[pid] = xp[pid] + x["p_start"] * es / SAVES_PER_POINT
        p_start = {pid: p["p_start"] for pid, p in inp["players"].items()}
        pos = {pid: p["pos"] for pid, p in inp["players"].items()}
        return xp, plus, esaves, p_start, pos


def choose_keeper(keepers, proj):
    """The starting keeper: the higher forecast, ties to the lower id."""
    return max(keepers, key=lambda pid: (proj.get(pid, 0.0), -pid))


def keeper_points(chosen, keepers, actual):
    """The chosen keeper's points if he played, else the other keeper's if
    he did (FPL's keeper substitution), else 0."""
    pts, mins = actual.get(chosen, (0.0, 0.0))
    if mins > 0:
        return pts
    other = [k for k in keepers if k != chosen]
    if other:
        p2, m2 = actual.get(other[0], (0.0, 0.0))
        if m2 > 0:
            return p2
    return 0.0


def test_2526(hist_dir, prior_dir, out=print, odds_file=None, first=FIRST, last=LAST, n_squads=CH.N_SQUADS,
              squad_seed=CH.SQUAD_SEED, seed=SEED, rescored=None):
    if rescored is None:
        raise MissingInput("the re-scored season is required (xp_v2_replay.rescore)")
    s = Season(hist_dir, prior_dir, odds_file)
    rp = s.rp
    last = min(last, rp.hist["through"])
    actual = XR.actuals_from(rescored)
    squads = CH.sample_squads(CH.gw1_candidates(rp.hist), n_squads, squad_seed)
    out(f"S6E TEST  2025/26 GW{first}-{last} re-scored under the 2026/27 rules: the starting keeper of {len(squads)} fixed squads "
        f"(seed {squad_seed}) chosen by xp_v2 against by xp_v2 + saves; realised keeper points paired; bootstrap over gameweeks "
        f"B={BT.B}, 90%, seed {seed}; k (saves per 90, 2024/25 split-half) = {s.k:.3f} (r {s.k_detail['r']:.3f}, "
        f"{s.k_detail['keepers']} keepers)")
    out(f"  {'GW':>4} {'squads':>6} {'xp_v2':>7} {'+saves':>7} {'diff':>7} {'differ':>7} {'n GK':>5} {'MAE v2':>7} {'MAE +sv':>8}")
    per, mae_pairs = [], []
    for t in range(first, last + 1):
        xp, plus, esaves, p_start, pos = s.forecasts(t)
        act = actual.get(t, {})
        diffs, differ, base_pts, plus_pts = [], 0, [], []
        for squad in squads:
            gks = sorted(r["id"] for r in rp.pl.squad_rows(squad, t) if r["pos"] == 1)
            a, b = choose_keeper(gks, xp), choose_keeper(gks, plus)
            pa, pb = keeper_points(a, gks, act), keeper_points(b, gks, act)
            diffs.append(pb - pa); differ += a != b; base_pts.append(pa); plus_pts.append(pb)
        gk_start = [pid for pid in esaves if p_start.get(pid, 0.0) >= STARTER_P]
        real = {pid: act.get(pid, (0.0, 0.0))[0] for pid in gk_start}
        mae_v2 = sum(abs(xp[p] - real[p]) for p in gk_start) / len(gk_start) if gk_start else float("nan")
        mae_pl = sum(abs(plus[p] - real[p]) for p in gk_start) / len(gk_start) if gk_start else float("nan")
        n = len(squads)
        rec = {"gw": t, "diff": sum(diffs) / n, "base": sum(base_pts) / n, "plus": sum(plus_pts) / n, "differ": differ / n,
               "n_gk": len(gk_start), "mae_v2": mae_v2, "mae_plus": mae_pl}
        per.append(rec)
        out(f"  {t:>4} {n:>6} {rec['base']:7.2f} {rec['plus']:7.2f} {rec['diff']:+7.2f} {rec['differ']:7.2f} {len(gk_start):>5} "
            f"{mae_v2:7.3f} {mae_pl:8.3f}")
    boot = BT.bootstrap_mean([r["diff"] for r in per], seed=seed)
    mae = BT.bootstrap_mean([r["mae_plus"] - r["mae_v2"] for r in per if r["n_gk"]], seed=seed)
    ok = boot["lo"] > 0
    out(f"  primary: mean per-gameweek keeper points, xp_v2 + saves - xp_v2: {boot['mean']:+.3f} per squad, 90% CI "
        f"[{boot['lo']:+.3f}, {boot['hi']:+.3f}] (n={boot['n']} gameweeks, p={boot['p']:.4f}); season {sum(r['diff'] for r in per):+.1f}")
    out(f"  secondary (information only): MAE of keeper points (P(start) >= {STARTER_P}) xp_v2 + saves - xp_v2 "
        f"{mae['mean']:+.3f} [{mae['lo']:+.3f}, {mae['hi']:+.3f}]; the choice differs in "
        f"{sum(r['differ'] for r in per) / len(per):.2f} of squad-gameweeks")
    out(f"  pre-registered bar: 90% lower bound > 0: {'PASS' if ok else 'FAIL'}"
        + (" (adoption at the GW10 checkpoint at the earliest, with Boris)" if ok else ""))
    return {"per": per, "boot": boot, "mae": mae, "pass": ok, "k": s.k}


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--prior", default=os.path.join(ROOT, "historical", "2024-25"))
    ap.add_argument("--rules", default=os.path.join(ROOT, "historical"))
    ap.add_argument("--odds", default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "xp_v2_saves"))
    ap.add_argument("--first", type=int, default=FIRST)
    ap.add_argument("--last", type=int, default=LAST)
    ap.add_argument("--squads", type=int, default=CH.N_SQUADS)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    if not a.test:
        ap.print_help()
        return 2
    os.makedirs(a.out, exist_ok=True)
    run = Run("tools/xp_v2_saves.py", a.out, argv)
    lines = []

    def out(s):
        print(s); lines.append(s)
    rescored_csv = os.path.join(a.out, "rescored_2025-26.csv")
    try:
        rescored = XR.rescore(a.rules, rescored_csv)
        test_2526(a.hist, a.prior, out, odds_file=a.odds, first=a.first, last=a.last, n_squads=a.squads, rescored=rescored)
    except (MissingInput, XR.MissingInput, BT.MissingInput, SH.MissingInput, CH.MissingInput) as e:
        print(f"missing input: {e}")
        return 2
    path = os.path.join(a.out, "s6e_2025-26.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run.wrote(rescored_csv)
    run.wrote(path)
    print(f"written: {path}; provenance: {run.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
