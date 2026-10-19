"""fpl_xpr.py - the runner's copy of tools/xp_v2_replay.py, the part W3 needs:
the S6b terms xp_v2 as tested reads (W3; prereg/W3.md, Part F item F-B).

Every definition below is copied verbatim from tools/xp_v2_replay.py by its syntax
tree, module aliases kept and pointed at the runner's copies, so the
runner never imports tools/; tests/test_W3.py holds the copies to the
tools. Standard library only.
"""
import fpl_edge as E
import fpl_hist as H
import fpl_xpv as XV
from collections import defaultdict


GATE_MINS = 45                      # the recording gate both models share (mins_last4)


SUB_WINDOW = XV.WINDOW              # S6: P(sub) over the last min(4, t-1) rounds


BONUS_TOP = 0.8                     # project_xg: top ICT ~0.8 bonus a gameweek


class MissingInput(Exception):
    pass


def sub_inputs_2526(by_round, t, pos_of, window=SUB_WINDOW):
    """S6's sub_inputs on the raw rows: P(sub) per player over the last
    min(window, t-1) rounds (appearances without a start / the window) and
    E[pts | sub] per position over every round < t (official 2025/26
    points of sub appearances, what the model saw)."""
    n = min(window, t - 1)
    apps = defaultdict(lambda: [0, 0])
    sub_pts = defaultdict(list)
    for rnd in range(1, t):
        for r in by_round.get(rnd, []):
            pid = int(r["element"])
            mins, starts = H._num(r.get("minutes")), H._num(r.get("starts"))
            if mins > 0 and not starts:
                sub_pts[pos_of.get(pid)].append(H._num(r.get("total_points")))
            if rnd > t - 1 - n and mins > 0:
                apps[pid][0] += 1
                apps[pid][1] += 1 if starts else 0
    p_sub = {pid: (a - s) / n for pid, (a, s) in apps.items()} if n else {}
    e_sub = {p: (sum(v) / len(v) if v else 0.0) for p in (1, 2, 3, 4) for v in [sub_pts.get(p, [])]}
    return p_sub, e_sub


def ict_percentile(by_round, t):
    """The player's percentile of season ICT (merged_gw's ict_index, rounds
    < t) among players with minutes; 0.5 with one player."""
    tot = defaultdict(float)
    for rnd in range(1, t):
        for r in by_round.get(rnd, []):
            if H._num(r.get("minutes")) > 0:
                tot[int(r["element"])] += H._num(r.get("ict_index"))
    order = sorted(tot, key=lambda p: (tot[p], p))
    n = len(order)
    return {pid: (i / (n - 1) if n > 1 else 0.5) for i, pid in enumerate(order)}


def defcon_rates(by_round, t, pos_of):
    """2 x the hit rate over the player's 60+-minute training matches at the
    current thresholds (defcon_expectation's rule; 0 without a threshold)."""
    played = defaultdict(lambda: [0, 0])
    for rnd in range(1, t):
        for r in by_round.get(rnd, []):
            pid = int(r["element"])
            thr = E.DEFCON_THRESHOLD.get(pos_of.get(pid))
            if not thr or H._num(r.get("minutes")) < 60:
                continue
            played[pid][0] += 1
            played[pid][1] += 1 if H._num(r.get("defensive_contribution")) >= thr else 0
    return {pid: 2.0 * h / n for pid, (n, h) in played.items() if n}


def xg_half(pos, xg_start, xa_start, cs_pts, defcon_pts, ict_pct):
    """project_xg's terms conditional on starting: appearance 2, goals,
    assists, the clean sheet (in points already), DEFCON (in points), bonus."""
    return 2.0 + xg_start * E.GOAL_VALUE.get(pos, 5) + xa_start * 3.0 + cs_pts + defcon_pts + BONUS_TOP * ict_pct
