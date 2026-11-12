"""tests/test_FJ.py - the GW10 checkpoint's script, worklog/checkpoint_gw10/checkpoint.py (prereg/FJ.md).

Boris's rulings of Thu 12 Nov night, FJ point 2 (verbatim in prereg/FJ.md): "Add tests/test_FJ.py (the sign of d;
the revert verdict on a toy; the tie order), since F-L re-runs this script at GW15."
Standard library only; no data, no network.
"""
import importlib.util
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
_spec = importlib.util.spec_from_file_location("fj_checkpoint", os.path.join(ROOT, "worklog", "checkpoint_gw10", "checkpoint.py"))
CK = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CK)
import fpl_bt as BT                                               # noqa: E402

# a legal 15 in slot order (1 GK, 2 DEF, 3 MID, 4 FWD): three defenders without an own forecast (counted 0) tie for
# the third DEF place; in slot order the first of them is id 230 (slot 3), by id it is 8 (slot 14), as in GW9
SQUAD = [{"id": i, "pos": p} for i, p in (
    (11, 1), (21, 2), (230, 2), (22, 2), (31, 3), (32, 3), (33, 3), (34, 3), (35, 3), (41, 4), (42, 4),
    (12, 1), (43, 4), (8, 2), (173, 2))]
OWN = {11: 2.0, 12: 1.0, 21: 3.0, 22: 2.0, 31: 3.0, 32: 3.0, 33: 3.0, 34: 3.0, 35: 3.0, 41: 4.0, 42: 3.5, 43: 0.5}
ACTUAL = {i: (2.0, 90.0) for i in OWN}
ACTUAL.update({230: (9.0, 90.0), 8: (6.0, 90.0), 173: (0.0, 0.0)})


def xi_ids(squad, proj, tie):
    return {r["id"] for r in CK.choice(CK.ordered(squad, tie), proj, ACTUAL)[0]}


class TieOrder(unittest.TestCase):
    def test_slot_order_follows_the_picks_and_id_order_the_lower_id(self):
        self.assertIn(230, xi_ids(SQUAD, OWN, "slot"))
        self.assertNotIn(8, xi_ids(SQUAD, OWN, "slot"))
        self.assertIn(8, xi_ids(SQUAD, OWN, "id"))
        self.assertNotIn(230, xi_ids(SQUAD, OWN, "id"))
        slot = CK.score(SQUAD, OWN, OWN, ACTUAL, "slot")
        by_id = CK.score(SQUAD, OWN, OWN, ACTUAL, "id")
        self.assertEqual(slot[0] - by_id[0], 9.0 - 6.0)              # the tied defender's points, nothing else
        self.assertEqual([r["id"] for r in CK.ordered(SQUAD, "id")], sorted(r["id"] for r in SQUAD))
        self.assertEqual(CK.ordered(SQUAD, "slot"), SQUAD)
        with self.assertRaises(ValueError):
            CK.ordered(SQUAD, "name")

    def test_the_default_is_the_pinned_slot_order(self):
        self.assertEqual(CK.score(SQUAD, OWN, OWN, ACTUAL), CK.score(SQUAD, OWN, OWN, ACTUAL, "slot"))


class SignOfD(unittest.TestCase):
    def test_d_is_xp_v2_minus_own(self):
        self.assertEqual(CK.paired([41, 72, 62], [41, 68, 74]), [0, -4, 12])
        xp = {**OWN, 43: 5.0, 42: 0.4}                         # xp_v2 starts 43, who scores 12; own starts 42 (2)
        actual = {**ACTUAL, 43: (12.0, 90.0)}
        own_pts, _, v2_pts, cap_v2 = CK.score(SQUAD, OWN, xp, actual)
        self.assertEqual(cap_v2, 43)                                  # the highest xp_v2 in its XI, doubled
        d = CK.paired([own_pts], [v2_pts])[0]
        self.assertGreater(d, 0)
        self.assertEqual(d, v2_pts - own_pts)


class RevertVerdict(unittest.TestCase):
    def test_own_returns_only_when_the_upper_bound_is_below_zero(self):
        self.assertEqual(CK.verdict({"lo": -9.0, "hi": -0.01}), "own returns")
        self.assertEqual(CK.verdict({"lo": -9.0, "hi": 0.0}), "xp_v2 stays")
        self.assertEqual(CK.verdict({"lo": -2.67, "hi": 8.0}), "xp_v2 stays")
        self.assertEqual(CK.verdict({"lo": -9.0, "hi": 8.0}), "xp_v2 stays")    # never read off the lower bound

    def test_on_toy_gameweeks(self):
        worse = BT.bootstrap_mean([-5, -3, -4])
        self.assertLess(worse["hi"], 0)
        self.assertEqual(CK.verdict(worse), "own returns")
        gw10 = BT.bootstrap_mean([0, -4, 12])
        self.assertAlmostEqual(gw10["lo"], -8 / 3)
        self.assertEqual(gw10["hi"], 8.0)
        self.assertEqual(CK.verdict(gw10), "xp_v2 stays")


if __name__ == "__main__":
    unittest.main()
