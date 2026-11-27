"""worklog/gw_pass/gw12/delta.py - the GW12 refresh's delta against the morning (data 2efc924) and the lean's numbers
(Boris's rulings of Fri 27 Nov, GW12 refresh points 1 and 3, verbatim in prereg/bundle.md with the reading pinned before
this code). Information only: it reads two folders of committed outputs and computes nothing from the data itself.
Standard library only.

    python -I delta.py --code DIR --old DIR --new DIR --out DIR

  --old    the morning's folder (worklog/gw_pass/gw12): gw12_pass.txt, bb_moves.txt, s7_post_transfer.txt, bb_timing.txt
  --new    the refresh's folder (worklog/gw_pass/gw12/refresh), the same four files

listed   a number that moved by more than 0.3 (xp_v2 and own of our 15 for GW12; the captain block's columns; the plan
         scores and gains in the four tables and the clean-sheet columns; the ARS-MCI lambdas; S7's values; bb_timing's
         weeks); a rank that changed (XI membership and the captains; each table's top-five order and roll's rank; the
         captain block's order; S7's actions; bb_timing's best week). Probabilities (P(10+), P(cs)) cannot move by 0.3:
         printed side by side, listed on a rank change only.
lean     roll's score and rank against the best move in each table; S7's GW12 HOLD, PLAY BB and PLAY FH values, margin
         and same-action share on the current 15; the frozen captain rule's pick (highest xp_v2 in xp_v2's XI) and the
         next two. Numbers only.
"""
import argparse
import os
import re
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
sys.path.insert(0, os.path.join(CODE, "tools"))
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run, sha256_of                             # noqa: E402

TH = 0.3
POS = r"(GK|DEF|MID|FWD)"
TABLES = ("GATED (Thiago 0)", "LIFTED (Thiago from GW14 at chance 100)", "GATED, Calafiori at P(start) 1.0",
          "LIFTED (Thiago from GW14), Calafiori at P(start) 1.0")
CS_SECTIONS = ("LIFTED (Thiago from GW14)  (check", "LIFTED, Calafiori at P(start) 1.0  (check")


class MissingInput(Exception):
    pass


def read(folder, name):
    p = os.path.join(folder, name)
    if not os.path.exists(p):
        raise MissingInput(f"{p} is missing")
    with open(p, encoding="utf-8") as fh:
        return fh.read().splitlines()


def section(lines, start, stop_pred=None):
    """The lines after the first one that starts (stripped) with start, up to the next blank line (or stop_pred)."""
    for i, s in enumerate(lines):
        if s.strip().startswith(start):
            out = []
            for t in lines[i + 1:]:
                if not t.strip() or (stop_pred and stop_pred(t)):
                    break
                out.append(t)
            return out
    raise MissingInput(f"no section starting {start!r}")


def side_by_side(lines):
    """OWN v XP_V2: {'own': [(slot, name, value)], 'xp_v2': [...]} and the two captains."""
    rx = re.compile(r"^\s+(\d+)\s+\*?\s*(\S.*?)\s+" + POS + r"\s+([\d.]+)\s+(\S.*?)\s+" + POS + r"\s+([\d.]+)$")
    i = next(i for i, s in enumerate(lines) if s.startswith("OWN v XP_V2"))
    own, xp = [], []
    cap = None
    for s in lines[i:]:
        m = rx.match(s)
        if m:
            own.append((int(m.group(1)), m.group(2), float(m.group(4))))
            xp.append((int(m.group(1)), m.group(5), float(m.group(7))))
        c = re.match(r"^\s+captain: own (.+?) \(([\d.]+)\)\s+\|\s+xp_v2 as tested (.+?) \(([\d.]+)\)", s)
        if c:
            cap = (c.group(1), float(c.group(2)), c.group(3), float(c.group(4)))
            break
    if len(own) != 15 or cap is None:
        raise MissingInput(f"the OWN v XP_V2 table: {len(own)} slots, captain line {'found' if cap else 'missing'}")
    return {"own": own, "xp_v2": xp, "cap": cap}


def s14(lines):
    rx = re.compile(r"^\s{2}(\S.*?)\s+" + POS + r"\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)$")
    i = next(i for i, s in enumerate(lines) if s.startswith("CAPTAIN TABLE: S14"))
    out = {}
    for s in lines[i:]:
        m = rx.match(s)
        if m:
            out[m.group(1)] = (float(m.group(3)), float(m.group(4)), float(m.group(5)))
        if s.strip().startswith("within 0.3"):
            break
    if len(out) < 14:
        raise MissingInput(f"S14 table: {len(out)} players read")
    return out


def plans(lines):
    """{table: [(rank, score, gain, plan)]} from bb_moves.txt (top five and roll)."""
    rx = re.compile(r"^\s+(\d+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(?:[+-][\d.]+\s+){6}\s*(\S.*)$")
    out = {}
    for t in TABLES:
        rows = []
        for s in section(lines, t + ":")[1:]:
            m = rx.match(s)
            if not m:
                raise MissingInput(f"bb_moves.txt, {t}: unreadable line {s!r}")
            rows.append((int(m.group(1)), float(m.group(2)), float(m.group(3)), m.group(5).strip()))
        out[t] = rows
    return out


def cs_moves(lines):
    rx = re.compile(r"^\s{4}(\S.*?\))\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?\d+)%$")
    clubs = re.compile(r"^\s{6}([A-Z]{3})\s+((?:[\d.]+\s+){6})\(A\) ([\d.]+) \((\d+) of (\d+)\)\s+\(B\) ([\d.]+)$")
    out = {}
    for sec in CS_SECTIONS:
        i = next(i for i, s in enumerate(lines) if s.strip().startswith(sec))
        mv, cl = {}, {}
        for s in lines[i + 1:]:
            if s.startswith("  LIFTED") or s.startswith("  every club") or not s.strip():
                break
            m = rx.match(s)
            if m:
                mv[m.group(1)] = tuple(float(m.group(k)) for k in (2, 3, 4, 5)) + (int(m.group(6)),)
            c = clubs.match(s)
            if c:
                cl[c.group(1)] = ([float(x) for x in c.group(2).split()], float(c.group(3)), float(c.group(6)))
        if len(mv) != 3 or not cl:
            raise MissingInput(f"clean-sheet section {sec!r}: {len(mv)} moves, {len(cl)} clubs")
        out[sec] = (mv, cl)
    return out


def captain_block(lines):
    i = next(i for i, s in enumerate(lines) if s.startswith("CAPTAIN (GW"))
    out = []
    for s in lines[i + 2:]:
        if s.strip().startswith("odds ARS-MCI"):
            break
        f = re.split(r"\s{2,}", s.strip())
        if len(f) < 10:
            raise MissingInput(f"captain block: unreadable line {s!r}")
        out.append((f[0], f[1], [None if x == "-" else float(x) for x in f[3:9]]))
    return out


def odds_line(lines):
    s = next(s for s in lines if s.strip().startswith("odds ARS-MCI"))
    m = re.search(r"lambda ARS ([\d.]+), lambda MCI ([\d.]+); P\(cs\) ARS ([\d.]+), P\(cs\) MCI ([\d.]+)", s)
    if not m:
        raise MissingInput(f"odds line unreadable: {s!r}")
    return tuple(float(x) for x in m.groups())


def s7_lines(lines, start):
    """{gw: (V_BB, V_FH, ours XI, FH XI, action)} of the first GW table after the line starting with start."""
    rx = re.compile(r"^\s+(\d+)\s+(own|own-model)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+(.+?)\s*$")
    i = next(i for i, s in enumerate(lines) if s.startswith(start))
    out = {}
    for s in lines[i:]:
        m = rx.match(s)
        if m:
            out[int(m.group(1))] = tuple(float(m.group(k)) for k in (3, 4, 5, 6)) + (m.group(7),)
        elif out and not s.strip():
            break
    if sorted(out) != list(range(12, 20)):
        raise MissingInput(f"S7 table after {start!r}: weeks {sorted(out)}, not GW12-19")
    return out


def s7_summary(lines):
    rx = re.compile(r"^\s{2}(current 15|\(a\))\s+(\S+(?: \S+)?)\s+([\d.]+)\s+([+-][\d.]+)\s+\[(.+?)\]\s+(\d+)%\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$")
    out = {}
    for s in lines:
        m = rx.match(s)
        if m:
            out[m.group(1)] = {"action": m.group(2), "vbb": float(m.group(3)), "margin": float(m.group(4)),
                               "ci": m.group(5), "same": int(m.group(6)), "hold": float(m.group(7)),
                               "bb": float(m.group(8)), "fh": float(m.group(9))}
    sq = next((s for s in lines if s.startswith("(a) ")), None)
    if len(out) != 2 or sq is None:
        raise MissingInput(f"S7 summary: {len(out)} lines, squad line {'found' if sq else 'missing'}")
    return out, sq


def bbt(lines):
    rx = re.compile(r"^\s{4}(current 15|\(a\))\s+((?:[\d.]+\s+){6})([+-][\d.]+)\s+(GW\d+)\s+(\d) of 6")
    out, cur = {}, None
    for s in lines:
        if s.startswith("  UNDER THE GATE"):
            cur = "gated"
        elif s.startswith("  LIFTED"):
            cur = "lifted"
        m = rx.match(s)
        if m and cur:
            out[(cur, m.group(1))] = ([float(x) for x in m.group(2).split()], float(m.group(3)), m.group(4))
    if len(out) != 4:
        raise MissingInput(f"bb_timing: {len(out)} rows read, not 4")
    return out


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name in ("--code", "--old", "--new", "--out"):
        ap.add_argument(name, required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/gw_pass/gw12/delta.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    L = []

    def out(s=""):
        print(s, flush=True)
        L.append(s)

    F = {k: {f: read(d, f) for f in ("gw12_pass.txt", "bb_moves.txt", "s7_post_transfer.txt", "bb_timing.txt")}
         for k, d in (("old", a.old), ("new", a.new))}
    head = {k: F[k]["bb_moves.txt"][1].strip() for k in F}
    n_listed = [0]

    def lst(s):
        n_listed[0] += 1
        out("  * " + s)

    def num(label, o, n):
        if o is None or n is None:
            if o != n:
                lst(f"{label}: {o} -> {n}")
            return
        if abs(n - o) > TH + 1e-9:
            lst(f"{label}: {o:.2f} -> {n:.2f} ({n - o:+.2f})")

    out("DELTA  GW12 refresh against the morning (Boris's rulings of Fri 27 Nov, GW12 refresh points 1 and 3); information only")
    out(f"  old: {head['old']}")
    out(f"  new: {head['new']}")
    out(f"  code {run_.commit[:7]} (modified tracked files {run_.dirty}); script sha256 {sha256_of(os.path.abspath(__file__))}; "
        f"generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  listed (*): a number that moved by more than {TH}, or a rank that changed; probabilities printed beside each other")

    # 1. XI and captains
    out()
    out("1. XI AND CAPTAINS (the bundle's OWN v XP_V2)")
    sb = {k: side_by_side(F[k]["gw12_pass.txt"]) for k in F}
    for src in ("own", "xp_v2"):
        vo = {nm: v for _, nm, v in sb["old"][src]}
        vn = {nm: v for _, nm, v in sb["new"][src]}
        for nm in sorted(set(vo) | set(vn)):
            num(f"{src} {nm}", vo.get(nm), vn.get(nm))
        xo = [nm for sl, nm, _ in sb["old"][src] if sl <= 11]
        xn = [nm for sl, nm, _ in sb["new"][src] if sl <= 11]
        if set(xo) != set(xn):
            lst(f"{src} XI: out {sorted(set(xo) - set(xn))}, in {sorted(set(xn) - set(xo))}")
        bo = [nm for sl, nm, _ in sb["old"][src] if sl > 11]
        bn = [nm for sl, nm, _ in sb["new"][src] if sl > 11]
        if bo != bn:
            lst(f"{src} bench order: {bo} -> {bn}")
    co, cn = sb["old"]["cap"], sb["new"]["cap"]
    out(f"  captain own: {co[0]} {co[1]:.2f} -> {cn[0]} {cn[1]:.2f};  xp_v2: {co[2]} {co[3]:.2f} -> {cn[2]} {cn[3]:.2f}")
    if co[0] != cn[0]:
        lst(f"own captain changed: {co[0]} -> {cn[0]}")
    if co[2] != cn[2]:
        lst(f"xp_v2 captain changed: {co[2]} -> {cn[2]}")

    # 2. transfers
    out()
    out("2. TRANSFER TABLES (bb_moves.txt; 1 free transfer, no hits)")
    po = plans(F["old"]["bb_moves.txt"])
    pn = plans(F["new"]["bb_moves.txt"])
    for t in TABLES:
        o = {p: (r, sc, g) for r, sc, g, p in po[t]}
        n = {p: (r, sc, g) for r, sc, g, p in pn[t]}
        out(f"  {t}")
        for p in list(dict.fromkeys([x[3] for x in po[t]] + [x[3] for x in pn[t]])):
            ro, rn = o.get(p), n.get(p)
            f = lambda v: "outside the top five" if v is None else f"#{v[0]} {v[1]:.2f} (gain {v[2]:.2f})"   # noqa: E731
            out(f"    {p:<44} {f(ro):<28} -> {f(rn)}")
            if ro and rn:
                if ro[0] != rn[0]:
                    lst(f"{t}: {p} rank {ro[0]} -> {rn[0]}")
                num(f"{t}: {p} score", ro[1], rn[1])
                num(f"{t}: {p} gain", ro[2], rn[2])
            else:
                lst(f"{t}: {p} {'left' if ro else 'entered'} the top five")
    cso = cs_moves(F["old"]["bb_moves.txt"])
    csn = cs_moves(F["new"]["bb_moves.txt"])
    out("  clean-sheet columns (gain, flat A, flat B, no CS; CS share)")
    for sec in CS_SECTIONS:
        (mo, clo), (mn, cln) = cso[sec], csn[sec]
        out(f"  {sec.split('  (')[0]}")
        for p in list(dict.fromkeys(list(mo) + list(mn))):
            vo, vn = mo.get(p), mn.get(p)
            out(f"    {p:<44} {'-' if vo is None else ' '.join(f'{x:.2f}' for x in vo[:4]) + f' {vo[4]}%':<30} -> "
                f"{'-' if vn is None else ' '.join(f'{x:.2f}' for x in vn[:4]) + f' {vn[4]}%'}")
            if vo and vn:
                for k, lab in enumerate(("gain", "flat A", "flat B", "no CS")):
                    num(f"CS {p} {lab}", vo[k], vn[k])
            else:
                lst(f"CS: {p} {'left' if vo else 'entered'} the top three")
        for club in sorted(set(clo) & set(cln)):
            out(f"    {club} P(cs) {' '.join(f'{x:.2f}' for x in clo[club][0])} -> {' '.join(f'{x:.2f}' for x in cln[club][0])}; "
                f"(A) {clo[club][1]:.2f} -> {cln[club][1]:.2f}; (B) {clo[club][2]:.2f} -> {cln[club][2]:.2f}")

    # 3. captain block
    out()
    out("3. CAPTAIN BLOCK (bb_moves.txt: xp_v2 live, own, xg, bottomup, bottomup_lambda, xp_v2 recorded) and S14's P(10+)")
    cbo = captain_block(F["old"]["bb_moves.txt"])
    cbn = captain_block(F["new"]["bb_moves.txt"])
    cols = ("xp_v2 live", "own", "xg", "bottomup", "bottomup_lambda", "xp_v2 recorded")
    do, dn = {nm: v for nm, _, v in cbo}, {nm: v for nm, _, v in cbn}
    for nm in list(dict.fromkeys([x[0] for x in cbo] + [x[0] for x in cbn])):
        out(f"    {nm:<14} {' '.join('-' if v is None else f'{v:.2f}' for v in do.get(nm, [None] * 6))}  ->  "
            f"{' '.join('-' if v is None else f'{v:.2f}' for v in dn.get(nm, [None] * 6))}")
        if nm in do and nm in dn:
            for k, c in enumerate(cols):
                num(f"captain block {nm} {c}", do[nm][k], dn[nm][k])
        else:
            lst(f"captain block: {nm} {'left' if nm in do else 'entered'}")
    oo, on = [x[0] for x in cbo], [x[0] for x in cbn]
    if oo != on:
        lst(f"captain block order: {oo} -> {on}")
    so, sn = s14(F["old"]["gw12_pass.txt"]), s14(F["new"]["gw12_pass.txt"])
    out("    P(10+) (S14): " + "; ".join(f"{nm} {so[nm][1]:.3f} -> {sn[nm][1]:.3f}" for nm in so if nm in sn))
    ro_ = sorted(so, key=lambda k: -so[k][1])[:3]
    rn_ = sorted(sn, key=lambda k: -sn[k][1])[:3]
    if ro_ != rn_:
        lst(f"P(10+) top three: {ro_} -> {rn_}")
    lo, ln = odds_line(F["old"]["bb_moves.txt"]), odds_line(F["new"]["bb_moves.txt"])
    out(f"    ARS-MCI: lambda ARS {lo[0]:.2f} -> {ln[0]:.2f}, MCI {lo[1]:.2f} -> {ln[1]:.2f}; P(cs) ARS {lo[2]:.3f} -> {ln[2]:.3f}, "
        f"MCI {lo[3]:.3f} -> {ln[3]:.3f}")
    num("lambda ARS", lo[0], ln[0])
    num("lambda MCI", lo[1], ln[1])

    # 4. chips
    out()
    out("4. CHIPS (S7 on own; bb_timing on xp_v2)")
    sqo = s7_summary(F["old"]["s7_post_transfer.txt"])
    sqn = s7_summary(F["new"]["s7_post_transfer.txt"])
    if sqo[1] != sqn[1]:
        lst(f"squad (a) changed: {sqo[1]} -> {sqn[1]}")
    for k in ("current 15", "(a)"):
        o, n = sqo[0].get(k), sqn[0].get(k)
        if o is None or n is None:
            raise MissingInput(f"S7 summary line for {k} missing")
        out(f"    {k}: {o['action']} margin {o['margin']:+.2f} same {o['same']}%  ->  {n['action']} margin {n['margin']:+.2f} same {n['same']}%")
        if o["action"] != n["action"]:
            lst(f"S7 {k} GW12 action {o['action']} -> {n['action']}")
        for f_ in ("vbb", "margin", "hold", "bb", "fh"):
            num(f"S7 {k} GW12 {f_}", o[f_], n[f_])
    for k, start in (("current 15", "CHIP CALCULATOR"), ("(a)", "(a) ")):
        src_o = F["old"]["gw12_pass.txt"] if k == "current 15" else F["old"]["s7_post_transfer.txt"]
        src_n = F["new"]["gw12_pass.txt"] if k == "current 15" else F["new"]["s7_post_transfer.txt"]
        to, tn = s7_lines(src_o, start), s7_lines(src_n, start)
        for gw in sorted(set(to) | set(tn)):
            if gw not in to or gw not in tn:
                lst(f"S7 {k} GW{gw} line missing on one side")
                continue
            for j, lab in enumerate(("V_BB", "V_FH", "ours XI", "FH XI")):
                num(f"S7 {k} GW{gw} {lab}", to[gw][j], tn[gw][j])
            if to[gw][4] != tn[gw][4]:
                lst(f"S7 {k} GW{gw} action {to[gw][4]} -> {tn[gw][4]}")
    bo, bn = bbt(F["old"]["bb_timing.txt"]), bbt(F["new"]["bb_timing.txt"])
    for key in sorted(set(bo) | set(bn)):
        if key not in bo or key not in bn:
            lst(f"bb_timing {key} missing on one side")
            continue
        (wo, go, bwo), (wn, gn, bwn) = bo[key], bn[key]
        out(f"    bb_timing {key[0]} {key[1]}: GW14-GW15 {go:+.2f} best {bwo}  ->  {gn:+.2f} best {bwn}")
        for j, w in enumerate(range(12, 18)):
            num(f"bb_timing {key[0]} {key[1]} GW{w}", wo[j], wn[j])
        num(f"bb_timing {key[0]} {key[1]} GW14-GW15", go, gn)
        if bwo != bwn:
            lst(f"bb_timing {key[0]} {key[1]} best week {bwo} -> {bwn}")

    out()
    out(f"  {n_listed[0]} item(s) listed")

    # the lean's numbers (point 3), refresh only
    out()
    out("THE LEAN'S NUMBERS (point 3; roll, no chip, captain by the frozen rule) on the refresh")
    for t in TABLES:
        rows = pn[t]
        best = rows[0]
        roll = next((r for r in rows if r[3] == "roll"), None)
        out(f"  {t}: roll {'not shown' if roll is None else f'#{roll[0]} {roll[1]:.2f}'}; best #{best[0]} {best[3]} {best[1]:.2f} "
            f"(gain {best[2]:.2f}, lost FT 1.00 included in the score)")
    s = sqn[0]["current 15"]
    out(f"  S7 GW12, current 15: HOLD {s['hold']:.2f}, PLAY BB {s['bb']:.2f}, PLAY FH {s['fh']:.2f}; {s['action']} margin {s['margin']:+.2f}, "
        f"90% [{s['ci']}], same action in {s['same']}%")
    xi = sorted([x for x in sb["new"]["xp_v2"] if x[0] <= 11], key=lambda x: -x[2])
    out(f"  captain by the frozen rule (highest xp_v2 in xp_v2's XI): {xi[0][1]} {xi[0][2]:.2f}; next {xi[1][1]} {xi[1][2]:.2f}, "
        f"{xi[2][1]} {xi[2][2]:.2f}")
    if xi[0][1] != sb["new"]["cap"][2]:
        raise MissingInput(f"the XI's highest xp_v2 {xi[0][1]} is not the bundle's captain {sb['new']['cap'][2]}")

    path_out = os.path.join(a.out, "delta.txt")
    with open(path_out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    run_.wrote(path_out)
    print(f"written: {path_out}; provenance: {run_.close()}")


if __name__ == "__main__":
    try:
        main()
    except MissingInput as e:
        sys.exit(f"MISSING INPUT: {e}")
