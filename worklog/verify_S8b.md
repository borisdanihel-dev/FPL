# verify_S8b — the planner without hits on xp_v2, 2024/25 (tools/planner_2425.py)

Verifier: Claude Fable 5.1 (claude-fable-5-1), effort high, run natively as
`backtest-verifier`; `.claude/agents/backtest-verifier.md` was read from disk
first and matched the loaded instructions. Worktree
`C:/Users/Boris/AppData/Local/Temp/claude/C--GIT-FPL/442a647f-7693-4ced-b840-0df7f5bfd943/scratchpad/s8b`,
branch `s8b-wip`, HEAD `7580cf2` (base `21d1c3a` = s6e2-wip), tree clean
before my checks. Date 2026-10-20, 12:20-13:50 local. Nothing outside this
file was written in the worktree; every scratch file lives in the session
scratchpad (`verify_s8b/`: `pit.py`, `run5.py`, `mutate.py`, their outputs,
and `git archive` copies `clean_before/`, `clean_after/`, `mut/`). The inputs
`C:/GIT/FPL/historical` (2024-25, 2023-24, 2026-27) and
`tools/odds/E0_2024-25_fetched_2026-10-19.csv` were read only; temporary
copies of the history were made for the truncation tests and deleted.
`C:/GIT/FPL-data` was read only (HEAD `e1154dd`, nightly 2026-10-19; never
pulled, synced or recorded). The full 4 h 10 min run was not rerun, as
instructed; the 5-squad full-season run below (3,727 s) and the
origin-level checks were my own. sha256 values are masked (first 4, then
"...").

## Prereg and rulings

`prereg/S8b.md` lives on master: `bd4d044` (2026-10-20 08:13:56 +0200)
precedes the first S8b code commit `401fb20` (08:26:56 +0200) and the test
commit `7580cf2` (08:33:24). It carries BUILD_PLAN Part F item F-F verbatim
and the "Ruling, Mon 19 Oct night" verbatim (points 1-6; point 5 sets the
lambdas: odds-implied for week t, the fallback fitted on results before the
origin for t+1..t+5, the source recorded per fixture). The item's range
`21d1c3a..7580cf2` changes two files only: `tools/planner_2425.py` (+223)
and `tests/test_S8b.py` (+153). `tools/planner.py`, `tools/xp_v2_live.py`,
`tools/xp_v2_replay.py`, `tools/xp_v2_2425.py`, `tools/odds_lambda.py`,
`tools/shares.py`, `tools/rules.py`, `fpl_edge.py` and `fpl_hist.py` are
untouched in that range, so "S8's replay loop unchanged" and "xp_v2 as
tested" rest on unchanged blobs.

## The task's seven points, in order

1. **S8's loop unchanged with hits forbidden.** `run()` calls
   `PL.replay(hist_dir, n_squads=50, seed=7, decay=0.85,
   schedule_name="boris", boot_seed=20261018, first=2, last=38,
   check_decays, hits_allowed=False)` inside `season_2425(...)`, which
   rebinds `PL.Replay` to a `Season2425` factory for the block and restores
   it in `finally`. `Season2425(PL.Replay)` overrides `forecasts` only;
   `market`, `squad_rows`, `realised` and the loop (prices of round t, clubs
   by hist_pit, 1 FT a week, bank to 5, no chips, `baseline_plan`) are
   S8's. The test `test_s8_loop_unchanged_with_hits_forbidden` asserts the
   kwargs, hits 0 on both sides, and the restore; my mutations v3 (hits
   allowed), v7 (decay 0.80) and v12 (not restored) each go red. The run
   output and my run both show transfers 37.0 / hits 0.0 on both sides
   (one FT a week over GW2-38 = 37; the baseline never rolls here).
2. **The forecasts.** `xp_week` calls `XL.core` (S6d's core, held to S6b's
   `Replay.xp_v2` by S6d's test) on `reliability_inputs(canonical_through(c,
   t-1))` with week u's fixtures (`s11.club_fixtures(team, u)`) and
   `horizon_lambdas(t, u)`: for u == t exactly `s5.lambdas(t)` (S5's odds
   row of the fixture, else S5's fallback); for u > t
   `OL.fixture_lambdas(None, model_t, ...)` with `model_t =
   fit_fallback(results of event < t, s5.deadline(t))` — the book is passed
   as `None`, so an odds row cannot be read. On the real data at origins 2,
   20 and 38: week t equals `xp_v2_replay.Replay.xp_v2(t)` with max |diff|
   0.000e+00 and no key mismatch (n 224 / 337 / 332); the `if v` filter
   drops nothing (0 exact zeros among 1,344 / 1,943 / 2,022 / 1,842 / 332
   core values at origins 2, 10, 20, 30, 38; minimum value 0.25). Sources:
   my regenerated `sources.csv` is byte-identical to the run's (sha256
   9a2b...); counts week t odds 370 (37 origins x 10), later weeks fallback
   1,700 (32 x 50 + 40 + 30 + 20 + 10), no odds row in any later week.
3. **The outcomes.** `self.rp.actual = XR.actuals_from(rescored)` replaces
   S8's official-points actuals with S10b's `normalise_season` re-score
   (2026/27 table, bonus official, DEFCON missing on every row; the tool
   refuses counts via `F.check_no_counts`). My regenerated re-score has
   sha256 49f8..., identical to the run's `rescored_2024-25.csv` and to
   `run.txt`. `realised` is S8's unchanged (XI and captain by the week's
   forecast, captain doubled, `rule_autosubs` on realised minutes). The
   test `test_the_outcomes_are_the_rescore` and my mutation v5 (re-score
   not installed, red) cover the wiring.
4. **Point-in-time.** Check 1 below: truncation and junk at origins 2, 20,
   38 give 0.000e+00 differences over all six weeks; timestamp audit clean.
5. **Assistant-manager rows.** 2024/25 has 322 rows of position AM (20
   elements 735-754, rounds 23-38, minutes 0, prices 0.5-1.5). The frozen
   adapter gives them pos 0. Where they reach: `canonical_at` (20 players,
   pos 0), `reliability_inputs` (p_start 0.0, mins_last4 0 -> gated out of
   `core`: 0 AM forecasts at t = 23, 30, 38), `market` (20 rows, pos 0) and
   therefore `build_pool` under key 0. They cannot reach a plan:
   `plan_candidates` and `baseline_plan` draw only `pool.get(out["pos"])`
   for squad rows, whose pos set is {1, 2, 3, 4} (GW1 squads predate round
   23 and incoming players come from those pools), and `xi_value` never
   sees a pos-0 row. They are absent from the re-score (S10b's
   `load_season` drops them: "20 manager rows out"), from `ict_percentile`,
   `sub_inputs_2526` and S11's `player_sums` (minutes 0). Decisive test: a
   history copy with every AM row deleted gives, at t = 23, 30 and 38,
   identical forecasts (all six weeks), identical p_start and pos apart
   from the AM keys themselves, an identical market apart from the AM
   rows, identical ranked plans (keys and scores; 210-248 plans) and
   baseline for squads 0 and 1, identical realised points, and identical
   sampled squads. No plan or result can change. (S15's greedy builder
   crashed on them; S8's pool-by-position path does not.)
6. **Tests and mutations.** Check 2 and check 6 below: suites 709 OK / 10
   skipped at `21d1c3a` and 715 OK / 10 skipped at `7580cf2`, matching the
   main session; b2 judged equivalent (reasoning below); my 13 mutations:
   11 red, 2 equivalent survivors.
7. **Provenance, isolation, secrets, no tuning.** `run.txt`: tool
   `tools/planner_2425.py`, args `--test --hist C:/GIT/FPL/historical`,
   commit `401fb20` (the code commit, 06:26:56 UTC; the run started
   06:26:57 UTC), modified tracked files 0, end 10:35:35 UTC, 14,918 s;
   the three output sha256s (49f8..., 9a2b..., 18b3...) equal the files on
   disk, whose mtimes (12:35:35 local = UTC+2) equal the recorded end. The
   only commit after the run started is `7580cf2`, which adds
   `tests/test_S8b.py` and nothing else (`git diff --stat 401fb20
   7580cf2`); the tree is clean, so no code moved after the result. No
   runner file changed (`git diff 21d1c3a 7580cf2 -- .github fpl_*.py
   test_fpl.py` is empty); `.github/workflows/nightly.yml` and
   `fpl_nightly.py` contain no reference to `tools/` or `analysis/`; the
   isolation test in `tests/test_S8b.py` (the nightly's modules import
   nothing named planner_2425, planner or xp_v2_2425) passes in both clean
   copies. Secrets: check 7.

## Check 1 — point-in-time leak check — PASS

- **1a truncation (decides).** For origins 2 (earliest), 20 (middle) and 38
  (latest) a temporary history root: every `merged_gw.csv` row of round > t
  deleted, every round-t row's statistics junked (minutes 90, starts 1,
  points 33, every xG/ICT/score column 7.7; element, round, fixture, team,
  was_home, kickoff and `value` kept, since S8's market reads the origin's
  price and club from round t), every `fixtures.csv` score of event >= t
  blanked, and the odds file cut to rows dated before round t+1's first
  kickoff (20 / 199 of 380 rows kept at t = 2 / 20). `Season2425.forecasts(t)`
  on the copy against the full data: max |forecast diff| over all six weeks
  0.000e+00, max |p_start diff| 0.000e+00, pos identical, the same weeks,
  the recorded sources identical, at all three origins. The junk variant
  (every row of round >= t junked, every result of event >= t set 9-0, the
  full odds file) also gives 0.000e+00 at all three origins.
- **1b timestamp audit (decides).** Deadline = round t's first kickoff
  (S5's `deadline(g)`: 2024-08-24 11:30, 2025-01-04 12:30, 2025-05-25 15:00
  UTC). Training rows (round < t) with kickoff >= deadline: 0 at each
  origin; fallback results (event < t) dated on or after the deadline date:
  0 of 10 / 189 / 370; later weeks' sources: {fallback} only. Across the
  whole season no fixture of round r kicks off at or after round r+1's
  first kickoff, no fixture of event >= t is dated before round t's first
  kickoff date, and every `merged_gw.csv` row's fixture event equals its
  round (27,605 rows). Week t's odds rows are dated the kickoff day
  (difference 0 days at every origin) and read the pre-closing columns
  (Avg*, else B365*): this is S5's accepted source and the night ruling's
  point 5 names it for week t; it is information, not a finding.
  Inherited from S8 and S6b, unchanged here: the fixture pairings of weeks
  t+1..t+5 are the final schedule (a rescheduled fixture is not
  point-in-time), and round t's price is vaastav's `value` for that round.
- **1c shift probe.** Not applicable: the primary is realised season points,
  planner minus baseline, not a correlation.

## Check 2 — clean-checkout test runs — PASS

`git archive` of each commit into the scratchpad, `FPL_DATA_DIR` unset,
`python -m unittest discover -p "test*.py"` from the archive root:
- before (`21d1c3a`): Ran 709 tests in 325 s, OK (skipped=10);
- after (`7580cf2`): Ran 715 tests in 349 s, OK (skipped=10).
Both match the main session's counts. `tests.test_S8b` alone: 6 tests, OK
(21.7 s) on the mutation copy before mutating.

## Check 3 — the pre-registered evaluation, rerun in part — PASS

The real run's per-squad results are not recorded (only the means, the
bootstrap and the first five squads' disagreement counts), so the
comparable quantities are those. My in-process run of the committed code
on the first 5 squads over GW2-38 with the decay checks on (the first 5 of
50 are the 5 of n=5: `sample_squads` draws sequentially from one seeded
rng, confirmed by id lists), 3,727 s:

| quantity | real run (50 squads) | mine (first 5) |
|---|---|---|
| decay 0.80/0.90 disagreements, squads 1-5 | [7, 3, 5, 8, 6] of 37 | [7, 3, 5, 8, 6] of 37 |
| lambda sources | week t odds 370, later fallback 1,700 | the same; `sources.csv` byte-identical (sha256 9a2b...) |
| re-score | sha256 49f8... | sha256 49f8... |
| transfers / hits, planner and baseline | 37.0 / 0.0, 37.0 | 37 / 0, 37 on every squad |
| planner, baseline points (mean) | 2074.9, 2055.3 | 2091.2, 2054.2 |
| paired gain | +19.58 [+1.28, +38.70] | +37.00 [-23.60, +95.00] (5 squads: no bar rests on it) |

Per squad (mine): planner 2040 / 2221 / 2018 / 2072 / 2105, baseline 2043
/ 2069 / 1972 / 2161 / 2026, gains -3, +152, +46, -89, +79. The matching
counts are deterministic functions of the forecasts, market and plans for
185 squad-weeks x 3 decays, so they tie my run to the real run's plans;
the 5-squad spread (sd ~93) is consistent with the 50-squad interval
(half-width 18.7 -> per-squad sd ~80). The report header, the bar line and
the robustness line in `s8b_2024-25.txt` match `run.txt` and the code's
constants. Differences in the comparable quantities: 0 (bar 1e-6).

## Check 4 — metric, filter, bootstrap, threshold — PASS

Code against the prereg: primary = per squad, planner − baseline season
points over GW2-38 (`gains` in `PL.replay`, `first=2`, `last=38`); sample =
50 squads, seed 7, 2024/25 GW1 ownership (`CH.N_SQUADS`, `CH.SQUAD_SEED`,
`gw1_candidates`); `hits_allowed=False`, `DECAY = 0.85`, `SCHEDULE =
"boris"` (1.5, 1.0, 0.6, 0.3), bank to `MAX_FT` 5, no chips; bootstrap unit
= squad, `BT.B` 10,000, `BT.CI` 0.90, `boot_seed = PL.SEED = BT.SEED =
20261018`; bar `pass_ = mean >= PASS_GAIN (5.0) and lo > 0`. The report
prints these verbatim and labels PASS "(adoption needs Boris)". Secondary
lines (transfers, S8's robustness line, the lambda sources) are
information only, as pre-registered. The lambdas follow the night ruling's
point 5 exactly (week t odds-implied else fallback; t+1..t+5 the fallback
on results before the origin; source per fixture recorded). No metric was
promoted and nothing was re-tuned after the result: the code commit
predates the run by one second and the only later commit adds tests.

## Check 5 — recording path and isolation — PASS

The item is offline. No runner file changed in `21d1c3a..7580cf2`;
`nightly.yml` and `fpl_nightly.py` reference nothing under `tools/`; the
isolation test passes in both clean copies. `C:/GIT/FPL-data` was not
touched: status clean, HEAD `e1154dd` (nightly 2026-10-19),
`projection_log.csv` sha256 6271... (mtime 08:08 local today, before this
verification; the runner is the only writer, so `--record` was not run).
There is no code path by which this item could move the log.

## Check 6 — mutation spot-check — PASS (11 of 13 red, 2 equivalent)

Scratch copy of `7580cf2` (`verify_s8b/mut`), one change at a time in
`tools/planner_2425.py`, `python -m unittest tests.test_S8b`, the file
restored and re-checked identical after each:

| mutation | result | failing test(s) |
|---|---|---|
| v1 later weeks read the week's own odds (`s5.lambdas(u)` for u > t) | RED | 5 tests (week-t/fallback, later rows, loop, bar, outcomes) |
| v2 fallback on results < u at `deadline(u)` (later results leak) | RED | week-t/fallback, later rows never move, loop, bar |
| v3 `hits_allowed=True` in the replay call | RED | loop unchanged with hits forbidden |
| v4 bar `lo >= 0` | RED | the bar |
| v5 re-score not installed (official points kept) | RED | the outcomes are the re-score |
| v6 zeros kept in the week's forecast (`dict(xp)`) | GREEN | equivalent, see below |
| v7 `DECAY = 0.80` | RED | loop unchanged |
| v8 = main session's b2: results < u at `deadline(t)` | GREEN | equivalent, see below |
| v9 sources not recorded | RED | week-t/fallback (sources) |
| v10 week t on the fallback too (`if u == t` branch removed) | RED | week-t/fallback |
| v11 `PASS_GAIN = 4.0` | RED | the bar |
| v12 `PL.Replay` not restored after the block | RED | restored-after-error, loop unchanged |
| v13 horizon one week short | RED | week-t/fallback (six weeks) |

- **b2 / v8 judged equivalent.** `fit_fallback` keeps only results whose
  kickoff date is strictly before the deadline date, and the deadline stays
  `deadline(t)`; a result of event in [t, u) can enter only if dated before
  round t's first kickoff, and in 2024/25 no fixture of event >= t is (0
  cases over all t; rounds are date-monotone). The toy season is the same.
  So `< u` and `< t` select the same results: the claim holds, and the
  explicit `< t` guard is the belt to the fallback's braces. (v2 shows the
  tests do catch a real leak when the deadline moves.)
- **v6 judged equivalent.** No exact-zero value exists on the real data at
  five origins, and every consumer in `planner.py` reads `xp.get(pid,
  0.0)` (`squad_by_pos`, `decayed`, `realised`), so a present zero and an
  absent key are the same number everywhere; `build_pool` iterates market
  rows, not the xp dict. A test gap at most, with no behavioural reach.

## Check 7 — secrets — PASS

`git grep` over `tools/planner_2425.py` and `tests/test_S8b.py` at
`7580cf2`, and grep over `tools/out/planner_2425/*.txt`, for `apiKey=`,
`Authorization`, `ODDS_API_KEY`, `sk-...` and 32-hex strings: no hit other
than the commit id in `run.txt` and the sha256 lines (not keys). The tool
reads a local CSV of odds and the local history; no URL, header or key
appears in the item's files or outputs.

## Information (no bar, no action)

- 2024/25 carries no DEFCON counts, so neither side has DEFCON (stated in
  the prereg and the report as a limitation).
- The 5-squad subset's own bar line prints FAIL because its interval
  covers 0 at n = 5; it is a subset for reproduction, not an evaluation.
- Other Python processes were running on the machine during my checks
  (the main session's reruns); my run wrote only to `verify_s8b/`.

VERDICT: PASS

The prereg (`bd4d044`, F-F and the night ruling verbatim) precedes the code; S8's replay loop runs unchanged with hits forbidden on the pre-registered configuration with only the season class swapped and restored; week t's forecast equals S6b's xp_v2(t) to 0.0 at origins 2, 20 and 38 and later weeks use the origin's fallback and never an odds row; truncation and junk tests at those origins move no forecast by more than 0.0 and every input row is dated before the origin's deadline; the outcomes are S10b's re-score (hash identical to my regeneration); the clean-checkout suites are 709 and 715 OK with 10 skipped; my 5-squad full-season run reproduces the real run's disagreement counts [7, 3, 5, 8, 6], its sources file byte for byte and its transfer and hit counts; the metric, sample, bootstrap and bar are the prereg's with nothing promoted or re-tuned after the result; the assistant-manager rows reach the market with pos 0 but provably cannot enter a plan or a result; 11 of 13 mutations go red and the two survivors (the main session's b2 and zeros-kept) are behaviourally equivalent; no runner file changed, the nightly imports nothing new, and no secret appears. The measured result (+19.58 per squad-season, 90% CI [+1.28, +38.70], PASS on the bar) stands as recorded; adoption still needs Boris's acceptance in chat.
