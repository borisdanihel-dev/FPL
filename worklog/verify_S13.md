# Verifier report — S13 (BUILD_PLAN.md Step 13, item N2, P(DEFCON) v2, offline)

Verifier: Claude Fable 5.1 (backtest-verifier agent; `.claude/agents/backtest-verifier.md`
read from disk first — it matched the loaded instructions). Date: 2026-10-19.
Worktree `C:\GIT\FPL-b`, branch `lane-b`, HEAD `385bd90`. Nothing outside this
file was written in the tree; `C:\GIT\FPL-data` was neither read nor written;
no `fpl_sync.py`, `--record` or `fpl_nightly.py` was run. All scratch work
(clean clones, truncated histories, the mutation clone, `pit.py`) lives in the
session scratchpad. The untracked `worklog/verify_S8.md` (another verifier's
run) was left alone.

## Prereg order — PASS

- `prereg/S13.md`: ruling verbatim in `7111240` (2026-10-19 01:09:17 +0200),
  template rows filled in `b456909` (01:28:09 +0200).
- The single S13 code commit is `385bd90` (04:25:11 +0200): `tools/defcon.py`
  (+324) and `tests/test_S13.py` (+229), nothing else. The prereg precedes it.
  `test_fpl.py` untouched; no runner file changed (see check 5).
- The ruling block ("RULING Step 13 (DEFCON probability): ... END RULINGS") is
  present verbatim in the prereg; the template rows pin the definitions the
  ruling leaves open (shrink, opponent factor, moments fit, comparator,
  deciles, bootstrap, forwards shown separately).

## Check 1 — point-in-time — PASS

Scratch script `pit.py` (scratchpad) against `C:\GIT\FPL-b\historical\2025-26`
and `tools/odds/E0_2025-26_fetched_2026-10-18.csv`, through the item's own
entry point `Season.origin(t)` and the S4/S5 harness (`canonical_at` →
`canonical_through(t−1)` → `reliability_inputs`; `odds_lambda.Season2526`).

### 1a Truncation test — PASS (origins 5, 21, 38)

For each origin t two truncated copies of the history were written and the
feature rebuilt from them with a fresh `Season`:

- `keep`: `merged_gw.csv` rows of round > t deleted; `fixtures.csv` restricted
  to events ≤ t with the scores of event t blanked (`finished=False`); the
  odds file cut to rows dated ≤ the last round-t kickoff + 1 day. Round-t rows
  intact (they supply the fixture, the minutes filter and the outcome).
- `junk`: as `keep`, and every round-t column except the pinned inputs
  (`element, round, fixture, was_home, minutes, name, position, team,
  opponent_team, kickoff_time`) overwritten with 99 — `defensive_contribution`
  included, so every round-t hit becomes 1.

| t | rows / fixtures / odds rows kept (date ≤) | origin rows | μ, factor, P_v2, P_cmp diffs > 1e-9 | r (DEF, MID, FWD) identical | n_train identical | hits |
|---|---|---|---|---|---|---|
| 5 | 3594 / 50 / 50 (2025-09-22) | 181 = 181 | 0 (keep), 0 (junk) | yes: 17.9148, 10.9338, 9.3061 | yes | keep equal; junk all 1 |
| 21 | 15770 / 210 / 210 (2026-01-09) | 189 = 189 | 0 (keep), 0 (junk) | yes: 8.6163, 8.5088, 7.8409 | yes | keep equal; junk all 1 |
| 38 | 29757 / 380 / 380 (2026-05-25) | 182 = 182 | 0 (keep), 0 (junk) | yes: 8.5198, 8.2008, 8.6915 | yes | keep equal; junk all 1 |

Source labels (odds/fallback) and row order were also identical. The round-t
rows therefore contribute only the fixture, the 60-minute filter and the
realised count; nothing of round t or later moves a probability or r.

### 1b Timestamp audit — PASS (every origin 5–38)

For every t in 5..38, with the cut = the round's first kickoff (the S5
convention; 2025/26 has no recorded deadlines):

- every training player-match (raw rows of rounds < t, 60+ minutes, DEF/MID/FWD;
  748 at t=5 … 6874 at t=38) belongs to a fixture of event < t that kicked off
  before the cut: 0 late rows at every origin;
- the canonical slice behind the rates, priors and reliability weight holds 0
  rows and 0 team matches of event ≥ t;
- no fixture of a round < t kicks off at or after the cut (no postponed match
  survives into training), no fixture of a round > t kicks off before it;
- the fallback's result set (event < t and kickoff date < cut date, as
  `fit_fallback` filters) has 0 late results; the fallback was never used
  (fallback share 0.00 at every origin, as the output prints);
- the odds row of every round-t fixture is the fixture's own match (date within
  one day of its kickoff), read from the pre-closing `Avg` columns only; 0 bad
  rows. Rows 10 per round, 11/13 on the doubles (26, 33, 36), 7–8 on the blanks
  (31, 34).
- Smallest gap between the last prior-round kickoff and the cut: 1 day 16:30
  (t=15), so every input also predates the real FPL deadline (90 minutes
  before the first kickoff).

Clubs come from `hist_pit.club_map` via `canonical_at(hist, t)`; the code
raises when the origin's club disagrees with the row's fixture (the item's own
test plants a GW6 transfer and a wrong map). Positions: no element carries
more than one `position` value in `merged_gw.csv`, so the adapter's
end-of-season position is the season's position.

### 1c Shift probe — N/A

The primary metric is a Brier score on a threshold hit, not a correlation on
points.

## Check 2 — clean-checkout suites — PASS

`git clone` of the worktree into the scratchpad, checked out at `385bd90~1`
(before) and `385bd90` (after), `FPL_DATA_DIR` unset,
`python -m unittest discover -p "test*.py" -s . -t .`:

- before (`d39ce45`): Ran 552 tests in 289.0 s, OK (skipped=10), 0 FAIL/ERROR.
- after (`385bd90`): Ran 559 tests in 290.6 s, OK (skipped=10), 0 FAIL/ERROR.

The 7 new tests are `tests/test_S13.py` (Maths ×3, Season ×3, CLI). Alone in
the tree: Ran 7 tests in 0.37 s, OK; hermetic (the S4/S5 toy season in a
temporary folder, toy odds, no network, no `C:\GIT\FPL-data`).

## Check 3 — the pre-registered evaluation re-run — PASS

1. `python tools/defcon.py --test --out <scratch>` from `C:\GIT\FPL-b` (5.9 s;
   defaults `historical/2025-26` and S5's 2025/26 odds file): the output is
   byte-identical (`cmp`, sha256 `74de36de…`) to
   `tools/out/defcon_test_2025-26.txt`. The in-process `test_2526` run is
   byte-identical too.
2. Independent recomputation in `pit.py` — my own loop over the raw rows, my
   own shrink, opponent factor from `Season2526.lambdas`, method-of-moments r
   and a negative-binomial tail by the recursive pmf (a different code path
   from `nb_logpmf`/`lgamma`), my own comparator and deciles; only
   `reliability_inputs`, `canonical_at`, `Season2526` and `bootstrap_mean`
   (all pinned by the prereg) shared:
   - row-level: every origin 5–38 has the same rows (pid, hit), r per position
     and max |ΔP| ≤ 1e-9 (asserted);
   - per-gameweek Brier (comparator and v2): max |mine − item| = 3.6e-16;
     n per gameweek identical; forwards n identical;
   - (a) mean comparator − v2 = −0.0188225937, 90% CI
     [−0.0247893045, −0.0128169088], n = 34, bootstrap p = 1.0e-4 → prints
     −0.0188 [−0.0248, −0.0128]; bar ≥ 0.005 with lower bound > 0: FAIL;
   - (b) pooled n = 5614; deciles (n, predicted, observed) identical to the
     item's to 1e-9; 1 of 10 within 0.05 (decile 6: 0.246 v 0.230); the next
     nearest is decile 5 at |diff| 0.05127, so the 1e-12 boundary tolerance
     changes nothing; bar ≥ 8: FAIL;
   - forwards (information): n 694, Brier comparator 0.01297, v2 0.02020,
     observed hit rate 0.013;
   - pre-registered result: FAIL (both must hold) — matches the item exactly.

## Check 4 — metric, filter, bootstrap, threshold as pre-registered — PASS

| Prereg | Code (`tools/defcon.py`) |
|---|---|
| Primary: Brier of P(DEFCON) v realised hit, per gameweek, comparator − v2 | `brier(prim, "p_cmp") − brier(prim, "p_v2")` per GW, `d = b_cmp − b_v2` |
| Sample: 60+ minutes, positions with a threshold; comparator keeps DEF/MID, v2 adds FWD 12; forwards shown separately; paired per GW on the same player-matches | `MIN_MINUTES = 60`; `THRESHOLDS = {2: 10, 3: 12, 4: 12}`; `COMPARATOR is E.DEFCON_THRESHOLD` (`{2: 10, 3: 12}`); the paired primary sample is DEF+MID (`PRIMARY_POS`), forwards printed separately; GW5–38 |
| Rate: season count / minutes × 90 over training rounds, shrunk to the positional median (180+ min) by the measured DEFCON reliability weight | `reliability_inputs(canonical_through(c, t−1), gws_played=t−1)`: `defcon90`, `priors[(pos,"defcon90")]` (prior_mins 180), `weights["defcon"]`; `shrunk_rate90` = own·w + prior·(1−w), the same formula as `backtest._p_defcon` |
| Opponent factor = λ_opp(fixture) / mean λ over the round's fixtures (S5's λ, fallback labelled) | `lam_opp / round_mean_lambda(round)` (mean over the round's team-fixtures); source label carried; fallback share printed (0.00) |
| r per position by moments on the training rounds, r = Σμ²/(Σ(x−μ)² − Σμ), clipped [0.5, 1000], Poisson when variance ≤ mean | `fit_dispersion`: exactly that; `R_LO, R_HI = 0.5, 1000`; `None` → Poisson pmf; training pairs = 60+-minute player-matches of rounds < t with the origin's own means |
| P = P(X ≥ threshold) under NB(μ, r); 2 × P | `nb_tail(mu, r, thr)`; the 2× is a print-side constant (not needed for Brier) |
| Comparator: hits / 60+-minute training matches at the current threshold; 0 for forwards and no match | `comparator_rate`; test proves 2·p_cmp == `defcon_expectation` on the toy |
| Bootstrap: unit gameweek, 10,000, 90% percentile, seed 20261018 | `BT.bootstrap_mean(d, seed=BT.SEED)` with `B = 10000`, `CI = 0.90`, `SEED = 20261018` |
| (a) mean ≥ 0.005 and lower bound > 0; (b) ≥ 8 of 10 deciles within 5 points (deciles of predicted P, pooled; predicted = mean P) | `PASS_BRIER = 0.005`, `boot["mean"] >= 0.005 and boot["lo"] > 0`; `calibration`: equal-count deciles sorted by P, predicted = mean P; `within(cal) >= CAL_MIN = 8`, `CAL_TOL = 0.05`; both must hold |
| Secondary: log loss, calibration table, r per position per origin, fallback share, forwards | all printed, none promoted |

No metric was promoted and nothing was re-tuned after the result: the item has
one code commit, the result is recorded as FAIL on both bars, and the output
regenerates byte-identically. The two post-first-run edits named by the caller
(the club-map consistency `raise` and the 1e-12 decile boundary tolerance)
change no number: the raise never fires on 2025/26 (my recomputation asserts
the same club agreement), and no decile sits within 1e-12 of the 0.05
boundary (nearest 0.05127).

Information only, no prereg conflict (the definitions are frozen):

- μ = rate × 90 for every 60+-minute match: 30.5 % of the 60+ rows in GW5–38
  are below 90 minutes (mean 85.4 minutes, mean minutes/90 = 0.949), so v2's
  mean is systematically above the per-match expectation for the sample,
  consistent with the over-prediction in deciles 7–10. The comparator's
  per-match hit rate absorbs partial minutes by construction.
- The moments fit uses the origin's own (in-sample) means on the training
  rounds; r falls from 17.9/10.9 at t=5 to about 8.5/8.2 by the second half.
- The pooled calibration and the primary metric use DEF+MID only (the
  comparator has no forward threshold), as the output header says; forwards
  appear only in the separate information line.

## Check 5 — recording path — PASS

The item is offline. `git diff --stat 385bd90~1 385bd90` lists only
`tests/test_S13.py` and `tools/defcon.py`; no runner file (`fpl_nightly.py`,
`fpl_ship.py`, `fpl_edge.py`, `fpl_sync.py`, `fpl_gate.py`, `fpl_publish.py`,
`fpl_hist.py`, `.github/`, `test_fpl.py`) nor any frozen tool it builds on
(`tools/backtest.py`, `tools/odds_lambda.py`, `tools/hist_pit.py`) changed, so
the recorded forecasts of every model cannot have moved. Run by me in the
tree: importing `fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate,
fpl_publish` loads nothing from `tools/` or `analysis/` (`[]`); the nightly
workflow references no `tools/` or `analysis/` path;
`tests/test_S3.py` (nightly isolation) and `tests/test_S13.py::CLI` passed in
the after suite. `projection_log.csv` was not regenerated (CLAUDE.md: the
runner is the only writer; `--record` is never run locally).

## Check 6 — mutation spot-check — PASS (8 of 8 red)

In a scratch clone of `385bd90` (`scratchpad/mut`; its `tools/defcon.py` is
the same blob `ee232db7…`, CRLF checkout only), one line changed per run,
`python -m unittest tests.test_S13`, then `git checkout -- tools/defcon.py`
(blob verified, suite green again). The tree's `tools/defcon.py` was never
edited.

| mutation | result |
|---|---|
| m1 training through t (`range(1, t)` → `range(1, t + 1)`) | RED: `test_point_in_time`, `test_comparator_reproduces_defcon_expectation` |
| m2 MID threshold 12 → 11 | RED: `test_thresholds_sample_and_the_opponent_factor`, `test_cli_and_isolation` |
| m3 opponent factor inverted (mean λ / λ_opp) | RED: `test_thresholds_sample_and_the_opponent_factor` |
| m4 Poisson limit only when variance < mean (`den <= 0` → `den < 0`) | RED (ZeroDivisionError): `test_dispersion_by_moments…` |
| m5 `nb_tail` sums one term too many (`range(k)` → `range(k + 1)`) | RED: `test_nb_tail_against_hand_sums_and_the_poisson_limit` |
| m6 comparator hit strict (`>=` → `>`) | RED: `test_comparator_reproduces_defcon_expectation` |
| m7 no shrink (own rate only) | RED: `test_thresholds_sample_and_the_opponent_factor` |
| m8 60-minute edge (`<` → `<=`) | RED: `test_thresholds_sample_and_the_opponent_factor` |

(A ninth attempt targeted a line that lives in `odds_lambda.py`, not in the
item; the patch did not apply and nothing ran.) The implementer's claim of
22 of 22 is not contradicted by anything I saw.

## Check 7 — secrets — PASS

`git diff 385bd90~1 385bd90` and `tools/out/defcon_test_2025-26.txt` grepped
for `apiKey=`, `api_key`, `Authorization`, `Bearer`, `x-api-key` and any
32+ character alphanumeric run: no hit. The odds CSV read by the item holds
no URL or key (0 matches for `apikey`/`http`). Nothing key-like to mask.

## VERDICT: PASS

The prereg (ruling verbatim at 01:09, template rows at 01:28) precedes the
single S13 code commit (04:25); the feature rebuilt at GW5, 21 and 38 from
truncated histories (later rows deleted, round-t stats scrambled, round-t
results blanked, later odds dropped) is identical to the item's output to
1e-9 in every probability, factor and dispersion, and at every origin 5–38
every training row, canonical row, fallback result and odds row predates the
origin's first kickoff; the clean-checkout suites run 552 → 559 tests, all
green; my regeneration is byte-identical to `tools/out/defcon_test_2025-26.txt`
and my independent recomputation matches the per-gameweek Brier scores to
4e-16 with the pre-registered result FAIL on both bars — (a) −0.0188
[−0.0248, −0.0128] against ≥ +0.005 with a positive lower bound, (b) 1 of 10
deciles against ≥ 8; metric, sample, bootstrap and thresholds are exactly the
prereg's with no promotion or re-tuning after the result; no runner file
changed and the nightly imports nothing from `tools/`; eight single-line
mutations each turn `tests/test_S13.py` red; no secret in any added or
changed file. The computation and the point-in-time discipline are right;
the item correctly records a FAIL of its own bar, so P(DEFCON) v2 drives no
decision and replaces nothing. The over-prediction in the top deciles is
consistent with the frozen μ = rate × 90 on a sample that is 30 % sub-90
minutes (information for the chat, not a defect of the item).
