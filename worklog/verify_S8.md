# verify_S8 — rolling-horizon transfer planner (tools/planner.py), re-verification

Verifier: Claude Fable 5.1 (claude-fable-5-1), effort high, run natively as
`backtest-verifier` with `.claude/agents/backtest-verifier.md` read from disk
first (it matched the loaded instructions). Repository `C:\GIT\FPL-b`, branch
`lane-b` at `8f28a0b`, tree clean before and after. Date 2026-10-19,
12:50-13:20 local. Nothing outside this file was written in the repository;
every scratch file lives in the session scratchpad (`rv2/`). `C:\GIT\FPL-data`
was read only (HEAD `9da6ff1`, nightly 2026-10-18; never pulled, synced or
recorded). The full 4 h 20 min replay was not rerun, as instructed; the three
replays under `tools/out/planner/` were checked against my own run of this
morning and their `run.txt` provenance.

## Summary of the first run (03:40-08:00, verdict FAIL)

Checks 1a/1b (truncation at origins 2, 20, 38 with every round >= t outcome
garbled: forecasts, P(start), market, candidate ranking and baseline identical,
worst difference 0.0; the instrumented `canonical_through` slice ends at t-1;
every live input before the GW8 deadline), 2, 5 and 7 passed; 4 passed with a
flag (the lost banked-FT charge is the (k+1)-th schedule value, the prereg's
acceptance test 1 says the k-th); 6 passed with five surviving mutations that
were test gaps (club cap 3 vs 4; the -4 x hits term; the replay's realised hit
charge; realised read from round t; HORIZON 6). Check 3 FAILED: the recorded
replay (+7.68 [-6.58, +22.06], planner 1919.5) was the first commit's
non-exhaustive candidate generator's; my in-process replay of the final code
`22a179c` (14,116 s) gave planner 1914.7 (12.58 hits, 49.5 transfers),
baseline 1911.8 (36.98 transfers), paired gain +2.90, 90% CI [-12.74, +18.40],
bootstrap p 0.7382, robustness [9, 4, 7, 3, 11]. Its text is still in the
scratchpad (`s8_verify/planner_replay_2025-26.txt`, sha256 3591..., with
`results.pkl`).

## Prereg and rulings

`prereg/S8.md`: `de7e1b3` (01:13:44 +0200) precedes the first code commit
`51520ef` (01:22:46). `git diff de7e1b3..HEAD -- prereg/S8.md` shows only two
appended sections, nothing above them touched: "Ruling morning 19 Oct"
(`0df1443`, 08:01:24, items 1-6, END RULING) and "RULING S8 verifier FAIL"
(`a01c862`, 08:22:03, items (a)-(e), END RULING), both before the code they
govern (`ff8422f` 08:04:53 for the exploratory variants; `5423434` 08:33:08
and `7f72141` 08:38:56 for the test gaps and provenance). The verbatim
rulings are the ones checked below.

## Check 1 — point-in-time — PASS (the first run's evidence stands)

`tools/planner.py` has blob `6a69e9c7...` at `7f72141` (the replay commit),
at HEAD `8f28a0b` and in the working tree. Against `22a179c` (the code my 1a/1b
evidence was taken on) `git diff 22a179c..7f72141 -- tools/planner.py`
changes: the `provenance` import; `EXPLORATORY`; `evaluate`/`rank_plans`/
`replay` gain `hits_allowed=True, buffer=HIT_BUFFER` keyword parameters with
the pre-registered defaults (`HIT + buffer` replaces `HIT_MIN_GAIN`, equal at
the default); two exploratory lines appended to the live output; the replay's
header/bar/`pass` lines branch on `pre_registered`; `--no-hits`, `--buffer`,
the output folder `tools/out/planner/` and `run.txt`. `Replay.__init__`,
`forecasts`, `market`, `squad_rows`, `realised`, `build_pool`,
`plan_candidates`, `legal`, `baseline_plan` and the replay loop's data path
are byte-for-byte unchanged. `fpl_edge.py` (`a783d6f0`), `tools/hist_pit.py`
and `fpl_hist.py` have the same blob at `22a179c` and `7f72141`;
`tools/chips.py` and `tools/backtest.py` differ only in `main()` (the
provenance `Run`, the per-tool output folder). `fpl_edge.py` changed between
`7f72141` and HEAD only in `record_status`/`main` (W1's `fpl_ep` SKIP path,
`RECORD_SKIP`), which the planner never calls (confirmed by `git diff
7f72141..HEAD -- fpl_edge.py`). Behavioural confirmation: a 3-squad GW2-12
replay of the `8f28a0b` archive (PYTHONHASHSEED=0) reproduces the `22a179c`
per-squad results exactly (planner 592.0 / 512.0 / 522.0, hits 7 / 8 / 7,
transfers 18 / 19 / 18; baseline 596.0 / 500.0 / 513.0, 11 transfers each),
and the full replay text is byte-identical to my `22a179c` run (check 3).
Hence the truncation test (1a) and timestamp audit (1b) of the first run
apply to the final code unchanged. 1c (shift probe) is not applicable: the
metric is realised season points, not a correlation. Note: the replay's inputs
`merged_gw.csv`, `fixtures.csv`, `teams.csv` under `historical/2025-26/` are
unchanged since 2026-10-18 13:43 UTC; `players_raw.csv` was rewritten at
09:32 UTC during the replays but no module in the planner's import chain
reads it (grep `players_raw` over `fpl_hist.py`, `fpl_edge.py`,
`tools/chips.py`, `tools/backtest.py`, `tools/hist_pit.py`,
`tools/planner.py`: no hit).

## Check 2 — clean-checkout test runs — PASS

`git archive` into the scratchpad, `FPL_DATA_DIR` unset, `python -m unittest
discover -p "test*.py"` from the archive root:
- before (`0df1443`, the parent of the first code commit of this
  re-verification, `ff8422f`): Ran 559, OK (skipped=10).
- after (`8f28a0b`): Ran 646, OK (skipped=10).
The difference includes lane A's merged tests (W1, S16, S10, the bundle,
provenance), not only S8's. `tests.test_S8` is 7 tests (clean 7 OK in the
mutation copy); `tests.test_provenance` 4 OK on the tree.

## Check 3 — the pre-registered evaluation — PASS

`tools/out/planner/s8_run3/planner_replay_2025-26.txt` is byte-identical
(`diff` empty; sha256 `35916137...` both) to my own in-process replay of
this morning: planner 1914.7 (hits 12.6, transfers 49.5), baseline 1911.8
(transfers 37.0), paired gain +2.90, 90% CI [-12.74, +18.40] (B = 10,000,
seed 20261018), bar FAIL, robustness [9, 4, 7, 3, 11] of 37. Full precision
from my `results.pkl`: mean 2.9, lo -12.74, hi 18.4, p 0.7382, planner hits
12.58, baseline transfers 36.98, baseline hits 0 in every squad; the morning's
independent bootstrap reproduced the interval to 0.0. Difference: 0 (bar 1e-6).

Provenance (`run.txt`, written by `tools/provenance.py` at the tool's start
and close):

| folder | args | commit | modified | start-end UTC | duration | output sha256 = file |
|---|---|---|---|---|---|---|
| s8_run3 | --replay | 7f72141 | 0 | 06:39:10-10:58:17 | 15,547 s | 3591... yes |
| s8_buffer3 | --replay --buffer 3.0 | 7f72141 | 0 | 06:39:19-10:56:44 | 15,445 s | 5036... yes |
| s8_nohits | --replay --no-hits | 7f72141 | 0 | 06:39:15-11:01:17 | 15,722 s | 85c5... yes |

`7f72141` was committed 06:38:56 UTC, 14 s before the first start; it is the
final `tools/planner.py` (blob equal at HEAD). The folder files' mtimes
(12:58, 12:56, 13:01 local = UTC+2) equal the recorded end times, and the
stdout copies `tools/out/planner_s8_*_stdout.txt` are identical to the folder
files. The three runs wrote to separate folders and files, so running
concurrently could not cross-contaminate. The exploratory files' headers end
"; EXPLORATORY (RULING morning 19 Oct item 2): no bar, no adoption", print
"exploratory line: no bar, no adoption" and contain no "pre-registered bar"
line; `s8_run3`'s header has no EXPLORATORY and prints the bar. The
exploratory numbers (buffer 3.0: 1912.3, 12.7 hits, 49.6 transfers, +0.48
[-14.26, +15.36], [11, 10, 6, 3, 11]; no hits: 1920.8, 0.0 hits, 36.9
transfers, +9.00 [-4.74, +22.56], [2, 3, 2, 2, 3]) were not reproduced in
full (no bar rests on them); a 3-squad GW2-12 run of each variant on the
`8f28a0b` archive behaves as recorded: no-hits gives 0 hits and the
baseline's transfer count (11 each) with the baseline untouched (596 / 500 /
513 in all three variants), `pass` is None and the exploratory line prints;
buffer 3.0 is identical to buffer 1.5 on those 33 squad-weeks (every hit
taken there clears 7.0), consistent with the full-season "changes almost
nothing".

## Check 4 — metric, filter, bootstrap, threshold, record text — PASS

- The primary configuration, sample, bootstrap and bar are unchanged in the
  code (`DECAY 0.85`, `SCHEDULES["boris"]`, `HIT_BUFFER 1.5`, `HIT_MIN_PSTART
  0.8`, `MAX_FT 5`, `CLUB_MAX 3`, `GKDEF_CLUB_MAX 2`, `POOL 25`, `HORIZON 6`,
  `REPLAY_FIRST, REPLAY_LAST = 2, 38`, 50 squads seed 7, `BT.B` 10,000,
  `BT.CI` 0.90, `SEED 20261018`, `PASS_GAIN 10.0`, `ok = mean >= 10 and lo >
  0`) and reach the default path untouched (check 1). The exploratory
  variants are opt-in arguments and separately named output files.
- The record matches the files: the CHANGELOG entry "S8 record" (line 3672)
  and the report's record section quote 1914.7 / 12.6 / 49.5 / 1911.8 / 37.0,
  +2.90 [-12.74, +18.40], FAIL, [9, 4, 7, 3, 11], the buffer-3.0 and no-hits
  rows and the 06:39-10:58 UTC window, all as in the three files and
  `run.txt`.
- The first entry (line 3457) is kept and not edited: against its original
  at `65b9232` the only change is the `VERIFIER_LINE` placeholder filled with
  "**FAIL** (see the amendment of 2026-10-19 below)" at `615e29b` (07:59,
  before the FAIL ruling) plus a trailing blank line; its numbers stand as
  written. The mark "the buggy generator's" is carried by the amendment entry
  ("its replay numbers are superseded and not to be cited") and the record
  entry, consistent with "a frozen entry is never edited, only amended".
- Lost-FT charge: ruling (b) is in the prereg verbatim with the reading
  stated in its heading ("the schedule's (k+1)-th value when k are banked");
  the code (`lost_ft_value`: `V(min(5, k+1)) - V(k')`) and its test
  (`lost_ft_value(boris, 1, 1) == 1.0`) implement that reading; no number
  changed. The prereg's acceptance test 1 wording ("the k-th value") stands
  above the ruling unedited, as the protocol requires.
- Nothing promoted, nothing re-tuned: the bar is FAIL on the pre-registered
  line; the exploratory lines carry no bar and are described as information
  only; disposition (d) keeps the planner a screen with the baseline as the
  default. The report's record section still holds the placeholder
  `REVERIFY_LINE` for this verdict (worklog/cc_2026-10-19_S8.md line 203),
  to be filled by the main session.

## Check 5 — recording path and isolation — PASS

`python tools/planner.py --data C:\GIT\FPL-data --out <scratch>/live` from
the `8f28a0b` archive wrote `planner_live.txt` and `run.txt` only (the
archive is not a git checkout, so `run.txt` honestly says "unknown (git
unavailable)"). The top-5 tables for both schedules are identical to the
tree's `tools/out/planner_live.txt` of 01:24 (`diff` shows only the two added
exploratory lines: no hits and buffer 3.0 both choose Thomas -> De Cuyper,
score 6.09, gain 7.09, hits 0 — as the record states). `projection_log.csv`
sha256 `e466c9cd...` before and after; `git -C C:\GIT\FPL-data status` clean.
The planner only reads the log (`E.read_log`). `.github/workflows/nightly.yml`
and `fpl_nightly.py` contain no reference to `tools/` or `analysis/`; the
suite's isolation test (in `tests/test_S8.py`) passes in both clean checkouts.
`git status` of `C:\GIT\FPL-b` after my runs: clean.

## Check 6 — mutation spot-check — PASS (7 of 7 red)

Scratch copy of `8f28a0b` (`rv2/mut`, identical to the tree modulo CRLF),
one line changed at a time, `python -m unittest tests.test_S8`, the file
restored (clean 7 OK before and after):

| mutation | result | failing test |
|---|---|---|
| `CLUB_MAX = 3` -> 4 | RED | test_score_hand_case_and_ft_values |
| `score = decayed_gain - lost` (the -4 x hits term dropped) | RED | test_score_hand_case_and_ft_values |
| replay `st["pts"] += realised(...)` without `- HIT * hits` | RED | test_replay_runs_and_scores |
| `Replay.realised` reading `actual[t + 1]` | RED | test_replay_runs_and_scores |
| `HORIZON = 6` -> 3 | RED | test_live_cli_and_isolation |
| exploratory: `if not hits_allowed: return None` removed | RED | test_hit_rule |
| exploratory: `HIT + buffer` -> `HIT_MIN_GAIN` (buffer ignored) | RED | test_hit_rule |

The five survivors of the first run are now caught (item (c)); the two
exploratory-variant mutations are caught by the hand cases added at
`ff8422f`/`501df57`.

## Check 7 — secrets — PASS

`tools/planner.py`, `tests/test_S8.py`, `tools/provenance.py`,
`tests/test_provenance.py`, `prereg/S8.md`, `prereg/provenance.md`,
`worklog/cc_2026-10-19_S8.md`, `CHANGELOG.md`, the three replay files, their
`run.txt` and the three stdout copies, and `git show` of `ff8422f`,
`501df57`, `5423434`, `7f72141`, `a01c862`, `0df1443`, `8f28a0b`: no
`apiKey=`, `api_key=`, `Authorization`, `Bearer`, `x-api-key`, no
`ODDS_API_KEY` value, no 32+-character key-like string other than git
hashes. The planner reads no network and no environment variable.

## VERDICT: PASS

The recorded S8 result is now the final code's: `s8_run3` ran on
`7f72141` (0 modified tracked files, 06:39-10:58 UTC, output hash matching
the file), whose `tools/planner.py` is the blob at HEAD, and its text is
byte-identical to my own in-process replay of this morning (+2.90 [-12.74,
+18.40], planner 1914.7 / 12.6 hits / 49.5 transfers, baseline 1911.8,
robustness [9, 4, 7, 3, 11]); the bar FAILS and nothing is adopted. The
point-in-time evidence of the first run carries over because the replay's
data path is byte-for-byte unchanged since `22a179c` and the short replay
reproduces its per-squad results exactly; the clean-checkout suites pass
(559 -> 646, OK); the record text matches the files, the first entry is kept
with its numbers untouched and superseded by amendment, the lost-FT reading
is in the prereg by ruling, and the exploratory lines carry no bar; all seven
mutations (the five earlier survivors and two exploratory-variant lines) go
red; the live regeneration leaves the projection log and the data worktree
untouched; no secret is present.
