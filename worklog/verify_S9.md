# Verifier report — S9 (league variance, relative xP, captain table — offline part)

Verifier: backtest-verifier, run on Fable 5.1 (claude-fable-5-1), effort high,
from `C:\GIT\FPL-b` (branch `lane-b`), 2026-10-18 ~22:50-23:30 UTC. Instructions
read from `.claude/agents/backtest-verifier.md` on disk. Data read-only from
`C:\GIT\FPL-data` at `9da6ff1` (nightly 2026-10-18); worktree clean before and
after. No source file touched; this file is the only write.

Descriptive item: checks 1, 2, 5, 6, 7 and the prereg's acceptance tests 1-6
were run; check 3 (reproduction) and check 4 (definitions) are reported as
information, as the launch asked.

## Prereg order — PASS

`git log`: `98ebddd` 2026-10-19 00:40:12 +0200 adds only `prereg/S9.md`;
first code commit `1dc2263` 00:45:39; test-order fix `2d56fd5` 00:46:17;
report/CHANGELOG `15ecae8` 00:47:08. The prereg carries the RULING Step 9
verbatim (points 1-5, END RULING). `git diff f25fe4d..2d56fd5 --stat`: only
`prereg/S9.md`, `tests/test_S9.py`, `tools/league.py`.

## Check 1 — point-in-time — PASS on the mechanics (but see Finding A)

a. Truncation (decides). Scratch copy of `fpl.sqlite` with every row of
   `event >= 7` deleted from `entry_gw`, `picks`, `player_gw`,
   `automatic_subs`, fixtures `finished = 0` and events `finished =
   data_checked = 0` for `id >= 7` (the calendar keeps its deadlines);
   `L.report(..., today=2026-10-18T22:00Z)` rebuilt: **0 of 50 lines differ**
   from `tools/out/league_2026-10-18.txt`. Settled set = [1..6]. The tool
   therefore reads nothing of GW7 although `entry_gw` and `picks` hold GW7
   rows for all seven managers (3xc rows for us and 4866471 in GW7 exist and
   are not used).
   Per-gameweek rebuild of the captain history (earliest, middle, latest =
   GW4, GW5, GW6; the only settled gameweeks with own rows), each from the
   last `own` snapshot made strictly before its deadline and our picks of
   that gameweek: GW4 top João Pedro FWD 7.20, GW5 Haaland FWD 8.70, GW6
   Tarkowski DEF 6.20 → **1 of 3**, as printed.
b. Timestamp audit (decides). `own` snapshots in the log: GW4
   2026-09-11T21:55:16Z (< deadline 09-12T12:30Z), GW5 09-17T21:55:18Z (<
   09-18T17:30Z), GW6 10-09T21:50:35Z (< 10-10T10:00Z), GW7 10-16T22:02:14Z
   (< 10-17T10:00Z), GW8 10-17T22:04:06Z and 10-18T21:58:06Z (both <
   10-23T17:30Z; the later one is read, through `fpl_edge.forecasts`). Every
   gameweek counted has `data_checked = 1` and 10/10 fixtures `finished = 1`;
   GW7 has `data_checked = 0`, 0/10 finished, and is excluded. Picks used for
   EO and for our 15 are GW6's (the last settled), printed as such.
c. Shift probe: not applicable (no forecast correlation metric).

## Check 2 — clean-checkout test runs — PASS

`git archive` of `f25fe4d` (before) and `2d56fd5` (after) into the
scratchpad, `FPL_DATA_DIR` unset:

| archive | `python test_fpl.py` | `python -m unittest tests.test_S9` | discovery `tests/` |
|---|---|---|---|
| before f25fe4d | Ran 386, OK (skipped=8) | file absent | — |
| after 2d56fd5 | Ran 386, OK (skipped=8) | Ran 5, OK | Ran 149, OK (skipped=2) |

Matches the implementer's counts. In the worktree itself: 5 OK.

## Check 3 — reproduction (information) — numbers match

`python tools/league.py --out <scratch>` from `C:\GIT\FPL-b`: rc 0, one file
`league_2026-10-18.txt`; body identical to the implementer's file line for
line (header line compared separately: same text, same date). Independent
recomputation from the database (my own script, not the tool): pooled
σ_d 18.6250, our σ 14.3306, line 105.4; σ_d,j / gap / P: 21.03/27/0.399,
20.24/56/0.298, 17.77/19/0.428, 15.82/1/0.496, 23.73/40/0.352,
10.03/−50/0.682 — all equal to the printed values. Bootstrap indices follow
`backtest.bootstrap_mean` (lo = sorted[round(0.05·B)], hi = sorted[round(0.95·B)−1]).

## Check 4 — definitions against the prereg (information; deviations noted)

Faithful: pooled σ_d = RMS of σ_d,j (`pooled_sigma_d`); Φ with zero drift,
sign −gap; the line strictly `>` (a gap on the line is "inside"); threat set
= rivals with gap > 0, else P(j above) ≥ 0.05; w_j = 1 − P(above j),
normalised (sum 1.000); multiplier rule starter 1 / captain 2 / 3xc 3 / bench
0 / bench 1 under bboost, cross-checked on every settled gameweek of every
manager (a mismatch raises `MissingInput`); relative xP = (mult − EO) × own;
allowance 0.5 before GW25, 1.0 from GW25; free-variance threshold 0.3; net
= points − transfers_cost; chip-week exclusion when either side's
`active_chip` is set; "next gameweek" = the coming deadline (GW8) for xP, EO
and the captain table while n and the gaps rest on the settled GW6 — stated
in the output header.

Deviations from the prereg text (none changes a printed number):
1. The prereg says "Bootstrap ... for pooled σ_d, each σ_d,j and each σ_i"
   and "Every σ and every P is printed with its interval". The output prints
   intervals for pooled σ_d and each σ_d,j only; σ_j (each σ_i), our σ, the
   no-chip σ_d and every P(above j) are printed without one.
2. The "free variance" flag carries an extra condition not in the prereg or
   the ruling: `cost < 0.3 and EO(option) < EO(top)` (league.py line 363).
   The ruling says only "when the xP difference between two options is
   under 0.3". Not exercised by the GW8 table (no option within 0.3 of
   Haaland); the toy test only covers the lower-EO case.
3. "allowed differential" flags `cost <= allowance` for every option below
   rank 1 without reading the EO; the prereg's "against the threat-set EO"
   is met only by printing the EO column beside it.

## Check 5 — recording path — PASS

Only `prereg/S9.md`, `tests/test_S9.py`, `tools/league.py` changed between
`f25fe4d` and `2d56fd5`; `15ecae8` adds `CHANGELOG.md`, the two worklog
files. No runner file, no workflow file. Nightly isolation, run by me:
importing `fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish`
loads no module under `tools/` (empty list). `C:\GIT\FPL-data` `git status`
clean before and after; `projection_log.csv` sha256 `e466...` and
`fpl.sqlite` sha256 `a4ac...` unchanged by my runs; the tool wrote only under
`--out` (the CLI test also checks the data folder's listing). No recording
code was added, so every model's recorded forecasts are byte-identical by
construction.

## Check 6 — mutation spot-check — PASS

Seven mutations, each alone in the scratch copy of `2d56fd5`, `python -m
unittest tests.test_S9` after each, restored and re-run green at the end:

| mutation | result |
|---|---|
| pooled σ_d as a plain mean of σ_d,j | FAILED (1) |
| the line at `>=` | FAILED (1) |
| Bench Boost bench multiplier 0 | FAILED (1) |
| Φ's sign (+gap) | FAILED (1) |
| hits not subtracted | FAILED (1) |
| picks of unsettled gameweeks loaded | FAILED (2) |
| allowance switch at GW24 | FAILED (1) |

## Check 7 — secrets — PASS

`prereg/S9.md`, `tests/test_S9.py`, `tools/league.py`,
`tools/out/league_2026-10-18.txt`: 0 hits for `apikey=`, `api_key`,
`Authorization:`, `Bearer `, 32-hex strings; no `ODDS_API_KEY` reference.

## Acceptance tests 1-6 (prereg) — all exercised

1. Toy league (3 managers, GW1-5 hand-set points and hits): σ_i, σ_d,j,
   pooled, ρ equal the hand values; Φ(0) = 0.5, Φ(−1) = 0.1587; "inside"
   on the line, "beyond" one point past it; weights sum to 1 — `test_sigmas_
   pooled_rho_phi_and_line`, `test_multipliers_threat_set_and_eo`. Pass.
2. Point-in-time: the toy's unsettled GW6 (99 points, the biggest) is never
   counted; rival picks used are GW5's with GW6 rows present; the
   post-deadline GW6 own snapshot (99.0) is never read — `test_point_in_
   time`; confirmed on the real database in check 1. Pass.
3. EO multipliers incl. TC and BB, the cross-check stops the run on a
   mismatch, EO = Σ w·mult, bench 0 — covered. Pass.
4. Captain table: ranking by own, allowance text, "allowed differential",
   the DEF/GK count 0 of 5 on the toy, 1 of 3 real (rebuilt by me). Pass.
5. Mutations: my seven above all red (the implementer reports 16/16). Pass.
6. CLI writes one `league_<date>.txt` and nothing else; nightly imports
   nothing under `tools/`; tests in `tests/test_S9.py`; `test_fpl.py`
   untouched (not in the diff). Pass.

## Finding A — the settled gameweek scores in `entry_gw` are provisional (decides)

The prereg's data row asserts: "`points` is the gross gameweek score, equal
to Σ pick multiplier × player points — checked on GW5 for every manager."
GW5 is the one settled gameweek where that holds for everyone. On the
database as of `9da6ff1`:

- `entry_gw.fetched_at_utc` is NULL on 42 of 49 rows (every GW1-6 row);
  `automatic_subs` is empty. `fpl_sync.sync_entries` re-fetches a manager's
  row only until `events.finished = 1`, i.e. before `data_checked`, so a row
  can freeze with provisional points (and pre-S2 rows froze earlier still).
- The API's own running totals expose it. A later row's `total_points −
  (points − transfers_cost)` is the final total of the previous gameweek:

  | manager | GW3+GW4 stored | GW3+GW4 final (tot5 − net5 − tot2) | GW6 stored | GW6 final (tot7 − net7 − tot5) | Σ mult×pts GW3/GW4/GW6 |
  |---|---|---|---|---|---|
  | ReturnOfTheDjedi FC | 118 | 138 | 63 | 65 | 45/93/65 |
  | Bruno Dos Tres | 119 | 133 | 71 | 71 | 53/80/71 |
  | Skori FC | 107 | 128 | 59 | 61 | 56/72/61 |
  | 1. FC Kiripolcz (us) | 111 | 123 | 49 | 49 | 59/62/49 |
  | No More Mr. Rice Guy | 90 | 108 | 60 | 61 | 48/60/60 |
  | Revelstoke FC | 147 | 168 | 64 | 66 | 66/102/64 |
  | PyroNeniZlocin | 99 | 128 | 30 | 36 | 68/48/30 |

  GW1, GW2 and GW5 rows are consistent (tot2 = p1 + p2, tot5 = tot7 − net7 −
  GW6 final for every manager). GW3 and GW4 `points` are short by 12-29 for
  all seven managers; GW6 is short for five of the six rivals (ours is
  right). Where the Σ equals the chain the difference is pure staleness;
  where it does not (zero-minute starters) autosubs are the remainder.
  `tools/league.py` reads these rows as the settled scores; its lockdown
  test is on the event, not on the row.
- Materiality, recomputed by me on the final scores (GW3/GW4 split by the
  Σ where no starter had 0 minutes, remainder to the other; PyroNeniZlocin
  has zero-minute starters in both, so both splits): pooled σ_d 18.62 →
  18.49 / 17.94; our σ 14.33 → 13.76; Skori σ_d,j 17.77 → 14.96;
  PyroNeniZlocin σ_d,j 10.03 → 16.06 / 11.74; gaps 27, 56, 19, 1, 40, −50 →
  29, 56, 21, 2, 42, −44; P(above) moves by ≤ 0.02; line 105.4 → 104.6 /
  101.5; the threat set (the five ahead) and every "inside" label are
  unchanged. The item's report (`worklog/cc_2026-10-18_S9.md`) repeats the
  GW5 claim and does not mention provisional rows.

This is a sync (lane A, runner) defect in origin, but the item built its
primary statistic on the assertion, verified it on one gameweek only, and
printed provisional scores as settled ones — against "a missing input is
reported and the work stops; nothing is substituted" and the lockdown rule's
"provisional grades are never recorded".

## VERDICT: FAIL

Every mechanical check passes — prereg before code, truncation at GW7
line-identical, every own row pre-deadline, 386/386 and 5/5 green in clean
archives, my reproduction equal to the printed numbers, seven mutations red,
no runner file or data file touched, no secrets — and the code implements
the pre-registered definitions faithfully (three textual deviations noted in
check 4: missing intervals for σ_i, our σ and every P; an extra EO condition
on the free-variance flag; the allowance flag not reading the EO). The item
fails on its input: the prereg's claim that `entry_gw.points` is the gross
settled score holds only on GW5; on the database as committed the GW3 and
GW4 rows of all seven managers and the GW6 rows of five rivals are
provisional (short by 1-29 points, proven by the API's own running totals
and by Σ multiplier × player points), `fetched_at_utc` is NULL on every
GW1-6 row, and the tool treats them as settled because its lockdown test is
on the event rather than on the row. The printed σ_d (18.62), σ_j, σ_d,j, ρ,
gaps and P are therefore not the settled-league quantities the prereg
defines (recomputed on final scores: σ_d 17.9-18.5, Skori σ_d,j 14.96,
PyroNeniZlocin 11.7-16.1, gaps +1 to +6 off, P within 0.02); the threat set
and the lines do not change. Before the item can pass, the settled rows need
a re-fetch after `data_checked` (lane A's sync) or the tool must derive the
settled score from a consistent source and stop with MISSING INPUT when a
settled gameweek's row predates lockdown; then rerun and re-verify.
