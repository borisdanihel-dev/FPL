"""tools/cup_backtest.py - Step 16 part 4: the cup Monte Carlo's point-in-time
backtest on 2024/25 and 2025/26 (BUILD_PLAN.md Step 16 point 4; prereg/S16.md, parts
3-4 and its amendment of 5 Nov). Pass: Brier skill score >= 0.10 against the base
rate, blanks and doubles of both seasons pooled.

The real backtest gets one run: nothing is changed after its result is seen. It waits
for Boris's rulings on the prereg's four questions, so main() refuses without
--run-once. Offline; the runner never imports it. Standard library only. It reads
downloaded files, so it runs with `python -I`.

    python -I tools/cup_backtest.py --run-once
"""
import argparse
import csv
import io
import os
import random
import sys
from collections import defaultdict
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import blank_double as BD                             # noqa: E402
import cup_mc as M                                    # noqa: E402

SEASONS = ("2024-25", "2025-26")
RATING_SEASONS = ("2023-24", "2024-25", "2025-26")
PASS_BSS = 0.10
BOOTSTRAP = 10000
BINS = 10
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(HERE, "historical")
OUT = os.path.join(HERE, "tools", "out", "s16_backtest")


def load_fixtures(hist, season, names):
    """[(id, event, kickoff, home, away)] with cup names, from the season's files."""
    by_fpl = {v["fpl"]: k for k, v in names.items() if v["fpl"]}
    with io.open(os.path.join(hist, season, "teams.csv"), encoding="utf-8", newline="") as fh:
        teams = {int(r["id"]): r["name"] for r in csv.DictReader(fh)}
    unknown = sorted(n for n in teams.values() if n not in by_fpl)
    if unknown:
        raise M.MissingInput(f"{season}: {unknown[0]} is not in names.csv")
    out = []
    with io.open(os.path.join(hist, season, "fixtures.csv"), encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            ev = (r.get("event") or "").strip()
            ko = (r.get("kickoff_time") or "").strip()
            out.append((int(r["id"]), int(ev) if ev not in ("", "None") else None,
                        datetime.fromisoformat(ko.replace("Z", "+00:00")) if ko not in ("", "None") else None,
                        by_fpl[teams[int(r["team_h"])]], by_fpl[teams[int(r["team_a"])]]))
    return out


def base_rates(hist, test_season):
    """(P(blank), P(double)) per team-gameweek over part 1's seasons before the test
    season, leaving out the void round and events above 38."""
    blank = double = total = 0
    for season in BD.SEASONS:
        if season >= test_season:
            break
        n, _, _, _ = BD.counts(BD.read_fixtures(os.path.join(hist, season, "fixtures.csv")))
        for (event, _), k in n.items():
            if event > BD.LAST_REGULAR_EVENT or (season, event) in BD.VOID_ROUNDS:
                continue
            total += 1
            blank += k == 0
            double += k >= 2
    if not total:
        raise M.MissingInput(f"no season before {test_season}")
    return blank / total, double / total


def forecast(season, ties, names, results, round_dates, origin_gw, n=M.N, seed=M.SEED, europe=()):
    """P(blank), P(double) from what is dated before the origin."""
    origin = M.uk_date(season.deadline[origin_gw])
    ratings = M.elo(results, origin)
    field, placeholders = {}, []
    known = [t for t in ties if t["competition"] == "FA Cup" and t["round"] == "R3"]
    if not (known and all(t["draw"] < origin for t in known)):         # amendment, item 1
        start = date(int(season.name[:4]), 7, 1)
        clubs, placeholders = M.fa_field(M.clubs_by_tier(results, start, origin), names)
        field["FA Cup"] = clubs + placeholders
    rating = M.club_ratings(ties, names, ratings, extra=[c for c in field.get("FA Cup", ()) if c not in placeholders])
    rating.update({q: M.PLACEHOLDER for q in placeholders})
    return M.simulate(season, ties, rating, field, round_dates, origin_gw, n=n, seed=seed, europe=europe)


def records(season, p_blank, p_double, origin_gw, base_blank, base_double):
    """One record per prediction: (season, origin, gw, club, kind, p, base, outcome)."""
    out = []
    for (club, gw), p in p_blank.items():
        out.append((season.name, origin_gw, gw, club, "blank", p, base_blank, int(season.actual[(club, gw)] == 0)))
    for (club, gw), p in p_double.items():
        out.append((season.name, origin_gw, gw, club, "double", p, base_double, int(season.actual[(club, gw)] >= 2)))
    return out


def bss(recs):
    """1 - BS_model / BS_base; None when the base rate has no error to beat."""
    model = sum((r[5] - r[7]) ** 2 for r in recs)
    base = sum((r[6] - r[7]) ** 2 for r in recs)
    return 1.0 - model / base if base else None


def bootstrap(recs, b=BOOTSTRAP, seed=M.SEED):
    """The 90% interval of the BSS over (season, target gameweek) blocks."""
    blocks = defaultdict(lambda: [0.0, 0.0])
    for r in recs:
        block = blocks[(r[0], r[2])]
        block[0] += (r[5] - r[7]) ** 2
        block[1] += (r[6] - r[7]) ** 2
    values = list(blocks.values())
    rng = random.Random(seed)
    draws = []
    for _ in range(b):
        picks = rng.choices(values, k=len(values))
        base = sum(p[1] for p in picks)
        if base:
            draws.append(1.0 - sum(p[0] for p in picks) / base)
    draws.sort()
    if not draws:
        raise M.MissingInput("every bootstrap resample has a base score of 0")
    return draws[int(0.05 * len(draws))], draws[min(len(draws) - 1, int(0.95 * len(draws)))]


def reliability(recs, bins=BINS):
    """[(bin, n, mean forecast, observed frequency)] over equal-width bins."""
    cells = defaultdict(list)
    for r in recs:
        cells[min(bins - 1, int(r[5] * bins))].append(r)
    return [(i, len(cells[i]), sum(r[5] for r in cells[i]) / len(cells[i]), sum(r[7] for r in cells[i]) / len(cells[i]))
            for i in sorted(cells)]


def report(recs, say):
    def line(label, rows):
        v = bss(rows)
        say(f"  {label:<26} n {len(rows):>6}  BSS {v:+.4f}" if v is not None else f"  {label:<26} n {len(rows):>6}  BSS none (no error to beat)")
    primary = bss(recs)
    low, high = bootstrap(recs)
    say(f"PRIMARY  BSS {primary:+.4f}  90% interval [{low:+.4f}, {high:+.4f}] over (season, target gameweek) blocks; bar {PASS_BSS:.2f}: "
        + ("PASS" if primary >= PASS_BSS else "FAIL"))
    say("")
    say("Information:")
    for kind in ("blank", "double"):
        line(kind, [r for r in recs if r[4] == kind])
    for season in SEASONS:
        line(season, [r for r in recs if r[0] == season])
        for kind in ("blank", "double"):
            line(f"{season} {kind}", [r for r in recs if r[0] == season and r[4] == kind])
    say("")
    say("Reliability (10 equal bins):")
    for kind in ("blank", "double"):
        for i, n, p, y in reliability([r for r in recs if r[4] == kind]):
            say(f"  {kind:<7} bin {i}: n {n:>6}  mean forecast {p:.4f}  observed {y:.4f}")
    return primary


def run(hist, cups, say, n=M.N):
    names = M.read_names(os.path.join(cups, "names.csv"))
    round_dates = M.read_round_dates(os.path.join(cups, "round_dates.csv"))
    results = M.read_results(os.path.join(hist, "football-data"), RATING_SEASONS)
    recs = []
    for season_name in SEASONS:
        season = M.Season(season_name, load_fixtures(hist, season_name, names))
        ties = M.read_cups(os.path.join(cups, f"cups_{season_name}.csv"))
        base_blank, base_double = base_rates(hist, season_name)
        say(f"{season_name}: base rate per team-gameweek, blank {base_blank:.5f}, double {base_double:.5f}")
        for g in M.ORIGIN_GWS:
            p_blank, p_double = forecast(season, ties, names, results, round_dates, g, n=n)
            recs += records(season, p_blank, p_double, g, base_blank, base_double)
            say(f"  origin GW{g}, deadline {season.deadline[g]:%Y-%m-%d %H:%M} UTC: {len(p_blank)} (club, gameweek) targets")
    say("")
    return report(recs, say), recs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-once", action="store_true", help="the prereg's one real run, after Boris's rulings")
    ap.add_argument("--hist", default=HIST)
    ap.add_argument("--cups", default=M.CUPS)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if not a.run_once:
        print("REFUSED: the real backtest gets one run (prereg/S16.md). Pass --run-once after Boris's rulings on the four questions.")
        return 2
    from provenance import Run
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("tools/cup_backtest.py", a.out, argv)
    path = os.path.join(a.out, "backtest.txt")
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        def say(text=""):
            print(text)
            fh.write(text + "\n")
        run(a.hist, a.cups, say)
    run_.wrote(path)
    run_.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
