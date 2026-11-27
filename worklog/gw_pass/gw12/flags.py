"""worklog/gw_pass/gw12/flags.py - the GW12 refresh's flags (Boris's rulings of Fri 27 Nov, GW12 refresh point 2,
verbatim in prereg/bundle.md with the reading pinned before this code). Information only, read-only; standard library.

    python -I flags.py --code DIR --data DIR --csv FILE --bb FILE --out DIR

  --code   a clean worktree of master: its modules are imported and its commit goes in run.txt
  --csv    the run's xp_v2_all.csv (the bundle's), for xp_v2 GW12 and P(start)
  --bb     the run's bb_moves.txt, for the top incoming player of each of its four tables

our 15     status, chance, news from the export; cautions = S12's count (yellow cards in league matches before the
           deadline, fpl_mv2.cautions_before on fpl_squad.ban_rows); "one booking from a ban" and P(ban) by S12's rule
           (fpl_squad.one_from_ban, fpl_mv2.p_ban_next with xp_v2's P(start)), i.e. the BAN RISK section's numbers
targets    Silva (BOU), Justin (LEE), Tavernier (BOU) and the top incoming player of each of bb_moves' four tables:
           status, chance, news, price, starts and minutes in the last four, xp_v2 GW12 and P(start), cautions and
           "one booking from a ban" with P(ban) by the same rule
news time  not held: neither the export nor fpl.sqlite carries FPL's news_added (reported, not substituted)
"""
import argparse
import csv
import os
import re
import subprocess
import sys
from datetime import datetime, timezone


def _arg(argv, name):
    for i, x in enumerate(argv):
        if x == name and i + 1 < len(argv):
            return argv[i + 1]
        if x.startswith(name + "="):
            return x.split("=", 1)[1]
    sys.exit(f"{name} is required")


CODE = os.path.abspath(_arg(sys.argv[1:], "--code"))
sys.path.insert(0, CODE)
sys.path.insert(0, os.path.join(CODE, "tools"))
import chips as CH                                                # noqa: E402
import fpl_edge as E                                              # noqa: E402
import fpl_mv2 as MV                                              # noqa: E402
import fpl_squad as SQ                                            # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run, sha256_of                             # noqa: E402

NAMED = (("Silva", "BOU"), ("Justin", "LEE"), ("Tavernier", "BOU"))     # Boris: Silva BOU, Justin, Tavernier
TABLES = ("GATED (Thiago 0)", "LIFTED (Thiago from GW14 at chance 100)", "GATED, Calafiori at P(start) 1.0",
          "LIFTED (Thiago from GW14), Calafiori at P(start) 1.0")
PLAN = re.compile(r"^\s+1\s+-?[\d.]+\s+-?[\d.]+\s+-?[\d.]+\s+(?:[+-][\d.]+\s+){6}\s*(.+?) -> (.+?) \(([A-Z]{3}), [\d.]+\)$")


class MissingInput(Exception):
    pass


def top_incoming(bb_path):
    """{table title: (in name, club)} of each table's rank-1 plan; a roll at rank 1 gives None."""
    with open(bb_path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    out, cur = {}, None
    for s in lines:
        head = s.strip()
        for t in TABLES:
            if head.startswith(t + ":"):
                cur = t
        if cur and cur not in out and re.match(r"^\s+1\s", s):
            m = PLAN.match(s)
            out[cur] = (m.group(2), m.group(3)) if m else None
    missing = [t for t in TABLES if t not in out]
    if missing:
        raise MissingInput(f"{bb_path}: no rank-1 line for {missing}")
    return out


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--csv", "--bb", "--out"):
        ap.add_argument(name, required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw12/flags.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    d, path = CH.newest_export(a.data)
    target, dl = SQ.next_target(d)
    data_head = subprocess.run(["git", "-C", a.data, "rev-parse", "--short", "HEAD"],
                               capture_output=True, text=True, check=True).stdout.strip()
    by_id = {p["id"]: p for p in d["all_players"]}
    with open(a.csv, encoding="utf-8", newline="") as fh:
        xcsv = {int(r["id"]): r for r in csv.DictReader(fh)}
    rows, prov = SQ.ban_rows(a.data, d)
    inp = E.reliability_inputs(E.canonical_through(E.canonical_from_export(d), d["gameweek"]), gws_played=d["gameweek"])
    rates = SQ.position_rates(rows, dl)

    out(f"FLAGS  GW{target} (deadline {dl:%Y-%m-%d %H:%M} UTC) (Boris's rulings of Fri 27 Nov, GW12 refresh point 2); information, read-only")
    out(f"  data {data_head}, export {os.path.basename(path)} (generated {d.get('generated', '?')}); code {run_.commit[:7]} "
        f"(modified tracked files {run_.dirty}); script sha256 {sha256_of(os.path.abspath(__file__))}; "
        f"generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out("  news time: not held - neither the export nor fpl.sqlite carries FPL's news_added (reported, not substituted)")
    out("  cautions: S12's count (yellow cards in league matches before the deadline); ban: one booking from a ban by S12's rule,")
    out("  P(ban) = min(1, rate90 x P(start)) with xp_v2's P(start), as the BAN RISK section")

    def cautions(pid):
        return MV.cautions_before(rows, pid, dl)

    def ban_text(pid, club, pos):
        band = SQ.one_from_ban(rows, pid, club, dl)
        if band is None:
            return ""
        total, n_next, _ = band
        if pos not in rates:
            raise MissingInput(f"no minutes for position {pos} before the deadline")
        rate = MV.booking_rate90(rows, pid, dl, rates[pos])
        p = inp["players"].get(pid)
        pb = "n/a (no rows)" if p is None else f"{MV.p_ban_next(rate, p['p_start']):.3f}"
        return f"ONE FROM A BAN (club match {n_next} next), P(ban) {pb}" + SQ.provisional_note(prov, club, dl)

    out()
    out("  OUR 15")
    out(f"    {'player':<16}{'club':<6}{'pos':<5}{'status':<8}{'chance':>7}  {'cautions':>8}  ban / news")
    for r in sorted(CH.my_squad(d), key=lambda r: (r["pos"], r["name"])):
        p = by_id[r["id"]]
        club = rows.club_of.get(r["id"])
        if club is None:
            raise MissingInput(f"{r['name']} has no club in fpl.sqlite players")
        ch = p.get("chance_next_round")
        ban = ban_text(r["id"], club, rows.pos.get(r["id"]))
        news = (p.get("news") or "").strip()
        tail = "; ".join(x for x in (ban, f'news "{news}"' if news else "no news") if x)
        out(f"    {r['name']:<16}{r['team']:<6}{['?', 'GK', 'DEF', 'MID', 'FWD'][r['pos']]:<5}{p['status']:<8}"
            f"{'-' if ch is None else ch:>7}  {cautions(r['id']):>8}  {tail}")

    tops = top_incoming(a.bb)
    want = [("named", n, t) for n, t in NAMED]
    for title, v in tops.items():
        if v is not None and v not in NAMED and v not in [(w[1], w[2]) for w in want]:
            want.append((f"top of {title}", v[0], v[1]))
    out()
    out("  TARGETS  (Silva BOU, Justin, Tavernier; and each table's rank-1 incoming player when not one of them)")
    for title, v in tops.items():
        out(f"    rank 1 of {title}: {'roll' if v is None else f'-> {v[0]} ({v[1]})'}")
    out(f"    {'player':<14}{'club':<6}{'why':<10}{'status':<8}{'chance':>7}{'price':>7}{'starts4':>9}{'mins4':>7}"
        f"{'xp_v2':>7}{'P(start)':>10}{'cautions':>10}  ban / news")
    for why, name, team in want:
        hits = [p for p in d["all_players"] if p["web_name"] == name and p["team"] == team]
        if len(hits) != 1:
            raise MissingInput(f"{name} ({team}): {len(hits)} players in the export")
        p = hits[0]
        x = xcsv.get(p["id"])
        if x is None:
            raise MissingInput(f"{name} ({team}) is not in {a.csv}")
        ch = p.get("chance_next_round")
        ps = x.get("p_start") or "-"
        news = (p.get("news") or "").strip()
        club = rows.club_of.get(p["id"])
        if club is None:
            raise MissingInput(f"{name} ({team}) has no club in fpl.sqlite players")
        ban = ban_text(p["id"], club, rows.pos.get(p["id"]))
        tail = "; ".join(x for x in (ban, f'news "{news}"' if news else "no news") if x)
        out(f"    {name:<14}{team:<6}{'named' if why == 'named' else 'top':<10}{p['status']:<8}{'-' if ch is None else ch:>7}"
            f"{p['price']:>7.1f}{p['starts_last4']:>9}{p['mins_last4']:>7}{float(x['xp_v2']):>7.2f}"
            f"{(f'{float(ps):.2f}' if ps != '-' else '-'):>10}{cautions(p['id']):>10}  {tail}")

    path_out = os.path.join(a.out, "flags.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")


if __name__ == "__main__":
    try:
        main()
    except MissingInput as e:
        sys.exit(f"MISSING INPUT: {e}")
