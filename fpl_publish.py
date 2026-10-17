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

Exit 0 after a push, or when there is nothing to commit; 1 otherwise.

Standard library only.
"""

import random
import subprocess
import sys
import time
from datetime import datetime, timezone

import fpl_gate

BRANCH = "data"
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


def main(argv=None, sleep=None, say=print):
    argv = sys.argv[1:] if argv is None else argv
    data = argv[0] if argv else "."
    if fpl_gate.main([data]) != 0:
        return 1
    _git(data, "add", "-A")
    if fpl_gate.main(["--secrets", data]) != 0:
        _git(data, "reset", "-q")
        return 1
    if _git(data, "diff", "--cached", "--quiet").returncode == 0:
        say("nothing to commit")
        return 0
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    r = _git(data, "commit", "-q", "-m", f"nightly {stamp} [skip ci]")
    if r.returncode != 0:
        say(f"COMMIT FAILED {r.stdout.strip()}")
        return 1
    return 0 if push(data, sleep=sleep, say=say) else 1


if __name__ == "__main__":
    sys.exit(main())
