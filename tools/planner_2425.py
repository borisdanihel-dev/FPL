"""tools/planner_2425.py - S8b (BUILD_PLAN.md Part F, F-F; prereg/S8b.md): S8's
planner without hits, on xp_v2, 2024/25. Offline; standard library only; the
nightly never imports it.

2024/25 GW2-38, S7's 50 squads (seed 7, 2024/25 GW1 ownership), 1 FT a week,
bank to 5, no chips: S8's rank_plans with hits forbidden, decay 0.85 and
Boris's FT schedule against S8's baseline (the best one-week move with the
free transfer when its xP gain > 0, else roll). S8's replay loop runs
unchanged; only its season is swapped in for the call:

  forecasts  xp_v2 as tested (S6d's core, S6b's terms) at origin t for weeks
             u = t..t+5 from rounds < t; week t's lambdas are S5's (odds,
             else the fallback) as in S6b, weeks t+1..t+5 the fallback
             fitted on results before the origin (the night ruling, point
             5); every fixture's source is recorded
  outcomes   2024/25 re-scored under the 2026/27 table by S10b (bonus
             official, DEFCON excluded: 2024/25 has no counts)

Pass: mean gain >= +5 points per squad-season and the 90% lower bound > 0
(bootstrap over squads, B = 10000, seed 20261018). Otherwise the simple rule
stays the default.

    python tools/planner_2425.py --test [--hist ROOT] [--odds FILE] [--out DIR]
"""
import argparse
import contextlib
import csv
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import planner as PL                                              # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_2425 as F                                            # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

SEASON, PRIOR = F.SEASON, F.PRIOR
PASS_GAIN = 5.0                     # F-F: mean >= +5 points per squad-season
DECAY = 0.85
SCHEDULE = "boris"


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted."""


class Season2425(PL.Replay):
    """S8's season (S7's squads, prices, clubs, pairings) with xp_v2 over the
    horizon and the re-scored outcomes. The instances are kept for the
    report (the lambda sources)."""
    instances = []

    def __init__(self, hist_dir, prior_dir, odds_file, rescored):
        super().__init__(hist_dir)
        # S6b's terms, composed as xp_v2_replay.Replay composes them (it would
        # build S8's season by name again): S11's season with S5's inside, the
        # raw rounds of the same load
        self.s11 = SH.Season(hist_dir, prior_dir, odds_file)
        self.s5, self.fixtures = self.s11.s, self.s11.s.fixtures
        self.hist, self.by_round = self.rp.hist, self.rp.hist["raw"]
        self.rp.actual = XR.actuals_from(rescored)                  # the outcomes: S10b's re-score
        self.sources = []                                           # (origin, week, fixture, home, away, source)
        self._model = {}
        Season2425.instances.append(self)

    def horizon_lambdas(self, t, u):
        """{fixture: (lambdas, source)} of week u at origin t: week t is S5's
        (odds, else the fallback); later weeks the fallback fitted on results
        of rounds < t, cut at round t's first kickoff (S5's own rule)."""
        s5 = self.s5
        if u == t:
            return s5.lambdas(t)
        if t not in self._model:
            results = [(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in s5.fixtures.values() if f["event"] < t]
            self._model[t] = OL.fit_fallback(results, s5.deadline(t))
        return {fid: OL.fixture_lambdas(None, self._model[t], f["kickoff"], f["home"], f["away"], s5.method)
                for fid, f in s5.fixtures.items() if f["event"] == u}

    def xp_week(self, t, u, inp, names):
        """{pid: xp_v2} of week u at origin t: S6d's core on the origin's
        inputs with week u's fixtures and lambdas."""
        x = self
        lam = self.horizon_lambdas(t, u)

        def lam_team(fid, team):
            l, f = lam[fid][0], x.fixtures[fid]
            return l["lambda_home"] if team == f["home"] else l["lambda_away"]

        def lam_opp(fid, team):
            l, f = lam[fid][0], x.fixtures[fid]
            return l["lambda_away"] if team == f["home"] else l["lambda_home"]
        xp, _ = XL.core(inp, names, x.by_round, t, x.s11.rows, x.s11.n2s, x.s11.tot, x.s11.prior,
                        lambda team: x.s11.club_fixtures(team, u), lam_team, lam_opp)
        for fid in sorted(lam, key=str):
            f = x.fixtures[fid]
            self.sources.append((t, u, fid, f["home"], f["away"], lam[fid][1]))
        return {pid: v for pid, v in xp.items() if v}

    def forecasts(self, t):
        """({u: {pid: xp_v2}} for u = t..min(t+5, 38), p_start, pos) at origin t."""
        if t in self._fc:
            return self._fc[t]
        c = BT.canonical_at(self.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        names = {pid: c["players"][pid]["name"] for pid in inp["players"]}
        out = {u: self.xp_week(t, u, inp, names) for u in range(t, min(t + PL.HORIZON - 1, PL.REPLAY_LAST) + 1)}
        self._fc[t] = (out, {pid: p["p_start"] for pid, p in inp["players"].items()},
                       {pid: p["pos"] for pid, p in inp["players"].items()})
        return self._fc[t]


@contextlib.contextmanager
def season_2425(prior_dir, odds_file, rescored):
    """S8's replay builds its season by name: Season2425 for the block, S8's
    restored after, whatever happens."""
    saved = PL.Replay
    PL.Replay = lambda hist_dir: Season2425(hist_dir, prior_dir, odds_file, rescored)
    try:
        yield
    finally:
        PL.Replay = saved


def run(hist_root, out=print, odds_file=F.ODDS, out_csv=None, sources_csv=None, n_squads=CH.N_SQUADS,
        squad_seed=CH.SQUAD_SEED, boot_seed=PL.SEED, first=PL.REPLAY_FIRST, last=PL.REPLAY_LAST, season=SEASON,
        prior=PRIOR, check_decays=True):
    hist_dir, prior_dir = os.path.join(hist_root, season), os.path.join(hist_root, prior)
    for p in (odds_file, os.path.join(prior_dir, "merged_gw.csv"), os.path.join(prior_dir, "teams.csv")):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing")
    F.check_no_counts(hist_dir)
    notes = []
    rescored = F.rescore(hist_root, out_csv, season, say=notes.append)
    Season2425.instances = []
    with F.season_names(season), season_2425(prior_dir, odds_file, rescored):
        r = PL.replay(hist_dir, n_squads=n_squads, seed=squad_seed, out=lambda s: None, decay=DECAY, schedule_name=SCHEDULE,
                      boot_seed=boot_seed, first=first, last=last, check_decays=check_decays, hits_allowed=False)
    if len(Season2425.instances) != 1:
        raise MissingInput(f"S8's replay built {len(Season2425.instances)} seasons, not one with xp_v2")
    s = Season2425.instances[0]
    b = r["boot"]
    res = dict(r, pass_=b["mean"] >= PASS_GAIN and b["lo"] > 0, sources=s.sources, notes=notes, season=season, prior=prior,
               first=first, last=last, n_squads=n_squads, squad_seed=squad_seed, boot_seed=boot_seed)
    if sources_csv:
        with open(sources_csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["origin", "week", "fixture", "home", "away", "source"])
            w.writerows(s.sources)
    report(res, out, odds_file)
    return res


def report(res, out, odds_file):
    lab = F.label
    rs = res["results"]
    n = len(rs)
    out(f"S8B TEST  {lab(res['season'])} GW{res['first']}-{res['last']} (F-F): S8's planner with hits forbidden against S8's "
        f"baseline (best one-week move when its gain > 0, else roll), {res['n_squads']} fixed squads (seed {res['squad_seed']}, "
        f"{lab(res['season'])} GW1 ownership), 1 FT a week, bank to {PL.MAX_FT}, no chips; xP = xp_v2 as tested over the six-week "
        f"horizon, decay {DECAY}, schedule {SCHEDULE} {PL.SCHEDULES[SCHEDULE]}; priors {lab(res['prior'])}; odds "
        f"{os.path.basename(odds_file)}; bootstrap over squads B={BT.B}, 90%, seed {res['boot_seed']}")
    out("  S8's replay loop unchanged (tools/planner.py replay, hits_allowed=False) with S8b's season: xp_v2 at origin t for weeks "
        "t..t+5 (week t: S5's odds-implied lambda, else the fallback; weeks t+1..t+5: the fallback fitted on results before the "
        "origin - the night ruling, point 5); outcomes re-scored under the 2026/27 table by S10b")
    out("  DEFCON: 2024/25 has no defensive-action counts, so neither the forecast nor the outcome carries DEFCON (a limitation)")
    for note in res["notes"]:
        out(f"  re-score: {note}")
    cnt = Counter(("week t" if o == u else "weeks t+1..t+5", src) for o, u, _, _, _, src in res["sources"])
    out("  lambda sources (fixture-weeks over all origins): " + ", ".join(f"{k[0]} {k[1]} {v}" for k, v in sorted(cnt.items())))
    out(f"  season points per squad (mean): planner {sum(r['planner']['pts'] for r in rs) / n:.1f} (transfers "
        f"{sum(r['planner']['transfers'] for r in rs) / n:.1f}, hits {sum(r['planner']['hits'] for r in rs) / n:.1f}), baseline "
        f"{sum(r['baseline']['pts'] for r in rs) / n:.1f} (transfers {sum(r['baseline']['transfers'] for r in rs) / n:.1f})")
    b = res["boot"]
    out(f"  primary: paired gain planner - baseline per squad-season {b['mean']:+.2f}, 90% CI [{b['lo']:+.2f}, {b['hi']:+.2f}] "
        f"(bootstrap over {b['n']} squads)")
    dis = [r["planner"]["disagree"] for r in rs[:5]]
    out(f"  robustness (first 5 squads): weeks where decay 0.80 or 0.90 chose a different plan: {dis} of "
        f"{res['last'] - res['first'] + 1} each")
    out(f"  pre-registered bar: mean >= +{PASS_GAIN:g} and the 90% lower bound > 0: "
        + ("PASS (adoption needs Boris)" if res["pass_"] else "FAIL - the simple rule stays the default"))


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test", action="store_true", required=True)
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"), help="the root holding 2024-25/, 2023-24/ and 2026-27/")
    ap.add_argument("--odds", default=F.ODDS)
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "planner_2425"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("tools/planner_2425.py", a.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    csv_path, src_path = os.path.join(a.out, f"rescored_{SEASON}.csv"), os.path.join(a.out, "sources.csv")
    try:
        run(a.hist, out, odds_file=a.odds, out_csv=csv_path, sources_csv=src_path)
    except (XR.MissingInput, OL.MissingInput, BT.MissingInput, CH.MissingInput, SH.MissingInput, PL.MissingInput) as e:
        print(f"missing input: {e} - nothing is substituted")
        return 2
    path = os.path.join(a.out, f"s8b_{SEASON}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    for p in (csv_path, src_path, path):
        run_.wrote(p)
    print(f"written: {path}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
