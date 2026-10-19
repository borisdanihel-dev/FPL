# Verifier report: S16 part 2, the 2026/27 calendar mapper (BUILD_PLAN.md Step 16, point 2)

- **Verifier:** backtest-verifier, read from `.claude/agents/backtest-verifier.md` on disk first (it matched the loaded instructions). Model **Fable 5.1**, effort **high**.
- **Item kind:** descriptive, offline tool under `tools/` (no pass/fail metric in the prereg). Checks 1, 2, 5, 6, 7 and the prereg's acceptance tests, plus the parking judgement the caller asked for.
- **Objects:** prereg `d813953:prereg/S16.md` (master); code `5dcead7` on `s16-wip` (parent `d813953`), adding `tools/calendar_2627.py` (146 lines) and `tests/test_S16.py` (155 lines), nothing else. `git ls-remote` shows `s16-wip` at `5dcead7` and `master` at `7aa568f` on GitHub, matching the local refs.
- **Where I worked:** two `git clone --no-hardlinks` copies of `C:\GIT\FPL` under the session scratchpad (`.../scratchpad/verify_S16/before` at `d813953`, `.../after` at `5dcead7`), a `.git`-free `tar` copy of `C:\GIT\FPL-data` (at `9da6ff1`) and copies of it, my own TZif generator for stand-in `Europe/London` and `Europe/Prague` zones exposed only through `PYTHONTZPATH`, and a `sitecustomize` clock shim. The real database was read only through a `mode=ro` URI; its sha256 (`a4ac...`) and `git status` in `C:\GIT\FPL-data` are unchanged. No push, fetch, ref, tag, hook or config change in any repository or worktree; no workflow dispatch; no Odds or FPL API call. The only file written in any repository is this one.

## Order and verbatim rulings: PASS

- `d813953` (prereg) committed 2026-10-19 01:34:09 +0200; `5dcead7` (code) committed 01:53:51 +0200 with `d813953` as its parent. The prereg precedes the first code commit.
- BUILD_PLAN.md Step 16 point 2: the prereg's copy equals `master:BUILD_PLAN.md` lines 579-583 (compared whitespace-normalised: equal).
- RULING lane A night work, item 3: equals the record in `master:worklog/SESSION_STATE_A.md` (equal).
- Boris's addition: equals the SESSION_STATE_A record after its lead-in; the prereg's quoted text begins "Addition to the night work: after Step 16 part 1 ...", SESSION_STATE_A quotes from "after Step 16 part 1 ...". The substantive text is identical. I cannot read the chat to say which lead-in is the verbatim one; noted as an observation, not a failure.
- No metric, filter, bootstrap or threshold exists in the prereg (all n/a), so nothing could be promoted or re-tuned after results; the branch holds one code commit of two new files.

## 1. Point-in-time leak check: n/a (PASS by scope)

The item produces no forecast, feature or evaluation metric, so 1a-1c do not apply. Its inputs are `events.deadline_time` (38 rows, the schedule as published in the data at `9da6ff1`) and `fixtures.kickoff_time` (380 rows, information only). The tool re-reads the database on every run, so a later rescheduling by FPL would re-map; the mapping in this report is the 18 Oct one.

## 2. Clean-checkout test runs: PASS

| run | before `d813953` | after `5dcead7` |
|---|---|---|
| bare (no `FPL_DATA_DIR`, no zones) | 459 OK (skipped=9) | 471 OK (skipped=9) |
| runner-like: `GITHUB_ACTIONS=true GITHUB_REF=refs/heads/s16-wip FPL_DRY_RUN=true`, `FPL_DATA_DIR` = own data copy, `PYTHONTZPATH` = stand-in zones | 459 OK, 0 skips | 471 OK, 0 skips |
| hermetic: `HOME`/`USERPROFILE`/`XDG_CONFIG_HOME` = empty folder, `GIT_CONFIG_NOSYSTEM=1`, empty `GIT_CONFIG_GLOBAL`, `TZ=Pacific/Kiritimati`, `LC_ALL=C`, no data, no zones | - | 471 OK (skipped=9); `tests.test_S16` alone 12 OK |

The after run's data copy was hashed file by file before and after the runner-like run: no file changed. 459 -> 471 = the 12 new tests, as claimed.

Stand-in zones: my generator (EU rules 1990-2037, transitions 01:00 UTC on the last Sundays of March and October) checked at 2026-10-17 21:40Z = 22:40 BST / 23:40 CEST, 2026-10-25 00:30Z = 01:30 BST and 01:30Z = 01:30 GMT, 2027-03-28 00:30Z = 00:30 GMT and 01:30Z = 02:30 BST.

## 3. Re-run of the pre-registered evaluation: n/a; acceptance tests verified

Acceptance tests of `prereg/S16.md`, each against the code, the tests, the real data and an independent recomputation:

1. **Window [deadline g, deadline g+1), GW38 open.** `window()` keeps `dl <= t`; `map_date()` takes deadlines `start < dl < end` as inside the day. Tests: 2027-06-01 -> GW38 with next `(None, None)`; mutations M1, M2, M11 red (below). PASS.
2. **UK calendar day by rule, no time-zone database.** `uk_offset()` codes BST from 01:00 UTC on the last Sunday of March to 01:00 UTC on the last Sunday of October; `uk_day()` derives the midnights. The tool imports no `zoneinfo` (grep). This Python (3.14.7) has no `tzdata` and raises `ZoneInfoNotFoundError` for `Europe/London`, and the tool still ran: it needs no database. 28 Mar 2027 and 25 Oct 2026 are Sundays (checked). The rule agrees with my own TZif zone at the five instants above; mutations M3, M4, M8 red. PASS.
3. **Mapping rules.** Independent recomputation with `zoneinfo` on my stand-in zone and the real deadlines: 21 Mar 2027 UK day [21 Mar 00:00Z, 22 Mar 00:00Z) holds no deadline, last deadline at or before it GW30 -> GW30; 3 Apr 2027 [2 Apr 23:00Z, 3 Apr 23:00Z) -> GW30; 24 Apr 2027 [23 Apr 23:00Z, 24 Apr 23:00Z) holds GW33's deadline 24 Apr 12:30Z, previous GW32 -> ambiguous 32/33; 22 May 2027 [21 May 23:00Z, 22 May 23:00Z) -> GW36. The tool's real-data output says the same and never picks a side ("GW32 or GW33 ... depends on the kickoff time, which the plan does not give"). 2026-08-01 raises `ValueError` (test; M6 red). A day holding GW1's deadline gives `between (None, 1)`. PASS.
4. **Output fields.** The real-data lines carry the gameweek or pair, both deadlines with hours, and the fixture count. Hours checked by hand: 10.5 / 468.5 (21 Mar), 321.5 / 157.5 (3 Apr), 154.5 / 13.5 (22 May); 24 Apr names GW33's deadline "Sat 24 Apr 13:30 UK". Fixture counts from the database: 0, 0, 10 (all ten 24 Apr 14:00Z, after the deadline, i.e. GW33's), 0. PASS.
5. **Tests.** 12 tests, hermetic (temporary database, deadlines frozen in the file, no zone database). The 38 frozen deadlines are identical to `events.deadline_time` in `fpl.sqlite` at `9da6ff1` (compared programmatically: 38 = 38, equal). Read-only open: the test proves the file's bytes are unchanged after `main()` and that `CREATE TABLE` raises on the connection; my real-data run left the sha256 unchanged and created no `-journal`/`-wal` file. Mutations: see check 6. PASS.
6. **Parking of parts 1, 3 and 4.** See "Parking judgement" below. PASS (honest).

Claim 3 (the four results on the 18 Oct data) is reproduced in full. Claim 4 (the year): the plan gives day and month only; the 2026/27 season runs from GW1's deadline 21 Aug 2026 to GW38's 30 May 2027, so March to May can only be 2027, and the 2026 readings fall before GW1 and would raise. The choice is the only consistent one; the tool and the prereg both state it. Sound.

Default path: `python tools/calendar_2627.py` with no argument reads `C:\GIT\FPL-data\fpl.sqlite` read-only; with a missing path it prints `no database at ...` and exits 1 without creating anything (test).

## 4. Metric, filter, bootstrap, threshold: n/a (PASS)

All n/a in the prereg; the rulings are present verbatim (see above); nothing promoted or re-tuned after results.

## 5. Recording path: PASS

Two copies of the data worktree (`rec_before`, `rec_after`), each with the working exports as checked out; a `sitecustomize` shim first on `PYTHONPATH` pinning `datetime.now()` to 2026-10-19T00:00:00Z (checked: the shim returns that instant); the nightly's own commands (`fpl_edge.py --record --source {own,xg,minutes,bottomup} --status`, `--watch`, `--diff --out`, `--stuck`) run from the `d813953` tree on one copy and from the `5dcead7` tree on the other. Both: `RECORD OK own 275, xg 260, minutes 260, bottomup 260`; `projection_log.csv` sha256 `b927...` on both, 6812 lines; `diff -r rec_before rec_after` empty. Ignoring carriage returns, the only difference from the original log is the 1055 appended rows (nothing removed or changed). The regenerated GW8 block equals the real 17 Oct 22:04Z nightly block exactly on (source, event, player_id, web_name, predicted), 1055 rows, which is the block the checked-out working export produced; the 18 Oct block (1077 rows) came from a later export and differs as expected. The runner path is untouched: the commit adds only the two files, neither exists on master, `nightly.yml` is unchanged, and `tests/test_S3.py::FastTrack::test_the_nightly_imports_nothing_under_tools_or_analysis` builds its forbidden set from `tools/*.py` at run time, so `calendar_2627` is covered; it passed in every run above.

## 6. Mutation spot-check: PASS

My own eleven mutations, each a byte-exact single replacement in `tools/calendar_2627.py` on a fresh copy (`tools/` + `tests/test_S16.py` + `tests/__init__.py`), `tests/test_S16.py` run by discovery:

| mutation | result |
|---|---|
| M1 window boundary `dl <= t` -> `dl < t` | FAILED (failures=1) |
| M2 inside boundary `start < dl` -> `start <= dl` | FAILED (errors=1) |
| M3 switch at 00:00 UTC instead of 01:00 | FAILED (failures=1) |
| M4 last Saturday instead of last Sunday | FAILED (failures=2) |
| M5 `?mode=ro` -> `?mode=rw` | FAILED (failures=1) |
| M6 no error before GW1 | FAILED (failures=1) |
| M7 Carabao date in 2026 | FAILED (errors=2) |
| M8 BST inverted | FAILED (failures=5, errors=1) |
| M9 fixtures not bounded by the day's start | FAILED (failures=2) |
| M10 ambiguous pair `(before, before)` | FAILED (failures=5) |
| M11 open end returns `(38, None)` | FAILED (failures=1) |
| control (unmutated) | 12 OK |

The implementer's scratch `mutate_s16.py` and `s16_mutations.txt` exist in the session scratchpad and record K1-K9 all red; I did not rerun them, my set above is independent and covers every rule in the prereg.

## 7. Secrets: PASS

`git show 5dcead7:tools/calendar_2627.py 5dcead7:tests/test_S16.py` grepped for `apikey=`, `api_key`, `authorization`, `bearer`, `token`, `secret`, `ODDS_API`, any 32+ character alphanumeric run and any `http(s)://`: no match. The files hold only a local path string and ISO timestamps. Nothing key-like to mask.

## Parking judgement (parts 1, 3, 4): honest

- `s16-wip` holds exactly two files, both part 2; no part is faked or stubbed.
- **Part 1** (history 2016/17-2025/26; its unit test needs 2024/25 and 2025/26): locally only `historical/2025-26/` exists (untracked in `C:\GIT\FPL`: `cleaned_players.csv`, `fixtures.csv` with 380 fixtures carrying `event` and scores, `merged_gw.csv`, `teams.csv`). A `find` over `C:\GIT\FPL` and `C:\GIT\FPL-data` for 2024-25 or 2016-17 folders finds nothing; `fpl.sqlite` `fixtures` holds 2026/27 only (kickoffs 2026-08-21 to 2027-05-30) and `player_history` is per-player season totals, not fixtures. The needed list (vaastav `fixtures.csv` for 2016-17 to 2024-25 plus each season's deadlines) is right; a download needs Boris under the night-work ruling, so parking part 1 and moving to part 2 followed the ruling.
- **Part 3** (cup Monte Carlo): no odds history, no Elo, no UEFA calendar, no free-midweek table anywhere local (`find` for uefa/elo/europ: nothing; `C:\GIT\FPL-data` at `9da6ff1` has no `odds/` folder, W1 being unmerged). One imprecision: "results to build Elo from ... neither is local" overstates slightly, since 2025/26 and 2026/27-to-date Premier League results are local; but a cup Elo needs cup results and lower-league clubs, which are not local, so the parking stands and the needed list is right.
- **Part 4** depends on part 3 and both seasons' cup draws and dates, none local: correctly parked.

## Observations (non-blocking)

1. The addition's lead-in differs between `prereg/S16.md` and `SESSION_STATE_A.md` (see "Order and verbatim rulings"); the ruling text itself is identical.
2. On 24 Apr 2027 all ten league fixtures kick off at 14:00Z, after GW33's 12:30Z deadline; the FA Cup semi-final's kickoff decides its gameweek and is not in the plan. The tool reports this correctly as information.
3. No CHANGELOG entry on `s16-wip` yet; by the protocol it follows the verifier. The item lands only after a green dry run of its landing branch (`dry/S16` under W1b); this verdict covers the code at `5dcead7`, not that dry run.
4. A plain `diff` of the regenerated log against the original flagged every line through line endings; ignoring carriage returns only the appended rows differ. Pre-existing `fpl_edge.py` behaviour, identical on both sides, not this item's.

VERDICT: PASS

The prereg `d813953` precedes the single code commit `5dcead7`, carries Step 16 point 2, the night-work item 3 and Boris's addition verbatim against their other recordings, and every acceptance test holds: the window, UK-day and mapping rules are coded as stated and agree with my independent zoneinfo recomputation on the real 18 Oct deadlines (21 Mar -> GW30, 3 Apr -> GW30, 24 Apr -> GW32 or GW33, 22 May -> GW36, fixtures 0/0/10/0); the 12 hermetic tests freeze deadlines identical to the database and pass bare, runner-like with stand-in zones and hermetically (459 -> 471); eleven independent mutations are all red; the database is provably untouched; the recording path is byte-identical before and after under a frozen clock and reproduces a real nightly block; the two files hold no secret; the runner imports nothing new; and parts 1, 3 and 4 are parked honestly with a correct list of missing inputs.
