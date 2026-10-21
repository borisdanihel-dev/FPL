# S2b — final re-fetch until data_checked

Committed before any code for this item.

- **Item:** S2b, a runner fix to Step 2 (BUILD_PLAN.md Step 2.1: a gameweek's
  points are final only at data_checked). Ruled 19 Oct (RULING S2b, below).
- **Hypothesis:** the sync stops re-fetching a gameweek at `events.finished = 1`.
  So player_gw, entry_gw and picks rows fetched before `data_checked = 1` stay
  provisional. Re-fetching every row whose fetch time is not later than the
  first sight of data_checked makes the stored points FPL's final points.
- **Data and sample filter:** `fpl.sqlite` on the data branch, 2026/27:
  - `events`, `player_gw`, `entry_gw`, `picks`, and `automatic_subs` (written
    from the same picks answer);
  - GW1-6, plus GW7 if it is locked down by the first real run.
  - "Stored" is the data commit before the first real run of the merged code;
    "final" is that run's data commit.
- **Comparison:** stored against final, per gameweek.
- **Primary metric (one):** n/a. This is a data-pipeline item; the measurement
  is descriptive and changes no rule.
- **Secondary metrics (information only):** none.
- **Bootstrap:** n/a.
- **Pass threshold:** n/a.
- **Acceptance tests (descriptive or data-pipeline items, instead of a metric):**
  1. `events.data_checked_seen_utc`:
     - added by ALTER TABLE, NULL for rows already stored;
     - set to the sync's bootstrap fetch time the first time a sync sees
       `data_checked = 1` for that event;
     - never changed after that, not by a re-run, and not by a sync that reads
       `data_checked = 0` again.
     - The nightly rewrite of `events` keeps it.
  2. Finality:
     - A player_gw, entry_gw or picks row is final only when its `fetched_at_utc`
       is not NULL and strictly later than its event's `data_checked_seen_utc`.
     - A gameweek with any non-final row is re-fetched: `event/{gw}/live/` for
       player_gw; `entry/{id}/event/{gw}/picks/` for that entry's entry_gw,
       picks and automatic_subs.
     - A gameweek whose rows are all final is not re-fetched.
     - The existing guards stay: `--refetch` forces a re-fetch, and fewer than
       301 player_gw rows means re-fetch.
     - `picks` has no `fetched_at_utc` today. It gets one by ALTER TABLE (NULL
       for stored rows, S2 ruling 3), written with its entry_gw row.
  3. On today's data, the first run of the merged code re-fetches GW1-6 once,
     and the run after it re-fetches none of them. The run log's `SYNC STATS`
     line gives the API call count, which is reported.
  4. Check 22:
     - reconciles every locked-down gameweek (`gameweek_settled`: data_checked
       = 1 and its fixtures finished), not only the latest;
     - lists each mismatch (gameweek, entry, FPL against computed), and any
       mismatch makes it a WARN;
     - stays silent on a gameweek not locked down (S3, point 6).
  5. Tests:
     - in `tests/test_S2b.py`, shown red on `w1-wip` before the fix;
     - at least one mutation per rule above, each red;
     - the suite green bare, runner-like, with stand-in zones and hermetically;
     - a frozen-clock regeneration of the forecasts byte-identical before and after.
  6. The measurement of ruling point 3:
     - per gameweek, stored against final for entry_gw points (every manager)
       and player_gw total_points;
     - every earlier recorded result that read provisional rows (calibration
       lines; S4, S5 and S6 2026/27 conditions), and how far it moves.
     - Before the run, which gameweeks hold provisional rows is read from the
       data branch's history: the first data commit with `data_checked = 1`,
       against each row's fetch time. No API calls beyond the sync's own.

No re-tuning after viewing results.

## Ruling

The chat's ruling, pasted verbatim before any code.

RULING S2b (runner fix, priority over the night-work queue): final re-fetch until data_checked.
Finding (lane B's S9 verifier, confirmed in fpl_sync.py on master): sync_player_gw and the entry_gw/picks loop skip a gameweek once events.finished = 1, so rows fetched before data_checked stay provisional (entry_gw GW3-4 short 12-29 points for every manager; GW6 short 1-6 for five rivals).
1. Add events.data_checked_seen_utc: set the first time a sync sees data_checked = 1, never changed after. A stored row (player_gw, entry_gw, picks) is final only if its fetched_at_utc is later than that time; otherwise the sync re-fetches it. NULL fetched_at_utc is never final. The first real run therefore re-fetches GW1-6 once; report the API call count.
2. Check 22 reconciles every locked-down gameweek, not only the latest, and WARNs per mismatch.
3. Measure before and after the first real run: per gameweek, stored v final for entry_gw points (all managers) and player_gw total_points. List every earlier recorded result that read provisional rows (calibration lines, S4/S5/S6 2026/27 conditions) and by how much it moves. Descriptive; no rule changes.
4. Branch s2b-wip off w1-wip (both touch fpl_sync.py); prereg first; tests and mutations as usual. Lands Tuesday before 21:00 UTC after W1 (Monday): dry run, verifier, tag pre-S2b, merge, Boris's real dispatch. W1b moves to Wednesday.
END RULING

## Morning ruling, 19 Oct

The chat's ruling, appended verbatim before any further S2b change.

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

## RULING 19 Oct afternoon (verbatim; point 5: the s2b-wip dry run moves to Tuesday after 00:00 UTC)

RULING 19 Oct afternoon:
1. Step 14: option (a), the distribution of xp_v2 itself (mean matches by construction). Record the missing saves term as a GW10-checkpoint item ("xp_v2 + saves" gets its own pre-registered test then); no change to the accepted model before that.
2. The live xp_v2 priors: 2025/26 is correct ("last season" = the season before the forecast season; S6b used 2024/25 only because it replayed 2025/26). Correct the handover note.
3. Pushes to dry/W2 during the GW8 freeze are allowed: a dry run writes only data-dryrun-*, never master. W1b's quiet windows still apply.
4. Step 16 parts 3-4: parked until after GW8; then propose exact sources (URL, size, what each provides) for approval. pre-S2 stays until the GW10 checkpoint.
5. Dry-run cap: today's six are used. The landing-2026-10-19b and s2b-wip dry runs move to Tuesday after 00:00 UTC.
6. Reconcile before relying on the GW5-7 retro: our actual GW6 (wildcard, captain Saka) scored 49 officially, while the retro scores our squad 59 (own's picks) and 61 (xp_v2's picks). Check that the retro used the actual GW6 15 (post-wildcard), the official points and FPL's actual autosubs, and explain the gap in the S6c/S6d report. Captain in reality was Saka (the vice was Haaland).
END RULING

## After the first real run: a verifier on the after-measurement (Ruling, Tue 20 Oct evening, point 2, verbatim)

The after-measurement is `worklog/cc_2026-10-20_S2b_after.md` (data `63e6a44`). A Fable verifier checks it tonight; it blocks nothing.

Ruling, Tue 20 Oct evening.

1. No new test now: s8c-wip 71c9d17 stays the commit Thursday's bundle runs from, exactly as verified. Add the sorted-clubs flag test when s8c-wip lands on Sun 25 Oct.
2. Yes: a Fable verifier on S2b's after-measurement (worklog/cc_2026-10-20_S2b_after.md) tonight; it blocks nothing.

Then tonight, on branches only: W3 points 2, 3 and 5 on w3-wip (merge by Thu 29 Oct via dry/W3), then the F-I downloads and Step 16's prereg. Wednesday: W1b as planned; tell Boris when his dry-run click is needed. Same rules: no runner pushes 21:00 UTC to the end of the nightly; no merges without Boris; stop at 6 items.

## The after-report corrected (Ruling, Tue 20 Oct night, point 1, verbatim)

The four slips of `worklog/verify_S2b_after.md` are corrected in `worklog/cc_2026-10-20_S2b_after.md`; an amending CHANGELOG entry is added and the 20 Oct entry stays as written.

Ruling, Tue 20 Oct night.

1. S2b after-report: yes. Correct the four slips in the report; add an amending CHANGELOG entry; the original entry stays as written.
2. Yes: appended last in the table is what was meant.
3. Change the GW8 grading so it does not depend on Friday's timing. The export cannot see a pending transfer before the deadline, so a refresh after Boris's transfer would still print the old 15.
   - s8c-wip: the bundle also writes worklog/gw_pass/gw8/xp_v2_all.csv from the same run: every player it forecasts, with id, name, team, position, xp_v2 for GW8, P(start) and the lambda source. Test that the printed output is byte-identical with and without the CSV. The verifier checks the diff. Done by Thu 22 Oct 14:00 UTC; the new head is the commit Thursday's bundle runs from.
   - w3-wip: REALISED takes the actual GW8 15 from the post-deadline picks, own from the projection log, and xp_v2 from that CSV; each model picks its XI and captain from those 15. The condition "the bundle's 15 equals the GW8 squad" is replaced by "all 15 are in the CSV"; otherwise "not recorded".
4. Committer time: OK, and the bundle's run.txt end time must also be before the deadline. Both are required.
5. Yes: the item count resets to 0 of 6. Wednesday: point 3, then W1b as planned (tell Boris when his dry-run click is needed, before 21:00 UTC), then Step 16's prereg. Same rules: branches only; no merges without Boris; no runner pushes 21:00 UTC to the end of the nightly or from Thu 22 Oct 11:30 UTC to the GW8 deadline.
