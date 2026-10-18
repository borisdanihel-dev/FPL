# Verifier report: S2, pre-check (before the merge to master)

- **Model / effort:** Fable 5.1 (`claude-fable-5-1`), effort high, as set in `.claude/agents/backtest-verifier.md`.
- **Verifier:** backtest-verifier (native). I read `.claude/agents/backtest-verifier.md` from disk first; it is identical to the loaded instructions, so the file governed without conflict.
- **Item:** S2 (BUILD_PLAN.md Step 2, item D2). Prereg `prereg/S2.md` at `9694334`.
- **Code checked:** branch `s2-wip`, head `04acd7d`, branched from master `9694334`; GitHub `origin/s2-wip` = `04acd7d`. Master is `ce830c4` (docs only since the prereg: `worklog/SESSION_STATE.md`). `git diff 9694334 s2-wip` touches `fpl_edge.py`, `fpl_gate.py`, `fpl_hist.py`, `fpl_nightly.py`, `fpl_sync.py`, `test_fpl.py`, `tools/migrate_data_branch.py` (+1305 / -117). `p1_eval.py` is untouched.
- **Data checked:** `C:\GIT\FPL-data` at `e84bee6` (nightly 2026-10-17), read only; every run used a clone of it.
- **Rulings checked:** the verbatim `RULING S2:` block, points 0-5, in `prereg/S2.md`, plus BUILD_PLAN.md Step 2 points 1-11 as at `69b360d`. I read no session transcript or chat log; `worklog/SESSION_STATE.md` was read only as a set of claims to test.
- **Scratch:** everything ran in `C:\Users\Boris\AppData\Local\Temp\verify_S2_pre\` (clones `code_master` = `ce830c4`, `code_s2` and `code_s2_mut` = `04acd7d`, `code_master_s2tests` = master code with the s2-wip test file, `data` + copies `data_m`, `data_s` = `e84bee6`, a bare `origin_bare.git`, a stand-in time zone under `tz\`). The folder has been deleted. Driver scripts lived in the session scratchpad, outside the project.
- **Pushes:** only to `origin_bare.git`, after repointing the data clone's origin to it. Nothing was pushed to GitHub, `C:\GIT\FPL` or `C:\GIT\FPL-data`.
- **Network, read-only:** one `GET` of the public `bootstrap-static/` (today's prices, for the A9 check) and the FPL API calls `fpl_sync.py` makes during the nightly rehearsal; `git ls-remote` of GitHub.
- **`C:\GIT\FPL` and `C:\GIT\FPL-data`, before and after:** identical. Same refs (`master ce830c4`, `s2-wip 04acd7d`, `data e84bee6`), same tags (`backup-2026-10-17`, `pre-data-branch`), same worktrees, no stash, same sha256 of `.git/config` (`8569a0ef...`) and `.git/hooks/pre-push` (`2ad9e278...`), both worktrees clean. GitHub refs unchanged. The only new file is this report.
- **Time zone stand-in:** this PC has no tzdata (`ZoneInfo("Europe/London")` raises `ZoneInfoNotFoundError`). I generated a TZif v2 file for `Europe/London` myself (explicit transitions 1990-2037: last Sunday of March 01:00 UTC to last Sunday of October 01:00 UTC, plus the POSIX footer `GMT0BST,M3.5.0/1,M10.5.0`) in the scratch folder and exposed it through `PYTHONTZPATH` only. Checked: 2026-10-17T21:40Z -> 22:40 BST; 2026-10-17T23:30Z -> 2026-10-18 00:30 BST; 2026-10-25T00:30Z -> BST, 01:30Z -> GMT; 2027-03-28 01:30Z -> BST. It was never placed in a repository.
- **Masking:** no key-like string was met in any file, log or output of this run. Commit ids are short ids.

## Prereg order (gate)

PASS.
- `9694334` (2026-10-18 10:32:44 +0200) adds only `prereg/S2.md`. The first S2 code commit is `79e007f` (10:42:13 +0200). `9694334` is the merge base of master and s2-wip, so every S2 commit descends from it.
- `prereg/S2.md` is byte-identical on master and s2-wip (no edit after the ruling). Every template row is n/a, as allowed for a ruling-only data-pipeline item; the ruling text is present verbatim, points 0-5, between `RULING S2:` and `END RULING`.

## Check 1: point-in-time leak check

PASS (the item produces no new forecast, feature or metric; the evidence is that the recorded forecasts are unchanged and every input is dated before its deadline).
- **1a (truncation):** nothing new to rebuild. Check 5 shows that every frozen source (own, xg, minutes, bottomup) records the same values under s2-wip as under master with the same inputs and clock, and that no pre-existing row changed.
- **1b (timestamp audit):** over the whole real log at `e84bee6` (4679 rows), 0 rows have `made_at >= events.deadline_time`. Minimum margin before the deadline per gameweek: GW4 14.58 h, GW5 19.58 h, GW6 12.16 h, GW7 11.96 h, GW8 127.89 h. After the rehearsal nightly (5734 rows): still 0. The same test (`test_the_real_log_has_no_row_at_or_after_its_deadline`) ran green with `FPL_DATA_DIR` set and will run on the runner, where the workflow sets `FPL_DATA_DIR=data` for the nightly's test step (Step 2.2's nightly test).
- **1c (shift probe):** no correlation metric in this item.
- The one input the item adds to a reader is `events.deadline_time` for the recording guard (`event_deadline`); the guard is now `now >= dl` (was `>`), stricter, never looser.

## Check 2: clean-checkout test run

PASS.

| checkout | tests | result |
|---|---|---|
| master `ce830c4` (before S2) | 309 | OK (skipped=3) |
| s2-wip `04acd7d` | 355 | OK (skipped=6) |
| s2-wip with `FPL_DATA_DIR` = the data clone after `--restore` and `PYTHONTZPATH` = the stand-in zone | 355 | **OK, 0 skips** |
| s2-wip, inside the nightly rehearsal (runner path) | 355 | OK |

- Implementer's claim: 355 green. Confirmed.
- The six skips without data are the three pre-existing ones (no real export / database here) plus the two real-log tests and `test_the_real_london_zone_where_installed`; all run with the data folder and the zone.

## Red before the fix (BUILD_PLAN Step 2: "each fix with a unit test that fails before the fix")

PASS. The s2-wip `test_fpl.py` run against master code: 355 tests, failures=16, errors=62. Every Step point has at least one new test red on master:

| Step | red on master (examples) |
|---|---|
| 2.1 lockdown 3 h, postponed, stuck alarm | `StepTwoEdge.test_a_fixture_not_started_three_hours_after_kickoff_is_postponed`, `..._a_started_fixture_past_three_hours_must_be_finished`, `..._a_fixture_inside_three_hours_of_kickoff_does_not_block`, `..._a_gameweek_not_final_72_hours_after_its_last_kickoff_is_stuck`, `..._the_stuck_command_exits_one...`, `NightlyRunner.test_a_stuck_gameweek_turns_the_run_red` |
| 2.2 deadline guard | `ProjectionLogKey.test_the_deadline_is_events_deadline_time` |
| 2.3 natural key, upsert, readers, duplicates reported | `ProjectionLogKey.test_a_new_snapshot_day_keeps_the_earlier_one`, `..._a_same_day_rerun_replaces_that_days_rows_only`, `..._readers_take_the_latest_snapshot_and_the_last_row_per_key`, `..._duplicates_are_reported_and_never_deleted` |
| 2.4 price dates, London date, flag, missing dates, tzdata error | `StepTwoSync.test_a_snapshot_carries_its_fetch_time_and_london_date`, `..._a_fetch_after_uk_midnight_is_flagged_in_summer_and_winter`, `..._a_missing_price_date_is_warned`, `..._without_the_london_zone_the_sync_stops_with_a_clear_error` |
| 2.5 gameweek by deadline | `StepTwoSync.test_the_current_gameweek_comes_from_deadlines_not_flags` |
| 2.6 casts, required fields, chance null = 100 | `StepTwoSync.test_numeric_strings_are_cast_and_a_missing_value_raises`, `..._a_missing_required_field_raises_instead_of_zero`, `StepTwoEdge.test_chance_of_playing_null_is_100_and_never_0` |
| 2.7 ruleset | `StepTwoRuleset.*` (3 tests) |
| 2.8 selling prices | `StepTwoSelling.*` (5 tests), `Budget.test_budget_is_the_bank_plus_selling_prices_never_value`, `BenchBoost.test_fodder_cost...`, `WildcardCrossPosition.test_split_parameter...` |
| 2.9 Windows I/O | `StepTwoFiles.test_every_text_open_names_utf8_and_newline`, `ProjectionLogKey.test_the_log_holds_no_carriage_return` |
| 2.10 bench audit after auto-subs | `StepTwoBenchAudit.*` (6 tests), `StepTwoSync.test_automatic_subs_are_stored_known_and_exported` |
| ruling 3 (new columns by ALTER TABLE, old rows untouched; gate list) | `StepTwoSync.test_rows_stored_before_s2_are_never_rewritten`, `..._fixtures_store_started_and_the_export_carries_it_and_every_deadline` |

- Two new tests were already green on master and so prove no fix: `StepTwoEdge.test_a_double_gameweek_is_one_row_with_two_fixtures` (master already stored one `player_gw` row per (player, gameweek) with `n_fixtures` in the export) and `test_no_code_turns_a_null_chance_into_zero` (a static check; master had no such pattern). Noted under Step 2.6 below.
- The other master errors (Reliability, HorizonTest, RollingOrigin, ConcentrationTest, ...) are collateral: the s2-wip helpers add `ruleset` to canonical rows, which master's `check_canonical` rejects.

## Check 3 and check 4

- **Check 3:** not applicable; the prereg has no evaluation, metric, bootstrap or threshold (all n/a).
- **Check 4:** PASS. Nothing promoted or re-tuned; the ruling is present verbatim. Fidelity to each point is judged below.

## Check 5: recording path

PASS.
- **Frozen clock.** A scratch `sitecustomize.py` (on `PYTHONPATH`) replaced `datetime.datetime` with a subclass whose `now()` returns 2026-10-18T12:00:00Z, before the GW8 deadline 2026-10-23T17:30:00Z (`events.deadline_time`).
- **Same inputs.** Two copies of the data clone at `e84bee6` with the working exports restored by `fpl_nightly.py --restore` (GW7 export = `exports/fpl_export_gw7_2026-10-17.json.gz`). `fpl_edge.py --record --source <src> --status reports/record_status.tmp` for own, xg, minutes, bottomup, with the working directory in the data copy as the nightly does: (A) master code on `data_m`; (B) s2-wip code on `data_s`.
- **Result.** Both: RECORD OK own 275 / xg 260 / minutes 260 / bottomup 260 (the implementer's numbers).
  - (A) master log: 4679 rows, CRLF, the GW8 2026-10-17 blocks replaced by 2026-10-18 blocks (the old behaviour).
  - (B) s2-wip log: 5734 rows, 0 `\r`; the 2026-10-17 GW8 blocks (275/260/260/260) kept, the 2026-10-18 blocks (275/260/260/260) added, 0 duplicate natural keys.
  - **The s2-wip log begins with the committed blob `HEAD:projection_log.csv` byte for byte** (239265 bytes, 4679 rows): no pre-existing row was rewritten, moved or deleted. (The data branch's `.gitattributes` has `projection_log.csv text eol=crlf`: the blob is stored LF and only the checkout is CRLF, which is why the LF writer changes nothing at the blob level.)
  - **`forecasts()` of the s2-wip log equals the master-code log row for row** (4679 rows, `made_at` included): every reader sees exactly what the old single-snapshot log held.
  - **Frozen `p1_eval.py`**, which reads the log itself (`csv.DictReader`, then `{player: row}` for xg / event 4): byte-identical output on the committed log and on the s2-wip multi-day log (graded 255, gap +0.110, interval +0.003..+0.226).
- **Rehearsal commit.** In the nightly + publish rehearsal (below) the data commit's diff of `projection_log.csv` is **+1055 / -0** lines, and the gate reported "frozen forecasts unchanged".

## Check 6: mutation spot-check

PASS. 31 one-line mutations in the scratch clone `code_s2_mut` at `04acd7d`, each applied alone, its target test class(es) run, the file restored with git and verified equal to the original; `git status` clean afterwards. **All 31 went red.**

| # | step | file | mutation | red test |
|---|---|---|---|---|
| M01 | 2.1 | fpl_edge | `POSTPONED_AFTER_H` 3 -> 0 | `StepTwoEdge.test_a_fixture_inside_three_hours_of_kickoff_does_not_block` |
| M02 | 2.1 | fpl_edge | `STUCK_AFTER_H` 72 -> 720 | `..._a_gameweek_not_final_72_hours_after_its_last_kickoff_is_stuck` |
| M03 | 2.1 | fpl_nightly | `--stuck` step's exit ignored | `NightlyRunner.test_a_stuck_gameweek_turns_the_run_red` |
| M04 | 2.2 | fpl_edge | `event_deadline` ignores `events.deadline_time` | `ProjectionLogKey.test_the_deadline_is_events_deadline_time` |
| M05 | 2.3 | fpl_edge | same-day filter dropped (every day's block replaced) | `..._a_new_snapshot_day_keeps_the_earlier_one` |
| M06 | 2.3 | fpl_edge | `forecasts()` keeps the first row per key | `..._readers_take_the_latest_snapshot_and_the_last_row_per_key` |
| M07 | 2.3 | fpl_edge | duplicate note never printed | `..._duplicates_are_reported_and_never_deleted` |
| M08 | 2.4 | fpl_sync | London date = UTC date | `StepTwoSync.test_a_fetch_after_uk_midnight_is_flagged_in_summer_and_winter` |
| M09 | 2.4 | fpl_sync | after-midnight flag never set | same |
| M10 | 2.4 | fpl_sync | missing dates never warned | `..._a_missing_price_date_is_warned` |
| M11 | 2.4 | fpl_sync | `london_tz` returns None instead of exiting | `..._without_the_london_zone_the_sync_stops_with_a_clear_error` |
| M12 | 2.5 | fpl_sync | `sync_bootstrap` returns the `is_current` flag | `..._the_current_gameweek_comes_from_deadlines_not_flags` |
| M13 | 2.6 | fpl_sync | `num()` -> `float(value or 0)` | `..._numeric_strings_are_cast_and_a_missing_value_raises` |
| M14 | 2.6 | fpl_sync | `required()` -> `obj.get(field) or 0` | `..._a_missing_required_field_raises_instead_of_zero` |
| M15 | 2.6 | fpl_edge | chance null -> 0 | `StepTwoEdge.test_chance_of_playing_null_is_100_and_never_0` |
| M16 | 2.7 | fpl_edge | `one_ruleset` check removed from `measure_reliability` | `StepTwoRuleset.test_reliability_refuses_rows_from_two_rulesets` |
| M17 | 2.7 | fpl_hist | historical rows labelled 2026-27 | `..._every_live_and_historical_row_carries_its_ruleset` |
| M18 | 2.8 | fpl_edge | formula without the falling branch | `StepTwoSelling.test_the_formula_in_tenths` |
| M19 | 2.8 | fpl_sync | formula returns `now` | 5 failures in `StepTwoSelling` |
| M20 | 2.8 | fpl_sync | Free Hit moves counted as purchases | `..._purchase_prices_come_from_transfers_or_the_season_start` |
| M21 | 2.8 | fpl_sync | late joiner's first squad guessed from the start price | `..._an_entry_that_joined_late_has_no_price_for_its_first_squad` |
| M22 | 2.8 | fpl_edge | `selling_budget` reads `value` | `Budget.test_budget_is_the_bank_plus_selling_prices_never_value` |
| M23 | 2.9 | fpl_edge | log writer back to CRLF | `ProjectionLogKey.test_the_log_holds_no_carriage_return` |
| M24 | 2.9 | fpl_hist | one `open()` loses `newline=""` | `StepTwoFiles.test_every_text_open_names_utf8_and_newline` |
| M25 | 2.10 | fpl_edge | `rule_autosubs` never substitutes | 4 failures in `StepTwoBenchAudit` |
| M26 | 2.10 | fpl_edge | FPL's stored list ignored | `..._fpl_s_stored_list_is_the_authority` |
| M27 | 2.10 | fpl_edge | rules applied while matches are still to play | `..._a_gameweek_still_in_play_gets_no_rule_substitution` |
| M28 | 2.10 | fpl_sync | `automatic_subs` never stored | `StepTwoSync.test_automatic_subs_are_stored_known_and_exported` |
| M29 | ruling 3 | fpl_gate | `automatic_subs` dropped from `EXPECTED_TABLES` | `DataGate.test_grow_only_holds_exactly_the_tables_the_sync_never_deletes_from` (+1) |
| M30 | 2.1 | fpl_sync | `started` stored as 1 always | `..._fixtures_store_started_and_the_export_carries_it_and_every_deadline` |
| M31 | 2.2/2.5 | fpl_sync | `events` exported only up to the current gameweek | same |

## Check 7: secrets

PASS.
- `git diff 9694334 s2-wip`: 0 lines matching `apikey=`, `api_key=`, `Authorization`, `Bearer`, a 32+ hex string, `sk-`, `ghp_` or `ODDS_API_KEY`.
- Per changed file at s2-wip: 0 hits in every file except `fpl_gate.py`, whose 2 hits are its own pre-existing `KEY_PATTERNS` constants and docstring (0 of them in the S2 diff).
- The nightly rehearsal output (1278 lines) and the data commit: 0 hits; the publish's own staged-secret scan said `SECRETS OK`.

## Nightly + publish rehearsal (s2-wip code, real clock, real API, stand-in zone, bare origin)

PASS, exit 0 for both steps.
- `FPL_DATA_DIR` = the data clone (origin repointed to `origin_bare.git`, which held `data` = `e84bee6`), `PYTHONTZPATH` = the stand-in zone, `python fpl_nightly.py` from `code_s2`.
- Run log: tests 355 OK; sync printed the seven migrations `+ player_gw.fetched_at_utc`, `+ player_gw.ruleset`, `+ price_history.fetched_at_utc`, `+ price_history.london_date`, `+ fixtures.started`, `+ fixtures.fetched_at_utc`, `+ entry_gw.fetched_at_utc`; `PRICE DATE FLAG: fetched 2026-10-18T09:36:05+00:00 = after 00:00 UK - this snapshot holds the prices of London day 2026-10-18` (correct: a morning fetch); `PRICE DATES MISSING: 4 day(s) without a snapshot: 2026-09-28, 2026-10-02, 2026-10-03, 2026-10-04` (true gaps in the real price history); no `GAMEWEEK FLAGS DISAGREE` (the API's flags agreed: current GW7, next GW8); `exported -> fpl_export_gw7.json`; RECORD OK own 275 / xg 260 / minutes 260 / bottomup 260, each "5 days, 7:53 before deadline"; watch file written; report built (the Free Hit screen now says "budget £99.7m = bank + selling prices"); `STUCK CHECK OK`; `ARCHIVE OK`; `Done`.
- Publish: `GATE OK integrity ok, 14 tables, price_history 25881 rows, frozen forecasts unchanged; fpl.sql written`; `SECRETS OK`; commit `nightly 2026-10-18 [skip ci]`; `PUSH OK origin data`. The bare origin's `data` moved `e84bee6` -> `91e0b7d`. The commit: `projection_log.csv` +1055/-0; new `exports/fpl_export_gw7_2026-10-18.json.gz`, `logs/run_2026-10-18.log`, `reports/fpl_2026-10-18.txt`, `reports/watch_2026-10-18.txt`; `fpl.sqlite` 1781760 -> 1888256 bytes; `fpl.sql` rewritten wholesale (62399 lines) because every dumped `INSERT` now carries the new columns - expected once, after the ALTER TABLE.
- Database after the run (read-only): tables = the 14 of `EXPECTED_TABLES`; `price_history` 25881 rows, 667 with `fetched_at_utc`/`london_date` (tonight, london_date 2026-10-18) and **25214 NULL**; `player_gw` 4550 rows, 667 with `fetched_at_utc`/`ruleset` = `2026-27` and **3883 NULL**; `entry_gw` 49 rows, 7 with `fetched_at_utc` (GW7) and **42 NULL**; `fixtures` 380/380 with `started` and `fetched_at_utc` (re-fetched every night); `automatic_subs` 0 rows (GW7 had none for the seven entries; `autosubs_known` lists all seven for GW7, so the bench audit used source "FPL").
- Export after the run: `events` 38 rows all with `deadline_time`; `fixtures_status` carries `started`; `squads` 105 rows, 0 missing `purchase_price` or `selling_price`; `automatic_subs` and `autosubs_known` present.

## Simulated GW10 / GW20 / GW38 (s2-wip code)

PASS. For each, `_recordable_export(gw=...)`: all 18 report sections ran without an exception or a short output; the four sources recorded 57 forecasts each; the log had 0 `\r` and 0 duplicate keys; `forecasts()` returned every row; a same-day re-run left the row count unchanged (228); `gameweek_settled` (True, []); `stuck_gameweeks` []; `effective_lineup` source "rules" for every squad (synthetic export: fixtures finished, no stored list). Sync side, `deadline_gameweeks` by `deadline_time` alone over 38 synthetic events: before GW1 -> (0, 1); mid-season -> (10, 11), (19, 20); after GW38's deadline -> (38, None).

## Ruling 4 (A9): the fifteen selling prices

PASS, 15 of 15. Recomputed with s2-wip's `purchase_prices()` and `selling_price()` from a read-only copy of `fpl.sqlite` at `e84bee6` (picks of entry 3073318, GW7; transfers; `now_cost - cost_change_start` for the original squad, `MIN(picks.event)` = 1), and the "current" price from today's live `bootstrap-static` (the data copy holds the 17 Oct evening prices; the screenshot was taken on 18 Oct):

| slot | player | current (live) | purchase | selling | screenshot |
|---|---|---|---|---|---|
| 1 | Verbruggen | 4.6 | 4.5 | 4.5 | 4.6/4.5/4.5 |
| 2 | Muharemovic | 5.0 | 5.0 | 5.0 | 5.0/5.0/5.0 |
| 3 | Calafiori | 6.0 | 5.8 | 5.9 | 6.0/5.8/5.9 |
| 4 | Tarkowski | 6.2 | 6.2 | 6.2 | 6.2/6.2/6.2 |
| 5 | Thomas | 4.0 | 4.0 | 4.0 | 4.0/4.0/4.0 |
| 6 | Saka | 9.6 | 9.5 | 9.5 | 9.6/9.5/9.5 |
| 7 | Mbeumo | 7.8 | 7.9 | 7.8 | 7.8/7.9/7.8 |
| 8 | Gross | 6.1 | 6.0 | 6.0 | 6.1/6.0/6.0 |
| 9 | Rudoni | 4.9 | 4.9 | 4.9 | 4.9/4.9/4.9 |
| 10 | Haaland | 15.7 | 15.5 | 15.6 | 15.7/15.5/15.6 |
| 11 | Barry | 5.7 | 5.6 | 5.6 | 5.7/5.6/5.6 |
| 12 | Kelleher | 5.0 | 5.0 | 5.0 | 5.0/5.0/5.0 |
| 13 | Branthwaite | 5.5 | 5.5 | 5.5 | 5.5/5.5/5.5 |
| 14 | Thiago | 7.8 | 7.8 | 7.8 | 7.8/7.8/7.8 |
| 15 | Slater | 4.5 | 4.5 | 4.5 | 4.5/4.5/4.5 |

- Calafiori rose 5.9 -> 6.0 at 00:00 UK on 18 Oct; with the 17 Oct price his selling price is 5.8, with today's 5.9 as on the screenshot - the one case where the day of the price matters, and it resolves the right way. Every purchase price comes from the data (the GW6 wildcard moves included; the 3xc chip in GW7 is not a Free Hit, so nothing is excluded).

## Ruling 2: the projection log, judged against the code

PASS. The implementer's reading (keep each snapshot day; a same-day re-run replaces that day's block for a source and gameweek; readers take, per (source, gameweek), the rows of the latest snapshot day and the last row per natural key) is exactly what the code does:
- `natural_key` = `(event, player_id, source, made_at[:10])`; `snapshot_date` = the UTC date of `made_at`; no schema change (`LOG_FIELDS` unchanged: made_at, source, event, player_id, web_name, predicted).
- `record_status` drops only rows with the same source, target and UTC day as the new stamp, then appends; it never touches another day's rows; it prints `LOG NOTE: n natural keys are held by more than one row` and keeps them.
- `forecasts()` takes the latest day per (source, event), then the last row per key, order kept; every reader other than the recorder goes through it (`sec_calibration`, `--watch`, `sec_free_hit`); `recover_stranded_log` and `record_status` read raw rows, as they must.
- The real log has 0 duplicate natural keys; the recorded forecasts of every frozen source are unchanged (check 5).
- `made_at` is the recording time, not the sync's fetch time (they are minutes apart in a nightly); the export's `generated` holds the fetch time. Under "no schema change" that is the only reading available; I note it, not fault it.

## Ruling 3: the database

PASS with one open item (below).
- The new columns (`fetched_at_utc` on price_history, player_gw, fixtures, entry_gw; `london_date`; `ruleset`; `started`) are added by `migrate()` with `ALTER TABLE ... ADD COLUMN` (confirmed by the seven `+ table.col` lines in the rehearsal and by `test_rows_stored_before_s2_are_never_rewritten`); every pre-existing row keeps its values and NULL in the new columns; nothing is deleted (`fpl_sync.py` still has no DELETE/DROP; the gate's grow-only check passed).
- `automatic_subs` is in the gate's `EXPECTED_TABLES` in the same commit as the schema (`efb7176`: fpl_sync.py + fpl_gate.py), and M29 shows the agreement is tested.
- **Open item (ruling 3, last clause):** "report how many rows could not be backfilled". The code backfills nothing (the implementer's comment: the fetch time was never recorded) and nothing prints that count. From the rehearsal database: **25214 `price_history` rows, 3883 `player_gw` rows and 42 `entry_gw` rows (29139 in all) keep NULL `fetched_at_utc`**; the 380 `fixtures` rows are re-fetched nightly and are all filled. These numbers must appear in the S2 report and the changelog entry so the ruling's report requirement is met; the code needs no change for it.

## Step 2 points, one by one

1. **Lockdown guard:** PASS. `gameweek_settled` requires `data_checked = 1` and every fixture with kickoff >= 3 h ago finished; a fixture not started 3 h after kickoff (`started = 0`) or without a kickoff counts as postponed and is excluded; fixtures with `event` null never enter `fixtures_status` (`WHERE f.event<=?`); `stuck_gameweeks` + `--stuck` + the nightly step raise the 72 h alarm (red run). An export without `started` (pre-S2) still needs every past fixture finished. The 09:00 UK note is in the docstring.
2. **Point-in-time guard:** PASS. Refuses at `now >= deadline_time` (exported for all 38 events; fallback 90 min before first kickoff for old exports); the real-log test finds 0 rows at or after the deadline and runs nightly on the runner. `fetched_at_utc` is on the scored, price, fixture and entry rows and `players.updated_at` already held it; **not** on picks, transfers, chips, standings, teams, player_history, and forecast rows carry `made_at` only (ruling 2 forbids a schema change there). Noted for the chat; not a failure of the ruling.
3. **Idempotent log:** PASS under ruling 2 (key without `fixture`; duplicates reported, not deleted - the real log has 0 anyway). Temp file + atomic rename unchanged from S1.
4. **Price dates:** PASS. London calendar date at fetch time via `zoneinfo`; `fetched_at_utc` stored; a fetch between 00:00 and 12:00 London is flagged (fired correctly in the morning rehearsal; the 21:40 UTC runner fetch is 22:40 BST / 21:40 GMT, not flagged); missing dates warned (4 real gaps); without `Europe/London` the sync exits with `TIME ZONE MISSING ... install the tzdata package` (confirmed on this PC, which has no tzdata; the runner installs `requirements.txt` - its Ubuntu image has the system database).
5. **Target gameweek:** PASS. `deadline_gameweeks` uses `deadline_time` only; the flags are compared and a disagreement is printed.
6. **Field handling:** PASS with two bullets that needed no fix. null chance -> 100 by explicit mapping (and the old code multiplied by nothing when null, so no forecast moved); numeric strings cast by `num()`; required fields raise; doubles were already one row per (element, gw) with `n_fixtures` (the new test was green on master); "scoring rules per fixture" has no code change and no test - the models already sum per fixture (`for f in fx`), the DEFCON term is at most 2 per fixture, and no model has a saves term. Report this as "already so / nothing to fix" in the S2 report rather than as a fix.
7. **ruleset:** PASS. On every canonical row (live `2026-27`, vaastav `2025-26`); `measure_reliability` refuses mixed rulesets; `check_canonical` now requires the field.
8. **Selling price:** PASS (formula tests 7.5->7.8 = 7.6, equal, falling, +0.1; purchase prices from transfers or the start price; wildcard moves included, Free Hit moves excluded; late joiner -> None; every budget - wildcard, bench boost, free hit, upgrade shortlist - from bank + selling prices, refused without them; A9 15/15).
9. **Windows I/O:** PASS. Every text `open()` in the runner files names `encoding="utf-8"`/`utf-8-sig` and `newline` (static test, M24 red); the log is LF (M23 red); the committed blob was already LF, so nothing is rewritten.
10. **Bench audit:** PASS. FPL's stored list where `autosubs_known`, else the rules on the minutes only when every fixture of the gameweek is finished, else "pending"; the required test (a 0-minute starter whose bench player came on shows no gain) is red on master and green now; M25-M28 red.
11. Verifier -> report -> commit -> push: this report; the S2 report, changelog and merge follow.

## Ruling 1 (branch) and ruling 0 / 5 (process)

PASS. s2-wip branches from master `9694334`; `origin/s2-wip` = `04acd7d` is the backup push; master has no S2 code (`git diff master s2-wip` = the seven files above plus `worklog/SESSION_STATE.md`, which s2-wip lacks from `ce830c4`). The merge, the 9d window (next deadline GW8 2026-10-23T17:30Z; 30 h window opens 2026-10-22T11:30Z; planned Mon 19 Oct, latest Tue 20 Oct before 21:00 UTC) and the proof dispatch are not mine to check now.

## To be re-checked after the merge

1. Tonight's scheduled nightly on the S1 layout: a `nightly 2026-10-18` commit on `data`, gate green, the Sunday `backup-2026-10-18` release present (ruling 1a) - the merge's gate.
2. The merge commit's tree equals `04acd7d` for the seven files (one byte-identical commit), and master's `worklog/SESSION_STATE.md` is reconciled.
3. The S2 report (`worklog/cc_2026-10-18_S2.md`) and the changelog carry: the unbackfilled counts (25214 / 3883 / 42), the two Step 2.6 bullets that needed no fix, the `fetched_at_utc` coverage (which tables have it), and the `made_at` reading.
4. The proof dispatch's run log on `data`: the seven `+ table.col` lines once; no `PRICE DATE FLAG` at 21:40 UTC; `PRICE DATES MISSING` lists the four known gaps; four RECORD OK; `STUCK CHECK OK`; `GATE OK ... 14 tables, frozen forecasts unchanged`; `projection_log.csv` additions only; tests 355 with 0 skips (real tzdata, `FPL_DATA_DIR=data`); the real `Europe/London` labels the fetch with the same London day.
5. The first night after the GW8 deadline (24 Oct): the GW8 rows (now several snapshot days) freeze and the gate still passes; `forecasts()` reads the 23 Oct snapshot.
6. The `fpl.sql` dump: one large rewrite on the first S2 night, then normal growth.
7. The final verifier run (ruling 5).

VERDICT: PASS

Reason: every acceptance test of the item holds on `s2-wip` at `04acd7d` - the prereg precedes the code; 309 -> 355 tests green on clean checkouts and with the real data; every Step 2 fix has a test that is red on master and green now, and all 31 one-line mutations go red; the recorded forecasts of the frozen sources are unchanged (the s2-wip log begins with the committed blob byte for byte, `forecasts()` of it equals the master-code output row for row with the same frozen clock, frozen `p1_eval.py` gives identical output, and the rehearsal commit adds 1055 rows and removes none); the fifteen selling prices match the A9 screenshot exactly; the nightly and publish rehearsal against my own bare origin went green with the seven ALTER TABLE columns, the price-date flag and the missing-date warning behaving as specified; simulated GW10/20/38 ran clean; no secret appears in anything the item touches. The one open item is a reporting clause of ruling 3 - the count of rows that could not be backfilled (25214 price_history, 3883 player_gw, 42 entry_gw) is printed nowhere and must be stated in the S2 report and changelog before the merge; it needs no code change and does not alter any recorded forecast.
