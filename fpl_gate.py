"""
fpl_gate.py  -  the data-safety gate before every runner commit (BUILD_PLAN.md
Step 1, item D1). The price history and the frozen forecasts exist nowhere
else, so a bad night must commit nothing rather than overwrite good data.

    python fpl_gate.py DATA_DIR              exit 0: safe to commit
                                             exit 1: commit nothing

compares DATA_DIR with its last commit (git show HEAD:...):
  * fpl.sqlite: PRAGMA integrity_check returns ok;
  * no table of the last commit is missing;
  * a new table is in EXPECTED_TABLES (a schema change updates that list in
    the same commit; there is no override flag);
  * no table in GROW_ONLY has fewer rows than in the last commit;
  * projection_log.csv: for every gameweek whose deadline has passed
    (events.deadline_time in fpl.sqlite), the rows are exactly those of the
    last commit - none missing, changed or added;
  * odds/: every odds file of the last commit is still there, byte-identical
    (append-only; RULING W1 odds storage).
On a pass it writes DATA_DIR/fpl.sql, a text dump of the whole database
(sqlite3.Connection.iterdump), committed alongside the binary. On a fail it
writes nothing.

    python fpl_gate.py --secrets DATA_DIR    exit 1 when a staged file holds
                                             apiKey=, api_key= or apikey= (any
                                             case), or the ODDS_API_KEY value
                                             wherever that variable is set;
                                             .gz files are read decompressed

A secret hit fails loudly (a GitHub error annotation on the runner): that
night commits nothing, which is accepted over any risk of a leak. Neither mode
ever prints a key value: a hit names the file only.

Standard library only.
"""

import argparse
import collections
import csv
import gzip
import io
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import zlib
from datetime import datetime, timezone

DB, DUMP, LOG = "fpl.sqlite", "fpl.sql", "projection_log.csv"
ODDS = "odds"               # the Odds API snapshots, one gzip file a night, append-only (W1)

# Every table fpl_sync.py creates. A table that is new since the last commit
# passes only if it is listed here; a schema change updates this list in the
# same commit (test_fpl.py checks the two agree).
EXPECTED_TABLES = frozenset({
    "automatic_subs", "chips", "entries", "entry_gw", "events", "fixtures", "picks",
    "player_gw", "player_history", "players", "price_history", "standings", "teams",
    "transfers"})

# Tables that only ever grow: fewer rows than the last commit fails the gate.
# A table qualifies only if fpl_sync.py never deletes from it. Today that is
# every table: fpl_sync.py has no DELETE, DROP, TRUNCATE or VACUUM, and every
# write is INSERT OR REPLACE on a table whose only uniqueness constraint is its
# primary key, which replaces at most the one row it collides with (test_fpl.py
# checks both facts against the source).
GROW_ONLY = tuple(sorted(EXPECTED_TABLES))

# Key-shaped strings that must never be committed, matched in any case.
KEY_PATTERNS = (b"apikey=", b"api_key=")


def _ro(path):
    """A read-only connection: the gate never writes to the database it checks."""
    return sqlite3.connect(pathlib.Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def table_counts(path):
    """{table: rows} for every table in the database at `path`."""
    con = _ro(path)
    try:
        names = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {n: con.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in names}
    finally:
        con.close()


def check(db, prev):
    """Failures (a list of strings; empty = pass) for `db` against `prev`, the
    database in the last commit. `prev` None means there is nothing to compare
    against, which is itself a failure: the runner always has a last commit."""
    if not os.path.exists(db):
        return [f"{DB} is missing"]
    try:
        con = _ro(db)
        try:
            result = [r[0] for r in con.execute("PRAGMA integrity_check")]
        finally:
            con.close()
        if result != ["ok"]:
            return [f"PRAGMA integrity_check: {'; '.join(map(str, result[:5]))}"]
        now = table_counts(db)
    except sqlite3.DatabaseError as e:
        return [f"{DB} is not a readable database: {e}"]
    if prev is None:
        return [f"no {DB} in the last commit to compare against"]
    before = table_counts(prev)
    fails = []
    gone = sorted(set(before) - set(now))
    if gone:
        fails.append(f"tables missing since the last commit: {gone}")
    unexpected = sorted(set(now) - set(before) - EXPECTED_TABLES)
    if unexpected:
        fails.append(f"new tables not in EXPECTED_TABLES: {unexpected}")
    for t in GROW_ONLY:                       # a table that vanished is in `gone`
        if t in now and now[t] < before.get(t, 0):
            fails.append(f"{t} rows fell from {before[t]} to {now[t]}")
    return fails


def deadlines(db):
    """{event id as text: deadline as an aware UTC datetime} from events."""
    con = _ro(db)
    try:
        rows = con.execute("SELECT id, deadline_time FROM events").fetchall()
    finally:
        con.close()
    return {str(i): datetime.fromisoformat(d.replace("Z", "+00:00"))
            for i, d in rows if d}


def _log_rows(text):
    """{event: Counter of whole rows} from projection_log.csv text (CRLF or LF)."""
    rows = [r for r in csv.reader(io.StringIO(text, newline="")) if r]
    if not rows:
        return {}
    col = rows[0].index("event")
    by = collections.defaultdict(collections.Counter)
    for r in rows[1:]:
        by[r[col]][tuple(r)] += 1
    return by


def check_log(now_text, prev_text, deadline_of, now):
    """Failures for projection_log.csv: every gameweek whose deadline has
    passed must hold exactly the rows of the last commit. Forecasts are frozen
    at the deadline; before it, --record may rewrite a gameweek freely."""
    if prev_text is None:
        return [f"no {LOG} in the last commit to compare against"]
    if now_text is None:
        return [f"{LOG} is missing"]
    before, after = _log_rows(prev_text), _log_rows(now_text)
    fails = []
    for event in sorted(set(before) | set(after), key=lambda e: (len(e), e)):
        deadline = deadline_of.get(event)
        if deadline is None:
            fails.append(f"{LOG}: GW{event} has no deadline in events - cannot check it")
            continue
        if deadline > now:
            continue
        b, a = before.get(event, collections.Counter()), after.get(event, collections.Counter())
        if a != b:
            gone, new = sum((b - a).values()), sum((a - b).values())
            fails.append(f"{LOG}: GW{event} is past its deadline and its rows changed "
                         f"({gone} missing or changed, {new} added)")
    return fails


def check_odds(data_dir):
    """Failures for odds/: every file there in the last commit must still be
    present and byte-identical. A new file is fine; a rewritten or deleted one
    fails (append-only; RULING W1 odds storage)."""
    r = subprocess.run(["git", "-C", data_dir, "ls-tree", "-r", "-z", "--name-only", "HEAD", "--",
                        ODDS + "/"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    fails = []
    for name in (n for n in r.stdout.decode("utf-8").split("\0") if n):
        path = os.path.join(data_dir, name)
        if not os.path.isfile(path):
            fails.append(f"{name} was deleted - odds files are append-only")
            continue
        with open(path, "rb") as fh:
            body = fh.read()
        if body != (_git_show(data_dir, name) or b""):
            fails.append(f"{name} was rewritten - odds files are append-only")
    return fails


def _git_show(data_dir, name):
    r = subprocess.run(["git", "-C", data_dir, "show", f"HEAD:{name}"],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return r.stdout if r.returncode == 0 and r.stdout else None


def previous_db(data_dir, tmp):
    """HEAD:fpl.sqlite written to a file in `tmp`, or None when HEAD has none."""
    body = _git_show(data_dir, DB)
    if body is None:
        return None
    path = os.path.join(tmp, "previous.sqlite")
    with open(path, "wb") as fh:
        fh.write(body)
    return path


def write_dump(db, out):
    """The whole database as SQL text, written via a temp file and a rename.
    Values are written exactly as stored: the file is LF-only and must be
    committed without end-of-line conversion (.gitattributes: fpl.sql -text)."""
    con = _ro(db)
    tmp = out + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as fh:
            for line in con.iterdump():
                fh.write(line + "\n")
    finally:
        con.close()
    os.replace(tmp, out)
    return out


def secret_hit(name, body, key):
    """True when one file's bytes hold a KEY_PATTERNS string (any case) or
    `key` (when set). A .gz file is read decompressed as well as raw; one that
    cannot be decompressed counts as a hit, since it cannot be cleared. Used
    by the staged scan below and by checks.py check 23 before the commit."""
    value = key.encode("utf-8") if key else None
    bodies = [body]
    if name.lower().endswith(".gz"):
        try:
            bodies.append(gzip.decompress(body))
        except (OSError, EOFError, zlib.error):
            return True
    return any(any(p in b.lower() for p in KEY_PATTERNS) or bool(value and value in b)
               for b in bodies)


def staged_secrets(data_dir, key):
    """Staged files in `data_dir` that secret_hit() flags. Returns their
    names, never what matched."""
    r = subprocess.run(["git", "-C", data_dir, "diff", "--cached", "--name-only", "-z",
                        "--diff-filter=ACMR"], stdout=subprocess.PIPE, check=True)
    hits = []
    for name in (n for n in r.stdout.decode("utf-8").split("\0") if n):
        path = os.path.join(data_dir, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as fh:
            if secret_hit(name, fh.read(), key):
                hits.append(name)
    return hits


def main(argv=None):
    ap = argparse.ArgumentParser(description="data-safety gate before a runner commit")
    ap.add_argument("data_dir")
    ap.add_argument("--secrets", action="store_true",
                    help="scan the staged files for a key pattern or the key value")
    a = ap.parse_args(argv)

    if a.secrets:
        hits = staged_secrets(a.data_dir, os.environ.get("ODDS_API_KEY", ""))
        for name in hits:
            print(f"SECRET FAIL  {name}: holds a key pattern or the key value - commit nothing")
        if hits:
            print("SECRET FAIL  NOTHING COMMITTED TONIGHT: remove the key from the file(s) "
                  "above, then rerun the workflow")
            if os.environ.get("GITHUB_ACTIONS") == "true":
                print(f"::error title=Secret scan blocked the commit::{len(hits)} staged "
                      f"file(s) hold a key pattern or the key value; nothing was committed")
        else:
            print("SECRETS OK   no staged file holds a key pattern or the key value")
        return 1 if hits else 0

    db = os.path.join(a.data_dir, DB)
    with tempfile.TemporaryDirectory() as tmp:
        fails = check(db, previous_db(a.data_dir, tmp))
    if not fails:
        log_path = os.path.join(a.data_dir, LOG)
        now_text = None
        if os.path.exists(log_path):
            with open(log_path, encoding="utf-8", newline="") as fh:
                now_text = fh.read()
        prev = _git_show(a.data_dir, LOG)
        fails = check_log(now_text, prev.decode("utf-8") if prev is not None else None,
                          deadlines(db), datetime.now(timezone.utc))
    if not fails:
        fails = check_odds(a.data_dir)
    for f in fails:
        print(f"GATE FAIL    {f}")
    if fails:
        print("GATE FAIL    commit nothing")
        return 1
    counts = table_counts(db)
    write_dump(db, os.path.join(a.data_dir, DUMP))
    print(f"GATE OK      integrity ok, {len(counts)} tables, "
          f"price_history {counts.get('price_history', 0)} rows, frozen forecasts "
          f"unchanged; {DUMP} written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
