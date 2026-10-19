"""tools/xp_v2_2425.py - S6f (BUILD_PLAN.md Part F, F-D; prereg/S6f.md): S6b
and S6c repeated on 2024/25. Offline; standard library only; the nightly
never imports it.

2024/25 GW5-38 (priors 2023/24, odds from football-data 2024/25), outcomes
re-scored under the 2026/27 table by S10b (bonus official, DEFCON
excluded). xp_v2 as tested (S6b's Replay.xp_v2) against own_rebuilt
(S6c's, the primary) and own_proxy (S6b's, secondary). Each chooses the XI
and captain of S7's 50 synthetic squads (seed 7, from 2024/25 GW1
ownership); realised points with rule_autosubs and the captain doubled.
Primary: per gameweek, the squad mean of (xp_v2 - own_rebuilt); bootstrap
over gameweeks (B = 10000, seed 20261018), 90%; pass: lower bound > 0. A
fail does not revert GW8+ by itself: it goes to the chat, and the GW10
revert rule still governs.

DEFCON is removed on both sides (RULING 19 Oct evening, point 1). The
re-score holds no DEFCON points (every row flagged), and the 2024/25 rows
carry no defensive-action counts, so every forecast DEFCON term is 0; the
tool refuses inputs that break either.

S6b's test_2526 and S6c's test_s6c run unchanged; this tool prints the
2024/25 report from the records they return. For the construction only,
football-data's "Ipswich" maps to vaastav 2024/25's "Ipswich" (S5's alias
table maps it to 2026/27's "Ipswich Town"); the table is restored after.

    python tools/xp_v2_2425.py --test [--hist ROOT] [--odds FILE] [--out DIR]
"""
import argparse
import contextlib
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import rules as R                                                 # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

SEASON, PRIOR = "2024-25", "2023-24"
ODDS = os.path.join(ROOT, "tools", "odds", "E0_2024-25_fetched_2026-10-19.csv")
SEASON_ALIASES = {"2024-25": {"Ipswich": "Ipswich"}}   # football-data -> vaastav 2024/25 (S5's table: 2026/27 names)
FIRST, LAST = XR.FIRST, XR.LAST
DEFCON_COLUMNS = ("defensive_contribution",)


class MissingInput(XR.MissingInput):
    """A required input is missing or breaks the ruling: reported, never substituted."""


@contextlib.contextmanager
def season_names(season):
    """S5's football-data alias table with the season's own names, for the
    duration of the block; restored after, whatever happens."""
    saved = OL.FD_ALIASES
    OL.FD_ALIASES = dict(saved, **SEASON_ALIASES.get(season, {}))
    try:
        yield OL.FD_ALIASES
    finally:
        OL.FD_ALIASES = saved


def check_no_counts(hist_dir):
    """The forecasts' DEFCON terms are 0 only if the season's rows carry no
    defensive-action counts: refuse a merged_gw.csv with a non-zero count."""
    path = os.path.join(hist_dir, "merged_gw.csv")
    if not os.path.exists(path):
        raise MissingInput(f"{path} is missing")
    with open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        cols = [c for c in DEFCON_COLUMNS if c in (rd.fieldnames or [])]
        for r in rd:
            for c in cols:
                if float(r[c] or 0) != 0:
                    raise MissingInput(f"{path}: {c} {r[c]} for element {r['element']} round {r['round']}: the ruling removes "
                                       f"DEFCON on both sides, and this tool removes it only from seasons without counts")
    return cols


def check_rescored(path):
    """The outcomes exclude DEFCON: every row flagged missing, no DEFCON points."""
    n = 0
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            n += 1
            if r["defcon_flag"] != R.DEFCON_MISSING or float(r["defensive_contribution"] or 0) != 0:
                raise MissingInput(f"{path}: element {r['element']} round {r['round']} carries DEFCON "
                                   f"({r['defensive_contribution']}, {r['defcon_flag']!r}); the ruling excludes it")
    if not n:
        raise MissingInput(f"{path}: no rows")
    return n


def rescore(hist_root, out_csv, season=SEASON, say=lambda s: None):
    """S10b's re-score of the season into out_csv, checked, read back."""
    R.normalise_season(out_csv, hist_root, season, say=say)
    check_rescored(out_csv)
    return XR.load_rescored(out_csv)


def run(hist_root, out=print, odds_file=ODDS, out_csv=None, first=FIRST, last=LAST, n_squads=CH.N_SQUADS,
        squad_seed=CH.SQUAD_SEED, seed=XR.SEED, season=SEASON, prior=PRIOR):
    hist_dir, prior_dir = os.path.join(hist_root, season), os.path.join(hist_root, prior)
    for p in (odds_file, os.path.join(prior_dir, "merged_gw.csv"), os.path.join(prior_dir, "teams.csv")):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing")
    cols = check_no_counts(hist_dir)
    notes = []
    rescored = rescore(hist_root, out_csv, season, say=notes.append)
    with season_names(season):
        c = XR.test_s6c(hist_dir, prior_dir, out=lambda s: None, odds_file=odds_file, first=first, last=last,
                        n_squads=n_squads, squad_seed=squad_seed, seed=seed, rescored=rescored)
        b = XR.test_2526(hist_dir, prior_dir, hist_root, out=lambda s: None, odds_file=odds_file, first=first, last=last,
                         n_squads=n_squads, squad_seed=squad_seed, seed=seed, rescored=rescored)
    if c["squads"] != b["squads"] or [r["gw"] for r in c["per"]] != [r["gw"] for r in b["per"]]:
        raise MissingInput("S6b's and S6c's runs drew different squads or gameweeks")
    res = {"s6c": c, "s6b": b, "pass": c["boot"]["lo"] > 0, "defcon_columns": cols, "notes": notes,
           "first": first, "last": c["per"][-1]["gw"], "season": season, "prior": prior}
    report(res, out, n_squads=len(c["squads"]), squad_seed=squad_seed, seed=seed, odds_file=odds_file)
    return res


def label(s):
    return s.replace("-", "/")


def report(res, out, n_squads, squad_seed, seed, odds_file):
    c, b = res["s6c"], res["s6b"]
    by_gw = {r["gw"]: r for r in b["per"]}
    out(f"S6F TEST  {label(res['season'])} GW{res['first']}-{res['last']} (F-D: S6b and S6c repeated), re-scored under the 2026/27 "
        f"table by S10b (bonus official, DEFCON excluded): xp_v2 as tested against own_rebuilt (primary) and own_proxy, each "
        f"choosing the XI and captain of {n_squads} fixed squads (seed {squad_seed}, {label(res['season'])} GW1 ownership), realised "
        f"points with rule_autosubs and the captain doubled; priors {label(res['prior'])}; odds {os.path.basename(odds_file)}; "
        f"bootstrap over gameweeks B={BT.B}, 90%, seed {seed}")
    out(f"  DEFCON removed on both sides (RULING 19 Oct evening, point 1): the outcomes hold no DEFCON points (every row "
        f"'{R.DEFCON_MISSING}'), and the {label(res['season'])} rows carry no defensive-action counts "
        f"({'columns ' + ', '.join(res['defcon_columns']) + ' all 0' if res['defcon_columns'] else 'no such column'}), so xp_v2's "
        f"hit-rate term and bottomup's defcon90 are 0. Limitation: the test says nothing about DEFCON, which 2026/27 pays")
    out(f"  harness: S6b's test_2526 and S6c's test_s6c unchanged; football-data 'Ipswich' -> vaastav 'Ipswich' for the "
        f"construction; backtest.load_2526 labels the rows' ruleset 2025-26 (a label that refuses mixing, no number moves)")
    for n in res["notes"]:
        out(f"  re-score: {n}")
    out(f"  {XR.OWN_REBUILT_LACKS.replace('2024/25', label(res['prior']))}")    # S6c's note, its prior season named for this run
    out(f"  {'GW':>4} {'own_rebuilt':>11} {'xp_v2':>8} {'diff':>7} {'own_proxy':>9} {'v2-prx':>7} {'reb-prx':>8} {'same XI':>8} "
        f"{'same cap':>9} {'n start':>8} {'rho reb':>8} {'rho v2':>7} {'MAE reb':>8} {'MAE v2':>7}")
    for r in c["per"]:
        out(f"  {r['gw']:>4} {r['reb']:11.2f} {r['v2']:8.2f} {r['diff']:+7.2f} {r['prx']:9.2f} {by_gw[r['gw']]['diff']:+7.2f} "
            f"{r['reb_prx']:+8.2f} {r['same_xi']:8.2f} {r['same_cap']:9.2f} {r['n_start']:>8} {r['rho_reb']:8.3f} {r['rho_v2']:7.3f} "
            f"{r['mae_reb']:8.3f} {r['mae_v2']:7.3f}")
    bb, cb = b["boot"], c["boot"]
    out(f"  season (GW{res['first']}-{res['last']}): own_rebuilt {sum(r['reb'] for r in c['per']):.1f}, xp_v2 "
        f"{sum(r['v2'] for r in c['per']):.1f}, own_proxy {sum(r['prx'] for r in c['per']):.1f} points per squad; "
        f"xp_v2 - own_rebuilt {c['season']:+.1f}, xp_v2 - own_proxy {b['season']:+.1f} per squad per season")
    out(f"  primary: mean per-gameweek difference xp_v2 - own_rebuilt {cb['mean']:+.3f} points per squad, 90% CI "
        f"[{cb['lo']:+.3f}, {cb['hi']:+.3f}] (n={cb['n']} gameweeks, p={cb['p']:.4f})")
    out(f"  secondary (information only): S6b's xp_v2 - own_proxy {bb['mean']:+.3f} [{bb['lo']:+.3f}, {bb['hi']:+.3f}]; "
        f"Spearman among starters xp_v2 - own_rebuilt {c['rho']['mean']:+.4f} [{c['rho']['lo']:+.4f}, {c['rho']['hi']:+.4f}]; "
        f"MAE xp_v2 - own_rebuilt {c['mae']['mean']:+.4f} [{c['mae']['lo']:+.4f}, {c['mae']['hi']:+.4f}]; own_rebuilt - "
        f"own_proxy {c['reb_prx']['mean']:+.3f} [{c['reb_prx']['lo']:+.3f}, {c['reb_prx']['hi']:+.3f}]; same XI "
        f"{sum(r['same_xi'] for r in c['per']) / len(c['per']):.2f}, same captain "
        f"{sum(r['same_cap'] for r in c['per']) / len(c['per']):.2f} of squad-gameweeks")
    out(f"  pre-registered bar: 90% lower bound > 0: " + ("PASS" if res["pass"] else
        "FAIL - this does not revert GW8+ by itself; it goes to the chat, and the GW10 revert rule still governs (F-D)"))


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test", action="store_true", required=True)
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"), help="the root holding 2024-25/, 2023-24/ and 2026-27/")
    ap.add_argument("--odds", default=ODDS)
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "xp_v2_2425"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("tools/xp_v2_2425.py", a.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    csv_path = os.path.join(a.out, f"rescored_{SEASON}.csv")
    try:
        run(a.hist, out, odds_file=a.odds, out_csv=csv_path)
    except (XR.MissingInput, OL.MissingInput, BT.MissingInput, CH.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        return 2
    path = os.path.join(a.out, f"s6f_{SEASON}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(csv_path)
    run_.wrote(path)
    print(f"written: {path}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
