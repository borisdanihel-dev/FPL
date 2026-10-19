# S6b — the xp_v2 past-season test (2025/26 re-scored under 2026/27 rules)

The chat's ruling, pasted verbatim on 2026-10-19 (received after the landing of
S4, S7, S5, S6 and S9 and the adoption of S11). Queued after S8's record and
re-verification; it needs Step 10 (lane A, landing today) on master for the
re-scoring. The template rows are filled in when the item starts, before any
S6b code, and this file is never edited after any of its evaluation numbers
exist. Offline under `tools/`; point-in-time S4 harness with `hist_pit` clubs;
provenance `run.txt`; verifier on Fable; the usual tests and mutations.

Template rows, filled on 2026-10-19 before any S6b code (the ruling below
governs where they differ):

- **Item:** S6b (the xp_v2 past-season test; BUILD_PLAN.md Step 6's
  past-season validation, ruled on 2026-10-19). Offline, `tools/xp_v2_replay.py`,
  tests in `tests/test_S6b.py`.
- **Hypothesis:** xp_v2 (S6's equal blend, with S5's bottomup_lambda in the
  bottomup half and S11's shares in the xg half) picks better XIs and
  captains than own's rebuildable proxy on 2025/26, in realised points
  under the 2026/27 rules.
- **Data and sample filter:** 2025/26 GW5–38 through the S4 harness
  (`canonical_at`, clubs of the origin, training rounds < t) and the raw
  rows; the season re-scored under the 2026/27 rules by Step 10
  (`python tools/rules.py normalise`, reading `historical/2025-26/`
  `merged_gw.csv` and `players_raw.csv` and `historical/2026-27/`
  `game_config.json` and `elements_positions.csv`, lane A's downloads
  copied with their recorded SHA-256 checked: `412ce017…`, `a72a9908…`,
  `ac3dc891…`); λ per fixture from S5's `Season2526` (the odds book, the
  labelled fallback); 2024/25 only through S11's priors and k. **Squads:**
  S7's 50 synthetic squads (`chips.sample_squads(chips.gw1_candidates(hist),
  50, seed 7)`), fixed all season, no transfers, no chips; XI legality by
  the 2025/26 positions (the season as played); the points by the 2026/27
  re-scoring (`points_2627_rules` per player-gameweek, a double gameweek
  one unit, the reclassified players scored in their 2026/27 position as
  Step 10 does). **Realised points of a squad-gameweek:** the XI by the
  model's projections (`chips.xi_and_bench`), the captain = the highest
  projection in the XI (ties by the lower id) doubled, automatic
  substitutions by `fpl_edge.rule_autosubs` on the re-scored minutes
  (`planner.Replay.realised` with the actuals swapped for the re-scored
  points and minutes).
- **Definitions pinned:**
  - *own_proxy* = `fpl_edge.project_reliability` on the harness's training
    inputs (`reliability_inputs(canonical_through(c, t−1))`), the
    rebuildable source S7 and S8 replayed (the harness's `bottomup`). It
    lacks, exactly, what live `own` (`fpl_edge.project`) uses and 2025/26
    cannot rebuild: (1) the form term — points over the last four
    gameweeks per 90 minutes, shrunk toward the positional prior (or the
    personal prior) by `SHRINK`; (2) the minutes-reliability scaling
    `min(1, mins_last4 / (90 × gameweeks))`; (3) the fixture-difficulty
    adjustment `1 + (3 − FDR) × 0.12` from the pre-deadline ticker; (4)
    `chance_next_round` and `status` (the injury and availability flags).
    own_proxy is a bottom-up expectation (appearance, xGI, clean sheet,
    DEFCON with measured weights); own is a form rate. Stated in every
    output line that names it.
  - *P(start)* = the current minutes model (`reliability_inputs`' `p_start`,
    `starts_last4` over the window); *P(sub)* = appearances without a start
    over the last min(4, t−1) rounds (S6's `sub_inputs` rule on the raw
    rows); *E[pts | sub]* per position = the mean official 2025/26 points of
    sub appearances in the training rounds (what the model saw before the
    deadline; the realised side is re-scored).
  - *bottomup half* E_bl | start = S5's `odds_lambda.forecast_lambda` (the
    harness inputs, the round's fixtures with λ_opp) divided by P(start),
    as S6 does.
  - *xg half* E_xg | start = `project_xg`'s terms conditional on starting,
    with S11's allocation for the attacking rates: goals = xG_player | start
    × GOAL_VALUE[pos] and assists = xA_player | start × 3, where
    xG_player | start = Σ over the round's fixtures of λ_team × shrunk share
    × (mean minutes per start / 90) (S11's forecast without its P(start)
    factor; `shares.Season.origin` row fields), xA likewise; the clean
    sheet = S5's odds-implied P(clean sheet) of each fixture × CS_VALUE[pos]
    (project_xg's FDR table is not rebuildable: stated); appearance 2;
    DEFCON = 2 × the player's hit rate over his 60+-minute training matches
    at the current thresholds (`defcon_expectation`'s rule, forwards 0);
    bonus = 0.8 × the player's ICT percentile among players with minutes in
    the training rounds (merged_gw's `ict_index`, season total). A player
    without an S11 row (no P(start) ≥ 0 inputs) has no xg half: no xp_v2,
    reported, never substituted.
  - *xp_v2* = P(start) × (E_xg + E_bl) / 2 + P(sub) × E[pts | sub] — S6's
    `xp_candidates(...)["blend"]`, the equal blend as frozen.
  - *Realised points* per player-gameweek = `points_2627_rules`; minutes
    from the same file; a player without a row that round: 0 points, 0
    minutes.
- **Comparison:** per gameweek and squad, the realised points of the XI and
  captain chosen by xp_v2 minus those chosen by own_proxy; the same squad,
  the same re-scored outcomes.
- **Primary metric (one, decision-based):** per gameweek the mean over the
  50 squads of (xp_v2 − own_proxy) realised points; the season figure =
  the sum over GW5–38 of the per-gameweek means (points per squad per
  season). Printed per gameweek and per season.
- **Secondary metrics (information only):** per gameweek among predicted
  starters (P(start) ≥ 0.8 with a fixture) the tie-corrected Spearman of
  each model's forecast against the re-scored points, paired (xp_v2 −
  own_proxy); the MAE likewise; the share of squad-gameweeks where the two
  models choose the same XI and the same captain.
- **Bootstrap:** unit = gameweek (a block of its 50 squad differences),
  10,000 resamples of the 34 per-gameweek means, 90% percentile interval,
  seed 20261018 (`backtest.bootstrap_mean`).
- **Pass threshold:** the 90% lower bound of the mean per-gameweek
  difference > 0. On PASS, adoption needs Boris's acceptance in chat
  (ruling 5).
- **Acceptance tests (in addition):** the re-scored actuals drive the
  realised points (a mutation reading the official points → red); the xg
  half's terms on a hand case (goals, assists, clean sheet, appearance,
  DEFCON, bonus, with S11's rates); the equal blend; own_proxy equal to the
  harness's bottomup forecast for the same player and round; the XI,
  captain and autosubs on a hand squad under two projections; point-in-time
  (rows and odds of rounds ≥ t altered leave origin t's two forecasts
  unchanged; training through t → red; the re-scored file is read for
  outcomes only); the bootstrap and the pass line; `run.txt`; CLI
  `python tools/xp_v2_replay.py --test`; nightly isolation; `test_fpl.py`
  untouched.

No re-tuning after viewing results.

## Ruling (verbatim)

RULING S6b (xp_v2 past-season test), queued after S8; needs Step 10 on master (landing today):
1. Season 2025/26 GW5-38, re-scored under 2026/27 rules by Step 10; point-in-time S4 harness, hist_pit clubs, provenance run.txt.
2. Comparator own_proxy = project_reliability (the rebuildable source used in S7 and S8); state exactly which own inputs it lacks. Candidate = xp_v2 as frozen in S6 (equal blend), with S5's bottomup_lambda in the bottomup half and S11's shares in the xg half; P(start) from the current minutes model.
3. Primary, decision-based: on S7's 50 squads (seed 7), fixed squads, no transfers, no chips, each model picks its best legal XI and captain every gameweek; realised points with rule_autosubs and the captain doubled. Per gameweek, the mean over squads of (xp_v2 - own_proxy); block bootstrap over gameweeks (B = 10,000, fixed seed), 90%. Pass: lower bound > 0. Print the mean per gameweek and per season.
4. Secondary, printed only: per-GW Spearman among starters and MAE among starters, paired.
5. On PASS, adoption needs Boris's acceptance in chat. The chat would then propose switching XI and captain to xp_v2 from the next deadline, with own printed beside it and the live GW7-10 numbers checked at the GW10 checkpoint.
Prereg first with this ruling verbatim, verifier on Fable, usual tests and mutations.
END RULING
