"""fpl_sections.py - the CHIPS and LEAGUE sections of the nightly report
(W2 piece c; prereg/W2.md acceptance 1, RULING W2 build point 1).

    CHIPS   S7's chip calculator: the V table, continuation values,
            PLAY/HOLD for the next gameweek, bench prep and the Free Hit
            screen (fpl_chips.live, tools/chips.py's live() copied verbatim)
    LEAGUE  S9: league odds, the variance line, threat-set EO and the captain
            table (fpl_league.report, tools/league.py's report() copied
            verbatim)

Run by the nightly after the report is built, in the data folder; the
sections are appended to the report. They read fpl.sqlite read-only, the
export and the projection log. A section whose input is missing prints one
line, `<SECTION> SKIPPED: <why>`, and the night goes on; check 31 WARNs on
it and never fails the night. Standard library only.

    python fpl_sections.py --report reports/fpl_<date>.txt [--data DIR]
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone

import fpl_bt
import fpl_chips
import fpl_league

TITLES = ("CHIPS", "LEAGUE")
MISSING = (fpl_bt.MissingInput, fpl_chips.MissingInput, fpl_league.MissingInput, sqlite3.Error, OSError, KeyError)
RULE = "=" * 78


def sections(data_dir, now=None):
    """[(title, lines, status line)] for the two sections; a missing input
    is the one line `<TITLE> SKIPPED: <why>` (never a substitute)."""
    now = now or datetime.now(timezone.utc)
    run = {"CHIPS": lambda out: fpl_chips.live(data_dir, out),
           "LEAGUE": lambda out: fpl_league.report(data_dir, out, now)}
    result = []
    for title in TITLES:
        lines = []
        try:
            run[title](lines.append)
            status = f"{title} OK {len(lines)} lines"
        except MISSING as e:
            why = f"{type(e).__name__}: {e}" if isinstance(e, (sqlite3.Error, OSError, KeyError)) else str(e)
            lines = [f"{title} SKIPPED: {why}"]
            status = lines[0]
        result.append((title, lines, status))
    return result


def render(result):
    """The text appended to the report: per section a ruled title and its lines."""
    out = []
    for title, lines, _ in result:
        out += ["", RULE, f"{title} (W2: {'S7 chip calculator' if title == 'CHIPS' else 'S9 league'})", RULE] + lines
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", required=True, help="the night's report, appended to")
    ap.add_argument("--data", default=".", help="the data folder (default: here)")
    a = ap.parse_args(argv)
    result = sections(a.data)
    with open(a.report, "a", encoding="utf-8", newline="") as fh:
        fh.write(render(result))
    for _, _, status in result:
        print(status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
