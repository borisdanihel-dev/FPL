"""
fpl_ship.py  -  after the nightly run: archive the export, back up the database,
ship the outputs to Google Drive. Standard library only.

    python fpl_ship.py --stamp 2026-09-21

Called by fpl_run.bat after the report step. Every copy prints its own result
line, so a failure is visible in the run log rather than silent:

    SHIP OK      projection_log.csv -> G:\\My Drive\\FPL
    SHIP HELD    ... -> outbox          (Drive not mounted; sent on the next run)
    SHIP FAILED  ...: <reason>          (exit code 1)

Rules:
* The dated export goes to archive\\ and is never overwritten by a later day:
  point-in-time inputs, for the same reason forecasts are point-in-time.
* fpl.sqlite is backed up to backup\\ (last 7 kept) and is NEVER shipped - a sync
  client touching a database mid-write is a risk this project does not need.
* The Drive folder, archive\\, backup\\ and outbox\\ all sit outside the glob that
  newest_export() uses, so a copy can never be mistaken for the live export.
"""

import argparse
import glob
import os
import re
import shutil
import sqlite3
import sys

DRIVE_DIR = r"G:\My Drive\FPL"
ARCHIVE, BACKUP, OUTBOX = "archive", "backup", "outbox"
KEEP_BACKUPS = 7
NEVER_SHIP = (".sqlite", ".sqlite-journal", ".sqlite-wal", ".db")


def newest_export(folder="."):
    files = glob.glob(os.path.join(folder, "fpl_export_gw*.json"))
    def gw_of(f):
        m = re.search(r"gw(\d+)\.json$", os.path.basename(f))
        return int(m.group(1)) if m else -1
    files = [f for f in files if gw_of(f) >= 0]
    return max(files, key=lambda f: (gw_of(f), os.path.getmtime(f))) if files else None


def archive_export(export, archive_dir, stamp):
    """Keep tonight's export as fpl_export_gwN_<stamp>.json. Earlier days stay."""
    os.makedirs(archive_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(export))[0]
    dest = os.path.join(archive_dir, f"{base}_{stamp}.json")
    shutil.copy2(export, dest)
    return dest


def backup_db(db, backup_dir, stamp, keep=KEEP_BACKUPS):
    """Consistent copy of the database via sqlite's backup API; prune to `keep`."""
    os.makedirs(backup_dir, exist_ok=True)
    dest = os.path.join(backup_dir, f"fpl_{stamp}.sqlite")
    src = sqlite3.connect(db)
    try:
        dst = sqlite3.connect(dest)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    old = sorted(glob.glob(os.path.join(backup_dir, "fpl_*.sqlite")))[:-keep]
    for f in old:
        os.remove(f)
    return dest, old


def ship(files, drive_dir=DRIVE_DIR, outbox_dir=OUTBOX, out=print):
    """Copy `files` to Drive, or hold them in the outbox when Drive is away.
    Returns the number of failures. Every file gets a result line."""
    failures = 0
    drive_root = os.path.dirname(drive_dir.rstrip("\\/"))
    mounted = os.path.isdir(drive_root)
    if mounted:
        os.makedirs(drive_dir, exist_ok=True)
        for held in sorted(glob.glob(os.path.join(outbox_dir, "*"))):
            name = os.path.basename(held)
            try:
                shutil.copy2(held, os.path.join(drive_dir, name))
                os.remove(held)
                out(f"SHIP OK      {name} (held in outbox) -> {drive_dir}")
            except OSError as e:
                failures += 1
                out(f"SHIP FAILED  {name} (held in outbox): {e}")
    else:
        out(f"SHIP Drive not mounted ({drive_root} missing) - holding files in "
            f"{outbox_dir}{os.sep}, they go up on the next run")

    for f in files:
        name = os.path.basename(f)
        if name.lower().endswith(NEVER_SHIP):
            failures += 1
            out(f"SHIP REFUSED {name}: the database is backed up locally and never shipped")
            continue
        if not os.path.isfile(f):
            failures += 1
            out(f"SHIP FAILED  {f}: not found")
            continue
        if mounted:
            try:
                shutil.copy2(f, os.path.join(drive_dir, name))
                out(f"SHIP OK      {name} -> {drive_dir}")
                continue
            except OSError as e:
                out(f"SHIP Drive copy failed for {name} ({e}) - trying the outbox")
        try:
            os.makedirs(outbox_dir, exist_ok=True)
            shutil.copy2(f, os.path.join(outbox_dir, name))
            out(f"SHIP HELD    {name} -> {outbox_dir}")
        except OSError as e:
            failures += 1
            out(f"SHIP FAILED  {name}: {e}")
    return failures


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stamp", required=True, help="UTC date of the run, YYYY-MM-DD")
    ap.add_argument("--drive", default=DRIVE_DIR)
    args = ap.parse_args()
    failures = 0

    export = newest_export(".")
    archived = None
    if export:
        try:
            archived = archive_export(export, ARCHIVE, args.stamp)
            print(f"ARCHIVE OK   {os.path.basename(export)} -> {archived}")
        except OSError as e:
            failures += 1
            print(f"ARCHIVE FAILED {export}: {e}")
    else:
        failures += 1
        print("ARCHIVE FAILED: no fpl_export_gw*.json in this folder")

    try:
        dest, pruned = backup_db("fpl.sqlite", BACKUP, args.stamp)
        print(f"BACKUP OK    fpl.sqlite -> {dest}"
              + (f"  (pruned {len(pruned)} older)" if pruned else ""))
    except (OSError, sqlite3.Error) as e:
        failures += 1
        print(f"BACKUP FAILED fpl.sqlite: {e}")

    files = [archived] if archived else []
    files += ["projection_log.csv",
              os.path.join("reports", f"run_{args.stamp}.log"),
              os.path.join("reports", f"fpl_{args.stamp}.txt")]
    failures += ship(files, args.drive, OUTBOX)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
