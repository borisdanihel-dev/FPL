"""
tools/calendar_2627.py  -  the 2026/27 calendar mapper (BUILD_PLAN.md Step 16,
point 2; prereg/S16.md). An offline tool: the nightly runner never imports it.
Standard library only.

    python tools/calendar_2627.py [DB]     DB defaults to C:\\GIT\\FPL-data\\fpl.sqlite

Maps each cup date of Step 16.2 to the gameweek whose window holds it, the
window of gameweek g being [deadline g, deadline g+1) from events.deadline_time
(GW38's window is open at the end). A date is a UK calendar day, midnight to
midnight Europe/London. A day that holds a deadline is ambiguous: the plan
gives dates without kickoff times, so the gameweek depends on the kickoff and
the tool names both sides instead of picking one. The league fixtures
scheduled that UK day are counted, information only. The database is opened
read-only.
"""

import os
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
DB = r"C:\GIT\FPL-data\fpl.sqlite"
# Step 16.2's dates. The 2026/27 season's March to May fall in 2027.
DATES = (("Carabao Cup final", date(2027, 3, 21)),
         ("FA Cup quarter-finals", date(2027, 4, 3)),
         ("FA Cup semi-finals", date(2027, 4, 24)),
         ("FA Cup final", date(2027, 5, 22)))


def _last_sunday(year, month):
    d = (date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)) - timedelta(days=1)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d


def uk_offset(t):
    """Europe/London's offset at the UTC instant t: +1 h (BST) from 01:00 UTC
    on the last Sunday of March to 01:00 UTC on the last Sunday of October,
    +0 (GMT) otherwise. No time-zone database needed."""
    def switch(month):
        return datetime.combine(_last_sunday(t.year, month), datetime.min.time(), UTC) + timedelta(hours=1)
    return timedelta(hours=1) if switch(3) <= t < switch(10) else timedelta(0)


def uk_day(d):
    """(start, end) of UK calendar day d as UTC instants. A UK midnight is
    the UTC midnight less the offset in force an hour before it; the clocks
    only change at 01:00 UTC, so that offset is the one at the midnight."""
    def midnight(day):
        utc = datetime.combine(day, datetime.min.time(), UTC)
        return utc - uk_offset(utc - timedelta(hours=1))
    return midnight(d), midnight(d + timedelta(days=1))


def utc(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)


def connect(path):
    """Read-only: this tool never writes to the data folder (FAST-TRACK item 1)."""
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)


def deadlines(con):
    return [(g, utc(t)) for g, t in con.execute("SELECT id, deadline_time FROM events ORDER BY id")]


def window(dls, t):
    """The gameweek whose window holds instant t; None before GW1's deadline."""
    held = [g for g, dl in dls if dl <= t]
    return max(held) if held else None


def map_date(dls, d):
    """{"gw": g} for a day wholly inside one window, or {"between": (g0, g1),
    "deadlines": [...]} for a day that holds a deadline (g0 None when the day
    holds GW1's). The deadlines either side come with it. A day wholly before
    GW1's deadline raises ValueError."""
    start, end = uk_day(d)
    inside = [(g, dl) for g, dl in dls if start < dl < end]
    before = window(dls, start)
    if before is None and not inside:
        raise ValueError(f"{d} is before GW1's deadline")
    prev = next((dl for g, dl in dls if g == before), None)
    out = {"date": d, "start": start, "end": end, "prev": (before, prev),
           "next": next(((g, dl) for g, dl in dls if dl >= end), (None, None))}
    if inside:
        out["between"] = (before, inside[-1][0])
        out["deadlines"] = inside
    else:
        out["gw"] = before
    return out


def fixtures_that_day(con, d):
    start, end = uk_day(d)
    return sum(1 for (k,) in con.execute("SELECT kickoff_time FROM fixtures WHERE kickoff_time IS NOT NULL")
               if start <= utc(k) < end)


def _uk(t):
    return (t + uk_offset(t)).strftime("%a %d %b %H:%M") + " UK"


def describe(name, m, n_fixtures):
    d = m["date"]
    head = f"{name:23s} {d:%a %d %b %Y}  "
    if "gw" in m:
        g0, t0 = m["prev"]
        g1, t1 = m["next"]
        h0 = (m["start"] - t0).total_seconds() / 3600
        tail = (f"; GW{g1} deadline {_uk(t1)}, {(t1 - m['end']).total_seconds() / 3600:.1f} h after it"
                if g1 else "; no later deadline")
        body = f"GW{g0}  (GW{g0} deadline {_uk(t0)}, {h0:.1f} h before the day{tail})"
    else:
        g0, g1 = m["between"]
        dl = ", ".join(f"GW{g} {_uk(t)}" for g, t in m["deadlines"])
        side = f"GW{g0}" if g0 else "before GW1"
        body = (f"{side} or GW{g1}: the day holds the deadline {dl}; which gameweek "
                f"depends on the kickoff time, which the plan does not give")
    return head + body + f"  | league fixtures that day: {n_fixtures}"


def main(argv=None, say=print):
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else DB
    if not os.path.exists(path):
        say(f"no database at {path}")
        return 1
    con = connect(path)
    try:
        dls = deadlines(con)
        say(f"2026/27 calendar mapper: {len(dls)} deadlines from {path} (read-only)")
        for name, d in DATES:
            say(describe(name, map_date(dls, d), fixtures_that_day(con, d)))
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
