# Verifier report: W3 amendment 2 (GW8 graded from the bundle's xp_v2_all.csv)

Verifier: backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high. Agent file read from
disk first (`.claude/agents/backtest-verifier.md`); it matches the loaded instructions.
Date: 2026-10-20. Nothing dispatched, no API called, nothing pushed, no source file edited.
Scratch: `scratchpad/v3_a2/` (archives, data copies, probe scripts, logs). Written: this file only.

Item: commit `bbe770a` on `w3-wip` (on top of `191b0b0`), files `fpl_squad.py` and
`tests/test_W3.py` (109 insertions, 183 deletions; no other file). Runner work on a branch, not merged.

## Prereg and ruling

- `prereg/W3.md` section "## Amendment 2: GW8 graded from the bundle's CSV" is on master at
  `6e7c918`, committer time 2026-10-20T18:30:34+02:00. The item's code commit `bbe770a` is at
  2026-10-20T18:41:24+02:00: prereg before code. PASS.
- The ruling text is in the prereg verbatim: "Ruling, Tue 20 Oct night", point 3 second bullet
  ("w3-wip: REALISED takes the actual GW8 15 from the post-deadline picks, own from the projection
  log, and xp_v2 from that CSV; each model picks its XI and captain from those 15. The condition
  "the bundle's 15 equals the GW8 squad" is replaced by "all 15 are in the CSV"; otherwise "not
  recorded".") and point 4 ("Committer time: OK, and the bundle's run.txt end time must also be
  before the deadline. Both are required."). PASS (check 4: no metric, no threshold; nothing promoted).

## (1) Design vs code, line by line (`git diff 191b0b0 bbe770a`)

| Prereg / ruling | Code | Finding |
|---|---|---|
| File `worklog/gw_pass/gw8/xp_v2_all.csv`, read from git history, never the working tree | `bundle_csv`: `git log --format=%H %cI -- worklog/gw_pass/gw8/xp_v2_all.csv`, then `git show <h>:...csv` and `git show <h>:...run.txt` | PASS; bytes come from `git show`, the working tree is never opened |
| Walk commits newest first; first one used where both hold | loop over `git log` output (newest first); `continue` on every failed condition; `return` on the first that holds | PASS |
| Committer time strictly before `events.deadline_time` | `if _utc(t) >= deadline: continue` with `%cI` parsed by `fromisoformat` (offset-aware) | PASS; probe: 19:30+02:00 (= deadline instant) rejected, one second before accepted |
| run.txt at the same commit gives `end_utc` strictly before the deadline | `re.search(r"^end_utc: (\S+)$", run, re.M)`; `_utc(end) < deadline` | PASS; probe: end == deadline rejected |
| run.txt lists `xp_v2_all.csv` with the SHA-256 of the file at that commit | `^  xp_v2_all\.csv  sha256 ([0-9a-f]{64})$` compared with `hashlib.sha256(raw)` of the blob | PASS; format equals `tools/provenance.py`'s `f"  {basename}  sha256 {sha}"`; a `(missing)` entry is skipped |
| With none: "xp_v2: not recorded before the deadline" | `bundle_csv` returns None, falls to the existing `not recorded` line | PASS |
| The 15: our actual GW8 15 from the post-deadline picks | the unchanged `picks` query (`entry_id`, `event`, `ORDER BY position`), `len == 15` guard | PASS; test `test_our_actual_15_after_a_transfer` and my probe |
| own from the projection log, as before | `recorded(log_rows, "own", ...)` untouched | PASS |
| xp_v2 from the CSV's `xp_v2` column for those 15 | `{int(r["id"]): float(r["xp_v2"])}`; `{pid: values[pid] for pid in squad ids}` | PASS; exact equality with a direct `csv.DictReader` read of the real CSV (668 players) |
| Any of the 15 missing -> "xp_v2: not recorded before the deadline" | `absent = [... if pid not in values]`; message `"xp_v2: not recorded before the deadline (GW8 bundle <7> (tools <7>): N of our 15 not in xp_v2_all.csv)"` | PASS, see judgement below |
| Scoring: `realised_on` for both | `RL.realised_on(squad, values_for_15, actual)` for xp_v2; `RL.realised_on(squad, proj, actual)` for own (unchanged) | PASS |
| Label `source: GW8 bundle <commit, 7> (tools <run.txt commit, 7>)` | `f"GW{g} bundle {h[:7]} (tools {tool[:7]})"`; `commit: unknown (git unavailable)` gives `tools unknown` | PASS |
| Removed: section-5 parser and bundle-order scoring | `ROW`, `CAP`, `POS`, `parse_bundle`, `bundle_commit`, `realised_order`, `bundle_xp_v2` deleted | PASS |
| Kept: `fetch-depth: 0` | `.github/workflows/nightly.yml` unchanged, line 76 `fetch-depth: 0` | PASS (its comment still cites amendment 1 (C); cosmetic) |

Judgements asked for:
- The parenthetical on the not-recorded line. The ruling says: otherwise "not recorded"; the prereg
  says the line says "xp_v2: not recorded before the deadline". The code prints that sentence verbatim
  and appends, in parentheses, which bundle commit it read and how many of the 15 were absent. The
  rule is unchanged (nothing is graded); the line still says what the ruling requires; the full text
  was pinned in the prereg's test list ("one of the 15 missing from the CSV gives 'not recorded'") and
  is asserted by `test_one_of_the_15_missing_is_not_recorded`. Within the ruling.
- The SHA-256 requirement. Not in the ruling's words (points 3 and 4 name committer time and run.txt
  end time); it is in the prereg's design, pinned at `6e7c918` before any code. It can only turn a
  grade into "not recorded", never the reverse, and it is what makes point 4 meaningful: the run.txt
  whose end time is checked is proved to be the run that wrote this CSV. Within the ruling.

Other observations (none a defect against the prereg):
- A commit that deletes the CSV (or run.txt) before the deadline is skipped and an older qualifying
  commit is used: the prereg's "first one where both hold" says exactly that; a retraction by
  deletion therefore does not retract.
- The bundle commit must be on the nightly's `master` HEAD history. If it reaches master by merge it
  keeps its committer time; if by rebase after the deadline it gets a new committer time and GW8 is
  "not recorded" (the conservative direction; the ruling chose committer time).
- The precedence `if not proj and ...` (log rows win over the bundle) is amendment 1's line, not new;
  no test covers it (my mutation M9 survived). For GW8 the log holds no xp_v2 rows.

## Leak check (check 1)

The item produces one evaluation: GW8's realised points for xp_v2. Its inputs are the CSV at a commit
whose committer time and run end are both strictly before `events.deadline_time` (2026-10-23T17:30:00Z,
read read-only from `C:\GIT\FPL-data` at `63e6a44`), the post-deadline picks and the official points.
- Timestamp audit (decides): committer time at the deadline (committed 17:30Z; 19:30+02:00) rejected;
  run end at the deadline rejected; one second before both accepted; committer before but run end at
  the deadline skipped in favour of the older commit (`test_a_run_ending_after_the_deadline_is_skipped`).
  PASS.
- Truncation (decides): only GW8 is in `BUNDLE_GWS`; no gameweek is graded yet. On the hermetic fixture
  with the real GW8 CSV in a scratch repo, `realised()`'s xp_v2 value and captain equal
  `fpl_realised.realised_on` on the CSV's values for the 15 picks, exactly (47.0, captain 12). PASS.
- Shift probe: not a correlation metric; not applicable.

## (2) Robustness (my probes, `scratchpad/v3_a2/e2e.py`, 27 of 27 passed)

- Real bundle (`s8c_a3_live`, tools `ea95cf6`, run end 2026-10-20T16:35:24+00:00) committed in a scratch
  repo under `core.autocrlf=true` at 16:36:24Z, then an unrelated commit after the deadline: graded from
  the bundle commit, 668 players, tools commit `ea95cf6057...` (full hash), values exact; `git show`
  returns the LF blob and its SHA-256 equals run.txt's `d8ba0bff...`.
- Line endings: the live CSV is LF-only. A CRLF working copy committed under `core.autocrlf=true`
  (normalised) graded; the same under the repository's own `.gitattributes` (`* text=auto`) with
  `autocrlf=false` graded; a CRLF blob actually stored (`autocrlf=false`, no attributes) is a SHA
  mismatch and "not recorded" (the safe direction). On the Linux nightly the blob is the LF file the
  tool hashed; the compare is on the blob, never the checkout.
- Shallow clone (`--depth 1`, HEAD after the deadline): None, no exception. Full clone: graded.
  Non-repository folder, missing folder, repository with no commits: None. No `git` on PATH: None,
  exit 0. Every path ends in "xp_v2: not recorded before the deadline"; no red night.
- run.txt `commit: unknown (git unavailable)`: graded, label `(tools unknown)`. run.txt listing the
  CSV as `(missing)`: not recorded. A player whose CSV row is 0 ("not forecast") is in the CSV: graded.
- Real data folder, read-only, real clock: "no gameweek from GW8 has passed its deadline yet", `[]`.
  At a simulated 25 Oct: "GW8: not locked down: not graded (data_checked 0, 0 of 10 fixtures finished)".

## (3) Clean-checkout suites (`git archive`, no `ODDS_API_KEY`, `python -m unittest discover -v -p "test*.py"`)

| Run | Result |
|---|---|
| before, `191b0b0`, bare | Ran 748 tests in 555.1s, OK (skipped=11) |
| after, `bbe770a`, bare | Ran 749 tests in 554.7s, OK (skipped=11) |
| after, `bbe770a`, `FPL_DATA_DIR=C:\GIT\FPL-data` | Ran 749 tests in 554.4s, OK (skipped=4) |

+1 test: `BundleGrading` 7 -> 8. `tests.test_S3.Hermetic.test_the_git_using_tests_pass_with_an_empty_home`
ok (it reruns `BundleGrading` in a child with an empty HOME; the helpers pass identity, dates and
`core.autocrlf=false` per command). `tests.test_S3.FastTrack.test_the_nightly_imports_nothing_under_tools_or_analysis` ok.
The prereg's six acceptance tests are all present and green (both times before; run end at/after
skipped; SHA mismatch skipped; one of 15 missing; actual 15 after a transfer; `realised_on`'s arithmetic).

## (4) Recording path (check 5)

`fpl_edge.py --record --source <src>` for all seven nightly sources, clock frozen at
2026-10-20T19:00:00Z (the `datetime` class swapped before import; `record_status` imports it locally),
on three copies of the data folder: `191b0b0` twice and `bbe770a` once. All three `projection_log.csv`
are byte-identical (SHA-256 `5ea2d015...`, 9461 rows; the status files identical: own 277, xg 257,
minutes 257, bottomup 257, fpl_ep 668, bottomup_lambda 257, `RECORD SKIP xp_v2 the export's
all_players has no code (the prior's key)` in both). `fpl_edge` never imports `fpl_squad`
(`fpl_sections` does, for the report's REALISED section). PASS. Side observation, not this item's:
the local working export `fpl_export_gw7.json` has no `code` on `all_players`, so xp_v2 recording
skips on this data copy at both commits.

## (5) Mutations (scratch copy, `tests.test_W3.BundleGrading`; `mutate.py`, `mutate2.py`)

| # | Mutation | Result |
|---|---|---|
| M1 | committer time at the deadline accepted (`>=` -> `>`) | RED (`test_only_at_or_after...`) |
| M2 | run end at the deadline accepted (`<` -> `<=`) | RED (`test_a_run_ending_after...`) |
| M3 | SHA-256 check removed | RED (`test_a_csv_not_as_run_txt...`) |
| M4b | missing-player check removed (`absent = []`, `values.get(pid, 0.0)`) | RED (`test_one_of_the_15_missing...`) |
| M5 | oldest qualifying commit instead of the newest | RED (`test_the_newest_valid_commit_wins`) |
| M6 | XI chosen on negated xp_v2 | RED (4 errors) |
| M7 | label `tools` shortened to 6 | RED (2 failures) |
| M8 | the required "not recorded before the deadline" sentence dropped | RED |
| M10 | committer-time filter removed | RED |
| M4 | (my first M4 was ineffective: a `defaultdict` still reports a missing key to `in`) | n/a |
| M9 | bundle wins over log rows (amendment 1's line, not new) | survived: no test with xp_v2 rows for GW8 |
| M11 | committer offset ignored (`[:19]` as UTC) | survived: every test commits with `+00:00` |

Nine effective mutations of the new logic, all red; the restored copy is green. M11 is a coverage
gap, not a code defect: my probe shows the real code rejects `19:30+02:00` against a 17:30Z deadline.
It matters because this machine's commits carry `+02:00` (e.g. `bbe770a` itself); for a positive
offset the naive reading errs on the conservative side.

## (6) Runner isolation

`fpl_squad.py` imports csv, hashlib, io, os, re, sqlite3, subprocess, collections, datetime and
`fpl_bt`, `fpl_chips`, `fpl_edge`, `fpl_mv2`, `fpl_pmf`, `fpl_realised`, `fpl_xpv2`; nothing under
`tools/` or `analysis/`; no `sys.path` edits. The diff touches no file under `tools/`. The suite's
`FastTrack` test is green. PASS.

## (7) Secrets

`git diff 191b0b0 bbe770a` grepped case-insensitively for `apikey`, `api_key`, `authorization`,
`bearer`, `secret`, `http://`, `https://`: no match. Long tokens: only the fake tools commit hash
`71c9d17d...` in the tests and `"ab" * 32` (a deliberately wrong SHA-256). No key, no URL, no header. PASS.

## Write guard

`git status --short` in the item worktree before this file was written: clean. After: this file only
(untracked, uncommitted). The read-only data worktree (`63e6a44`) was not written to.

## Recommendations for the chat (not conditions of the verdict)

1. Add one `BundleGrading` test whose committer date carries a non-zero offset (e.g. `+02:00`), so
   the offset handling in `_utc` is pinned (mutation M11 survives today).
2. The `fetch-depth: 0` comment in `nightly.yml` still cites amendment 1 (C); update when next touched.

VERDICT: PASS. The prereg with the ruling verbatim was committed (18:30) before the code (18:41); the code does exactly the pinned design: the CSV at the newest commit on the checkout's history whose committer time and run.txt end are both strictly before the GW8 deadline and whose run.txt carries the CSV blob's SHA-256, read through git only; our actual 15 from the post-deadline picks, own from the log, xp_v2 from the CSV, both scored by `realised_on`; every missing input, shallow or absent history, or absent git ends in "xp_v2: not recorded before the deadline". My own e2e with the real 668-player CSV (tools ea95cf6) reproduces the main session's read, the clean suites go 748 -> 749 OK (bare and with data, Hermetic included), the frozen-clock projection log is byte-identical across 191b0b0 and bbe770a, nine of nine effective mutations go red, nothing under tools/ is imported and no secret is present. The parenthetical reason and the SHA-256 condition are within the ruling (the required sentence is verbatim; the extra condition only ever withholds a grade and is pinned in the prereg before code).
