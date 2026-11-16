"""S10b (prereg/S10b.md; RULINGS PART F, F-C): 2023/24 and 2024/25 through
Step 10's rule normaliser. Hermetic: toy history folders in temporary
folders; no network, no real data."""
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tools"))

import rules as R                                                 # noqa: E402
from tests.test_S10 import SCORING, TABLE, row                    # noqa: E402

OLD_COLS = ["name", "position", "element", "fixture", "round", "minutes", "goals_scored", "assists", "clean_sheets",
            "goals_conceded", "saves", "penalties_saved", "penalties_missed", "own_goals", "yellow_cards",
            "red_cards", "bonus", "total_points"]               # no defensive-action columns, as 2023/24 and 2024/25


def toy_root(tmp, season="2024-25", rows=None):
    """A history root with one earlier season (no DEFCON columns, a manager
    row) and the 2026/27 table and positions."""
    for d in (season, "2026-27"):
        os.makedirs(os.path.join(tmp, d), exist_ok=True)
    own = R.own_table(TABLE)
    rows = rows or [
        row(element=1, round=1, position="MID", minutes=90, goals_scored=1, clean_sheets=1, assists=1),
        row(element=2, round=1, position="DEF", minutes=90, clean_sheets=1, bonus=2, goals_conceded=0),
        row(element=3, round=1, position="GK", minutes=90, saves=7, goals_conceded=3),
        row(element=4, round=1, position="FWD", minutes=20),
        row(element=2, round=2, fixture=2, position="DEF", minutes=90, goals_conceded=4, yellow_cards=1),
        row(element=5, round=2, fixture=2, position="DEF", minutes=0),
    ]
    with open(os.path.join(tmp, season, "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=OLD_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            pos = R.CSV_POSITION[r["position"]]
            tot = sum(R.score(r, pos, own, 0).values())
            w.writerow(dict(r, name=f"P{r['element']}", total_points=str(tot) if r.get("total_points", "0") == "0" else r["total_points"]))
        w.writerow({c: "0" for c in OLD_COLS} | {"name": "Boss", "position": "AM", "element": "99", "round": "1",
                                                 "total_points": "17"})           # a manager row: out
    with open(os.path.join(tmp, season, "players_raw.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("id,code,element_type\n1,1001,3\n2,1002,2\n3,1003,1\n4,1004,4\n5,1005,2\n99,1099,5\n")
    with open(os.path.join(tmp, "2026-27", "elements_positions.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("id,code,element_type,web_name\n50,1001,4,P1\n51,1002,3,P2\n52,1003,1,P3\n")   # P1 FWD, P2 MID; P4, P5 gone
    with open(os.path.join(tmp, "2026-27", "game_config.json"), "w", encoding="utf-8") as fh:
        json.dump({"scoring": SCORING}, fh)
    return tmp


class OwnTable(unittest.TestCase):
    def test_only_the_defcon_category_changes(self):
        own = R.own_table(TABLE)
        for k in TABLE:
            if k == "defensive_contribution":
                self.assertEqual(own[k], {p: 0 for p in R.POSITIONS})
            else:
                self.assertEqual(own[k], TABLE[k], k)
        self.assertEqual(TABLE["defensive_contribution"]["DEF"], 2)                     # the original untouched
        r = row(position="DEF", minutes=90, clean_sheets=1, defensive_contribution=12)
        self.assertEqual(sum(R.score(r, "DEF", TABLE).values()) - sum(R.score(r, "DEF", own).values()), 2)


class Reproduction(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_share_the_managers_and_a_miss(self):
        toy_root(self.tmp)
        said = []
        primary = R.test_season(self.tmp, "2024-25", say=said.append)
        self.assertEqual(primary, 1.0)
        text = "\n".join(said)
        self.assertIn("1 manager rows out", text)
        self.assertIn("PRIMARY  5 of 5 player-gameweeks with minutes > 0 within +-1: 1.0000", text)   # P5 never played
        self.assertIn("no - DEFCON missing", text)
        self.assertIn("bonus: official, 2024-25 BPS", text)
        bad = [row(element=1, round=1, position="MID", minutes=90, goals_scored=1, total_points=9),   # official 9, re-scored 7
               row(element=2, round=1, position="DEF", minutes=90, clean_sheets=1)]
        tmp2 = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp2, True)
        toy_root(tmp2, rows=bad)
        said = []
        self.assertEqual(R.test_season(tmp2, "2024-25", say=said.append), 0.5)
        self.assertIn("(bar 0.99: FAIL)", "\n".join(said))
        self.assertIn("MID goals_scored 1", "\n".join(said))                               # the miss listed by category
        units = list(R.season_gameweeks([row(element=7, round=1, minutes=90)], lambda r: "MID", TABLE, parts=False).values())
        self.assertEqual(len(units), 1)

    def test_a_season_with_the_parts_rebuilds_defcon(self):
        rows = [row(element=1, position="DEF", minutes=90, clearances_blocks_interceptions=6, tackles=4)]
        units = R.season_gameweeks(rows, lambda r: "DEF", TABLE, parts=True)
        self.assertEqual(units[(1, 1)]["parts"]["defensive_contribution"], 2)               # 10 CBIT: the threshold
        units = R.season_gameweeks(rows, lambda r: "DEF", TABLE, parts=False)
        self.assertEqual(units[(1, 1)]["parts"]["defensive_contribution"], 0)               # missing: never invented


class Normalise(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        toy_root(self.tmp)

    def test_the_output(self):
        out = os.path.join(self.tmp, "out.csv")
        said = []
        R.normalise_season(out, self.tmp, "2024-25", say=said.append)
        with open(out, encoding="utf-8", newline="") as fh:
            got = {(int(r["element"]), int(r["round"])): r for r in csv.DictReader(fh)}
        self.assertNotIn(99, {k[0] for k in got})                                          # the manager row out
        p1 = got[(1, 1)]
        self.assertEqual((p1["position_own"], p1["position_2627"], p1["in_2627"]), ("MID", "FWD", "1"))
        self.assertEqual(int(p1["points_2627_rules"]), 2 + 4 + 3)                           # a FWD's goal, the assist, no clean sheet
        p2 = got[(1 - 1 + 2, 1)]
        self.assertEqual(p2["position_2627"], "MID")
        self.assertEqual(int(p2["clean_sheets"]), 1)                                       # a MID's clean sheet: 1
        self.assertEqual(int(p2["bonus"]), 2); self.assertEqual(p2["bonus_flag"], "2024-25 BPS")
        p4 = got[(4, 1)]
        self.assertEqual((p4["position_2627"], p4["in_2627"]), ("FWD", "0"))                  # gone in 2026/27: own position
        self.assertTrue(all(r["defcon_flag"] == R.DEFCON_MISSING for r in got.values()))
        self.assertTrue(all(int(r["defensive_contribution"]) == 0 for r in got.values()))
        self.assertEqual(int(got[(2, 2)]["official"]), 2 - 2 - 1)                          # own table: 90 min, 4 conceded, a yellow
        self.assertEqual(int(got[(2, 2)]["points_2627_rules"]), 2 - 1)                    # as a 2026/27 MID: no conceded penalty
        self.assertIn("without a code: 0", said[-1]); self.assertIn("('MID', 'FWD'): 1", said[-1])
        self.assertIn("DEFCON missing (0 points, flagged on every row)", said[-1])


class CLI(unittest.TestCase):
    def test_the_season_argument_and_run_txt(self):
        tmp = tempfile.mkdtemp()
        try:
            toy_root(tmp)
            out = os.path.join(tmp, "out")
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(R.main(["test", "--season", "2024-25", "--hist", tmp, "--out", out], say=print), 0)
            with open(os.path.join(out, "rules_test_2024-25.txt"), encoding="utf-8") as fh:
                self.assertIn("PRIMARY  5 of 5", fh.read())
            import provenance as PV
            rec = PV.read_run(out)
            self.assertEqual(rec["tool"], "tools/rules.py"); self.assertIn("rules_test_2024-25.txt", rec["outputs"])
            csv_out = os.path.join(tmp, "n.csv")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(R.main(["normalise", csv_out, "--season", "2024-25", "--hist", tmp], say=print), 0)
            self.assertTrue(os.path.exists(csv_out))
            with self.assertRaises(SystemExit):
                with redirect_stdout(io.StringIO()):
                    R.main(["test", "--season", "2019-20", "--hist", tmp])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'rules')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=HERE, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
