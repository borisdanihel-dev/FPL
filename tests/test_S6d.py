"""S6d - the live "xp_v2 as tested" forecast (tools/xp_v2_live.py, the
bundle's section 5; prereg/S6d.md). Hermetic: S6b's toy 2025/26 (S4/S5/S11
toys), S5's toy 2026/27 data folder with names, ICT and odds snapshots
added, and a toy history root (2025-26 priors, 2026-27 codes) in temporary
folders; no network, no real data."""
import csv
import gzip
import io
import json
import os
import shutil
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
import odds_lambda as OL                                          # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import gw_pass as G                                               # noqa: E402
import provenance as PV                                           # noqa: E402
from tests.test_S4 import TEAMS                                   # noqa: E402
from tests.test_S5 import toy_season, toy_2627, toy_snapshot, api_event, CLUBS   # noqa: E402
from tests.test_S11 import toy_prior                              # noqa: E402

NOW9 = datetime(2098, 12, 1, tzinfo=timezone.utc)                   # before the toy's GW9 deadline (2099-01-01 12:00)
NO_CODE = 2                                                         # a 2026/27 player without a code row


def toy_hist_root(root):
    """2025-26/: S11's toy prior with the toy 2026/27 clubs' short names and
    names 'N <id>', players_raw (code 9000 + id); 2026-27/elements_positions:
    2026/27 id -> code 9000 + id + 1 (so the code reaches 2025/26 element
    id + 1), no row for NO_CODE."""
    h = os.path.join(root, "2025-26")
    os.makedirs(h); os.makedirs(os.path.join(root, "2026-27"))
    toy_prior(h)
    with open(os.path.join(h, "teams.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("id,name,short_name\n")
        for i, (name, _) in enumerate(TEAMS, 1):
            fh.write(f"{i},{name},{CLUBS[i - 1]}\n")
    p = os.path.join(h, "merged_gw.csv")
    with open(p, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["name"] = f"N {r['element']}"
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    ids = sorted({int(r["element"]) for r in rows})
    with open(os.path.join(h, "players_raw.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("id,code,web_name\n")
        for i in ids:
            fh.write(f"{i},{9000 + i},W{i}\n")
    with open(os.path.join(root, "2026-27", "elements_positions.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write("id,code,element_type,web_name\n")
        for pid in range(1, 31):
            if pid != NO_CODE:
                fh.write(f"{pid},{9000 + pid + 1},1,W{pid}\n")
    return root


def toy_live(tmp, export_gw=8, post_deadline_export=False, status=None, chance=None, sub=None):
    """S5's toy 2026/27 folder plus first and second names in fpl.sqlite,
    ICT in the export, and the export edits: status {pid: s}, chance {pid:
    c}, sub {pid: event} (a 30-minute appearance without a start)."""
    gw8, odds = toy_2627(tmp, post_deadline_export=post_deadline_export, export_gw=export_gw)
    c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
    c.execute("alter table players add column first_name text"); c.execute("alter table players add column second_name text")
    c.execute("update players set first_name = 'N', second_name = cast(id as text)"); c.commit(); c.close()
    for f in os.listdir(os.path.join(tmp, "exports")):
        path = os.path.join(tmp, "exports", f)
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        for p in d["all_players"]:
            p["influence"], p["creativity"], p["threat"] = float(p["id"] % 7), float(p["id"] % 3), float(p["id"] % 5) / 2
            p["status"] = (status or {}).get(p["id"], p["status"])
            p["chance_next_round"] = (chance or {}).get(p["id"], p["chance_next_round"])
        for r in d["player_gw_recent"]:
            if (sub or {}).get(r["player_id"]) == r["event"]:
                r["mins"], r["starts"], r["pts"] = 30, 0, 2
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(d, fh)
    return gw8, odds


def gw9_snapshot(tmp, name, fetched_at):
    _, _, fixtures, _, _ = OL.sqlite_tables(tmp)
    gw9 = [f for f in fixtures if f["event"] == 9]
    events = [api_event(f["home"], f["away"], f["kickoff"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                        [("b1", 2.0, 3.4, 3.8, 1.9, 1.9, False)]) for f in gw9]
    toy_snapshot(tmp, name, events, fetched_at=fetched_at)


class AsTested(unittest.TestCase):
    def test_core_equals_s6b_replay(self):
        tmp, tmp24 = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            odds = toy_season(tmp, skip_fixture=13); toy_prior(tmp24)
            rp = XR.Replay(tmp, tmp24, odds)
            for t in (5, 6):
                want, wd = rp.xp_v2(t)
                c = BT.canonical_at(rp.hist, t)
                inp = E.reliability_inputs(E.canonical_through(c, t - 1), gws_played=t - 1)
                names = {pid: c["players"][pid]["name"] for pid in inp["players"]}
                got, gd = XL.core(inp, names, rp.by_round, t, rp.s11.rows, rp.s11.n2s, rp.s11.tot, rp.s11.prior,
                                  lambda team: rp.s11.club_fixtures(team, t), lambda fid, team: rp.s11.lambda_team(fid, team)[0],
                                  lambda fid, team: rp.s5.lam_opp(fid, team)[0])
                self.assertTrue(want)
                self.assertEqual(got, want)                                                  # exactly S6b's numbers
                for pid in want:
                    for k in ("p_start", "e_xg", "e_bl", "p_sub", "e_sub", "xg", "xa", "cs", "defcon", "ict"):
                        self.assertEqual(gd[pid][k], wd[pid][k], (t, pid, k))
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(tmp24, ignore_errors=True)


class Live(unittest.TestCase):
    def setUp(self):
        self.tmp, self.hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        toy_hist_root(self.hist)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True); shutil.rmtree(self.hist, ignore_errors=True)

    def test_live_point_in_time_and_the_snapshot(self):
        toy_live(self.tmp)
        res = XL.live(self.tmp, self.hist, now=NOW9)
        self.assertEqual(res["target"], 9); self.assertIsNone(res["snapshot"])
        self.assertTrue(res["xp"]); self.assertTrue(all(s == "fallback" for s in res["sources"].values()))
        gw9_snapshot(self.tmp, "odds_2099-01-01T13-00-00Z.json.gz", "2099-01-01T13:00:00Z")   # after the deadline: never used
        self.assertIsNone(XL.live(self.tmp, self.hist, now=NOW9)["snapshot"])
        gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        res2 = XL.live(self.tmp, self.hist, now=NOW9)
        self.assertEqual(res2["snapshot"][0], "odds_2098-12-31T10-00-00Z.json.gz")
        self.assertTrue(all(s == "odds" for s in res2["sources"].values()))
        self.assertNotEqual(res2["xp"], res["xp"])                                          # the odds move the lambdas
        # the clean sheet of a defender: exp(-lambda_opp) of his fixture, lambda_opp the OPPONENT's from S5 directly
        snap = OL.newest_snapshot(self.tmp, datetime(2099, 1, 1, 12, tzinfo=timezone.utc))
        book = OL.snapshot_book(snap[1])[0]
        d = res2["d"]
        club = {p["id"]: (p["team"], p["pos"]) for p in d["all_players"]}
        checked = 0
        for pid, x in res2["detail"].items():
            team, pos = club[pid]
            if pos != 2:
                continue
            f = next(f for f in d["fixtures_next6"] if f["event"] == 9 and team in (f["home"], f["away"]))
            ko = datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
            lam, src = OL.fixture_lambdas(book, None, ko, f["home"], f["away"])
            opp = lam["lambda_away"] if team == f["home"] else lam["lambda_home"]
            self.assertEqual(src, "odds")
            self.assertAlmostEqual(x["cs"], OL.p_clean_sheet(opp) * E.CS_VALUE[2])
            checked += 1
        self.assertGreater(checked, 0)
        # rows of the target gameweek never move the forecast
        path = os.path.join(self.tmp, "exports", "fpl_export_gw8_2026-10-17.json.gz")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            d = json.load(fh)
        d["player_gw_recent"] += [dict(r, event=9, pts=30, xg=3.0, xa=2.0, mins=90, starts=1, defcon=20)
                                  for r in d["player_gw_recent"] if r["event"] == 8]
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            json.dump(d, fh)
        self.assertEqual(XL.live(self.tmp, self.hist, now=NOW9)["xp"], res2["xp"])

    def test_an_export_after_the_deadline_is_refused(self):
        toy_live(self.tmp, export_gw=7, post_deadline_export=True)                          # gw7 of 10-18 12:00, after GW8's 11:00
        with self.assertRaises(XL.MissingInput):
            XL.live(self.tmp, self.hist, now=datetime(2026, 10, 18, 0, 0, tzinfo=timezone.utc))
        # retro takes GW8's newest export generated before its deadline, never the later one
        _, _, fixtures, _, _ = OL.sqlite_tables(self.tmp)
        gw8_odds = os.path.join(self.tmp, "E0_toy27_fetched_2026-10-18.csv")
        got = XL.retro(self.tmp, 8, self.hist, odds_file=gw8_odds)
        best = OL.pre_deadline_export(OL.dated_exports(self.tmp), datetime(2026, 10, 18, 11, tzinfo=timezone.utc), 8)
        self.assertTrue(best[1].endswith("fpl_export_gw7_2026-10-17.json.gz"))
        n2s = {n: s for n, s in sqlite3.connect(os.path.join(self.tmp, "fpl.sqlite")).execute("select name, short_name from teams")}
        book = OL.OddsBook(OL.load_odds(gw8_odds, n2s))
        dl = datetime(2026, 10, 18, 11, tzinfo=timezone.utc)
        model = OL.fit_fallback([(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in fixtures if f["finished"] and f["kickoff"] < dl], dl)
        names, _ = XL.prior_names(os.path.join(self.tmp, "fpl.sqlite"), os.path.join(self.hist, "2026-27", "elements_positions.csv"),
                                  os.path.join(self.hist, "2025-26"))
        want, _, srcs = XL.forecast(best[2], 8, book, model, XL.load_prior(self.hist), names)
        self.assertEqual(got, want); self.assertTrue(got)
        self.assertTrue(all(s == "odds" for s in srcs.values()))
        fn = XL.retro_fn(self.hist, gw8_odds)
        self.assertEqual(fn(self.tmp, 8), got); self.assertIn("football-data", fn.note)
        with self.assertRaises(XR.MissingInput):
            XL.retro_fn(self.hist, os.path.join(self.tmp, "none.csv"))(self.tmp, 8)        # S6c's print catches it as its own

    def test_the_prior_key_by_code_then_name(self):
        toy_live(self.tmp)
        names, by_code = XL.prior_names(os.path.join(self.tmp, "fpl.sqlite"),
                                        os.path.join(self.hist, "2026-27", "elements_positions.csv"),
                                        os.path.join(self.hist, "2025-26"))
        self.assertEqual(names[1], "N 2")                                                   # by code: 2026/27 id 1 -> 2025/26 element 2
        self.assertEqual(names[NO_CODE], f"N {NO_CODE}")                                    # no code row: the 2026/27 first + second name
        self.assertEqual(by_code, 29)
        res = XL.live(self.tmp, self.hist, now=NOW9)
        prior = XL.load_prior(self.hist)
        # player 1 (ARS) reaches his own 2025/26 share at ARS through code; 'N 1' would not be him
        for pid in (1, NO_CODE):
            if pid in res["detail"]:
                self.assertEqual(res["detail"][pid]["prior"], "own 2024/25 at the club")
                self.assertIn((names[pid], "ARS"), prior.by_name_club)
        self.assertIn(1, res["detail"])
        # a player whose name has no row at his club takes S11's club-position mean
        club = {p["id"]: p["team"] for p in res["d"]["all_players"]}
        far = [pid for pid in res["detail"] if (names[pid], club[pid]) not in prior.by_name_club]
        self.assertTrue(far)
        self.assertTrue(all(res["detail"][pid]["prior"] in ("club-position mean", "league-position mean (club without 2024/25 rows)") for pid in far))
        self.assertEqual(XL.prior_label("own 2024/25 at the club"), "own 2025/26 at the club")
        os.remove(os.path.join(self.hist, "2026-27", "elements_positions.csv"))
        with self.assertRaises(XL.MissingInput):
            XL.live(self.tmp, self.hist, now=NOW9)

    def test_gate_and_the_sub_term_with_chance(self):
        toy_live(self.tmp, status={3: "d"}, chance={4: 50}, sub={4: 8})
        res = XL.live(self.tmp, self.hist, now=NOW9)
        self.assertNotIn(3, res["xp"])                                                      # status d: no xp_v2
        x = res["detail"][4]
        d = res["d"]
        c = E.canonical_through(E.canonical_from_export(d), 8)
        inp = E.reliability_inputs(c, gws_played=8)
        by_round, _ = XL.export_rows(d)
        p_sub, e_sub = XR.sub_inputs_2526(by_round, 9, {pid: p["pos"] for pid, p in inp["players"].items()})
        self.assertAlmostEqual(p_sub[4], 0.25)                                              # one sub appearance in the last four
        self.assertAlmostEqual(x["p_sub"], 0.25 * 0.5)                                      # times chance 50%
        self.assertEqual(x["p_start"], inp["players"][4]["p_start"])                        # the current minutes model, chance included
        self.assertAlmostEqual(res["xp"][4], x["p_start"] * (x["e_xg"] + x["e_bl"]) / 2 + x["p_sub"] * x["e_sub"])
        for pid, p in inp["players"].items():
            if p["mins_last4"] < 45:
                self.assertNotIn(pid, res["xp"])
        ict = XL.ict_live(d)
        tot = {p["id"]: p["influence"] + p["creativity"] + p["threat"] for p in d["all_players"] if p["minutes"] > 0}
        order = sorted(tot, key=lambda k: (tot[k], k))
        self.assertEqual(ict, {pid: i / (len(order) - 1) for i, pid in enumerate(order)})     # season I + C + T, players with minutes


class Bundle(unittest.TestCase):
    def test_section_five_and_the_keeper_line(self):
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_live(tmp); toy_hist_root(hist)
            gw9_snapshot(tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
            buf = io.StringIO()
            G.bundle(tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=hist)
            text = buf.getvalue()
            self.assertIn("OWN v XP_V2 AS TESTED: XI, BENCH AND CAPTAIN", text)
            self.assertIn("from GW8 xp_v2 as tested picks the XI and captain (RULING S6b acceptance point 1)", text)
            self.assertIn("captain: own", text); self.assertIn("|  xp_v2 as tested", text)
            self.assertIn("DEFAULT = xp_v2 as tested", text)
            self.assertIn("odds_2098-12-31T10-00-00Z.json.gz", text)
            sec5 = text.split("OWN v XP_V2 AS TESTED")[1].split("KEEPER LINE")[0]
            self.assertNotIn("own picks", sec5)
            slots = [ln.split()[0] for ln in sec5.splitlines() if ln.strip() and ln.split()[0].isdigit() and "slots differ" not in ln]
            self.assertEqual(slots, [str(i) for i in range(1, 16)])                                 # the XI, then the bench
            res = XL.live(tmp, hist, now=NOW9)
            cv = G.side_by_side(G.CH.my_squad(res["d"]), {}, res["xp"])["captain"][1]
            self.assertIn(f"|  xp_v2 as tested {cv['name']} ({cv['proj']:.2f})", sec5)            # the captain by xp_v2 as tested
            keepers = [r for r in G.CH.my_squad(res["d"]) if r["pos"] == 1]
            sec6 = text.split("KEEPER LINE")[1]
            for r in keepers:
                v = res["xp"].get(r["id"])
                self.assertIn(f"xp_v2 {'n/a' if v is None else f'{v:.2f}':>5}", sec6)
            # no priors: missing input, and own picks; nothing substituted
            shutil.rmtree(os.path.join(hist, "2025-26"))
            buf = io.StringIO()
            G.bundle(tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=hist)
            sec5 = buf.getvalue().split("OWN v XP_V2 AS TESTED")[1].split("KEEPER LINE")[0]
            self.assertIn("missing input:", sec5); self.assertIn("own picks GW9 (RULING S6b acceptance point 1", sec5)
            self.assertNotIn("captain:", sec5)
            self.assertIn("xp_v2   n/a", buf.getvalue().split("KEEPER LINE")[1])
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)


class CLI(unittest.TestCase):
    def test_cli_run_txt_and_isolation(self):
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_live(tmp); toy_hist_root(hist)
            out = os.path.join(tmp, "out")
            with redirect_stdout(io.StringIO()):
                rc = XL.main(["--data", tmp, "--hist", hist, "--out", out])
            self.assertEqual(rc, 0)                                                         # the real clock: the toy's next deadline is GW9 (2099)
            with open(os.path.join(out, "xp_v2_live_gw9.txt"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("XP_V2 AS TESTED  GW9", text); self.assertIn("priors 2025/26 (S11)", text)
            rec = PV.read_run(out)
            self.assertEqual(rec["tool"], "tools/xp_v2_live.py"); self.assertIn("xp_v2_live_gw9.txt", rec["outputs"])
            shutil.rmtree(os.path.join(hist, "2025-26"))
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(XL.main(["--data", tmp, "--hist", hist, "--out", out]), 2)
            self.assertIn("own picks GW8 (ruling point 1)", buf.getvalue())
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)
        code = ("import sys, os; import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate, fpl_publish; "
                "bad = [m for m, mod in sys.modules.items() if (getattr(mod, '__file__', None) or '')"
                ".replace(os.sep, '/').find('/tools/') >= 0 or m.split('.')[0] in ('tools', 'analysis', 'xp_v2_live')]; print(bad)")
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[]", r.stderr)


if __name__ == "__main__":
    unittest.main()
