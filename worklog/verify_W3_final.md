# verify_W3_final — the W3 landing (master `47ac1ea`) and its two real runs of Thu 12 Nov 2026

**VERDICT: FAIL — on check 4 only (a ruling is not on file). Every code and data check passes.**

- **What fails:** the landing happened on Wed 11 Nov. `prereg/W3.md` (amendment 3) says
  "W3 merges Sat 7 Nov after the GW10 deadline, via `dry/W3`". The text that moved it, and
  the plan item quoted at my launch ("W3 merge (with the +02:00 committer test, the
  fetch-depth comment and the captain-without-row test); Boris clicks the real run"), are
  in no file under `prereg/`, nor in `BUILD_PLAN.md`, `CHANGELOG.md` or
  `worklog/SESSION_STATE_A.md` at `47ac1ea`, nor on any other branch. My instructions say a
  ruling that is not in the prereg is a FAIL of check 4, and that an agent's message is not
  Boris's word. It is a gap in the record, not a defect in the code or the data.
- **What cures it:** Boris's text for the 11 Nov landing pasted verbatim into
  `prereg/W3.md`, marked as recorded after the fact. No code changes; nothing below needs
  to be redone.
- **What passes:** the merged code is the verified code; both real runs ran `47ac1ea`
  and were real; the xp_v2 rows and all six other sources reproduce exactly; the W3
  report sections reproduce byte for byte and agree with my independent recomputation;
  point-in-time holds; nothing regressed against `6ca6cd5`; no secret.
- **Three notes for the chat** (section "Decisions for the chat"): the one-run export lag
  now also governs CAPTAIN and BAN RISK (ruled only for CHIPS); a false "FH candidate"
  flag in the CHIPS section of tonight's report (W2 code, not W3); a two-run day replaces
  the first run's rows and archive.

Verifier: Claude Code, model Fable 5.2 (`claude-fable-5-2`). Fable was available; no
fallback. Effort: the agent file says high; the run's configuration shows a numeric
reasoning-effort value of 30, which I cannot map to the named level with certainty.
`.claude/agents/backtest-verifier.md` was read from disk first and again on resume; it
matches my loaded instructions.

**The first attempt stopped on an API connection error before writing anything.** This
report comes from the resumed run, which reused the same scratch folder (intact: every
copy, script and result below was made in this session). `git status` in `C:\GIT\FPL` and
`C:\GIT\FPL-data` was empty before this file was written; `HEAD` = `origin/master` =
`47ac1ea`, data `6f9ecb8`.

How I worked: read-only. Code and data copies by `git archive` / `git show` into
`...\scratchpad\vfy_w3_final` (`code` 47ac1ea, `code62` 62bda73, `codepre` b44e796;
`d_6ca`, `d_dry`, `d_2e0`, `d_6f9` for the four data commits). No git command that writes;
`git ls-remote` and two unauthenticated GETs of the public Actions API were the only
network calls. No `fpl_sync.py`, no `--record`, no `fpl_nightly.py` except `--restore` on
a scratch copy. `ODDS_API_KEY` unset in every command. Data files opened only by Python
with `-I`. `C:\GIT\FPL-b` not touched.

## Gate: prereg before code — PASS (by committer time)

| prereg commit (master) | time | first code it governs (w3-wip) | time |
|---|---|---|---|
| `ccb5882` W3 | 19 Oct 21:30:36 +02 | `66ae89a` | 22:09:28 |
| `0596125` amendment 1 | 20 Oct 16:02:56 | `aea1f42` | 16:15:17 |
| `6e7c918` amendment 2 | 20 Oct 18:30:34 | `bbe770a` | 18:41:24 |
| `0be8309` amendment 3 | 3 Nov 22:42:58 +01 | `43a174f` | 22:51:34 |
| `16aa4ed` amendment 3 follow-up | 3 Nov 23:05:18 | `aa07818` | 23:06:03 |

The last two are ancestors of their code commits. The first three are on master while the
code is on the branch, so the order rests on committer times (the author's clock), as the
earlier W3 verifiers accepted. `prereg/W3.md` gained 3 lines after `62bda73` (`7f6ec4b`,
a correction appended under the note it corrects); nothing earlier was edited.

## Check 4 — rulings on file: FAIL (record only)

- On file, verbatim, in `prereg/W3.md`: F-B; RULING 19 Oct evening; Ruling Mon 19 Oct;
  Ruling Tue 20 Oct; Tue 20 Oct evening; Tue 20 Oct night and its point 3 clarified;
  Wednesday 21 Oct; Rulings Tue 3 Nov night. The merge rule is `prereg/S2.md` point 6.
- The three additions named in the plan item are each pinned in amendment 3, so their
  content is covered.
- Not on file: the plan item itself, and anything that moves the landing from Sat 7 Nov
  to Wed 11 Nov. The state file (last commit `5e9f480`, Fri 6 Nov) still says "W3 Sat
  7 Nov; S8c, with point 5, Sun 8 Nov".
- No metric, filter, bootstrap or threshold exists for W3 (a wiring item), so nothing was
  promoted or re-tuned.

## g. The merged code is the verified code — PASS

- `47ac1ea` has parents `62bda73` (first) and `b44e796`.
- `git diff --name-only 62bda73 47ac1ea` outside `prereg/`, `worklog/`, `CHANGELOG.md`: 0
  files. The 97 other blobs hash to the same list at both commits. What differs: 3 prereg
  files (+29 lines, appended) and 11 worklog files.
- `62bda73` over the verified `aa07818`: `CHANGELOG.md`, `worklog/cc_2026-11-03_W3_a3.md`,
  `worklog/verify_W3_a3.md` only.
- Tag `pre-W3` (annotated, `7c4f29f`) points at `b44e796`, locally and on the remote.
- The three plan additions are where claimed and ran `ok` in both real runs
  (`logs/run_2026-11-12.log`):

| addition | place at `47ac1ea` | log lines (run 1, run 2) |
|---|---|---|
| `test_a_committer_date_at_plus_02_00_is_read_as_its_instant` | `tests/test_W3.py:732` | 1401-1402, 3933-3934 |
| the comment over `fetch-depth: 0` (cites amendment 2) | `.github/workflows/nightly.yml:84-85` (the key at 87-88) | held by `test_the_nightly_checks_out_the_history`: 1410, 3942 |
| `test_captain_with_no_player_gw_row_counts_as_0_minutes` | `tests/test_W2fix.py:88` | 1393-1394, 3925-3926 |

- Merge rule (S2 point 6), times in UTC on 11 Nov from the reflogs: `dry/W3` pushed
  11:36:53; dry run started 11:37:08, committed `64a58c8` 11:39:16; read back 11:39:53;
  tag 11:41:54; master pushed 11:41:56 (the launch says 11:41:58). Outside the freezes:
  the previous nightly ended 01:29 UTC; the GW11 deadline is 21 Nov 11:00 UTC.
  (b) the pre-check is `worklog/verify_W3_a3.md`, PASS. Boris's one real dispatch is run 2.
- Note: the read-back and the master push are 2 min 03 s apart, and the dry run had
  skipped CAPTAIN (below). CAPTAIN first ran on the runner in run 2, after the merge.

## a. Which code ran, and that both runs were real — PASS

- GitHub's run objects (public API, read with `-I`):

| run | event | branch | head_sha | started | conclusion |
|---|---|---|---|---|---|
| 43141722407 | `schedule` | master | `47ac1ea...` | 02:29:03Z | success |
| 43272346801 | `workflow_dispatch` | master | `47ac1ea...` | 17:42:58Z | success |

- `git ls-remote`: master is still `47ac1ea`; data `6f9ecb8`.
- Each log section: `Ran 787 tests`, `OK (skipped=13)`; the 11 Nov nightly on pre-W3 code
  ran 755. The 32 new tests are 28 in `tests.test_W3`, 1 in `test_W2fix`, 2 in `test_fpl`,
  1 in `test_W2`.
- Real, not dry: the data commits are `nightly 2026-11-12 [skip ci]` by
  `github-actions[bot]`, on `data`, parents `6ca6cd5` -> `2e0b948` -> `6f9ecb8`; the status
  went to `reports/status.txt`; the Odds API answered (`credits used 48, remaining 452`,
  then `52`, `448`; a dry run has no key).
- Not checked: the `dry_run` input of run 2 is not in the run object; the above stands in
  for it.

## b. Status, and nothing regressed against `6ca6cd5` — PASS

| | 11 Nov nightly `6ca6cd5` | run 1 `2e0b948` | run 2 `6f9ecb8` |
|---|---|---|---|
| status | WARN 29/30 | WARN 28/30 | WARN 29/30 |
| check 17 | WARN, gap 2026-11-05 | the same | the same |
| check 31 | OK (CHIPS 34, LEAGUE 58) | WARN, CAPTAIN SKIPPED | OK, five sections |
| tests (28) | 755 | 787 | 787 |
| own / xg, minutes, bottomup, bottomup_lambda / fpl_ep | 301 / 279 / 672 | 300 / 278 / 672 | 299 / 277 / 672 |
| xp_v2 | none | 300 | 299 |
| duplicate keys (19) | 0 | 0 | 0 |
| rows at or after the deadline (20) | 0 of 53043 | 0 of 55427 | 0 of 55421 |
| secret check (23) | OK, 7 files | OK | OK |
| price-history rows | 41281 | 41953 (+672) | 41953 (+0, same London day) |

- Every other check is OK in all three; check 27 is the standing SKIP.
- My own count of the logs agrees: `2e0b948` = the `6ca6cd5` log byte for byte plus 2384
  rows; `6f9ecb8` = the same prefix plus 2378 rows. All new rows are event 11. Duplicate
  natural keys: 0 in each.
- The row counts fall by one a run because one player a run lost status `a`: Strand
  Larsen (CRY) `a` -> `d` before run 1, Manzambi (AVL) `a` -> `d` before run 2. No other
  status changed.
- `fpl.sqlite`: integrity ok; 14 tables, the same row counts except `price_history`;
  `fixtures` has 13 columns with `finished_provisional` last, 0 NULL of 380 (100 are 1,
  all also finished). The `+ fixtures.finished_provisional` migration line appears in run
  1's sync and not in run 2's.
- The base report is unchanged in shape: 605 lines at `6ca6cd5`, 626 in run 1 (+21, the
  three W3 sections with CAPTAIN as one line), 646 in run 2.

## c. The first-night explanation — PASS (confirmed from the archives)

- `fpl_nightly.py` runs `fpl_sections.py` before "archiving the export". The sections read
  `fpl_chips.newest_export`, the newest dated file under `exports/`. The record reads the
  working export just written by the sync, which is why run 1 recorded xp_v2 (300 rows,
  "482 players keyed by code") and still skipped CAPTAIN.
- Players with a `code` key in `all_players`:

| archive | at commit | generated | with `code` |
|---|---|---|---|
| `fpl_export_gw10_2026-11-11.json.gz` | `6ca6cd5`, `2e0b948` | 11 Nov 01:29:39Z (pre-W3 code) | 0 of 672 |
| `fpl_export_gw10_2026-11-12.json.gz` | `2e0b948` (run 1's) | 12 Nov 02:31:50Z | 672 of 672 |
| the same name | `6f9ecb8` (run 2's) | 12 Nov 17:45:51Z | 672 of 672 |

- Reconstruction: with the exports as run 1's sections saw them (newest = 11-11), the W3
  code gives `CAPTAIN SKIPPED: the export's all_players has no code (the prior's key)`
  and the whole appended block equals run 1's report (9531 characters). With run 1's
  archive in place it prints the table. With the exports as run 2's sections saw them
  (run 1's archive), the block equals run 2's report (10904 characters).

## d. The W3 sections in `reports/fpl_2026-11-12.txt` at `6f9ecb8` — PASS

**The sections as a whole.** CHIPS, LEAGUE, CAPTAIN, BAN RISK and REALISED rebuilt on my
copy from run 2's database, log and odds with run 1's archive: identical to the report,
character for character.

**CAPTAIN** (lines 609-630; prereg (2)).
- The table against the offline tool (`tools/xp_v2_live.live` + `tools/points_pmf`, which
  read the historical files and the database, not the prior file): all 13 rows match in
  mean, P>=10, P>=15 and p90. Runner v tool on the same inputs: `==` on every float, the
  detail and the pmf summaries.
- Against the xp_v2 rows run 2 recorded for GW11: the 13 printed means equal the logged
  values within 0.004 (2-place print v 3-place log). Gabriel 5.62 v 5.621, Haaland 5.59 v
  5.590, Groß 5.30 v 5.303. |pmf mean - xp_v2| is at most 4e-13.
- Thiago (status `s`) and Thomas (`d`) print "no xp_v2 forecast"; neither has a logged
  row. Correct: the gate is status `a`.
- Captain Gabriel, the highest xp_v2 in the XI. Haaland is 0.030 behind, so he is the one
  option within 0.3. The header names the export and the odds snapshot (`1745Z`).

**BAN RISK** (lines 633-637; prereg (2), amendment 1 (B)), from SQL on `fpl.sqlite`:

| | cautions | minutes | club matches counted | position pooled rate | rate90 | P(start) | P(ban) |
|---|---|---|---|---|---|---|---|
| Groß (BHA, MID) | 4 | 880 | 10, next is the 11th | 0.2049 (193 yellows / 84788 min) | 0.3498 -> 0.350 | 1.00 | 0.350 |
| Thiago (BRE, FWD) | 4 | 824 | 10, next is the 11th | 0.1752 (36 / 18488) | 0.3573 -> 0.357 | 0.00 | 0.000 |

- Nobody else of the 15 is on 4 or 9 (Rogers 3; the rest 0-2).
- Thiago's P(start) is 0 because the export has him suspended (status `s`); on 6 Nov the
  same line gave 0.365.
- No fixture before the deadline is provisional only (100 finished), so no label is due.

**REALISED** (lines 640-646; prereg (3), amendment 2), with my own XI picker (all 1365
elevens), autosubs and doubling:

| GW | locked down | own | xp_v2 |
|---|---|---|---|
| 8 | yes | 41, captain Haaland, snapshot 2026-10-23T14:22:52Z | 41, captain Haaland, from the bundle CSV |
| 9 | yes | 72, captain Haaland, snapshot 2026-10-30 | no rows in the log |
| 10 | yes | 62, captain Gabriel, snapshot 2026-11-06 | no rows in the log |

- All equal the report. Total over 1 gameweek with both: own 41, xp_v2 41, +0.
- The bundle: `6034baa` is the newest of 3 commits touching
  `worklog/gw_pass/gw8/xp_v2_all.csv`. Committer time 14:26:29 UTC and `run.txt` end
  14:26:18 UTC, both before the 17:30 UTC deadline; the CSV's SHA-256 is the one
  `run.txt` records; tools commit `d9071b8`; all 15 picks are in the CSV. The label is
  right.
- No starter of either XI was on 0 minutes in GW8-10, so the autosub rule was not
  exercised by these numbers.

## Check 1 / e. Point-in-time — PASS

- **1a, rebuild.** GW11 is the only gameweek with xp_v2 output and it is not played yet,
  so "three gameweeks" reduces to GW11, done for both runs. From the archived export, the
  odds snapshot and the prior file alone I get run 1's 300 rows and run 2's 299 rows:
  same order, ids, names and value strings. The offline tool, by its different input
  route, agrees on every row after rounding (max |tool - logged| 0.000499).
- **1a, poison.** Added to a copy of the inputs: 1344 player rows of GW11 and GW12 (90
  minutes, 25 points), ten GW11 results of 9-0, and an odds snapshot stamped one minute
  after the deadline with every price tripled. The forecast is unchanged, `==` on every
  value, both runs. Control: xG +3 on the GW10 rows moves 277 of 299 values.
- **1b, timestamps.** Every xp_v2 row is event 11: run 1 `made_at` 02:31:54Z, run 2
  17:45:55Z, the dry run 11 Nov 11:39:06Z, all before 21 Nov 11:00Z. Exports generated
  02:31:50Z and 17:45:51Z; `player_gw_recent` events 1-10, none >= 11; `fixtures_played`
  100 results, last kickoff 8 Nov 16:30Z; odds snapshots `0231Z` and `1745Z`. The prior is
  season 2025-26 and its three recorded input hashes equal my local historical files.
- **1c:** not applicable; W3 prints no correlation.
- **The dated archive is a byte copy of the working export** (`archive_export_gz`), which
  is what makes the rebuild exact.

## Check 5 / e. The recording path did not move — PASS

- With the pre-W3 code (`b44e796`) and with `47ac1ea`, in process, the log writer replaced
  by a capture (nothing written, `--record` not run), on each run's archived export and
  odds folder: own, xg, minutes, bottomup, fpl_ep and bottomup_lambda are identical to
  the logged rows for both runs. That is every row, not a sample: 2084 in run 1, 2079 in
  run 2, compared as (event, id, name, value string) in order.
- `fpl_edge.py` changed by +13 lines, the xp_v2 branch only. The W2 modules
  (`fpl_chips`, `fpl_league`, `fpl_bt`, `fpl_pit`, `fpl_lambda`) are untouched.
- Rows of earlier days are byte-identical (the prefix above).

## Check 2. Tests on a clean extract — PASS

| tree | bare | with data and `historical/` |
|---|---|---|
| `b44e796` (before) | Ran 755, OK (skipped=10) | not run |
| `47ac1ea` (after) | Ran 787, OK (skipped=11) | Ran 787, OK (skipped=2) |

- Windows, Python 3.14.7; the runner is 3.14.10 on Linux. The two remaining skips are "no
  time-zone database here".
- `tools/make_prior.py --check`: the committed prior file is identical to a regeneration.
- Static import closure of the runner (the workflow's three scripts and the five steps of
  `fpl_nightly.py`): 25 modules, none under `tools/` or `analysis/`, standard library
  only. The record's modules (`fpl_xpv2`, `fpl_xpr`, `fpl_xpv`, `fpl_shares`) do not
  mention `sqlite3`.

## Check 6. Mutations — PASS (10 of 10 red)

On a scratch copy, one line at a time, restored after each (74 tests of `test_W3`,
`test_W2fix`, `test_W1`; green before and after):

| mutation | red test(s) |
|---|---|
| `_utc` reads the wall clock as UTC | `test_a_committer_date_at_plus_02_00_is_read_as_its_instant` |
| a captain with no row read as having played, `fpl_league.py` | `test_captain_with_no_player_gw_row_counts_as_0_minutes` |
| the same in `tools/league.py` | the same test |
| xp_v2 rounded to 2 places | `test_the_record_rows_and_skips_without_a_database` |
| caution band `count` for `count - 1` | `test_the_bands` and 2 more |
| lockdown guard dropped | `test_equals_info_2627_and_the_guard` |
| `fetch-depth: 0` -> `1` | `test_the_nightly_checks_out_the_history` |
| prior key never reached through `code` | 5 tests |
| a bundle commit at or after the deadline accepted | 2 tests |
| `xp_v2` dropped from `fpl_nightly.SOURCES` | 2 tests |

## Check 7. Secrets — PASS

- The 31 files the landing adds or changes: no URL with `apiKey=` and a value, no
  Authorization value, no token, no 32-hex string. The pattern's 3 hits in
  `tests/test_W1.py` are the keyword argument `ODDS_API_KEY=fake_key()`, not in W3's diff.
- The files changed by the data commits and the dry commit (logs, reports, status,
  export, `fpl.sql`, `fpl.sqlite`, the log, the odds snapshots): the same patterns, 0 hits
  except 32-hex strings in the odds snapshots, each the `"id"` of an Odds API event (20
  per snapshot). Not keys; none is printed here.
- I did not compare against the key's value: the key stayed unset.

## f. The dry run against run 1 — PASS

- Dry run `64a58c8` (`dry run 2026-11-11 dry/W3 47ac1ea [skip ci]`, parent `6ca6cd5`, on
  `data-dryrun-W3` only): its status is `reports/status_dryrun.txt`, WARN 27/30 (17, 30,
  31), as claimed. `reports/status.txt` on that branch is still the 11 Nov nightly's.
- The same 787 tests with the same results. Record 301 / 279 / 672 / xp_v2 301 against
  run 1's 300 / 278 / 672 / 300: Strand Larsen's status. Its xp_v2 rows also match the
  offline tool.
- Reports: 30 differing lines of 627. They are the status line, the date in the LEAGUE
  header, and ownership percentages and their sort order (0.1 steps). The W3 sections are
  the same: CAPTAIN SKIPPED for the same reason, BAN RISK 3 lines, REALISED 5 lines with
  GW8 from bundle `6034baa`, so `fetch-depth: 0` was exercised.
- Explained by "dry": no Odds API call (it used the nightly's `0129Z` snapshot); the
  status file's name; the branch.
- Not checked: that the dry run created no Release and no issue.

## Decisions for the chat

1. **The missing ruling** (the FAIL). Paste Boris's text for the 11 Nov landing into
   `prereg/W3.md`, or tell me where it is on file.
2. **The export lag now governs CAPTAIN and BAN RISK.** Amendment 3 point 3 accepts it for
   CHIPS ("chips are only revealed after a deadline"). The same reader feeds CAPTAIN (the
   15, statuses, minutes) and BAN RISK (the 15 and P(start)); the odds and the database
   are the current run's. On a normal night the table is one night behind on
   availability, including the night before a deadline. Tonight it made no difference
   for our 15. The CAPTAIN header names the export; the BAN RISK header does not. A
   decision, not a W3 defect: the prereg says "the export's latest squad".
3. **A false "FH candidate" in tonight's CHIPS section (W2 code, unchanged by W3).**
   Line 539 says `GW11 own 30.8 22.2 +8.5 ... FH candidate (gap > 8)`. The base report's
   own Free Hit screen in the same file (line 351) says `28.7 22.2 +6.5`, no flag, and
   the chip table (line 517) says FH XI 28.71.
   - Cause: Manzambi (AVL) was `a` in the 02:31 export the section read and `d` by the
     17:45 record, so the log has no own row for him. `fpl_edge.free_hit_table` then
     values him by its fallback at 4.21, on bottomup's scale, among own values of 2-3.
     He enters the Free Hit XI in place of E.Le Fée (2.156).
   - The same happened on 11 Nov with pre-W3 code (`6ca6cd5`: 31.1, +8.8, flagged,
     against 28.7, +6.5), so it is not a regression.
   - It can print a Free Hit flag that tonight's own data does not support.
4. **A two-run day.** Run 2 replaced run 1's same-day rows (S2's rule, pre-W3 code) and
   overwrote the archive of the same name. Run 1's 300 xp_v2 rows exist only at data
   `2e0b948`. The report at `6f9ecb8` names `fpl_export_gw10_2026-11-12.json.gz`, but the
   file of that name there is run 2's export, not the one its sections read. `runcommit`
   does not cover this.
5. For the record, no action: the runner counts 482 players keyed by code and the tool
   481; the prior key is the same for all 672 players.

**VERDICT: FAIL.** Check 4 fails because the ruling that the launch relies on for the
landing itself, the plan item and the move from Sat 7 Nov (as `prereg/W3.md` rules) to
Wed 11 Nov, is not in `prereg/W3.md` or anywhere else on file, and my instructions make
that a FAIL whatever the code does. Everything I could test passes: `47ac1ea` carries
exactly the code verified at `62bda73`; GitHub records both 12 Nov runs on `47ac1ea`
(scheduled, then Boris's dispatch) and both wrote to `data`; the xp_v2 rows are for GW11,
made 9 days before its deadline, reproduced exactly from pre-deadline inputs and
unmoved by planted future data; the six other sources are row for row what the pre-W3
code produces; the five report sections reproduce character for character, and CAPTAIN,
BAN RISK and REALISED agree with independent recomputation; the first-night CAPTAIN skip
is explained by the pre-W3 archive with no `code`; tests 755 -> 787 green, 10 of 10
mutations red, no secret. Once the ruling is on file the item has no open defect; notes
2-4 are decisions, and note 3 is a W2 behaviour worth fixing whichever way note 2 goes.
