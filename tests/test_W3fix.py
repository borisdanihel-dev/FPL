"""tests/test_W3fix.py - W3fix (prereg/W3fix.md; Boris's rulings of Thu 12 Nov, points 2 and 3).

Ruling 2: "CAPTAIN and BAN RISK must read the current night's export (availability matters before a deadline).
CHIPS may stay one night behind, as amendment 3 allows. Fix with a test."
"""
import json
import os
import sqlite3
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_chips                                                  # noqa: E402
import fpl_squad as SQ                                            # noqa: E402
from tests.test_S6d import gw9_snapshot                           # noqa: E402
from tests.test_W3 import drop_world, toy_world                   # noqa: E402

WORKING = "fpl_export_gw8.json"            # tonight's working export in the toy world (the archive is gw8_2026-10-17)


class TonightsExport(unittest.TestCase):
    """The newest dated archive (last night's export) has our player available; tonight's working export has
    him flagged with chance 0. CAPTAIN and BAN RISK must follow tonight's."""

    def setUp(self):
        toy_world(self)
        gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        self.working = os.path.join(self.tmp, WORKING)
        self.assertTrue(os.path.exists(self.working), "the toy world has the working export the nightly always has")

    def tearDown(self):
        drop_world(self)

    def _flag(self, pid):
        """Tonight's working export: the archive's content with `pid` flagged ('i', chance 0)."""
        with open(self.working, encoding="utf-8") as fh:
            d = json.load(fh)
        hit = [p for p in d["all_players"] if p["id"] == pid]
        self.assertEqual(len(hit), 1)
        hit[0]["status"], hit[0]["chance_next_round"] = "i", 0
        with open(self.working, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(d, fh)

    def test_captain_reads_tonights_export(self):
        before = []
        cap = SQ.captain(self.tmp, before.append, prior_path=self.prior)["captain"]
        self._flag(cap)
        got = []
        res = SQ.captain(self.tmp, got.append, prior_path=self.prior)
        self.assertTrue(got[0].startswith(f"  GW9 from {WORKING}: "), got[0])
        name = {r["id"]: r["name"] for r in fpl_chips.my_squad(self.d)}[cap]
        self.assertIn(f"  {name:<16}", "\n".join(got))
        self.assertTrue(any(s.startswith(f"  {name:<16}") and s.endswith("no xp_v2 forecast") for s in got), got)
        self.assertNotEqual(res["captain"], cap)                       # the flagged captain gives way

    def test_ban_risk_reads_tonights_export(self):
        squad = fpl_chips.my_squad(self.d)
        ours = squad[5]
        c = sqlite3.connect(os.path.join(self.tmp, "fpl.sqlite"))
        evs = [e for (e,) in c.execute("select event from player_gw where player_id = ? and minutes > 0 order by event",
                                       (ours["id"],))]
        for e in evs[:4]:
            c.execute("update player_gw set yellow = 1 where player_id = ? and event = ?", (ours["id"], e))
        c.commit()
        c.close()
        before = []
        SQ.ban_risk(self.tmp, before.append)
        line = [s for s in before if s.startswith(f"  {ours['name']:<16}")]
        self.assertEqual(len(line), 1, before)
        self.assertNotIn("P(start) 0.00", line[0])                     # available in last night's archive
        self._flag(ours["id"])
        got = []
        SQ.ban_risk(self.tmp, got.append)
        self.assertIn(f"from {WORKING}", got[0])
        line = [s for s in got if s.startswith(f"  {ours['name']:<16}")]
        self.assertEqual(len(line), 1, got)
        self.assertIn("P(start) 0.00  P(ban) 0.000", line[0])

    def test_no_working_export_is_a_missing_input_never_the_archive(self):
        os.remove(self.working)
        for section in (lambda: SQ.captain(self.tmp, [].append, prior_path=self.prior),
                        lambda: SQ.ban_risk(self.tmp, [].append)):
            with self.assertRaises(SQ.MissingInput):
                section()


if __name__ == "__main__":
    unittest.main()
