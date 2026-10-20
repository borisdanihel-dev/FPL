# S6e — xp_v2 + saves: the goalkeepers' save points

Committed before any S6e code. The ruling is item F-E of RULINGS PART F (19
Oct 2026), verbatim at the end. Offline under `tools/`; the nightly imports
nothing of it. Adoption at the GW10 checkpoint at the earliest (the ruling),
and only after its test passes and Boris accepts. Never edited after any of
its evaluation numbers exist.

- **Item:** S6e (Part F, F-E; the GW10-checkpoint item "xp_v2 + saves" of
  RULING 19 Oct afternoon point 1). `tools/xp_v2_saves.py`; tests in
  `tests/test_S6e.py`.
- **Hypothesis:** adding the expected save points to the goalkeepers'
  xp_v2 picks starting keepers who score more.
- **Data and sample filter (2025/26 first):**
  - 2025/26 GW5–38 through S6b's replay (`tools/xp_v2_replay.py`: the S4
    harness, `canonical_at`, clubs of the origin, training rounds < t, S5's
    λ, S11's priors and k from 2024/25);
  - outcomes = Step 10's re-score under the 2026/27 rules
    (`points_2627_rules`, minutes);
  - squads = S7's 50 (`chips.sample_squads`, seed 7), fixed all season,
    each with its two keepers.
  - The 2024/25 run (F-C done) needs S6b's replay generalised to another
    season. That work is shared with F-D, which is parked on a question
    (`worklog/SESSION_STATE_A.md`), so it comes second, under this same
    prereg, once the harness serves 2024/25.
- **Definitions pinned:**
  - *E[saves | start]* for a goalkeeper at origin t = (Z × his saves per
    90 + (1 − Z) × the positional mean saves per 90) × (minutes per start
    / 90), summed over the round's fixtures with each fixture weighted by
    λ_opp,f / λ̄_t.
    - His saves per 90 come from his training rows (rounds < t).
    - The positional mean is over every goalkeeper with minutes in the
      training rounds (minutes-weighted).
    - Z = m / (m + k): m = his training minutes / 90; k by S11's
      split-half method (`shares.credibility_k`'s rule) on 2024/25's
      goalkeeper saves per 90 (odd against even gameweeks), the prior
      season as S11.
    - λ_opp,f = S5's λ of the opponent in fixture f; λ̄_t = the mean λ over
      every side of round t's fixtures.
    - Minutes per start as S6b's.
  - *E[save points | start]* = E[saves | start] / 3 (the ruling's form).
  - *xp_v2 + saves* = xp_v2 as tested (S6b's `Replay.xp_v2`, unchanged) +
    P(start) × E[save points | start] for goalkeepers; every other player
    unchanged.
  - *The keeper choice:* per squad-gameweek, the starting keeper = the
    squad's goalkeeper with the higher forecast (ties by the lower id),
    under xp_v2 and under xp_v2 + saves.
  - *Realised keeper points* = the re-scored points of the chosen keeper,
    or of the other keeper if the chosen one did not play and the other did
    (FPL's automatic substitution of a keeper); 0 if neither played.
- **Comparison:** per squad-gameweek, realised keeper points under xp_v2
  + saves minus under xp_v2 (0 where both choose the same keeper).
- **Primary metric (one):** per gameweek the mean over the 50 squads of
  that difference.
- **Secondary metrics (information only):**
  - the MAE of keeper points (forecast against re-scored points) among
    goalkeepers with P(start) ≥ 0.8, per model, paired;
  - the share of squad-gameweeks where the choice differs;
  - k and the positional mean.
- **Bootstrap:** unit = gameweek (block bootstrap), 10,000 resamples of the
  34 per-gameweek means, 90% percentile interval, seed 20261018.
- **Pass threshold:** the 90% lower bound of the primary > 0, on 2025/26
  (and, when it runs, separately on 2024/25). Adoption at the GW10
  checkpoint at the earliest, with Boris's acceptance.
- **Acceptance tests:**
  - E[saves | start] by hand (the shrink, Z with k, minutes per start, the
    λ ratio);
  - outfield players unchanged;
  - the keeper choice and its tie rule;
  - the realised points with the substitution case;
  - point-in-time: rows of rounds ≥ t altered leave origin t unchanged;
  - the bootstrap and the pass line;
  - `run.txt`; the CLI; nightly isolation; `test_fpl.py` untouched.

No re-tuning after viewing results.

## Ruling (verbatim, RULINGS PART F, item F-E)

F-E. S6e (xp_v2 + saves): for goalkeepers add E[save points | start] = E[saves] / 3, E[saves] = the keeper's saves per 90 shrunk to the positional mean (S11's credibility method) x (lambda_opp / league mean lambda). Test on 2025/26, and on 2024/25 after F-C: per squad-gameweek, the starting keeper chosen by xp_v2 v by xp_v2 + saves; realised keeper points paired; block bootstrap over gameweeks; pass: 90% lower bound > 0. Secondary: MAE of keeper points. Adoption at the GW10 checkpoint at the earliest.
