"""S6c - the safety check: xp_v2 as tested against own_rebuilt
(tools/xp_v2_replay.py --s6c; prereg/S6c.md). Hermetic: the toy seasons of
the S4/S5/S11 tests, S6b's toy Step 10 root, a players_raw with web names,
FDR columns in the toy fixtures, and a toy 2026/27 data folder (fpl.sqlite
and projection_log.csv) in temporary folders; no network, no real data."""
import csv
import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import xp_v2_replay as X                                          # noqa: E402
from tests.test_S5 import toy_season                              # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402
from tests.test_S6b import toy_rules_root                         # noqa: E402

FDR_H, FDR_A = 2, 4


def add_s6c_inputs(hist, fdr=(FDR_H, FDR_A)):
    """The toy 2025/26 gains players_raw.csv (web_name W<id>) and the FDR
    columns of fixtures.csv (home 2, away 4 unless given)."""
    with open(os.path.join(hist, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        ids = sorted({int(r["element"]) for r in csv.DictReader(fh)})
    with open(os.path.join(hist, "players_raw.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("id,code,web_name\n")
        for pid in ids:
            fh.write(f"{pid},{1000 + pid},W{pid}\n")
    path = os.path.join(hist, "fixtures.csv")
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["team_h_difficulty"], r["team_a_difficulty"] = str(fdr[0]), str(fdr[1])
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


def by_hand(pts4, mins4, gws, prior, fdrs):
    """own's project() written out: form shrunk by SHRINK, the minutes
    reliability, the FDR adjustment per fixture, summed, rounded to 3."""
    raw90 = pts4 / mins4 * 90
    matches = mins4 / 90.0
    per90 = (raw90 * matches + prior * 4.0) / (matches + 4.0)
    rel = min(1.0, mins4 / (90.0 * max(1, gws)))
    return round(sum(per90 * rel * (1.0 + (3.0 - (fdr or 3.0)) * 0.12) for fdr in fdrs), 3)


def toy_2627(folder, locked=(5, 6), gws=(5, 6, 7)):
    """fpl.sqlite with events, fixtures, players, picks (entry 3073318) and
    player_gw for GW5-7, and a projection_log.csv with own rows: GW5 has two
    snapshots before the deadline and one after it."""
    db = sqlite3.connect(os.path.join(folder, "fpl.sqlite"))
    db.executescript("""
      create table events(id integer, name text, deadline_time text, finished integer, average_score integer,
        highest_score integer, most_captained integer, data_checked integer);
      create table fixtures(id integer, event integer, finished integer);
      create table players(id integer, web_name text, position integer);
      create table picks(entry_id integer, event integer, player_id integer, position integer, multiplier integer,
        is_captain integer, is_vice integer);
      create table player_gw(player_id integer, event integer, minutes integer, total_points integer);
    """)
    shape = [1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4]           # 2 GK, 5 DEF, 5 MID, 3 FWD
    db.executemany("insert into players values (?,?,?)", [(i, f"W{i}", pos) for i, pos in enumerate(shape, 1)])
    for g in gws:
        ok = 1 if g in locked else 0
        db.execute("insert into events values (?,?,?,?,?,?,?,?)", (g, f"Gameweek {g}", f"2026-09-{10 + g:02d}T10:00:00Z",
                                                                    ok, 0, 0, 0, ok))
        db.executemany("insert into fixtures values (?,?,?)", [(100 * g + k, g, 1 if ok else (k % 2)) for k in range(3)])
        db.executemany("insert into picks values (?,?,?,?,?,?,?)",
                       [(X.ENTRY, g, pid, slot, 1, 0, 0) for slot, pid in enumerate(range(1, 16), 1)])
        db.executemany("insert into player_gw values (?,?,?,?)",
                       [(pid, g, 0 if pid == 3 else 90, pid % 7 + 1) for pid in range(1, 16)])
    db.commit(); db.close()
    with open(os.path.join(folder, "projection_log.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh); w.writerow(E.LOG_FIELDS)
        for pid in range(1, 16):
            w.writerow(["2026-09-13T21:55:00+00:00", "own", 5, pid, f"W{pid}", f"{pid:.3f}"])          # older snapshot
            w.writerow(["2026-09-14T21:55:00+00:00", "own", 5, pid, f"W{pid}", f"{16 - pid:.3f}"])     # the last before GW5's deadline
            w.writerow(["2026-09-15T21:55:00+00:00", "own", 5, pid, f"W{pid}", f"{pid * 3:.3f}"])      # after it: never read
            w.writerow(["2026-09-15T21:55:00+00:00", "own", 6, pid, f"W{pid}", f"{pid % 5:.3f}"])
            w.writerow(["2026-09-15T21:55:00+00:00", "xg", 6, pid, f"W{pid}", "9.0"])                  # another source, written after own: never read


class Toys(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(); cls.tmp24 = tempfile.mkdtemp(); cls.rules = tempfile.mkdtemp()
        cls.odds = toy_season(cls.tmp, skip_fixture=13)
        add_s6c_inputs(cls.tmp)
        toy_prior(cls.tmp24)
        toy_rules_root(cls.rules, cls.tmp)
        cls.rescored = X.rescore(cls.rules, os.path.join(cls.rules, "rescored.csv"))

    @classmethod
    def tearDownClass(cls):
        for d in (cls.tmp, cls.tmp24, cls.rules):
            shutil.rmtree(d, ignore_errors=True)

    def inputs(self, rp, t):
        c = BT.canonical_at(rp.hist, t)
        tr = E.canonical_through(c, t - 1)
        return c, tr, E.reliability_inputs(tr, gws_played=t - 1)

    def hand(self, rp, t, pid, fdrs, prior_dir=None):
        """own_rebuilt of one player written out (by_hand) with his prior."""
        c, tr, inp = self.inputs(rp, t)
        form = X.last4(tr["rows"], t - 1)
        totals, _ = X.prior_season_totals(prior_dir or self.tmp24)
        pos_prior = E.positional_priors([{"pos": p["pos"], "pts_last4": form.get(k, (0, 0))[0],
                                          "mins_last4": form.get(k, (0, 0))[1]} for k, p in inp["players"].items()])
        tot = totals.get(c["players"][pid]["name"])
        if tot is not None and tot[1] >= X.PERSONAL_MINS and tot[0] > 0:
            prior = tot[0] / tot[1] * 90
        else:
            prior = pos_prior[inp["players"][pid]["pos"]]
        return by_hand(form[pid][0], form[pid][1], t - 1, prior, fdrs)

    def test_own_rebuilt_by_hand(self):
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        reb = rp.own_rebuilt(6)
        self.assertTrue(reb)
        c, tr, inp = self.inputs(rp, 6)
        form = X.last4(tr["rows"], 5)
        totals, _ = X.prior_season_totals(self.tmp24)
        players = [{"pos": p["pos"], "pts_last4": form.get(pid, (0, 0))[0], "mins_last4": form.get(pid, (0, 0))[1]}
                   for pid, p in inp["players"].items()]
        pos_prior = E.positional_priors(players)
        n_personal = n_positional = 0
        for pid, v in reb.items():
            p = inp["players"][pid]
            pts4, mins4 = form[pid]
            self.assertEqual(mins4, p["mins_last4"])                                       # the harness's window, the export's
            tot = totals.get(c["players"][pid]["name"])
            if tot is not None and tot[1] >= X.PERSONAL_MINS and tot[0] > 0:
                prior = tot[0] / tot[1] * 90; n_personal += 1
            else:
                prior = pos_prior[p["pos"]]; n_positional += 1
            fx = rp.s11.club_fixtures(p["team"], 6)
            fdrs = [FDR_H if p["team"] == f["home"] else FDR_A for _, f in fx]
            self.assertEqual(v, by_hand(pts4, mins4, 5, prior, fdrs), pid)
        self.assertGreater(n_personal, 0); self.assertGreater(n_positional, 0)            # both priors occur in the toy
        # the 45-minute gate: a player under it gets nothing; none at or below 0 is kept
        for pid, p in inp["players"].items():
            if form.get(pid, (0, 0))[1] < 45:
                self.assertNotIn(pid, reb)
        self.assertTrue(all(v > 0 for v in reb.values()))
        self.assertEqual((X.OWN_HORIZON, X.PERSONAL_MINS, X.ENTRY, X.INFO_GWS), (6, 450, 3073318, (5, 6, 7)))
        self.assertEqual(X.OWN_REBUILT_LACKS[:16], "own_rebuilt = li")
        for word in ("pre-deadline FDR", "status", "chance_next_round", "before 2024/25", "full name"):
            self.assertIn(word, X.OWN_REBUILT_LACKS)

    def test_window_fdr_side_and_double(self):
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        base = rp.own_rebuilt(6)
        pid = max(base, key=lambda k: (base[k], -k))
        for rnd, moves in ((1, False), (6, False), (2, True)):                             # t-5 and t: no; t-4: yes
            rp2 = X.Replay(self.tmp, self.tmp24, self.odds)
            for r in rp2.hist["c"]["rows"]:
                if r["player_id"] == pid and r["event"] == rnd:
                    r["pts"] = (r["pts"] or 0) + 20
            got = rp2.own_rebuilt(6)
            (self.assertNotEqual if moves else self.assertEqual)(got[pid], base[pid], rnd)
        # the FDR side: home takes team_h_difficulty; swapping the columns moves every forecast
        swapped = tempfile.mkdtemp()
        try:
            for name in os.listdir(self.tmp):
                if os.path.isfile(os.path.join(self.tmp, name)):
                    shutil.copy(os.path.join(self.tmp, name), swapped)
            add_s6c_inputs(swapped, fdr=(FDR_A, FDR_H))
            sw = X.Replay(swapped, self.tmp24, self.odds).own_rebuilt(6)
        finally:
            shutil.rmtree(swapped, ignore_errors=True)
        self.assertEqual(set(sw), set(base))
        self.assertTrue(all(sw[k] != base[k] for k in base))
        # a double gameweek sums its fixtures
        rp3 = X.Replay(self.tmp, self.tmp24, self.odds)
        c, tr, inp = self.inputs(rp3, 6)
        team = inp["players"][pid]["team"]
        fid, f = rp3.s11.club_fixtures(team, 6)[0]
        extra = dict(f, home=f["away"], away=f["home"])                                     # the return fixture in the same round
        rp3.s5.fixtures["DGW"] = extra
        dbl = rp3.own_rebuilt(6)
        fdrs = [FDR_H if team == g["home"] else FDR_A for g in (f, extra)]
        self.assertEqual(sorted(fdrs), [FDR_H, FDR_A])
        self.assertEqual(dbl[pid], self.hand(rp3, 6, pid, fdrs))
        self.assertEqual(base[pid], self.hand(rp3, 6, pid, fdrs[:1]))
        self.assertGreater(dbl[pid], base[pid])

    def test_personal_prior_filter_and_ambiguous_names(self):
        tmp24b = tempfile.mkdtemp()
        try:
            toy_prior(tmp24b, rename={2: "P1"})                                              # 'P1' held by two 2024/25 elements
            totals, ambiguous = X.prior_season_totals(tmp24b)
            self.assertIn("P1", ambiguous); self.assertNotIn("P1", totals)
            rp = X.Replay(self.tmp, tmp24b, self.odds)
            reb = rp.own_rebuilt(6)
            hist_rows = []
            c, tr, inp = self.inputs(rp, 6)
            for pid in sorted(inp["players"]):
                tot = totals.get(c["players"][pid]["name"])
                if tot is not None and tot[1] >= X.PERSONAL_MINS:
                    hist_rows.append(pid)
            self.assertNotIn(1, hist_rows)                                                   # the ambiguous name: no personal prior
            under = [n for n, (p, m) in totals.items() if m < X.PERSONAL_MINS]
            self.assertTrue(under)                                                           # some toy 2024/25 players are under 450
            # a player under 450 minutes falls to the positional prior: his forecast equals the positional one
            form = X.last4(tr["rows"], 5)
            pos_prior = E.positional_priors([{"pos": p["pos"], "pts_last4": form.get(k, (0, 0))[0],
                                              "mins_last4": form.get(k, (0, 0))[1]} for k, p in inp["players"].items()])
            checked = 0
            for pid, v in reb.items():
                name = c["players"][pid]["name"]
                if name in under or name == "P1":
                    p = inp["players"][pid]
                    fx = rp.s11.club_fixtures(p["team"], 6)
                    fdrs = [FDR_H if p["team"] == f["home"] else FDR_A for _, f in fx]
                    self.assertEqual(v, by_hand(form[pid][0], form[pid][1], 5, pos_prior[p["pos"]], fdrs))
                    checked += 1
            self.assertGreater(checked, 0)
        finally:
            shutil.rmtree(tmp24b, ignore_errors=True)
        nowr = tempfile.mkdtemp()
        try:
            for name in os.listdir(self.tmp):
                if os.path.isfile(os.path.join(self.tmp, name)) and name != "players_raw.csv":
                    shutil.copy(os.path.join(self.tmp, name), nowr)
            with self.assertRaises(X.MissingInput):
                X.Replay(nowr, self.tmp24, self.odds).own_rebuilt(6)                        # no web names: refused
        finally:
            shutil.rmtree(nowr, ignore_errors=True)

    def test_point_in_time(self):
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        reb, v2 = rp.own_rebuilt(5), rp.xp_v2(5)[0]
        rp2 = X.Replay(self.tmp, self.tmp24, self.odds)
        for r in rp2.hist["c"]["rows"]:
            if r["event"] >= 5:
                r["pts"] = 50; r["minutes"] = 90; r["starts"] = 1; r["xg"] = 9.0
        for g in range(5, rp2.hist["through"] + 1):
            for r in rp2.hist["raw"][g]:
                r["minutes"] = "90"; r["starts"] = "1"; r["total_points"] = "50"
        self.assertEqual(rp2.own_rebuilt(5), reb)
        self.assertEqual({p: round(v, 12) for p, v in rp2.xp_v2(5)[0].items()}, {p: round(v, 12) for p, v in v2.items()})
        rp3 = X.Replay(self.tmp, self.tmp24, self.odds)
        for r in rp3.hist["c"]["rows"]:
            if r["event"] == 4:
                r["pts"] = (r["pts"] or 0) + 7
        self.assertNotEqual(rp3.own_rebuilt(5), reb)                                         # round t-1 is training: it moves

    def test_s6c_run_reproduces_s6b_and_the_decision_line(self):
        buf = io.StringIO()
        res = X.test_s6c(self.tmp, self.tmp24, out=lambda s: buf.write(s + chr(10)), odds_file=self.odds, first=5, last=6,
                         n_squads=3, rescored=self.rescored)
        s6b = X.test_2526(self.tmp, self.tmp24, self.rules, out=lambda s: None, odds_file=self.odds, first=5, last=6,
                          n_squads=3, rescored=self.rescored)
        text = buf.getvalue()
        self.assertEqual([r["gw"] for r in res["per"]], [5, 6])
        for a, b in zip(res["per"], s6b["per"]):
            self.assertEqual(a["v2"], b["v2"]); self.assertEqual(a["prx"], b["own"])         # xp_v2 as tested and own_proxy: S6b's path
        self.assertEqual(res["squads"], s6b["squads"])
        # the own_rebuilt side is own_rebuilt's realised points on the re-scored outcomes
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        rp.pl.rp.actual = X.actuals_from(self.rescored)
        squads = CH.sample_squads(CH.gw1_candidates(rp.hist), 3, 7)
        for rec in res["per"]:
            t = rec["gw"]
            reb = rp.own_rebuilt(t)
            want = sum(rp.pl.realised(rp.pl.squad_rows(s, t), t, reb) for s in squads) / 3
            self.assertAlmostEqual(rec["reb"], want)
            self.assertAlmostEqual(rec["diff"], rec["v2"] - rec["reb"])
            self.assertAlmostEqual(rec["reb_prx"], rec["reb"] - rec["prx"])
        self.assertAlmostEqual(res["season"], sum(r["diff"] for r in res["per"]))
        self.assertIn(X.OWN_REBUILT_LACKS, text); self.assertIn("decision (the ruling", text)
        self.assertIn(res["decision"], text); self.assertIn("own_rebuilt - own_proxy", text)
        self.assertEqual(res["decision"], X.decision_line(res["boot"]))
        self.assertEqual(X.decision_line({"hi": -0.001}), "GW8 SWITCH SUSPENDED: own picks GW8")
        self.assertEqual(X.decision_line({"hi": 0.0}), "GW8 SWITCH STANDS")
        self.assertEqual(X.decision_line({"hi": 0.4, "lo": -0.9}), "GW8 SWITCH STANDS")
        from unittest import mock
        with mock.patch.object(X.BT, "bootstrap_mean", return_value={"mean": -1.0, "lo": -2.5, "hi": -0.2, "n": 2, "p": 0.01}):
            r2 = X.test_s6c(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=2,
                            rescored=self.rescored)
        self.assertEqual(r2["decision"], "GW8 SWITCH SUSPENDED: own picks GW8")              # the upper bound decides
        with mock.patch.object(X.BT, "bootstrap_mean", return_value={"mean": -1.0, "lo": -2.5, "hi": 0.1, "n": 2, "p": 0.2}):
            r3 = X.test_s6c(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=2,
                            rescored=self.rescored)
        self.assertEqual(r3["decision"], "GW8 SWITCH STANDS")
        lifted = {k: (v[0] + 30.0, v[1]) if k[1] == 5 else v for k, v in self.rescored.items()}
        r4 = X.test_s6c(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=3,
                        rescored=lifted)
        self.assertGreater(r4["per"][0]["reb"], res["per"][0]["reb"] + 100)                  # the outcomes are the re-scored points
        with self.assertRaises(X.MissingInput):
            X.test_s6c(self.tmp, self.tmp24, out=lambda s: None, odds_file=self.odds, first=5, last=6, n_squads=3)

    def test_realised_on_matches_the_replay(self):
        rp = X.Replay(self.tmp, self.tmp24, self.odds)
        rp.pl.rp.actual = X.actuals_from(self.rescored)
        for squad in CH.sample_squads(CH.gw1_candidates(rp.hist), 4, 7):
            rows = rp.pl.squad_rows(squad, 5)
            xp = rp.own_rebuilt(5)
            self.assertEqual(X.realised_on(rows, xp, rp.pl.rp.actual[5])[0], rp.pl.realised(rows, 5, xp))


class Info2627(unittest.TestCase):
    def test_last_snapshot_lockdown_and_not_available(self):
        d = tempfile.mkdtemp()
        try:
            toy_2627(d)
            buf = io.StringIO()
            recs = X.info_2627(d, out=lambda s: buf.write(s + chr(10)))
            text = buf.getvalue()
            self.assertEqual([r["graded"] for r in recs], [True, True, False])                # GW7 not locked down
            self.assertIn("GW7: not locked down: not graded", text)
            self.assertEqual(recs[0]["snapshot"], "2026-09-14T21:55:00+00:00")                # the last snapshot before the deadline
            log_rows = E.read_log(os.path.join(d, E.LOG_PATH))
            own5, day = X.recorded_own(log_rows, 5, {"events": [{"event": 5, "deadline_time": "2026-09-15T10:00:00Z"}]})
            self.assertEqual(day, "2026-09-14T21:55:00+00:00"); self.assertEqual(own5[1], 15.0); self.assertEqual(own5[15], 1.0)
            self.assertEqual(X.recorded_own(log_rows, 5, {"events": [{"event": 5, "deadline_time": "2026-09-14T10:00:00Z"}]})[1],
                             "2026-09-13T21:55:00+00:00")                                      # an earlier deadline: the earlier snapshot
            rows = [{"id": i, "pos": p} for i, p in enumerate([1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4], 1)]
            actual = {pid: (float(pid % 7 + 1), 0.0 if pid == 3 else 90.0) for pid in range(1, 16)}
            self.assertEqual(recs[0]["own"], X.realised_on(rows, own5, actual)[0])
            self.assertEqual(recs[0]["own_cap"], 1)                                           # the highest own projection in the XI
            self.assertEqual(recs[1]["own"], X.realised_on(rows, {pid: float(pid % 5) for pid in range(1, 16)}, actual)[0])   # GW6: own's rows, not xg's
            self.assertIn("xp_v2 as tested: not available", text)
            self.assertIn("captain W1;", text)                                                  # the captain by name
            self.assertNotIn("v2", recs[0])
            # with a live xp_v2 the paired line prints
            buf2 = io.StringIO()
            recs2 = X.info_2627(d, out=lambda s: buf2.write(s + chr(10)), xp_v2_fn=lambda dd, g: {pid: float(pid) for pid in range(1, 16)})
            self.assertEqual(recs2[0]["v2_cap"], 15)
            self.assertIn("xp_v2 - own", buf2.getvalue())
            # the guard needs data_checked AND every fixture finished
            db = sqlite3.connect(os.path.join(d, "fpl.sqlite"))
            db.execute("update events set data_checked = 1 where id = 7"); db.commit()
            recs3 = X.info_2627(d, out=lambda s: None)
            self.assertFalse(recs3[2]["graded"])                                              # GW7 fixtures still unfinished
            db.execute("update events set data_checked = 0 where id = 7")
            db.execute("update fixtures set finished = 1 where event = 7"); db.commit()
            self.assertFalse(X.info_2627(d, out=lambda s: None)[2]["graded"])                 # every fixture finished, not data_checked
            db.execute("update events set data_checked = 1 where id = 7"); db.commit(); db.close()
            self.assertTrue(X.info_2627(d, out=lambda s: None)[2]["graded"])                  # both: graded
        finally:
            shutil.rmtree(d, ignore_errors=True)
        with self.assertRaises(X.MissingInput):
            X.info_2627(tempfile.gettempdir() + os.sep + "no-such-fpl-data-folder")


class CLI(unittest.TestCase):
    def test_cli(self):
        tmp, tmp24, rules, data = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            odds = toy_season(tmp); add_s6c_inputs(tmp); toy_prior(tmp24); toy_rules_root(rules, tmp); toy_2627(data)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = X.main(["--s6c", "--hist", tmp, "--prior", tmp24, "--rules", rules, "--odds", odds, "--out", out,
                             "--data", data, "--last", "6", "--squads", "2"])
            self.assertEqual(rc, 0)
            with open(os.path.join(out, "s6c_2025-26.txt"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("S6C SAFETY CHECK", text); self.assertIn("decision (the ruling", text)
            self.assertIn("2026/27 GW5-7 (information only", text)
            with open(os.path.join(out, "run.txt"), encoding="utf-8") as fh:
                run = fh.read()
            self.assertIn("s6c_2025-26.txt", run); self.assertIn("rescored_2025-26.csv", run)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(X.main(["--s6c", "--hist", tmp, "--prior", tmp24, "--rules", rules, "--odds", odds,
                                         "--out", out, "--data", os.path.join(data, "missing"), "--last", "6",
                                         "--squads", "2"]), 2)                                    # no data folder: refused
        finally:
            for d in (tmp, tmp24, rules, data):
                shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
