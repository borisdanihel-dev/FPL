# Verifier report: S16 part 1, blank and double gameweek history

- Verifier: `backtest-verifier`, model Fable 5.1 (`claude-fable-5-1`), effort high as `.claude/agents/backtest-verifier.md` states (read from disk first; it governs). 19 Oct 2026.
- Item: BUILD_PLAN.md Step 16 point 1; RULING lane A 19 Oct midday, point 2. Offline, under `tools/`. Descriptive item with a reproduction test: checks 1, 2, 5, 6, 7 and the prereg's part 1 acceptance tests.
- Code: branch `s16-wip`, single commit `2ed24d6` on master `47142a3`, adding `tools/blank_double.py` (196 lines) and `tests/test_S16_part1.py` (133 lines), nothing else (`git diff --name-status 47142a3 2ed24d6`: 2 x `A`). `git ls-remote origin` gives the same two hashes for `master` and `s16-wip` as the local refs.
- Written: this file only. `git status` in `C:\GIT\FPL` before and after: only the pre-existing untracked `worklog/verify_S2b_pre.md` and `verify_W1b_pre.md`; `C:\GIT\FPL-data` clean at `9da6ff1`, its `projection_log.csv` sha256 `e466...` unchanged; `C:\GIT\FPL-b` not touched; nothing written under `historical/` (read-only files, mtimes unchanged); no fetch, push, ref, tag, hook or config change (refs listed before and after, identical). No dispatch, API or download. All work in the scratchpad (`v_*` files and folders) on `git archive` extractions of `47142a3` and `2ed24d6`.
- Downloads-are-data rule: every read of anything under `historical/` was a Python script run with `python -I`, the path as an argument, from `C:\GIT\FPL` (`v_hash.py`, `v_count.py`, `v_compare.py`, `v_events.py`); nothing there was sourced, executed or piped.

## Prereg ordering: PASS

`prereg/S16.md` sections "Midday ruling, 19 Oct (part 1)" (lines 88-96, the ruling verbatim, three points, `END RULING`) and "Part 1, acceptance tests" (lines 98-135) first appear in `47142a3` (2026-10-19 10:29:41 +0200; absent from `47142a3^`, grep count 0). The only code commit, `2ed24d6` (10:51:14 +0200), has `47142a3` as its parent; `git log --all -- tools/blank_double.py tests/test_S16_part1.py` shows no earlier commit touching either file. The prereg carries "No re-tuning after viewing results"; the ruling text is present verbatim, so nothing to report under check 4.

## Inputs and their hashes

`v_hash.py` (bytes, `python -I`), every file under `historical/`:

| file | bytes | SHA-256 | manifest |
|---|---|---|---|
| 2018-19/fixtures.csv | 636313 | `f50cbc202ea89289e359a74c2e82e988965f063f4016bbe49426d3de483cc046` | equal |
| 2019-20/fixtures.csv | 668794 | `81851c3c55373c443aa6b7062be85d5710d61ab784239e9810655b343728e0ed` | equal |
| 2020-21/fixtures.csv | 660303 | `75ca4859c7898bff9c73055337651893c041e596462d08935f2a6964c437f65d` | equal |
| 2021-22/fixtures.csv | 668973 | `9fc11cc675ff49dd5b8858211aa5cbe08375e064810536931e0ac38c060dee64` | equal |
| 2022-23/fixtures.csv | 696260 | `e783060da73700d4ec6fd12acec4568524eac8bb3ba3ccd8ce68a374dadba8f8` | equal |
| 2023-24/fixtures.csv | 712532 | `d8521bdbb80edb5141bc17df71bf6026275f2e56fd6a6dc6041b3ae23a39ce6a` | equal |
| 2024-25/fixtures.csv | 751413 | `ce696e187569ca7c45da2562811d3c38f525b58e65575531be37bebd0769ee28` | equal |
| 2025-26/fixtures.csv | 1014129 | `2d7e3950d346df14ca486cb09e9b9ba406d37d943775244eed06cdc021ffb3a9` | not in the manifest (local since 17 Oct 17:05) |
| 2025-26/merged_gw.csv | 5445456 | `0d09f1f1cb1b5520ec8e2f25238aa652efe2a263d8ca7cb2b6538b27bf86727d` | not in the manifest (17 Oct) |
| 2025-26/teams.csv | 1744 | `b29df099cb0ad25413e284e53116099b0e0496874f99743dbc0870d8241b46c5` | not in the manifest (17 Oct) |
| 2025-26/players_raw.csv | 380363 | `412ce0172016f8f98f25177dc6de9f3cd2a8ec7a6135f9aa638d7fdee784d67b` | equal (not used by this item) |

The seven vaastav `fixtures.csv` (commit `9779cdb`) match `worklog/downloads_2026-10-19.md` byte count and digest. The three 2025-26 files have no manifest entry, so their provenance rests on the 17 Oct session; their digests are recorded above for the first time.

## Check 1: point-in-time leak check: PASS (not applicable in substance)

The item records no forecast, builds no feature any model reads and produces no evaluation metric: it is a season-end description. 1a truncation and 1b timestamp tests have no gameweek to truncate at: every input file post-dates the whole season it describes (fetched 2026-10-19T06:24Z per the manifest, or local since 17 Oct), every season is complete (`finished` is `True` on every 2022-23 row, 380 fixtures in every season), and the runner imports nothing from it (`tests/test_S3.py::FastTrack::test_the_nightly_imports_nothing_under_tools_or_analysis` and `tests/test_S4.py`'s twin, green in all four suite runs below; `grep -rn blank_double` finds no reference outside `tools/` and its test). 1c shift probe: no correlation on points. One design note, not a defect: the `event` field in a season-end fixtures file is the as-played event after rescheduling, so it is hindsight relative to any in-season deadline. That is exactly what the ruling asks for ("Use each fixture's FPL event field; no deadlines needed") and is right for a history; it must not be reused as an in-season feature without a dated source.

## Check 2: clean-checkout suite: PASS

`python -m unittest discover -p "test*.py"` on `git archive` extractions (content byte-identical to the commits: `git hash-object` of the extracted `tools/blank_double.py` = blob `75db6ce`, `tests/test_S16_part1.py` = blob `4353a37`; the extraction has CRLF endings by `text=auto`, content otherwise identical):

| mode | `47142a3` (before) | `2ed24d6` (after) |
|---|---|---|
| bare (`FPL_DATA_DIR` unset) | Ran 605, OK (skipped=10) | Ran 613, OK (skipped=10) |
| runner-like (`GITHUB_ACTIONS=true`, `GITHUB_REF=refs/heads/s16-wip`, `FPL_DRY_RUN=true`, `FPL_DATA_DIR=C:\GIT\FPL-data`) | - | Ran 613, OK (skipped=3); data worktree still clean after |
| stand-in zones (`PYTHONTZPATH` = the implementer's `tz2`) | - | Ran 613, OK (skipped=8) |
| hermetic (empty HOME, USERPROFILE, XDG_CONFIG_HOME, `GIT_CONFIG_NOSYSTEM=1`, empty global config, author variables unset) | - | Ran 613, OK (skipped=10) |

The 8 added are exactly `tests/test_S16_part1.py` (7 in `Counts`, 1 in `Isolated`, listed verbosely, all ok in 0.15 s). The implementer's `s16p1_suites_out.txt` says 613 in all four modes with skipped 10/3/1/10; mine agree except the zone run (8 skipped, not 1), which depends on the stand-in zone folder's state, not on this item. The tests are hermetic: `tempfile.mkdtemp` with cleanup, toy CSVs, no clock, zone, locale or git config; the `Isolated` test runs the tool under `sys.executable -I` with `cwd` in the temporary folder.

## Check 3: the reproduction test, re-run and an independent count: PASS

`python -I <clean 2ed24d6>/tools/blank_double.py test --hist C:/GIT/FPL/historical` from `C:\GIT\FPL`, exit 0, output identical line for line to the implementer's `s16p1_test.txt` (`diff` empty):

```
REPRODUCE 2024-25: 760 team-events (20 teams x 38 events): every count equal
REPRODUCE 2025-26: 760 team-events (20 teams x 38 events): every count equal
  secondary, 2025-26 against merged_gw.csv: 750 team-events with a fixture; every count equal
REPRODUCTION PASS
```

`history` likewise: 125 lines, identical to `s16p1_history.txt`.

My own reader (`v_count.py`: `csv.reader`, header indices by name, a plain dict, written without the tool, run with `python -I`) and the comparison (`v_compare.py`), every season:

| season | fixtures | ids | events | team-events | tool `counts()` vs mine | tool `straight_count()` vs mine | blanks | doubles |
|---|---|---|---|---|---|---|---|---|
| 2018-19 | 380 | 1-20 | 38 | 760 | same keys, 0 differ | 0 differ | 22 = 22 | 22 = 22 |
| 2019-20 | 380 | 1-20 | 38 (1-29, 39-47) | 760 | 0 differ | 0 differ | 6 = 6 | 6 = 6 |
| 2020-21 | 380 | 1-20 | 38 | 760 | 0 differ | 0 differ | 44 = 44 | 43 = 43 |
| 2021-22 | 380 | 1-20 | 38 | 760 | 0 differ | 0 differ | 61 = 61 | 61 = 61 |
| 2022-23 | 380 | 1-20 | 37 (no 7) | 740 | 0 differ | 0 differ | 22 = 22 | 42 = 42 |
| 2023-24 | 380 | 1-20 | 38 | 760 | 0 differ | 0 differ | 23 = 23 | 23 = 23 |
| 2024-25 | 380 | 1-20 | 38 | 760 | 0 differ | 0 differ | 10 = 10 | 10 = 10 |
| 2025-26 | 380 | 1-20 | 38 | 760 | 0 differ | 0 differ | 10 = 10 | 10 = 10 |

Unscheduled fixtures: 0 in every season (both readers). Every per-event blank and double list in my output matches the implementer's history (checked line by line: e.g. 2020-21 GW35 team 13 x3, 2021-22's 61/61, 2025-26 GW31 blank ids 1, 8, 13, 20 = ARS, CRY, MCI, WOL). Secondary source: my own `merged_gw.csv` count (distinct `fixture` ids per `(round, team)`, team mapped through `teams.csv`) gives 750 keys, 0 differences from the tool's and 0 from the fixtures-file counts; the 10 zero team-events (the 2025-26 blanks) have no `merged_gw.csv` row. `teams.csv` has columns `id`, `name`, `short_name`; the tool's `team_names` equals my `csv.reader` mapping (20 ids; Burnley 3, Bournemouth 4 as FPL numbered them); no `teams.csv` for 2024-25 gives `{}`, so ids print as `team N` as the prereg says. Differences from the implementer's numbers: none (integers).

On the prereg's words "The straight count is a separate reader written independently of the tool": `straight_count` lives in the same file, by the same author, sharing no code with `read_fixtures`/`counts` (`csv.reader` with header indices, a `Counter`). My reader above is the independent one; the two agree on all 6,080 team-events across the eight seasons.

## Acceptance tests of the prereg (part 1)

1. The tool: stdlib only (`argparse, csv, os, sys, collections`), no repository import (mutation P7 confirms a repository import would break the `-I` run), opens with mode `r` only; eight seasons 2018-19 to 2025-26; ids 1-20; names only where `teams.csv` exists; no download code (no URL, no `urllib`, no `http`). PASS.
2. Unscheduled kept apart (toy test; `"", "None"` both handled; none in the real data); 2019-20's 39-47 kept and flagged (`numbered above 38: [39..47]; unused numbers: [30..38]`). PASS.
3. The reproduction test: see check 3, PASS; the secondary against `merged_gw.csv` equal.
4. Output: per season every event with a blank or double and its teams; totals; the cross-season table by event number (seasons / team-events, blank and double). Present in all 125 lines. PASS.
5. Tests: blank, double, triple, unscheduled, event above 38, the comparator catching one changed count (three variants), the read-only open (bytes unchanged after `history` and `straight_count`), plus the `-I` subprocess run. One mutation per rule, each red (check 6). PASS.

## Judgements the launcher asked for

**2022-23 GW7 (for the chat, nothing changed).** The file holds 380 fixtures in 37 events: event 7 has 0 rows, no fixture kicks off 9-12 Sept 2022, and the ten postponed matches sit in later events (`8: 7` fixtures, `12: 9`, `19: 11`, `20: 12`, `22: 11`, `23: 11`, `27: 12`, `28: 7`, `29: 16`, `32: 8`, `34: 13`, `36: 11`, `37: 12`). Under the ruling's method (each fixture's `event` field, no deadlines) the set of events can only be inferred from the fixtures, so an event that held no fixture is invisible; the tool follows that literally and flags GW7 as an unused number, with no team blanks. Two facts for the chat: (a) GW7 2022/23 was a real, played FPL event (its deadline passed on 10 Sept 2022 with every fixture postponed on 9 Sept; everyone scored 0), unlike 2019-20's ids 30-38, which the game skipped to "GW30+" = id 39 and which nobody ever played; the fixtures files cannot tell the two cases apart (`finished` is `True` on every row; no event deadlines were downloaded, by the ruling). (b) The blank/double symmetry seen everywhere else breaks here: every other season has blanks = doubles (2020-21's 44 vs 43 is one triple), while 2022-23 has 22 blanks against 42 doubles; the 20 doubles created by rescheduling GW7's ten fixtures have their 20 matching blanks in GW7 itself. For Step 16's purpose (blank and double likelihood by event number, for chips) the one whole-round blank in eight seasons is the kind of event the planner cares about most, and the table's row `GW7: blank 0 / 0; double 1 / 2` understates it. My reading: the tool is right under the ruling as written and flags the gap honestly, so this is not a defect of the item; it is an open decision: keep the literal rule and annotate unused numbers inside 1..38 as candidate whole-round blanks the file cannot confirm, or amend the ruling so an unused number inside 1..38 counts as 20 team blanks (2022-23 would read 42 / 42; the 2019-20 ids 30-38 would need an explicit exception, since those were never played). A one-line rule either way; the chat should decide before part 4 uses this history.

**The cosmetic line.** `2022-23: 20 teams, 37 events (numbered above 38: []; unused numbers: [7])`: `history()` prints both lists whenever either is non-empty (`if late or gaps`). Cosmetic only; the values are correct; reproduced in my run.

## Check 5: recording path: PASS

Two copies of the data worktree at `9da6ff1` (`.git` excluded, `diff -rq` empty before, `projection_log.csv` sha256 `e466...`, 5757 lines), a `sitecustomize` shim first on `PYTHONPATH` pinning `datetime.now()` to 2026-10-19T00:00:00Z (checked), the nightly's own commands (`fpl_edge.py --record --source {own,xg,minutes,bottomup,fpl_ep} --status`, `--watch watchlist.txt --out`, `--diff --out`, `--stuck`) from the `47142a3` tree on one copy and the `2ed24d6` tree on the other. Both: `RECORD OK own 275, xg 260, minutes 260, bottomup 260`, `RECORD SKIP fpl_ep the export has no ep_next for any player`, every command exit 0, `projection_log.csv` 6812 lines, sha256 `b927...` on both (the digest the S10 and S16 verifiers obtained from the same data), `diff -rq` of the two copies empty. Against the real log: its 5757 lines are an exact prefix of the regenerated log; 1055 rows appended, 0 removed or changed. The item does not touch `fpl_edge.py`, `fpl_nightly.py` or the workflow (the commit adds two files only), and the real data worktree is untouched.

## Check 6: mutation spot-check: PASS

On LF-normalised scratch copies of the `2ed24d6` tree (the extraction's CRLF endings defeated both scripts' multi-line patterns; after normalisation `git hash-object` = blob `75db6ce`, so the content is the commit's). The implementer's `mutate_s16p1.py` re-run by me: P1-P10 all RED (10/10; P3, P4, P8, P10 by errors, the rest by failures), file restored (sha `d408...` before and after). My own nine single replacements, `tests.test_S16_part1`:

| mutation | result |
|---|---|
| V1 away side not counted | FAILED (failures=6) |
| V2 a blank is a count of 1 | FAILED (failures=2) |
| V3 straight count skips the away side | FAILED (failures=4) |
| V4 comparator always agrees | FAILED (failures=2) |
| V5 regular events end at 47 | FAILED (failures=1) |
| V6 table doubles not accumulated | FAILED (failures=1) |
| V7 a team seen only in an unscheduled fixture dropped from the teams | OK (not caught) |
| V8 exit code 0 after a failed reproduction | OK (not caught) |
| V9 a triple reported as a double of 2 | FAILED (failures=2) |

7/9 red; the two green ones are coverage notes, not defects: V7 needs a team with no scheduled fixture, which the toy and the real data (0 unscheduled fixtures) never have; V8 is the process exit code, which only the `Isolated` test sees and only on the passing path, while the in-process test checks `test()` returns `False` and prints `REPRODUCTION FAIL`. The prereg's acceptance list does not ask for either.

## Check 7: secrets: PASS

`git show 2ed24d6:tools/blank_double.py 2ed24d6:tests/test_S16_part1.py | grep -i -E "apikey|api_key|authorization|bearer|secret|token|https?://|[A-Za-z0-9]{32,}"`: no match. No URL, no header, no key-like string in either file.

## The implementer's process notes

- The shell `head` on `historical/2025-26/teams.csv` after the rule was adopted: a read with no execution, no pipe into a shell and no heredoc. It breaches the letter of the rule (not a Python `-I` reader) but not its purpose; `teams.csv` is unchanged (mtime 17 Oct 17:05, digest above) and the tool's own mapping equals my `-I` read of it. No effect on the result. Worth a one-line mention in the item report, nothing more.
- The 06:45 UTC incident (CHANGELOG `47142a3` line 3410): all seven `fixtures.csv` and `players_raw.csv` match the manifest's digests now; the code commit touches two new files only; nothing under `historical/` was created or changed. No effect on the result.

## Claims checked

1. Rules as claimed: both teams counted per fixture (V1/V3/P8 red), blank = 0 in an event holding fixtures, double >= 2 (P2, V2, V9), unscheduled apart (P3, P4), events above 38 kept and flagged (P6, V5), ids 1-20 named only with `teams.csv`. Confirmed.
2. Reproduction test: re-run identical; independent count equal on 6,080 team-events over eight seasons and on the secondary 750. Confirmed.
3. History totals 22/22, 6/6, 44/43, 61/61, 22/42 (37 events, GW7 unused), 23/23, 10/10, 10/10: confirmed by my reader; the GW7 reading is the open decision above.
4. Tests 8, hermetic, 605 -> 613 green in four modes; P1-P10 red: confirmed.
5. Runner path untouched: two new files; no runner reference; the no-import test green. Confirmed.
6. Process notes: no effect on the result.

VERDICT: PASS

The prereg's ruling and acceptance tests were committed in `47142a3` before the single code commit `2ed24d6`; the inputs match the manifest (the three 17 Oct files now have recorded digests); the reproduction test re-run gives the implementer's lines exactly and my own `-I` reader, written without the tool, agrees with it on every one of the 6,080 team-events across the eight seasons and on the 750 secondary keys; every acceptance test of the prereg holds; the suite goes 605 -> 613 green bare, runner-like, with stand-in zones and hermetically; the recording path is byte-identical before and after under a frozen clock; 10 + 7 mutations are red and the two that survive are coverage notes outside the prereg's list; the two files hold no secret and the runner imports nothing new. The one open point is interpretive, not a defect: under the ruling's fixtures-only method 2022-23's GW7 appears as an unused number with no team blanks, although it was a played whole-round blank (20 team blanks, which would restore the 42/42 symmetry); the chat should rule on it before this history feeds part 4.
