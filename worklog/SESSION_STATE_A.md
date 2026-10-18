# Session state — lane A (C:\GIT\FPL)

Lane A: runner work, wiring items and history items (RULING FAST-TRACK, item
4; `prereg/FAST.md`, BUILD_PLAN.md Part E). Updated at the end of every item,
before the push. A fresh lane-A session reads `CLAUDE.md`, `BUILD_PLAN.md` and
this file, then waits for the next instruction.

- **Night of 18/19 Oct: RULING lane A night work** (verbatim, recorded once):

  > Keep working until morning without Boris, on branches only:
  > 1. W1b (automatic dry runs, as already ruled) on w1b-wip off w1-wip: prereg on master first (docs only), then code, tests, mutations, push w1b-wip. No dry run until Boris is up; W1b merges the day after W1 (one wiring merge a day).
  > 2. Step 10, the rule normaliser, on s10-wip off master: everything except the hist_pit re-measure (that waits for S4 on master). Prereg first. Offline under tools/, reading C:\GIT\FPL-data read-only. Its tests live in tests/, which the nightly now runs, so it lands only after a green dry run of its landing branch, same rule as lane B.
  > 3. If time remains: Step 16 part 1 (blank/double history 2016/17-2025/26, offline) on s16-wip, prereg first.
  > Never tonight: anything on master except preregs and SESSION_STATE_A.md; dispatch requests; touching lane-b. A download or decision that needs Boris: park it in SESSION_STATE_A.md and move to the next item. Stop after 6 items without a chat review. Morning: one report block per item, then the Monday W1 order: confirm the 03:17 run, tag pre-W1, merge, Boris's real dispatch, final verifier. Lane B lands S4+S7+S5+S6 after W1's real dispatch is green.

  Addition (Boris, same night, verbatim): "after Step 16 part 1, do part 2
  (the 2026/27 calendar mapper: cup dates to gameweeks by deadline). Parts 3-4
  only if every input already exists locally (Elo may be built from archived
  results); a missing input (e.g. the European fixture calendar) is parked with
  the list of what is needed, no downloads without Boris. Order tonight: S2b,
  W1b, Step 10, Step 16 parts 1-2."

  RULING S2b (same night) has priority over this queue: verbatim in
  `prereg/S2b.md`, on `s2b-wip` off `w1-wip`. It lands Tuesday before 21:00 UTC,
  after W1 (Monday); W1b moves to Wednesday.
- **Parked for Boris:**
  - **W1b, no spec in this session.** The night ruling calls W1b "automatic dry
    runs, as already ruled". The only W1b text in the repository or this
    session is one clause in RULING W1 decisions, point 1: "W1b's
    push-triggered dry runs never call it". Nothing was built. Questions:
    1. Which pushes start a dry run: every branch, only `*-wip`, lane B's landing
       branches? Do docs-only pushes count?
    2. Do push-triggered runs count against "At most 6 dry runs a day" (S2
       amendment 2, point 9), and what does the 7th push do?
    3. `data-dryrun` is one branch: two lanes pushing at once overwrite each
       other's result. One `data-dryrun-<branch>` each, or one run at a time?
    4. Is the manual dispatch dry run kept alongside?
  - **S3 report (Boris, 19 Oct, verbatim lines):** record in
    `worklog/cc_2026-10-18_S3.md` on Monday, since master takes only preregs
    and this file tonight. The 18:45 UTC dispatch was nightly #21,
    workflow_dispatch on master `1af9644`, Success, 58 s:
    - `Is this run due:  DUE          not the backup cron`
    - `Weekly backup:    BACKUP skipped: a manual dispatch backs up only with force_backup ticked`
    - `Failure issue:    ALERT none: the run is green and no issue is open`

    The same log shows GATE OK (integrity ok, 14 tables, price_history 25882
    rows, frozen forecasts unchanged) and SECRETS OK. That outstanding item
    is closed.
  - **Low priority, whenever lane A next touches test_fpl.py:** the
    BackupStep tests leave gh.log open (ResourceWarning: unclosed file,
    test_fpl.py:5419). Close it, with no behaviour change.
- **Monday 19 Oct, first task** (RULING S3 dispatch result): confirm
  tonight's scheduled run - the data commit, status.txt with checks 9 and
  26 now active instead of SKIP, release backup-2026-10-18, and what the
  03:17 UTC backup run did. Seen on 18 Oct at 21:58 UTC, still to be confirmed:
  data `9da6ff1` (21:58:09Z), STATUS OK 27/27, checks 9 and 26 OK, tag
  `backup-2026-10-18` at `9da6ff1`.
- **Current item:** W1 (wiring: fpl_ep and the Odds API collector), on
  `w1-wip` (`ab047c3`); prereg `prereg/W1.md` (`7efc2b2`, decisions `91b10c7`,
  odds storage `249be76`; on w1-wip: master merged in `021656c`, pre-check
  decisions `23c1e1e`). Odds are raw gzip files in `odds/` on data, append-only;
  no odds table; check 24 names files over 50 MB. Suite 499, green normally and
  hermetically.
  - RULING W1 pre-check decisions applied on w1-wip `ab047c3` (18 Oct, after the pre-check):
    - the API only when `GITHUB_ACTIONS` is "true", else
      `ODDS SKIPPED (not in GitHub Actions)` and exit 0;
    - check 30 WARNs `credits unknown` when any of x-requests-used,
      -remaining or -last is missing;
    - no action on bookmakers outside uk/eu.
    Four new tests, red on `d928ebe` (14 failures), green on `ab047c3`. Suite
    495 -> 499 bare, runner-like, with stand-in zones and hermetically. Mutations
    P1, P1b, P2 and P2b are red, and W15 was re-pointed and is red. A frozen-clock regeneration is
    byte-identical between `d928ebe` and `ab047c3`.
  - RULING W1 decisions applied:
    - 4 credits a night, about 124 a month;
    - `odds_live` dispatch input, so a dry run skips the API unless it is ticked;
    - every odds problem is a WARN only;
    - check 30 WARNs below 60 credits;
    - no `ep_next` is `RECORD SKIP fpl_ep` (a WARN), and missing players are counted.
    `ODDS_API_KEY` is confirmed by Boris, re-entered 20:15 UTC on 18 Oct.
  - Tests 459 -> 495, green normally and hermetically. Mutations: 15 of 18
    (3 obsolete after the storage change) + 10 + 11, all red.
  - Second dry run `bf91cf5` (`d928ebe`, `odds_live` ticked) ruled green
    (RULING W1 dry run 2, 18 Oct): STATUS OK 28/28, odds file 10,472 bytes,
    fpl.sqlite unchanged at 1,896,448 bytes, 492 credits left.
  - Verifier pre-check: **PASS** (Fable 5.1, effort high), in
    `worklog/verify_W1_pre.md`. That file stays untracked until Monday. The write guard
    is clean: only that file changed; lane-b moved by lane B's own pushes.
    Its four observations went to the chat, and the first three were ruled in
    RULING W1 pre-check decisions:
    - a local `python fpl_odds.py` with the key set was a real run;
    - missing credits headers gave `remaining None` and an OK check 30;
    - non-uk/eu bookmaker keys appear in the answer;
    - w1-wip's own `prereg/W1.md` predated the two rulings. Master was merged
      into w1-wip in `021656c`, so it now carries all three.
  - Dry run 3 of `ab047c3` (`odds_live` unticked), moved to the night of 18 Oct by
    Boris: data-dryrun `f7c5706` on `9da6ff1`. Green:
    - 499 tests; `+ players.ep_next`; `ODDS SKIPPED (dry run)`, no `odds/`;
      five RECORD OK (fpl_ep 668);
    - STATUS WARN 27/28, the only WARN being check 30's dry-run skip;
    - the 1077 same-day GW8 rows of the four frozen sources changed `made_at` only,
      with 0 predicted values changed against master's code;
    - GATE OK, with an identical fpl.sql.
  - Verifier re-check on the delta: **PASS** (Fable 5.1, effort high), in
    `worklog/verify_W1_recheck.md`, untracked until Monday. The write guard
    (git status, git diff) is clean. One ref move, not attributed: `C:\GIT\FPL-data` was
    pulled (fast-forward e8629f0 -> 9da6ff1) at 22:37:57 UTC, 33 s after the
    guard snapshot. The verifier says it did not touch it; lane B pulls FPL-data
    by its protocol and was active then.
  - Next, Monday morning, in order:
    - confirm tonight's nightly and the 03:17 run (the first task above);
    - commit `verify_W1_pre.md`, `verify_W1_recheck.md` and this file;
    - tag `pre-W1`, then merge (at most one wiring merge a day, never in a freeze window);
    - Boris's real dispatch;
    - the final verifier, the report and CHANGELOG.
    It lands by Wed 21 Oct 20:00 UTC.
- **S3: done** (18 Oct). Merged `1af9644` (tag `pre-S3` = `3ce5a08`); real
  dispatch `e8629f0` STATUS WARN 24/25, ruled green (the WARN is check 3, a
  new FPL player); final verifier PASS (`worklog/verify_S3.md`). Report
  `worklog/cc_2026-10-18_S3.md`. Open S3 decisions are listed there.
- **S2: closed** (RULING FAST-TRACK: "S2 is closed"). On master since `9b4a462`
  and `50abf60`; final verifier PASS (`worklog/verify_S2.md`); report
  `worklog/cc_2026-10-18_S2.md`. Revert tags `pre-S2` (`1cddca9`) and
  `pre-S2-backup` (`2bee604`). Two S2 checks still fall to lane A:
  1. Tonight's scheduled nightly (18 Oct, 21:40 UTC). It confirms S1 and S2
     together and should make `backup-2026-10-18`. If it fails, revert to
     `pre-S2` first, then investigate.
  2. After GW7 locks down (Tue 20 Oct or later): the GW7 before/after
     calibration comparison, reported with the GW7 grading (S2 amendment 2,
     point 1). If it differs, revert to `pre-S2` first.
- **Open for the chat:**
  - reverting to `pre-S2` after the GW8 deadline would grade GW8's several
    snapshots together (S2 final decision 1);
  - `CLAUDE.md` items b and g still name `worklog/SESSION_STATE.md`, which is
    now an index pointing to the two lane files.
- **Queue (FAST-TRACK item 8, as amended on 18/19 Oct):**
  - W1: merge Monday.
  - S2b: lands Tuesday.
  - W1b: Wednesday, waiting for its spec.
  - Step 10.
  - W2: after the GW8 deadline.
  - Step 16.
  - W3, Steps 17-18, W4.
  - **Step 10 addition** (RULING Step 10 addition, 18 Oct, verbatim; also in
    BUILD_PLAN.md Step 10): once lane B has merged tools/hist_pit.py, re-measure the earlier 2025/26 findings that used fpl_hist.canonical_from_vaastav (the horizon test H=6, the F test, backtest_2025-26 and concentration_2025-26) with the point-in-time club map. Descriptive only: report old against new side by side; no rule changes unless a pre-registered test calls for one.
  - **W2 addition** (RULING W1 dry run 2 + W2 addition, 18 Oct, verbatim; goes
    into `prereg/W2.md` before any W2 code): Add to W2 (after the GW8 deadline): record bottomup_lambda nightly as a sixth source from the night's odds file (S5 adopted it as an input). The runner never imports tools/, so the formula moves into the runner path, tested to give byte-identical numbers to lane B's tools/odds_lambda.py on the same snapshot.
- **Models (FAST-TRACK amendment 1):** lane A's main session stays on Opus
  5.5; the verifier runs on Fable for every item, falling back to Opus at
  xhigh only if the Fable weekly bar is above 80% before its reset. Each
  report names the models used.
- **Dry runs used:** 18 Oct: 6 of 6.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE_A.md`).
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
