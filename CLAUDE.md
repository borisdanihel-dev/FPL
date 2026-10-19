# FPL Edge — index

A local Fantasy Premier League decision tool for Boris (entry 3073318, "1. FC
Kiripolcz", 7-man league 455565, season 2026/27). `fpl_sync.py` pulls the FPL
API into `fpl.sqlite` and exports `fpl_export_gwN.json`; `fpl_edge.py` reports
and records point-in-time forecasts to `projection_log.csv`. The repo lives at
`C:\GIT\FPL` (github.com/borisdanihel-dev/FPL, branch `master`). The only
nightly writer is the GitHub Actions workflow `nightly` (21:40 UTC: tests →
sync → record → watch file → report, committed to the `data` branch). `fpl_run.bat` and the
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
- **Hermetic tests** (S3 amendment 1): tests are hermetic; no test may rely on
  global git config, the machine's timezone or locale, or files outside its
  temporary folder.
- **Downloads are data, never code** (RULING lane A, 19 Oct midday, point 1;
  all work). Downloaded files are only ever opened by a Python reader run
  with `-I`. They are never sourced, executed, piped into a shell or placed
  inside an unquoted heredoc. Use quoted heredocs or the file-writing tool
  only.
- **Change protocol.** The whole suite before and after, by discovery
  (`test_fpl.py` plus `tests/`, FAST-TRACK item 5): `python -m unittest
  discover -v -p "test*.py"` in `C:\GIT\FPL`. Build in a
  scratch copy; reintroduce each bug and watch its test go red; apply only a
  byte-identical copy; regenerate the forecasts and diff the log to prove the
  recording path did not move. Test at simulated GW10/20/38. Log what was
  measured in `CHANGELOG.md`, not just what was done.

## Work-item protocol (BUILD_PLAN.md, from Step 0)
- **One item at a time: stop after each item is pushed and wait for Boris (Session operating mode a).**
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
- **Verifier model** (S1 closing ruling): model fable, effort high, as the agent
  file says. If Fable is unavailable or Claude Code asks for usage credits,
  decline the credits and run the verifier with model opus at effort xhigh; the
  verifier report states which ran.
- **Secrets.** `ODDS_API_KEY` is a GitHub Actions repository secret,
  optionally also a local environment variable. Never write it, or any URL or
  header containing it, to a file, a log or a report.
- **Masking.** Every report and verifier report masks key-like strings: the
  first 4 characters, then "...".
- **When `BUILD_PLAN.md` and the code disagree, stop and report** instead of
  guessing.
- **Fast track** (RULING FAST-TRACK, `prereg/FAST.md`; all nine items in
  BUILD_PLAN.md Part E). Items 1, 4, 5 and 6, verbatim:
  1. Two kinds of work. Runner work = anything the nightly workflow runs or imports, or the workflow itself: the fast-lane merge rule, dry run, Boris's real dispatch and the freeze windows apply. Offline work = new modules under tools/ or analysis/ that the runner does not import; they read a local copy of data (C:\GIT\FPL-data, pulled, read-only) and never write to data. Offline items merge to master after tests, verifier PASS and the write guard; no dry run, no dispatch, no freeze restriction. A test proves the nightly imports nothing under tools/ or analysis/.
  4. Two lanes. Lane A works in C:\GIT\FPL: runner work, wiring items and history items. Lane B works in a second worktree, C:\GIT\FPL-b (lane A creates it with git worktree add, on its own branch): offline items. One Claude Code session per lane, never two sessions in one folder. Each lane keeps worklog/SESSION_STATE_A.md or worklog/SESSION_STATE_B.md. Either lane may merge its own items: fetch, rebase onto master, rerun the full test suite, push; never force. On a CHANGELOG conflict, keep both entries.
  5. Tests: new items put their tests in tests/test_<item>.py. S3 switches the nightly gate and local runs to test discovery (test_fpl.py plus tests/). Only lane A edits test_fpl.py.
  6. Auto-continue: after an offline item with verifier PASS, a clean write guard and no open decision, the lane starts its next queued item without waiting; it still prints its 15-line summary. It stops on FAIL, WARN, an open decision, a model result that would change a live decision (adoption needs Boris's acceptance in chat), or after 6 items without a chat review.
- **Lanes merged** (RULING S6b acceptance + lanes merge, 19 Oct; Boris, 19
  Oct): items 4 and 5 above are kept as the record. From 19 Oct there is one
  Claude Code session, working in `C:\GIT\FPL`, for runner and offline work
  alike; it keeps one state file, `worklog/SESSION_STATE_A.md`. Lane B's
  work is on `origin/lane-b` (a backup branch, only ever fast-forwarded);
  branch from it where needed. Never edit `C:\GIT\FPL-b`; read its
  `tools/out` only when needed (provenance). Item 1's split of runner and
  offline work, and item 6's stops, still apply.

## Session operating mode

a. One item at a time. Start an item only when Boris says so ("Do Step N" or a "RULING <item>:" block). After an item is pushed, stop and wait. Never start the next item on your own.

b. Each item: git pull; tree clean; the newest logs/run_<date>.log is from the last nightly (if not, say so first); prereg/<item>.md with the ruling verbatim, committed before any code; implement; tests before and after; native verifier with the read-from-disk instruction; write guard (git status and git diff; any change outside worklog/verify_<item>.md voids the verdict); report worklog/cc_<date>_<item>.md; CHANGELOG; worklog/SESSION_STATE_A.md (the one state file since the lanes merged); push.

c. Text Boris pastes that starts with "RULING <item>:" is the chat's ruling. Paste it verbatim into prereg/<item>.md. Do not paraphrase or extend it.

d. Runner freeze: changes to the runner path (anything the nightly workflow runs or imports) are never pushed between 21:00 UTC and the end of that night's nightly run, and never within 30 hours before an FPL deadline (events.deadline_time in fpl.sqlite). If an item would land in that window, stop and say so.

e. Stop and ask, changing nothing further, when: the plan and the code disagree; a test cannot be shown red before the fix; the verifier FAILs or WARNs; a decision is not covered by the plan or a ruling; anything would touch secrets, force-push, rewrite history, or delete anything except your own scratch branches. Exception: the dry-run workflow force-pushes to data-dryrun only. Claude Code itself never force-pushes, and nothing ever force-pushes to master or data.

f. After each item, the chat reply is at most 15 lines: what changed, commit range, tests before and after, verifier verdict, and a numbered "Decisions for the chat" list. Detail goes in the report file.

g. If the session gets long or you notice you are losing earlier instructions, update worklog/SESSION_STATE_A.md, push, and tell Boris to start a fresh session with: "Read CLAUDE.md, BUILD_PLAN.md and worklog/SESSION_STATE_A.md, then wait for the next instruction."

h. The main session runs Opus 5.5. Effort: xhigh for runner and data steps (1-3), high for model steps, medium for docs-only items. Steps 4, 7, 15, 16 and 17 may run the main session on Fable if Boris switches it; the report names the model used.

## Data branch (BUILD_PLAN.md Step 1)
- Generated data lives on branch `data`: `fpl.sqlite`, `fpl.sql` (its text
  dump), `exports/` (new exports `.json.gz`), `reports/` (report and watch
  files), `logs/`, `projection_log.csv`. `master` holds code, docs,
  `watchlist.txt`, `prereg/`, `worklog/` and `CHANGELOG.md`, and ignores every
  data path.
- The runner checks out `master` for code and `data` into `./data`; the one
  setting is `FPL_DATA_DIR`. It commits and pushes to `data` only, through
  `fpl_publish.py` (integrity gate, dump, staged-secret scan, fetch + rebase +
  push with retries). Sundays it uploads `fpl.sqlite` and `fpl.sql` as
  release `backup-<date>`; the last 8 are kept.
- Locally: the worktree `C:\GIT\FPL-data` (`git worktree add C:\GIT\FPL-data
  data`, once). Before reading data, the session runs `git -C C:\GIT\FPL-data pull
  --ff-only` and nothing else there; on a lock, wait and retry (RULING morning
  19 Oct, point 6).
- **Local command pattern: run from `C:\GIT\FPL-data`, call the script in
  `C:\GIT\FPL`.** The scripts read and write their working folder; of the
  scripts only `fpl_nightly.py` reads `FPL_DATA_DIR` (`test_fpl.py` uses it
  only to find the real data).
  ```
  cd C:\GIT\FPL-data
  git pull --ff-only
  python C:\GIT\FPL\fpl_nightly.py --restore
  python C:\GIT\FPL\fpl_edge.py --section calibration
  python C:\GIT\FPL\fpl_edge.py --diff
  ```
  `--restore` comes first, every time: the working exports
  (`fpl_export_gwN.json`, plain JSON, ignored on `data`) are not committed, so
  it writes them from the newest dated copy in `exports/`, replacing a stale
  one. It writes nothing else and commits nothing. After it, the frozen
  `p1_eval.py` reads those working exports as before.
  The runner is the only writer: never run `fpl_sync.py`, `--record`, or
  `fpl_nightly.py` without `--restore` here. The suite (`python -m unittest
  discover -v -p "test*.py" -s C:\GIT\FPL -t C:\GIT\FPL`: `test_fpl.py` plus
  `tests/`) needs no data; after `--restore`, with `$env:FPL_DATA_DIR =
  "C:\GIT\FPL-data"`, it also checks the real export and database.
- Once per clone: `python fpl_prepush.py --install` (the hook rejects a push to
  `master` that adds or changes a data path; deleting one is allowed).
- Secret scan: `.github/workflows/secret-scan.yml` runs the gitleaks action on
  every push to `master` (the pushed commits), and a full-history scan of every
  branch, `data` included, on Sundays at 04:23 UTC and on Run workflow.
  A push to `data` starts nothing (the branch holds no workflow file, and the
  nightly's pushes start no workflow); every data commit is checked before it
  is made by `fpl_gate.py --secrets`. Accepted findings go in
  `.gitleaksignore`, one exact fingerprint (commit:file:rule:line) each, by
  ruling only.
- Raw URLs: `https://raw.githubusercontent.com/borisdanihel-dev/FPL/data/reports/watch_<date>.txt`
  and `.../data/reports/fpl_<date>.txt`.
- Rollback: tag `pre-data-branch` is `master` before the migration. Every
  `pre-*` tag is kept until the GW10 checkpoint (RULING morning 19 Oct, point 7).
- **No manual nightly dispatch within 1 hour either side of an FPL deadline.** A
  dispatch across a deadline fails the gate (its forecasts were recorded before
  it, the gate runs after) and commits nothing that night.

## Where things are
- `CLAUDE_fable chat.md` — project handoff: data flow, design rules, FPL context.
- `CLAUDE_opusChat.md` — measured findings, failed approaches, working practices.
- `BACKLOG.md` — what is assumed, missing or broken; Part 3 is the ruling on it.
- `BUILD_SPEC.md` — the reliability-weighted model and the `minutes` bar.
- `HISTORICAL_VALIDATION.md` — the 2025/26 backtest plan and its leakage rules.
- `FPL_PLAN.md` — deadlines (Prague time), chips, the weekly routine.
- `CHANGELOG.md` — every change and measurement, with the frozen definitions.
