"""
fpl_publish.py  -  commit tonight's data to the `data` branch and push it
(BUILD_PLAN.md Step 1.1, 1.5 and 1.6). The workflow runs it after
fpl_nightly.py even when the run was red, so a failure still commits its log -
unless the gate fails, which commits nothing at all.

    python fpl_publish.py DATA_DIR

  1. the gate (fpl_gate.py): integrity, missing and new tables, grow-only row
     counts, frozen forecasts in projection_log.csv; on a pass it writes
     fpl.sql;
  2. git add -A in DATA_DIR (the data branch's .gitignore keeps the working
     exports and scratch files out);
  3. the staged-secret scan; a hit unstages everything and commits nothing;
  4. commit, then push to origin's data branch: on a refusal, wait (with
     jitter), fetch, rebase onto what was fetched, push again - up to 3
     retries. A rebase conflict is aborted and fails the step. Never forced.

A dry run (S2 amendment 2, point 5) does 1-3 the same way, then commits and
force-pushes the result to origin's data-dryrun branch - and only there: it
never pushes to data. Any run whose ref is not master is dry, whatever it
asked for; a scheduled run is never dry; a dispatch on master is dry while
its dry_run input is ticked (the workflow passes it as FPL_DRY_RUN).

Before all of it: when tonight's checks (checks.py, S3) wrote a status file
whose first line is STATUS FAIL, a real run commits nothing (Step 3.1: FAIL =
no data commit and a red run). A dry run says what a real one would have done
and still reports to data-dryrun, so a failed dry run can be read back.

Exit 0 after a push, or when a real run has nothing to commit; 1 otherwise.

Standard library only.
"""

import os
import random
import subprocess
import sys
import time
from datetime import datetime, timezone

import fpl_gate

BRANCH = "data"
DRY_BRANCH = "data-dryrun"           # a dry run's only push target (S2 amendment 2, point 5)
MASTER = "refs/heads/master"
RETRIES = 3


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")


def push(repo, branch=BRANCH, retries=RETRIES, sleep=None, say=print):
    """Push HEAD to origin/<branch>; fetch + rebase + push again on a refusal.
    Returns True once a push lands."""
    sleep = sleep or time.sleep
    for attempt in range(retries + 1):
        r = _git(repo, "push", "origin", f"HEAD:refs/heads/{branch}")
        if r.returncode == 0:
            say(f"PUSH OK      origin {branch}" + (f" after {attempt} retries" if attempt else ""))
            return True
        say(f"PUSH REFUSED attempt {attempt + 1}: {r.stdout.strip().splitlines()[-1:] or ''}")
        if attempt == retries:
            break
        sleep(random.uniform(2, 8) * (attempt + 1))
        if _git(repo, "fetch", "origin", branch).returncode != 0:
            continue
        if _git(repo, "rebase", "FETCH_HEAD").returncode != 0:
            _git(repo, "rebase", "--abort")
            say("PUSH FAILED  rebase conflict with what origin has - aborted, nothing forced")
            return False
    say(f"PUSH FAILED  after {retries} retries")
    return False


def run_mode(env):
    """("dry" | "real", why) for this run (S2 amendment 2, point 5). Any run
    whose ref is not master is dry, whatever it asked for; a scheduled run on
    master is never dry; otherwise FPL_DRY_RUN decides ("true" = dry). A
    local run has no GITHUB_REF and is real unless FPL_DRY_RUN is "true"."""
    ref = env.get("GITHUB_REF") or ""
    if ref and ref != MASTER:
        return "dry", f"ref {ref} is not {MASTER}"
    if env.get("GITHUB_EVENT_NAME") == "schedule":
        return "real", "scheduled run"
    if (env.get("FPL_DRY_RUN") or "").strip().lower() == "true":
        return "dry", "dry_run is ticked"
    return "real", ("dry_run is not ticked" if ref else "local run")


def push_dry(repo, say=print):
    """Force-push HEAD to origin's data-dryrun: the dry run's only push.
    Never to data."""
    assert DRY_BRANCH != BRANCH
    r = _git(repo, "push", "--force", "origin", f"HEAD:refs/heads/{DRY_BRANCH}")
    if r.returncode == 0:
        say(f"PUSH OK      origin {DRY_BRANCH} (dry run, forced; {BRANCH} untouched)")
        return True
    say(f"PUSH FAILED  origin {DRY_BRANCH}: {r.stdout.strip().splitlines()[-1:] or ''}")
    return False


def checks_failed(data, mode):
    """The FAIL lines of the status file tonight's checks wrote
    (reports/status.txt, or reports/status_dryrun.txt on a dry run), or []
    when it says no FAIL or was not written tonight - the same as in the
    last commit, or absent."""
    name = f"reports/{'status_dryrun.txt' if mode == 'dry' else 'status.txt'}"
    path = os.path.join(data, name)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    head = _git(data, "show", f"HEAD:{name}")
    if head.returncode == 0 and head.stdout.splitlines() == text.splitlines():
        return []
    lines = text.splitlines()
    if not lines or not lines[0].startswith("STATUS FAIL"):
        return []
    return [l.strip() for l in lines[1:] if l.split()[1:2] == ["FAIL"]] or [lines[0]]


def main(argv=None, sleep=None, say=print, env=None):
    argv = sys.argv[1:] if argv is None else argv
    env = os.environ if env is None else env
    data = argv[0] if argv else "."
    mode, why = run_mode(env)
    if mode == "dry":
        say(f"DRY RUN      {why}: the result goes to {DRY_BRANCH} only, never to {BRANCH}")
    failed = checks_failed(data, mode)
    for line in failed:
        say(f"CHECKS FAIL  {line}")
    if failed and mode == "real":
        say("CHECKS FAIL  nothing committed tonight (Step 3.1)")
        return 1
    if failed:
        say("CHECKS FAIL  a real run would commit nothing; the dry run still reports "
            f"to {DRY_BRANCH}")
    if fpl_gate.main([data]) != 0:
        return 1
    _git(data, "add", "-A")
    if fpl_gate.main(["--secrets", data]) != 0:
        _git(data, "reset", "-q")
        return 1
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _git(data, "diff", "--cached", "--quiet").returncode == 0:
        say("nothing to commit")
        if mode == "real":
            return 0
    else:
        msg = (f"dry run {stamp} {env.get('GITHUB_REF_NAME', '')} "
               f"{env.get('GITHUB_SHA', '')[:7]} [skip ci]" if mode == "dry"
               else f"nightly {stamp} [skip ci]")
        r = _git(data, "commit", "-q", "-m", " ".join(msg.split()))
        if r.returncode != 0:
            say(f"COMMIT FAILED {r.stdout.strip()}")
            return 1
    if mode == "dry":
        return 0 if push_dry(data, say=say) else 1
    return 0 if push(data, sleep=sleep, say=say) else 1


if __name__ == "__main__":
    sys.exit(main())
