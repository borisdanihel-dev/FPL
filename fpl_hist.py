"""
fpl_hist.py  -  historical validation entry point (HISTORICAL_VALIDATION.md).

Adapts a season of github.com/vaastav/Fantasy-Premier-League CSVs into the
canonical slice that `fpl_edge.py` reads, then calls **the same functions the
live pipeline calls**. There is no second implementation of the measurement or
the model here: if the historical run passes, it is our code that passed.

    python fpl_hist.py historical/2025-26 --season 2025/26
    python fpl_hist.py historical/2025-26 --windows 4,8,12,20,38

Two things this adapter owns, because they are properties of the source and not
of the model:

* **De-duplication.** `merged_gw.csv` repeats some (element, fixture) rows
  verbatim. De-duplicating on that pair removes exactly the repeats; doing it on
  (element, round) would delete genuine double gameweeks instead. Every removal
  is reported - a silent de-dup that began dropping real rows after an upstream
  data change would be invisible.
* **Per-fixture to per-gameweek.** The source has one row per match; the
  canonical row is one per player per gameweek, with `n_fixtures` and the
  fixtures listed, matching what the live export carries.
"""

import argparse
import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402

POS = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def dedup_rows(rows, key=("element", "fixture")):
    """Drop repeated source rows. Returns (kept, note). The note names the
    count and the players, so a change upstream cannot pass unnoticed."""
    seen, kept, dropped = set(), [], defaultdict(int)
    for r in rows:
        k = tuple(r[f] for f in key)
        if k in seen:
            dropped[(r["element"], r.get("name", "?"))] += 1
            continue
        seen.add(k)
        kept.append(r)
    n = sum(dropped.values())
    if not n:
        return kept, "de-duplication on (element, fixture): no repeated rows"
    who = ", ".join(f"{name} (element {el}) x{c}"
                    for (el, name), c in sorted(dropped.items(), key=lambda kv: -kv[1]))
    return kept, (f"de-duplication on (element, fixture): removed {n} repeated "
                  f"row(s) from {len(dropped)} player(s) - {who}")


def canonical_from_vaastav(folder, season=None):
    """Adapter: a vaastav season folder -> canonical slice."""
    def read(name):
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} is missing - this adapter will not "
                                    f"substitute for it")
        with open(path, encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    teams = read("teams.csv")
    short_by_id = {t["id"]: t["short_name"] for t in teams}
    short_by_name = {t["name"]: t["short_name"] for t in teams}
    fixtures = {f["id"]: f for f in read("fixtures.csv")}
    raw = read(os.path.join("gws", "merged_gw.csv")
               if os.path.exists(os.path.join(folder, "gws", "merged_gw.csv"))
               else "merged_gw.csv")

    rows_in, note = dedup_rows(raw)
    notes = [note]

    players, by_key = {}, defaultdict(list)
    for r in rows_in:
        by_key[(int(r["element"]), int(r["round"]))].append(r)
        pid = int(r["element"])
        players[pid] = {"player_id": pid, "name": r["name"],
                        "pos": POS.get(r["position"], 0),
                        "team": short_by_name.get(r["team"], r["team"]),
                        "chance_next_round": None}

    rows = []
    for (pid, event), group in sorted(by_key.items()):
        fx = []
        for r in group:
            opp = short_by_id.get(r.get("opponent_team"), r.get("opponent_team"))
            fx.append({"opponent": opp,
                       "was_home": str(r.get("was_home")).lower() == "true",
                       "fixture_id": r.get("fixture")})
        rows.append({
            "player_id": pid, "event": event,
            "minutes": sum(_num(r["minutes"]) for r in group),
            "starts": sum(_num(r.get("starts")) for r in group),
            "pts": sum(_num(r["total_points"]) for r in group),
            "xg": sum(_num(r.get("expected_goals")) for r in group),
            "xa": sum(_num(r.get("expected_assists")) for r in group),
            "bps": sum(_num(r.get("bps")) for r in group),
            "defcon": sum(_num(r.get("defensive_contribution")) for r in group),
            "n_fixtures": len(group), "fixtures": fx})

    matches = []
    for f in fixtures.values():
        if f.get("team_h_score") in (None, "") or f.get("event") in (None, ""):
            continue
        h, a = short_by_id.get(f["team_h"]), short_by_id.get(f["team_a"])
        hs, as_ = _num(f["team_h_score"]), _num(f["team_a_score"])
        ev = int(f["event"])
        matches.append({"event": ev, "team": h, "opponent": a, "was_home": True,
                        "goals_for": hs, "goals_against": as_, "fixture_id": f["id"]})
        matches.append({"event": ev, "team": a, "opponent": h, "was_home": False,
                        "goals_for": as_, "goals_against": hs, "fixture_id": f["id"]})

    doubles = sum(1 for r in rows if r["n_fixtures"] > 1)
    notes.append(f"{len(rows)} player-gameweeks from {len(rows_in)} source rows; "
                 f"{doubles} of them cover more than one fixture")
    return E.check_canonical({
        "source": "vaastav", "season": season or os.path.basename(folder.rstrip("/\\")),
        "through_gw": max((r["event"] for r in rows), default=0),
        "players": players, "rows": rows, "team_matches": matches, "notes": notes})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="a vaastav season folder, e.g. historical/2025-26")
    ap.add_argument("--season", default=None)
    ap.add_argument("--windows", default="",
                    help="comma-separated training windows, e.g. 4,8,12,20,38")
    args = ap.parse_args()
    E.force_utf8()
    c = canonical_from_vaastav(args.folder, args.season)
    print(f"[{c['source']} {c['season']}: {len(c['players'])} players, "
          f"{len(c['rows'])} player-gameweeks, GW1-{c['through_gw']}]")
    for n in c["notes"]:
        print(f"  ! {n}")
    print()
    if not args.windows:
        print(E.reliability_table(E.measure_reliability(c),
                                  f"RELIABILITY  {c['season']}  (odd vs even gameweeks)"))
        return
    for w in [int(x) for x in args.windows.split(",")]:
        sl = E.canonical_through(c, w)
        print(E.reliability_table(
            E.measure_reliability(sl),
            f"RELIABILITY  {c['season']}  through GW{w}  (odd vs even)"))
        print()


if __name__ == "__main__":
    main()
