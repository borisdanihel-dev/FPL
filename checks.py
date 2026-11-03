"""
checks.py  -  the nightly checks, the status line and reports/status.txt
(BUILD_PLAN.md Step 3, item D3; ruling S3).

    python checks.py --stamp YYYY-MM-DD        run in DATA_DIR by fpl_nightly.py

Reads the data folder (fpl.sqlite, projection_log.csv, the working export),
its last commit (git show HEAD:...), tonight's run log logs/run_<stamp>.log
(the run's start time, the test result, the sync's "SYNC STATS" line and the
record summary) and the newest run log of the last commit. Runs the 27 checks
of Step 3 and two more, 28 "test gate" and 29 "record" (ruling S3 amendment 1,
point 3: the status line never reads OK on a night whose suite or record
failed), and writes:

  reports/status.txt   the status line, then one line per check. A dry run
                       writes reports/status_dryrun.txt instead and never
                       status.txt (ruling S3, point 7).
  the status line at the top of tonight's report (reports/fpl_<stamp>.txt).

    STATUS OK|WARN|FAIL | generated <UTC> | next deadline <GW, UTC and Prague>
    | checks n/N | repo <MB>

n/N counts the checks that ran (a SKIP - not applicable tonight, or manual -
is outside N) and of those the ones that are OK. Exit 1 when any check FAILs:
fpl_publish.py then commits nothing (Step 3.1: FAIL = no data commit and a red
run). WARN goes into the status line and the run stays green.

Which breach is a FAIL and which a WARN is the table of Step 3; where the
table names neither, a breach is a FAIL when it means the night's API answer
or the stored data cannot be trusted (it would be committed wrongly), and a
WARN when the data is sound but someone should look (SEVERITY below). A check
that raises is a WARN that says so: a bug in a check never blocks a commit the
gate would let through.

Standard library only.
"""

import argparse
import collections
import csv
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone

OK, WARN, FAIL, SKIP = "OK", "WARN", "FAIL", "SKIP"
DB, LOG = "fpl.sqlite", "projection_log.csv"
REPORTS, LOGS = "reports", "logs"
STATUS, STATUS_DRY = "status.txt", "status_dryrun.txt"
STATS_PREFIX = "SYNC STATS "             # printed by fpl_sync.py at the end of every sync
PRAGUE = "Europe/Prague"
REPO_WARN_MB, REPO_FAIL_MB = 500, 900
BIG_FILE_MB = 50            # GitHub warns at 50 MB a file, refuses 100 MB (W1 odds storage, point 4)
API = "https://api.github.com"
_urlopen = urllib.request.urlopen

# the 27 checks of Step 3, in its order
NAMES = {
    1: "core endpoints", 2: "element-summary failures", 3: "player count", 4: "teams",
    5: "fixtures", 6: "fixtures per gameweek", 7: "team appearances per gameweek",
    8: "required fields", 9: "element key set", 10: "distinct prices", 11: "price step",
    12: "price changes", 13: "chance of playing 0", 14: "position changes",
    15: "SQLite integrity", 16: "price-history rows", 17: "price-date gaps",
    18: "projection-log growth", 19: "projection-log duplicate keys",
    20: "forecast rows after the deadline", 21: "stuck gameweek",
    22: "manager score reconciliation", 23: "secret in the files to commit",
    24: "repo size", 25: "run duration", 26: "heartbeat", 27: "workflow state",
    28: "test gate", 29: "record", 30: "odds snapshot", 31: "report sections"}

# what a breach is, check by check: the table's own word where it gives one
SEVERITY = {1: FAIL, 2: FAIL, 3: FAIL, 4: FAIL, 5: FAIL, 6: WARN, 7: WARN, 8: FAIL, 9: WARN,
            10: FAIL, 11: FAIL, 12: WARN, 13: FAIL, 14: WARN, 15: FAIL, 16: FAIL, 17: WARN,
            18: FAIL, 19: WARN, 20: FAIL, 21: WARN, 22: WARN, 23: FAIL, 24: FAIL, 25: WARN,
            26: WARN, 27: SKIP, 28: FAIL, 29: FAIL, 30: WARN, 31: WARN}
SOURCES = ("own", "xg", "minutes", "bottomup", "fpl_ep", "bottomup_lambda")     # as fpl_nightly.SOURCES
SKIPPABLE = ("fpl_ep", "bottomup_lambda")      # a RECORD SKIP is a WARN (W1: no ep_next; W2: no odds snapshot)
CREDITS_WARN = 60           # Odds API credits left below this: check 30 WARNs (W1 decisions)
CREDIT_HEADERS = ("x-requests-used", "x-requests-remaining", "x-requests-last")   # in the ODDS OK line's order

Result = collections.namedtuple("Result", "n name level detail")


class Ctx:
    """Everything the checks read; built by load(), or by a test."""

    def __init__(self, **kw):
        self.db = self.prev = self.stats = self.prev_stats = self.export = None
        self.log, self.prev_log = [], None
        self.now = datetime.now(timezone.utc)
        self.started = self.prev_status = self.repo_kb = None
        self.run_log = ""                     # tonight's block of the run log
        self.repo_why = "not measured"
        self.changed = []                     # [(name, bytes)] the files the commit would add
        self.big_files = []                   # [(name, size)] data files over BIG_FILE_MB
        self.key = ""
        self.known_gaps = {}
        self.__dict__.update(kw)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _q(con, sql, args=()):
    return con.execute(sql, args).fetchall() if con is not None else []


def _tonight_players(con):
    """[(id, position, now_cost, chance)] of the players the last sync wrote."""
    return _q(con, "SELECT id, position, now_cost, chance_next_round FROM players "
                   "WHERE updated_at = (SELECT MAX(updated_at) FROM players)")


def _price_steps(con):
    """[(player, now, before, nights)] for the newest price date against each
    player's previous snapshot."""
    last = _q(con, "SELECT MAX(date) FROM price_history")
    if not last or last[0][0] is None:
        return None, []
    day = last[0][0]
    rows = _q(con, """SELECT p.player_id, p.now_cost, q.now_cost,
                             CAST(julianday(p.date) - julianday(q.date) AS INTEGER)
                      FROM price_history p JOIN price_history q ON q.player_id = p.player_id
                       AND q.date = (SELECT MAX(date) FROM price_history
                                     WHERE player_id = p.player_id AND date < p.date)
                      WHERE p.date = ?""", (day,))
    return day, rows


def _short(items, n=5):
    items = list(items)
    return ", ".join(map(str, items[:n])) + (f" (+{len(items) - n} more)" if len(items) > n else "")


def _row_key(r):
    return tuple(r.get(k) for k in ("made_at", "source", "event", "player_id", "web_name", "predicted"))


def _deadlines(con):
    out = {}
    for i, d in _q(con, "SELECT id, deadline_time FROM events"):
        if d:
            out[str(i)] = datetime.fromisoformat(d.replace("Z", "+00:00"))
    return out


# ---------------------------------------------------------------------------
# the checks: each returns (level, detail); the level of a breach is SEVERITY
# ---------------------------------------------------------------------------

def c01(x):
    if x.stats is None:
        return FAIL, "no SYNC STATS line in tonight's run log: the sync did not run to its end"
    final = {}
    for path, status in x.stats.get("calls", []):
        final[path] = status
    groups = {"bootstrap": [p for p in final if p.startswith("bootstrap-static")],
              "fixtures": [p for p in final if p.startswith("fixtures")],
              "live": [p for p in final if re.match(r"event/\d+/live", p)],
              "standings": [p for p in final if p.startswith("leagues-classic/")]}
    bad = []
    for name, paths in groups.items():
        if not paths and name != "live":      # no live call when every gameweek is stored and final
            bad.append(f"{name} never called")
        bad += [f"{p} {final[p]}" for p in paths if final[p] != 200]
    if bad:
        return FAIL, _short(bad)
    n = sum(len(v) for v in groups.values())
    return OK, f"{n} core calls, all HTTP 200"


def c02(x):
    if x.stats is None:
        return FAIL, "no SYNC STATS"
    calls = [s for p, s in x.stats.get("calls", []) if p.startswith("element-summary/")]
    bad = sum(1 for s in calls if s != 200)
    if not calls:
        return OK, "no element-summary calls tonight (the nightly sync makes none)"
    if bad > 0.02 * len(calls):
        return FAIL, f"{bad} of {len(calls)} failed (> 2%)"
    return OK, f"{bad} of {len(calls)} failed"


def c03(x):
    if x.stats is None or x.stats.get("elements") is None:
        return FAIL, "no element count in SYNC STATS"
    n = x.stats["elements"]
    if not 550 <= n <= 900:
        return FAIL, f"{n} players, outside 550-900"
    before = _q(x.prev, "SELECT COUNT(*) FROM players WHERE updated_at = "
                        "(SELECT MAX(updated_at) FROM players)")
    prev_n = before[0][0] if before else None
    if prev_n and abs(n - prev_n) > 0.05 * prev_n:
        return FAIL, f"{n} players against {prev_n} last night (more than 5% apart)"
    known = {i for (i,) in _q(x.prev, "SELECT id FROM players")}
    new = sorted(set(x.stats.get("element_ids", [])) - known) if known else []
    if new:
        return WARN, f"{n} players; {len(new)} new id(s): {_short(new)}"
    return OK, f"{n} players" + (f" ({prev_n} last night)" if prev_n else "")


def c04(x):
    n = (x.stats or {}).get("teams")
    return (OK, "20 teams") if n == 20 else (FAIL, f"{n} teams, not 20")


def c05(x):
    n = (x.stats or {}).get("fixtures")
    return (OK, "380 fixtures") if n == 380 else (FAIL, f"{n} fixtures, not 380")


def c06(x):
    per = collections.Counter(e for (e,) in _q(x.db, "SELECT event FROM fixtures"))
    odd = [f"GW{e} {per[e]}" for e in range(1, 39) if per.get(e, 0) != 10]
    if per.get(None):
        odd.append(f"{per[None]} without a gameweek (postponed, not yet moved)")
    if odd:
        return WARN, "not 10: " + _short(odd, 8) + " (postponement, double or blank)"
    return OK, "10 in each of GW1-38"


def c07(x):
    per = collections.defaultdict(collections.Counter)
    n_fx = collections.Counter()
    for e, h, a in _q(x.db, "SELECT event, team_h, team_a FROM fixtures WHERE event IS NOT NULL"):
        per[e][h] += 1
        per[e][a] += 1
        n_fx[e] += 1
    teams = [t for (t,) in _q(x.db, "SELECT id FROM teams")]
    bad = []
    for e in sorted(per):
        if n_fx[e] != 10:
            continue                       # flagged by check 6: a blank or a double
        off = [t for t in teams if per[e][t] != 1]
        if off:
            bad.append(f"GW{e} teams {_short(off, 4)}")
    if bad:
        return WARN, "a 10-fixture gameweek where a team does not play exactly once: " + _short(bad)
    return OK, "every team once in every 10-fixture gameweek"


def c08(x):
    if x.stats is None or "field_problems" not in x.stats:
        return FAIL, "no field report in SYNC STATS"
    bad = x.stats["field_problems"]
    if bad:
        return FAIL, f"{len(bad)} missing or mistyped: {_short(bad)}"
    return OK, "every required element and event field present and typed"


def c09(x):
    keys = (x.stats or {}).get("element_keys")
    before = (x.prev_stats or {}).get("element_keys")
    if keys is None or before is None:
        return SKIP, "no earlier SYNC STATS to compare with"
    new, gone = sorted(set(keys) - set(before)), sorted(set(before) - set(keys))
    if new or gone:
        return WARN, f"new keys {new or '-'}; gone {gone or '-'}"
    return OK, f"{len(keys)} keys, unchanged"


def c10(x):
    n = len({p[2] for p in _tonight_players(x.db)})
    return (OK, f"{n} distinct prices") if n >= 20 else (FAIL, f"only {n} distinct prices")


def c11(x):
    day, rows = _price_steps(x.db)
    if day is None:
        return FAIL, "no price history"
    bad = [f"{p}: {b}->{n} in {k} night(s)" for p, n, b, k in rows if abs(n - b) > max(k, 1)]
    if bad:
        return FAIL, f"{len(bad)} step(s) above 0.1 a night: {_short(bad)}"
    return OK, f"{len(rows)} players against their previous snapshot, every step within 0.1 a night"


def c12(x):
    day, rows = _price_steps(x.db)
    n = sum(1 for _, now, before, _ in rows if now != before)
    return (OK, f"{n} price changes") if n <= 60 else (WARN, f"{n} price changes (> 60)")


def c13(x):
    rows = _tonight_players(x.db)
    if not rows:
        return FAIL, "no players"
    zero = sum(1 for r in rows if r[3] == 0)
    share = zero / len(rows)
    if share >= 0.40:
        return FAIL, f"{zero} of {len(rows)} ({share:.0%}) at chance 0"
    return OK, f"{zero} of {len(rows)} ({share:.0%}) at chance 0"


def c14(x):
    before = dict(_q(x.prev, "SELECT id, position FROM players"))
    moved = [f"{i}: {before[i]}->{pos}" for i, pos, _, _ in _tonight_players(x.db)
             if i in before and before[i] != pos]
    return (WARN, f"{len(moved)} moved: {_short(moved)}") if moved else (OK, "no position changes")


def c15(x):
    if x.db is None:
        return FAIL, f"no {DB}"
    res = [r[0] for r in _q(x.db, "PRAGMA integrity_check")]
    return (OK, "ok") if res == ["ok"] else (FAIL, "; ".join(map(str, res[:3])))


def c16(x):
    now = _q(x.db, "SELECT COUNT(*) FROM price_history")[0][0] if x.db is not None else 0
    if x.prev is None:
        return SKIP, f"{now} rows; no last commit to compare with"
    before = _q(x.prev, "SELECT COUNT(*) FROM price_history")[0][0]
    if now < before:
        return FAIL, f"{before} -> {now} rows"
    day = _q(x.db, "SELECT MAX(date) FROM price_history")[0][0]
    seen = _q(x.prev, "SELECT 1 FROM price_history WHERE date = ? LIMIT 1", (day,))
    expect = 0 if seen else (x.stats or {}).get("elements") or 0
    added = now - before
    if abs(added - expect) > max(5, 0.05 * expect):
        return WARN, f"{before} -> {now} rows: +{added}, expected about +{expect}"
    return OK, f"{before} -> {now} rows (+{added})"


def c17(x):
    import fpl_sync
    dates = [d for (d,) in _q(x.db, "SELECT DISTINCT date FROM price_history")]
    gaps = [g for g in fpl_sync.missing_dates(dates) if g not in x.known_gaps]
    return (WARN, f"{len(gaps)} day(s) without a snapshot: {_short(gaps)}") if gaps \
        else (OK, f"no gap outside the {len(x.known_gaps)} known ones")


def _added(x):
    if x.prev_log is None:
        return None
    left = collections.Counter(_row_key(r) for r in x.prev_log)
    out = []
    for r in x.log:
        k = _row_key(r)
        if left[k]:
            left[k] -= 1
        else:
            out.append(r)
    return out


def c18(x):
    added = _added(x)
    if added is None:
        return SKIP, "no last commit's log to compare with"
    n = (x.stats or {}).get("elements")
    if not n:
        return FAIL, "no player count to measure the growth against"
    per = collections.Counter(r["source"] for r in added)
    over = [f"{s} +{c}" for s, c in sorted(per.items()) if c > 1.2 * n]
    if over:
        return FAIL, f"more than 1.2 x {n} new rows: {_short(over)}"
    return OK, "new rows " + (", ".join(f"{s} +{c}" for s, c in sorted(per.items())) or "none")


def c19(x):
    import fpl_edge
    dups = fpl_edge.duplicate_keys(x.log)
    return (WARN, f"{len(dups)} natural keys held twice or more") if dups else (OK, "0 duplicate keys")


def c20(x):
    deadline = _deadlines(x.db)
    added = _added(x) or []
    new_ids = {id(r) for r in added}
    late_new, late_old = [], []
    for r in x.log:
        dl = deadline.get(str(r["event"]))
        if dl is not None and datetime.fromisoformat(r["made_at"]) >= dl:
            (late_new if id(r) in new_ids else late_old).append(r)
    if late_new:
        return FAIL, f"{len(late_new)} new row(s) made at or after their deadline"
    if late_old:
        return WARN, f"{len(late_old)} committed row(s) made at or after their deadline"
    return OK, f"0 of {len(x.log)} rows at or after their deadline"


def c21(x):
    if x.export is None:
        return SKIP, "no export"
    import fpl_edge
    stuck = fpl_edge.stuck_gameweeks(x.export, x.now)
    if stuck:
        return WARN, "; ".join(f"GW{e} not final {h:.0f} h after its last kickoff" for e, h, _ in stuck)
    return OK, "none"


def entry_points(con, entry, event):
    """(computed, FPL's) points of one entry in one gameweek: player points x
    the multipliers after FPL's automatic substitutions (its stored list),
    the captaincy passing to the vice-captain when the captain plays 0
    minutes, and a bench boost counting the bench. None when the picks or the
    stored substitutions are missing."""
    picks = _q(con, """SELECT p.player_id, p.position, p.multiplier, p.is_captain, p.is_vice,
                              COALESCE(g.total_points, 0), COALESCE(g.minutes, 0)
                       FROM picks p LEFT JOIN player_gw g
                         ON g.player_id = p.player_id AND g.event = p.event
                       WHERE p.entry_id = ? AND p.event = ?""", (entry, event))
    fpl = _q(con, "SELECT points, fetched_at_utc FROM entry_gw WHERE entry_id = ? AND event = ?",
             (entry, event))
    if not picks or not fpl or fpl[0][1] is None:
        return None
    pts = {p[0]: p[5] for p in picks}
    mins = {p[0]: p[6] for p in picks}
    boost = any(p[1] > 11 and p[2] > 0 for p in picks)
    eff = {p[0]: (1 if p[1] <= 11 or boost else 0) for p in picks}
    for (inn, out) in _q(con, "SELECT element_in, element_out FROM automatic_subs "
                              "WHERE entry_id = ? AND event = ?", (entry, event)):
        eff[out], eff[inn] = 0, 1
    cap = next((p[0] for p in picks if p[3]), None)
    vice = next((p[0] for p in picks if p[4]), None)
    times = max([p[2] for p in picks if p[3] or p[4]] + [2])
    if cap is not None and mins.get(cap, 0) > 0:
        eff[cap] = times
    elif vice is not None and mins.get(vice, 0) > 0 and eff.get(vice):
        eff[vice] = times
    return sum(pts[p] * eff[p] for p in pts), fpl[0][0]


def _gw_span(gws):
    """[1, 2, 3, 5] -> "GW1-GW3, GW5"."""
    out, run = [], []
    for g in sorted(gws):
        if run and g != run[-1] + 1:
            out.append(f"GW{run[0]}" + (f"-GW{run[-1]}" if len(run) > 1 else ""))
            run = []
        run.append(g)
    if run:
        out.append(f"GW{run[0]}" + (f"-GW{run[-1]}" if len(run) > 1 else ""))
    return ", ".join(out)


def c22(x):
    """Every locked-down gameweek, not only the latest (RULING S2b, point 2):
    each entry's points computed from its stored picks, player points and
    substitutions against FPL's. Each mismatch is listed - none is cut - and
    any makes a WARN. The gameweek in progress stays silent (ruling S3,
    point 6)."""
    if x.export is None:
        return SKIP, "no export"
    import fpl_edge
    deadline = _deadlines(x.db)
    started = sorted(int(e) for e, dl in deadline.items() if dl <= x.now)
    if not started:
        return SKIP, "no gameweek has started"
    locked = [g for g in started if fpl_edge.gameweek_settled(x.export, g, x.now)[0]]
    quiet = ("" if started[-1] in locked else
             f"GW{started[-1]} not locked down: silent mid-gameweek (ruling S3, point 6)")
    bad, n, seen = [], 0, []
    for event in locked:
        for (entry,) in _q(x.db, "SELECT DISTINCT entry_id FROM entry_gw WHERE event = ? "
                                 "ORDER BY entry_id", (event,)):
            got = entry_points(x.db, entry, event)
            if got is None:
                continue
            n += 1
            seen.append(event)
            if got[0] != got[1]:
                bad.append(f"GW{event} {entry}: FPL {got[1]}, computed {got[0]}")
    tail = f"; {quiet}" if quiet else ""
    if bad:
        return WARN, (f"{len(bad)} of {n} entry-gameweeks differ in {_gw_span(set(seen))}: "
                      + "; ".join(bad) + tail)
    if not n:
        return SKIP, (quiet or "no entry with its substitutions stored in a locked-down gameweek"
                      if not locked else
                      f"no entry with its substitutions stored in {_gw_span(locked)}" + tail)
    return OK, f"{n} entry-gameweeks in {_gw_span(set(seen))}, every one equal" + tail


def c23(x):
    import fpl_gate
    hits = [name for name, body in x.changed if fpl_gate.secret_hit(name, body, x.key)]
    if hits:
        return FAIL, f"{len(hits)} file(s) hold a key pattern or the key value: {_short(hits)}"
    return OK, f"{len(x.changed)} file(s) to commit, none holds a key pattern or the key value"


def c24(x):
    """The repository's size (GitHub API), and every single file of the data
    folder: one over BIG_FILE_MB is a WARN that names it (W1 odds storage,
    point 4: GitHub refuses a file over 100 MB, so the push would fail)."""
    big = [f"{n} {s / 1048576:.0f} MB" for n, s in sorted(x.big_files)]
    mb = x.repo_kb / 1024 if x.repo_kb is not None else None
    if mb is not None and mb >= REPO_FAIL_MB:
        return FAIL, f"{mb:.0f} MB (>= {REPO_FAIL_MB})" + (f"; over {BIG_FILE_MB} MB: {_short(big)}" if big else "")
    if big:
        return WARN, f"file(s) over {BIG_FILE_MB} MB: {_short(big)}" + (f"; repo {mb:.0f} MB" if mb is not None else "")
    if mb is None:
        return SKIP, x.repo_why
    if mb >= REPO_WARN_MB:
        return WARN, f"{mb:.0f} MB (>= {REPO_WARN_MB})"
    return OK, f"{mb:.0f} MB"


def c25(x):
    if x.started is None:
        return SKIP, "no start time in the run log"
    minutes = (x.now - x.started).total_seconds() / 60
    return (WARN, f"{minutes:.1f} min (> 15)") if minutes > 15 else (OK, f"{minutes:.1f} min")


def c26(x):
    when = status_time(x.prev_status)
    if when is None:
        return SKIP, "no earlier status.txt"
    hours = (x.now - when).total_seconds() / 3600
    if hours >= 30:
        return WARN, f"the last status.txt is {hours:.0f} h old (a night was missed)"
    return OK, f"the last status.txt is {hours:.1f} h old"


def c27(x):
    return SKIP, ("manual: the Actions tab, Boris's weekly glance (a disabled workflow "
                  "runs no check, and the token has no actions scope)")


def c28(x):
    """The test gate: tonight's suite, from the run log (fpl_nightly.py prints
    TESTS OK or TESTS FAILED after it)."""
    text = x.run_log or ""
    part = text[text.find("running tests ..."):] if "running tests ..." in text else text
    ran = re.findall(r"^Ran (\d+) tests?", part, re.M)
    if "TESTS FAILED" in part:
        res = re.findall(r"^(FAILED \(.*\))\s*$", part, re.M)
        return FAIL, f"the suite is red: {res[0] if res else 'TESTS FAILED'}"
    if "TESTS OK" in part:
        return OK, f"{ran[0] if ran else '?'} tests green"
    return FAIL, "no test result in tonight's run log: the suite did not run"


def c29(x):
    """Every source recorded: the record summary of the run log has RECORD OK
    for each of SOURCES; a RECORD FAIL - a failure, or a source skipped because
    the suite was red - or a missing source fails. fpl_ep's RECORD SKIP (no
    ep_next in the export) is a WARN only (RULING W1 decisions, point 3), and so
    is bottomup_lambda's (no odds snapshot before the deadline; W2)."""
    text = x.run_log or ""
    i = text.rfind("record summary:")
    if i < 0:
        return FAIL, "no record summary in tonight's run log"
    got = {}
    for line in text[i:].splitlines()[1:]:
        m = re.match(r"RECORD (OK|FAIL|SKIP) (\S+) ?(.*)", line.strip())
        if not m:
            break
        got[m.group(2)] = (m.group(1), m.group(3))
    bad = [f"{s} {why}" for s, (st, why) in got.items()
           if st == "FAIL" or (st == "SKIP" and s not in SKIPPABLE)]
    bad += [f"{s} missing" for s in SOURCES if s not in got]
    if bad:
        return FAIL, _short(bad)
    skipped = [s for s in SKIPPABLE if got[s][0] == "SKIP"]
    if skipped:
        return WARN, "; ".join(f"{s} skipped: {got[s][1]}" for s in skipped) + \
            f"; the other {len(SOURCES) - len(skipped)} recorded"
    return OK, ", ".join(f"{s} {got[s][1]}" for s in SOURCES)


def c30(x):
    """Tonight's odds snapshot (W1): fpl_odds.py's one line in the run log.
    Missing, skipped or failed is a WARN - the odds are collected for later
    models, and tonight's other data is sound without them. An OK line is a
    WARN too when a credit header is missing ("credits unknown"; RULING W1
    pre-check decisions, point 2) or fewer than CREDITS_WARN credits remain."""
    lines = [l.strip() for l in (x.run_log or "").splitlines()
             if l.startswith(("ODDS OK", "ODDS FAILED", "ODDS SKIPPED"))]
    if not lines:
        return WARN, "no odds line in tonight's run log: the collector did not run"
    line = lines[-1]
    if line.startswith("ODDS OK"):
        got = re.search(r"credits used (\S+), remaining (\S+), this request (\S+)", line)
        heads = dict(zip(CREDIT_HEADERS, got.groups())) if got else {}
        unknown = [h for h in CREDIT_HEADERS if not re.fullmatch(r"\d+(\.\d+)?", heads.get(h, ""))]
        if unknown:
            return WARN, f"credits unknown (no {', '.join(unknown)}): {line}"
        if float(heads["x-requests-remaining"]) < CREDITS_WARN:
            return WARN, f"credits remaining {heads['x-requests-remaining']} (< {CREDITS_WARN}): {line}"
        return OK, line[len("ODDS OK"):].strip()
    return WARN, line


SECTION_TITLES = ("CHIPS", "LEAGUE")             # as fpl_sections.TITLES (W2)


def c31(x):
    """The report sections (W2): fpl_sections.py's lines in the run log, one
    per section, "<TITLE> OK <n> lines" or "<TITLE> SKIPPED: <why>". A skip,
    a missing line or a failed step is a WARN, never a FAIL."""
    text = x.run_log or ""
    failed = [l.strip() for l in text.splitlines() if l.startswith("SECTIONS FAILED")]
    got = {}
    for line in text.splitlines():
        m = re.match(r"(CHIPS|LEAGUE) (OK \d+ lines|SKIPPED: .*)$", line.strip())
        if m:
            got[m.group(1)] = m.group(2)
    if failed:
        return WARN, failed[-1]
    bad = [f"{t} {got[t]}" for t in SECTION_TITLES if t in got and got[t].startswith("SKIPPED")]
    bad += [f"{t} missing" for t in SECTION_TITLES if t not in got]
    if bad:
        return WARN, _short(bad)
    return OK, ", ".join(f"{t} {got[t][3:]}" for t in SECTION_TITLES)


CHECKS = [globals()[f"c{n:02d}"] for n in range(1, 32)]


def run_all(x):
    out = []
    for n, fn in enumerate(CHECKS, 1):
        try:
            level, detail = fn(x)
        except Exception as e:  # noqa: BLE001 - a bug in a check is reported, never fatal
            level, detail = WARN, f"the check itself failed: {type(e).__name__}: {e}"
        out.append(Result(n, NAMES[n], level, detail))
    return out


# ---------------------------------------------------------------------------
# the status line
# ---------------------------------------------------------------------------

def prague_tz():
    """Europe/Prague from zoneinfo: the status line's local time, right on
    both sides of a clock change (ruling S3, point 5)."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        return ZoneInfo(PRAGUE)
    except ZoneInfoNotFoundError:
        sys.exit("TIME ZONE MISSING: Europe/Prague is not available. On Windows install "
                 "the tzdata package (python -m pip install tzdata).")


def overall(results):
    levels = {r.level for r in results}
    return FAIL if FAIL in levels else WARN if WARN in levels else OK


def next_deadline(con, now):
    rows = [(int(e), dl) for e, dl in _deadlines(con).items() if dl > now]
    return min(rows, key=lambda r: r[1]) if rows else None


def status_line(results, now, deadline, repo_kb, tz):
    ran = [r for r in results if r.level != SKIP]
    good = sum(1 for r in ran if r.level == OK)
    if deadline is None:
        dl = "none"
    else:
        event, when = deadline
        dl = (f"GW{event} {when.astimezone(timezone.utc):%Y-%m-%d %H:%M} UTC / "
              f"{when.astimezone(tz):%Y-%m-%d %H:%M} Prague")
    repo = f"{repo_kb / 1024:.0f} MB" if repo_kb is not None else "? MB"
    return (f"STATUS {overall(results)} | generated {now.astimezone(timezone.utc):%Y-%m-%dT%H:%M:%SZ}"
            f" | next deadline {dl} | checks {good}/{len(ran)} | repo {repo}")


def status_time(text):
    """The generated time of a status file's first line, or None."""
    m = re.search(r"\| generated (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z", text or "")
    return datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc) if m else None


def render(results, line):
    return line + "\n" + "".join(f"{r.n:>2} {r.level:4} {r.name}: {r.detail}\n" for r in results)


# ---------------------------------------------------------------------------
# loading the data folder
# ---------------------------------------------------------------------------

def _git(data, *args):
    r = subprocess.run(["git", "-C", data, *args], stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL)
    return r.stdout if r.returncode == 0 else None


def _ro(path):
    import pathlib
    return sqlite3.connect(pathlib.Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def run_block(text):
    """The text of the last run in a run log: from its last "==== run" line."""
    i = text.rfind("==== run ")
    return text[i:] if i >= 0 else text


def sync_stats(text):
    """The last SYNC STATS of a run log text, or None."""
    found = None
    for line in (text or "").splitlines():
        if line.startswith(STATS_PREFIX):
            try:
                found = json.loads(line[len(STATS_PREFIX):])
            except ValueError:
                pass
    return found


def started_at(text):
    m = re.search(r"started (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC", text or "")
    return datetime.fromisoformat(m.group(1)).replace(tzinfo=timezone.utc) if m else None


def _read_csv(text):
    return [r for r in csv.DictReader(io.StringIO(text, newline=""))] if text else []


def changed_files(data):
    """[(name, bytes)] of the files the commit would add or change."""
    out = _git(data, "status", "--porcelain", "-z", "--untracked-files=all")
    if out is None:
        return []
    files = []
    for entry in (e for e in out.decode("utf-8").split("\0") if e):
        name = entry[3:]
        path = os.path.join(data, name)
        if entry[:2].strip() != "D" and os.path.isfile(path):
            with open(path, "rb") as fh:
                files.append((name, fh.read()))
    return files


def big_files(data, limit_mb=BIG_FILE_MB):
    """[(path relative to the data folder, size)] of every file over limit_mb,
    .git excluded."""
    out = []
    for root, dirs, files in os.walk(data):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            p = os.path.join(root, f)
            size = os.path.getsize(p)
            if size > limit_mb * 1048576:
                out.append((os.path.relpath(p, data).replace(os.sep, "/"), size))
    return out


def repo_size(env):
    """(kb, why): the repository size from the GitHub API (check 24), or
    (None, the reason it was not measured). The token is sent, never shown."""
    repo = env.get("GITHUB_REPOSITORY")
    token = env.get("GH_TOKEN") or env.get("GITHUB_TOKEN")
    if not repo:
        return None, "not measured: no GITHUB_REPOSITORY (a local run)"
    req = urllib.request.Request(f"{API}/repos/{repo}", headers={
        "Accept": "application/vnd.github+json", "User-Agent": "fpl-checks"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with _urlopen(req, timeout=20) as r:
            return int(json.load(r)["size"]), ""
    except Exception as e:  # noqa: BLE001
        return None, f"not measured: {type(e).__name__}"


def load(data, stamp, now=None, env=None):
    """The Ctx of a data folder after tonight's steps."""
    import fpl_edge
    import fpl_sync
    env = os.environ if env is None else env
    x = Ctx(now=now or datetime.now(timezone.utc), key=env.get("ODDS_API_KEY", ""))
    db = os.path.join(data, DB)
    x.db = _ro(db) if os.path.exists(db) else None
    body = _git(data, "show", f"HEAD:{DB}")
    if body:
        tmp = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
        tmp.write(body)
        tmp.close()
        x.prev = _ro(tmp.name)
        x._prev_path = tmp.name
    run_log = os.path.join(data, LOGS, f"run_{stamp}.log")
    text = ""
    if os.path.exists(run_log):
        with open(run_log, encoding="utf-8", newline="") as fh:
            text = run_block(fh.read())
    x.stats, x.started, x.run_log = sync_stats(text), started_at(text), text
    names = (_git(data, "ls-tree", "--name-only", "HEAD", f"{LOGS}/") or b"").decode().split()
    logs = sorted(n for n in names if re.search(r"run_\d{4}-\d{2}-\d{2}\.log$", n))
    if logs:
        prev = _git(data, "show", f"HEAD:{logs[-1]}")
        x.prev_stats = sync_stats(prev.decode("utf-8", "replace")) if prev else None
    x.log = fpl_edge.read_log(os.path.join(data, LOG))
    prev_log = _git(data, "show", f"HEAD:{LOG}")
    x.prev_log = _read_csv(prev_log.decode("utf-8")) if prev_log is not None else None
    export = fpl_edge.newest_export(data)
    if export:
        with open(export, encoding="utf-8", newline="") as fh:
            x.export = json.load(fh)
    prev_status = _git(data, "show", f"HEAD:{REPORTS}/{STATUS}")
    x.prev_status = prev_status.decode("utf-8", "replace") if prev_status else None
    x.changed = changed_files(data)
    x.big_files = big_files(data)
    x.repo_kb, x.repo_why = repo_size(env)
    x.known_gaps = fpl_sync.known_price_gaps()[0]
    return x


def main(argv=None, env=None, tz=None, now=None):
    import fpl_publish
    ap = argparse.ArgumentParser(description="the nightly checks (Step 3)")
    ap.add_argument("--stamp", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--data", default=".")
    a = ap.parse_args(argv)
    env = os.environ if env is None else env
    x = load(a.data, a.stamp, now=now, env=env)
    try:
        results = run_all(x)
        line = status_line(results, x.now, next_deadline(x.db, x.now), x.repo_kb,
                           tz or prague_tz())
    finally:
        for con in (x.db, x.prev):
            if con is not None:
                con.close()
        if getattr(x, "_prev_path", None):
            os.remove(x._prev_path)
    dry = fpl_publish.run_mode(env)[0] == "dry"
    os.makedirs(os.path.join(a.data, REPORTS), exist_ok=True)
    out = os.path.join(a.data, REPORTS, STATUS_DRY if dry else STATUS)
    text = render(results, line)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    report = os.path.join(a.data, REPORTS, f"fpl_{a.stamp}.txt")
    if os.path.exists(report):
        with open(report, encoding="utf-8", newline="") as fh:
            body = fh.read()
        if not body.startswith("STATUS "):
            with open(report, "w", encoding="utf-8", newline="") as fh:
                fh.write(line + "\n\n" + body)
    print("checks:")
    print(text, end="")
    print(f"CHECKS {overall(results)}  -> {os.path.join(REPORTS, os.path.basename(out))}")
    return 1 if overall(results) == FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
