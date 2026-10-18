# Verifier report — S9 (league variance, relative xP, captain table — offline part)

## First run (2026-10-18, FAIL) — summary

The first verification (Fable 5.1, `2d56fd5`) passed every mechanical check
(prereg before code; truncation at GW7 line-identical; every `own` snapshot
pre-deadline; 386/386 and 5/5 green in clean archives; my reproduction equal
to the printed numbers; seven mutations red; no runner or data file touched;
no secrets) and failed the item on its input: `entry_gw.points` was
provisional on settled gameweeks (GW3 and GW4 for all seven managers, GW6 for
five rivals; short by 1-29 points, proven by the API's running totals and by
Σ multiplier × player points; `fetched_at_utc` NULL on every GW1-6 row;
the sync stops re-fetching at `finished = 1`, before `data_checked`). It also
noted three textual deviations from the prereg: no intervals for σ_i, our σ,
the no-chip σ_d and P(above j); an extra EO condition on the "free variance"
flag; the "allowed differential" flag not reading the EO. RULING S9 decisions
(verbatim in `prereg/S9.md`, commit `1f0d881`) answered all four: the sync fix
is lane A's S2b; meanwhile the tool derives each settled score from the totals
chain, prints provisional rows, excludes and counts uncorrectable ones; an
interval for every sigma and every P; the free-variance EO condition kept as
the ruling's reading; the allowed-differential flag reads the threat-set EO.

## This run (re-verification after the ruling)

Verifier: backtest-verifier, run on Fable 5.1 (claude-fable-5-1), effort high,
from `C:\GIT\FPL-b` (branch `lane-b`), 2026-10-18 ~23:30 UTC to 2026-10-19
~00:10 UTC. Instructions read from `.claude/agents/backtest-verifier.md` on
disk. Data read-only from `C:\GIT\FPL-data` at `9da6ff1` (= `origin/data`
after fetch; the same snapshot as the first run; `fpl.sqlite` sha256
`a4ac...`, `projection_log.csv` sha256 `e466...` before and after). Item
range `94cbe3b..5aceef2`; clean archives of both in the scratchpad. No source
file touched; this file is the only write. While I ran, lane B committed S8,
S12 and S13 work on top (`51520ef..b456909`, `tools/planner.py`,
`tests/test_S8.py`, preregs, worklog); `git diff 5aceef2 HEAD` on
`tools/league.py`, `tests/test_S9.py`, `tools/backtest.py`,
`tools/console_utf8.py`, `fpl_edge.py` and `prereg/S9.md` is empty, so the
worktree runs below are of the item's code.

Descriptive item (no pass/fail metric): checks 1, 2, 5, 6, 7 decide; checks 3
and 4 are reported as the launch asked.

## Prereg order — PASS

`git log`: `98ebddd` (2026-10-19 00:40) added `prereg/S9.md` before the first
S9 code `1dc2263` (00:45). The ruling on the result: `1f0d881` (01:07:57,
only `prereg/S9.md`, "RULING S9 decisions" verbatim, END RULING) precedes the
fix code `629da70` (01:13:12) and `5aceef2` (01:15:40). `git diff
94cbe3b..5aceef2 --stat`: `prereg/S8.md`, `S9.md`, `S11.md`, `S12.md`,
`S13.md`, `tests/test_S9.py`, `tools/league.py`, `worklog/SESSION_STATE_B.md`.

## Check 1 — point-in-time, the chain — PASS

a. Chain reconstruction (my own script, `tools/league.py` not imported). For
   every entry and settled g: final_total[g] = row(g+1).total_points −
   (row(g+1).points − transfers_cost); final_total[g−1] = row(g).total −
   row(g).net (0 before GW1); net[g] = difference. Result: 18 provisional
   rows, 0 excluded, the same rows and differences as the output (GW3 all
   seven, +6..+21; GW4 six — Bruno, Djedi, Revelstoke, Rice Guy, Kiripolcz,
   PyroNeniZlocin, +2..+11; GW6 five, +1..+6; the launch's "GW4 five" is a
   slip in the message, the output and my count are six). The first run's
   method (GW3+GW4 = tot5 − net5 − tot2; GW6 = tot7 − net7 − tot5) equals the
   chain for every manager.
   API totals: the `standings` table (the league endpoint, fetched separately
   from `entry_gw`) holds `event_total` and `total` per event; for events 3-6
   all 28 rows equal the chain's net and final total exactly. The seven
   "event 2" standings rows do not match the chain's GW2 (they carry a GW3
   snapshot under the event-2 label, e.g. ReturnOfTheDjedi 45/217, and
   PyroNeniZlocin's is itself provisional, 68/176 vs 71/179); the tool does
   not read `standings`, so this is information for lane A's sync, not an S9
   input. Σ multiplier × `player_gw.total_points` with autosubs rebuilt from
   minutes (bench order, formation validity, GK-for-GK, vice for a 0-minute
   captain, no subs under Bench Boost): equals the chain on 42 of 42 rows
   GW1-6 (the raw Σ differs on exactly the seven rows with a 0-minute
   starter: ours GW4 62→64, Rice Guy GW6 60→61, Revelstoke GW6 64→66,
   PyroNeniZlocin GW3 68→71, GW4 48→57, GW6 30→36).
a'. Truncation (decides). Scratch copy of `fpl.sqlite` with every row of
   `event >= 7` deleted from `entry_gw`, `picks`, `player_gw`,
   `automatic_subs`, `standings`; fixtures `finished = started = 0` and
   events `finished = data_checked = 0` for `id >= 7`. Tool rerun
   (`today = 2026-10-18T22:00Z`): settled [1..6]; GW6 excluded for all seven
   managers ("7 rows the chain cannot correct, excluded", seven "excluded:
   <manager> GW6 (no later row to correct it)" lines) — the expected GW6
   effect; 13 provisional rows = the 18 minus the five GW6 ones, same
   differences; GW1-5 chain nets and final totals identical to the full run
   for every manager (checked programmatically). The truncated run's
   statistics (settled through GW5, n = 33: pooled σ_d 19.36 [11.55, 21.51],
   our σ 13.39 [1.87, 17.02], no-chip 17.87 [6.29, 19.22], line 111.2, and
   the six rival rows) are identical, line for line, to my reconstruction on
   the truncated database. Side note: in this degenerate state the header
   reads "settled through GW5 ... (GW6, GW7 played, not yet settled)" because
   `last` is the last gameweek with our score, while GW6 is settled-but-
   excluded; cosmetic.
   Captain history (GW4/GW5/GW6 from each gameweek's last pre-deadline `own`
   snapshot and our picks of that gameweek, first run: 1 of 3): the diff
   leaves `captain_history`, `our_xi`, the `own` reader and the picks reader
   untouched, and the line prints the same "1 of 3".
b. Timestamp audit (decides). The chain's GW6 reads the GW7 row, fetched
   2026-10-18T21:57:54..21:58:06Z (`fetched_at_utc`), before the run; GW6's
   `data_checked = 1` is already in the first data-branch commit holding a
   GW7 row (`e84bee6`, 2026-10-17 22:04Z), and the GW6 final total implied by
   the GW7 row is constant across all four GW7 fetches (`e84bee6`, `4af6abe`,
   `e8629f0`, `9da6ff1`) for all seven managers (406, 433, 398, 377, 379,
   419, 333). GW1-6 rows carry `fetched_at_utc` NULL (pre-S2), as before.
   `own` snapshots as in the first run: GW4 09-11T21:55Z, GW5 09-17T21:55Z,
   GW6 10-09T21:50Z, GW7 10-16T22:02Z, GW8 10-18T21:58Z, each before its
   deadline. GW7 (`data_checked = 0`, 0/10 finished) is excluded from
   everything but the chain's next-row read.
c. Shift probe: not applicable (no forecast correlation metric).

## Check 2 — clean-archive test runs — PASS

`git archive` of `94cbe3b` (before) and `5aceef2` (after), `FPL_DATA_DIR`
unset:

| archive | `python test_fpl.py` | `python -m unittest tests.test_S9` | discovery `tests/` |
|---|---|---|---|
| before 94cbe3b | Ran 386, OK (skipped=8) | Ran 5, OK | Ran 149, OK (skipped=2) |
| after 5aceef2 | Ran 386, OK (skipped=8) | Ran 8, OK | Ran 152, OK (skipped=2) |

Matches the implementer (8 OK; 386 OK, 8 skipped).

## Check 3 — reproduction — numbers match (max abs diff 0.0)

`python tools/league.py --out <scratch>` from `C:\GIT\FPL-b`: rc 0, one file
`league_2026-10-18.txt` (UTC date at run time), byte-identical to
`tools/out/league_2026-10-18.txt` including the header;
`L.report(today=2026-10-18T22:00Z)` likewise identical. Independent
recomputation (my script, own chain, own statistics, own bootstrap with the
pre-registered RNG protocol): pooled σ_d 18.03 [10.45, 20.31], our σ 13.76
[3.01, 18.35], no-chip 17.87 [5.62, 19.72], line 102.0; σ_j / σ_d,j / ρ /
gap / P [90%]: 26.94/21.74/0.60/29/0.388 [0.312, 0.400];
22.76/20.35/0.47/56/0.291 [0.172, 0.313]; 22.74/14.96/0.77/21/0.418 [0.361,
0.427]; 24.63/13.95/0.89/2/0.492 [0.487, 0.493]; 21.74/22.08/0.29/42/0.340
[0.239, 0.357]; 13.41/12.53/0.57/−44/0.667 [0.649, 0.772]; all "inside";
threat set the five ahead. Raw (unrounded) comparison of 5 global and 66
per-rival values against `variance_table`: max abs diff 0.0 (< 1e-6).

## Check 4 — definitions against the prereg and the ruling

- Ruling point 2 (chain): `totals_chain` as defined; "WARN provisional:
  <manager> GW<g> stored <a>, chain <b> (<±diff>)" per row; "<k> rows the
  chain cannot correct, excluded" plus one "excluded:" line each; `load`
  returns `provisional` and `excluded`. Faithful.
- Ruling point 3 (1): intervals printed for pooled σ_d, our σ, the no-chip
  σ_d, every σ_j, every σ_d,j and every P(above j); P's interval from the
  resampled pooled σ_d (it equals Φ(−gap/(σ√n)) at the σ_d interval's ends,
  checked). Faithful for the primary table. Information: the drift-version
  P(above) lines ("information only") are printed without an interval; the
  first run's deviation list named P(above j), which the ruling answered —
  the chat may want to say whether "every P" also covers the drift version.
  Also the P bootstrap drops the resamples where the pooled σ_d is 0 (all six
  draws the same gameweek, ~1 in 7,776), which the σ_d bootstrap keeps;
  the effect on a percentile index at B = 10,000 is nil here.
- Ruling point 3 (2): "free variance" = cost < 0.3 AND a lower EO than the
  top (line 428) — the ruling's reading, kept. Faithful.
- Ruling point 3 (3): "allowed differential" = cost <= allowance AND a lower
  threat-set EO than the top (line 426); the header says so. Faithful.
- Unchanged and still faithful: pooled σ_d = RMS of σ_d,j; Φ sign; the line
  strictly `>`; threat set rule; w_j = 1 − P(above j) normalised (sum 1.000);
  multiplier rule cross-checked on every settled gameweek; net = points −
  cost; chip-week exclusion; allowance 0.5 before GW25 / 1.0 from GW25; the
  bootstrap B = 10,000, seed 20261018, 90% percentile.
- No metric promoted or re-tuned after the results: the primary (pooled
  σ_d), the sample (settled gameweeks, now read through the chain by ruling)
  and the bootstrap settings are those of the prereg; the item has no bar.

## Check 5 — recording path — PASS

Only `prereg/*.md`, `tests/test_S9.py`, `tools/league.py` and
`worklog/SESSION_STATE_B.md` changed between `94cbe3b` and `5aceef2`; `git
diff` on `.github`, `fpl_nightly.py`, `fpl_ship.py`, `fpl_edge.py`,
`fpl_sync.py`, `fpl_gate.py`, `fpl_publish.py`, `test_fpl.py` is empty.
Nightly isolation, run by me: importing `fpl_nightly, fpl_ship, fpl_edge,
fpl_sync, fpl_gate, fpl_publish` loads no module under `tools/` or
`analysis/` (empty list). `C:\GIT\FPL-data` `git status` clean before and
after; `fpl.sqlite` `a4ac...` and `projection_log.csv` `e466...` unchanged;
the tool wrote only under `--out` (`/tools/out/` is gitignored). No recording
code exists in the item, so every model's recorded forecasts are byte-
identical by construction.

## Check 6 — mutation spot-check — PASS (12 of 12 red)

Each alone in the scratch copy of `5aceef2`, `python -m unittest
tests.test_S9` after each, restored and re-run green (8 OK) at the end:

| mutation | result |
|---|---|
| chain: stored net instead of the chain | FAILED (1) |
| chain: provisional rows not reported | FAILED (1) |
| chain: uncorrectable row kept (stored total used) | FAILED (1) |
| chain: next row's total not net of its own points | FAILED (2) |
| chain: previous total from the previous row's stored total | FAILED (1) |
| chain: only a settled next row corrects | FAILED (5) |
| P interval collapsed | FAILED (1) |
| σ_j interval taken from the diffs | FAILED (1) |
| our σ interval collapsed | FAILED (1) |
| allowed differential ignores the EO | FAILED (1) |
| free variance without the EO condition | FAILED (1) |
| lockdown dropped: every gameweek with a later row counted | FAILED (4) |

The last one is the mutation the toy's GW7 row (`5aceef2`) makes visible.

## Check 7 — secrets — PASS

Every file in `git diff --name-only 94cbe3b..5aceef2` plus
`tools/out/league_2026-10-18.txt`: 0 hits for `apikey=`, `api_key`,
`Authorization:`, `Bearer `, `ODDS_API_KEY`, 32-hex strings.

## Acceptance tests 1-6 (prereg) — all exercised

1. Toy league hand values (σ_i, σ_d,j, pooled, ρ, Φ(0), Φ(−1), the line on
   and past it, weights sum to 1) — green, unchanged. 2. Point-in-time: the
   toy's unsettled GW6 (and now GW7) never counted though later rows exist;
   rival picks GW5's; post-deadline own snapshot never read — green; real
   database in check 1. 3. Multipliers incl. TC/BB, mismatch stops the run,
   EO = Σ w·mult — green. 4. Captain table: ranking, both flags on the
   one-rival-ahead toys, DEF/GK count — green. 5. Mutations: 12 red above
   (implementer 21 of 21). 6. CLI writes one file, nothing else; nightly
   imports nothing under `tools/`; tests in `tests/test_S9.py`; `test_fpl.py`
   untouched.

## VERDICT: PASS

The ruling was committed verbatim before the fix code; the settled scores
now come from the totals chain, which I rebuilt independently and found equal
on every row to the first run's method, to the league `standings` totals for
events 3-6, and to Σ multiplier × player points with autosubs reconstructed
from minutes; the 18 provisional rows are printed with their differences and
the uncorrectable case is excluded and counted (seven GW6 rows when GW7 is
removed, with GW1-5 unchanged and the truncated statistics identical to my
reconstruction); the GW7 row the chain reads postdates GW6's lockdown and
implies the same GW6 totals across all four of its fetches; every sigma and
every P(above j) carries a bootstrap interval, both flags are as ruled, and
my raw numbers match the implementer's at 0.0; 386/386 and 8/8 green in clean
archives, twelve mutations red, no runner or data file touched, no secrets.
Two information points for the chat, neither moving a number: the drift-
version P (information only) prints no interval, and the `standings` table's
"event 2" rows are mislabelled GW3 snapshots (a lane A sync matter).
