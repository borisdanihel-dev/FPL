"""
p1_eval.py  -  the frozen P1 evaluation (CHANGELOG 2026-09-11 22:04 and after).

Committed before GW4 kicked off, so how every edge case is read was decided
before anyone could see which way it moves the answer. Standard library only.

Run once, on the first export after GW5 has finished (Mon 21 Sep onward):

    python p1_eval.py fpl_export_gw3.json fpl_export_gw5.json
    python p1_eval.py fpl_export_gw3.json fpl_export_gw5.json --log projection_log.csv

Rules, as frozen:
  predictor   minutes share over GW1-3, from the GW3 export only. Undefined
              (player dropped, reason reported) when he has no GW1-3 minutes or
              is missing from that export - never read as zero.
  population  the xg rows for event 4 in projection_log.csv, one per player.
  flag        share <= 0.667, inclusive (<= 180 of 270 minutes).
  outcome     blanked in at least one of GW4, GW5 = no minutes in a gameweek his
              team played. "His team played" is read from finished fixtures,
              never inferred from a missing row: no row + team played = blank;
              team had no finished fixture = player dropped.
  pass        flagged minus unflagged blank rate, Newcombe hybrid-score 95%
              interval (holds at small counts), lower bound above zero.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict

Z = 1.96
FLAG_MAX = 0.667            # inclusive: 180/270 = 0.6667 is flagged, 181/270 is not
WEEKS = (4, 5)
THIN = 5                    # a 2x2 cell below this is printed as a warning
CAVEAT = ("UNPROVEN, not disproven. At 84 flagged / 172 unflagged the test has "
          "80% power only against gaps of roughly 13-16 points (baseline 5-15%); "
          "a 10-point gap is about a coin flip. A failure here is consistent "
          "with a real effect of moderate size.")

DROP_PREDICTOR = "no predictor: no GW1-3 minutes, or absent from the GW3 export"
DROP_CLUB = "changed club or left the game between the exports"
DROP_FIXTURE = "team had no finished fixture in GW4 or GW5 (blank, postponed, or not yet finished)"


# ---------------------------------------------------------------------------
# intervals
# ---------------------------------------------------------------------------

def wilson(x, n):
    """Wilson score interval for x successes in n trials."""
    if n == 0:
        return 0.0, 1.0
    p = x / n
    denom = 1 + Z * Z / n
    centre = (p + Z * Z / (2 * n)) / denom
    half = Z * (p * (1 - p) / n + Z * Z / (4 * n * n)) ** 0.5 / denom
    return centre - half, centre + half


def newcombe(x1, n1, x2, n2):
    """Difference in proportions p1 - p2 with Newcombe's hybrid score interval
    (1998, method 10). Unlike the normal approximation it does not collapse to
    zero width when a cell is empty, and it stays inside [-1, 1]."""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1)
    l2, u2 = wilson(x2, n2)
    d = p1 - p2
    lo = d - ((p1 - l1) ** 2 + (u2 - p2) ** 2) ** 0.5
    hi = d + ((u1 - p1) ** 2 + (p2 - l2) ** 2) ** 0.5
    return d, lo, hi


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------

def predictor(pre):
    """player_id -> minutes share over GW1-3, or None where it is undefined.

    Reads the GW3 export and nothing else: the GW5-time value spans GW1-4 and
    would contain GW4's outcome."""
    if pre.get("gameweek") != 3:
        raise ValueError(f"predictor must come from the GW3 export, got "
                         f"GW{pre.get('gameweek')}")
    fixtures = defaultdict(int)
    for f in pre.get("fixtures_played") or []:
        if 1 <= f["event"] <= 3:
            fixtures[f["home"]] += 1
            fixtures[f["away"]] += 1
    out = {}
    for p in pre["all_players"]:
        mins, n = p.get("mins_last4"), fixtures.get(p["team"], 0)
        out[p["id"]] = mins / (90.0 * n) if mins and n else None
    return out


def weekly_minutes(post):
    """(player_id, event) -> minutes, for GW4 and GW5. Keyed by id: web_names
    are not unique, so an export without ids is refused rather than guessed."""
    rows = post.get("player_gw_recent") or []
    if not rows or "player_id" not in rows[0]:
        raise ValueError("the post export has no player_id in player_gw_recent - "
                         "web_names are not unique. Re-export with the current "
                         "fpl_sync.py.")
    mins = defaultdict(int)
    for r in rows:
        if r["event"] in WEEKS:
            mins[(int(r["player_id"]), r["event"])] += r["mins"] or 0
    return mins


def team_fixtures(post):
    """(team, event) -> finished fixtures that gameweek, for GW4 and GW5."""
    n = defaultdict(int)
    for f in post.get("fixtures_played") or []:
        if f["event"] in WEEKS:
            n[(f["home"], f["event"])] += 1
            n[(f["away"], f["event"])] += 1
    return n


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------

def evaluate(pre, post, log_rows):
    gw = post.get("gameweek", 0)
    if not 5 <= gw <= 9:
        raise ValueError(f"post export must be GW5-GW9 (GW4 falls out of its "
                         f"six-week window after GW9); got GW{gw}")
    share = predictor(pre)
    team_pre = {p["id"]: p["team"] for p in pre["all_players"]}
    team_post = {p["id"]: p["team"] for p in post["all_players"]}
    mins, nfix = weekly_minutes(post), team_fixtures(post)
    pop = sorted({int(r["player_id"]) for r in log_rows
                  if r["source"] == "xg" and int(r["event"]) == 4})

    players, dropped = [], defaultdict(list)
    for pid in pop:
        s = share.get(pid)
        if s is None:
            dropped[DROP_PREDICTOR].append(pid)
            continue
        team = team_pre[pid]
        if team_post.get(pid) != team:
            dropped[DROP_CLUB].append(pid)
            continue
        if any(nfix[(team, w)] == 0 for w in WEEKS):
            dropped[DROP_FIXTURE].append(pid)
            continue
        weeks = [mins[(pid, w)] for w in WEEKS]
        players.append({
            "id": pid, "share": s, "flag": s <= FLAG_MAX,
            "blank_weeks": [m == 0 for m in weeks],
            "blank": any(m == 0 for m in weeks),
            "full": all(mins[(pid, w)] >= 90 * nfix[(team, w)] for w in WEEKS),
        })

    flagged = [p for p in players if p["flag"]]
    rest = [p for p in players if not p["flag"]]
    a = sum(p["blank"] for p in flagged)
    b = len(flagged) - a
    c = sum(p["blank"] for p in rest)
    d = len(rest) - c
    out = {"players": players, "dropped": dict(dropped), "table": (a, b, c, d),
           "thin": min(a, b, c, d) < THIN}
    if not flagged or not rest:
        out["verdict"] = "CANNOT EVALUATE - one group is empty"
        return out

    out["primary"] = newcombe(a, a + b, c, c + d)
    xa = sum(sum(p["blank_weeks"]) for p in flagged)
    xc = sum(sum(p["blank_weeks"]) for p in rest)
    out["pooled"] = newcombe(xa, 2 * len(flagged), xc, 2 * len(rest))
    out["cost"] = {
        "flagged_did_not_blank": b / (a + b),
        "flagged_every_minute": sum(p["full"] for p in flagged) / (a + b),
        "good_players_flagged": b / (b + d) if b + d else 0.0,
    }
    _, lo, hi = out["primary"]
    if lo > 0:
        out["verdict"] = "PASS"
    elif hi < 0:
        out["verdict"] = ("FAIL - inverted: flagged players blanked LESS than "
                          "unflagged. The screen points the wrong way.")
    else:
        out["verdict"] = CAVEAT
    return out


def report(r):
    a, b, c, d = r["table"]
    lines = ["=" * 78, "P1 EVALUATION  (frozen before GW4 - see CHANGELOG)", "=" * 78]
    n_drop = sum(len(v) for v in r["dropped"].values())
    lines.append(f"\n  graded {len(r['players'])} players, dropped {n_drop}")
    for why, ids in sorted(r["dropped"].items()):
        lines.append(f"    {len(ids):>3}  {why}")
    lines += ["\n  PRIMARY: blanked in at least one of GW4, GW5 - one row per player",
              f"    {'':12s}{'blanked':>9}{'did not':>9}{'total':>7}{'rate':>8}",
              f"    {'flagged':12s}{a:>9}{b:>9}{a + b:>7}"
              f"{(a / (a + b) if a + b else 0):>8.0%}",
              f"    {'unflagged':12s}{c:>9}{d:>9}{c + d:>7}"
              f"{(c / (c + d) if c + d else 0):>8.0%}"]
    if r["thin"]:
        lines.append(f"    ! thin cell (fewer than {THIN}): the interval rests on "
                     f"very few events - read the counts, not just the interval")
    if "primary" in r:
        g, lo, hi = r["primary"]
        lines.append(f"    gap {g:+.3f}   95% interval {lo:+.3f} .. {hi:+.3f}  (Newcombe)")
        g2, lo2, hi2 = r["pooled"]
        lines.append(f"\n  SECONDARY, OPTIMISTIC - pooled player-gameweeks, each player twice:")
        lines.append(f"    gap {g2:+.3f}   95% interval {lo2:+.3f} .. {hi2:+.3f}  "
                     f"(too narrow: blanking is correlated within a player)")
        k = r["cost"]
        lines += ["\n  COST OF EXCLUDING ON THE FLAG",
                  f"    flagged who did not blank (featured both weeks) "
                  f"{k['flagged_did_not_blank']:>6.0%}",
                  f"    flagged who played every available minute        "
                  f"{k['flagged_every_minute']:>6.0%}",
                  f"    of all players who did not blank, share flagged  "
                  f"{k['good_players_flagged']:>6.0%}"]
    lines.append(f"\n  VERDICT: {r['verdict']}\n")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pre", help="the GW3 export (predictor)")
    ap.add_argument("post", help="an export from GW5-GW9 (outcomes)")
    ap.add_argument("--log", default="projection_log.csv")
    args = ap.parse_args()
    load = lambda p: json.load(open(p, encoding="utf-8"))
    with open(args.log, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    print(report(evaluate(load(args.pre), load(args.post), rows)))


if __name__ == "__main__":
    main()
