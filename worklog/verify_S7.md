# verify_S7 — backtest-verifier report

Item S7 (tools/chips.py, tests/test_S7.py), repository C:\GIT\FPL-b, branch
lane-b, verified at commit eb585b5 (code commit d0fc715; docs 56631b4 and
eb585b5). Verifier model: Fable 5.1 (claude-fable-5-1), effort high, as
.claude/agents/backtest-verifier.md on disk (read first; it matches the loaded
instructions). Model item with a pre-registered test: checks 1-7 plus the
prereg's acceptance tests 1-6. Date 2026-10-18. No key-like strings occur in
any file or output examined (nothing to mask). Data read-only from
C:\GIT\FPL-data (HEAD e8629f0 "nightly 2026-10-18", clean before and after)
and C:\GIT\FPL-b\historical\2025-26; my outputs under tools/out/verify_s7/
(ignored) and the session scratchpad.

## Prereg before code — PASS

- prereg/S7.md committed f9ca3d0 (2026-10-18 15:40:27 +0200); Amendment 1
  94fbc36 (15:43:22); first code commit d0fc715 (21:06:15); docs 56631b4
  (21:11:56) and eb585b5 (21:18:07, report/CHANGELOG only: the BB/FH split
  sentence). `git show d0fc715 --stat`: tests/test_S7.py and tools/chips.py
  only. `git diff b3ff48a..HEAD --stat` outside worklog/ and CHANGELOG.md:
  the same two files.
- The ruling text "RULING S7 (Step 7, P4, offline)" points 1-5 and
  "Amendment 1" point 4 are present verbatim in prereg/S7.md; the amendment
  header states it was appended before any code and before any evaluation
  number, and the git order confirms it.

## Check 1 — point-in-time leak check

### 1a Truncation test (decides) — PASS

Method (scratchpad trunc_1a.py, output trunc_1a.txt): for t in (5, 12, 19) a
copy of historical/2025-26 holding rows with round < t unchanged; rows with
round >= t with every outcome column garbaged (minutes 90, points 50, xG
3.0, BPS 99, defcon 40, scores 7-7, ...), pairing columns kept (name,
position, team, element, fixture, round, kickoff_time, opponent_team,
was_home); `value` and `selected` kept for round t only and set to 999 for
rounds > t; fixtures.csv events >= t with fake 7-7 scores and pairing only.
Rebuilt with the item's own `chips.Replay` (`forecasts(t)`, `values(squad,
t)`, `induction`, `heuristic_action`) on the same 50 seed-7 squads and
compared with the full copy:

| origin | forecasts (weeks t..19) | V_BB / V_FH, 50 squads | XIs, bench order, FH XI | calculator / heuristic action |
|---|---|---|---|---|
| GW5  | 15 weeks, 314 players each, max abs diff 0.000e+00 | max abs diff 0.000e+00 | identical 50/50 | identical 50/50, 50/50 |
| GW12 | 8 weeks, 291 players each, max abs diff 0.000e+00 | 0.000e+00 | identical 50/50 | identical 50/50, 50/50 |
| GW19 | 1 week, 308 players, max abs diff 0.000e+00 | 0.000e+00 | identical 50/50 | identical 50/50, 50/50 |

Squads sampled from the truncated copy are identical to the full copy's (GW1
rows are untouched). Worst difference over every forecast and chip value:
0.0. The realised gains do read round t: on the garbaged copy squad 0's (BB,
FH) gains move from (0.0, 20.0) / (0.0, 38.0) / (0.0, 10.0) to (200.0, 0.0)
at the three origins, i.e. `bb_gain`/`fh_gain` read `actual[t]` only, after
the decision (also by inspection: they index `self.actual[t]` and nothing
else).

### 1b Timestamp audit (decides) — PASS

- 2025/26 (scratchpad audit_1b.py, output audit_1b.txt): for every origin t
  in 5..19, rows with round < t whose kickoff_time is at or after round t's
  first kickoff: 0; fixtures.csv events < t kicked off at/after round t's
  first kickoff: 0. So no training row (round < t) was played after origin
  t's deadline (rounds 5-19 start 2025-09-20 .. 2025-12-30, in order).
  Forecasts at t are built from `canonical_through(canonical_at(hist, t),
  t - 1)` with `gws_played = t - 1` (training rows and team matches with
  event <= t-1, clubs as of t), plus the pairing of week u from
  `team_matches` (fixture list, scores not used for u >= t: 1a shows fake
  scores change nothing). Prices: `price_at(pid, t)` reads rounds <= t;
  fodder reads round t's `value`.
- Live path: export fpl_export_gw7_2026-10-18.json.gz generated
  2026-10-18T18:45:03Z, before the GW8 deadline 2026-10-23T17:30:00Z. The
  log holds 560 own rows for GW8 in two snapshots (2026-10-17T22:04:06Z,
  2026-10-18T18:45:03Z), 0 at or after the deadline; `chips.own_week_points`
  reads 285 'own' rows for GW8, exactly the last pre-deadline snapshot's 285
  players with equal values (read independently of `fpl_edge.forecasts`).
  Weeks 9-13 use `project()` on the same export ('own-model' 285, 'gate'
  383 per week); weeks 14-19 are proxies and labelled so.

### 1c Shift probe — not applicable

The item's metric is realised chip points (a paired difference of realised
sums), not a correlation of forecasts with points; there is no target to
shift. The S4 shift probe on the `bottomup` source the replay uses stands
(verify_S4.md: 2025/26 bottomup all +0.065 / starters +0.147, no WARN).

## Check 2 — clean-checkout test runs — PASS

Clean archives (`git archive`) in the scratchpad, no FPL_DATA_DIR:
- before (b3ff48a): `python test_fpl.py` Ran 386 tests, OK (skipped=8).
- after (HEAD): `python test_fpl.py` Ran 386 tests, OK (skipped=8);
  `python -m unittest tests.test_S7` Ran 13 tests, OK.
Matches the implementer's 386 OK (8 skipped) before and after, 13 new.

## Check 3 — pre-registered evaluation re-run — PASS

`python tools/chips.py --replay --out tools/out/verify_s7` (my run, 13 min):
tools/out/verify_s7/chips_replay_2025-26.txt is **byte-identical** (`cmp`)
to the implementer's final-code run tools/out/final/chips_replay_2025-26.txt
(whose run log ends "FINAL REPLAY DONE"; the file equals the log modulo
CRLF). The preview run (the implementer's earlier process, preserved in
tools/out/chips_replay_run.log; tools/out/chips_replay_2025-26.txt itself was
overwritten with the final content at 21:18:01 by the main session) matches
mine on every number; the only difference is the added "mean BB gain / mean
FH gain" text. Numbers (printed at 2 dp; the computation is deterministic,
seeded 20261018, so equal text from equal inputs is the strongest available
comparison; no full-precision output exists on the implementer's side):

- realised chip points per squad: calculator 16.56, heuristic 16.74,
  both-early 10.80;
- paired gain calculator - heuristic: mean -0.18, 90% CI [-1.26, +0.72]
  (50 squads, B = 10,000, seed 20261018); bar mean >= 0 and lower > -3:
  **FAIL** (lower bound clears -3, mean below 0);
- information: calculator - both-early +5.76 [+1.00, +10.60]; BB gain
  +3.20 for both planned policies, FH gain +13.36 vs +13.54; chip weeks as
  printed.

Live: `python tools/chips.py --out tools/out/verify_s7` gives a chips_live.txt
byte-identical to tools/out/chips_live.txt (GW8 PLAY BB, margin +0.07,
residual pools GK 62 / DEF 301 / MID 368 / FWD 82, 18% same action, bench
prep and Free Hit screen as reported). The margin arithmetic ties to the
table: V(8, BB+FH) 12.39 minus the best other action (PLAY FH 5.79 + V(9,
BB) 6.53 = 12.32) = 0.07; against HOLD alone it would be 0.13.

## Check 4 — metric, filter, bootstrap, bar as pre-registered — PASS

- Primary metric: realised chip points per squad = BB gain (bench points
  minus `rule_autosubs` on realised minutes, bench in forecast order) + FH
  gain (realised FH XI with the highest-forecast captain doubled minus
  realised own best-forecast XI, captain doubled); unplayed chip 0. Code:
  `Replay.bb_gain`, `Replay.fh_gain`, `Replay.realised_xi` — as the prereg.
- Sample: 50 squads, `random.Random(7)`, weighted draws without replacement
  by GW1 `selected`, quotas 2/5/5/3 filled in draw order, club cap 3, cost
  <= 1000 tenths at GW1 `value`, rejection on cost; held fixed GW5-19;
  selling price `fpl_edge.selling_price(GW1 price, price at t)`, bank 1000
  minus the GW1 cost. I re-sampled: 50 squads, reproducible from seed 7,
  all 50 legal (quotas, club cap, 15 distinct, cost 805-1000 tenths). Origins
  GW5-19 for every policy; `bottomup` (`project_reliability` trained on
  rounds < t on week u's pairings) for every comparator alike.
- Comparators: heuristic exactly as the prereg sentence (BB when the bench
  sum, weight 1, at t is >= every remaining week's; else FH when the gap at
  t is >= every remaining week's, t != 19; `heuristic_action` returns at
  most one chip per week); both-early BB GW5, FH GW6.
- Bootstrap: `BT.bootstrap_mean` on the per-squad paired difference, B =
  10,000 (`BT.B`), CI 0.90 percentile (`BT.CI`), seed 20261018 (`BT.SEED`);
  unit = squad, the deviation from the template's gameweek unit stated in
  the prereg with its limitation.
- Bar: `b1["mean"] >= 0 and b1["lo"] > -3.0` (PASS_LOWER = -3.0) — the
  prereg's and BUILD_PLAN Step 7 item 6's.
- No metric promoted, no re-tuning: the headline in the report and CHANGELOG
  is the primary metric with its FAIL; the preview run (before the
  print-only change) and the final run carry the same numbers, and my run
  reproduces them byte for byte, so nothing moved between the first result
  and the committed code. The split by chip added in eb585b5 is the
  prereg's listed secondary ("the split BB / FH"), information only.

Items the chat should see (none moves the primary metric or the bar):
1. **V_BB wording.** Prereg acceptance test 1 says "in the planned BB week
   w = 1.0 for the bench, so V_BB there is the full bench xP", which is
   self-contradictory under its own formula (w = 1.0 gives Σ xP × 0 = 0).
   The code uses V_BB = Σ xP × (1 - w) in every week, the report calls the
   sentence a wording slip, and BUILD_PLAN Step 7 item 1 defines V_BB,t as
   "bench xP minus the autosub contribution that would happen anyway" with
   the 1.0 of item 2 being the bench *weight* in a planned BB week. The
   code follows BUILD_PLAN and the ruling; the realised BB gain is defined
   the same way in the prereg's primary metric. A declared reading made in
   the first code commit, not a tuning on results.
2. **Tie rule** "a tie goes to playing, BB before FH" is not in the prereg;
   it is declared in the code's docstring (d0fc715) and tested. It affects
   only exact ties (within 1e-12) and is the natural choice given chips
   worth 0 after GW19.
3. **Margin definition.** The prereg's secondary "mean margin PLAY vs HOLD"
   is implemented as "chosen action minus the best other action" (live
   output +0.07 rather than +0.13 vs HOLD). Secondary, information only;
   the stricter of the two.
4. **Replay secondary not printed.** The prereg lists "the mean margin PLAY
   vs HOLD and its interval from the residual resampling" among the replay's
   secondary metrics and says the replay's residuals come from graded weeks
   < t; the replay prints no margin interval (the decision uses forecast
   means, as pre-registered). An omission of an information-only output.

## Check 5 — recording path — PASS

The item changes no runner file: md5 of fpl_edge.py, fpl_hist.py,
fpl_nightly.py, fpl_sync.py, fpl_gate.py, fpl_publish.py, fpl_ship.py,
checks.py, fpl_alert.py, test_fpl.py, tools/backtest.py, tools/hist_pit.py
and .github/workflows/nightly.yml identical between the b3ff48a and HEAD
archives (e.g. fpl_edge.py 222f97400abb both). Nightly isolation: importing
fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish and
fpl_hist loads no module from tools/ or analysis/ (empty list); no runner
file has an import of tools/analysis/chips/backtest/hist_pit; no workflow
references tools/ or analysis/. With byte-identical recording code the
projection log cannot move; the log was not regenerated locally (the runner
is the only writer, `--record` is never run here), and the data worktree is
untouched by every run in this verification (status clean, HEAD e8629f0
before and after).

## Check 6 — mutation spot-check — PASS (15 of 18 red)

One-line mutations applied one at a time to a scratch archive of HEAD
(scratchpad mut/, the repository untouched; scratch file restored
byte-identical), `python -m unittest tests.test_S7` after each (baseline 13
OK; scratchpad mutate2.py, output mutate2.txt):
- M1 FH allowed in GW19: RED (toy optimum, tie/last-week tests).
- M2 chips worth 1.0 after GW19: RED (toy optimum, live labels).
- M3 bench weights flat: RED (hand values).
- M4 tie holds the chip: RED (tie test).
- M5 margin against the worst alternative: RED (toy optimum).
- M6 replay trains through round t: RED (forecasts point-in-time).
- M7 replay on end-of-season clubs: RED (club of the origin).
- M8 BB gain ignores the autosubs: RED (hand cases).
- M9 heuristic plays FH in the last week: RED (hand values).
- M10 recorded own row ignored: RED (own week points).
- M11 replay captain not doubled: RED (hand cases).
- M12 sampled squads ignore the budget: RED (squads legal).
- M13 own-model gate dropped: RED (own week points).
- M14 live budget read from `value` instead of `selling_budget`: SURVIVED.
- M15 heuristic fed the weighted V_BB instead of the bench sum: SURVIVED.
- M16 proxy weeks dropped: RED (live labels, CLI).
- M17 sampled squads ignore the club cap: RED (squads legal).
- M18 bootstrap seed changed: SURVIVED.
The three survivors are test gaps, not defects: by inspection
`live()` takes `E.selling_budget(d)` (refusing a missing selling price,
tested), `replay()` feeds `heuristic_action` the unweighted `bench_sum`, and
the seed is `BT.SEED = 20261018` and is printed in the output. Prereg
acceptance test 4's "a test shows the budget is the selling budget, not
value" is met for the Free Hit screen (item N's frozen `free_hit_table`,
which calls `selling_budget` and raises without it) and for `my_squad`
(MissingInput without selling prices), but no test pins the live V_FH's
budget variable (M14).

## Check 7 — secrets — PASS

Every file the item adds or changes (tools/chips.py, tests/test_S7.py,
CHANGELOG.md, worklog/SESSION_STATE_B.md, worklog/cc_2026-10-18_S7.md) and
the outputs examined (tools/out/chips_live.txt, chips_replay_*.txt,
final/*): no API key, no URL with apiKey=, no Authorization header value
(grep for apikey=, api_key, authorization, bearer, sk-..., 32-hex: no
match). chips.py reads only local files; no network code.

## Acceptance tests 1-6 (prereg)

1. Chip values: V_BB = Σ bench xP × (1 - w), w = 0.30/0.10/0.03 outfield in
   forecast order, 0.03 sub keeper (`bench_boost_value`, tested by hand
   values; wording note in check 4 item 1). V_FH = `best_one_week_xi` under
   `selling_budget` minus our `_best_xi` from the 15, labelled "no transfers
   assumed" (amendment 1; the label is in the live output and tested). PASS.
2. Induction over (t, S ⊆ {BB, FH}), V(20, ·) = 0, one chip a week, FH
   never at 19; outputs the V table for every subset, the continuation
   values and PLAY BB / PLAY FH / HOLD for the next week; 1,000 residual
   resamples by position (pools from the S4 harness's graded own weeks,
   counts printed) give the margin interval and the same-action share. Toy
   three-week case: FH17 + BB18 = 9 is the optimum (checked by hand), tested
   with FH never at 19, both worth 0 after 19, no two chips in one week.
   PASS.
3. Bench prep for the planned BB week: best same-position replacement by
   that week's xP within bank + selling price, club cap kept; printed
   (information only). PASS.
4. Free Hit screen: item N's `free_hit_table`/`free_hit_lines` (FH_GAP 8,
   FH_NOT_A 3, selling budget) printed by the live run. PASS (test gap for
   chips' own budget variable noted in check 6).
5. Replay: the 50 squads legal and reproducible (my check and the test); a
   forecast at origin t never reads a row with round >= t (1a zero
   difference; mutation M6 red); one chip per week and FH != 19 for both
   policies (by the policy loop's `elif` and `t != last`, tested); realised
   gains hand-checked (test_realised_gains_hand_cases, M8/M11 red). PASS.
6. `python tools/chips.py` and `--replay` run from this worktree against
   the read-only data copy, writing only under `--out`; nightly isolation
   test present and reproduced; tests in tests/test_S7.py. PASS.

## Other findings (information)

- The pre-registered test is honestly reported as FAIL: calculator -0.18
  per squad against the heuristic, with BB gains identical (+3.20) and the
  whole difference in Free Hit timing (+13.36 vs +13.54); 45/50 BB weeks
  and 47/50 FH weeks coincide. The calculator is not adopted; Part C rule 9
  is for the chat.
- The live recommendation (GW8 PLAY BB by +0.07 xP, 18% resample agreement)
  is information only, as the report says.
- The main session overwrote tools/out/chips_replay_2025-26.txt with the
  final content during this verification (21:18:01); the preview's text
  survives in tools/out/chips_replay_run.log and was compared from there.
  tools/out/ is ignored by git, so this does not touch the write guard.

VERDICT: PASS

Reason: the prereg and its amendment were committed before any code and hold
the ruling verbatim; the replay's forecasts and chip values rebuild with zero
difference from inputs truncated at origins 5, 12 and 19, no training row or
live own row is dated after its deadline, and the realised gains read only
the origin week's outcomes after the decision; my own replay reproduces the
implementer's final output byte for byte and the preview on every number;
the metric, sample, bootstrap (squad unit, B = 10,000, 90%, seed 20261018)
and the bar (mean >= 0 and lower bound > -3) are exactly the prereg's, and
the pre-registered test's FAIL (-0.18 [-1.26, +0.72]) is reported without
tuning or metric promotion; the item changes no runner file, the nightly
imports nothing under tools/, 15 of 18 mutations go red and no secrets
occur. The V_BB wording slip, the undeclared tie rule, the margin-vs-best-
other definition and the missing replay margin interval are declared
readings or information-only omissions for the chat, not moved bars.
