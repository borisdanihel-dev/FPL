"""worklog/gw_pass/gw11/bb_moves.py - the GW11 transfer tables on the planner's score (Boris, answers of Thu 19 Nov
night, GW11 deadline pass point b; information only, read-only; no tool change, master stays the bundle commit).
Adapted from worklog/gw_pass/gw10/bb_moves.py. Standard library only.

    python -I bb_moves.py --code DIR --data DIR --hist DIR [--csv FILE] --out DIR

  --code   a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --csv    the bundle's xp_v2_all.csv, checked against the gated matrix's first column

matrix     the planner's xp_v2 horizon matrix (builder.live_matrix, as planner_live runs it). Two cases:
           gate     as the bundle: a player whose status is not 'a' has no value in any week (Thiago s, Thomas d: 0)
           lifted   the same, with two status gates lifted (Boris: "with Thiago lifted from GW14 and Thomas at his
                    chance (information, as in GW10)"):
                      Thiago  0 in GW11-13; from GW14 his gate lifted and taken as available (chance 100): P(start) =
                              his starts in the last four / 4, P(sub) unscaled - his own model numbers otherwise
                      Thomas  his gate lifted at the export's chance in GW11 (50% on 19 Nov, 75% on 20 Nov), then as
                              normal (chance 100) - the FM 'd' rule (Boris, answers on FM of Thu 19 Nov late); information
                              beside it: his chance in every week
score      S8's rank_plans and evaluate as planner_live runs them (no hits, decay 0.85, Boris's schedule), with Boris's
           2 free transfers and bank 0.9; the Bench Boost score is planner_live.bb_rescore: week t's gain is all 15 by
           xP plus the captain (the bench at full weight)
named      Thiago + Thomas out; Thiago out only (roll one)
"""
import argparse
import csv
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone


def _arg(argv, name):
    for i, x in enumerate(argv):
        if x == name and i + 1 < len(argv):
            return argv[i + 1]
        if x.startswith(name + "="):
            return x.split("=", 1)[1]
    sys.exit(f"{name} is required")


CODE = os.path.abspath(_arg(sys.argv[1:], "--code"))
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(CODE, "tools"))
import builder as B                                               # noqa: E402
import capflag as CF                                              # noqa: E402
import chips as CH                                                # noqa: E402
import fpl_edge as E                                              # noqa: E402
import planner as PL                                              # noqa: E402
import planner_live as PLV                                        # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run, sha256_of                             # noqa: E402

DECAY = PLV.DECAY
SCHED = PL.SCHEDULES[PLV.SCHEDULE]
FTS = 2                                   # Boris: 2 free transfers this week
THIAGO_FROM = 14                         # Boris: "Thiago is banned GW11-13 (back GW14)"
NAMED = (("Thiago", "Thomas"), ("Thiago",))


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def lifted_matrix(data_dir, hist_root, weeks_n, lifts):
    """builder.live_matrix with status gates lifted per player and week; nothing else changed. lifts: {pid: (first,
    normal_from)}: the gate is lifted in weeks >= first (None: every week); from normal_from (None: never) the player
    is taken as available (chance 100): P(start) = starts in the last four / the window, P(sub) unscaled; before it
    the export's chance scales both, as the model does. Returns (weeks, the detail of every week, the export d)."""
    now = datetime.now(timezone.utc)
    OL, XL, SH, XV = B.OL, B.XL, B.SH, B.XV
    _, deadlines, fixtures, _, _ = OL.sqlite_tables(data_dir)
    dl, target = sorted((dl, ev) for ev, dl in deadlines.items() if dl > now)[0]
    d, path = CH.newest_export(data_dir)
    snap = OL.newest_snapshot(data_dir, dl)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    model = XL._model(fixtures, dl)
    prior = XL.load_prior(hist_root)
    names, _ = XL.prior_names(os.path.join(data_dir, "fpl.sqlite"), os.path.join(hist_root, "2026-27", "elements_positions.csv"),
                              os.path.join(hist_root, XL.PRIOR_SEASON))
    c = E.canonical_through(E.canonical_from_export(d), d["gameweek"])
    gws = d["gameweek"]
    inp = E.reliability_inputs(c, gws_played=gws)
    starts4 = Counter()
    for r in c["rows"]:
        if gws - min(4, gws) < r["event"] <= gws:
            starts4[r["player_id"]] += r["starts"] or 0
    by_round, rows = XL.export_rows(d)
    tot = SH.team_totals(rows, {})
    gate0 = {int(p["id"]): p["status"] == "a" for p in d["all_players"]}
    chance0 = XV.chance_scale(d)
    weeks, details = [], []
    for u in range(target, target + weeks_n):
        fx = XL.target_fixtures(d, u)
        lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}

        def fixtures_of(team, fx=fx):
            return [(fid, f) for fid, f in fx.items() if team in (f["home"], f["away"])]

        def lam_team(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_home"] if team == fx[fid]["home"] else lam[fid][0]["lambda_away"]

        def lam_opp(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_away"] if team == fx[fid]["home"] else lam[fid][0]["lambda_home"]
        gate, chance, players = dict(gate0), dict(chance0), dict(inp["players"])
        for pid, (first, normal_from) in lifts.items():
            if first is not None and u < first:
                continue
            gate[pid] = True
            if normal_from is not None and u >= normal_from and pid in players:
                players[pid] = dict(players[pid], p_start=min(1.0, starts4[pid] / max(1, min(4, gws))))
                chance[pid] = 1.0
        xp, det = XL.core(dict(inp, players=players), names, by_round, target, rows, {}, tot, prior, fixtures_of,
                          lam_team, lam_opp, ict=XL.ict_live(d), chance=chance, gate=gate)
        weeks.append(xp)
        details.append(det)
    return weeks, details, d


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--hist", "--out"):
        ap.add_argument(name, required=True)
    ap.add_argument("--csv")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw11/bb_moves.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    d, path, target, XP, srcs, p_start, snap = PLV.live_inputs(a.data, a.hist)
    weeks = list(range(target, target + len(XP)))
    squad = CH.my_squad(d)
    budget, why = E.selling_budget(d)
    if budget is None:
        raise MissingInput(f"no budget: {why}")
    bank = budget - sum(r["selling"] for r in squad)
    market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"],
               "status": p["status"]} for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
    by_id = {p["id"]: p for p in d["all_players"]}

    def ours(name):
        m = [r for r in squad if r["name"] == name]
        if len(m) != 1:
            raise MissingInput(f"{name} is not one player of our 15")
        return m[0]
    data_commit = subprocess.run(["git", "-C", a.data, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    out(f"TRANSFER TABLES  GW{target} (Boris, Thu 19 Nov night, GW11 pass point b); information, read-only, no tool change")
    out(f"  data {data_commit[:7]}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {sha256_of(os.path.abspath(__file__))}; generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  matrix: the planner's xp_v2 horizon matrix GW{weeks[0]}-{weeks[-1]} (builder.live_matrix; odds "
        f"{snap or 'none before the deadline'} where they price the fixture, else the fallback)")
    if a.csv:
        csv_rows = list(csv.DictReader(open(a.csv, encoding="utf-8", newline="")))
        bad = [r["id"] for r in csv_rows if abs(float(r["xp_v2"]) - XP[0].get(int(r["id"]), 0.0)) > 1e-9]
        out(f"  check: the GW{target} column against the bundle's {os.path.basename(a.csv)}: {len(csv_rows) - len(bad)} of "
            f"{len(csv_rows)} players equal" + ("" if not bad else f"; differ: {', '.join(bad[:10])}"))
    thiago, thomas = ours("Thiago"), ours("Thomas")
    same, _, _ = lifted_matrix(a.data, a.hist, len(XP), {})
    out(f"  check: this script's copy of the matrix, no gate lifted, equals the planner's: "
        f"{all(same[t] == XP[t] for t in range(len(XP)))}")
    lifts = {thiago["id"]: (THIAGO_FROM, THIAGO_FROM), thomas["id"]: (None, target + 1)}
    every = {thiago["id"]: (THIAGO_FROM, THIAGO_FROM), thomas["id"]: (None, None)}
    XL_, det, _ = lifted_matrix(a.data, a.hist, len(XP), lifts)
    XE_, dete, _ = lifted_matrix(a.data, a.hist, len(XP), every)
    moved = [(t, pid) for M in (XL_, XE_) for t in range(len(XP)) for pid in set(XP[t]) | set(M[t])
             if pid not in lifts and XP[t].get(pid) != M[t].get(pid)]
    out(f"  check: lifting the two gates (both versions) moves no other player's value: {not moved}")
    ban_end = re.search(r"Suspended until (\d{1,2} [A-Z][a-z]{2})", by_id[thiago["id"]].get("news", ""))
    bre = [f for f in d.get("fixtures_next6") or [] if thiago["team"] in (f["home"], f["away"])]
    first_ok = next((f["event"] for f in sorted(bre, key=lambda f: f["kickoff_time"])
                     if ban_end and datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00")).date()
                     >= datetime.strptime(f"{ban_end.group(1)} {datetime.now(timezone.utc).year}", "%d %b %Y").date()), None)
    out(f"  check: Thiago's news names the ban's end ({ban_end.group(1) if ban_end else 'none'}); {thiago['team']}'s first fixture "
        f"on or after it is in GW{first_ok}; the lift starts in GW{THIAGO_FROM} (Boris's GW14)")
    for name in ("Thiago", "Thomas"):
        r = ours(name)
        p = by_id[r["id"]]
        out(f"  {name} ({r['team']}, selling {r['selling']:.1f}): status {p['status']}, chance_next_round {p.get('chance_next_round')}, "
            f"news \"{p.get('news', '')}\"; gate: " + (", ".join(f"GW{u} {XP[t][r['id']]:.2f}" for t, u in enumerate(weeks) if r["id"] in XP[t])
                                                      or "no value in any week"))
        if name == "Thomas":
            out(f"    every week at his chance (information): " + ", ".join(f"GW{u} {XE_[t].get(r['id'], 0.0):.2f}" for t, u in enumerate(weeks)))
        out(f"    lifted: " + ", ".join(f"GW{u} {XL_[t].get(r['id'], 0.0):.2f}" for t, u in enumerate(weeks))
            + (f"  (P(start) from GW{THIAGO_FROM} {det[weeks.index(THIAGO_FROM)][r['id']]['p_start']:.2f})" if name == "Thiago"
               and THIAGO_FROM in weeks and r["id"] in det[weeks.index(THIAGO_FROM)] else
               f"  (P(start) {det[0][r['id']]['p_start']:.2f}, P(sub) {det[0][r['id']]['p_sub']:.2f})" if r["id"] in det[0] else ""))
    out(f"  score: S8's rank_plans and evaluate ({FTS} free transfers, no hits, decay {DECAY}, Boris's schedule {SCHED}); bank {bank:.1f}; "
        f"Bench Boost = planner_live.bb_rescore (GW{target}'s gain: all 15 by xP + the captain)")
    for label, M in (("UNDER THE GATE (Thiago, Thomas 0)", XP),
                     (f"LIFTED (Thiago from GW{THIAGO_FROM} at chance 100; Thomas at his chance in GW{target}, then as normal)", XL_),
                     (f"INFORMATION: LIFTED WITH THOMAS AT HIS CHANCE IN EVERY WEEK (Thiago as above)", XE_)):
        scored, _ = PL.rank_plans(squad, bank, market, M, FTS, p_start, DECAY, SCHED, hits_allowed=False)
        if not scored:
            raise MissingInput("no plan scored")
        bb = PLV.bb_rescore(scored, squad, M[0])
        plain = {PL.plan_key(ev): (i, ev) for i, ev in enumerate(scored, 1)}
        boost = {PL.plan_key(ev): (i, ev) for i, ev in enumerate(bb, 1)}
        out()
        out(f"  {label}: {len(scored)} plans")
        out(f"    {'':<40} {'BB score':>8} {'GW' + str(target) + ' gain':>9} {'rank':>5}   {'no-BB':>6} {'rank':>5}   plan")

        def row(tag, key):
            if key is None:
                out(f"    {tag:<40} none scored (outside the pool of the top {PL.POOL} per position, or illegal)")
                return
            (ib, eb), (ip, ep) = boost[key], plain[key]
            out(f"    {tag:<40} {eb['score']:8.2f} {eb['gains'][0]:+9.2f} {ib:>5}   {ep['score']:6.2f} {ip:>5}   {PLV.plan_text(ep)}"
                + CF.move_flag(squad, ep["outs"], ep["ins"]))

        def best(evs, test):
            ev = next((e for e in evs if test(e)), None)
            return PL.plan_key(ev) if ev else None
        row("best with a Bench Boost", best(bb, lambda e: True))
        row("best pair with a Bench Boost", best(bb, lambda e: e["used"] == 2))
        row("best without a Bench Boost", best(scored, lambda e: True))
        row("best pair without a Bench Boost", best(scored, lambda e: e["used"] == 2))
        for names in NAMED:
            ids = {ours(n)["id"] for n in names}
            tag = " + ".join(names) + (" out" if len(names) > 1 else " out only (roll one)")
            row(f"{tag}, best under BB", best(bb, lambda e, ids=ids: {o["id"] for o in e["outs"]} == ids))
            row(f"{tag}, best without BB", best(scored, lambda e, ids=ids: {o["id"] for o in e["outs"]} == ids))
        row("roll both", best(scored, lambda e: not e["outs"]))
    path_out = os.path.join(a.out, "bb_moves.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines).rstrip("\n") + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MissingInput as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
