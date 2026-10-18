# S1-closing — the chat's closing ruling on S1

**Verdict: PASS** (`worklog/verify_S1-closing.md`). The verifier ran on **Fable 5.1 at effort high**, with no credit prompt and no Opus fallback; this was its first run on Fable. The main session ran on **Opus 5.5**.

**Commits:**
- prereg `44358a0` (the ruling verbatim, every template row filled);
- the change `69b360d`, built in a scratch clone and applied as a blob-identical copy (5/5 files);
- this report, `verify_S1-closing.md`, the changelog and `SESSION_STATE.md` in the next commit.

**Tests:** 308 → 309, green. The block/agent identity test is green before and after. The new test pins `model: fable`, `effort: high` and the masking sentence. It and the `secret-scan.yml` runner assertion were red against the old files. Changing one word in the agent file (fable → opus) turned the identity test and the new test red. The verifier's 7 mutations were all red. The recording path is unchanged: logs regenerated at a frozen time are byte-identical (`69d3...`).

## Ruling by ruling

1. **Verifier model — done.** `.claude/agents/backtest-verifier.md` and the `BUILD_PLAN.md` verifier block are byte-identical (2,897 bytes) and say `model: fable` and `effort: high`. The fallback is in the `CLAUDE.md` work-item protocol under **Verifier model**: if Fable is unavailable or credits are asked for, decline them and run opus at effort xhigh; the verifier report states which ran. This launch passed model fable and effort high explicitly, because the session had loaded the old agent definition.
2. **Masking sentence — done**, in the block and the agent file: "Mask key-like strings in your report: the first 4 characters, then '...'."
3. **Session model and effort — done.** `CLAUDE.md`, Session operating mode, item h, has the ruling's sentence verbatim.
4. **Docs that lag — done.**
   - `BUILD_PLAN.md` Step 1.6 now says gitleaks runs in `secret-scan.yml`, with no local download.
   - `CLAUDE.md` line 9 now says "committed to the `data` branch". The line runs past the file's wrap width; that is cosmetic.
   - `secret-scan.yml` now has `runs-on: ubuntu-24.04`, and `ubuntu-latest` is banned by its test.
5. **Dispatch near a deadline — done.** `CLAUDE.md`, Data branch: "No manual nightly dispatch within 1 hour either side of an FPL deadline", with the reason.
6. **`scratch/s1-wip` deleted.**
   - The re-check I ran just before the delete was broken: Git Bash path conversion mangled the `rev:path` arguments, so its "DIFF" lines were errors, not differences.
   - The delete therefore rested on the earlier evidence: the migration script's 12/12 blob check and the S1 verifier's confirmation.
   - Re-run correctly afterwards (with `MSYS_NO_PATHCONV=1`): `dddcb92` and the deleted head `b738e6d` are 12/12 blob-identical, with the whole non-data tree identical. `b738e6d` is still in the object store.
7. **Live runs before Step 2 — half confirmed.**
   - **Sunday secret scan:** run 39098380500, event `schedule`, **success**. It started at 04:48:38Z, 25 minutes after the `23 4 * * 0` cron; GitHub's scheduler often starts late.
   - **First scheduled nightly on the new layout ("nightly 2026-10-18" on `data`, gate green):** pending. It runs at 21:40 UTC today. I will confirm it before Step 2 starts.
   - The `runs-on: ubuntu-24.04` pin in `secret-scan.yml` gets its first live run from this push.
8. **Tests, verifier, write guard, push — done.** Write guard: `git status` showed only `?? worklog/verify_S1-closing.md`, `git diff` was empty, and the state snapshot of both folders was identical.

## Decisions for the chat

None. The one open point is ruling point 7's nightly, which I report on as soon as it lands.
