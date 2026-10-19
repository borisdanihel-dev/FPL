"""S10 (BUILD_PLAN.md Step 10; prereg/S10.md): the rule normaliser, on toy
rows. Hermetic: a toy game_config, no real data, no network."""

import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tools"))

import rules as R           # noqa: E402

SCORING = {"short_play": 1, "long_play": 2, "assists": 3, "saves": 1, "penalties_saved": 5,
           "penalties_missed": -2, "own_goals": -2, "yellow_cards": -1, "red_cards": -3, "bonus": 1,
           "goals_scored": {"GKP": 10, "DEF": 6, "MID": 5, "FWD": 4},
           "clean_sheets": {"GKP": 4, "DEF": 4, "MID": 1, "FWD": 0},
           "goals_conceded": {"GKP": -1, "DEF": -1, "MID": 0, "FWD": 0},
           "defensive_contribution": {"GKP": 0, "DEF": 2, "MID": 2, "FWD": 2},
           "bps": 0, "influence": 0}          # extra keys are ignored
TABLE = R.load_table({"scoring": SCORING})
ZERO = {k: 0 for k in ("minutes", "goals_scored", "assists", "clean_sheets", "goals_conceded", "saves",
                       "penalties_saved", "penalties_missed", "own_goals", "yellow_cards", "red_cards",
                       "defensive_contribution", "bonus", "clearances_blocks_interceptions", "tackles",
                       "recoveries", "total_points")}


def row(**kw):
    r = dict(ZERO, element=1, round=1, fixture=1, position="MID")
    r.update(kw)
    return {k: str(v) for k, v in r.items()}


def pts(pos="MID", **kw):
    return sum(R.score(row(**kw), pos, TABLE).values())


class Table(unittest.TestCase):

    def test_every_category_read_and_a_missing_one_raises(self):
        self.assertEqual(TABLE["goals_scored"]["GKP"], 10)
        self.assertEqual(TABLE["long_play"], 2)
        for drop in ("saves", "bonus", "long_play"):
            with self.subTest(drop=drop), self.assertRaises(KeyError):
                R.load_table({"scoring": {k: v for k, v in SCORING.items() if k != drop}})
        partial = dict(SCORING, clean_sheets={"GKP": 4, "DEF": 4, "MID": 1})
        with self.assertRaises(KeyError):
            R.load_table({"scoring": partial})


class Score(unittest.TestCase):
    """Each category and each threshold edge."""

    def test_appearance(self):
        self.assertEqual(pts(minutes=0), 0)
        self.assertEqual(pts(minutes=1), 1)
        self.assertEqual(pts(minutes=59), 1)
        self.assertEqual(pts(minutes=60), 2)

    def test_goals_and_assists_by_position(self):
        for pos, g in (("GKP", 10), ("DEF", 6), ("MID", 5), ("FWD", 4)):
            self.assertEqual(pts(pos, minutes=90, goals_scored=1) - 2, g, pos)
        self.assertEqual(pts(minutes=90, assists=2) - 2, 6)

    def test_clean_sheet_needs_sixty_minutes(self):
        self.assertEqual(pts("DEF", minutes=60, clean_sheets=1), 2 + 4)
        self.assertEqual(pts("DEF", minutes=59, clean_sheets=1), 1)
        self.assertEqual(pts("MID", minutes=90, clean_sheets=1), 2 + 1)
        self.assertEqual(pts("FWD", minutes=90, clean_sheets=1), 2)

    def test_per_two_conceded_and_per_three_saves(self):
        self.assertEqual(pts("GKP", minutes=90, goals_conceded=1), 2)
        self.assertEqual(pts("GKP", minutes=90, goals_conceded=2), 1)
        self.assertEqual(pts("GKP", minutes=90, goals_conceded=5), 0)
        self.assertEqual(pts("MID", minutes=90, goals_conceded=4), 2)
        self.assertEqual(pts("GKP", minutes=90, saves=2), 2)
        self.assertEqual(pts("GKP", minutes=90, saves=3), 3)
        self.assertEqual(pts("GKP", minutes=90, saves=7), 4)

    def test_penalties_own_goals_cards_bonus(self):
        self.assertEqual(pts("GKP", minutes=90, penalties_saved=1), 7)
        self.assertEqual(pts(minutes=90, penalties_missed=1, own_goals=1, yellow_cards=1, red_cards=1), 2 - 8)
        self.assertEqual(pts(minutes=90, bonus=3), 5)

    def test_a_bench_card_counts_without_appearance(self):
        self.assertEqual(pts(minutes=0, yellow_cards=1), -1)

    def test_defensive_contribution_thresholds(self):
        self.assertEqual(pts("DEF", minutes=90, defensive_contribution=9), 2)
        self.assertEqual(pts("DEF", minutes=90, defensive_contribution=10), 4)
        self.assertEqual(pts("MID", minutes=90, defensive_contribution=11), 2)
        self.assertEqual(pts("MID", minutes=90, defensive_contribution=12), 4)
        self.assertEqual(pts("FWD", minutes=90, defensive_contribution=12), 4)
        self.assertEqual(pts("GKP", minutes=90, defensive_contribution=30), 2)

    def test_defcon_rebuilt_from_its_parts(self):
        r = row(clearances_blocks_interceptions=5, tackles=4, recoveries=3)
        self.assertEqual(R.defcon_count(r, "DEF"), 9)
        self.assertEqual(R.defcon_count(r, "MID"), 12)
        self.assertEqual(R.defcon_count(r, "FWD"), 12)
        self.assertIsNone(R.defcon_count(r, "GKP"))
        self.assertEqual(sum(R.score(row(minutes=90, clearances_blocks_interceptions=5, tackles=4,
                                         recoveries=3), "MID", TABLE, R.defcon_count(r, "MID")).values()), 4)


class PlayerGameweeks(unittest.TestCase):

    def test_a_double_gameweek_is_one_unit(self):
        rows = [row(element=7, round=5, fixture=1, minutes=90, goals_scored=1, total_points=7),
                row(element=7, round=5, fixture=2, minutes=30, total_points=1),
                row(element=8, round=5, fixture=1, minutes=0)]
        units = R.player_gameweeks(rows, lambda r: "MID", TABLE)
        self.assertEqual(units[(7, 5)]["points"], 8)
        self.assertEqual(units[(7, 5)]["official"], 8)
        self.assertEqual(units[(7, 5)]["minutes"], 120)
        self.assertEqual(units[(8, 5)]["minutes"], 0)

    def test_share_and_bootstrap(self):
        units = [{"round": g, "points": 2, "official": 2 + (g == 3 and i == 0) * 2} for g in range(1, 6)
                 for i in range(10)]
        self.assertAlmostEqual(R.share(units, R.within), 49 / 50)
        lo, hi = R.bootstrap(units, R.within, n=2000, seed=7)
        self.assertLessEqual(lo, 49 / 50)
        self.assertGreaterEqual(hi, 49 / 50)
        self.assertEqual((lo, hi), R.bootstrap(units, R.within, n=2000, seed=7))
        self.assertTrue(R.within({"points": 3, "official": 4}))
        self.assertFalse(R.within({"points": 3, "official": 5}))

    def test_the_bootstrap_uses_its_seed(self):
        import random as real
        seeds = []

        class Spy(real.Random):
            def __init__(self, *a):
                seeds.append(a)
                super().__init__(*a)
        saved = R.random.Random
        R.random.Random = Spy
        try:
            R.bootstrap([{"round": 1, "points": 1, "official": 1}], R.within, n=10, seed=20261019)
        finally:
            R.random.Random = saved
        self.assertEqual(seeds, [(20261019,)])


class Assists(unittest.TestCase):

    def test_no_change_is_a_printed_no_op(self):
        factor, line = R.assists_line(TABLE, 3)
        self.assertEqual(factor, 1.0)
        self.assertIn("no change, no rescale", line)
        factor, line = R.assists_line(dict(TABLE, assists=4), 3)
        self.assertAlmostEqual(factor, 4 / 3)
        self.assertIn("rescaled", line)


class Normalise(unittest.TestCase):
    """A toy history folder: a reclassified player re-scored in the new
    position, a player absent in 2026/27 kept and flagged, bonus flagged."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for d in ("2025-26", "2026-27"):
            os.makedirs(os.path.join(self.tmp, d))
        cols = ["name", "position", "element", "fixture", "round", *ZERO]
        rows = [row(element=1, position="MID", minutes=90, goals_scored=1, clean_sheets=1, total_points=8),
                row(element=2, position="DEF", minutes=90, bonus=2, total_points=4)]
        with open(os.path.join(self.tmp, "2025-26", "merged_gw.csv"), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow(dict(r, name=f"P{r['element']}"))
        with open(os.path.join(self.tmp, "2025-26", "players_raw.csv"), "w", encoding="utf-8", newline="") as fh:
            fh.write("id,code,element_type\n1,1001,3\n2,1002,2\n")
        with open(os.path.join(self.tmp, "2026-27", "elements_positions.csv"), "w", encoding="utf-8", newline="") as fh:
            fh.write("id,code,element_type,web_name\n50,1001,4,P1\n")      # P1 now a FWD; P2 gone
        with open(os.path.join(self.tmp, "2026-27", "game_config.json"), "w", encoding="utf-8") as fh:
            json.dump({"scoring": SCORING}, fh)

    def test_the_output(self):
        out = os.path.join(self.tmp, "out.csv")
        said = []
        R.normalise(out, hist=self.tmp, say=said.append)
        with open(out, encoding="utf-8", newline="") as fh:
            got = {int(r["element"]): r for r in csv.DictReader(fh)}
        p1, p2 = got[1], got[2]
        self.assertEqual((p1["position_2526"], p1["position_2627"], p1["in_2627"]), ("MID", "FWD", "1"))
        self.assertEqual(int(p1["points_2627_rules"]), 2 + 4 + 0)          # a FWD's goal and no clean sheet
        self.assertEqual(int(p1["official_2526"]), 8)
        self.assertEqual((p2["position_2627"], p2["in_2627"]), ("DEF", "0"))
        self.assertEqual(p2["bonus_flag"], "2025/26 BPS")
        self.assertEqual(int(p2["bonus"]), 2)
        self.assertIn("no change, no rescale", said[0])
        self.assertIn("('MID', 'FWD'): 1", said[-1])

    def test_the_reproduction_test_runs_on_toy_data(self):
        said = []
        primary = R.test(hist=self.tmp, say=said.append)
        self.assertEqual(primary, 1.0)
        self.assertTrue(said[1].startswith("PRIMARY  2 of 2 player-gameweeks"))
        self.assertIn("bonus: official, 2025/26 BPS", said[-1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
