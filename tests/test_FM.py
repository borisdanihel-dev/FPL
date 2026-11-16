"""tests/test_FM.py - status gate v2, the rule behind xp_v2_g2 (prereg/FM.md; Boris's answers of Thu 12 Nov night).

Toys only; standard library; no data, no network. The first part: the rule's pure functions (the table in
prereg/FM.md row by row, the dates, point 5's window). The matrix and the GW4-10 check follow (Tue 17 Nov).
"""
import os
import sys
import unittest
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gate_v2 as G                                               # noqa: E402

GEN = datetime(2026, 11, 16, 1, 20, tzinfo=timezone.utc)
T = 11


def ko(*days):
    return {i: datetime(2026, 11, d, 15, 0, tzinfo=timezone.utc) if d <= 30 else
            datetime(2026, 12, d - 30, 15, 0, tzinfo=timezone.utc) for i, d in enumerate(days, 1)}


class ReturnDate(unittest.TestCase):
    def test_the_two_dated_forms(self):
        self.assertEqual(G.return_date("Suspended until 5 Dec", GEN), date(2026, 12, 5))
        self.assertEqual(G.return_date("Hamstring injury - Expected back 28 Nov", GEN), date(2026, 11, 28))

    def test_the_year_rolls_over(self):
        self.assertEqual(G.return_date("Knee injury - Expected back 3 Jan", GEN), date(2027, 1, 3))
        self.assertEqual(G.return_date("Suspended until 16 Nov", GEN), date(2026, 11, 16))   # today counts

    def test_no_date(self):
        for news in ("Knee injury - Unknown return date", "", None, "Calf injury - 75% chance of playing",
                     "Suspended until further notice", "Expected back 31 Nov"):
            self.assertIsNone(G.return_date(news, GEN), news)


class Kind(unittest.TestCase):
    def test_each_status(self):
        self.assertEqual(G.kind({"status": "a"}, GEN)[0], "a")
        self.assertEqual(G.kind({"status": "d", "chance_next_round": 75}, GEN), ("d", None, 0.75))
        self.assertEqual(G.kind({"status": "s", "news": "Suspended until 5 Dec"}, GEN), ("dated", date(2026, 12, 5), None))
        self.assertEqual(G.kind({"status": "s", "news": "Suspended"}, GEN)[0], "s")
        self.assertEqual(G.kind({"status": "i", "news": "Thigh injury - Expected back 28 Nov"}, GEN)[:2],
                         ("dated", date(2026, 11, 28)))
        self.assertEqual(G.kind({"status": "i", "news": "Knee injury - Unknown return date"}, GEN)[0], "i")
        for st in ("u", "n", None):
            self.assertEqual(G.kind({"status": st}, GEN)[0], "out")


class WeekPlan(unittest.TestCase):
    """prereg/FM.md's table, row by row."""

    def test_a_is_v1(self):
        for u in range(T, T + 6):
            self.assertEqual(G.week_plan("a", None, None, u, T, ko(21)), ("v1", None))

    def test_d_lifted_in_t_then_normal(self):
        self.assertEqual(G.week_plan("d", None, 0.5, T, T, ko(21)), ("lifted", None))
        self.assertEqual(G.week_plan("d", None, 0.5, T + 1, T, ko(28)), ("normal", None))

    def test_dated_zero_before_the_date_then_normal(self):
        when = date(2026, 12, 5)
        self.assertEqual(G.week_plan("dated", when, None, T, T, ko(21)), ("out", None))
        self.assertEqual(G.week_plan("dated", when, None, T + 3, T, ko(35)), ("normal", None))   # on the date: plays
        self.assertEqual(G.week_plan("dated", when, None, T + 3, T, ko(34, 37)), ("normal", [2]))  # a split double

    def test_s_without_a_date(self):
        self.assertEqual(G.week_plan("s", None, None, T, T, ko(21)), ("out", None))
        self.assertEqual(G.week_plan("s", None, None, T + 1, T, ko(28)), ("normal", None))

    def test_i_unknown_return(self):
        self.assertEqual(G.week_plan("i", None, None, T, T, ko(21)), ("out", None))
        self.assertEqual(G.week_plan("i", None, None, T + 1, T, ko(28)), ("out", None))
        self.assertEqual(G.week_plan("i", None, None, T + 2, T, ko(35)), ("half", None))
        self.assertEqual(G.HALF, 0.5)

    def test_u_and_n_out(self):
        for u in range(T, T + 6):
            self.assertEqual(G.week_plan("out", None, None, u, T, ko(21)), ("out", None))


class PointFive(unittest.TestCase):
    """Suspended gameweeks count as neither started nor missed: the window is the last four unsuspended ones."""

    ROWS = [{"player_id": 1, "event": e, "starts": s, "minutes": m}
            for e, s, m in ((5, 1, 90), (6, 1, 90), (7, 1, 90), (8, 1, 60))] + \
           [{"player_id": 2, "event": e, "starts": 1, "minutes": 90} for e in (5, 6, 7, 8, 9, 10)]

    def test_suspended_gameweeks_leave_the_window(self):
        w = G.window(self.ROWS, 10, {1: {9, 10}})
        self.assertEqual(w[1], (4, 330.0, 4))            # GW5-8, not GW7-10 with two missed
        self.assertEqual(G.window(self.ROWS, 10, {})[1], (2, 150.0, 4))   # v1's window: GW7-10
        self.assertEqual(w[2], (4, 360.0, 4))

    def test_suspensions_from_the_archive_and_unknown_weeks(self):
        from datetime import timedelta
        base = datetime(2026, 8, 20, 10, tzinfo=timezone.utc)
        dl = {e: base + timedelta(days=7 * e) for e in range(1, 6)}
        exports = [(dl[e] - timedelta(days=1), "p",
                    {"all_players": [{"id": 1, "status": "s" if e == 4 else "a"}, {"id": 2, "status": "i"}]})
                   for e in (3, 4, 5)]
        sus, unknown = G.suspensions(exports, dl, 5)
        self.assertEqual(sus[1], {4})
        self.assertNotIn(2, sus)                          # injured is not suspended
        self.assertEqual(unknown, {1, 2})


if __name__ == "__main__":
    unittest.main()
