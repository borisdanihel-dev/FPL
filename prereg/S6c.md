# S6c — the safety check: xp_v2 as tested against own_rebuilt (2025/26 re-scored)

Committed on `s6c-wip` (branched from `origin/lane-b` at `e534200`) before any
S6c code. The ruling is point 2 of RULING S6b acceptance + lanes merge
(2026-10-19), pasted verbatim at the end with the whole block it came in, and
Boris's queue line for this item. Offline under `tools/`; the nightly imports
nothing of it. Never edited after any of its evaluation numbers exist.

- **Item:** S6c (the safety check on S6b's accepted switch; BUILD_PLAN.md
  Step 6). `tools/xp_v2_replay.py` gains an `own_rebuilt` projection beside
  `own_proxy` and a `--s6c` mode; tests in `tests/test_S6c.py`.
- **Hypothesis:** none to adopt. The question is whether own, rebuilt with
  every input 2025/26 can supply, beats xp_v2 as tested clearly enough to
  suspend the GW8 switch.
- **Data and sample filter:** exactly S6b's (`prereg/S6b.md`): 2025/26 GW5–38
  through the S4 harness (`canonical_at`, clubs of the origin, training
  rounds < t), re-scored under the 2026/27 rules by Step 10 (`rescore`, the
  same four inputs and SHA-256s); S7's 50 squads (seed 7), fixed, no
  transfers, no chips; XI legality by the 2025/26 positions; realised points
  by `points_2627_rules` with `rule_autosubs` on the re-scored minutes and
  the captain doubled (`planner.Replay.realised`). In addition, for
  `own_rebuilt` only: `historical/2024-25/merged_gw.csv` (S11's prior file,
  SHA-256 `5bbbcba6…`) for the personal prior, and
  `historical/2025-26/players_raw.csv` (`412ce017…`) for each player's
  2025/26 `web_name`.
- **Definitions pinned:**
  - *xp_v2* = S6b's `Replay.xp_v2`, unchanged code: S6's equal blend with
    S5's bottomup_lambda in the bottomup half, S11's shares in the xg half,
    P(start) from the current minutes model. The S6b per-gameweek xp_v2
    realised points must reproduce exactly (an acceptance test).
  - *own_rebuilt* at origin t = live own's formula, `fpl_edge.project` called
    as the recording branch calls it (`record_status`, source own): for every
    harness player at origin t with `mins_last4` ≥ 45 and at least one
    fixture in round t, the sum over the club's round-t fixtures (S5's fixture
    table, the one xp_v2 uses) of `project(p, {team: [(t, label, fdr)]}, 6,
    t − 1, priors, personal)[0]`; values ≤ 0 are not recorded (live's
    `if proj > 0`). Its inputs:
    - **form term:** `pts_last4` and `mins_last4` = the official 2025/26
      total points and minutes summed over rounds t−4..t−1 (the export's
      `event BETWEEN gw−3 AND gw` with gw = t − 1; what own would have
      seen; the realised side alone is re-scored); `gws_played` = t − 1;
    - **positional prior:** `fpl_edge.positional_priors` over every harness
      player at origin t (live: every player in the export), positions of
      the origin;
    - **personal prior:** `fpl_edge.personal_priors` on a `player_history`
      built from 2024/25: per harness player whose full name (`name`) matches
      exactly one 2024/25 element, that element's 2024/25 total points and
      minutes (manager rows out), kept at ≥ 450 minutes (the export's
      filter), keyed by the player's 2025/26 `web_name` and listed in
      2025/26 id order, as the export lists it;
    - **minutes-reliability scaling:** inside `project`, `min(1, mins_last4 /
      (90 × max(1, t − 1)))`;
    - **FDR adjustment:** inside `project`, `1 + (3 − FDR) × 0.12` with the
      file's end-of-season FDR, `fixtures.csv` `team_h_difficulty` for the
      home side and `team_a_difficulty` for the away side (0 or missing →
      3.0, `project`'s own rule);
    - **status and chance:** taken as available for both sides (the gate
      `status == 'a'` passes for every player; xp_v2's P(start) uses no
      chance, as in S6b).
  - *What own_rebuilt still lacks against live own, exactly:* (1) the
    pre-deadline FDR (the file holds end-of-season values); (2) `status` and
    `chance_next_round` (taken as available); (3) personal priors from
    seasons before 2024/25 (live takes the latest season with ≥ 450 minutes;
    only 2024/25 is local): such players fall to the positional prior; (4)
    the personal prior's identity is the full name within one 2024/25
    element, not the FPL id; a name held by two 2024/25 elements gets none.
    Stated in every output line that names it.
- **Comparison:** per gameweek and squad, the realised points of the XI and
  captain chosen by xp_v2 minus those chosen by own_rebuilt; the same
  squads, the same re-scored outcomes (S6b's machinery, own_rebuilt in
  own_proxy's place).
- **Primary metric (one):** per gameweek the mean over the 50 squads of
  (xp_v2 − own_rebuilt) realised points; printed per gameweek and as the
  season sum over GW5–38 (points per squad per season).
- **Secondary metrics (information only):** per gameweek among predicted
  starters (P(start) ≥ 0.8, a forecast from both models) the tie-corrected
  Spearman and the MAE of each model against the re-scored points, paired
  (xp_v2 − own_rebuilt); the share of squad-gameweeks with the same XI and
  the same captain; the per-gameweek mean of (own_rebuilt − own_proxy) with
  its interval, to show what the rebuilt inputs add to own.
- **Bootstrap:** unit = gameweek (a block of its 50 squad differences),
  10,000 resamples of the 34 per-gameweek means, 90% percentile interval,
  seed 20261018 (`backtest.bootstrap_mean`), as S6b.
- **Decision threshold (the ruling; not an adoption bar):** the switch to
  xp_v2 is suspended for GW8 only if the 90% upper bound of the mean
  per-gameweek (xp_v2 − own_rebuilt) is below 0. Printed as `GW8 SWITCH
  STANDS` or `GW8 SWITCH SUSPENDED: own picks GW8`.
- **2026/27 GW5–7, information only (the ruling's last sentence):** on our
  real squad (`fpl.sqlite` `picks`, entry 3073318, the 15 of each
  gameweek), the XI (`chips.xi_and_bench`) and captain (the highest in the
  XI) each model would choose, and their realised official points
  (`player_gw`) with `rule_autosubs` and the captain doubled. Recorded own =
  `projection_log.csv` on `data`, source `own`, the gameweek's last
  snapshot made before its deadline; a squad player without a row
  projects 0. Graded only under the lockdown guard (`data_checked = 1` and
  every fixture `finished = 1`); otherwise printed `not locked down: not
  graded`. xp_v2 as tested on 2026/27 needs the live allocation (queue item
  2, not built when S6c runs): until it exists the column is printed `not
  available`, never substituted; item 2's report prints the GW5–7 line with
  it, as information.
- **Acceptance tests (in addition):** own_rebuilt on a hand player equals
  `project` by hand (form shrink to the personal prior, then to the
  positional prior when there is none; reliability; FDR adjustment); the
  form window is rounds t−4..t−1 (a row of round t−5 or of round ≥ t
  altered → origin t unchanged; a row of round t−4 altered → changed); the
  FDR side (home takes `team_h_difficulty`; a swap → red); the personal
  prior's 450-minute filter and the ambiguous-name rule; a double gameweek
  sums its fixtures; point-in-time (rows of rounds ≥ t altered leave origin
  t's two forecasts unchanged); xp_v2's per-gameweek realised points equal
  S6b's code path; the decision line on both sides of 0; the GW5–7 section
  (the last pre-deadline snapshot, the lockdown guard, `not available`);
  `run.txt`; CLI `python tools/xp_v2_replay.py --s6c`; nightly isolation;
  `test_fpl.py` untouched.

No re-tuning after viewing results.

## Queue line (Boris, 2026-10-19, verbatim)

1. S6c (today), branch s6c-wip off origin/lane-b, as ruled in prereg/S6b.md.

## Ruling (verbatim, from prereg/S6b.md)

RULING S6b acceptance + lanes merge:
1. Boris accepts xp_v2 as tested in S6b (S11 shares in the xg half, S5 bottomup_lambda in the other, current minutes model) for XI and captain from GW8. own keeps being recorded nightly and is printed beside xp_v2 at every deadline; both are compared weekly in grading. Vetoes on hard facts as before. If the live forecast cannot use S11's shares by the GW8 pass, own picks GW8.
2. S6c, a safety check: own_rebuilt = live own's formula with every rebuildable input (form term, minutes-reliability scaling, FDR adjustment from the file's end-of-season FDR), status and chance taken as available for both sides; same squads, metric and bootstrap as S6b. The switch is suspended for GW8 only if the 90% upper bound of (xp_v2 - own_rebuilt) is below 0. Also print 2026/27 GW5-7, recorded own against xp_v2 as tested, as information.
3. Revert rule, fixed now: at the GW10 checkpoint, if the live paired decision metric over GW8-10 has its 90% upper bound below 0, own returns.
4. Lanes merge: this is lane B's last task. Record this ruling verbatim in prereg/S6b.md, write a complete handover in SESSION_STATE_B.md (open items: S6c; the live "xp_v2 as tested" forecast in the bundle; the bundle runs Thursday about 18:00 and Friday morning with files committed under worklog/gw_pass/gw8/; the next landing of S8, S11, S12, S13, S6b, S6c, the bundle and the CLAUDE.md provenance line; Step 14), push lane-b, and stop. Leave C:\GIT\FPL-b and its tools/out untouched.
END RULING

## RULING 19 Oct afternoon (verbatim; point 6: reconcile the GW5-7 retro with the official GW6 score; recorded after S6c's evaluation numbers - a ruling, not an edit of the rows above)

RULING 19 Oct afternoon:
1. Step 14: option (a), the distribution of xp_v2 itself (mean matches by construction). Record the missing saves term as a GW10-checkpoint item ("xp_v2 + saves" gets its own pre-registered test then); no change to the accepted model before that.
2. The live xp_v2 priors: 2025/26 is correct ("last season" = the season before the forecast season; S6b used 2024/25 only because it replayed 2025/26). Correct the handover note.
3. Pushes to dry/W2 during the GW8 freeze are allowed: a dry run writes only data-dryrun-*, never master. W1b's quiet windows still apply.
4. Step 16 parts 3-4: parked until after GW8; then propose exact sources (URL, size, what each provides) for approval. pre-S2 stays until the GW10 checkpoint.
5. Dry-run cap: today's six are used. The landing-2026-10-19b and s2b-wip dry runs move to Tuesday after 00:00 UTC.
6. Reconcile before relying on the GW5-7 retro: our actual GW6 (wildcard, captain Saka) scored 49 officially, while the retro scores our squad 59 (own's picks) and 61 (xp_v2's picks). Check that the retro used the actual GW6 15 (post-wildcard), the official points and FPL's actual autosubs, and explain the gap in the S6c/S6d report. Captain in reality was Saka (the vice was Haaland).
END RULING
