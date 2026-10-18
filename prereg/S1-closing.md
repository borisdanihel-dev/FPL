# S1-closing — the chat's closing ruling on S1

Committed before any change for this item.

- **Item:** S1-closing (follow-up to S1, BUILD_PLAN.md Step 1). Setup and docs:
  the verifier's model, effort and masking; the session's model and effort
  rules; lagging docs; one CLAUDE.md dispatch rule; the secret-scan runner
  pin; local branch clean-up; the first live runs of the new layout.
- **Hypothesis:** n/a. No forecast, feature or evaluation metric.
- **Data and sample filter:** n/a.
- **Comparison:** n/a.
- **Primary metric (one):** n/a.
- **Secondary metrics (information only):** none.
- **Bootstrap:** n/a.
- **Pass threshold:** n/a.
- **Acceptance tests:** the ruling below, points 1–8, verbatim as Boris
  pasted it.

RULING S1 closing:
1. Verifier model: in .claude/agents/backtest-verifier.md and the BUILD_PLAN.md verifier block, identically, set model: fable and add effort: high. Fallback: if Fable is unavailable or Claude Code asks for usage credits, decline the credits and run the verifier with model opus at effort xhigh; the verifier report states which ran.
2. The verifier block also gets: "Mask key-like strings in your report: the first 4 characters, then '...'."
3. CLAUDE.md, Session operating mode: the main session runs Opus 5.5. Effort: xhigh for runner and data steps (1-3), high for model steps, medium for docs-only items. Steps 4, 7, 15, 16 and 17 may run the main session on Fable if Boris switches it; the report names the model used.
4. Docs that lag: BUILD_PLAN.md Step 1.6 says gitleaks runs in secret-scan.yml (no local download); CLAUDE.md line 9 says nightly output is committed to the data branch; secret-scan.yml runs-on: ubuntu-24.04.
5. Accepted: a manual dispatch across a deadline fails the gate and commits nothing. Add to CLAUDE.md: no manual nightly dispatch within 1 hour either side of an FPL deadline.
6. Delete the local branch scratch/s1-wip.
7. Before Step 2 starts: confirm tonight's first scheduled nightly on the new layout (a "nightly 2026-10-18" commit on data, gate green) and the Sunday 04:23 UTC secret-scan run, and report both.
8. Tests before and after (the block/agent identity test stays green); verifier on this item, its first run on Fable; write guard; push.
END RULING

No re-tuning after viewing results.
