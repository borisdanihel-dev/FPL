"""worklog/gw_pass/gw10/s7_post_transfer.py - the S7 chip calculator on the two squads we would field after GW10's
transfers (Boris, Fri 6 Nov; information only, read-only; no tool change, s8c-wip d9071b8 stays the bundle commit).
Standard library only.

    python -I s7_post_transfer.py --code DIR --data DIR --bundle FILE --out DIR

  --code    a clean worktree of the bundle commit: its tools/ are imported and its commit goes in run.txt
  --bundle  the bundle's gw10_pass.txt: the control below must reproduce its S7 section line for line

method    tools/chips.py live() exactly as the bundle runs it, with one input replaced: my_squad() returns the 15 after
          the two transfers. Each incoming player takes the outgoing player's slot, with selling price = today's price
          (a player bought today sells for what he cost). The Free Hit budget is then bank after + selling prices,
          which equals the export's bank + selling prices (asserted), so the header's budget is unchanged.
control   the current 15 through the same path, compared with the bundle's S7 section.
squads    (a) Branthwaite -> De Cuyper, Thomas -> Van Hecke   (step 4: the best pair with a Bench Boost)
          (b) Branthwaite -> Gabriel, Calafiori -> De Cuyper  (step 4: the best pair without a Bench Boost)
not shown the FREE HIT SCREEN that live() prints last reads the export's squad (fpl_edge.free_hit_table), not
          my_squad(), so for (a) and (b) it would describe the current 15; it is cut from their output.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys
from collections import Counter
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
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

SQUADS = (
    ("(a)", "Branthwaite -> De Cuyper, Thomas -> Van Hecke",
     (("Branthwaite", "EVE", "De Cuyper", "BHA"), ("Thomas", "COV", "Van Hecke", "TOT"))),
    ("(b)", "Branthwaite -> Gabriel, Calafiori -> De Cuyper",
     (("Branthwaite", "EVE", "Gabriel", "ARS"), ("Calafiori", "ARS", "De Cuyper", "BHA"))),
)
CUT = "  FREE HIT SCREEN"
LINE_GW = re.compile(r"^\s+(\d+)\s")
LINE_NEXT = re.compile(r"NEXT GAMEWEEK GW(\d+): (.+?)\s+\(margin over the best other action ([+-]\d+\.\d+) xP\)")
LINE_UNC = re.compile(r"90% \[([+-]\d+\.\d+), ([+-]\d+\.\d+)\], same action in (\d+%)")


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def one(rows, name, team, where):
    hits = [p for p in rows if p["web_name"] == name and p["team"] == team]
    if len(hits) != 1:
        raise MissingInput(f"{where}: {len(hits)} players named {name} at {team}, not 1")
    return hits[0]


def post_squad(d, cur, moves):
    """The 15 after `moves` (out name, out club, in name, in club), each in by the out player's slot; checked legal."""
    rows, ids = list(cur), {r["id"] for r in cur}
    bank_tenths = round(E.selling_budget(d)[0] * 10) - sum(round(r["selling"] * 10) for r in cur)
    for out_name, out_team, in_name, in_team in moves:
        i = [k for k, r in enumerate(rows) if r["name"] == out_name and r["team"] == out_team]
        if len(i) != 1:
            raise MissingInput(f"{out_name} ({out_team}) is not once in our 15")
        o = rows[i[0]]
        p = one(d["all_players"], in_name, in_team, "incoming")
        if p["id"] in ids:
            raise MissingInput(f"{in_name} is already in our 15")
        if p["pos"] != o["pos"]:
            raise MissingInput(f"{in_name} is not in {out_name}'s position")
        bank_tenths += round(o["selling"] * 10) - round(p["price"] * 10)
        rows[i[0]] = {"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"],
                      "price": p["price"], "selling": p["price"], "status": p["status"]}
        ids = {r["id"] for r in rows}
    clubs = Counter(r["team"] for r in rows)
    if bank_tenths < 0:
        raise MissingInput(f"bank after the moves is {bank_tenths / 10:.1f}, below 0")
    if max(clubs.values()) > CH.CLUB_MAX:
        raise MissingInput(f"club limit broken: {clubs.most_common(1)}")
    if Counter(r["pos"] for r in rows) != Counter(CH.QUOTA):
        raise MissingInput("the 15 is not 2 GK, 5 DEF, 5 MID, 3 FWD")
    total = bank_tenths + sum(round(r["selling"] * 10) for r in rows)
    if total != round(E.selling_budget(d)[0] * 10):
        raise MissingInput("bank after + selling prices differs from the export's budget")
    return rows, bank_tenths / 10, clubs


def run_live(data_dir, squad):
    """chips.live() with my_squad() returning `squad`; its printed lines."""
    lines = []
    real = CH.my_squad
    CH.my_squad = lambda d: [dict(r) for r in squad]
    try:
        res = CH.live(data_dir, out=lines.append)
    finally:
        CH.my_squad = real
    return lines, res


def gw_values(res):
    """The value of each action at the first gameweek (chips.action_values, as the margin uses it)."""
    vals = CH.action_values(res["v_bb"], res["v_fh"], res["induction"], res["weeks"][0], res["chips"])
    return tuple(f"{vals[k]:.2f}" if k in vals else "-" for k in ("HOLD", "PLAY BB", "PLAY FH"))


def bundle_s7(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read().splitlines()
    start = next(i for i, s in enumerate(text) if s.startswith("CHIP CALCULATOR"))
    end = next(i for i in range(start, len(text)) if text[i].startswith("====="))
    sec = text[start:end]
    while sec and not sec[-1].strip():
        sec.pop()
    return sec


def summary(lines):
    m = next((LINE_NEXT.search(s) for s in lines if LINE_NEXT.search(s)), None)
    u = next((LINE_UNC.search(s) for s in lines if LINE_UNC.search(s)), None)
    gw10 = next(s for s in lines if LINE_GW.match(s) and LINE_GW.match(s).group(1) == "10")
    v_bb = gw10.split()[2]
    if m is None or u is None:
        raise MissingInput("the calculator printed no action or no interval")
    return m.group(2), v_bb, m.group(3), f"[{u.group(1)}, {u.group(2)}]", u.group(3)


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--data", "--bundle", "--out"):
        ap.add_argument(name, required=True)
    a = ap.parse_args(argv)
    run_ = Run("worklog/gw_pass/gw10/s7_post_transfer.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    out_lines = []

    def out(s=""):
        print(s, flush=True)
        out_lines.append(s)

    d, path = CH.newest_export(a.data)
    cur = CH.my_squad(d)
    data_head = subprocess.run(["git", "-C", a.data, "rev-parse", "--short", "HEAD"],
                               capture_output=True, text=True, check=True).stdout.strip()
    with open(os.path.abspath(__file__), "rb") as fh:
        me_sha = hashlib.sha256(fh.read()).hexdigest()
    budget = E.selling_budget(d)[0]
    bank = (round(budget * 10) - sum(round(r["selling"] * 10) for r in cur)) / 10

    out("S7 CHIP CALCULATOR ON THE POST-TRANSFER SQUADS  GW10 (Boris, Fri 6 Nov); information, read-only, no tool change")
    out(f"  data {data_head}, export {os.path.basename(path)}; code {run_.commit[:7]} (modified tracked files {run_.dirty}); "
        f"script sha256 {me_sha}; generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out("  method: tools/chips.py live() unchanged, with my_squad() returning the 15 after the two transfers (each")
    out("  incoming player in the outgoing player's slot, selling price = today's price). xP source as the bundle: own.")
    out(f"  Free Hit budget: bank after + selling prices = the export's £{budget:.1f}m (bank now {bank:.1f}), so unchanged.")
    out("  The FREE HIT SCREEN that live() prints last reads the export's squad, not my_squad(): cut from (a) and (b).")

    ctrl, ctrl_res = run_live(a.data, cur)
    ref = bundle_s7(a.bundle)
    same = sum(1 for x, y in zip(ctrl, ref) if x == y)
    ok = len(ctrl) == len(ref) == same
    out(f"  control: the current 15 through the same path vs the bundle's S7 section: {same} of {len(ref)} lines equal "
        f"({len(ctrl)} printed){'' if ok else '  - MISMATCH'}")
    if not ok:
        raise MissingInput("the control does not reproduce the bundle's S7 section; nothing else is reported")

    rows_sum = [("current 15",) + summary(ctrl) + gw_values(ctrl_res)]
    for tag, label, moves in SQUADS:
        squad, bank_after, clubs = post_squad(d, cur, moves)
        lines, res = run_live(a.data, squad)
        cut = next((i for i, s in enumerate(lines) if s.startswith(CUT)), len(lines))
        lines = lines[:cut]
        while lines and not lines[-1].strip():
            lines.pop()
        out("")
        out("=" * 110)
        out(f"{tag} {label}   bank after {bank_after:.1f}; clubs at 3: "
            f"{', '.join(sorted(c for c, n in clubs.items() if n == 3)) or 'none'}")
        out("=" * 110)
        out("  the 15: " + ", ".join(f"{r['name']} ({r['team']}, {r['status']})" for r in squad))
        for s in lines:
            out(s)
        rows_sum.append((tag,) + summary(lines) + gw_values(res))

    out("")
    out("=" * 110)
    out("GW10 SUMMARY (own xP; margin over the best other action; 90% interval of 1000 residual resamples, XIs fixed)")
    out("=" * 110)
    out(f"  {'squad':<11} {'GW10 action':<12} {'V_BB':>6} {'margin':>8}   {'90% interval':<18} {'same':>5}   "
        f"GW10 value of: {'HOLD':>6} {'PLAY BB':>8} {'PLAY FH':>8}")
    for name, act, v_bb, mg, iv, same_pct, v_hold, v_pbb, v_pfh in rows_sum:
        out(f"  {name:<11} {act:<12} {v_bb:>6} {mg:>8}   {iv:<18} {same_pct:>5}   "
            f"{'':>14} {v_hold:>6} {v_pbb:>8} {v_pfh:>8}")
    out("  value of an action = its chip's GW10 value + V(GW11, the chips left after it); HOLD = V(GW11, BB+FH).")
    out("  The interval re-runs the induction on each resample with fresh noise in every week, so HOLD takes the best")
    out("  of the later noisy weeks: a play-now action carries the long lower tail, HOLD the long upper one.")

    os.makedirs(a.out, exist_ok=True)
    path_out = os.path.join(a.out, "s7_post_transfer.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out_lines) + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MissingInput as e:
        print(f"missing input: {e} - nothing is substituted")
        sys.exit(2)
