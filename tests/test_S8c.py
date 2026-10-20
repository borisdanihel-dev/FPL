"""S8c - the live transfer planner on xp_v2, no hits, and the bundle's planner
section (tools/planner_live.py, tools/gw_pass.py; prereg/S8c.md, Ruling Tue
20 Oct point 1). Hermetic: S6d's toy 2026/27 data folder and toy history
root in temporary folders; no real data."""
import csv
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import builder as B                                               # noqa: E402
import capflag as CF                                              # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import chips as CH                                                # noqa: E402
import gw_pass as G                                               # noqa: E402
import planner as PL                                              # noqa: E402
import planner_live as PLV                                        # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import points_pmf as PM                                           # noqa: E402
import fpl_edge as FE                                             # noqa: E402
from tests.test_S6d import toy_live, toy_hist_root, gw9_snapshot, NOW9   # noqa: E402
from tests.test_S5 import api_event, toy_snapshot                 # noqa: E402


class Toy(unittest.TestCase):
    def setUp(self):
        self.tmp, self.hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        toy_live(self.tmp); toy_hist_root(self.hist)
        gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        self.budget = mock.patch.object(PLV.E, "selling_budget", return_value=(100.0, ""))
        self.budget.start()

    def tearDown(self):
        self.budget.stop()
        shutil.rmtree(self.tmp, ignore_errors=True); shutil.rmtree(self.hist, ignore_errors=True)

    def test_the_matrix_is_s15s_with_every_source(self):
        d, path, target, weeks_xp, srcs, p_start, snap = PLV.live_inputs(self.tmp, self.hist)
        want = B.live_matrix(self.tmp, self.hist, PL.HORIZON)
        self.assertEqual(weeks_xp, want[3]); self.assertEqual(target, want[2])
        self.assertEqual(Counter(("week t" if u == target else "later weeks", s) for u, _, _, s in srcs), want[4])
        self.assertEqual(snap, "odds_2098-12-31T10-00-00Z.json.gz")
        self.assertTrue(srcs and all(s in ("odds", "fallback") for *_, s in srcs))

    def test_the_plans_are_s8s_with_no_hits_and_one_ft(self):
        lines = []
        res = PLV.plan(self.tmp, self.hist, lines.append)
        d, path, target, weeks_xp, srcs, p_start, snap = PLV.live_inputs(self.tmp, self.hist)
        squad = CH.my_squad(d)
        bank = 100.0 - sum(r["selling"] for r in squad)
        market = [{"id": p["id"], "name": p["web_name"], "team": p["team"], "pos": p["pos"], "price": p["price"], "status": p["status"]}
                  for p in d["all_players"] if p["status"] == "a" and (p.get("mins_last4") or 0) >= 45]
        want, pool = PL.rank_plans(squad, bank, market, weeks_xp, 1, p_start, 0.85, PL.SCHEDULES["boris"], hits_allowed=False)
        self.assertEqual(res["scored"], want)
        self.assertTrue(all(ev["hits"] == 0 and ev["used"] <= 1 for ev in res["scored"]))      # no hit, one free transfer
        self.assertEqual(res["simple"], PL.baseline_plan(squad, bank, pool, weeks_xp[0], 1))
        self.assertTrue(lines[0].startswith("TRANSFER PLANNER ON XP_V2  GW9-14")); self.assertIn("no hits", lines[0])
        self.assertTrue(any(l.startswith("  DEFAULT: ") for l in lines))
        self.assertTrue(any(l.startswith("  the simple rule beside it") for l in lines))
        self.assertTrue(any(l.startswith("  lambdas GW9: ") and "odds" in l for l in lines))
        with mock.patch.object(PLV.PL, "baseline_plan", wraps=PL.baseline_plan) as bp:
            PLV.plan(self.tmp, self.hist, lambda s: None)
        self.assertEqual(bp.call_args.args[3], weeks_xp[0]); self.assertNotEqual(weeks_xp[0], weeks_xp[1])   # the simple rule on week t
        with mock.patch.object(PLV.PL, "rank_plans", wraps=PL.rank_plans) as rp:
            PLV.plan(self.tmp, self.hist, lambda s: None)
        args, kw = rp.call_args
        self.assertEqual((args[4], args[6], kw["hits_allowed"]), (1, 0.85, False)); self.assertEqual(args[7], PL.SCHEDULES["boris"])

    def test_the_bundle_section_and_its_fallback(self):
        buf = io.StringIO()
        G.bundle(self.tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=self.hist)
        text = buf.getvalue()
        sec = text.split("TRANSFER PLANNER: THE XP_V2 NO-HIT DEFAULT, S8 AND THE BASELINE")[1].split("S9 LEAGUE")[0]
        self.assertIn("TRANSFER PLANNER ON XP_V2", sec); self.assertIn("below, information: S8's planner on own xP", sec)
        self.assertIn("the transfer default from GW8 is the no-hit planner on xp_v2", text.splitlines()[0])
        shutil.rmtree(os.path.join(self.hist, "2025-26"))
        buf = io.StringIO()
        G.bundle(self.tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=self.hist)
        sec = buf.getvalue().split("TRANSFER PLANNER: THE XP_V2 NO-HIT DEFAULT, S8 AND THE BASELINE")[1].split("S9 LEAGUE")[0]
        self.assertIn("the xp_v2 planner: missing input", sec); self.assertIn("the ruling's fallback", sec)
        self.assertNotIn("TRANSFER PLANNER ON XP_V2", sec)
        self.assertIn("TRANSFER PLANNER  export", sec)                                         # S8's own planner still printed


class UnpricedFixture(unittest.TestCase):
    """Amendment 1, point 2: a fixture the snapshot does not price is printed as the fallback."""

    def setUp(self):
        self.tmp, self.hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        toy_live(self.tmp); toy_hist_root(self.hist)
        _, _, fixtures, _, _ = OL.sqlite_tables(self.tmp)
        gw9 = [f for f in fixtures if f["event"] == 9]
        self.assertGreaterEqual(len(gw9), 2)
        events = [api_event(f["home"], f["away"], f["kickoff"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                            [("b1", 2.0, 3.4, 3.8, 1.9, 1.9, False)]) for f in gw9[:1]]          # only the first is priced
        toy_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", events, fetched_at="2098-12-31T10:00:00Z")
        self.budget = mock.patch.object(PLV.E, "selling_budget", return_value=(100.0, ""))
        self.budget.start()

    def tearDown(self):
        self.budget.stop()
        shutil.rmtree(self.tmp, ignore_errors=True); shutil.rmtree(self.hist, ignore_errors=True)

    def test_the_unpriced_fixture_prints_fallback(self):
        d, path, target, weeks_xp, srcs, p_start, snap = PLV.live_inputs(self.tmp, self.hist)
        week_t = [s for u, _, _, s in srcs if u == target]
        self.assertEqual(week_t.count("odds"), 1); self.assertEqual(week_t.count("fallback"), len(week_t) - 1)
        self.assertEqual(Counter(("week t" if u == target else "later weeks", s) for u, _, _, s in srcs),
                         B.live_matrix(self.tmp, self.hist, PL.HORIZON)[4])                        # the matrix's own sources
        lines = []
        PLV.plan(self.tmp, self.hist, lines.append)
        self.assertEqual([l for l in lines if l.startswith(f"  lambdas GW{target}: ")],
                         [f"  lambdas GW{target}: " + ", ".join(f"{h}-{a} {s}" for u, h, a, s in srcs if u == target)])
        self.assertIn(" fallback", lines[[l.startswith(f"  lambdas GW{target}: ") for l in lines].index(True)])


def breaking_move(squad, n0=90000):
    """(club, outs, ins): a move that brings one club to 3 goalkeepers and defenders,
    the players out being midfielders and forwards."""
    club = next(r["team"] for r in squad if r["pos"] in (1, 2))
    k = 3 - sum(1 for r in squad if r["pos"] in (1, 2) and r["team"] == club)
    outs = [r for r in squad if r["pos"] in (3, 4)][:k]
    ins = [{"id": n0 + j, "name": f"New{j}", "team": club, "pos": 2, "price": 4.0, "status": "a"} for j in range(k)]
    return club, outs, ins


def ev_of(outs, ins, score):
    return {"score": score, "gain": score, "gains": [score / 6] * 6, "lost": 0.0, "used": len(ins), "hits": 0,
            "outs": list(outs), "ins": list(ins)}


class CapFlag(unittest.TestCase):
    """Amendment 1, point 3: every printed squad or suggested move that breaks the GK+DEF 2-per-club cap is flagged."""

    def test_the_helper(self):
        rows = [{"id": 1, "team": "ARS", "pos": 1}, {"id": 2, "team": "ARS", "pos": 2}, {"id": 3, "team": "ARS", "pos": 3},
                {"id": 4, "team": "LIV", "pos": 2}, {"id": 5, "team": "LIV", "pos": 2}]
        self.assertEqual(CF.flag(rows), "")                                                        # 2 is the cap; a MID does not count
        more = rows + [{"id": 6, "team": "LIV", "pos": 1}, {"id": 7, "team": "ARS", "pos": 2}, {"id": 8, "team": "ARS", "pos": 2}]
        self.assertEqual(CF.flag(more), "   breaks the cap: ARS 4, LIV 3")                        # sorted by club
        self.assertEqual(CF.move_flag(rows, [rows[2]], [{"id": 9, "team": "ARS", "pos": 2}]), "   breaks the cap: ARS 3")
        self.assertEqual(CF.move_flag(more, [more[5]], []), "   breaks the cap: ARS 4")            # judged after the move
        self.assertEqual(CF.move_flag(more, [more[0], more[6]], []), "   breaks the cap: LIV 3")
        self.assertEqual(CF.move_flag(more, [more[0], more[6], more[5]], []), "")
        self.assertEqual(CF.move_flag(rows, [], []), "")

    def setUp(self):
        self.tmp, self.hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        toy_live(self.tmp); toy_hist_root(self.hist)
        gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        self.budget = mock.patch.object(PLV.E, "selling_budget", return_value=(100.0, ""))
        self.budget.start()
        d, _ = CH.newest_export(self.tmp)
        self.orig = CH.my_squad
        self.toy15 = self.orig(d)
        self.assertEqual(CF.flag(self.toy15), "   breaks the cap: ARS 3")                         # the toy's own 15 is over the cap
        teams = sorted({p["team"] for p in d["all_players"]})

        def kept(dd):                                    # a copy of the toy's 15 that keeps the cap: the excess GK+DEF moved to a free club
            rows = [dict(r) for r in self.orig(dd)]
            while CF.breaks(rows):
                club = CF.breaks(rows)[0][0]
                r = [r for r in rows if r["pos"] in (1, 2) and r["team"] == club][-1]
                gkdef, total = Counter(x["team"] for x in rows if x["pos"] in (1, 2)), Counter(x["team"] for x in rows)
                r["team"] = next(t for t in teams if gkdef[t] == 0 and total[t] < 3)
            return rows
        self.mine = mock.patch.object(CH, "my_squad", side_effect=kept)
        self.mine.start()
        self.squad = CH.my_squad(d)
        self.assertEqual(CF.flag(self.squad), "")
        self.club, self.outs, self.ins = breaking_move(self.squad)
        self.flag = f"   breaks the cap: {self.club} 3"
        self.brk, self.keep = ev_of(self.outs, self.ins, 9.0), ev_of([], [], 1.0)

    def tearDown(self):
        self.mine.stop(); self.budget.stop()
        shutil.rmtree(self.tmp, ignore_errors=True); shutil.rmtree(self.hist, ignore_errors=True)

    def test_planner_live(self):
        real = PL.rank_plans

        def rank(*a, **k):
            _, pool = real(*a, **k)
            return [self.brk, self.keep], pool
        lines = []
        with mock.patch.object(PL, "rank_plans", side_effect=rank), \
             mock.patch.object(PL, "baseline_plan", return_value=(tuple(self.outs), tuple(self.ins))):
            PLV.plan(self.tmp, self.hist, lines.append)
        top = [l for l in lines if l.startswith(("   1 ", "   2 "))]
        self.assertTrue(top[0].endswith(self.flag), top[0]); self.assertNotIn("breaks the cap", top[1])
        self.assertTrue(next(l for l in lines if l.startswith("  DEFAULT: ")).endswith(self.flag))
        simple = next(l for l in lines if l.startswith("  the simple rule beside it"))
        self.assertIn(PLV.plan_text(self.brk) + self.flag + "; on the planner's score", simple)
        bb = [l for l in lines if l.startswith(("    1 ", "    2 "))]
        self.assertEqual(sorted(l.endswith(self.flag) for l in bb), [False, True])
        self.assertTrue(all(("roll" in l) != l.endswith(self.flag) for l in bb))

    def test_s8s_planner(self):
        real = PL.rank_plans

        def rank(squad, bank, market, xp_weeks, k, p_start, decay=PL.DECAY, schedule=None, **kw):
            _, pool = real(squad, bank, market, xp_weeks, k, p_start, decay, schedule or PL.SCHEDULES["boris"])
            if kw:
                return [self.brk], pool                                        # the exploratory lines
            return ([self.keep, self.brk] if decay == PL.DECAY else [self.brk]), pool
        lines = []
        with mock.patch.object(PL, "rank_plans", side_effect=rank):
            PL.live(self.tmp, lines.append)
        firsts = [l for l in lines if l.startswith("   1 ")]
        self.assertEqual(len(firsts), len(PL.SCHEDULES))
        for l in firsts:                                                           # the roll, and the decay alternatives flagged in brackets
            self.assertNotIn("roll" + self.flag, l)
            self.assertIn("[decay 0.8 prefers " + "; ".join(f"{o['name']} -> {n['name']}" for o, n in zip(self.outs, self.ins))
                          + self.flag + "; decay 0.9 prefers ", l)
            self.assertTrue(l.endswith(self.flag + "]"), l)
        for l in [l for l in lines if l.startswith("   2 ")]:
            self.assertTrue(l.endswith(self.flag), l)
        expl = [l for l in lines if l.startswith("  exploratory, ")]
        self.assertEqual(len(expl), 2)
        for l in expl:
            self.assertIn(self.flag + "  score ", l)

    def test_the_bundle(self):
        real = PL.rank_plans

        def rank(*a, **k):
            _, pool = real(*a, **k)
            return [self.brk, self.keep], pool
        named = [("a named move", self.brk, None), ("roll", self.keep, None)]
        buf = io.StringIO()
        with mock.patch.object(PL, "rank_plans", side_effect=rank), \
             mock.patch.object(PL, "baseline_plan", return_value=(tuple(self.outs), tuple(self.ins))), \
             mock.patch.object(G, "named_plans", return_value=named):
            G.bundle(self.tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=self.hist)
        lines = buf.getvalue().splitlines()
        for head in ("  BASELINE (", "  planner top plan: ", "  planner, no hits: "):
            l = next(l for l in lines if l.startswith(head))
            self.assertTrue(l.endswith(self.flag), l)
        self.assertTrue(next(l for l in lines if "a named move: " in l).endswith(self.flag))
        self.assertTrue(next(l for l in lines if l.rstrip().endswith("roll: roll")))               # the roll keeps the cap: no flag
        summary = next(l for l in lines if " slots differ; the XI " in l)
        self.assertNotIn("breaks the cap", summary)                                                 # our 15 keeps the cap

    def test_the_bundle_flags_our_15(self):
        buf = io.StringIO()
        with mock.patch.object(CH, "my_squad", side_effect=self.orig):                           # the toy's own 15, over the cap
            G.bundle(self.tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=self.hist)
        lines = buf.getvalue().splitlines()
        summary = next(l for l in lines if " slots differ; the XI " in l)
        self.assertTrue(summary.endswith("   breaks the cap: ARS 3"), summary)
        self.assertTrue(next(l for l in lines if l.startswith("  DEFAULT: roll") or l.startswith("  DEFAULT: ")))


def CHt_newest(tmp):
    return CH.newest_export(tmp)[0]


class FixedNow(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW9


class XpV2Csv(unittest.TestCase):
    """Amendment 3: the bundle writes xp_v2_all.csv from the same run; the print is unchanged."""

    def setUp(self):
        self.tmp, self.hist, self.out = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        for p in (self.tmp, self.hist, self.out):
            self.addCleanup(shutil.rmtree, p, True)
        toy_live(self.tmp); toy_hist_root(self.hist)
        _, _, fixtures, _, _ = OL.sqlite_tables(self.tmp)
        gw9 = [f for f in fixtures if f["event"] == 9]
        events = [api_event(f["home"], f["away"], f["kickoff"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                            [("b1", 2.0, 3.4, 3.8, 1.9, 1.9, False)]) for f in gw9[:1]]          # one priced, the rest on the fallback
        toy_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", events, fetched_at="2098-12-31T10:00:00Z")
        import gzip, json
        path = os.path.join(self.tmp, "exports", sorted(os.listdir(os.path.join(self.tmp, "exports")))[-1])
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        mine = {r["player_id"] for r in d["squads"] if r["entry_id"] == d["my_entry"]}
        self.out_id = next(int(p["id"]) for p in d["all_players"] if p["id"] not in mine and p["status"] == "a")
        for p in d["all_players"]:
            if int(p["id"]) == self.out_id:
                p["status"] = "i"                                                            # injured: not forecast
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(d, fh)
        for p in (mock.patch.object(G.E, "selling_budget", return_value=(100.0, "")), mock.patch.object(G, "datetime", FixedNow)):
            p.start(); self.addCleanup(p.stop)

    def main(self, out):
        with redirect_stdout(io.StringIO()):
            return G.main(["--data", self.tmp, "--hist", self.hist, "--out", out])

    def test_the_rows_are_the_forecast(self):
        self.assertEqual(self.main(self.out), 0)
        with open(os.path.join(self.out, "xp_v2_all.csv"), encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(rows[0], ["id", "name", "team", "position", "xp_v2", "p_start", "lambda_source"])
        res = XL.live(self.tmp, self.hist, NOW9)
        d = res["d"]
        self.assertEqual([int(r[0]) for r in rows[1:]], sorted(int(p["id"]) for p in d["all_players"]))   # every player, by id
        by = {int(r[0]): r for r in rows[1:]}
        fx = XL.target_fixtures(d, res["target"])
        seen = Counter()
        for p in d["all_players"]:
            pid, r = int(p["id"]), by[int(p["id"])]
            self.assertEqual(r[1:4], [p["web_name"], p["team"], {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}[p["pos"]]])
            if pid in res["xp"]:
                self.assertEqual(r[4:6], [repr(float(res["xp"][pid])), repr(float(res["detail"][pid]["p_start"]))])   # exact, repr
                want = ";".join(res["sources"][fid] for fid, f in sorted(fx.items(), key=lambda kv: (kv[1]["kickoff"], kv[0]))
                                if p["team"] in (f["home"], f["away"]))
                self.assertEqual(r[6], want)
                seen[r[6]] += 1
            else:
                self.assertEqual(r[4:], ["0.0", "", "not forecast"])                                 # the bundle's "0 in the choice"
                seen["not forecast"] += 1
        self.assertTrue(seen["odds"] and seen["fallback"] and seen["not forecast"], seen)
        self.assertEqual(by[self.out_id][4:], ["0.0", "", "not forecast"])
        with open(os.path.join(self.out, "run.txt"), encoding="utf-8") as fh:
            run = fh.read()
        sha = hashlib.sha256(open(os.path.join(self.out, "xp_v2_all.csv"), "rb").read()).hexdigest()
        self.assertIn(f"  xp_v2_all.csv  sha256 {sha}", run)

    def test_the_print_is_the_same_without_the_csv(self):
        self.assertEqual(self.main(self.out), 0)
        real = G.bundle
        other = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, other, True)
        with mock.patch.object(G, "bundle", side_effect=lambda *a, **k: real(*a, **dict(k, keep=None))):
            self.assertEqual(self.main(other), 0)
        self.assertTrue(os.path.exists(os.path.join(self.out, "xp_v2_all.csv")))
        self.assertFalse(os.path.exists(os.path.join(other, "xp_v2_all.csv")))
        a, b = (open(os.path.join(p, "gw9_pass.txt"), "rb").read() for p in (self.out, other))
        self.assertEqual(a, b)                                                                       # byte-identical

    def test_every_value_is_the_pickers(self):
        """The clarified point 3: every CSV value equals the value the bundle's xp_v2 XI picker used."""
        import gzip, json
        path = os.path.join(self.tmp, "exports", sorted(os.listdir(os.path.join(self.tmp, "exports")))[-1])
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        mine = [r["player_id"] for r in sorted(d["squads"], key=lambda r: r["slot"]) if r["entry_id"] == d["my_entry"]]
        ours_out = next(int(p["id"]) for p in d["all_players"] if p["id"] in mine and p["pos"] == 3)
        for p in d["all_players"]:
            if int(p["id"]) == ours_out:
                p["status"] = "d"                                                          # one of our 15 not forecast
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(d, fh)
        res = XL.live(self.tmp, self.hist, NOW9)
        self.assertNotIn(ours_out, res["xp"])
        calls, real = [], CH.xi_and_bench

        def spy(squad, pts):
            xi, bench, gk = real(squad, pts)
            calls.append((pts, {r["id"]: r["proj"] for r in list(xi) + list(bench) + [gk]}))
            return xi, bench, gk
        with mock.patch.object(G.CH, "xi_and_bench", side_effect=spy):
            self.assertEqual(self.main(self.out), 0)
        with open(os.path.join(self.out, "xp_v2_all.csv"), encoding="utf-8", newline="") as fh:
            by = {int(r["id"]): r for r in csv.DictReader(fh)}
        used = [u for pts, u in calls if pts == res["xp"]]                                   # the xp_v2 XI picker's call in section 5
        self.assertTrue(used)
        self.assertEqual(set(used[0]), {int(x) for x in mine})
        for pid, v in used[0].items():                                                       # our 15, as the picker ran
            self.assertEqual(by[pid]["xp_v2"], repr(float(v)), pid)
        self.assertEqual(used[0][ours_out], 0.0); self.assertEqual(by[ours_out]["lambda_source"], "not forecast")
        squad = CH.my_squad(CHt_newest(self.tmp))
        for p in d["all_players"]:                                                           # every export player through the picker
            pid = int(p["id"])
            if pid in {r["id"] for r in squad}:
                continue
            slot = next(i for i, r in enumerate(squad) if r["pos"] == p["pos"])
            trial = [dict(r) for r in squad]
            trial[slot] = dict(trial[slot], id=pid)
            xi, bench, gk = real(trial, res["xp"])
            got = {r["id"]: r["proj"] for r in list(xi) + list(bench) + [gk]}[pid]
            self.assertEqual(by[pid]["xp_v2"], repr(float(got)), pid)
            self.assertEqual(by[pid]["lambda_source"] == "not forecast", pid not in res["xp"], pid)

    def test_no_section_5_no_csv(self):
        shutil.rmtree(os.path.join(self.hist, "2025-26"))
        self.assertEqual(self.main(self.out), 0)
        self.assertTrue(os.path.exists(os.path.join(self.out, "gw9_pass.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.out, "xp_v2_all.csv")))


class IfHePlays(unittest.TestCase):
    """Amendment 4: for our players FPL flags, xp_v2 and own as if available, the captain table place; the rest unchanged."""

    def setUp(self):
        import gzip, json
        self.tmp, self.hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        for p in (self.tmp, self.hist):
            self.addCleanup(shutil.rmtree, p, True)
        toy_live(self.tmp); toy_hist_root(self.hist)
        gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        for p in (mock.patch.object(G.E, "selling_budget", return_value=(100.0, "")), mock.patch.object(G, "datetime", FixedNow)):
            p.start(); self.addCleanup(p.stop)
        self.path = os.path.join(self.tmp, "exports", sorted(os.listdir(os.path.join(self.tmp, "exports")))[-1])
        with gzip.open(self.path, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        mine = [r["player_id"] for r in sorted(d["squads"], key=lambda r: r["slot"]) if r["entry_id"] == d["my_entry"]]
        self.flag = next(int(p["id"]) for p in d["all_players"] if p["id"] in mine and p["pos"] == 3)
        self.plain = next(int(p["id"]) for p in d["all_players"] if p["id"] in mine and p["pos"] == 2)
        self.base = XL.live(self.tmp, self.hist, NOW9)                                       # before the flag
        self.other = next(int(p["id"]) for p in d["all_players"]
                          if p["id"] not in mine and int(p["id"]) in self.base["xp"])           # flagged too, not ours
        for p in d["all_players"]:
            if int(p["id"]) == self.flag:
                p.update(status="d", chance_next_round=75, news="Knock - 75% chance of playing")
            if int(p["id"]) == self.other:
                p.update(status="i", chance_next_round=0, news="Injured")
        with gzip.open(self.path, "wt", encoding="utf-8") as fh:
            json.dump(d, fh)

    def run_main(self, block=True):
        out = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, out, True)
        ctx = mock.patch.object(G, "if_he_plays", return_value=[]) if not block else mock.patch.object(G, "OWN_HORIZON", G.OWN_HORIZON)
        with ctx, redirect_stdout(io.StringIO()):
            self.assertEqual(G.main(["--data", self.tmp, "--hist", self.hist, "--out", out]), 0)
        return (open(os.path.join(out, "gw9_pass.txt"), "rb").read(), open(os.path.join(out, "xp_v2_all.csv"), "rb").read())

    def test_the_lift_changes_only_that_player(self):
        real = XL.XR.sub_inputs_2526

        def sub_inputs(*a, **k):                                                     # a P(sub) to scale (the toy's are 0)
            p_sub, e_sub = real(*a, **k)
            p_sub = dict(p_sub); p_sub[self.flag] = 0.4
            return p_sub, e_sub
        with mock.patch.object(XL.XR, "sub_inputs_2526", side_effect=sub_inputs):
            gated = XL.live(self.tmp, self.hist, NOW9)
            lifted = XL.live(self.tmp, self.hist, NOW9, lift=(self.flag,))
        self.assertNotIn(self.flag, gated["xp"]); self.assertIn(self.flag, lifted["xp"])
        self.assertNotIn(self.other, lifted["xp"])                                                       # only his gate is lifted
        self.assertEqual({k: v for k, v in lifted["xp"].items() if k != self.flag}, gated["xp"])        # nothing else moves
        self.assertAlmostEqual(lifted["detail"][self.flag]["p_sub"], 0.4 * 0.75, places=12)            # P(sub) scaled by chance as now
        d, _ = CH.newest_export(self.tmp)
        inp = FE.reliability_inputs(FE.canonical_through(FE.canonical_from_export(d), d["gameweek"]), gws_played=d["gameweek"])
        self.assertEqual(lifted["detail"][self.flag]["p_start"], inp["players"][self.flag]["p_start"])   # the same P(start) input

    def test_the_block(self):
        text = self.run_main()[0].decode("utf-8")
        lines = text.splitlines()
        i = lines.index(G.FLAG_HEADER)
        self.assertTrue(lines[i - 1].startswith("  ") and " slots differ; the XI " in lines[i - 1])   # the end of section 5
        self.assertTrue(lines[i + 1].startswith("    ") and 'status d, chance_next_round 75, news "Knock - 75% chance of playing"' in lines[i + 1])
        lifted = XL.live(self.tmp, self.hist, NOW9, lift=(self.flag,))
        x, det = lifted["xp"][self.flag], lifted["detail"][self.flag]
        d, _ = CH.newest_export(self.tmp)
        p = next(q for q in d["all_players"] if int(q["id"]) == self.flag)
        own, why = G.own_if_plays(d, p, 9)
        squad = CH.my_squad(d)
        sums = PM.live_pmfs(XL.live(self.tmp, self.hist, NOW9))
        one = PM.live_pmfs(dict(lifted, xp={self.flag: x}, detail={self.flag: det}))[self.flag]
        sums[self.flag] = one
        k = [q["id"] for q in sorted(squad, key=lambda q: -(sums[q["id"]]["mean"] if q["id"] in sums else -1))].index(self.flag) + 1
        self.assertEqual(lines[i + 2], f"      if he plays; the picks treat him as 0: xp_v2 {x:.2f} (P(start) {det['p_start']:.2f}, "
                                       f"P(sub) {det['p_sub']:.2f} scaled by chance); own {own:.2f}; captain table place on that number: "
                                       f"{k} of 15 (mean {one['mean']:.2f}, P>=10 {one['p10']:.3f}, P>=15 {one['p15']:.3f}, p90 {one['p90']})")
        self.assertEqual(lines[i + 3], "")                                                              # then section 6

    def test_the_rest_is_byte_identical_and_the_csv_too(self):
        with_block, csv_a = self.run_main()
        without, csv_b = self.run_main(block=False)
        lines = with_block.decode("utf-8").splitlines(keepends=True)
        i = [l.rstrip("\r\n") for l in lines].index(G.FLAG_HEADER)
        self.assertEqual("".join(lines[:i] + lines[i + 3:]).encode("utf-8"), without)
        self.assertEqual(csv_a, csv_b)

    def test_own_is_the_record_branch(self):
        d, _ = CH.newest_export(self.tmp)
        tmp_log = os.path.join(self.tmp, "own_check.csv")
        FE.record_status(d, 6, "own", path=tmp_log)
        rows = {int(r["player_id"]): float(r["predicted"]) for r in FE.read_log(tmp_log) if r["source"] == "own"}
        p = next(q for q in d["all_players"] if int(q["id"]) == self.plain)
        self.assertEqual(round(G.own_if_plays(d, p, 9)[0], 3), rows[self.plain])                      # an unflagged player: the recorded row
        self.assertNotIn(self.flag, rows)                                                                # the gate drops the flagged one

    def test_no_flagged_player_no_block(self):
        import gzip, json
        with gzip.open(self.path, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        for p in d["all_players"]:
            if int(p["id"]) == self.flag:
                p["status"] = "a"
        with gzip.open(self.path, "wt", encoding="utf-8") as fh:
            json.dump(d, fh)
        with_block, _ = self.run_main()
        without, _ = self.run_main(block=False)
        self.assertEqual(with_block, without)
        self.assertNotIn(G.FLAG_HEADER.encode("utf-8"), with_block)


class BenchBoost(unittest.TestCase):
    def rows(self):
        return [{"id": i, "pos": pos, "name": f"P{i}", "team": f"T{i}", "price": 5.0}
                for i, pos in enumerate((1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4), 1)]

    def test_by_hand(self):
        rows = self.rows()
        xp = {i: float(i) for i in range(1, 16)}
        self.assertAlmostEqual(PLV.bb_value(rows, xp), sum(range(1, 16)) + 15.0)              # all 15 + the captain (15)
        inc = {"id": 99, "pos": 2, "name": "N", "team": "TN", "price": 5.0}
        ev = {"score": 2.0, "gain": 3.0, "gains": [1.0, 2.0], "used": 1, "outs": [rows[2]], "ins": [inc], "hits": 0, "lost": 1.0}
        out = PLV.bb_rescore([ev], rows, {**xp, 99: 10.0})
        g0 = 10.0 - 3.0                                                                         # out 3, in 10; the captain stays 15
        self.assertAlmostEqual(out[0]["gains"][0], g0); self.assertAlmostEqual(out[0]["score"], 2.0 - 1.0 + g0)
        self.assertEqual(out[0]["gains"][1:], [2.0])


class Isolation(unittest.TestCase):
    def test_the_nightly_imports_nothing_here(self):
        code = ("import sys; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "print([m for m in sys.modules if m.split('.')[0] in ('planner_live', 'gw_pass', 'builder')])")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
