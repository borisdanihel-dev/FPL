"""
fpl_prepush.py  -  the pre-push hook that keeps generated data off master
(BUILD_PLAN.md Step 1.5). The data lives on the `data` branch; a push to
master whose new commits add or change a data path is rejected. Deleting one
is allowed: that is what the migration commit does.

    python fpl_prepush.py --install     write this clone's .git/hooks/pre-push

Git runs the hook with the remote's name and URL as arguments and one line per
ref on stdin: <local ref> <local sha> <remote ref> <remote sha>. The commits
checked are those not yet on any remote-tracking branch.

Standard library only.
"""

import os
import subprocess
import sys

DATA_FILES = ("fpl.sqlite", "fpl.sql", "projection_log.csv")
DATA_DIRS = ("exports/", "reports/", "logs/")
MASTER = "refs/heads/master"
ZERO = "0" * 40


def is_data(path):
    return path in DATA_FILES or path.startswith(DATA_DIRS)


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], stdout=subprocess.PIPE,
                          check=True, encoding="utf-8").stdout


def offending(repo, local_sha):
    """(commit, path) for every data path added or changed by a commit that
    `local_sha` would send: one not reachable from any remote-tracking branch."""
    hits = []
    for c in _git(repo, "rev-list", local_sha, "--not", "--remotes").split():
        names = _git(repo, "diff-tree", "--root", "-m", "--no-commit-id", "--name-only",
                     "-r", "--diff-filter=ACMRT", c).split("\n")
        hits += [(c, n) for n in dict.fromkeys(names) if n and is_data(n)]
    return hits


def check(repo, lines):
    """All offending (commit, path) pairs for the pushed refs in `lines`."""
    bad = []
    for line in lines:
        parts = line.split()
        if len(parts) != 4:
            continue
        _, local_sha, remote_ref, _ = parts
        if remote_ref == MASTER and local_sha != ZERO:
            bad += offending(repo, local_sha)
    return bad


def install(repo="."):
    """Write the hook into this clone (never into the repository's files)."""
    hooks = _git(repo, "rev-parse", "--git-path", "hooks").strip()
    hooks = hooks if os.path.isabs(hooks) else os.path.join(repo, hooks)
    os.makedirs(hooks, exist_ok=True)
    path = os.path.join(hooks, "pre-push")
    py = sys.executable.replace("\\", "/")
    me = os.path.abspath(__file__).replace("\\", "/")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("#!/bin/sh\n"
                 "# written by fpl_prepush.py --install: no data paths on master.\n"
                 "# The full path: worktrees share this hook, and the data worktree\n"
                 "# holds no code.\n"
                 f'exec "{py}" "{me}" "$@"\n')
    os.chmod(path, 0o755)
    return path


def main(argv=None, stdin=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--install"]:
        print(f"installed {install()}")
        return 0
    bad = check(".", (stdin or sys.stdin).read().splitlines())
    for c, path in bad:
        print(f"PRE-PUSH REJECTED  {c[:7]} adds or changes {path}: "
              f"data belongs on the data branch", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
