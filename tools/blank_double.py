"""
tools/blank_double.py  -  blank and double gameweek history (BUILD_PLAN.md
Step 16, point 1; prereg/S16.md, part 1; RULING lane A, 19 Oct midday,
point 2). Offline: the nightly runner never imports it. Standard library only.

The fixtures files are downloads: run this only as `python -I` (CLAUDE.md,
"downloads are data, never code"). It opens them read-only, as CSV data.

    python -I tools/blank_double.py history [--hist DIR]
        For every season with DIR/<season>/fixtures.csv, from 2018-19, each
        team's fixture count in each FPL event. 0 is a blank, 2 or more a
        double. Then a table by event number across the seasons.

    python -I tools/blank_double.py test [--hist DIR]
        The reproduction test: for 2024-25 and 2025-26, per team and event,
        the counts equal those counted straight from the official fixtures
        files, exactly. Secondary: 2025-26 against merged_gw.csv.

A fixture with no event (unscheduled) is counted apart, never placed in an
event. Events above 38 (2019/20's restart) are kept as FPL numbered them,
and flagged. Teams are the season's own ids 1-20; names come only from a
local teams.csv.
"""

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(HERE, "historical")
SEASONS = ("2018-19", "2019-20", "2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26")
REPRODUCE = ("2024-25", "2025-26")
LAST_REGULAR_EVENT = 38


def read_fixtures(path):
    """[(event or None, team_h, team_a)] from a fixtures.csv, read-only."""
    with open(path, encoding="utf-8", newline="") as fh:
        return [(int(r["event"]) if (r.get("event") or "").strip() not in ("", "None") else None,
                 int(r["team_h"]), int(r["team_a"])) for r in csv.DictReader(fh)]


def counts(fixtures):
    """({(event, team): fixtures}, [unscheduled fixtures], teams, events).
    Every team has a count in every event that holds a fixture, 0 included:
    those zeros are the blanks."""
    teams = sorted({t for _, h, a in fixtures for t in (h, a)})
    events = sorted({e for e, _, _ in fixtures if e is not None})
    n = {(e, t): 0 for e in events for t in teams}
    unscheduled = []
    for e, h, a in fixtures:
        if e is None:
            unscheduled.append((h, a))
            continue
        n[(e, h)] += 1
        n[(e, a)] += 1
    return n, unscheduled, teams, events


def blanks_and_doubles(n):
    """{event: {"blank": [teams], "double": [(team, fixtures)]}} for every
    event with a blank or a double."""
    out = defaultdict(lambda: {"blank": [], "double": []})
    for (e, t), k in sorted(n.items()):
        if k == 0:
            out[e]["blank"].append(t)
        elif k >= 2:
            out[e]["double"].append((t, k))
    return dict(out)


def team_names(hist, season):
    p = os.path.join(hist, season, "teams.csv")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8", newline="") as fh:
        return {int(r["id"]): r["short_name"] for r in csv.DictReader(fh)}


def straight_count(path):
    """The reproduction test's reference: {(event, team): fixtures} counted
    straight from the file with csv.reader and the header's column indices -
    no code shared with read_fixtures or counts."""
    with open(path, encoding="utf-8", newline="") as fh:
        rows = csv.reader(fh)
        head = next(rows)
        ie, ih, ia = head.index("event"), head.index("team_h"), head.index("team_a")
        c = Counter()
        for r in rows:
            if r[ie] not in ("", "None"):
                c[(int(r[ie]), int(r[ih]))] += 1
                c[(int(r[ie]), int(r[ia]))] += 1
    return c


def compare(tool, reference):
    """Every (event, team) whose counts differ, zeros included."""
    keys = set(tool) | set(reference)
    return sorted((k, tool.get(k, 0), reference.get(k, 0)) for k in keys
                  if tool.get(k, 0) != reference.get(k, 0))


def gw_counts_from_merged(hist, season):
    """Secondary source for one season: {(round, team id): distinct fixtures}
    from the players' fixture rows in merged_gw.csv, the team named by
    teams.csv."""
    ids = {v: k for k, v in team_names_full(hist, season).items()}
    fixtures = defaultdict(set)
    with open(os.path.join(hist, season, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            fixtures[(int(r["round"]), ids[r["team"]])].add(int(r["fixture"]))
    return {k: len(v) for k, v in fixtures.items()}


def team_names_full(hist, season):
    with open(os.path.join(hist, season, "teams.csv"), encoding="utf-8", newline="") as fh:
        return {int(r["id"]): r["name"] for r in csv.DictReader(fh)}


def _label(t, names):
    return names.get(t, f"team {t}")


def history(hist=HIST, say=print):
    table = defaultdict(lambda: {"blank_seasons": set(), "double_seasons": set(), "blank": 0, "double": 0})
    for season in SEASONS:
        path = os.path.join(hist, season, "fixtures.csv")
        if not os.path.exists(path):
            say(f"{season}: no fixtures.csv - skipped")
            continue
        n, unscheduled, teams, events = counts(read_fixtures(path))
        names = team_names(hist, season)
        bd = blanks_and_doubles(n)
        late = [e for e in events if e > LAST_REGULAR_EVENT]
        gaps = [e for e in range(1, max(events) + 1) if e not in events]
        say(f"{season}: {len(teams)} teams, {len(events)} events"
            + (f" (numbered above 38: {late}; unused numbers: {gaps})" if late or gaps else "")
            + (f"; {len(unscheduled)} unscheduled fixtures" if unscheduled else "")
            + f"; {sum(len(v['blank']) for v in bd.values())} team blanks, "
              f"{sum(len(v['double']) for v in bd.values())} team doubles")
        for e in sorted(bd):
            b, d = bd[e]["blank"], bd[e]["double"]
            say(f"  GW{e}: " + "; ".join(x for x in (
                f"blank {len(b)}: " + ", ".join(_label(t, names) for t in b) if b else "",
                f"double {len(d)}: " + ", ".join(_label(t, names) + (f" x{k}" if k > 2 else "") for t, k in d)
                if d else "") if x))
            if b:
                table[e]["blank_seasons"].add(season)
                table[e]["blank"] += len(b)
            if d:
                table[e]["double_seasons"].add(season)
                table[e]["double"] += len(d)
    say("by event number, across the seasons: seasons with a blank / team blanks; "
        "seasons with a double / team doubles")
    for e in sorted(table):
        t = table[e]
        say(f"  GW{e}: blank {len(t['blank_seasons'])} / {t['blank']}; "
            f"double {len(t['double_seasons'])} / {t['double']}")
    return table


def test(hist=HIST, say=print):
    ok = True
    for season in REPRODUCE:
        path = os.path.join(hist, season, "fixtures.csv")
        n, _, teams, events = counts(read_fixtures(path))
        diff = compare(n, straight_count(path))
        ok &= not diff
        say(f"REPRODUCE {season}: {len(n)} team-events ({len(teams)} teams x {len(events)} events): "
            + ("every count equal" if not diff else f"{len(diff)} differ: {diff[:5]}"))
    if os.path.exists(os.path.join(hist, "2025-26", "merged_gw.csv")):
        n, _, _, _ = counts(read_fixtures(os.path.join(hist, "2025-26", "fixtures.csv")))
        merged = gw_counts_from_merged(hist, "2025-26")
        played = {k: v for k, v in n.items() if v > 0}
        diff = compare(played, merged)
        say(f"  secondary, 2025-26 against merged_gw.csv: {len(played)} team-events with a fixture; "
            + ("every count equal" if not diff else f"{len(diff)} differ: {diff[:5]}"))
    say(f"REPRODUCTION {'PASS' if ok else 'FAIL'}")
    return ok


def main(argv=None, say=print):
    ap = argparse.ArgumentParser(description="blank and double gameweek history (Step 16 part 1)")
    ap.add_argument("cmd", choices=("history", "test"))
    ap.add_argument("--hist", default=HIST)
    a = ap.parse_args(argv)
    if a.cmd == "history":
        history(a.hist, say)
        return 0
    return 0 if test(a.hist, say) else 1


if __name__ == "__main__":
    sys.exit(main())
