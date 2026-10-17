# Verifier report: S0c

- **Verifier:** backtest-verifier (native). Launch prompt began with the required
  read-from-disk sentence. `.claude/agents/backtest-verifier.md` was read from
  disk first (the 76d939b version, which includes the independence paragraph)
  and governed this run.
- **Item commits:** `4dca2b5` (prereg), `76d939b` (change). Base `01d6d0f`.
  Both are local and unpushed (`master` is ahead of `origin/master` by 2).
- **Ruling checked:** the verbatim `RULING S0c:` … `END RULING` block in
  `prereg/S0c.md`. No session transcript or chat log was read.
- **Scratch:** every clone, test run, mutation and regeneration ran in
  `C:\Users\Boris\AppData\Local\Temp\verify_S0c\` (clones `base`, `head`,
  `head_lf`, `mut`, `rec_base`, `rec_head`). Helper script and blob extracts:
  the session scratchpad. Nothing in `C:\GIT\FPL` changed except this file.

## Prereg order (gate)

PASS.
- `4dca2b5` has parent `01d6d0f` and contains one file only, `prereg/S0c.md`
  (+32 lines). It is dated 2026-10-17 20:37:42 +0200.
- `76d939b` has parent `4dca2b5` and holds every code and doc change. It is
  dated 20:41:43 +0200.
- `git diff 4dca2b5 76d939b -- prereg/` is empty, so the prereg was not edited
  after it was committed.

## Check 1: point-in-time leak check

PASS (not applicable; evidence that nothing is produced).
- The item produces no forecast, feature or evaluation metric.
- `git diff --numstat 01d6d0f 76d939b` lists 7 files. The only `.py` file is
  `test_fpl.py`, with 36 additions and 0 deletions: two new tests in
  `NightlyWorkflow`/`VerifierAgent` plus the new `VerifierAgent` class.
- None of these changed: `fpl_edge.py`, `fpl_sync.py`, `fpl_nightly.py`,
  `fpl_hist.py`, `p1_eval.py`, `.github/`, the exports, the log or `fpl.sqlite`.
- 1a and 1b have no input to rebuild. 1c has no correlation metric to probe.

## Check 2: clean-checkout test run

PASS. Each commit was freshly cloned and checked out, then tested with
`python test_fpl.py` (Python 3.14.7).

| checkout | tests | result |
|---|---|---|
| `01d6d0f` (before) | 250 | OK (skipped=2) |
| `76d939b` (after) | 253 | OK (skipped=2) |

- The +3 tests are `NightlyWorkflow.test_requirements_quote_the_current_rule`,
  `VerifierAgent.test_the_plan_block_is_the_agent_file` and
  `VerifierAgent.test_the_agent_reads_rulings_from_the_prereg_only`.
- The 2 skips are the same before and after ("no real export in this folder").
- The default clone (`core.autocrlf=true`) checks the files out as CRLF.
- In a Linux-like LF checkout (`core.autocrlf=false`, `core.eol=lf`, clone
  `head_lf`), `VerifierAgent` and `NightlyWorkflow` also pass (7 tests OK). So
  the new tests will not turn the nightly's test step red, and through it block
  `--record`.

## Check 3: re-run the pre-registered evaluation

Not applicable. The prereg states primary metric, bootstrap and pass threshold
as n/a, so there is no evaluation to re-run.

## Check 4: prereg fidelity (as defined for rulings)

PASS.
- The ruling is present verbatim in `prereg/S0c.md`, between `RULING S0c:` and
  `END RULING`, and was committed before any change (see gate).
- There is no metric, sample filter, bootstrap or threshold to promote or
  re-tune, and none was added after the fact.
- The implementation adds nothing the ruling does not call for. The two extra
  tests and the pointer sentence in `requirements.txt` are supporting, not new
  rules.
- **Form note (not a failure):** `prereg/S0c.md` omits the template rows
  Hypothesis, Data and sample filter, Comparison and Secondary metrics.
  `S0b.md` had them written out as n/a.

## Check 5: recording path

PASS.
- Fresh clones at `01d6d0f` and `76d939b` regenerated all four nightly sources
  (`own`, `xg`, `minutes`, `bottomup`) with
  `fpl_edge.py exports/fpl_export_gw6_2026-10-16.json --record --source <s>`.
- `datetime.now` was frozen at 2026-10-17T09:00:00Z by a scratch wrapper
  (`frozen_record.py`), so that `made_at` is equal between the runs and the
  GW7 deadline guard (10:00Z) is open.
- Results: RECORD OK own 279, xg 257, minutes 257, bottomup 257 in both.
- Both `projection_log.csv` files are 3625 lines, sha256
  `e88a5e5eaa09a286db14abff9187f7b7e8f475af54424980318ea4551190ac9d`, and
  `cmp` finds them **byte-identical**.
- Cross-check against the committed log:
  - All 2574 non-GW7 rows are unchanged, including `made_at`.
  - The 1050 regenerated GW7 rows have the same keys as the nightly's committed
    GW7 rows (made_at 2026-10-16T22:02Z), with 0 predicted values differing by
    more than 1e-9.

## Check 6: mutation spot-check

PASS. All mutations were made in clone `mut` at `76d939b`. Each went red, and
each was restored and went green.

| # | mutation | result |
|---|---|---|
| M1 | one word in the agent file (`You verify;` → `You check;`) | `test_the_plan_block_is_the_agent_file` FAIL ("the verifier block in BUILD_PLAN.md and the agent file differ"); restored → OK. This is ruling point 3's red-then-green, reproduced independently. |
| M2 | one word in the BUILD_PLAN.md block (`verdict FAIL.` → `verdict PASS.`) | same test FAIL |
| M3 | trailing space on one agent-file line | same test FAIL |
| M4 | independence paragraph removed from both files (byte test still equal) | `test_the_agent_reads_rulings_from_the_prereg_only` FAIL |
| M5 | one word in the `requirements.txt` quote (`only;` → `mostly;`) | `test_requirements_quote_the_current_rule` FAIL |
| M6 | package line `requests==2.32.0` added to `requirements.txt` | `test_requirements_install_nothing` FAIL |

After everything was restored, the full suite gave 253 OK (skipped=2).

Known limit, by design: the byte test maps CRLF to LF before comparing. A
difference in line endings alone therefore passes. Under `* text=auto` git
stores both files as LF anyway. The stored blobs were compared directly (see
R3) and are identical.

## Check 7: secrets

PASS.
- The 7 files the item adds or changes were scanned at `76d939b` (`prereg/S0c.md`,
  the agent file, `BUILD_PLAN.md`, `CLAUDE.md`, `requirements.txt`,
  `test_fpl.py`, `worklog/SESSION_STATE.md`), along with every added line of
  the diff.
- Patterns: `apikey`, `api_key=`, `authorization`, `bearer`, `x-api-key`,
  `token=`, 32-hex and 40+ character tokens.
- Hits are only rule prose (the words "Secrets"/"secret", the env-var *name*
  `ODDS_API_KEY`, the check-7 wording) and long test method names.
- There is no key value, no URL with `apiKey=`, and no Authorization header
  value.
- `ODDS_API_KEY` is not set in this shell, so no value-match scan was possible.
  The pattern scan only is reported.

## Acceptance tests: the ruling's points

| # | point | verdict | evidence |
|---|---|---|---|
| R1 | Independence sentence in the BUILD_PLAN verifier block and the agent file, identically | PASS | The quoted sentence matches word for word in both (whitespace-normalised match). The two are byte-identical (see R3). |
| R2 | Rulings pasted verbatim into the prereg before code: CLAUDE.md work-item protocol and BUILD_PLAN Part B | PASS | The **Rulings** bullet is inside `## Work-item protocol` in CLAUDE.md. The **Rulings** paragraph is in Part B. |
| R3 | New test: block and agent file byte-identical; red with one word changed, then green | PASS | The block extracted from the `76d939b` blob of BUILD_PLAN.md and the agent-file blob are both 2811 bytes, sha256 `1742bb23…dbb3`, `cmp` identical, 0 CR. The test exists (`VerifierAgent.test_the_plan_block_is_the_agent_file`). Red/green shown in M1. |
| R4 | `requirements.txt` quotes the current rule; the no-package-lines test kept | PASS | The comment quotes `"Runner code is Python standard library only; optional local tools under tools/ have their own requirements"`. `test_requirements_install_nothing` is unchanged (0 deleted lines in `test_fpl.py`) and goes red under M6. |
| R5 | Step 2 item 10 data source | PASS | The ruling text is present verbatim. The old "if the export has them, otherwise …" wording is gone. Factual: `fpl_sync.py:321` does fetch `entry/{eid}/event/{gw}/picks/`. |
| R6 | Read-from-disk launch sentence in the CLAUDE.md work-item protocol and BUILD_PLAN Part B | PASS | The exact sentence appears in both, framed "Every verifier launch starts with:". This launch complied. |
| R7 | Part B step 1 text replaced | PASS | The new text is verbatim, including `C:\GIT\FPL`. "Start a fresh Claude Code session" no longer appears in Part B; it did at the base. The trailing " and paste:" became " Paste:", a necessary grammatical join. |
| R8 | `worklog/SESSION_STATE.md` with five fields; updated at the end of every item before the push | PASS | All five fields are present, plus the update rule; CLAUDE.md 9b lists it before the push. "Runner freeze window (9d): not active" is correct. The next deadline is GW8 2026-10-23T17:30Z (both `fpl.sqlite` `events.deadline_time` and kickoff − 90 min), so the freeze starts 2026-10-22T11:30Z. Now is 2026-10-17T18:47Z. The item does not touch the runner path anyway. |
| R9 | "Session operating mode" a–g word for word | PASS | The section `## Session operating mode` is in CLAUDE.md. Lines a–g extracted from the `76d939b` blob and from the prereg (indent stripped) are byte-identical (7 lines, `cmp`). |
| R10 | Tests before and after, native verifier, write guard, push | PASS so far | Tests 250 → 253, all OK. This native verifier run is done. The write guard, report, CHANGELOG, final SESSION_STATE update and push happen after this report (9b order) and are not verifiable here. |

## Observations for the chat (none affects the verdict)

1. **Ruling 9d cites "deadline_time in the newest export", but the export has
   no such field.**
   - In the newest export (`exports/fpl_export_gw6_2026-10-16.json`), the
     `events` rows carry only `event`, `finished` and `data_checked`.
   - `deadline_time` exists only in `fpl.sqlite` `events`. `fpl_edge.next_deadline`
     derives the deadline as first kickoff − 90 min.
   - Today both give the same GW8 deadline.
   - The text was correctly pasted verbatim, but the rule names a source that
     does not exist.
2. **"One step per session" may now read as a contradiction.** The rule is
   still in the CLAUDE.md work-item protocol and the BUILD_PLAN.md standing
   rules. It now sits beside Part B step 1 ("Use the current Claude Code
   session …") and Session operating mode (a). The ruling did not ask for
   that rule to change, so the implementer rightly left it.
3. **The SESSION_STATE "current item" line is still pending.** It reads
   "verifier, report and push pending" and must be updated before the push
   (R8 / 9b).
4. **The implementer's own red/green demonstration for R3 cannot be checked
   yet.** The item report `worklog/cc_<date>_S0c.md` has not been written.
   M1 above reproduces it independently.

VERDICT: PASS

S0c is a protocol and docs item. Its prereg holds the ruling verbatim, committed in `4dca2b5` before any change, and is untouched since. Each of the ten ruling points is in place, checked byte for byte where the ruling says "identically" or "word for word" (R1, R3, R9) and verbatim for the quoted texts (R4–R7); R10's post-verifier steps (write guard, report, CHANGELOG, push) are still to come. The clean-checkout suite goes from 250 to 253 tests, all passing, in CRLF and LF checkouts. The new byte-identity test goes red when one word changes in the agent file or the plan block and green when restored, and the other new tests go red under their own mutations. The item touches no recording-path code: forecasts regenerated with a frozen clock give byte-identical `projection_log.csv` files at base and item, and they reproduce the nightly's committed GW7 values exactly. No file the item adds or changes contains a secret. The remaining notes are a ruling that cites an export field that does not exist (9d), wording in "One step per session" that may now read as a contradiction, and steps still due after this report. They are decisions for the chat, not defects in the item.
