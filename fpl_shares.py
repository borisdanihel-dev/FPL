"""fpl_shares.py - the runner's copy of tools/shares.py, the part W3 needs:
S11's share functions xp_v2 as tested reads (W3; prereg/W3.md, Part F item F-B).

Every definition below is copied verbatim from tools/shares.py by its syntax
tree, module aliases kept and pointed at the runner's copies, so the
runner never imports tools/; tests/test_W3.py holds the copies to the
tools. Standard library only.
"""
import fpl_hist as H
from collections import defaultdict


PRIOR_MINS = 180                          # the club-position mean prior: players with 180+ minutes there


class MissingInput(Exception):
    pass


def team_totals(rows, name_to_short):
    """(fixture, club) -> {xg, xa} summed over the club's rows in that fixture."""
    tot = defaultdict(lambda: {"xg": 0.0, "xa": 0.0})
    for r in rows:
        club = name_to_short.get(r["team"], r["team"])
        t = tot[(str(r["fixture"]), club)]
        t["xg"] += H._num(r.get("expected_goals")); t["xa"] += H._num(r.get("expected_assists"))
    return tot


def player_sums(rows, name_to_short, rounds, tot, by="element"):
    """Per key (element id, or name): own and team xG/xA over the fixtures
    the player appeared in (minutes > 0) within `rounds`, his minutes,
    starts and minutes in starts, and his club per fixture count."""
    out = {}
    for r in rows:
        rnd = int(r["round"])
        if rnd not in rounds:
            continue
        mins = H._num(r.get("minutes"))
        if mins <= 0:
            continue
        key = int(r["element"]) if by == "element" else r["name"]
        club = name_to_short.get(r["team"], r["team"])
        a = out.setdefault(key, {"xg": 0.0, "xa": 0.0, "team_xg": 0.0, "team_xa": 0.0, "minutes": 0.0, "starts": 0,
                                 "start_minutes": 0.0, "clubs": defaultdict(float), "pos": H.POS.get(r.get("position"), 0)})
        t = tot[(str(r["fixture"]), club)]
        a["xg"] += H._num(r.get("expected_goals")); a["xa"] += H._num(r.get("expected_assists"))
        a["team_xg"] += t["xg"]; a["team_xa"] += t["xa"]
        a["minutes"] += mins
        if H._num(r.get("starts")) >= 1:
            a["starts"] += 1; a["start_minutes"] += mins
        a["clubs"][club] += mins
    return out


def share_of(a, metric):
    team = a["team_" + metric]
    return a[metric] / team if team > 0 else 0.0


# ---------------------------------------------------------------------------
# the runner's prior (not in tools/shares.py): S11's Prior state read from
# the committed file priors/s11_prior_<season>.json (tools/make_prior.py
# writes it from the vaastav files); prior() below is S11's, verbatim
# ---------------------------------------------------------------------------

class Prior:
    """S11's Prior (tools/shares.py) from its saved state: the per (name,
    club) sums in S11's order; the club-position and league-position lists
    rebuilt by S11's rule (players with PRIOR_MINS+ minutes); k per metric.
    tests/test_W3.py holds every answer to shares.Prior on the files."""

    def __init__(self, state):
        self.folder = state["folder"]
        self.by_name_club = {(name, club): dict(a) for name, club, a in state["by_name_club"]}
        self.club_pos = defaultdict(list)
        self.league_pos = defaultdict(list)
        for (name, club), a in self.by_name_club.items():
            if a["minutes"] >= PRIOR_MINS:
                pair = (share_of(a, "xg"), share_of(a, "xa"))
                self.club_pos[(club, a["pos"])].append(pair)
                self.league_pos[a["pos"]].append(pair)
        self.clubs = {club for _, club in self.by_name_club}
        self.k, self.rel = dict(state["k"]), dict(state["rel"])

    def prior(self, name, pos, club, metric):
        """(prior share, source) for a 2025/26 player at `club`."""
        a = self.by_name_club.get((name, club))
        if a is not None and a["minutes"] > 0 and a["team_" + metric] > 0:
            return share_of(a, metric), "own 2024/25 at the club"
        i = 0 if metric == "xg" else 1
        vals = self.club_pos.get((club, pos))
        if vals:
            return sum(v[i] for v in vals) / len(vals), "club-position mean"
        vals = self.league_pos.get(pos)
        if not vals:
            raise MissingInput(f"no 2024/25 share for position {pos}")
        return sum(v[i] for v in vals) / len(vals), "league-position mean (club without 2024/25 rows)"
