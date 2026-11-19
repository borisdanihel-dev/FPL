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
