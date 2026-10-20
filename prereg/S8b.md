# S8b — the planner without hits on xp_v2, 2024/25 (Part F, F-F)

Committed before any S8b code. Offline: `tools/planner_2425.py`, which the
runner never imports. Branch `s8b-wip`, off `s6e2-wip` (it holds S6f's
2024/25 harness, S10b's re-score and the landing's tools).

## The ruling (BUILD_PLAN.md Part F, F-F, verbatim)

F-F. S8b (planner without hits): on 2024/25 GW2-38, 50 squads (seed 7, 2024/25 GW1 ownership), planner with hits forbidden, xP = xp_v2, decay 0.85, Boris's FT schedule, against the baseline (best one-week move when its gain > 0, else roll). Pass: mean >= +5 points per squad-season and 90% lower bound > 0. Otherwise the simple rule stays the default.

The lambdas beyond week t are set by point 5 of the night ruling (verbatim
at the end of this file).

## Template

- **Item:** S8b (BUILD_PLAN.md Part F, F-F).
- **Hypothesis:** with hits forbidden and xp_v2 as the forecast, S8's
  rolling-horizon planner gains at least 5 points per squad-season over the
  baseline.
- **Forecast, xp_v2 over the horizon:** at origin t, for each week u =
  t..min(t+5, 38):
  - xp_v2 as tested is S6d's `core` (`tools/xp_v2_live.py`, held to S6b's
    `Replay.xp_v2` by a test).
  - Its training inputs come from rounds < t: P(start), S11's shares and
    priors (2023/24), P(sub), ICT, DEFCON (none in 2024/25).
  - The fixtures are week u's.
  - **The lambdas (night ruling, point 5):**
    - week t: S5's odds-implied lambda (football-data 2024/25,
      pre-closing), else S5's fallback; this is S6b's `lambdas(t)`, so
      week t's forecast equals S6b's xp_v2(t) (a test);
    - weeks t+1..t+5: the fallback fitted on results before the origin
      (results of rounds < t, cut at round t's first kickoff, as S5).
    - Each origin's source per fixture is recorded in `sources.csv` and
      counted in the report.
  - A player without a fixture in week u scores 0 there (as S8); the gate
    is mins_last4 >= 45 (as S6b).
- **Data and sample filter:**
  - 2024/25 GW2–38 (GW2 is the first origin, with one training round, as
    S8);
  - S7's 50 squads (seed 7, 2024/25 GW1 ownership); prices of the origin
    round; clubs of the origin (hist_pit); 1 FT a week, bank to 5, no
    chips;
  - every input point-in-time.
  - **Outcomes:** 2024/25 re-scored under the 2026/27 table by S10b, the
    Part F convention (S6f, S6e2): bonus official, DEFCON excluded. A
    stated limitation: 2024/25 has no DEFCON counts, so neither the
    forecast nor the outcome has DEFCON.
- **Comparison:** S8's `rank_plans` with `hits_allowed=False`, decay 0.85
  and Boris's schedule (1.5 / 1.0 / 0.6 / 0.3), against S8's
  `baseline_plan`: the best one-week move with the free transfer when its
  xP gain > 0, else roll, never a hit.
  - S8's `replay` loop runs unchanged; only its season class is swapped,
    for the call, for one with the forecasts above and the re-scored
    outcomes.
  - The XI and captain are by forecast; autosubs by `rule_autosubs`; the
    captain is doubled.
- **Primary metric (one):** per squad, season points over GW2–38, planner
  − baseline (no hits on either side).
- **Secondary metrics (information only):**
  - transfers per squad;
  - S8's robustness line (decay 0.80 and 0.90 disagreements, first 5
    squads);
  - the lambda sources.
- **Bootstrap:** unit = squad (as S8), 10,000 resamples, seed 20261018,
  90% CI.
- **Pass threshold:** mean >= +5 points per squad-season and the 90% lower
  bound > 0. Otherwise the simple rule stays the default.

## Tests and checks

- `tests/test_S8b.py`, hermetic:
  - week t's forecast equals S6b's xp_v2(t);
  - weeks after t use the origin's fallback (never an odds row or a later
    result), and the sources are recorded;
  - the target's own rows never move a forecast;
  - S8's loop unchanged, with hits forbidden;
  - the bar;
  - isolation.
- Mutations (shown red).
- The full suite before and after.
- The verifier (Fable; Opus xhigh as ruled); the write guard.
- The report in `worklog/cc_<date>_S8b.md` and the CHANGELOG.

No re-tuning after viewing results.

## Ruling, Mon 19 Oct night (verbatim)

The night ruling, verbatim; point 5 sets the lambdas beyond week t.

Ruling, Mon 19 Oct (chat review; the item count resets to 0 of 6).

1. W3 prior file: OK as proposed. priors/s11_prior_2025-26.json on master (109 KB, SHA-256s recorded); the export gains code, first_name, second_name. Merge by Thu 29 Oct via dry/W3, outside the 9d windows, with Boris's click.
2. GW8 grading: grade GW8's xp_v2 from worklog/gw_pass/gw8/, labelled "source: GW8 bundle <commit>", only if that commit is timestamped before the GW8 deadline (Fri 23 Oct 17:30 UTC); otherwise "not recorded". Thursday's bundle must carry both own and xp_v2 for all 15 players plus the captain table, so GW8 counts toward the GW10 checkpoint.
3. Ban risk: count fixtures with finished_provisional = true and label those lines "provisional" until FPL marks them finished. Fixtures still in progress don't count. A missed ban warning costs a dead slot; a false one costs a glance.
4. S6f: recorded as FAIL. GW8 stays on xp_v2 for XI and captain, own shown beside it; the GW10 revert rule is unchanged. Record in BUILD_PLAN Part F as F-L (record only, no code): the same revert rule is applied again at GW15 over GW8–15, same metric, same bar.
5. F-F / F-G lambdas: OK as proposed. Odds-implied lambda for week t; for t+1..t+5, the fallback fitted on results before the origin. Live: the Odds API snapshot where it prices the fixture, else the fallback. Record per fixture which source was used. Prereg verbatim first.
6. S6e2: yes. Bound floor_points (stop once the pmf has underflowed, plus a hard cap on j), add tests at mu 120 and 12.765, re-verify, then file the report and CHANGELOG. The FAIL stands. The keeper-saves line closes here: no S6e3. Keepers stay on xp_v2 with bottomup_lambda as the tie-break.

Overnight order: S6e2 fix → F-F → F-G → then Part F in order (F-H, F-I as a proposal doc only). Same rules: work on branches; on master only preregs and SESSION_STATE_A.md; no runner pushes 21:00 UTC to the end of the nightly; no merges, landings or dispatch requests; park questions with the exact wording and move on; stop at 6 items. Verifier Fable 5.1 (allowed past 80% until its Tue 08:00 reset), fallback Opus xhigh.

Morning: one report block per item, plus tonight's 21:40 UTC nightly result.
