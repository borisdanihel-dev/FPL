"""worklog/checkpoint_gw10/checkpoint.py - the GW10 checkpoint's paired decision metric (prereg/FJ.md; Boris's
rulings of Thu 12 Nov, point B). Report only; nothing in the runner, the models or the decisions changes.
Standard library only.

    python -I checkpoint.py --code DIR --data DIR --out DIR [--tie slot|id]

  --code  a clean worktree of master at the prereg's commit: its fpl_squad, fpl_realised, fpl_chips, fpl_edge and
          fpl_bt are imported unchanged, its git history holds the bundle commits, and its commit goes in run.txt
          (without --code, as when tests/test_FJ.py imports this file: the repository this file is in)
  --data  a copy of the data worktree (fpl.sqlite, projection_log.csv)
  --tie   how equal forecasts are ordered before realised_on: 'slot' (our picks in slot order; the GW10 run as
          pinned, the default) or 'id' (the lower player id first; the GW15 run, prereg/FJ.md, rulings of Thu 12
          Nov night). The other order is printed beside it as information.

method (pinned in prereg/FJ.md before this ran)
  - lockdown guard per gameweek: data_checked = 1 and every fixture finished = 1;
  - our actual 15: entry 3073318's picks;
  - xp_v2: worklog/gw_pass/gw<g>/xp_v2_all.csv at the bundle commit the ruling names (GW8 6034baa, GW9 e708c91,
    GW10 c0c6c3f), read and checked by fpl_squad.bundle_csv (before the deadline, run.txt's SHA-256);
  - own: its last snapshot before the deadline in projection_log.csv (fpl_squad.recorded);
  - each model's XI, bench and captain and its realised points: fpl_realised.realised_on, unchanged;
  - d = realised(xp_v2) - realised(own) per gameweek; fpl_bt.bootstrap_mean (unit gameweek, B 10000, seed
    20261018, 90%); revert rule: own returns if the 90% upper bound is below 0.
"""
import argparse
import hashlib
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone


def _arg(argv, name):
    for i, x in enumerate(argv):
        if x == name and i + 1 < len(argv):
            return argv[i + 1]
        if x.startswith(name + "="):
            return x.split("=", 1)[1]
    sys.exit(f"{name} is required")


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE = os.path.abspath(_arg(sys.argv[1:], "--code")) if "--code" in " ".join(sys.argv[1:]) else ROOT
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(CODE, "tools"))
import fpl_bt as BT                                               # noqa: E402
import fpl_chips as CH                                            # noqa: E402
import fpl_edge as E                                              # noqa: E402
import fpl_realised as RL                                         # noqa: E402
import fpl_squad as SQ                                            # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

ENTRY = 3073318
GWS = (8, 9, 10)
BUNDLE = {8: "6034baa", 9: "e708c91", 10: "c0c6c3f"}          # the ruling's commits
POS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def _utc(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def choice(squad, proj, actual):
    """The display of realised_on's choice: (XI, bench in order with the keeper first, captain, autosubs)."""
    p = {r["id"]: proj.get(r["id"], 0.0) for r in squad}
    xi, bench, gk = CH.xi_and_bench([dict(r) for r in squad], p)
    lineup = [{"slot": s, "pos": r["pos"], "id": r["id"], "minutes": actual.get(r["id"], (0, 0))[1]}
              for s, r in enumerate(xi, 1)]
    lineup += [{"slot": s, "pos": r["pos"], "id": r["id"], "minutes": actual.get(r["id"], (0, 0))[1]}
               for s, r in enumerate([gk] + list(bench), 12)]
    subs = [(c["id"], g["id"]) for c, g in E.rule_autosubs(lineup)]
    cap = max(xi, key=lambda r: (r["proj"], -r["id"]))
    return xi, [gk] + list(bench), cap["id"], subs


def ordered(squad, tie):
    """The 15 as realised_on receives them: as given (slot order) or by player id (the lower id first)."""
    if tie not in ("slot", "id"):
        raise ValueError(f"tie must be 'slot' or 'id', not {tie!r}")
    return list(squad) if tie == "slot" else sorted(squad, key=lambda r: r["id"])


def score(squad, own, xp, actual, tie="slot"):
    """(own's realised points, its captain, xp_v2's, its captain) on our 15 under one tie order."""
    sq = ordered(squad, tie)
    pts_own, cap_own = RL.realised_on(sq, own, actual)
    pts_v2, cap_v2 = RL.realised_on(sq, xp, actual)
    return pts_own, cap_own, pts_v2, cap_v2


def paired(own_pts, v2_pts):
    """d per gameweek: realised(xp_v2) - realised(own)."""
    return [v - o for o, v in zip(own_pts, v2_pts)]


def verdict(boot):
    """The revert rule (S6b acceptance, point 3): own returns only if the 90% upper bound is below 0."""
    return "own returns" if boot["hi"] < 0 else "xp_v2 stays"


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--tie", choices=("slot", "id"), default="slot")
    a = ap.parse_args(argv)
    run_ = Run("worklog/checkpoint_gw10/checkpoint.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    db_path, log_path = os.path.join(a.data, "fpl.sqlite"), os.path.join(a.data, E.LOG_PATH)
    for p in (db_path, log_path):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing")
    with open(os.path.abspath(__file__), "rb") as fh:
        me_sha = hashlib.sha256(fh.read()).hexdigest()
    with open(db_path, "rb") as fh:
        db_sha = hashlib.sha256(fh.read()).hexdigest()
    with open(log_path, "rb") as fh:
        log_sha = hashlib.sha256(fh.read()).hexdigest()
    log_rows = E.read_log(log_path)
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    events = list(db.execute("SELECT id, deadline_time, finished, data_checked FROM events ORDER BY id"))
    d_ev = {"events": [{"event": ev, "deadline_time": dl} for ev, dl, _, _ in events]}
    deadline = {ev: _utc(dl) for ev, dl, _, _ in events if dl}
    checked = {ev: chk for ev, _, _, chk in events}
    web = dict(db.execute("SELECT id, web_name FROM players"))

    out("GW10 CHECKPOINT: THE PAIRED own v xp_v2 DECISION METRIC OVER GW8-10 (prereg/FJ.md; rulings of Thu 12 Nov, B)")
    out(f"  code {run_.commit[:7]} (modified tracked files {run_.dirty}); script sha256 {me_sha}")
    out(f"  data: fpl.sqlite sha256 {db_sha[:16]}..., projection_log.csv sha256 {log_sha[:16]}... ({len(log_rows)} rows); "
        f"generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out("  our actual 15 each gameweek (entry 3073318's picks); each model's XI by its xP, bench in forecast order, the")
    out("  captain = highest xP in its XI (doubled), rule_autosubs on realised minutes: fpl_realised.realised_on, unchanged;")
    out("  no vice promotion, no chips. d = realised(xp_v2) - realised(own).")

    other = "id" if a.tie == "slot" else "slot"
    d, per, alt = [], [], []
    for g in GWS:
        n_fx, n_fin = db.execute("SELECT COUNT(*), COALESCE(SUM(finished = 1), 0) FROM fixtures WHERE event = ?",
                                 (g,)).fetchone()
        if not (checked.get(g) == 1 and n_fx and n_fin == n_fx):
            raise MissingInput(f"GW{g} is not locked down (data_checked {checked.get(g)}, {n_fin} of {n_fx} finished)")
        picks = db.execute("SELECT p.player_id, pl.position FROM picks p JOIN players pl ON pl.id = p.player_id "
                           "WHERE p.entry_id = ? AND p.event = ? ORDER BY p.position", (ENTRY, g)).fetchall()
        if len(picks) != 15:
            raise MissingInput(f"GW{g}: {len(picks)} picks, not 15")
        squad = [{"id": pid, "pos": pos} for pid, pos in picks]
        actual = {pid: (float(pts or 0), float(mins or 0)) for pid, pts, mins in db.execute(
            "SELECT player_id, total_points, minutes FROM player_gw WHERE event = ?", (g,))}
        own, made = SQ.recorded(log_rows, "own", g, d_ev)
        if not own:
            raise MissingInput(f"GW{g}: no own rows before the deadline")
        b = SQ.bundle_csv(CODE, g, deadline[g])
        if b is None:
            raise MissingInput(f"GW{g}: no bundle xp_v2_all.csv passes fpl_squad.bundle_csv's checks")
        h, xp, tool = b
        if not h.startswith(BUNDLE[g]):
            raise MissingInput(f"GW{g}: the reader picks bundle {h[:7]}, not the ruling's {BUNDLE[g]}")
        absent = [r["id"] for r in squad if r["id"] not in xp]
        if absent:
            raise MissingInput(f"GW{g}: {len(absent)} of our 15 not in the bundle's xp_v2_all.csv")
        no_own = [r["id"] for r in squad if r["id"] not in own]
        xp15 = {r["id"]: xp[r["id"]] for r in squad}
        pts_own, cap_own, pts_v2, cap_v2 = score(squad, own, xp15, actual, a.tie)
        d.append(pts_v2 - pts_own)
        per.append((g, pts_own, pts_v2, cap_own, cap_v2))
        alt.append(score(squad, own, xp15, actual, other))
        squad = ordered(squad, a.tie)                                     # the display follows the run's order

        out("")
        out(f"GW{g}  deadline {deadline[g]:%Y-%m-%d %H:%M} UTC; locked down (data_checked 1, {n_fin}/{n_fx} finished)")
        out(f"  own: snapshot made {made}; {15 - len(no_own)} of our 15 with a row"
            + (f" (no row, counted 0: {', '.join(web.get(i, str(i)) for i in no_own)})" if no_own else ""))
        out(f"  xp_v2: bundle {h[:7]} (tools {tool[:7]}), fpl_squad.bundle_csv's checks passed")
        own_c = choice(squad, own, actual)
        v2_c = choice(squad, {r["id"]: xp[r["id"]] for r in squad}, actual)
        out(f"  {'player':<16} {'pos':<4} {'own':>6} {'xp_v2':>6} {'pts':>4} {'min':>4}   own role   xp_v2 role")
        roles = []
        for model, (xi, bench, cap, subs) in (("own", own_c), ("xp_v2", v2_c)):
            role = {r["id"]: "XI" for r in xi}
            role.update({r["id"]: f"bench {k}" for k, r in enumerate(bench, 1)})
            role[cap] = "XI (C)"
            for cin, cout in subs:
                role[cin] += " sub on"
                role[cout] += " sub off"
            roles.append(role)
        for r in sorted(squad, key=lambda r: (r["pos"], -xp[r["id"]])):
            i = r["id"]
            o = f"{own[i]:6.2f}" if i in own else "     -"
            pts, mins = actual.get(i, (0.0, 0.0))
            out(f"  {web.get(i, str(i)):<16} {POS[r['pos']]:<4} {o} {xp[i]:6.2f} {pts:4.0f} {mins:4.0f}   "
                f"{roles[0][i]:<10} {roles[1][i]}")
        out(f"  realised: own {pts_own:.0f} (captain {web.get(cap_own, cap_own)}), xp_v2 {pts_v2:.0f} "
            f"(captain {web.get(cap_v2, cap_v2)}); d = {pts_v2 - pts_own:+.0f}")
    db.close()

    boot = BT.bootstrap_mean(d)
    assert d == paired([p[1] for p in per], [p[2] for p in per])
    out("")
    out("=" * 100)
    out("SUMMARY")
    out("=" * 100)
    out(f"  {'GW':<4} {'own':>5} {'xp_v2':>6} {'d':>5}   captains (own / xp_v2)")
    for (g, po, pv, co, cv), x in zip(per, d):
        out(f"  {g:<4} {po:5.0f} {pv:6.0f} {x:+5.0f}   {web.get(co, co)} / {web.get(cv, cv)}")
    out(f"  total {sum(p[1] for p in per):.0f} v {sum(p[2] for p in per):.0f}; mean d = {boot['mean']:+.2f} a gameweek, "
        f"90% [{boot['lo']:+.2f}, {boot['hi']:+.2f}] (bootstrap over {boot['n']} gameweeks, B {BT.B}, seed {BT.SEED}); "
        f"two-sided bootstrap p {boot['p']:.3f}")
    out(f"  revert rule (S6b acceptance, point 3): own returns if the 90% upper bound is below 0. "
        f"Upper bound {boot['hi']:+.2f}: {verdict(boot)}. Reported only; Boris decides.")
    out("  with three gameweeks the percentile interval can only take values from the 10 resample multisets; it is coarse.")
    d_alt = paired([x[0] for x in alt], [x[2] for x in alt])
    b_alt = BT.bootstrap_mean(d_alt)
    out(f"  tie order: this run '{a.tie}' ({'our picks in slot order' if a.tie == 'slot' else 'the lower player id first'}); "
        f"information, the other order '{other}': own {', '.join(f'{x[0]:.0f}' for x in alt)}, "
        f"xp_v2 {', '.join(f'{x[2]:.0f}' for x in alt)}, d {', '.join(f'{x:+.0f}' for x in d_alt)}; "
        f"mean {b_alt['mean']:+.2f}, 90% [{b_alt['lo']:+.2f}, {b_alt['hi']:+.2f}]: {verdict(b_alt)}")

    os.makedirs(a.out, exist_ok=True)
    path_out = os.path.join(a.out, "checkpoint.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MissingInput as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
