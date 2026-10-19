"""fpl_sections.py - the added sections of the nightly report: CHIPS and
LEAGUE (W2 piece c; prereg/W2.md acceptance 1, RULING W2 build point 1),
CAPTAIN, BAN RISK and REALISED (W3; prereg/W3.md, F-B parts 2 and 3).

    CHIPS   S7's chip calculator: the V table, continuation values,
            PLAY/HOLD for the next gameweek, bench prep and the Free Hit
            screen (fpl_chips.live, tools/chips.py's live() copied verbatim)
    LEAGUE  S9: league odds, the variance line, threat-set EO and the captain
            table (fpl_league.report, tools/league.py's report() copied
            verbatim)
    CAPTAIN   Step 14's captain table under xp_v2 as tested and the options
              within 0.3 xP of its captain (fpl_squad.captain)
    BAN RISK  our players one booking from a ban, S12's rule
              (fpl_squad.ban_risk)
    REALISED  from GW8, own v xp_v2 on our squad from the recorded rows
              (fpl_squad.realised)

Run by the nightly after the report is built, in the data folder; the
sections are appended to the report. They read fpl.sqlite read-only, the
export and the projection log. A section whose input is missing prints one
line, `<SECTION> SKIPPED: <why>`, and the night goes on; so does any other
exception inside a section (`<SECTION> SKIPPED: <type>: <message>`, W2
amendment 2). Check 31 WARNs on it and never fails the night. Standard
library only.

    python fpl_sections.py --report reports/fpl_<date>.txt [--data DIR]
"""
import argparse
import os
import sys
from datetime import datetime, timezone

import fpl_bt
import fpl_chips
import fpl_lambda
import fpl_league
import fpl_mv2
import fpl_shares
import fpl_squad
import fpl_xpr

TITLES = ("CHIPS", "LEAGUE", "CAPTAIN", "BAN RISK", "REALISED")
LABELS = {"CHIPS": "W2: S7 chip calculator", "LEAGUE": "W2: S9 league", "CAPTAIN": "W3: Step 14 captain table",
          "BAN RISK": "W3: S12 suspensions", "REALISED": "W3: own v xp_v2 on our squad"}
MISSING = (fpl_bt.MissingInput, fpl_chips.MissingInput, fpl_league.MissingInput, fpl_squad.MissingInput, fpl_xpr.MissingInput,
           fpl_mv2.MissingInput, fpl_lambda.MissingInput, fpl_shares.MissingInput)
RULE = "=" * 78


def sections(data_dir, now=None):
    """[(title, lines, status line)] for the sections; a missing input
    is the one line `<TITLE> SKIPPED: <why>` (never a substitute), and any
    other exception the line `<TITLE> SKIPPED: <type>: <message>` (W2
    amendment 2: never a red night)."""
    now = now or datetime.now(timezone.utc)
    run = {"CHIPS": lambda out: fpl_chips.live(data_dir, out),
           "LEAGUE": lambda out: fpl_league.report(data_dir, out, now),
           "CAPTAIN": lambda out: fpl_squad.captain(data_dir, out),
           "BAN RISK": lambda out: fpl_squad.ban_risk(data_dir, out),
           "REALISED": lambda out: fpl_squad.realised(data_dir, out, now)}
    result = []
    for title in TITLES:
        lines = []
        try:
            run[title](lines.append)
            status = f"{title} OK {len(lines)} lines"
        except Exception as e:
            why = str(e) if isinstance(e, MISSING) else f"{type(e).__name__}: {e}"
            lines = [f"{title} SKIPPED: {why}"]
            status = lines[0]
        result.append((title, lines, status))
    return result


def render(result):
    """The text appended to the report: per section a ruled title and its lines."""
    out = []
    for title, lines, _ in result:
        out += ["", RULE, f"{title} ({LABELS[title]})", RULE] + lines
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
