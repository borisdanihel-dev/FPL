"""S16 part 2 (BUILD_PLAN.md Step 16, point 2; prereg/S16.md): the 2026/27
calendar mapper. Hermetic: the 2026/27 deadlines are frozen here, the database
is a temporary file, no time-zone database is used."""

import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tools"))

import calendar_2627 as K   # noqa: E402

UTC = timezone.utc
# events.deadline_time of 2026/27, as fpl.sqlite held it on 18 Oct 2026
DEADLINES = [
    "2026-08-21T17:30:00Z", "2026-08-28T17:30:00Z", "2026-09-04T17:30:00Z", "2026-09-12T12:30:00Z",
    "2026-09-18T17:30:00Z", "2026-10-10T10:00:00Z", "2026-10-17T10:00:00Z", "2026-10-23T17:30:00Z",
    "2026-10-31T11:00:00Z", "2026-11-06T18:30:00Z", "2026-11-21T11:00:00Z", "2026-11-27T18:30:00Z",
    "2026-12-02T18:30:00Z", "2026-12-05T13:30:00Z", "2026-12-12T13:30:00Z", "2026-12-19T13:30:00Z",
    "2026-12-26T11:00:00Z", "2026-12-29T18:00:00Z", "2027-01-01T18:30:00Z", "2027-01-05T18:00:00Z",
    "2027-01-16T13:30:00Z", "2027-01-23T13:30:00Z", "2027-01-30T13:30:00Z", "2027-02-06T13:30:00Z",
    "2027-02-10T18:30:00Z", "2027-02-20T13:30:00Z", "2027-02-27T13:30:00Z", "2027-03-03T18:30:00Z",
    "2027-03-13T13:30:00Z", "2027-03-20T13:30:00Z", "2027-04-10T12:30:00Z", "2027-04-17T12:30:00Z",
    "2027-04-24T12:30:00Z", "2027-05-01T12:30:00Z", "2027-05-08T12:30:00Z", "2027-05-15T12:30:00Z",
    "2027-05-23T12:30:00Z", "2027-05-30T13:30:00Z"]
DLS = [(g, K.utc(t)) for g, t in enumerate(DEADLINES, 1)]


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


class UkDay(unittest.TestCase):
    """A date is a UK calendar day; BST from 01:00 UTC on the last Sunday of
    March to 01:00 UTC on the last Sunday of October."""

    def test_gmt_and_bst_days(self):
        self.assertEqual(K.uk_day(date(2027, 3, 21)), (at("2027-03-21T00:00"), at("2027-03-22T00:00")))
        self.assertEqual(K.uk_day(date(2027, 4, 24)), (at("2027-04-23T23:00"), at("2027-04-24T23:00")))

    def test_both_switch_days(self):
        self.assertEqual(K.uk_day(date(2027, 3, 28)), (at("2027-03-28T00:00"), at("2027-03-28T23:00")))
        self.assertEqual(K.uk_day(date(2026, 10, 25)), (at("2026-10-24T23:00"), at("2026-10-26T00:00")))

    def test_the_offset_turns_at_one_utc(self):
        self.assertEqual(K.uk_offset(at("2027-03-28T00:59")), timedelta(0))
        self.assertEqual(K.uk_offset(at("2027-03-28T01:00")), timedelta(hours=1))
        self.assertEqual(K.uk_offset(at("2026-10-25T00:59")), timedelta(hours=1))
        self.assertEqual(K.uk_offset(at("2026-10-25T01:00")), timedelta(0))


class Mapping(unittest.TestCase):
    """Windows [deadline g, deadline g+1); a day holding a deadline is
    ambiguous and named both ways, never a side."""

    def test_a_day_inside_one_window(self):
        m = K.map_date(DLS, date(2027, 3, 21))
        self.assertEqual(m["gw"], 30)
        self.assertNotIn("between", m)
        self.assertEqual(m["prev"], (30, at("2027-03-20T13:30")))
        self.assertEqual(m["next"], (31, at("2027-04-10T12:30")))

    def test_a_day_holding_a_deadline_is_ambiguous(self):
        m = K.map_date(DLS, date(2027, 4, 24))
        self.assertNotIn("gw", m)
        self.assertEqual(m["between"], (32, 33))
        self.assertEqual(m["deadlines"], [(33, at("2027-04-24T12:30"))])

    def test_a_deadline_just_after_uk_midnight_in_bst_belongs_to_that_day(self):
        dls = [(1, at("2027-04-01T12:00")), (2, at("2027-04-23T23:30"))]      # 00:30 UK on 24 Apr
        self.assertEqual(K.map_date(dls, date(2027, 4, 24))["between"], (1, 2))
        self.assertEqual(K.map_date(dls, date(2027, 4, 23))["gw"], 1)

    def test_a_deadline_at_the_very_start_of_the_day_leaves_it_whole(self):
        dls = [(1, at("2027-04-01T12:00")), (2, at("2027-04-23T23:00"))]      # 00:00 UK on 24 Apr
        self.assertEqual(K.map_date(dls, date(2027, 4, 24))["gw"], 2)

    def test_before_gw1_is_an_error_and_after_gw38_is_gw38(self):
        with self.assertRaises(ValueError):
            K.map_date(DLS, date(2026, 8, 1))
        m = K.map_date(DLS, date(2027, 6, 1))
        self.assertEqual(m["gw"], 38)
        self.assertEqual(m["next"], (None, None))
        self.assertEqual(K.map_date(DLS, date(2026, 8, 21))["between"], (None, 1))

    def test_the_four_plan_dates_on_the_2026_27_deadlines(self):
        got = {name: K.map_date(DLS, d) for name, d in K.DATES}
        self.assertEqual(got["Carabao Cup final"]["gw"], 30)
        self.assertEqual(got["FA Cup quarter-finals"]["gw"], 30)
        self.assertEqual(got["FA Cup semi-finals"]["between"], (32, 33))
        self.assertEqual(got["FA Cup final"]["gw"], 36)
        self.assertEqual([d for _, d in K.DATES],
                         [date(2027, 3, 21), date(2027, 4, 3), date(2027, 4, 24), date(2027, 5, 22)])


class Database(unittest.TestCase):
    """Read-only, and the league fixtures of each UK day counted."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "fpl.sqlite")
        con = sqlite3.connect(self.path)
        con.executescript("CREATE TABLE events (id INTEGER PRIMARY KEY, deadline_time TEXT);"
                          "CREATE TABLE fixtures (id INTEGER PRIMARY KEY, event INTEGER, kickoff_time TEXT);")
        con.executemany("INSERT INTO events VALUES (?,?)", list(enumerate(DEADLINES, 1)))
        con.executemany("INSERT INTO fixtures VALUES (?,?,?)",
                        [(1, 33, "2027-04-24T14:00:00Z"), (2, 33, "2027-04-23T23:30:00Z"),   # both 24 Apr UK
                         (3, 32, "2027-04-23T22:30:00Z"), (4, 33, None)])                   # 23 Apr UK; no time
        con.commit()
        con.close()

    def test_the_database_is_opened_read_only(self):
        with open(self.path, "rb") as fh:
            before = fh.read()
        out = []
        self.assertEqual(K.main([self.path], say=out.append), 0)
        with open(self.path, "rb") as fh:
            self.assertEqual(fh.read(), before)
        con = K.connect(self.path)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                con.execute("CREATE TABLE x (a)")
        finally:
            con.close()
        self.assertEqual(len(out), 5)
        self.assertIn("(read-only)", out[0])
        self.assertIn("GW32 or GW33", out[3])
        self.assertTrue(out[3].endswith("league fixtures that day: 2"), out[3])

    def test_fixtures_are_counted_by_the_uk_day(self):
        con = K.connect(self.path)
        try:
            self.assertEqual(K.fixtures_that_day(con, date(2027, 4, 24)), 2)
            self.assertEqual(K.fixtures_that_day(con, date(2027, 4, 23)), 1)
        finally:
            con.close()

    def test_a_missing_database_says_so(self):
        out = []
        self.assertEqual(K.main([os.path.join(self.tmp, "none.sqlite")], say=out.append), 1)
        self.assertTrue(out[0].startswith("no database at"))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "none.sqlite")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
