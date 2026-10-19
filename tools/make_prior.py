"""tools/make_prior.py - W3: the S11 prior file the runner reads
(prereg/W3.md, design (1)). Offline; standard library only; the nightly
never imports it.

The runner has no historical/ folder and its record never opens the
database, so last season's S11 prior travels as a committed file,
priors/s11_prior_<season>.json:

  - S11's Prior state (tools/shares.py) on historical/<season>: the per
    (name, club) sums of xg, xa, team xg, team xa and minutes with the
    position, in S11's order; k and rel per metric;
  - code_name: the player's code -> his <season> vaastav name, by
    players_raw.csv (code -> id) and merged_gw.csv (id -> the first name
    seen), as tools/xp_v2_live.py's prior_names;
  - the SHA-256 of each input file.

JSON floats round-trip exactly; fpl_shares.Prior rebuilds the rest with
S11's rule. --check regenerates in memory and compares byte for byte.

    python tools/make_prior.py [--hist ROOT] [--out FILE] [--check]
"""
import argparse
import csv
import hashlib
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shares as SH                                               # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

SEASON = "2025-26"                  # last season (BUILD_PLAN.md Step 11; RULING 19 Oct afternoon point 2)
INPUTS = ("merged_gw.csv", "teams.csv", "players_raw.csv")
OUT = os.path.join(ROOT, "priors", f"s11_prior_{SEASON}.json")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def code_names(folder):
    """{code: name} as tools/xp_v2_live.py's prior_names reaches a name:
    players_raw code -> id, merged_gw id -> the first name seen; codes whose
    id has no merged_gw row are left out (prior_names falls back then)."""
    with open(os.path.join(folder, "players_raw.csv"), encoding="utf-8", newline="") as fh:
        id25 = {r["code"]: int(r["id"]) for r in csv.DictReader(fh)}
    name25 = {}
    with open(os.path.join(folder, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            name25.setdefault(int(r["element"]), r["name"])
    return {code: name25[i] for code, i in id25.items() if i in name25}


def state_of(folder, season=SEASON):
    for name in INPUTS:
        if not os.path.exists(os.path.join(folder, name)):
            raise SH.MissingInput(f"{os.path.join(folder, name)} is missing")
    prior = SH.Prior(folder)
    return {"season": season, "folder": f"historical/{season}", "made_by": "tools/make_prior.py (W3)",
            "inputs": {name: sha256(os.path.join(folder, name)) for name in INPUTS},
            "prior_mins": SH.PRIOR_MINS, "k": prior.k, "rel": prior.rel,
            "by_name_club": [[name, club, a] for (name, club), a in prior.by_name_club.items()],
            "code_name": code_names(folder)}


def render(state):
    """The file's text: one (name, club) entry and one code per line, so a
    regeneration diffs line by line; ASCII only."""
    lines = ["{"]
    for key in ("season", "folder", "made_by", "inputs", "prior_mins", "k", "rel"):
        lines.append(f" {json.dumps(key)}: {json.dumps(state[key], sort_keys=True)},")
    lines.append(' "by_name_club": [')
    lines.append(",\n".join("  " + json.dumps(e, sort_keys=True) for e in state["by_name_club"]))
    lines.append(" ],")
    lines.append(' "code_name": {')
    lines.append(",\n".join(f"  {json.dumps(c)}: {json.dumps(n)}"
                            for c, n in sorted(state["code_name"].items(), key=lambda kv: int(kv[0]))))
    lines.append(" }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"))
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--check", action="store_true", help="regenerate in memory and compare with --out byte for byte")
    a = ap.parse_args(argv)
    try:
        text = render(state_of(os.path.join(a.hist, SEASON)))
    except SH.MissingInput as e:
        print(f"missing input: {e} - nothing written")
        return 2
    if a.check:
        with open(a.out, encoding="utf-8", newline="") as fh:
            same = fh.read() == text
        print(f"{a.out}: {'identical to' if same else 'DIFFERS from'} a regeneration from {os.path.join(a.hist, SEASON)}")
        return 0 if same else 1
    run = Run("tools/make_prior.py", os.path.join(ROOT, "tools", "out", "make_prior"), argv)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    run.wrote(a.out)
    print(f"written: {a.out} ({len(text.encode('utf-8'))} bytes); provenance: {run.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
