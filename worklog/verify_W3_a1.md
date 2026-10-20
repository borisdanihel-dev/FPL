# Verifier report: W3 amendment 1 (fixtures.finished_provisional, ban risk on provisional results, GW8 graded from the bundle; runner work, unmerged)

Verifier: the `backtest-verifier` agent, model Fable 5.1, effort high. The
agent file on disk, `.claude/agents/backtest-verifier.md`, was read first;
it matches the loaded instructions. Scope: branch `w3-wip` at `aea1f42`
(the amendment), base `d3ea9c6` (the merge of `origin/master` into
`w3-wip`). Prereg: `prereg/W3.md` on master at `0596125`, section
"Amendment 1". Everything below was measured on clean `git archive` copies
of `d3ea9c6` and `aea1f42` and on file copies of `C:\GIT\FPL-data` at
`63e6a44`, all under the session scratchpad (`scratchpad/v3_a1/`);
`C:\GIT\FPL-data` and the `w3` worktree were read only (`git status`
clean in both at the end; `C:\GIT\FPL-data` still at `63e6a44`). No session
transcript or chat log was read. No API was called; no dispatch, no push.
The only file written outside the scratchpad is this one.

## Prereg ordering and the rulings (check 4)

- `prereg/W3.md` amendment: committed on master in `0596125` at
  2026-10-20 16:02:56 +0200. The amendment's only code commit is `aea1f42`
  at 16:15:17 +0200. Prereg before code: **PASS**.
- Note for the record: `0596125` is not an ancestor of `aea1f42`. The merge
  `d3ea9c6` (16:01:31) was made one minute before the prereg commit, so
  `w3-wip`'s own copy of `prereg/W3.md` lacks the amendment section (`git
  diff aea1f42 master -- prereg/W3.md` = +155 lines on master). The prereg
  is where the protocol puts it (on master only; the night ruling: "on
  master only preregs and SESSION_STATE_A.md") and it arrives on the
  branch at the merge; `git diff 0596125 master -- prereg/W3.md` is empty,
  so it was not edited after.
- The three rulings the task names are present verbatim-as-text at the end
  of the section: "Ruling, Mon 19 Oct" (points 1-6 plus the overnight
  order), "Ruling, Tue 20 Oct" (points 1-5 plus the order) and "Ruling,
  Tue 20 Oct evening". I cannot compare them with the chat (I never read
  it); I checked that each design point cites one of them and does not go
  beyond it (see "The three decisions" below).
- No metric, no threshold, no bootstrap in this amendment: a
  data-pipeline / report item. Checks 1, 2, 5, 6, 7 and the item's own
  acceptance tests apply; check 3 is the real-data re-run below.

## The merge commit d3ea9c6 (requested)

- `git diff d3ea9c6^1 d3ea9c6 -- fpl_sync.py`: adds master's S2b side
  (`events.data_checked_seen_utc`, `picks.fetched_at_utc`, `is_final`,
  the ON CONFLICT events upsert). `git diff d3ea9c6^2 d3ea9c6 --
  fpl_sync.py`: adds w3-wip's W2 side (`players.code`, `PLAYER_COLS`,
  `standings.label_error` + `flag_standings_labels`, the W2 fetched_at_utc
  columns). The merged `MIGRATIONS` dict holds both sides' entries, each
  once; no conflict markers in `fpl_sync.py` or `CHANGELOG.md` at
  `d3ea9c6` or `aea1f42`.
- `CHANGELOG.md`: every line of each parent is present in the merged file
  (set containment both ways: 0 lines of parent 1 missing, 0 of parent 2).
- The clean-checkout suite of `d3ea9c6` is green (below), which is the
  functional proof of the resolution.

## Check 1: point-in-time (PASS where it applies)

- 1a truncation: not applicable; the amendment builds no feature from
  dated exports or historical rows.
- 1b timestamp audit (the GW8 grade): the only input the grade takes from
  the future-facing world is the bundle file, and it is read at the newest
  commit whose **committer time is strictly before** `events.deadline_time`
  (GW8: `2026-10-23T17:30:00Z` in the real database), with `git log
  --format=%H %cI -- <path>` and `git show <commit>:<path>`, never the
  working tree. Evidence: the item's tests `test_only_after_the_deadline_is_
  not_recorded` (a commit at exactly 17:30:00Z is not graded) and
  `test_graded_from_the_commit_before_the_deadline` (a post-deadline edit is
  ignored); my mutations m1 (`<` to `<=`) and m10 (read the working tree
  instead of `git show`) both go red; my probes: a committer time given as
  `19:00:00+02:00` (17:00Z) is graded, `19:40:00+02:00` (17:40Z) is not.
  **PASS.**
- 1c shift probe: not applicable (no correlation metric).

## Check 2: clean-checkout suites (PASS)

`python -m unittest discover -p "test*.py"` on the archives, `ODDS_API_KEY`
and `FPL_DATA_DIR` unset unless stated:

| tree | run | result |
|---|---|---|
| before `d3ea9c6` | bare | Ran 737 tests in 297.8s, OK (skipped=11) |
| after `aea1f42` | bare | Ran 748 tests in 287.8s, OK (skipped=11) |
| after `aea1f42` | `FPL_DATA_DIR=C:\GIT\FPL-data` | Ran 748 tests in 263.0s, OK (skipped=4) |

The amendment adds 11 tests and removes none (`+    def test_` count in
the diff: 11 / 0): 737 + 11 = 748. Also by name on the after tree:
`tests.test_S3.Hermetic.test_the_git_using_tests_pass_with_an_empty_home`
ok and `tests.test_S3.FastTrack.test_the_nightly_imports_nothing_under_
tools_or_analysis` ok (2 tests, 60.9s). `Hermetic._git_classes()` lists
`tests.test_W3.Realised`, `tests.test_W3.BundleGrading` and
`tests.test_W3.Sections` (the three W3 classes that touch git), so they
were rerun with an empty HOME, an empty global config and no identity in
the environment. The test helpers give identity, dates and
`core.autocrlf=false` per command (`-c` flags, `GIT_AUTHOR_DATE` /
`GIT_COMMITTER_DATE`).

## Check 3: the real-data re-run (PASS)

On a file copy of `C:\GIT\FPL-data` at `63e6a44`, migrated in place with
the after tree's `fpl_sync.migrate` (my own copy, not the main session's):

- `migrate` printed `+ fixtures.finished_provisional` (and the W2 columns
  and S2b's, as the merged `MIGRATIONS` says); `PRAGMA table_info(fixtures)`
  = 13 columns, the last `finished_provisional`; all 380 rows: the migrated
  row equals the old row + `(None,)`; `finished_provisional` is NULL on all
  380. A fresh database from `SCHEMA` has the same column order as the
  migrated one.
- The dump (`fpl_gate.write_dump`): 380 `INSERT INTO "fixtures"` rows
  before and after; every new row is the old row with `,NULL` appended
  before `);` - the first 12 values keep their positions.
- `fpl_sections.sections(copy, now=2026-10-20T15:00Z)`:
  `CAPTAIN SKIPPED: the export's all_players has no code (the prior's key)`
  (master's export carries no `code` yet, as the task says);
  `BAN RISK OK 2 lines` with
  `Thiago            BRE FWD  cautions 4, club match 8 next  rate90 0.444  P(start) 1.00  P(ban) 0.444`
  and the rule line ending `; a result FPL has ended but not yet marked
  finished counts, labelled provisional`; `REALISED OK 2 lines`, `no
  gameweek from GW8 has passed its deadline yet`. These equal the main
  session's `w3_real_report_sections.txt` line for line.
- With no provisional fixture, `fpl_squad.ban_rows` returns `prov == {}` and
  a `Rows` equal to `fpl_mv2.rows_2627` in all six fields on the real data.
- Injection on the copy (Thiago's GW7 fixture, id 62, BRE-LIV):
  `finished=0, finished_provisional=1`: 1 hit, the line ends
  `   provisional: BRE-LIV not yet marked finished by FPL`;
  `finished=0, finished_provisional=0` (in progress): 0 hits, `none of our
  15 is one booking from a ban`; `finished=0, NULL`: 0 hits;
  `finished=1, finished_provisional=1`: 1 hit, no label.

## Check 5: the recording path (PASS)

The suite has no before/after byte comparison of the log, so I did it on
copies: for each tree, a fresh copy of data `63e6a44`, the working export
restored by `fpl_nightly.restore_exports`, then `fpl_edge.record_status`
for every source in `fpl_nightly.SOURCES` (own, xg, minutes, bottomup,
fpl_ep, bottomup_lambda, xp_v2) with `datetime.now` frozen at
2026-10-20T21:40:00Z (before the GW8 deadline). Both trees: own 277, xg
257, minutes 257, bottomup 257, fpl_ep 668, bottomup_lambda 257 (snapshot
`odds_2026-10-20T1301Z.json.gz`, 257 of 257), xp_v2 skip (no `code`).
`cmp rec_before/projection_log.csv rec_after/projection_log.csv`:
**IDENTICAL** (9461 rows each; the original had 9204, so rows were written
- 257 new bottomup_lambda rows, the rest same-day replacements). The
amendment touches no recording code (`fpl_sync.sync_fixtures`,
`fpl_squad`, the workflow, tests); this is the proof it moved nothing.

## Check 6: mutations (PASS, 10 of 10 red)

Each in its own copy of the after tree, `python -m unittest tests.test_W3`
(28 tests):

| | mutation | red test |
|---|---|---|
| m1 | deadline `<` to `<=` | BundleGrading.test_only_after_the_deadline_is_not_recorded |
| m2 | `done = bool(fin)` (provisional ignored) | BanRiskProvisional.test_provisional_counted_and_labelled_in_progress_not |
| m3 | `done = bool(fin) or pv is not None` (in progress counted) | the same test |
| m4 | the 15-equals-ours check disabled | BundleGrading.test_a_different_15_is_not_graded |
| m5 | `finished_provisional INTEGER` removed from MIGRATIONS | FinishedProvisional.test_the_migration_appends_it_last |
| m6 | label text changed | BanRiskProvisional (the label assertion) |
| m7 | captain not doubled in `realised_order` | BundleGrading.test_realised_order_is_realised_on |
| m8 | `fetch-depth: 0` removed from the workflow | BundleGrading.test_the_nightly_checks_out_the_history |
| m9 | sync writes 0 for an absent field (instead of NULL) | FinishedProvisional.test_the_sync_writes_it |
| m10 | bundle read from the working tree instead of `git show` | BundleGrading.test_graded_from_the_commit_before_the_deadline |

## Check 7: secrets (PASS)

The four files the amendment changes (`fpl_sync.py`, `fpl_squad.py`,
`.github/workflows/nightly.yml`, `tests/test_W3.py`): no `apiKey=`, no
`Authorization` value, no key value. Hits of the pattern scan are the
pinned action SHAs, the test's 40-character tool commit hash and the
workflow's pre-existing `${{ secrets.ODDS_API_KEY }}` references (the
name, not a value). The scratch archives hold no key file; my shell had
`ODDS_API_KEY` unset.

## Runner isolation (PASS)

`fpl_squad.py` imports `os, re, sqlite3, subprocess, collections, datetime`
and the runner modules only; `tests.test_S3.FastTrack.test_the_nightly_
imports_nothing_under_tools_or_analysis` ok.

## Design vs code, line by line

(A) `finished_provisional`: `CREATE TABLE fixtures` ends with
`finished_provisional INTEGER`; `MIGRATIONS["fixtures"]` appends it after
`fetched_at_utc`; `sync_fixtures` names its 13 columns and writes
`None if f.get("finished_provisional") is None else int(f["finished_provisional"] is True)`
(1 / 0 / NULL; the same `is True` idiom as `started`). As designed.

(B) `ban_rows`: `done = bool(fin) or pv == 1`; `prov[club]` only when
`pv == 1 and not fin`; NULL falls through both; the `known` set and
`played` rows use `done` exactly where `_rows_2627` uses `fin`; the
column is read through `PRAGMA table_info` so a database without it still
works (`NULL` selected). `provisional_note` joins the club's
provisional-only fixtures before the cut with ", " and appends
`   provisional: <HOME>-<AWAY> not yet marked finished by FPL`. S12's
band, `CRED_K`, `p_ban_next` and `fpl_mv2.py` are untouched. As designed.

(C) `bundle_commit` / `parse_bundle` / `bundle_xp_v2` / `realised_order`:
as designed (section "Check 1" for the time rule). `parse_bundle` finds
the "OWN v XP_V2 AS TESTED" title, takes slots 1-15 from the right-hand
column, needs exactly `[1..15]` and a `captain:` line, else `None`.
`bundle_xp_v2` maps names by `players.web_name` and position, refuses
unless the 15 ids equal our GW8 `picks` (both difference lists printed),
needs the captain to be one of its XI, then scores the printed XI / bench
order / captain through `realised_order`, whose arithmetic equals
`fpl_realised.realised_on` (the item's 50-draw test; m7 red). The label
is `source: GW8 bundle <7> (tools <7>)`. In `realised`, the branch runs
only for `g in BUNDLE_GWS == (8,)` and only when the log holds no xp_v2
rows for GW8; the total line still needs both sources. The workflow's
master checkout has `fetch-depth: 0`; the data checkout is unchanged.

## The questions the task asked

Shallow checkout or missing git: silent "not recorded", never a crash.
Probes on the after tree: a `--depth 1` clone whose bundle commit is older
than the tip gives `bundle_commit == None` (the full clone finds it); a
non-repository folder, `subprocess.run` raising `FileNotFoundError`, and
a `TimeoutExpired` all give `None`; `realised()` end to end on the toy with
a shallow or a non-existent repo prints `xp_v2: not recorded before the
deadline`. And `fpl_sections.sections` wraps every section in
`try/except Exception` to a `SKIPPED` line (W2 amendment 2), so even an
unforeseen exception cannot red the night.

The parser against the tool's real print: `tools/gw_pass.py` at `aea1f42`
prints section 5 with the same three f-strings as at `71c9d17` (the title,
the row and the captain line are byte-identical between the two commits;
the file differs elsewhere by 8/18 lines), so the item's
`test_the_parser_reads_the_tools_own_print`, which runs the tool's own
`bundle()` and compares with `side_by_side`, covers the real print. My
own probe with the same f-string: `De Cuyper`, `Van de Ven-Longname` (19
characters, pushes the columns), `Muharemović`, `E.Le Fée`, `O'Riley`,
`J.Timber GK`, a negative own value `-0.12`, a two-digit `12.35`, and CRLF
text all parse to the right 15 and captain; a text without the captain
line gives `None`. The bundle file is written with `encoding="utf-8"` and
read as UTF-8 from `git show`.

Hermetic tests: yes (check 2).

## The three decisions, against the rulings

(a) "appended at the end of the CSV" (Ruling, Tue 20 Oct, point 5). There
is no fixtures CSV: `git ls-files '*.csv'` on `w3-wip`, `master` and
`data` lists only `overrides.csv`, two `tools/odds/E0_*` odds files and
`projection_log.csv`. The positional readers are the `fpl.sql` INSERT
rows, and those keep their first 12 values (verified on all 380). No
runner module reads `fixtures` by position: every `SELECT` on `fixtures`
in `checks.py`, `fpl_bt.py`, `fpl_chips.py`, `fpl_mv2.py`, `fpl_squad.py`,
`fpl_sync.py` names its columns; no `SELECT *` on it outside tests. The
column is last in both the migrated and the fresh schema. Within the
ruling; the prereg itself flags the reading of "CSV" as a decision for the
chat.

(b) Within the night ruling, point 3, word for word: counted when
`finished_provisional = true`; labelled "provisional" until FPL marks it
finished (the label disappears once `finished = 1`); still in progress
(neither flag) not counted. NULL = not provisional is the only reading
that substitutes nothing.

(c) Within the night ruling, point 2, with two additions the prereg pins:
the committer time as "timestamped" (stricter than the author date, which
survives a rebase), and "graded only when the bundle's 15 is our GW8 15".
The second condition is not in the ruling; it is the "nothing is
substituted" rule applied (a bundle for a different 15 cannot be scored on
ours without inventing a lineup), and the prereg names the case where it
bites (a transfer after Thursday's bundle; Friday's refresh carries the
GW8 15). The label gains "(tools <run.txt commit>)", information only.

## Observations (none changes the verdict)

1. Landing hazard for the real grade: if the commit that adds
   `worklog/gw_pass/gw8/gw8_pass.txt` reaches master by a **merge commit**,
   `git log -- path` still lists the original commit with its pre-deadline
   committer time (my probe: graded). If it is **squashed or rebased**
   after the deadline, the committer time moves and GW8 reads "xp_v2: not
   recorded before the deadline" (my probe: `None`). s8c-wip lands on Sun
   25 Oct: land it with a merge commit, and commit the Thursday bundle
   output before Fri 23 Oct 17:30 UTC on a branch that master will merge,
   not rebase.
2. Names map through `players.web_name` as stored on the grading night,
   not as printed on Thursday. An FPL web_name change in between gives
   "not graded" with the two lists (nothing substituted), not a wrong
   grade.
3. Wording: when `run.txt` exists but its `commit:` line is not a hash
   (provenance writes `unknown (git unavailable)` when git cannot answer),
   the label says "tools no run.txt at that commit". Cosmetic.
4. A non-UTF-8 byte in the bundle file would raise in `git()`'s
   `.decode("utf-8")` (outside its `except`) and surface as `REALISED
   SKIPPED: UnicodeDecodeError: ...` for the whole section, not a red
   night. The tool writes UTF-8, so this is theoretical.
5. The captain lookup (`web.get(id) == cap_name` over the XI) ignores
   position; two XI players with the same web_name would give "its
   captain X is not one of its XI: not graded". Not the case for our 15.
6. The amendment's `CHANGELOG` entry and `worklog/cc_<date>_W3_a1.md` are
   not yet on `w3-wip` (they follow the verifier, per the prereg).

VERDICT: PASS. The prereg amendment (master `0596125`, 16:02:56) predates the only code commit (`aea1f42`, 16:15:17) and is unedited since; the three rulings are present and each design point stays within them, with the one addition (the 15-must-match guard) being the no-substitution rule and flagged for the chat; the merge `d3ea9c6` keeps both sides of `fpl_sync.py` and `CHANGELOG.md`; clean-checkout suites 737 OK before and 748 OK after (bare and with `FPL_DATA_DIR`), the Hermetic rerun covering the three git-using W3 classes; the real-data copy migrates with the column last, old rows NULL, every dump row keeping its first 12 values, and the sections reproduce the main session's lines exactly; the regenerated projection log is byte-identical between `d3ea9c6` and `aea1f42` under a frozen clock; all ten mutations go red; no secrets; a shallow checkout or a missing git yields "not recorded", never a red night; the parser reads the tool's print with spaces, diacritics and long names.
