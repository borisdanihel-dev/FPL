# Verifier report: S15 (BUILD_PLAN Part F item F-G, Step 15; offline)

Verifier model: Fable 5.1 (claude-fable-5-1), effort high, as
`.claude/agents/backtest-verifier.md` on disk says (read first; it is identical
to the loaded instructions). Worktree
`C:/Users/Boris/AppData/Local/Temp/claude/C--GIT-FPL/442a647f-7693-4ced-b840-0df7f5bfd943/scratchpad/s15`,
branch `s15-wip`, HEAD 91f401d, base 7580cf2 (`s8b-wip`), status clean before
and after this run. Everything I ran was run from clean `git archive` copies of
7580cf2 and 91f401d in my scratch folder
(`.../scratchpad/verify_s15/{base,head,mut}`) with all outputs under
`.../scratchpad/verify_s15/`; the only file written in the worktree is this one.
Inputs read only: `C:/GIT/FPL/historical` (2025-26, 2024-25, 2023-24,
2026-27), the tracked `tools/odds/E0_2025-26_fetched_2026-10-18.csv` and
`E0_2024-25_fetched_2026-10-19.csv`, and for the live check `C:/GIT/FPL-data`
at e1154dd (not pulled, not changed: `git status` empty afterwards).

## Full regeneration (check 3.3)

`python tools/builder.py --test --hist C:/GIT/FPL/historical --out <my scratch>/regen`
from the clean 91f401d archive: 5,470 s (09:39:17-11:10:27 UTC), sha256 of my
`builder_test.txt` e60ab353... The implementer's file (sha256 f328fe73...,
`tools/out/builder/run.txt`: commit 91f401d, modified tracked files 0, 5,476 s)
differs from mine only in the two `re-score: normalised ... -> <path>` lines,
which carry the `--out` path; every other line, all 68 per-date rows included,
is byte-identical. The printed result: pooled 68 dates +33.31 [+25.29,
+41.54], builder >= rule on 0.78, projected >= rule on every date -> PASS;
2025/26 +23.94 [+13.32, +34.50] (0.71); 2024/25 +42.68 [+30.79, +54.71]
(0.85); every sixth date +44.75 [+24.08, +66.00] over 12; not 4-3-3 on 68 of
68 (cost 1.66); first-week BB bench builder 13.09 v rule 7.69; the GK+DEF cap
projected cost 0.49, realised +0.57. All equal to the implementer's numbers
(difference 0 < 1e-6).

## Prereg and commit order

- `prereg/S15.md` on master: ae1d368 (2026-10-20 08:35:58 +0200) and amendment
  1 at 3b31599 (08:36:55 +0200). First S15 code: 6f362a8 (08:42:51 +0200), then
  fef1edc (tests), 0f72c86 (tests), 91f401d (the AM filter + one assertion).
  Prereg committed before any code: yes. (574 lines of `tools/builder.py`
  committed six minutes after the prereg suggests the code was drafted
  earlier; the protocol's requirement is the commit order, which holds.)
- The rulings are in the prereg verbatim: F-G, BUILD_PLAN Step 15, the Mon 19
  Oct night ruling (point 5 sets the lambdas), and amendment 1 (the local
  search's candidates).
- `git diff --stat 7580cf2..91f401d`: `tests/test_S15.py` (+308) and
  `tools/builder.py` (+574) only. No runner file, no workflow, no data path.

## Check 1 - point-in-time leak check

**1a Truncation test (decides): PASS.** `scripts/truncate.py` (mine) rebuilt
each origin from a copy of the season folder in which rows of rounds > t are
removed, rows of round t keep only identity, fixture and price fields with
every performance field set to a sentinel (minutes 77, points 7, xG 0.70,
ICT 7.7, ...), and every fixture of rounds >= t carries the sentinel score 7-7
(the harness derives the pairings from fixtures that have a score, so they
must survive). The full-data outcomes object was passed in unchanged (it feeds
realised points only). Compared, with tolerance 1e-9: the six-week matrix
(every player, every week), the market (id, club, position, price), the
rule's player list (mins_last4, order), `played`, the pairings, the
reliability inputs (p_start, mins_last4, xgi90, team, pos), the excluded
counts, the lambda sources, the rule's squad and spend, the builder's squad
and both objectives.

| season | origin | rows kept / sentinel / dropped | fixtures >= t with 7-7 | matrix sizes | rule proj | builder proj | result |
|---|---|---|---|---|---|---|---|
| 2025/26 | GW5 | 2852 / 742 / 26163 | 340 | 342 x 6 | 256.956080 | 264.275864 | identical |
| 2025/26 | GW21 | 14975 / 795 / 13987 | 180 | 319 x 6 | 255.187756 | 275.053214 | identical |
| 2025/26 | GW38 | 28916 / 841 / 0 | 10 | 334 x 1 | 58.773892 | 61.504693 | identical |
| 2024/25 | GW5 | 2550 / 661 / 24394 | 340 | 324 x 6 | 245.460422 | 252.384525 | identical |
| 2024/25 | GW21 | 13454 / 724 / 13427 | 181 | 337 x 6 | 239.520954 | 297.708149 | identical |
| 2024/25 | GW38 | 26801 / 804 / 0 | 10 | 332 x 1 | 62.344843 | 64.375788 | identical |

**1b Timestamp audit (decides): PASS for S15's own inputs; two inherited,
ruling-sanctioned limitations noted.** By code reading of every input path
of `Origin`, `Season2425.forecasts` and `realised`:
- training rows: `canonical_through(c, t-1)`; `mins_last4` over rounds
  t-4..t-1; `sub_inputs_2526`, `ict_percentile`, `defcon_rates` and S11's
  `player_sums` read rounds < t only; the fallback is fitted on results with
  `event < t`, cut at round t's first kickoff (S5's rule);
- prices of round t (`rp.price[t]`), clubs `club_at(cm, pid, t)`, every
  player status 'a' (no historical status; as the prereg pins);
- realised points use the re-scored outcomes of weeks t..t+5 only after the
  squads are fixed;
- inherited (S5/S6b/S8b, ordered by the night ruling point 5, identical for
  both sides): week t's lambdas come from football-data closing odds, which
  are dated by match date (after the deadline for a gameweek's later matches);
  the pairings of weeks t..t+5 come from the final `fixtures.csv`, so a
  postponed match appears at the round it was eventually played; the
  adapter's position per player is the last row's. None is S15's and none
  can be removed by S15; the mutation m22 shows the test suite catches a
  window that includes round t.

**1c Shift probe: not applicable** (no correlation metric on points; the
primary metric is realised window points builder - rule).

## Check 2 - clean-checkout suites

`python -m unittest discover -p "test*.py"` on clean archives, `FPL_DATA_DIR`
unset: 7580cf2 **715 OK, skipped=10** (330 s); 91f401d **727 OK, skipped=10**
(335 s). `tests/test_S15.py` holds 12 tests (Objective 2, Search 1, Gaps 4,
RulePort 1, Bar 1, Season 1, Live 1, Isolation 1); 715 + 12 = 727. The main
session's "728 expected at 91f401d" is wrong: 91f401d adds an assertion inside
`test_a_date_and_point_in_time`, not a test.

## Check 3 - the pre-registered evaluation re-run

**3.1 The pooled verdict's arithmetic from the per-date table** (`scripts/verdict_check.py`,
my own bootstrap: unit = date, B = 10,000, seed 20261018, percentile 90%, the
same index rule as `backtest.bootstrap_mean`), parsed from the implementer's
`tools/out/builder/builder_test.txt` (sha256 f328fe73... = run.txt):
- pooled n=68: mean **+33.3088**, CI **[+25.2941, +41.5441]**, share **0.7794**,
  projected >= rule on every date (minimum margin +2.04) -> PASS; printed
  +33.31 [+25.29, +41.54], 0.78: match.
- 2025/26: +23.9412 [+13.3235, +34.5000], share 0.7059 (printed +23.94
  [+13.32, +34.50], 0.71); 2024/25: +42.6765 [+30.7941, +54.7059], 0.8529
  (printed +42.68 [+30.79, +54.71], 0.85); every sixth date n=12: +44.7500
  [+24.0833, +66.0000] (printed +44.75 [+24.08, +66.00]).
- not 4-3-3 on 68 of 68, mean 4-3-3 cost 1.6569 (printed 1.66); realised cap
  cost +0.5735 (printed +0.57). The projected cap cost (0.49) and the bench
  points (13.09 / 7.69) are not in the table; see the regeneration.

**3.2 Ten dates end to end** (`scripts/sample.py` + `scripts/vlib.py`, my own
code written from the prereg's definitions: the best XI by brute force over
all 1365 eleven-subsets, captain = highest xp in the XI, S7's bench weights,
decay 0.85; realised = XI by the origin's matrix each week, FPL autosubs on
realised minutes with the bench in forecast order, the captain doubled;
legality; a single-swap local-optimum check over the top-25 pool outside the
15; the layer-1 gate recomputed from the canonical rows; the frozen
`fpl_edge.build_three_layer_squad` called by me on the port's candidates with
the quota split). Every number equals the harness's record and the printed
table (realised to the unit, objectives to 1e-4 shown, equal to 1e-9 in the
json):

| season | GW | rule real | builder real | proj rule | proj builder | form | bench b/r | rule spent | builder spent | single-swap improvement | gate = port | order ok | frozen build = record |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2025/26 | 5 | 373 | 386 | 256.9561 | 264.2759 | 4-5-1 | 12 / 10 | 97.7 | 99.7 | none | yes | yes | yes |
| 2025/26 | 12 | 311 | 351 | 281.4326 | 290.8781 | 5-4-1 | 9 / 6 | 98.4 | 99.9 | none | yes | yes | yes |
| 2025/26 | 21 | 272 | 319 | 255.1878 | 275.0532 | 3-5-2 | 15 / 2 | 89.6 | 99.8 | none | yes | yes | yes |
| 2025/26 | 28 | 290 | 393 | 261.1113 | 276.1362 | 5-4-1 | 12 / 8 | 94.1 | 100.0 | none | yes | yes | yes |
| 2025/26 | 38 | 75 | 70 | 58.7739 | 61.5047 | 5-4-1 | 16 / 6 | 89.5 | 99.1 | none | yes | yes | yes |
| 2024/25 | 5 | 241 | 299 | 245.4604 | 252.3845 | 3-5-2 | 7 / 6 | 98.5 | 100.0 | none | yes | yes | yes |
| 2024/25 | 15 | 336 | 369 | 250.3361 | 258.0693 | 3-5-2 | 8 / 5 | 97.8 | 100.0 | none | yes | yes | yes |
| 2024/25 | 23 | 344 | 479 | 251.2844 | 309.6855 | 3-4-3 | 19 / 7 | 91.4 | 99.6 | none | yes | yes | yes |
| 2024/25 | 30 | 206 | 326 | 235.7786 | 255.4221 | 4-5-1 | 12 / 5 | 81.4 | 98.3 | none | yes | yes | yes |
| 2024/25 | 38 | 57 | 62 | 62.3448 | 64.3758 | 3-5-2 | 11 / 6 | 93.7 | 99.5 | none | yes | yes | yes |

Both squads legal under 100.0, quota 2/5/5/3 and 3 per club on every date;
the builder's squad is a single-swap local optimum on every date; the GK/DEF
keys equal the matrix's six-week sum and the MID/FWD keys equal
p_start x nfix on every candidate.

**3.3 Full regeneration:** see the section near the top of this report.

## Check 4 - prereg conformance

PASS. Primary metric = per-date realised window points builder - rule, dates
pooled over both seasons (68), bootstrap unit = date, B = 10,000, seed
20261018, 90% CI, the three-part bar (mean > 0 with the CI excluding 0; builder
>= rule on >= 60% of dates, ties counting; projected builder >= rule on every
date) - all as in `verdict()` and the printed report, and all as the prereg
pins. Secondary lines are information only and were not promoted. The one
code change after the first run (91f401d) is the AM filter, examined below;
no parameter, metric or filter was changed after a result existed. Two
small readings to record, neither affecting the verdict:
- amendment 1 says the pair swaps are tried "by position, then by the pool's
  order"; the code tries them in the squad list's current order, then the
  pool's order (deterministic, fixed per state, but not literally by
  position). The search's stopping rule, candidates and single-swap
  best-improvement are as pinned.
- the cap-on build (for the cap's cost) starts from the greedy squad only,
  not from the rule's squad; the prereg does not require a rule start there.

**The AM fix (91f401d) is a data correction, not a design change.** Reproduced
with the 6f362a8 code (`scripts/am_crash.py`): the 2024/25 GW23 market holds
20 rows with position 0 (vaastav's "AM" assistant managers, 322 rows from
GW23), none of which has a matrix value; `greedy` raises `KeyError(0)` on
them; the GW22 market is identical with and without the filter. Assistant
managers cannot sit in a 15, so the filter removes non-players only; it
cannot change any 2025/26 date or any 2024/25 date before GW23. The first run
printed no result: `test()` computes every date of both seasons before
`report()` prints anything and `builder_test.txt` is written only after
`test()` returns, so a crash inside `season_dates` leaves only a traceback.

## Check 5 - recording path

PASS by construction: no runner file changed (diff-stat above); from the
91f401d copy, importing `fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate,
fpl_publish` loads none of `builder, planner_2425, planner, chips,
xp_v2_live, odds_lambda, shares, xp_v2_replay, xp_v2_2425, backtest`
(printed `[]`); no workflow references `builder`. `--record` is the runner's
alone and was not run (CLAUDE.md forbids it locally); nothing in this item can
reach `projection_log.csv`.

## Check 6 - mutations

`scripts/mutate.py`: 24 one-line mutations of `tools/builder.py` in a scratch
copy, `tests/test_S15.py` each time; **22 of 24 red**, the suite green again
after the restore. Red: captain dropped, sub-keeper weight dropped, outfield
bench weights dropped, decay off, share bar 0.50, projected invariant ignored,
CI lower bound ignored, AM filter removed, pair swaps removed, pool includes
the 15, A/B cap on, rule's squad not a start, rule formation 3-4-3, club max
4, GK+DEF cap 3, live cap off, free hit / BB over six weeks, nfix_later from
weeks[1:], quota split not proportional, mins window including round t, one
formation only, bench_full ignored. Not caught: `share <= 0.667` -> `<`
(equality is unreachable with integer minutes over 90 x n matches; an
equivalent mutant in practice) and the 45-minute gate moved to 44 (the toy
export has no player at exactly 44 minutes; the live function has the same
constant and the real-export equality below would catch a real divergence).

## Check 7 - secrets, provenance, isolation

PASS. `git diff 7580cf2..91f401d` contains no `apiKey`, `Authorization`,
bearer or 32+ character key-like string. `tools/out/builder/run.txt`: commit
91f401d, modified tracked files 0, 5,476 s, sha256 of `builder_test.txt`
f328fe73... (matches the file). `tools/out/` is git-ignored. The nightly
imports nothing new (above).

## The item's own checks

1. **The rule port.** `scripts/port_real_export.py` on the real
   `fpl_export_gw7_2026-10-19.json.gz` (gameweek 7, generated
   2026-10-19T22:05:17Z): `rule_candidates` equals `fpl_edge.wildcard_candidates`
   on every field compared (id, name, team, price, sum6, nfix, nfix_later,
   p_start, xgi90, key, rank, share) for all of GK 19 / DEF 71 / MID 80 / FWD 19
   candidates, the excluded counts are equal ({status not 'a': 200, share <=
   0.667: 92, under 45 min: 187}), the quota split equals `budget_split` with no
   squad ({13.33, 33.33, 33.33, 20.0}), and the frozen build gives the same 15
   with spent 86.9 on both. The test additionally asserts the frozen function
   is called once, unchanged, with (4, 3, 3) and 100.0 (mock-wrapped). The
   history inputs are as pinned (the mins window t-4..t-1 and the team
   matches from the fixture schedule in that window, round-t prices,
   `club_at(t)`, all 'a', the GK/DEF sum6 = the shared matrix, the MID/FWD key
   p_start x nfix then xgi90, `nfix_later` over `weeks[2:]`); the players are
   fed in the export's order (by position, then points desc), which the
   stable sort needs for tie order. **Fairness:** the rule leaves money
   unspent because its frozen fill-and-upgrade never trades the bench's
   cheapness for XI money (81.4-98.5 of 100.0 on my ten dates, 86.9 on the
   live GW7 export); that is the rule as frozen and the A/B is against the
   rule as frozen, with the no-squad quota split the prereg pins for a
   hypothetical wildcard (the live rule would use the current squad's spend
   shape, which can move its picks). Boris should read part of the builder's
   edge as "it spends the budget".
2. **The builder.** `week_value` is `_best_xi`'s loop (same formations, same
   strict-greater tie rule) plus the captain and S7's weights (0.30/0.10/0.03
   in forecast order, 0.03 the sub keeper); `objective` = sum 0.85^k V_k;
   `legal` = quota, distinct, budget, 3 per club, the GK+DEF cap when on;
   greedy = decayed xP per million with the cheapest-fill feasibility check,
   then the cheapest fill; local search = amendment 1 (singles best
   improvement, pairs first improvement, back to singles, stop at 1e-9, S8's
   pool of 25 per position outside the 15); multi-start from greedy and from
   every legal given start - the rule's squad in the A/B - so projected
   builder >= rule by construction (confirmed on every date: minimum margin
   +2.04); the cap off in the A/B (`build(..., False, starts=[rsq])`) and on
   for its cost (`build(..., True)`), asserted by the test and by mutation
   m12/m13.
3. **The matrix.** `Season2425.forecasts(t)`: week t = `s5.lambdas(t)` (S5's
   odds, else fallback; 340 week-t fixture-weeks all odds in both seasons),
   weeks t+1..t+5 the fallback fitted on results of rounds < t cut at round
   t's first kickoff (1550 fixture-weeks per season = 29 x 50 + 40 + 30 + 20 +
   10), through S6d's `core` on `reliability_inputs(canonical_through(c,
   t-1))`; sources recorded. Outcomes: `XR.rescore` (2025/26, Step 10, 29338
   player-gameweeks) and `F.rescore` (2024/25, S10b, 26919, DEFCON absent and
   flagged). Realised = `PL.Replay.realised` (S8's) per week with the
   origin's matrix choosing XI and captain; my independent realised equals it
   on all ten dates. Point-in-time: check 1a.
4. **Independent recompute:** check 3.2 and 3.1.
5. **Tests:** check 2 and check 6.
6. **Live.** From the 91f401d copy, read-only against `C:/GIT/FPL-data`
   (e1154dd), `--out` in my scratch: `--wildcard` GW8-13 from
   `fpl_export_gw7_2026-10-19.json.gz`, budget 99.7 = bank + selling prices,
   sources week t odds 10, later weeks odds 10 (the snapshot prices GW9) and
   fallback 40, objective 286.59 with the cap on, 286.59 without (cost 0.00),
   4-5-1, spent 99.6; `--freehit` GW8 one week, objective 65.93, cap cost
   0.00, 5-4-1; `--bb` GW8 one week bench at full weight, objective 80.54, cap
   cost 0.00, 5-4-1, spent 99.5. Each prints "information only". The toy
   (`Live.test_wildcard_freehit_bb`) asserts the cap on then off, GW9-14 for
   the wildcard, one week for the others. `git status` in FPL-data empty
   afterwards.
7. **Provenance etc.:** check 7, check 5 and check 4's AM paragraph.

## Scratch artefacts (outside the worktree)

`.../scratchpad/verify_s15/`: `suite_base.txt`, `suite_head.txt`,
`sample_2526.txt`, `sample_2425.txt` (+ `sample_*/sample_<season>.json`),
`trunc_2526.txt`, `trunc_2425.txt`, `mutations.txt`, `live_*.txt` + `live/`,
`am_crash.txt`, `regen/` + `regen_stdout.txt`, `scripts/`.

VERDICT: PASS

Reason: the prereg (ae1d368, amendment 3b31599) was committed before the first
S15 code (6f362a8) and holds the rulings verbatim; the evaluation is exactly
the pre-registered one (per-date realised window points builder - rule, 68
pooled dates, bootstrap over dates B = 10,000 seed 20261018 90%, the three-part
bar) and my full regeneration from a clean 91f401d copy reproduces the
implementer's output byte for byte apart from two path lines, my own bootstrap
of the per-date table gives +33.3088 [+25.2941, +41.5441] with share 0.7794,
and ten dates recomputed end to end with independently written objective,
realised, legality and local-optimum code match to 1e-9; the truncation test
on six origins (both seasons, GW5/21/38) rebuilt the matrix, the market, the
rule's inputs and both squads identically from inputs of rounds < t with
round t's outcomes replaced by sentinels; the rule port equals
`fpl_edge.wildcard_candidates` and the frozen build on the real GW7 export;
the suites are 715 and 727 OK (10 skipped) on clean copies, 22 of 24
mutations go red (the two survivors are unreachable boundary values); no
runner file changed, the nightly imports nothing new, no secrets; and the one
post-run change (the AM filter) is a reproduced data correction after a crash
that printed no result. Noted for Boris, not failures: the week-t lambdas and
the final-schedule pairings are inherited S5/S8b conventions shared by both
sides and ordered by the night ruling; the rule's unspent budget (81.4-98.5
on my sample, 86.9 live) is the frozen rule's own behaviour under the pinned
no-squad quota split, so part of the builder's edge is simply spending the
money; the pair-swap order is the squad's order then the pool's rather than
literally "by position"; and the correct post-item test count is 727, not 728.
Adoption still needs Boris's acceptance in chat (information only until then).
