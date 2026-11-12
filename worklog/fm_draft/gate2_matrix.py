"""Scratch, information for the prereg/FM.md draft only: the GW11 xp_v2 horizon matrix (S15's builder.live_matrix,
s8c-wip) for three of our players under the current gate (v1) and the proposed status gate v2.

    python -I gate2_matrix.py --code S8C_WORKTREE --data DATA_COPY --hist C:\\GIT\\FPL\\historical

v1 (live): a player whose status is not 'a' has no value in any week; chance scales P(sub) only.
v2 (proposal, Boris's plan item 5):
  'd'  week t: P(start) x chance (and P(sub) x chance, as now); later weeks as normal (chance 1)
  's'  0 for the club's fixtures before the ban's end, then normal (chance 1)
  'i'  unknown return: 0 for two gameweeks, then scaled by the last known chance
"normal" = the gate lifted and chance 1 (the model's own P(start), which already falls with low recent minutes).
"""
import os
import sys
from collections import Counter


def _arg(name):
    a = sys.argv[1:]
    return a[a.index(name) + 1]


CODE = os.path.abspath(_arg("--code"))
DATA, HIST = _arg("--data"), _arg("--hist")
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(CODE, "tools"))
import builder as B                                               # noqa: E402
import chips as CH                                                # noqa: E402
import fpl_edge as E                                              # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2 as XV                                                # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
from datetime import datetime, timezone                           # noqa: E402

WEEKS = 6
NAMES = (("Thiago", "BRE"), ("Thomas", "COV"), ("Calafiori", "ARS"))


def matrix(lift=frozenset(), chance_one=frozenset(), clear=frozenset()):
    """builder.live_matrix's loop, with `lift` players' gate set True and `chance_one` players' chance set 1;
    `clear` players are taken as status 'a' with no flag (chance_next_round None) in the export itself, so
    P(start) and P(sub) carry no chance ("as normal"); returns (d, target, [{pid: xp}], [{pid: detail}])."""
    now = datetime.now(timezone.utc)
    name_to_short, deadlines, fixtures, settled, _ = OL.sqlite_tables(DATA)
    dl, target = sorted((dl, ev) for ev, dl in deadlines.items() if dl > now)[0]
    d, path = CH.newest_export(DATA)
    for p in d["all_players"]:
        if p["id"] in clear:
            p["status"], p["chance_next_round"] = "a", None
    snap = OL.newest_snapshot(DATA, dl)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    model = XL._model(fixtures, dl)
    prior = XL.load_prior(HIST)
    names, _ = XL.prior_names(os.path.join(DATA, "fpl.sqlite"), os.path.join(HIST, "2026-27", "elements_positions.csv"),
                              os.path.join(HIST, XL.PRIOR_SEASON))
    c = E.canonical_through(E.canonical_from_export(d), d["gameweek"])
    inp = E.reliability_inputs(c, gws_played=d["gameweek"])
    by_round, rows = XL.export_rows(d)
    tot = SH.team_totals(rows, {})
    gate = {int(p["id"]): p["status"] == "a" for p in d["all_players"]}
    for pid in lift:
        gate[pid] = True
    chance = XV.chance_scale(d)
    for pid in chance_one:
        chance[pid] = 1.0
    weeks, dets = [], []
    for u in range(target, target + WEEKS):
        fx = XL.target_fixtures(d, u)
        lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}

        def fixtures_of(team, fx=fx):
            return [(fid, f) for fid, f in fx.items() if team in (f["home"], f["away"])]

        def lam_team(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_home"] if team == fx[fid]["home"] else lam[fid][0]["lambda_away"]

        def lam_opp(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_away"] if team == fx[fid]["home"] else lam[fid][0]["lambda_home"]
        xp, det = XL.core(inp, names, by_round, target, rows, {}, tot, prior, fixtures_of, lam_team, lam_opp,
                          ict=XL.ict_live(d), chance=chance, gate=gate)
        weeks.append(xp)
        dets.append(det)
    return d, target, weeks, dets, os.path.basename(path), (os.path.basename(snap[0]) if snap and isinstance(snap[0], str) else str(snap[0])[:60] if snap else None)


def main():
    d, target, live, _, exp_name, snap = matrix()
    by = {(p["web_name"], p["team"]): p for p in d["all_players"]}
    ids = {n: by[n]["id"] for n in NAMES}
    ref_weeks = B.live_matrix(DATA, HIST, WEEKS)[3]          # builder.live_matrix itself, nothing lifted
    same = all(ref_weeks[t] == live[t] for t in range(WEEKS))
    _, _, lifted, ldet, _, _ = matrix(lift=frozenset(ids.values()))            # gate lifted, the flag's chance kept
    _, _, normal, ndet, _, _ = matrix(clear=frozenset(ids.values()))           # as normal: status a, no flag
    others = [(t, pid) for t in range(WEEKS) for pid in set(live[t]) | set(normal[t])
              if pid not in ids.values() and live[t].get(pid) != normal[t].get(pid)]
    print(f"check: clearing the three flags moves no other player: {not others}")
    # status gate v2 for GW11-16: Thiago 's' until 5 Dec (BRE out GW11-13, back GW14); Thomas 'd' 50%; Calafiori 'a'
    v2 = {ids[("Thiago", "BRE")]: [0.0, 0.0, 0.0] + [normal[t].get(ids[("Thiago", "BRE")], 0.0) for t in (3, 4, 5)],
          ids[("Thomas", "COV")]: [lifted[0].get(ids[("Thomas", "COV")], 0.0)]
          + [normal[t].get(ids[("Thomas", "COV")], 0.0) for t in range(1, WEEKS)],
          ids[("Calafiori", "ARS")]: [live[t].get(ids[("Calafiori", "ARS")], 0.0) for t in range(WEEKS)]}
    print("V2 TABLE  player        " + " ".join(f"  GW{target + t}" for t in range(WEEKS)) + "   sum")
    for n in NAMES:
        pid = ids[n]
        v1 = [live[t].get(pid, 0.0) for t in range(WEEKS)]
        print(f"  v1  {n[0]:<12} " + " ".join(f"{x:6.2f}" for x in v1) + f"  {sum(v1):5.2f}")
        print(f"  v2  {n[0]:<12} " + " ".join(f"{x:6.2f}" for x in v2[pid]) + f"  {sum(v2[pid]):5.2f}")
        dn = ndet[0].get(pid)
        if dn:
            print(f"      as normal: P(start) {dn['p_start']:.3f}, P(sub) {dn['p_sub']:.3f}")
    print(f"export {exp_name}; odds {snap}; target GW{target}; weeks GW{target}-GW{target + WEEKS - 1}")
    print(f"check: this copy with nothing lifted equals builder.live_matrix in every week: {same}")
    others = [(t, pid) for t in range(WEEKS) for pid in set(live[t]) | set(lifted[t])
              if pid not in ids.values() and live[t].get(pid) != lifted[t].get(pid)]
    print(f"check: lifting the three moves no other player: {not others}")
    for n in NAMES:
        p = by[n]
        print(f"{n[0]} ({n[1]}): status {p['status']}, chance {E.chance_of_playing(p)}, news {p['news']!r}, "
              f"mins_last4 {p['mins_last4']}")
        pid = p["id"]
        v1 = [live[t].get(pid) for t in range(WEEKS)]
        nor = [lifted[t].get(pid) for t in range(WEEKS)]
        det0 = ldet[0].get(pid)
        print("   v1 (live)     " + " ".join("   -  " if x is None else f"{x:6.2f}" for x in v1))
        print("   normal        " + " ".join("   -  " if x is None else f"{x:6.2f}" for x in nor))
        if det0:
            print(f"   GW{target} detail (gate lifted, chance 1): P(start) {det0['p_start']:.3f}, e_xg {det0['e_xg']:.3f}, "
                  f"e_bl {det0['e_bl']:.3f}, P(sub) {det0['p_sub']:.3f}, e_sub {det0['e_sub']:.3f}")
        for t in range(WEEKS):
            dt = ldet[t].get(pid)
            if dt:
                print(f"     GW{target + t}: P(start) {dt['p_start']:.3f} fixtures {len(dt['fixtures'])} "
                      f"opp {[f['opp'] for f in dt['fixtures']]}")


if __name__ == "__main__":
    main()
