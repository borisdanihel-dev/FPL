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


class OneScale(unittest.TestCase):
    """Ruling 3, option (a) (Boris, Mon 16 Nov; prereg/W3fix.md, amending item N): in a week with own rows a player
    with no own forecast counts 0, with a note, in the base report's Free Hit screen and in CHIPS. The 12 Nov case:
    a player at 'a' in last night's export (CHIPS's) and 'd' tonight has no own row; bottomup valued him far above
    own's scale, he entered CHIPS's Free Hit XI and flagged a Free Hit the base screen did not."""

    @classmethod
    def setUpClass(cls):
        import copy
        import io
        import shutil
        import tempfile
        from contextlib import redirect_stdout
        from test_fpl import _recordable_export
        import fpl_edge as E
        cls.E, cls.shutil = E, shutil
        cls.tmp = tempfile.mkdtemp()
        tonight = _recordable_export(blank_team="HUL")
        nxt = tonight["gameweek"] + 1
        playing = {t for f in tonight["fixtures_next6"] if f["event"] == nxt for t in (f["home"], f["away"])}
        ours = set(E.my_squad_ids(tonight))
        gate = [p for p in tonight["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45
                and p["team"] in playing and p["id"] not in ours]
        cls.stale = max(gate, key=lambda p: (p["price"], -p["id"]))       # dear: never the cheapest bench pick
        cls.archive = copy.deepcopy(tonight)                               # last night's export: still 'a'
        hurt = next(p for p in tonight["all_players"] if p["id"] == cls.stale["id"])
        hurt["status"], hurt["chance_next_round"] = "d", 50               # tonight: 'd', so own records no row
        cls.mine = next(p for p in tonight["all_players"] if p["id"] in ours and p["status"] == "a"
                        and p["team"] in playing and p["pos"] != 1)
        cls.mine_name = cls.mine["web_name"]
        cls.mine["status"], cls.mine["chance_next_round"] = "d", 75      # one of ours flagged tonight: no own row
        for p in cls.archive["all_players"]:
            if p["id"] == cls.mine["id"]:
                p["status"], p["chance_next_round"] = "d", 75
        cls.tonight, cls.next = tonight, nxt
        path = os.path.join(cls.tmp, "projection_log.csv")
        with redirect_stdout(io.StringIO()):
            for src in ("own", "bottomup"):
                E.record_projections(tonight, 6, src, None, path)
        cls.log = E.read_log(path)
        own = {int(r["player_id"]) for r in cls.log if r["source"] == "own" and int(r["event"]) == nxt}
        assert own and cls.stale["id"] not in own and cls.mine["id"] not in own

    @classmethod
    def tearDownClass(cls):
        cls.shutil.rmtree(cls.tmp, ignore_errors=True)

    def _planted(self):
        """bottomup far above own's scale for the stale player, as on 12 Nov (4.21 among own values of 2-3)."""
        from unittest import mock
        real = self.E.project_week
        stale = self.stale["id"]
        return mock.patch.object(self.E, "project_week",
                                 side_effect=lambda pid, *a, **k: 40.0 if pid == stale else real(pid, *a, **k))

    def test_the_flag_agrees_with_the_base_screen(self):
        with self._planted():
            base = self.E.free_hit_table(self.tonight, self.log)["weeks"][0]
            chips = self.E.free_hit_table(self.archive, self.log)["weeks"][0]      # CHIPS's screen, last night's export
        self.assertEqual(base["metric"], "own")
        self.assertNotIn(self.stale["id"], {p["id"] for p in chips["fh"]["xi"]})
        self.assertAlmostEqual(chips["fh"]["pts"], base["fh"]["pts"], 9)
        self.assertAlmostEqual(chips["gap"], base["gap"], 9)
        self.assertEqual(chips["flag"], base["flag"])
        self.assertEqual(chips["no_own_gate"], 1)                               # the stale player, through its gate
        self.assertEqual(base["no_own_gate"], 0)                                # own records exactly tonight's gate

    def test_no_own_row_counts_zero_in_the_own_week_only(self):
        with self._planted():
            weeks, pts, src = self.E.one_week_points(self.archive, self.log)
        for pid in (self.stale["id"], self.mine["id"]):
            self.assertEqual((pts[self.next][pid], src[self.next][pid]), (0.0, "no own"))
            self.assertEqual(src[weeks[1]][pid], "bottomup")                    # no own rows that week: one scale
        self.assertEqual(pts[weeks[1]][self.stale["id"]], 40.0)

    def test_chips_counts_zero_in_its_own_week(self):
        weeks, pts, src = fpl_chips.own_week_points(self.archive, self.log)
        self.assertEqual((pts[self.next][self.stale["id"]], src[self.next][self.stale["id"]]), (0.0, "no own"))
        self.assertEqual(src[weeks[1]][self.stale["id"]], "own-model")         # later weeks: the formula, as before
        self.assertGreater(pts[weeks[1]][self.stale["id"]], 0)
        self.assertEqual(src[self.next][self.mine["id"]], "gate")               # 'd': outside the gate, 0, as before

    def test_the_note(self):
        t = self.E.free_hit_table(self.tonight, self.log)
        own = {int(r["player_id"]) for r in self.log if r["source"] == "own" and int(r["event"]) == self.next}
        playing = {x for f in self.tonight["fixtures_next6"] if f["event"] == self.next for x in (f["home"], f["away"])}
        by_id = {p["id"]: p for p in self.tonight["all_players"]}
        want = [by_id[i]["web_name"] for i in self.E.my_squad_ids(self.tonight)
                if i not in own and by_id[i]["team"] in playing]
        self.assertIn(self.mine_name, want)
        self.assertEqual(t["weeks"][0]["no_own_ours"], want)
        notes = [s for s in self.E.free_hit_lines(t) if s.startswith("    GW")]
        self.assertEqual(notes, [f"    GW{self.next}: a player with no own forecast counts 0 (W3fix Ruling 3, amending "
                                 f"item N): {len(want)} of our 15 ({', '.join(want)}), 0 in the Free Hit gate"])
        self.assertNotIn(self.mine["id"], {p["id"] for p in t["weeks"][0]["ours_xi"]}, "counted 0, he is benched")
        self.assertEqual(t["weeks"][1]["no_own_ours"], [])                     # a bottomup week has no note
        self.assertEqual(len(notes), sum(1 for w in t["weeks"] if w["metric"] == "own"))


if __name__ == "__main__":
    unittest.main()
