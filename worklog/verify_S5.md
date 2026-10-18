# verify_S5 — backtest-verifier report

Item S5 in C:\GIT\FPL-b (branch lane-b). Three verifier runs, all on Fable 5.1
(claude-fable-5-1), effort high, as .claude/agents/backtest-verifier.md on disk (read first
each time; it matches the loaded instructions). No key-like string occurs in any file or
output examined (nothing to mask). The data worktree C:\GIT\FPL-data was read only (clean
before and after, HEAD e8629f0 "nightly 2026-10-18", no odds/ folder); nothing outside this
file was written in the repository. Scratch material under the session scratchpad
(fix/: before, after, head and mut archives, repro/, before_rep/).

## History

- **First run (code 01be62b, 2026-10-18) — PASS, 1c WARN cleared by 1a/1b.** Prereg
  f9ca3d0 and Amendment 1 (94fbc36) committed before the single code commit; truncation
  rebuild of GW5/20/38 differed by exactly 0.0 (1a PASS); every input dated before its
  deadline, only pre-closing Avg/B365 columns read (1b PASS); shift probe WARN for
  bottomup_lambda on DEF/GK starters (unshifted +0.2269; drop +0.1126 against the 0.10
  line, bottomup's own drop +0.0642), cleared by 1a and 1b as the rule allows; clean
  checkout 386 OK (8 skipped) before and after, tests.test_S5 10 OK; the three
  pre-registered outputs reproduced byte-identically (primary +0.0153 [+0.0098, +0.0214]
  n=34 PASS; Friday sensitivity +0.0162 [+0.0091, +0.0242]; condition mean +0.1375
  [+0.1282, +0.1469] n=2, power 142.6 gameweeks); metric, sample, bootstrap (B=10,000,
  90%, seed 20261018, paired by gameweek) and both bars exactly the prereg's; no runner
  file changed; 11 of 14 mutations red; no secrets. The chat accepted it ("RULING S5
  result", commit 4abc716).
- **Amendment run (RULING S5 result points 3-4; code fa05534) — FAIL on check 3 only.**
  Ruling 4abc716 (23:09:12) before code fa05534 (23:14:50); 1b PASS on the real live run
  (export generated 2026-10-18T18:45:03Z, fallback trained on 60 finished fixtures GW1-6,
  last kickoff 2026-10-12T19:00Z; snapshot selection strict `taken < deadline`, 13 of 13
  toy cases as wanted); clean checkout 386 OK (8 skipped), tests.test_S5 10 -> 14; the
  pre-registered --test, --condition and --fixture outputs byte-identical; the amendment
  diff additive (primary_test, condition_2627, constants, backtest.py untouched);
  aggregation probe exact (h2h_lay, 1.5/3.5 lines, alternate markets, partial books
  excluded); no runner file changed; 12 of 13 mutations red, including the first run's
  two condition-path survivors; no secrets. FAIL: `python tools/odds_lambda.py --live`
  run as a plain command with stdout captured exited 1 with `UnicodeEncodeError:
  'charmap' codec can't encode character '\u0107'` on the squad line "Muharemović"
  (cp1252 on a redirected Windows stdout) and wrote no file; with a UTF-8 stdout the file
  was byte-identical, so no number was affected.

## This run — amendment re-run after RULING S5 amendment fix (code 313bcb0)

### Ruling before code — PASS

`git log`: 9ea56c4 (prereg/S5.md, "Ruling on the amendment fix (verbatim)", 2026-10-18
23:30:01 +0200) precedes 313bcb0 (23:34:17), the only code commit of the fix; 3173026
(23:34:18) touches CHANGELOG.md and worklog/ only. `git diff 9ea56c4..HEAD --stat`:
tools/console_utf8.py (+17, new), tools/backtest.py (+3), tools/chips.py (+2),
tools/odds_lambda.py (+2), tests/test_S5.py (+80, -4: toy_2627 gains export_gw and rename,
class ConsoleEncoding with four tests), tests/test_S7.py (+4, -2: toy_export gains
rename), CHANGELOG.md, worklog/SESSION_STATE_B.md, worklog/cc_2026-10-18_S5.md. The
ruling text is present verbatim under "Ruling on the amendment fix (verbatim)".

Against the ruling, item by item: one shared helper under tools/ (console_utf8.py,
`utf8_console()`: `stream.reconfigure(encoding="utf-8")` on sys.stdout and sys.stderr
where the stream has `reconfigure`) — yes; called first in `main()` of all three tools
(odds_lambda.py:875, chips.py:667, backtest.py:862) — yes; every output file opened with
encoding="utf-8" explicitly — yes, the single `"w"` open of each tool (odds_lambda.py:917,
chips.py:691, backtest.py:901) and no other write path; a test per CLI in a subprocess
with PYTHONIOENCODING=cp1252 and PYTHONUTF8=0 on a toy holding "Ćaleta-Car", exit 0 and
the name byte-exact in the output file — yes for odds_lambda --live (toy keeper renamed,
`assertIn(NON_CP1252, text)` on the UTF-8-decoded file) and chips (toy sub keeper renamed,
printed by bench prep); backtest --report asserts exit 0 and a valid UTF-8 file holding
"REPORT 2025-26" only, because the report prints no player names — a deviation stated in
the test, the CHANGELOG and the report (noted below under check 6); the reconfigure
mutation goes red — confirmed by my own mutation M1; "seven gameweeks" corrected to six —
worklog/cc_2026-10-18_S5.md line 168-169 now reads "six gameweeks of results, 60
fixtures", and line 164 records the correction.

### Check 2 — clean-checkout test runs — PASS

`git archive` of each commit into an empty scratch folder (no historical/ data copy, no
FPL-data, FPL_DATA_DIR unset):
- before (9ea56c4): `python test_fpl.py` Ran 386, OK (skipped=8); `python -m unittest
  tests.test_S5` Ran 14, OK.
- after (313bcb0): 386 OK (skipped=8); tests.test_S5 Ran 18, OK.
- HEAD (3173026): 386 OK (skipped=8); tests.test_S5 Ran 18, OK.
Matches the implementer's counts (386 OK, 8 skipped; 14 -> 18). The four new tests are
ConsoleEncoding.test_helper_reconfigures_the_console, test_odds_lambda_live_on_cp1252,
test_chips_live_on_cp1252 and test_backtest_report_on_cp1252; the suite's
CLI.test_cli_and_isolation is among the 18 and green.

### Check 3 — reproduction through the harness, the way that crashed before — PASS

From C:\GIT\FPL-b with `PYTHONIOENCODING=cp1252 PYTHONUTF8=0` exported (a probe printed
`sys.stdout.encoding` = cp1252), each command a plain subprocess with stdout and stderr
redirected to files and my own `--out` (scratchpad fix/repro), the default `--data`
(C:\GIT\FPL-data at e8629f0) and `--hist`:
- `python tools/odds_lambda.py --live --out <scratch>`: rc 0, stderr empty, stdout 2291
  bytes = the file; `cmp` against tools/out/odds_lambda_live.txt silent (byte-identical,
  2291 bytes); the file and the captured stdout are valid UTF-8, hold non-ASCII and the
  name "Muharemović" that crashed the pre-fix run; "NO SNAPSHOT ... every fixture uses the
  time-decayed fallback (labelled)" in the header as before.
- `python tools/chips.py --out <scratch>` (defaults: N_SQUADS, RESAMPLES): rc 0, stderr
  empty; `cmp` against tools/out/chips_live.txt silent (3106 bytes); valid UTF-8 with
  non-ASCII.
- `python tools/backtest.py --report --out <scratch>`: rc 0, stderr empty; 4993 bytes,
  valid UTF-8, ASCII only. It differs from tools/out/report.txt (4865 bytes, written
  2026-10-18 17:09, before the 18:45 nightly) by exactly one appended line, "players
  dropped between snapshots (not graded on the older forecast): GW8 bottomup: 4, GW8
  minutes: 4, GW8 own: 4, GW8 xg: 4" — a data change (GW8 forecasts recorded by that
  nightly), not a code change: the pre-fix code at 9ea56c4 (archive, run with a UTF-8
  stdout) writes a report byte-identical to the fixed code's (`cmp` silent). The
  committed tools/out/report.txt is a stale, gitignored local artefact of S4; the
  implementer did not claim to regenerate it.
- The crash reproduced on the pre-fix archive: 9ea56c4's `odds_lambda.py --live` under
  the same cp1252 environment exits 1 with `UnicodeEncodeError: 'charmap' codec can't
  encode character '\u0107'`; the fixed code exits 0. So the fix is what changed the
  outcome, not the environment.
- Pre-registered outputs under the same cp1252 environment: `--season 2025-26 --test`,
  `--season 2026-27 --condition`, `--fixture ARS CHE`: rc 0 each and byte-identical to
  tools/out/odds_lambda_test_2025-26.txt (3670 bytes), odds_lambda_condition_2026-27.txt
  (1168) and odds_lambda_fixture_ARS_CHE.txt (106). The first run's numbers stand
  unchanged (primary +0.0153 [+0.0098, +0.0214]; condition +0.1375 [+0.1282, +0.1469]).

### Check 4 — pre-registered test and condition untouched — PASS

The fix diff in tools/odds_lambda.py is two lines (an import and the `utf8_console()`
call at the top of main); backtest.py three lines (a sys.path insert, an import, the
call); chips.py two lines. No model function, constant, metric, sample filter, bootstrap
setting or bar is in the diff, and the three pre-registered outputs reproduce byte for
byte. Nothing promoted, nothing re-tuned.

### Check 5 — recording path — PASS

`git diff 9ea56c4..HEAD --name-only` contains no runner file (nothing matching fpl_*,
test_fpl.py, p1_eval.py, hist_pit.py or .github/). .github/workflows/*.yml names nothing
under tools/ or analysis/ and nothing called console_utf8. My subprocess probe importing
fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish and fpl_hist from
C:\GIT\FPL-b loads no module from tools/ or analysis/ (empty list; console_utf8 not in
sys.modules); the suite's test_cli_and_isolation is green. The projection log was not
regenerated here (the runner is the only writer; `--record` is never run locally); the
data worktree is clean before and after every run (`git status` empty, HEAD e8629f0).

### Check 6 — mutation spot-check — PASS (6 of 8 red; the two survivors explained)

Scratch copy of the HEAD archive, one mutation at a time, `python -m unittest
tests.test_S5.ConsoleEncoding` after each (baseline 4 OK in 11.9 s), the file restored
after each (the copy equals the archive afterwards; `diff -r --strip-trailing-cr` clean —
my restore wrote LF where the archive has CRLF, a scratch artefact only):
- M1 helper: `reconfigure` dropped (`pass`): RED (3 failures — helper probe, odds_lambda
  live, chips live). This is the ruling's mutation.
- M2 helper: stdout left alone (stderr only): RED (3).
- M3 odds_lambda main: the call removed: RED (test_odds_lambda_live_on_cp1252).
- M4 chips main: the call removed: RED (test_chips_live_on_cp1252).
- M5 backtest main: the call removed: SURVIVED — expected and stated by the implementer:
  `--report` prints no player names, so its test can only assert exit 0 and valid UTF-8;
  with the call removed the ASCII-only report still exits 0. The helper itself and the
  wiring in the two tools that print names are covered (M1-M4); backtest's wiring is
  verified by reading (backtest.py:862 calls `utf8_console()` first in main) and by the
  fact that the three-line diff is identical in form to chips.py's, whose test goes red.
  A gap in the test, not in the fix.
- M6 odds_lambda output file written cp1252 (errors=replace): RED (byte-exact name).
- M7 chips output file written cp1252: RED (the test's UTF-8 decode errors).
- M8 helper: streams set to cp1252 with errors="replace" (no crash, the name mangled on
  stdout): RED (the helper probe asserts the name byte-exact on stdout).

### Check 7 — secrets — PASS

grep over tools/console_utf8.py, tools/backtest.py, tools/chips.py, tools/odds_lambda.py,
tests/test_S5.py, tests/test_S7.py and the fix's CHANGELOG/worklog diff for `apiKey=`,
`Authorization`, `ODDS_API_KEY`, `api_key`, `Bearer`, `secret`, `token`, `http://`,
`https://` and any 32+ character alphanumeric run: no match.

### Checks 1 — not re-run

The fix changes no input, feature, forecast or metric (checks 1a/1b stand from the
first run and the amendment run; 1c's WARN was cleared by 1a/1b and accepted by the
ruling on the result).

### Write guard

`git status --short` in C:\GIT\FPL-b after this report: only ` M worklog/verify_S5.md`
(this file). C:\GIT\FPL-data clean, no odds/ folder created, tools/out/ gitignored and
not written by me (my runs used `--out` under the scratchpad).

VERDICT: PASS

Reason: the ruling on the amendment fix (9ea56c4, 23:30:01) precedes its only code commit
(313bcb0, 23:34:17) and is implemented as written — one shared helper under tools/
reconfiguring stdout and stderr to UTF-8, called first in the main of all three tools,
every output file opened with encoding="utf-8", a cp1252 subprocess test per CLI on a toy
holding "Ćaleta-Car" with the name byte-exact in the file for the two tools that print
names (backtest's report prints none; its test asserts exit 0 and valid UTF-8, a stated
deviation), the report's "seven gameweeks" corrected to six. Run the way that failed
before — plain subprocesses with PYTHONIOENCODING=cp1252, PYTHONUTF8=0 and stdout
captured — `odds_lambda.py --live`, `chips.py` and `backtest.py --report` now exit 0 with
empty stderr, the two live files are byte-identical to tools/out/odds_lambda_live.txt and
chips_live.txt, the report is byte-identical to what the pre-fix code writes on today's
data (the committed copy is a stale local artefact from before the 18:45 nightly, one data
line shorter), and the pre-registered --test, --condition and --fixture outputs are
unchanged byte for byte; the same command on the pre-fix archive still crashes with the
UnicodeEncodeError, so the fix is what changed the outcome. Clean-checkout tests 386 OK
(8 skipped) before and after, test_S5 14 -> 18; the ruling's mutation (reconfigure
dropped) and five others go red, the only survivors being the stated backtest wiring gap;
no runner file changed and the nightly imports nothing under tools/; no secrets. The
amendment stands verified; per the ruling, S6 may continue.
