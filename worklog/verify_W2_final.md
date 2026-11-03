# verify_W2_final — W2 and W2fix on the live nightly of Tue 3 Nov 2026

**VERDICT: PASS**

Verifier: Claude Code, model Fable 5.1 (claude-fable-5-1), effort high, as
`.claude/agents/backtest-verifier.md` on disk says (read first; it matches the
loaded instructions). Run on 2026-11-03 after the data commit `39578fe`.

Scope: the live run on master at data commit `39578fe` (Boris's manual
dispatch, dry_run unticked; log started 20:14:38 UTC, status generated
20:17:17 UTC), checked against `prereg/W2.md` (with its amendments) and
`prereg/W2fix.md`. Everything that opens a data file was run on my own copy
under the session scratchpad (`.../scratchpad/verify_w2_final`), with
`ODDS_API_KEY` unset in every command and data files read by Python with
`-I`. No git command that writes, no sync, no `--record`, no `fpl_nightly.py`.
`git status` in `C:\GIT\FPL` was clean before this report was written.

## Prereg before code (gate)

- `prereg/W2.md`: first committed `08d6a95` 2026-10-19 13:23:12 +0200; the
  first W2 code commit is `4d48697` 2026-10-19 18:10:30 +0200. Amendments
  (standings `6efb6a4`, afternoon ruling `fc56fd5`, amendment 2 `a78e2e7`
  21:11 before `c21e0e0` 21:24, Wed 21 Oct `87485f3`, amendment 3 `5d4ad2b`
  before `ba138c7`) each precede the code they govern. PASS.
- `prereg/W2fix.md`: `d2e1b43` 17:00:39 +0100, before the code `8c7a34a`
  17:04:21 +0100. PASS.
- Rulings present verbatim in the prereg: "RULING W2 build", the W2 addition
  of 18 Oct, RULING morning 19 Oct point 3, RULING W2 standings + lanes
  merge, RULING 19 Oct afternoon, RULING 19 Oct evening, Wednesday 21 Oct,
  Boris's 21 Oct message (amendment 3); W2fix: Boris's message of Tue 3 Nov.
  PASS.
- Head: `ea0957c` differs from `271eecc` only in `worklog/SESSION_STATE_A.md`
  (`git diff 271eecc ea0957c --stat`: 1 file, +34/-1). Confirmed.

## a. Which code ran; real run, not dry — PASS (with one note)

- Neither `logs/run_2026-11-03.log` nor `reports/status.txt` names the
  commit. A real run's data commit message is `nightly <date> [skip ci]`
  (`fpl_publish.py` lines 177-179); only a dry run's message carries
  `GITHUB_SHA[:7]`. So the commit cannot be read off the live artefacts.
  **Established instead:**
  - The code was `ea0957c` (= `271eecc` plus the state file): `origin/master`'s
    reflog shows `ea0957c` pushed 2026-11-03 17:23:19 +0100 (16:23 UTC), the
    last push before the run started at 20:14:38 UTC. The log runs
    `Ran 755 tests` (the 2 Nov nightly `0c61ea1` ran 752; W2fix adds 3) and
    names the three `tests.test_W2fix.VicePromotion` tests; `LEAGUE OK 58
    lines` is impossible on pre-W2fix code with entry 18931 GW8 in the data
    (the 26 Oct-2 Nov nights prove that).
  - Real, not dry: the data branch moved (`origin/data` 0c61ea1 -> 39578fe,
    author github-actions[bot], message `nightly 2026-11-03 [skip ci]`); the
    Odds API key was present (`ODDS OK ... credits used 12, remaining 488`;
    a dry run gets no key); started 20:14 UTC, not the 21:40 cron, so a
    manual dispatch. `data-dryrun*` is not involved.

## b. The status — PASS

`reports/status.txt` at 39578fe: `STATUS OK | generated 2026-11-03T20:17:17Z
| ... | checks 30/30`; `28 OK test gate: 755 tests green`; `29 OK record:
own 306, xg 283, minutes 283, bottomup 283, fpl_ep 670, bottomup_lambda 283
(snapshot odds_2026-11-03T2017Z.json.gz, 283 of 283 players with odds-priced
fixtures)`; `31 OK report sections: CHIPS 35 lines, LEAGUE 58 lines`.

Check 31 on every live nightly since the merge (`git show <c>:reports/status.txt`):

| data commit | night | check 31 |
|---|---|---|
| 1449cd0 | 23 Oct | (pre-merge: 29 checks, no check 31) |
| 2ec703f | 24 Oct | OK CHIPS 36 lines, LEAGUE 51 lines |
| 23f7494 | 25 Oct | OK CHIPS 36 lines, LEAGUE 51 lines |
| 0164ab9 .. 0c61ea1 | 26 Oct - 2 Nov (8 nights) | WARN LEAGUE SKIPPED: entry 18931 GW8 player 411: multiplier 2 but the rule says 1 (chip None) |
| 39578fe | 3 Nov | OK CHIPS 35 lines, LEAGUE 58 lines |

The 3 Nov run is the first since 26 Oct without the entry 18931 message.
(The other WARNs on 24 Oct and 1 Nov were check 3, a new player id; not W2.)

## c. The sections in the live report — PASS

- `reports/fpl_2026-11-03.txt` (603 lines): rule + `CHIPS (W2: S7 chip
  calculator)` + rule at 504-506, CHIPS lines 507-541 = 35; `LEAGUE (W2: S9
  league)` at 544, LEAGUE lines 546-603 = 58. Both match check 31.
- Coherence of LEAGUE: header `settled through GW8, 30 gameweeks left; coming
  deadline GW10 (GW9 played, not yet settled)`; `7 rows the chain cannot
  correct, excluded`, the seven GW9 rows named (one per entry: the chain
  settles g only from the g+1 row, GW10 has none); the DB has GW9
  `finished=1, data_checked=1`, so GW9 is in the lockdown-settled set and
  the chain excludes it, which is exactly what the text says. Threat set =
  the four rivals with gap > 0 (42, 50, 20, 31). sigma_d, our sigma, the
  no-chip sigma, every sigma_j/sigma_dj and P(above) are printed with 90%
  intervals; B=10000, seed 20261018.
- **Recompute**: `fpl_sections.sections(".", now=2026-11-03T20:17:10Z)` with
  `ea0957c`'s modules (`git archive`) on a copy of the data at 39578fe. One
  adjustment needed to mirror section time: the night's archive step runs
  after the sections, so `exports/fpl_export_gw9_2026-11-03.json.gz` was
  hidden (CHIPS reads the newest archive under `exports/`,
  `fpl_chips.newest_export`; the live CHIPS header names
  `fpl_export_gw9_2026-11-02.json.gz`). Result: `CHIPS OK 35 lines`,
  `LEAGUE OK 58 lines`; the 101 rendered lines (from line 503) are identical
  to the live report line for line and byte for byte after normalising the
  CRLF that the Windows checkout puts on the file (the committed blob is
  LF-only: `CRLF 0 LF 603`). No other difference.
- Note for the chat (not a defect of this run): by W2's design CHIPS reads
  the previous night's archived export, one night stale within the same
  gameweek; the record and LEAGUE read the fresh export/database.

## d. The multiplier check on live data — PASS

`fpl_league.load(".")` on the copied `fpl.sqlite` loads (no MissingInput).
Stored picks: 63 entry-gameweeks, GW1-9 (all settled), 7 entries, every one
with exactly one captain and one vice. Captain on 0 minutes: exactly one,
entry 18931 GW8, chip None, captain 165 (Joao Pedro) at position 13,
multiplier 0, 0 minutes; vice 411 (Haaland) at position 10, multiplier 2,
90 minutes. Applying `expected_multiplier` by hand to all 945 picks: without
the promotion the only mismatch is `(18931, 8, 411, 2, 1, None)` — the exact
WARN text of 26 Oct-2 Nov; with the promotion, zero mismatches. The vice is
promoted nowhere else. Chips as stored in `entry_gw` (13) include both
4866471 GW6 wildcard / GW7 3xc and ours GW6 wildcard / GW7 3xc (amendment 3
holds live).

## e. bottomup_lambda as the sixth source, live — PASS

From `projection_log.csv` at 39578fe (38510 rows): bottomup_lambda has 2979
rows over 11 nights, 24 Oct-3 Nov, events 9 and 10; made_at >= deadline: 0
(for every row of every source: 0). `fpl_edge.duplicate_keys`: 0; my own
check on (made_at, source, event, player): 0. Per night (by UTC date):

| night | event | own | xg | minutes | bottomup | fpl_ep | bottomup_lambda | status 18/29 |
|---|---|---|---|---|---|---|---|---|
| 19 Oct | 8 | 281 | 261 | 261 | 261 | 668 | - | pre-merge |
| 20 Oct | 8 | 276 | 256 | 256 | 256 | 668 | - | |
| 21 Oct | 8 | 277 | 257 | 257 | 257 | 668 | - | |
| 22 Oct | 8 | 277 | 257 | 257 | 257 | 668 | - | |
| 23 Oct (two runs, 14:22 and 22:06) | 8, 9 | 278+259 | 258+241 | 258+241 | 258+241 | 668+668 | - | 23 Oct night: 259/241/241/241/668 |
| 24 Oct | 9 | 267 | 248 | 248 | 248 | 669 | 248 | equal |
| 25 Oct | 9 | 293 | 270 | 270 | 270 | 669 | 270 | equal |
| 26 Oct | 9 | 293 | 270 | 270 | 270 | 669 | 270 | equal |
| 27 Oct | 9 | 292 | 269 | 269 | 269 | 669 | 269 | equal |
| 28 Oct | 9 | 292 | 269 | 269 | 269 | 669 | 269 | equal |
| 29 Oct | 9 | 289 | 266 | 266 | 266 | 669 | 266 | equal |
| 30 Oct | 9 | 293 | 270 | 270 | 270 | 669 | 270 | equal |
| 31 Oct | 10 | 296 | 271 | 271 | 271 | 669 | 271 | equal |
| 1 Nov | 10 | 303 | 280 | 280 | 280 | 670 | 280 | equal |
| 2 Nov | 10 | 306 | 283 | 283 | 283 | 670 | 283 | equal |
| 3 Nov | 10 | 306 | 283 | 283 | 283 | 670 | 283 | equal |

Every night's counts equal check 18's "+n" and check 29's record line. The
five older sources move only with the market (the per-night own/xg/minutes/
bottomup/fpl_ep pattern is the same before and after 24 Oct; xg = minutes =
bottomup every night, as before). bottomup_lambda's player set equals
bottomup's on every night (same pool filter). Nothing already recorded was
disturbed: `projection_log.csv` at 1449cd0 (pre-merge) is a byte prefix of
2ec703f (+1928 lines) and of 39578fe (+22508); 0c61ea1 is a byte prefix of
39578fe (+2108). Point-in-time: every bottomup_lambda row's made_at is before
its event's deadline (GW9 2026-10-31 11:00Z, GW10 2026-11-06 18:30Z).

## f. The sync columns — PASS

Live `fpl.sqlite` at 39578fe: `transfers.fetched_at_utc` 92/92 non-null,
`chips.fetched_at_utc` 13/13 (both tables rewritten nightly),
`picks.fetched_at_utc` 945/945 (S2b), `standings.fetched_at_utc` 14/56 (the
rows written since the column; the 42 stored rows NULL, as the prereg says),
`standings.label_error` present, = 1 on exactly the seven event-2 rows
(entries 18931, 881799, 2322726, 3073318, 4866471, 5826302, 8690100), 0 on
49; `players.code` 670/670 non-null, 670 distinct.
`player_history.fetched_at_utc`: column present, 0/1927 non-null — the
INSERT sets it (`fpl_sync.py` lines 563-566, 12 columns incl.
`fetched_at_utc`) but no player_history row has been written since the
column was added (the nightly makes no element-summary calls, check 2).
Consistent with "NULL for stored rows, set on every write".

## g. No test or check weakened — PASS

- Gate: `fpl_nightly.TEST_ARGS = ("-m", "unittest", "discover", "-v", "-p",
  "test*.py")`; the live log lists `tests.test_*` and `test_fpl.*` cases and
  ends `Ran 755 tests ... OK (skipped=12)` (the 12 skips are the cmd.exe
  tests on Linux). The workflow runs `python fpl_nightly.py` (line 121).
- `git diff 5c3e3bf ea0957c --stat`: 36 files. Code: checks.py, fpl_bt.py,
  fpl_chips.py, fpl_edge.py (+11, the record branch), fpl_lambda.py,
  fpl_league.py, fpl_nightly.py, fpl_pit.py, fpl_sections.py, fpl_sync.py,
  tools/league.py, test_fpl.py, tests/test_S3.py, tests/test_W1.py,
  tests/test_W2.py, tests/test_W2fix.py — all named by the W2/W2fix commits,
  preregs and reports (`cc_2026-10-19_W2.md` lines 90-92 name test_W1,
  test_S3, test_fpl). Non-code: CHANGELOG, prereg/W2fix.md, the four
  verifier and four cc reports, SESSION_STATE_A.md, and
  worklog/gw_pass/gw9/* (commits e708c91, 72becd6: the GW9 pass, worklog
  only, not W2). Nothing else.
- The test diffs only widen: five sources -> six, 30 checks -> 31, status
  line counts, the no-database world gains fpl_lambda, the I/O rule list
  gains the five new runner files. checks.py's removed lines are the
  five-source table/`CHECKS` range replaced by six/31. No assertion
  relaxed.
- tools/ imports: on the clean archive of ea0957c,
  `tests.test_S3.FastTrack.test_the_nightly_imports_nothing_under_tools_or_analysis`,
  `tests.test_S4.CLI.test_nightly_imports_nothing_under_tools_or_analysis`,
  `tests.test_W2.SixthSource.test_the_record_never_imports_tools_or_opens_the_database`,
  `tests.test_W2.ReportSections.test_byte_identical_to_the_tools`,
  `tests.test_W2.SixthSource.test_the_numbers_are_the_tools` and
  `tests.test_S3.FastTrack.test_the_suite_runs_by_discovery_with_tests_included`: 6 run, OK.

## h. Secrets — PASS

Pattern scan (`apiKey=`, `api_key=`, `Authorization`, `Bearer `, 32-hex) of
status.txt, fpl_2026-11-03.txt, watch_2026-11-03.txt, run_2026-11-03.log and
the committed export: 0 hits. The committed odds snapshot has 20 32-hex
hits, all the Odds API event `"id"` fields (e.g. `0cfb...`, `230a...`); no
`apiKey`/`key` field in the payload. Check 23 on the runner compared the key
value itself: none. Nothing to mask in this report beyond those ids.

## The agent file's numbered checks

1. Point-in-time leak check — PASS.
   a. Truncation (decides): bottomup_lambda rebuilt from only the inputs on
      hand at record time for the earliest, middle and latest nights —
      24 Oct (export gw8_2026-10-24, target GW9, 10 odds files, 10 later
      ones hidden), 29 Oct (gw8_2026-10-29, GW9, 15 files, 5 hidden), 3 Nov
      (gw9_2026-11-03, GW10, 20 files): 248/266/283 rows, same key sets as
      the log, max |diff| 0.0 each night.
   b. Timestamp audit (decides): the snapshot used each night is the newest
      before the deadline (22:02Z 24 Oct, 22:17Z 29 Oct, 20:17Z 3 Nov, all <
      deadline); the export date <= the deadline date; the fallback's
      results (70/80/90) all kicked off before the deadline; every log row's
      made_at < its deadline (0 of 38510 at or after).
   c. Shift probe: not applicable (no correlation metric in this item).
2. Clean-checkout suites (git archive, bare, no FPL_DATA_DIR, key unset):
   before `5c3e3bf`: Ran 739, OK (skipped=10); after `ea0957c`: Ran 755, OK
   (skipped=10). The runner: 755 green. PASS.
3. Pre-registered evaluation: n/a (wiring; "Primary metric: n/a" in both
   preregs). The equivalents — the byte-identical section recompute (c) and
   the 0.0-diff lambda rebuild (1a) — PASS.
4. Metric/filter/bootstrap/threshold as in the prereg: n/a for both; the
   rulings are verbatim in the preregs; no metric promoted, no re-tuning
   (W2fix is a rule fix pinned before its code, with its tests named in
   advance). PASS.
5. Recording path: I may not run `--record` here, so proved from the data
   branch instead: each night's log is a byte prefix of the next (see e), so
   no row of the five older sources moved on any live night; the frozen-
   clock regeneration was done by the pre-merge verifiers. PASS.
6. Mutations (scratch copy of ea0957c):
   - `fpl_league.py` and `tools/league.py` line 190/218, the promotion
     condition `== 0` -> `< 0`: `tests.test_W2fix` Ran 3, FAILED
     (failures=2). Restored: OK.
   - `fpl_sections.py` line 49, `except Exception` -> `except MISSING`:
     `tests.test_W2` FAILED (errors=1,
     `test_any_exception_in_a_section_is_skipped_and_the_other_runs`).
     Restored: OK. PASS.
7. Secrets: see h. PASS.

## VERDICT: PASS

The live run of 3 Nov ran the merged W2 + W2fix code (755 tests green,
the W2fix tests present, pushed to master four hours before the run) as a
real manual dispatch that moved `data` to 39578fe; the status is 30/30 with
check 31 OK for the first time since 26 Oct; the CHIPS and LEAGUE sections
in the live report are byte-identical to a recompute of the runner modules
on the same data (once the night's later archive is hidden) and LEAGUE's
text is coherent with the database; the vice-captain promotion applies to
exactly one stored entry-gameweek and every one of the 945 picks passes the
rule; bottomup_lambda's rows rebuild to 0.0 difference from pre-deadline
inputs on three nights, all rows precede their deadlines, no key is
duplicated, every night's counts match checks 18/29, and the five older
sources' rows were only appended to; the W2 columns are present and
populated as the prereg says; no test or check was weakened and the runner
imports nothing under tools/; no key-like string beyond Odds API event ids
is in the committed files. The one gap is that a real run's log, status and
commit message do not name the code commit; it was established from the
push times and the run's own fingerprints.
