# FPL Edge — index

A local Fantasy Premier League decision tool for Boris (entry 3073318, "1. FC
Kiripolcz", 7-man league 455565, season 2026/27). `fpl_sync.py` pulls the FPL
API into `fpl.sqlite` and exports `fpl_export_gwN.json`; `fpl_edge.py` reports
and records point-in-time forecasts to `projection_log.csv`. The repo lives at
`C:\GIT\FPL` (github.com/borisdanihel-dev/FPL, branch `master`). The only
nightly writer is the GitHub Actions workflow `nightly` (21:40 UTC: tests →
sync → record → watch file → report, committed back). `fpl_run.bat` and the
`FPL_SYnc` scheduled task are retired and must not be run. Do `git pull`
before any local session.
Windows, Python 3.14. The measured findings are the product; the code serves them.

## Standing rules
- **Never fabricate.** A missing input is reported and the work stops; nothing
  is substituted. Every correlation is printed with its interval.
- **Point-in-time.** Forecasts are recorded before the deadline or not at all.
  Never open `projection_log.csv` in Excel — it locks the file; read it on
  GitHub, or copy it first.
- **Lockdown guard.** A gameweek is graded only when its event has
  `data_checked = 1` and every fixture has `finished = 1`. Provisional grades
  are never recorded. Run `p1_eval.py` only after `--section calibration`
  accepts the gameweek; `p1_eval.py` itself is frozen.
- **Model-change protocol.** Definitions are frozen in `CHANGELOG.md`,
  timestamped, before the deadline that tests them; a frozen entry is never
  edited, only amended by a new one. A model drives a decision only after
  clearing its pre-stated bar. Nothing is tuned on the data that exposed it.
- **Change protocol.** `python test_fpl.py` before and after. Build in a
  scratch copy; reintroduce each bug and watch its test go red; apply only a
  byte-identical copy; regenerate the forecasts and diff the log to prove the
  recording path did not move. Test at simulated GW10/20/38. Log what was
  measured in `CHANGELOG.md`, not just what was done.

## Work-item protocol (BUILD_PLAN.md, from Step 0)
- **One step per session.** Stop after the step's report; do not start the
  next step until Boris says so.
- **Runner code is Python standard library only.** Optional local tools (e.g.
  a MILP solver) live under `tools/`, with their own requirements file, and
  the nightly runner never imports them.
- **Never edit frozen models in place.** A new or changed model is recorded to
  the projection log under a **new source name**. It replaces nothing until
  its pre-registered test passes and Boris accepts it in chat.
- **Every item:** `prereg/<item>.md` committed before any code for it (copy
  `prereg/TEMPLATE.md`) → implement → tests → the `backtest-verifier` agent
  (`.claude/agents/backtest-verifier.md`) → report in
  `worklog/cc_<date>_<item>.md`, the verifier's in `worklog/verify_<item>.md`
  → changelog → commit and push. A FAIL verdict means the item is not done.
- **Verifier write guard.** After every verifier run, the main session runs
  `git status` and `git diff`. Any change outside `worklog/verify_<item>.md`
  voids the verdict: revert it and rerun the verifier.
- **Rulings.** The chat's ruling text for an item is pasted verbatim into
  `prereg/<item>.md` before any code.
- **Verifier launch.** Every verifier launch starts with: "Read .claude/agents/backtest-verifier.md from disk first; where it differs from your loaded instructions, the file on disk governs."
- **Secrets.** `ODDS_API_KEY` is a GitHub Actions repository secret,
  optionally also a local environment variable. Never write it, or any URL or
  header containing it, to a file, a log or a report.
- **When `BUILD_PLAN.md` and the code disagree, stop and report** instead of
  guessing.

## Session operating mode

a. One item at a time. Start an item only when Boris says so ("Do Step N" or a "RULING <item>:" block). After an item is pushed, stop and wait. Never start the next item on your own.

b. Each item: git pull; tree clean; the newest logs/run_<date>.log is from the last nightly (if not, say so first); prereg/<item>.md with the ruling verbatim, committed before any code; implement; tests before and after; native verifier with the read-from-disk instruction; write guard (git status and git diff; any change outside worklog/verify_<item>.md voids the verdict); report worklog/cc_<date>_<item>.md; CHANGELOG; worklog/SESSION_STATE.md; push.

c. Text Boris pastes that starts with "RULING <item>:" is the chat's ruling. Paste it verbatim into prereg/<item>.md. Do not paraphrase or extend it.

d. Runner freeze: changes to the runner path (.github/workflows, fpl_nightly.py, fpl_sync.py, the record step) are pushed before 23:00 Prague and never within 30 hours before the next FPL deadline (deadline_time in the newest export). If an item would land in that window, stop and say so.

e. Stop and ask, changing nothing further, when: the plan and the code disagree; a test cannot be shown red before the fix; the verifier FAILs or WARNs; a decision is not covered by the plan or a ruling; anything would touch secrets, force-push, rewrite history, or delete anything except your own scratch branches.

f. After each item, the chat reply is at most 15 lines: what changed, commit range, tests before and after, verifier verdict, and a numbered "Decisions for the chat" list. Detail goes in the report file.

g. If the session gets long or you notice you are losing earlier instructions, update worklog/SESSION_STATE.md, push, and tell Boris to start a fresh session with: "Read CLAUDE.md, BUILD_PLAN.md and worklog/SESSION_STATE.md, then wait for the next instruction."

## Where things are
- `CLAUDE_fable chat.md` — project handoff: data flow, design rules, FPL context.
- `CLAUDE_opusChat.md` — measured findings, failed approaches, working practices.
- `BACKLOG.md` — what is assumed, missing or broken; Part 3 is the ruling on it.
- `BUILD_SPEC.md` — the reliability-weighted model and the `minutes` bar.
- `HISTORICAL_VALIDATION.md` — the 2025/26 backtest plan and its leakage rules.
- `FPL_PLAN.md` — deadlines (Prague time), chips, the weekly routine.
- `CHANGELOG.md` — every change and measurement, with the frozen definitions.
