"""tools/defcon.py - S13 (BUILD_PLAN.md Step 13, item N2): P(DEFCON) v2,
offline. Standard library only; the nightly never imports it.

A negative-binomial count model per player-match: mean mu = the player's
shrunk per-90 DEFCON action rate x 90 x an opponent factor from the
odds-implied lambda of S5 (lambda_opp / the round's mean lambda); the
dispersion r per position fitted on the training rounds by the method of
moments on the model's own means (clipped to [0.5, 1000]; the Poisson limit
when the variance is at or below the mean). P(DEFCON) = P(X >= threshold),
expected points = 2 x P. Thresholds (2025/26 rules): DEF 10 CBIT, MID 12
CBIRT, FWD 12 CBIRT, GK none. The comparator is the current hit-rate
approach (fpl_edge.defcon_expectation): hits / matches over the player's
60+-minute matches in the training rounds, 0 for forwards and for a player
without such a match.

The pre-registered test (prereg/S13.md): 2025/26 GW5-38 point-in-time
through the S4 harness (canonical_at, training rounds < t, clubs of the
origin), player-matches with 60+ minutes, DEF and MID paired per gameweek
(forwards shown separately); (a) Brier comparator - v2 >= 0.005 with the
90% bootstrap lower bound > 0 (B = 10000 over gameweeks, seed 20261018);
(b) observed v predicted hit rate within 5 points in at least 8 of 10
deciles of predicted P (pooled). Both must hold; adoption needs Boris.

    python tools/defcon.py --test [--hist DIR] [--odds FILE] [--out DIR]
"""
import argparse
import math
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
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

THRESHOLDS = {2: 10, 3: 12, 4: 12}        # v2, 2025/26 rules: DEF 10 CBIT, MID 12 CBIRT, FWD 12 CBIRT; GK none
COMPARATOR = E.DEFCON_THRESHOLD           # the current code: DEF 10, MID 12; forwards 0
PRIMARY_POS = (2, 3)                      # the paired sample: positions with a threshold in both models
MIN_MINUTES = 60
R_LO, R_HI = 0.5, 1000.0
PASS_BRIER = 0.005
CAL_TOL, CAL_MIN, DECILES = 0.05, 8, 10
EPS = 1e-6
SEED = BT.SEED


class MissingInput(Exception):
    pass


# ---------------------------------------------------------------------------
# the negative binomial
# ---------------------------------------------------------------------------

def nb_logpmf(mu, r, x):
    """log P(X = x) under NB with mean mu and dispersion r (variance
    mu + mu^2 / r); r None = the Poisson limit."""
    if r is None:
        return x * math.log(mu) - mu - math.lgamma(x + 1)
    return (math.lgamma(x + r) - math.lgamma(r) - math.lgamma(x + 1)
            + r * math.log(r / (r + mu)) + x * math.log(mu / (r + mu)))


def nb_tail(mu, r, k):
    """P(X >= k)."""
    if k <= 0:
        return 1.0
    if mu <= 0:
        return 0.0
    below = sum(math.exp(nb_logpmf(mu, r, x)) for x in range(k))
    return min(1.0, max(0.0, 1.0 - below))


def fit_dispersion(pairs):
    """Method of moments on (count, mean) pairs: r = sum(mu^2) /
    (sum((x - mu)^2) - sum(mu)), clipped to [R_LO, R_HI]; None (Poisson)
    when the variance is at or below the mean."""
    if not pairs:
        raise MissingInput("no training player-matches to fit the dispersion on")
    s_mu2 = sum(mu * mu for _, mu in pairs)
    den = sum((x - mu) ** 2 for x, mu in pairs) - sum(mu for _, mu in pairs)
    if den <= 0:
        return None
    return min(R_HI, max(R_LO, s_mu2 / den))


# ---------------------------------------------------------------------------
# the rate, the opponent factor, the comparator
# ---------------------------------------------------------------------------

def shrunk_rate90(inp, p):
    """The player's season DEFCON actions per 90 over the training rounds,
    shrunk toward the positional median by the measured reliability weight
    (reliability_inputs, as bottomup's defcon term does)."""
    prior = inp["priors"].get((p["pos"], "defcon90"), 0.0)
    w = inp["weights"]["defcon"]
    return prior if p["defcon90"] is None else p["defcon90"] * w + prior * (1 - w)


def round_mean_lambda(season, g):
    lams = season.lambdas(g)
    vals = [lam[k] for lam, _ in lams.values() for k in ("lambda_home", "lambda_away")]
    if not vals:
        raise MissingInput(f"round {g}: no fixture with a lambda")
    return sum(vals) / len(vals)


def opponent_factor(season, fid, team):
    """(lambda_opp / the round's mean lambda, source) for `team` in fixture
    `fid`; the lambda is S5's (odds, else the labelled fallback)."""
    lam_opp, src = season.lam_opp(fid, team)
    return lam_opp / round_mean_lambda(season, season.fixtures[fid]["event"]), src


def comparator_rate(train_rows, pos):
    """The current hit-rate approach on the player's 60+-minute training
    matches: hits / matches at the current code's threshold; 0 for a
    position without one (forwards, keepers) or without such a match."""
    thr = COMPARATOR.get(pos)
    if not thr:
        return 0.0
    played = [x for x in train_rows]
    if not played:
        return 0.0
    return sum(1 for x in played if x >= thr) / len(played)


def row_team(f, r):
    return f["home"] if str(r.get("was_home")).lower() == "true" else f["away"]


# ---------------------------------------------------------------------------
# 2025/26, point-in-time
# ---------------------------------------------------------------------------

class Season:
    def __init__(self, hist_dir, odds_file=None):
        self.s = OL.Season2526(hist_dir, odds_file)
        self.hist = self.s.hist
        self.fixtures = self.s.fixtures

    def _match(self, r):
        """(fixture, minutes, actions) of a raw row; raises on a missing input."""
        fid = str(r["fixture"])
        if fid not in self.fixtures:
            raise MissingInput(f"fixture {fid} of element {r['element']} is not in fixtures.csv")
        if "defensive_contribution" not in r:
            raise MissingInput(f"element {r['element']} round {r['round']}: no defensive_contribution column")
        return self.fixtures[fid], H._num(r["minutes"]), int(H._num(r["defensive_contribution"]))

    def origin(self, t):
        """Gameweek t from rounds < t: the rates and priors of the training
        slice, r per position on the training player-matches, the comparator's
        hit rates, and the round-t rows (60+ minutes, a threshold position)."""
        if t < 2 or t > self.hist["through"]:
            raise MissingInput(f"GW{t} is outside the rebuildable range 2..{self.hist['through']}")
        c = BT.canonical_at(self.hist, t)
        inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
        pairs = defaultdict(list)
        hist_counts = defaultdict(list)
        for g in range(1, t):
            for r in self.hist["raw"].get(g, []):
                pid = int(r["element"])
                p = inp["players"].get(pid)
                if p is None or p["pos"] not in THRESHOLDS:
                    continue
                f, mins, x = self._match(r)
                if mins < MIN_MINUTES:
                    continue
                hist_counts[pid].append(x)
                factor, _ = opponent_factor(self.s, str(r["fixture"]), row_team(f, r))
                pairs[p["pos"]].append((x, shrunk_rate90(inp, p) * factor))
        r_pos = {pos: fit_dispersion(pairs[pos]) for pos in THRESHOLDS}
        rows = []
        for r in self.hist["raw"].get(t, []):
            pid = int(r["element"])
            p = inp["players"].get(pid)
            if p is None or p["pos"] not in THRESHOLDS:
                continue
            f, mins, x = self._match(r)
            if mins < MIN_MINUTES:
                continue
            team = row_team(f, r)
            if p["team"] != team:                       # the club of the origin (hist_pit) must be the row's club
                raise MissingInput(f"GW{t}: element {pid} plays for {team} in the row but the club map says {p['team']}")
            factor, src = opponent_factor(self.s, str(r["fixture"]), team)
            mu = shrunk_rate90(inp, p) * factor
            thr = THRESHOLDS[p["pos"]]
            rows.append({"pid": pid, "pos": p["pos"], "mu": mu, "factor": factor, "source": src, "x": x,
                         "p_v2": nb_tail(mu, r_pos[p["pos"]], thr),
                         "p_cmp": comparator_rate(hist_counts.get(pid, []), p["pos"]),
                         "hit": 1 if x >= thr else 0})
        return {"gw": t, "rows": rows, "r": r_pos, "n_train": {pos: len(pairs[pos]) for pos in THRESHOLDS}}


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------

def brier(rows, key):
    return sum((r[key] - r["hit"]) ** 2 for r in rows) / len(rows) if rows else None


def logloss(rows, key):
    if not rows:
        return None
    tot = 0.0
    for r in rows:
        p = min(1 - EPS, max(EPS, r[key]))
        tot -= math.log(p) if r["hit"] else math.log(1 - p)
    return tot / len(rows)


def calibration(rows, key, deciles=DECILES):
    """Deciles of predicted P over the pooled rows (equal counts, sorted by
    P): [(n, predicted = mean P, observed hit rate)]."""
    srt = sorted(rows, key=lambda r: (r[key], r["pid"]))
    n = len(srt)
    out = []
    for i in range(deciles):
        chunk = srt[i * n // deciles:(i + 1) * n // deciles]
        if not chunk:
            out.append((0, None, None))
            continue
        out.append((len(chunk), sum(r[key] for r in chunk) / len(chunk), sum(r["hit"] for r in chunk) / len(chunk)))
    return out


def within(cal, tol=CAL_TOL):
    return sum(1 for n, pred, obs in cal if n and abs(pred - obs) <= tol + 1e-12)   # the boundary counts, not float noise


def r_text(r):
    return "Poisson" if r is None else f"{r:.2f}"


def test_2526(hist_dir, out=print, first=5, last=None, odds_file=None, seed=SEED):
    season = Season(hist_dir, odds_file)
    last = last or season.hist["through"]
    out(f"S13 TEST  2025/26 GW{first}-{last}: P(DEFCON) v2 (negative binomial, odds-implied opponent factor) against the "
        f"hit-rate comparator (defcon_expectation's rule on the training rounds), player-matches with {MIN_MINUTES}+ minutes, "
        f"DEF and MID paired per gameweek; thresholds DEF {THRESHOLDS[2]} CBIT, MID {THRESHOLDS[3]} CBIRT (FWD {THRESHOLDS[4]} CBIRT, "
        f"shown separately; the comparator gives forwards 0); bootstrap over gameweeks B={BT.B}, 90%, seed {seed}")
    out(f"  {'GW':>4} {'n':>5} {'Brier cmp':>10} {'Brier v2':>9} {'diff':>8} {'LL cmp':>7} {'LL v2':>6} {'r DEF':>8} {'r MID':>8} {'r FWD':>8} "
        f"{'fallback':>9} {'FWD n':>6} {'FWD cmp':>8} {'FWD v2':>7}")
    per, pooled, pooled_fwd = [], [], []
    for t in range(first, last + 1):
        o = season.origin(t)
        prim = [r for r in o["rows"] if r["pos"] in PRIMARY_POS]
        fwd = [r for r in o["rows"] if r["pos"] == 4]
        if not prim:
            raise MissingInput(f"GW{t}: no DEF/MID player-match with {MIN_MINUTES}+ minutes")
        rec = {"gw": t, "n": len(prim), "b_cmp": brier(prim, "p_cmp"), "b_v2": brier(prim, "p_v2"),
               "ll_cmp": logloss(prim, "p_cmp"), "ll_v2": logloss(prim, "p_v2"), "r": o["r"],
               "fallback": sum(1 for r in o["rows"] if r["source"] == "fallback") / len(o["rows"]),
               "n_fwd": len(fwd), "b_fwd_cmp": brier(fwd, "p_cmp"), "b_fwd_v2": brier(fwd, "p_v2")}
        per.append(rec)
        pooled.extend(prim); pooled_fwd.extend(fwd)
        out(f"  {t:>4} {rec['n']:>5} {rec['b_cmp']:10.4f} {rec['b_v2']:9.4f} {rec['b_cmp'] - rec['b_v2']:+8.4f} {rec['ll_cmp']:7.3f} {rec['ll_v2']:6.3f} "
            f"{r_text(o['r'][2]):>8} {r_text(o['r'][3]):>8} {r_text(o['r'][4]):>8} {rec['fallback']:9.2f} {rec['n_fwd']:>6} "
            f"{(rec['b_fwd_cmp'] if rec['b_fwd_cmp'] is not None else float('nan')):8.4f} {(rec['b_fwd_v2'] if rec['b_fwd_v2'] is not None else float('nan')):7.4f}")
    d = [r["b_cmp"] - r["b_v2"] for r in per]
    boot = BT.bootstrap_mean(d, seed=seed)
    cal = calibration(pooled, "p_v2")
    cal_cmp = calibration(pooled, "p_cmp")
    out(f"  calibration, v2, DEF and MID pooled GW{first}-{last} (n={len(pooled)}), deciles of predicted P; the comparator's deciles for information:")
    out(f"  {'decile':>8} {'n':>6} {'predicted':>10} {'observed':>9} {'|diff|':>7} {'| cmp n':>8} {'predicted':>10} {'observed':>9}")
    for i, ((n, pr, ob), (n2, pr2, ob2)) in enumerate(zip(cal, cal_cmp), 1):
        out(f"  {i:>8} {n:>6} {pr:10.3f} {ob:9.3f} {abs(pr - ob):7.3f} {n2:>8} {pr2:10.3f} {ob2:9.3f}")
    k = within(cal)
    a_ok = boot["mean"] >= PASS_BRIER and boot["lo"] > 0
    b_ok = k >= CAL_MIN
    if pooled_fwd:
        out(f"  forwards (information only, n={len(pooled_fwd)}): Brier comparator {brier(pooled_fwd, 'p_cmp'):.4f} (predicts 0), "
            f"v2 {brier(pooled_fwd, 'p_v2'):.4f}; observed hit rate {sum(r['hit'] for r in pooled_fwd) / len(pooled_fwd):.3f}")
    out(f"  (a) Brier improvement comparator - v2: {boot['mean']:+.4f} [{boot['lo']:+.4f}, {boot['hi']:+.4f}] n={boot['n']}; "
        f"bar >= {PASS_BRIER} with lower bound > 0: {'PASS' if a_ok else 'FAIL'}")
    out(f"  (b) calibration: {k} of {DECILES} deciles within {CAL_TOL:.2f}; bar >= {CAL_MIN}: {'PASS' if b_ok else 'FAIL'}")
    out(f"  pre-registered result: {'PASS' if (a_ok and b_ok) else 'FAIL'} (both must hold)")
    return {"per": per, "boot": boot, "cal": cal, "within": k, "pass": a_ok and b_ok, "pooled": pooled, "fwd": pooled_fwd}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical", "2025-26"))
    ap.add_argument("--odds", default=None, help="football-data CSV (default: S5's 2025/26 file)")
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out"))
    ap.add_argument("--first", type=int, default=5)
    ap.add_argument("--last", type=int, default=None)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args(argv)
    if not a.test:
        ap.print_help()
        return 2
    run = Run("tools/defcon.py", a.out, argv)
    lines = []

    def out(s):
        print(s)
        lines.append(s)
    try:
        test_2526(a.hist, out, first=a.first, last=a.last, odds_file=a.odds)
    except (MissingInput, OL.MissingInput, BT.MissingInput) as e:
        print(f"missing input: {e}")
        return 2
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "defcon_test_2025-26.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run.wrote(path)
    print(f"written: {path}; provenance: {run.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
