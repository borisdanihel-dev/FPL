# Verifier report — S11 (BUILD_PLAN.md Step 11, item H2, share-of-team allocation with 2024/25 priors, offline) — re-verification

Verifier: Claude Fable 5.1 (backtest-verifier agent; `.claude/agents/backtest-verifier.md`
read from disk first — it matched the loaded instructions, so the file governs
without difference). Date: 2026-10-19. Worktree `C:\GIT\FPL-b`, branch
`lane-b`, HEAD `3029867` (the re-verification was requested after `8e36a84`;
`3029867` on top is the bundle item and touches no S11 file). The tree was
clean at my start and at my end (`git status --short` empty both times).
Nothing outside this file was written in the tree; `C:\GIT\FPL`,
`C:\GIT\FPL-landing` and `C:\GIT\FPL-data` were neither read nor written; no
`fpl_sync.py`, `--record`, `fpl_nightly.py` or `tools/planner.py --replay` was
run; `tools/out/planner/` and any `worklog/verify_bundle.md` were left alone.
All scratch work (two clean clones, the mutation clone, the regenerated
output) lives in the session scratchpad.

Note for the write guard: at my final `git status` (09:03) `tools/gw_pass.py`
showed as modified (+113 lines: `CONFIRMED_FT`, `NAMED_SWAP`, `norm_name`,
`find_player`, `why_illegal` — "bundle amendment 1"), file time 09:02:44,
i.e. written during my run by the lane's concurrent bundle work. It was clean
at my start and at my mid-run status check; I did not create or touch it, and
it is not an S11 file. No other tracked file is modified.

## Summary of the first run (HEAD `7f72141`, verdict FAIL)

Prereg order PASS (ruling verbatim in `7111240`, template rows in `47eed25`,
code in `5c258e3`, no prereg edit after). Check 1 PASS: truncation test at
origins 5, 21, 38 (round ≥ t rows deleted or overwritten with 99) reproduced
every share, prior, Z, minutes share and forecast to 0.0; timestamp audit over
every origin 5–38 found 0 late rows; shift probe N/A (goals/assists, not
points; pooled rho(g) 0.307 v rho(g+1) 0.284, information). Check 2 PASS:
clean clones 559 before (`a01c862`) → 571 after (`7f72141`), OK. Check 3 PASS:
independent recomputation matched k (xg 3.184597, xa 3.494331), every
per-origin row to 0.0, per-gameweek Spearman to 3e-16, and the result —
goals +0.0060599 Holm 95% [+0.0021040, +0.0103964], assists +0.0043020 Holm
90% [+0.0003819, +0.0082903], both lower bounds > 0 — to 1e-10. Check 4 PASS
(every constant and definition as pinned; nothing promoted or re-tuned).
Check 5 PASS (offline; no runner file changed; the nightly imports nothing
under `tools/`). Check 7 PASS. **Check 6 FAIL**: of 9 mutations 8 went red,
but m8 — `ms = p["p_start"] * m_start / 90.0` → `ms = m_start / 90.0` —
survived, because every sampled toy starter had P(start) exactly 1.0, so the
acceptance test for the minutes share did not discriminate the P(start)
factor. Information for the chat (not a verdict factor): the assists result
is fragile under other bootstrap seeds (95% lower bound −0.0001 to −0.0003;
its Holm level is 90% only because goals takes the 95% slot); goals is stable
under every seed tried.

## What changed since the first run

- `8e36a84` (2026-10-19 08:56:07 +0200): `tests/test_S11.py` +9 lines in
  `Season.test_sample_forecast_and_comparator` — a fresh toy `Season` with
  `hist["c"]["players"][pid0]["chance_next_round"] = 90`, asserting the
  harness's P(start) = 0.9, `ms` = 0.9 × 90/90 and `xg` = 0.9 × the unflagged
  forecast; plus the first verifier report. Nothing else.
- `3029867`: `tools/gw_pass.py`, `tests/test_bundle.py`, `prereg/bundle.md`
  (the bundle item). `git diff --stat 7f72141 HEAD` lists exactly these five
  files; `prereg/S11.md` is unchanged since `47eed25` (diff 0 lines).
- `tools/shares.py`: blob `d80589a...` at `7f72141`, at HEAD and on disk
  (`git hash-object`) — byte-identical. `tools/backtest.py`,
  `tools/odds_lambda.py`, `tools/provenance.py`, `fpl_edge.py`, `test_fpl.py`:
  `git diff 7f72141 HEAD` is empty (0 lines).
- Output `tools/out/shares/shares_test_2025-26.txt`: sha256 `5eba2c41...`,
  unchanged; `run.txt` still names commit `7f72141...`, 0 modified tracked
  files, 7 s.
- Inputs: the three 2024/25 files re-hashed by me now — `merged_gw.csv`
  5,125,595 bytes `5bbbcba6...`, `fixtures.csv` 751,413 bytes `ce696e18...`,
  `teams.csv` 1,717 bytes `d10a6db8...` — exactly the prereg's records.

## Check 1 — point-in-time — PASS (stands from the first run)

`tools/shares.py` is byte-identical to the file the first run tested, the
harness functions it pins are unchanged, and the 2024/25 inputs hash to the
prereg's values, so the truncation test (1a, origins 5, 21, 38: 0.0
difference), the timestamp audit (1b, every origin 5–38: 0 violations) and
the shift probe (1c, N/A) stand without re-running.

## Check 2 — clean-checkout suite — PASS

`git clone` of the worktree into the scratchpad, checked out at `3029867`
(HEAD), `FPL_DATA_DIR` unset, `python -m unittest discover -p "test*.py" -s .
-t .`: **Ran 576 tests in 325.3 s, OK (skipped=10), rc 0**. Before the item
(first run, `a01c862`): 559; after the item's code (`7f72141`): 571; now 576 =
571 + the 5 bundle tests. `tests.test_S11` alone in the clean clone, verbose:
8 of 8 ok (Hand ×4, Season ×3, CLI), 1.4 s; hermetic — the new assertions
use the existing temporary toy folders (`self.tmp`, `self.tmp24`), no
network, no environment, no `C:\GIT\FPL-data`.

## Check 3 — the pre-registered evaluation — PASS (stands; output regenerated)

Not recomputed independently again: the code, the harness and the inputs are
unchanged (above). As a direct confirmation I re-ran `python tools/shares.py
--test --out <scratch>` from `C:\GIT\FPL-b` at HEAD: the output is
byte-identical to the committed `tools/out/shares/shares_test_2025-26.txt`
(`cmp` silent, both sha256 `5eba2c41...`); the scratch `run.txt` names commit
`3029867...`, 0 modified tracked files. The numbers of the first run (goals
+0.0060599, Holm 95% lower bound +0.0021040; assists +0.0043020, Holm 90%
lower bound +0.0003819) therefore stand to the byte.

## Check 4 — metric, filter, bootstrap, threshold — PASS (stands)

`prereg/S11.md` unchanged since `47eed25` (before the code commit `5c258e3`);
`tools/shares.py` unchanged since `7f72141`; the only S11 change after the
result was seen is a test assertion (`8e36a84`) that pins the pre-registered
minutes-share definition (P(start) × m_start/90) more tightly — no metric
promoted, nothing re-tuned, no number moved.

## Check 5 — recording path — PASS (stands)

`git diff --name-only 5c258e3~1 HEAD` still lists only `tests/*`, `tools/*`,
`prereg/*` and `worklog/*`; no runner file changed. The first run's import
check (the nightly modules load nothing from `tools/` or `analysis/`) stands,
and `tests/test_S3.py` (nightly isolation) and `tests/test_S11.py::CLI`
passed in the 576-test clean suite above. `projection_log.csv` was not
regenerated (the runner is the only writer).

## Check 6 — mutation spot-check — PASS (3 of 3 red, the survivor included)

Scratch clone of `3029867` (`scratchpad/mut11b`; `tools/shares.py` blob
`d80589a...`, `tests/test_S11.py` blob `461ae02...` = the fixed test). One
line changed per run with `sed`, `python -m unittest tests.test_S11`, the
file restored from a saved copy after each (blob `d80589a...` verified, `git
status` clean, suite green again: Ran 8, OK). The tree's `tools/shares.py`
was never edited.

| mutation | line | result |
|---|---|---|
| baseline, unmutated | — | Ran 8 tests, OK |
| **m8 minutes share ignores P(start)** — `ms = p["p_start"] * m_start / 90.0` → `ms = m_start / 90.0` (the first run's survivor) | 241 | **RED**: `FAIL: test_sample_forecast_and_comparator (tests.test_S11.Season.test_sample_forecast_and_comparator)` — `AssertionError: 1.0 != 0.9 within 7 places (0.09999999999999998 difference)`; Ran 8, FAILED (failures=1) |
| m1 training through t — `range(1, t)` → `range(1, t + 1)` | 219 | RED: `test_point_in_time`, `test_sample_forecast_and_comparator`; FAILED (failures=2) |
| m3 k = n(1 − r) instead of n(1 − r)/r | 187 | RED: `test_credibility_k_by_hand`; FAILED (failures=1) |
| restored | — | blob `d80589a...`, Ran 8 tests, OK |

The gap is closed: the flagged starter (chance 90 → P(start) 0.9, still in the
sample at ≥ 0.8) makes the P(start) factor visible, and the assertion fails on
exactly that factor (1.0 where 0.9 is required), then on the scaled forecast.

## Check 7 — secrets — PASS

`grep -i` over `tools/shares.py`, `tests/test_S11.py` (the only S11 file
changed since the first run) and this report's predecessor for `apiKey=`,
`api_key`, `Authorization:`, `Bearer `, `ODDS_API_KEY` and 32+-hex strings:
only the first report's own list of the patterns searched. No `urllib`,
`requests`, `http` or `environ` in `tests/test_S11.py` or `tools/shares.py`.
No key, no keyed URL, no header value.

## VERDICT: PASS

The only failed check of the first run is closed: in a scratch clone at HEAD
the surviving mutation (dropping the P(start) factor from the expected
minutes share) now turns `tests.test_S11.Season.test_sample_forecast_and_comparator`
red with `1.0 != 0.9`, the restored file is green, and two earlier mutations
(training through t; k without the /r) are red again. Nothing that produced
the measured result moved: `tools/shares.py` is the same blob as at `7f72141`,
the harness files and the 2024/25 inputs are unchanged and re-hashed to the
prereg's records, the output regenerates byte-identically at HEAD (sha256
`5eba2c41...`), `prereg/S11.md` is unchanged since before the code, and the
clean suite at HEAD is 576 tests OK (559 before the item, 571 after its code,
+5 bundle tests). The first run's point-in-time, re-run, prereg-conformance,
recording-path and secrets findings stand on that evidence. The result as
recorded — goals adoptable (Holm 95% lower bound +0.0021), assists adoptable
on the pre-registered seed (Holm 90% lower bound +0.0004) but fragile under
other seeds, as noted — is for Boris to accept in chat; adoption is not a
verifier decision.
