# W1b — automatic dry runs

Committed before any code for this item.

- **Item:** W1b, runner work (the nightly workflow and its gate). Ruled 19 Oct
  (RULING W1b, below). Built on `w1b-wip` off `w1-wip`; merges Wednesday, the
  day after S2b (one wiring merge a day).
- **Hypothesis:** n/a. The workflow and pipeline change; no model.
- **Data and sample filter:** none.
- **Comparison:** none.
- **Primary metric (one):** n/a.
- **Secondary metrics (information only):** none.
- **Bootstrap:** n/a.
- **Pass threshold:** n/a.
- **Acceptance tests (descriptive or data-pipeline items, instead of a metric):**
  1. Trigger:
     - `nightly.yml` gains `push: branches: ["dry/**"]` and no other push
       filter: no tags, no paths, no other branch. Schedule and dispatch are
       unchanged.
     - A push-triggered run's ref is never master, so it is always dry
       (`fpl_publish.run_mode`).
  2. The dry-run path, as today:
     - `FPL_DRY_RUN` is true; the run never pushes to data, never makes a
       release, never touches the failure issue.
     - The key is not passed: `ODDS_API_KEY` is empty on a push event, in both
       steps that carry it. `FPL_ODDS_LIVE` is empty, so the line reads `ODDS
       SKIPPED (dry run)`.
     - The concurrency group is `nightly-dryrun`, never `nightly-data`, with
       `cancel-in-progress: false`.
  3. Results:
     - A push-triggered run force-pushes to `data-dryrun-<item>`, `<item>`
       being the ref name after `dry/`. A manual dispatch force-pushes to
       `data-dryrun`.
     - `fpl_publish.push_dry` refuses any other target, `data` above all.
     - Deleting `dry/<item>` and `data-dryrun-<item>` after landing is a
       deletion, never a force-push. The pre-push hook allows `dry/*` pushes
       and `data-dryrun-*` deletions.
  4. Cap:
     - The `--due` gate counts today's (UTC) dry runs with the Actions API,
       with `actions: read` granted to the one job. Push-triggered and manual
       runs count together; a run counts if its "Nightly run" step started,
       and the run itself is left out.
     - Dry runs are named `dry run <ref>` (`run-name`) so the count can find
       them. Manual dry runs made before W1b lands carry no such name and are
       not counted.
     - At 6 counted it prints `DRY RUN SKIPPED: 6 of 6 today`, sets run=false,
       and the run ends green.
     - If it cannot count (no token, an HTTP or network error, more runs than
       one page), it skips with the reason.
  5. Quiet windows. The run skips green, with a line saying why:
     - from 21:30 UTC until the data branch has a commit made at or after that
       21:30 (the night's nightly);
     - within 1 hour either side of any deadline (`events.deadline_time` in
       the checked-out data).
  6. Manual dispatch keeps its inputs (`dry_run`, `odds_live`, `force_backup`),
     writes `data-dryrun`, and is the only way to run `odds_live`. A real run
     (master, `dry_run` unticked, or the schedule) is never gated by the cap
     or the windows.
  7. Tests in `tests/test_W1b.py`:
     - the trigger filter, the windows, the cap and the result-branch name as
       pure functions;
     - a parse of the workflow text: the push trigger is `dry/**` only, and the
       job's group is `nightly-dryrun` for a push;
     - the pre-push hook allows `dry/*` and `data-dryrun-*`;
     - the `--due` gate end to end with a fake Actions API, and no network.
     - Red before the fix where a test pins a change; one mutation per rule,
       each red. The suite green bare, runner-like, with stand-in zones and
       hermetically; a frozen-clock regeneration byte-identical.
  8. `CLAUDE.md` and `BUILD_PLAN.md` Part E record the procedure, so lane B
     uses it: push to `dry/<item>`, read back `data-dryrun-<item>`, a second
     run as `dry/<item>-2`, delete both after landing.
  9. Readings taken where the ruling leaves a choice, each listed for the chat
     in the report:
     - **(a) Who is gated.** The cap and the quiet windows apply to every dry
       run, push-triggered or manual. Point 4 says the two kinds "together
       count" and "the 7th ends green"; point 6 keeps the dispatch's inputs
       and result branch.
     - **(b) The 21:30 window has an end.** It also closes at 03:17 UTC, the
       backup run's slot, so a night whose nightly never commits cannot block
       the dry run of its fix all the next day.

No re-tuning after viewing results.

## Ruling

The chat's ruling, pasted verbatim before any code.

RULING W1b (automatic dry runs; answers the four parked questions):
Goal: Boris clicks only real runs.
1. Trigger: a push to a branch matching dry/** and nothing else. A lane asks for a dry run by pushing its work to dry/<item> (normal push; a second dry run after a rebase uses dry/<item>-2, never force). Every push there runs, docs-only or not; lanes push there only when they want a dry run.
2. Same dry-run path as today: dry_run forced, never data, never a release, never the Odds API (the key is not passed). Own concurrency group nightly-dryrun, so it can never queue against or cancel the scheduled run or a real dispatch (nightly-data).
3. Results: each push-triggered run force-pushes its result to data-dryrun-<item> (the name after "dry/"), so the lanes never overwrite each other. Only the dry-run job ever force-pushes, and only to data-dryrun and data-dryrun-*. After an item lands, its lane deletes its own dry/<item> and data-dryrun-<item> (a deletion, never a force-push).
4. Cap: push-triggered and manual dry runs together count against "at most 6 a UTC day". The 7th ends green with "DRY RUN SKIPPED: 6 of 6 today". Count with actions: read on that job only; if it cannot count, it skips.
5. Quiet windows: skip, green with a log line, from 21:30 UTC until that night's nightly has committed, and within 1 hour of a deadline.
6. Manual dispatch stays exactly as now (dry_run, odds_live, force_backup) and writes data-dryrun; it is the only way to run odds_live.
7. Tests in tests/test_W1b.py: trigger filter, windows, cap and result-branch naming as pure functions; a workflow parse test that the push trigger is dry/** only and the job's group is nightly-dryrun; check that the pre-push hook allows dry/* and data-dryrun-*. Usual gates: prereg with this ruling verbatim, one last manual dry run, Fable verifier, tag pre-W1b; merge Wednesday, then Boris's real dispatch. Record the procedure in CLAUDE.md and BUILD_PLAN.md Part E so lane B uses it.
Build it tonight on w1b-wip after S2b, as queued.
END RULING

Earlier texts this item answers (verbatim):

RULING lane A night work, item 1: "W1b (automatic dry runs, as already ruled) on w1b-wip off w1-wip: prereg on master first (docs only), then code, tests, mutations, push w1b-wip. No dry run until Boris is up; W1b merges the day after W1 (one wiring merge a day)."

RULING W1 decisions, point 1 (clause): "W1b's push-triggered dry runs never call it."

RULING S2b, point 4 (clause): "W1b moves to Wednesday."

## Morning ruling, 19 Oct

The chat's ruling, appended verbatim before any further W1b change.

RULING morning 19 Oct (lane A):
1. Go: commit the W1 verifier files and the S3 log lines, tag pre-W1, merge W1 now, ask Boris for the real dispatch; final verifier after it.
2. Downloads approved, from github.com/vaastav/Fantasy-Premier-League into historical/<season>/ (gitignored, read-only afterwards), recording URL, fetch time and SHA-256 per file: data/2025-26/players_raw.csv; for Step 16 part 1, data/<season>/fixtures.csv and the gameweek deadlines for 2016-17 to 2024-25. Nothing else; Step 16 parts 3-4 stay parked.
3. Step 10 answers: Q1 (a), the live game_config as the points table; the reproduction test checks the "no points change" claim, and a failure is a finding. Q2 (a) now via players_raw.csv; storing code in the sync goes into W2. Q3 (b), no BPS re-score: bonus stays official, flagged "2025/26 BPS". Q4 (a), rescale only if game_config shows a 2026/27 assist-points change, else a printed no-op. Step 10 covers 2025/26 only for now.
4. W1b: reading (a) accepted, the cap and windows apply to manual dry runs too. The 21:30 window closes at 04:00 UTC, which covers the backup run. Point 3 accepted as documented. Point 6: on merge day, a missing deadline row makes the gate WARN instead of skipping silently.
5. S2b decisions 1-3 accepted; check 22 is the guard on point 1.
6. C:\GIT\FPL-data: either lane may run git -C C:\GIT\FPL-data pull --ff-only and nothing else; on a lock, wait and retry.
7. CLAUDE.md b and g: name SESSION_STATE_A.md / SESSION_STATE_B.md. Keep every pre-* tag until the GW10 checkpoint. Finish the S3 report list as you proposed.
Order today: W1 merge and dispatch; Step 10 on s10-wip; Step 16 part 1 after its download; S16 lands after a dry run.
END RULING
