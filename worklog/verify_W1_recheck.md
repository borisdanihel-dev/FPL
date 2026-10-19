# Verifier re-check: W1, the delta d928ebe..ab047c3 (RULING W1 pre-check decisions)

Re-check on the delta required by RULING W1 pre-check decisions, after the
pre-check that passed on w1-wip `d928ebe` (`worklog/verify_W1_pre.md`, read
for context, not changed). Written 2026-10-18, about 23:00 UTC (19 Oct 01:00
Prague), by the backtest-verifier agent. Model: Fable 5.1 (claude-fable-5-1);
effort: high, as `.claude/agents/backtest-verifier.md` says (read from disk
first; it matched the loaded instructions). Checks applied in their
data-pipeline form (the prereg has no pass/fail metric): 1, 2, 5, 6, 7 plus the
item's own acceptance tests; 3 and 4 are n/a as in the pre-check, except that
check 4's "ruling present verbatim" part is decided below.

Nothing was pushed, fetched into or changed in `C:\GIT\FPL`, `C:\GIT\FPL-data`
or `C:\GIT\FPL-b`; no tag, hook or config was touched; no workflow was
dispatched; the Odds API was not called; the real key was never read (the one
fake key was built at run time: `k360...`). GitHub was read with
`git ls-remote` only. All scratch work is under the session scratchpad: a
clone of `C:\GIT\FPL` with the data refs fetched *from that clone's origin on
disk*, worktrees at `d928ebe`, `ab047c3`, `9da6ff1` and `f7c5706`, and
copies for the mutations. Blobs were read with `git cat-file`.

## What was verified against

- GitHub (`git ls-remote`, 22:40 UTC): master `19690cc`, w1-wip `ab047c3`,
  data `9da6ff1`, data-dryrun `f7c5706`. `C:\GIT\FPL`'s local refs agree
  (`refs/heads/master 19690cc`, `refs/heads/w1-wip ab047c3`,
  `origin/data 9da6ff1`, `origin/data-dryrun f7c5706`). `C:\GIT\FPL-data` was
  found at `9da6ff1`, clean (the launch note said `e8629f0`; it was only read
  here).
- The delta, three commits on w1-wip (author = committer time, +02:00):

  | commit | time (UTC) | files |
  |---|---|---|
  | `021656c` merge of master `19690cc` | 21:39:40 | vs `d928ebe`: `prereg/W1.md` (+25), `worklog/SESSION_STATE_A.md` only; `git diff 19690cc 021656c -- prereg worklog CHANGELOG.md BUILD_PLAN.md` is empty, so the docs are exactly master's; vs master it carries w1-wip's W1 code unchanged |
  | `23c1e1e` ruling | 21:39:45 | `prereg/W1.md` +11 lines, nothing else |
  | `ab047c3` code | 21:54:04 | `checks.py` (+15/-7), `fpl_odds.py` (+9/-3), `tests/test_W1.py` (+66/-8), nothing else |

  `git diff d928ebe ab047c3 -- fpl_edge.py fpl_sync.py fpl_nightly.py
  fpl_gate.py fpl_publish.py fpl_alert.py .github` is empty: the delta touches
  no file of the sync, record, report, gate or publish path.

## Prereg and commit order: PASS

`prereg/W1.md` at `23c1e1e` (unchanged at `ab047c3`) ends with the section
"Pre-check decisions" holding, verbatim, the ruling quoted in the task
(points 1-3, the "These change code after the pre-check ..." paragraph, `END
RULING`). `23c1e1e` (21:39:45Z) precedes `ab047c3` (21:54:04Z), the first and
only code commit of the delta. Master is `19690cc` locally and on GitHub:
nothing went to master. The claim that `23c1e1e` was *pushed* at about
21:41 UTC is not something `git ls-remote` can show; the commit order is what
the agent file asks for, and it holds.

## Check 1 - point-in-time: PASS

The delta adds no forecast; fpl_ep is re-verified on the new dry run.

- 1a Truncation (decides): the 668 `fpl_ep` rows of `f7c5706`'s
  `projection_log.csv` (event 8, `made_at` 2026-10-18T22:35:07+00:00) rebuilt
  from the dated export `exports/fpl_export_gw7_2026-10-18.json.gz` of the same
  commit (`generated` 2026-10-18T22:35:06+00:00) as `(id, web_name,
  round(float(ep_next), 3))` for every player with an `ep_next` (668 of 668):
  identical sets, max |difference| 0.0. PASS.
- 1b Timestamps (decides): export 22:35:06 <= record 22:35:07 <= GW8 deadline
  2026-10-23T17:30:00Z (`events.deadline_time` in `f7c5706`'s `fpl.sqlite`).
  No odds file was fetched (the dry run skipped the API). PASS.
- 1c Shift probe: n/a, no correlation metric.

Information: the dry run's export differs from the real nightly's
(`9da6ff1`, 21:58) not only in `ep_next` but in `all_players`,
`league_ownership` and `top_players_recent`, because the dry run re-synced the
FPL API 37 minutes later. Check 5 therefore compares the two codes on one
export.

## Check 2 - clean-checkout test runs: PASS

Scratch worktrees; `ODDS_API_KEY`, `GH_TOKEN`, `GITHUB_TOKEN` removed;
`FPL_DATA_DIR` = a scratch worktree of `f7c5706` after
`fpl_nightly.py --restore` (RESTORE OK, 5 exports). Python 3.14.7.

| run (`python -m unittest discover -p "test*.py" -s . -t .`) | `d928ebe` | `ab047c3` |
|---|---|---|
| bare | **495 OK**, skipped=2 | **499 OK**, skipped=2 |
| runner-like: `GITHUB_ACTIONS=true GITHUB_REF=refs/heads/w1-wip FPL_DRY_RUN=true` | - | **499 OK**, skipped=2 |
| stand-in zones: `PYTHONTZPATH` = scratch copies of Git's `mingw64/share/zoneinfo/Europe/{London,Prague}` | - | **499 OK**, 0 skipped |
| hermetic: `env -i` with PATH/SYSTEMROOT/TEMP/TMP, empty HOME, USERPROFILE, XDG_CONFIG_HOME, `GIT_CONFIG_NOSYSTEM=1`, empty `GIT_CONFIG_GLOBAL`, no identity | - | **499 OK**, skipped=2 |
| the dry run `f7c5706`, ubuntu, from its log | - | **499 OK**, skipped=11 |

495 -> 499 as claimed; every run exit 0, no FAIL or ERROR line. The four new
tests, copied as `ab047c3`'s `tests/test_W1.py` onto the `d928ebe` code, are
red: `FAILED (failures=14)` = 7 subtests of
`test_the_api_is_called_only_in_github_actions`, 1 of
`test_the_command_line_reads_github_actions_from_its_environment`, 1 of
`test_an_answer_without_credit_headers_is_kept_and_a_warn`, 5 subtests of
`test_missing_credit_headers_are_a_warn`. Red before, green after.

## Check 3 - pre-registered evaluation: n/a

No metric in the prereg. Reproduced instead: the five RECORD OK counts of the
dry run (own 285, xg 264, minutes 264, bottomup 264, fpl_ep 668) by running
`--record` myself on the same export (check 5), and the projection-log
figures (below).

## Check 4 - metric, filter, bootstrap, threshold: n/a; ruling present: PASS

All n/a in the prereg; nothing promoted or re-tuned. The ruling the task names
is in `prereg/W1.md` verbatim (above).

## Check 5 - recording path: PASS (byte-identical)

Same restored export (`f7c5706`'s `fpl_export_gw7.json`), two scratch copies
of the data folder, `fpl_edge.py --record --source <s> --status ...` for the
five sources, then `--watch watchlist.txt --out` and `--diff --out`, with the
`d928ebe` code and with the `ab047c3` code:

- status lines identical (`RECORD OK own 285 / xg 264 / minutes 264 /
  bottomup 264 / fpl_ep 668`);
- the two `projection_log.csv` (6424 rows each, 0 duplicate
  `(source, event, player_id, day)` keys) are byte-identical once `made_at`
  (the clock, 1745 rows of today) is masked; every other field equal in every
  row; my rows equal `f7c5706`'s row for row except `made_at`;
- the watch file (6,273 bytes) and the report (30,069 bytes) are byte-identical
  between the two codes.

Export: `fpl_sync.py` is byte-identical between `d928ebe` and `ab047c3`
(empty diff), so the export is unchanged by construction.

## Check 6 - mutation spot-check: PASS (8 of 8 red)

Each in a fresh scratch copy of `ab047c3`, `tests.test_W1` (or the named
class) run with no key:

| # | mutation | red test(s) |
|---|---|---|
| P1 | the `GITHUB_ACTIONS` guard removed | `test_the_api_is_called_only_in_github_actions` (7 subtests), `test_the_command_line_reads_github_actions_from_its_environment` |
| P1b | `!= "true"` -> `not env.get(...)` (any non-empty value counts) | `test_the_api_is_called_only_in_github_actions` (3 subtests: "false", "True", "1") |
| P2 | "credits unknown" returns OK | `test_an_answer_without_credit_headers_is_kept_and_a_warn`, `test_missing_credit_headers_are_a_warn` (5 subtests) |
| P2b | only `x-requests-remaining` checked | `test_missing_credit_headers_are_a_warn` (2 subtests) |
| P2c | a line with no credits part defaulted to numbers | `test_missing_credit_headers_are_a_warn` |
| M4 | `CREDITS_WARN` 60 -> 0 | `OddsCheck.test_credits_below_60_are_a_warn` |
| M7 | the dry-run guard removed | `test_a_dry_run_calls_the_api_only_with_odds_live` (3 subtests) |
| M14 | `SEVERITY[30]` WARN -> FAIL | `test_ok_skipped_failed_missing` |

## Check 7 - secrets: PASS

- The three files the delta changes, at `ab047c3`, searched for `apiKey=`/
  `api_key=` with a value, `Authorization`, `Bearer `, 32+ hex characters and
  an `ODDS_API_KEY=` literal: the only hits are `checks.py:709` (the GitHub
  token header from a variable, pre-existing, no value) and `tests/test_W1.py`
  building fake keys at run time (`fake_key()`, `secrets.token_hex`). The
  added lines of the delta hold no key-like string.
- The dry run's new or changed text files (run log, `status_dryrun.txt`,
  report, watch file): no key pattern, no `ODDS_API_KEY` value, no 32-hex
  string.
- `fpl_gate.py --secrets` on `f7c5706`'s content staged against `9da6ff1`,
  with a fake key in the environment: `SECRETS OK no staged file holds a key
  pattern or the key value`.

## The implementer's claims, tested

1. Order and master - hold (above).
2. Decision 1 - holds. `fpl_odds.main` returns `0` after one line, `"ODDS
   SKIPPED (not in GitHub Actions)"`, before `run_mode` and before any
   request, unless `env.get("GITHUB_ACTIONS") == "true"` exactly; the tests
   inject absent, `""`, `"false"`, `"True"`, `"1"` (no call, that line, no
   `odds/` folder) and `"true"` (one call, `ODDS OK`) for a real and an
   odds_live dry env, and `main()` without an argument under
   `mock.patch.dict(os.environ, ..., clear=True)` both ways; the three
   existing call-expecting tests now pass `GITHUB_ACTIONS="true"` and assert
   the call count. P1 and P1b red.
   Judged: the exact-string reading is right - GitHub documents
   `GITHUB_ACTIONS` as always set to `true` while Actions runs a workflow,
   and the ruling says `"true"`. Nothing on the runner loses its call:
   `fpl_nightly.run()` passes `dict(os.environ, PYTHONIOENCODING=...,
   PYTHONDONTWRITEBYTECODE=...)` minus only the `drop` list to every step,
   and the odds step drops nothing (only the test step drops the key and
   tokens); the workflow step sets no `GITHUB_ACTIONS` of its own. Tonight's
   dry run is direct evidence: its collector, a subprocess on the runner,
   printed `ODDS SKIPPED (dry run): odds_live not ticked`, the branch *after*
   the new guard, so the guard saw `true` there. No test runs the real
   collector as a process (the nightly tests stub `fpl_odds.py`), every
   `O.main` call in the tests injects an opener, and the suite on the runner
   has no key, so `GITHUB_ACTIONS=true` in the Actions test step cannot cause
   a call. Side effect, intended by the ruling: a local `python fpl_odds.py`
   can never call the API now, which closes the pre-check's first observation.
3. Decision 2 - holds. `c30` parses `credits used X, remaining Y, this
   request Z` from the last ODDS line; any of the three not a number
   (`\d+(\.\d+)?`), or the credits part missing, is `WARN, "credits unknown
   (no <names>): <line>"`; the below-60 WARN is kept, and an OK line with all
   three numbers is OK. Exercised directly with the pre-check's real line
   (OK), `remaining 59` (WARN below 60), all `None` (WARN naming all three),
   `remaining 492.0` (OK), an old-format line without a credits part (WARN
   unknown), and the two SKIPPED forms (WARN). The collector with an empty
   header set still writes the snapshot (`odds/odds_...json.gz` present) and
   its line goes through `c30` as `credits unknown`; with only
   `x-requests-remaining` present it is `credits unknown (no
   x-requests-used, x-requests-last)`. P2, P2b and P2c red.
   Judged: the ruling says "Missing credit headers: check 30 WARNs ('credits
   unknown'), like remaining below 60" - plural, with no narrowing to
   `remaining`. The any-of-three reading is the literal one and the WARN
   names which header is missing; it is stricter than remaining-only in one
   direction only (remaining present, used or last absent -> WARN instead of
   OK). It meets the ruling. Whether Boris prefers the narrower reading is
   the open decision the implementer lists; it is a chat decision, not a
   defect.
4. Decision 3 - holds: the delta's `fpl_odds.py` diff is the docstring and
   the guard in `main()`; `rows()`, `collect()` and the stored body are
   untouched, every bookmaker is still kept.
5. Tests - hold (check 2, mutations in check 6).
6. Recording path - holds, byte-identical (check 5).
7. Dry run 3, `f7c5706` ("dry run 2026-10-18 w1-wip ab047c3 [skip ci]",
   22:35:09Z; parent `9da6ff1`, the real nightly of 21:58:09Z) - every line
   holds:
   - the day's run log is the real nightly's 4233 lines plus the dry run's
     section (`started 2026-10-18 22:34:28 UTC`): `Ran 499 tests ... OK
     (skipped=11)`, `TESTS OK`, `+ players.ep_next`, `collecting odds ...` /
     `ODDS SKIPPED (dry run): odds_live not ticked - no Odds API call`, five
     `RECORD OK` (fpl_ep 668), `ARCHIVE OK`, `STATUS WARN ... checks 27/28`,
     `CHECKS WARN -> reports/status_dryrun.txt`;
   - `reports/status_dryrun.txt`: `STATUS WARN ... checks 27/28`; the only
     WARN is `30 WARN odds snapshot: ODDS SKIPPED (dry run) ...`; 22 and 27
     SKIP; `28 OK test gate: 499 tests green`; `29 OK record: ... fpl_ep
     668`; `18 OK projection-log growth: ... fpl_ep +668 ...`; `19 OK 0
     duplicate keys`; `20 OK 0 of 6424 rows at or after their deadline`;
     `23 OK 6 file(s) to commit`. `reports/status.txt` is byte-identical to
     `9da6ff1`'s. The commit holds no `odds/` path;
   - projection log 5756 -> 6424 rows; 0 keys lost, 668 new (all fpl_ep,
     event 8, one `made_at`); the 3624 GW<=7 rows identical as ordered
     lists; the 1093 GW8 keys of the four frozen sources are the same set,
     and exactly 1077 rows (285+264+264+264, the 18 Oct ones) differ in
     `made_at` only (21:58 -> 22:35), 0 in `predicted` - the same-UTC-day
     replacement, across a re-sync and a code change;
   - `fpl.sqlite` 1,896,448 bytes in both commits, integrity ok, 14 tables
     (no odds table) in both; `players.ep_next` absent at `9da6ff1`, present
     at `f7c5706` with 668 of 668 filled (313 zero, 1 negative, as the API
     gave them);
   - the gate re-run by me with the `ab047c3` code on `f7c5706`'s content
     staged in a worktree at `9da6ff1`: `GATE OK integrity ok, 14 tables,
     price_history 25882 rows, frozen forecasts unchanged; fpl.sql written`,
     and that `fpl.sql` (2,546,374 bytes) is byte-identical to `f7c5706`'s.

## Observations (information, no verdict weight)

- `c30` reads the *last* ODDS line of the run log it is given; on a day with
  a real nightly and a later dry run, the dry run's status shows the dry
  run's line (seen tonight), which is the right one for that status file.
  Pre-existing behaviour, not in the delta.
- The implementer's "any of three" reading is the stricter one; the only
  practical difference from "remaining only" is a WARN when the API answers
  with `remaining` but without `used` or `last`.

## Write guard

`git status` in `C:\GIT\FPL` shows the two entries that were there at launch
(`M worklog/SESSION_STATE_A.md`, `?? worklog/verify_W1_pre.md`) and this
file, untracked. `C:\GIT\FPL-data` (`9da6ff1`, clean) and `C:\GIT\FPL-b` were
only read. The scratch worktrees are a scratch clone's own, under the
session scratchpad.

VERDICT: PASS

Reason: the ruling is in `prereg/W1.md` verbatim and committed (23c1e1e,
21:39:45Z) before the delta's only code commit (ab047c3, 21:54:04Z), master is
untouched at 19690cc and the merge commit is docs-only against w1-wip; the
guard calls the API only when `GITHUB_ACTIONS` is exactly `"true"`, is tested
both ways with injected environments and through `os.environ`, and tonight's
dry run proves the runner's subprocess passes it; check 30 WARNs "credits
unknown" when any credit header is missing while keeping the snapshot and the
below-60 WARN, a literal reading of the ruling; the suite goes 495 -> 499
green bare, runner-like, with stand-in zones and hermetically, the four new
tests are red on the old code (14 failures), and all 8 mutations go red; the
delta touches no file of the sync, record, report or gate path and the five
sources, the watch file and the report regenerate byte-identically (clock
aside) between d928ebe and ab047c3 on one export; the only forecast, fpl_ep,
rebuilds exactly from the dated export and is recorded before the GW8
deadline; no changed file or dry-run output holds a key, and the dry run's
claims reproduce from its committed blobs, including GATE OK with an
identical `fpl.sql`.
