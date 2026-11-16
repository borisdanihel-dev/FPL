"""tools/xp_v2_saves2.py - S6e2 (RULING 19 Oct evening, point 2;
prereg/S6e2.md): xp_v2 + the discretised save points, tested on 2024/25
only. Offline; standard library only; the nightly never imports it.
Adoption at the GW10 checkpoint at the earliest, with Boris.

For goalkeepers, xp_v2 + save points = xp_v2 as tested + P(start) x the sum
over the round's fixtures f of E[floor(S_f / 3)], S_f ~ Poisson(mu_f), mu_f
= S6e's E[saves | start] for that fixture alone (tools/xp_v2_saves.py's
expected_saves on [lambda_opp of f]: shrunk saves per 90 x minutes per
start / 90 x lambda_opp / the round's mean lambda; k by S6e's split-half on
the prior season's keepers, here 2023/24). FPL pays one point per full
three saves in a match, so a double gameweek sums two floors.

The test is S6e's test_2526 loop, unchanged, with these forecasts, on
2024/25 GW5-38 through S6f's harness (tools/xp_v2_2425.py: priors 2023/24,
football-data 2024/25 with the Ipswich alias for the construction, S10b's
re-score with DEFCON excluded): on S7's 50 squads the starting keeper
chosen by xp_v2 against by xp_v2 + save points, realised keeper points
paired, bootstrap over gameweeks (B = 10000, seed 20261018); pass: the 90%
lower bound > 0.

    python tools/xp_v2_saves2.py --test [--hist ROOT] [--odds FILE] [--out DIR]
"""
import argparse
import contextlib
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_saves as SV                                          # noqa: E402
import xp_v2_2425 as F                                            # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

TAIL = 1e-15                        # E[floor(S/3)]'s sum stops when P(S >= 3j) is below this
J_CAP = 10000                       # and after this many terms whatever happens (amendment 1)
SEASON, PRIOR = F.SEASON, F.PRIOR


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted."""


def floor_points(mu, per=SV.SAVES_PER_POINT, tail=TAIL, j_cap=J_CAP):
    """E[floor(S / per)] for S ~ Poisson(mu) = sum over j >= 1 of P(S >= per j).
    The sum stops when the tail is below `tail`, once the pmf has underflowed
    past the mode (rounding can hold 1 - cdf just above `tail` for ever;
    amendment 1), or after j_cap terms."""
    if mu <= 0:
        return 0.0
    total, cdf, p, k, j = 0.0, 0.0, math.exp(-mu), 0, 1
    while j <= j_cap:
        while k <= per * j - 1:
            cdf += p
            k += 1
            p *= mu / k
        surv = 1.0 - cdf
        if surv < tail or (k > mu and p == 0.0):
            return total
        total += surv
        j += 1
    return total


class Season2(SV.Season):
    """S6e's Season with the discretised save points; forecasts() is S6e's
    except the keeper term. The instances and, per keeper-origin, (E[saves] /
    3, the discretised points) are kept for the report."""
    instances = []

    def __init__(self, hist_dir, prior_dir, odds_file=None):
        super().__init__(hist_dir, prior_dir, odds_file)
        self.sizes = []
        Season2.instances.append(self)

    def forecasts(self, t):
        rp = self.rp
        c = BT.canonical_at(rp.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        names = {pid: c["players"][pid]["name"] for pid in inp["players"]}
        xp, detail = XL.core(inp, names, rp.by_round, t, rp.s11.rows, rp.s11.n2s, rp.s11.tot, rp.s11.prior,
                             lambda team: rp.s11.club_fixtures(team, t), lambda fid, team: rp.s11.lambda_team(fid, team)[0],
                             lambda fid, team: rp.s5.lam_opp(fid, team)[0])
        lams = [v for lam, _ in rp.s5.lambdas(t).values() for v in (lam["lambda_home"], lam["lambda_away"])]
        lam_bar = sum(lams) / len(lams) if lams else 0.0
        rates, mean90 = SV.keeper_rates(rp.by_round, t)
        starts = [a[3] / a[2] for a in rates.values() if a[2]]
        pos_mean_start = sum(starts) / len(starts) if starts else 90.0
        plus, esaves = dict(xp), {}
        for pid, x in detail.items():
            if inp["players"][pid]["pos"] != 1:
                continue
            mus = [SV.expected_saves(rates.get(pid), mean90, self.k, [f["lam_opp"]], lam_bar, pos_mean_start)
                   for f in x["fixtures"]]                    # S6e's E[saves | start], one fixture at a time
            es = sum(mus)
            pts = sum(floor_points(mu) for mu in mus)
            esaves[pid] = es
            plus[pid] = xp[pid] + x["p_start"] * pts
            self.sizes.append((es / SV.SAVES_PER_POINT, pts))
        p_start = {pid: p["p_start"] for pid, p in inp["players"].items()}
        pos = {pid: p["pos"] for pid, p in inp["players"].items()}
        return xp, plus, esaves, p_start, pos


@contextlib.contextmanager
def discretised():
    """S6e's test loop builds its Season by name: Season2 for the block, S6e's
    restored after, whatever happens."""
    saved = SV.Season
    SV.Season = Season2
    try:
        yield
    finally:
        SV.Season = saved


def run(hist_root, out=print, odds_file=F.ODDS, out_csv=None, first=XR.FIRST, last=XR.LAST, n_squads=CH.N_SQUADS,
        squad_seed=CH.SQUAD_SEED, seed=SV.SEED, season=SEASON, prior=PRIOR):
    hist_dir, prior_dir = os.path.join(hist_root, season), os.path.join(hist_root, prior)
    for p in (odds_file, os.path.join(prior_dir, "merged_gw.csv"), os.path.join(prior_dir, "teams.csv")):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing")
    F.check_no_counts(hist_dir)
    notes = []
    rescored = F.rescore(hist_root, out_csv, season, say=notes.append)
    Season2.instances = []
    with F.season_names(season), discretised():
        r = SV.test_2526(hist_dir, prior_dir, out=lambda s: None, odds_file=odds_file, first=first, last=last,
                         n_squads=n_squads, squad_seed=squad_seed, seed=seed, rescored=rescored)
    if len(Season2.instances) != 1:
        raise MissingInput(f"S6e's loop built {len(Season2.instances)} seasons, not one with the discretised term")
    s = Season2.instances[0]
    res = dict(r, season=season, prior=prior, first=first, last=r["per"][-1]["gw"], k_detail=s.k_detail, sizes=s.sizes,
               notes=notes, n_squads=n_squads, squad_seed=squad_seed, seed=seed)
    report(res, out, odds_file)
    return res


def report(res, out, odds_file):
    lab = F.label
    kd = res["k_detail"]
    out(f"S6E2 TEST  {lab(res['season'])} GW{res['first']}-{res['last']} re-scored under the 2026/27 table by S10b (bonus official, "
        f"DEFCON excluded): the starting keeper of {res['n_squads']} fixed squads (seed {res['squad_seed']}, {lab(res['season'])} GW1 "
        f"ownership) chosen by xp_v2 against by xp_v2 + save points, E[save points | start] = sum over fixtures of E[floor(S/3)], "
        f"S ~ Poisson(S6e's E[saves] for the fixture); realised keeper points paired; priors {lab(res['prior'])}; odds "
        f"{os.path.basename(odds_file)}; bootstrap over gameweeks B={BT.B}, 90%, seed {res['seed']}; k (saves per 90, "
        f"{lab(res['prior'])} split-half) = {res['k']:.3f} (r {kd['r']:.3f}, {kd['keepers']} keepers)")
    out("  S6e's test loop unchanged (tools/xp_v2_saves.py test_2526) with the discretised forecasts; S6f's 2024/25 harness")
    for n in res["notes"]:
        out(f"  re-score: {n}")
    out(f"  {'GW':>4} {'xp_v2':>7} {'+pts':>7} {'diff':>7} {'differ':>7} {'n GK':>5} {'MAE v2':>7} {'MAE +pt':>8}")
    for rec in res["per"]:
        out(f"  {rec['gw']:>4} {rec['base']:7.2f} {rec['plus']:7.2f} {rec['diff']:+7.2f} {rec['differ']:7.2f} {rec['n_gk']:>5} "
            f"{rec['mae_v2']:7.3f} {rec['mae_plus']:8.3f}")
    boot, mae = res["boot"], res["mae"]
    out(f"  primary: mean per-gameweek keeper points, xp_v2 + save points - xp_v2: {boot['mean']:+.3f} per squad, 90% CI "
        f"[{boot['lo']:+.3f}, {boot['hi']:+.3f}] (n={boot['n']} gameweeks, p={boot['p']:.4f}); season "
        f"{sum(r['diff'] for r in res['per']):+.1f}")
    sizes = res["sizes"]
    third = sum(a for a, _ in sizes) / len(sizes) if sizes else float("nan")
    floor = sum(b for _, b in sizes) / len(sizes) if sizes else float("nan")
    out(f"  secondary (information only): MAE of keeper points (P(start) >= {SV.STARTER_P}) xp_v2 + save points - xp_v2 "
        f"{mae['mean']:+.3f} [{mae['lo']:+.3f}, {mae['hi']:+.3f}]; the choice differs in "
        f"{sum(r['differ'] for r in res['per']) / len(res['per']):.2f} of squad-gameweeks; the correction: mean E[floor(S/3)] "
        f"{floor:.3f} against S6e's E[S]/3 {third:.3f} over {len(sizes)} keeper forecasts")
    out("  pre-registered bar: 90% lower bound > 0: " + ("PASS (adoption at the GW10 checkpoint at the earliest, with Boris)"
                                                         if res["pass"] else "FAIL"))


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test", action="store_true", required=True)
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"), help="the root holding 2024-25/, 2023-24/ and 2026-27/")
    ap.add_argument("--odds", default=F.ODDS)
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "xp_v2_saves2"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("tools/xp_v2_saves2.py", a.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    csv_path = os.path.join(a.out, f"rescored_{SEASON}.csv")
    try:
        run(a.hist, out, odds_file=a.odds, out_csv=csv_path)
    except (XR.MissingInput, OL.MissingInput, BT.MissingInput, CH.MissingInput, SH.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        return 2
    path = os.path.join(a.out, f"s6e2_{SEASON}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(csv_path)
    run_.wrote(path)
    print(f"written: {path}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
