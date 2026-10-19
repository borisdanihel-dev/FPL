"""
tests/test_S12.py - the minutes model v2 (prereg/S12.md).

    python -m unittest tests.test_S12
"""

import csv
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import minutes_v2 as M                                            # noqa: E402
from tests.test_S4 import toy_hist, plant_transfer                # noqa: E402

KO = lambda n: datetime(2025, 9, 1, 15, tzinfo=timezone.utc) + timedelta(days=n)    # noqa: E731


def toy_rows(n_matches=6, rest=(7, 7, 7, 7, 7), keepers=(1, 2, 3), outfield=(10, 11, 12, 13)):
    """One club ALP with keepers 1-3 and outfield 10-13 (DEF), n matches;
    keeper 1 starts every match but the last (keeper 2 starts it); 10 and 11
    start every match; 12 starts whenever 11 does not; 13 never starts.
    Returns (rows, kickoffs)."""
    kos = [KO(0)]
    for r in rest:
        kos.append(kos[-1] + timedelta(days=r))
    while len(kos) < n_matches:
        kos.append(kos[-1] + timedelta(days=7))
    matches = {"ALP": [(kos[i], f"m{i}", i + 1) for i in range(n_matches)]}
    played = {}
    for i in range(n_matches):
        key = f"m{i}"
        last = i == n_matches - 1
        played[(1, key)] = (0 if last else 90, 0 if last else 1, 0)
        played[(2, key)] = (90 if last else 0, 1 if last else 0, 0)
        played[(3, key)] = (0, 0, 0)
        played[(10, key)] = (90, 1, 1 if i in (0, 2, 4) else 0)
        played[(11, key)] = (90, 1, 0)
        played[(12, key)] = (20, 0, 0)
        played[(13, key)] = (0, 0, 0)
    club_of = {pid: "ALP" for pid in keepers + outfield}
    pos = {1: 1, 2: 1, 3: 1, 10: 2, 11: 2, 12: 2, 13: 2}
    return M.Rows(matches, played, club_of, pos), kos


class Rules(unittest.TestCase):
    def test_states_and_lock(self):
        rows, kos = toy_rows()
        cut = kos[-1] + timedelta(days=1)                      # after every match
        self.assertEqual(M.base_states(rows, 10, "ALP", cut), (1.0, 0.0))
        self.assertEqual(M.base_states(rows, 12, "ALP", cut), (0.0, 1.0))      # four sub appearances
        self.assertEqual(M.base_states(rows, 13, "ALP", cut), (0.0, 0.0))
        self.assertEqual(M.base_states(rows, 1, "ALP", cut), (0.75, 0.0))      # missed the last of four
        lock = M.keeper_lock(rows, "ALP", cut)
        self.assertEqual(lock, {1: 0.95, 2: 0.05, 3: 0.0})                     # 1 started 2 of the last 3, 2 started 1
        self.assertEqual(M.keeper_lock(rows, "ALP", cut, flagged={1}), {2: 0.05, 3: 0.0})
        # a tie: with two matches left in the window both keepers have one start; the latest starter leads
        cut2 = kos[-1] + timedelta(days=1)
        rows2, kos2 = toy_rows(n_matches=2)
        self.assertEqual(M.keeper_lock(rows2, "ALP", cut2)[2], 0.95)
        self.assertEqual(M.keeper_lock(rows2, "ALP", cut2)[1], 0.05)

    def test_cover(self):
        rows, kos = toy_rows()
        cut = kos[-1] + timedelta(days=1)
        rows.club_of[13] = "ALP"; rows.pos[13] = 2
        for key in ("m2", "m4"):
            rows.played[(13, key)] = (90, 1, 0)                                 # 13: exactly 2 of the last 4 - not a regular
        rows.club_of[14] = "ALP"; rows.pos[14] = 2
        for key in ("m2", "m3", "m4"):
            rows.played[(14, key)] = (90, 1, 0)                                 # 14: 3 of the last 4 (regular), 0 minutes in m5...
        rows.played[(14, "m1")] = (0, 0, 0)                                     # ...but did not start the 4 before m5: not "out"
        regs, absent = M.regulars_and_absent(rows, "ALP", cut)
        self.assertEqual(sorted(regs), [1, 10, 11, 14])                         # keeper 1 started 3 of the last 4 too
        self.assertEqual(absent, [1])                                           # only 1: 0 minutes last match after starting the 4 before
        self.assertEqual(M.replacement_for(rows, "ALP", 1, cut), 2)             # keeper 2 started when 1 did not
        self.assertIsNone(M.replacement_for(rows, "ALP", 11, cut))              # 11 never missed a match
        rows_live, _ = toy_rows()
        regs, absent = M.regulars_and_absent(rows_live, "ALP", cut, out_live={11})
        self.assertEqual(absent, [11])
        self.assertEqual(M.replacement_for(rows_live, "ALP", 11, cut), None)
        # the pinned rule: the replacement is whoever started most in the matches the regular missed; a
        # co-starter who never misses wins ties on total starts (rows3 is built so that 12 wins outright)
        rows3, kos3 = toy_rows()
        for key in ("m0", "m5"):
            rows3.played[(10, key)] = (0, 0, 0)                                 # 10 out in m0 and m5, started m1-m4
            rows3.played[(12, key)] = (90, 1, 0)                                # 12 started both matches 10 missed
        rows3.played[(11, "m5")] = (0, 0, 0)                                    # 11 missed m5 too: counts 1 against 12's 2
        regs3, absent3 = M.regulars_and_absent(rows3, "ALP", cut)
        self.assertIn(10, regs3); self.assertIn(10, absent3)                    # 3 of the last 4 and 0 minutes in m5 after starting m1-m4
        self.assertEqual(M.replacement_for(rows3, "ALP", 10, cut), 12)
        v3, _ = M.v2_pstart(rows3, cut, factor=(1.0, None, None, 0))
        self.assertEqual(M.base_states(rows3, 12, "ALP", cut)[0], 0.25)         # 12's own share
        self.assertEqual(v3[12], 1.0)                                           # inherits 10's share before the absence (m1-m4: 4 of 4)
        v2, _ = M.v2_pstart(rows, cut, out_live={10}, factor=(1.0, None, None, 0))
        self.assertEqual(v2[12], 0.0)                                           # in `rows` nobody started when 10 was out: no replacement

    def test_congestion_factor(self):
        rows, kos = toy_rows(n_matches=10, rest=(7, 2, 7, 2, 7, 2, 7, 2, 7))
        cut = kos[-1] + timedelta(days=1)
        c, lo, hi, n = M.congestion_factor(rows, cut, b=200)
        self.assertEqual(c, 1.0)                                                # regulars start every match: no effect, interval includes 1
        rows2, kos2 = toy_rows(n_matches=12, rest=(7, 7, 7, 2, 7, 2, 7, 2, 7, 2, 7))
        for _, key, _ in rows2.matches["ALP"]:                                   # keeper 1 starts every match: a third regular
            rows2.played[(1, key)] = (90, 1, 0); rows2.played[(2, key)] = (0, 0, 0)
        congested = [i for i, (ko, key, ev) in enumerate(rows2.matches["ALP"]) if i >= 1 and (ko - rows2.matches["ALP"][i - 1][0]).days <= 3]
        for k, i in enumerate(congested):                                        # 10 and 11 rest alternate congested matches: both stay regular
            rows2.played[(10 if k % 2 else 11, rows2.matches["ALP"][i][1])] = (0, 0, 0)
        cut2 = kos2[-1] + timedelta(days=1)
        c2, lo2, hi2, n2 = M.congestion_factor(rows2, cut2, b=400)
        self.assertAlmostEqual(c2, 2 / 3)                                       # two of three regulars start a congested match, all three otherwise
        self.assertLess(hi2, 1.0)
        rows3, kos3 = toy_rows(n_matches=3)
        self.assertEqual(M.congestion_factor(rows3, kos3[-1] + timedelta(days=1), b=50)[0], 1.0)   # no training match

    def test_suspensions(self):
        rows, kos = toy_rows()
        cut = kos[-1] + timedelta(days=1)
        self.assertEqual(M.cautions_before(rows, 10, cut), 3)
        self.assertFalse(M.suspended_next(rows, 10, "ALP", cut))                # 3 cautions
        rows.played[(10, "m5")] = (90, 1, 1); rows.played[(10, "m3")] = (90, 1, 1)   # 5th caution in the previous match (match 6 < 19)
        self.assertEqual(M.cautions_before(rows, 10, cut), 5)
        self.assertTrue(M.suspended_next(rows, 10, "ALP", cut))
        rows.played[(10, "m5")] = (90, 1, 0); rows.played[(10, "m1")] = (90, 1, 1)   # the 5th came earlier: already served
        self.assertFalse(M.suspended_next(rows, 10, "ALP", cut))
        self.assertAlmostEqual(M.p_ban_next(0.3, 0.9), 0.27)
        self.assertEqual(M.p_ban_next(2.0, 0.9), 1.0)
        rate = M.booking_rate90(rows, 10, cut, pos_mean=0.1)                   # 5 cautions in 540 minutes = 0.833/90, shrunk 6/(6+4)
        self.assertAlmostEqual(rate, 0.6 * (5 / 6) + 0.4 * 0.1)
        v2, _ = M.v2_pstart(rows, cut, factor=(1.0, None, None, 0))
        rows.played[(10, "m5")] = (90, 1, 1); rows.played[(10, "m1")] = (90, 1, 0)
        v2b, _ = M.v2_pstart(rows, cut, factor=(1.0, None, None, 0))
        self.assertEqual(v2b[10], 0.0)                                          # banned for the next match
        self.assertEqual(v2[10], 1.0)


class Season(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        toy_hist(cls.tmp.name)
        with open(os.path.join(cls.tmp.name, "fixtures.csv"), newline="") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            r["kickoff_time"] = f"2025-08-{14 + int(r['event']):02d}T14:00:00Z"
        with open(os.path.join(cls.tmp.name, "fixtures.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        with open(os.path.join(cls.tmp.name, "merged_gw.csv"), newline="") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            r["yellow_cards"] = "1" if int(r["element"]) % 7 == 0 and int(r["round"]) in (2, 4) else "0"
        with open(os.path.join(cls.tmp.name, "merged_gw.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) + (["yellow_cards"] if "yellow_cards" not in rows[0] else []))
            w.writeheader(); w.writerows(rows)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_point_in_time_and_the_current_model(self):
        hist = BT.load_2526(self.tmp.name); hist["dir"] = self.tmp.name
        rows, _, _ = M.rows_2526(hist, 5)
        cut = M.origin_cut(rows, 5)
        self.assertTrue(all(ev < 5 for (pid, key), _ in rows.played.items() for ev in [next(e for ms in rows.matches.values() for ko, k, e in ms if k == key)]))
        v2, _ = M.v2_pstart(rows, cut, factor=(1.0, None, None, 0))
        hist2 = BT.load_2526(self.tmp.name); hist2["dir"] = self.tmp.name
        for rnd in (5, 6):
            for r in hist2["raw"][rnd]:
                r["minutes"] = "0"; r["starts"] = "0"; r["yellow_cards"] = "3"
        rows2, _, _ = M.rows_2526(hist2, 5)
        self.assertEqual(M.v2_pstart(rows2, cut, factor=(1.0, None, None, 0))[0], v2)
        with tempfile.TemporaryDirectory() as tmp:
            toy_hist(tmp)
            plant_transfer(tmp, 3, 6, 2)
            hist3 = BT.load_2526(tmp); hist3["dir"] = tmp
            self.assertEqual(M.rows_2526(hist3, 5)[0].club_of[3], "ALP")     # the club of the origin
        buf = io.StringIO()
        res = M.test_2526(self.tmp.name, out=lambda s: buf.write(s + chr(10)), first=5, last=6)
        self.assertEqual([r["gw"] for r in res["per"]], [5, 6])
        self.assertIn("pre-registered result", buf.getvalue())
        self.assertEqual(M.PASS_BRIER, 0.01); self.assertEqual(M.MAE_SLACK, 0.02)


class Live(unittest.TestCase):
    def test_overrides_applied_logged_scored_and_never_in_the_replay(self):
        from tests.test_S6 import toy_season
        with tempfile.TemporaryDirectory() as tmp:
            toy_season(tmp)
            ov = os.path.join(tmp, "overrides.csv")
            with open(ov, "w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=["player", "gw", "p_start", "reason", "timestamp_utc"]); w.writeheader()
                w.writerow({"player": 1, "gw": 9, "p_start": 0.11, "reason": "test", "timestamp_utc": "2026-10-18T00:00:00Z"})
                w.writerow({"player": 2, "gw": 8, "p_start": 0.22, "reason": "old gameweek", "timestamp_utc": "2026-10-18T00:00:00Z"})
            out = os.path.join(tmp, "out"); os.makedirs(out)
            buf = io.StringIO()
            res = M.live(tmp, out=lambda s: buf.write(s + chr(10)), now=datetime(2098, 12, 1, tzinfo=timezone.utc), overrides_path=ov, out_dir=out)
            self.assertEqual(res["target"], 9)
            self.assertEqual(res["v2"][1], 0.11)                                 # applied for the coming gameweek
            self.assertNotEqual(res["v2"].get(2), 0.22)                          # a past gameweek's row is ignored
            self.assertEqual([o["player"] for o in res["applied"]], ["1"])
            log = os.path.join(out, M.OVERRIDES_LOG)
            with open(log, newline="") as fh:
                logged = list(csv.DictReader(fh))
            self.assertEqual(len(logged), 1); self.assertEqual(logged[0]["gw"], "9")
            self.assertIn("1 overrides applied", buf.getvalue())
            # scoring: GW9 is not settled -> 0 of 1 scored; a settled gameweek scores
            buf = io.StringIO()
            scored = M.score_overrides(tmp, out=lambda s: buf.write(s + chr(10)), out_dir=out)
            self.assertEqual(scored, [])
            with open(log, "a", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=logged[0].keys())
                w.writerow({"applied_at_utc": "x", "gw": 8, "player": 1, "p_start": "0.9", "model_p_start": "0.5", "reason": "r", "timestamp_utc": "t"})
            scored = M.score_overrides(tmp, out=lambda s: None, out_dir=out)
            self.assertEqual(len(scored), 1)
        self.assertNotIn("overrides", open(os.path.join(ROOT, "tools", "minutes_v2.py"), encoding="utf-8").read().split("def test_2526")[1].split("def rows_2627")[0])


class CLI(unittest.TestCase):
    def test_cli_and_isolation(self):
        from tests.test_S6 import toy_season
        with tempfile.TemporaryDirectory() as tmp:
            toy_season(tmp)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = M.main(["--score-overrides", "--data", tmp, "--out", out])
            self.assertEqual(rc, 2)                                              # no override applied yet: refused
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'minutes_v2')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
