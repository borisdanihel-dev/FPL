# verify_S5 — backtest-verifier report

Item S5 in C:\GIT\FPL-b (branch lane-b). Two verifier runs, both on Fable 5.1
(claude-fable-5-1), effort high, as .claude/agents/backtest-verifier.md on disk (read first
each time; it matches the loaded instructions). No key-like string occurs in any file or
output examined (nothing to mask). The data worktree C:\GIT\FPL-data was read only (clean
before and after, HEAD e8629f0 "nightly 2026-10-18"); nothing outside this file was written
in the repository. Scratch material under the session scratchpad (amend/: before, after,
head and mut archives, repro/, tests_*.txt, probe_1b_live.py/.txt, probe_agg.py/.txt,
mutate.py/.txt).

## First run (code 01be62b, 2026-10-18) — stands: PASS, 1c WARN cleared by 1a/1b

Verified at 01be62b: prereg f9ca3d0 and Amendment 1 (94fbc36) committed hours before the
single code commit, ruling text verbatim; truncation rebuild of GW5/20/38 from rows of
round <= g and odds dated no later than round g (round g's outcomes garbled) differed from
the graded run by exactly 0.0 in every lambda, probability, forecast and Brier row (1a
PASS); every 2026/27 export used was generated before its deadline, the fallback trains
only on results kicked off before the deadline, only pre-closing Avg/B365 columns are read
(1b PASS); the shift probe gave a WARN for bottomup_lambda on DEF/GK starters (unshifted
+0.2269 under 0.25; drop +0.1126 against the 0.10 line, bottomup's own drop +0.0642),
cleared by 1a and 1b as the rule allows and reported; clean-checkout tests 386 OK (8
skipped) before and after, tests.test_S5 10 OK; the three pre-registered outputs
reproduced byte-identically (primary +0.0153 [+0.0098, +0.0214] n=34 PASS; Friday
sensitivity +0.0162 [+0.0091, +0.0242]; condition mean +0.1375 [+0.1282, +0.1469] n=2,
PASS in form, power 142.6 gameweeks); metric, sample, bootstrap (B=10,000, 90%, seed
20261018, paired by gameweek) and both bars exactly the prereg's; no runner file changed;
11 of 14 mutations red (survivors: the documented round-guard no-op M3, and M8/M13 in the
untested condition path); no secrets. Verdict PASS. The chat accepted it: "RULING S5
result" is verbatim in prereg/S5.md under "Ruling on the result" (commit 4abc716,
23:09:12), adopting bottomup_lambda as an S6 input and asking for points 3-4 below.

## Amendment run (RULING S5 result, points 3-4; code fa05534)

### Ruling before code — PASS

`git log`: 4abc716 (prereg/S5.md, "Ruling on the result (verbatim)", 23:09:12) precedes
fa05534 (23:14:50), the only code commit of the amendment; `git log -- tools/odds_lambda.py
tests/test_S5.py` shows 01be62b and fa05534 alone. `git diff 4abc716..fa05534 --stat`:
tests/test_S5.py (+231) and tools/odds_lambda.py (+210, -1) only; 9d48522 and 74f56d6
touch CHANGELOG.md and worklog/ only. Points 3 and 4 of the ruling are present verbatim.

### Check 1 — point-in-time, live path

- 1a (truncation): not applicable as a rebuild — the live forecast is for GW8 (deadline
  2026-10-23 17:30 UTC), in the future; every input is by construction dated before now.
  The condition path's toy test (point 3) now proves the pre-deadline selection directly
  (mutation V8 below red; it survived in the first run).
- 1b (timestamp audit) — PASS. Real live run of 2026-10-18: the export used is
  fpl_export_gw7_2026-10-18.json.gz, generated 2026-10-18T18:45:03Z (before the deadline;
  chips.newest_export takes the newest by (gameweek, date), there is no later one); the
  fallback trains on finished fixtures with kickoff < deadline: 60 fixtures, GW1-6, last
  kickoff 2026-10-12T19:00Z (GW7's 10 fixtures are finished = 0 in fpl.sqlite at e8629f0;
  the implementer's report says "seven gameweeks of results" — it is six, the output
  itself states nothing about the count); no finished fixture is dated after now; no
  odds/ folder exists under C:\GIT\FPL-data, so "NO SNAPSHOT" is correct.
  Snapshot selection on my own toy files (probe_1b_live.py, deadline 2026-10-23 17:30Z):
  `odds_2026-10-22T21-50-00Z.json.gz` taken 22nd 21:50 included; `odds_2026-10-23.json.gz`
  (date-only on the deadline day) read as 23:59:59 and excluded; `odds_2026-10-22.json.gz`
  (date-only the day before) 23:59:59 and included; `odds_2026-10-23T17-30-00Z` (exactly at
  the deadline) excluded; `odds_2026-10-23T17-29-59Z` included; `odds_2026-10-23T17-31-00Z`
  excluded; `odds_2026-10-23_1700` included, `odds_2026-10-23_1730` excluded; a payload
  `fetched_at` 2026-10-23T18:00Z inside a file named 10-22T10-00 → excluded (the payload
  wins); a payload `fetched_at` 10-23T10:00Z inside a file named 10-24 → included (the
  payload wins — the fetch time in the file is the authoritative stamp; noted). All files
  together → `odds_2026-10-23T17-29-59Z.json.gz` chosen; a file with no stamp in name or
  payload → MissingInput (the run stops); only a later file → None → fallback. 13 of 13 as
  wanted. The comparison is strict (`taken < deadline`).
- 1c: not applicable (the amendment adds no correlation metric; the first run's probe
  stands).

### Check 2 — clean-checkout test runs — PASS

`git archive` of each commit into an empty scratch folder (no historical/, no data,
FPL_DATA_DIR unset):
- before (4abc716): `python test_fpl.py` Ran 386, OK (skipped=8); `python -m unittest
  tests.test_S5` Ran 10, OK.
- after (fa05534): 386 OK (skipped=8); tests.test_S5 Ran 14, OK.
- HEAD (74f56d6): 386 OK (skipped=8); tests.test_S5 Ran 14, OK (the four new tests:
  Condition.test_condition_uses_the_pre_deadline_export_and_the_starters_threshold,
  LiveMode.test_aggregation_means_counts_and_exclusions, test_snapshot_time_and_selection,
  test_live_with_and_without_a_snapshot).
Matches the implementer's counts (386 OK, 8 skipped; 10 → 14).

### Check 3 — reproduction through the harness — FAIL (the live CLI)

From C:\GIT\FPL-b with my own `--out` (scratchpad amend/repro):
- `--season 2025-26 --test`, `--season 2026-27 --condition`, `--fixture ARS CHE`: all
  three byte-identical to tools/out/odds_lambda_test_2025-26.txt,
  odds_lambda_condition_2026-27.txt and odds_lambda_fixture_ARS_CHE.txt (`cmp` silent).
  The first run's numbers stand unchanged under the amended code.
- `--live --out <scratch>`, run as a plain command with stdout captured (the way any
  script, log capture or a Claude Code session runs it): rc 1, traceback
  `UnicodeEncodeError: 'charmap' codec can't encode character '\u0107'` from `print(s)`
  in `main.out` on the squad line "Muharemović" — on Windows a redirected stdout uses the
  locale encoding cp1252 — after the fixture table and one squad line were printed; no
  output file is written (main writes it only after every line is printed) and no
  "MISSING INPUT" line appears. The tests cannot see this: they pass an `out` callable or
  `redirect_stdout(io.StringIO())`.
- The same command with `PYTHONUTF8=1` (and separately `PYTHONIOENCODING=utf-8`): rc 0
  and the file is byte-identical to tools/out/odds_lambda_live.txt, so the numbers are
  deterministic and reproducible; the implementer's file was evidently produced from a
  console (PEP 528 console I/O is UTF-8). The defect is the reporting path, not the
  model: any squad or player name outside cp1252 crashes a captured run of the deliverable
  of ruling point 4. Fix is one line in `main` (e.g. `sys.stdout.reconfigure(
  encoding="utf-8", errors="replace")`, or write the file before echoing), plus a test
  that runs `main(["--live", ...])` through a cp1252-encoded stream.

### Check 4 — pre-registered test and condition untouched — PASS

The amendment diff is additive: imports (`re`, `timezone`), docstring lines, the live
section (snapshot_time, snapshot_events, newest_snapshot, aggregate_event, snapshot_book,
live), and the `--live` flag with its `elif` in main; `primary_test`, `condition_2627`,
`rebuild_2627`, `pre_deadline_export`, the constants (PASS_BRIER, STARTER_P, XI,
MIN_WEIGHTED, MAX_GOALS, seed) and backtest.py are not in the diff. Metric, sample,
bootstrap and both bars are therefore exactly the prereg's, as verified in the first run;
no metric was promoted and nothing was re-tuned (the pre-registered outputs reproduce
byte for byte). Ruling point 4's requirements map to the output: per fixture λ_home,
λ_away, P(cs) per side, bookmaker counts (h2h/totals) and source; our 15's GK/DEF with
bottomup and bottomup_lambda; the method stated in the header (mean decimal price across
bookmakers, h2h without h2h_lay, totals at 2.5, power de-margin, bisections); no snapshot
→ fallback, labelled on every line; tests on toy snapshot files. Point 3: the Condition
test uses a post-deadline export of the same gameweek with different stats that must
never be chosen, counts n independently against P(start) >= 0.8 (below the full count),
and refuses with no pre-deadline export.

Aggregation probe on my own event (probe_agg.py; LIV v BHA, six bookmakers): b1 with h2h,
h2h_lay and totals lines 1.5/2.5/3.5; b2 h2h without a draw price; b3 totals 2.5 plus an
`alternate_totals` 2.5; b4 h2h in shuffled outcome order and a 3.5 line only; b5 h2h_lay
only; b6 an h2h price of 1.0. Result: n_h2h 2 (b1, b4), n_totals 2 (b1, b3), H 1.6, D 4.1,
A 5.5, over 1.9, under 1.9 — exactly the hand means, the lay market, the 1.5/3.5 lines,
the alternate market, the partial and the 1.0-priced book all excluded; a lay-only event
and an event without a 2.5 line give None (fallback, labelled by the caller); an unknown
team name raises MissingInput; the live lambdas from the aggregated book equal
lambdas_from_odds on the hand means to 1e-12; all 20 short names in fpl.sqlite have an
API_TEAMS target. Readings noted, not defects: a date-only file name counts as 23:59:59,
so it outranks an explicit same-day stamp of the same day (both before the deadline); W1's
file layout is not on master yet (the implementer says so; list or dict under
events/data/response/odds).

### Check 5 — recording path — PASS

No runner file is in the amendment (fpl_edge.py, fpl_hist.py, fpl_nightly.py, fpl_sync.py,
fpl_gate.py, fpl_publish.py, fpl_ship.py, .github/workflows unchanged; nightly.yml names
nothing under tools/ or analysis/). My subprocess probe importing fpl_nightly, fpl_ship,
fpl_edge, fpl_sync, fpl_gate, fpl_publish and fpl_hist loads no module from tools/ or
analysis/ (empty list); the suite's test_cli_and_isolation does the same. The projection
log was not regenerated here (the runner is the only writer; `--record` is never run
locally); the data worktree is clean before and after every run (`git status` empty,
HEAD e8629f0), no odds/ folder was created, and tools/out/ is gitignored.

### Check 6 — mutation spot-check — PASS (12 of 13 red)

Scratch copy of the HEAD archive, one mutation at a time in tools/odds_lambda.py,
`python -m unittest tests.test_S5` after each (baseline 14 OK), module restored and
verified byte-equal afterwards (mutate.py / mutate.txt):
- V1 newest_snapshot accepts a file taken exactly at the deadline (`<=`): SURVIVED — a
  test gap, not a defect: my probe shows the code excludes the file at exactly 17:30:00
  (strict `<`), the tests hold no equality case.
- V2 deadline guard dropped: RED. V3 date-only stamp read as the start of the day: RED.
  V4 payload fetch-time fields ignored: RED. V5 h2h_lay counted: RED (2). V6 every totals
  line counted: RED (2). V7 h2h sums not divided by the count: RED (2). V8
  pre_deadline_export accepts a post-deadline export (first run's M8): RED. V9 condition
  starters threshold ignored (first run's M13): RED. V10 newest_snapshot picks the oldest:
  RED. V11 live ignores the snapshot it found: RED. V12 live takes the first deadline of
  all, not the first after now: RED. V13 a fixture absent from the snapshot labelled
  "odds": RED (2).
The first run's two condition-path survivors (M8, M13) now go red, as the ruling asked.

### Check 7 — secrets — PASS

grep over tools/odds_lambda.py, tests/test_S5.py, the four output files and the amendment's
CHANGELOG/worklog diff for `apiKey=`, `Authorization`, `ODDS_API_KEY`, `api_key`, `Bearer`,
`secret`, `token`, `http://`, `https://` and any 32+ character alphanumeric run: no match.

### Write guard

`git status --short` in C:\GIT\FPL-b after this report: only ` M worklog/verify_S5.md`
(this file; it was committed by the first run). C:\GIT\FPL-data clean.

VERDICT: FAIL

Reason: the ruling precedes the amendment code and its points 3-4 are implemented as
written — the pre-registered primary test and condition are untouched and reproduce byte
for byte, so the first run's PASS and numbers stand; the snapshot selection never takes a
file at or after the deadline (strict, a date-only name read as the end of its UTC day,
the payload's fetch time authoritative, an unstamped file stops the run), the aggregation
excludes h2h_lay, every non-2.5 totals line, alternate markets and partial books and
returns the hand means, the fallback is labelled on every fixture of the real run, no
runner file changed, 12 of 13 mutations go red including the first run's two survivors,
and no secrets appear. The amendment fails on reproduction of its own deliverable: the
plain command `python tools/odds_lambda.py --live --out <dir>` with stdout captured exits
1 with a UnicodeEncodeError on the squad line "Muharemović" (cp1252 on a redirected
Windows stdout), prints a traceback instead of a labelled stop and writes no
odds_lambda_live.txt; only with a UTF-8 stdout (PYTHONUTF8=1 or a console) is the file
produced, and then it is byte-identical. Because the Thursday deadline pass and any
Claude Code session run this command with captured output, and any non-cp1252 name
triggers it, the item is not done until `main` encodes its echo safely (or writes the
file first) and a test exercises `main(["--live", ...])` through a cp1252 stream; no
number, forecast or pre-registered result is affected, so a re-verification after that
one-line fix should only need checks 2, 3 and 6 on the live path.
