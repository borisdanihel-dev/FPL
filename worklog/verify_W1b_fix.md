# W1b - verifier report (the fix of the two slips, w1b-wip 596de21 on a81e2b1)

- **Verifier:** backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high.
  `.claude/agents/backtest-verifier.md` read from disk first; it matches the loaded
  instructions. Date: 2026-10-20 (UTC evening).
- **Item:** W1b, runner work. This run re-checks only the delta a81e2b1..596de21, the fix of
  D1 (comments still saying 6) and D2 (no manual-dispatch test through `due_main`; mutation
  M13 survived) from `worklog/verify_W1b.md` (PASS at a81e2b1). Descriptive/pipeline item:
  no metric, no forecast, no feature; checks 1 and 3 of the agent file are n/a, the recording
  path was proven untouched at 09fcff4 and the delta here touches no recording code.
- **Not done, by instruction:** nothing dispatched, nothing pushed, no API call, nothing
  committed. The data worktree was not touched. Scratch under `scratchpad/v1b_fix/` only;
  this file is the only write in the worktree (`git status --short` before: clean at
  596de21).

## Prereg and rulings

- `prereg/W1b.md`: first commit 7aa568f (2026-10-19 02:08:40 +0200) before the first code
  commit a9248d1 (02:35:16); F-A appended at 677f34e (19 Oct 17:26:34) before 09fcff4
  (20 Oct 18:45:16) and before this fix 596de21 (20 Oct 19:18:53). The blob is identical on
  the worktree, `C:\GIT\FPL\prereg\W1b.md`, HEAD and origin/master (f7ff900c...; the
  worktree's checkout differs from the master folder's only by CRLF line endings). RULING
  W1b, the morning ruling of 19 Oct and F-A are in it verbatim. PASS.
- 596de21 is on `origin/w1b-wip` (pushed), the worktree HEAD is 596de21.

## Check 1 - the diff a81e2b1..596de21

- `git diff --stat`: 3 files, +21 -3: `.github/workflows/nightly.yml` (2 lines),
  `fpl_nightly.py` (1 line), `tests/test_W1b.py` (+18).
- `nightly.yml`: both changed lines start with `#` (lines 9 and 14 of the header comment);
  the diff of the non-comment lines of the two versions is empty (rc=0). Line 9 now reads
  "At most 12 dry runs a day (F-A; 6 under point 9)", line 14 "when 12 dry runs, pushed and
  manual together, already ran that UTC day".
- `fpl_nightly.py`: the only changed line is inside the `due_main` docstring ("the cap of 6 a
  day (RULING W1b)" -> "the cap of 12 a day (RULING W1b; F-A)"); the non-comment diff shows
  that one docstring line and nothing else; no statement changes.
- `tests/test_W1b.py`: one new test, `DueGate.test_a_manual_dry_run_is_gated_too`: a
  `workflow_dispatch` on `refs/heads/master` with `FPL_DRY_RUN=true` through `N.due_main`
  with the fake Actions API (`_api`, `D._GET` patched; `_GET` is `None` in the module, so no
  network is reached) and a scratch git data checkout: below the cap -> `run=true` and
  `DRY RUN      1 of 12 today; the result goes to data-dryrun`; 12 counted -> `run=false`,
  `DRY RUN SKIPPED: 12 of 12 today`; 03:59 UTC -> `run=false` (the night window);
  2026-10-23 17:00 -> `run=false` (within 1 hour of GW8's 17:30 deadline); the same dispatch
  with `FPL_DRY_RUN=false` and 12 counted -> `run=true` and the fake API never called (a
  real run never reaches the gate). That is exactly D2's gap. PASS.

## Check 2 - the new test red under M13 and one more mutation, green on 596de21

Fresh `git archive` copies of 596de21 (`scratchpad/v1b_fix/{green,m13,mb,mc}`); one line
changed each (CR-insensitive diff shown); `python -m unittest tests.test_W1b`, keys unset.

| copy | mutation | tests.test_W1b (31) |
|---|---|---|
| green | none | OK |
| m13 | `fpl_nightly.py` `if due and fpl_publish.run_mode(env)[0] == "dry":` -> `if due and env.get("GITHUB_EVENT_NAME") == "push":` (gate on push events only, the survivor) | FAILED, 1: `DueGate.test_a_manual_dry_run_is_gated_too`, line 353: `'DUE          not the backup cron' != 'DRY RUN      1 of 12 today; the result goes to data-dryrun'` |
| mb | `fpl_dryrun.py` `if n >= CAP:` -> `if n >= CAP and env.get("GITHUB_EVENT_NAME") == "push":` (a manual dry run bypasses the cap) | FAILED, 2: the new test (line 356, `'run=true' != 'run=false'`) and `Cap.test_a_manual_dry_run_counts_and_is_capped_too` |
| mc | `fpl_dryrun.py` `why = quiet(now, deadlines, tip)` -> `... if env.get("GITHUB_EVENT_NAME") == "push" else None` (a manual dry run bypasses the quiet windows) | FAILED, 1: the new test only (line 358, `'run=true' != 'run=false'`) |

M13 is now red; the manual path is pinned for the cap and, by the new test alone, for the
quiet windows. PASS.

## Check 3 - clean-checkout suites (git archive, keys removed)

`git archive` into `scratchpad/v1b_fix/<commit>/`; `python -m unittest discover -p "test*.py"`
from inside; `ODDS_API_KEY`, `FPL_DATA_DIR`, `FPL_ODDS_LIVE` unset (`env -u`); Python 3.14,
Windows.

| checkout | result |
|---|---|
| a81e2b1 (before the fix), bare | Ran 738 tests in 338.8s, OK (skipped=10) |
| 596de21 (the fix), bare | Ran 739 tests in 338.3s, OK (skipped=10) |

The one added test is the new `DueGate` test (tests.test_W1b 30 -> 31). PASS.

## Check 4 - no current-rule text still says 6

Grep over the repo at 596de21 for "6 dry runs", "6 of 6", "6 a day", "6 per day", "at most
6", "cap of 6", "six", and every `\b6\b` in the W1b files; `prereg/`, `CHANGELOG.md`,
`historical/` and the verifier reports excepted.

- Current-rule texts: `CLAUDE.md` line 177 ("once 12 dry runs, pushed and manual together"),
  `BUILD_PLAN.md` Part E item 4 lines 134-139 ("The same gate applies to a manual dry run ...
  once 12 dry runs ... `12 of 12`"), `fpl_dryrun.py` line 42 (`CAP = 12`, "was 6" as
  history), `nightly.yml` lines 9 and 14 (12; "6 under point 9" as history), `fpl_nightly.py`
  line 351 (12), `tests/test_W1b.py` (the "6" at lines 261 and 289 are `self.runs(6)`, a
  below-cap count; the Cap docstring says "12 a UTC day"). None says the cap is 6. PASS.
- Not current-rule text, listed for completeness: `worklog/cc_2026-10-19_W1b.md` line 45
  ("at 6 dry runs that UTC day") and line 42 ("03:17 UTC at the latest") - the item's report
  as written on 19 Oct before the morning ruling's 04:00 and F-A's 12; it carries no
  amendment naming either (the landing report is the place). `worklog/SESSION_STATE_B.md`
  lines 207 and 339 - lane B's retired state file (lanes merged 19 Oct; line 339 quotes a
  ruling). `worklog/SESSION_STATE_A.md` line 905 "Dry runs used: 18 Oct: 6 of 6" - a usage
  count from the day the cap was 6. `CHANGELOG.md` has no W1b landing entry yet on w1b-wip
  (line 3962, a frozen entry, says the cap moves to 12 when W1b is worked).

## Check 5 - secrets

- `ODDS_API_KEY` unset in this shell. Over `git diff a81e2b1 596de21`: no `apiKey=`, no
  `Authorization` value, no key-like run of 32+ characters; the only token-ish text is the
  test's literal `GH_TOKEN` `t-no...` (a fake, and the fake API never sends it). Over the
  three touched files: the one hit is the `nightly.yml` comment that names the string
  `"apiKey="` the scan looks for (no value). PASS.

## VERDICT: PASS

The fix commit 596de21 changes exactly what the two slips asked: the two `nightly.yml` header
comments and the `due_main` docstring now say 12 (the non-comment diff of both files is
empty apart from that docstring line, so no behaviour moved), and one new test drives a
manual dispatch dry run through `due_main` with the fake Actions API and no network, pinning
the cap, the night window, the deadline hour and that a real run never reaches the gate;
that test is green on 596de21 and red under the surviving M13 and under two further
manual-path mutations of mine (cap bypass, quiet-window bypass, the latter caught by the new
test alone); the clean bare suites are 738 OK before and 739 OK after; no text describing the
current rule still says 6 (the only "6" left are historical references, the item's 19 Oct
report and the retired lane B state file); the prereg with F-A verbatim predates every code
commit and is byte-identical to master's; no secret is in the diff.
