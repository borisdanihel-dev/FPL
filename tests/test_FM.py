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
NOW9 = datetime(2098, 12, 1, tzinfo=timezone.utc)      # before the toy's GW9 deadline (tests/test_S6d.py)
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


class CheckStatistic(unittest.TestCase):
    """The check's metric, its bootstrap unit (the origin) and its bar, on toy numbers."""

    def test_the_pooled_mean_and_the_unit(self):
        import gate_v2_check as GC
        boot = GC.cluster_bootstrap([(6.0, 3), (0.0, 1), (-2.0, 2)])
        self.assertAlmostEqual(boot["mean"], 4.0 / 6)                     # pooled over player-weeks, not per origin
        self.assertEqual((boot["n_clusters"], boot["n"]), (3, 6))
        lo_cluster = min(s / n for s, n in [(6.0, 3), (0.0, 1), (-2.0, 2)])
        self.assertGreaterEqual(boot["lo"], lo_cluster - 1e-12)            # resampling origins can't go below the worst one
        same = GC.cluster_bootstrap([(6.0, 3), (0.0, 1), (-2.0, 2)])
        self.assertEqual(boot, same)                                       # the seed is fixed

    def test_the_bar_reads_the_lower_bound(self):
        import gate_v2_check as GC
        self.assertTrue(GC.passes({"lo": 0.01}))
        self.assertFalse(GC.passes({"lo": 0.0}))
        self.assertFalse(GC.passes({"lo": -0.5, "hi": 3.0}))
        self.assertFalse(GC.passes({"lo": None}))
        better = GC.cluster_bootstrap([(3.0, 2), (2.0, 2), (4.0, 1), (1.0, 1)])
        self.assertTrue(GC.passes(better))
        worse = GC.cluster_bootstrap([(-3.0, 2), (-2.0, 2), (-4.0, 1), (1.0, 1)])
        self.assertFalse(GC.passes(worse))

    def test_the_sign_of_e(self):
        r, v1, v2 = 6.0, 0.0, 4.5                                          # a flagged player who played: v2 is closer
        self.assertGreater(abs(v1 - r) - abs(v2 - r), 0)


class MatrixOnAToy(unittest.TestCase):
    """gate_v2.matrix on W3's toy world (prereg/FM.md, the tests pinned before the code): v1 is the live forecast;
    under v2 every status-'a' player is v1; each row of the rule's table on a toy player; a double gameweek split by
    the date; nothing generated after a deadline is read. The toy's horizon is GW9; GW10-11 are added as copies of
    GW9's fixtures a week and two weeks later."""

    @classmethod
    def setUpClass(cls):
        import copy
        import gzip
        import json
        from datetime import timedelta
        from tests.test_W3 import toy_world
        import xp_v2_live as XL
        toy_world(cls)
        cls.XL, cls.copy, cls.json, cls.gzip, cls.td = XL, copy, json, gzip, timedelta
        cls.d0, cls.path, cls.dl, cls.book, cls.model, _ = G.origin(cls.tmp, 9)
        cls.prior = XL.load_prior(cls.hist)
        cls.names, _ = XL.prior_names(os.path.join(cls.tmp, "fpl.sqlite"),
                                      os.path.join(cls.hist, "2026-27", "elements_positions.csv"),
                                      os.path.join(cls.hist, XL.PRIOR_SEASON))
        d = copy.deepcopy(cls.d0)
        base = [f for f in d["fixtures_next6"] if f["event"] == 9]
        for k, ev in ((1, 10), (2, 11)):
            for f in base:
                ko = datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00")) + timedelta(days=7 * k)
                d["fixtures_next6"].append(dict(f, event=ev, home=f["away"], away=f["home"],
                                                kickoff_time=ko.strftime("%Y-%m-%dT%H:%M:%SZ")))
        d["generated"] = "2098-12-30T10:00:00+00:00"                              # the toy's export says 2026; its fixtures are in 2099
        cls.d = d
        v1, _ = G.matrix(d, 9, 3, cls.book, cls.model, cls.prior, cls.names, "v1")
        cls.v1 = v1
        cls.pid = max(v1[0], key=lambda q: (v1[0][q], -q))                    # a player the model values
        cls.team = next(p["team"] for p in d["all_players"] if p["id"] == cls.pid)

    @classmethod
    def tearDownClass(cls):
        from tests.test_W3 import drop_world
        drop_world(cls)

    def flagged(self, **kw):
        d = self.copy.deepcopy(self.d)
        p = next(p for p in d["all_players"] if p["id"] == self.pid)
        p.update(kw)
        return d

    def v2(self, d):
        return G.matrix(d, 9, 3, self.book, self.model, self.prior, self.names, "v2", {})

    def test_v1_week_t_is_the_live_forecast(self):
        res = self.XL.live(self.tmp, self.hist, now=NOW9)
        self.assertEqual(self.v1[0], res["xp"])

    def test_every_a_player_is_v1(self):
        v2, modes = self.v2(self.d)
        self.assertEqual(v2, self.v1)
        self.assertTrue(all(m == ["v1"] * 3 for m in modes.values()))
        d = self.flagged(status="a", chance_next_round=75)                     # 'a' with a chance below 100: still v1
        v1c, _ = G.matrix(d, 9, 3, self.book, self.model, self.prior, self.names, "v1")
        self.assertEqual(self.v2(d)[0], v1c)
        self.assertLess(v1c[0][self.pid], self.v1[0][self.pid])

    def test_d_is_lifted_in_t_then_normal(self):
        d = self.flagged(status="d", chance_next_round=50)
        v2, modes = self.v2(d)
        lifted, _, _ = self.XL.forecast(d, 9, self.book, self.model, self.prior, self.names, lift=[self.pid])
        self.assertAlmostEqual(v2[0][self.pid], lifted[self.pid], 12)
        self.assertAlmostEqual(v2[1][self.pid], self.v1[1][self.pid], 12)           # as normal: chance 100
        self.assertEqual(modes[self.pid], ["lifted", "normal", "normal"])
        self.assertNotIn(self.pid, G.matrix(d, 9, 3, self.book, self.model, self.prior, self.names, "v1")[0][0])

    def test_s_with_a_date_is_zero_until_it(self):
        ko10 = min(datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00")) for f in self.d["fixtures_next6"]
                   if f["event"] == 10)
        d = self.flagged(status="s", chance_next_round=0, news=f"Suspended until {ko10.day} {ko10:%b}")
        v2, modes = self.v2(d)
        self.assertNotIn(self.pid, v2[0])
        self.assertAlmostEqual(v2[1][self.pid], self.v1[1][self.pid], 12)
        self.assertEqual(modes[self.pid][:2], ["out", "normal"])

    def test_i_unknown_is_zero_twice_then_half(self):
        d = self.flagged(status="i", chance_next_round=0, news="Knee injury - Unknown return date")
        v2, modes = self.v2(d)
        self.assertNotIn(self.pid, v2[0])
        self.assertNotIn(self.pid, v2[1])
        self.assertAlmostEqual(v2[2][self.pid], 0.5 * self.v1[2][self.pid], 12)
        self.assertEqual(modes[self.pid], ["out", "out", "half"])

    def test_a_double_gameweek_split_by_the_date(self):
        d = self.copy.deepcopy(self.d)
        mine = next(f for f in d["fixtures_next6"] if f["event"] == 10 and self.team in (f["home"], f["away"]))
        ko = datetime.fromisoformat(mine["kickoff_time"].replace("Z", "+00:00"))
        later = dict(mine, home=mine["away"], away=mine["home"], kickoff_time=(ko + self.td(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        d["fixtures_next6"].append(later)
        back = ko + self.td(days=2)
        p = next(p for p in d["all_players"] if p["id"] == self.pid)
        p.update(status="i", chance_next_round=0, news=f"Thigh injury - Expected back {back.day} {back:%b}")
        v2, modes = self.v2(d)
        only = self.copy.deepcopy(d)                                               # his week 10: the later fixture alone
        only["fixtures_next6"] = [f for f in only["fixtures_next6"] if f is not mine and f != mine]
        next(q for q in only["all_players"] if q["id"] == self.pid).update(status="a", chance_next_round=None, news="")
        alone, _ = G.matrix(only, 9, 3, self.book, self.model, self.prior, self.names, "v1")
        self.assertEqual(modes[self.pid][1], "normal (split)")
        self.assertAlmostEqual(v2[1][self.pid], alone[1][self.pid], 12)
        both, _ = G.matrix(self.flagged(), 9, 3, self.book, self.model, self.prior, self.names, "v1")
        self.assertNotAlmostEqual(v2[1][self.pid], both[1][self.pid] + alone[1][self.pid], 6)

    def test_nothing_after_the_deadline_is_read(self):
        late = self.json.loads(self.json.dumps(self.d0))
        late["generated"] = (self.dl + self.td(hours=1)).isoformat()
        next(p for p in late["all_players"] if p["id"] == self.pid)["status"] = "i"
        planted = os.path.join(self.tmp, "exports", "fpl_export_gw8_2099-01-02.json.gz")
        with self.gzip.open(planted, "wt", encoding="utf-8") as fh:
            self.json.dump(late, fh)
        try:
            d, path, _, _, _, _ = G.origin(self.tmp, 9)
            self.assertEqual(path, self.path)
            self.assertEqual(d["generated"], self.d0["generated"])
        finally:
            os.remove(planted)


class CheckEndToEnd(unittest.TestCase):
    """gate_v2_check.main on W3's toy (Boris, answers on FM of Thu 19 Nov late, point 3: an end-to-end test of the
    check's main()): GW9 locked with points, three flagged players in the origin's export and one under 45 minutes;
    the printed numbers against the rows file and an independent sum."""

    def setUp(self):
        import gzip
        import json
        import sqlite3
        from tests.test_W3 import toy_world
        toy_world(self)
        exp = os.path.join(self.tmp, "exports", "fpl_export_gw8_2026-10-17.json.gz")
        with gzip.open(exp, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        teams9 = {t for f in d["fixtures_next6"] if f["event"] == 9 for t in (f["home"], f["away"])}
        cand = [p for p in d["all_players"] if p["team"] in teams9 and (p.get("mins_last4") or 0) >= 45]
        self.hurt, self.gone, self.ban, self.short = (p["id"] for p in cand[:4])
        flags = {self.hurt: ("d", 50, "Calf injury - 50% chance of playing"),
                 self.gone: ("i", 0, "Knee injury - Unknown return date"),
                 self.ban: ("s", 0, "Suspended"),
                 self.short: ("d", 75, "Knock - 75% chance of playing")}
        for p in d["all_players"]:
            if p["id"] in flags:
                p["status"], p["chance_next_round"], p["news"] = flags[p["id"]]
            if p["id"] == self.short:
                p["mins_last4"] = 30                                        # under 45: outside the population
        from datetime import timedelta
        for f in [f for f in d["fixtures_next6"] if f["event"] == 9]:        # GW10 in the horizon, never locked
            ko = datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00")) + timedelta(days=7)
            d["fixtures_next6"].append(dict(f, event=10, home=f["away"], away=f["home"],
                                            kickoff_time=ko.strftime("%Y-%m-%dT%H:%M:%SZ")))
        with gzip.open(exp, "wt", encoding="utf-8") as fh:
            json.dump(d, fh)
        self.points = {p["id"]: 2 for p in d["all_players"]}
        self.points.update({self.hurt: 6, self.gone: 0, self.ban: 0})
        c = sqlite3.connect(os.path.join(self.tmp, "fpl.sqlite"))
        c.execute("update events set data_checked = 1, finished = 1 where id = 9")
        c.execute("update fixtures set finished = 1 where event = 9")
        c.executemany("insert into player_gw (player_id, event, total_points, minutes) values (?, 9, ?, ?)",
                      [(pid, pts, 90 if pts else 0) for pid, pts in self.points.items()])
        c.commit()
        c.close()

    def tearDown(self):
        from tests.test_W3 import drop_world
        drop_world(self)

    def run_main(self, origins="9", last="9"):
        import csv
        import io
        import tempfile
        from contextlib import redirect_stdout
        import gate_v2_check as GC
        out = tempfile.mkdtemp(dir=self.side)
        with redirect_stdout(io.StringIO()):
            GC.main(["--data", self.tmp, "--hist", self.hist, "--out", out, "--origins", origins, "--last", last])
        with open(os.path.join(out, "gate_v2_check.txt"), encoding="utf-8") as fh:
            text = fh.read()
        with open(os.path.join(out, "gate_v2_rows.csv"), encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        return text, rows

    def test_the_numbers_from_the_rows(self):
        text, rows = self.run_main()
        flagged = [r for r in rows if r["group"] == "flagged"]
        self.assertEqual({int(r["id"]) for r in flagged}, {self.hurt, self.gone, self.ban})   # never the 30-minute one
        e = []
        for r in flagged:
            v1, v2, real = float(r["v1"]), float(r["v2"]), float(r["r"])
            self.assertEqual(real, self.points[int(r["id"])])                   # GW9's points, not another week's
            self.assertEqual(v1, 0.0)                                            # v1: the gate
            self.assertAlmostEqual(float(r["e"]), abs(v1 - real) - abs(v2 - real), 9)
            e.append(abs(v1 - real) - abs(v2 - real))
        by_id = {int(r["id"]): float(r["v2"]) for r in flagged}
        self.assertGreater(by_id[self.hurt], 0.0)                                # d: lifted in week t
        self.assertEqual((by_id[self.gone], by_id[self.ban]), (0.0, 0.0))        # i unknown, s without a date: 0 in t
        mean = sum(e) / len(e)
        self.assertGreater(mean, 0)
        self.assertIn(f"over 3 flagged player-weeks in 1 origins: mean {mean:+.3f}, 90% [{mean:+.3f}, {mean:+.3f}]", text)
        self.assertIn("bar: the 90% lower bound above 0 - PASS.", text)
        self.assertIn("THE RETROSPECTIVE CHECK, GW9-9 scored through GW9", text)

    def test_only_locked_weeks_up_to_the_last_are_scored(self):
        _, rows = self.run_main(last="10")                                    # GW10 is in the horizon but not locked
        self.assertEqual({r["week"] for r in rows}, {"9"})
        text, rows = self.run_main(last="8")                                  # nothing up to GW8 from origin 9
        self.assertEqual(rows, [])
        self.assertIn("over 0 flagged player-weeks", text)

    def test_an_origin_without_its_export_is_reported_not_scored(self):
        text, rows = self.run_main("8-9")
        self.assertRegex(text, r"(?m)^  GW8\s+missing input, not scored: ")
        self.assertIn("NOT SCORED: GW8 (missing input above); the primary line covers 1 of 2 origins", text)
        self.assertEqual({r["origin"] for r in rows}, {"9"})


if __name__ == "__main__":
    unittest.main()
