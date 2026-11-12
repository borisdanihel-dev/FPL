"""fpl_realised.py - the runner's copy of tools/xp_v2_replay.py, the part W3 needs:
S6c's realised points on a squad and the recorded rows, for the
REALISED section (apart from fpl_xpr, so the record never imports the
chip modules) (W3; prereg/W3.md, Part F item F-B).

Every definition below is copied verbatim from tools/xp_v2_replay.py by its syntax
tree, module aliases kept and pointed at the runner's copies, so the
runner never imports tools/; tests/test_W3.py holds the copies to the
tools. Standard library only.
"""
import fpl_chips as CH
import fpl_edge as E


def realised_on(rows, proj, actual):
    """planner.Replay.realised on given outcomes {pid: (points, minutes)}: the
    XI by projection, rule_autosubs on the minutes, the captain doubled."""
    proj = {r["id"]: proj.get(r["id"], 0.0) for r in rows}
    xi, bench, gk = CH.xi_and_bench([dict(r) for r in rows], proj)
    lineup = [{"slot": s, "pos": r["pos"], "id": r["id"], "minutes": actual.get(r["id"], (0, 0))[1]}
              for s, r in enumerate(xi, 1)]
    lineup += [{"slot": s, "pos": r["pos"], "id": r["id"], "minutes": actual.get(r["id"], (0, 0))[1]}
               for s, r in enumerate([gk] + list(bench), 12)]
    pts = sum(actual.get(r["id"], (0.0, 0))[0] for r in xi)
    for cand, gone in E.rule_autosubs(lineup):
        pts += actual.get(cand["id"], (0.0, 0))[0] - actual.get(gone["id"], (0.0, 0))[0]
    cap = max(xi, key=lambda r: (r["proj"], -r["id"]))
    return pts + actual.get(cap["id"], (0.0, 0))[0], cap["id"]


def recorded_own(log_rows, event, d_ev):
    """{pid: predicted} of source own for `event` as every reader takes it,
    fpl_edge.forecasts: the gameweek's last snapshot made before its
    deadline (the deadlines in d_ev); and that snapshot's made_at."""
    rows = [r for r in E.forecasts(log_rows, d_ev) if r["source"] == "own" and int(r["event"]) == event]
    if not rows:
        return {}, None
    return {int(r["player_id"]): float(r["predicted"]) for r in rows}, rows[0]["made_at"]
