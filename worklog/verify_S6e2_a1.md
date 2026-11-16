# Verifier report: S6e2 amendment 1 (floor_points bounded; re-verification after the WARN)

Verifier: backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high
(`.claude/agents/backtest-verifier.md` read from disk first; it matches the
loaded instructions). Date 2026-10-20.

Scope: branch `s6e2-wip` in the scratch worktree, HEAD `21d1c3a` (the fix),
against `d80644c` / `7f0b148` (the item as verified before, WARN in
`worklog/verify_S6e2.md`, read first). Ruling: master
`3b74e0c:prereg/S6e2.md`, section "Amendment 1" (the night ruling verbatim,
point 6). Inputs read only: `C:/GIT/FPL/historical/{2024-25,2023-24,2026-27}`
and the tracked `tools/odds/E0_2024-25_fetched_2026-10-19.csv`. All my
scratch work lives in `.../scratchpad/verify_s6e2_a1/` (`check.py`,
`check2.py`, `cmp_report.py`, `iso.py`, their logs, the clean exports, the
mutation copy and three regenerated runs). Nothing outside this file was
written in the worktree or in `C:\GIT\FPL`. No key-like string occurs in
anything the item changes; hashes are shown masked (first 4, "...") except
where the task names them in full.

## Prereg before code: PASS

`3b74e0c` (master, 2026-10-20 08:08:34 +0200) adds the "Amendment 1" section
to `prereg/S6e2.md`: the ruling's point 6 verbatim ("Bound floor_points
(stop once the pmf has underflowed, plus a hard cap on j), add tests at mu
120 and 12.765, re-verify, then file the report and CHANGELOG. The FAIL
stands. The keeper-saves line closes here: no S6e3.") plus the fix as
stated (stop at underflow past the mode, k > mu; J_CAP; tests at 120 and
12.765 against a direct sum, the verifier's listed values, the integers
41-399; a test of the cap; the rerun must reproduce the report byte for
byte). The fix commit `21d1c3a` is 08:12:21 +0200, after it, and names it
("prereg master 3b74e0c"). The branch itself carries no `prereg/` (preregs
live on master only, by the ruling's "on master only preregs and
SESSION_STATE_A.md"); `3b74e0c` is not an ancestor of `21d1c3a`, which is
that design, not a gap. `git diff --name-only 7f0b148 21d1c3a`:
`tools/xp_v2_saves2.py` and `tests/test_S6e2.py` only.

## Check 1 (the task's point 1): floor_points terminates and is right: PASS, with a domain note

Termination is now structural: the outer loop is `while j <= j_cap` with
`j += 1` on every pass and the inner loop runs exactly `per` steps per pass,
so the function returns after at most `per x j_cap` pmf steps whatever the
inputs. Measured (`check.py`, against my own 80-digit decimal reference,
the direct sum `sum_k floor(k/3) P(S=k)` carried until the pmf is below
1e-70 past the mode; not the test file's `exact`):

| mu band | n | worst abs error |
|---|---|---|
| 0.001..60 step 0.001 | 60,009 | 5.65e-13 (mu 59.265) |
| integers 61..400 | 341 | 6.54e-13 (mu 96) |
| integers 401..700 | 300 | 4.83e-13 (mu 593) |
| 700..709 | 13 | 3.98e-13 (mu 708) |

plus the listed values: 12.765 (9.2e-14), 13.818 (9.1e-14), 14.592
(9.5e-14), 16.173 (1.9e-13), 120.0 (1.4e-14), 700.0 (1.1e-13); mu <= 0
gives 0.0; 60,968 values in 24 s, every call returned. The main session's
"worst 6.5e-13 at mu 96" is what I measure. The old code (`d80644c`) with
the new test file: `floor_points(120.0)` does not return in 20 s and the
new test hangs (red). Which stop ends the loop, by an instrumented copy
with `j_cap = 10**6`: 1.0, 8.4337 and 700.0 by the tail (j 6, 14, 306);
12.765, 120.0 by the underflow stop (j 109, 250); never the cap. Over the
whole sweep: 59,005 tail stops, 1,935 underflow stops, 0 cap stops; the
smallest mu ended by the underflow stop is 12.765, exactly the smallest
non-terminating value of the WARN. The cap: `floor_points(9.0, j_cap=2)` =
1.8780772840525648 = P(S>=3) + P(S>=6) by the pmf (1.878077284052565).

**Domain note (not a hang; outside the ruling's scope):** `math.exp(-mu)`
is a denormal double from mu 708.4 and 0.0 from mu 745.134, and the pmf is
built by multiplying forward from it. From mu 713.5 the error exceeds
1e-11 (1.1e-11 there; 1.2e-9 at 720; 0.074 at 740; 22.2 at 743; 6.3 at
745) and from 745.2 the loop sees p == 0 from the start, the cdf never
accumulates and the result is the integer floor((mu-1)/3)-type value
(error 0.333 at 746 and 800, 0 at 1000). So the function is right to
~6e-13 for 0 < mu <= 709 and wrong, but finite and returned, above ~713.
The test's largest value is 700, inside the good domain; the implementer
claims nothing above it. 713 expected saves in one fixture is not a value
the model can produce (a match lasts 90 minutes; the run's largest mu is
8.43), the ruling asked for a bound on termination and closes the line
("no S6e3"), and a fix would need a log-space pmf. I record it as a
limitation of the function's contract for reuse, not as a defect of this
item.

## Check 2 (the task's point 2): the real run is unchanged: PASS

`python tools/xp_v2_saves2.py --test --hist C:/GIT/FPL/historical --out
<my folder>` from a clean `git archive` export of `21d1c3a` and, separately,
of `d80644c`. Both reports have 42 lines; against the worktree's
`tools/out/xp_v2_saves2/s6e2_2024-25.txt` (sha256
`f0cbaedfc110639183bff7518b7c74841f757ac4f5b754e353dbcec57706e243`, the one
the task names; the worktree's `run.txt` says commit `21d1c3a`, 0 modified
tracked files, the same sha) every line is equal except line 4, the
re-score note that prints the `--out` path the CLI was given; with that one
path swapped to the worktree's, both of my reports are byte-identical to
it (sha256 `f0cb...`). `rescored_2024-25.csv` sha256 `49f8...` on all three.
Numbers: primary +0.024 per squad per gameweek, 90% CI [-0.016, +0.066]
(n = 34, p = 0.3200), season +0.8; MAE +0.305 [+0.254, +0.355]; differ
0.05; mean E[floor(S/3)] 0.767 against E[S]/3 1.100 over 846; k 17.402
(r 0.371, 37 keepers); bar FAIL. In-process re-run with `floor_points`
wrapped to record every call: 857 calls (846 keeper forecasts, 11 double),
largest mu 8.433745, 0 of 857 at or above 12.765, and every call ended by
the tail stop (underflow 0, cap 0); primary 0.0241176 [-0.0164706,
+0.0664706], p 0.32, pass False. The FAIL stands; no reported number
touches either new stop.

## Check 3 (the task's point 3): the d14 equivalence claim: PASS with a correction

d14 = stop when `p < 1e-300`, without the `k > mu` guard. My replica
against the real function: over mu 0.001..60 step 0.001 and the integers
61..700 the worst difference is 3.2e-14 (743 of 60,641 values differ at
all, by rounding of the last few frozen terms), so the item's tests
(1e-11, largest mu 700) cannot see it and "equivalent in the tested
domain" is right. The stated bound "mu < ~735" is wrong: the first check
happens at k = 3 with p = exp(-mu) mu^3 / 6, which falls below 1e-300 from
mu 708.7, and d14 returns 0.0 from there (d14(710) = 0.0 against the real
236.333, right to 3.7e-13). A test at mu 710 would have killed d14; at mu
700 both agree. The mutant being a correct alternative below 708.7 is the
reason it survives, not a gap in the tests on the stated domain.

## Check 4 (the task's point 4): suite and mutations: PASS

Clean `git archive` of each commit into a fresh folder, `FPL_DATA_DIR`
unset, `python -m unittest discover -p "test*.py"`:
- `d80644c`: Ran 708 tests in 343.2 s, OK (skipped=10);
- `21d1c3a`: Ran 709 tests in 343.4 s, OK (skipped=10).
Exactly the implementer's counts; the one new test is
`ByHand.test_floor_points_always_returns`. Isolation (my own probe in the
clean `21d1c3a` export): importing `fpl_nightly, fpl_ship, fpl_edge,
fpl_sync, fpl_gate, fpl_publish` loads no module under `tools/` or
`analysis/` and none of `xp_v2_saves2`, `xp_v2_saves`, `xp_v2_2425`.

My own 12 mutations of `floor_points` in a scratch export of `21d1c3a`,
`tests/test_S6e2.py`'s `ByHand` after each (300 s timeout), the file
restored and shown unmutated (OK) at the end:

| mutation | result |
|---|---|
| m1 drop the underflow stop | RED (the cap ends it; 1e4 frozen terms miss 1e-11) |
| m2 `while True` (no cap) | RED (j_cap=2 test) |
| m3 `p == 0.0` -> `p < 1e-12` | survived: worst 8.7e-12 from the real on mu <= 708, under 1e-11 |
| m4 J_CAP = 100 | RED |
| m5 drop the `k > mu` guard (`p == 0.0` alone) | survived: identical to the real on mu <= 744 (differs only where exp(-mu) == 0) |
| m6 `return total + surv` at the stop | survived: worst 3.6e-15 from the real |
| m7 `k > mu` -> `k > 3 * mu` | survived: identical to the real on mu <= 708 |
| m8 inner loop `<= per * j` (off by one) | RED (2 tests) |
| m9 drop the tail stop | survived: worst 5.0e-13 from the real |
| m10 the cap returns 0.0 | RED |
| m11 `mu / (k + 1)` | RED (2 tests) |
| m12 `while j < j_cap` | RED |

7 of 12 red; each survivor is a numerically equivalent variant on the
tested domain (measured above), not an undetected bug. Consistent with the
implementer's 13 of 14 and the d14 survivor.

## Check 5 (the task's point 5): files, runner, secrets: PASS

`git diff --name-only 7f0b148 21d1c3a`: `tests/test_S6e2.py`,
`tools/xp_v2_saves2.py` (13 lines changed in the tool: `J_CAP`, the
`j_cap` parameter, the docstring, `while j <= j_cap`, the extra stop, the
trailing `return total`). No runner file; `.github/workflows/nightly.yml`
still runs `fpl_nightly.py`, `fpl_publish.py`, `fpl_alert.py` only.
`grep -Ei 'apikey=|authorization|api_key|bearer |[a-f0-9]{32}'` over both
files at `21d1c3a`: 0 hits.

## Checks not applicable here

The leak checks (1a-c), the harness re-run against the prereg's metric and
the prereg-compliance check were done in `worklog/verify_S6e2.md` on
`d80644c` and are unchanged by this amendment: the only code change is
inside `floor_points`, which my check 2 shows returns the same value on
every one of the 857 calls the run makes (same report bytes, same primary
to 0.0). Recording path: offline tool, no `FPL_DATA_DIR`, no
`projection_log.csv`; nothing on the recording path changed.

## Write guard

`git status --short` in the worktree before writing this file: empty
(`tools/out/` is gitignored). After: only `worklog/verify_S6e2_a1.md`,
untracked.

## VERDICT: PASS

The amendment does what the ruling (master `3b74e0c`, committed before the
fix `21d1c3a`) asks and nothing else: `floor_points` now stops at the tail,
once the pmf has underflowed past the mode, or at J_CAP, so it returns for
every input by construction; my sweep of 60,968 values (0.001..60 by
0.001, the integers to 1000, the WARN's values) all return and agree with
an 80-digit reference to 6.5e-13 for every mu up to 709, the WARN's
smallest hanging value 12.765 is exactly the first one the new stop ends,
the old code still hangs on the new test, the cap test is right; the real
run is byte-identical to the pre-fix report (sha256 `f0cb...`, up to the
`--out` path the CLI prints), its largest mu 8.43 reaches neither new stop
on any of 857 calls, and the FAIL (+0.024 [-0.016, +0.066]) stands; the
suite is 708 -> 709 OK (10 skipped) on clean exports; 7 of my 12 mutations
go red and the 5 survivors are measured equivalents; d14's survival is
explained, though its stated bound is ~708.7, not ~735; only the two files
changed, no runner file, no secret. One limitation is recorded for reuse,
not held against the item: above mu ~713 `exp(-mu)` is denormal or zero
and the value is wrong (finite, returned), a regime 85 times the run's
largest mu and outside what the ruling scoped.
