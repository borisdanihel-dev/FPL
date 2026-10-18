"""
fpl_nightly.py  -  the nightly run as GitHub Actions executes it.

    python fpl_nightly.py            # code from this folder, data from FPL_DATA_DIR
    python fpl_nightly.py --restore  # local: only the working exports, see restore_only
    python fpl_nightly.py --due      # the workflow's first step: is this run due? (S3)

The same steps as fpl_run.bat, in the same order, on any platform:

    tests  ->  sync  ->  record own / xg / minutes / bottomup  ->  report  ->  stuck check
           ->  archive  ->  checks (checks.py: the status line and reports/status.txt)

The tests run by discovery: test_fpl.py plus tests/ (RULING FAST-TRACK, item 5).

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

Code and data live apart (BUILD_PLAN.md Step 1.4): the scripts and
watchlist.txt come from this file's folder (master); every data file is read
and written in DATA_DIR, the checkout of the `data` branch - the one setting,
taken from the environment variable FPL_DATA_DIR. Each step runs with DATA_DIR
as its working folder, so fpl_sync.py and fpl_edge.py find fpl.sqlite, the
exports and projection_log.csv there. The test suite runs in the code folder.
Unset, DATA_DIR is the code folder itself (the layout before the split).
New dated exports are gzipped (fpl_export_gwN_<date>.json.gz); the older
plain .json copies are read as they are.

Standard library only. Never touches the database: fpl_sync.py owns fpl.sqlite,
and projection_log.csv is written from the export alone.
"""

import glob
import gzip
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import fpl_ship

# the suite by discovery: test_fpl.py and tests/test_<item>.py (FAST-TRACK item 5)
TEST_ARGS = ("-m", "unittest", "discover", "-v", "-p", "test*.py")
NIGHTLY_UTC = (21, 40)              # the scheduled nightly: cron "40 21 * * *"
BACKUP_CRON = "17 3 * * *"          # the backup run: only when the nightly left no status
STATUS_REL = os.path.join("reports", "status.txt")

SOURCES = ("own", "xg", "minutes", "bottomup")
EXPORTS, LOGS, REPORTS = "exports", "logs", "reports"
DATED = re.compile(r"^fpl_export_gw(\d+)_(\d{4}-\d{2}-\d{2})\.json(\.gz)?$")
DATA_ENV = "FPL_DATA_DIR"


def utc_stamp():
    """The UTC date - the date price_history uses, and fpl_run.bat's stamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _dated_bytes(path):
    if path.endswith(".gz"):
        with gzip.open(path, "rb") as fh:
            return fh.read()
    with open(path, "rb") as fh:
        return fh.read()


def restore_exports(root, say=print, refresh=False):
    """Fresh checkout: put the newest dated copy of each gameweek's export back
    in the root as fpl_export_gwN.json. A file already there is never touched -
    unless `refresh` (--restore on a local data worktree), where it is replaced
    when the newest dated copy differs, so a pull never leaves a stale working
    export behind. Returns the names written."""
    newest = {}
    for path in glob.glob(os.path.join(root, EXPORTS, "fpl_export_gw*_*.json*")):
        m = DATED.match(os.path.basename(path))
        if not m:
            continue
        # newest date first; on one date the .gz (the new layout, written later
        # than an old-layout .json that night) wins, whatever the listing order
        gw, key = int(m.group(1)), (m.group(2), bool(m.group(3)))
        if gw not in newest or key > newest[gw][0]:
            newest[gw] = (key, path)
    restored = []
    for gw in sorted(newest):
        stamp, path = newest[gw]
        dest = os.path.join(root, f"fpl_export_gw{gw}.json")
        if os.path.exists(dest):
            if not refresh:
                continue
            with open(dest, "rb") as fh:
                if fh.read() == _dated_bytes(path):
                    continue
        if path.endswith(".gz"):
            with gzip.open(path, "rb") as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out)
        else:
            shutil.copy2(path, dest)
        restored.append(os.path.basename(dest))
        say(f"RESTORED     {os.path.basename(path)} -> {os.path.basename(dest)}")
    return restored


def restore_only(data, code, say=print):
    """--restore: the local half of the data-branch layout (S1 amendment 2,
    point 2). Writes the plain working exports - untracked, ignored on the data
    branch - into the data folder from its dated copies, through the nightly's
    own restore step, and nothing else: no sync, no record, no commit.
    The data folder is FPL_DATA_DIR, else the current folder; never the code."""
    data = os.path.abspath(data)
    if os.path.normcase(data) == os.path.normcase(os.path.abspath(code)):
        say(f"RESTORE FAILED: {data} is the code folder - run it from the data folder "
            f"(cd C:\\GIT\\FPL-data) or set {DATA_ENV}")
        return 1
    if not glob.glob(os.path.join(data, EXPORTS, "fpl_export_gw*_*.json*")):
        say(f"RESTORE FAILED: no dated exports in {os.path.join(data, EXPORTS)}")
        return 1
    written = restore_exports(data, say, refresh=True)
    say(f"RESTORE OK   {len(written)} working export(s) written in {data}; "
        f"the others were already current")
    return 0


def archive_export_gz(export, archive_dir, stamp):
    """Keep tonight's export as exports/fpl_export_gwN_<stamp>.json.gz. The gzip
    header carries no name and no time, so the same export always gives the
    same bytes. Earlier days stay."""
    os.makedirs(archive_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(export))[0]
    dest = os.path.join(archive_dir, f"{base}_{stamp}.json.gz")
    with open(export, "rb") as src, open(dest, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as out:
            shutil.copyfileobj(src, out)
    return dest


def nightly(root=".", stamp=None, py=None, echo=print, data=None):
    """Run the nightly steps: code from `root`, data in `data` (default: `root`).
    Returns the exit code: 0 only when every step succeeded."""
    root = os.path.abspath(root)
    data = os.path.abspath(data or root)
    stamp = stamp or utc_stamp()
    py = py or sys.executable
    for d in (EXPORTS, LOGS, REPORTS):
        os.makedirs(os.path.join(data, d), exist_ok=True)
    log_path = os.path.join(data, LOGS, f"run_{stamp}.log")
    status_rel = os.path.join(REPORTS, "record_status.tmp")
    status = os.path.join(data, status_rel)
    report_rel = os.path.join(REPORTS, f"fpl_{stamp}.txt")
    failed = []

    with open(log_path, "a", encoding="utf-8", newline="") as log:      # append: a second run
        def say(line=""):                                    # the same day keeps the first
            log.write(line + "\n")
            log.flush()
            echo(line)

        def run(cmd, cwd):
            """One command; its output goes to the log and the console."""
            # no __pycache__ in the code or data folder from the discovered suite
            env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
            for line in r.stdout.splitlines():
                say(line)
            return r.returncode

        def step(script, *args, cwd=data):
            """One python step: `script` from the code folder, run in the data
            folder."""
            return run([py, os.path.join(root, script), *args], cwd)

        say(f"==== run {stamp} UTC, started "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC ====")
        say(f"working dir: {root}")
        say(f"data dir: {data}")
        say(f"using: {py}")

        restore_exports(data, say)

        say("running tests ...")
        tests_ok = run([py, *TEST_ARGS, "-s", root, "-t", root], root) == 0
        if tests_ok:
            say("TESTS OK")                  # read by checks.py, check 28 (the test gate)
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
                    lines = (open(status, encoding="utf-8", newline="").read().splitlines()
                             if os.path.exists(status) else [])
                    if not any(l.startswith(f"RECORD FAIL {src} ") for l in lines):
                        with open(status, "a", encoding="utf-8", newline="") as fh:
                            fh.write(f"RECORD FAIL {src} python exited with an error before "
                                     f"reporting - see the run log\n")
        else:
            record_bad = True
            say("SKIPPED --record: test suite is red, no forecasts written")
            with open(status, "a", encoding="utf-8", newline="") as fh:
                for src in SOURCES:
                    fh.write(f"RECORD FAIL {src} skipped - test suite is red\n")

        # the watch file: a chat-sized digest of the watched ids and the top
        # twelve per position, from the forecasts just recorded (item L)
        watch_rel = os.path.join(REPORTS, f"watch_{stamp}.txt")
        watchlist = os.path.join(root, "watchlist.txt")
        if os.path.exists(watchlist):
            say("writing the watch file ...")
            if step("fpl_edge.py", "--watch", watchlist, "--out", watch_rel) != 0:
                failed.append("watch")
                say("WATCH FAILED")
        else:
            say("WATCH skipped: no watchlist.txt")

        say("building report ...")
        if step("fpl_edge.py", "--diff", "--out", report_rel) != 0:
            failed.append("report")
            say("EDGE FAILED")

        # the GW stuck alarm: a gameweek not final 72 h after its last kickoff
        # turns the run red (BUILD_PLAN.md Step 2.1)
        say("checking for a stuck gameweek ...")
        if step("fpl_edge.py", "--stuck") != 0:
            failed.append("stuck")

        say("record summary:")
        if os.path.exists(status):
            for line in open(status, encoding="utf-8", newline="").read().splitlines():
                say(line)
        else:
            record_bad = True
            say("RECORD FAIL all no status was written")
        if record_bad:
            failed.append("record")

        # the dated export is tonight's point-in-time input; the workflow commits it.
        # No Drive, no outbox, no database backup: git history is the archive.
        say("archiving the export ...")
        export = fpl_ship.newest_export(data)
        if export:
            try:
                dest = archive_export_gz(export, os.path.join(data, EXPORTS), stamp)
                say(f"ARCHIVE OK   {os.path.basename(export)} -> "
                    f"{os.path.join(EXPORTS, os.path.basename(dest))}")
            except OSError as e:
                failed.append("archive")
                say(f"ARCHIVE FAILED {export}: {e}")
        else:
            failed.append("archive")
            say("ARCHIVE FAILED: no fpl_export_gw*.json in this folder")

        # the 27 checks of Step 3: the status line at the top of the report and
        # reports/status.txt; a FAIL also stops fpl_publish.py from committing
        say("running the checks ...")
        if step("checks.py", "--stamp", stamp) != 0:
            failed.append("checks")

        if failed:
            say(f"FINISHED WITH ERRORS: {', '.join(failed)}")
            return 1
        say(f"Done. Report: {report_rel}")
        return 0


def last_nightly_slot(now):
    """The latest scheduled nightly time (21:40 UTC) at or before `now`."""
    slot = now.replace(hour=NIGHTLY_UTC[0], minute=NIGHTLY_UTC[1], second=0, microsecond=0)
    return slot if slot <= now else slot - timedelta(days=1)


def backup_due(data, now, schedule):
    """(due, why) for a run of the workflow (ruling S3, point 4). Only the
    backup cron can be skipped: it is due when the nightly of the last slot
    left no status.txt - none at all, or one generated before that slot. A
    run of the nightly's own cron, or a dispatch, is always due. Reads one
    file and writes nothing."""
    import checks
    if schedule != BACKUP_CRON:
        return True, "not the backup cron"
    path = os.path.join(data, STATUS_REL)
    slot = last_nightly_slot(now)
    if not os.path.exists(path):
        return True, f"no {STATUS_REL}: the nightly of {slot:%Y-%m-%d %H:%M} UTC left none"
    with open(path, encoding="utf-8", newline="") as fh:
        when = checks.status_time(fh.readline())
    if when is None or when < slot:
        return True, (f"{STATUS_REL} is from {when:%Y-%m-%d %H:%M} UTC, before the "
                      f"{slot:%Y-%m-%d %H:%M} UTC nightly" if when else
                      f"{STATUS_REL} has no generated time")
    return False, f"{STATUS_REL} from {when:%Y-%m-%d %H:%M} UTC exists: the nightly ran"


def due_main(data, env=None, now=None, say=print):
    """--due: print whether this run is due and, on the runner, write
    run=true|false to GITHUB_OUTPUT for the later steps. Exit 0 either way."""
    env = os.environ if env is None else env
    due, why = backup_due(data, now or datetime.now(timezone.utc), env.get("FPL_SCHEDULE", ""))
    say(("DUE          " if due else "NOT DUE      backup run skipped: ") + why)
    out = env.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8", newline="") as fh:
            fh.write(f"run={'true' if due else 'false'}\n")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    here = os.path.dirname(os.path.abspath(__file__))
    if argv == ["--restore"]:
        sys.exit(restore_only(os.environ.get(DATA_ENV) or os.getcwd(), here))
    if argv == ["--due"]:
        sys.exit(due_main(os.environ.get(DATA_ENV) or os.getcwd()))
    if argv:
        sys.exit(f"usage: fpl_nightly.py [--restore | --due]  (got {' '.join(argv)})")
    sys.exit(nightly(root=here, data=os.environ.get(DATA_ENV) or None))


if __name__ == "__main__":
    main()
