# Verifier report — S6 (Step 6, M1: xP rebuild and blend, `xp_v2`)

Verifier: Claude Fable 5.1 (claude-fable-5-1), native `backtest-verifier`
agent; the agent file was read from disk first (`.claude/agents/backtest-verifier.md`,
no difference from the loaded instructions). Run on 2026-10-18/19 in
`C:\GIT\FPL-b` (branch `lane-b`, HEAD `e762093`), data read-only from
`C:\GIT\FPL-data` (`e8629f0`, nightly 2026-10-18). Only this file was written
in the repo; everything else went to the session scratchpad.

## Prereg order

`prereg/S6.md` committed in `f9ca3d0` (2026-10-18 15:40:27 +0200), amendment 1
in `94fbc36` (15:43:22); RULING S5 result (bottomup_lambda adopted as the
bottomup half) `4abc716` (23:09:12); first S6 code commit `8bb22a8`
(23:53:17; adds `tools/xp_v2.py`, `tests/test_S6.py`, the report draft). The
prereg and its amendment precede the code. The ruling (RULING S6, points 1-2)
and Amendment 1 (points 3, 5a-c) are present verbatim in the prereg. PASS.

## Check 1 — point-in-time leak check

Evaluated gameweeks: `weeks_with_sources()` = [5, 6] (the only settled
gameweeks with `own`, `xg`, `bottomup`, `minutes` recorded; GW7 has
`data_checked = 0` and 10/10 fixtures unfinished). Earliest = GW5, latest =
GW6, no middle gameweek exists.

### 1a Truncation test — PASS

For each of GW5 and GW6 I built a scratch data copy holding only inputs
available before that gameweek's deadline, then rebuilt `Season.week(g)` with
the committed code and compared every player's `p_start`, `e_xg`, `e_bl`,
`p_sub`, `bl`, `blend`, `xg_only`, `bl_only`, plus `E[pts|sub]` per position:

- exports: only those with `generated` < deadline (GW5: 2 of 29 kept; GW6: 18);
- `projection_log.csv`: only rows with `made_at` < deadline (GW5: 1573 of
  5756; GW6: 2574);
- odds CSV: only rows dated up to the gameweek's last kickoff (GW5: 50 rows;
  GW6: 60);
- `fpl.sqlite`: every `player_gw` row with `event >= g` overwritten
  (`total_points = 99, minutes = 1, starts = 0, goals = 9, expected_goals = 9`;
  2002 rows for GW5, 1335 for GW6), every fixture score with `event >= g`
  set to 9-9, `picks` for events > g deleted.

Result: same export chosen, same player set, max |diff| = 0.00e+00 for every
field and for `E[pts|sub]`, both gameweeks. A second variant altering only
`event > g` (so the target's realised points survive) reproduced the per-
gameweek metrics (`rho`, `rho_own`, `dec`, `dec_own`, `n`) for all three
candidates with max |diff| = 0.00e+00: the metrics use nothing after the
target gameweek. Worst case over all runs 0.00e+00 <= 1e-9.

### 1b Timestamp audit — PASS

| input | GW5 (deadline 2026-09-18T17:30Z) | GW6 (deadline 2026-10-10T10:00Z) |
|---|---|---|
| log `own` / `xg` / `bottomup` / `minutes` snapshot used (S2 rule, re-derived from the raw CSV) | 2026-09-17T21:55:18-19Z, 278/256/256/256 rows, all < deadline; one snapshot per source | 2026-10-09T21:50:35-36Z, 263/246/246/246 rows, all < deadline; one snapshot per source |
| export for `bottomup_lambda` and `chance_next_round` | `fpl_export_gw4_2026-09-17.json`, generated 2026-09-17T21:55:18Z < deadline; later same-gameweek exports: none | `fpl_export_gw5_2026-10-09.json`, generated 2026-10-09T21:50:35Z < deadline; 17 later gw5 exports exist, none used |
| `player_gw` rows for P(sub), E[pts|sub] | `event < 5` by the SQL; max event 4, last kickoff 2026-09-14T19:00Z < deadline | `event < 6`; max event 5, last kickoff 2026-09-20T15:30Z < deadline |
| fallback fit results | 40 fixtures, max kickoff 2026-09-14T19:00Z < deadline | 50 fixtures, max kickoff 2026-09-20T15:30Z < deadline |
| odds (football-data pre-closing) | 10/10 GW5 fixtures matched, match dates 2026-09-18..20 | 10/10 GW6 fixtures matched, match dates 2026-10-10..12 |
| `picks` (our 15) | 15 rows for GW5 | 15 rows for GW6 |

The odds rows are dated on match day, after the deadline, but they are the
pre-closing odds of the gameweek's own fixtures and carry no result; this is
the limitation the prereg states for the 2026/27 bottomup_lambda rebuild
(S5) and I treat it as declared, not as a leak. No `minutes` row exceeds 1.0
(the tool's cap never engaged). P(start) from the export equals the recorded
`minutes` row to 0.000 on both gameweeks (so E_bl / P(start) divides the
rebuilt lambda by the same P(start) that produced it).

### 1c Shift probe — no WARN

Starters (P(start) >= 0.8, own recorded) with 60+ minutes in g and g+1,
pooled over GW5->6 (103 players) and GW6->7 (100 players; GW7 is not settled,
its `player_gw` rows are partial, information only):

| source | n | unshifted | shifted (g+1) | diff |
|---|---|---|---|---|
| blend (xp_v2) | 203 | +0.046 | +0.022 | +0.024 |
| bl_only | 203 | +0.088 | +0.061 | +0.028 |
| xg_only | 203 | +0.022 | -0.008 | +0.030 |
| own | 203 | +0.128 | +0.042 | +0.087 |

Unshifted values are all below 0.25 and every unshifted-minus-shifted is
below 0.10. No WARN (and 1a/1b are clean regardless).

## Check 2 — clean-checkout test run — PASS

`git archive` of `19b6bbc` (before) and `HEAD` (after) into scratch folders,
`FPL_DATA_DIR=C:\GIT\FPL-data`:

- before: `python test_fpl.py` -> Ran 386 tests, OK (skipped=1)
- after: `python test_fpl.py` -> Ran 386 tests, OK (skipped=1)
- after: `python -m unittest tests.test_S6` -> Ran 8 tests, OK

Note: the report and CHANGELOG say "9 tests" for `tests/test_S6.py`; the file
has 8 (`Components` 2, `SeasonTests` 4, `CLI` 2). They also say "8 skipped" for
`test_fpl.py`; with the data folder available 1 is skipped. Both are counting
errors in the write-up, not in the code.

## Check 3 — re-run of the pre-registered evaluation — PASS

Run by me with `--out` in the scratchpad:
`python tools/xp_v2.py --develop --cut 6`, `--validate --cut 6`, `--forecast`
(all rc=0). `diff` against `tools/out/xp_v2_develop_cut6.txt`,
`xp_v2_validate_cut6.txt`, `xp_v2_forecast.txt`: IDENTICAL, byte for byte,
so every number matches within 1e-6. Development (in-sample, GW5-6): own rho
+0.203 / +0.170; blend +0.131 / +0.056, mean +0.0937, rho - own -0.0927,
XI+C - own +0.00; xg_only mean +0.0750; bl_only mean +0.1066 (best single,
frozen); s_d 0.0296 -> G = 13.6 at delta 0.02; E[pts|sub] GK 0.00 (n=0), DEF
1.12 / 1.08, MID 1.21 / 1.25, FWD 1.56 / 1.42. Validation: 0 settled
gameweeks after the cut -> INCONCLUSIVE, nothing adopted. Forecast GW8 from
`fpl_export_gw7_2026-10-18.json.gz`, bottomup_lambda on the fallback (no odds
snapshot), 264 players, information only.

## Check 4 — metric, filter, bootstrap, threshold against the prereg — PASS (one wording note)

- Primary metric: mean per-gameweek tie-corrected Spearman (`E._spearman`,
  average ranks for ties) among predicted starters, `xp_v2` - `own`, on the
  validation set (`validate()`: `d_rho = rho - rho_own` per gameweek > cut).
  Matches.
- Sample filter: starters = recorded `minutes` row of the same gameweek
  >= `BT.STARTER_P` = 0.8, never realised minutes; paired on the same players
  (`own` present, `xg`, `minutes` and the rebuilt bottomup_lambda present).
  Matches. Decision metric: XI + captain from our 15 in `picks`, S4
  `decision_points`. Matches.
- Bootstrap: `BT.bootstrap_mean`, B = 10000, CI = 0.90 percentile, unit =
  gameweek, paired differences, seed `BT.SEED` = 20261018. Matches.
- Pass rule: CI lower bound > 0 on the chosen candidate AND
  `len(weeks) >= G` with G = `power_gameweeks(s_d, 0.02)` from the S4
  calculator and s_d from the development set; otherwise "inconclusive" and
  nothing adopted. Matches ruling 2 and amendment 5c.
- Candidates: equal-weight blend (primary) and the best single model chosen
  on the development set by mean starters Spearman, frozen (amendment 5b; no
  fitted weights exist in the code). No penalty term anywhere in the code
  (amendment 5a). The cut is a CLI argument; without it the tool refuses
  (rc 2). The cut GW6 is mechanically the prereg's rule (last settled
  gameweek on the day of `8bb22a8`; GW7 unsettled), so no discretion was
  involved.
- Wording note, not a moved bar: the replacement rule in `validate()` is
  `single.rho - blend.rho >= 0.02 and single.dec > blend.dec`, while the
  prereg reads "wins ... by >= 0.02 on the primary metric AND on the decision
  metric". With integer decision points over n validation gameweeks any
  positive mean difference is >= 1/n, so the two readings coincide for
  n < 50 (both checkpoints, and a season); the comparison selects between two
  xp_v2 candidates and does not touch the pass threshold against `own`. No
  validation result exists, so nothing was changed after seeing results. It
  should still be aligned with the prereg text before the GW10 checkpoint.
- No metric promoted and no re-tuning after results: the development numbers
  are labelled in-sample, the validation set is empty, the report's reading
  draws no conclusion.
- One statement in the report I did not confirm: "GW4's export has no
  `player_id`" as the reason GW4 is outside the development set. In the log
  GW4 has only `own` and `xg` snapshots (no `minutes`, no `bottomup`), so GW4
  is excluded by the prereg's own rule (GW5 onward) whatever the export
  holds; the development set GW5-6 is correct either way.

## Check 5 — recording path — PASS

- `git diff 19b6bbc..HEAD --stat`: only `CHANGELOG.md`, `tests/test_S6.py`,
  `tools/xp_v2.py`, `worklog/SESSION_STATE_B.md`, `worklog/cc_2026-10-18_S6.md`.
  No runner file, no workflow file changed.
- Nightly isolation, run by me: importing `fpl_nightly, fpl_ship, fpl_edge,
  fpl_sync, fpl_gate, fpl_publish` in a subprocess loads no module under
  `tools/` (empty list).
- `C:\GIT\FPL-data\projection_log.csv` sha256 `7d230c3e...` before and after
  my three tool runs; `git -C C:\GIT\FPL-data status` clean before and after.
  The tool writes only under `--out`; `test_log_is_never_written` covers it.
  No model's recorded forecasts can have moved: the item added no recording
  code and the log is byte-identical.

## Check 6 — mutation spot-check — PASS

Nine mutations of my own on the clean scratch checkout's `tools/xp_v2.py`,
each run against `tests.test_S6` (8 tests), file restored byte-identical
afterwards (`filecmp` True):

| mutation | result |
|---|---|
| M1 minutes model averaged in as points (`(p_start*(e_xg+e_bl)+p_start)/3`) | RED (2 failures) |
| M2 sub inputs read the target gameweek (`event <= ?`) | RED |
| M3 export chosen without the deadline (newest of gameweek g-1) | RED |
| M4 lockdown dropped (`if False:`) | RED |
| M5 best single chosen as the worst (`<`) | RED |
| M6 validation includes the cut (`g >= cut`) | RED |
| M7 starters filter dropped in `metrics` | RED |
| M8 conditional xg not divided by P(start) | RED |
| M9 `--cut` requirement removed | RED (error) |

The implementer's 13 listed mutations overlap these; I did not re-run theirs.

## Check 7 — secrets — PASS

`grep -i` over every file changed in `19b6bbc..HEAD` for `apikey=`, `api_key=`,
`authorization`, `bearer `, and 32-hex-character runs: no match.
`tools/xp_v2.py` and `tests/test_S6.py` contain no key, no URL and no header.
No key-like string appears in this report.

## Acceptance tests 1-6 as amended

1. Conditional forecasts: `test_conditional_forecasts_hand_case` (hand case
   for both models; P(start) = 0 gives P(sub) x E[pts|sub]); on the real
   data `e_xg * p_start` and `e_bl * p_start` reproduce the recorded rows
   (`test_week_is_point_in_time` on the toy; M8 red). PASS.
2. Minutes model never averaged in as points: M1 red. PASS.
3. Best single model chosen on the development set only, frozen for
   validation; the cut a frozen argument: `test_develop_validate_and_the_frozen_choice`,
   M5, M6, M9 red. PASS.
4. Point-in-time: check 1b on both evaluated gameweeks (only two exist);
   lockdown refusal `test_lockdown_and_missing_source_refuse`, M4 red. PASS.
5. Dropped by amendment 1 point 5a; no penalty code exists. n/a.
6. CLI `--develop --cut`, `--validate --cut`, `--forecast` under `--out`,
   never writes the log, nightly isolation: `test_cli_cut_required_and_isolation`,
   `test_log_is_never_written`, my own isolation run. PASS.

## Notes for the main session (no verdict impact)

- Fix the test counts in the report and CHANGELOG (8 tests, not 9; skipped
  count depends on `FPL_DATA_DIR`).
- Align the decision-metric half of the replacement rule with the prereg
  wording (>= 0.02) before the GW10 checkpoint, or record in the prereg why
  "any positive win" is the intended reading; today they cannot differ.
- The GW4 "no player_id" sentence should say what was actually observed.

VERDICT: PASS

Reason: the prereg and its amendment were committed hours before the first
code commit and hold the rulings verbatim; the item's development output,
validation output and forecast reproduce byte-for-byte from my own runs; the
truncation rebuild of both evaluated gameweeks from pre-deadline-only data
reproduces every xp_v2 component and metric to 0.00e+00 and every input row
used predates its deadline (the odds limitation is the one the prereg
declares); the shift probe raises no WARN; the metric, starters filter,
bootstrap (B = 10,000, 90%, seed 20261018), candidates and the inconclusive
rule are exactly the prereg's as amended, with the validation set empty by
construction so no result was seen and nothing could be tuned on it; no
runner file changed, the nightly imports nothing under `tools/`, and the
projection log is byte-identical; nine of nine mutations go red; no secrets.
The only findings are write-up counting errors and a wording gap in the
candidate-replacement rule that cannot change an outcome before 50 validation
gameweeks.
