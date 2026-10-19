"""
tools/hist_pit.py - the point-in-time club map for a vaastav season
(prereg/S4.md amendment 2). Offline; the nightly never imports it. The frozen
fpl_hist.canonical_from_vaastav is not edited: it gives every player the club
of his last row in the whole file, which leaks mid-season transfers into
early-gameweek rebuilds (verifier, S4). This module derives the club per
gameweek instead:

  * a player's club in gameweek g is the home team of his row's fixture if
    was_home, else the away team - cross-checked against the row's `team`
    column (a mismatch stops the run; nothing is substituted);
  * a gameweek without a row (a blank) carries the last known club forward;
  * before a player's first row he does not exist for the replay - no
    backfill from later rows.

    cm = club_map("historical/2025-26")
    club_at(cm, pid, g)            -> club short name, or None before his first row
    players_at(c, cm, g)           -> the canonical players dict as of gameweek g
"""

import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import fpl_hist as H                                              # noqa: E402


def _read(folder, name):
    path = os.path.join(folder, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} is missing - nothing is substituted for it")
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def derive_clubs(rows, fixtures, short_by_id, short_by_name):
    """{(pid, round): club} from the de-duplicated rows: the fixture's home
    team if was_home else its away team, cross-checked against the row's
    team column. Raises ValueError on a mismatch, an unknown fixture, or two
    rows of one player in one round that disagree."""
    out = {}
    for r in rows:
        pid, rnd = int(r["element"]), int(r["round"])
        f = fixtures.get(str(r["fixture"]))
        if f is None:
            raise ValueError(f"row for element {pid} round {rnd}: fixture {r['fixture']!r} is not in fixtures.csv")
        home = str(r.get("was_home")).lower() == "true"
        club = short_by_id.get(f["team_h"] if home else f["team_a"])
        stated = short_by_name.get(r.get("team"), r.get("team"))
        if club is None or club != stated:
            raise ValueError(f"row for element {pid} round {rnd}: the fixture says {club!r}, "
                             f"the team column says {stated!r}")
        prev = out.get((pid, rnd))
        if prev is not None and prev != club:
            raise ValueError(f"element {pid} round {rnd}: two rows with different clubs {prev!r} and {club!r}")
        out[(pid, rnd)] = club
    return out


def club_map(folder):
    """{"by_gw": {g: {pid: club}}, "first": {pid: first round}, "through":
    last round, "rows": {(pid, round): club}}. by_gw[g] holds every player
    who has had a row by g, at his last known club (carried forward over a
    blank); a player is absent before his first row."""
    teams = _read(folder, "teams.csv")
    short_by_id = {t["id"]: t["short_name"] for t in teams}
    short_by_name = {t["name"]: t["short_name"] for t in teams}
    fixtures = {f["id"]: f for f in _read(folder, "fixtures.csv")}
    raw = _read(folder, os.path.join("gws", "merged_gw.csv")
                if os.path.exists(os.path.join(folder, "gws", "merged_gw.csv")) else "merged_gw.csv")
    rows, _ = H.dedup_rows(raw)
    per = derive_clubs(rows, fixtures, short_by_id, short_by_name)
    through = max((rnd for _, rnd in per), default=0)
    by_round = defaultdict(dict)
    for (pid, rnd), club in per.items():
        by_round[rnd][pid] = club
    by_gw, first, current = {}, {}, {}
    for g in range(1, through + 1):
        for pid, club in by_round.get(g, {}).items():
            first.setdefault(pid, g)
            current[pid] = club
        by_gw[g] = dict(current)
    return {"by_gw": by_gw, "first": first, "through": through, "rows": per}


def club_at(cm, pid, g):
    """The club of `pid` as of gameweek g (rounds <= g only), or None before
    his first row."""
    if g < 1:
        return None
    g = min(g, cm["through"])
    return cm["by_gw"].get(g, {}).get(pid)


def players_at(c, cm, g):
    """The canonical players dict as of gameweek g: only players who exist
    by g, each at club_at(cm, pid, g). Every other field is the adapter's."""
    out = {}
    for pid, p in c["players"].items():
        club = club_at(cm, pid, g)
        if club is not None:
            out[pid] = dict(p, team=club)
    return out


def changes(cm):
    """[(pid, round, from, to)] - every mid-season club change in the map."""
    out, prev = [], {}
    for g in sorted(cm["by_gw"]):
        for pid, club in cm["by_gw"][g].items():
            if pid in prev and prev[pid] != club:
                out.append((pid, g, prev[pid], club))
            prev[pid] = club
    return out


if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "historical", "2025-26")
    cm = club_map(folder)
    ch = changes(cm)
    print(f"{folder}: {len(cm['first'])} players, rounds 1-{cm['through']}, {len(ch)} mid-season club changes")
    for pid, g, a, b in ch:
        print(f"  element {pid}: {a} -> {b} from GW{g}")
