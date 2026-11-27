# verify_W3fix — pre-check of `origin/w3fix-wip` `7c40c6a` (W3fix Rulings 2 and 3, plus fj-wip's tests) before its dry run and merge

**VERDICT: WARN.** Every measured claim in the launch reproduces, no check fails, and the
branch is fit for its dry run. Two things need Boris before the merge: (1) Ruling 3's last
clause, "the FH flag must agree with the base screen in the same report", is met for the
cause it names (the scale) but not in every case, and the question about it is not in
`prereg/W3fix.md`; (2) five of my 35 mutants stay green, four of them gaps in the new
logic's tests. Details and the
other notes are under "Decisions for the chat".

Verifier: Claude Code, model Fable 5.2 (`claude-fable-5-2`); Fable was available, no
fallback. Effort: launched at high, not confirmable. Run: Mon 16 Nov 2026, 18:38 to
19:15 UTC. `.claude/agents/backtest-verifier.md` was read from disk first; it matches my
loaded instructions. No session transcript or chat log was read. I read two of the
implementer's scratch scripts (`r3_hist.py` and its `commits.txt`) only to learn how
claim 5's 186 rows were counted, after my own measurement was done.

State checked: `C:\GIT\FPL` master `6df4cc8`, clean before and after (this file is the only
change). `C:\GIT\FPL-data` at `352228e`, `pull --ff-only` said "Already up to date";
nothing else was run there. All work was done in
`C:\Users\Boris\AppData\Local\Temp\claude\0131a5cb73db9b13\442a647f-7693-4ced-b840-0df7f5bfd943\scratchpad\vw3fix`
(git-archive copies of `7c40c6a`, `860e935`, `6df4cc8`; a copy of the data; a scratch clone
with its remote removed). Nothing was pushed, merged or deleted.

## Summary table

| Check | Result | Evidence in one line |
|---|---|---|
| 0 prereg before code | PASS | each pin is an ancestor of its code commit and earlier by commit time (table below) |
| 1 point-in-time | PASS (nothing is recorded) | the item records no forecast; inputs of the checkpoint run are all before their deadlines |
| 2 suites | PASS | master 855 OK; `860e935` 858 OK three ways; `7c40c6a` 876 OK three ways; trial merge with master 876 OK |
| 3 re-run of the numbers | PASS | 12 Nov case, tonight's report, the id and slot checkpoint runs: every cited figure reproduced |
| 4 rulings and frozen settings | PASS, with note 1 | rulings verbatim on file; FH_GAP 8.0, FH_NOT_A 3, bootstrap settings untouched; one clause of Ruling 3 only partly met |
| 5 recording path | PASS | 2,360 GW11 rows re-recorded with master's code and the branch's: identical in every column but `made_at` |
| 6 mutation | PASS, with note 4 | 30 of my 35 mutants red; the three claimed W3fix mutants and my eight `main()` mutants all red; 5 survive (4 gaps in the new logic's tests, 1 in the mirror) |
| 7 secrets | PASS | no key pattern, `apiKey=` or Authorization value in the 9 changed files or the two preregs |

## Check 0 — prereg committed before the code

| Pin | Code | Gap | Ancestor |
|---|---|---|---|
| `e692192` Ruling 2, Thu 12 Nov 21:25:11 UTC | `14523e2`, 21:27:42 | 2 min 31 s | yes |
| `4274955` Ruling 3 option (a) and FJ, Mon 16 Nov 17:44:51 UTC | `96a7c5f`, 17:53:23 | 8 min 32 s | yes (via merge `860e935`) |
| `2af773c` Ruling 3 addendum, 18:03:13 UTC | `3e4bbd5`, 18:04:04 | 51 s | yes (via merge `14354a3`) |
| `4274955` FJ tie rule and `main()` test | `4455cbd`, 18:05:21 | 20 min 30 s | yes (via merge `620a534`) |

By `git log` the rule holds for all four. The gaps are short; a 51-second gap means the
mirror in `tools/chips.py` was already written when its pin was committed. Git cannot
show the order in the working tree. I found no sign of tuning: the pins hold no fitted
number, and FH_GAP and FH_NOT_A are unchanged.

The rulings are on file verbatim: Thu 12 Nov points 2 and 3, the parked (a)/(b) question,
"Answers, Mon 16 Nov" point 2 (the exact sentence quoted in the launch is in
`prereg/W3fix.md`), the Ruling 3 pin and its addendum; in `prereg/FJ.md` the Mon 16 Nov
point 3 and the pin after it. Item N's frozen entry (CHANGELOG, "2026-10-15 — item N: the
Free Hit screen") is not edited by the branch.

## Check 2 — suites, by discovery, on git-archive copies

| Tree | Bare | With `FPL_DATA_DIR` (copy of data `352228e`, `--restore` run in the copy) | Hostile global git config (`[commit] gpgsign = true`, `[tag] gpgsign = true`) |
|---|---|---|---|
| master `6df4cc8` | 855 OK (11 skipped) | not run (the real run's check 28 says 855) | not run |
| before, `860e935` | 858 OK (11 skipped) | 858 OK (4 skipped) | 858 OK (11 skipped) |
| after, `7c40c6a` | 876 OK (11 skipped) | 876 OK (4 skipped) | 876 OK (11 skipped) |
| trial merge of `7c40c6a` into `6df4cc8` | 876 OK (11 skipped) | not run | not run |

- 855 + 3 (`TonightsExport`) = 858; + 4 (`OneScale`) + 14 (`tests/test_FJ.py`) = 876. The
  21 tests of the two new modules all ran, none skipped.
- The hostile config was in force: a control commit under it fails with exit 128 ("gpg
  failed to sign the data").
- The branch is two commits behind master (`fc36850`, `6df4cc8`; docs only: CHANGELOG,
  the state file, the S8c report, `verify_S8c_final.md`). The trial merge
  (`git merge-tree` in the scratch clone) has no conflict; its tree is `7c40c6a` plus
  those four files.

## Claims 1 to 8

### 1. Ruling 2 — CAPTAIN and BAN RISK read tonight's working export. Confirmed.

- `fpl_squad.current_export` returns `fpl_ship.newest_export(data_dir)`, the working
  `fpl_export_gw<N>.json`; `captain` and `ban_risk` call it in place of
  `fpl_chips.newest_export`. No working export raises `MissingInput`. The nightly runs the
  sections after the sync and before the archive step (`fpl_nightly.py`), so this is
  tonight's export.
- `tests.test_W3fix.TonightsExport` with master's `fpl_squad.py` and the tests kept: red 3
  of 3.
- Mutants: CAPTAIN back on the archive, BAN RISK back on the archive, the archive
  substituted when no working export exists, BAN RISK's header without "from <export>":
  each red.
- Real data, the night of 9 Nov (data `ce1d51f`; Thiago was `a` in the 8 Nov archive and
  `s` that night). BAN RISK with master's code: Thiago P(start) 0.75, P(ban) 0.274. With
  the branch: P(start) 0.00, P(ban) 0.000. Groß moves 0.75 to 1.00. CAPTAIN could not be
  run on that night (the export has no `code`, with either code tree); since 12 Nov, when
  exports carry it, none of our 15 changed status between the archive and the night's
  export, so CAPTAIN has no real case yet. The toy test covers it.
- Tonight (data `352228e`): CAPTAIN and BAN RISK change only in their header line.

### 2. Ruling 3, option (a). Confirmed.

- `fpl_edge.one_week_points`: in a week with own rows, a player with a fixture and no own
  row gets 0, source `no own`. `fpl_chips.own_week_points`: a player through the gate with
  no own row gets 0 in an own week. `free_hit_lines` prints one note per own week.
- Weeks without own rows are unchanged: across 35 nightly data commits, every bottomup-week
  row of both screens is identical with old and new code (asserted to 1e-12).
- `OneScale` with `fpl_edge.py` and `fpl_chips.py` of `860e935` and the tests kept: red 4 of
  4. `test_fpl.FreeHit.test_metric_is_own_where_recorded_else_bottomup` is red on the old
  code too, as it should be after its amendment.
- The three claimed mutants: bottomup back in `one_week_points` red (4 tests); own-model
  back in `own_week_points` red (1); the note dropped red (1).
- Edge cases on tonight's export: one week left, no upcoming fixtures, the own week's
  fixtures removed, no own rows for GW11: no error, and a note only when the week is `own`.

### 3. The 12 Nov case and tonight. Confirmed.

CHIPS's screen on run 1's archive (data `2e0b948`) with the log at `6f9ecb8`:

| | FH XI | ours | gap | flag | Manzambi |
|---|---|---|---|---|---|
| old code | 30.767505 | 22.233000 | +8.534505 | FH candidate (gap > 8) | in the FH XI at 4.21 |
| new code | 28.709000 | 22.233000 | +6.476000 | none | counts 0, not in the XI |
| base screen on run 2's export (old or new) | 28.709000 | 22.233000 | +6.476000 | none | |

The report committed at `6f9ecb8` shows the same two lines (351 and 539). Through
`fpl_chips.live` on that data the only changes are the header note ("1 in this export
(Manzambi)"), the screen's label, the GW11 row and the note; no other CHIPS line moves.

Tonight: I replayed record, watch, report and sections on a copy of data `352228e`
(newest dated archive set to the earlier run's, `93916ee`, as it was when the sections
ran). With master's code the replay equals the real report except the status line, the
REALISED GW8 line (my code copy has no git history for the bundle) and the watch's
recorded time. Master's code against the branch's: the watch file gains one note line; the
report changes in the metric text, three note lines, CHIPS's header note, the screen's
label, and the CAPTAIN and BAN RISK headers. No number moves.

### 4. The addendum — `tools/chips.py`. Confirmed.

- `own_week_points` is text-identical in `fpl_chips.py` and `tools/chips.py`; the changed
  lines of the two files are identical.
- With `tools/chips.py` of `860e935` put back, `test_byte_identical_to_the_tools` is red (1
  failure), as the addendum says.
- On real data the runner's CHIPS section equals the tool's, 36 lines of 36, on the 12 Nov
  data and on tonight's.
- `tools/gw_pass.py` and `tools/planner.py` are not changed by the branch; they reach the
  rule only through `CH.own_week_points`. Tonight no player is affected.

### 5. The measurement for Boris. The figures reproduce; one item is missing from the list.

- The implementer's script, rerun by me on both code trees: 162 of 186 and 171 of 186;
  the base screen's own week changes on 14 of 31 nights; flags added 24 Oct GW9
  (+5.1 to +8.4) and 1 Nov GW10 (+7.3 to +8.3); reason changed 30 Oct GW9. All as claimed.
- That script drops the three nights a gameweek rolled over, and on a day with two runs it
  gives CHIPS the previous day's export, not the earlier run's. My own count takes every
  one of the 35 data commits since 19 Oct, with CHIPS on the newest archive of the parent
  commit (what was on disk), rows paired by gameweek:

| | old code | new code |
|---|---|---|
| week-rows where the two screens agree on flagged or not | 182 of 207 | 191 of 207 |
| of the own-week rows | 25 of 35 | 34 of 35 |
| base screen, own week: "ours" moved | | 19 of 35 commits, always down |
| base screen, own week: FH XI side moved | | 0 of 35 |
| base screen: flag added / removed / reason changed | | 2 / 0 / 2 |

- The second reason change is 31 Oct GW10 (data `cdaa998`): "3 of our XI not 'a'" at +5.6
  becomes "gap > 8" at +8.8. It is absent from the launch's list because that night is a
  rollover night.
- The 16 rows that still disagree with the new code: 15 in bottomup weeks and one own week
  (1 Nov GW10: base +8.31 flagged, CHIPS +7.95 not). All come from CHIPS reading the
  previous export.

### 6. FJ. Confirmed.

- `xi_lex` against my own implementation of the pinned rule (decimals as written, every
  legal XI, highest sum, smallest sorted ids, bench and captain by the lower id) on 1,500
  random 15s with many ties and missing forecasts: 0 differences in the XI, the bench
  order, the captain and the realised points.
- On GW8-10 (clone at `7c40c6a`, data `352228e`, `run.txt` says modified 0):

| Run | own | xp_v2 | d | mean | 90% | verdict |
|---|---|---|---|---|---|---|
| `--tie id` | 41, 69, 62 | 41, 68, 74 | +0, -1, +12 | +3.67 | [-0.67, +8.00] | xp_v2 stays |
| `--tie slot` | 41, 72, 62 | 41, 68, 74 | +0, -4, +12 | +2.67 | [-2.67, +8.00] | xp_v2 stays |

- The slot run equals the committed `worklog/checkpoint_gw10/checkpoint.txt` in every line
  but the header's code and data line.
- Inputs: own snapshots made 23 Oct 14:22, 30 Oct 22:13 and 6 Nov 01:48 UTC, each before its
  deadline; bundles `6034baa`, `e708c91`, `c0c6c3f` committed before their deadlines.
- `tests/test_FJ.py`: 14 tests, green. My eight `main()` mutants (2, 10 to 16): red 8 of 8.
  Mutant 2 is also red with the script's own `assert` removed, so the test reads the
  numbers.
- Rule mutants, mine: largest ids on a tie, no tie-break, bench by the higher id, captain by
  the higher id, FWD capped at 2, DEF minimum 2, captain not doubled, no autosubs, the id
  run back on `realised_on`: all red. Float sums: green, as claimed. In my 1,500 toys float
  sums never picked a different XI (Python 3.12+ sums floats with compensation; the runner
  is on 3.14), so the claim that no realistic toy separates them holds. One more survivor:
  a missing forecast counted 1 in `xi_lex`.

### 7. Suites. Confirmed: 876 OK three ways on `7c40c6a`, 858 OK on `860e935` (table above).

### 8. Point-in-time and secrets. Confirmed.

- Nothing in the item records a forecast. The seven sources re-recorded on two copies of
  tonight's data, one with master's code and one with the branch's: 2,360 GW11 rows each
  (own 296, xg 274, minutes 274, bottomup 274, fpl_ep 672, bottomup_lambda 274, xp_v2 296),
  identical to each other and to the real run's rows in every column but `made_at` (the
  clock). All 64,909 rows of the three logs agree in order.
- Callers: `one_week_points` is used only by `free_hit_table`; `own_week_points` in the
  runner only by `fpl_chips.live`. Neither is on the record path.
- Secrets: the 9 changed files and both preregs hold no `apiKey=`, no Authorization value,
  no 32-hex string and no token pattern. The only long strings in the added lines are test
  names.

## Check 6 — the mutants that stay green

| Mutant | Where | What it means |
|---|---|---|
| CHIPS's header note dropped (in `fpl_chips.py` and `tools/chips.py` together) | `live` | the pin's "Its header notes the rule" has no test |
| the note's gate count taken from every status-`a` player | `free_hit_table` | "<m> in the Free Hit gate" is checked only on a toy where both counts are equal |
| sums compared as floats | `xi_lex` | "sums are compared exactly" is tested on `_exact` alone, not on the XI |
| a missing forecast counts 1 | `xi_lex` | "a missing forecast counts 0" is not tested where it changes the XI |

The fifth survivor: own-model back in `tools/chips.py` alone stays green in W2's identity
test (its toy has no such player); `tests.test_W3fix` covers the runner's copy, and the two
functions are text-identical today.

Count: 35 mutants (15 of W3fix, 20 of `checkpoint.py`), 30 red, 5 green. The four reverts
to the old code (claims 1, 2 and 4) are separate and all red.

## Decisions for the chat

1. **Ruling 3's last clause.** The ruling says "the FH flag must agree with the base screen
   in the same report". After this change the two screens can still disagree: 16 of 207
   week-rows since 19 Oct by my count (15 of 186 by the implementer's), one of them an own
   week (1 Nov GW10). The cause is that CHIPS's screen reads the previous export. On the
   same export the two screens are the same function on the same inputs and cannot differ.
   The parked question offered option (a) "to make the flag agree in every case"; as built,
   (a) removes the scale cause only. Choose: accept the remaining cases (CHIPS one night
   behind, as Ruling 2 allows), or have CHIPS's Free Hit screen, and only that screen, read
   tonight's export. Also: the pin says this question is "parked below, with a
   measurement", but it is not in `prereg/W3fix.md`; the state file says it is in the chat
   reply. It should be in the prereg before the merge.
2. **The amended metric on the base screen.** A flagged player of ours now counts 0 in the
   own week, so "ours" falls and the gap rises: flags added on 2 of 35 past commits, none
   removed. The "3 or more of our XI not 'a'" trigger no longer fires in an own week: the
   count was 3 twice with the old code and is at most 1 with the new (both nights are now
   flagged by the gap). FH_GAP and FH_NOT_A are untouched. Is that the intended reading of
   option (a)?
3. **`tools/chips.py`** (already parked): keep the mirror (a), or amend W2's identity test
   (b). The mirror is exact and W2's test is green.
4. **The surviving mutants** (table above: four gaps, plus the mirror). Add small tests
   before the merge, or accept them.
5. **CAPTAIN's header lost the export's date.** It now reads "from fpl_export_gw10.json".
   On a night when the sync fails, that file is the restored copy of last night's export
   (the run is red that night). Should both headers also print the export's own timestamp,
   as the watch file does?
6. **The committed checkpoint output** (`worklog/checkpoint_gw10/checkpoint.txt`,
   `run.txt`) is from `b7e4716`; the script changed in `4455cbd`. My rerun on `7c40c6a`
   gives the same numbers. Regenerate it now, or leave it until the GW15 run?
7. **Before the merge:** the CHANGELOG amendment entry for item N (the pin says it lands
   with the item) and the item report are not on the branch yet; the branch needs master's
   two docs commits (clean merge, 876 OK on the merged tree). The launch's claim 5 should
   add 31 Oct GW10 to its reason changes.

## Evidence files (scratch, not committed)

Under `...\scratchpad\vw3fix`: `out\*.txt` (the eight suite runs), `scripts\` (my scripts
and mutant specs), `mut\`, `mutfj\` (mutant copies), `nov12\` (the 12 Nov case),
`tn_old\`, `tn_new\` (tonight's replay), `hist\` (the 35-commit measurement and the
implementer's script rerun), `ck_id\`, `ck_slot\` (the checkpoint runs with `run.txt`).

VERDICT: WARN — every claim reproduces and no check fails: the suites are 876 OK three
ways (858 before, 855 on master, 876 on the trial merge), the 12 Nov false flag is gone
and CHIPS's screen then equals the base screen, tonight's report changes only in notes and
headers, the seven recorded sources do not move, and the GW15 tie rule matches an
independent implementation. It is not a PASS because Ruling 3's requirement that the flag
agree with the base screen in the same report is met only for the scale cause (16 of 207
past week-rows would still differ, since CHIPS reads the previous export), the question
about that is not on file in the prereg, and five of my 35 mutants survive the tests (four
gaps in the new logic's tests, one in the mirror). None of this blocks the dry run; items 1, 2 and 4 need Boris's answer before
the merge.

---

# Re-check of `origin/w3fix-wip` `5385c57` (Thu 19 Nov 2026) — Boris's answers of Thu 19 Nov night, points 1, 2, 4 and 5

**VERDICT: WARN.** Seven of the eight claims reproduce in full and no check fails. Claim 3
does not reproduce in full: of my five surviving mutants, four are now red and one is
still green. The float-sum mutant, exactly as I ran it in the pre-check (`xi_lex` builds
its values as floats), passes all 884 tests; the new test covers the comparison key but
not what `xi_lex` feeds it. Ruling point 4 asks for a test for each of the five, so this
needs Boris's answer (decision 1). Everything else is ready for its landing steps.

Verifier: Claude Code, model Fable 5.2 (`claude-fable-5-2`); Fable was available, no
fallback. Effort: launched at high, not confirmable. Run: Thu 19 Nov 2026, 21:49 to
22:20 UTC. `.claude/agents/backtest-verifier.md` was read from disk first; it matches my
loaded instructions. No session transcript or chat log was read.

State checked: `C:\GIT\FPL` master `2f0f3cd` (origin/master is `448e652`; `101a485` and
`2f0f3cd` are local only), with the untracked folder `worklog/gw_pass/gw11/` left alone.
`origin/w3fix-wip` fetched at `5385c57`. `C:\GIT\FPL-data` at `029bcfd`; `pull --ff-only`
said "Already up to date". All work was done in
`C:\Users\Boris\AppData\Local\Temp\claude\0131a5cb73db9b13\442a647f-7693-4ced-b840-0df7f5bfd943\scratchpad\vw3fix2`
(git-archive copies of `5385c57`, `38a2174`, `7c40c6a`, `2f0f3cd`; a copy of the data with
`--restore` run in the copy; the pre-check's scratch clone moved to `5385c57`). Nothing
was pushed, merged or deleted.

One deviation to report: my script that lists each data commit's exports ran read-only
git commands (`log`, `ls-tree`, `rev-parse`, `show`) with `-C C:\GIT\FPL-data`, because my
edit to point it at `C:\GIT\FPL` did not apply. Nothing was written there: its status is
clean and its head is still `029bcfd`. Later reads of the data branch went through
`C:\GIT\FPL`'s object store.

## Summary table

| Check | Result | Evidence in one line |
|---|---|---|
| 0 prereg before code | PASS | the pin `101a485` (21:03:08 UTC) is an ancestor of `38a2174` (21:16:21 UTC) and `5385c57` (21:25:47 UTC) |
| 1 point-in-time | PASS (nothing is recorded) | the screen reads the log through `forecasts` (pre-deadline snapshots only); the checkpoint's inputs are unchanged |
| 2 suites | PASS | `7c40c6a` 876 OK; `5385c57` 884 OK three ways; trial merge with master `2f0f3cd` 884 OK |
| 3 re-run of the numbers | PASS | every measured claim reproduced on real data (claims 1, 2, 4, 5, 7 below) |
| 4 rulings and frozen settings | PASS, with decision 1 | the answers and their pin are on file verbatim; FH_GAP 8.0, FH_NOT_A 3 and the bootstrap settings are untouched; ruling point 4 is met for four of the five mutants |
| 5 recording path | PASS | 2,340 GW11 rows re-recorded with master's code and the branch's: identical in every column but `made_at` |
| 6 mutation | WARN | 22 of 28 mutants red; the original float-sum survivor is still green; five other survivors are minor (table below) |
| 7 secrets | PASS | no key pattern, `apiKey=` or Authorization value in the 9 changed files or the prereg additions |

## Check 0 — prereg committed before the code

| Commit | What | Time (UTC, Thu 19 Nov) |
|---|---|---|
| `448e652` | Boris's answers verbatim in `prereg/W3fix.md` and `prereg/FJ.md` | 20:53:32 |
| `101a485` | the pin of points 1, 2, 4, 5 | 21:03:08 |
| `307ceb7` | master (with the pin) merged into the branch | 21:05:08 |
| `38a2174` | the code and tests of points 1, 2, 4, 5 | 21:16:21 |
| `5385c57` | `newline=''` on the new open | 21:25:47 |

The pin precedes its code by 13 min 13 s and is its ancestor. The pin's heading says
"21:10 UTC"; its commit is at 21:03 UTC (a wrong time in the heading, nothing else). The
five answers quoted in the launch equal lines 216 to 220 of `prereg/W3fix.md` word for
word, and `prereg/FJ.md` holds answer 8. The branch does not touch `CHANGELOG.md` beyond
master's own entries, so item N's frozen entry is unedited. Only `w3fix-wip` was pushed
(a work branch); there is no `dry/W3fix` yet.

## Check 2 — suites, by discovery, on git-archive copies

| Tree | Bare | With `FPL_DATA_DIR` (copy of data `029bcfd`, `--restore` in the copy) | Hostile global git config (`[commit] gpgsign = true`, `[tag] gpgsign = true`) |
|---|---|---|---|
| before, `7c40c6a` | 876 OK (11 skipped) | not rerun (pre-check: 876) | not rerun (pre-check: 876) |
| after, `5385c57` | 884 OK (11 skipped) | 884 OK (4 skipped) | 884 OK (11 skipped) |
| trial merge of `5385c57` with master `2f0f3cd` | 884 OK (11 skipped) | not run | not run |
| `5385c57`'s tests on `7c40c6a`'s code | 884 run, 8 red | | |

- 876 + 8 = 884. The eight new tests, by name: `TonightsExport.test_the_headers_print_the_exports_own_time`,
  `OneScale.test_the_gate_count_skips_a_player_under_45_minutes`,
  `OneScale.test_tools_chips_counts_zero_in_its_own_week`,
  `InjuryCrisisStillFlags.test_three_flagged_starters_without_own_rows_still_trigger`,
  the three of `ChipsScreenOnTonightsExport`, and
  `GW15TieRule.test_a_missing_forecast_counts_zero`. `tests.test_W3fix` runs 14 and
  `tests.test_FJ` 15, none skipped.
- The hostile config was in force: a control commit under it fails with exit 128 ("gpg
  failed to sign the data").
- The trial merge (`git merge-tree` in the scratch clone) has no conflict; it adds
  master's `prereg/FM.md` change and `worklog/verify_FM.md`.

## Claims 1 to 8

### 1. Point 1 — CHIPS's Free Hit screen is built from tonight's working export. Confirmed.

- Code: `fpl_chips.live` and `tools/chips.py`'s `live` read `fpl_ship.newest_export(data_dir)`
  and build the screen with `E.free_hit_table(dt, E.forecasts(log_rows, dt))`, the log
  being the data folder's `projection_log.csv` at that moment. The changed lines of the
  two files are identical except the `# noqa` on the import. The calculator above still
  reads `newest_export` (the dated archive).
- Tonight's data (`029bcfd`, the copy after `--restore`): the runner's section and the
  tool's are identical, 36 lines of 36. CHIPS's screen equals the base screen line for
  line, 8 lines (the header row, GW11 to GW16, one note). GW11: FH XI 28.7, ours 22.2,
  gap +6.5, no flag.
- On tonight's data the working export and the newest archive are the same file, so that
  comparison cannot tell the two apart. I therefore replayed every one of the 38 data
  commits since 19 Oct as the sections saw it: `exports/` holding the parent commit's
  newest dated export, the working export being that commit's own, with that commit's log
  and database. Result: 38 of 38 ran; runner equals tool 38 of 38; CHIPS's screen equals
  the base screen of that night line for line 38 of 38 (228 week-rows, every flag equal);
  the screen's label names the working export 38 of 38; the calculator's header names the
  archive 38 of 38. On 32 of the 38 nights the archive's own screen differs from that
  night's, so the comparison does discriminate. The three rollover nights (archive one
  gameweek behind the working export) are among the 38.
- The 12 Nov case (`6f9ecb8`) is one of the 38: CHIPS's screen equals the base screen,
  GW11 gap +6.48, no flag (before Ruling 3 CHIPS showed +8.53, flagged).
- No working export (the working files removed from a copy): the section is 28 lines and
  ends with the one line "FREE HIT SCREEN not built: no working export
  (fpl_export_gw<N>.json) in the data folder - never last night's"; runner equals tool.

### 2. Point 2 — "not a" is counted on our best XI before the zero. Confirmed.

- Code: `free_hit_table` rebuilds, for our players marked `no own`, the bottomup value
  with the same inputs `one_week_points` uses, picks our best XI on those values and
  counts "not a" there. `ours` and the gap still come from the amended metric.
- Three code trees on every data commit, base screen (that night's export and log):

| | 35 commits to `352228e` | all 38 to `029bcfd` |
|---|---|---|
| week-rows | 210 (35 own-week) | 228 (38 own-week) |
| not-'a' count equals the pre-Ruling-3 code's (`860e935`) | 210 of 210 | 228 of 228 |
| gap, FH XI and `ours` equal the Ruling 3 code's (`7c40c6a`), to 1e-12 | 210 of 210 | 228 of 228 |
| flag equals `free_hit_flag`(Ruling 3's gap, the pre-Ruling-3 count) | 210 of 210 | 228 of 228 |
| largest own-week count: pre-Ruling-3 / Ruling 3 / now | 3 / 1 / 3 | 3 / 1 / 3 |

- The same holds on the previous-export side (228 of 228 on each line).
- "Reasons equal the pre-Ruling-3 code's" is exact for the not-'a' reason. The whole flag
  text differs from the pre-Ruling-3 code's in 4 own-week rows, all through the gap, which
  is Ruling 3's: 24 Oct GW9 and 1 Nov GW10 are flagged by "gap > 8" (not flagged before);
  30 Oct GW9 and 31 Oct GW10 now read "FH candidate (gap > 8, 3 of our XI not 'a')"
  (before Ruling 3: "3 of our XI not 'a'" alone; under `7c40c6a`: "gap > 8" alone).
- The toy test `InjuryCrisisStillFlags` is red on `7c40c6a`'s code and on my mutant that
  counts after the zero.

### 3. Point 4 — the five surviving mutants. Four red, one still green.

| Pre-check survivor | On `5385c57` | Killed by |
|---|---|---|
| 1 CHIPS's header note dropped (both files) | RED | `ChipsScreenOnTonightsExport.test_the_header_note` |
| 2 the note's gate count from every status-'a' player | RED | `OneScale.test_the_gate_count_skips_a_player_under_45_minutes` and two more |
| 3 float sums in `xi_lex` (`val` built with `float`, my pre-check mutant unchanged) | **green** | nothing: `tests.test_FJ` 15 OK, and no other test imports `checkpoint.py` |
| 4 a missing forecast counts 1 in `xi_lex` | RED | `GW15TieRule.test_a_missing_forecast_counts_zero` |
| 5 own-model back in `tools/chips.py` alone | RED | `OneScale.test_tools_chips_counts_zero_in_its_own_week` |

About survivor 3:
- The new lines in `test_sums_are_compared_exactly` call `xi_key` with exact values the
  test builds itself. A mutant that sums floats inside `xi_key` is red. A mutant in
  `xi_lex` (values built as floats, or an inline float key that bypasses `xi_key`) is
  green: nothing checks what `xi_lex` hands to the key. The pre-check described the gap as
  "tested on `_exact` alone, not on the XI"; that is still so.
- The pin's wording for this test is "its comparison key ties 0.1 + 0.2 with 0.3", and
  the test does exactly that. So the code matches its pin; the pin's test does not kill
  the mutant the ruling was about.
- How much it matters: on the runner's Python (3.14, whose built-in `sum` is compensated)
  I could not make the mutant choose another XI: 0 of 6,000 random 15s, 3,074 of them
  with a tie at the top. With a plain left-to-right float loop (older Pythons, or a
  rewrite of the sum) 281 of the 6,000 would differ. So the exact arithmetic is a real
  guard, and it is unguarded by the tests.
- A small check closes it: in my scratch, a spy on `xi_key` that asserts every value is
  a `Fraction` separates the code (550 calls, all exact) from both mutants.

### 4. Point 5 — the headers print the export's own generated time. Confirmed.

- Tonight's data: CAPTAIN's header reads "GW11 from fpl_export_gw10.json (generated
  2026-11-19 02:49 UTC): ..." and BAN RISK's "GW11 from fpl_export_gw10.json (generated
  2026-11-19 02:49 UTC) (S12's rule): ...". The export's field is
  `2026-11-19T02:49:05+00:00`. Against `7c40c6a` these two header lines are the only
  change in the two sections (25 lines each).
- `_gen` probed directly: an aware time is converted to UTC (`03:49:05+01:00` gives
  02:49 UTC); a naive time is read as UTC (`02:49:59` gives 02:49 UTC); seconds are cut,
  not rounded; no field, an empty value or unreadable text gives "unknown".
- This machine is on Central European Time (UTC+1), so the naive-time test does
  discriminate here: my mutant that reads a naive time in the machine's zone is red. On
  a machine already on UTC (the runner) that mutant would pass; the test cannot be made
  to see it there.

### 5. Red on the previous code. Confirmed: 8 tests.

`5385c57`'s tests on `7c40c6a`'s five code files, the whole suite: 884 run, 7 failures
and 1 error. They are `FreeHit.test_gap_is_fh_minus_ours_by_the_same_metric`,
`Captain.test_the_lines_are_gw_pass_section_seven`, the two screen tests of
`ChipsScreenOnTonightsExport`, `InjuryCrisisStillFlags`, `TonightsExport`'s captain and
headers tests, and `test_sums_are_compared_exactly`. The last is an error only because
`xi_key` does not exist in the old code. The four tests written for unchanged behaviour
(header note, gate count, tools/chips own week, missing forecast) are green on the old
code, as they must be; they are red on their mutants.

"Mutants 8 of 8 red": the implementer's eight mutants are not on the branch, so I could
not rerun them. Of my own 28, 22 are red; my survivor 3 as I ran it is not (claim 3).

### 6. Suites. Confirmed: 884 OK three ways on `5385c57`; `7c40c6a` 876 OK bare (table above).

### 7. Nothing records differently. Confirmed.

The seven sources re-recorded on three copies of tonight's data, with master's code
(`2f0f3cd`), `7c40c6a`'s and `5385c57`'s: 2,340 GW11 rows each (own 292, xg 271, minutes
271, bottomup 271, fpl_ep 672, bottomup_lambda 271, xp_v2 292). The three logs and the
real one are identical in every column but `made_at`, all 71,935 rows, in order.

The same replay through watch, report and sections (the 19 Nov archive removed, as it was
when the sections ran):
- master against `5385c57`: the watch file gains the one note line. The report changes in
  the metric text, the not-'a' legend, two note lines, CHIPS's header note, the screen's
  label, and the CAPTAIN and BAN RISK headers. No number moves.
- `7c40c6a` against `5385c57`: the watch file is the same but for its recorded time. The
  report changes in four places: the legend (two lines), the screen's label, and the two
  headers.

The checkpoint script, refactored by `38a2174` (`xi_key`): rerun in the scratch clone at
`5385c57` (`run.txt`: modified 0), `--tie id` gives d = +0, -1, +12, mean +3.67, 90%
[-0.67, +8.00], xp_v2 stays; `--tie slot` equals the committed `checkpoint.txt` below its
header. Both equal my `7c40c6a` runs line for line below the header. `xi_lex` against my
independent rule on 1,500 random 15s: 0 differences.

### 8. What is left. Decisions 6 and 7 are not done; they are not the only items left.

Not on the branch at `5385c57`:
- `worklog/checkpoint_gw10/checkpoint.txt` and `run.txt` are still from `b7e4716` (FJ
  answer 8: regenerate with the landing; the script has changed twice since).
- The CHANGELOG entries (item N's amendment and the item's own), the report
  `worklog/cc_<date>_W3fix.md`, the state file. The pre-check asked the report to add
  31 Oct GW10 to its reason changes.
- Master's `2f0f3cd` (docs; a clean merge, 884 OK on the merged tree).
- The runner-work steps, none started: the dry run (`dry/W3fix`), the `pre-W3fix` tag,
  the merge, Boris's real run and its check, and deleting the dry branches.
- Whatever decision 1 brings.

## Check 6 — mutants on `5385c57`

28 mutants: 22 red, 6 green.

| Group | Red | Green |
|---|---|---|
| the five pre-check survivors, plus two variants of the float one | 5 (survivors 1, 2, 4, 5; float sums inside `xi_key`) | 2 (survivor 3 as run before; `xi_lex` with an inline float key) |
| point 1 (8) | 6: screen on the archive (both files; the tool alone); calculator moved to tonight's export; label names the archive; no working export followed by the archive's table; no working export replaced by the archive's screen | 2 (below) |
| point 2 (5) | 4: count after the zero; count on all 15; frozen values left at 0; `ours` and the gap from the frozen XI | 1 (below) |
| point 5 (7) | 6: naive time in the machine's zone; aware time not converted; either header without the time; seconds printed; the file's modified time in place of the export's | 1 (below) |
| `5385c57` (1) | 1: `newline=''` dropped (`test_fpl.StepTwoFiles`) | |

The four green ones beside the float pair, all minor:

| Mutant | Why it is green | Measured on real data |
|---|---|---|
| the screen's log read through the archive's deadlines (`E.forecasts(log_rows, d)`) | the toy's two exports share their deadlines | the same rows are read and the screen is identical on 38 of 38 commits |
| the frozen value by the three-layer terms, not bottomup | the toys' counts do not depend on the scale | no count or flag differs on 456 week-rows (38 commits, both sides) |
| no working export: the archive's table printed above the one line | the test reads the header line and what follows it | contrived; the two natural forms are red |
| an export with no readable `generated`: the section stops, where the code prints "unknown" | no test has such an export | |

## Notes

- CHIPS's screen label says "tonight's export" and prints no time. On a night the sync
  fails, the working export is the restored copy of last night's. Point 5 named the
  CAPTAIN and BAN RISK headers only.
- The report's legend now says the not-'a' count is taken before the zero. The watch
  file's one-line legend does not. In an injury-crisis week the table can show "not a 3"
  beside an `ours` XI that holds fewer flagged players; that is the ruling.
- The Ruling 3 pin of Mon 16 Nov says the CHANGELOG amendment "lands with the item,
  before the GW11 deadline". The answers of Thu 19 Nov move the landing to after that
  deadline, so the amended screen first appears for GW12. The entry should say so.

## Decisions for the chat

1. **The float-sum mutant still survives.** Ruling point 4 asks for a test for each of the
   five. Four are covered. For the fifth, the new test checks `xi_key` with exact values
   it builds itself; `xi_lex` handing floats to the key passes all 884 tests. Add a test
   of what `xi_lex` hands to its key (a few lines; a spy does it), or accept the gap on
   the grounds that on Python 3.14 the mutant changed no XI in 6,000 toys (it would on a
   plain float loop, 281 of 6,000)?
2. **The other four green mutants** (table above): add tests, or accept them as minor?
3. **The dry run's timing.** The freeze from Fri 20 Nov 05:00 UTC is "tools and worklog
   only", and W3fix lands from Sat 21 Nov. May `dry/W3fix` be pushed during the freeze
   (it writes only `data-dryrun-W3fix`), or does it wait until after the deadline (Sat 21
   Nov 11:00 UTC)? No ruling on file covers a dry-run push inside the 30-hour window.
4. **CHIPS's screen label**: print the export's generated time there too, as point 5 does
   for the two headers, or leave it?
5. **Landing list** (claim 8): regenerate `checkpoint.txt` and `run.txt`; the CHANGELOG
   entries (saying the amended screen starts with GW12); the report (with 31 Oct GW10);
   merge master `2f0f3cd`; then the dry run, the tag, the merge and Boris's real run.

## Evidence files (scratch, not committed)

Under `...\scratchpad\vw3fix2`: `out\new_bare.txt`, `new_data.txt`, `new_host.txt`,
`old_bare.txt`, `merged_bare.txt`, `oldcode_newtests.txt` (the six suite runs);
`out\mutants.txt`, `scripts\spec_recheck.json`, `scripts\spec_recheck2.json`, `mut\` (the
mutants); `hist\` (`plan.json`, `result_pre.json`, `result_r3.json`, `result_new.json`,
`result_p2d.json`, `live_new.json`: the 38-commit measurements); `tn_master\`, `tn_r3\`,
`tn_new\` (tonight's replay); `ck_id\`, `ck_slot\` (the checkpoint runs with `run.txt`);
`scripts\float_search.py`, `scripts\spy.py` (survivor 3).

VERDICT: WARN — every measured claim reproduces and no check fails: 884 OK three ways on
`5385c57` (876 before, 884 on the trial merge with master), 8 tests red on the previous
code, CHIPS's Free Hit screen equals the base screen line for line on tonight's data and
on all 38 data commits replayed as the sections saw them, the not-'a' count equals the
pre-Ruling-3 code's and the gap equals Ruling 3's on all 228 week-rows, the two headers
print the export's own time in UTC, and the seven recorded sources do not move. It is not
a PASS because ruling point 4 asks for a test for each of the five surviving mutants and
one still survives: the float-sum mutant as I ran it in the pre-check passes all 884
tests, since the new test checks the comparison key and not what `xi_lex` feeds it. That
needs Boris's answer (add the small test, or accept it); the landing steps listed under
claim 8 are still to do.

---

# Re-check of `origin/w3fix-wip` `3847ebd` (Fri 27 Nov 2026) — Boris's answers of Fri 27 Nov, 1, 2 and 4

**VERDICT: WARN.** No check fails and every measured claim reproduces. Answers 1 and 4
are done as pinned. Answer 2 is done for three of the four minor mutants. For the fourth
(the frozen value by the three-layer terms) the new test is red on the mutant as the
implementer wrote it, but the same wrong behaviour written with the terms spelled out
passes all 890 tests. The pin asks for "a toy whose count depends on the scale"; the
toy's player is a defender, and for a defender the three-layer terms are all the terms.
That needs Boris's answer (decision 1). The runner change itself is one label line and
moves nothing else.

Verifier: Claude Code, model Fable 5.2 (`claude-fable-5-2`); Fable was available, no
fallback. Effort: as launched, not confirmable from inside the run. Run: Fri 27 Nov 2026,
12:56 to 13:33 UTC. `.claude/agents/backtest-verifier.md` was read from disk first; it
matches my loaded instructions. No session transcript or chat log was read, and I did
not open the scratch files that hold pasted chat text (`rulings_fri27.txt`,
`answers_*.txt`).

State checked:
- `C:\GIT\FPL` master `cf5b429`, clean; GitHub holds `w3fix-wip` at `3847ebd` and master
  at `cf5b429` (`ls-remote`); there is no `dry/*` branch yet.
- The worktree `scratchpad\w3fix` is on `w3fix-wip` at `3847ebd`, clean before and after.
- `C:\GIT\FPL-data` at `2efc924`. I did not pull, and I did not need `--restore`: every
  working export there already equals its newest dated copy byte for byte. All 325 files
  have the same SHA-256, size and modified time before and after my run.
- All work was done under `scratchpad\verify_w3fix_27`: git-archive copies of `3847ebd`,
  `5b0964c` and `5385c57`, a clone of `w3fix-wip`, and copies of the data. Nothing was
  committed, pushed, merged or deleted outside that folder.

The implementer notes that the cleanup of the temp folder deleted 325 tracked files from
this worktree at 06:00 and that they were restored. My checks do not depend on the
worktree's files: they ran on copies taken from the commit. `3847ebd` deletes no file
relative to master.

## Summary table

| Check | Result | Evidence in one line |
|---|---|---|
| 0 prereg before code | PASS | rulings and pins `2831a63` (12:30:19 UTC) are an ancestor of the code `3847ebd` (12:55:30 UTC) |
| 1 point-in-time | PASS (nothing is recorded) | the screen reads 14,248 log rows, 0 made at or after their deadline; rebuilt from the working export it equals CHIPS's screen on 47 of 47 nights |
| 2 suites | PASS | `5b0964c` 884 OK; `3847ebd` 890 OK four ways; 6 tests added, 0 removed |
| 3 re-run of the numbers | PASS | suites, the 2 red tests on the previous code, the mutants and the label on tonight's data all reproduce |
| 4 rulings and frozen settings | PASS, with decision 1 | answers 1 to 5 and their pin are on file; no constant is touched; answer 2's second test does not do what its pin describes |
| 5 recording path | PASS | 2,400 GW12 rows re-recorded with the old and the new code: 0 cells differ outside `made_at` in 90,969 rows |
| 6 mutation | WARN | 39 of 42 new mutants red; 3 green, one of them a real gap (decision 1); 11 of 11 rebuilt earlier mutants red |
| 7 secrets | PASS | no key pattern, `apiKey=` or Authorization value in the 4 changed files or the commit's added lines |

The five checks of the launch:

| Asked | Result |
|---|---|
| (1) Answer 1: the spy test, red on both float variants | PASS |
| (2) Answer 2: one test per minor mutant, each red on its mutant | three PASS; the second is red on one spelling of its mutant and green on the other (WARN) |
| (3) Answer 4: the label, both files byte for byte, the restored copy, the only report change | PASS |
| (4) Suites 890 OK; earlier claims hold; no recorded row moves | PASS |
| (5) The nightly imports nothing under `tools/` or `analysis/`; no forecast can move | PASS |

## Check 0 — prereg committed before the code

| Commit | What | Time (UTC, Fri 27 Nov) |
|---|---|---|
| `2831a63` | Boris's rulings verbatim and the pin of answers 1 to 5, in `prereg/W3fix.md` | 12:30:19 |
| `cf5b429` | master's head (worklog and prereg only since `2831a63`) | 12:35:25 |
| `5b0964c` | master merged into the branch | 12:41:30 |
| `3847ebd` | the code and tests of answers 1, 2 and 4 | 12:55:30 |

- The pin precedes its code by 25 min 11 s and is its ancestor. `prereg/W3fix.md` is the
  same file at `2831a63` and at `3847ebd`.
- The pin's heading says "12:40 UTC"; its commit is at 12:30 UTC (a wrong time in the
  heading, nothing else).
- `5385c57` to `5b0964c` changes only `prereg/` and `worklog/` (no code, no test, not
  `checkpoint.py`). `5b0964c` to `3847ebd` changes four files: `fpl_chips.py` and
  `tools/chips.py` (3 lines each), `tests/test_W3fix.py`, `tests/test_FJ.py`.
- Against master the whole branch changes 9 files and deletes none; `cf5b429` is the
  merge base.

## Check 2 — suites, by discovery

| Tree | How | Result |
|---|---|---|
| `5b0964c` (before) | git-archive copy, plain | 884 OK, 11 skipped |
| `3847ebd` | git-archive copy, plain | 890 OK, 11 skipped |
| `3847ebd` | the same, `FPL_DATA_DIR=C:/GIT/FPL-data` (data `2efc924`) | 890 OK, 4 skipped |
| `3847ebd` | a clone, run from another folder with `-s`/`-t`, empty global git config, system config off, `TZ=JST-9` | 890 OK, 11 skipped |
| `3847ebd` | the clone again, global git config with `gpgsign = true` for commits and tags, `TZ=PST8PDT` | 890 OK, 11 skipped |
| `5b0964c`'s code with `3847ebd`'s two test files | git-archive copy, plain | 890 run, 2 failures |

- The 884 earlier test ids are all in the 890; the six new ones are the five tests of
  answers 1 and 2 and the label test.
- The two failures on the previous code are
  `test_the_label_prints_the_exports_own_time` (new) and
  `test_the_screen_is_the_base_screen_of_tonight` (an existing test whose head assertion
  was amended). The commit message calls them "2 of the new tests"; one is new and one is
  amended. The five tests for unchanged behaviour are green on the old code, as they
  must be.

## The five checks of the launch

### (1) Answer 1 — the `xi_lex` spy test. Confirmed.

- `GW15TieRule.test_xi_lex_hands_its_key_exact_values` patches `xi_key` with a spy. It
  asserts that every value handed over is a `Fraction`, that every player of the XI has a
  value, and that the key is called once per formation-legal XI, on three projections.
- Red on both variants named in the pin, and on a third spelling:

| Mutant | Result |
|---|---|
| `val` built with `float` (my survivor of 16 and 19 Nov) | RED |
| an inline float key on the raw forecasts, bypassing `xi_key` | RED |
| an inline float key on `float(val[...])`, bypassing `xi_key` (the implementer's form) | RED |

- Two wrong implementations still pass all 890 tests:
  - `xi_key` is called and its result thrown away, and a float key decides;
  - `val` is built as `Fraction(float(v))`, the binary value rather than the decimal
    written.
- Neither changes an XI. On 9,000 random 15s (three kinds of forecast values; 1,750 with a
  tie at the top) both, and the float-`val` mutant, choose the code's XI 9,000 times of
  9,000 on Python 3.14. So I count them as contrived, not as a gap. The spy is the check
  I proposed on 19 Nov; it tests the type handed over, not the value.

### (2) Answer 2 — one test per minor mutant. Three confirmed; the second is partial.

| Minor mutant of my Check 6 | New test | My mutants |
|---|---|---|
| 1 the screen's log through the archive's deadlines | `test_the_screen_reads_the_log_through_tonights_deadlines` | 4 of 4 red (each file alone, both, and the log not cut at all) |
| 2 the frozen value by the three-layer terms | `test_the_frozen_value_is_bottomup_with_all_terms` | 2 of 3 red; **1 green** |
| 3 no working export, the archive's table above the line | `test_no_working_export_prints_no_table` | 4 of 4 red (each file alone, both, and the table below the line) |
| 4 an unreadable `generated` stops the section | `test_an_unreadable_generated_time_prints_unknown_and_goes_on` | 5 of 5 red (raise; no `except`; only a missing field handled; only bad text handled; the raw text printed) |

About mutant 2:
- The mutant has two spellings with the same behaviour. `project_week(..., w)` with no
  terms (the default is the three-layer terms) is RED. `project_week(..., w,
  three_layer_terms(pos))` is **green**: it passes `tests.test_W3fix` and the whole suite,
  890 OK.
- Why: the test plants `project_week` to return 40 when `terms == ALL_TERMS` and 0
  otherwise, for one of our players. That player (`OneScale.mine`) is a defender, and
  `three_layer_terms` returns `ALL_TERMS` for keepers and defenders. So for him the two
  scales are one scale. The test tells the code from the mutant only by the argument
  being left out, not by the value.
- The pin's words for this test are "a toy whose count depends on the scale". With a
  defender it does not.
- I cannot say which spelling I ran on 19 Nov: the cleanup removed that mutant's files.
  The report of 19 Nov describes the behaviour, which is the same for both.
- How much it matters: small. On tonight's data the green mutant's CHIPS section is byte
  for byte the code's. On 19 Nov the same behaviour changed no count or flag on 456
  week-rows. It can only differ for a midfielder or forward of ours with no own row.
- The fix is one word in the fixture. In a scratch copy I chose the toy player from
  midfielders and forwards (`p["pos"] in (3, 4)`): the code stays 19 OK in
  `tests.test_W3fix`, and both spellings go red.

### (3) Answer 4 — the label. Confirmed.

- Both files print `FREE HIT SCREEN from <file> (generated <_gen(dt)>) (tonight's export;
  ...`, with `fpl_squad._gen`, the function behind the CAPTAIN and BAN RISK headers. The
  whole `live()` function is identical in `fpl_chips.py` and `tools/chips.py` (107 lines),
  and the two diffs are the same three lines.
- Tonight's data (`2efc924`, the 27 Nov archive removed, as it was when the sections ran):
  `FREE HIT SCREEN from fpl_export_gw11.json (generated 2026-11-27 03:47 UTC) (tonight's
  export; ...`. The export's field is `2026-11-27T03:47:30+00:00`. Runner equals tool,
  35 lines.
- The restored copy, on real data, written by the runner's own `--restore` into a copy
  with no working exports:

| Case | Working export | File written | Label | CAPTAIN and BAN RISK headers |
|---|---|---|---|---|
| the 27 Nov archive is the newest (tomorrow's sync fails) | the copy of 27 Nov's | 27 Nov 13:04 UTC | generated 2026-11-27 03:47 UTC | the same time |
| the 26 Nov archive is the newest (tonight's sync had failed) | the copy of 26 Nov's | 27 Nov 13:04 UTC | generated 2026-11-26 03:46 UTC | the same time |

- The only report change on tonight's data. Record, watch, report and sections replayed
  on two copies, with `5b0964c`'s code and `3847ebd`'s:
  - the report: 654 lines each, one line differs, the label;
  - the watch file: identical, 82 lines;
  - CAPTAIN and BAN RISK: identical.
- 17 mutants for the label, 17 red: no time; the archive's field; the file's modified
  time; the clock; the raw text cut to minutes; the time moved inside the note; "unknown"
  printed as something else; the archive's field whenever the two exports hold the same
  players; a naive time read in the machine's zone; an aware time not converted; seconds
  printed; the label right with the screen back on the archive. The first three were run
  on each file alone, the second and third also on both.
- The tool's own command line (`tools/chips.py --data <copy> --out <scratch>`), run from
  another folder on the clone, prints the same label; its `run.txt` says commit `3847ebd`,
  modified 0.

### (4) Suites, the earlier claims, the recording path. Confirmed.

- Suites: the table above. 890 OK plain, with the data, and two hostile ways.
- The code of the earlier claims is unchanged: outside tests, `5385c57` to `3847ebd`
  changes only the label lines.
- Eleven of the earlier checks' mutants, rebuilt on `3847ebd`, are all red: the screen on
  the archive (both files; the tool alone), the label naming the archive, the header note
  dropped, own-model back in either chips file alone, "not a" counted after the zero, the
  gate count from every status-'a' player, a missing forecast counted 1, either header
  without its time.
- The nights, replayed as the sections saw them with `3847ebd`'s code, on every data
  commit (52; 5 cannot run: two have no archive from a night before, three hold pre-S2
  exports):

| | 47 nights |
|---|---|
| runner's CHIPS section equals the tool's | 47 |
| CHIPS's screen equals the base screen of that night's export, line for line | 47 (282 week-rows) |
| the label's time equals the export's own field, in UTC to the minute | 47 |
| the calculator's header names the night before's archive | 47 |
| BAN RISK's header carries the export's name and time | 47 |
| CAPTAIN's header carries them | 19; on the other 28 (to 11 Nov) the export has no `code` and CAPTAIN is skipped, as before |

  The 9 nights since the last re-check (20 to 27 Nov, with Boris's second run of 20 Nov)
  are among them, and so are the four rollover nights (23 Oct, 31 Oct, 7 Nov, 22 Nov) and
  12 Nov (`6f9ecb8`: no flag).
- Tonight against the real report (`reports/fpl_2026-11-27.txt`, written by master's
  code), rebuilt from the clone: the differences are the status header (added by
  `checks.py`, which I did not run), the metric text, the legend, the two note lines,
  CHIPS's header note, the label, and the CAPTAIN and BAN RISK headers. No table row and
  no number differs. Master's CAPTAIN and BAN RISK read the 26 Nov archive; the branch's
  read tonight's export (Ruling 2).
- The recording path: the seven sources re-recorded on two copies of tonight's data,
  2,400 GW12 rows each (own 303, xg 280, minutes 280, bottomup 280, fpl_ep 674,
  bottomup_lambda 280, xp_v2 303). Old code against new code: 0 cells differ. Each
  against the real log: 90,969 rows in order, 0 cells differ outside `made_at`.

### (5) Imports, and nothing that moves a forecast. Confirmed.

- Each of the 27 runner modules imported in its own interpreter: 0 modules loaded from
  `tools/` or `analysis/`. For `fpl_sections` I also ran CHIPS, CAPTAIN and BAN RISK on a
  data copy, so the new import inside `live()` is exercised: still 0.
- `fpl_edge.py` (the recorder) loads no other local module; `fpl_xpv2` loads neither
  `fpl_chips` nor `fpl_squad`. The change is a label inside `live()`, which the record
  step never reaches.
- New in this commit: `tools/chips.py` imports the runner's `fpl_squad` inside `live()`.
  That is tool to runner, the allowed direction.

## Check 1 — point-in-time

- Nothing is forecast, recorded or graded by this change.
- Timestamp audit on tonight's data: the screen reads 14,248 log rows; 0 were made at or
  after their gameweek's deadline. The GW12 rows were made at 03:47 UTC, before the
  18:30 UTC deadline, and so was the export.
- Truncation: CHIPS's screen equals the screen rebuilt from the working export and the
  log cut at that export's deadlines, on 47 of 47 nights.
- No correlation metric, so no shift probe.

## Check 6 — mutants on `3847ebd`

42 new mutants: 39 red, 3 green. 11 rebuilt earlier mutants: 11 red.

| Group | Red | Green |
|---|---|---|
| answer 1 (9) | 7: the three float variants; `_exact` from the float; float sums in `xi_key`; values rounded to one decimal; XIs with five defenders skipped | 2: the key called then ignored; `Fraction(float(v))` |
| answer 2 (16) | 15 | 1: the frozen value by `three_layer_terms(pos)` |
| answer 4 (17) | 17 | |

All three green mutants pass the whole suite (890 OK each).

## Notes

- `_gen` gives "unknown" for a missing field, an empty value, `null`, a number or text
  that is not a time. A time within hours of year 1 or year 9999 with an offset raises
  `OverflowError` instead; the sections' catch-all would print a SKIPPED line. The sync
  writes the current time, so this cannot happen from our own exports.
- The naive-time mutant is red here because this machine is on Central European Time. On
  a machine on UTC (the runner) it would pass; the same was noted on 19 Nov.
- Two worktrees appeared during my run (`ckpt_code3` at `3847ebd`, `ckpt_data3` at
  `6f9ecb8`; their folders are dated 12:58 UTC). I did not open them. If decision 1
  changes the commit, a `run.txt` made at `3847ebd` is no longer from the item's final
  code and is regenerated (the provenance rule).
- Not on the branch yet, as the pin's order has it: `checkpoint.txt` and `run.txt`, the
  CHANGELOG entries, the report, the state file; then `dry/W3fix` at or after 19:30 UTC,
  the tag and the merge.

## Decisions for the chat

1. **The test for minor mutant 2.** It is red on the mutant with the terms left out and
   green on the same mutant with the terms spelled out, because the toy's player is a
   defender. Choose the toy player from midfielders and forwards (one word in the
   fixture; in my scratch copy the code stays green and both spellings go red), then a
   short re-check of that change, or accept the gap (no count or flag differs on tonight's
   data or on the 456 week-rows of 19 Nov)? The pin already describes the stronger test.
2. **The spy of answer 1** (no action needed unless you want it): two contrived variants
   pass it and change no XI in 9,000 random squads. A value check in the spy (`val` equals
   `_exact` of each forecast) would close the second. I would accept both as they are.

## Evidence files (scratch, not committed)

Under `...\scratchpad\verify_w3fix_27`:
- `out\old_plain.txt`, `new_plain.txt`, `new_data.txt`, `new_clone_hostile.txt`,
  `new_clone_hostile2.txt`, `oldcode_newtests.txt`, `full_m03.txt`, `full_m04.txt`,
  `full_m14.txt` (the nine suite runs);
- `scripts\mutate.py`, `out\mutants.txt`, `mut\m03`, `m04`, `m14` (the green mutants; the
  red ones' copies were removed and regenerate from the script);
  `scripts\mutate_old.py`, `out\mutants_old.txt`; `demo\` (the fixture with a midfielder
  or forward); `scripts\xi_search.py`, `out\xi_search.txt`;
- `scripts\replay.sh`, `dataA\`, `dataB\` (tonight's replay: `reports\fpl_REPLAY.txt`,
  `watch_REPLAY.txt`, `projection_log.csv`), `out\logcmp.txt`, `out\real_vs_B2.diff`;
- `dataR\`, `dataR2\`, `scripts\lives.py`, `out\data*_chips_*.txt` (the restored copies);
- `scripts\night.py`, `out\hist.jsonl`, `out\hist_all.jsonl` (the 52 data commits);
- `scripts\imports.py`, `out\imports.txt`; `scripts\audit.py`, `out\audit.txt`;
  `out\data_manifest_before.txt`, `data_manifest_after.txt`; `out\tool_chips\run.txt`.

VERDICT: WARN — every measured claim reproduces and no check fails: 884 OK before and
890 OK four ways on `3847ebd`, the spy test of answer 1 is red on both float variants,
the label prints the working export's own time in both files byte for byte (a restored
copy shows last night's time), the label is the only line of tonight's report that
changes, CHIPS's screen equals the base screen on all 47 replayed nights, the nightly
imports nothing under `tools/` or `analysis/`, and the seven recorded sources do not
move. It is not a PASS because answer 2 asks for a test for each of the four minor
mutants and the test for the second does not see its behaviour: with the three-layer
terms spelled out, the frozen-value mutant passes all 890 tests, since the toy's player
is a defender and the pin's "toy whose count depends on the scale" needs a midfielder or
forward. That is one word in a test fixture and needs Boris's answer (fix and re-check,
or accept); the landing steps are still to do.
