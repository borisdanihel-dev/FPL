"""tools/provenance.py - run.txt for every output folder (RULING S8 verifier
FAIL item (e), prereg/provenance.md). Standard library only; offline tools
only, the nightly never imports it.

A tool opens a Run at its start and closes it after writing its outputs;
the folder then holds `run.txt` with the tool, its arguments, the commit it
ran on (plus the count of modified tracked files, so a dirty tree is
visible), its start and end times in UTC, and the SHA-256 of every output
it wrote. A report may cite a run only when that commit equals the item's
final code. Nothing is guessed: with no git available the commit reads
"unknown (git unavailable)".
"""
import hashlib
import os
import subprocess
import sys
from datetime import datetime, timezone

RUN_FILE = "run.txt"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0)


def git_state(root):
    """(commit hash, modified tracked files) of the checkout at `root`;
    ("unknown (git unavailable)", None) when git cannot answer."""
    try:
        head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30)
        if head.returncode != 0:
            return "unknown (git unavailable)", None
        dirty = subprocess.run(["git", "-C", root, "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, timeout=30)
        n = len([ln for ln in dirty.stdout.splitlines() if ln.strip()]) if dirty.returncode == 0 else None
        return head.stdout.strip(), n
    except (OSError, subprocess.SubprocessError):
        return "unknown (git unavailable)", None


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Run:
    """with Run("tools/planner.py", out_dir, argv) as run: ... run.wrote(path)"""

    def __init__(self, tool, out_dir, argv=None, root=None):
        self.tool = tool
        self.out_dir = out_dir
        self.argv = list(sys.argv[1:] if argv is None else argv)
        self.root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.start = utc_now()
        self.commit, self.dirty = git_state(self.root)
        self.outputs = []

    def wrote(self, path):
        self.outputs.append(path)
        return path

    def close(self):
        end = utc_now()
        os.makedirs(self.out_dir, exist_ok=True)
        lines = [f"tool: {self.tool}",
                 f"args: {' '.join(self.argv) if self.argv else '(none)'}",
                 f"commit: {self.commit}",
                 f"modified tracked files at the run: {'unknown' if self.dirty is None else self.dirty}",
                 f"start_utc: {self.start.isoformat()}",
                 f"end_utc: {end.isoformat()}",
                 f"duration_s: {int((end - self.start).total_seconds())}",
                 "outputs:"]
        for p in self.outputs:
            lines.append(f"  {os.path.basename(p)}  sha256 {sha256_of(p)}" if os.path.exists(p) else f"  {os.path.basename(p)}  (missing)")
        path = os.path.join(self.out_dir, RUN_FILE)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        return path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.close()
        return False


def read_run(out_dir):
    """{field: value} of an output folder's run.txt; None when absent."""
    path = os.path.join(out_dir, RUN_FILE)
    if not os.path.exists(path):
        return None
    out = {"outputs": {}}
    with open(path, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.rstrip("\n")
            if ln == "outputs:":
                continue
            if ln.startswith("  ") and "sha256" in ln:
                name, _, digest = ln.strip().rpartition("sha256 ")
                out["outputs"][name.strip()] = digest.strip()
            elif ":" in ln and not ln.startswith("  "):
                k, _, v = ln.partition(":")
                out[k.strip()] = v.strip()
    return out
