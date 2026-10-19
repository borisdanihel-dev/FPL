"""S16 part 1 (BUILD_PLAN.md Step 16 point 1; prereg/S16.md part 1; RULING
lane A 19 Oct midday point 2): blank and double gameweek history from each
fixture's FPL event. Hermetic: toy fixtures files in a temporary folder."""

import csv
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tools"))

import blank_double as B    # noqa: E402

# a toy season of 4 teams: GW1 normal, GW2 team 4 blanks and team 1 doubles,
# GW3 team 2 plays three times, one fixture unscheduled
TOY = [(1, 1, 2), (1, 3, 4),
       (2, 1, 2), (2, 1, 3),
       (3, 2, 1), (3, 2, 3), (3, 2, 4),
       (None, 3, 1)]


def write_fixtures(folder, fixtures):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "fixtures.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["code", "event", "finished", "id", "kickoff_time", "minutes", "team_a", "team_h"])
        for i, (e, h, a) in enumerate(fixtures, 1):
            w.writerow([1000 + i, "" if e is None else e, "True", i, "2025-01-01T15:00:00Z", 90, a, h])
    return path


class Counts(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = write_fixtures(os.path.join(self.tmp, "2024-25"), TOY)

    def test_blanks_doubles_triples_and_the_unscheduled(self):
        n, unscheduled, teams, events = B.counts(B.read_fixtures(self.path))
        self.assertEqual(teams, [1, 2, 3, 4])
        self.assertEqual(events, [1, 2, 3])
        self.assertEqual(unscheduled, [(3, 1)])
        self.assertEqual([n[(1, t)] for t in teams], [1, 1, 1, 1])
        self.assertEqual([n[(2, t)] for t in teams], [2, 1, 1, 0])
        self.assertEqual([n[(3, t)] for t in teams], [1, 3, 1, 1])
        bd = B.blanks_and_doubles(n)
        self.assertEqual(sorted(bd), [2, 3])
        self.assertEqual(bd[2], {"blank": [4], "double": [(1, 2)]})
        self.assertEqual(bd[3], {"blank": [], "double": [(2, 3)]})

    def test_the_straight_count_and_the_comparator(self):
        n, _, _, _ = B.counts(B.read_fixtures(self.path))
        ref = B.straight_count(self.path)
        self.assertEqual(B.compare(n, ref), [])
        ref[(2, 4)] = 1                                       # one changed count is caught
        self.assertEqual(B.compare(n, ref), [((2, 4), 0, 1)])
        del ref[(2, 4)]
        ref[(3, 2)] = 2
        self.assertEqual(B.compare(n, ref), [((3, 2), 3, 2)])
        del ref[(3, 2)]                                       # a count the reference lacks entirely
        self.assertEqual(B.compare(n, ref), [((3, 2), 3, 0)])

    def test_events_above_38_are_kept_and_flagged(self):
        path = write_fixtures(os.path.join(self.tmp, "2019-20"),
                             [(1, 1, 2), (1, 3, 4), (39, 1, 3), (39, 2, 4)])
        n, _, _, events = B.counts(B.read_fixtures(path))
        self.assertEqual(events, [1, 39])
        said = []
        B.history(self.tmp, say=said.append)
        line = next(s for s in said if s.startswith("2019-20:"))
        self.assertIn("numbered above 38: [39]", line)
        self.assertIn("unused numbers: [2, 3,", line)

    def test_the_history_and_the_table(self):
        said = []
        table = B.history(self.tmp, say=said.append)
        self.assertIn("2024-25: 4 teams, 3 events; 1 unscheduled fixtures; 1 team blanks, 2 team doubles", said)
        self.assertIn("  GW2: blank 1: team 4; double 1: team 1", said)
        self.assertIn("  GW3: double 1: team 2 x3", said)
        self.assertEqual(table[2]["blank"], 1)
        self.assertEqual(table[3]["double"], 1)
        self.assertIn("2018-19: no fixtures.csv - skipped", said)

    def test_the_reproduction_test_on_toys(self):
        write_fixtures(os.path.join(self.tmp, "2025-26"), TOY[:4])
        said = []
        self.assertTrue(B.test(self.tmp, say=said.append))
        self.assertEqual(said[-1], "REPRODUCTION PASS")

    def test_a_differing_count_fails_the_reproduction(self):
        write_fixtures(os.path.join(self.tmp, "2025-26"), TOY[:4])
        saved = B.straight_count
        B.straight_count = lambda path: {**saved(path), (1, 1): 2}
        said = []
        try:
            self.assertFalse(B.test(self.tmp, say=said.append))
        finally:
            B.straight_count = saved
        self.assertEqual(said[-1], "REPRODUCTION FAIL")
        self.assertIn("1 differ: [((1, 1), 1, 2)]", said[0])

    def test_files_are_only_read(self):
        before = open(self.path, "rb").read()
        B.history(self.tmp, say=lambda s: None)
        B.straight_count(self.path)
        self.assertEqual(open(self.path, "rb").read(), before)


class Isolated(unittest.TestCase):
    """The tool runs under python -I: no import from its folder or the
    repository is needed (downloads are data, never code)."""

    def test_it_runs_isolated(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        write_fixtures(os.path.join(tmp, "2024-25"), TOY[:2])
        write_fixtures(os.path.join(tmp, "2025-26"), TOY[:2])
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "tools", "blank_double.py"), "test",
                            "--hist", tmp], capture_output=True, text=True, cwd=tmp)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("REPRODUCTION PASS", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
