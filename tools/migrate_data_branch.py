"""
tools/migrate_data_branch.py  -  the one-time move of generated data from
master to the orphan branch `data` (BUILD_PLAN.md Step 1.4; ruling S1 points
4 and 6). A local tool: the nightly runner never imports it. Standard library.

    python tools/migrate_data_branch.py measure FOLDER OUT.json
        row counts for every table in FOLDER/fpl.sqlite, the data rows of
        FOLDER/projection_log.csv, and for every tracked data file its git blob
        id, the sha256 of the blob (the bytes git stores) and the sha256 of the
        file in FOLDER (the bytes this checkout wrote)

    python tools/migrate_data_branch.py build
        create refs/heads/data in this clone (never pushes): one parentless
        commit whose data files are master's own blobs - the same object ids,
        so byte-identical by construction - plus the data branch's .gitignore
        and .gitattributes. Refuses if `data` already exists.

    python tools/migrate_data_branch.py compare BEFORE.json AFTER.json
        side by side; exit 1 on any difference
"""

import csv
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile

DATA_PATHS = ["fpl.sqlite", "projection_log.csv", "exports", "reports", "logs"]

DATA_GITIGNORE = """\
# the data branch: generated data only (BUILD_PLAN.md Step 1.4)
# the working exports are restored from exports/ on every run
/fpl_export_gw*.json
reports/record_status.tmp
reports/run_*.log
projection_log.csv.tmp
*.tmp
"""

DATA_GITATTRIBUTES = """\
* text=auto
# csv.writer ends every row with CRLF on any platform: keep the checkout CRLF
projection_log.csv text eol=crlf
# binary: never diffed, never merged
*.sqlite binary
*.gz binary
# the dump holds stored values byte for byte: no end-of-line conversion
fpl.sql -text
"""


def git(*args, cwd=".", stdin=None, env=None):
    r = subprocess.run(["git", "-C", cwd, *args], input=stdin, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, env=env)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.decode(errors='replace').strip()}")
    return r.stdout


def measure(folder):
    db = os.path.join(folder, "fpl.sqlite")
    con = sqlite3.connect(pathlib.Path(db).resolve().as_uri() + "?mode=ro", uri=True)
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    counts = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    integrity = [r[0] for r in con.execute("PRAGMA integrity_check")]
    con.close()
    with open(os.path.join(folder, "projection_log.csv"), encoding="utf-8", newline="") as fh:
        log_rows = sum(1 for _ in csv.reader(fh)) - 1
    files = {}
    for line in git("ls-files", "-s", "-z", "--", *DATA_PATHS, cwd=folder).decode().split("\0"):
        if not line:
            continue
        meta, path = line.split("\t", 1)
        blob = meta.split()[1]
        stored = git("cat-file", "blob", blob, cwd=folder)
        with open(os.path.join(folder, path), "rb") as fh:
            disk = fh.read()
        files[path] = {"blob": blob, "sha256_stored": hashlib.sha256(stored).hexdigest(),
                       "sha256_disk": hashlib.sha256(disk).hexdigest(), "bytes_stored": len(stored)}
    return {"folder": os.path.abspath(folder), "head": git("rev-parse", "HEAD", cwd=folder).decode().strip(),
            "integrity_check": integrity, "tables": counts, "projection_log_rows": log_rows,
            "files": files}


def build():
    if subprocess.run(["git", "rev-parse", "--verify", "-q", "refs/heads/data"],
                      stdout=subprocess.DEVNULL).returncode == 0:
        sys.exit("refs/heads/data already exists - nothing built")
    head = git("rev-parse", "HEAD").decode().strip()
    listing = git("ls-tree", "-r", "-z", head, "--", *DATA_PATHS)
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
        git("read-tree", "--empty", env=env)
        info = b"".join(entry.split(b"\t", 1)[0].replace(b" blob ", b" ") + b"\t"
                        + entry.split(b"\t", 1)[1] + b"\0"
                        for entry in listing.split(b"\0") if entry)
        git("update-index", "-z", "--index-info", stdin=info, env=env)
        for name, body in ((".gitignore", DATA_GITIGNORE), (".gitattributes", DATA_GITATTRIBUTES)):
            blob = git("hash-object", "-w", "--stdin", stdin=body.encode()).decode().strip()
            git("update-index", "--add", "--cacheinfo", f"100644,{blob},{name}", env=env)
        tree = git("write-tree", env=env).decode().strip()
    msg = (f"data: first commit - the generated data from master {head[:7]}, "
           f"byte-identical (same blobs)\n")
    commit = git("commit-tree", tree, stdin=msg.encode()).decode().strip()
    git("update-ref", "refs/heads/data", commit, "")
    moved = [e.split(b"\t", 1) for e in listing.split(b"\0") if e]
    same = all(git("rev-parse", f"{commit}:{p.decode()}").strip() == m.split()[2] for m, p in moved)
    print(f"built refs/heads/data {commit[:7]}: {len(moved)} files from master {head[:7]}, "
          f"blobs identical: {same}")
    return 0 if same else 1


def compare(before_path, after_path):
    with open(before_path, encoding="utf-8", newline="") as fh:
        a = json.load(fh)
    with open(after_path, encoding="utf-8", newline="") as fh:
        b = json.load(fh)
    bad = 0
    print(f"{'':28s} {'before':>12s} {'after':>12s}")
    for t in sorted(set(a["tables"]) | set(b["tables"])):
        x, y = a["tables"].get(t), b["tables"].get(t)
        bad += x != y
        print(f"table {t:22s} {x!s:>12s} {y!s:>12s}{'' if x == y else '   DIFFERENT'}")
    x, y = a["projection_log_rows"], b["projection_log_rows"]
    bad += x != y
    print(f"{'projection_log.csv rows':28s} {x:>12d} {y:>12d}{'' if x == y else '   DIFFERENT'}")
    print(f"{'integrity_check':28s} {','.join(a['integrity_check']):>12s} "
          f"{','.join(b['integrity_check']):>12s}")
    bad += a["integrity_check"] != ["ok"] or b["integrity_check"] != ["ok"]
    for kind in ("blob", "sha256_stored", "sha256_disk"):
        diff = sorted(p for p in set(a["files"]) | set(b["files"])
                      if a["files"].get(p, {}).get(kind) != b["files"].get(p, {}).get(kind))
        bad += bool(diff)
        print(f"files with the same {kind:14s} {len(a['files']) - len(diff)}/{len(a['files'])}"
              + (f"   DIFFERENT: {diff[:5]}" if diff else ""))
    return 1 if bad else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["measure"] and len(argv) == 3:
        with open(argv[2], "w", encoding="utf-8", newline="") as fh:
            json.dump(measure(argv[1]), fh, indent=1, sort_keys=True)
        print(f"measured {argv[1]} -> {argv[2]}")
        return 0
    if argv == ["build"]:
        return build()
    if argv[:1] == ["compare"] and len(argv) == 3:
        return compare(argv[1], argv[2])
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
