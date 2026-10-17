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
- **Standard library only.** No pip, no third-party dependencies.
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
- **Secrets.** `ODDS_API_KEY` is a GitHub Actions repository secret,
  optionally also a local environment variable. Never write it, or any URL or
  header containing it, to a file, a log or a report.
- **When `BUILD_PLAN.md` and the code disagree, stop and report** instead of
  guessing.

## Where things are
- `CLAUDE_fable chat.md` — project handoff: data flow, design rules, FPL context.
- `CLAUDE_opusChat.md` — measured findings, failed approaches, working practices.
- `BACKLOG.md` — what is assumed, missing or broken; Part 3 is the ruling on it.
- `BUILD_SPEC.md` — the reliability-weighted model and the `minutes` bar.
- `HISTORICAL_VALIDATION.md` — the 2025/26 backtest plan and its leakage rules.
- `FPL_PLAN.md` — deadlines (Prague time), chips, the weekly routine.
- `CHANGELOG.md` — every change and measurement, with the frozen definitions.
