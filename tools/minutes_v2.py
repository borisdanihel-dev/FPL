"""
tools/minutes_v2.py - the minutes model v2 (BUILD_PLAN.md Step 12, item S12,
offline). Standard library only; the nightly never imports it.

    python tools/minutes_v2.py --test             # the pre-registered 2025/26 test against the current model
    python tools/minutes_v2.py --live             # P(start) for the next gameweek from the data worktree (+ overrides.csv)
    python tools/minutes_v2.py --score-overrides  # Brier of every applied override against the model, settled gameweeks

Definitions, as pre-registered in prereg/S12.md (the ruling verbatim there):
  states      P(start) = starts / matches over the club's last min(4, t-1) league matches before the
              deadline (a player without a row in a match counts 0); P(sub) = appearances without a
              start / the same; P(none) = the rest; live, scaled by chance_next_round as the current model
  GK lock     the keeper with the most starts in the club's last 3 matches: 0.95 (unless flagged live);
              the next most: 0.05; every other keeper 0; a tie: the keeper who started the latest match
  cover       a regular starter (started >= 3 of the club's last 4) who is out (live: status not 'a';
              replay: 0 minutes in the previous match after starting the 4 before it): his replacement -
              the same-position teammate who started most often in the training matches the regular did
              not start (ties: more starts overall, then the lower id) - gets max(own, the regular's
              P(start) before the absence)
  congestion  c = start rate of regular starters with <= 3 days' rest / with > 3 days' rest, fitted on the
              training rounds at every origin; P(start) x c (capped at 1) for a club with <= 3 days' rest;
              c = 1 when its 90% bootstrap interval over training rounds includes 1
  suspensions cautions = yellow cards before the deadline; a 5th before the club's 19th league match or a
              10th before its 32nd, received in the previous match -> P(start) = 0 for the next match;
              for the horizon (t+1): P(ban) = min(1, rate90 x P(start)), rate90 shrunk m/(m+4)
  overrides   overrides.csv on master (player, gw, p_start, reason, timestamp_utc), live only; every
              applied override is appended to tools/out/minutes_overrides_log.csv and scored later
  test        2025/26 GW5-38, the recording gate, paired per gameweek against fpl_edge.start_probability
              (the S4 harness's rebuilt p_start): (a) Brier of P(start) better by >= 0.01 with the 90% CI
              lower bound > 0; (b) MAE of bottomup xP with each P(start) not worse by more than 0.02;
              (c) keeper-starter mismatches <= the current model's. All three must hold.
"""

import argparse
import csv
import math
import os
import random
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402

WINDOW = 4
LOCK_WINDOW = 3
LOCK_P, LOCK_SECOND_P = 0.95, 0.05
REGULAR_MIN = 3                    # started >= 3 of the club's last 4
REST_SHORT = 3                     # days
CAUTION_BANDS = ((5, 19), (10, 32))  # (caution count that bans, before the club's n-th match)
CRED_K = 4.0
SEED = BT.SEED
B_FACTOR = BT.B
PASS_BRIER = 0.01
MAE_SLACK = 0.02
OVERRIDES = os.path.join(ROOT, "overrides.csv")
OVERRIDES_LOG = "minutes_overrides_log.csv"


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# the club match lists and per-player rows (both seasons share this shape)
# ---------------------------------------------------------------------------

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


def rest_days(rows, club, kickoff):
    prev = [m for m in rows.matches.get(club, []) if m[0] < kickoff]
    return (kickoff - prev[-1][0]).days if prev else None


# ---------------------------------------------------------------------------
# the model
# ---------------------------------------------------------------------------

def base_states(rows, pid, club, kickoff_cut):
    """(P(start), P(sub)) over the club's last min(4, n) matches before the cut."""
    last = rows.club_matches_before(club, kickoff_cut)[-WINDOW:]
    if not last:
        return 0.0, 0.0
    starts = apps = 0
    for _, key, _ in last:
        mins, started, _ = rows.played.get((pid, key), (0, 0, 0))
        starts += 1 if started else 0
        apps += 1 if mins > 0 else 0
    return starts / len(last), (apps - starts) / len(last)


def keeper_lock(rows, club, kickoff_cut, flagged=()):
    """{pid: P(start)} for the club's keepers."""
    last = rows.club_matches_before(club, kickoff_cut)[-LOCK_WINDOW:]
    keepers = [pid for pid, c in rows.club_of.items() if c == club and rows.pos.get(pid) == 1]
    if not keepers or not last:
        return {}
    starts, latest = {}, {}
    for pid in keepers:
        s = 0
        for i, (_, key, _) in enumerate(last):
            _, started, _ = rows.played.get((pid, key), (0, 0, 0))
            if started:
                s += 1
                latest[pid] = i
        starts[pid] = s
    order = sorted(keepers, key=lambda p: (-starts[p], -latest.get(p, -1), p))
    out = {}
    for i, pid in enumerate(order):
        if pid in flagged:
            continue
        out[pid] = LOCK_P if i == 0 else (LOCK_SECOND_P if i == 1 else 0.0)
    return out


def regulars_and_absent(rows, club, kickoff_cut, out_live=None):
    """Regular starters of the club (>= 3 of the last 4) and which of them
    are out: live by the flag set `out_live`; replay by 0 minutes in the
    previous match after starting the 4 before it."""
    last = rows.club_matches_before(club, kickoff_cut)
    regs, absent = [], []
    for pid, c in rows.club_of.items():
        if c != club:
            continue
        last4 = last[-WINDOW:]
        if len(last4) < WINDOW:
            continue
        starts4 = sum(1 for _, key, _ in last4 if rows.played.get((pid, key), (0, 0, 0))[1])
        if starts4 >= REGULAR_MIN:
            regs.append(pid)
            if out_live is not None:
                if pid in out_live:
                    absent.append(pid)
            elif len(last) >= WINDOW + 1:
                prev = last[-1]
                before = last[-WINDOW - 1:-1]
                mins_prev = rows.played.get((pid, prev[1]), (0, 0, 0))[0]
                if mins_prev == 0 and all(rows.played.get((pid, key), (0, 0, 0))[1] for _, key, _ in before):
                    absent.append(pid)
    return regs, absent


def replacement_for(rows, club, pid, kickoff_cut):
    """The same-position teammate who started most often in the club's
    training matches the regular did not start."""
    pos = rows.pos.get(pid)
    counts, total = defaultdict(int), defaultdict(int)
    for _, key, _ in rows.club_matches_before(club, kickoff_cut):
        reg_started = rows.played.get((pid, key), (0, 0, 0))[1]
        for cand, c in rows.club_of.items():
            if c != club or cand == pid or rows.pos.get(cand) != pos:
                continue
            started = rows.played.get((cand, key), (0, 0, 0))[1]
            if started:
                total[cand] += 1
                if not reg_started:
                    counts[cand] += 1
    if not counts:
        return None
    return sorted(counts, key=lambda c: (-counts[c], -total[c], c))[0]


def congestion_factor(rows, kickoff_cut, b=B_FACTOR, seed=SEED):
    """c = start rate of regular starters with <= 3 days' rest / > 3 days,
    over the training matches (every club's matches before the cut whose
    club had at least 4 earlier matches); 1.0 when the 90% bootstrap
    interval over training rounds includes 1. Returns (c, lo, hi, n_short)."""
    per_round = defaultdict(lambda: [0, 0, 0, 0])      # event -> [short starts, short n, long starts, long n]
    for club, ms in rows.matches.items():
        for i, (ko, key, ev) in enumerate(ms):
            if ko >= kickoff_cut or i < WINDOW or (rows.known is not None and key not in rows.known):
                continue
            last4 = ms[i - WINDOW:i]
            rest = (ko - ms[i - 1][0]).days
            short = rest <= REST_SHORT
            for pid, c in rows.club_of.items():
                if c != club:
                    continue
                if sum(1 for _, k, _ in last4 if rows.played.get((pid, k), (0, 0, 0))[1]) >= REGULAR_MIN:
                    started = rows.played.get((pid, key), (0, 0, 0))[1]
                    cell = per_round[ev]
                    if short:
                        cell[0] += 1 if started else 0; cell[1] += 1
                    else:
                        cell[2] += 1 if started else 0; cell[3] += 1

    def ratio(cells):
        s_s = sum(c[0] for c in cells); s_n = sum(c[1] for c in cells)
        l_s = sum(c[2] for c in cells); l_n = sum(c[3] for c in cells)
        if not s_n or not l_n or not l_s:
            return None
        return (s_s / s_n) / (l_s / l_n)
    rounds = sorted(per_round)
    c = ratio([per_round[r] for r in rounds])
    if c is None:
        return 1.0, None, None, 0
    rng = random.Random(seed)
    boots = []
    for _ in range(b):
        smp = [per_round[r] for r in rng.choices(rounds, k=len(rounds))]
        v = ratio(smp)
        if v is not None:
            boots.append(v)
    boots.sort()
    lo, hi = boots[int(0.05 * len(boots))], boots[int(0.95 * len(boots)) - 1]
    if lo <= 1.0 <= hi:
        return 1.0, lo, hi, sum(per_round[r][1] for r in rounds)
    return c, lo, hi, sum(per_round[r][1] for r in rounds)


def cautions_before(rows, pid, kickoff_cut):
    return sum(y for (p, key), (_, _, y) in rows.played.items() if p == pid and key in rows_key_before(rows, kickoff_cut))


def rows_key_before(rows, kickoff_cut):
    if not hasattr(rows, "_kb") or rows._kb[0] != kickoff_cut:
        keys = {key for ms in rows.matches.values() for ko, key, _ in ms if ko < kickoff_cut}
        rows._kb = (kickoff_cut, keys)
    return rows._kb[1]


def suspended_next(rows, pid, club, kickoff_cut):
    """True when the player's caution count reached a banning total in the
    club's previous match, before the band's match number."""
    last = rows.club_matches_before(club, kickoff_cut)
    if not last:
        return False
    prev = last[-1]
    _, _, y_prev = rows.played.get((pid, prev[1]), (0, 0, 0))
    if not y_prev:
        return False
    total = cautions_before(rows, pid, kickoff_cut)
    n_next = len(last) + 1
    for count, before in CAUTION_BANDS:
        if total >= count and total - y_prev < count and n_next <= before:
            return True
    return False


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


def v2_pstart(rows, kickoff_cut, out_live=None, flagged=(), chance=None, factor=None, trace=None):
    """{pid: P(start)} for every player with a club at the origin, by the
    pre-registered rules; `trace` collects which rule touched whom."""
    chance = chance or {}
    if factor is None:
        factor = congestion_factor(rows, kickoff_cut)
    c_fac = factor[0]
    out, p_sub = {}, {}
    clubs = defaultdict(list)
    for pid, club in rows.club_of.items():
        clubs[club].append(pid)
    for club, pids in clubs.items():
        nxt = [m for m in rows.matches.get(club, []) if m[0] >= kickoff_cut]
        ko_next = nxt[0][0] if nxt else None
        rest = rest_days(rows, club, ko_next) if ko_next else None
        congested = rest is not None and rest <= REST_SHORT
        for pid in pids:
            ps, psub = base_states(rows, pid, club, kickoff_cut)
            if congested and c_fac != 1.0:
                ps = min(1.0, ps * c_fac)
                if trace is not None:
                    trace["congestion"].add(pid)
            out[pid], p_sub[pid] = ps, psub
        for pid, p in keeper_lock(rows, club, kickoff_cut, flagged).items():
            out[pid] = p
            if trace is not None:
                trace["lock"].add(pid)
        regs, absent = regulars_and_absent(rows, club, kickoff_cut, out_live)
        for pid in absent:
            rep = replacement_for(rows, club, pid, kickoff_cut)
            if rep is None:
                continue
            last = rows.club_matches_before(club, kickoff_cut)
            before_cut = last[-1][0] if out_live is None and last else kickoff_cut
            reg_p = base_states(rows, pid, club, before_cut)[0]
            if out[rep] < reg_p:
                out[rep] = reg_p
                if trace is not None:
                    trace["cover"].add(rep)
        for pid in pids:
            if suspended_next(rows, pid, club, kickoff_cut):
                out[pid] = 0.0
                if trace is not None:
                    trace["suspension"].add(pid)
    for pid in out:
        out[pid] = min(1.0, out[pid] * chance.get(pid, 1.0))
    return out, p_sub


# ---------------------------------------------------------------------------
# 2025/26: the pre-registered test
# ---------------------------------------------------------------------------

def rows_2526(hist, t):
    """Rows at origin t: clubs of the origin, every club match's kickoff,
    results of rounds < t only."""
    c, cm = hist["c"], hist["cm"]
    with open(os.path.join(hist["dir"], "fixtures.csv"), encoding="utf-8", newline="") as fh:
        fixtures = {f["id"]: f for f in csv.DictReader(fh)}
    with open(os.path.join(hist["dir"], "teams.csv"), encoding="utf-8", newline="") as fh:
        short = {tm["id"]: tm["short_name"] for tm in csv.DictReader(fh)}
    matches = defaultdict(list)
    for fid, f in fixtures.items():
        if not f.get("kickoff_time") or not f.get("event"):
            continue
        ko = datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
        matches[short[f["team_h"]]].append((ko, fid, int(f["event"])))
        matches[short[f["team_a"]]].append((ko, fid, int(f["event"])))
    played = {}
    for rnd, rs in hist["raw"].items():
        if rnd >= t:
            continue
        for r in rs:
            played[(int(r["element"]), str(r["fixture"]))] = (H._num(r["minutes"]), 1 if H._num(r.get("starts")) >= 1 else 0,
                                                              int(H._num(r.get("yellow_cards"))))
    club_of = {pid: club for pid in c["players"] for club in [hist["cm"]["by_gw"].get(t, {}).get(pid)] if club}
    pos = {pid: p["pos"] for pid, p in c["players"].items()}
    names = {pid: p["name"] for pid, p in c["players"].items()}
    known = {fid for fid, f in fixtures.items() if f.get("event") and int(f["event"]) < t}
    return Rows(matches, played, club_of, pos, names, known), fixtures, short


def origin_cut(rows, t):
    """The first kickoff of round t: the replay's deadline proxy."""
    kos = [ko for ms in rows.matches.values() for ko, _, ev in ms if ev == t]
    if not kos:
        raise MissingInput(f"no fixture in round {t}")
    return min(kos)


def test_2526(hist_dir, out=print, first=5, last=None, seed=SEED):
    hist = BT.load_2526(hist_dir)
    hist["dir"] = hist_dir
    last = last or hist["through"]
    out(f"S12 TEST  2025/26 GW{first}-{last}: P(start) v2 against the current model (start_probability on the same "
        f"inputs), the recording gate, paired per gameweek; bootstrap over gameweeks B={BT.B}, 90%, seed {seed}")
    out(f"  {'GW':>4} {'n':>5} {'Brier cur':>10} {'Brier v2':>9} {'diff':>8} {'MAE cur':>8} {'MAE v2':>7} {'GK mis cur':>11} {'GK mis v2':>10} {'c':>6} {'touched lock/cover/cong/susp':>30}")
    per = []
    for t in range(first, last + 1):
        rows, fixtures, short = rows_2526(hist, t)
        cut = origin_cut(rows, t)
        c_t = BT.canonical_at(hist, t)
        inp = E.reliability_inputs(E.canonical_through(c_t, t - 1), gws_played=t - 1)
        factor = congestion_factor(rows, cut)
        trace = defaultdict(set)
        v2, _ = v2_pstart(rows, cut, factor=factor, trace=trace)
        pairings = defaultdict(list)
        for m in c_t["team_matches"]:
            if m["event"] == t:
                pairings[m["team"]].append((m["opponent"], m["was_home"]))
        actual_pts = {r["player_id"]: float(r["pts"] or 0) for r in c_t["rows"] if r["event"] == t}
        started = {}
        for r in hist["raw"].get(t, []):
            pid = int(r["element"])
            started[pid] = max(started.get(pid, 0), 1 if H._num(r.get("starts")) >= 1 else 0)
        b_cur, b_v2, mae_cur, mae_v2 = [], [], [], []
        for pid, p in inp["players"].items():
            if p["mins_last4"] < 45 or not pairings.get(p["team"]):
                continue
            y = started.get(pid, 0)
            pc, pv = p["p_start"], v2.get(pid, 0.0)
            b_cur.append((pc - y) ** 2); b_v2.append((pv - y) ** 2)
            fx = pairings[p["team"]]
            x_cur = E.project_reliability(pid, inp, fx)
            inp2 = dict(inp, players={**inp["players"], pid: dict(p, p_start=pv)})
            x_v2 = E.project_reliability(pid, inp2, fx)
            a = actual_pts.get(pid, 0.0)
            mae_cur.append(abs((x_cur or 0.0) - a)); mae_v2.append(abs((x_v2 or 0.0) - a))
        # keeper mismatches: per club with a match in t, the top-P keeper vs who started
        mis_cur = mis_v2 = 0
        for club in pairings:
            ks = [pid for pid, c in rows.club_of.items() if c == club and rows.pos.get(pid) == 1]
            if not ks:
                continue
            top_cur = max(ks, key=lambda k: (inp["players"].get(k, {}).get("p_start", 0.0), -k))
            top_v2 = max(ks, key=lambda k: (v2.get(k, 0.0), -k))
            starters = {k for k in ks if started.get(k, 0)}
            if starters:
                mis_cur += 0 if top_cur in starters else 1
                mis_v2 += 0 if top_v2 in starters else 1
        n = len(b_cur)
        rec = {"gw": t, "n": n, "b_cur": sum(b_cur) / n, "b_v2": sum(b_v2) / n, "mae_cur": sum(mae_cur) / n,
               "mae_v2": sum(mae_v2) / n, "mis_cur": mis_cur, "mis_v2": mis_v2, "c": factor[0], "c_ci": factor[1:3],
               "touched": {k: len(v) for k, v in trace.items()}}
        per.append(rec)
        tc = rec["touched"]
        out(f"  {t:>4} {n:>5} {rec['b_cur']:10.4f} {rec['b_v2']:9.4f} {rec['b_cur'] - rec['b_v2']:+8.4f} {rec['mae_cur']:8.3f} {rec['mae_v2']:7.3f} "
            f"{mis_cur:>11} {mis_v2:>10} {factor[0]:6.3f} {tc.get('lock', 0):>8}/{tc.get('cover', 0)}/{tc.get('congestion', 0)}/{tc.get('suspension', 0)}")
    d_brier = [r["b_cur"] - r["b_v2"] for r in per]
    d_mae = [r["mae_v2"] - r["mae_cur"] for r in per]
    bb = BT.bootstrap_mean(d_brier, seed=seed)
    bm = BT.bootstrap_mean(d_mae, seed=seed)
    mis_c, mis_v = sum(r["mis_cur"] for r in per), sum(r["mis_v2"] for r in per)
    a_ok = bb["mean"] >= PASS_BRIER and bb["lo"] > 0
    b_ok = bm["mean"] <= MAE_SLACK
    c_ok = mis_v <= mis_c
    out(f"  (a) Brier improvement current - v2: {bb['mean']:+.4f} [{bb['lo']:+.4f}, {bb['hi']:+.4f}] n={bb['n']}; bar >= {PASS_BRIER} with lower bound > 0: {'PASS' if a_ok else 'FAIL'}")
    out(f"  (b) bottomup MAE v2 - current: {bm['mean']:+.4f} [{bm['lo']:+.4f}, {bm['hi']:+.4f}]; bar <= +{MAE_SLACK}: {'PASS' if b_ok else 'FAIL'}")
    out(f"  (c) keeper-starter mismatches: current {mis_c}, v2 {mis_v}; bar v2 <= current: {'PASS' if c_ok else 'FAIL'}")
    out(f"  pre-registered result: {'PASS' if (a_ok and b_ok and c_ok) else 'FAIL'} (all three must hold)")
    return {"per": per, "brier": bb, "mae": bm, "mis": (mis_c, mis_v), "pass": a_ok and b_ok and c_ok}


# ---------------------------------------------------------------------------
# live
# ---------------------------------------------------------------------------

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


def load_overrides(path=OVERRIDES):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh)]


def live(data_dir, out=print, now=None, overrides_path=OVERRIDES, out_dir=None):
    now = now or datetime.now(timezone.utc)
    d, path = CH.newest_export(data_dir)
    rows = rows_2627(data_dir, d)
    c = sqlite3.connect(f"file:{os.path.join(data_dir, 'fpl.sqlite')}?mode=ro", uri=True)
    deadlines = {ev: datetime.fromisoformat(dl.replace("Z", "+00:00")) for ev, dl in c.execute("select id, deadline_time from events")}
    c.close()
    upcoming = sorted((dl, ev) for ev, dl in deadlines.items() if dl > now)
    if not upcoming:
        raise MissingInput("no deadline after now")
    dl, target = upcoming[0]
    flagged = {p["id"] for p in d["all_players"] if p["status"] != "a"}
    chance = {p["id"]: E.chance_of_playing(p) / 100.0 for p in d["all_players"]}
    factor = congestion_factor(rows, dl)
    trace = defaultdict(set)
    v2, p_sub = v2_pstart(rows, dl, out_live=flagged, flagged=flagged, chance=chance, factor=factor, trace=trace)
    applied = []
    for o in load_overrides(overrides_path):
        try:
            if int(o["gw"]) == target and int(o["player"]) in v2:
                v2[int(o["player"])] = float(o["p_start"]); applied.append(o)
        except (KeyError, ValueError):
            raise MissingInput(f"malformed override row: {o}")
    out(f"MINUTES V2 LIVE  GW{target} (deadline {dl:%Y-%m-%d %H:%M} UTC) from {os.path.basename(path)} and fpl.sqlite; "
        f"congestion factor {factor[0]:.3f}" + (f" [{factor[1]:.3f}, {factor[2]:.3f}]" if factor[1] is not None else "") +
        f"; touched: lock {len(trace['lock'])}, cover {len(trace['cover'])}, congestion {len(trace['congestion'])}, suspension {len(trace['suspension'])}; "
        f"{len(applied)} overrides applied; information only")
    cur = {p["id"]: E.start_probability(p, d["gameweek"]) for p in d["all_players"]}
    by_id = {p["id"]: p for p in d["all_players"]}
    out(f"  {'player':<18}{'team':>5}{'pos':>4}{'current':>8}{'v2':>6}{'P(sub)':>7}  rule")
    for pid in sorted(v2, key=lambda p: (-abs(v2[p] - cur.get(p, 0.0)), p))[:40]:
        p = by_id.get(pid, {})
        rule = ", ".join(k for k in ("lock", "cover", "congestion", "suspension") if pid in trace[k])
        if any(int(o["player"]) == pid for o in applied):
            rule = (rule + ", " if rule else "") + "override"
        out(f"  {p.get('web_name', pid):<18}{p.get('team', rows.club_of.get(pid, '?')):>5}{BT.POS_NAME.get(rows.pos.get(pid), '?'):>4}"
            f"{cur.get(pid, 0.0):8.2f}{v2[pid]:6.2f}{p_sub.get(pid, 0.0):7.2f}  {rule}")
    if applied and out_dir:
        log = os.path.join(out_dir, OVERRIDES_LOG)
        new = not os.path.exists(log)
        with open(log, "a", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["applied_at_utc", "gw", "player", "p_start", "model_p_start", "reason", "timestamp_utc"])
            if new:
                w.writeheader()
            for o in applied:
                pid = int(o["player"])
                model_p = v2_pstart(rows, dl, out_live=flagged, flagged=flagged, chance=chance, factor=factor)[0].get(pid, 0.0)
                w.writerow({"applied_at_utc": now.isoformat(timespec="seconds"), "gw": target, "player": pid, "p_start": o["p_start"],
                            "model_p_start": f"{model_p:.4f}", "reason": o.get("reason", ""), "timestamp_utc": o.get("timestamp_utc", "")})
    return {"target": target, "v2": v2, "current": cur, "applied": applied, "factor": factor}


def score_overrides(data_dir, out=print, out_dir=None):
    log = os.path.join(out_dir or os.path.join(ROOT, "tools", "out"), OVERRIDES_LOG)
    if not os.path.exists(log):
        raise MissingInput(f"{log} is missing: no override has been applied")
    settled = BT.load_2627(data_dir)["settled"]
    c = sqlite3.connect(f"file:{os.path.join(data_dir, 'fpl.sqlite')}?mode=ro", uri=True)
    started = {(pid, ev): (1 if s else 0) for pid, ev, s in c.execute("select player_id, event, starts from player_gw")}
    c.close()
    with open(log, encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh)]
    scored = [(r, started.get((int(r["player"]), int(r["gw"])), 0)) for r in rows if int(r["gw"]) in settled]
    out(f"OVERRIDES SCORED  {len(scored)} of {len(rows)} applied overrides on settled gameweeks")
    if scored:
        b_o = sum((float(r["p_start"]) - y) ** 2 for r, y in scored) / len(scored)
        b_m = sum((float(r["model_p_start"]) - y) ** 2 for r, y in scored) / len(scored)
        out(f"  Brier override {b_o:.4f} vs model {b_m:.4f} ({'override better' if b_o < b_m else 'model better or equal'})")
        for r, y in scored:
            out(f"  GW{r['gw']} player {r['player']}: override {float(r['p_start']):.2f}, model {float(r['model_p_start']):.2f}, started {y}; {r['reason']}")
    return scored


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    ap.add_argument("--overrides", default=OVERRIDES)
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--score-overrides", action="store_true")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        if args.test:
            test_2526(args.hist, out)
            name = "minutes_v2_test_2025-26.txt"
        elif args.live:
            live(args.data, out, overrides_path=args.overrides, out_dir=args.out)
            name = "minutes_v2_live.txt"
        elif args.score_overrides:
            score_overrides(args.data, out, out_dir=args.out)
            name = "minutes_v2_overrides_scored.txt"
        else:
            ap.print_help()
            return 0
    except MissingInput as e:
        print(f"MISSING INPUT: {e} - stopping; nothing is substituted")
        return 2
    with open(os.path.join(args.out, name), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
