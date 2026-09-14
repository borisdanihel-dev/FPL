# BUILD SPEC — reliability-weighted projection + honest baselines

Written 2026-09-14. **Must be frozen and logged before the GW5 deadline,
Fri 18 Sep 19:30 CEST.** After that GW5 is no longer a clean test.

Companion to `CLAUDE.md`, `BACKLOG.md`, `CHANGELOG.md`.

---

## 0. The point of this document

Everything below is secondary to one idea:

> **A metric that does not correlate with itself cannot predict anything else.**

Measure that correlation. Use it as the weight. Never guess it.

Three projection attempts have already failed because they weighted inputs by
intuition. `SHRINK = 4.0` is a number I picked; it has no empirical basis.
Replace it everywhere with a measured quantity.

---

## 1. P0 — the reliability harness (build this first)

Nothing else in this document is meaningful until this exists, because every
weight downstream comes out of it.

### 1.1 `measure_reliability(d, metrics, min_mins=45)`

For each metric, split every player's season into **odd gameweeks** and **even
gameweeks**, compute the per-90 rate in each half, and correlate the two halves
across players with a **tie-corrected Spearman** (see §1.3).

Odd/even rather than first-half/second-half: it removes trend, form drift and
fixture-run effects, which would otherwise contaminate the estimate.

Then convert the half-season correlation to a full-sample reliability using
Spearman–Brown:

```
r_full = 2 * r_half / (1 + r_half)
```

Return, per metric: `n`, `r_half`, `r_full`, and a 95% interval
(`± 1.96 / sqrt(n-1)`).

**Metrics to measure, at minimum:** `pts`, `xg`, `xa`, `xg+xa`, `bps`,
`defcon`, and `minutes`.

**`minutes` must be handled separately.** It cannot be expressed per 90 — that
divides minutes by minutes and yields a constant for everyone. I made exactly
this mistake and it reported rho 0.000, which would have been read as "minutes
carry no signal" when corrected it is 0.784, the strongest measurement in the
game. Measure total minutes per half, over the whole population, with
non-featuring players counted as zero.

**Write a test that a constant-valued metric returns rho 0 and is reported as
undefined, not as a finding.**

### 1.2 Baseline measurements, for regression-testing the harness

From GW1–4 of this season (n=242 for per-90 metrics, n=399 for minutes):

| metric | r_half | r_full | weight on observed |
|---|---|---|---|
| minutes | 0.784 | 0.879 | 88% |
| DEFCON | 0.569 | 0.725 | 73% |
| xG+xA | 0.479 | 0.648 | 65% |
| xA | 0.435 | 0.606 | 61% |
| xG | 0.433 | 0.604 | 60% |
| BPS | 0.227 | 0.370 | 37% |
| **points** | **0.153** | **0.265** | **27%** |

Points is the least reliable input available and is what every failed attempt
was built on. **The model must contain no points term anywhere.**

These figures are a sanity check, not constants to hardcode. Reliability rises
with sample size; recompute every gameweek.

### 1.3 Tie-corrected Spearman (R1 in `BACKLOG.md`)

Required before any of the above means anything. Average ranks for ties. The
existing `_spearman` assigns ordinal ranks in input order, and
`player_gw_recent` is sorted `total_points DESC`, so ties break in a way that
is correlated with the prediction. Same data, different row order, produced
−0.112 to +0.097.

**Test: shuffling input order must not change rho.** Mutate the ranker back and
confirm that test fails.

---

## 2. The model — `project_reliability()`

Every term is a scoring rule multiplied by a measured probability. No fitted
weights, so every line can be argued with individually.

```
xP =  2.0 * P(start)
    + xGI_shrunk * 0.62 * GOAL_VALUE[pos] * P(start)
    + xGI_shrunk * 0.38 * 3.0             * P(start)
    + P(clean_sheet) * CS_VALUE[pos]      * P(start)
    + 2.0 * P(defcon_threshold)           * P(start)
```

`GOAL_VALUE = {GK:6, DEF:6, MID:5, FWD:4}`,
`CS_VALUE = {GK:4, DEF:4, MID:1, FWD:0}`.

### 2.1 Shrinkage — the core of the whole thing

For every rate metric:

```
estimate = observed_rate * r_full + positional_prior * (1 - r_full)
```

where `r_full` comes from §1.1, **computed this gameweek, not hardcoded**, and
the positional prior is the median rate among players with 180+ minutes.

Shrink the **components**, never the output. Pulling final points toward last
season's points-per-game is precisely what we tested and measured making things
worse (MAE 2.47 → 2.55).

### 2.2 Clean sheets — Poisson, not FDR buckets

```
lambda = team_goals_conceded_per_match * (opponent_xG_per_match / league_mean_xG)
P(clean_sheet) = exp(-lambda)
```

Continuous rather than four buckets, and a proper probability model.

Build it only from **measured** team rates. Do not use `teams.att_h/att_a/
def_h/def_a` — that is FPL's 1000–1400 strength scale, set pre-season.
Do not use `all_players.xgc`, which is a player's on-pitch expected goals
conceded, not a team rate.

Ramezani & Dinh (arXiv 2505.02170) found xGC has the weakest association with
points of any feature they tested, and their attack-minus-defence surrogate
underperformed because conceding risk is poorly individualised at player level.
**Keep clean sheets at team level.**

### 2.3 DEFCON — logistic on the threshold

```
P(hit) = 1 / (1 + exp(-(defcon_rate_shrunk - threshold) / 2.0))
```

Threshold 10 for DEF, 12 for MID, undefined for GK and FWD (contribute 0).

Note `defcon_expectation()` already returns **points**, not a rate. Multiplying
it by 2 again double-counts to a 4-point maximum. There is a test for this;
keep it.

### 2.4 Minutes

```
P(start) = starts in last min(4, gws_played) gameweeks / min(4, gws_played)
```

Scaled by `chance_next_round / 100` when not null.

Denominator must cap at 4 — `starts_last4` caps at 4 by construction, so an
uncapped denominator makes a nailed starter read 0.4 by GW10.

Use `is None`, not `or`. `p.get("starts_last4") or p.get("starts")` treats a
genuine zero as missing, so a dropped player falls back to season starts and
reads as half-nailed.

### 2.5 Blank and double gameweeks

No fixture that gameweek → **no forecast at all**. Do not assign a default
difficulty. Double gameweek → sum the per-fixture projections.

The `own` branch of `record_projections` still has this bug
(`fpl_edge.py:1494`) even though the `xg` branch was fixed. It is latent until
roughly GW18, then it corrupts the head-to-head that decides which model is
used — and by then the log rows are frozen. Fix it now. Test at simulated GW18,
mutation-verified.

---

## 3. The baselines — and the acceptance bar

**Log four sources to `projection_log.csv`, every gameweek, side by side:**

| source | what it is |
|---|---|
| `own` | existing points-based model. Retained as the known-failing control. |
| `xg` | existing bottom-up model. |
| `bottomup` | §2, the new one. |
| `minutes` | **P(start) alone. Nothing else.** |

### 3.1 The bar has changed. This is the most important line in this document.

Previously: beat a constant predictor. That is a trivial opponent and I set it
too low.

**The new bar: `bottomup` must beat `minutes`.**

On GW1-3 → GW4, with blanks counted as zero:

```
minutes share alone   +0.359   <- free, no model
bottomup (prototype)  +0.338
recent points/90      +0.239
xG+xA/90 alone        +0.159
```

The prototype cleared +0.20 and beat a constant on MAE — and was still **worse
than asking "will he play?"** Every attacking term, the Poisson clean sheet and
the DEFCON logistic added nothing over that one question.

This happens because counting blanks as zero makes the test dominated by the
playing signal: anything correlated with featuring earns rank correlation for
free. That is a property of the test, not a discovery about football.

**If `bottomup` cannot beat `minutes` over GW5 and GW6, use `minutes` and stop
building models.** That is a legitimate and cheap outcome, not a failure.

### 3.2 Two verdicts, reported separately

Rank correlation is dominated by who plays. So also report, for the
**players who featured only**:

- rho among those with 60+ minutes in the target week

That answers the second question — not "who blanks" but "how well do the
starters do" — which is what a captaincy or transfer decision actually needs.
A model can be useful for one and worthless for the other.

### 3.3 Freeze before Friday

Definitions — variable, window, population, baseline set — committed to
`CHANGELOG.md` with a timestamp **before the GW5 deadline (Fri 18 Sep 19:30
CEST)**. A model tuned after seeing GW5 is not tested by GW5.

My prototype figure of +0.338 was produced having already seen GW4's results.
It is exploratory and must not be quoted as a validation.

---

## 4. Testing standard

Unchanged, and it has caught every real bug in this project:

- Reintroduce each fixed bug and confirm the intended test goes red. A test
  that passes with the bug present is worse than no test — three of mine did.
- Test at simulated GW10, GW18, GW38. Three `project_xg` bugs were invisible at
  GW3 and wrong by GW5.
- Assert on behaviour, not source text.
- No conditional guards that let a test skip its own assertion.
- Every reliability figure printed with its interval. Four of five "findings"
  in the fixture-sensitivity table did not survive theirs.

---

## 5. Order of work

1. **R1 tie-corrected Spearman** + shuffle-invariance test.
2. **R2 grade the whole population** — benched-but-team-played counts as 0.
3. **`measure_reliability()`**, with the constant-metric guard.
4. **`minutes` baseline source** — trivial, and it is the bar everything else
   must clear.
5. **`project_reliability()`** using weights from step 3.
6. **Freeze definitions in `CHANGELOG.md`**, log all four sources for GW5.
7. G3 `own` branch blank/double fix.

Steps 1–4 matter more than step 5. A correct measuring instrument and an honest
baseline are worth more than another model, because without them we cannot tell
whether the model works — which is how three of them shipped.
