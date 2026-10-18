# verify_S5 — backtest-verifier report

Item S5 (tools/odds_lambda.py, tests/test_S5.py, tools/odds/E0_2025-26_fetched_2026-10-18.csv,
tools/odds/E0_2026-27_fetched_2026-10-18.csv; outputs tools/out/odds_lambda_*.txt),
repository C:\GIT\FPL-b, branch lane-b, verified at code commit 01be62b (HEAD 7c724b5
adds only the report/CHANGELOG/state draft). Verifier model: Fable 5.1
(claude-fable-5-1), effort high, as .claude/agents/backtest-verifier.md on disk (read
first; it matches the loaded instructions). Model item with a pre-registered test:
checks 1-7 plus the prereg's acceptance tests 1-6. Date 2026-10-18. No key-like string
occurs in any file or output examined (nothing to mask). Scratch scripts and outputs
under the session scratchpad (leak_1a.py/.txt, shift_1c.py/.txt, audit_1b.py/.txt,
mutate.py/.txt, before/, after/, repro/, mut/, trunc_*). Nothing outside this file was
written in the repository; the data worktree C:\GIT\FPL-data was read only.

## Prereg before code — PASS

- prereg/S5.md committed f9ca3d0 (2026-10-18 15:40:27); Amendment 1 appended 94fbc36
  (15:43:22); odds CSVs df5d5fa; first and only code commit 01be62b (22:42:04).
  `git log -- tools/odds_lambda.py tests/test_S5.py` shows 01be62b alone.
- The ruling text ("RULING S5 ... points 1-3") and Amendment 1 (points 2 and 3 of
  RULING lane B go) are present verbatim in prereg/S5.md.
- `git diff 8e8583b..01be62b --stat`: tests/test_S5.py (+243) and tools/odds_lambda.py
  (+713) only.

## Check 1 — point-in-time leak check

### 1a Truncation test (decides) — PASS

Method (scratchpad leak_1a.py): for g in (5, 20, 38) a copy of historical/2025-26 with
merged_gw.csv rows of round <= g only (no later row), fixtures.csv events <= g only,
and a copy of the 2025/26 odds CSV holding only rows dated on or before the last kickoff
date of round g (50 / 200 / 380 rows). Two variants: T1 (round g's rows unchanged, so
pairings and outcomes exist) and T2 (as T1 with every outcome column of round g garbled:
minutes 90, points 50, clean sheets 0, GC 9, xG 3.0, BPS 99, ...; fixture g scores 7-7;
odds FTHG/FTAG 9-9). Rebuilt with the item's own `Season2526(hist, odds).lambdas(g)`
and `.week(g)` and compared with the full-file run (what `--test` graded).

| GW | compared (full vs truncated) | T1 | T2 |
|----|------------------------------|----|----|
| 5  | lambda_home/away of 20 fixtures, sources (all "odds") | 0.0, identical | 0.0, identical |
| 5  | bottomup forecasts 342 = 342; bottomup_lambda 342 = 342; p_start | 0.0 | 0.0 |
| 5  | Brier rows 94 = 94: p_model, p_lambda, lam_opp, outcome, pts; Brier (0.22287, 0.13046) | 0.0 | n/a (outcomes garbled by construction) |
| 20 | lambdas 20 fixtures; forecasts 336 = 336 both sources; p_start | 0.0 | 0.0 |
| 20 | Brier rows 99 = 99 all fields; Brier (0.16692, 0.12816) | 0.0 | n/a |
| 38 | lambdas 20 fixtures; forecasts 334 = 334 both sources; p_start | 0.0 | 0.0 |
| 38 | Brier rows 92 = 92 all fields; Brier (0.21082, 0.17780) | 0.0 | n/a |

Worst difference over every lambda, probability, forecast and Brier row: 0.0 (bar 1e-9).
The per-gameweek Brier pairs tie to the output file (GW5 0.2229/0.1305, GW20
0.1669/0.1282, GW38 0.2108/0.1778). The fallback never fired (every 2025/26 and 2026/27
fixture has an odds row); its code reads results with kickoff date < deadline date
(`fit_fallback`) and, in the 2025/26 harness, rounds < g; the round guard alone is a
no-op because of the date guard (mutation M3 below), the date guard alone and both
together go red (M2, M3+M2).

### 1b Timestamp audit (decides) — PASS

- 2026/27 (scratchpad audit_1b.py): GW5 deadline 2026-09-18T17:30Z, export used
  fpl_export_gw4_2026-09-17.json generated 2026-09-17T21:55:18Z (before); GW6 deadline
  2026-10-10T10:00Z, export fpl_export_gw5_2026-10-09.json generated
  2026-10-09T21:50:35Z (before). No export of gameweek g-1 generated at or after the
  deadline exists for either (the selection is the newest export with `generated <
  deadline` and gameweek = g-1). GW4: export fpl_export_gw3_2026-09-11.json (21:55Z,
  before the 12 Sep 12:30Z deadline) has no player_id and is refused by the frozen
  adapter — printed as excluded, not substituted. Fallback training set: finished
  fixtures with kickoff < deadline (latest 2026-09-14T19:00Z for GW5, 2026-09-20T15:30Z
  for GW6). Odds rows joined for all 10 fixtures of GW4/5/6 on the fixture's own date
  (row dates 18-20 Sep and 10-12 Oct), every row's columns tag "Avg" (all 60 rows of the
  2026/27 file; the 380 rows of 2025/26 likewise, zero B365 fallbacks).
- Loader probe on a CSV where Avg, AvgC, B365, B365C, PS and PSC all differ: the row
  with Avg gives exactly the Avg values; the row without Avg gives exactly the B365
  values; no closing or Pinnacle value is ever read. The code's only column tuples are
  `PRE_CLOSING = (("AvgH","AvgD","AvgA","Avg>2.5","Avg<2.5"), ("B365H",...,"B365<2.5"))`;
  no `*C*`, `PS*` or `P>2.5` name appears in the code (grep).
- 2025/26 historical side: for every origin g in 5-38 no row of a round < g kicked off
  at or after round g's first kickoff (0 of 34), and no fixtures.csv event's last kickoff
  is at or after the next event's first kickoff; so "rounds < g" is also "kicked off
  before g's first kickoff" (the deadline proxy, 90 minutes before it, is stated in the
  code and report).
- Stated limitation, carried from the prereg: football-data's pre-closing odds carry no
  fetch time; the row used for a fixture is the fixture's own match row, collected
  before kickoff but not provably before the FPL deadline. The Friday sensitivity
  (+0.0162 [+0.0091, +0.0242] without the 10 Friday-kickoff gameweeks) is printed as
  pre-registered. Not a FAIL: the limitation is pre-registered and the live source will be
  timestamped.

### 1c Shift probe (warns only) — WARN, cleared by 1a and 1b

Pooled over GW5-37 of 2025/26, players with 60+ minutes in both g and g+1, forecast at g
against points at g (unshifted) and at g+1 (shifted), scratchpad shift_1c.py:

| set | source | n | unshifted | shifted | difference |
|-----|--------|---|-----------|---------|------------|
| DEF/GK starters (the metric's set) | bottomup | 1614 | +0.1612 | +0.0970 | +0.0642 ok |
| DEF/GK starters | bottomup_lambda | 1614 | +0.2269 | +0.1143 | **+0.1126 WARN** |
| all gated players | bottomup | 4977 | +0.0648 | +0.0505 | +0.0143 ok |
| all gated players | bottomup_lambda | 4977 | +0.1234 | +0.0897 | +0.0337 ok |

The unshifted value stays under 0.25; the drop for the λ source on DEF/GK starters is
0.1126, 0.013 over the 0.10 line (bottomup's own drop is 0.064; the odds λ is a
stronger fixture term than the FDR-based ones the 0.02-0.06 range was measured on, and
the quintile spread +2.30 shows the same). Per the rule a WARN is cleared only by 1a and
1b; both passed with zero differences and every input dated before the deadline, so the
WARN is cleared. Reported here so the main session sees it.

## Check 2 — clean-checkout test runs — PASS

`git archive` of each commit into an empty folder (no historical/, no data; FPL_DATA_DIR
unset), scratchpad tests_before.txt / tests_after.txt:
- before (8e8583b): `python test_fpl.py` Ran 386, OK (skipped=8); `python -m unittest
  tests.test_S5` cannot import (module absent) — expected.
- after (01be62b): `python test_fpl.py` Ran 386, OK (skipped=8); `tests.test_S5` Ran 10,
  OK. Matches the implementer's counts (386 OK, 8 skipped; 10 OK).

## Check 3 — re-run of the pre-registered evaluation — PASS

From the worktree, `python tools/odds_lambda.py --season 2025-26 --test --out <scratch>`,
`--season 2026-27 --condition --out <scratch>`, `--fixture ARS CHE --out <scratch>`:
all three output files are byte-identical to tools/out/odds_lambda_test_2025-26.txt,
odds_lambda_condition_2026-27.txt and odds_lambda_fixture_ARS_CHE.txt (`diff` empty), so
every number matches within 1e-6: primary +0.0153, 90% CI [+0.0098, +0.0214], n=34,
PASS; Friday sensitivity +0.0162 [+0.0091, +0.0242], n=24; fallback 0 of 3193; log loss
+0.0368 [+0.0238, +0.0506]; proportional 0.1757 vs power 0.1757 (model 0.1910); DEF
quintile spread +2.30 by λ_opp (4.74, 4.23, 3.97, 3.21, 2.44, n=1394), −1.92 by undated
FDR; DEF/GK starters Spearman model +0.1257, λ +0.1800, diff +0.0543 [+0.0278, +0.0804],
s_d 0.0960, G 142.6; condition GW5 n=67 +0.0033/+0.1502 (+0.1469), GW6 n=66
+0.0696/+0.1977 (+0.1282), mean +0.1375 [+0.1282, +0.1469], n=2, PASS in form, power
142.6 gameweeks needed (have 2); rebuilt bottomup = log rows, max |diff| 0.000 on 256 and
246 rows; ARS v CHE GW3 source odds, λ 1.852/1.006, P(cs) 0.366/0.157.

## Check 4 — metric, sample, bootstrap, threshold as pre-registered — PASS

Read against prereg/S5.md and the code:
- Primary metric: Brier of P(clean sheet) per gameweek, paired difference bottomup minus
  bottomup_lambda (positive = improvement) — `primary_test`: `bm - bl` per gameweek,
  `BT.bootstrap_mean(diffs)`.
- Sample: 2025/26 GW5-38 (`first=5`, `last = hist["through"]` = 38), GK/DEF
  (`pos in (1, 2)`), 60+ minutes in the fixture (`H._num(r["minutes"]) >= 60`), among
  players through bottomup's recording gate (`mins_last4 >= 45`, the same gate as
  fpl_edge's record path) — the prereg's "compared where both exist".
- Bootstrap: unit gameweek, B = 10,000, 90% percentile, paired, seed 20261018 —
  backtest.py `B = 10000`, `CI = 0.90`, `SEED = 20261018`, `bootstrap_mean` percentile.
- Bar (a): `ok = mean >= PASS_BRIER (0.005) and lo > 0`; the test suite pins
  `PASS_BRIER == 0.005` (mutation M9 red). Bar (b): `ok = b["hi"] >= 0` on the
  per-gameweek Spearman difference λ − model for DEF/GK starters (P(start) >= 0.8, the
  prereg's own definition; `STARTER_P = 0.8`), with G at Δ = 0.02 from `power_gameweeks`
  at the s_d measured on 2025/26 — as written.
- 2026/27 range: the ruling says GW1 to the latest settled gameweek; the code iterates
  every settled gameweek (1-6; GW7 is not data_checked) and prints why GW1-4 contribute
  nothing. The prereg's "GW4 to latest" is a subset of the same loop.
- Secondaries (log loss, quintile spread, both sources' Spearman, proportional variant)
  and the Friday sensitivity are labelled information only in the output, report and
  CHANGELOG; the headline is the primary Brier. No metric was promoted.
- Re-tuning: one code commit; the model's constants are the prereg's (ξ 0.0065,
  < 4 weighted matches → league average, 15 goals, power de-margin); the fallback never
  fires so nothing in the result could have been tuned through it. The implementer's
  report says three first-round mutation survivors led to test changes (tests tightened,
  not the model) — not re-tuning on results.
- Two readings not spelled out in the prereg, both conservative and stated in the code
  and report: the 2025/26 fallback deadline = the round's first kickoff date (no recorded
  deadlines; results on that date are excluded); the 2026/27 "starters" = rebuilt
  P(start) >= 0.8 from the pre-deadline export.

## Check 5 — recording path — PASS

The item adds no recording code. `git diff 8e8583b..01be62b --stat` touches no runner
file (fpl_edge.py, fpl_hist.py, fpl_nightly.py, fpl_sync.py, fpl_gate.py,
fpl_publish.py, fpl_ship.py, .github/workflows unchanged). Nightly isolation: importing
fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish and fpl_hist loads no
module from tools/ or analysis/ (empty list, my own subprocess probe; the suite's
test_cli_and_isolation does the same). The projection log was not regenerated here (the
runner is the only writer; `--record` is never run locally); the data worktree
C:\GIT\FPL-data is clean before and after every run in this verification (`git status`
empty, HEAD e8629f0 "nightly 2026-10-18"). The item's own condition output shows the
rebuilt `bottomup` equal to the recorded log rows (max |diff| 0.000, 256 and 246 rows),
i.e. the frozen model is reproduced, not moved.

## Check 6 — mutation spot-check — PASS (11 of 14 red)

Scratch copy of the 01be62b archive (repository files untouched), one mutation at a
time in tools/odds_lambda.py, `python -m unittest tests.test_S5` after each (baseline
10 OK), scratchpad mutate.py / mutate.txt:
- M1 OddsBook.find matches any date (a later match's odds row usable): RED.
- M2 fit_fallback date guard dropped: RED (test_fit_uses_only_results_before_the_deadline).
- M3 Season2526.lambdas round guard alone (`event <= g`): SURVIVED — the implementer's
  stated no-op (the date guard excludes the same results).
- M3+M2 both guards dropped: RED (2 failures, including the primary point-in-time test).
- M4 load_odds reads closing columns first: RED.
- M5 expected_gc_penalty counts every goal: RED.
- M6 forecast_lambda gives MID the λ terms: RED.
- M7 the 60-minute condition dropped: RED.
- M8 pre_deadline_export accepts an export generated after the deadline: SURVIVED.
- M9 PASS_BRIER bar moved to 0: RED.
- M10 λ_total solves the CDF at 3 goals: RED.
- M11 power de-margin returns the proportional probabilities: RED.
- M12 P(clean sheet) ignores λ: RED (2 failures).
- M13 condition's starters threshold ignored: SURVIVED.
- M14 training through round g: RED (primary point-in-time test).
Information: M8 and M13 live in the 2026/27 condition path, which the suite exercises
only through the "no fpl.sqlite → rc 2" refusal; neither changes the recorded result
(1b shows no export of gameweek g-1 generated after the deadline exists, so M8 selects
the same file; the output's n = 67/66 starters against 256/246 rebuilt rows shows the
0.8 threshold in effect). A test gap, not a defect; the item's acceptance tests do not
require a toy-level condition test.

## Check 7 — secrets — PASS

grep over tools/odds_lambda.py, tests/test_S5.py, the three output files and both CSVs
for `apiKey=`, `Authorization`, `ODDS_API_KEY`, `api_key`, `Bearer`, `secret`, `token`,
`http://`, `https://` and any 32+ character alphanumeric run: no match. The CSVs hold
only match rows (380 and 60 data rows).

## Acceptance tests 1-6 of the prereg

1. De-margin proportional and power both sum to 1 within 1e-9 on hand cases
   (test_demargin; M11 red); the forecast uses the power method
   (`lambdas_from_odds(..., method="power")`, `Season2526` default). PASS.
2. λ_total by bisection on the Poisson CDF at 2 (M10 red); split by bisection on P(home
   win) with the Skellam sum to 15 goals (`p_home_win`, n = MAX_GOALS = 15); symmetric
   odds give λ_h = λ_a (test_lambda_total_and_split: split(2.0, p(1,1)) → 1.0/1.0). PASS.
3. Fallback: time-decayed Poisson team model, exp(−0.0065 × days), league average under 4
   weighted matches, source printed per fixture; fed a future result → red (M2). PASS.
4. bottomup_lambda = bottomup with the cs term's λ replaced and −P(start) × E[floor(GC/2)]
   (`lambda_terms`, `forecast_lambda`; MID/FWD identical to project_reliability, tested);
   stronger opponent → lower P(cs) (test_clean_sheet_moves_with_opponent_strength). PASS.
5. Point-in-time on three gameweeks within 1e-9 (check 1a: 0.0 on GW5/20/38); a mutation
   reading a later match's odds row → red (M1). PASS.
6. CLI `--season 2025-26 --test`, `--season 2026-27 --condition`, `--fixture ARS CHE`
   reproduced byte-identically; nightly isolation tested; tests in tests/test_S5.py; no
   key, `apiKey=` URL or Authorization header in any added file (check 7). PASS.

## Write guard

`git status --short` in C:\GIT\FPL-b after this report: only `?? worklog/verify_S5.md`;
nothing else touched (the data worktree C:\GIT\FPL-data is clean, HEAD e8629f0).

VERDICT: PASS

Reason: the prereg and its amendment were committed hours before the single code commit and the ruling text is verbatim; the three pre-registered outputs reproduce byte-identically through the item's own harness; the truncation rebuild of GW5, GW20 and GW38 from rows of round <= g only and odds dated no later than round g (and with round g's outcomes garbled) differs from the graded run by exactly 0.0 in every lambda, probability, forecast and Brier row; every 2026/27 export used was generated before its gameweek's deadline, the fallback trains only on results kicked off before the deadline, and only pre-closing Avg/B365 columns are read (closing and Pinnacle columns never, proved on a CSV where they differ); the metric, sample, bootstrap (B = 10,000, 90%, seed 20261018, paired by gameweek) and both bars are exactly the prereg's with no promotion or re-tuning; no runner file changed and the nightly imports nothing under tools/; 11 of 14 mutations go red (the three survivors are a documented no-op guard and two untested lines in the condition path that do not alter the recorded result); no secrets. The shift probe raises a WARN for the λ source on DEF/GK starters (drop 0.1126 against the 0.10 line, unshifted 0.2269 under 0.25), which checks 1a and 1b clear with zero-difference evidence; it is reported for the main session. The 2026/27 condition passes in form only (n = 2 against 142.6 gameweeks of power), as the output states; adoption of bottomup_lambda still needs Boris's acceptance in chat.
