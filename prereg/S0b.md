# S0b — rulings on the S0 report

Committed before any change for this item.

- **Item:** S0b (BUILD_PLAN.md Step 0, follow-up). Boris's rulings on
  `worklog/cc_2026-10-17_S0.md`. Protocol, docs and local config only; no
  model, forecast, feature or evaluation code changes.
- **Hypothesis:** n/a (protocol and docs).
- **Data and sample filter:** the 2025/26 per-gameweek table
  (`historical/2025-26`) for the smoke test's toy evaluation only, on a scratch
  branch; nothing on `master` reads data differently.
- **Comparison:** n/a.
- **Primary metric (one):** n/a — a descriptive and data-pipeline item.
- **Secondary metrics (information only):** none.
- **Bootstrap:** n/a.
- **Pass threshold:** n/a.
- **Acceptance tests (descriptive or data-pipeline items, instead of a metric):**
  1. Verifier check 1 is replaced by the ruling's text (1a truncation test,
     1b timestamp audit, both deciding; 1c shift probe, warning only) in
     `.claude/agents/backtest-verifier.md` and in the "Verifier agent" block
     of `BUILD_PLAN.md`. The two stay byte-identical, and nothing else in the
     agent text changes. `CHANGELOG.md` logs the amendment and cites the
     2026-09-14 ceiling entry (ceiling 0.15; fixture term 0.02-0.06).
  2. The planted-leak smoke test is rerun with the native `backtest-verifier`
     agent on a scratch branch with its own prereg (`prereg/SMOKE2.md`), never
     pushed. The verdict is FAIL with check 1a FAIL and check 1b FAIL. The
     report is saved as `worklog/verify_SMOKE2.md`, and the scratch branch is
     deleted; `git ls-remote --heads origin` lists only `master`.
  3. `CLAUDE.md`: the line "Standard library only. No pip, no third-party
     dependencies." is gone; the work-item protocol's runner-stdlib / `tools/`
     rule is the only stdlib rule left.
  4. `FPL_PLAN.md`: line 1 is "Historical (written after GW3). Superseded by
     BUILD_PLAN.md. fpl_run.bat is retired; the nightly runs on GitHub
     Actions." The diff against the previous commit is that one added line.
  5. Push setup: this clone's local `.git/config` has `remote.origin.url` =
     `git@github.com:borisdanihel-dev/FPL.git` and `core.sshCommand` = `ssh -i
     C:/Users/Boris/.ssh/fpl_deploy_ed25519 -o IdentitiesOnly=yes`; the global
     config is unchanged; `git ls-remote origin` and the final push work
     through it. No key material enters the repository.
  6. `BUILD_PLAN.md` Step 2 holds the new item "Bench audit respects
     automatic substitutions" with its test; the verifier step is renumbered
     after it.
  7. Verifier write guard: the rule is in the work-item protocol of
     `CLAUDE.md` and in Part B of `BUILD_PLAN.md`. It is applied to this item's
     own verifier runs (SMOKE2 and S0b): after each, `git status` and
     `git diff` show no change outside `worklog/verify_<item>.md`, and the
     report records what they showed.
  8. `python test_fpl.py` before and after: same count, green. No `.py` file
     changes on `master`, so the recording path cannot move.

No re-tuning after viewing results.
