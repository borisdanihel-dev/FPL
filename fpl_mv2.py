"""fpl_mv2.py - the runner's copy of tools/minutes_v2.py, the part W3 needs:
S12's caution count, booking rate and P(ban) (W3; prereg/W3.md, Part F item F-B).

Every definition below is copied verbatim from tools/minutes_v2.py by its syntax
tree, module aliases kept and pointed at the runner's copies, so the
runner never imports tools/; tests/test_W3.py holds the copies to the
tools. Standard library only.
"""
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone


CAUTION_BANDS = ((5, 19), (10, 32))  # (caution count that bans, before the club's n-th match)


CRED_K = 4.0


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


class Rows:
    """matches[club] = [(kickoff, match_key, event)] in kickoff order, league
    only; played[(pid, match_key)] = (minutes, started, yellow); club_of[pid]
    at the origin; pos[pid]. Only matches before `cut` are 'known' (results);
    later matches contribute their kickoff (congestion) only."""

    def __init__(self, matches, played, club_of, pos, names=None, known=None):
        self.matches = {c: sorted(v) for c, v in matches.items()}
        self.played = played
        self.club_of = club_of
        self.pos = pos
        self.names = names or {}
        self.known = known                 # match keys whose results are known at the origin; None = every match before the cut

    def club_matches_before(self, club, kickoff_cut):
        """The club's matches before the cut whose results are known (a
        fixture already kicked off but not finished at data time is not a
        missed match)."""
        return [m for m in self.matches.get(club, []) if m[0] < kickoff_cut and (self.known is None or m[1] in self.known)]

    def match_index(self, club, kickoff):
        """1-based number of the club's league match at `kickoff`."""
        return sum(1 for m in self.matches.get(club, []) if m[0] <= kickoff)


def cautions_before(rows, pid, kickoff_cut):
    return sum(y for (p, key), (_, _, y) in rows.played.items() if p == pid and key in rows_key_before(rows, kickoff_cut))


def rows_key_before(rows, kickoff_cut):
    if not hasattr(rows, "_kb") or rows._kb[0] != kickoff_cut:
        keys = {key for ms in rows.matches.values() for ko, key, _ in ms if ko < kickoff_cut}
        rows._kb = (kickoff_cut, keys)
    return rows._kb[1]


def p_ban_next(rate90, p_start):
    """P(ban for the fixture after this one) = P(booking this match)."""
    return min(1.0, rate90 * p_start)


def booking_rate90(rows, pid, kickoff_cut, pos_mean):
    keys = rows_key_before(rows, kickoff_cut)
    mins = sum(m for (p, key), (m, _, _) in rows.played.items() if p == pid and key in keys)
    y = sum(yy for (p, key), (_, _, yy) in rows.played.items() if p == pid and key in keys)
    m = mins / 90.0
    own = y / m if m else 0.0
    z = m / (m + CRED_K)
    return z * own + (1 - z) * pos_mean


def rows_2627(data_dir, d):
    """Rows from fpl.sqlite (finished fixtures as results, every fixture's
    kickoff) with the export's statuses."""
    db = os.path.join(data_dir, "fpl.sqlite")
    if not os.path.exists(db):
        raise MissingInput(f"{db} is missing")
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return _rows_2627(c, d)
    finally:
        c.close()


def _rows_2627(c, d):
    short = {i: s for i, s in c.execute("select id, short_name from teams")}
    matches = defaultdict(list)
    fx_event = {}
    for fid, ev, ko, h, a, fin in c.execute("select id, event, kickoff_time, team_h, team_a, finished from fixtures where event is not null"):
        kot = datetime.fromisoformat(ko.replace("Z", "+00:00"))
        matches[short[h]].append((kot, str(fid), ev)); matches[short[a]].append((kot, str(fid), ev))
        fx_event[str(fid)] = (ev, short[h], short[a], fin)
    played = {}
    team_of = {pid: short[t] for pid, t in c.execute("select id, team_id from players")}
    pos = {pid: p for pid, p in c.execute("select id, position from players")}
    for pid, ev, mins, starts, yellow in c.execute("select player_id, event, minutes, starts, yellow from player_gw"):
        club = team_of.get(pid)
        for fid, (e, h, a, fin) in fx_event.items():
            if e == ev and fin and club in (h, a):
                played[(pid, fid)] = (mins or 0, 1 if starts else 0, yellow or 0)
    names = {p["id"]: p["web_name"] for p in d["all_players"]}
    known = {fid for fid, (e, h, a, fin) in fx_event.items() if fin}
    return Rows(matches, played, team_of, pos, names, known)
