# Verifier report: S8c amendment 3, point 3 clarified (tests only)

Model: Fable 5.1 (claude-fable-5-1), effort high; the agent file
`.claude/agents/backtest-verifier.md` read from disk first (it matches the
loaded instructions). 2026-10-20.

Item: a test that every value in `xp_v2_all.csv` equals the value the
bundle's xp_v2 XI picker used (prereg `prereg/S8c.md`, section "## Amendment 3,
point 3 clarified", master `65d6797`). Delta reviewed: `git diff 93579dc
2ff26dd` on `s8c-wip` (worktree
`C:/Users/Boris/AppData/Local/Temp/claude/C--GIT-FPL/442a647f-7693-4ced-b840-0df7f5bfd943/scratchpad/s8c`).
Data: `C:\GIT\FPL-data` at `63e6a44` (pull --ff-only: already up to date;
`git status` empty before and after my runs). `ODDS_API_KEY` unset in every
command; no API call, no dispatch, no push. Scratch: `.../scratchpad/v8c_a3b/`.

## Prereg before code

- Prereg: master `65d6797`, committer time 2026-10-20T19:24:47+02:00. The
  verbatim ruling is in `prereg/S8c.md` line 238 ("Ruling, Tue 20 Oct night,
  point 3 clarified: ...") and the pinned test design above it (lines 229-236):
  the picker is `chips.xi_and_bench` via `side_by_side`, valuing
  `pts.get(id, 0.0)`; no code change; our 15 captured as the bundle ran, one
  made not forecast on the toy; every other export player through the picker;
  red when a not-forecast player is written at any other value.
- Test commit: `s8c-wip` `2ff26dd`, committer time 2026-10-20T19:25:58+02:00,
  71 s after the prereg. The prereg is on master, not an ancestor of the
  branch (the same pattern as amendment 3 itself: prereg master `6e7c918`,
  code `ea95cf6`); the ordering holds by committer time. PASS.

## (1) The diff touches tests only

`git diff --stat 93579dc 2ff26dd`: `tests/test_S8c.py | 48 ++++`, one file.
`git diff --stat 93579dc 2ff26dd -- tools/ fpl_*.py .github/` is empty. No
tool, no runner file, no workflow. The new code is a module helper
`CHt_newest` and `XpV2Csv.test_every_value_is_the_pickers`. PASS.

## (2) The picker's value for a not-forecast player, on the real data

Code at `2ff26dd`:
- `tools/chips.py:187-201` `xi_and_bench(squad, pts)`:
  `rows = [dict(r, proj=pts.get(r["id"], 0.0)) for r in squad]`, then
  `E._best_xi(rows)`, the sub keeper and the outfield bench sorted by
  `(-proj, id)`. A player missing from `pts` is valued 0.0.
- `tools/gw_pass.py:235-250` `side_by_side(squad, own_pts, v2_pts)` calls
  `CH.xi_and_bench([dict(r) for r in squad], v2_pts)`; section 5
  (`own_v_xp`, lines 355-389) calls it with `v2 = res["xp"]` from
  `XL.live(data_dir, hist_root, now)` and keeps the same `res` for the CSV
  (`keep["res"] = res`, line 384; `write_xp_v2_csv(args.out, keep["res"])`,
  line 449). `xp_v2_rows` (lines 268-285) writes `repr(float(xp[pid]))` for a
  forecast player and `repr(0.0), "", "not forecast"` otherwise.
- So the CSV's not-forecast value and the picker's are the same constant by
  construction; the prereg's claim ("used at 0.0, no code changes") holds.

Real run: `spy_real.py` (my scratch) imports `gw_pass` from a clean
`git archive 2ff26dd`, wraps `chips.xi_and_bench` to record every call's
`pts` and the `proj` of each returned row, wraps `write_xp_v2_csv` to catch the
`res` it received, and runs `G.main(["--data", C:/GIT/FPL-data, "--hist",
C:/GIT/FPL/historical, "--out", v8c_a3b/out])`. Output (`v8c_a3b/spy_real.txt`):
- rc 0; 27 `xi_and_bench` calls in the bundle; exactly 1 with
  `pts == res["xp"]`, and it is the identical object (section 5's xp_v2
  column). The other 26 are own-xP calls (chip values, the named plans,
  side_by_side's own column), none equal to the xp_v2 forecast.
- CSV: 668 rows = the export's `all_players`; 277 forecast, 391 not forecast.
- Our 15 (ids 109, 334, 8, 229, 173, 12, 427, 124, 183, 411, 249, 82, 230,
  106, 290): all 15 picker values equal the CSV's `xp_v2` string as
  `repr(float(v))`, e.g. Saka 6.048251108563258, Kelleher 3.499803329446343.
  Haaland 411: in our 15, not in `res["xp"]`, picker 0.0, CSV row
  `411,Haaland,MCI,FWD,0.0,,not forecast`; the print (gw8_pass.txt line 190)
  says "no xp_v2 for Haaland (0 in the choice ...)". Mismatches: 0.
- Every other export player (653): put in our 15 in place of a same-position
  player and valued by the same `xi_and_bench` on `res["xp"]`; CSV value and
  flag equal the picker's for all 653. Mismatches: 0. All 391 not-forecast
  rows are `0.0,,not forecast`.
- `run.txt` records `xp_v2_all.csv sha256 d8ba0bff...`, equal to the file's
  SHA and to the SHA the amendment-3 verifier recorded on the same data
  (`worklog/verify_S8c_a3.md`): the tool's output has not moved. (`commit:
  unknown (git unavailable)` in run.txt is because the archive is not a git
  repository; the data branch and `projection_log.csv` are unchanged.)
PASS.

## (3) The new test

`XpV2Csv.test_every_value_is_the_pickers` (tests/test_S8c.py, 44 lines):
- Captures the picker's own values in the bundle's run: `mock.patch.object(
  G.CH, "xi_and_bench", side_effect=spy)` around `self.main(self.out)`
  (= `G.main([...--out])`, the whole bundle through `main`, CSV included);
  the spy calls the real picker and records `(pts, {id: proj})`. It selects
  the call with `pts == res["xp"]` where `res = XL.live(self.tmp, self.hist,
  NOW9)` is the test's own copy of the forecast (the bundle's clock is pinned
  to `NOW9` by `FixedNow` in setUp), asserts the call exists and is on exactly
  our 15 (`set(used[0]) == set(mine)`), then asserts each of the 15 CSV
  `xp_v2` strings equals `repr(float(v))` of the picker's value.
- Covers a not-forecast squad member: the test sets one of our 15 (the first
  MID) to status "d" in the toy export, asserts he is not in `res["xp"]`, that
  the picker used 0.0 for him and that his flag is "not forecast". (setUp
  already makes a non-squad player injured, so "not forecast" is also hit
  outside the squad.)
- Every other export player through the same picker: for each `all_players`
  row not in `CH.my_squad`, a trial 15 with him in a same-position slot,
  `real(trial, res["xp"])`, and the CSV's value and flag compared to the
  picker's `proj` and to `pid not in res["xp"]`.
- Hermetic: toy folders from `tests/test_S6d` in `tempfile.mkdtemp()`, the
  clock and the selling budget mocked; no real data, no network.
- Note (not a defect): if some other `xi_and_bench` call ever used an equal
  dict, `used[0]` would be that call; it would still be the same picker on the
  same forecast, so the values asserted are unchanged. On the real data
  exactly one call matches.

Mutations of my own, each a scratch copy of the `2ff26dd` archive, the single
test run bare (`env -u FPL_DATA_DIR`):
1. `tools/gw_pass.py` not-forecast row written `repr(0.5)`: red,
   `AssertionError: '0.5' != '0.0'` at the our-15 loop. Catches a not-forecast
   value other than the picker's 0.0 (the ruling's "red when a not-forecast
   player is written at any other value").
2. `tools/gw_pass.py` forecast value `repr(round(float(xp[pid]), 2))`: red,
   `'5.57' != '5.5740618521972705'`. Catches any rounding or re-formatting of
   a forecast value; the CSV must round-trip the picker's float exactly.
3. `tools/chips.py` picker `pts.get(r["id"], 1.0)`: red, `'0.0' != '1.0'` at
   the our-15 loop. Catches a picker that treats a missing player at anything
   other than what the CSV writes; the test compares to what the picker
   actually used, not to a constant, so a future change to the picker's
   default would be flagged rather than silently diverging from the CSV.
4. `tools/gw_pass.py` flag text `"no forecast"`: red, `'no forecast' !=
   'not forecast'`. Catches the flag W3 keys on.
Unmutated: the test passes (in the 768-test suite below). PASS.

## (4) Clean-checkout suites (git archive, bare, `FPL_DATA_DIR` and `ODDS_API_KEY` unset)

- Before, `93579dc`: `Ran 767 tests in 284.540s  OK (skipped=10)`.
- After, `2ff26dd`: `Ran 768 tests in 292.533s  OK (skipped=10)`.
The +1 is the new test. (The caller's "767 OK before 93579dc" is the
amendment-3 count; 93579dc itself added no test, as confirmed.) PASS.

## (5) Secrets

`git show 2ff26dd:tests/test_S8c.py` scanned for `apikey`, `authorization`,
`bearer` (case-insensitive) and 32+ hex runs: none. `tools/` has no
`urlopen`/`urllib.request`/`http.client`/`requests` and no `ODDS_API_KEY`
reference; nothing in my outputs (`spy_real.txt`, `run.txt`, the CSV, the
print) holds a key-like string. PASS.

## Checks 1, 3 and 5 of the agent file

Not applicable: the item adds a test only; no forecast, feature or metric is
produced or changed; no runner or recording-path file is touched (diff
confirmed empty outside `tests/`), and the data worktree is unchanged after my
runs. The prereg pins no pass/fail metric; its acceptance test is the one
verified above.

VERDICT: PASS. The prereg (master 65d6797, with the clarified ruling verbatim and the test design pinned) precedes the only commit, 2ff26dd, which changes tests/test_S8c.py alone (no tool, runner or workflow file); the picker `chips.xi_and_bench` values a missing player at `pts.get(id, 0.0)` and section 5 passes the same `res["xp"]` to the picker and to the CSV writer, which my spy on the real data (63e6a44) confirms for all 668 rows - our 15 including Haaland (411, not forecast, picker 0.0 = CSV 0.0 "not forecast") and the 653 others through the same picker, with the CSV hash equal to the amendment-3 verifier's; the new test captures the picker's values in the bundle's own run through `main`, covers a not-forecast squad member and every other export player, and goes red under four mutations (0.5 for a not-forecast player, a rounded forecast, a picker default of 1.0, a changed flag); the clean suites are 767 -> 768 OK; no secrets.
