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
