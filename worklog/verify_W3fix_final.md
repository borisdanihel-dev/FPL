# verify_W3fix_final — W3fix after its landing (`7c1cb85`) and its first live run (data `e67fbb4`)

**VERDICT: PASS.** The merged runner is byte for byte the verified one, every condition of
the advance approval is supported by the files or by GitHub's own record, and the first
live run (a scheduled, real run on master `99af3cc`) reproduces from its own inputs with
the merged code. Four items for the chat are at the end; the first asks Boris to confirm a
reading of his approval rule.

Verifier: Claude Code, model Fable 5.2 (`claude-fable-5-2`), the agent file's model; no
fallback. Effort: as launched (the agent file says high; not confirmable from inside the
run). Run: Sat 28 Nov 2026, 03:34 to 03:53 UTC. `.claude/agents/backtest-verifier.md` was
read from disk first; it equals my loaded instructions. No session transcript or chat log
was read, and I did not open the scratch files that hold pasted chat text.

How I worked:
- Everything ran in my own scratch folder (`scratchpad\vfinal`): three fresh single-branch
  clones (`7c1cb85`, `99af3cc`, `05761f1`), `git archive` copies of data `e67fbb4`,
  `0768766` and `136a7a0`, and replay folders built from them.
- `C:\GIT\FPL`: read-only git commands. Master `99af3cc`, clean before and after.
- `C:\GIT\FPL-data`: in the first minutes I ran read-only commands there (`rev-parse`,
  `log`, `show`, `status`, and `cat`/`grep` of `status.txt` and the run log). No pull, no
  `--restore`, no write. After that I used copies only. It is at `e67fbb4`, clean, before
  and after.
- Network: `git ls-remote origin`, and one unauthenticated GET of the public GitHub
  Actions run list (no token, no `gh`). The agent file neither allows nor forbids this;
  see decision 2. The reply was saved in its own folder and parsed with `python -I`.
- Nothing was committed, pushed, merged, tagged or deleted.

## Summary

| Asked | Result | Evidence in one line |
|---|---|---|
| 1. The approval's conditions | Supported; two rest on the session's word | six of eight shown from files or GitHub; the write guard and "not revoked" cannot be shown from files |
| 2. The merged code is the verified code | PASS | the 108 non-doc files are one tree at `f1c3704`, `3fe7500`, `7c1cb85` and `99af3cc` |
| 3. Which commit the run ran | `99af3cc`, a scheduled real run | GitHub run 131: event `schedule`, branch master, head `99af3cc`, success |
| 4. The run's outputs | PASS | gate 890; 29/30; both screens equal; the report and the 2,316 rows reproduce |
| 5. No regression, no secret | PASS | old code against new on the same data: 0 recorded cells differ; the report differs only where the rulings say |
| 6. Prereg before code, rulings on file | PASS | each pin is committed before its code; the prereg is append-only over 23 commits |

The agent file's checks:

| Check | Result | Evidence |
|---|---|---|
| 0 prereg before code | PASS | section 6 |
| 1 point-in-time | PASS | 0 of 93,273 rows at or after their deadline; the GW13 rows rebuild from the run's own inputs with 0 of 11,580 cells different; no correlation metric, so no shift probe |
| 2 suites | PASS | 855 OK before (`05761f1`); 890 OK on `7c1cb85`; 890 OK on `99af3cc` with the live data |
| 3 re-run | PASS | no metric in the prereg; every figure of the landing record that I re-ran reproduces |
| 4 rulings and frozen settings | PASS, with decision 1 | every ruling the landing relies on is in `prereg/W3fix.md`; no constant is touched |
| 5 recording path | PASS | the old log is a byte prefix of the new one; old and new code record the same rows |
| 6 mutation | PASS | 3 of 3 one-line mutants red; the real code green |
| 7 secrets | PASS | no key, `apiKey=` URL or Authorization value in the data commit or in the lines the item added on master |

## 1. The advance approval's conditions

The rule is in `prereg/W3fix.md` ("Rulings, Fri 27 Nov 16:25 UTC", point 1) and in
`BUILD_PLAN.md` Part B. The two copies are the same text, character for character (7
lines, 892 characters), and so are the two copies of the 16:30 clarification. The rule
was committed in `86e50b3` at 16:23:02 UTC and reached GitHub at 16:23:07 UTC, 3 h 15 min
before the merge was pushed. It names "W3fix tonight (dry run 19:31 UTC from 3fe7500)".

| Condition | Do the files support it? | Evidence |
|---|---|---|
| Verifier PASS | Yes | The narrow re-check of `f1c3704` is PASS (`a552b15`, 14:16:23 UTC), and it is an ancestor of the merge. No code or test changed after it (section 2). |
| Dry run green | Yes | GitHub run 130, "dry run dry/W3fix", a push of `3fe7500`: created 19:31:32 UTC, success at 19:34:15. Its result is `data-dryrun-W3fix` `136a7a0` (19:34:10 UTC). |
| Full suite on a fresh clone | Yes for the result | My own fresh clone at `7c1cb85`: 890 OK, 11 skipped, the count and skips the session reports. That the session ran it at 19:32-19:38 UTC is its own statement. |
| Write guard clean | The session's statement only | Indirect support: the merge is mechanical (below), and the commits that added verifier sections (`e41cdaf`, `a552b15`) change `worklog/verify_W3fix.md` alone. |
| Inside 19:30-21:00 UTC | Yes | GitHub's secret-scan run for the push of `7c1cb85` was created at 19:38:46 UTC. |
| Not in a deadline freeze | Yes | From `fpl.sqlite` (the same in `0768766` and `e67fbb4`): GW12's deadline was 27 Nov 18:30 UTC, 1 h 08 min 46 s before the push; GW13's is 1 Dec 18:30 UTC, so its 30-hour freeze starts 30 Nov 12:30 UTC. |
| No other runner change that night | Yes | On master from Thu 26 Nov 21:00 UTC to the head, the merge is the only commit that touches a runner or test file. |
| Not revoked | Nothing on file revokes it | The last ruling before the merge (18:30 UTC, `prereg/claudemd.md`, answer committed 18:36:25 UTC) says "commit after tonight's W3fix merge". A revocation made in chat would not be visible to me. |

More on four of them:

- **Verifier PASS.** The last full check, of `3847ebd`, was WARN. The PASS is the narrow
  re-check that Boris's WARN ruling asked for ("Re-check only this"). The question that
  ruling left open (point 3, the surviving mutants) was answered at 15:30 and 16:00 UTC:
  the tests T1 and T2, which are not part of this landing.
- **Dry run.** I read `reports/status_dryrun.txt` and the log on `136a7a0`:
  - STATUS WARN, 28/30; the WARNs are check 17 (the 5 Nov price-date gap) and check 30
    ("ODDS SKIPPED (dry run)").
  - Test gate 890. It ran; it was not skipped. The push came 61.5 minutes after the GW12
    deadline, outside the one-hour window.
  - Recorded for GW13: own 288, xg 264, minutes 264, bottomup 264, fpl_ep 674,
    bottomup_lambda 264, xp_v2 288. That is 2,306 rows, the growth of the log (90,957 to
    93,263), with 0 rows at or after their deadline.
  - The three labels read "generated 2026-11-27 19:33 UTC"; the dry run's export says
    `2026-11-27T19:33:55+00:00`.
- **The merge is mechanical.** I merged `05761f1` and `3fe7500` again in a scratch clone:
  no conflict, and my tree is `7c1cb85`'s tree (`2a0a4da`). Its combined diff is empty, and
  the two sides share no file since their merge base `617e040`.
- **No other runner change.** Master's other commits that day touch `prereg/`,
  `worklog/`, `BUILD_PLAN.md`, `CHANGELOG.md` and `CLAUDE.md`, plus offline scripts under
  `worklog/` (`gw_pass/gw12/*.py`, `w3fix_tie/check.py`). GitHub shows no nightly-workflow
  run between the manual dispatch of 13:58 UTC (run 129) and the live run except the dry
  run.

The rule's other lines:
- "After merging, post the merge commit and the report in the worklog": `eb973d5`
  (19:40:02 UTC), pushed at 19:46:32 UTC together with `f0f2f7b` and `99af3cc`.
- "Advance approval never covers changes to the decision rules, chips or transfers": see
  decision 1.

Two details of the landing record:
- The tag `pre-W3fix` is annotated (`99da26f`) and points at `05761f1`; its tagger time is
  19:38:39 UTC. "Pushed before the merge" cannot be shown to the second.
- The merge commit was made at 19:32:46 UTC, before the dry run finished, but pushed at
  19:38:46 UTC, after it was green. The push is what lands, so the order holds.

## 2. The merged code is the verified code

All tracked files outside `prereg/`, `worklog/` and the root `*.md`, hashed as git stores
them:

| Commit | What | Files | Tree hash of that set | `checkpoint.py` |
|---|---|---|---|---|
| `05761f1` | master before the merge | 106 | `ff3348b6...` | `b900026` |
| `f1c3704` | the narrow re-check's commit | 108 | `268b84a5...` | `183cc75` |
| `3fe7500` | the dry run's commit | 108 | `268b84a5...` | `183cc75` |
| `7c1cb85` | the merge | 108 | `268b84a5...` | `183cc75` |
| `99af3cc` | the commit the live run used | 108 | `268b84a5...` | `183cc75` |

- `f1c3704` to `3fe7500`: `CHANGELOG.md`, `prereg/W3fix.md`, the state file, the report,
  the checkpoint's two output files, the GW12 refresh folder (from master) and
  `worklog/verify_W3fix.md`. No code, no test.
- `3fe7500` to `7c1cb85`: master's side only, 11 files: `BUILD_PLAN.md`, five preregs, the
  state file, the recovery-dispatch proposal and `worklog/w3fix_tie/` (3 files).
- What the merge brought to master (`05761f1` to `7c1cb85`), 14 files: `fpl_chips.py`,
  `fpl_edge.py`, `fpl_squad.py`, `test_fpl.py`, `tests/test_W3.py`, `tests/test_W3fix.py`,
  `tests/test_FJ.py`, `tools/chips.py`, `worklog/checkpoint_gw10/` (3 files),
  `CHANGELOG.md`, the report and `worklog/verify_W3fix.md`.
- `BUILD_PLAN.md` is read by one test (the verifier block against the agent file). The
  agent file is the same blob in all five commits, and the suite is green on the merge.

After the merge, up to the run: `eb973d5`, `f0f2f7b`, `99af3cc`. Together they change
four files: `CHANGELOG.md`, `CLAUDE.md`, `worklog/SESSION_STATE_A.md` and
`worklog/cc_2026-11-27_W3fix.md`.
- No runner module, test or workflow opens any of the four. A grep over every `.py` and
  the workflows finds their names only in comments, in docstrings and in one list of path
  names that a path-rule test passes to `is_data`.
- The one worklog path the runner does read, `worklog/gw_pass/` (REALISED, through git),
  is the same tree at `3fe7500`, `7c1cb85` and `99af3cc`.
- So the nightly's checkout differs from the merge commit in docs only, which is the
  check `prereg/claudemd.md` hands to this verifier.

## 3. Which master commit the first live run ran

GitHub's record (public Actions API, run 131 of the nightly workflow):

| Field | Value |
|---|---|
| name | `nightly` (a dry run is named `dry run <branch>`) |
| event | `schedule` |
| branch, commit | master, `99af3cc` |
| created | 28 Nov 03:29:17 UTC |
| finished | 03:32:08 UTC, success, attempt 1 |

- It ran `99af3cc`, not `7c1cb85` itself: three docs commits later, with the same runner
  (section 2). The landing record said this would be so.
- Master's head has been `99af3cc` since the push of 19:46:32 UTC, and still is
  (`ls-remote`).
- The run's own files agree with GitHub: the log starts at 03:29:38 UTC, the export says
  03:31:44, the rows are stamped 03:31:44 to 03:31:47, the status 03:31:57, and the data
  commit is at 03:31:59.
- The log shows the merged code. It lists 890 test ids, exactly the 890 of my run on
  `7c1cb85`: the 855 of `05761f1` plus 19 in `tests.test_W3fix` and 16 in `tests.test_FJ`.

It was a real run and wrote to `data` only:
- A scheduled run on master is never dry (the workflow's own rule).
- It wrote `reports/status.txt` (a dry run writes `status_dryrun.txt`) and called the Odds
  API ("ODDS OK ... this request 4"; a pushed dry run gets no key).
- `e67fbb4` is by `github-actions[bot]`, "nightly 2026-11-28 [skip ci]", with `0768766` as
  its only parent. It changes 9 files, all data paths.
- No other ref moved: all 37 remote branches equal my local tracking refs. `data-dryrun`
  is still at 23 Oct, `data-dryrun-W3fix` at 19:34 UTC Fri, and the newest backup tag is
  `backup-2026-11-22` (none is due on a Saturday).

The 21:40 UTC cron started 5 h 49 min late. The earlier nights show the same (03:45,
03:44, 04:32 and 05:29 UTC), so this is not new with W3fix.

## 4. The run's outputs

**Test gate.** "Ran 890 tests ... OK (skipped=13)"; check 28 says "890 tests green". The
13 skips are 11 Windows-only tests and 2 that need the 2025/26 files.

**Status.** STATUS WARN, 29/30. The one WARN is check 17, the standing 5 Nov price-date
gap; check 27 is the usual SKIP. Every check has the same result as on `0768766`. I
recomputed these from the committed files:

| Check | The status file says | My figure |
|---|---|---|
| 15 integrity | ok | ok |
| 16 price-history rows | 52,045 to 52,719 (+674) | the same |
| 18 log growth | own 289, xg 266, minutes 266, bottomup 266, fpl_ep 674, bottomup_lambda 266, xp_v2 289 | the same: 2,316 rows, all GW13 |
| 19 duplicate keys | 0 | 0 on the code's key (gameweek, player, source, snapshot day) |
| 20 rows after the deadline | 0 of 93,273 | 0 of 93,273 |
| 31 section lines | CHIPS 35, LEAGUE 51, CAPTAIN 18, BAN RISK 3, REALISED 7 | the same in my replay |

**CHIPS and the Free Hit screen** (`reports/fpl_2026-11-28.txt`):
- The label reads `FREE HIT SCREEN from fpl_export_gw12.json (generated 2026-11-28 03:31
  UTC) (tonight's export; ...`. The export's own field is `2026-11-28T03:31:44+00:00`
  (answer 4 of Fri 27 Nov).
- CHIPS's screen equals the base screen line for line: the header, six rows (GW13 to
  GW18) and the note. Neither flags a week, so the flags agree (Ruling 3; point 1 of
  19 Nov).
- The note reads "GW13: a player with no own forecast counts 0 (W3fix Ruling 3, amending
  item N): 1 of our 15 (Thiago), 0 in the Free Hit gate". Checked against the export and
  the log:
  - Thiago is the only one of our 15 without a GW13 own row; his status is `s`
    ("Suspended until 5 Dec").
  - Own's 289 recorded players are exactly the gate (status `a`, 45+ minutes in
    GW9-12), so 0 gated players lack a row.
- CHIPS's header carries the Ruling 3 note ("... 0 in this export").
- CAPTAIN and BAN RISK both start "GW13 from fpl_export_gw12.json (generated 2026-11-28
  03:31 UTC)" (Ruling 2; point 5 of 19 Nov). Thiago reads "no xp_v2 forecast" and
  P(start) 0.00.

**The whole report reproduces.** I rebuilt the night in a scratch folder as it stood at
the record step: the log of `0768766`, the database and odds snapshot of `e67fbb4`, the
working exports restored by the runner's own `--restore`, and `fpl_export_gw12.json`
unpacked from the run's archive (2,197,212 bytes, the same bytes). Then record, watch,
report and sections with the code of `99af3cc`:
- The report: 637 lines, identical to the real one after its two status-header lines
  (written by `checks.py`, which I did not run).
- The watch file: identical except the record time in its first line (03:40 in my
  replay, 03:31 in the run).

**The recording path did not move.**
- The log blob of `0768766` (4,816,172 bytes) is a byte prefix of `e67fbb4`'s (4,940,115
  bytes). The 2,316 added lines are all GW13.
- The real log against my replay with the merged code: 93,273 rows in order, 466,365
  cells compared, 0 differ outside `made_at`. For the 2,316 new rows: 11,580 cells, 0
  differ.
- The same replay with the code of `05761f1` (before W3fix): 0 cells differ from the real
  log, and 0 from the merged code's replay.

**Point-in-time.**
- 0 of 93,273 rows were made at or after their gameweek's deadline.
- The new rows were made at 03:31:44 to 03:31:47 UTC on 28 Nov, 3 days 14 h 58 min
  before GW13's deadline (1 Dec 18:30 UTC), from an export generated at 03:31:44 and an
  odds snapshot of 03:31 UTC.
- The run records one gameweek; the rows of every earlier gameweek are byte-identical.

**Duplicate keys.** 0 on the code's natural key, and 0 on (made_at, source, gameweek,
player).

**Mutation spot-check** (scratch copies of `7c1cb85`; `tests.test_W3fix`, `tests.test_W3`
and `tests.test_W2`, 64 tests):

| Copy | Change | Result |
|---|---|---|
| real | none | OK |
| m1 | bottomup back in `one_week_points` (Ruling 3 off) | 6 red |
| m2 | the CHIPS label without its generated time | 2 red |
| m3 | `current_export` returns the dated archive (Ruling 2 off) | 6 red |

## 5. No regression; no secret

**The same night, old code against new code.** Both replays read the same data, so every
difference is the code's.
- Recorded rows: 0 cells differ.
- The watch file: one line added, the note.
- The report: 82 diff lines, in six groups, each one a ruling's change:
  1. the metric text of the base screen (Ruling 3);
  2. the flag legend: "counted on our best XI before Ruling 3's zero" (point 2 of 19 Nov);
  3. the note under the base table, and again under CHIPS's screen;
  4. the Ruling 3 note in CHIPS's header;
  5. CHIPS's Free Hit screen: the label, and the table of tonight's export (GW13-18) in
     place of last night's archive (GW12-17) (point 1 of 19 Nov; answer 4 of 27 Nov);
  6. CAPTAIN and BAN RISK: GW13 from tonight's export with its time, in place of GW12
     from the 27 Nov archive (Ruling 2). The old code would have printed a captain table
     for GW12 nine hours after its deadline, which is the fault Ruling 2 fixes.
- No other line differs: the base screen's rows, the calculator's table, LEAGUE, REALISED
  and every earlier section are the same.

**Against the real report of `0768766`.** The same 18 section headings in the same
order, and the same result for each of the 31 status lines. The numbers differ because
the gameweek rolled over (GW12's deadline passed between the two runs).

**Two things in tonight's report that look like changes and are not W3fix's:**
- The Free Hit levels are about a fifth lower than on 27 Nov (GW14 bottomup 43.7, was
  55.1). The old code gives the same rows on tonight's data. See decision 4.
- The CHIP CALCULATOR still reads "export fpl_export_gw11_2026-11-27.json.gz ... next
  GW12" and "NEXT GAMEWEEK GW12: HOLD", nine hours after GW12's deadline. That is the
  calculator one night behind, which Ruling 2 allows ("CHIPS may stay one night behind");
  it is the same under the old code.

**Secrets.** I scanned the 9 files `e67fbb4` adds or changes, as raw bytes and, for the
two `.gz` files, unpacked: `apiKey=` and `api_key` in any case, Authorization and bearer
values, GitHub and other vendor token shapes, private-key headers, password-style
assignments, 32-hex strings (the Odds API key's shape), 40+ hex strings and long mixed
tokens.
- 7 files: no hit.
- The odds snapshot: 19 strings of 32 hex characters (`ab87...`, `0bc1...`, `9d23...`,
  `f45e...` and 15 more). Each is the `id` of one of the snapshot's 19 events, and all 19
  were already in earlier committed snapshots. They are the API's event ids, not a key.
- The run log: 38 long tokens, all of them file paths (`/hom...`) inside Python warnings.
- The lines the item added on master (`05761f1` to `99af3cc`): one prose mention of
  `apiKey=` in the earlier verifier report, one commit id and two SHA-256 values in the
  checkpoint's `run.txt`. No key.

## 6. Prereg before code; the rulings on file

| Ruling text and pin | Committed (UTC) | Its code | Committed (UTC) |
|---|---|---|---|
| Rulings of Thu 12 Nov (`a4cb2df`); the Ruling 2 pin (`e692192`) | 12 Nov 21:01:10; 21:25:11 | `14523e2` | 12 Nov 21:27:42 |
| Answers of Mon 16 Nov (`dbc6ad0`); the Ruling 3 pin (`4274955`) | 16 Nov 17:35:21; 17:44:51 | `96a7c5f` | 16 Nov 17:53:23 |
| The addendum (`2af773c`) | 16 Nov 18:03:13 | `3e4bbd5` | 16 Nov 18:04:04 |
| Answers of Thu 19 Nov (`448e652`); their pin (`101a485`) | 19 Nov 20:53:32; 21:03:08 | `38a2174`, `5385c57` | 19 Nov 21:16:21; 21:25:47 |
| Answers of Fri 27 Nov and their pin (`2831a63`) | 27 Nov 12:30:19 | `3847ebd` | 27 Nov 12:55:30 |
| The WARN ruling (`1b3b52b`) | 27 Nov 13:36:07 | `f1c3704` | 27 Nov 13:59:57 |
| The advance approval (`86e50b3`); its clarification (`92a1970`) | 27 Nov 16:23:02; 16:30:24 | the merge `7c1cb85` | made 19:32:46, pushed 19:38:46 |

- `prereg/W3fix.md` first appears in `a4cb2df`, 26 minutes before the item's first code.
- The file is append-only: 23 commits up to the merge, each adds lines and none removes
  or changes one. It is the same file at `7c1cb85` and at `99af3cc`.
- Every ruling the landing relies on is there as a verbatim block: Rulings 2 and 3 (12
  Nov), option (a) (16 Nov), the five answers of 19 Nov, answers 1-5 of 27 Nov, the WARN
  ruling, the rulings of 15:30, 16:00 and 16:20 UTC, the advance approval (16:25) and
  its clarification (16:30). The CLAUDE.md ruling is in `prereg/claudemd.md`.
- Three of Boris's ruling headings carry a time a few minutes later than their commit:
  "16:00" was committed at 15:55:10, "16:20" at 16:17:57 and "16:25" at 16:23:02 (on
  GitHub at 16:23:07). The prereg already notes that his labels are his own. The order
  ruling, then code, then merge does not depend on them.
- What I can and cannot say: the text is on file, unchanged, and earlier than what it
  authorises. That Boris wrote it is not something the files can show.

## Notes

- The CHANGELOG entry "W3fix ready" still says "the merge tonight on Boris's click" in
  its heading. It was written before the 16:25 rule and is not to be edited. The "W3fix
  done" entry is still to be written (decision 3).
- Still to do from the landing list: the "W3fix done" entry, and deleting `dry/W3fix` and
  `data-dryrun-W3fix` (both still exist).
- Check 23 says "7 file(s) to commit" and the commit holds 9. The other two are
  `fpl.sql` and `status.txt`, written after the check. `0768766` shows the same 7 and 9.

## Decisions for the chat

1. **The approval rule's scope line.** The 16:25 rule says "Advance approval never covers
   changes to the decision rules, chips or transfers", and in the same message names
   W3fix for tonight. W3fix amends the Free Hit screen's frozen metric (item N) and the
   chip calculator's own-week rule, both by Boris's own rulings of 16 and 19 Nov. The
   session's eight-point list does not mention this line. I read the naming of W3fix as
   governing, and tonight no number, flag or action of either screen changed. Confirm
   that reading (yes), or say how the line should be applied to items that touch
   `fpl_chips` (no)?
2. **Network reads by the verifier.** The agent file is silent on them. I made one
   unauthenticated GET of the public Actions run list; without it, the run's commit and
   the push times rest on the log and on local reflogs. Allow such reads in the agent
   file (yes), or keep the verifier to git and files (no)?
3. **The "W3fix done" entry** should record, as measured here: merged under the advance
   approval at 19:38:46 UTC; the first live run ran `99af3cc` (docs only ahead of
   `7c1cb85`), event `schedule`, started 03:29 UTC on 28 Nov; gate 890; 29/30.
4. **Information, not W3fix: the night after a deadline.** Before a gameweek's first
   kickoff the last-four window already counts that gameweek (tonight GW9-12, with GW12
   all zeros). So tonight's gate holds 289 players, where GW8-11 would give 304, and
   every level reads lower (7 Nov shows the same drop under the old code). Tonight's GW13
   rows are recorded on that window. Worth a look before GW13's deadline if these rows
   are read for a decision.

## Evidence files (scratch, not committed)

Under `...\scratchpad\vfinal`:
- `clone_merge\`, `clone_head\`, `clone_before\`; `out\suite_merge_plain.txt`,
  `out\suite_head_data.txt`, `out\suite_before_plain.txt` (the three suite runs);
- `data_new\`, `data_old\`, `data_dry\` (copies of `e67fbb4`, `0768766`, `136a7a0`);
  `data_T\` (the copy the suite read);
- `worldH\`, `worldB\`, `scripts\replay.sh` (the night replayed with the merged and the
  old code); `out\real_vs_H.diff`, `out\B_vs_H.diff`;
- `scripts\logcmp.py`, `out\logcmp.txt`; `scripts\screen_check.py`,
  `out\screen_check.txt`; `scripts\deadlines.py`; `scripts\sections.py`;
  `scripts\testids.py`;
- `scripts\secrets.py`, `out\secrets.txt`; `scripts\odds_ids.py`;
- `scripts\trees.sh`, `scripts\remerge.sh`, `remerge\`; `scripts\order.sh`;
  `scripts\verbatim.py`;
- `scripts\mutate.py`, `scripts\mutate_m3.py`, `mut\`, `out\mutants.txt`;
- `dl_runs\runs.json`, `scripts\runs.py` (the Actions run list).

VERDICT: PASS — the landing and its first live run hold up. The runner and tests at the
merge `7c1cb85` are byte for byte those of the verifier's PASS (`f1c3704`) and of the dry
run (`3fe7500`), and the merge is a mechanical one of two sides with no file in common.
Six of the approval's eight conditions are shown by the files or by GitHub's own record
(PASS before the merge, a green dry run, 890 OK on a fresh clone, a push at 19:38:46 UTC,
no freeze, no other runner change); the write guard at the merge is the session's
statement, and nothing on file revokes the approval. The first live run was the scheduled
nightly on master `99af3cc`, three docs commits after the merge with the same runner, and
it committed to `data` only. Its gate is 890, its status 29/30 with the one standing
WARN, CHIPS's Free Hit screen equals the base screen and carries the export's own time,
and CAPTAIN and BAN RISK read tonight's export. Its report and its 2,316 GW13 rows
reproduce from its own inputs with the merged code, and the code before W3fix records
the same rows, so the recording path did not move. No row is late or duplicated, and no
key is in the commit. Each pin was committed before its code and the prereg is
append-only. Decision 1 asks Boris to confirm how his rule's scope line applies; it does
not change what the files show.
