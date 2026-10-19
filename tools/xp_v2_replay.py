"""tools/xp_v2_replay.py - S6b, the xp_v2 past-season test (prereg/S6b.md,
RULING S6b). Offline; standard library only; the nightly never imports it.

2025/26 GW5-38, re-scored under the 2026/27 rules by Step 10
(tools/rules.py normalise), point-in-time through the S4 harness with
hist_pit clubs. Two models choose the XI and captain of S7's 50 synthetic
squads every gameweek (fixed squads, no transfers, no chips):

  own_proxy  fpl_edge.project_reliability on the training inputs - the
             rebuildable source S7 and S8 replayed. It lacks what live own
             (fpl_edge.project) uses and 2025/26 cannot rebuild: the form
             term (points over the last four per 90, shrunk to the
             positional prior), the minutes-reliability scaling, the
             pre-deadline FDR adjustment, and chance_next_round and status.
  xp_v2      S6's equal blend, P(start) x (E_xg + E_bl) / 2 + P(sub) x
             E[pts | sub]: E_bl | start from S5's bottomup_lambda, E_xg |
             start from project_xg's terms with S11's shares for the
             attacking rates (goals, assists), S5's odds-implied clean
             sheet, appearance 2, DEFCON by the hit-rate rule, bonus by the
             ICT percentile; P(start) from the current minutes model.

Realised points: the XI by the model's projections, the captain (the
highest in the XI) doubled, automatic substitutions by rule_autosubs on
the re-scored minutes (planner.Replay.realised with the re-scored
actuals). Primary: per gameweek the mean over squads of (xp_v2 -
own_proxy); bootstrap over gameweeks (B = 10000, seed 20261018), 90%;
pass: lower bound > 0. Secondary (printed): per-gameweek Spearman and MAE
among predicted starters, paired. On PASS adoption needs Boris.

    python tools/xp_v2_replay.py --test [--hist DIR] [--prior DIR] [--rules ROOT] [--odds FILE] [--out DIR]
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import fpl_hist as H                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import chips as CH                                                # noqa: E402
import planner as PL                                              # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2 as XV                                                # noqa: E402
import rules as R                                                 # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

FIRST, LAST = 5, 38
STARTER_P = BT.STARTER_P
GATE_MINS = 45                      # the recording gate both models share (mins_last4)
SUB_WINDOW = XV.WINDOW              # S6: P(sub) over the last min(4, t-1) rounds
BONUS_TOP = 0.8                     # project_xg: top ICT ~0.8 bonus a gameweek
SEED = BT.SEED
OWN_PROXY_LACKS = ("own_proxy = project_reliability (the harness's bottomup); it lacks own's form term (points over the last "
                   "four per 90, shrunk to the positional prior), the minutes-reliability scaling, the pre-deadline FDR "
                   "adjustment, and chance_next_round and status")


class MissingInput(Exception):
    pass


# ---------------------------------------------------------------------------
# the outcomes: Step 10's re-scoring
# ---------------------------------------------------------------------------

def rescore(hist_root, out_csv, say=lambda s: None):
    """Step 10's normaliser into out_csv; {(element, round): (points under the
    2026/27 rules, minutes)} read back from that file."""
    for rel in (("2025-26", "merged_gw.csv"), ("2025-26", "players_raw.csv"), ("2026-27", "game_config.json"),
                ("2026-27", "elements_positions.csv")):
        if not os.path.exists(os.path.join(hist_root, *rel)):
            raise MissingInput(f"{os.path.join(hist_root, *rel)} is missing (Step 10's input)")
    R.normalise(out_csv, hist=hist_root, say=say)
    return load_rescored(out_csv)


def load_rescored(path):
    out = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            out[(int(r["element"]), int(r["round"]))] = (float(r["points_2627_rules"]), float(r["minutes"]))
    if not out:
        raise MissingInput(f"{path}: no re-scored player-gameweeks")
    return out


def actuals_from(rescored):
    """planner.Replay's actual shape: event -> pid -> (points, minutes)."""
    actual = defaultdict(dict)
    for (pid, rnd), (pts, mins) in rescored.items():
        actual[rnd][pid] = (pts, mins)
    return actual


# ---------------------------------------------------------------------------
# the xg half's rebuildable inputs (training rounds < t)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# the replay
# ---------------------------------------------------------------------------

class Replay:
    def __init__(self, hist_dir, prior_dir, odds_file=None):
        self.pl = PL.Replay(hist_dir)                       # own_proxy forecasts, squad rows, realised points
        self.hist = self.pl.rp.hist
        self.by_round = self.hist["raw"]
        self.s11 = SH.Season(hist_dir, prior_dir, odds_file)   # S11's shares, priors, k, lambda_team; S5's season inside
        self.s5 = self.s11.s
        self.fixtures = self.s5.fixtures

    def own_proxy(self, t):
        fc, p_start, pos = self.pl.forecasts(t)
        return fc[t], p_start

    def xp_v2(self, t):
        """{pid: xp_v2} at origin t from rounds < t, with the per-player detail."""
        if t < 2 or t > self.hist["through"]:
            raise MissingInput(f"GW{t} is outside the rebuildable range 2..{self.hist['through']}")
        c = BT.canonical_at(self.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        pos_of = {pid: p["pos"] for pid, p in inp["players"].items()}
        p_sub, e_sub = sub_inputs_2526(self.by_round, t, pos_of)
        ict = ict_percentile(self.by_round, t)
        dc = defcon_rates(self.by_round, t, pos_of)
        train = set(range(1, t))
        agg = SH.player_sums(self.s11.rows, self.s11.n2s, train, self.s11.tot)
        pos_start = defaultdict(list)
        for pid, a in agg.items():
            if pid in inp["players"] and a["starts"]:
                pos_start[inp["players"][pid]["pos"]].append(a["start_minutes"] / a["starts"])
        pos_mean_start = {pos: sum(v) / len(v) for pos, v in pos_start.items()}
        out, detail = {}, {}
        for pid, p in inp["players"].items():
            if p["mins_last4"] < GATE_MINS:
                continue
            fx = self.s11.club_fixtures(p["team"], t)
            if not fx:
                continue
            ps = p["p_start"]
            a = agg.get(pid)
            m = a["minutes"] / 90.0 if a else 0.0
            m_start = (a["start_minutes"] / a["starts"]) if a and a["starts"] else pos_mean_start.get(p["pos"], 90.0)
            lam_fx, cs, alloc = [], 0.0, {"xg": 0.0, "xa": 0.0}
            for fid, f in fx:
                home = p["team"] == f["home"]
                opp = f["away"] if home else f["home"]
                lam_opp, _ = self.s5.lam_opp(fid, p["team"])
                lam_fx.append((opp, home, lam_opp))
                cs += OL.p_clean_sheet(lam_opp) * E.CS_VALUE.get(p["pos"], 0)
                lam_team, _ = self.s11.lambda_team(fid, p["team"])
                for key in ("xg", "xa"):
                    s = SH.share_of(a, key) if a else 0.0
                    s0, _ = self.s11.prior.prior(c["players"][pid]["name"], p["pos"], p["team"], key)
                    z = m / (m + self.s11.prior.k[key])
                    alloc[key] += lam_team * (z * s + (1 - z) * s0) * (m_start / 90.0)   # per start: S11's forecast without P(start)
            bl = OL.forecast_lambda(pid, inp, lam_fx)
            e_bl = (bl / ps) if (ps > 0 and bl is not None) else 0.0
            e_xg = xg_half(p["pos"], alloc["xg"], alloc["xa"], cs, dc.get(pid, 0.0), ict.get(pid, 0.5))
            psub = min(1.0, p_sub.get(pid, 0.0))
            v = XV.xp_candidates(ps, e_xg, e_bl, psub, e_sub.get(p["pos"], 0.0))["blend"]
            out[pid] = v
            detail[pid] = {"p_start": ps, "e_xg": e_xg, "e_bl": e_bl, "p_sub": psub, "e_sub": e_sub.get(p["pos"], 0.0),
                           "xg": alloc["xg"], "xa": alloc["xa"], "cs": cs, "defcon": dc.get(pid, 0.0), "ict": ict.get(pid, 0.5)}
        return out, detail


def pick(rows, xp):
    """(XI ids, captain id) under a projection: chips.xi_and_bench, the captain
    the highest projection in the XI (ties by the lower id)."""
    xi, bench, gk = CH.xi_and_bench([dict(r) for r in rows], xp)
    cap = max(xi, key=lambda r: (r["proj"], -r["id"]))
    return frozenset(r["id"] for r in xi), cap["id"]


def test_2526(hist_dir, prior_dir, hist_root, out=print, odds_file=None, first=FIRST, last=LAST,
              n_squads=CH.N_SQUADS, squad_seed=CH.SQUAD_SEED, seed=SEED, rescored=None, say_rules=lambda s: None):
    rp = Replay(hist_dir, prior_dir, odds_file)
    last = min(last, rp.hist["through"])
    if rescored is None:
        raise MissingInput("the re-scored season is required (rescore(hist_root, out_csv))")
    rp.pl.rp.actual = actuals_from(rescored)                # the outcomes: the 2026/27 re-scoring, never the official points
    squads = CH.sample_squads(CH.gw1_candidates(rp.hist), n_squads, squad_seed)
    out(f"S6B TEST  2025/26 GW{first}-{last} re-scored under the 2026/27 rules (Step 10): xp_v2 (S6's equal blend; S5's "
        f"bottomup_lambda in the bottomup half, S11's shares in the xg half; P(start) the current minutes model) against own_proxy, "
        f"each choosing the XI and captain of {len(squads)} fixed squads (seed {squad_seed}), realised points with rule_autosubs and "
        f"the captain doubled; bootstrap over gameweeks B={BT.B}, 90%, seed {seed}")
    out(f"  {OWN_PROXY_LACKS}")
    out(f"  {'GW':>4} {'squads':>6} {'own_proxy':>10} {'xp_v2':>8} {'diff':>7} {'same XI':>8} {'same cap':>9} "
        f"{'n start':>8} {'rho own':>8} {'rho v2':>7} {'d rho':>7} {'MAE own':>8} {'MAE v2':>7} {'d MAE':>7}")
    per = []
    for t in range(first, last + 1):
        own, p_start = rp.own_proxy(t)
        v2, detail = rp.xp_v2(t)
        actual = rp.pl.rp.actual.get(t, {})
        diffs, same_xi, same_cap, pts_o, pts_v = [], 0, 0, [], []
        for squad in squads:
            rows = rp.pl.squad_rows(squad, t)
            r_own = rp.pl.realised(rows, t, own)
            r_v2 = rp.pl.realised(rows, t, v2)
            diffs.append(r_v2 - r_own); pts_o.append(r_own); pts_v.append(r_v2)
            xi_o, cap_o = pick(rows, own); xi_v, cap_v = pick(rows, v2)
            same_xi += xi_o == xi_v; same_cap += cap_o == cap_v
        starters = [pid for pid in v2 if pid in own and p_start.get(pid, 0.0) >= STARTER_P]
        real = [actual.get(pid, (0.0, 0.0))[0] for pid in starters]
        rec = {"gw": t, "n": len(squads), "own": sum(pts_o) / len(pts_o), "v2": sum(pts_v) / len(pts_v),
               "diff": sum(diffs) / len(diffs), "same_xi": same_xi / len(squads), "same_cap": same_cap / len(squads),
               "n_start": len(starters),
               "rho_own": E._spearman([own[p] for p in starters], real), "rho_v2": E._spearman([v2[p] for p in starters], real),
               "mae_own": sum(abs(own[p] - r) for p, r in zip(starters, real)) / len(starters) if starters else float("nan"),
               "mae_v2": sum(abs(v2[p] - r) for p, r in zip(starters, real)) / len(starters) if starters else float("nan")}
        per.append(rec)
        out(f"  {t:>4} {rec['n']:>6} {rec['own']:10.2f} {rec['v2']:8.2f} {rec['diff']:+7.2f} {rec['same_xi']:8.2f} {rec['same_cap']:9.2f} "
            f"{rec['n_start']:>8} {rec['rho_own']:8.3f} {rec['rho_v2']:7.3f} {rec['rho_v2'] - rec['rho_own']:+7.3f} "
            f"{rec['mae_own']:8.3f} {rec['mae_v2']:7.3f} {rec['mae_v2'] - rec['mae_own']:+7.3f}")
    d = [r["diff"] for r in per]
    boot = BT.bootstrap_mean(d, seed=seed)
    season = sum(d)
    rho = BT.bootstrap_mean([r["rho_v2"] - r["rho_own"] for r in per], seed=seed)
    mae = BT.bootstrap_mean([r["mae_v2"] - r["mae_own"] for r in per], seed=seed)
    ok = boot["lo"] > 0
    out(f"  season (GW{first}-{last}): own_proxy {sum(r['own'] for r in per):.1f}, xp_v2 {sum(r['v2'] for r in per):.1f} points per squad; "
        f"xp_v2 - own_proxy {season:+.1f} per squad per season")
    out(f"  primary: mean per-gameweek difference xp_v2 - own_proxy {boot['mean']:+.3f} points per squad, 90% CI "
        f"[{boot['lo']:+.3f}, {boot['hi']:+.3f}] (n={boot['n']} gameweeks, p={boot['p']:.4f})")
    out(f"  secondary (information only): Spearman among starters xp_v2 - own_proxy {rho['mean']:+.4f} [{rho['lo']:+.4f}, {rho['hi']:+.4f}]; "
        f"MAE xp_v2 - own_proxy {mae['mean']:+.4f} [{mae['lo']:+.4f}, {mae['hi']:+.4f}]; same XI {sum(r['same_xi'] for r in per) / len(per):.2f}, "
        f"same captain {sum(r['same_cap'] for r in per) / len(per):.2f} of squad-gameweeks")
    out(f"  pre-registered bar: 90% lower bound > 0: {'PASS' if ok else 'FAIL'}" + (" (adoption needs Boris)" if ok else ""))
    return {"per": per, "boot": boot, "season": season, "rho": rho, "mae": mae, "pass": ok,
            "squads": [sorted(p["id"] for p in s) for s in squads]}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--prior", default=os.path.join(ROOT, "historical", "2024-25"))
    ap.add_argument("--rules", default=os.path.join(ROOT, "historical"), help="Step 10's root: 2025-26/ and 2026-27/")
    ap.add_argument("--odds", default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "xp_v2_replay"))
    ap.add_argument("--first", type=int, default=FIRST)
    ap.add_argument("--last", type=int, default=LAST)
    ap.add_argument("--squads", type=int, default=CH.N_SQUADS)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    if not a.test:
        ap.print_help()
        return 2
    os.makedirs(a.out, exist_ok=True)
    run = Run("tools/xp_v2_replay.py", a.out, argv)
    lines = []

    def out(s):
        print(s)
        lines.append(s)
    rescored_csv = os.path.join(a.out, "rescored_2025-26.csv")
    try:
        rescored = rescore(a.rules, rescored_csv, say=out)
        test_2526(a.hist, a.prior, a.rules, out, odds_file=a.odds, first=a.first, last=a.last, n_squads=a.squads,
                  rescored=rescored)
    except (MissingInput, OL.MissingInput, BT.MissingInput, SH.MissingInput, PL.MissingInput, CH.MissingInput) as e:
        print(f"missing input: {e}")
        return 2
    path = os.path.join(a.out, "xp_v2_replay_2025-26.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run.wrote(rescored_csv)
    run.wrote(path)
    print(f"written: {path}; provenance: {run.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
