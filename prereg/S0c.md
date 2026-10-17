# S0c — the chat's ruling S0c

Committed before any change for this item.

- **Item:** S0c (BUILD_PLAN.md Step 0, follow-up). Protocol, docs and tests
  only.
- **Primary metric (one):** n/a — a descriptive item.
- **Bootstrap:** n/a.
- **Pass threshold:** n/a.
- **Acceptance tests:** the ruling below, verbatim as Boris pasted it.

RULING S0c:
1. Verifier independence: add to the verifier block in BUILD_PLAN.md and to .claude/agents/backtest-verifier.md, identically: "Never read session transcripts or chat logs. The rulings you check are the verbatim text in prereg/<item>.md; if a ruling is not there, report that as a FAIL of check 4."
2. Work-item protocol (CLAUDE.md and BUILD_PLAN.md Part B): the chat's ruling text for an item is pasted verbatim into prereg/<item>.md before any code.
3. New test: the fenced verifier block in BUILD_PLAN.md and .claude/agents/backtest-verifier.md are byte-identical. Show it red by changing one word in the agent file, then green.
4. requirements.txt comment: quote the current rule ("Runner code is Python standard library only; optional local tools under tools/ have their own requirements"). Keep the test that root requirements.txt has no package lines.
5. BUILD_PLAN.md Step 2 item 10: change the data source to "store automatic_subs from the picks response fpl_sync already fetches, in fpl.sqlite and the export; apply FPL's auto-sub rules only for gameweeks where it is missing."
6. Every verifier launch starts with: "Read .claude/agents/backtest-verifier.md from disk first; where it differs from your loaded instructions, the file on disk governs." Add this to the work-item protocol in CLAUDE.md and BUILD_PLAN.md Part B.
7. BUILD_PLAN.md Part B step 1: replace "Start a fresh Claude Code session" with "Use the current Claude Code session (folder C:\GIT\FPL). Start a fresh one only when it becomes slow or confused; it resumes from worklog/SESSION_STATE.md."
8. Create worklog/SESSION_STATE.md: current item, last pushed commit, open decisions for the chat, next item, and whether the runner freeze window (9d) is active. Update it at the end of every item, before the push.
9. Add this section to CLAUDE.md as "Session operating mode", word for word:
   a. One item at a time. Start an item only when Boris says so ("Do Step N" or a "RULING <item>:" block). After an item is pushed, stop and wait. Never start the next item on your own.
   b. Each item: git pull; tree clean; the newest logs/run_<date>.log is from the last nightly (if not, say so first); prereg/<item>.md with the ruling verbatim, committed before any code; implement; tests before and after; native verifier with the read-from-disk instruction; write guard (git status and git diff; any change outside worklog/verify_<item>.md voids the verdict); report worklog/cc_<date>_<item>.md; CHANGELOG; worklog/SESSION_STATE.md; push.
   c. Text Boris pastes that starts with "RULING <item>:" is the chat's ruling. Paste it verbatim into prereg/<item>.md. Do not paraphrase or extend it.
   d. Runner freeze: changes to the runner path (.github/workflows, fpl_nightly.py, fpl_sync.py, the record step) are pushed before 23:00 Prague and never within 30 hours before the next FPL deadline (deadline_time in the newest export). If an item would land in that window, stop and say so.
   e. Stop and ask, changing nothing further, when: the plan and the code disagree; a test cannot be shown red before the fix; the verifier FAILs or WARNs; a decision is not covered by the plan or a ruling; anything would touch secrets, force-push, rewrite history, or delete anything except your own scratch branches.
   f. After each item, the chat reply is at most 15 lines: what changed, commit range, tests before and after, verifier verdict, and a numbered "Decisions for the chat" list. Detail goes in the report file.
   g. If the session gets long or you notice you are losing earlier instructions, update worklog/SESSION_STATE.md, push, and tell Boris to start a fresh session with: "Read CLAUDE.md, BUILD_PLAN.md and worklog/SESSION_STATE.md, then wait for the next instruction."
10. Tests before and after, native verifier on S0c, write guard, push.
END RULING

No re-tuning after viewing results.
