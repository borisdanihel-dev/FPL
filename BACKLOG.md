# Backlog — data gaps and untested assumptions

Companion to `CLAUDE.md`. That file records what was measured and what failed.
This one records what is still assumed, missing, or broken.

Ordered by value. Nothing here is urgent before the GW6 wildcard.

---

## Epistemic status of every input we currently use

**Measured, survives a 95% interval** — act on these:

| Finding | Number |
|---|---|
| FDR predicts clean sheets, not goals | 38% vs 12% CS; +0.06 goals |
| Defenders lose points at FDR 4+ | −1.27 (CI 0.25 to 2.30) |
| Effect is at the hard end only | FDR 2v3 = −0.06; 3v4+ = +1.33 |
| Recent points are anti-predictive | rho −0.202, SE 0.10 |

**Assumed, never tested** — used in reasoning, unvalidated:

- Set-piece and penalty order predicts returns
- DEFCON hit rate persists week to week
- Position arbitrage (defenders with attacking output) is exploitable
- Floor/consistency from 3 matches means anything
- **Minutes and starts predict points** — probably the strongest signal in the
  game, and we have never once measured it

**Absent from the data entirely:**

- Midweek and European minutes (FPL API is Premier League only)
- Team news / press conferences (unstructured, manual)
- Bonus points modelling (`bps` is stored, nothing reads it)
- Penalty conversion rates and second-choice takers
- Opponent xGC joined to a specific upcoming fixture
- Set-piece volume (being on corners matters more if the team wins 12 a game)

---

## P1 — Test minutes reliability as a single-variable predictor

The one experiment worth running now. Rank every player by
starts-per-available-gameweek, correlate against next-gameweek points using the
existing backtest harness. Single variable, not a composite — so unlike the
three failed projection attempts, the result is interpretable either way.

- Clears +0.20 → build the wildcard on it explicitly
- Fails too → nothing predicts at this sample size, and the wildcard rests
  purely on rules-level edges (position arbitrage, set pieces, DEFCON)

Runs on data already in the export. No new fetching.

## P2 — Rest days from Premier League fixtures

`fixtures` carries kickoff times for every tie. A `days_since_last_PL_match`
column in `--brief` catches the Saturday–Tuesday–Saturday congestion pattern.

Does **not** catch cup or European minutes — those are invisible to the FPL API
and stay manual. Worth stating that limit in the output so it isn't mistaken
for a full fatigue picture.

## P3 — Bonus points from BPS

`player_gw.bps` is stored and unused. Bonus averages roughly 0.3 points per
player per game and is close to deterministic given the BPS mechanics. Cheap
addition to `project_xg`, where the bonus term is currently a crude ICT
percentile.

## P4 — Opponent-specific clean sheet estimate

Currently `project_xg` uses measured CS rate by FDR bucket. Better: join the
opponent's actual attacking output (xG per 90) and the team's own xGC to the
specific fixture. All three inputs are already in the export — `teams` carries
`att_h`/`att_a`/`def_h`/`def_a`, `all_players` carries `xgc`, and
`fixtures_next6` has the pairing.

## P5 — Validate the assumed inputs

Once three graded gameweeks exist, test each separately against next-gameweek
points rather than trusting them:

- set-piece order (pens #1 vs not)
- DEFCON hit rate (2-of-3 vs 0-of-3)
- position arbitrage (defender xG+xA per 90)

Same harness as P1. Any that fail should stop driving decisions.

---

## Known warts

**`price_changes_7d` mislabels its window.** The query takes the oldest sample
within 7 days, not the sample from 7 days ago. With a short or gapped history
the `price_7d_ago` column is not 7 days ago and nothing says so. Becomes
correct once 7 unbroken days accumulate; silently under-reports after any
missed run.

**`--section wildcard` has a weak minutes filter.** `mins_last4 >= 45` lets in
players who barely feature. Replace with a starts-based floor — started every
available gameweek. **Do not add an ownership floor**: low ownership is the
edge in a 7-man league.

**`project()` is retained only as the `own` baseline.** It has failed three
times. It must not drive decisions.


---
---

# Part 2 — Decision engine: changes from the Claude Code review

Added 2026-09-11. Part 1 above is unchanged. Where a measurement below
contradicts it, the correction is stated in 2.0 rather than edited in place, so
the history stays readable. Numbers are reproducible from `fpl.sqlite`; method
is in `CHANGELOG.md`.

## 2.0 Corrections to Part 1 — read first

**Every rank correlation in this project is computed with a broken ruler.**
Two defects compound:

1. **`_spearman` does not handle ties.** Tied values get distinct ranks in input
   order. 16% of player pairs are tied on actual gameweek points (GW3: 54
   players on 2 pts, 49 on 1), so the answer depends on row order.
2. **The row order is correlated with the prediction.** `player_gw_recent` is
   exported `ORDER BY g.event, g.total_points DESC`, and `gw_index()` keeps that
   order. Among players tied on the target week's points, whoever scored most in
   the *first* week of the window gets the lowest rank. Any form-based
   predictor is pushed **negative by construction**.

Same data, same function — only the row order changes (form GW1-2 → GW3, n=207):

| | rho |
|---|---|
| export row order — what the harness computes | **−0.112** |
| 300 random row orders | −0.058 .. +0.024 |
| reversed row order | +0.097 |
| tie-corrected — the correct value | **−0.009**, 95% CI −0.146 .. +0.127 |

**What this does to Part 1:**

- **"Recent points are anti-predictive, rho −0.202" does not survive.** I could
  not reproduce −0.202 exactly (the original population, or late bonus
  corrections, may differ), but the mechanism produces most of it and the
  correct value is −0.009 with an interval centred on zero. Move it from "act on
  these" to "assumed". What stays true: form is **not predictive**. It is not
  *anti*-predictive.
- **The three failed `project()` attempts** — the rho column is biased down.
  Attempt 3 (the current code) reports −0.026; the same inputs tie-corrected give
  **+0.059**, and −0.026 falls outside all 300 random orderings (+0.018 ..
  +0.090). Still nowhere near +0.20, so `project()` still fails and still must
  not drive decisions — but "rates players backwards" was an artifact. The MAE
  vs constant verdicts are unaffected by ties.
- **"Minutes and starts predict points — never measured"** — now measured once,
  and it is the strongest signal found so far (below). The current harness
  would have hidden it.

**P1 says "use the existing backtest harness". That harness cannot run P1.**
Beyond ties, a third defect:

3. **Only players who played in the target week are ever graded.** The export
   drops zero-minute rows (`fpl_sync.py:415`, `g.minutes>0`); `sec_backtest`
   requires a target-week row; `sec_calibration` skips forecasts without one
   (`fpl_edge.py:1554`, `if a is None: continue`). A benched player's forecast
   is never scored. In GW3, 18 of 225 players with 90+ minutes in GW1-2 (8%) got
   no minutes — precisely the cases a minutes predictor exists to catch.

| predictor, GW1-2 → GW3 (tie-corrected) | played only — current harness | benched counted as 0 |
|---|---|---|
| starts per GW | +0.039 (CI −0.097 .. +0.176) | +0.142 (CI +0.011 .. +0.273) |
| minutes share | +0.061 (CI −0.076 .. +0.197) | **+0.194 (CI +0.063 .. +0.325)** |

On the current harness P1 would have returned about +0.04, Part 1's rule would
have concluded "nothing predicts", and the wildcard would have been built on
rules-level edges alone. (Starts per GW takes only two values here, 0.5 and 1.0;
the untied function swings −0.025 .. +0.266 on it depending on row order.)

**P2** — premise measured: of 740 gaps between consecutive PL matches across
all 20 teams this season, **64 are under 4 days** and 81 are 4–5. PL-only
congestion is real, not rare. Rest days are still an *untested predictor* and
belong in "assumed" until the harness says otherwise — they should not appear
in `--brief` looking like a signal.

**P3** — "close to deterministic given the BPS mechanics" holds once the match
is played. A forecast needs BPS *before* the match, which is as hard as
forecasting points. Still worth doing: it replaces the invented `0.8 × ICT
percentile` weight (design rule 6) with a measured per-player bonus rate. The
ceiling is small, because bonus is small.

**P4** — conflicts with design rule 5. `teams.att_h/att_a/def_h/def_a` *is*
FPL's 1000–1400 strength scale, which rule 5 excludes; `all_players.xgc` is a
player's on-pitch xGC, not team xGC. With three matches per team the measured
version is noise. Defer to ~GW10, build only from measured team xG/xGC, and let
it in only if it beats the FDR-bucket version in calibration.

**P5** — binary splits (pens #1 vs not, DEFCON 2-of-3 vs 0-of-3) should be
tested as a difference in mean points with a 95% interval — `_gap_ci()` exists
and is what `sec_sensitivity` uses — not as a rank correlation against a
two-valued predictor. Three tests at 95% carry a ~14% chance that at least one
passes by luck. And at this sample size, failing the bar mostly means
*underpowered*, not *no effect*: "stop driving decisions" is right, but label it
"unproven", not "disproven".

## 2.1 Priority 0 — fix the ruler, before P1

Grading is recomputed from `projection_log.csv` + the export on every run; it is
never frozen. So these fixes regrade GW4 retroactively and **nothing
irreplaceable is at stake** — but they must land before a calibration table is
read and acted on.

- **R1 — tie-corrected Spearman.** Average ranks for ties. Tests: shuffling the
  input order must not change rho (the test that would have caught this), and a
  hand-computed example with ties. Mutation: restore the old ranker, confirm the
  shuffle test goes red.
- **R2 — grade the whole forecast population.** A player whose team played and
  who got 0 minutes is graded against 0 points; only a true blank is excluded.
  Needs zero-minute rows in the export (they are already in `fpl.sqlite`). Audit
  every `gw_index()` consumer first — `defcon`, `consistency`, `backtest`,
  `sensitivity`, `defcon_expectation`, `compare`, `calibration` — several assume
  a row means an appearance. Test at simulated GW10 with a benched player.
- **R3 — re-derive every rho on record** under R1+R2 and update
  `CLAUDE_opusChat.md`. Re-run the MAE verdicts under R2 too: counting zeros
  moves both the models and the constant baseline.

## 2.2 P1, on the fixed ruler

Preview: minutes share +0.194 on one week. The bar is +0.20 over three graded
weeks with an interval clear of zero.

**Freeze the predictor definition before GW4 kicks off (Sat 12 Sep 16:00).**
GW3 has already been looked at for two candidate predictors, so it is
exploratory. GW4 and GW5 are clean tests only if the definition — variable,
window, population — is fixed before they are played. Proposed: minutes share
over the last `min(4, gws_played)` gameweeks, population = the recorded `xg`
forecast set, benched = 0.

P1 has no fitted parameters, so scoring it retrospectively is as honest as a
point-in-time forecast *provided the definition was frozen first*. By the GW6
wildcard that gives GW3 (exploratory) + GW4 + GW5 (clean): **two clean weeks,
not three.** Decide in advance whether two is enough to act on — not after
seeing them.

Option: record it as a third `source` in `projection_log.csv` so it is graded
beside `own` and `xg`. Only its rho column means anything; it is a 0–1 score, not
points.

## 2.3 Record path

- **`own` branch mishandles blank and double gameweeks** (`fpl_edge.py:1494`).
  The `xg` branch was fixed; this one still gives a blank-GW player `fdr 3.0`
  and a full forecast, and a double one match's worth. Latent until the first
  blank/double (~GW18), then it corrupts the head-to-head. Fix with a test at
  simulated GW18, mutation-verified.
- **A partial sync exits 0.** `get()` returns `None` after three attempts and
  prints `! failed <url>`; only `sync_bootstrap` hard-exits. A failed league or
  fixtures call gives an export mixing fresh player data with stale standings,
  and no `SYNC FAILED`. Mostly harmless for forecasts; it makes "no SYNC FAILED"
  weaker evidence than it looks.
- **Log names use the local date; `price_history` uses the UTC date.** The
  10 Sep 23:55 run was missed; catch-up fired 01:56 CEST on 11 Sep (23:56 UTC),
  so its price row correctly landed on 10 Sep — 4 minutes inside the 02:00
  boundary — but its log is `run_2026-09-11.log`. There is no
  `run_2026-09-10.log`, so the folder looks like a missed day when it isn't, and
  the 11 Sep 23:55 run overwrites the catch-up's log and report (`>` truncates).

## 2.4 Wildcard

- **Starts floor** (Part 1 wart) — agreed. Before committing, count how many
  players per position survive "started every available gameweek"; a player
  rested once for a cup tie would be dropped for the wrong reason. P1 decides
  how much weight minutes deserve.
- **No ownership floor** — agreed.

## 2.5 Hygiene

- `git init` the folder. Diverged copies of `fpl_edge.py` / `fpl_sync.py` sit
  in Downloads; `fpl_edge_xg_fixes.patch` is applied and verified and can go
  once history exists.
- `sec_eo` divides by `n_rivals` unguarded (a one-entry league crashes).
- `sec_backtest` reassigns `tick` inside its loop; `sec_wildcard` assigns an
  unused `quota`.
- `CLAUDE_fable chat.md` is stale: GW4 deadline given as 15:30 (correct 14:30
  CEST, per `next_deadline()`), 61 tests / 1722 lines (now 67 / 1732), and it
  lists `fpl_xg.py`, which is not in the folder.

## 2.6 Considered and declined

- **Truthful exit code for `--record`** — declined 2026-09-08; the run log is
  checked by hand. If revisited: exit non-zero only when a deadline exists, has
  not passed, and zero rows were written — "recorded nothing" is normal after a
  deadline.
- **Separate midday record-only task** — withdrawn. Same machine, so it fails
  together with the nightly one; and forecasts don't move mid-week (0 of 535
  values changed 7 → 8 Sep).
- **Missing-forecast warning in `--brief`** — withdrawn; detection on deadline
  day adds nothing over a daily manual check.

## 2.7 Done this session

Measurements in `CHANGELOG.md`.

- GW4 log audit — all 535 rows reproduce; the xG patch is a no-op at GW3→4 and
  worth +34% for a nailed starter by GW10.
- Mutation audit — 5/5 `project_xg` fixes now caught; the tautological
  double-GW test replaced with an end-to-end one.
- `fpl_run.bat` gates `--record` on a green suite, verified on both branches.
- Task Scheduler catch-up, battery and wake-to-run settings (applied by Boris);
  first catch-up observed 11 Sep 01:56.


---
---

# Part 3 — Decisions on Part 2

Added 2026-09-11, before GW4 kicks off. Part 2's analysis is accepted; this is
the ruling on what gets built and what waits. Parts 1 and 2 unchanged.

**One item has a hard deadline: D2, before Sat 12 Sep 16:00 CEST.**
Everything else can slip.

---

## GREEN — build now

### G1. R1, R2, R3 — fix the ruler
Part 2 §2.1. Tie-corrected Spearman; grade the whole forecast population with
benched-but-team-played counted as 0; re-derive every rho on record.

**Why first:** every rank correlation in this project was computed with a
defective instrument, and the defect is not random. `_spearman` assigns
ordinal ranks to tied values, and `player_gw_recent` is ordered
`total_points DESC`, so ties break in favour of whoever scored more earlier in
the window — pushing any form-based predictor negative by construction. Every
number downstream inherits it. Fixing anything else first means measuring the
fix with the broken ruler.

R2 matters independently: a forecast for a player who was benched is currently
never graded, which removes exactly the cases a minutes predictor exists to
catch. It moved minutes share from +0.061 to +0.194 on one week.

**Nothing irreplaceable is at stake** — grading recomputes from
`projection_log.csv` on every run, so GW4 regrades retroactively. But it must
land before any calibration table is read and acted on.

**Test that would have caught it:** shuffling input row order must not change
rho. Add it, then mutate the ranker back and confirm it goes red.

### G2. Freeze the P1 predictor definition — **before Sat 12 Sep 16:00 CEST**
Write into `CHANGELOG.md`, timestamped, and do not touch afterwards:

> Minutes share over the last `min(4, gws_played)` gameweeks.
> Population: the recorded `xg` forecast set.
> Benched but team played = 0. True blank gameweek = excluded.

**Why now:** GW3 has already been inspected for two candidate predictors, so it
is exploratory and cannot count as a clean test. GW4 and GW5 are clean *only*
if the variable, window and population are fixed before they are played. After
kickoff the option is gone for GW4 — a third of the evidence available before
the wildcard.

P1 has no fitted parameters, so scoring it retrospectively is legitimate
**provided the definition was frozen first**. That proviso is the whole point.

### G3. `own` branch blank/double gameweek bug
`fpl_edge.py:1494`. The `xg` branch skips blanks and sums doubles; the `own`
branch still assigns `fdr 3.0` to a team with no fixture and counts one match
of a double.

**Why now rather than later:** latent until roughly GW18, then it silently
corrupts the head-to-head that decides which model is used — and by then the
log rows are frozen and cannot be regenerated. Cheap today, unfixable then.
Test at simulated GW18, mutation-verified.

### G4. `git init`
**Why:** diverged copies of `fpl_edge.py` and `fpl_sync.py` sit in Downloads
with no way to tell which is current. Two string-replace patches in this
project have already silently matched nothing and reported success; without
history there is no way to confirm an edit landed except re-reading the file.
Once history exists, `fpl_edge_xg_fixes.patch` can go.

### G5. Hygiene
`sec_eo` divides by `n_rivals` unguarded; `sec_backtest` reassigns `tick`
inside its loop; `sec_wildcard` assigns an unused `quota`; the stale chat file
(wrong deadline, wrong test count, references a file that does not exist).

**Why:** all trivial, and the stale file states the GW4 deadline as 15:30 when
it is 14:30 CEST. A wrong deadline in a document someone might trust is worse
than no document.

---

## AMBER — build, but scoped down

### A1. P2 rest days — as a calendar fact, not a signal
Build `days_since_last_PL_match`. **Do not present it in `--brief` as though it
predicts anything.**

**Why the caveat:** the premise is measured — 64 of 740 gaps this season are
under 4 days, so PL-only congestion is real. But whether short rest *costs
points* has never been tested. Part 1's own framing applies: it belongs in
"assumed" until the harness says otherwise. Label it as what it is — a fact
about the calendar — or it will be read as a reason to bench someone.

Also state the limit in the output: cup and European minutes are invisible to
the FPL API, so this is not a full fatigue picture.

### A2. Starts floor on `--section wildcard`
Count survivors per position under "started every available gameweek" before
committing. **Do not apply it until P1 reports.**

**Why:** a player rested once for a cup tie gets dropped for the wrong reason.
Mitchell missed the Middlesbrough tie among eight changes and is a nailed
starter. P1 decides how much weight minutes deserve; the floor should follow
that answer, not precede it.

**No ownership floor.** Ownership measures popularity. Low ownership is the
edge in a seven-man league — Khalaili at 0.2% is the best arbitrage candidate
found so far.

### A3. Log naming — stop the truncation
Part 2 §2.3. Log names use the local date, `price_history` uses UTC, and `>`
overwrites.

**Why it matters, narrowly:** the catch-up run on 11 Sep 01:56 correctly landed
its price row on 10 Sep, but wrote `run_2026-09-11.log` — and the 23:55 run
that evening overwrote it. The price data survived; the evidence that a
catch-up happened did not. Fix the truncation. Low priority.

---

## RED — not now, with reasons

### R-P3. Bonus points from BPS
**Why not:** Part 2's own correction undercuts the case. BPS is near
deterministic *after* a match; forecasting it beforehand is as hard as
forecasting points. The real gain is replacing the invented `0.8 × ICT
percentile` weight with a measured rate — worthwhile, but on a component worth
about 0.3 points per player per game. Small ceiling, non-trivial work, no
bearing on the wildcard.

**Revisit:** after P1 reports, if the bottom-up model is being used at all.

### R-P4. Opponent-specific clean sheet estimate
**Why not:** it conflicts with the rule excluding FPL's 1000–1400 strength
scale, and `all_players.xgc` is a player's on-pitch xGC rather than team xGC,
so the inputs are not what Part 1 assumed. With three matches per team the
measured version is noise.

**Revisit:** ~GW10, built only from measured team xG and xGC, and admitted only
if it beats the FDR-bucket version in calibration.

### R-P5. Validating the assumed inputs
**Why not yet:** the method needs correcting anyway — binary splits (pens #1 vs
not, DEFCON 2-of-3 vs 0-of-3) are a difference in means with a 95% interval via
`_gap_ci()`, not a rank correlation against a two-valued predictor. And three
tests at 95% carry a ~14% chance one passes by luck.

At this sample size, failing the bar mostly means **underpowered**, not **no
effect**. Anything that fails should be labelled *unproven*, not *disproven*.

**Revisit:** GW8+.

---

## The decision that is not code

### D1. Two clean weeks, not three — and what two buys
`CLAUDE.md` requires three graded gameweeks before a model drives the wildcard.
By GW6 there will be GW3 (exploratory) plus GW4 and GW5 (clean) — **two**.

**Ruling: two is enough for a floor-protection signal, not for a ranking one.**

Use minutes share to **exclude players likely to blank**. Do not use it to
**order the players who start**.

**Why the distinction is real, and why it deflates the headline.** Minutes
share predicting points is partly definitional: appearance points mean playing
scores 2 and not playing scores 0, so any predictor of *whether* someone
features earns rank correlation for free. Part 2's own two columns say exactly
this — +0.194 counting blanks as zero, +0.061 among players who actually
played, with an interval spanning zero.

So it predicts **who blanks**, not **how well the starters do**. That is still
worth having: a wildcard squad's main failure mode is dead slots, and the
Bench Boost depends entirely on fifteen players featuring. It is not a ranking
model and must not be used as one.

**This is recorded before GW4 and GW5 are played.** Choosing a threshold after
seeing the result is how you pick the one that gives you the answer you wanted.

### D2. Deadline
G2 before **Sat 12 Sep 16:00 CEST**. Everything else can slip.

---

## Correction to Part 1, carried forward

**"Recent points are anti-predictive, rho −0.202" is withdrawn.** The
tie-corrected value is −0.009 with a 95% interval of −0.146 to +0.127. Form is
**not predictive**. It is not **anti-predictive** — that was an artifact of the
broken ranker plus the export's row order.

Move the row from "measured, act on these" to "assumed". No decision taken so
far depended on form being negative, only on it not being positive, so the
plan is unaffected. But the claim was overstated and it was the headline
finding.

The three failed `project()` attempts stand: attempt 3 tie-corrects from −0.026
to +0.059, still nowhere near +0.20. It still fails and still must not drive
decisions — but "rates players backwards" was an artifact, not a property.
MAE-versus-constant verdicts are unaffected by ties.
