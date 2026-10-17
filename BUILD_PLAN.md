# FPL build plan v2 — Oct 2026 → Feb 2027

One instruction file for Claude Code. It replaces v1 and merges four research reports:
1. Point-probability methods: odds-implied λ, share-of-team allocation, minutes, DEFCON, distributions.
2. Second-half planning: chips, doubles/blanks, mini-league maths, using past seasons, backtesting.
3. Data and infrastructure audit.
4. Model and decisions audit.

It lives in the repo root as `BUILD_PLAN.md`.

---

## Standing rules for Claude Code (every step)

- **One item at a time: stop after each item is pushed and wait for Boris (Session operating mode a).**
- **Runner code is Python standard library only.** Optional local tools (e.g. a MILP solver) live under `tools/`, with their own requirements file, and the nightly runner never imports them.
- **Never edit frozen models in place.** A new or changed model is recorded to the projection log under a **new source name**. It replaces nothing until its pre-registered test passes and Boris accepts it in chat.
- **Work-item protocol** (set up in Step 0): prereg first → implement → tests → `backtest-verifier` → report in `worklog/` → changelog → commit and push. A FAIL verdict means the step is not done.
- **Secrets.** `ODDS_API_KEY` is a GitHub Actions repository secret, optionally also a local environment variable. Never write it, or any URL or header containing it, to a file, a log or a report.
- **When this file and the code disagree, stop and report** instead of guessing.

---

## Part A — Boris: setup

- [x] **A6.** Odds API key added as repository secret `ODDS_API_KEY` (17 Oct).
- [x] **A2.** `BUILD_PLAN.md` is in the repo root.
- [ ] **A1.** On the PC, open Claude Code in `C:\GIT\FPL`.
- [ ] **A3.** Paste the Step 0 line and approve the permission prompts.
- [ ] **A4.** After Step 0, close Claude Code and start a fresh session, so the verifier agent loads.
- [ ] **A5.** Send the Step 0 report to the chat.
- [ ] **A7.** Install the GitHub Mobile app and turn on notifications for the repo. In GitHub notification settings, set Actions to "failed workflows only".
- [ ] **A8.** In the repo's Settings, open the security section and turn on **Secret scanning** and **Push protection**. Both are free for public repos.
- [ ] **A9 (during Step 2).** When Claude Code asks, send a screenshot of the FPL **Transfers** page showing your players' selling prices.
- [ ] **Weekly, about 1 minute.** In the repo's **Actions** tab, check that the nightly workflow is active and has a recent green run. Any commit you or Claude Code push counts as repo activity, which stops GitHub pausing the schedule.

## Part B — Boris: the loop for every step

1. **Use the current Claude Code session (folder C:\GIT\FPL). Start a fresh one only when it becomes slow or confused; it resumes from worklog/SESSION_STATE.md.** Paste: `git pull, then do Step N in BUILD_PLAN.md.`
2. **Approve permissions** and wait for the report (`worklog/cc_<date>_<item>.md`) with the verifier verdict.
3. **Send the report to the chat.** I accept it, reverse parts of it, or send back fixes.
4. **Start the next step only after that.** Never run two steps at once: they touch the same files.

**Verifier write guard (Claude Code, every verifier run).** After every verifier run, the main session runs `git status` and `git diff`. Any change outside `worklog/verify_<item>.md` voids the verdict: the change is reverted and the verifier is rerun.

**Rulings (Claude Code, every item).** The chat's ruling text for an item is pasted verbatim into `prereg/<item>.md` before any code.

**Verifier launch (Claude Code, every verifier run).** Every verifier launch starts with: "Read .claude/agents/backtest-verifier.md from disk first; where it differs from your loaded instructions, the file on disk governs."

## Part C — Decision rules in force now (Boris and the chat; the steps below build the tooling)

1. **Expected points first.** At a 56-point gap with ~31 GWs left, maximise xP. Variance-seeking starts only when the gap exceeds σ_d·√n (σ_d is measured in Step 9; on current assumptions about GW25–27).
2. **XI, keeper and captain = the best xP.** Use `own` until `xp_v2` passes Step 6.
   - Vetoes are allowed only on hard facts (injury, dropped, confirmed rotation).
   - From Step 12 onward, a veto is entered as a P(start) override with a reason, and is logged and scored later.
3. **Captain** = highest xP in the whole XI.
   - A differential captain is allowed only if it costs ≤ 0.5 xP before GW25, or ≤ 1.0 after.
   - Judge the differential by effective ownership among the managers *ahead* of us.
4. **Boris's flags.** Show own / xg / bottomup and the six-week sum side by side. The flag wins unless the six-week rule beats it by more than 3 points.
5. **Hits.** Take a −4 only if the decayed gain (0.85 per GW over 6 GWs) is ≥ 5.5, and the gain does not rest on one fixture or on a player with P(start) < 0.8. The old "pays back within six GWs" rule is too loose.
6. **Free transfers.**
   - Never sit on 5.
   - Roll when the best move is worth less than the next banked FT.
   - Go into March with about 2 banked.
7. **Price timing.** Transfer before the 00:00 UK price change only if all three hold:
   - the move is already decided;
   - the official predictor shows above 100%;
   - no team news is pending.
8. **Bench order** = descending xP, including P(play), then check the formation is still legal.
9. **Chips, first half.** Bench Boost 1 and Free Hit 1 go in our best *normal* weeks between GW8 and GW18, when the Step 7 calculator says PLAY.
   - Bench Boost 1 is no longer pinned to GW10.
   - Never play Free Hit 1 in GW19.
   - One chip per GW.
10. **Chips, second half.** Default order: Wildcard 2 → Bench Boost 2 (biggest double) → Free Hit 2 (biggest blank) → Triple Captain 2 (premium double). Steps 16 and 18 adjust it.
    - Time at least one chip differently from the leader.
    - Avoid stacking likely cup finalists or semi-finalists, or their opponents, beyond what a Free Hit can cover.
11. **Club cap of 2 GK+DEF per club** stays as Boris's choice. From Step 15, its expected-points cost is shown at every squad build.
12. **Don't overreact to one gameweek.** Models are recalibrated only at the GW10, GW19 and GW29 checkpoints (Step 20).

## Part D — Calendar

| When | Who | What |
|---|---|---|
| Sun 18 – Tue 20 Oct | CC | Step 0 |
| by Sat 24 Oct | CC | Steps 1–2 (data safety, silent errors). UK clocks change on Sun 25 Oct, which puts the nightly run closer to the 00:00 UK price change. |
| by Wed 28 Oct | CC | Step 3 (monitoring and alerts) |
| by Wed 4 Nov | CC | Step 4 (backtest harness), Step 5 (odds λ) |
| by ~Sat 14 Nov | CC | Step 6 (xP rebuild), Step 7 (first-half chip calculator) |
| GW10–18 | Chat | Bench Boost 1 and Free Hit 1 when Step 7 says PLAY |
| Nov – Dec | CC | Phase 2 (Steps 8–15) |
| Jan – Feb | CC | Phase 3 (Steps 16–20). Cup semi-finals settle around 1 Feb; FA Cup quarter-finals are on 3 Apr. |
| Sat 2 Jan, 13:30 GMT | Boris | GW19 deadline: both first-half chips must be used before it |

**If time is short:** the minimum is Steps 0, 1, 2, 4 and 7.

---

## Verifier agent (created in Step 0)

Path: `.claude/agents/backtest-verifier.md`. Exact content:

```markdown
---
name: backtest-verifier
description: Independent verifier for FPL model and data changes. Use proactively after any work item that changes forecasts, the data pipeline, the backtest harness or decision calculators, before the item's report is written.
tools: Read, Glob, Grep, Bash, Write
model: inherit
---
You verify; you never implement. You did not write this code: assume it is
wrong until the evidence says otherwise. Never edit source files. Write only
worklog/verify_<item>.md.

Input: the work-item id. Read prereg/<item>.md. Use git log to confirm it was
committed before the first code commit of the item; if not, verdict FAIL.

Never read session transcripts or chat logs. The rulings you check are the
verbatim text in prereg/<item>.md; if a ruling is not there, report that as a
FAIL of check 4.

Checks, each PASS/FAIL with evidence:
1. Point-in-time leak check, for any item that produces a forecast, feature
   or evaluation metric:
   a. Truncation test (decides): for 3 gameweeks (earliest, middle, latest
      evaluated), rebuild the feature only from inputs available before that
      gameweek's deadline (dated exports on or before the deadline date;
      historical rows with round < g). Any value differing from the item's
      output by more than 1e-9 = FAIL.
   b. Timestamp audit (decides): every input row used for gameweek g is dated
      at or before g's deadline. Any later row = FAIL.
   c. Shift probe (warns only): for correlation metrics on points, recompute
      with the target moved to g+1, among players with 60+ minutes in both g
      and g+1, pooled over all gameweeks. WARN if the unshifted value is
      above 0.25 (measured ceiling 0.15) or unshifted minus shifted is more
      than 0.10 (fixture information adds only 0.02-0.06). A WARN is cleared
      only by a and b.
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
7. Secrets: no file the item adds or changes contains an API key, a URL
   with apiKey=, or an Authorization header value.

For descriptive or data-pipeline items (no pass/fail metric in the prereg),
run checks 1, 2, 5, 6, 7 and verify the item's own acceptance tests.

End with VERDICT: PASS or FAIL, and the one-paragraph reason.
```

---

# Phase 1 — foundation (Oct – mid-Nov)

## Step 0 — protocol, verifier, small fixes

**Boris pastes:** `git pull, then do Step 0 in BUILD_PLAN.md.`

Item S0. Setup only; no model changes.

1. `git pull`. Confirm the working tree is clean and that the runner's latest nightly commit is present. If old local runs left tracked files modified, stop and ask Boris before running `git checkout -- .`.
2. Create `.claude/agents/backtest-verifier.md` with exactly the content in "Verifier agent" above.
3. Create `prereg/README.md` and `prereg/TEMPLATE.md`. Every item gets `prereg/<item>.md`, committed **before** any code for it, containing:
   - item id and hypothesis;
   - data and sample filter (point-in-time sources only; "starters" means forecast P(start) ≥ 0.8, never realised minutes);
   - comparison;
   - **one** primary metric, with secondary metrics marked as information only;
   - bootstrap unit = gameweek, 10,000 resamples, 90% CI;
   - pass threshold;
   - the line "no re-tuning after viewing results".
4. Create `worklog/`. Claude Code reports go to `worklog/cc_<date>_<item>.md` and verifier reports to `worklog/verify_<item>.md`. Add a "Work-item protocol" section to `CLAUDE.md` with the standing rules above.
5. Small fixes, each with tests and a changelog entry:
   - (a) `watchlist.txt`: replace E.Le Fée (542) with João Pedro, and add De Cuyper (115). Look up João Pedro's id by web_name and team CHE in the latest export, and print it in the report.
   - (b) Bench audit: include the goalkeeper swap in "perfect-XI gain". Re-run GW6: it must show Verbruggen +7 as well as Rudoni.
6. Smoke-test the verifier:
   - On a scratch branch, add a toy evaluation that uses gameweek g's realised points as a feature for gameweek g (a leak), with a prereg file.
   - Run `backtest-verifier`. It must FAIL check 1. Quote its output in the report.
   - Delete the scratch branch.
7. Write the report, update the changelog, commit and push.

## Step 1 — data safety (the price history must never be lost)

**Boris pastes:** `git pull, then do Step 1 in BUILD_PLAN.md.`

Item D1. Acceptance tests are listed per point.

1. **Integrity gate before every runner commit:**
   - `PRAGMA integrity_check` returns ok;
   - price-history row count never decreases against the previous commit;
   - the table list is unchanged.
   
   On failure: commit nothing and exit non-zero. *Test:* a planted truncated database is rejected.
2. **Nightly text dump** `fpl.sql` via `sqlite3.Connection.iterdump()`, committed alongside the binary. *Test:* rebuild a database from the dump; row counts match.
3. **Weekly backup:**
   - On Sundays, upload `fpl.sqlite` and `fpl.sql` as assets of a GitHub Release `backup-<YYYY-MM-DD>` (`gh` on the runner, `contents: write`).
   - Keep the last 8 releases.
4. **Data branch.** Create an orphan branch `data`.
   - **What moves where:**
     - On `data`, all generated data: `fpl.sqlite`, `fpl.sql`, `exports/` (new exports gzipped as `.json.gz`), `reports/`, `logs/`, `projection_log.csv` and the watch files.
     - On `master`: code, docs, `watchlist.txt`, `prereg/`, `worklog/` and the changelog.
   - **Migration:**
     - The first `data` commit holds the current data files.
     - One commit on `master` then removes them (history stays).
     - Add the data paths to `master`'s `.gitignore`.
   - **Runner:**
     - Check out `master` for code and `data` into `./data`.
     - All scripts read and write through one `DATA_DIR` setting.
     - Commit and push to `data` only.
   - **Local:** `git worktree add C:\GIT\FPL-data data`, documented in `CLAUDE.md`; local `DATA_DIR` points there.
   - **Prove it:** one manual dispatch writes only to `data`, `master` is unchanged, and the tests are green. Put the new raw URL pattern in the report, e.g. `https://raw.githubusercontent.com/borisdanihel-dev/FPL/data/reports/watch_<date>.txt`.
5. **Push safety:**
   - `concurrency: {group: nightly-data, cancel-in-progress: false}`;
   - push = fetch + rebase + push, with up to 3 retries and jitter;
   - `.gitattributes`: `*.sqlite binary`;
   - a pre-push hook (with an install script) that rejects commits to `master` touching data paths.
6. **Secret hygiene:**
   - Fail the commit if the key value, or any `apiKey=` string, appears in staged files.
   - Never log full request URLs.
   - Give `permissions: contents: write` to the pushing job only.
   - Triggers are only `schedule` and `workflow_dispatch`.
   - Run `gitleaks` once locally over the full history and report the findings without printing any secret value.
7. Verifier → report → commit → push.

## Step 2 — silent-error fixes

**Boris pastes:** `git pull, then do Step 2 in BUILD_PLAN.md.`

Item D2. Each fix needs a unit test that fails before the fix and passes after.

1. **Lockdown guard.**
   - A gameweek is final only when `data_checked` is true AND every fixture of that gameweek whose kickoff is ≥ 3 h in the past is finished.
   - Fixtures not started 3 h after kickoff, and fixtures with `event` null, count as postponed and are excluded.
   - Raise a "GW stuck" alarm when a gameweek is not final 72 h after its last kickoff.
   - Note: in 2026/27 lockdown happens at 09:00 UK the morning after the last match, so the same-night run never sees the gameweek as final.
2. **Point-in-time guard.**
   - Reject any forecast row whose snapshot time is ≥ the target gameweek's `deadline_time`.
   - Every feature and forecast row carries `fetched_at_utc`.
   - A nightly test over the whole log must find 0 such rows.
3. **Idempotent projection log.**
   - Natural key `(event, element, fixture, source, snapshot_date)`; re-runs upsert and never append duplicates.
   - Write via a temp file and atomic rename.
   - De-duplicate the existing log once and report the rows removed. The duplicate-key test must find 0.
4. **Price dates.** Prices change daily at **00:00 UK** (2026/27 rule; 01:30 is outdated).
   - Label each snapshot with the Europe/London calendar date at fetch time: the prices valid for that London day.
   - Store `fetched_at_utc`.
   - Flag a run that fetched after 00:00 UK, because it holds the next day's prices.
   - Warn when a date is missing.
   - Use `zoneinfo`. On Windows, require the `tzdata` package or fail with a clear error.
5. **Target gameweek** = the first event with `deadline_time > now_utc`. Never use the `is_next`/`is_current` flags; log it when they disagree.
6. **Field handling:**
   - `chance_of_playing_*` null → 100, by explicit mapping (never `or 0`);
   - numeric fields that arrive as strings (`form`, `selected_by_percent`, `expected_goals`, …) are cast explicitly;
   - required fields raise an error instead of defaulting to 0;
   - double gameweeks are aggregated once per (element, gw), with `n_fixtures`;
   - scoring rules apply per fixture: 60-minute thresholds, saves//3, DEFCON capped at 2 per match.
7. **`ruleset` column** (`2025-26`, `2026-27`) on every scored row. Never mix rulesets in BPS or bonus comparisons.
8. **Selling price.**
   - Formula, in tenths: `sell = buy + (now − buy)//2 if now > buy else now`.
   - Purchase prices come from the entry's transfer history (wildcard moves included) or the original squad's prices.
   - Use selling prices, never `value`, in every budget calculation.
   - *Tests:* 7.5 → 7.8 sells for 7.6; equal; falling; +0.1.
   - Ask Boris for the in-app screenshot (A9) and match all 15 players exactly.
9. **Windows I/O:** open every file with `encoding="utf-8", newline=""`. Test that the CSV contains no `\r`.
10. **Bench audit respects automatic substitutions:** points that already counted through an auto-sub are not a bench gain. Data source: store automatic_subs from the picks response fpl_sync already fetches, in fpl.sqlite and the export; apply FPL's auto-sub rules only for gameweeks where it is missing. *Test:* a starter on 0 minutes whose bench player came on shows no gain.
11. Verifier → report → commit → push.

## Step 3 — nightly checks, status line and alerts

**Boris pastes:** `git pull, then do Step 3 in BUILD_PLAN.md.`

Item D3. Every check needs a test with a planted failure.

1. **`checks.py`** implements the table below. FAIL = no data commit and a red run; WARN goes into the status line.
2. **Status line** at the top of every report and in `reports/status.txt`:
   `STATUS OK|WARN|FAIL | generated <UTC> | next deadline <GW, UTC and Prague> | checks n/N | repo <MB>`.
3. **On failure,** open or update one GitHub issue, "Nightly run failed", listing the failing checks; GitHub Mobile notifies Boris. Close it on the next green run.
4. **Backup schedule:** a second cron, `17 3 * * *`, that runs only when today's status file is missing. Set `timeout-minutes: 30`.
5. **Action versions** (S1 amendment 3): bump `actions/checkout` and `actions/setup-python` past their Node 20 releases in every workflow, with a proof dispatch.
6. Verifier → report → commit → push.

| # | Check | Threshold |
|---|---|---|
| 1 | Core endpoints (bootstrap, fixtures, live, standings) | all HTTP 200, else FAIL |
| 2 | element-summary failures | ≤ 2% of players, else FAIL. Retry only 429/5xx/network errors, at most one retry on 403. Pause 0.3–0.5 s between player calls. |
| 3 | Player count | 550–900 and within ±5% of last night; WARN on new ids |
| 4 | Teams | exactly 20 |
| 5 | Fixtures | exactly 380 in total |
| 6 | Fixtures per gameweek | 10, unless a postponement, double or blank is flagged (WARN) |
| 7 | Team appearances per normal gameweek | exactly 1; 0 or 2 only when flagged |
| 8 | Required fields present and typed | 100% (id, code, team, element_type, now_cost, status, minutes, total_points, defensive_contribution, deadline_time, data_checked) |
| 9 | Element key set vs yesterday | unchanged, else WARN |
| 10 | Distinct `now_cost` values | ≥ 20 |
| 11 | Price step | \|Δ\| ≤ 0.1 × nights since last snapshot |
| 12 | Price changes per night | ≤ 60, else WARN |
| 13 | `chance_of_playing` = 0 | < 40% of players |
| 14 | Position (element_type) changes | 0, else WARN |
| 15 | SQLite integrity | ok |
| 16 | Price-history rows | never decrease; about +player count per night |
| 17 | Price-date gaps | none, else WARN |
| 18 | Projection-log growth | ≤ 1.2 × players per source per night |
| 19 | Projection-log duplicate keys | 0 |
| 20 | Forecast rows after deadline | 0 |
| 21 | Stuck gameweek | none unlocked 72 h after the last kickoff |
| 22 | Manager score reconciliation after lockdown | computed = `entry_history.points` |
| 23 | Secret in staged files | 0 |
| 24 | Repo size (`GET /repos/...` `size`) | WARN at 500 MB, FAIL at 900 MB |
| 25 | Run duration | WARN above 15 min |
| 26 | Heartbeat | `status.txt` less than 30 h old |
| 27 | Workflow state | active (Boris's weekly glance) |

## Step 4 — backtest harness

**Boris pastes:** `git pull, then do Step 4 in BUILD_PLAN.md.`

Item P1. Write `prereg/P1.md` first.

1. **`backtest.py`.** Walk-forward evaluation over the 2026/27 projection log (point-in-time as logged), plus 2025/26 using only forecasts that can be rebuilt from pre-deadline data. State plainly which models qualify for 2025/26.
2. **Start recording FPL's `ep_next` nightly** as source `fpl_ep`. It is free and point-in-time from now on, and serves as an external benchmark.
3. **Per-gameweek metrics:**
   - Spearman and Kendall, for all players and for predicted starters;
   - top-k regret for k = 1, 3, 11;
   - MAE;
   - Brier score and log loss for the binary components: P(start), P(clean sheet), P(goal), P(DEFCON), P(bonus ≥ 1);
   - **decision metric:** the realised points of the XI plus captain each model would pick from a fixed squad.
4. **Comparisons:**
   - per-gameweek difference;
   - paired bootstrap over gameweeks (10,000 resamples, 90% CI);
   - Holm and Benjamini–Hochberg (q = 0.10) helpers.
5. **Power calculator:**
   - G = ((z_{1−α/2} + z_{1−β})·s_d/Δ)²;
   - measure s_d on 2025/26;
   - print the gameweeks needed for Δ = 0.01, 0.02 and 0.03.
6. **Self-test on synthetic data:**
   - the true effect is detected 80% ± 5% of the time over 400 replications;
   - the false-positive rate is 5% ± 2%.
7. **CLI:** `python backtest.py --compare own bottomup --season 2025-26 --filter starters`.
8. **Report table:** own vs xg vs bottomup vs minutes vs fpl_ep, for 2025/26 and 2026/27 to date.
9. Verifier → report → commit → push.

## Step 5 — odds-implied fixture λ (fixes the flat fixture term)

**Boris pastes:** `git pull, then do Step 5 in BUILD_PLAN.md.`

Item P3. Write `prereg/P3.md` first.

1. **Probe the sources from the runner:**
   - The Odds API (`soccer_epl`, `h2h,totals`, regions `uk,eu`): confirm totals coverage and log the credits used. The free tier is 500 per month; nightly use should be about 60.
   - football-data.co.uk: the 2025/26 CSV for the backtest. Use the average or Bet365 columns (not Pinnacle) and pre-closing odds only.
   - Store every odds snapshot in SQLite with its fetch time. Forecasts may only use snapshots fetched before the deadline.
2. **Fit Poisson λ:**
   - de-margin the odds (proportional and power methods);
   - solve total goals from P(under 2.5) by bisection;
   - split home/away by bisection on P(home win);
   - P(clean sheet) = e^(−λ_opp).
   - **Fallback** when odds are missing: a time-decayed Poisson team model. Say which source fired, per fixture.
3. **New source `bottomup_lambda`:** use λ in the GK/DEF clean-sheet and goals-conceded terms. Unit test: P(clean sheet) must move with opponent strength.
4. **Pre-registered test:**
   - Primary: Brier score on clean sheet, for GK/DEF with ≥ 60 minutes, 2025/26.
   - Pass: improves by ≥ 0.005 with the CI excluding 0, **and** starters-only DEF/GK Spearman does not fall in 2026/27.
   - Secondary: the DEF points spread between the easiest and hardest fixture quintiles (currently about 0.17; it should be at least 1.0).
5. Verifier → report → commit → push.

## Step 6 — xP rebuild and blend

**Boris pastes:** `git pull, then do Step 6 in BUILD_PLAN.md.`

Item M1. Write `prereg/M1.md` first.

1. **New source `xp_v2`:**
   - xP = P(start) · mean(E_xg[pts | start], E_bottomup[pts | start]) + P(sub) · E[pts | sub].
   - P(start) comes from the minutes model. The minutes model is **never** averaged in as a points forecast.
   - Bottomup uses `bottomup_lambda` if Step 5 passed.
2. **Penalty term** inside both conditional forecasts: P(taker) × team penalties per match × 0.78 × the position's goal points.
   - P(taker) comes from the API's penalty order.
   - Decay P(taker) when there is evidence the taker has changed.
3. **Pre-registered test:**
   - Candidates: equal-weight blend (primary), best single model, inverse-MSE weights, and inverse-MSE weights shrunk 50% toward equal.
   - Develop on 2025/26; validate on 2026/27.
   - Primary metric: mean per-GW Spearman among predicted starters. Decision metric: XI plus captain points.
   - Replace equal weights only if an alternative wins on validation by ≥ 0.02 **and** on decision points.
   - Report `fpl_ep` alongside. If `xp_v2` doesn't beat `fpl_ep` among starters, say so at the top of the report.
4. **If `xp_v2` beats `own` on the primary metric** (CI excluding 0), propose it as the new decision model. Boris accepts in chat.
5. Verifier → report → commit → push.

## Step 7 — first-half chip calculator and Free Hit screen

**Boris pastes:** `git pull, then do Step 7 in BUILD_PLAN.md.`

Item P4. Write `prereg/P4.md` first.

1. **Chip values** for each remaining gameweek t ≤ 19:
   - V_BB,t = bench xP minus the autosub contribution that would happen anyway.
   - V_FH,t = best legal XI for gameweek t under the **selling-price** budget, minus our XI after normal transfers.
   - Use the best accepted xP source. Beyond 6 weeks, label it a proxy.
2. **Bench weights:**
   - normal weeks: 0.30 / 0.10 / 0.03, sub GK 0.03;
   - planned BB week: 1.0.
   - Output "bench prep": the free transfers that would raise V_BB in the planned week.
3. **Uncertainty:** resample Step 4's empirical residuals by position.
4. **Backward induction** over (gameweek, chips left):
   - one chip per gameweek;
   - both chips are worth 0 after GW19;
   - Free Hit 1 is never played in GW19.
   - Output each night: the V table, the continuation values, and **PLAY BB / PLAY FH / HOLD** for the next gameweek.
5. **Free Hit screen:** for each future gameweek, the gap between the best legal one-week XI and ours. Flag a gap above 8, or 3+ of our XI not `a`.
6. **Pre-registered test:**
   - Replay the 2025/26 first half on ≥ 50 sampled real squads, using point-in-time forecasts.
   - Metric: realised chip points.
   - Compare against the heuristic (BB on the highest bench week, FH on the weakest XI week) and against "use both as early as possible".
   - Pass: mean paired gain ≥ 0 and the CI lower bound above −3 points against the heuristic.
7. Verifier → report → commit → push.

---

# Phase 2 — models and decisions (Nov – Dec)

## Step 8 — rolling-horizon transfer planner (stdlib)

Item T1.

1. **Candidates:**
   - 0, 1 or 2 transfers, from the top ~25 per position by decayed xP;
   - the best legal XI and captain re-optimised for each candidate;
   - the selling-price budget.
2. **Score** = Σ_{t=0..5} 0.85^t ΔxP_t − 4 × hits − lost banked-FT value.
   - Two FT schedules: Boris's 1.5 / 1.0 / 0.6 / 0.3, and the solver default 2.1 / 1.8 / 1.5 / 1.1.
   - Take a hit only if the decayed gain is ≥ 4 + 1.5, not dependent on one fixture, and every incoming player has P(start) ≥ 0.8.
   - Never leave 5 FTs banked.
   - Robustness: rerun at decay 0.80 and 0.90, and flag when the answers disagree.
3. **Price line:** if the chosen target's official predicted progress is above 100% (or the outgoing player's is below −100%) and no flag is pending, print "make this transfer tonight".
4. **Test:**
   - Replay 2025/26 GW2–38.
   - Primary configuration: decay 0.85, Boris's schedule, buffer 1.5.
   - Baseline: "use the FT on the best one-week move, no hits".
   - Pass: ≥ +10 season points net of hits, with the CI excluding 0.
   - Other configurations are exploratory only.

## Step 9 — league variance, relative xP, captaincy table

Item L1. Descriptive.

1. **Per rival:** σ_i, ρ_ij and σ_d, with CIs; P(finishing above rival j) = Φ(−gap/(σ_d·√n)).
   - Show the **variance line**: gap > σ_d·√n.
   - Add a nightly "LEAGUE ODDS" section.
2. **League effective ownership** among the managers ahead of us.
   - relative xP = (our multiplier − the rivals' threat-weighted multiplier) × xP.
   - Flag "free variance" when ΔxP < 0.3.
3. **Captain table:**
   - argmax xP across the whole XI (no MID/FWD restriction);
   - the differential allowance per Part C rule 3;
   - log how often a DEF or GK comes out on top.

## Step 10 — rule normaliser (needed before past seasons are used)

Item H1.

- Re-score past seasons under the 2026/27 rules:
  - rescale assists;
  - rebuild DEFCON where defensive counts exist;
  - recompute BPS under the 2026/27 formula;
  - apply position reclassifications.
- Use `code` as the cross-season player key.
- Test: re-scoring 2025/26 under the 2025/26 rules reproduces official points within ±1 for ≥ 99% of player-gameweeks.

## Step 11 — share-of-team allocation with historical priors

Item H2.

1. Player xG/xA = λ_team × shrunk share × minutes.
2. **Credibility weights:**
   - Z = m/(m + k), with k = n(1 − r_n)/r_n from split-half reliability, per metric;
   - priors come from last season;
   - finishing skill (G − xG) is shrunk almost to 0;
   - transfers, promoted teams and new managers are treated as structural breaks.
3. **Test:**
   - walk-forward on 2025/26;
   - primary: per-GW Spearman among predicted starters vs the current-season-only model;
   - Holm correction across the metric family;
   - secondary: log loss on P(goal).

## Step 12 — minutes model v2, overrides and suspensions

Item N1.

1. **States:** start, sub, none.
   - Goalkeeper lock: the keeper with the most starts in the last 3 games gets P = 0.95 unless flagged.
   - `covering_for` links for role-holders.
   - A congestion factor is **fitted**, and dropped if it comes out ≈ 1.
2. **`overrides.csv`** (player, gw, P(start), reason, timestamp), editable by Boris or the chat.
   - Every override is applied, logged, and later scored: Brier score of the override vs the model.
3. **Suspensions.** A player on 4 cautions before his club's 19th league match, or on 9 before its 32nd, has:
   - P(ban in the next fixture) = P(booking this match), from his per-90 booking rate;
   - this feeds the next fixture's P(start).
4. **Test:**
   - Brier score of P(start) improves by ≥ 0.01, with the CI excluding 0;
   - overall MAE does not worsen by more than 0.02;
   - the goalkeeper-starter mismatch count is ≤ the current model's.

## Step 13 — DEFCON probability

Item N2.

- Negative binomial: mean = shrunk per-90 rate × minutes × opponent factor from λ. DEFCON expected points = 2 × P(reaching the threshold).
- Test: Brier score improves by ≥ 0.005, and the observed vs predicted hit rate agrees within 5 points in at least 8 of 10 deciles.

## Step 14 — points distributions

Item N3.

- Full PMF per player by convolving the components.
- Captain table with mean, P(≥ 10), P(≥ 15) and the 90th percentile.
- Test: Brier score of P(≥ 10) vs the haul-rate baseline, and the predicted count of 10+ hauls within ±15% of the actual count.

## Step 15 — unified squad builder (replaces the three-layer rule only after A/B)

Item Q1.

1. **One objective:** decayed per-fixture xP over 6 GWs, subject to:
   - a global budget at selling prices;
   - any of the 7 legal formations;
   - bench weights;
   - captain from any position;
   - FPL's 3-per-club limit;
   - the 2-per-club GK+DEF cap as a **toggle**, with its xP cost reported every time.
2. **Solvers:**
   - Stdlib: greedy plus local search, for nightly squad checks.
   - Optional local MILP under `tools/milp/` (PuLP + HiGHS, or open-fpl-solver fed with our xP matrix), for Wildcard, Free Hit and Bench Boost builds.
3. **Pre-registered A/B:**
   - Same frozen xP matrices for both sides.
   - Every gameweek from GW5 (2025/26, and 2026/27 to date) is treated as a hypothetical wildcard.
   - Metric: realised points over the next 6 GWs, with FPL autosubs and the actual captain applied.
   - Pass: mean difference > 0 with the CI excluding 0, **and** the builder ≥ the rule on ≥ 60% of dates.
   - The builder's projected xP must always be ≥ the rule's; otherwise there is a bug.
   - Secondary: how often the best formation isn't 4-3-3, and by how much; bench points in BB weeks.
4. The frozen rule is replaced only after the A/B passes and Boris accepts.

---

# Phase 3 — second half (Jan – Feb)

## Step 16 — blank/double history and predictor

Item B1.

1. **History** from archived fixtures, 2016/17 to 2025/26. Unit test: it must reproduce the 2024/25 and 2025/26 events exactly.
2. **2026/27 calendar mapper:** map these dates to gameweeks using the deadlines:
   - Carabao Cup final, 21 Mar;
   - FA Cup quarter-finals, 3 Apr;
   - FA Cup semi-finals, 24 Apr;
   - FA Cup final, 22 May.
3. **Monte Carlo of the cup brackets,** using de-margined "to qualify" odds or Elo:
   - P(team blanks in GW k) by inclusion–exclusion;
   - P(team doubles in GW k) from a table of midweeks that are free given European fixtures.
4. **Test:** a point-in-time backtest on 2024/25 and 2025/26. Pass: Brier skill score ≥ 0.10 vs the base rate.

## Step 17 — mini-league win simulator

Item B2.

- 100k joint simulations, with correlated draws for shared players and captains, plus each manager's chip schedule.
- Outputs: P(win), and ΔP(win) for each candidate move.
- Test: on 500+ public 2025/26 leagues at GW20, 26 and 32, Brier skill ≥ 0.05 vs "the current leader wins".

## Step 18 — second-half chip calculator

Item B3.

- Step 7 extended to Wildcard 2, Bench Boost 2, Free Hit 2 and Triple Captain 2, using Step 16's blank/double scenarios.
- Value each chip **relative** to the leader's likely chip timing.
- Default order per Part C rule 10.
- Test: replay of 2025/26, gain ≥ 0 vs the default heuristic.

## Step 19 — free-transfer value

Item B4.

- Re-run the planner with ±1 FT to estimate the value of each banked transfer.
- Use the estimate instead of the priors if it differs by more than 0.5 with stable CIs over 8+ gameweeks.

## Step 20 — recalibration checkpoints

Item C1.

- At GW10, GW19 and GW29, re-run the harness on all sources and report drift.
- No model changes outside pre-registered tests.

*Optional:* a realised chip-return dataset (top-10k vs random managers) to fill the evidence gap on actual chip gains.

---

## Not worth doing (all four reports agree)

- **Modelling:**
  - deep learning or news-sentiment NLP;
  - form-chasing features (single-game R² ≈ 0.12);
  - bivariate Poisson;
  - FPL's own 1–5 FDR;
  - a fatigue penalty for European games (fatigue acts through rotation, so it belongs in P(start));
  - referee card tendencies.
- **Data sources:**
  - FBref (advanced stats removed Jan 2026);
  - the ClubElo API (reported down);
  - paid feeds over $20/month.
- **Infrastructure:**
  - Git LFS;
  - diff-only exports;
  - "keepalive" hacks for the 60-day schedule rule.
- **Decision habits:**
  - pinning a chip to a "perfect week" when there are no doubles or blanks;
  - judging a decision by a single gameweek's outcome.

**Optional, under the $20 cap and Boris's call:** FPL Review Premium (about $4.50/month) as an external benchmark of point-in-time projections.
