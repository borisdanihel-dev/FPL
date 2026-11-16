"""tools/capflag.py - the GK+DEF 2-per-club cap flag (prereg/S8c.md
amendment 1; Ruling, Tue 20 Oct afternoon, point 3). Print only: no rule,
ranking, legality or plan changes. Offline; standard library only; the
nightly never imports it.

A squad breaks the cap when one club has more than 2 goalkeepers and
defenders among its 15; a suggested move is judged on the squad after it
(our 15, minus the players out, plus the players in). The flag is
"breaks the cap: ARS 3" (several clubs joined by ", ", sorted by club),
appended to its line after three spaces.
"""
from collections import Counter

CAP = 2                             # Boris's choice: at most 2 GK+DEF per club
GKDEF = (1, 2)


def breaks(rows):
    """[(club, n)], sorted by club, for every club over the cap."""
    c = Counter(r["team"] for r in rows if r["pos"] in GKDEF)
    return sorted((t, n) for t, n in c.items() if n > CAP)


def after(squad, outs, ins):
    """The squad after a move: our 15, minus the players out, plus the players in."""
    gone = {o["id"] for o in outs}
    return [r for r in squad if r["id"] not in gone] + list(ins)


def flag(rows):
    """'   breaks the cap: ARS 3' for a squad over the cap, else ''."""
    b = breaks(rows)
    return ("   breaks the cap: " + ", ".join(f"{t} {n}" for t, n in b)) if b else ""


def move_flag(squad, outs, ins):
    """The flag of a suggested move, judged on the squad after it."""
    return flag(after(squad, outs, ins))
