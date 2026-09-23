# HISTORICAL VALIDATION — plan of work

Written 2026-09-14. Takes priority over most of `BUILD_SPEC.md`, for one reason:

> On four gameweeks we cannot tell whether `bottomup` fails because the
> **architecture is wrong** or because the **sample is too small**. A full past
> season separates those two, today, instead of in March.

Read alongside `BUILD_SPEC.md` (the model and the reliability harness) and
`BACKLOG.md` Part 3 (what is green/amber/red).

---

## The question this answers

Run the reliability-weighted model over a completed season, gameweek by
gameweek, and score it against the same baselines.

- **Beats `minutes` with 20+ gameweeks of training** → the architecture is
  sound, this season is just young. Keep building, expect it to start working
  around GW12–15.
- **Still loses with a full season** → the architecture is wrong. Stop. Use
  `minutes` and spend the effort on the mini-league layer instead.

Either answer is worth more than another week of GW5 data.

---

## Split by position. This is not optional.

**Attackers transfer cleanly.** Goals, assists and appearance points are
unchanged between seasons. A MID/FWD result from 2025/26 is a true statement
about 2026/27.

**Defenders do not.** Defensive contribution arrived in 2025/26, and the
2026/27 BPS changes all postdate it: CBI dropped from 1 BPS per 2 actions to
1 per 3, the −1 for being tackled was removed, goalkeeper saves were reworked
to a flat 2 BPS with a big-chance bonus. A defender model validated on last
season is validated against rules that no longer exist.

**Therefore: if the model beats `minutes` for MID and FWD but not for DEF,
that is a PASS, not a mixed result.** The defensive half needs this season's
data and cannot be shortcut. Report every figure per position. A single
combined number blurs the one distinction that matters.

---

## Step 1 — get the data and verify it before trusting it

Source: `github.com/vaastav/Fantasy-Premier-League` — per-gameweek player data
by season. Both papers use it (Ramezani & Dinh trained on GW1–26 of 2023/24 and
tested on GW27–38; OpenFPL used four seasons).

**Verify before building anything on it:**

- Does 2025/26 carry `defensive_contribution` per gameweek? If not, the DEF
  half of this exercise is impossible and only the attacker result stands.
- Are `expected_goals` and `expected_assists` populated? The FPL API only began
  publishing these around 2022/23. Earlier seasons would need Understat.
- Does it carry opponent, venue and fixture difficulty per player-gameweek?
  The model needs opponent to compute the Poisson clean-sheet term.
- Do minutes, starts and points reconcile against a handful of known results?
  Spot-check five players you can verify independently.

**If any of these are missing, say so and stop rather than substituting.** A
fabricated input produced the reversed FDR finding earlier in this project.

Keep it in a separate folder. Do not mix it into `fpl.sqlite`.

---

## Step 2 — measure reliability on that season, fresh

**Do not carry over our weights.** The 0.648 for xG+xA and 0.725 for DEFCON
come from four gameweeks of 2026/27. Over a full season reliability will be
substantially higher, and reusing our figures would understate what the model
can do with real training data.

Same method as `BUILD_SPEC.md` §1: odd versus even gameweeks, per-90 rates,
tie-corrected Spearman, Spearman–Brown to full-sample reliability, interval on
every figure.

**Report reliability as a function of training window** — recompute at 4, 8,
12, 20 and 38 gameweeks. That curve is itself a finding: it tells us when each
metric becomes usable, which is the number we have been guessing at all along.

---

## Step 3 — rolling-origin backtest

For each gameweek `t` from 5 to 38:

- train on gameweeks `1 … t-1`
- predict gameweek `t`
- score against actual

**Leakage rules, non-negotiable:**

- No same-gameweek outcome as an input — no points, bonus, BPS, goals, clean
  sheets, minutes from the target week.
- Reliability weights computed from the training window only. Recomputed each
  `t`, never from the whole season.
- Priors from the training window only.

Both papers guard this explicitly; Ramezani & Dinh list the exact fields they
exclude.

---

## Step 4 — score against the same four baselines

Identical to `BUILD_SPEC.md` §3, so the results are directly comparable:

| source | what it is |
|---|---|
| `minutes` | P(start) alone. **The bar.** |
| `points` | recent points per 90. The known-failing control. |
| `xgi` | xG+xA per 90 alone. |
| `bottomup` | the reliability-weighted model. |

**Report per gameweek and cumulatively, per position, with intervals:**

- tie-corrected Spearman, whole population, blanks counted as 0
- tie-corrected Spearman, **players who featured only** (60+ minutes) — this
  answers "how well do the starters do", which is what a captaincy or transfer
  decision needs, and it is a different question from "who blanks"
- MAE against a constant predictor
- rho as a function of training-window length

That last one is the headline output. **If rho rises with training window and
crosses `minutes` somewhere around GW12–20, we know what to expect this
season and roughly when.**

---

## Step 5 — the ablation

Strip the model to P(start) alone, then add one term at a time:

1. P(start) only
2. \+ xGI term
3. \+ clean sheet term
4. \+ DEFCON term

Report rho after each. **Any term that does not move rho is decoration and
should come out.** On four gameweeks the whole model was worth roughly what
P(start) was worth alone — this tells us whether that holds with real data or
was a sample-size artifact.

Do this per position too. The clean sheet term should matter for DEF and GK and
not at all for FWD; if it does not behave that way, something is wrong in the
implementation rather than the theory.

---

## Step 6 — what to do with the answer

Write the result into `CHANGELOG.md` with the numbers, then:

- **`bottomup` beats `minutes` for MID/FWD with 20+ GWs** → build it per
  `BUILD_SPEC.md`, expect it to start earning around the crossover point, and
  use `minutes` until then.
- **It never beats `minutes` at any window** → stop building projections. Use
  `minutes` for exclusion, and put the effort into the mini-league layer, which
  is the part no public tool does.
- **Mixed by position** → use it where it wins, `minutes` where it does not.
  A model does not have to work everywhere to be worth having.

---

## Still frozen before Friday, regardless

None of this changes the GW5 commitment. Before **Fri 18 Sep 19:30 CEST**:

- definitions committed to `CHANGELOG.md`, timestamped
- all four sources logged for GW5

That is cheap and independent. The historical work tells us what to expect;
the GW5 log is what actually tests it on this season's rules.

---

## Testing standard

As ever, and it has caught every real bug here:

- Reintroduce each fixed bug, confirm the intended test goes red.
- Assert on behaviour, not source text.
- No conditional guards that let a test skip its own assertion.
- Every correlation printed with its interval.
- If an input is missing, say so and stop. Never substitute a stand-in.

---

## Horizon test — result (appended 2026-09-23 18:27:53 UTC, code commit `5a9ec05`)

Run: `python fpl_hist.py historical/2025-26 --season 2025/26 --horizon`, 7 s. Definition as pre-registered in `9b43a78` (2026-09-14 18:08 CEST), unchanged; the definition block is reproduced at the top of the output. No pass criterion was set, so none is applied; the table is the result. Rows pooled by training window as in Steps 3–5, plus one all-origins row per position, labelled `all`.

```
HORIZON TEST  2025/26  origins GW5-38
  Pre-registered 2026-09-14 (commit 9b43a78), run without change:
    For H in {1, 2, 4, 6, 8, 12}, on 2025/26 with the rolling-origin harness:
    train on GW1..t-1; predict the SUM of points over GW t..t+H-1 with the SUM
    of per-fixture bottomup projections over the same gameweeks, fixture
    pairings taken as known in advance and results not; minutes-H = P(start)
    times the number of fixtures in the horizon. Whole population with blanks
    as 0, per position, tie-corrected Spearman with intervals, pooled by
    training window as in Steps 3-5. A player is in the population if he
    passes the usual gate at t and his team has at least one fixture in the
    horizon.
  Implementation detail, not a redefinition: an origin t is used for a given H
  only when t+H-1 <= GW38, so every graded horizon is complete.

==============================================================================
H = 1   sum over GW t..t+0   origins GW5-38 (34)
==============================================================================
  training    pos       n     bottomup-H rho, 95%      minutes-H rho, 95%
  GW 4-7      ALL    1359   +0.335 +0.282..+0.388   +0.332 +0.279..+0.385
  GW 4-7      GK      101   +0.407 +0.211..+0.603   +0.449 +0.253..+0.645
  GW 4-7      DEF     480   +0.331 +0.242..+0.421   +0.312 +0.223..+0.402
  GW 4-7      MID     651   +0.351 +0.274..+0.428   +0.337 +0.260..+0.414
  GW 4-7      FWD     127   +0.479 +0.305..+0.654   +0.457 +0.283..+0.632

  GW 8-11     ALL    1306   +0.374 +0.319..+0.428   +0.378 +0.324..+0.433
  GW 8-11     GK       89   +0.372 +0.163..+0.581   +0.454 +0.245..+0.663
  GW 8-11     DEF     466   +0.453 +0.362..+0.543   +0.425 +0.334..+0.516
  GW 8-11     MID     610   +0.392 +0.312..+0.471   +0.366 +0.287..+0.446
  GW 8-11     FWD     141   +0.387 +0.221..+0.553   +0.383 +0.217..+0.549

  GW12-19     ALL    2619   +0.273 +0.235..+0.311   +0.271 +0.233..+0.310
  GW12-19     GK      179   +0.364 +0.217..+0.511   +0.353 +0.206..+0.500
  GW12-19     DEF     957   +0.285 +0.222..+0.348   +0.260 +0.197..+0.324
  GW12-19     MID    1200   +0.301 +0.244..+0.357   +0.286 +0.229..+0.343
  GW12-19     FWD     283   +0.292 +0.176..+0.409   +0.288 +0.171..+0.405

  GW20-37     ALL    5755   +0.318 +0.293..+0.344   +0.318 +0.293..+0.344
  GW20-37     GK      425   +0.393 +0.298..+0.488   +0.416 +0.321..+0.511
  GW20-37     DEF    2137   +0.334 +0.291..+0.376   +0.312 +0.270..+0.355
  GW20-37     MID    2530   +0.334 +0.295..+0.373   +0.319 +0.280..+0.358
  GW20-37     FWD     663   +0.347 +0.271..+0.423   +0.346 +0.270..+0.422

  GW 4-37 all ALL   11039   +0.317 +0.298..+0.336   +0.317 +0.298..+0.336
  GW 4-37 all GK      794   +0.391 +0.321..+0.460   +0.416 +0.346..+0.485
  GW 4-37 all DEF    4040   +0.336 +0.305..+0.367   +0.313 +0.282..+0.344
  GW 4-37 all MID    4991   +0.335 +0.308..+0.363   +0.320 +0.292..+0.348
  GW 4-37 all FWD    1214   +0.355 +0.298..+0.411   +0.349 +0.293..+0.406

==============================================================================
H = 2   sum over GW t..t+1   origins GW5-37 (33)
==============================================================================
  training    pos       n     bottomup-H rho, 95%      minutes-H rho, 95%
  GW 4-7      ALL    1359   +0.371 +0.318..+0.425   +0.353 +0.300..+0.406
  GW 4-7      GK      101   +0.464 +0.268..+0.660   +0.493 +0.297..+0.689
  GW 4-7      DEF     480   +0.360 +0.270..+0.449   +0.327 +0.238..+0.417
  GW 4-7      MID     651   +0.403 +0.326..+0.480   +0.374 +0.297..+0.451
  GW 4-7      FWD     127   +0.470 +0.295..+0.645   +0.428 +0.253..+0.603

  GW 8-11     ALL    1306   +0.414 +0.360..+0.469   +0.412 +0.357..+0.466
  GW 8-11     GK       89   +0.434 +0.225..+0.643   +0.460 +0.251..+0.669
  GW 8-11     DEF     466   +0.467 +0.376..+0.558   +0.440 +0.349..+0.531
  GW 8-11     MID     610   +0.440 +0.360..+0.519   +0.415 +0.335..+0.494
  GW 8-11     FWD     141   +0.398 +0.232..+0.564   +0.382 +0.216..+0.547

  GW12-19     ALL    2619   +0.309 +0.270..+0.347   +0.297 +0.259..+0.335
  GW12-19     GK      179   +0.429 +0.283..+0.576   +0.401 +0.254..+0.548
  GW12-19     DEF     957   +0.350 +0.286..+0.413   +0.309 +0.246..+0.372
  GW12-19     MID    1200   +0.313 +0.256..+0.369   +0.293 +0.236..+0.350
  GW12-19     FWD     283   +0.289 +0.173..+0.406   +0.288 +0.171..+0.404

  GW20-37     ALL    5579   +0.353 +0.327..+0.379   +0.344 +0.318..+0.370
  GW20-37     GK      412   +0.464 +0.367..+0.560   +0.454 +0.357..+0.551
  GW20-37     DEF    2068   +0.375 +0.331..+0.418   +0.347 +0.304..+0.390
  GW20-37     MID    2460   +0.361 +0.322..+0.401   +0.339 +0.299..+0.378
  GW20-37     FWD     639   +0.353 +0.275..+0.430   +0.341 +0.263..+0.419

  GW 4-37 all ALL   10863   +0.353 +0.334..+0.372   +0.343 +0.324..+0.362
  GW 4-37 all GK      781   +0.455 +0.385..+0.525   +0.452 +0.382..+0.522
  GW 4-37 all DEF    3971   +0.378 +0.347..+0.410   +0.347 +0.316..+0.378
  GW 4-37 all MID    4921   +0.364 +0.336..+0.392   +0.343 +0.315..+0.371
  GW 4-37 all FWD    1190   +0.357 +0.300..+0.414   +0.342 +0.285..+0.399

==============================================================================
H = 4   sum over GW t..t+3   origins GW5-35 (31)
==============================================================================
  training    pos       n     bottomup-H rho, 95%      minutes-H rho, 95%
  GW 4-7      ALL    1359   +0.419 +0.366..+0.472   +0.382 +0.329..+0.436
  GW 4-7      GK      101   +0.539 +0.343..+0.735   +0.506 +0.310..+0.702
  GW 4-7      DEF     480   +0.404 +0.314..+0.493   +0.346 +0.257..+0.436
  GW 4-7      MID     651   +0.461 +0.384..+0.538   +0.422 +0.345..+0.499
  GW 4-7      FWD     127   +0.456 +0.282..+0.631   +0.403 +0.228..+0.577

  GW 8-11     ALL    1306   +0.433 +0.379..+0.487   +0.416 +0.362..+0.471
  GW 8-11     GK       89   +0.440 +0.231..+0.649   +0.463 +0.254..+0.672
  GW 8-11     DEF     466   +0.457 +0.366..+0.548   +0.419 +0.328..+0.510
  GW 8-11     MID     610   +0.480 +0.401..+0.560   +0.438 +0.359..+0.517
  GW 8-11     FWD     141   +0.415 +0.249..+0.580   +0.401 +0.235..+0.567

  GW12-19     ALL    2619   +0.313 +0.275..+0.352   +0.293 +0.255..+0.331
  GW12-19     GK      179   +0.465 +0.318..+0.612   +0.387 +0.240..+0.534
  GW12-19     DEF     957   +0.356 +0.292..+0.419   +0.299 +0.235..+0.362
  GW12-19     MID    1200   +0.312 +0.256..+0.369   +0.284 +0.227..+0.340
  GW12-19     FWD     283   +0.299 +0.182..+0.416   +0.297 +0.180..+0.413

  GW20-37     ALL    4912   +0.375 +0.348..+0.403   +0.353 +0.325..+0.381
  GW20-37     GK      363   +0.507 +0.404..+0.610   +0.467 +0.364..+0.570
  GW20-37     DEF    1824   +0.396 +0.350..+0.442   +0.357 +0.311..+0.403
  GW20-37     MID    2167   +0.379 +0.337..+0.421   +0.344 +0.302..+0.386
  GW20-37     FWD     558   +0.384 +0.301..+0.467   +0.351 +0.268..+0.434

  GW 4-37 all ALL   10196   +0.374 +0.355..+0.393   +0.352 +0.332..+0.371
  GW 4-37 all GK      732   +0.498 +0.426..+0.571   +0.459 +0.386..+0.531
  GW 4-37 all DEF    3727   +0.397 +0.365..+0.430   +0.351 +0.318..+0.383
  GW 4-37 all MID    4628   +0.385 +0.356..+0.414   +0.353 +0.324..+0.382
  GW 4-37 all FWD    1109   +0.371 +0.313..+0.430   +0.345 +0.286..+0.403

==============================================================================
H = 6   sum over GW t..t+5   origins GW5-33 (29)
==============================================================================
  training    pos       n     bottomup-H rho, 95%      minutes-H rho, 95%
  GW 4-7      ALL    1359   +0.442 +0.388..+0.495   +0.396 +0.343..+0.450
  GW 4-7      GK      101   +0.591 +0.395..+0.787   +0.521 +0.325..+0.717
  GW 4-7      DEF     480   +0.438 +0.349..+0.528   +0.358 +0.268..+0.448
  GW 4-7      MID     651   +0.497 +0.420..+0.574   +0.452 +0.375..+0.529
  GW 4-7      FWD     127   +0.412 +0.237..+0.587   +0.344 +0.170..+0.519

  GW 8-11     ALL    1306   +0.449 +0.395..+0.504   +0.419 +0.365..+0.474
  GW 8-11     GK       89   +0.529 +0.320..+0.738   +0.492 +0.283..+0.701
  GW 8-11     DEF     466   +0.473 +0.382..+0.564   +0.418 +0.327..+0.508
  GW 8-11     MID     610   +0.491 +0.412..+0.571   +0.442 +0.363..+0.522
  GW 8-11     FWD     141   +0.427 +0.261..+0.592   +0.419 +0.253..+0.584

  GW12-19     ALL    2619   +0.316 +0.278..+0.354   +0.290 +0.251..+0.328
  GW12-19     GK      179   +0.475 +0.328..+0.622   +0.361 +0.214..+0.508
  GW12-19     DEF     957   +0.354 +0.290..+0.417   +0.284 +0.221..+0.348
  GW12-19     MID    1200   +0.308 +0.251..+0.364   +0.269 +0.212..+0.325
  GW12-19     FWD     283   +0.363 +0.247..+0.480   +0.354 +0.237..+0.471

  GW20-37     ALL    4256   +0.397 +0.367..+0.427   +0.374 +0.344..+0.404
  GW20-37     GK      311   +0.489 +0.378..+0.600   +0.453 +0.341..+0.564
  GW20-37     DEF    1590   +0.425 +0.376..+0.475   +0.385 +0.336..+0.434
  GW20-37     MID    1871   +0.401 +0.356..+0.446   +0.359 +0.314..+0.405
  GW20-37     FWD     484   +0.401 +0.312..+0.490   +0.367 +0.278..+0.457

  GW 4-37 all ALL    9540   +0.390 +0.370..+0.410   +0.362 +0.342..+0.383
  GW 4-37 all GK      680   +0.513 +0.438..+0.588   +0.451 +0.376..+0.526
  GW 4-37 all DEF    3493   +0.418 +0.385..+0.451   +0.361 +0.328..+0.395
  GW 4-37 all MID    4332   +0.400 +0.370..+0.430   +0.362 +0.332..+0.391
  GW 4-37 all FWD    1035   +0.392 +0.331..+0.453   +0.363 +0.302..+0.424

==============================================================================
H = 8   sum over GW t..t+7   origins GW5-31 (27)
==============================================================================
  training    pos       n     bottomup-H rho, 95%      minutes-H rho, 95%
  GW 4-7      ALL    1359   +0.453 +0.400..+0.506   +0.404 +0.351..+0.457
  GW 4-7      GK      101   +0.592 +0.396..+0.788   +0.505 +0.309..+0.701
  GW 4-7      DEF     480   +0.480 +0.390..+0.569   +0.392 +0.303..+0.482
  GW 4-7      MID     651   +0.499 +0.422..+0.576   +0.453 +0.376..+0.530
  GW 4-7      FWD     127   +0.337 +0.163..+0.512   +0.266 +0.092..+0.441

  GW 8-11     ALL    1306   +0.452 +0.398..+0.507   +0.415 +0.360..+0.469
  GW 8-11     GK       89   +0.573 +0.364..+0.782   +0.514 +0.305..+0.723
  GW 8-11     DEF     466   +0.493 +0.402..+0.584   +0.422 +0.331..+0.513
  GW 8-11     MID     610   +0.475 +0.396..+0.554   +0.422 +0.342..+0.501
  GW 8-11     FWD     141   +0.430 +0.265..+0.596   +0.426 +0.260..+0.592

  GW12-19     ALL    2619   +0.338 +0.299..+0.376   +0.307 +0.269..+0.345
  GW12-19     GK      179   +0.499 +0.352..+0.646   +0.332 +0.185..+0.479
  GW12-19     DEF     957   +0.378 +0.314..+0.441   +0.299 +0.236..+0.363
  GW12-19     MID    1200   +0.328 +0.271..+0.385   +0.285 +0.228..+0.341
  GW12-19     FWD     283   +0.372 +0.255..+0.488   +0.363 +0.246..+0.480

  GW20-37     ALL    3596   +0.403 +0.370..+0.435   +0.376 +0.343..+0.408
  GW20-37     GK      259   +0.453 +0.331..+0.575   +0.390 +0.268..+0.512
  GW20-37     DEF    1344   +0.428 +0.375..+0.481   +0.380 +0.327..+0.434
  GW20-37     MID    1585   +0.408 +0.359..+0.457   +0.363 +0.314..+0.412
  GW20-37     FWD     408   +0.436 +0.338..+0.533   +0.398 +0.301..+0.495

  GW 4-37 all ALL    8880   +0.400 +0.379..+0.421   +0.367 +0.347..+0.388
  GW 4-37 all GK      628   +0.511 +0.433..+0.590   +0.414 +0.336..+0.492
  GW 4-37 all DEF    3247   +0.435 +0.401..+0.470   +0.368 +0.334..+0.402
  GW 4-37 all MID    4046   +0.405 +0.374..+0.436   +0.364 +0.333..+0.395
  GW 4-37 all FWD     959   +0.401 +0.338..+0.464   +0.373 +0.310..+0.436

==============================================================================
H = 12  sum over GW t..t+11   origins GW5-27 (23)
==============================================================================
  training    pos       n     bottomup-H rho, 95%      minutes-H rho, 95%
  GW 4-7      ALL    1359   +0.453 +0.400..+0.506   +0.411 +0.358..+0.465
  GW 4-7      GK      101   +0.564 +0.368..+0.760   +0.514 +0.318..+0.710
  GW 4-7      DEF     480   +0.493 +0.403..+0.582   +0.410 +0.321..+0.500
  GW 4-7      MID     651   +0.475 +0.399..+0.552   +0.436 +0.360..+0.513
  GW 4-7      FWD     127   +0.388 +0.213..+0.562   +0.336 +0.162..+0.511

  GW 8-11     ALL    1306   +0.464 +0.410..+0.518   +0.425 +0.371..+0.479
  GW 8-11     GK       89   +0.556 +0.347..+0.764   +0.474 +0.265..+0.683
  GW 8-11     DEF     466   +0.526 +0.435..+0.617   +0.450 +0.359..+0.541
  GW 8-11     MID     610   +0.462 +0.382..+0.541   +0.412 +0.333..+0.492
  GW 8-11     FWD     141   +0.453 +0.287..+0.619   +0.444 +0.278..+0.609

  GW12-19     ALL    2619   +0.370 +0.332..+0.408   +0.333 +0.294..+0.371
  GW12-19     GK      179   +0.571 +0.424..+0.718   +0.290 +0.143..+0.437
  GW12-19     DEF     957   +0.439 +0.376..+0.503   +0.352 +0.289..+0.416
  GW12-19     MID    1200   +0.343 +0.287..+0.400   +0.295 +0.238..+0.352
  GW12-19     FWD     283   +0.369 +0.252..+0.485   +0.371 +0.254..+0.487

  GW20-37     ALL    2292   +0.401 +0.360..+0.442   +0.370 +0.329..+0.411
  GW20-37     GK      163   +0.482 +0.328..+0.636   +0.347 +0.193..+0.501
  GW20-37     DEF     865   +0.444 +0.377..+0.510   +0.393 +0.326..+0.460
  GW20-37     MID    1008   +0.373 +0.312..+0.435   +0.326 +0.264..+0.388
  GW20-37     FWD     256   +0.488 +0.365..+0.610   +0.449 +0.327..+0.572

  GW 4-37 all ALL    7576   +0.412 +0.389..+0.434   +0.376 +0.353..+0.398
  GW 4-37 all GK      532   +0.541 +0.456..+0.626   +0.385 +0.300..+0.470
  GW 4-37 all DEF    2768   +0.470 +0.433..+0.507   +0.395 +0.358..+0.432
  GW 4-37 all MID    3469   +0.396 +0.362..+0.429   +0.353 +0.320..+0.387
  GW 4-37 all FWD     807   +0.427 +0.358..+0.496   +0.404 +0.335..+0.473

```
