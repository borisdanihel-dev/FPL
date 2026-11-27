# claudemd: CLAUDE.md points to BUILD_PLAN.md Part B (docs only)

This prereg records a ruling for a docs item (`prereg/README.md`: "A ruling-only prereg is acceptable for setup
and docs items if it lists acceptance tests"). It is committed before the edit; written Fri 27 Nov 18:30 UTC, and the commit time governs.

## Ruling, Fri 27 Nov 18:30 UTC (Boris's message verbatim)

Ruling (Fri 27 Nov, 18:30 UTC): yes, update CLAUDE.md. Docs only; commit after tonight's W3fix merge (or Sat morning if that runs late).
Replace the line "Boris clicks only real runs" with:
"Boris clicks real runs and merges unless a rule in BUILD_PLAN.md Part B covers them: advance-approved merges, recovery dispatches (worklog/proposal_recovery_dispatch.md) and, once live, W5's scheduled pre-deadline run. Read Part B before asking him to click."
Keep it to that; no other CLAUDE.md edits.

## The question it answers

After Boris's 16:30 rulings, the session asked whether to add a pointer in CLAUDE.md. CLAUDE.md is the file
every fresh session reads first. Its "Dry runs by push" bullet still said "Boris clicks only real runs". It did
not mention the advance-approval rule or the recovery-dispatch rule (both in BUILD_PLAN.md Part B).

## Acceptance tests

1. The edit replaces exactly one sentence in CLAUDE.md, in the "Dry runs by push" bullet:
   "Boris clicks only real runs." (currently split across lines 166-167). It becomes the ruled text, word for
   word. The new words are wrapped at the file's width, as the old sentence was.
   Check: after collapsing whitespace, the new CLAUDE.md equals the old one with that one sentence replaced.
   `git diff --stat` on the commit shows CLAUDE.md alone.
2. Order: the commit comes after the W3fix merge commit on master (`git merge-base --is-ancestor`).
   - If the merge runs late, the edit goes on Sat 28 morning instead.
   - If W3fix does not merge tonight, it also goes on Sat 28 morning (session reading of "or Sat morning").
3. It is never pushed while that night's nightly is running. It goes either:
   - before 21:00 UTC, with the post-merge worklog post; or
   - after the nightly has committed to `data`.

   The W3fix final verifier then checks that the nightly's checkout differs from the merge commit only in docs.
4. The full suite by discovery passes before and after the edit with the same count. The change is docs only;
   no runner or test file reads CLAUDE.md.
5. A CHANGELOG line and the state file record it. No other CLAUDE.md edits.

No verifier run is planned for this one-sentence docs edit (session reading; Boris may ask for one).

## Boris's answer, Fri 27 Nov (received 18:36 UTC), verbatim

18:30 ruling: plan accepted as written; no verifier for the CLAUDE.md sentence.
