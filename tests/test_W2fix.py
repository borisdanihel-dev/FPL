"""tests/test_W2fix.py - W2fix: the multiplier check promotes the vice-captain
when the captain played 0 minutes (prereg/W2fix.md). Hermetic: S9's toy
league in a temporary folder; both modules, the runner's fpl_league and the
offline tools/league."""
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tools"))

from tests.test_S9 import toy_league, RIVAL_B   # noqa: E402

CAP, VICE, BENCH_MID = 10, 17, 14               # rival B's captain (slot 6), the vice (slot 10), a bench MID (slot 14)
EV = 4                                          # a settled gameweek of the toy


def vice_case(tmp, chip=None, cap_minutes=(0,), vice_mult=2):
    """S9's toy league with rival B's GW4 changed: the vice is player 17; the
    captain plays `cap_minutes` (one player_gw row per fixture, in that order);
    a captain on 0 minutes is autosubbed (FPL's stored picks): he moves to
    slot 14 at x0 and the bench MID takes slot 6 at x1; a captain who played
    keeps slot 6 at the chip's captain multiplier. The vice has `vice_mult`."""
    toy_league(tmp)
    c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
    b = RIVAL_B
    c.execute("update entry_gw set active_chip = ? where entry_id = ? and event = ?", (chip, b, EV))
    c.execute("update picks set is_vice = 1 where entry_id = ? and event = ? and player_id = ?", (b, EV, VICE))
    for m in cap_minutes:
        c.execute("insert into player_gw (player_id, event, minutes) values (?, ?, ?)", (CAP, EV, m))
    c.execute("insert into player_gw (player_id, event, minutes) values (?, ?, 90)", (VICE, EV))
    if sum(cap_minutes) == 0:
        c.execute("update picks set position = 14, multiplier = 0 where entry_id = ? and event = ? and player_id = ?", (b, EV, CAP))
        c.execute("update picks set position = 6, multiplier = 1 where entry_id = ? and event = ? and player_id = ?", (b, EV, BENCH_MID))
    else:
        c.execute("update picks set multiplier = ? where entry_id = ? and event = ? and player_id = ?",
                  (3 if chip == "3xc" else 2, b, EV, CAP))
    c.execute("update picks set multiplier = ? where entry_id = ? and event = ? and player_id = ?", (vice_mult, b, EV, VICE))
    c.commit(); c.close()


class VicePromotion(unittest.TestCase):

    def modules(self):
        import fpl_league
        import league as LGt
        return fpl_league, LGt

    def run_case(self, **kw):
        out = []
        for mod in self.modules():
            tmp = tempfile.mkdtemp()
            try:
                vice_case(tmp, **kw)
                try:
                    mod.load(tmp)
                    out.append((mod.__name__, None))
                except mod.MissingInput as e:
                    out.append((mod.__name__, str(e)))
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
        return out

    def test_captain_0_minutes_vice_promoted_x2(self):
        for name, err in self.run_case(vice_mult=2):
            self.assertIsNone(err, name)
        for name, err in self.run_case(vice_mult=1):              # a wrong vice multiplier still stops the run
            self.assertIn(f"entry {RIVAL_B} GW{EV} player {VICE}: multiplier 1 but the rule says 2", err, name)

    def test_triple_captain_vice_promoted_x3(self):
        for name, err in self.run_case(chip="3xc", vice_mult=3):
            self.assertIsNone(err, name)
        for name, err in self.run_case(chip="3xc", vice_mult=2):
            self.assertIn(f"player {VICE}: multiplier 2 but the rule says 3 (chip 3xc)", err, name)

    def test_no_promotion_when_the_captain_played(self):
        for name, err in self.run_case(cap_minutes=(30, 0), vice_mult=1):    # a double: 30 + 0 minutes, the 0 row last
            self.assertIsNone(err, name)
        for name, err in self.run_case(cap_minutes=(30, 0), vice_mult=2):
            self.assertIn(f"player {VICE}: multiplier 2 but the rule says 1 (chip None)", err, name)
        for name, err in self.run_case(chip="3xc", cap_minutes=(1,), vice_mult=1):
            self.assertIsNone(err, name)


if __name__ == "__main__":
    unittest.main()
