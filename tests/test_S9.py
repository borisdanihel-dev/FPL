"""
tests/test_S9.py - league variance, relative xP, captain table (prereg/S9.md).

    python -m unittest tests.test_S9
"""

import csv
import io
import math
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import league as L                                                # noqa: E402

US = L.MY_ENTRY
RIVAL_A, RIVAL_B = 111, 222
# hand-set net points over five settled gameweeks (GW1-5): ours, A, B
PTS = {US: [50, 60, 40, 70, 55], RIVAL_A: [45, 65, 50, 60, 50], RIVAL_B: [40, 40, 45, 50, 45]}
HITS = {US: [0, 4, 0, 0, 0], RIVAL_A: [0, 0, 0, 0, 0], RIVAL_B: [0, 0, 4, 0, 0]}
CHIPS = {(RIVAL_A, 3): "3xc", (RIVAL_B, 2): "bboost", (US, 5): "wildcard"}


def toy_league(tmp, unsettled_gw6=True, a_total_gap=None, gaps=None):
    """Three managers, GW1-5 settled (GW6 present but unsettled), 15 players
    each, own rows for GW1-6 made before each deadline, a post-deadline
    own snapshot for GW6, and GW6 picks that must never be used."""
    db = os.path.join(tmp, "fpl.sqlite")
    c = sqlite3.connect(db)
    c.executescript("""
      create table teams(id integer, name text, short_name text);
      create table entries(id integer, entry_name text, player_name text);
      create table events(id integer, deadline_time text, finished integer, data_checked integer);
      create table fixtures(id integer, event integer, finished integer);
      create table players(id integer, web_name text, team_id integer, position integer);
      create table player_gw(player_id integer, event integer, total_points integer, minutes integer, starts integer,
        clean_sheets integer, goals integer, bonus integer, defensive_contribution integer);
      create table entry_gw(entry_id integer, event integer, points integer, total_points integer, transfers integer,
        transfers_cost integer, points_on_bench integer, active_chip text);
      create table picks(entry_id integer, event integer, player_id integer, position integer, multiplier integer, is_captain integer, is_vice integer);
    """)
    c.executemany("insert into teams values (?,?,?)", [(1, "Alpha", "ALP"), (2, "Beta", "BET"), (3, "Gamma", "GAM")])
    c.executemany("insert into entries values (?,?,?)", [(US, "Us", "Boris"), (RIVAL_A, "Rival A", "A"), (RIVAL_B, "Rival B", "B")])
    for ev in range(1, 7):
        c.execute("insert into events values (?,?,?,?)", (ev, f"2026-09-{ev + 10:02d}T11:00:00Z", 1 if ev < 6 else 0, 1 if ev < 6 else 0))
        c.execute("insert into fixtures values (?,?,?)", (ev, ev, 1 if ev < 6 else 0))
    # 20 players: GK 1-2, DEF 3-9, MID 10-16, FWD 17-20
    for pid in range(1, 21):
        pos = 1 if pid <= 2 else 2 if pid <= 9 else 3 if pid <= 16 else 4
        c.execute("insert into players values (?,?,?,?)", (pid, f"P{pid}", 1 + pid % 3, pos))
    for eid in (US, RIVAL_A, RIVAL_B):
        total = 0
        for i, ev in enumerate(range(1, 6)):
            net = PTS[eid][i]
            gross = net + HITS[eid][i]
            total += net
            c.execute("insert into entry_gw values (?,?,?,?,?,?,?,?)", (eid, ev, gross, total, 1, HITS[eid][i], 5, CHIPS.get((eid, ev))))
        c.execute("insert into entry_gw values (?,?,?,?,?,?,?,?)", (eid, 6, 99, total + 99, 0, 0, 0, None))   # unsettled: never counted
    gaps = dict(gaps or {})
    if a_total_gap is not None:
        gaps[RIVAL_A] = a_total_gap
    for eid, gap in gaps.items():                     # move a rival's total so the gap is exactly `gap`
        c.execute("update entry_gw set total_points = (select total_points from entry_gw where entry_id = ? and event = 5) + ? where entry_id = ? and event = 5", (US, gap, eid))
    # picks: everyone holds players 1-15 in order (GK 1,2 DEF 3-7 MID 10-14 FWD 17-19 -> positions 1..15 by slot)
    squad = [1, 3, 4, 5, 6, 10, 11, 12, 13, 17, 18, 2, 7, 14, 19]
    for eid in (US, RIVAL_A, RIVAL_B):
        for ev in range(1, 7):
            chip = CHIPS.get((eid, ev))
            cap = {US: 10, RIVAL_A: 17, RIVAL_B: 10}[eid]
            for slot, pid in enumerate(squad, 1):
                mult = L.expected_multiplier(slot, 1 if pid == cap else 0, chip)
                c.execute("insert into picks values (?,?,?,?,?,?,?)", (eid, ev, pid, slot, mult, 1 if pid == cap else 0, 0))
    c.commit(); c.close()
    with open(os.path.join(tmp, E.LOG_PATH), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=E.LOG_FIELDS); w.writeheader()
        for ev in range(1, 7):
            for pid in range(1, 21):
                val = 6.0 if pid == 10 else 5.8 if pid == 17 else 5.6 if pid == 3 else 2.0 + pid / 20
                w.writerow({"made_at": f"2026-09-{ev + 9:02d}T21:55:00+00:00", "source": "own", "event": ev,
                            "player_id": pid, "web_name": f"P{pid}", "predicted": val})
        for pid in range(1, 21):                       # a post-deadline GW6 snapshot: never read
            w.writerow({"made_at": "2026-09-16T12:00:00+00:00", "source": "own", "event": 6,
                        "player_id": pid, "web_name": f"P{pid}", "predicted": 99.0})
    return db


def hand_sd(v):
    m = sum(v) / len(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


class Variance(unittest.TestCase):
    def test_sigmas_pooled_rho_phi_and_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_league(tmp)
            data = L.load(tmp)
            self.assertEqual(data["settled"], [1, 2, 3, 4, 5])
            var = L.variance_table(data)
            self.assertEqual((var["last"], var["n_left"]), (5, 33))
            d_a = [u - a for u, a in zip(PTS[US], PTS[RIVAL_A])]
            d_b = [u - b for u, b in zip(PTS[US], PTS[RIVAL_B])]
            pooled = math.sqrt((hand_sd(d_a) ** 2 + hand_sd(d_b) ** 2) / 2)
            self.assertAlmostEqual(var["sigma_d"], pooled)
            rows = {r["entry"]: r for r in var["rows"]}
            self.assertAlmostEqual(rows[RIVAL_A]["sigma_dj"], hand_sd(d_a))
            self.assertAlmostEqual(rows[RIVAL_A]["sigma_j"], hand_sd(PTS[RIVAL_A]))
            self.assertAlmostEqual(var["sigma_me"], hand_sd(PTS[US]))
            self.assertAlmostEqual(rows[RIVAL_A]["rho"], L.pearson(PTS[US], PTS[RIVAL_A]))
            self.assertEqual(rows[RIVAL_A]["gap"], sum(PTS[RIVAL_A]) - sum(PTS[US]))         # net of hits
            self.assertEqual(rows[RIVAL_B]["gap"], sum(PTS[RIVAL_B]) - sum(PTS[US]))
            lo, hi = var["sigma_d_ci"]
            self.assertLessEqual(lo, var["sigma_d"]); self.assertGreaterEqual(hi, var["sigma_d"])
            # chip weeks dropped for the no-chip sigma: A's GW3 (TC) and our GW5 (WC)
            d_a_nc = [u - a for i, (u, a) in enumerate(zip(PTS[US], PTS[RIVAL_A])) if i + 1 not in (3, 5)]
            self.assertAlmostEqual(rows[RIVAL_A]["sigma_dj_nochip"], hand_sd(d_a_nc))
        self.assertEqual(L.line_label(5.0, 5.0), "inside")                # a gap exactly on the line is inside
        self.assertEqual(L.line_label(5.0001, 5.0), "beyond the line")
        self.assertAlmostEqual(L.phi(0.0), 0.5)
        self.assertAlmostEqual(L.phi(-1.0), 0.15865525, places=6)
        with tempfile.TemporaryDirectory() as tmp:
            toy_league(tmp)
            data = L.load(tmp)
            var = L.variance_table(data)
            line = var["sigma_d"] * math.sqrt(var["n_left"])
            gap_on_line = int(math.floor(line))               # just inside; the next integer is beyond
        with tempfile.TemporaryDirectory() as tmp:
            toy_league(tmp, a_total_gap=gap_on_line)
            var = L.variance_table(L.load(tmp))
            r = {x["entry"]: x for x in var["rows"]}[RIVAL_A]
            self.assertEqual(r["line"], "inside")
            self.assertAlmostEqual(r["p_above"], L.phi(-gap_on_line / line))
        with tempfile.TemporaryDirectory() as tmp:
            toy_league(tmp, a_total_gap=gap_on_line + 1)
            var = L.variance_table(L.load(tmp))
            self.assertEqual({x["entry"]: x for x in var["rows"]}[RIVAL_A]["line"], "beyond the line")

    def test_point_in_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_league(tmp)
            data = L.load(tmp)
            self.assertNotIn(6, data["gw"][US])                                   # GW6 is unsettled: never counted
            self.assertNotIn(6, data["picks"][RIVAL_A])
            ev, rows = L.last_settled_picks(data, RIVAL_A)
            self.assertEqual(ev, 5)
            self.assertEqual(max(data["own"][6].values()), 6.0)                   # the post-deadline GW6 snapshot never read
            # the unsettled gameweek carries the biggest score: counting it would move sigma
            var = L.variance_table(data)
            self.assertEqual(var["rows"][0]["n"], 5)

    def test_multipliers_threat_set_and_eo(self):
        self.assertEqual(L.expected_multiplier(5, 1, None), 2)
        self.assertEqual(L.expected_multiplier(5, 1, "3xc"), 3)
        self.assertEqual(L.expected_multiplier(12, 0, None), 0)
        self.assertEqual(L.expected_multiplier(12, 0, "bboost"), 1)
        self.assertEqual(L.expected_multiplier(5, 0, "bboost"), 1)
        with tempfile.TemporaryDirectory() as tmp:
            db = toy_league(tmp)
            data = L.load(tmp)
            var = L.variance_table(data)
            threats, w = L.threat_set(var)
            # A is ahead of us (270 > 275? totals: ours 275, A 270, B 220) -> nobody ahead: we lead
            totals = {e: sum(PTS[e]) for e in PTS}
            ahead = [e for e in (RIVAL_A, RIVAL_B) if totals[e] > totals[US]]
            if ahead:
                self.assertEqual(sorted(r["entry"] for r in threats), sorted(ahead))
            else:
                self.assertTrue(all(1 - r["p_above"] >= L.THREAT_MIN_P for r in threats))
            self.assertAlmostEqual(sum(w.values()), 1.0)
            for r in threats:
                self.assertAlmostEqual(w[r["entry"]], (1 - r["p_above"]) / sum(1 - x["p_above"] for x in threats))
            eo, used = L.league_eo(data, w)
            self.assertTrue(all(ev == 5 for ev in used.values()))
            # captain of A is 17 (x2), of B is 10 (x2); starters 1; bench 0 (no chip in GW5 for A or B)
            self.assertAlmostEqual(eo[17], w.get(RIVAL_A, 0) * 2 + w.get(RIVAL_B, 0) * 1)
            self.assertAlmostEqual(eo[10], w.get(RIVAL_A, 0) * 1 + w.get(RIVAL_B, 0) * 2)
            self.assertAlmostEqual(eo.get(7, 0.0), 0.0)                              # bench
            # a mismatching multiplier stops the run
            c = sqlite3.connect(db); c.execute("update picks set multiplier = 3 where entry_id = ? and event = 5 and is_captain = 1", (RIVAL_A,)); c.commit(); c.close()
            with self.assertRaises(L.MissingInput):
                L.load(tmp)
        with tempfile.TemporaryDirectory() as tmp:                                    # a rival ahead: the threat set is exactly the rivals ahead
            toy_league(tmp, gaps={RIVAL_A: 10})
            var = L.variance_table(L.load(tmp))
            threats, w = L.threat_set(var)
            self.assertEqual([r["entry"] for r in threats], [RIVAL_A])
            b = {r["entry"]: r for r in var["rows"]}[RIVAL_B]
            self.assertGreaterEqual(1 - b["p_above"], L.THREAT_MIN_P)                # B would qualify by P alone, but is behind
            self.assertEqual(w, {RIVAL_A: 1.0})

    def test_captain_table_and_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_league(tmp)
            buf = io.StringIO()
            res = L.report(tmp, out=lambda s: buf.write(s + chr(10)), today=datetime(2026, 9, 16, tzinfo=timezone.utc))
            text = buf.getvalue()
            self.assertEqual(res["next_gw"], 6)
            ranked = sorted(res["xi"], key=lambda r: (-r["proj"], r["id"]))
            self.assertEqual([r["id"] for r in ranked[:3]], [10, 17, 3])                 # own 6.0, 5.8, 5.6
            self.assertIn("allowance 0.5 xP (before GW25)", text)
            self.assertIn("allowed differential", text)                                  # 17 at cost 0.2
            self.assertIn("a DEF or GK topped our XI's own xP in 0 of 5", text)
        with tempfile.TemporaryDirectory() as tmp:                                    # B the only threat: B captains 10, so 17 is a free variance
            toy_league(tmp, gaps={RIVAL_B: 10})
            buf = io.StringIO()
            L.report(tmp, out=lambda s: buf.write(s + chr(10)), today=datetime(2026, 9, 16, tzinfo=timezone.utc))
            line17 = next(l for l in buf.getvalue().splitlines() if " P17 " in l and "FWD" in l and "0.20" in l)
            self.assertIn("free variance", line17)
            self.assertIn("allowed differential", line17)
            line3 = next(l for l in buf.getvalue().splitlines() if " P3 " in l and "DEF" in l and "0.40" in l)
            self.assertNotIn("free variance", line3)                                  # cost 0.4 is not under 0.3
            self.assertIn("hidden until its deadline", text)
            self.assertEqual(L.allowance(24), 0.5); self.assertEqual(L.allowance(25), 1.0)


class CLI(unittest.TestCase):
    def test_cli_writes_one_file_and_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            toy_league(tmp)
            out = os.path.join(tmp, "out")
            before = sorted(os.listdir(tmp))
            with redirect_stdout(io.StringIO()):
                rc = L.main(["--data", tmp, "--out", out])
            self.assertEqual(rc, 0)
            files = os.listdir(out)
            self.assertEqual(len(files), 1); self.assertTrue(files[0].startswith("league_"))
            self.assertEqual(sorted(os.listdir(tmp)), sorted(before + ["out"]))
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'league')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
