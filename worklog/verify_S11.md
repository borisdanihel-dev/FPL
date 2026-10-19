# Verifier report — S11 (BUILD_PLAN.md Step 11, item H2, share-of-team allocation with 2024/25 priors, offline)

Verifier: Claude Fable 5.1 (backtest-verifier agent; `.claude/agents/backtest-verifier.md`
read from disk first — it matched the loaded instructions, so the file governs
without difference). Date: 2026-10-19. Worktree `C:\GIT\FPL-b`, branch
`lane-b`, HEAD `7f72141`. Nothing outside this file was written in the tree;
`C:\GIT\FPL` and `C:\GIT\FPL-data` were neither read nor written; no
`fpl_sync.py`, `--record`, `fpl_nightly.py` or `tools/planner.py --replay` was
run; the three background planner replays under `tools/out/planner/` were left
alone. All scratch work (the regenerated output, the clean clones, the
truncated histories, the mutation clone, `pit.py`, `trunc.py`, `audit.py`,
`mutate_s11v.py`) lives in the session scratchpad.

Note for the write guard: `git status` at the end of my run shows two untracked
files, `tools/gw_pass.py` and `tests/test_bundle.py`, which I did not create
or touch (the tree was clean at my start; they appeared during the run,
presumably the lane's bundle work). No tracked file is modified.

## Prereg order — PASS

- `prereg/S11.md`: the "RULINGS for after Step 8 ... RULING Step 11 ... END
  RULINGS (Step 11 part)" block committed verbatim in `7111240` (2026-10-19
  01:09:17 +0200); "RULING morning 19 Oct" (item 5, the 2024/25 download)
  added in `0df1443` (08:01:24); the template rows (hypothesis, data, pinned
  definitions, metric family, bootstrap, Holm threshold, acceptance tests,
  and the 2024/25 download record with URL, fetch time and SHA-256) in
  `47eed25` (08:06:31).
- The S11 code commit is `5c258e3` (08:22:04): `tools/shares.py` (+380) and
  `tests/test_S11.py` (+283), nothing else. The prereg precedes it.
- `git diff 7111240 HEAD -- prereg/S11.md` shows only the additions above; no
  row was edited after the code commit. `git diff 5c258e3 HEAD -- tools/shares.py`
  is the provenance wiring only (the `Run` import, the per-tool `--out`
  default `tools/out/shares`, `run.wrote`/`run.close`): 5 insertions, 2
  deletions, no definition or number touched. `tests/test_S11.py` unchanged
  after `5c258e3`. `tools/backtest.py` and `tools/odds_lambda.py` changed
  between `5c258e3~1` and HEAD only in their `main` (the same provenance
  wiring); the harness functions S11 pins (`load_2526`, `canonical_at`,
  `bootstrap_mean`, `Season2526`) are untouched. `test_fpl.py` untouched.
- Data: the three 2024/25 files hash to exactly the prereg's records
  (`merged_gw.csv` 5,125,595 bytes `5bbbcba6...`, `fixtures.csv` 751,413
  bytes `ce696e18...`, `teams.csv` 1,717 bytes `d10a6db8...`), as recomputed
  by me with `sha256sum`. 2025/26 is `historical/2025-26` (the vaastav copy
  of 2026-10-18), odds `tools/odds/E0_2025-26_fetched_2026-10-18.csv`
  (S5's file, the pre-closing `Avg` columns only).
- Output: `tools/out/shares/run.txt` names commit `7f72141...` = HEAD,
  0 modified tracked files, 7 s, sha256 `5eba2c41...` of
  `shares_test_2025-26.txt`.

## Check 1 — point-in-time — PASS

Scratch scripts against the real 2025/26 and 2024/25 folders, through the
item's own entry point `Season.origin(t)` and the pinned S4/S5 harness.

### 1a Truncation test — PASS (origins 5, 21, 38)

For each t a truncated copy of 2025/26 was written and origin t rebuilt from
it with a fresh `Season` (and the untouched 2024/25 folder): `merged_gw.csv`
rows of round > t deleted and, in the round-t rows, every column except the
pinned inputs (`name, position, team, element, fixture, round, was_home,
opponent_team, kickoff_time, GW`) overwritten with 99 (minutes, starts,
expected_goals, expected_assists, goals_scored, assists included);
`fixtures.csv` restricted to events ≤ t with round t's scores blanked and
`finished=False`; the odds file cut to rows dated ≤ the last round-t kickoff
+ 1 day.

| t | rows / fixtures / odds rows kept (date ≤) | sample | max abs diff over 12 fields (xg, xa, xg_cmp, xa_cmp, Z, s, s0, ms, m) | sources and prior labels | outcome read from round t |
|---|---|---|---|---|---|
| 5 | 3594 / 50 / 50 (2025-09-22) | 133 = 133, same pids | 0.0 | identical | realised goals = 99 × rows for 133/133 |
| 21 | 15770 / 210 / 210 (2026-01-09) | 129 = 129, same pids | 0.0 | identical | 129/129 |
| 38 | 29757 / 380 / 380 (2026-05-25) | 89 = 89, same pids | 0.0 | identical | 89/89 |

k per metric identical in every rebuild. So the round-t rows supply only the
fixture (via `fixtures.csv`), the club and the realised outcome; nothing of
round t or later moves a share, a prior, Z, the minutes share or a forecast.

2024/25 enters only through the priors and k: with `historical/2024-25`
perturbed (expected_goals × 1.5 on odd elements, expected_assists × 0.7 on
even), at t = 5, 21, 38 the current share, the comparator forecast, the
minutes share and m are unchanged to 0.0, while s0 moves for 121/133,
116/129, 77/89 rows and Z for every row (k xg 3.1846 → 3.0217, xa 3.4943 →
3.4507).

### 1b Timestamp audit — PASS (every origin 5–38)

Cut = the round's first kickoff (the S5 convention; 2025/26 has no recorded
deadlines; the real deadline is 90 minutes earlier). For every t in 5..38:

- every training row (rounds < t, minutes > 0) belongs to a fixture that
  kicked off before the cut: 0 late rows; every row's fixture event equals
  its round: 0 mismatches;
- no fixture of a round < t kicks off at or after the cut; no fixture of a
  round > t before it;
- the canonical slice behind P(start) and the position means holds 0 rows and
  0 team matches of event ≥ t;
- the odds row of every round-t fixture is the fixture's own match (same
  home/away, date within one day of the kickoff), pre-closing columns; 0 bad
  rows; source `odds` for every fixture of every round (fallback share 0.00,
  as the output prints); the fallback's result set (event < t, kickoff <
  cut) has 0 late results;
- `chance_next_round` is None for every player (the vaastav adapter carries
  no flag), so no late availability information enters P(start);
- the 2024/25 rows (27,605) kick off 2024-08-16 .. 2025-05-25, all before
  the 2025/26 GW1 kickoff;
- smallest gap between the last training kickoff and the cut: 1 day 16:30
  (t = 15); total violations 0.

### 1c Shift probe — N/A (information)

The primary metrics are correlations on goals and assists, not on points, so
the probe's thresholds (ceiling 0.15 / 0.25 on points) do not apply. For
information, pooled over GW5–37 among players with 60+ minutes in g and g+1
(n = 2875): v2 xG v goals(g) 0.307, v goals(g+1) 0.284; comparator 0.300 and
0.279. The shifted value is almost as high as the unshifted (difference
0.02–0.03), the signature of persistent skill, not of a leak; 1a and 1b decide
in any case.

## Check 2 — clean-checkout suites — PASS

`git clone` of the worktree into the scratchpad, checked out at `a01c862`
(= `5c258e3~1`, before) and `7f72141` (HEAD, after), `FPL_DATA_DIR` unset,
`python -m unittest discover -p "test*.py" -s . -t .`:

- before (`a01c862`): Ran 559 tests in 285.6 s, OK (skipped=10), rc 0.
- after (`7f72141`): Ran 571 tests in 314.3 s, OK (skipped=10), rc 0.

The 12 new tests are `tests/test_S11.py` (8: Hand ×4, Season ×3, CLI) plus
the provenance and S8/S9 test changes of `5423434`/`7f72141`. Alone, in the
tree and in the clean clone: `python -m unittest tests.test_S11` → Ran 8
tests, OK; hermetic (toy seasons in temporary folders, no network, no
`C:\GIT\FPL-data`).

## Check 3 — the pre-registered evaluation re-run — PASS

1. `python tools/shares.py --test --out <scratch>` from `C:\GIT\FPL-b` (8.2 s):
   the output is byte-identical to `tools/out/shares/shares_test_2025-26.txt`
   (`cmp` silent; both sha256 `5eba2c41...`); its `run.txt` names commit
   `7f72141...`, 0 modified tracked files.
2. Independent recomputation (`pit.py`): my own CSV reading and
   de-duplication, my own fixture-level team xG/xA totals, shares, priors
   (own-at-club by exact `name`, club-position mean over 180+ minutes,
   league-position mean), split-half k (odd v even rounds, 45+ minutes each
   half, my own tie-group Spearman, n = mean minutes/90 per half), minutes
   shares, forecasts, comparator, per-gameweek Spearman and log loss, Holm
   ordering; shared with the item only the prereg-pinned harness
   (`canonical_at`, `canonical_through`, `reliability_inputs` for P(start),
   `Season2526.lambdas`, `bootstrap_mean`):
   - k: xg 3.184597 (r 0.733615, n 8.770276, 471 players), xa 3.494331
     (r 0.715088, 471) — identical to the item's to the last digit;
   - every origin 5–38: the same sample (pid set), max |mine − item| = 0.0 for
     xg, xa, xg_cmp, xa_cmp, Z, s, s0, minutes share, m, realised goals and
     assists; prior-source labels and λ sources identical;
   - per-gameweek Spearman (v2 and comparator, both metrics) and log loss:
     max |mine − item| = 3.3e-16; n per gameweek identical; fallback rows 0;
   - goals: mean +0.0060599431, 90% [+0.0026646905, +0.0096204300],
     p = 0.0004; Holm level 95% (smaller p): [+0.0021039937, +0.0103964295]
     → lower bound > 0;
   - assists: mean +0.0043019505, 90% [+0.0003818943, +0.0082903273],
     p = 0.0698; Holm level 90%: [+0.0003818943, +0.0082903273] → lower
     bound > 0;
   - secondary log loss comparator − v2: +0.0066 [+0.0018, +0.0123];
   - pre-registered result: goals PASS, assists PASS — matches the item's
     printed numbers exactly (within 1e-10, far inside 1e-6).
3. The comparator is the same allocation with Z = 1: `xg_cmp = Σ λ × s × ms`
   with the same λ, the same minutes share and the same sample, verified row
   by row at every origin (and by mutation m2 below).
4. Information, not a prereg conflict: the assists result is fragile.
   With other bootstrap seeds (1, 2, 3) the assists 95% lower bound is
   −0.0001 to −0.0003 and p 0.060–0.068; its Holm level is 90% only because
   goals takes the 95% slot, and its 90% lower bound (+0.0004) sits 0.0004
   above zero. Goals is stable (95% lower bound +0.0021 to +0.0022 under every
   seed; t = 2.83 over 34 weeks, 22 positive / 12 negative). Assists: t =
   1.75, 20 positive / 14 negative. The prereg's seed 20261018 decides, and
   under it both lower bounds are positive.
5. The prereg's descriptive name-match numbers reproduce: 289 of the 441
   2025/26 players with 180+ minutes have a 2024/25 row by exact `name`,
   239 at their last 2025/26 club. Operationally the "own" prior needs
   2024/25 minutes > 0 at that club (233 of the 441); the rest take the
   club-position or league-position mean, as the table's own/club/league
   counts show (e.g. 85/28/20 at GW5).

## Check 4 — metric, filter, bootstrap, threshold as pre-registered — PASS

| Prereg | Code (`tools/shares.py`) |
|---|---|
| Sample: origin t, predicted starters P(start) ≥ 0.8 (the recording model's rebuilt `reliability_inputs` on `canonical_through(c, t−1)`), with a fixture in round t; GW5–38 | `STARTER_P = BT.STARTER_P` (0.8); `inp = reliability_inputs(canonical_through(canonical_at(hist, t), t−1), gws_played=t−1)`; `p_start < STARTER_P or not pos` → out; `club_fixtures(team, t)` empty → out; `--first 5`, `--last` = through (38) |
| Team xG/xA of a fixture = Σ rows of the club in that fixture | `team_totals` keyed (fixture, club) |
| Current share = Σ own / Σ team over the fixtures appeared in (any minutes), rounds < t; 0 with no appearance | `player_sums(..., rounds = range(1, t))`, `mins <= 0 → skip`; `share_of` 0 when team = 0; `s = 0.0` with no `agg` |
| Prior: own 2024/25 share at the same club (minutes there), else club-position mean (180+ minutes), else league-position mean (stated) | `Prior.prior`: `(name, club)` with minutes > 0 and team > 0 → "own 2024/25 at the club"; `club_pos[(club, pos)]` over `PRIOR_MINS = 180` → "club-position mean"; `league_pos[pos]` → "league-position mean (club without 2024/25 rows)"; AM rows excluded; a missing position raises |
| Z = m/(m + k), m = minutes/90 in training rounds; k = n(1 − r)/r per metric on 2024/25, r = tie-corrected Spearman odd v even among 45+ minutes each half, n = mean minutes/90 per half; r's 95% interval printed | `z = m / (m + k[key])`; `credibility_k`: odd/even `player_sums`, `HALF_MINUTES = 45`, `E._spearman`, `n = mean(mins/90)`, `k = n(1−r)/r`; r ≤ 0 raises; printed with ±1.96/√(n−1) |
| Expected minutes share = P(start) × m_start/90, m_start = mean minutes in starts, else the position mean | `ms = p_start * m_start / 90`, `m_start = start_minutes/starts` else `pos_mean_start[pos]` |
| Forecast = Σ round-t fixtures λ_team × shrunk share × minutes share; goals = xG, assists = xA; manager line | `row[key] = Σ lam * shrunk * ms`; `MANAGER_LINE` printed |
| Comparator = the same with Z = 1 | `row[key + "_cmp"] = Σ lam * s * ms` |
| Primary: per-GW tie-corrected Spearman (`fpl_edge._spearman`) of forecast v realised goals, and v realised assists, v2 − comparator, paired on the same starters | `E._spearman(forecast, real)` on the same `rows`; `diffs = rho − rho_cmp` |
| Bootstrap: unit gameweek, 10,000, 90% percentile, seed 20261018, two-sided bootstrap p | `BT.bootstrap_mean(v, seed=SEED)`; `B = 10000`, `CI = 0.90`, `SEED = 20261018` |
| Holm at 90%: smaller p at α 0.05 (95% interval), then the other at α 0.10 (90%), stop at the first failure; adopt only if the Holm-adjusted lower bound > 0 | `holm_intervals`: order by p, `level = 1 − 0.10/(2 − i)` → 0.95 then 0.90; `ok = not stop and lo > 0`; `adopt = ok`; `stop` after a failure |
| Secondary: log loss of P(goal) = 1 − exp(−xG), pooled Spearman, k and r, name-match rate, fallback share | log loss printed and bootstrapped; k, r, n, players printed; fallback column; the pooled Spearman and the name-match rate are not printed (information only; computed by me above) |

No metric was promoted and nothing was re-tuned after the result: one code
commit holds the logic, the later diff is provenance-only, every constant
equals the prereg, and the output regenerates byte-identically at HEAD.
Whether any code existed before `47eed25` cannot be seen in git (the output
file is ignored); the git order is prereg → code.

## Check 5 — recording path — PASS

The item is offline. `git diff --name-only 5c258e3~1 HEAD` lists only
`tests/*` and `tools/*`; no runner file (`fpl_nightly.py`, `fpl_ship.py`,
`fpl_edge.py`, `fpl_sync.py`, `fpl_gate.py`, `fpl_publish.py`, `fpl_hist.py`,
`.github/`, `test_fpl.py`) changed, so the recorded forecasts of every model
cannot have moved. Run by me in the tree with `python -I`: importing
`fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish` loads
nothing from `tools/` or `analysis/` (`[]`); `.github/workflows/nightly.yml`
references no `tools/` or `analysis/` path; `tests/test_S3.py` (nightly
isolation) and `tests/test_S11.py::CLI` passed in the after suite.
`projection_log.csv` was not regenerated (CLAUDE.md: the runner is the only
writer; `--record` is never run locally).

## Check 6 — mutation spot-check — FAIL (8 of 9 red; one survivor)

In a scratch clone of `7f72141` (`scratchpad/mut11`; its `tools/shares.py` is
the same blob `d80589a...`), one line changed per run, `python -m unittest
tests.test_S11`, the file restored from `src0` and `git checkout --` after
(blob verified, suite green again). The tree's `tools/shares.py` was never
edited.

| mutation | result |
|---|---|
| m1 training through t (`range(1, t)` → `range(1, t + 1)`) | RED: `test_point_in_time`, `test_sample_forecast_and_comparator` |
| m2 comparator uses the shrunk share (Z ≠ 1) | RED: `test_point_in_time`, `test_sample_forecast_and_comparator` |
| m3 k = n(1 − r) instead of n(1 − r)/r | RED: `test_credibility_k_by_hand` |
| m4 club-position mean skipped (straight to the league mean) | RED: `test_prior_cases`, `test_name_match_club_change_and_promoted` |
| m5 Holm: both metrics at 90% | RED: `test_logloss_and_holm_by_hand`, `test_point_in_time` |
| m6 a 0-minute appearance counts in the share | RED: `test_shares_and_team_totals` |
| m7 prior population: any minutes instead of 180+ | RED: `test_prior_cases` |
| **m8 minutes share ignores P(start)** (`ms = p["p_start"] * m_start / 90.0` → `ms = m_start / 90.0`) | **GREEN — survived**: Ran 8 tests, OK |
| m9 Z from m + 1 instead of m + k | RED: `test_sample_forecast_and_comparator` |

Why m8 survives: in the toy season every sampled player (P(start) ≥ 0.8) has
P(start) exactly 1.0 and 90 minutes per start (checked: origin 5 → 26 rows all
at p_start 1.0, ms 1.0; origin 6 → 27 rows all 1.0; the CLI toy likewise), so
`assertAlmostEqual(r["ms"], p["p_start"] * m_start / 90)` and
`assertLessEqual(r["ms"], p["p_start"])` hold with or without the factor, and
the 70-minute case only exercises m_start. The prereg's acceptance test "the
forecast = λ × share × minutes share" with minutes share = P(start) ×
m_start/90 is therefore not discriminating for the P(start) factor. The code
itself is right — my independent recomputation applies P(start) × m_start/90
and matches every forecast to 0.0 at every origin — but a test must go red
for a broken line of the new logic, and here none does. The implementer's
"20 of 20 mutations red" is not contradicted (that set need not include this
line); the gap is in coverage. A toy player with 0.8 ≤ P(start) < 1 in the
sample (e.g. 3 starts in the last 4 rounds) would close it; no evaluation
number changes.

## Check 7 — secrets — PASS

`grep -i` over `tools/shares.py`, `tests/test_S11.py`, `tools/provenance.py`,
`tests/test_provenance.py`, `prereg/S11.md`,
`tools/out/shares/shares_test_2025-26.txt` and `run.txt` for `apiKey=`,
`api_key`, `Authorization:`, `Bearer `, `ODDS_API_KEY` and 32+-hex strings:
only the data-file SHA-256 records in the prereg, the test's sha256 of
"hello\n" and the commit hash in `run.txt`. No key, no keyed URL, no header
value. The code reads local CSVs only and makes no network call.

## VERDICT: FAIL

The measured result stands exactly as recorded: the prereg (ruling verbatim,
definitions, data hashes) precedes the single code commit; the output
regenerates byte-identically at HEAD; my independent recomputation reproduces
k, every share, prior, Z, forecast and comparator to 0.0, every per-gameweek
Spearman to 3e-16, and the intervals, p-values and Holm levels to 1e-10
(goals +0.0061, Holm 95% [+0.0021, +0.0104]; assists +0.0043, Holm 90%
[+0.0004, +0.0083]; both lower bounds > 0, adoptable under the ruling,
adoption needing Boris); the truncation test and the timestamp audit find no
leak; the suites are green before (559) and after (571); nothing on the
runner path changed; no secrets. The item fails on check 6 only: a mutation
that drops the P(start) factor from the expected minutes share survives the
tests, because every sampled player in the toy season has P(start) = 1.0, so
the prereg's acceptance test for the minutes share does not discriminate.
This is a test-coverage gap, not a model or number defect; closing it needs
only a toy starter with 0.8 ≤ P(start) < 1 in the sample and a red-then-green
run, after which the item can be re-verified without any change to the
evaluation. Information for the chat, not a verdict factor: the assists
result is fragile (other bootstrap seeds put its 95% lower bound just below
zero; its 90% lower bound is +0.0004), while the goals result is stable under
every seed tried.
