# verify_S6d — the live "xp_v2 as tested" forecast in the bundle

Verifier: the `backtest-verifier` agent on model Fable 5.1 (effort high), read from
`.claude/agents/backtest-verifier.md` on disk in the worktree. Worktree
`C:\Users\Boris\AppData\Local\Temp\claude\C--GIT-FPL\442a647f-7693-4ced-b840-0df7f5bfd943\scratchpad\s6d`,
branch `s6d-wip`, HEAD `a1595e4`; base `s6c-wip` at `28d0578`. Data: `C:\GIT\FPL-data` at `bd724ca`
(nightly 2026-10-19 06:13 UTC), read only; `git status` there was clean before and after every run.
Everything that writes (test suites, mutations, re-runs, the recording demonstration) ran in
scratch copies under the session scratchpad (`git archive` of `28d0578` and `a1595e4`), never in the
worktree, `C:\GIT\FPL` or the data worktree. This file is the only file written inside the worktree.
No git pull, fetch, commit, push or checkout was run anywhere.

## Prereg and ruling

- `prereg/S6d.md` was committed in `9fa7ab1` (2026-10-19 15:12:14 +0200); the first code commit is
  `4d2d1c7` (15:23:01 +0200). `git log -- prereg/S6d.md` shows only `9fa7ab1`: never edited after.
- The ruling text is verbatim in the prereg: Boris's queue line 2 and the whole
  `RULING S6b acceptance + lanes merge` block (points 1-4, `END RULING`).
- The item is descriptive (acceptance tests, no pass/fail metric): checks 1, 2, 5, 6, 7 and the
  acceptance tests apply; 3 and 4 are run as far as they have content.
- The diff `28d0578..a1595e4` touches exactly: `CHANGELOG.md`, `prereg/S6d.md`, `tests/test_S6c.py`
  (one assertion for the captain name), `tests/test_S6d.py`, `tools/gw_pass.py`,
  `tools/xp_v2_live.py`, `tools/xp_v2_replay.py`, `worklog/cc_2026-10-19_S6c.md`,
  `worklog/verify_S6c.md` (the last three via the S6c merge `c98487b`). `git diff --stat` excluding
  `tools/ tests/ prereg/ worklog/ CHANGELOG.md` is empty: no runner file changed.

## The as-tested equivalence (acceptance test 1, real 2025/26) — PASS

Own script (scratch, `a1595e4` code, the worktree's gitignored `historical/`;
`2024-25/merged_gw.csv` sha256 `5bbb...`, `2025-26/merged_gw.csv` `0d09...`): `XR.Replay(2025-26,
2024-25)` with S5's 2025/26 football-data book, `Replay.xp_v2(t)` against `XL.core()` fed the
replay's own inputs (the same `reliability_inputs`, `by_round`, S11 rows/totals/Prior, club fixtures,
`lambda_team`, `lam_opp`):

| t | players replay | players core | same key set | max abs diff xp_v2 | max abs diff, every detail field | `got == want` |
|---|---|---|---|---|---|---|
| 5 | 342 | 342 | yes | 0.0 | 0.0 | True |
| 21 | 319 | 319 | yes | 0.0 | 0.0 | True |
| 38 | 334 | 334 | yes | 0.0 | 0.0 | True |

Matches the claim (342 / 319 / 334, max |diff| 0). The toy version (`AsTested.test_core_equals_s6b_replay`)
passes in the suite.

## Check 1: point-in-time — PASS (a and b); c not applicable

Own script on the real data (`a1595e4` code, scratch), GW8 live and the retro GW5-7:

**1a truncation (decides).** For each target g the forecast was rebuilt from the pre-deadline
export with every row of event >= g removed, the odds book taken before the deadline, the fallback
fitted only on finished results kicked off before the deadline, S11's 2025/26 priors and the
code-keyed names, and compared to the item's function (`XL.live` / `XL.retro`):

| target | export used | generated | deadline | rows of event >= g in the export | truncated rebuild == item | players |
|---|---|---|---|---|---|---|
| GW8 (live) | `fpl_export_gw7_2026-10-19.json.gz` | 2026-10-19 06:13:10 UTC | 2026-10-23 17:30 UTC | 0 | True, max diff 0.0 | 285 |
| GW5 (retro) | `fpl_export_gw4_2026-09-17.json` | 2026-09-17 21:55:18 UTC | 2026-09-18 17:30 UTC | 0 | True | 278 |
| GW6 (retro) | `fpl_export_gw5_2026-10-09.json` | 2026-10-09 21:50:35 UTC | 2026-10-10 10:00 UTC | 0 | True | 263 |
| GW7 (retro) | `fpl_export_gw6_2026-10-16.json` | 2026-10-16 22:02:14 UTC | 2026-10-17 10:00 UTC | 0 | True | 279 |

Sensitivity: feeding the previous export (`gw7_2026-10-18`) instead changes 261 of 285 GW8 values,
so the function does read the export it names. The implementer's `xp_v2_live_gw8.txt` top-25 values
re-matched 25 of 25 against my live numbers; the whole file is byte-identical (below).

**1b timestamp audit (decides).** GW8: export generated 06:13 UTC on 19 Oct < deadline; snapshot
`odds_2026-10-19T0613Z.json.gz` taken 06:13 UTC on 19 Oct < deadline (`newest_snapshot` only
accepts `taken < deadline`); the fallback used 60 finished results, latest kickoff 2026-10-12
19:00 UTC, none at or after the deadline; 0 GW8 fixtures finished; the export's rows reach event 7
only (GW7's 273 appearance rows, from matches kicked off 17-18 Oct, i.e. before the GW8 deadline).
Retro: each gameweek's export is the newest of gameweek g-1 generated before g's deadline
(`pre_deadline_export` requires both `gen < deadline` and `gameweek == g-1`); 27 / 11 / 4 later
exports were excluded for GW5 / 6 / 7; no export of gameweek g-1 exists after the deadline; the
fallback's results reach event g-1 at most and none kicked off at or after the deadline. Priors are
2025/26 (last season); `elements_positions.csv` (19 Oct bootstrap) supplies only `code`, which is
immutable; `fpl.sqlite` supplies first + second names. The GW5-7 column's λ come from
`tools/odds/E0_2026-27_fetched_2026-10-18.csv`: pre-closing match-day prices, fetched after the
fact, exactly as the prereg and the print state (information only, not a decision input); GW7's
fixtures are not in that file, so the GW7 column is all fallback (and GW7 is not graded anyway).

**1c shift probe.** Not applicable: the item produces no correlation metric on points.

Also verified on the real data for the prereg's stated assumptions: no player has more than one
club across all 29 dated exports since 2026-09-11; every event 1-8 has 10 fixtures and no club
twice (no double gameweek); the export's `player_gw_recent` holds every appearance row (minutes > 0)
of events 1-7, equal per event to `player_gw` in `fpl.sqlite` (310/312/307/307/302/315/273), so
S11's shares and team totals on the export's rows are the season's, not a window.

## Check 2: clean-checkout test run — PASS

`python -m unittest discover -p "test*.py"` on `git archive` copies, `FPL_DATA_DIR` unset:
- `28d0578` (before): Ran 660 tests, OK (skipped=10).
- `a1595e4` (after): Ran 667 tests, OK (skipped=10).
The 7 new tests are `tests/test_S6d.py`. The skips are the data-dependent ones ("no real export in
this folder", "no real fpl.sqlite", "no real projection_log.csv in FPL_DATA_DIR"); the
implementer's 9 reflects one of them finding the data. The suite's nightly-isolation probe passed, and
I re-ran it directly: importing `fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish`
loads no module under `tools/` (`[]`); `.github/workflows/nightly.yml` mentions no `tools/` or
`analysis/` path.

## Check 3: re-run through the harness — PASS (no metric; outputs reproduced)

From the `a1595e4` archive against `C:\GIT\FPL-data` (`--hist` / `--prior` / `--rules` pointed at the
worktree's `historical/`), outputs to scratch:
- `tools/xp_v2_live.py --data C:\GIT\FPL-data`: `xp_v2_live_gw8.txt` byte-identical to the
  implementer's (285 players; 10 of 10 fixtures from odds; 481 of 668 players keyed by code; Saka
  6.00, Gabriel 5.86, Calafiori 5.83, Haaland 5.68 at the top).
- `tools/gw_pass.py --data C:\GIT\FPL-data`: `gw8_pass.txt` identical except line 1's generated
  clock (13:41 vs 13:26 UTC). Section 5: own captain Haaland 4.44, xp_v2 as tested captain Saka
  6.00, 10 slots differ, "DEFAULT = xp_v2 as tested"; the keeper line prints Verbruggen 2.70,
  Kelleher 3.51.
- `tools/xp_v2_replay.py --s6c --data C:\GIT\FPL-data`: `s6c_2025-26.txt` identical except line
  2's output path; `rescored_2025-26.csv` sha256 `55fa...` identical. S6c's numbers unchanged:
  xp_v2 - own_rebuilt +0.515 [+0.213, +0.816], GW8 SWITCH STANDS. The GW5-7 print: GW5 own 54 /
  xp_v2 54 (captain Haaland both); GW6 own 59 (captain Tarkowski) / xp_v2 61 (captain Saka), +2;
  GW7 not locked down.
- `tools/gw_pass.py` with an empty `--hist` on the real data: section 5 prints
  `missing input: ...\2025-26\merged_gw.csv is missing (S11's priors, last season)` and
  `own picks GW8 (RULING S6b acceptance point 1: ...); nothing is substituted`, no captain line; the
  keeper line prints `xp_v2   n/a`.

## Check 4: the prereg's definitions are what the code does — PASS (no metric to promote)

Read `tools/xp_v2_live.py` against the pinned definitions: `core()` is `Replay.xp_v2` line for line
(same `sub_inputs_2526`, `ict_percentile`, `defcon_rates`, `player_sums`/`share_of`, the
`m / (m + k)` shrinkage, minutes per start with the positional fallback then 90, `p_clean_sheet x
CS_VALUE`, `forecast_lambda / P(start)`, `xp_candidates["blend"]`), plus the three live hooks the
prereg names: `gate` (status `a`), `chance` on P(sub) (`min(1, P(sub) x chance/100)`, `XV.chance_scale`),
and an `ict` built from the export's season influence + creativity + threat among minutes > 0.
`forecast()`: training slice `canonical_through(canonical_from_export(d), d["gameweek"])`,
`reliability_inputs(..., gws_played=d["gameweek"])`; S11 rows one unit per player-gameweek with the
export's club; `fixture_lambdas(book, model, kickoff, home, away)` per target fixture from
`fixtures_next6`; the fallback `fit_fallback` on finished results with kickoff before the deadline;
`MissingInput` when a player has no name or the target has no fixtures. `PRIOR_SEASON = "2025-26"`;
`prior_names` keys by `code` (`elements_positions.csv` id -> code, 2025/26 `players_raw.csv` code ->
id, `merged_gw.csv` id -> name), else first + second name; then S11's `Prior.prior` rule. The GW5-7
column uses `pre_deadline_export` and `odds_path("2026-27")`; the bundle's section 5 prints the
default line, own beside it, `missing input` + `own picks GW<target>` on any failure, and the S6
forecast on recorded xg rows is gone from the bundle. The prereg's one open point (2025/26 priors per
BUILD_PLAN Step 11, against lane B's handover naming 2024/25) is recorded there as a decision for
the chat; the code follows the prereg. Nothing was tuned: the item has no metric, and the S6c numbers
are unchanged.

## Check 5: recording path — PASS

No runner file changed (diff above). Demonstrated anyway: scratch copies of `fpl_export_gw7.json`,
`fpl.sqlite` and `projection_log.csv` from the data worktree; `fpl_edge.py --record --source <src>`
for own, xg, minutes, bottomup, fpl_ep with the `28d0578` code and with the `a1595e4` code. Both
recorded 275 / 260 / 260 / 260 forecasts for GW8 (fpl_ep skipped: no ep_next), both logs 7479 rows,
identical in every column but `made_at`. The real `projection_log.csv` (7501 rows) and the data
worktree were not touched (`git status` clean).

## Check 6: mutation spot-check — PASS (10 of 12 red; 1 equivalent; 1 test gap noted)

Scratch copy of `a1595e4`, one line changed each, `python -m unittest tests.test_S6d tests.test_S6c`
(control: OK):

| mutation | result |
|---|---|
| chance factor dropped from P(sub) | FAILED (1) |
| status gate always True | FAILED (1) |
| prior key ignores `code` (name only) | FAILED (1) |
| shrinkage k doubled | FAILED (1) |
| export generated after the deadline accepted | FAILED (1) |
| snapshot after the deadline accepted | FAILED (1) |
| `own picks GW<target>` line removed (gw_pass) | FAILED (1) |
| keeper line's xp_v2 dropped | FAILED (1) |
| training slice not truncated to the export's gameweek | FAILED (1) |
| captain printed by id, not name (replay print) | FAILED (1) |
| D3: `export_rows` keeps rows of event > gameweek | OK — equivalent, as claimed: `core()` reads rounds < t only and the slice is truncated separately |
| 45-minute gate removed from `core()` | OK — the hermetic tests do not catch it: the toy has 0 of 30 players under 45 minutes in the last four |

The last one is a test gap, not an implementation fault: with the gate removed the prereg's real
2025/26 acceptance check fails loudly (741 / 795 / 841 players against the replay's 342 / 319 /
334), so the gate is verified by acceptance test 1 on the real data, and `tests/test_S6d.py`'s
`for pid ... if p["mins_last4"] < 45: assertNotIn` is vacuous on the toy. Worth a toy player under
45 minutes in a later item; it does not change the verdict.

## Check 7: secrets — PASS

The nine changed files grepped for `apiKey=`, `Authorization`, `api_key`, `ODDS_API_KEY` and any
32+ character alphanumeric run: only the CHANGELOG's and verify_S6c's sentences saying the key is
never written, and commit hashes. The three output files under `tools/out/` (gitignored) hold no
key-like string. No URL with a key, no header value, anywhere.

## Acceptance tests (the prereg's list)

(1) as tested: toy at two origins (suite) and real 2025/26 at GW5/21/38 (above, exact) — PASS.
(2) point-in-time on the toy folder: a post-deadline export refused, a post-deadline snapshot not
used, target-gameweek rows do not move the forecast — in the suite and confirmed by mutations 5-6
and 9 — PASS. (3) prior key by code, then name, then S11's means — suite, mutation 3 — PASS.
(4) gate and the sub term with chance — suite, mutations 1-2 — PASS. (5) the bundle section on a toy
folder and on the real data with the priors absent — PASS. (6) the GW5-7 print with the live column
— suite and the real S6c re-run — PASS. (7) `run.txt` (provenance records at `a1595e4`, 0 modified
tracked files), nightly isolation, `test_fpl.py` untouched (not in the diff) — PASS.

## VERDICT: PASS

The prereg (`9fa7ab1`) precedes every code commit and carries the ruling verbatim; the live core is
exactly S6b's `Replay.xp_v2` on the real 2025/26 at GW5, 21 and 38 (max |diff| 0, same player sets);
every live and retro input is dated before its deadline and a truncated rebuild from pre-deadline
inputs reproduces the item's numbers to the last bit for GW8 and GW5-7; the suite goes 660 -> 667 OK
on clean archives; my re-runs of the three real commands reproduce the implementer's outputs
byte-for-byte apart from a clock and a path line, with S6c's +0.515 [+0.213, +0.816] unchanged and
the real "own picks GW8" path shown; no runner file changed and recording is identical before and
after; 10 of 12 mutations go red with one verified equivalent and one gap (the 45-minute gate,
caught only by the real-data check); no secrets. Noted for the chat, not a defect: the 2025/26 prior
season (per BUILD_PLAN Step 11) against lane B's handover; the GW7 retro column is all fallback
because the football-data file fetched on 18 Oct has no GW7 rows.
