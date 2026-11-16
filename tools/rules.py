"""
tools/rules.py  -  the rule normaliser (BUILD_PLAN.md Step 10; prereg/S10.md).
Offline: the nightly runner never imports it. Standard library only. 2025/26
only for now (RULING morning 19 Oct, point 3).

    python tools/rules.py test [--hist DIR] [--seed N]
        The reproduction test. Every 2025/26 player-gameweek of
        DIR/2025-26/merged_gw.csv is re-scored with the 2026/27 points table
        (DIR/2026-27/game_config.json) under its 2025/26 position. The result
        is compared with FPL's total_points, within +-1, among players who
        appeared, with a 90% gameweek-bootstrap CI. Secondary lines follow.

    python tools/rules.py normalise OUT.csv [--hist DIR]
        2025/26 player-gameweeks re-scored under the 2026/27 rules: the
        2026/27 position by code, DEFCON rebuilt from its components, official
        bonus flagged "2025/26 BPS", assists rescaled only if game_config shows
        a change. One row per player-gameweek, with every category.

The points table is game_config.scoring, read whole. A missing category is
an error, never a default. game_config gives no thresholds; those below are
FPL's scoring rules as the project already encodes them (fpl_edge.py
DEFCON_THRESHOLD), frozen in prereg/S10.md. The reproduction test checks them.
"""

import argparse
import csv
import json
import os
import random
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

HIST = os.path.join(HERE, "historical")
POSITIONS = ("GKP", "DEF", "MID", "FWD")
ELEMENT_TYPE = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
CSV_POSITION = {"GK": "GKP", "GKP": "GKP", "DEF": "DEF", "MID": "MID", "FWD": "FWD"}

# thresholds (prereg/S10.md): not in game_config
LONG_PLAY_MINUTES = 60          # long_play at 60+, short_play below; clean sheet needs 60+
SAVES_PER_POINT = 3
CONCEDED_PER_POINT = 2
DEFCON_THRESHOLD = {"GKP": None, "DEF": 10, "MID": 12, "FWD": 12}
DEFCON_PARTS = {"DEF": ("clearances_blocks_interceptions", "tackles"),
                "MID": ("clearances_blocks_interceptions", "tackles", "recoveries"),
                "FWD": ("clearances_blocks_interceptions", "tackles", "recoveries")}

FLAT = ("short_play", "long_play", "assists", "saves", "penalties_saved", "penalties_missed",
        "own_goals", "yellow_cards", "red_cards", "bonus")
BY_POSITION = ("goals_scored", "clean_sheets", "goals_conceded", "defensive_contribution")
CATEGORIES = ("appearance", "goals_scored", "assists", "clean_sheets", "goals_conceded", "saves",
              "penalties_saved", "penalties_missed", "own_goals", "yellow_cards", "red_cards",
              "defensive_contribution", "bonus")
BPS_FLAG = "2025/26 BPS"         # bonus stays official, never re-scored (Q3)


def load_table(game_config):
    """{category: points} or {category: {position: points}} from
    game_config["scoring"]. Any missing category or position raises KeyError."""
    sc = game_config["scoring"]
    table = {k: int(sc[k]) for k in FLAT}
    for k in BY_POSITION:
        table[k] = {p: int(sc[k][p]) for p in POSITIONS}
    return table


def defcon_count(row, pos):
    """CBIT (DEF) or CBIRT (MID, FWD) rebuilt from its components; None for a
    goalkeeper, who has no defensive contribution."""
    parts = DEFCON_PARTS.get(pos)
    return None if parts is None else sum(int(row[p]) for p in parts)


def score(row, pos, table, defcon=None):
    """{category: points} for one fixture row of a player in position `pos`.
    The table applied literally: each recorded count times its points;
    appearance points only with minutes > 0; a clean sheet only with 60+
    minutes; per 3 saves and per 2 goals conceded; DEFCON once at the
    threshold, from `defcon` if given, else the official column."""
    m = int(row["minutes"])
    dc = int(row["defensive_contribution"]) if defcon is None else defcon
    thr = DEFCON_THRESHOLD[pos]
    return {
        "appearance": (table["long_play"] if m >= LONG_PLAY_MINUTES else table["short_play"]) if m > 0 else 0,
        "goals_scored": int(row["goals_scored"]) * table["goals_scored"][pos],
        "assists": int(row["assists"]) * table["assists"],
        "clean_sheets": table["clean_sheets"][pos] if int(row["clean_sheets"]) and m >= LONG_PLAY_MINUTES else 0,
        "goals_conceded": (int(row["goals_conceded"]) // CONCEDED_PER_POINT) * table["goals_conceded"][pos],
        "saves": (int(row["saves"]) // SAVES_PER_POINT) * table["saves"],
        "penalties_saved": int(row["penalties_saved"]) * table["penalties_saved"],
        "penalties_missed": int(row["penalties_missed"]) * table["penalties_missed"],
        "own_goals": int(row["own_goals"]) * table["own_goals"],
        "yellow_cards": int(row["yellow_cards"]) * table["yellow_cards"],
        "red_cards": int(row["red_cards"]) * table["red_cards"],
        "defensive_contribution": table["defensive_contribution"][pos] if thr is not None and dc >= thr else 0,
        "bonus": int(row["bonus"]) * table["bonus"],
    }


def player_gameweeks(rows, pos_of, table, rebuild=False):
    """{(element, round): {"round", "minutes", "official", "points", "parts"}}:
    each fixture row scored in pos_of(row), summed per player and round (a
    double gameweek is one unit)."""
    out = {}
    for r in rows:
        key = (int(r["element"]), int(r["round"]))
        pos = pos_of(r)
        parts = score(r, pos, table, defcon_count(r, pos) if rebuild else None)
        g = out.setdefault(key, {"round": key[1], "minutes": 0, "official": 0, "points": 0,
                                 "parts": Counter(), "pos": pos})
        g["minutes"] += int(r["minutes"])
        g["official"] += int(r["total_points"])
        g["points"] += sum(parts.values())
        g["parts"].update(parts)
    return out


def share(units, ok):
    return sum(1 for u in units if ok(u)) / len(units) if units else float("nan")


def bootstrap(units, ok, n=10000, seed=20261019, level=0.90):
    """(low, high) of the share over gameweek resamples (unit = gameweek)."""
    by_gw = defaultdict(list)
    for u in units:
        by_gw[u["round"]].append(1 if ok(u) else 0)
    gws = sorted(by_gw)
    rng = random.Random(seed)
    stats = []
    for _ in range(n):
        hits = tot = 0
        for g in (rng.choice(gws) for _ in gws):
            hits += sum(by_gw[g])
            tot += len(by_gw[g])
        stats.append(hits / tot)
    stats.sort()
    lo = stats[int((1 - level) / 2 * n)]
    hi = stats[int((1 + level) / 2 * n) - 1]
    return lo, hi


def within(u, tol=1):
    return abs(u["points"] - u["official"]) <= tol


def load_inputs(hist):
    import fpl_hist
    with open(os.path.join(hist, "2025-26", "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        rows, note = fpl_hist.dedup_rows(list(csv.DictReader(fh)))
    with open(os.path.join(hist, "2026-27", "game_config.json"), encoding="utf-8") as fh:
        table = load_table(json.load(fh))
    return rows, note, table


def codes_2526(hist):
    """{2025/26 element id: (code, 2025/26 position)} from players_raw.csv."""
    with open(os.path.join(hist, "2025-26", "players_raw.csv"), encoding="utf-8", newline="") as fh:
        return {int(r["id"]): (int(r["code"]), ELEMENT_TYPE[int(r["element_type"])]) for r in csv.DictReader(fh)}


def positions_2627(hist):
    """{code: 2026/27 position} from the live bootstrap's elements."""
    with open(os.path.join(hist, "2026-27", "elements_positions.csv"), encoding="utf-8", newline="") as fh:
        return {int(r["code"]): ELEMENT_TYPE[int(r["element_type"])] for r in csv.DictReader(fh)}


def assists_line(table, assists_2526):
    """Q4: rescale only if game_config shows a 2026/27 assist-points change."""
    if table["assists"] == assists_2526:
        return 1.0, (f"assists: {table['assists']} points in 2026/27 game_config, {assists_2526} in the "
                     f"2025/26 table under test - no change, no rescale")
    return table["assists"] / assists_2526, (f"assists: {assists_2526} -> {table['assists']} points, "
                                             f"rescaled x{table['assists'] / assists_2526:g}")


def test(hist=HIST, seed=20261019, say=print):
    rows, note, table = load_inputs(hist)
    say(f"rule normaliser - the reproduction test (prereg/S10.md); {note}")
    units = list(player_gameweeks(rows, lambda r: CSV_POSITION[r["position"]], table).values())
    appeared = [u for u in units if u["minutes"] > 0]
    primary = share(appeared, within)
    lo, hi = bootstrap(appeared, within, seed=seed)
    say(f"PRIMARY  {sum(1 for u in appeared if within(u))} of {len(appeared)} player-gameweeks with "
        f"minutes > 0 within +-1: {primary:.4f}  90% CI {lo:.4f} - {hi:.4f}  "
        f"(bar 0.99: {'PASS' if primary >= 0.99 else 'FAIL'})")
    say(f"  all {len(units)} player-gameweeks within +-1: {share(units, within):.4f}; "
        f"exact (appeared): {share(appeared, lambda u: u['points'] == u['official']):.4f}")
    for pos in POSITIONS:
        sub = [u for u in appeared if u["pos"] == pos]
        say(f"  {pos}: {share(sub, within):.4f} of {len(sub)}")
    resid = Counter(u["official"] - u["points"] for u in appeared if not within(u))
    say(f"  misses by official - re-scored: {dict(sorted(resid.items()))}")
    exact_resid = Counter(u["official"] - u["points"] for u in units if u["official"] != u["points"])
    say(f"  every non-exact unit by official - re-scored: {dict(sorted(exact_resid.items()))}")
    agree = defaultdict(lambda: [0, 0])
    for r in rows:
        pos = CSV_POSITION[r["position"]]
        if pos == "GKP" or int(r["minutes"]) == 0:
            continue
        agree[pos][0] += defcon_count(r, pos) == int(r["defensive_contribution"])
        agree[pos][1] += 1
    say("  DEFCON rebuilt from its parts = the official column (minutes > 0): " +
        ", ".join(f"{p} {a}/{n}" for p, (a, n) in sorted(agree.items())))
    _, line = assists_line(table, table["assists"])
    say("  " + line)
    say(f"  bonus: official, {BPS_FLAG} - no BPS re-score (Q3)")
    return primary


def normalise(out, hist=HIST, say=print):
    rows, note, table = load_inputs(hist)
    codes, new_pos = codes_2526(hist), positions_2627(hist)
    factor, line = assists_line(table, table["assists"])
    say(line)

    def pos_of(r):
        code, _ = codes[int(r["element"])]
        return new_pos.get(code, CSV_POSITION[r["position"]])
    units = player_gameweeks(rows, pos_of, table, rebuild=True)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["season", "round", "element", "code", "position_2526", "position_2627", "in_2627",
                    "minutes", *CATEGORIES, "points_2627_rules", "official_2526", "bonus_flag"])
        moved = Counter()
        for (el, rnd), u in sorted(units.items()):
            code, pos_old = codes[el]
            inside = code in new_pos
            moved[(pos_old, u["pos"])] += 1
            parts = dict(u["parts"])
            parts["assists"] = int(round(parts["assists"] * factor))
            w.writerow(["2025-26", rnd, el, code, pos_old, u["pos"], int(inside), u["minutes"],
                        *(parts[c] for c in CATEGORIES), sum(parts.values()), u["official"], BPS_FLAG])
    changed = {k: v for k, v in moved.items() if k[0] != k[1]}
    say(f"normalised {len(units)} player-gameweeks -> {out}; position changes (2025/26 -> 2026/27, "
        f"player-gameweeks): {changed or 'none'}")
    return units


# ---------------------------------------------------------------------------
# S10b (prereg/S10b.md; RULINGS PART F, F-C): earlier seasons
# ---------------------------------------------------------------------------

SEASONS_10B = ("2023-24", "2024-25")
DEFCON_MISSING = "DEFCON missing"     # the season's rows hold no defensive-action counts


def own_table(table):
    """The claim under test: a season before 2025/26 scored with the 2026/27
    table without the defensive-contribution category (DEFCON points began
    in 2025/26). Every other category as the table has it."""
    out = dict(table)
    out["defensive_contribution"] = {p: 0 for p in POSITIONS}
    return out


def load_season(hist, season):
    """The season's de-duplicated rows without manager rows (position AM),
    the note, the 2026/27 table and whether the rows hold the DEFCON parts."""
    import fpl_hist
    with open(os.path.join(hist, season, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        rows, note = fpl_hist.dedup_rows(list(csv.DictReader(fh)))
    managers = sum(1 for r in rows if r["position"] not in CSV_POSITION)
    rows = [r for r in rows if r["position"] in CSV_POSITION]
    with open(os.path.join(hist, "2026-27", "game_config.json"), encoding="utf-8") as fh:
        table = load_table(json.load(fh))
    parts = bool(rows) and all(c in rows[0] for c in DEFCON_PARTS["MID"])
    return rows, f"{note}; {managers} manager rows out", table, parts


def codes_season(hist, season):
    """{element id: (code, position)} of the season's players_raw.csv
    (managers, element_type 5, left out)."""
    with open(os.path.join(hist, season, "players_raw.csv"), encoding="utf-8", newline="") as fh:
        return {int(r["id"]): (int(r["code"]), ELEMENT_TYPE[int(r["element_type"])])
                for r in csv.DictReader(fh) if int(r["element_type"]) in ELEMENT_TYPE}


def season_gameweeks(rows, pos_of, table, parts):
    """As player_gameweeks; DEFCON from its parts when the rows hold them,
    else 0 (the season has no counts: DEFCON missing, never invented)."""
    out = {}
    for r in rows:
        key = (int(r["element"]), int(r["round"]))
        pos = pos_of(r)
        dc = defcon_count(r, pos) if parts else 0
        pts = score(r, pos, table, 0 if dc is None else dc)
        g = out.setdefault(key, {"round": key[1], "minutes": 0, "official": 0, "points": 0,
                                 "parts": Counter(), "pos": pos})
        g["minutes"] += int(r["minutes"])
        g["official"] += int(r["total_points"])
        g["points"] += sum(pts.values())
        g["parts"].update(pts)
    return out


def test_season(hist, season, seed=20261019, say=print):
    """The reproduction test for one earlier season (prereg/S10b.md): its own
    table under its own positions, within +-1 among players who appeared."""
    rows, note, table, parts = load_season(hist, season)
    own = own_table(table)
    say(f"rule normaliser - the reproduction test for {season} (prereg/S10b.md); {note}; "
        f"own table = the 2026/27 table without the DEFCON category (the claim under test)")
    units = list(season_gameweeks(rows, lambda r: CSV_POSITION[r["position"]], own, parts=False).values())
    appeared = [u for u in units if u["minutes"] > 0]
    primary = share(appeared, within)
    lo, hi = bootstrap(appeared, within, seed=seed)
    say(f"PRIMARY  {sum(1 for u in appeared if within(u))} of {len(appeared)} player-gameweeks with "
        f"minutes > 0 within +-1: {primary:.4f}  90% CI {lo:.4f} - {hi:.4f}  "
        f"(bar 0.99: {'PASS' if primary >= 0.99 else 'FAIL'})")
    say(f"  all {len(units)} player-gameweeks within +-1: {share(units, within):.4f}; "
        f"exact (appeared): {share(appeared, lambda u: u['points'] == u['official']):.4f}")
    for pos in POSITIONS:
        sub = [u for u in appeared if u["pos"] == pos]
        say(f"  {pos}: {share(sub, within):.4f} of {len(sub)}")
    miss = [u for u in appeared if not within(u)]
    say(f"  misses by official - re-scored: {dict(sorted(Counter(u['official'] - u['points'] for u in miss).items()))}")
    cats = Counter((u["pos"], c) for u in miss for c, v in u["parts"].items() if v and c not in ("appearance", "bonus"))
    say("  misses by position and scoring category present (information): " +
        (", ".join(f"{p} {c} {n}" for (p, c), n in sorted(cats.items())) or "none"))
    say(f"  DEFCON parts in the rows: {'yes' if parts else 'no - ' + DEFCON_MISSING}")
    say(f"  bonus: official, {season} BPS - no BPS re-score")
    return primary


def normalise_season(out, hist, season, say=print):
    """The season re-scored under the 2026/27 table by the 2026/27 position
    (by code), DEFCON from its parts or flagged missing, bonus official."""
    rows, note, table, parts = load_season(hist, season)
    codes, new_pos = codes_season(hist, season), positions_2627(hist)
    factor, line = assists_line(table, table["assists"])
    say(line)

    def pos_of(r):
        code = codes.get(int(r["element"]), (None, None))[0]
        return new_pos.get(code, CSV_POSITION[r["position"]])
    units = season_gameweeks(rows, pos_of, table, parts)
    own_pos = {}
    for r in rows:
        own_pos.setdefault(int(r["element"]), CSV_POSITION[r["position"]])
    flag = "" if parts else DEFCON_MISSING
    moved, no_code = Counter(), 0
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["season", "round", "element", "code", "position_own", "position_2627", "in_2627",
                    "minutes", *CATEGORIES, "points_2627_rules", "official", "bonus_flag", "defcon_flag"])
        for (el, rnd), u in sorted(units.items()):
            code = codes.get(el, (None, None))[0]
            inside = code in new_pos
            no_code += code is None
            moved[(own_pos[el], u["pos"])] += 1
            p = dict(u["parts"])
            p["assists"] = int(round(p["assists"] * factor))
            w.writerow([season, rnd, el, "" if code is None else code, own_pos[el], u["pos"], int(inside), u["minutes"],
                        *(p[c] for c in CATEGORIES), sum(p.values()), u["official"], f"{season} BPS", flag])
    changed = {k: v for k, v in moved.items() if k[0] != k[1]}
    say(f"normalised {len(units)} {season} player-gameweeks -> {out}; position changes ({season} -> 2026/27, "
        f"player-gameweeks): {changed or 'none'}; without a code: {no_code}; DEFCON: "
        f"{'from its parts' if parts else DEFCON_MISSING + ' (0 points, flagged on every row)'}")
    return units


def main(argv=None, say=print):
    ap = argparse.ArgumentParser(description="rule normaliser (Step 10)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("test")
    t.add_argument("--hist", default=HIST)
    t.add_argument("--seed", type=int, default=20261019)
    t.add_argument("--season", default="2025-26", choices=("2025-26",) + SEASONS_10B)
    t.add_argument("--out", default=None, help="S10b: write the lines and run.txt into this folder")
    n = sub.add_parser("normalise")
    n.add_argument("out")
    n.add_argument("--hist", default=HIST)
    n.add_argument("--season", default="2025-26", choices=("2025-26",) + SEASONS_10B)
    a = ap.parse_args(argv)
    if a.season == "2025-26":                      # Step 10, unchanged
        if a.cmd == "test":
            test(a.hist, a.seed, say)
        else:
            normalise(a.out, a.hist, say)
        return 0
    if a.cmd == "normalise":
        normalise_season(a.out, a.hist, a.season, say)
        return 0
    lines = []

    def both(line):
        say(line)
        lines.append(line)
    run = None
    if a.out:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from provenance import Run
        os.makedirs(a.out, exist_ok=True)
        run = Run("tools/rules.py", a.out, argv)
    test_season(a.hist, a.season, a.seed, both)
    if run is not None:
        path = os.path.join(a.out, f"rules_test_{a.season}.txt")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write("\n".join(lines) + "\n")
        run.wrote(path)
        run.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
