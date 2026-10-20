# Verifier: S2b after-measurement (worklog/cc_2026-10-20_S2b_after.md; data 63e6a44)

Written 2026-10-20, about 14:25 UTC, by the backtest-verifier agent. Model:
Fable 5.1 (claude-fable-5-1), effort high, as `.claude/agents/backtest-verifier.md`
says (read from disk first; it matched the loaded instructions). Ordered by the
Ruling of Tue 20 Oct evening, point 2 (verbatim in `prereg/S2b.md`, lines
105-114: "a Fable verifier on S2b's after-measurement ... it blocks nothing").
Data-pipeline form: the prereg's metric, bootstrap and threshold are n/a; the
checks are that what the report and the CHANGELOG entry say is true and
complete.

Nothing was written to `C:\GIT\FPL`, `C:\GIT\FPL-data` or any branch; nothing
dispatched; no FPL or Odds API call; `ODDS_API_KEY` is not set in this shell.
All reads of the data branch were `git -C C:\GIT\FPL-data show <commit>:<path>`
(after one `pull --ff-only`, "Already up to date") into the scratch folder
`scratchpad/v2b_after/`. The main session's materials under
`scratchpad/s2b_after/` were read only.

## What was verified against

- Master `0596125` at launch (the report and CHANGELOG entry were committed in
  `f61d267`, 2 files, +133; the evening ruling in `309e435`). `prereg/S2b.md`
  first committed in `f612a2c` (19 Oct 01:10 +02:00), before the first S2b
  code commit `19b303c` (01:38): PASS.
- Before = data `e1154dd` (19 Oct 22:05 UTC), after = `63e6a44` (20 Oct 13:01
  UTC), dry run = `origin/data-dryrun 4b199eb` (10:59 UTC). The main session's
  `before.sqlite` / `after.sqlite` hash to the two commits' blobs exactly
  (sha256 7aab..., aec4...).

## Check 1 - stored v final, reproduced independently: PASS (with three wording defects, below)

My own script (`v2b_after/v_measure.py`, every column of every table, not
only the ones `s2b_measure.py` tracks), run on the two committed databases:

- **entry_gw points, per gameweek and manager:** GW1, 2, 5: 0 of 7. GW3: 7 of 7
  (ReturnOfTheDjedi +9, Bruno +6, Skori +21, Kiripolcz +6, Rice Guy +16,
  Revelstoke +19, Pyro +18). GW4: 6 of 7 (+11, +8, +6, +2, +2, +11). GW6: 5 of 7
  (+2, +2, +1, +2, +6). GW7: 6 of 7 (+2, +13, +11, +9, +2, +2). Every number
  equals the report's table and `measure.txt`. The other entry_gw columns that
  moved in GW1-6: `total_points` 18, `overall_rank` 7 per gameweek (every
  gameweek, including GW1, 2, 5 - the standings re-ranked), `points_on_bench`
  4 + 5 + 4; `fetched_at_utc` on all 49 rows.
- **Our entry:** GW3 53 -> 59, GW4 58 -> 64, GW6 points_on_bench 11 -> 22,
  GW7 74 -> 83 (open), season total 451 -> 460: all as reported.
- **player_gw:** 0 rows new or gone in GW1-7; `total_points` unchanged in every
  gameweek; `bps` 10 / 4 / 1, `minutes` 2 (GW4 Willock 33 -> 32,
  Fernandez-Pardo 56 -> 57), `defensive_contribution` 5 / 3 / 3 in GW4 / 6 / 7:
  as reported. **Also moved, not in the report's list:** `expected_goals`
  8 / 8 / 7 and `expected_assists` 5 / 4 / 2 cells (GW4 / 6 / 7), plus
  `ruleset` NULL -> '2026-27' and `fetched_at_utc` on every re-fetched GW1-6
  row (the rehearsal report had listed xG 16 and xA 9; `s2b_measure.py` only
  tracks bonus, bps, minutes, dc).
- **picks:** 105 rows a gameweek, none new or gone; multiplier/position cells
  changed GW3 Pyro 7; GW4 Kiripolcz 2, Pyro 4; GW6 Revelstoke 7, Rice Guy 11,
  Pyro 4 (the three rivals in the S9 table); GW7 Bruno 8, Skori 9, Pyro 4.
- **automatic_subs:** 0 -> 18 rows (GW1-7: 1, 2, 1, 3, 3, 4, 4), the same
  (entry, in, out) triples as `measure.txt`.
- **First sight and fetch times:** `data_checked_seen_utc` = 13:00:50 on GW1-6
  (one distinct value) and NULL on the other 32 events; `player_gw` fetched
  13:00:51-13:00:54, `entry_gw` and `picks` 13:00:57-**13:01:33**; 0 rows of
  any table fetched at or before their event's first sight; 0 NULL. The
  report's "13:00:51-13:01:22" is wrong at the top: 13:01:22 is our own GW7
  entry row; PyroNeniZlocin's rows are at 13:01:29-13:01:33. Finality is not
  affected (every time is later than 13:00:50).
- **Rehearsal and dry run:** GW1-6 entry_gw, player_gw and automatic_subs lines
  of `measure.txt` are text-identical to `s2b_measure_preview.txt`. Against
  `4b199eb`: 0 differing cells in entry_gw, player_gw and picks for GW1-7 on
  every column but the fetch time (GW7 entry_gw differs only because the dry
  run was fetched before Monday's result landed), and the same 14
  (entry, event, in, out) automatic_subs rows for GW1-6.
- **GW7 is the open gameweek's move:** fixtures `finished` 0 of 10 at
  `e1154dd`, 10 of 10 at `63e6a44`; `data_checked` 0, first sight NULL in both.
  Under the old rule (finished = 0) and the new one (seen NULL) alike GW7 is
  re-fetched every night. The report's "its last match finished between the two
  fetches" is loose - all ten flipped to finished together - but the claim
  that this is the normal re-fetch, not S2b's, holds.

## Check 2 - the run's log and status: PASS

`logs/run_2026-10-20.log` (1,884 lines, started 12:59:28 UTC; `status.txt`
generated 13:01:35Z): `SYNC STATS` lists **73 calls, 73 x HTTP 200**
(1 bootstrap, 1 fixtures, 7 live, 1 standings, 7 history, 7 transfers, 49
picks) against 25 on 19 Oct (1 live, 7 picks): 48 extra = 6 live + 42 picks.
Lines 1282-1283 `+ events.data_checked_seen_utc`, `+ picks.fetched_at_utc`.
`Ran 708 tests ... OK (skipped=12)`, `TESTS OK`. `STATUS OK | ... checks
29/29`. Check 22: `OK manager score reconciliation: 42 entry-gameweeks in
GW1-GW6, every one equal; GW7 not locked down: silent mid-gameweek (ruling S3,
point 6)` (before, at `e1154dd`: `SKIP`). RECORD own 277, xg 257, minutes 257,
bottomup 257, fpl_ep 668, each "3 days, 4:28 before deadline"; check 18 the
same growth, 19 "0 duplicate keys", 20 "0 of 9204 rows at or after their
deadline". `projection_log.csv`: the 19 Oct file (383,168 bytes, 7,489 lines)
is a byte-prefix of the 20 Oct file (470,968 bytes, 9,205 lines); the 1,716
new rows are all GW8, made_at 13:01:33-34Z. Odds: 20 events, 480 credits
left. The log does not print the master commit; `4531cdd` (12:05 UTC) was
master's tip at 12:59 UTC and `684cd3f` came at 13:04 UTC, so "master
4531cdd" is consistent but not provable from the log.

## Check 3 - the re-runs: PASS; the list of earlier results is not complete (below)

- **Design:** my `git archive e1154dd` is byte-identical to the main session's
  `data_before` (`diff -rq` empty), and its `data_after` is that folder with
  only `fpl.sqlite` replaced by `63e6a44`'s (`diff -rq` empty against mine).
  Same exports, same log (the archive's `projection_log.csv` is the blob with
  CRLF from `git archive`; stripped, the same sha256). `tools/`, `fpl_edge.py`
  and `fpl_xpv2.py` are unchanged from `684cd3f` to `0596125`; the five tools
  contain no network code; every `run.txt` names commit `684cd3f`, 0 modified
  tracked files.
- **The main session's 28 logs** all end normally; 12 of 14 pairs are
  byte-identical, `league.log` and `s6c.log` differ exactly as the report says
  (18 WARN lines gone; three rival rows; the GW7 "0 of 10" -> "10 of 10"
  line and the output path).
- **My own re-runs** from master (`--data` my folders, `--out` my scratch, exit
  0 each, before and after): `tools/league.py`, `tools/odds_lambda.py --season
  2026-27 --condition`, `tools/backtest.py --compare own xg --season 2026-27
  --filter all`, `tools/xp_v2_replay.py --s6c`. After path normalisation every
  one matches the main session's output line for line, before and after; so
  S5 +0.1375 [+0.1282, +0.1469] n = 2 and the S4 compare are identical, S9
  moves as tabled.
- **Beyond the report, run by me:** `tools/chips.py` (S7, "residuals by
  position (2026/27 own, GW4-6)"): identical before and after.
  `fpl_edge.py --section calibration` on working exports built by hand (gw3-6
  newest dated copies; gw7 = the 19 Oct export, then the run's 20 Oct export):
  identical except the GW7 "REFUSED" block's ten `finished = 0` fixture lines,
  which drop out; every GW4-6 grade and rho is the same. `tools/xp_v2_live.py`
  (S6d) on the 19 Oct against the 20 Oct export (the latter carries the
  re-fetched GW4/GW6 bps, defcon, xG, xA cells in `player_gw_recent`: 13
  (event, column) groups changed, 0 rows added): 20 of the top 25 xp_v2 values
  move, max |move| 0.03 (Saka 6.02 -> 6.04; Mukiele/Murillo and
  Odegaard/Muharemovic swap rank).
- **Completeness of the list** (readers of entry_gw, picks, automatic_subs,
  player_gw minutes/defcon/bps/xG/xA with a recorded 2026/27 result): S9,
  S4, S5, S6, S6c, the calibration lines and p1_eval are in the report. Not
  in it: **S6d** (CHANGELOG 3870, GW8 from `fpl_export_gw7_2026-10-19`; moves
  by up to 0.03 xP, information only, regenerated by every bundle run) and
  **S7** (identical). `tools/gw_pass.py` reads the moved tables but has no
  recorded output on master yet (the bundle runs Thursday); `tools/minutes_v2.py`
  reads player_gw minutes/starts and the two GW4 minute changes cross no
  gate (not re-run).

## Check 4 - numbers quoted in the report and the CHANGELOG entry: one wrong, one wrong

- Rival table: all twelve numbers (28.0 -> 30.9, 2 -> 1, +3.5 -> +0.7,
  0.575 -> 0.508; 24.6 -> 27.5, 2 -> 1, +7.0 -> +4.1, 0.500 -> 0.431;
  14.5 -> 16.4, 5 -> 4, +17.1 -> +15.2, 0.925 -> 0.907) are in my
  `league.log` diff. Pooled sigma_d 18.03 [10.45, 20.31], our sigma 13.76,
  line 102.0: in both before and after. automatic_subs 0 -> 18: yes. Tests
  687 -> 708: 687 discovered at `5c90e08` (= `ce357fb^1`, `pre-S2b`), 708 at
  `ce357fb` and at HEAD.
- **CHANGELOG "P(above) moves by -0.067 to -0.018": wrong.** The three moves
  are -0.067 (Rice Guy), **-0.069** (Revelstoke, 0.500 -> 0.431) and -0.018
  (Pyro); the range is -0.069 to -0.018. The report's per-rival table is
  right; the summary range in the frozen entry omits the largest move.
- **Report "(13:00:51-13:01:22)": wrong** at the upper bound (13:01:33, above).

## Check 5 - secrets: PASS

The report, the CHANGELOG entry, `measure.txt`, `run_tools.sh`, all 28 tool
logs and 10 `run.txt` files, `status.txt` and the run log, searched for
`apiKey=`, `api_key=`, `Authorization`, `Bearer `, 32+ hex characters: only
the commit SHA `684c...` and the sha256 lines of the tools' own outputs. No
key, no URL with a key, no header value.

## Clean-checkout suite (agent-file check 2): PASS

`git archive HEAD` (`0596125`) into scratch, `python -m unittest discover -p
"test*.py" -s . -t .`, Python 3.14, no `FPL_DATA_DIR`, `ODDS_API_KEY` /
`GH_TOKEN` / `GITHUB_TOKEN` removed: **Ran 708 tests ... OK (skipped=10)**,
exit 0, 0 FAIL/ERROR lines. The item itself changes no code (2 files: the
report and CHANGELOG), so before = after.

## Write guard

`C:\GIT\FPL`: `?? worklog/verify_W1b_pre.md` only (there at launch).
`C:\GIT\FPL-data`: `63e6a44`, clean, `fpl.sqlite` sha256 aec4... unchanged.
The s2b worktree (`434df0b`, `s2b-wip`): clean at launch; after this run only
`?? worklog/verify_S2b_after.md`.

VERDICT: WARN

Reason: the measurement itself is true and reproduces to the number from the
two committed databases (every entry_gw move, our entry's 53 -> 59, 58 -> 64,
bench 11 -> 22 and 451 -> 460, total_points unchanged, 18 automatic_subs rows,
first sight 13:00:50 with every row fetched after it, GW1-6 equal to the
rehearsal and the dry run, GW7 the open gameweek's), the run was clean (73 x
HTTP 200, STATUS OK 29/29, check 22 OK 42, the log a byte-prefix plus 1,716
GW8 rows), and the before/after re-runs isolate the database and give the
identical / moved verdicts the report states, with my own S9, S5, S4, S6c and
S7 runs matching line for line; but the frozen CHANGELOG entry's P(above) range
"-0.067 to -0.018" omits the largest move (Revelstoke -0.069), the report's
fetch-time range ends at 13:01:22 instead of 13:01:33, its "other player_gw
columns that moved" omits expected_goals and expected_assists, and its list of
earlier recorded results omits S6d (which moves by up to 0.03 xP on the
re-fetched export) and S7 (identical). None of this changes a rule or a
decision; an amending CHANGELOG line with the corrected range, the two
omissions and the S6d/S7 lines would clear the WARN.
