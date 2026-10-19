# S6d — the live "xp_v2 as tested" forecast in the bundle

Committed on `s6d-wip` (from `s6c-wip` at `28d0578`) before any S6d code.
The ruling is Boris's queue line for this item and point 1 of RULING S6b
acceptance + lanes merge, both verbatim at the end (the point is quoted with
the whole block it came in). Offline under `tools/` (a new
`tools/xp_v2_live.py`, and `tools/gw_pass.py`); the nightly imports nothing
of it. Never edited after any of its outputs exist.

- **Item:** S6d (queue item 2 of 19 Oct; BUILD_PLAN.md Step 6, the accepted
  decision model run live). Tests in `tests/test_S6d.py`.
- **Hypothesis:** none; an implementation item with acceptance tests. It
  brings the model Boris accepted (xp_v2 as tested in S6b) to the deadline
  pass, so that GW8 can switch (ruling point 1: "If the live forecast
  cannot use S11's shares by the GW8 pass, own picks GW8").
- **Data and sample filter (live):** the newest export in the data folder
  whose next gameweek is the target and which was generated before the
  target's deadline (`fpl.sqlite` `events.deadline_time`); `fpl.sqlite`
  (players' first and second names, finished results for S5's fallback);
  the newest Odds API snapshot under `odds/` taken before the deadline
  (S5's live mode; without one every fixture takes S5's labelled
  fallback); `historical/2025-26/` (S11's priors: last season) and
  `historical/2026-27/elements_positions.csv` (the 2026/27 `code`). Rows of
  the target gameweek are never read.
- **Definitions pinned — xp_v2 as tested = S6b's `Replay.xp_v2`, term by
  term, on 2026/27 inputs.** A core function takes the inputs S6b's replay
  builds (the training slice's `reliability_inputs`, the raw rows per
  round, S11's rows, team totals and `Prior`, the target's fixtures and
  their λ) and returns S6b's numbers on S6b's inputs; the live adapter
  builds the same inputs from 2026/27:
  - *players and P(start):* `reliability_inputs(canonical_from_export(d),
    gws_played = d["gameweek"])`: the current minutes model, which reads
    `chance_next_round` live;
  - *gate:* `mins_last4` ≥ 45 (S6b's gate) and, live, status `a` (the
    recording gate every live source applies); a player outside it, or
    without a fixture in the target, gets no xp_v2 and no substitute;
  - *xg half* E_xg | start = `xg_half(pos, xG | start, xA | start, Σ P(cs) ×
    CS_VALUE[pos], DEFCON, ICT percentile)`:
    - xG | start = Σ over the target's fixtures of λ_team × (Z × share +
      (1 − Z) × prior share) × (minutes per start / 90), xA likewise;
      share = his xG (xA) over the gameweeks he appeared in / his club's xG
      (xA) in those gameweeks (S11's `player_sums` and `team_totals` on the
      export's rows, one unit per player-gameweek: no double gameweek in
      2026/27 through GW8; club = his club in the export: no player has
      moved between Premier League clubs since the first dated export,
      2026-09-11; earlier rows take that club, stated); Z = m / (m + k), m =
      his minutes / 90, k per metric = S11's `Prior` k;
    - prior share = S11's `Prior(historical/2025-26)` — "priors come from
      last season" (BUILD_PLAN.md Step 11; S11 and S6b took 2024/25 for
      2025/26; lane B's handover named 2024/25 for the live forecast, which
      would be two seasons back: the plan's rule governs, recorded as a
      decision for the chat). The key is his 2025/26 vaastav name reached by
      `code` (`elements_positions.csv` id → code; 2025/26 `players_raw.csv`
      code → 2025/26 id; `merged_gw.csv` id → name), else his 2026/27 first
      + second name; then S11's rule: his own 2025/26 share at the same
      club, else the club-position mean, else the league-position mean;
    - λ_team and λ_opp per fixture = S5's `fixture_lambdas(book, model,
      kickoff, home, away)` (the snapshot's book; the fallback fitted on
      finished results before the deadline), the target's fixtures and
      kickoffs from the export's `fixtures_next6`;
    - minutes per start = his minutes in starts / starts, else the
      positional mean among players with starts, else 90;
    - P(cs) = exp(−λ_opp); DEFCON = `defcon_rates` (2 × his hit rate over
      his 60+-minute rows at the current thresholds); ICT percentile =
      `ict_percentile`'s ordering of season influence + creativity + threat
      (the export) among players with minutes > 0;
  - *bottomup half* E_bl | start = S5's `forecast_lambda(pid, inp, [(opp,
    home, λ_opp)])` / P(start) (0 when P(start) is 0);
  - *sub term:* P(sub) and E[pts | sub] by S6b's `sub_inputs_2526` on the
    export's rows; live, P(sub) × `chance_next_round` / 100 (S6's live
    rule; 100 throughout S6b), capped at 1;
  - *xp_v2* = `xp_candidates(...)["blend"]`.
- **The bundle (section 5, "OWN v XP_V2 AS TESTED"):** our XI (slots 1–11),
  bench order (12–15) and captain under own (the recorded rows, as now) and
  under xp_v2 as tested, side by side; the header says that from GW8 xp_v2
  as tested is the default for XI and captain (ruling point 1), own is
  printed beside it, and vetoes are on hard facts. The keeper line adds each
  keeper's xp_v2. When an input is missing the section prints `missing
  input: ...` and `own picks GW8 (ruling point 1)`; nothing is substituted.
  The S6 forecast on the recorded xg rows leaves the bundle (it is not the
  accepted model).
- **2026/27 GW5–7 (S6c's information print):** the same function on each
  gameweek's newest export generated before its deadline
  (`odds_lambda.pre_deadline_export`), λ from S5's 2026/27 football-data
  book (`tools/odds/E0_2026-27_fetched_2026-10-18.csv`; no Odds API
  snapshot exists before 19 Oct, and S6b's 2025/26 test read football-data
  the same way) and the fallback fitted on results before that deadline;
  printed through S6c's `info_2627` (`--s6c` gains the live column). The
  file was fetched on 18 Oct; its prices are football-data's pre-closing
  prices, stated in the print.
- **Acceptance tests (no metric):** (1) as tested: the core fed S6b's
  inputs equals `Replay.xp_v2` for every player at two toy origins to
  1e-12, and on the real 2025/26 at GW5, 21 and 38 (in the report); (2)
  point-in-time on a toy 2026/27 folder: an export generated after the
  deadline is refused, an odds snapshot taken after the deadline is not
  used, rows of the target gameweek do not move the forecast; (3) the prior
  key: a renamed player finds his own prior through `code`, a player
  without a code row through his exact name, else S11's means; (4) the
  gate and the sub term with chance; (5) the bundle section on a toy
  folder: the side by side, the default line, the keeper line, and
  `missing input` with `own picks GW8` when the odds book or the priors are
  absent; (6) the GW5–7 print with the live column; (7) `run.txt`; nightly
  isolation; `test_fpl.py` untouched.

No re-tuning after viewing results.

## Queue line (Boris, 2026-10-19, verbatim)

2. The live "xp_v2 as tested" forecast (S11 shares in the xg half, bottomup_lambda, current minutes model) in tools/gw_pass.py, beside own: XI, bench and captain. Required for the GW8 switch.

## Ruling (verbatim, from prereg/S6b.md)

RULING S6b acceptance + lanes merge:
1. Boris accepts xp_v2 as tested in S6b (S11 shares in the xg half, S5 bottomup_lambda in the other, current minutes model) for XI and captain from GW8. own keeps being recorded nightly and is printed beside xp_v2 at every deadline; both are compared weekly in grading. Vetoes on hard facts as before. If the live forecast cannot use S11's shares by the GW8 pass, own picks GW8.
2. S6c, a safety check: own_rebuilt = live own's formula with every rebuildable input (form term, minutes-reliability scaling, FDR adjustment from the file's end-of-season FDR), status and chance taken as available for both sides; same squads, metric and bootstrap as S6b. The switch is suspended for GW8 only if the 90% upper bound of (xp_v2 - own_rebuilt) is below 0. Also print 2026/27 GW5-7, recorded own against xp_v2 as tested, as information.
3. Revert rule, fixed now: at the GW10 checkpoint, if the live paired decision metric over GW8-10 has its 90% upper bound below 0, own returns.
4. Lanes merge: this is lane B's last task. Record this ruling verbatim in prereg/S6b.md, write a complete handover in SESSION_STATE_B.md (open items: S6c; the live "xp_v2 as tested" forecast in the bundle; the bundle runs Thursday about 18:00 and Friday morning with files committed under worklog/gw_pass/gw8/; the next landing of S8, S11, S12, S13, S6b, S6c, the bundle and the CLAUDE.md provenance line; Step 14), push lane-b, and stop. Leave C:\GIT\FPL-b and its tools/out untouched.
END RULING
