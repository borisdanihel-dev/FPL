"""worklog/w3fix_tie/check.py - evidence for the question parked after Boris's ruling of Fri 27 Nov 15:30 UTC, point 2
(the decimal-tie test for xi_lex; prereg/W3fix.md). Information only, read-only; standard library.

    python -I check.py --code DIR --out DIR

  --code   a worktree holding worklog/checkpoint_gw10/checkpoint.py with xi_lex (w3fix-wip): imported, and its commit
           goes in run.txt

Part 1  random 15s (seeded) with forecasts on coarse decimal grids, so that ties at the top are common: for every tie
        at the top of xi_lex, do all the tied XIs hold the same multiset of values; do the two surviving mutants (m03:
        xi_key called, its result ignored, float sums then ids; m04: val = Fraction(float(v))) ever change the XI, the
        bench or the keeper
Part 2  the ruling's shape: core + {0.1, 0.2} against core + {0.3, 0.0}, both legal - what xi_lex picks
Part 3  is Python's sum() order-sensitive on forecast-like values (5 orders of each random 11-value list)
Part 4  two candidate tests (scratch form, not in tests/), run on the code and on both mutants:
        T1  the 0.1 + 0.2 against 0.3 tie on the values xi_lex hands xi_key, decided by the id list
        T2  xi_lex returns the XI its key ranks first (xi_key patched to rank the lowest sum first)
"""
import argparse
import os
import random
import sys
import types
from datetime import datetime, timezone
from itertools import combinations
from unittest import mock


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
from provenance import Run, sha256_of                             # noqa: E402

CK_PATH = os.path.join(CODE, "worklog", "checkpoint_gw10", "checkpoint.py")
KEY = 'key=lambda c: xi_key(c, val))'
M03 = 'key=lambda c: (xi_key(c, val), (-sum(r["proj"] for r in c), sorted(r["id"] for r in c)))[1])'
VAL = 'val = {r["id"]: _exact(r["proj"]) for r in rows}'
M04 = 'val = {r["id"]: Fraction(float(r["proj"])) for r in rows}'


def load(name, swap=None):
    """checkpoint.py as a module, with one exact text swap (old, new) applied when given."""
    with open(CK_PATH, encoding="utf-8") as fh:
        src = fh.read()
    if swap:
        if src.count(swap[0]) != 1:
            raise SystemExit(f"MISSING INPUT: {swap[0]!r} is not in {CK_PATH} exactly once")
        src = src.replace(*swap)
    mod = types.ModuleType(name)
    mod.__file__ = CK_PATH
    exec(compile(src, CK_PATH, "exec"), mod.__dict__)
    return mod


TOY = [{"id": i, "pos": p} for i, p in ((1, 1), (2, 1), (10, 2), (11, 2), (12, 2), (5, 2), (13, 2), (20, 3), (21, 3),
                                        (22, 3), (23, 3), (24, 3), (30, 4), (31, 4), (300, 4))]
PROJ = {1: 5.0, 2: 1.0, 10: 6.0, 11: 6.0, 12: 6.0, 5: 2.0, 13: 0.5, 20: 6.0, 21: 6.0, 22: 6.0, 23: 6.0, 24: 1.0,
        30: 6.0, 31: 6.0, 300: 2.0}


def t1(CK):
    """The 0.1 + 0.2 against 0.3 tie on xi_lex's own values; the smaller sorted ids win."""
    proj = {**PROJ, 13: 0.1, 24: 0.2, 5: 0.3, 300: 0.0}
    seen, real = [], CK.xi_key
    with mock.patch.object(CK, "xi_key", side_effect=lambda xi, val: (seen.append(val), real(xi, val))[1]):
        CK.xi_lex(TOY, proj)
    val = seen[0]
    core = [r for r in TOY if r["id"] in (1, 10, 11, 12, 20, 21, 22, 23, 30)]
    a = core + [r for r in TOY if r["id"] in (13, 24)]          # DEF 13 0.1 + MID 24 0.2
    b = core + [r for r in TOY if r["id"] in (5, 300)]          # DEF 5 0.3 + FWD 300 0.0
    if not (CK.legal(a) and CK.legal(b)):
        return "toy broken"
    if real(a, val)[0] != real(b, val)[0]:
        return "red (sums differ)"
    return "green" if real(b, val) < real(a, val) else "red (ids do not decide)"


def t2(CK):
    """xi_lex returns the XI its key ranks first."""
    def lowest_first(xi, val):
        return sum(val[r["id"]] for r in xi), sorted(r["id"] for r in xi)
    legal = [c for c in combinations(TOY, 11) if CK.legal(c)]
    val = {i: CK._exact(v) for i, v in PROJ.items()}
    want = {r["id"] for r in min(legal, key=lambda c: lowest_first(c, val))}
    with mock.patch.object(CK, "xi_key", side_effect=lowest_first):
        got = {r["id"] for r in CK.xi_lex(TOY, PROJ)[0]}
    return "green" if got == want else "red (key ignored)"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--code", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run_ = Run("worklog/w3fix_tie/check.py", a.out, argv if argv is not None else sys.argv[1:], root=CODE)
    lines = []

    def out(s=""):
        print(s, flush=True)
        lines.append(s)

    real, m03, m04 = load("ck_real"), load("ck_m03", (KEY, M03)), load("ck_m04", (VAL, M04))
    out("W3FIX TIE CHECK (the question parked after Boris's ruling of Fri 27 Nov 15:30 UTC, point 2); information only")
    out(f"  code {run_.commit[:7]} (modified tracked files {run_.dirty}); checkpoint.py sha256 {sha256_of(CK_PATH)}")
    out(f"  script sha256 {sha256_of(os.path.abspath(__file__))}; Python {sys.version.split()[0]}; "
        f"generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out(f"  m03: {M03}")
    out(f"  m04: {M04}")

    def lex(CK, squad, proj):
        xi, bench, gk = CK.xi_lex(squad, proj)
        return [r["id"] for r in xi], [r["id"] for r in bench], gk["id"]

    pos = [1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4]
    grids = [[k / 10 for k in range(0, 8)], [k / 100 for k in range(0, 40, 3)], [0.0, 0.1, 0.2, 0.3]]
    rng = random.Random(20261127)
    n = ties = multi = d03 = d04 = 0
    for trial in range(3000):
        squad = [{"id": i, "pos": p} for i, p in zip(rng.sample(range(1, 700), 15), pos)]
        rng.shuffle(squad)
        proj = {r["id"]: rng.choice(grids[trial % 3]) for r in squad}
        want = lex(real, squad, proj)
        d03 += lex(m03, squad, proj) != want
        d04 += lex(m04, squad, proj) != want
        val = {r["id"]: real._exact(proj[r["id"]]) for r in squad}
        legal = [c for c in combinations(squad, 11) if real.legal(c)]
        top = max(sum(val[r["id"]] for r in c) for c in legal)
        tied = [c for c in legal if sum(val[r["id"]] for r in c) == top]
        n += 1
        if len(tied) > 1:
            ties += 1
            multi += len({tuple(sorted(val[r["id"]] for r in c)) for c in tied}) > 1
    out()
    out("PART 1  random 15s, forecasts on the grids 0.0-0.7 by 0.1, 0.00-0.39 by 0.03, {0.0, 0.1, 0.2, 0.3}; seed 20261127")
    out(f"  squads {n}; with a tie at the top {ties}; ties whose XIs hold different multisets of values {multi}")
    out(f"  XI, bench or keeper changed: m03 {d03}, m04 {d04}")

    squad = [{"id": i, "pos": p} for i, p in ((1, 1), (2, 1), (10, 2), (11, 2), (12, 2), (13, 2), (14, 2), (20, 3),
                                             (21, 3), (22, 3), (23, 3), (24, 3), (30, 4), (31, 4), (32, 4))]
    proj = {1: 5.0, 2: 1.0, 10: 6.0, 11: 6.0, 12: 6.0, 20: 6.0, 21: 6.0, 22: 6.0, 30: 6.0, 31: 6.0,
            13: 0.1, 14: 0.2, 23: 0.3, 24: 0.0, 32: -1.0}
    pick = sorted(set(lex(real, squad, proj)[0]) & {13, 14, 23, 24})
    out()
    out("PART 2  the ruling's shape: core + DEF 13 (0.1) + DEF 14 (0.2) against core + MID 23 (0.3) + MID 24 (0.0)")
    out(f"  xi_lex takes {pick} of the four, sum {float(sum(real._exact(proj[i]) for i in pick))} - a mix, "
        f"above the 0.3 of either")

    cnt = 0
    for _ in range(20000):
        v = [rng.choice([round(rng.uniform(0, 9), 2), rng.choice([0.1, 0.2, 0.3, 0.7])]) for _ in range(11)]
        cnt += len({sum(p) for p in (v, v[::-1], sorted(v), rng.sample(v, 11), rng.sample(v, 11))}) > 1
    out()
    out("PART 3  Python's sum() on 20,000 random 11-value lists, 5 orders each")
    out(f"  lists with more than one result {cnt}")
    out(f"  the naive left-to-right loop: (0.1 + 0.2) + 0.3 = {(0.1 + 0.2) + 0.3!r}, (0.3 + 0.2) + 0.1 = "
        f"{(0.3 + 0.2) + 0.1!r}; sum(): {sum([0.1, 0.2, 0.3])!r} and {sum([0.3, 0.2, 0.1])!r}")

    out()
    out("PART 4  candidate tests (scratch form, not in tests/)")
    out(f"  {'test':<6}{'code':<10}{'m03':<26}{'m04':<26}")
    for name, t in (("T1", t1), ("T2", t2)):
        out(f"  {name:<6}{t(real):<10}{t(m03):<26}{t(m04):<26}")
    out("  T1: the 0.1 + 0.2 against 0.3 tie on the values xi_lex hands xi_key, decided by the id list")
    out("  T2: xi_lex returns the XI its key ranks first (xi_key patched to rank the lowest sum first)")

    path = os.path.join(a.out, "check.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run_.wrote(path)
    print(f"written: {path}; provenance: {run_.close()}")


if __name__ == "__main__":
    main()
