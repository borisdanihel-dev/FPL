"""Scratch: fpl_squad.ban_risk from the bundle commit on the data, with a # source line. argv: code data outfile"""
import os, subprocess, sys
from datetime import datetime, timezone
code, data, outp = sys.argv[1:4]
sys.path.insert(0, code); sys.path.insert(0, os.path.join(code, "tools"))
import fpl_squad as SQ
head = subprocess.run(["git", "-C", code, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = len(subprocess.run(["git", "-C", code, "status", "--porcelain", "--untracked-files=no"], capture_output=True, text=True).stdout.splitlines())
dh = subprocess.run(["git", "-C", data, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
lines = [f"# fpl_squad.ban_risk from master {head} (modified tracked files {dirty}) on data {dh}, {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}"]
SQ.ban_risk(data, lines.append)
with open(outp, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(lines))
