"""
fpl_nightly.py  -  the nightly run as GitHub Actions executes it.

    python fpl_nightly.py            # in the repository root

The same steps as fpl_run.bat, in the same order, on any platform:

    tests  ->  sync  ->  record own / xg / minutes / bottomup  ->  report

with the Windows paths gone and the Google Drive shipping replaced by files the
workflow commits back to the repository:

    logs/run_<UTC date>.log                    everything every step printed
    reports/fpl_<UTC date>.txt                 the report (fpl_edge.py --diff --out)
    reports/watch_<UTC date>.txt               the watch file for watchlist.txt (item L)
    exports/fpl_export_gwN_<UTC date>.json     tonight's export, point-in-time
    projection_log.csv                         written by fpl_edge.py --record only

Rules carried over from fpl_run.bat:
* A red test suite blocks --record. Forecasts freeze at the deadline and cannot
  be regenerated, so one bad set contaminates the calibration table for good.
* One status line per source (RECORD OK / RECORD FAIL); a crash that wrote no
  line of its own still gets one.
* A failed step never stops the later ones: the report is still built and the
  export still archived, so the run log explains itself.

One rule is stricter here: ANY failure - tests, sync, a record, the report, the
archive - makes the run exit 1, so the workflow goes red and GitHub sends mail.
fpl_run.bat stays the manual local path. For the same export both paths write
the same forecasts and the same report (tested in test_fpl.py).

A runner starts from a fresh checkout, where the working export
(fpl_export_gwN.json, untracked) does not exist. Step 0 restores it from the
newest dated copy per gameweek in exports/, so --diff finds the previous
gameweek and a failed sync falls back to yesterday's data - what the local
folder gives fpl_run.bat for free.

Standard library only. Never touches the database: fpl_sync.py owns fpl.sqlite,
and projection_log.csv is written from the export alone.
"""

import glob
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import fpl_ship

SOURCES = ("own", "xg", "minutes", "bottomup")
EXPORTS, LOGS, REPORTS = "exports", "logs", "reports"
DATED = re.compile(r"^fpl_export_gw(\d+)_(\d{4}-\d{2}-\d{2})\.json$")


def utc_stamp():
    """The UTC date - the date price_history uses, and fpl_run.bat's stamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def restore_exports(root, say=print):
    """Fresh checkout: put the newest dated copy of each gameweek's export back
    in the root as fpl_export_gwN.json. A file already there is never touched.
    Returns the names restored."""
    newest = {}
    for path in glob.glob(os.path.join(root, EXPORTS, "fpl_export_gw*_*.json")):
        m = DATED.match(os.path.basename(path))
        if m and (int(m.group(1)) not in newest or m.group(2) > newest[int(m.group(1))][0]):
            newest[int(m.group(1))] = (m.group(2), path)
    restored = []
    for gw in sorted(newest):
        stamp, path = newest[gw]
        dest = os.path.join(root, f"fpl_export_gw{gw}.json")
        if os.path.exists(dest):
            continue
        shutil.copy2(path, dest)
        restored.append(os.path.basename(dest))
        say(f"RESTORED     {os.path.basename(path)} -> {os.path.basename(dest)}")
    return restored


def nightly(root=".", stamp=None, py=None, echo=print):
    """Run the nightly steps in `root`. Returns the exit code: 0 only when
    every step succeeded."""
    root = os.path.abspath(root)
    stamp = stamp or utc_stamp()
    py = py or sys.executable
    for d in (EXPORTS, LOGS, REPORTS):
        os.makedirs(os.path.join(root, d), exist_ok=True)
    log_path = os.path.join(root, LOGS, f"run_{stamp}.log")
    status_rel = os.path.join(REPORTS, "record_status.tmp")
    status = os.path.join(root, status_rel)
    report_rel = os.path.join(REPORTS, f"fpl_{stamp}.txt")
    failed = []

    with open(log_path, "a", encoding="utf-8") as log:      # append: a second run
        def say(line=""):                                    # the same day keeps the first
            log.write(line + "\n")
            log.flush()
            echo(line)

        def step(*args):
            """One python step in `root`; its output goes to the log and the console."""
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            r = subprocess.run([py, *args], cwd=root, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
            for line in r.stdout.splitlines():
                say(line)
            return r.returncode

        say(f"==== run {stamp} UTC, started "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC ====")
        say(f"working dir: {root}")
        say(f"using: {py}")

        restore_exports(root, say)

        say("running tests ...")
        tests_ok = step("test_fpl.py") == 0
        if not tests_ok:
            failed.append("tests")
            say(f"TESTS FAILED - see {os.path.join(LOGS, os.path.basename(log_path))}")

        say("syncing FPL API ...")
        if step("fpl_sync.py") != 0:
            failed.append("sync")
            say("SYNC FAILED - continuing with existing data")

        # one status line per source, written by fpl_edge.py and summarised below
        record_bad = False
        if os.path.exists(status):
            os.remove(status)
        if tests_ok:
            say("recording forecasts for next GW ...")
            for src in SOURCES:
                code = step("fpl_edge.py", "--record", "--source", src, "--status", status_rel)
                if code != 0:
                    record_bad = True
                    lines = (open(status, encoding="utf-8").read().splitlines()
                             if os.path.exists(status) else [])
                    if not any(l.startswith(f"RECORD FAIL {src} ") for l in lines):
                        with open(status, "a", encoding="utf-8") as fh:
                            fh.write(f"RECORD FAIL {src} python exited with an error before "
                                     f"reporting - see the run log\n")
        else:
            record_bad = True
            say("SKIPPED --record: test suite is red, no forecasts written")
            with open(status, "a", encoding="utf-8") as fh:
                for src in SOURCES:
                    fh.write(f"RECORD FAIL {src} skipped - test suite is red\n")

        # the watch file: a chat-sized digest of the watched ids and the top
        # twelve per position, from the forecasts just recorded (item L)
        watch_rel = os.path.join(REPORTS, f"watch_{stamp}.txt")
        if os.path.exists(os.path.join(root, "watchlist.txt")):
            say("writing the watch file ...")
            if step("fpl_edge.py", "--watch", "watchlist.txt", "--out", watch_rel) != 0:
                failed.append("watch")
                say("WATCH FAILED")
        else:
            say("WATCH skipped: no watchlist.txt")

        say("building report ...")
        if step("fpl_edge.py", "--diff", "--out", report_rel) != 0:
            failed.append("report")
            say("EDGE FAILED")

        say("record summary:")
        if os.path.exists(status):
            for line in open(status, encoding="utf-8").read().splitlines():
                say(line)
        else:
            record_bad = True
            say("RECORD FAIL all no status was written")
        if record_bad:
            failed.append("record")

        # the dated export is tonight's point-in-time input; the workflow commits it.
        # No Drive, no outbox, no database backup: git history is the archive.
        say("archiving the export ...")
        export = fpl_ship.newest_export(root)
        if export:
            try:
                dest = fpl_ship.archive_export(export, os.path.join(root, EXPORTS), stamp)
                say(f"ARCHIVE OK   {os.path.basename(export)} -> "
                    f"{os.path.join(EXPORTS, os.path.basename(dest))}")
            except OSError as e:
                failed.append("archive")
                say(f"ARCHIVE FAILED {export}: {e}")
        else:
            failed.append("archive")
            say("ARCHIVE FAILED: no fpl_export_gw*.json in this folder")

        if failed:
            say(f"FINISHED WITH ERRORS: {', '.join(failed)}")
            return 1
        say(f"Done. Report: {report_rel}")
        return 0


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    sys.exit(nightly())


if __name__ == "__main__":
    main()
