# FPL Edge — index

A local Fantasy Premier League decision tool for Boris (entry 3073318, "1. FC
Kiripolcz", 7-man league 455565, season 2026/27). `fpl_sync.py` pulls the FPL
API into `fpl.sqlite` and exports `fpl_export_gwN.json`; `fpl_edge.py` reports
and records point-in-time forecasts to `projection_log.csv`; `fpl_run.bat` runs
nightly at 23:55 (tests → sync → record → report → archive/backup/ship).
Windows, Python 3.14. The measured findings are the product; the code serves them.

## Standing rules
- **Standard library only.** No pip, no third-party dependencies.
- **Never fabricate.** A missing input is reported and the work stops; nothing
  is substituted. Every correlation is printed with its interval.
- **Point-in-time.** Forecasts are recorded before the deadline or not at all.
  Never open `projection_log.csv` in Excel — it locks the file; open the copy
  in `G:\My Drive\FPL\`.
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

## Where things are
- `CLAUDE_fable chat.md` — project handoff: data flow, design rules, FPL context.
- `CLAUDE_opusChat.md` — measured findings, failed approaches, working practices.
- `BACKLOG.md` — what is assumed, missing or broken; Part 3 is the ruling on it.
- `BUILD_SPEC.md` — the reliability-weighted model and the `minutes` bar.
- `HISTORICAL_VALIDATION.md` — the 2025/26 backtest plan and its leakage rules.
- `FPL_PLAN.md` — deadlines (Prague time), chips, the weekly routine.
- `CHANGELOG.md` — every change and measurement, with the frozen definitions.
