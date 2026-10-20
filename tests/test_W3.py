"""W3 - xp_v2 as tested recorded nightly, and the CAPTAIN, BAN RISK and
REALISED report sections (prereg/W3.md, Part F item F-B). Hermetic: S6d's
toy 2026/27 data folder and toy history root, toy databases and logs, all in
temporary folders; the real-data checks run only with FPL_DATA_DIR set and
historical/2025-26 present."""
import ast
import csv
import gzip
import io
import json
import math
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fpl_edge as E                                              # noqa: E402
import checks as C                                                # noqa: E402
import fpl_gate                                                   # noqa: E402
import fpl_sync                                                   # noqa: E402
import fpl_chips                                                  # noqa: E402
import fpl_mv2                                                    # noqa: E402
import fpl_realised                                               # noqa: E402
import fpl_sections as FS                                         # noqa: E402
import fpl_shares                                                 # noqa: E402
import fpl_squad as SQ                                            # noqa: E402
import fpl_xpv2                                                   # noqa: E402
import chips as CHt                                               # noqa: E402
import gw_pass as G                                               # noqa: E402
import make_prior as MP                                           # noqa: E402
import minutes_v2 as MVt                                          # noqa: E402
import points_pmf as PMt                                          # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2_live as XL                                           # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
from tests.test_S6d import toy_live, toy_hist_root, gw9_snapshot, NOW9   # noqa: E402

DL9 = datetime(2099, 1, 1, 12, tzinfo=timezone.utc)                 # the toy's GW9 deadline (fpl.sqlite events)
COPIES = {"fpl_xpv2": "xp_v2_live", "fpl_xpr": "xp_v2_replay", "fpl_shares": "shares", "fpl_xpv": "xp_v2",
          "fpl_pmf": "points_pmf", "fpl_mv2": "minutes_v2", "fpl_realised": "xp_v2_replay"}
HAND = {"fpl_xpv2": {"PRIOR_FILE", "load_prior_file", "export_names", "live_forecast", "record"}, "fpl_shares": {"Prior"}}
RECORD_MODULES = ("fpl_xpv2", "fpl_xpr", "fpl_shares", "fpl_xpv", "fpl_lambda", "fpl_hist")


def runner_export(tmp, hist):
    """The toy export as W3's sync writes it: each player's code (the toy
    code file the tool reads), first and second names (fpl.sqlite players),
    the events' deadlines and the finished fixtures as fixtures_played
    (fpl.sqlite events and fixtures, as the real export carries them);
    written back in place."""
    with open(os.path.join(hist, "2026-27", "elements_positions.csv"), encoding="utf-8", newline="") as fh:
        code = {int(r["id"]): int(r["code"]) for r in csv.DictReader(fh)}
    c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
    names = {pid: (fn, sn) for pid, fn, sn in c.execute("select id, first_name, second_name from players")}
    events = [{"event": ev, "deadline_time": dl} for ev, dl in c.execute("select id, deadline_time from events")]
    short = dict(c.execute("select id, short_name from teams"))
    played = [{"event": ev, "home": short[h], "away": short[a], "h_goals": hg, "a_goals": ag, "kickoff_time": ko}
              for ev, ko, h, a, hg, ag in c.execute("select event, kickoff_time, team_h, team_a, team_h_score, team_a_score "
                                                    "from fixtures where finished = 1 order by kickoff_time, id")]
    c.close()
    path = os.path.join(tmp, "exports", sorted(os.listdir(os.path.join(tmp, "exports")))[-1])
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        d = json.load(fh)
    for p in d["all_players"]:
        p["code"] = code.get(p["id"])
        p["first_name"], p["second_name"] = names[p["id"]]
    d["events"], d["fixtures_played"] = events, played
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(d, fh)
    return d


def prior_file(hist, folder):
    path = os.path.join(folder, "s11_prior_2025-26.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(MP.render(MP.state_of(os.path.join(hist, "2025-26"))))
    return path


def toy_world(test):
    test.tmp, test.hist, test.side = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
    toy_live(test.tmp); toy_hist_root(test.hist)
    test.d = runner_export(test.tmp, test.hist)
    test.prior = prior_file(test.hist, test.side)


def drop_world(test):
    for p in (test.tmp, test.hist, test.side):
        shutil.rmtree(p, ignore_errors=True)


def segments(path):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    out = {}
    for n in ast.parse(src).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            out[n.name] = ast.get_source_segment(src, n)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for x in ([t] if isinstance(t, ast.Name) else getattr(t, "elts", [])):
                    if isinstance(x, ast.Name):
                        out[x.id] = ast.get_source_segment(src, n)
    return out, src


class Copies(unittest.TestCase):
    """(1) the port: every copied definition is the tools' text; the record's
    modules import neither tools/ nor the database."""

    def test_every_copied_definition_is_the_tools_text(self):
        for mod, tool in COPIES.items():
            mine, _ = segments(os.path.join(ROOT, mod + ".py"))
            theirs, _ = segments(os.path.join(ROOT, "tools", tool + ".py"))
            copied = [n for n in mine if n not in HAND.get(mod, set())]
            self.assertTrue(copied, mod)
            for name in copied:
                self.assertIn(name, theirs, f"{mod}.{name} is not in tools/{tool}.py")
                self.assertEqual(mine[name], theirs[name], f"{mod}.{name} differs from tools/{tool}.py")
        with open(os.path.join(ROOT, "fpl_shares.py"), encoding="utf-8") as fh:
            src = fh.read()
        with open(os.path.join(ROOT, "tools", "shares.py"), encoding="utf-8") as fh:
            tsrc = fh.read()

        def method(text, cls):
            node = next(n for n in ast.parse(text).body if isinstance(n, ast.ClassDef) and n.name == cls)
            return ast.get_source_segment(text, next(m for m in node.body if isinstance(m, ast.FunctionDef) and m.name == "prior"))
        self.assertEqual(method(src, "Prior"), method(tsrc, "Prior"))                  # S11's prior(), verbatim

    def test_the_record_imports_neither_tools_nor_the_database(self):
        tools = {f[:-3] for f in os.listdir(os.path.join(ROOT, "tools")) if f.endswith(".py")} | {"tools"}
        for mod in RECORD_MODULES:
            with open(os.path.join(ROOT, mod + ".py"), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
            self.assertNotIn("sqlite3", names, mod)
            self.assertFalse(names & tools, f"{mod} imports {names & tools}")
            self.assertTrue(names <= set(sys.stdlib_module_names) | set(RECORD_MODULES) | {"fpl_edge"}, f"{mod}: {names}")


class SyncExport(unittest.TestCase):
    """(1) the export carries each player's code and names (the prior's key)."""

    def test_all_players_carry_code_and_names(self):
        from contextlib import redirect_stdout
        import fpl_sync as S
        db = sqlite3.connect(":memory:")
        db.executescript(S.SCHEMA)
        with redirect_stdout(io.StringIO()):
            S.migrate(db)
        db.execute("INSERT INTO teams (id, name, short_name) VALUES (1, 'Arsenal', 'ARS')")
        db.executemany("INSERT INTO players (id, web_name, first_name, second_name, team_id, position, code) VALUES (?,?,?,?,?,?,?)",
                       [(1, "Saka", "Bukayo", "Saka", 1, 3, 223340), (2, "New", "A", "New", 1, 2, None)])
        db.commit()
        cwd, tmp = os.getcwd(), tempfile.mkdtemp()
        try:
            os.chdir(tmp)                                                                 # the export writes its file here
            with redirect_stdout(io.StringIO()):
                S.export(db, 7)
            with open(os.path.join(tmp, "fpl_export_gw7.json"), encoding="utf-8") as fh:
                d = json.load(fh)
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)
        got = {p["id"]: (p["code"], p["first_name"], p["second_name"]) for p in d["all_players"]}
        self.assertEqual(got, {1: (223340, "Bukayo", "Saka"), 2: (None, "A", "New")})
        names, by_code = fpl_xpv2.export_names(d, {"223340": "Bukayo Saka (2025/26)"})
        self.assertEqual((names, by_code), ({1: "Bukayo Saka (2025/26)", 2: "A New"}, 1))


class PriorFile(unittest.TestCase):
    """(1b) the committed S11 state answers every query as shares.Prior on
    the files, and regenerates byte for byte."""

    def setUp(self):
        self.hist = tempfile.mkdtemp()
        toy_hist_root(self.hist)
        self.folder = os.path.join(self.hist, "2025-26")
        p = os.path.join(self.folder, "merged_gw.csv")
        with open(p, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        few = dict(rows[0], element="777", name="Few Minutes", minutes="30", expected_goals="0.4", expected_assists="0.1")
        with open(p, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows + [few])

    def tearDown(self):
        shutil.rmtree(self.hist, ignore_errors=True)

    def test_the_file_answers_as_shares_prior(self):
        text = MP.render(MP.state_of(self.folder))
        self.assertEqual(text, MP.render(MP.state_of(self.folder)))                     # deterministic
        path = os.path.join(self.hist, "p.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        mine, theirs = fpl_shares.Prior(fpl_xpv2.load_prior_file(path)), SH.Prior(self.folder)
        self.assertEqual(mine.k, theirs.k); self.assertEqual(mine.by_name_club, theirs.by_name_club)
        self.assertEqual(list(mine.by_name_club), list(theirs.by_name_club))         # S11's order
        self.assertEqual(dict(mine.club_pos), dict(theirs.club_pos)); self.assertEqual(dict(mine.league_pos), dict(theirs.league_pos))
        names = {n for n, _ in theirs.by_name_club} | {"Nobody At All"}
        clubs = theirs.clubs | {"ZZZ"}
        asked = 0
        for name in names:
            for club in clubs:
                for pos in (1, 2, 3, 4):
                    for metric in ("xg", "xa"):
                        try:
                            want = theirs.prior(name, pos, club, metric)
                        except SH.MissingInput:
                            with self.assertRaises(fpl_shares.MissingInput):
                                mine.prior(name, pos, club, metric)
                            continue
                        self.assertEqual(mine.prior(name, pos, club, metric), want)
                        asked += 1
        self.assertGreater(asked, 100)
        few = next(a for (n, _), a in mine.by_name_club.items() if n == "Few Minutes")
        self.assertLess(few["minutes"], fpl_shares.PRIOR_MINS)                          # in the sums, never in the position lists
        self.assertNotIn((fpl_shares.share_of(few, "xg"), fpl_shares.share_of(few, "xa")),
                         [pair for v in mine.club_pos.values() for pair in v])
        state = json.loads(text)
        self.assertEqual(set(state["inputs"]), set(MP.INPUTS))
        self.assertEqual(len(state["inputs"]["merged_gw.csv"]), 64)

    def test_a_missing_or_wrong_file_is_refused(self):
        with self.assertRaises(OSError):
            fpl_xpv2.load_prior_file(os.path.join(self.hist, "none.json"))
        state = MP.state_of(self.folder)
        for edit, err in ((lambda s: s.pop("code_name"), KeyError), (lambda s: s.update(season="2024-25"), ValueError)):
            s = json.loads(MP.render(state)); edit(s)
            path = os.path.join(self.hist, "bad.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(s, fh)
            with self.assertRaises(err):
                fpl_xpv2.load_prior_file(path)

    @unittest.skipUnless(os.environ.get("FPL_DATA_DIR") and os.path.isdir(os.path.join(ROOT, "historical", "2025-26")),
                         "the real 2025/26 files: FPL_DATA_DIR and historical/2025-26")
    def test_the_committed_file_regenerates_from_the_real_files(self):
        self.assertEqual(MP.main(["--hist", os.path.join(ROOT, "historical"), "--check"]), 0)


class Forecast(unittest.TestCase):
    """(1a, 1c) the runner's forecast and record against tools/xp_v2_live.py
    on the same inputs."""

    def setUp(self):
        toy_world(self)

    def tearDown(self):
        drop_world(self)

    def runner(self):
        return fpl_xpv2.live_forecast(self.d, 9, DL9, self.tmp, fpl_xpv2.load_prior_file(self.prior))

    def test_identical_to_the_tool_without_and_with_a_snapshot(self):
        for snap in (None, "before", "after"):
            if snap == "before":
                gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
            if snap == "after":
                gw9_snapshot(self.tmp, "odds_2099-01-01T13-00-00Z.json.gz", "2099-01-01T13:00:00Z")   # never used
            want, got = XL.live(self.tmp, self.hist, now=NOW9), self.runner()
            self.assertTrue(want["xp"])
            for key in ("xp", "detail", "sources", "snapshot", "by_code"):
                self.assertEqual(got[key], want[key], (snap, key))
        self.assertEqual(got["snapshot"][0], "odds_2098-12-31T10-00-00Z.json.gz")
        self.assertTrue(all(s == "odds" for s in got["sources"].values()))

    def test_the_key_by_code_then_name(self):
        names, by_code = fpl_xpv2.export_names(self.d, fpl_xpv2.load_prior_file(self.prior)["code_name"])
        want, want_by = XL.prior_names(os.path.join(self.tmp, "fpl.sqlite"), os.path.join(self.hist, "2026-27", "elements_positions.csv"),
                                       os.path.join(self.hist, "2025-26"))
        self.assertEqual(names, want); self.assertEqual(by_code, want_by)
        self.assertEqual(names[2], "N 2")                                                # no code row: the 2026/27 name
        self.assertEqual(names[3], "N 4")                                                # code 9004 reaches 2025/26 element 4
        d = json.loads(json.dumps(self.d))
        del d["all_players"][0]["code"]
        with self.assertRaises(fpl_xpv2.MissingInput):
            fpl_xpv2.export_names(d, {})

    def test_target_rows_never_move_the_forecast(self):
        before = self.runner()["xp"]
        self.d["player_gw_recent"] += [dict(r, event=9, pts=30, xg=3.0, xa=2.0, mins=90, starts=1, defcon=20)
                                       for r in self.d["player_gw_recent"] if r["event"] == 8]
        self.assertEqual(self.runner()["xp"], before)

    def test_the_record_rows_and_skips_without_a_database(self):
        gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
        gw9_snapshot(self.tmp, "odds_2099-01-01T13-00-00Z.json.gz", "2099-01-01T13:00:00Z")   # after the deadline: never used
        want = XL.live(self.tmp, self.hist, now=NOW9)["xp"]
        data = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(self.tmp, "odds"), os.path.join(data, "odds"))   # no fpl.sqlite here
            log = os.path.join(data, "projection_log.csv")
            with mock.patch.object(fpl_xpv2, "PRIOR_FILE", self.prior):
                ok, n, why = E.record_status(self.d, 6, source="xp_v2", path=log)
            self.assertTrue(ok); self.assertIn("snapshot odds_2098-12-31T10-00-00Z.json.gz", why)
            rows = [r for r in E.read_log(log) if r["source"] == "xp_v2"]
            self.assertEqual(n, len(rows))
            self.assertEqual(sorted((int(r["player_id"]), float(r["predicted"])) for r in rows),
                             sorted((pid, round(v, 3)) for pid, v in want.items() if v > 0))
            self.assertEqual({r["event"] for r in rows}, {"9"})
            self.assertEqual([f for f in os.listdir(data) if "sqlite" in f], [])
            with mock.patch.object(fpl_xpv2, "PRIOR_FILE", os.path.join(data, "none.json")):
                ok, n, why = E.record_status(self.d, 6, source="xp_v2", path=log)
            self.assertEqual((ok, n), (E.RECORD_SKIP, 0)); self.assertIn("missing or unreadable", why)
            d = json.loads(json.dumps(self.d))
            for p in d["all_players"]:
                del p["code"]
            with mock.patch.object(fpl_xpv2, "PRIOR_FILE", self.prior):
                ok, n, why = E.record_status(d, 6, source="xp_v2", path=log)
            self.assertEqual((ok, n), (E.RECORD_SKIP, 0)); self.assertIn("has no code", why)
        finally:
            shutil.rmtree(data, ignore_errors=True)

    def test_the_nightly_and_check_29_know_the_seventh_source(self):
        import fpl_nightly as N
        self.assertEqual(N.SOURCES[-1], "xp_v2"); self.assertEqual(C.SOURCES, N.SOURCES); self.assertIn("xp_v2", C.SKIPPABLE)
        nl = chr(10)
        base = "record summary:" + nl + "".join(f"RECORD OK {s} 5" + nl for s in C.SOURCES[:-1])
        self.assertEqual(C.c29(C.Ctx(run_log=base + "RECORD OK xp_v2 5" + nl))[0], C.OK)
        self.assertEqual(C.c29(C.Ctx(run_log=base + "RECORD SKIP xp_v2 no prior" + nl)),
                         (C.WARN, "xp_v2 skipped: no prior; the other 6 recorded"))
        self.assertEqual(C.c29(C.Ctx(run_log=base + "RECORD FAIL xp_v2 boom" + nl))[0], C.FAIL)
        self.assertEqual(C.c29(C.Ctx(run_log=base)), (C.FAIL, "xp_v2 missing"))


class Captain(unittest.TestCase):
    """(2) CAPTAIN: the lines of tools/gw_pass.py's section 7 on the same inputs."""

    def setUp(self):
        toy_world(self)
        gw9_snapshot(self.tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")

    def tearDown(self):
        drop_world(self)

    def test_the_lines_are_gw_pass_section_seven(self):
        res = XL.live(self.tmp, self.hist, now=NOW9)
        sums = PMt.live_pmfs(res)
        squad = CHt.my_squad(res["d"])
        want = []
        PMt.captain_table(squad, sums, want.append)
        cap, options = G.captain_band(G.side_by_side(squad, {}, res["xp"]), sums)
        PMt.print_options(cap, options, sums, {r["id"]: r["name"] for r in squad}, want.append)
        got = []
        out = SQ.captain(self.tmp, got.append, prior_path=self.prior)
        self.assertEqual(got[1:], want)
        self.assertTrue(got[0].startswith("  GW9 from fpl_export_gw8_2026-10-17.json.gz: the points distribution of xp_v2"))
        self.assertIn("odds_2098-12-31T10-00-00Z.json.gz", got[0])
        self.assertEqual((out["captain"], out["options"]), (cap, options))
        xi = [b["id"] for _, _, b in G.side_by_side(squad, {}, res["xp"])["rows"][:11]]
        self.assertEqual(out["captain"], max(xi, key=lambda pid: (res["xp"].get(pid, 0.0), -pid)))   # the highest xp_v2 in the XI
        xp = {r["id"]: 1.0 for r in squad}
        a, b = sorted(r["id"] for r in squad if r["pos"] == 3)[:2]
        xp[a] = xp[b] = 9.0                                                               # a tie at the top
        xi2, cap2 = SQ.xp_v2_captain(squad, xp)
        self.assertEqual(cap2["id"], a)                                                   # ties to the lower id, as gw_pass
        self.assertEqual(cap2["id"], G.side_by_side(squad, {}, xp)["captain"][1]["id"])


def rows_with(club_matches, cautions, minutes=90):
    """S12 Rows for one club: `club_matches` known league matches before the
    cut, player 1 booked `cautions` times in the first of them."""
    t0 = datetime(2026, 8, 1, tzinfo=timezone.utc)
    matches = {"AAA": [(t0 + timedelta(days=7 * i), str(i), i + 1) for i in range(club_matches + 1)]}
    played = {(1, str(i)): (minutes, 1, cautions if i == 0 else 0) for i in range(club_matches)}
    return fpl_mv2.Rows(matches, played, {1: "AAA"}, {1: 3}), t0 + timedelta(days=7 * club_matches - 1)


class BanRisk(unittest.TestCase):
    """(2) BAN RISK: S12's band one match on, the booking rate shrunk to the
    pooled position rate, P(ban) = min(1, rate90 x P(start))."""

    def test_the_bands(self):
        for matches, cautions, want in ((17, 4, (4, 18)), (18, 4, None), (5, 3, None), (5, 5, None),
                                        (30, 9, (9, 31)), (31, 9, None), (19, 4, None)):
            rows, cut = rows_with(matches, cautions)
            got = SQ.one_from_ban(rows, 1, "AAA", cut)
            self.assertEqual(None if got is None else got[:2], want, (matches, cautions))

    def test_the_section_by_hand(self):
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_live(tmp); toy_hist_root(hist)
            d = runner_export(tmp, hist)
            squad = fpl_chips.my_squad(d)
            out = []
            self.assertEqual(SQ.ban_risk(tmp, out.append), 0)
            self.assertEqual(out[-1], "  none of our 15 is one booking from a ban")
            ours, other = squad[5]["id"], 30 if 30 not in {r["id"] for r in squad} else None
            path = os.path.join(tmp, "exports", sorted(os.listdir(os.path.join(tmp, "exports")))[-1])
            for r in d["player_gw_recent"]:
                if r["player_id"] == ours and r["event"] in (7, 8):
                    r["starts"] = 0                                                       # on the bench twice: P(start) < 1
            with gzip.open(path, "wt", encoding="utf-8") as fh:
                json.dump(d, fh)
            c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
            for pid in (ours, other):
                if pid is None:
                    continue
                evs = [e for (e,) in c.execute("select event from player_gw where player_id = ? and minutes > 0 order by event", (pid,))]
                for e in evs[:4]:
                    c.execute("update player_gw set yellow = 1 where player_id = ? and event = ?", (pid, e))
            c.commit()
            rows = fpl_mv2.rows_2627(tmp, d)
            keys = fpl_mv2.rows_key_before(rows, DL9)
            pos = rows.pos[ours]
            ys = sum(y for (p, k), (m, _, y) in rows.played.items() if k in keys and rows.pos.get(p) == pos)
            ms = sum(m for (p, k), (m, _, y) in rows.played.items() if k in keys and rows.pos.get(p) == pos)
            mean = ys / (ms / 90.0)
            own_m = sum(m for (p, k), (m, _, y) in rows.played.items() if p == ours and k in keys) / 90.0
            rate = own_m / (own_m + 4.0) * (4 / own_m) + 4.0 / (own_m + 4.0) * mean
            inp = E.reliability_inputs(E.canonical_through(E.canonical_from_export(d), d["gameweek"]), gws_played=d["gameweek"])
            ps = inp["players"][ours]["p_start"]
            self.assertLess(ps, 1.0)
            c.close()
            out = []
            self.assertEqual(SQ.ban_risk(tmp, out.append), 1)                            # ours only, never another club's player
            line = out[-1]
            self.assertIn(f"cautions 4, club match {len(rows.club_matches_before(rows.club_of[ours], DL9)) + 1} next", line)
            self.assertIn(f"rate90 {rate:.3f}", line); self.assertIn(f"P(start) {ps:.2f}", line)
            self.assertIn(f"P(ban) {min(1.0, rate * ps):.3f}", line)
            self.assertAlmostEqual(SQ.position_rates(rows, DL9)[pos], mean)
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)


def toy_realised(tmp, entry=77):
    """fpl.sqlite with GW7 (before GW8: never shown), GW8 locked down, GW9
    past its deadline with a fixture unfinished, GW10 in the future; our 15
    picks for GW7-9; points and minutes; a log with own and xp_v2 rows."""
    c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
    c.executescript("""
      create table events(id integer, deadline_time text, finished integer, data_checked integer);
      create table fixtures(id integer, event integer, finished integer);
      create table players(id integer, position integer, web_name text);
      create table picks(entry_id integer, event integer, player_id integer, position integer);
      create table player_gw(player_id integer, event integer, total_points integer, minutes integer);
    """)
    c.executemany("insert into events values (?,?,?,?)", [(7, "2026-10-17T10:00:00Z", 1, 1), (8, "2026-10-23T17:30:00Z", 1, 1),
                                                           (9, "2026-10-31T11:00:00Z", 0, 0), (10, "2099-01-01T11:00:00Z", 0, 0)])
    c.executemany("insert into fixtures values (?,?,?)", [(1, 7, 1), (2, 8, 1), (3, 8, 1), (4, 9, 1), (5, 9, 0)])
    pos = [1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4]
    c.executemany("insert into players values (?,?,?)", [(i, p, f"P{i}") for i, p in enumerate(pos, 1)] + [(99, 3, "Other")])
    for ev in (7, 8, 9):
        c.executemany("insert into picks values (?,?,?,?)", [(entry, ev, i, i) for i in range(1, 16)])
    pts = {i: (i % 7) + 1 for i in range(1, 16)}
    c.executemany("insert into player_gw values (?,?,?,?)",
                  [(i, 8, pts[i], 0 if i == 8 else 90) for i in range(1, 16)] + [(99, 8, 20, 90)])
    c.commit(); c.close()
    made, late = "2026-10-22T21:45:00+00:00", "2026-10-23T18:00:00+00:00"
    rows = []
    for i in range(1, 16):
        rows.append({"made_at": made, "source": "own", "event": "8", "player_id": str(i), "web_name": f"P{i}", "predicted": str(float(i))})
        rows.append({"made_at": made, "source": "xp_v2", "event": "8", "player_id": str(i), "web_name": f"P{i}",
                     "predicted": str(float(16 - i))})
        rows.append({"made_at": late, "source": "xp_v2", "event": "8", "player_id": str(i), "web_name": f"P{i}",
                     "predicted": str(float(i * 3))})                                    # after the deadline: never read
        rows.append({"made_at": made, "source": "own", "event": "9", "player_id": str(i), "web_name": f"P{i}", "predicted": "1.0"})
    with open(os.path.join(tmp, E.LOG_PATH), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return entry


class Realised(unittest.TestCase):
    """(3) REALISED: S6c's info_2627 numbers, from the recorded pre-deadline
    rows of both sources, under the lockdown guard, from GW8."""

    def test_equals_info_2627_and_the_guard(self):
        tmp = tempfile.mkdtemp()
        try:
            entry = toy_realised(tmp)
            now = datetime(2026, 11, 1, tzinfo=timezone.utc)
            out = []
            recs = SQ.realised(tmp, out.append, now=now, entry=entry, repo=tmp)
            self.assertEqual([r["gw"] for r in recs], [8, 9])                           # GW7 is before GW8; GW10 not yet
            g8 = recs[0]
            log_rows = E.read_log(os.path.join(tmp, E.LOG_PATH))
            d_ev = {"events": [{"event": 8, "deadline_time": "2026-10-23T17:30:00Z"}]}
            v2, _ = SQ.recorded(log_rows, "xp_v2", 8, d_ev)
            self.assertEqual(v2[1], 15.0)                                                 # the pre-deadline row, not the late one
            tool = XR.info_2627(tmp, out=lambda s: None, gws=(8,), entry=entry, xp_v2_fn=lambda data_dir, g: v2)[0]
            for key in ("own", "own_cap", "v2", "v2_cap"):
                self.assertEqual(g8["xp_v2" if key == "v2" else "xp_v2_cap" if key == "v2_cap" else key], tool[key], key)
            self.assertEqual(SQ.recorded(log_rows, "own", 8, d_ev), XR.recorded_own(log_rows, 8, d_ev))
            self.assertIn("GW8: own", out[1]); self.assertIn(f"xp_v2 - own {g8['xp_v2'] - g8['own']:+.0f}", out[1])
            self.assertEqual(out[2], "  GW9: not locked down: not graded (data_checked 0, 1 of 2 fixtures finished)")
            self.assertTrue(out[-1].startswith("  total over 1 gameweek with both: own"))
            out = []
            SQ.realised(tmp, out.append, now=datetime(2026, 10, 23, tzinfo=timezone.utc), entry=entry, repo=tmp)
            self.assertEqual(out[-1], "  no gameweek from GW8 has passed its deadline yet")
            c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
            c.execute("update events set data_checked = 0 where id = 8"); c.commit(); c.close()
            out = []
            self.assertFalse(SQ.realised(tmp, out.append, now=now, entry=entry, repo=tmp)[0]["graded"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_source_without_rows_is_not_recorded(self):
        tmp = tempfile.mkdtemp()
        try:
            entry = toy_realised(tmp)
            rows = [r for r in E.read_log(os.path.join(tmp, E.LOG_PATH)) if r["source"] != "xp_v2"]
            with open(os.path.join(tmp, E.LOG_PATH), "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
            git_repo(tmp)                                                                  # a repository without the bundle
            out = []
            SQ.realised(tmp, out.append, now=datetime(2026, 11, 1, tzinfo=timezone.utc), entry=entry, repo=tmp)
            self.assertIn("xp_v2: not recorded before the deadline", out[1])
            self.assertFalse(any(l.startswith("  total") for l in out))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


OLD_FIXTURES = """CREATE TABLE fixtures (
    id INTEGER PRIMARY KEY, event INTEGER, kickoff_time TEXT,
    team_h INTEGER, team_a INTEGER, team_h_difficulty INTEGER,
    team_a_difficulty INTEGER, team_h_score INTEGER, team_a_score INTEGER,
    finished INTEGER, started INTEGER, fetched_at_utc TEXT)"""


class FinishedProvisional(unittest.TestCase):
    """Amendment 1 (A): fixtures.finished_provisional, appended last; old rows NULL; the dump's positions kept."""

    def test_the_migration_appends_it_last(self):
        tmp = tempfile.mkdtemp()
        try:
            old = sqlite3.connect(os.path.join(tmp, "old.sqlite"))
            old.execute(OLD_FIXTURES)
            row = (1, 7, "2026-10-04T14:00:00Z", 1, 2, 3, 4, 2, 1, 1, 1, "2026-10-05T21:40:00+00:00")
            old.execute("INSERT INTO fixtures VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", row)
            old.executescript(fpl_sync.SCHEMA)
            fpl_sync.migrate(old)
            cols = [r[1] for r in old.execute("PRAGMA table_info(fixtures)")]
            self.assertEqual(cols[-1], "finished_provisional"); self.assertEqual(len(cols), 13)
            self.assertEqual(old.execute("SELECT * FROM fixtures").fetchone(), row + (None,))   # the stored row keeps NULL
            new = sqlite3.connect(os.path.join(tmp, "new.sqlite"))
            new.executescript(fpl_sync.SCHEMA)
            fpl_sync.migrate(new)
            self.assertEqual([r[1:3] for r in new.execute("PRAGMA table_info(fixtures)")],
                             [r[1:3] for r in old.execute("PRAGMA table_info(fixtures)")])      # a fresh database, the same order
            old.commit(); old.close(); new.close()
            dump = os.path.join(tmp, "fpl.sql")
            fpl_gate.write_dump(os.path.join(tmp, "old.sqlite"), dump)
            with open(dump, encoding="utf-8") as fh:
                ins = [l for l in fh if l.startswith('INSERT INTO "fixtures"')]
            self.assertEqual(ins, ["INSERT INTO \"fixtures\" VALUES(1,7,'2026-10-04T14:00:00Z',1,2,3,4,2,1,1,1,"
                                   "'2026-10-05T21:40:00+00:00',NULL);\n"])                      # the first 12 values in place
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_sync_writes_it(self):
        db = sqlite3.connect(":memory:")
        db.executescript(fpl_sync.SCHEMA)
        base = {"event": 8, "kickoff_time": "2026-10-24T14:00:00Z", "team_h": 1, "team_a": 2, "team_h_difficulty": 3,
                "team_a_difficulty": 3, "team_h_score": None, "team_a_score": None, "finished": False, "started": True}
        fx = [dict(base, id=1, finished_provisional=True), dict(base, id=2, finished_provisional=False), dict(base, id=3)]
        with mock.patch.object(fpl_sync, "get", return_value=fx), mock.patch("builtins.print"):
            fpl_sync.sync_fixtures(db)
        self.assertEqual(db.execute("SELECT id, finished, finished_provisional FROM fixtures ORDER BY id").fetchall(),
                         [(1, 0, 1), (2, 0, 0), (3, 0, None)])                                  # absent: NULL, nothing substituted


class BanRiskProvisional(unittest.TestCase):
    """Amendment 1 (B): a result FPL ended but has not marked finished counts, labelled; one in progress does not."""

    def setup_toy(self, tmp, hist):
        toy_live(tmp); toy_hist_root(hist)
        d = runner_export(tmp, hist)
        ours = fpl_chips.my_squad(d)[5]["id"]
        c = sqlite3.connect(os.path.join(tmp, "fpl.sqlite"))
        if "finished_provisional" not in {r[1] for r in c.execute("PRAGMA table_info(fixtures)")}:
            c.execute("ALTER TABLE fixtures ADD COLUMN finished_provisional INTEGER")
        evs = [e for (e,) in c.execute("select event from player_gw where player_id = ? and minutes > 0 order by event", (ours,))]
        for e in evs[:4]:
            c.execute("update player_gw set yellow = 1 where player_id = ? and event = ?", (ours, e))
        club = c.execute("select team_id from players where id = ?", (ours,)).fetchone()[0]
        fid, h, a = c.execute("select f.id, th.short_name, ta.short_name from fixtures f join teams th on th.id = f.team_h "
                              "join teams ta on ta.id = f.team_a where f.event = ? and ? in (f.team_h, f.team_a)",
                              (evs[3], club)).fetchone()
        c.commit(); c.close()
        return ours, fid, f"{h}-{a}"

    def lines(self, tmp):
        out = []
        n = SQ.ban_risk(tmp, out.append)
        return n, out

    def test_provisional_counted_and_labelled_in_progress_not(self):
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            ours, fid, ha = self.setup_toy(tmp, hist)
            n, out = self.lines(tmp)                                                       # all finished: listed, no label
            self.assertEqual(n, 1); self.assertNotIn("provisional:", out[-1])
            self.assertIn("a result FPL has ended but not yet marked finished counts, labelled provisional", out[0])
            db = os.path.join(tmp, "fpl.sqlite")
            c = sqlite3.connect(db)
            c.execute("update fixtures set finished = 1, finished_provisional = 1 where id = ?", (fid,)); c.commit()
            n, out = self.lines(tmp)                                                       # finished (and provisional): no label
            self.assertEqual(n, 1); self.assertNotIn("provisional:", out[-1])
            c.execute("update fixtures set finished = 0, finished_provisional = 1 where id = ?", (fid,)); c.commit()
            n, out = self.lines(tmp)
            self.assertEqual(n, 1)
            self.assertTrue(out[-1].endswith(f"   provisional: {ha} not yet marked finished by FPL"), out[-1])
            self.assertIn("cautions 4", out[-1])
            c.execute("update fixtures set finished = 0, finished_provisional = 0 where id = ?", (fid,)); c.commit()
            n, out = self.lines(tmp)                                                       # in progress: not counted
            self.assertEqual(n, 0); self.assertEqual(out[-1], "  none of our 15 is one booking from a ban")
            c.execute("update fixtures set finished = 0, finished_provisional = NULL where id = ?", (fid,)); c.commit()
            self.assertEqual(self.lines(tmp)[0], 0)                                        # NULL: not provisional
            c.close()
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)

    def test_without_provisional_the_rows_are_s12s(self):
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            self.setup_toy(tmp, hist)
            d, _ = fpl_chips.newest_export(tmp)
            mine, prov = SQ.ban_rows(tmp, d)
            theirs = fpl_mv2.rows_2627(tmp, d)
            self.assertEqual(prov, {})
            for k in ("matches", "played", "club_of", "pos", "names", "known"):
                self.assertEqual(getattr(mine, k), getattr(theirs, k), k)
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)


def git_repo(path):
    """A git repository at `path`, hermetic: identity, line endings and dates given per command."""
    subprocess.run(["git", "init", "-q", path], check=True, capture_output=True)
    return path


def git_commit(repo, files, when):
    for rel, text in files.items():
        full = os.path.join(repo, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    base = ["git", "-C", repo, "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false"]
    subprocess.run(base + ["add", "-A"], check=True, capture_output=True, env=env)
    subprocess.run(base + ["commit", "-q", "-m", "bundle"], check=True, capture_output=True, env=env)
    return subprocess.run(base + ["rev-parse", "HEAD"], check=True, capture_output=True, env=env, encoding="utf-8").stdout.strip()


POS_NAME = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


def bundle_text(order, names, pos, cap, own_order=None):
    """Section 5 of tools/gw_pass.py as it prints (its f-strings), xp_v2's order on the right."""
    own_order = own_order or order
    lines = ["GW PASS  GW8 ...", "", "=" * 78, "OWN v XP_V2 AS TESTED: XI, BENCH AND CAPTAIN", "=" * 78, "  GW8: ...", "  own = ...",
             f"  {'slot':>4}  {'own':<34}{'xp_v2 as tested':<34}"]
    for slot, (a, b) in enumerate(zip(own_order, order), 1):
        tag = "   " if a == b else " * "
        lines.append(f"  {slot:>4}{tag}{names[a]:<16}{POS_NAME[pos[a]]:>4} {1.0:5.2f}       {names[b]:<16}{POS_NAME[pos[b]]:>4} {2.0:5.2f}")
    lines.append(f"  captain: own {names[own_order[0]]} (1.00)  |  xp_v2 as tested {names[cap]} (2.00)" + ("" if cap == own_order[0] else "   *"))
    lines += ["  9 slots differ; ...", "", "=" * 78, "KEEPER LINE: OWN P(START) AND THE S12 KEEPER LOCK"]
    return "\n".join(lines) + "\n"


RUN_TXT = "tool: tools/gw_pass.py\ncommit: 71c9d17d72888e69f47213f156388daf1081bcba\nmodified tracked files at the run: 0\n"


class BundleGrading(unittest.TestCase):
    """Amendment 1 (C): GW8's xp_v2 from worklog/gw_pass/gw8/ at its last commit before the deadline."""

    def setUp(self):
        self.tmp, self.repo = tempfile.mkdtemp(), tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True); self.addCleanup(shutil.rmtree, self.repo, True)
        self.entry = toy_realised(self.tmp)
        rows = [r for r in E.read_log(os.path.join(self.tmp, E.LOG_PATH)) if r["source"] != "xp_v2"]   # W3 merges after GW8
        with open(os.path.join(self.tmp, E.LOG_PATH), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        c = sqlite3.connect(os.path.join(self.tmp, "fpl.sqlite"))
        c.execute("update players set web_name = 'De Cuyper' where id = 5")                       # a name with a space
        c.commit()
        self.pos = dict(c.execute("select id, position from players"))
        self.names = dict(c.execute("select id, web_name from players"))
        self.actual = {pid: (float(p), float(m)) for pid, p, m in c.execute("select player_id, total_points, minutes from player_gw where event = 8")}
        c.close()
        git_repo(self.repo)
        # xp_v2's order: GKs 1 and 2, then the XI by id descending within the legal shape, the bench last
        self.order = [2, 7, 6, 5, 4, 12, 11, 10, 9, 15, 14, 1, 3, 8, 13]
        self.cap = 12
        self.now = datetime(2026, 11, 1, tzinfo=timezone.utc)

    def run_(self):
        out = []
        recs = SQ.realised(self.tmp, out.append, now=self.now, entry=self.entry, repo=self.repo)
        return recs[0], out[1]

    def want(self, order, cap):
        rows = [{"id": i, "pos": self.pos[i]} for i in order]
        return SQ.realised_order(rows[:11], rows[11:], cap, self.actual)

    def test_graded_from_the_commit_before_the_deadline(self):
        h = git_commit(self.repo, {"worklog/gw_pass/gw8/gw8_pass.txt": bundle_text(self.order, self.names, self.pos, self.cap),
                                   "worklog/gw_pass/gw8/run.txt": RUN_TXT}, "2026-10-22T16:00:00+00:00")
        later = list(self.order); later[0], later[11] = later[11], later[0]
        git_commit(self.repo, {"worklog/gw_pass/gw8/gw8_pass.txt": bundle_text(later, self.names, self.pos, 15)},
                   "2026-10-24T09:00:00+00:00")                                                       # after the deadline: ignored
        g8, line = self.run_()
        self.assertEqual(g8["xp_v2"], self.want(self.order, self.cap)); self.assertEqual(g8["xp_v2_cap"], self.cap)
        self.assertIn(f"xp_v2 {g8['xp_v2']:.0f} (captain P12; source: GW8 bundle {h[:7]} (tools 71c9d17))", line)
        self.assertIn(f"xp_v2 - own {g8['xp_v2'] - g8['own']:+.0f}", line)

    def test_only_after_the_deadline_is_not_recorded(self):
        git_commit(self.repo, {"worklog/gw_pass/gw8/gw8_pass.txt": bundle_text(self.order, self.names, self.pos, self.cap),
                               "worklog/gw_pass/gw8/run.txt": RUN_TXT}, "2026-10-23T17:30:00+00:00")   # at the deadline: not before
        g8, line = self.run_()
        self.assertNotIn("xp_v2", g8); self.assertIn("xp_v2: not recorded before the deadline", line)

    def test_a_different_15_is_not_graded(self):
        names = dict(self.names); names[13] = "Other"
        h = git_commit(self.repo, {"worklog/gw_pass/gw8/gw8_pass.txt": bundle_text(self.order, names, self.pos, self.cap),
                                   "worklog/gw_pass/gw8/run.txt": RUN_TXT}, "2026-10-22T16:00:00+00:00")
        g8, line = self.run_()
        self.assertNotIn("xp_v2", g8)
        self.assertIn(f"xp_v2 (GW8 bundle {h[:7]} (tools 71c9d17)): the bundle's 15 is not our GW8 15 (only in the bundle: Other; "
                      f"only in our picks: P13): not graded", line)

    def test_no_run_txt_is_said(self):
        h = git_commit(self.repo, {"worklog/gw_pass/gw8/gw8_pass.txt": bundle_text(self.order, self.names, self.pos, self.cap)},
                       "2026-10-22T16:00:00+00:00")
        g8, line = self.run_()
        self.assertIn(f"source: GW8 bundle {h[:7]} (tools no run.txt at that commit)", line)

    def test_realised_order_is_realised_on(self):
        rng = random.Random(7)
        rows = [{"id": i, "pos": self.pos[i]} for i in range(1, 16)]
        matters = 0
        for _ in range(50):
            proj = {i: rng.uniform(0, 8) for i in range(1, 16)}
            actual = {i: (float(rng.randint(0, 12)), float(rng.choice((0, 45, 90, 90, 90, 90, 90)))) for i in range(1, 16)}   # one blank in seven: the bench order matters
            xi, bench, gk = fpl_chips.xi_and_bench([dict(r) for r in rows], proj)
            cap = max(xi, key=lambda r: (r["proj"], -r["id"]))
            got = SQ.realised_order(xi, [gk] + list(bench), cap["id"], actual)
            self.assertEqual(got, fpl_realised.realised_on(rows, proj, actual)[0])
            b = [gk] + list(bench)
            matters += got != SQ.realised_order(xi, b[:1] + b[:0:-1], cap["id"], actual)
        self.assertGreater(matters, 5)                                                     # the cases test the bench order

    def test_the_parser_reads_the_tools_own_print(self):
        tmp, hist = tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_live(tmp); toy_hist_root(hist)
            gw9_snapshot(tmp, "odds_2098-12-31T10-00-00Z.json.gz", "2098-12-31T10:00:00Z")
            buf = io.StringIO()
            with mock.patch.object(G.E, "selling_budget", return_value=(100.0, "")):
                G.bundle(tmp, out=lambda s="": buf.write(s + chr(10)), now=NOW9, hist_root=hist)
            rows, cap = SQ.parse_bundle(buf.getvalue())
            d, _ = CHt.newest_export(tmp)
            sq = CHt.my_squad(d)
            res = XL.live(tmp, hist, NOW9)
            log_rows = E.read_log(os.path.join(tmp, E.LOG_PATH))
            weeks, pts, src = CHt.own_week_points(d, log_rows)
            sbs = G.side_by_side(sq, pts[weeks[0]], res["xp"])
            self.assertEqual(rows, [(slot, b["name"], b["pos"]) for slot, a, b in sbs["rows"]])
            self.assertEqual(cap, sbs["captain"][1]["name"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True); shutil.rmtree(hist, ignore_errors=True)

    def test_the_nightly_checks_out_the_history(self):
        with open(os.path.join(ROOT, ".github", "workflows", "nightly.yml"), encoding="utf-8") as fh:
            text = fh.read()
        first = text.split("- uses: actions/checkout@")[1]
        self.assertIn("fetch-depth: 0", first.split("- uses:")[0])                             # the master checkout
        self.assertNotIn("ref: data", first.split("- uses:")[0])


class Sections(unittest.TestCase):
    """The three sections run in the nightly report after CHIPS and LEAGUE,
    and check 31 reads all five."""

    def test_in_the_report_and_check_31(self):
        tmp, hist, side = tempfile.mkdtemp(), tempfile.mkdtemp(), tempfile.mkdtemp()
        try:
            toy_live(tmp); toy_hist_root(hist)
            runner_export(tmp, hist)
            prior = prior_file(hist, side)
            git_repo(side)                                                                 # REALISED reads this repository, not ours
            with mock.patch.object(fpl_xpv2, "PRIOR_FILE", prior), mock.patch.object(SQ, "REPO", side):
                res = FS.sections(tmp, now=NOW9)
            self.assertEqual([t for t, _, _ in res], ["CHIPS", "LEAGUE", "CAPTAIN", "BAN RISK", "REALISED"])
            st = {t: s for t, _, s in res}
            for t in ("CAPTAIN", "BAN RISK", "REALISED"):
                self.assertRegex(st[t], rf"^{t} OK \d+ lines$")
            text = FS.render(res)
            self.assertIn("CAPTAIN (W3: Step 14 captain table)", text); self.assertIn("BAN RISK (W3: S12 suspensions)", text)
            log = "adding the report sections ..." + chr(10) + chr(10).join(s for _, _, s in res) + chr(10)
            level, detail = C.c31(C.Ctx(run_log=log))
            for t in ("CAPTAIN", "BAN RISK", "REALISED"):
                self.assertIn(st[t][len(t) + 4:], detail if level == C.OK else st[t])
            with mock.patch.object(fpl_xpv2, "PRIOR_FILE", os.path.join(side, "none.json")), mock.patch.object(SQ, "REPO", side):
                res = dict((t, s) for t, _, s in FS.sections(tmp, now=NOW9))
            self.assertTrue(res["CAPTAIN"].startswith("CAPTAIN SKIPPED: FileNotFoundError: "))
            self.assertRegex(res["BAN RISK"], r"^BAN RISK OK \d+ lines$")                # the others go on
        finally:
            for p in (tmp, hist, side):
                shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
