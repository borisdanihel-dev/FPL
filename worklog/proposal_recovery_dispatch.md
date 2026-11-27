# Recovery runs dispatched by Claude Code: IN FORCE from Fri 27 Nov 16:30 UTC (Boris's ruling, point 3), with the amendments at the end

Boris's rulings of Fri 27 Nov 16:25 UTC, point 4 (verbatim in `prereg/W3fix.md`, `runcommit.md`, `W5.md`).
Session draft, Fri 27 Nov 16:24 UTC.

## What was checked
- `gh` 2.106.0 is installed at `C:\Program Files\GitHub CLI\gh.exe`. It is not on the Git Bash PATH, so it is
  called by its full path.
- `gh auth status`: logged in to github.com as the repo owner's account (keyring), git over https, token scopes
  `gist`, `read:org`, `repo`, `workflow`. The `workflow` scope is what a dispatch needs. The token itself was
  never printed: the check filters every line holding a token.

## Proposed rules (Boris's list, made checkable)
1. **What:** only `gh workflow run nightly.yml --ref master -f dry_run=false -f odds_live=false -f
   force_backup=false`. Nothing else goes through `gh`: no other workflow, ref or input; no re-run, cancel,
   secret or API call.
   - "Nothing ticked" in the Actions form is a real run. The form's `dry_run` box defaults to ticked
     (`default: true`), so the command passes `dry_run=false` explicitly.
2. **When, all checked and logged before the dispatch:**
   - a. Recovery only: the last scheduled nightly (21:40 UTC, with its 03:17 UTC backup) failed or left no data
     commit for that night, or Boris asks in chat.
   - b. Clean master: local master equals `origin/master`, `git status` is clean, and the commit is recorded.
   - c. Not within 2 h of a deadline: the next event's `deadline_time`, read from the FPL API at check time (as
     W5's gate does), falling back to `fpl.sqlite` and saying so.
   - d. Not from 21:00 UTC until that night's nightly has committed.
   - e. No nightly run queued or running (`gh run list --workflow nightly.yml --limit 5`): never a second
     writer, even though the concurrency group would queue it.
   - f. At most 2 a UTC day, counted from the dispatch log below, and from `gh run list` dispatches by this
     account that day.
3. **Log:** one line per dispatch in `worklog/dispatch_log.md`, committed before the dispatch. It holds the UTC
   time, master's commit, the reason, and the result of each check a-f. After the run come the run id, the
   conclusion and the data commit (or "none").
4. **After the run:** the same read-back as after a nightly (STATUS line, checks, recorded counts). A failed
   recovery run is reported to Boris. A second dispatch that day needs a new reason, never "retry".
5. **Never:** within W5's pre-deadline window to stand in for it (W5's gate decides its own run); a dry run
   through this path (dry runs stay pushes to `dry/<item>`, RULING W1b); `--show-token`; or printing `gh auth`
   output that holds a token.

## Not done
No dispatch has been made, and none will be made until Boris rules.

## Ruling, Fri 27 Nov 16:30 UTC (Boris's message verbatim; for this file: point 3)

Rulings (Fri 27 Nov, 16:30 UTC). Record verbatim.

1. T1/T2 on Sat 28: merge under the advance approval, after runcommit.
- Clarification of the approval rule (add to BUILD_PLAN.md Part B under point 1): "no other runner change that night" applies only when the item being merged is itself a runner change.
- A test-only item can merge the same night as a runner change. Test-only means its diff touches only tests/, worklog/, prereg/ or docs, nothing the runner imports or executes, and the verifier confirms that.
- Order: runcommit first. Then rebase T1/T2 on the merged master and run the full suite on a fresh clone.
- If 21:00 UTC comes first, T1/T2 wait for the next free night, still approved in advance.

2. W5 naming accepted (W4 stays the later queue item).

3. Recovery dispatch: proposal_recovery_dispatch.md accepted, effective now, with two amendments:
a. Boris's explicit request in chat overrides rule 2a (recovery only) and rule 5 (not standing in for W5), but never 2b–2f.
b. Review after W5 has run live for two deadlines.
Report every dispatch in your next status message.

4. Time-label correction noted; no further action.

Standing rule holds: a WARN or FAIL stops that item only; park it and carry on.

## The rules as amended (session, from the ruling's point 3)
- a. Boris's explicit request in chat lifts rule 2a (recovery only) and rule 5's first item (not standing in for
  W5). Rules 2b-2f still hold every time. The log line quotes his request.
- b. The rules are reviewed after W5 has run live for two deadlines.
- Every dispatch is reported in the next status message to Boris.
- "## Not done" above is superseded: from 16:30 UTC a dispatch may be made under these rules. None has been made
  yet. The log is `worklog/dispatch_log.md`, created with the first dispatch.
