# verify_S14 — points distributions (BUILD_PLAN.md Step 14, item N3)

Verifier: backtest-verifier, run on Fable 5.1 (claude-fable-5-1), effort high, instructions read
from `.claude/agents/backtest-verifier.md` in the worktree (identical to the loaded instructions).
Date 2026-10-19. Worktree `…\scratchpad\s14`, branch `s14-wip`, HEAD `0def550`, tree clean at the
start. Everything that writes files ran in my own scratch copies under `…\scratchpad\verify_s14\`
(`after` = 0def550 without `.git`, `before` = `git archive 149f57d`, `mut` = a third copy for the
mutations, `data_before`/`data_after` = copies of the three data files). `C:\GIT\FPL-data` (commit
`bd724ca`) was read only; no git pull, fetch, commit, push or checkout anywhere. The only file I wrote
inside the worktree is this one.

## Prereg ordering — PASS

`git log -- prereg/S14.md`: `c896f99` (15:29, RULING Step 14 verbatim and the open question),
`fc56fd5` (16:40, RULING 19 Oct afternoon verbatim; point 1 = option (a)), `15e18fa` (16:46, the
template rows). First and only S14 code commit `0def550` at 16:54:37, touching exactly
`tests/test_S14.py`, `tools/gw_pass.py`, `tools/points_pmf.py`, `tools/xp_v2_live.py` — no prereg,
runner, `test_fpl.py`, CHANGELOG or worklog change. Both rulings are in `prereg/S14.md` verbatim.

## Check 1: point-in-time — PASS

My script `verify_s14/verify_pmf.py` (log `verify_pmf.log`), run against the `after` copy with the
real `historical/2025-26` (players_raw.csv sha256 412ce017…, merged_gw.csv rounds 1–38, 29,338
player-gameweeks), `historical/2024-25` (merged_gw.csv 5bbbcba6…), `historical/2026-27`
(game_config.json a72a9908…, elements_positions.csv ac3dc891…) and
`tools/odds/E0_2025-26_fetched_2026-10-18.csv` (3e3a8352…). My own run of Step 10's normaliser gave a
`rescored_2025-26.csv` byte-identical (sha256 55fa029e…) to the harness run's.

**1a. Truncation test (decides) — PASS.** For t = 5, 21, 38 I built a history folder with rounds
> t deleted, every round-t row poisoned (minutes 90, starts 1, total_points 50, bonus 3, goals 4,
assists 3, clean sheet 1, ICT 999.9, DEFCON 99, xG/xA 5.0, …), `fixtures.csv` with the scores and
`finished` of every event ≥ t blanked, and the football-data file cut to rows dated on or before the
last kickoff of round t (50 / 210 / 380 rows kept). Rows kept / poisoned / dropped: GW5 2,852 / 742 /
26,163; GW21 14,975 / 795 / 13,987; GW38 28,916 / 841 / 0. `Season.pmfs(t)` on the truncated folder
gives the same population (342 / 319 / 334) and every PMF probability and xp_v2 value equal to the
full-data run with max difference 0.00e+00 at all three gameweeks. The haul-rate baseline per position
from the truncated re-scoring (`gate_rounds` + `baseline`) is identical to my own from the full data
(GW5 {GK 0.03226, DEF 0.0424, MID 0.05094, FWD 0.04286}; GW21 {0.02552, 0.03843, 0.04728, 0.04187};
GW38 {0.03365, 0.03552, 0.04595, 0.04666}). The poisoned round-t outcomes would have scored 342 / 319 /
334 hauls (real: 9 / 12 / 10) — neither the PMF nor the baseline saw them.

**1b. Timestamp audit (decides) — PASS.** Access audit with a recording dict in place of the raw
rows: at origin t the PMF path (`XL.core`, the sub PMFs, the bonus table, ICT, DEFCON, S11's sums)
reads rounds 1..t−1 only (GW5: 1..4, GW21: 1..20, GW38: 1..37). `gate_rounds` is built once over
rounds 2..38 (a table), and `baseline(t)` sums rounds 2..t−1 only (equal to my own sum at every t).
The per-player outcome is `rescored[(pid, t)]` of round t itself (the target). Fallback λ: S5's
`Season.lambdas(g)` fits on fixtures with event < g before `deadline(g)`; the odds λ for round t's
fixtures are football-data's pre-closing prices keyed by match date (S5's accepted input; the prereg
pins "S5's λ"). Priors: 2024/25 only. Live (`--captain` and bundle section 7): export
`fpl_export_gw7_2026-10-19.json.gz` generated 2026-10-19 06:13 UTC and odds snapshot
`odds_2026-10-19T0613Z.json.gz` 06:13 UTC, both before the GW8 deadline 2026-10-23 17:30 UTC; the
export's `player_gw_recent` reaches event 7 = the export's gameweek, so the live bonus cells and sub
PMF use events ≤ 7. I checked the export fields the live bonus table reads with `or 0`
(`g_`, `a_`, `cs`, `bonus`, `starts`): all 2,007 rows carry them, with plausible values
(cs ∈ {0, 1}, 409 clean sheets, none with goals conceded > 0 or minutes < 60; bonus 0–3; the top
row B.Fernandes GW2 23 pts, 3 goals, 1 assist, bonus 3), so no silent zero substitution.

**1c. Shift probe — not applicable (the metric is a Brier score, not a correlation on points);**
computed as information anyway: among 4,977 player-gameweeks with 60+ minutes in t and t+1, the
pooled Brier(baseline) − Brier(PMF) is +0.00121 unshifted and +0.00048 with the outcome moved to t+1.
No WARN condition applies.

## Check 2: clean-checkout test run — PASS

`python -m unittest discover -p "test*.py" -s . -t .` (no `FPL_DATA_DIR`), in the scratch copies:
- before (`git archive 149f57d`, the parent): **676 tests OK (skipped=9)**, 342 s;
- after (0def550): **686 tests OK (skipped=9)**, 346 s.
Delta +10 = `tests/test_S14.py`'s ten. The implementer's "667 → 677" is off by nine in absolute
terms (the count before the master merge `149f57d`); the delta of ten matches.

## Check 3: re-run of the pre-registered evaluation — PASS

`python tools/points_pmf.py --test` from the `after` copy (73 s here): `points_pmf_2025-26.txt`
identical to the implementer's file in every line but the output path on line 2 (the normaliser's
"-> …\rescored_2025-26.csv"). `python tools/points_pmf.py --captain --data C:\GIT\FPL-data`:
`captain_gw8.txt` byte-identical.

Through the harness (`PM.test_2526` called from my script): primary +0.001179, 90% CI
[+0.000696, +0.001779], n = 34, predicted 403.600 against 449 actual (−10.1%), max |E[PMF] − xp_v2|
9.85e-12, 49 independent-parts cases, bonus "no start 665, tilted 10374" (no flat fallback) — the
claimed +0.00118 [+0.00070, +0.00178], 403.6 v 449, 9.85e-12, 49. My own loop (own gate and
baseline counts, own Brier sums, `BT.bootstrap_mean` seed 20261018) matches the harness within 1e-9
on the mean and both bounds, exactly on the counts, and within 1e-12 on every per-gameweek
difference. Both pass conditions hold: lower bound +0.000696 > 0 and −10.1% within ±15%.

**The mean equals xp_v2 by construction (my own script, GW5 / 21 / 38):** against S6b's own
`Replay.xp_v2(t)` (not `XL.core`), the population is identical (342 / 319 / 334); max |E[PMF] −
xp_v2| 5.08e-13 / 6.67e-13 / 4.73e-13; every PMF sums to 1 within 3.3e-16 with no negative mass;
per half, max |E[X] − e_xg| ≤ 7.4e-13, max |E[L] − e_bl| ≤ 7.6e-13, max |E[U] − E[pts | sub]| ≤
2.2e-16; and my own independently written term sums (E[X] = 2 + Σ_f (xG_f·GOAL + xA_f·3 +
e^{−λ_opp,f}·CS) + DEFCON + 0.8·ICT; E[L] = Σ_f (2 + 0.62·xgi·GOAL + 0.38·xgi·3 + 2·p_dc + K_f))
equal S6b's `e_xg` and `e_bl` within 1.8e-15. Hand check of the one-count GK/DEF structure on a
real DEF (pid 541, GW5, λ_opp 1.4457): P(K = 4) = e^{−λ}, P(K = 0) = P(GC = 1), P(K = −1) = P(GC ∈
{2, 3}), P(K = −2) = P(GC ∈ {4, 5}), no mass at 2 or 3 — the clean sheet never coincides with a
penalty. Live: max |E[PMF] − xp_v2| 5.67e-13 over the 285 forecast players; our 15 all forecast;
Saka mean 6.0015, P≥10 0.1855, P≥15 0.0516, p90 12 at the top, as claimed.

## Check 4: prereg compliance — PASS

Read against the template rows: population = every player-gameweek with an xp_v2 forecast at
origin t (XL.core's gate: `mins_last4 >= 45`, a fixture; verified equal to S6b's population);
outcome = `points_2627_rules` of round t, 0 without a row, one unit per (element, round)
(`rules.normalise` keys its units by (element, round), so a double is summed); baseline = per
position (the origin's) the share with re-scored points ≥ 10 over rounds 2..t−1 among the same gate
(`gate_rounds`/`baseline`); primary = per-gameweek mean of Brier(baseline) − Brier(PMF) for ≥ 10;
bootstrap `BT.bootstrap_mean`: B = 10,000, CI = 0.90 percentile, seed 20261018, unit = gameweek,
n = 34; pass = lower bound > 0 **and** |Σ P(≥10) − actual| ≤ 0.15 × actual; mean check bar 0.05
printed; secondary 15+, reliability deciles, independent-parts count printed as information. The
PMF definitions match the rows: mixture P(start)·(½X + ½L) + P(sub)·U + rest at δ0, independent
parts when P(start) + P(sub) > 1 (49 cases, printed); X with Poisson goals/assists per fixture at
S11's allocation, Bernoulli clean sheet at e^{−λ_opp}, DEFCON Bernoulli at the hit rate (= defcon/2),
appearance/DEFCON/bonus once per gameweek; the bonus table by (group × involvements 0/1/2+ × clean
sheet for GK/DEF) from starts in rounds < t, 30-row back-off in the stated order, exponential tilt by
bisection to 0.8 × ICT percentile, B = 0 at a zero target, Bernoulli(target) fallback when
unreachable (0 cases); L per fixture with `project_reliability`'s shrunk xgi and logistic DEFCON,
one Poisson(λ_opp) count for the GK/DEF clean sheet and goals conceded, the MID own-rate clean sheet;
U the empirical sub points per position from the same rows as E[pts | sub]; no saves; Poisson tail
at 15. Summaries mean, P(≥10), P(≥15), p90 = smallest k with P(≤ k) ≥ 0.9. Captain table: our 15
sorted by mean, bonus cells from the export's starts. The listed acceptance tests all exist in
`tests/test_S14.py` (sums to 1, mean within 1e-6 on toys, one Poisson count hand case, tilt, double
summed, mixture and fallback, summaries on a hand PMF, point-in-time of PMF and baseline, both pass
conditions, the bundle table, run.txt/CLI/isolation; `test_fpl.py` untouched). No metric was
promoted and no constant differs from the prereg; the prereg was committed eight minutes before the
code and not edited since.

## Check 5: recording path — PASS

No runner file changed: `diff -rq before after` lists only `tests/test_S14.py`,
`tools/points_pmf.py` (new), `tools/gw_pass.py` and `tools/xp_v2_live.py`. The nightly path
(`fpl_nightly.py`, `fpl_ship.py`, `fpl_edge.py`, `fpl_sync.py`, `fpl_gate.py`, `fpl_publish.py`,
`fpl_alert.py`, `fpl_odds.py`) imports nothing under `tools/` or `analysis/` (grep), the workflows
reference none, and `tests/test_S14.py`'s isolation test (a subprocess importing the six runner
modules and listing anything from `/tools/`) prints `[]`. Demonstrated anyway: scratch copies of
`fpl_export_gw7.json`, `fpl.sqlite` and `projection_log.csv`; `fpl_edge.py --record --source` for
own, xg, minutes, bottomup, fpl_ep with the `149f57d` code and with the `0def550` code: both record
275 / 260 / 260 / 260 GW8 forecasts (fpl_ep skipped: no ep_next), both logs 7,480 rows, identical in
every column but `made_at`. The real `projection_log.csv` (7,502 rows) and the data worktree were
not touched (`git status` clean).

`xp_v2_live` did not move: `tools/xp_v2_live.py --data C:\GIT\FPL-data` with both codes gives a
byte-identical `xp_v2_live_gw8.txt`; `XL.live()` under both codes: 285 players, the same set, max
|xp diff| 0.0, max difference 0.0 on every shared detail key; the new `fixtures` list sums to the
`xg`/`xa` aggregates exactly (max 0.0). `tools/gw_pass.py --data C:\GIT\FPL-data` with both codes:
the bundles differ only in the generation timestamp on line 1 and the appended section 7; no
"missing input" or failed section in either.

## Check 6: mutation spot-check — PASS (10 of 10 red)

In the `mut` copy, one line changed at a time, `python -m unittest tests.test_S14` after each, the
original restored and green afterwards:
1. halves' weights 0.5/0.5 → 0.6/0.4: FAILED (4);
2. goals conceded `k // 2` → `k // 3`: FAILED (5);
3. baseline rounds `range(2, t)` → `range(2, t + 1)`: FAILED (1, the point-in-time test);
4. subs include starters: FAILED (2);
5. `BONUS_MIN_ROWS` 30 → 3: FAILED (1);
6. pass line `and` → `or`: FAILED (1);
7. DEFCON value 2 → 3 in X: FAILED (4);
8. PMF training rounds `range(1, t)` → `range(1, t + 1)`: FAILED (3);
9. mixture branch forced (`if True`): errors=1;
10. independent note forced False: FAILED (1).

## Check 7: secrets — PASS

The four files of `0def550` (and the added lines of the two diffs) contain no API key, no URL with
`apiKey=`, no Authorization header, no `http`, token or `ODDS_API` string. Nothing I ran wrote to
the worktree, `C:\GIT\FPL` or `C:\GIT\FPL-data`; the two pre-existing untracked files in
`C:\GIT\FPL` (`worklog/verify_S2b_pre.md`, `worklog/verify_W1b_pre.md`) predate this run.

## Notes (not verdict items)

- `tools/out/points_pmf/run.txt` in the worktree describes the later `--captain` run (duration 1 s);
  the `--test` run's run.txt was overwritten because both commands share the output folder. The
  report should cite a run.txt that matches the output it quotes (run `--test` last, or give the two
  commands different `--out` folders). My own `--test` run reproduced the file in full.
- The implementer's test counts (667 → 677) are from before the master merge; at `149f57d` →
  `0def550` they are 676 → 686.
- The result is information only; adoption needs Boris's acceptance in chat (prereg).

VERDICT: PASS

Reason: the prereg (both rulings verbatim and the filled rows) was committed before the only S14
code commit and was not edited after; the PMF is exactly the pre-registered distribution of xp_v2 as
tested — on the real 2025/26 its mean equals S6b's own `Replay.xp_v2` within 7e-13 at GW5/21/38 and
each half's mean equals the corresponding term; the truncation test with rounds > t deleted and
round t poisoned reproduces every PMF probability and the haul-rate baseline to 0.00e+00 at GW5/21/38
and the access audit shows only rounds < t are read; my re-run through the harness and my own
independent loop both give +0.001179 [+0.000696, +0.001779] and 403.6 against 449 (−10.1%), the
metric, filter, baseline, bootstrap and both pass conditions being those of the prereg; the suite
goes 676 → 686 OK; nothing on the runner path changed and the recording path and the live xp_v2
numbers are byte-identical under both codes; ten of ten mutations go red; no secrets.
