"""
tests/test_S6.py - the xP rebuild and blend (prereg/S6.md acceptance tests).

    python -m unittest tests.test_S6
"""

import csv
import io
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import xp_v2 as X                                                 # noqa: E402
from tests.test_S5 import toy_2627                                # noqa: E402

PRE = "2026-10-17T21:56:00+00:00"        # before the toy's GW8 deadline (2026-10-18T11:00Z)
POST = "2026-10-18T12:00:00+00:00"       # after it: never read


def toy_season(tmp):
    """toy_2627 plus a log with own/xg/bottomup/minutes for GW8 made before
    the deadline, a post-deadline xg snapshot, and our 15 in picks."""
    gw8, odds = toy_2627(tmp, post_deadline_export=True)
    c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
    players = c.execute("select id, position from players order by id").fetchall()
    gk = [p for p, pos in players if pos == 1][:2]
    de = [p for p, pos in players if pos == 2][:5]
    mi = [p for p, pos in players if pos == 3][:5]
    fw = [p for p, pos in players if pos == 4][:3]
    for slot, pid in enumerate(gk + de + mi + fw, 1):
        c.execute("insert into picks values (?,?,?,?)", (BT.MY_ENTRY, 8, pid, slot))
    c.execute("update player_gw set minutes = 20, starts = 0, total_points = 2 where event in (5, 6, 8) and player_id % 4 = 0")  # sub appearances
    c.commit(); c.close()
    with open(os.path.join(tmp, E.LOG_PATH), "a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=E.LOG_FIELDS)
        for pid, pos in players:
            vals = {"own": 3.0 + (pid % 7) / 5, "xg": 2.0 + pid / 10, "bottomup": 2.5 + pid / 20,
                    "minutes": 1.0 if pid % 5 else 0.5}
            for src, v in vals.items():
                w.writerow({"made_at": PRE, "source": src, "event": 8, "player_id": pid, "web_name": f"P{pid}", "predicted": v})
            w.writerow({"made_at": POST, "source": "xg", "event": 8, "player_id": pid, "web_name": f"P{pid}", "predicted": 99.0})
    return gw8, odds


class Components(unittest.TestCase):
    def test_conditional_forecasts_hand_case(self):
        c = X.xp_candidates(0.8, 5.0, 3.0, 0.1, 1.2)
        self.assertAlmostEqual(c["blend"], 0.8 * 4.0 + 0.12)
        self.assertAlmostEqual(c["xg_only"], 0.8 * 5.0 + 0.12)
        self.assertAlmostEqual(c["bl_only"], 0.8 * 3.0 + 0.12)
        c0 = X.xp_candidates(0.0, 5.0, 3.0, 0.3, 1.5)             # P(start) 0: the sub term alone
        for v in (c0["blend"], c0["xg_only"], c0["bl_only"]):
            self.assertAlmostEqual(v, 0.45)
        # the minutes model enters only as P(start): a different P(start) scales the start term, nothing else
        a, b = X.xp_candidates(1.0, 4.0, 2.0, 0.0, 0.0), X.xp_candidates(0.5, 4.0, 2.0, 0.0, 0.0)
        self.assertAlmostEqual(a["blend"], 3.0); self.assertAlmostEqual(b["blend"], 1.5)

    def test_sub_inputs_before_the_deadline_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_season(tmp)
            db = os.path.join(tmp, "fpl.sqlite")
            p_sub, e_sub, counts, pos = X.sub_inputs(db, 8)
            self.assertTrue(all(0 <= v <= 1 for v in p_sub.values()))
            self.assertTrue(any(v > 0 for v in p_sub.values()))
            self.assertTrue(any(counts[p] > 0 for p in (1, 2, 3, 4)))
            c = sqlite3.connect(db)
            want = {}
            for p in (1, 2, 3, 4):
                vals = [float(x) for (x,) in c.execute("select total_points from player_gw where event < 8 and minutes > 0 and starts = 0 and player_id in (select id from players where position = ?)", (p,))]
                want[p] = sum(vals) / len(vals) if vals else 0.0
            c.close()
            self.assertEqual(e_sub, want)
            # rows of event >= 8 do not reach gameweek 8's inputs
            db2 = os.path.join(tmp, "copy.sqlite"); shutil.copy(db, db2)
            c = sqlite3.connect(db2); c.execute("update player_gw set total_points = 99, minutes = 1, starts = 0 where event >= 8"); c.commit(); c.close()
            self.assertEqual(X.sub_inputs(db2, 8)[:3], (p_sub, e_sub, counts))


class SeasonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.gw8, cls.odds = toy_season(cls.tmp.name)
        cls.s = X.Season(cls.tmp.name, odds_file=cls.odds)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_week_is_point_in_time(self):
        w = self.s.week(8)
        self.assertEqual(w["export"], "fpl_export_gw7_2026-10-17.json.gz")     # the pre-deadline export, never the later one
        self.assertTrue(w["rows"])
        for pid, r in w["rows"].items():
            self.assertNotEqual(r["e_xg"] * r["p_start"], 99.0)                # the post-deadline xg snapshot never read
            self.assertAlmostEqual(r["e_xg"] * r["p_start"], 2.0 + pid / 10 if r["p_start"] else 0.0)
            self.assertAlmostEqual(r["e_bl"] * r["p_start"], r["bl"] if r["p_start"] else 0.0)
            self.assertEqual(r["p_start"], 1.0 if pid % 5 else 0.5)            # P(start) is the minutes row
            self.assertAlmostEqual(r["blend"], r["p_start"] * (r["e_xg"] + r["e_bl"]) / 2 + r["p_sub"] * w["e_sub"][r["pos"]])
        self.assertEqual(self.s.weeks_with_sources(), [8])
        with self.assertRaises(X.MissingInput):
            self.s.week(9)                                                     # not settled: lockdown

    def test_develop_validate_and_the_frozen_choice(self):
        buf = io.StringIO()
        dev = X.develop(self.tmp.name, 8, out=lambda s: buf.write(s + chr(10)), odds_file=self.odds)
        self.assertEqual(dev["weeks"], [8])
        means = {c: sum(m["rho"] for m in dev["per"][c]) / len(dev["per"][c]) for c in ("xg_only", "bl_only")}
        self.assertEqual(dev["best_single"], max(means, key=means.get))        # chosen on the development set alone
        self.assertIsNone(dev["s_d"])                                           # one gameweek: s_d undefined
        self.assertIn("in-sample", buf.getvalue())
        buf = io.StringIO()
        val = X.validate(self.tmp.name, 8, out=lambda s: buf.write(s + chr(10)), odds_file=self.odds)
        self.assertEqual((val["weeks"], val["verdict"]), ([], "inconclusive"))
        self.assertIn("nothing adopted", buf.getvalue())
        with self.assertRaises(X.MissingInput):                                 # no development gameweek before the cut
            X.validate(self.tmp.name, 7, out=lambda s: None, odds_file=self.odds)

    def test_lockdown_and_missing_source_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            gw8, odds = toy_season(tmp)
            c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
            c.execute("update events set data_checked = 0 where id = 8"); c.commit(); c.close()
            with self.assertRaises(X.MissingInput) as cm:                   # every input exists; only the lockdown stops it
                X.Season(tmp, odds_file=odds).week(8)
            self.assertIn("not settled", str(cm.exception))
        with tempfile.TemporaryDirectory() as tmp:
            gw8, odds = toy_season(tmp)
            log = os.path.join(tmp, E.LOG_PATH)
            rows = [r for r in E.read_log(log) if r["source"] != "own"]
            E.write_log_atomic(log, rows)
            with self.assertRaises(X.MissingInput) as cm:                   # a missing source is refused, never worked around
                X.Season(tmp, odds_file=odds).week(8)
            self.assertIn("own", str(cm.exception))

    def test_metrics_pair_on_starters_and_our_15(self):
        m = self.s.metrics(8, "blend")
        w = self.s.week(8)
        self.assertEqual(m["n"], sum(1 for r in w["rows"].values() if r["p_start"] >= 0.8 and r["own"] is not None))
        self.assertLess(m["n"], len(w["rows"]))
        self.assertIsInstance(m["dec"], float); self.assertIsInstance(m["dec_own"], float)


class CLI(unittest.TestCase):
    def test_cli_cut_required_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            gw8, odds = toy_season(tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(X.main(["--develop", "--data", tmp, "--odds", odds, "--out", out]), 2)      # the cut is a frozen argument
                self.assertEqual(X.main(["--develop", "--cut", "8", "--data", tmp, "--odds", odds, "--out", out]), 0)
                self.assertEqual(X.main(["--validate", "--cut", "8", "--data", tmp, "--odds", odds, "--out", out]), 0)
                self.assertEqual(X.main(["--forecast", "--data", tmp, "--odds", odds, "--out", out]), 2)      # the toy export is a gameweek behind
            self.assertTrue(os.path.exists(os.path.join(out, "xp_v2_develop_cut8.txt")))
            self.assertTrue(os.path.exists(os.path.join(out, "xp_v2_validate_cut8.txt")))
            self.assertFalse(os.path.exists(os.path.join(tmp, E.LOG_PATH + ".tmp")))
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'xp_v2', 'odds_lambda', 'chips', 'backtest', 'hist_pit', 'console_utf8')]; "
                "print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)

    def test_log_is_never_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            gw8, odds = toy_season(tmp)
            log = os.path.join(tmp, E.LOG_PATH)
            before = open(log, "rb").read()
            with redirect_stdout(io.StringIO()):
                X.main(["--develop", "--cut", "8", "--data", tmp, "--odds", odds, "--out", os.path.join(tmp, "out")])
            with open(log, "rb") as fh:
                self.assertEqual(fh.read(), before)


if __name__ == "__main__":
    unittest.main()
