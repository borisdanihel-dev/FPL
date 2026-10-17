# FPL build plan — Oct 2026 → Feb 2027

Save this file in the repo as `docs/BUILD_PLAN.md` (folder `C:\Users\Boris\Documents\FPL\docs\`).
Claude Code reads its instructions from here. You paste one short line per step (shown under each step).

---

## Part A — Boris: one-time setup (≈15 min)

- [ ] **A1.** On the PC, open Claude Code in `C:\Users\Boris\Documents\FPL`.
- [ ] **A2.** Copy this file into the repo as `docs/BUILD_PLAN.md`.
- [ ] **A3.** Paste the **Step 0** line into Claude Code and approve its permission prompts.
- [ ] **A4.** When Step 0 is done, **close Claude Code and start a fresh session**, so the new verifier agent gets loaded.
- [ ] **A5.** Send the Step 0 report to the chat (the text, or the file `reports/cc_<date>_itemS0.md`).
- [ ] **A6 (before Step 3):** create a free API key at the-odds-api.com, then add it to GitHub:
  - Repo **Settings → Secrets and variables → Actions → New repository secret**.
  - Name: `ODDS_API_KEY`. Value: the key.
  - Never paste the key into a chat or a file in the repo.

## Part B — Boris: the loop for every step

1. **Start a fresh session.** `git pull` first if the PC has been off (Claude Code can do this).
2. **Paste the step's one-line prompt**, then approve permissions.
3. **Wait for the report.** Each step ends with a report file and a verifier verdict.
4. **Send the report to the chat.** I accept it, reverse parts of it, or send back fixes.
5. **Only then start the next step.** Never run two steps at once: they touch the same files.

**If time is short** (moving month): the minimum before the Bench Boost decision on **Thu 5 Nov** is **Step 1 + Step 4**.

## Part C — calendar

| When | Who | What |
|---|---|---|
| Sun 18 – Tue 20 Oct | Boris → CC | Step 0 (setup + verifier) |
| Mon 19 – Thu 22 Oct | Chat | GW7 grading; GW8 deadline pass. GW8 transfer plan: Thiago → João Pedro. GW8 deadline is Fri 23 Oct, early evening — check the app. |
| by Thu 22 Oct | CC | Step 1 (backtest harness) |
| by Wed 28 Oct | Boris | A6 (odds API key) |
| by Wed 28 Oct | CC | Step 2 (league variance) |
| by Wed 4 Nov | CC | Step 3 (odds-implied fixture λ), Step 4 (first-half chip calculator) |
| Thu 5 Nov | Chat | Bench Boost 1 decision for GW10, from the Step 4 output |
| Nov – Dec | CC | Phase 2 (Steps 5–10); I write each prompt when the step before it is accepted |
| Jan – Feb | CC | Phase 3 (Steps 11–15). The cup draws decide doubles and blanks from ~1 Feb |
| by Sat 2 Jan 13:30 GMT | Boris | GW19 deadline. Both first-half chips must be used before it |

---

## Verifier agent (Claude Code creates this file in Step 0)

Path: `.claude/agents/backtest-verifier.md`. Exact content:

```markdown
---
name: backtest-verifier
description: Independent verifier for FPL model changes. Use proactively after any work item that changes forecasts, the backtest harness or chip calculators, before the item's report is written.
tools: Read, Glob, Grep, Bash, Write
model: inherit
---
You verify; you never implement. You did not write this code: assume it is
wrong until the evidence says otherwise. Never edit source files. Write only
reports/verify_<item>.md.

Input: the work-item id. Read prereg/<item>.md. Use git log to confirm it was
committed before the first code commit of the item; if not, verdict FAIL.

Checks, each PASS/FAIL with evidence:
1. Point-in-time: every input used for gameweek g must exist before g's
   deadline (logged forecasts, pre-closing odds, data timestamps). Run one
   leak probe: shift the target by one gameweek and confirm the metric
   collapses toward zero.
2. Clean-checkout test run: report counts before and after the item.
3. Re-run the pre-registered evaluation yourself through the harness. Your
   numbers must match the implementer's within 1e-6.
4. The primary metric, sample filter, bootstrap settings and pass threshold
   must be exactly those in the prereg. Flag any metric promoted after the
   results were seen, and any re-tuning after the results were seen.
5. Recording path: regenerate current forecasts; the projection log must be
   byte-identical for every model the item did not change.
6. Mutation spot-check: break one line of the new logic in a scratch copy;
   a test must go red.

For descriptive items (no pass/fail in the prereg), run checks 1, 2, 5, 6
and verify the numbers reproduce.

End with VERDICT: PASS or FAIL, and the one-paragraph reason.
```

---

## Step 0 — protocol, verifier, small fixes

**Boris pastes:** `Do Step 0 in docs/BUILD_PLAN.md.`

Item S0. Setup only; no model changes.
1. `git pull`. Confirm the working tree is clean and the runner's latest nightly commit is present.
2. Create `.claude/agents/backtest-verifier.md` with exactly the content in the section "Verifier agent" above.
3. Create `prereg/README.md` and `prereg/TEMPLATE.md`. Every work item gets `prereg/<item>.md`, committed **before** any code for that item, containing:
   - item id and hypothesis;
   - data and sample filter: point-in-time sources only; "starters" means forecast P(start) ≥ 0.8 unless the item says otherwise;
   - comparison model;
   - **one** primary metric; secondary metrics are for information only;
   - bootstrap unit = gameweek, 10,000 resamples, 90% CI;
   - pass threshold;
   - the line "no re-tuning after viewing results".
4. Add a "Work-item protocol" section to `CLAUDE.md`:
   - order: prereg first → implement → tests → run the `backtest-verifier` subagent → write `reports/cc_<date>_item<id>.md` with the verifier verdict quoted → changelog → commit and push;
   - an item with a FAIL verdict is not done.
5. Small fixes, each with tests and a changelog entry:
   - (a) `watchlist.txt`: replace E.Le Fée (542) with João Pedro, and add De Cuyper (115). Look up João Pedro's id by web_name and team CHE in the latest export and print it in the report.
   - (b) Bench audit: include the goalkeeper swap in "perfect-XI gain". Re-run GW6: it must show Verbruggen +7 as well as Rudoni.
6. Smoke-test the verifier:
   - On a scratch branch, add a toy evaluation that deliberately uses gameweek g's realised points as a feature for gameweek g (a leak), with a prereg file.
   - Run the backtest-verifier on it. It must return FAIL on check 1.
   - Quote its output in the report, then delete the scratch branch.
7. Report `reports/cc_<date>_itemS0.md`; commit; push.

## Step 1 — backtest harness (foundation)

**Boris pastes:** `Do Step 1 in docs/BUILD_PLAN.md.`

Item P1. Stdlib only. Write `prereg/P1.md` first (pass criteria in point 5).
1. **Module `backtest.py`.** Walk-forward evaluation over:
   - (a) the 2026/27 projection log (point-in-time as logged);
   - (b) 2025/26, using only forecasts reconstructable from data available before each deadline. Say plainly in the report which models qualify for (b).
2. **Per-gameweek metrics:**
   - Spearman and Kendall (all players, and predicted starters);
   - top-k regret for k = 1, 3, 11 (realised points of the model's top k minus the true top k);
   - MAE;
   - Brier and log loss for any binary component forecast present: P(start), P(clean sheet), P(goal), P(DEFCON), P(bonus ≥ 1).
3. **Comparison of two models:**
   - per-gameweek difference d_g;
   - paired bootstrap over gameweeks (10,000 resamples, 90% CI);
   - Holm and Benjamini–Hochberg (q = 0.10) helpers for families of tests.
4. **Power calculator:**
   - G = ((z_{1−α/2} + z_{1−β})·s_d/Δ)².
   - Measure s_d for per-gameweek Spearman (own vs bottomup) on 2025/26.
   - Print the gameweeks needed for Δ = 0.01, 0.02 and 0.03 at α = 0.05 and 80% power.
5. **Self-test on synthetic data with a known effect.** Pass when:
   - the true effect is detected at 80% ± 5% over 400 replications;
   - with no effect, the false-positive rate is 5% ± 2%.
6. **CLI:** `python backtest.py --compare own bottomup --season 2025-26 --filter starters`.
7. **Run it on own v xg v bottomup v minutes**, for 2025/26 and for 2026/27 GW1–7 (GW7 once graded). Table in the report.
8. Verifier → report `reports/cc_<date>_itemP1.md` → commit → push.

## Step 2 — league score variance (replaces the ±15 assumption)

**Boris pastes:** `Do Step 2 in docs/BUILD_PLAN.md.`

Item P2. Descriptive; prereg states "descriptive, no pass/fail".
1. **Pull gameweek history** for all 7 entries in league 455565: 2026/27 so far, plus 2025/26 for any entry that existed then.
2. **Compute:**
   - each manager's weekly score SD σ_i;
   - pairwise correlations ρ_ij;
   - the SD σ_d of the weekly score difference between us and each rival;
   - all with bootstrap CIs.
3. **Compute P(we finish above rival j)** with the normal approximation Φ((n·μ_d − gap)/(σ_d·√n)), with μ_d = 0 and n = remaining gameweeks.
4. **Add a "LEAGUE ODDS" section to the nightly report** with these numbers and the "variance line" gap > σ_d·√n. Recompute every night.
5. Verifier → report → commit → push.

## Step 3 — odds-implied fixture λ (fixes the flat fixture term)

**Precondition:** Boris has done A6.
**Boris pastes:** `Do Step 3 in docs/BUILD_PLAN.md.`

Item P3. Write `prereg/P3.md` first.
1. **Probe both sources from the GitHub runner and report the results:**
   - The Odds API (`soccer_epl`, markets `h2h,totals`, regions `uk,eu`): confirm totals coverage; log credits used.
   - football-data.co.uk: the 2025/26 season CSV and the weekly fixtures file. Use average or Bet365 columns, not Pinnacle; pre-closing columns only for backtests.
   - Store every odds snapshot in SQLite with its fetch timestamp. Forecasts may only use snapshots fetched before the deadline.
2. **Fit the Poisson λ:**
   - de-margin (proportional and power methods);
   - total goals from P(under 2.5) by bisection;
   - home/away split by bisection on P(home win), using the Poisson score grid;
   - P(clean sheet) = e^(−λ_opp).
   - Fallback when there are no odds: a time-decayed Poisson team model from goals (or xG where available). Say which one fired, per fixture.
3. **Feed λ into the GK/DEF clean-sheet and goals-conceded terms** as a new model variant. Do not replace the frozen models; record the variant to the projection log under a new source name.
4. **Pre-registered test:**
   - Primary: Brier score on clean sheet, GK/DEF with ≥ 60 minutes, 2025/26, variant vs current bottomup term.
   - Pass: Brier improves by ≥ 0.005 with the 90% CI excluding 0, **and** starters-only DEF/GK Spearman does not fall on 2026/27 GW1–7.
   - Secondary (information only): the projected DEF points spread between the easiest and hardest fixture quintiles (currently about 0.17).
5. Verifier → report → commit → push.

## Step 4 — first-half chip calculator (Bench Boost 1 / Free Hit 1)

**Boris pastes:** `Do Step 4 in docs/BUILD_PLAN.md.`

Item P4. Write `prereg/P4.md` first.
1. **Chip values for each remaining first-half gameweek t (≤ GW19):**
   - **V_BB,t:** bench points with the autosub-adjusted marginal (bench total minus the points autosubs would bring in anyway).
   - **V_FH,t:** best legal XI for that gameweek within the current team value, minus our XI after normal transfers.
   - Use the own model where forecasts exist. Beyond the six-week horizon, use the Step 3 λ variant if it passed, otherwise bottomup, and label it as a proxy.
2. **Uncertainty:** simulate each V_t by resampling the model's historical errors from Step 1 (empirical residuals by position).
3. **Backward induction** over (gameweek, chips left), one chip per gameweek, both chips worth 0 after GW19. Output each night:
   - the V_t table;
   - the continuation values;
   - "PLAY BB / PLAY FH / HOLD" for the next gameweek.
   - Add this to the nightly report and the watch file.
4. **Pre-registered test:**
   - Replay the first half of 2025/26 on at least 50 sampled real squads (from the FPL API, entries with history), with point-in-time forecasts.
   - Metric: realised chip points.
   - Compare against the heuristic (BB on the squad's highest projected bench week, FH on its weakest XI week) and against "use both at the earliest gameweek".
   - Pass: mean paired gain ≥ 0 and the 90% CI lower bound > −3 points against the heuristic.
5. Verifier → report → commit → push.

---

## Phase 2 (Nov–Dec): I write each prompt when the step before it is accepted

| Step | Item | One line |
|---|---|---|
| 5 | Rule normaliser | Re-score past seasons under 2026/27 rules: assist rescaling, DEFCON reconstruction where defensive counts exist, BPS recomputed, position reclassifications. Must reproduce 2025/26 official points within ±1 for ≥ 99% of player-gameweeks. |
| 6 | Shrunk share-of-team allocation | Player xG/xA = λ_team × shrunk share × minutes. Credibility weights k from split-half reliability; priors from last season; resets for transfers and promoted teams. |
| 7 | Minutes model | Start / sub / no-appearance states; goalkeeper lock; role-holder links (`covering_for`); congestion factor, fitted rather than assumed; a press-conference override CSV you can edit. |
| 8 | DEFCON probability | Negative binomial on shrunk per-90 rates × minutes × opponent factor from λ. |
| 9 | Points distributions | Full PMF per player; captain table with mean, P(≥10), P(≥15); EO as the tiebreak within 0.3. |
| 10 | Free Hit screen | Best legal one-week XI minus ours, per future gameweek; flag a gap > 8 or 3+ of our XI not `a`. |

## Phase 3 (Jan–Feb)

| Step | Item | One line |
|---|---|---|
| 11 | Blank/double table + predictor | History from archived fixtures; Monte Carlo of the cup brackets; P(team blanks / doubles in GW k). |
| 12 | Mini-league win simulator | Joint simulation with shared players and captains plus rival chip schedules; ΔP(win) per candidate move. |
| 13 | Relative-xP view | (Our multiplier − rivals' threat-weighted multiplier) × xP; flags "free variance" options. |
| 14 | Free-transfer value | Solver re-run with ±1 free transfer; compare with the 1.5 / 1.0 / 0.6 / 0.3 priors. |
| 15 | Second-half chip calculator | Step 4 extended to WC2 / BB2 / FH2 / TC2 with blank and double scenarios from Step 11. |
| — | Optional | Realised chip-return dataset. |
