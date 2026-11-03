# verify_W2_a3 - W2 amendment 3, the multiplier check's chip lookup

**VERDICT: PASS**

Verifier: Claude Fable 5.1 (claude-fable-5-1), effort high, the native
`backtest-verifier` agent; the agent file was read from disk first
(`.claude/agents/backtest-verifier.md`, no difference from the loaded
instructions). Run on 2026-10-21. ODDS_API_KEY was unset in every command
(`env -u ODDS_API_KEY`); no key-like string was seen in any file checked.

Scratch folder (all my work; nothing in any repository was written except
this file):
`C:/Users/Boris/AppData/Local/Temp/claude/C--GIT-FPL/442a647f-7693-4ced-b840-0df7f5bfd943/scratchpad/verify_w2a3`
(`new/` = `git archive ba138c7`, `old/` = `git archive f6fb2fa`, `mut_*/` =
mutation copies of `new/`, `real_*/` = copies of the read-only data copy
`w2real`, data `7dbc319`). No commit, push, fetch or checkout anywhere; no
git command and no write in `C:/GIT/FPL-data`; `w2real` was only copied
(its `fpl.sqlite` SHA-256 prefix `3012f2dc20745312` before and after; no
working export was written into it).

Reason (one paragraph): the prereg amendment (master `5d4ad2b`, 18:13:48
+0200) precedes the one code commit (w2-wip `ba138c7`, 18:18:09 +0200), is
appended with 0 lines removed, and the diff is exactly what it pins: one
line in `tools/league.py` and one in `fpl_league.py`
(`check_multipliers(gw, picks)` -> `check_multipliers(stored, picks)`) plus
the test; every other definition is untouched and the two modules are still
AST-identical definition by definition. The fix is correct: the chain's chip
is `rows[ev]["chip"]`, i.e. the stored chip by construction, so no check
that passed before can change (proved on the real data: 42 chain-settled
pairs, 0 differing); a picks gameweek with no `entry_gw` row reads None
under both lookups (shown on the toy league, same message). On the real
data the old code fails LEAGUE at check 31's cause (`entry 4866471 GW7
player 411: multiplier 3 but the rule says 2 (chip None)`) and, with
4866471's GW7 picks removed, fails on our own entry `3073318 GW7` the same
way, so "Our own GW7 Triple Captain passes" was not so; the new code gives
CHIPS OK and LEAGUE OK with GW7 excluded from the chain for all 7 entries.
The new test is hermetic, runs both row orders and both modules, and goes
red on the old lookup, on last-row-wins and first-row-wins one-chip-per-
entry lookups, on a one-module-only regression, on an off-by-one gameweek
and on a silenced raise. Suite 751 -> 752 OK; the recording path is
unchanged (old and new code record identical rows; every source the item
did not touch is byte-identical).

## a. Protocol - PASS

- `git log`: prereg `5d4ad2b` (master, 2026-10-21 18:13:48 +0200) before
  code `ba138c7` (w2-wip, 2026-10-21 18:18:09 +0200). `ba138c7`'s parent is
  `f6fb2fa`; `5d4ad2b` is not its ancestor (the amendment is on master, as
  every earlier W2 prereg commit was: 08d6a95, 6efb6a4, fc56fd5, a78e2e7,
  87485f3 are all master commits merged into w2-wip later). `git show
  ba138c7:prereg/W2.md | grep "Amendment 3"` finds nothing: w2-wip's copy of
  the prereg will receive the amendment on the merge with master. Note only;
  the prereg was committed before the code.
- `git show 5d4ad2b -- prereg/W2.md`: 43 insertions, 0 deletions (`grep -c
  '^-[^-]'` = 0): appended, nothing removed. Boris's message is quoted
  verbatim in a blockquote; the finding and the fix are pinned below it.
- `git diff f6fb2fa..ba138c7 --stat`: `fpl_league.py` 2 +-, `tools/league.py`
  2 +-, `tests/test_W2.py` +50. The two module hunks are the single call
  line in `load` (plus a trailing comment). `totals_chain`,
  `expected_multiplier`, `check_multipliers`, `variance_table` and every
  other definition: no hunk.
- Verbatim copy: per-definition AST compare of `tools/league.py` vs
  `fpl_league.py` at `ba138c7`: defs only in tools `['main']`, only in runner
  `[]`, differing `[]`; constants only in tools `['ROOT']`, differing `[]`.
  The W2 copy test `ReportSections.test_byte_identical_to_the_tools` passes.
- W2 worktree status at the start: `## w2-wip...origin/w2-wip`, clean.

## b. Correctness - PASS

- Stored vs chain chip: `totals_chain` sets `gw[eid][ev]["chip"] =
  rows[ev]["chip"]`, `rows` being `stored[eid]`; the two are the same object
  value. Script `chip_identity.py` on the real copy: "chain-settled
  (entry,gw) pairs: 42 ; chip differs from stored: []". So on every gameweek
  the chain settles, the fix changes nothing; it only adds the gameweeks the
  chain cannot settle (the newest settled one, or any row without a
  successor), which the picks loop already covered and which read None
  before.
- The stored chips the new check uses on GW7 picks: `{881799: None,
  5826302: None, 18931: None, 4866471: '3xc', 3073318: '3xc', 2322726: None,
  8690100: None}`; `entry_gw.active_chip` equals the `chips` table exactly
  (set equality True, nothing only on either side).
- No `entry_gw` row for a picks gameweek: toy league with rival B's GW5
  `entry_gw` row deleted and its captain set to 3: new lookup -> `entry 222
  GW5 player 10: multiplier 3 but the rule says 2 (chip None)`; old lookup
  -> the same message. Unchanged behaviour (`stored` is a `defaultdict`, but
  `.get(eid, {})` does not create a key).
- Downstream: the chain's chip is used only in `variance_table`'s no-chip
  sigma, over chain-settled gameweeks, where it equals the stored chip;
  `league_eo` uses the picks' multiplier, not the chip. Nothing downstream
  reads a chip where the stored one is meant.
- Point-in-time: `picks` are filtered by `ev in settled` before the check;
  `stored` rows are read only by (entry, settled gameweek) of those picks.
  The item produces no forecast, feature or metric (check 1 not applicable
  beyond this; no later-dated input enters the check).

## c. The new test - PASS

- `tests/test_W2.py` `chips_in_a_row` + `ChipLookup`: `tempfile.mkdtemp()`
  only, S9's `toy_league` writes the sqlite and log inside it, `rmtree` in
  `finally`; grep for git config / TZ / locale / `FPL-data` / `C:\GIT` in
  `tests/test_W2.py` and `tests/test_S9.py`: nothing. Hermetic.
- Both row orders (`reverse` False/True, rows deleted and reinserted so
  rowid order follows insertion), both modules (`fpl_league` and
  `tools/league`), asserts: `load` succeeds with the GW5 3xc; `(b, 5)` in
  `excluded`; `5 not in gw[b]`; after setting the captain to 2,
  `MissingInput` with `entry 222 GW5` and `(chip 3xc)` in the message.
- `python -m unittest tests.test_W2 tests.test_S9` on `new/`: Ran 21 tests,
  OK (one pre-existing ResourceWarning from the fpl_lambda AST test at line
  239, not this item).
- Mutations (each applied to both modules unless stated; diffs checked with
  `diff --strip-trailing-cr`), `python -m unittest tests.test_W2.ChipLookup`:
  - `mut_old` (the old lookup, `check_multipliers(gw, picks)`): red,
    `entry 222 GW5 player 10: multiplier 3 but the rule says 2 (chip None)`.
  - `mut_last` (one chip per entry, last row wins): red, `entry 111 GW1
    player 17: multiplier 2 but the rule says 3 (chip 3xc)`.
  - `mut_first` (one chip per entry, first row wins): red, same message.
  - `mut_oneonly` (only `fpl_league.py` reverts to the old lookup; the tool
    keeps the fix): red, `entry 222 GW5 ... (chip None)` - a drift in one
    module is caught.
  - `mut_offby1` (my own: chip read from `ev - 1`): red, `entry 111 GW3
    player 17: multiplier 3 but the rule says 2 (chip None)`.
  - `mut_noraise` (my own: the raise replaced by `pass`): red,
    `AssertionError: MissingInput not raised`.
  Unmutated `new/`: Ran 1 test, OK.

## d. The real data - PASS

`run_sections.py`: `fpl_sections.sections(data, now=2026-10-21T15:00Z)` on
copies of `w2real` (data 7dbc319) after `fpl_nightly.py --restore` in the
copy (`RESTORED fpl_export_gw7_2026-10-21.json.gz -> fpl_export_gw7.json`).
- `ba138c7`: `CHIPS OK 37 lines`; `LEAGUE OK 58 lines` ("settled through
  GW6 ... coming deadline GW8 (GW7 played, not yet settled)"; "every stored
  row equals the chain; 7 rows the chain cannot correct, excluded", one per
  entry for GW7).
- `f6fb2fa`: `CHIPS OK 37 lines`; `LEAGUE SKIPPED: entry 4866471 GW7 player
  411: multiplier 3 but the rule says 2 (chip None)` - check 31's cause.
- Finding 4 (`run_ours.py`, old code): the picks iteration order by rowid is
  `[881799, 5826302, 18931, 4866471, 3073318, 2322726, 8690100]`, so 4866471
  is reached first; with 4866471's 15 GW7 picks deleted in a scratch copy
  the old code fails `entry 3073318 GW7 player 411: multiplier 3 but the
  rule says 2 (chip None)`. Our GW7 Triple Captain (player 411, slot 10,
  multiplier 3) did not pass the old lookup; it was not reached.
- New code: `settled [1..7]`, `excluded` = GW7 for all 7 entries, our GW7
  not in the chain, our GW7 captain pick `(411, 10, 3, 1)` checked against
  the stored chip `3xc`.
- Findings 1-3 and 5 confirmed: `entry_gw` holds 4866471's GW6 wildcard
  (rowid 251) and GW7 3xc (rowid 277) as separate rows, keyed per (entry,
  gameweek) in `stored`; the chain settles g only from the row of g+1; the
  identical line was in `tools/league.py` at `f6fb2fa` (line 158) and is
  fixed there too.

## e. The suite - PASS

`python -m unittest discover -p "test*.py" -s . -t .` on `git archive`
copies:
- `old/` (f6fb2fa) bare: Ran 751 tests, OK (skipped=10).
- `new/` (ba138c7) bare: Ran 752 tests, OK (skipped=10).
- `new/` with `FPL_DATA_DIR=C:\GIT\FPL-data` (read only): Ran 752 tests, OK
  (skipped=3).
These equal the implementer's counts.

## Check 5, recording path - PASS

`fpl_edge.py --record --source own` run in two separate copies of the data
(`real_rec_old` with f6fb2fa's code, `real_rec_new` with ba138c7's):
both `RECORD OK own 276` (GW8, 2 days before the deadline). Old vs new
`projection_log.csv`: identical ignoring `made_at`; the only `made_at`
differences are the 276 `own` GW8 rows just written (wall clock). Every
other source (`bottomup`, `fpl_ep`, `minutes`, `xg`) and every `own` row for
events other than 8: byte-identical including `made_at` across the original,
old and new logs. The item touches nothing on the recording path (diff: 3
files, none of them `fpl_edge.py`).

## Checks 3 and 4 - not applicable

The amendment pins no metric, sample filter, bootstrap setting or threshold:
it is a correctness fix to a data check. The acceptance tests it pins (both
row orders, newest settled gameweek without a later row, 3xc passes, wrong
multiplier stops, red on the old lookup and on one-chip-per-entry) are
verified in c. Boris's ruling text is present verbatim in `prereg/W2.md`.

## Check 7, secrets - PASS

`grep -i -E "apikey|api_key|authorization|bearer|[A-Za-z0-9]{32,}"` on
`fpl_league.py`, `tools/league.py`, `tests/test_W2.py` at ba138c7: no
match.

## Notes (no action required for the verdict)

- The LEAGUE header still says "settled through GW6" because the chain's
  `last` is the newest gameweek it can settle; that is S9's pre-existing
  rule, untouched by this item.
- w2-wip's `prereg/W2.md` does not yet carry amendment 3 (it is on master);
  the merge brings it in.
