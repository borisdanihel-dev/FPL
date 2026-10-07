"""
test_fpl.py — regression tests for fpl_edge.py

    python test_fpl.py            run everything
    python test_fpl.py -v         verbose

Stdlib only. Builds synthetic exports in a temp folder, so it never touches
your real data and needs no network. Run it after editing either script.
"""

import csv
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                            # noqa: E402
import p1_eval as P1                                            # noqa: E402
import fpl_hist as H                                            # noqa: E402
import fpl_ship as SHIP                                         # noqa: E402
import fpl_nightly as N                                         # noqa: E402

TEAMS = ["ARS", "BHA", "CHE", "CRY", "HUL", "LIV", "MCI", "MUN", "NEW", "NFO"]
ENTRIES = ["My Team", "Rival A", "Rival B", "Rival C"]
MY_ID = 999
UNICODE_NAMES = ["Muharemović", "Groß", "João Pedro", "Ødegaard", "Horníček"]


def _kickoff(base, days, hhmm):
    """ISO kickoff `days` after `base` - valid for any gameweek, so tests can
    simulate GW18 or GW38 without inventing the 33rd of September."""
    from datetime import date, timedelta
    return f"{date.fromisoformat(base) + timedelta(days=days)}T{hhmm}:00Z"


def make_export(gw=3, n_entries=4, with_gw_rows=True, with_all_players=True,
                blank_team=None, horizon_gws=6, double_team=None):
    """A synthetic export with known, checkable properties."""
    players = []
    pid = 0
    for pos in (1, 2, 3, 4):
        per_pos = {1: 8, 2: 20, 3: 20, 4: 12}[pos]
        for i in range(per_pos):
            pid += 1
            name = UNICODE_NAMES[pid % len(UNICODE_NAMES)] + str(pid)
            players.append({
                "id": pid, "web_name": name, "team": TEAMS[pid % len(TEAMS)],
                "pos": pos, "price": 4.0 + (pid % 12) * 0.5,
                "price_change_season": 0.0, "owned_pct": (pid % 50) + 0.5,
                "status": "a" if pid % 17 else "d",
                "chance_next_round": None if pid % 17 else 50,
                "news": "" if pid % 17 else "Knock - 50% chance",
                "total_points": (pid % 25), "minutes": 90 * gw,
                "goals": 0, "assists": 0, "clean_sheets": 0, "bonus": 0,
                "xg": 0.0, "xa": 0.0, "starts": gw,
                "pens_order": 1 if pid % 20 == 0 else None,
                "corners_order": None, "fk_order": None, "xgc": 1.0,
                "form": 3.0, "ppg": 3.0,
                "threat": 10.0 * (pid % 7), "creativity": 5.0, "influence": 5.0,
                "tin_event": 1000, "tout_event": 500, "net_transfers": 500,
                "pts_last4": (pid % 25), "mins_last4": 90 * gw,
                "defcon_last4": (pid % 40), "starts_last4": gw,
            })

    squads, ownership = [], []
    for e_i, entry in enumerate(ENTRIES[:n_entries]):
        picks = players[e_i:] + players[:e_i]
        chosen = ([p for p in picks if p["pos"] == 1][:2]
                  + [p for p in picks if p["pos"] == 2][:5]
                  + [p for p in picks if p["pos"] == 3][:5]
                  + [p for p in picks if p["pos"] == 4][:3])
        for slot, p in enumerate(chosen, 1):
            squads.append({
                "entry_id": MY_ID if e_i == 0 else 100 + e_i,
                "entry_name": entry, "slot": slot, "web_name": p["web_name"],
                "team": p["team"], "pos": p["pos"], "price": p["price"],
                "multiplier": (2 if slot == 10 else 1) if slot <= 11 else 0,
                "is_captain": 1 if slot == 10 else 0,
                "is_vice": 1 if slot == 9 else 0,
                "gw_points": p["pts_last4"] // max(1, gw), "minutes": 90,
            })
        if e_i == 0:
            for p in chosen:
                ownership.append({"web_name": p["web_name"], "team": p["team"],
                                  "price": p["price"], "owners": 1, "i_own": 1,
                                  "total_points": p["total_points"]})

    fixtures = []
    for ev in range(gw + 1, gw + 1 + horizon_gws):
        pool = [t for t in TEAMS if not (blank_team and t == blank_team
                                         and ev == gw + 1)]
        for a, b in zip(pool[0::2], pool[1::2]):
            fixtures.append({"event": ev, "home": a, "away": b,
                             "h_fdr": 2 + (ev % 3), "a_fdr": 2 + ((ev + 1) % 3),
                             "kickoff_time": _kickoff("2026-09-10", ev, "14:00")})
        if double_team and ev == gw + 1:
            opp = next(t for t in TEAMS if t != double_team)
            fixtures.append({"event": ev, "home": double_team, "away": opp,
                             "h_fdr": 2, "a_fdr": 2,
                             "kickoff_time": _kickoff("2026-09-10", ev, "18:00")})

    played = []
    for ev in range(1, gw + 1):
        for a, b in zip(TEAMS[0::2], TEAMS[1::2]):
            played.append({"event": ev, "home": a, "away": b,
                           "h_goals": (ev + len(a)) % 4, "a_goals": ev % 3,
                           "h_fdr": 2 + (ev % 3), "a_fdr": 2 + ((ev + 1) % 3),
                           "kickoff_time": _kickoff("2026-08-20", ev, "14:00")})

    out = {
        "schema": 2, "generated": "2026-09-07T00:00:00+00:00",
        "league_id": 1, "my_entry": MY_ID, "gameweek": gw,
        "standings": [{
            "entry_id": MY_ID if i == 0 else 100 + i, "entry_name": e,
            "player_name": e, "rank": i + 1, "event_total": 50 - i,
            "total": 200 - i * 10, "value": 1003, "bank": 2,
            "points_on_bench": 5, "transfers": 2 if i == 0 else 1,
            "transfers_cost": 0, "active_chip": None,
        } for i, e in enumerate(ENTRIES[:n_entries])],
        "chips_used": [{"entry_name": "Rival A", "name": "3xc", "event": gw}],
        "squads": squads,
        "transfers": [{"entry_name": "My Team", "event": gw,
                       "player_in": "x", "player_out": "y",
                       "cost_in": 5.0, "cost_out": 5.0}] * 2,
        "league_ownership": ownership,
        "top_players_recent": [],
        "fixtures_next6": fixtures,
        "price_changes_7d": [],
        "fixtures_played": played,
        "events": [{"event": ev, "finished": 1, "data_checked": 1}
                   for ev in range(1, gw + 1)],
        "fixtures_status": [{"event": f["event"], "home": f["home"],
                             "away": f["away"], "kickoff_time": f["kickoff_time"],
                             "finished": 1} for f in played],
        "player_history": [
            {"web_name": p["web_name"], "team": p["team"], "pos": p["pos"],
             "season": "2025/26", "minutes": 2500, "pts": 90 + (p["id"] % 60),
             "starts": 28, "goals": 5, "assists": 4, "cs": 8,
             "xg": 4.5, "xa": 3.5}
            for p in players[:40]],
        "teams": [{"team": t, "name": t, "strength": 3, "att_h": 1100,
                   "att_a": 1100, "def_h": 1100, "def_a": 1100} for t in TEAMS],
    }
    if with_all_players:
        out["all_players"] = players
    if with_gw_rows:
        out["player_gw_recent"] = [
            {"event": ev, "player_id": p["id"], "n_fixtures": 1,
             "web_name": p["web_name"], "team": p["team"],
             "pos": p["pos"], "pts": (p["id"] + ev) % 13, "mins": 90,
             "starts": 1, "g_": 0, "a_": 0, "cs": 0, "gc": 1, "bonus": 0,
             "bps": 10, "defcon": (p["id"] + ev) % 18, "xg": 0.1, "xa": 0.1,
             "opp": TEAMS[(p["id"] + ev) % len(TEAMS)],
             "venue": "H" if (p["id"] + ev) % 2 else "A",
             "fdr": 2 + ((p["id"] + ev) % 3), "opp_goals": ev % 3}
            for ev in range(1, gw + 1) for p in players]
    return out


def run(section, data, horizon=6):
    """Run one section, return its stdout."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        E.SECTIONS[section](data, horizon)
    return buf.getvalue()


class Smoke(unittest.TestCase):
    """Every section runs on a well-formed export."""

    @classmethod
    def setUpClass(cls):
        cls.d = make_export()

    def test_all_sections_produce_output(self):
        for name in E.SECTIONS:
            with self.subTest(section=name):
                out = run(name, self.d)
                self.assertGreater(len(out), 50, f"{name} produced almost nothing")

    def test_no_section_is_silent_in_full_report(self):
        full = "".join(run(n, self.d) for n in E.SECTIONS
                       if n not in ("brief", "wildcard", "backtest"))
        self.assertGreater(full.count("="), 20)


class Degradation(unittest.TestCase):
    """Malformed or partial exports must not crash."""

    def test_missing_all_players(self):
        d = make_export(with_all_players=False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_diff(make_export(), d, 6)
        self.assertIn("missing", buf.getvalue())

    def test_missing_gw_rows_backtest(self):
        out = run("backtest", make_export(with_gw_rows=False))
        self.assertIn("refetch", out)

    def test_missing_fixtures_played_fdr(self):
        d = make_export()
        d.pop("fixtures_played")
        out = run("fdr", d)
        self.assertIn("Needs finished fixtures", out)

    def test_fdr_handles_null_scores(self):
        """Postponed fixtures come back with null scores and must be skipped."""
        d = make_export()
        d["fixtures_played"][0]["h_goals"] = None
        d["fixtures_played"][0]["a_goals"] = None
        out = run("fdr", d)
        self.assertIn("FDR AUDIT", out)

    def test_sensitivity_needs_per_match_fdr(self):
        d = make_export()
        for r in d["player_gw_recent"]:
            r.pop("fdr")
        out = run("sensitivity", d)
        self.assertIn("Needs per-match FDR", out)

    def test_personal_prior_overrides_positional(self):
        """A known player must be anchored to his own history, not the median."""
        d = make_export()
        priors = E.positional_priors(d["all_players"])
        personal = E.personal_priors(d)
        name = next(iter(personal))
        row = next(p for p in d["all_players"] if p["web_name"] == name)
        subj = {"web_name": name, "pos": row["pos"], "team": row["team"],
                "pts_last4": 30, "mins_last4": 270}
        with_p, _, _ = E.project(subj, {}, 6, 3, priors, personal)
        without, _, _ = E.project(subj, {}, 6, 3, priors, None)
        self.assertNotAlmostEqual(with_p, without, places=3,
                                  msg="personal prior had no effect")

    def test_consistency_needs_gw_rows(self):
        d = make_export(with_gw_rows=False)
        self.assertIn("Needs per-gameweek rows", run("consistency", d))

    def test_arbitrage_without_threat(self):
        d = make_export()
        for p in d["all_players"]:
            p.pop("threat", None)
        out = run("arbitrage", d)
        self.assertIn("threat unavailable", out)

    def test_personal_priors_read_history(self):
        d = make_export()
        pri = E.personal_priors(d)
        self.assertTrue(pri, "history present but no priors built")
        for v in pri.values():
            self.assertGreater(v, 0)

    def test_personal_priors_empty_without_history(self):
        d = make_export()
        d.pop("player_history")
        self.assertEqual(E.personal_priors(d), {})

    def test_missing_gw_rows_defcon(self):
        out = run("defcon", make_export(with_gw_rows=False))
        self.assertIn("unavailable", out)

    def test_single_gameweek_backtest_declines(self):
        out = run("backtest", make_export(gw=1))
        self.assertIn("Needs 3+", out)

    def test_same_gameweek_diff_warns(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_diff(make_export(gw=3), make_export(gw=3), 6)
        self.assertIn("against itself", buf.getvalue())

    def test_empty_standings_does_not_crash(self):
        d, prev = make_export(), make_export()
        prev["standings"] = []
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_diff(d, prev, 6)
        self.assertIn("no comparable standings", buf.getvalue())


class Correctness(unittest.TestCase):

    def setUp(self):
        self.d = make_export()

    def test_identity_uses_entry_id(self):
        self.assertEqual(E.my_name(self.d), "My Team")

    def test_identity_falls_back_without_entry_id(self):
        d = make_export()
        for row in d["squads"]:
            row.pop("entry_id")
        d.pop("my_entry")
        self.assertEqual(E.my_name(d), "My Team")

    def test_free_transfer_estimate(self):
        # GW2 unused (+1), GW3 grants 1 -> 2 banked, 2 spent -> 0, +1 for GW4
        self.assertEqual(E.estimate_free_transfers(self.d), 1)

    def test_free_transfers_cap_at_five(self):
        d = make_export(gw=12)
        d["transfers"] = []
        self.assertEqual(E.estimate_free_transfers(d), 5)

    def test_ticker_has_one_row_per_gameweek(self):
        tick, gws = E.build_ticker(self.d, 6)
        self.assertEqual(len(gws), 6)
        for team, fx in tick.items():
            self.assertEqual(len(fx), 6, f"{team} has {len(fx)} fixtures")

    def test_best_xi_is_legal(self):
        pool = [dict(p, proj=(p["id"] % 9) + 1.0) for p in self.d["all_players"]]
        squad = (([p for p in pool if p["pos"] == 1][:2])
                 + ([p for p in pool if p["pos"] == 2][:5])
                 + ([p for p in pool if p["pos"] == 3][:5])
                 + ([p for p in pool if p["pos"] == 4][:3]))
        xi = E._best_xi(squad)
        self.assertEqual(len(xi), 11)
        counts = {k: sum(1 for p in xi if p["pos"] == k) for k in (1, 2, 3, 4)}
        self.assertEqual(counts[1], 1)
        self.assertGreaterEqual(counts[2], 3)
        self.assertGreaterEqual(counts[3], 2)
        self.assertGreaterEqual(counts[4], 1)

    def test_built_squad_respects_all_constraints(self):
        tick, _ = E.build_ticker(self.d, 6)
        priors = E.positional_priors(self.d["all_players"])
        pool = []
        for p in self.d["all_players"]:
            if p["status"] != "a":
                continue
            proj, _, _ = E.project(p, tick, 6, 3, priors)
            if proj <= 0:
                continue
            q = dict(p, proj=proj, vpm=proj / p["price"])
            pool.append(q)
        squad = E._build_squad(pool, 100.0)
        self.assertIsNotNone(squad)
        self.assertEqual(len(squad), 15)
        self.assertLessEqual(sum(p["price"] for p in squad), 100.0)
        for pos, want in ((1, 2), (2, 5), (3, 5), (4, 3)):
            self.assertEqual(sum(1 for p in squad if p["pos"] == pos), want)
        clubs = {}
        for p in squad:
            clubs[p["team"]] = clubs.get(p["team"], 0) + 1
        self.assertLessEqual(max(clubs.values()), 3)

    def test_projection_is_shrunk_not_raw(self):
        """A three-game hot streak must not project at its raw rate."""
        priors = E.positional_priors(self.d["all_players"])
        hot = {"web_name": "Hot Streak", "pos": 3, "team": "ARS",
               "pts_last4": 45, "mins_last4": 270}
        proj, per90, _ = E.project(hot, {}, 6, 3, priors)
        self.assertLess(per90, 15.0, "shrinkage is not being applied")
        self.assertGreater(per90, priors[3])


class Regressions(unittest.TestCase):
    """One test per bug that reached production."""

    def test_diff_with_no_previous_export_still_reports(self):
        """The report came out empty when --diff found nothing to compare."""
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "fpl_export_gw3.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(make_export(), f)
            self.assertIsNone(E.previous_export(path, tmp))
            out = run("league", make_export())
            self.assertIn("LEAGUE", out)
        finally:
            shutil.rmtree(tmp)

    def test_unicode_survives_a_cp1252_stream(self):
        """A cp1252 console killed the whole run on a player named Muharemović."""
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
        tee = E._Tee(stream)
        tee.write("Muharemović Groß Ødegaard\n")
        tee.flush()
        self.assertIn(b"Gro", raw.getvalue())

    def test_blank_gameweek_is_labelled_not_mislabelled(self):
        """nextfx used to show a team's GW+2 fixture as if it were GW+1."""
        d = make_export(blank_team="HUL")
        nxt = d["gameweek"] + 1

        # the blank must actually exist, or the test proves nothing
        tick, _ = E.build_ticker(d, 6)
        self.assertEqual([f for f in tick["HUL"] if f[0] == nxt], [],
                         "test fixture is wrong: HUL should have no GW%d game" % nxt)
        self.assertTrue([f for f in tick["HUL"] if f[0] > nxt],
                        "HUL needs later fixtures, or there is nothing to mislabel")

        # force a HUL player into my XI so brief must render that cell
        for row in d["squads"]:
            if row["entry_name"] == "My Team" and row["slot"] == 3:
                row["team"] = "HUL"
                break
        else:
            self.fail("could not place a HUL player in the XI")

        out = run("brief", d)
        self.assertIn("BLANK", out,
                      "a blanking team must be reported as BLANK, not shown "
                      "with a later gameweek's fixture")

    def test_backtest_ignores_future_fixture_difficulty(self):
        """Behavioural, not textual: changing only the FORWARD ticker must not
        change a backtest of a past gameweek."""
        a = make_export()
        b = make_export()
        for f in b["fixtures_next6"]:          # make the future look totally different
            f["h_fdr"], f["a_fdr"] = 5, 5
        self.assertNotEqual([f["h_fdr"] for f in a["fixtures_next6"]],
                            [f["h_fdr"] for f in b["fixtures_next6"]])
        self.assertEqual(run("backtest", a), run("backtest", b),
                         "backtest output moved when only future fixtures changed")

    def test_backtest_uses_the_tested_gameweeks_own_difficulty(self):
        """Changing the FDR attached to the target gameweek must move the model."""
        a = make_export()
        b = make_export()
        target = max(r["event"] for r in b["player_gw_recent"])
        for r in b["player_gw_recent"]:
            if r["event"] == target:
                r["fdr"] = 5
        self.assertNotEqual(run("backtest", a), run("backtest", b),
                            "backtest ignored the tested gameweek's own FDR")

    def test_starts_last4_disagreement_is_detectable(self):
        """starts_last4 was silently zero for un-refetched gameweeks."""
        d = make_export()
        bad = dict(d["all_players"][0])
        bad["starts"], bad["starts_last4"] = 3, 1
        self.assertNotEqual(bad["starts"], bad["starts_last4"])


class ExternalProjections(unittest.TestCase):
    """The compare loader must accept the shapes real tools emit."""

    def _csv(self, header, rows):
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "proj.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(",".join(header) + "\n")
            for r in rows:
                f.write(",".join(str(x) for x in r) + "\n")
        return tmp, path

    def test_reads_id_and_xpts(self):
        tmp, path = self._csv(["element", "gw", "xPts"], [[1, 3, 5.5], [2, 3, 1.2]])
        try:
            ext, err = E.load_projections(path)
            self.assertIsNone(err)
            self.assertEqual(ext[("id", 1)][3], 5.5)
        finally:
            shutil.rmtree(tmp)

    def test_reads_name_and_alternative_header(self):
        tmp, path = self._csv(["player", "prediction"], [["Groß1", 4.4]])
        try:
            ext, err = E.load_projections(path)
            self.assertIsNone(err)
            self.assertEqual(ext[("name", "Groß1")][None], 4.4)
        finally:
            shutil.rmtree(tmp)

    def test_rejects_file_without_forecast_column(self):
        tmp, path = self._csv(["element", "team"], [[1, "ARS"]])
        try:
            _, err = E.load_projections(path)
            self.assertIn("no forecast column", err)
        finally:
            shutil.rmtree(tmp)

    def test_skips_unparseable_rows(self):
        tmp, path = self._csv(["element", "xPts"], [[1, "n/a"], [2, 3.0]])
        try:
            ext, err = E.load_projections(path)
            self.assertIsNone(err)
            self.assertEqual(len(ext), 1)
        finally:
            shutil.rmtree(tmp)

    def test_defcon_expectation_bounds(self):
        """Expected DEFCON points must sit between 0 and 2 per start."""
        d = make_export()
        dc = E.defcon_expectation(d)
        self.assertTrue(dc, "no expectations computed")
        for name, v in dc.items():
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 2.0)

    def test_defcon_expectation_zero_for_keepers_and_forwards(self):
        d = make_export()
        dc = E.defcon_expectation(d)
        idx = E.gw_index(d)
        for name, v in dc.items():
            pos = idx[name][0]["pos"]
            if pos in (1, 4):
                self.assertEqual(v, 0.0, f"{name} is pos {pos}, no threshold exists")

    def test_defcon_correction_recovers_missing_points(self):
        """A projection that is perfect except for DEFCON must improve."""
        tmp = tempfile.mkdtemp()
        try:
            d = make_export()
            target = max(r["event"] for r in d["player_gw_recent"])
            by = {p["web_name"]: p for p in d["all_players"]}
            path = os.path.join(tmp, "p.csv")
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write("element,gw,xPts\n")
                for r in d["player_gw_recent"]:
                    if r["event"] != target:
                        continue
                    p = by.get(r["web_name"])
                    if not p:
                        continue
                    thr = E.DEFCON_THRESHOLD.get(r["pos"])
                    got = 2 if (thr and (r["defcon"] or 0) >= thr) else 0
                    f.write(f"{p['id']},{target},{r['pts']-got}\n")
            buf = io.StringIO()
            with redirect_stdout(buf):
                E.sec_compare(d, 6, path)
            self.assertIn("the correction helps", buf.getvalue())
        finally:
            shutil.rmtree(tmp)

    def test_compare_reports_missing_file(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_compare(make_export(), 6, "does_not_exist.csv")
        self.assertIn("Not found", buf.getvalue())

    def test_compare_warns_on_poor_match_rate(self):
        tmp, path = self._csv(["player", "xPts"], [["Nobody", 5.0]])
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                E.sec_compare(make_export(), 6, path)
            self.assertIn("unmatched", buf.getvalue())
        finally:
            shutil.rmtree(tmp)


class ProjectionLog(unittest.TestCase):
    """Point-in-time discipline: the log must never contain hindsight."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log = os.path.join(self.tmp, "log.csv")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _future_export(self, days=5):
        from datetime import datetime, timedelta, timezone
        d = make_export()
        when = datetime.now(timezone.utc) + timedelta(days=days)
        for f in d["fixtures_next6"]:
            if f["event"] == d["gameweek"] + 1:
                f["kickoff_time"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
        return d

    def test_records_before_deadline(self):
        d = self._future_export()
        buf = io.StringIO()
        with redirect_stdout(buf):
            n = E.record_projections(d, 6, "own", None, self.log)
        self.assertGreater(n, 0)
        self.assertTrue(os.path.exists(self.log))

    def test_refuses_after_deadline(self):
        from datetime import datetime, timedelta, timezone
        d = make_export()
        past = datetime.now(timezone.utc) - timedelta(days=2)
        for f in d["fixtures_next6"]:
            if f["event"] == d["gameweek"] + 1:
                f["kickoff_time"] = past.strftime("%Y-%m-%dT%H:%M:%SZ")
        buf = io.StringIO()
        with redirect_stdout(buf):
            n = E.record_projections(d, 6, "own", None, self.log)
        self.assertEqual(n, 0, "recorded a forecast after the deadline")
        self.assertIn("Refusing", buf.getvalue())
        self.assertFalse(os.path.exists(self.log))

    def test_rerun_replaces_rather_than_duplicates(self):
        d = self._future_export()
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.record_projections(d, 6, "own", None, self.log)
            first = len(E.read_log(self.log))
            E.record_projections(d, 6, "own", None, self.log)
            second = len(E.read_log(self.log))
        self.assertEqual(first, second, "re-recording duplicated rows")

    def test_sources_do_not_collide(self):
        d = self._future_export()
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.record_projections(d, 6, "own", None, self.log)
            n1 = len(E.read_log(self.log))
            E.record_projections(d, 6, "other", None, self.log)
            n2 = len(E.read_log(self.log))
        self.assertGreater(n2, n1, "second source overwrote the first")

    def test_calibration_reports_pending_before_results(self):
        d = self._future_export()
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.record_projections(d, 6, "own", None, self.log)
            E.sec_calibration(d, 6, self.log)
        self.assertIn("not played yet", buf.getvalue())

    def test_calibration_grades_once_results_exist(self):
        d = self._future_export()
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.record_projections(d, 6, "own", None, self.log)
        target = d["gameweek"] + 1
        played = dict(d)
        rows = list(d["player_gw_recent"])
        for r in d["player_gw_recent"]:
            if r["event"] == d["gameweek"]:
                rows.append(dict(r, event=target))
        played["player_gw_recent"] = rows
        played["gameweek"] = target
        played["events"] = d["events"] + [{"event": target, "finished": 1,
                                           "data_checked": 1}]
        played["fixtures_status"] = d["fixtures_status"] + [
            {"event": target, "home": f["home"], "away": f["away"],
             "kickoff_time": f["kickoff_time"], "finished": 1}
            for f in d["fixtures_next6"] if f["event"] == target]
        played["fixtures_played"] = d["fixtures_played"] + [
            {"event": target, "home": f["home"], "away": f["away"], "h_goals": 1,
             "a_goals": 0, "h_fdr": f["h_fdr"], "a_fdr": f["a_fdr"],
             "kickoff_time": f["kickoff_time"]}
            for f in d["fixtures_next6"] if f["event"] == target]
        with redirect_stdout(buf):
            E.sec_calibration(played, 6, self.log)
        out = buf.getvalue()
        self.assertIn("MAE", out)
        self.assertIn("constant", out)

    def test_empty_log_is_not_an_error(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_calibration(make_export(), 6, self.log)
        self.assertIn("No forecasts recorded", buf.getvalue())


class BottomUpModel(unittest.TestCase):
    """project_xg is built from scoring rules, so each term is checkable."""

    def setUp(self):
        self.d = make_export()
        self.cs, self.dflt = E.cs_rate_by_fdr(self.d)
        self.hist = E.history_rates(self.d)

    def _p(self, **kw):
        base = {"web_name": "Test", "pos": 3, "team": "ARS", "price": 6.0,
                "mins_last4": 270, "starts_last4": 3, "starts": 3,
                "xg": 0.9, "xa": 0.6, "chance_next_round": None,
                "_defcon_pts": 0.0}
        base.update(kw)
        return base

    def test_non_starter_projects_to_zero(self):
        v = E.project_xg(self._p(starts_last4=0, starts=0), 3, 3,
                         self.cs, self.dflt, self.hist)
        self.assertEqual(v, 0.0)

    def test_injury_doubt_scales_it_down(self):
        full = E.project_xg(self._p(), 3, 3, self.cs, self.dflt, self.hist)
        doubt = E.project_xg(self._p(chance_next_round=25), 3, 3,
                             self.cs, self.dflt, self.hist)
        self.assertLess(doubt, full)
        self.assertAlmostEqual(doubt / full, 0.25, delta=0.02)

    def test_defenders_gain_more_from_easy_fixtures_than_forwards(self):
        """Clean sheet value is 4 for a defender, 0 for a forward. Uses an
        explicit CS table: the synthetic fixture has too few results to
        differentiate the buckets, which is itself correct behaviour."""
        table = {2: 0.40, 3: 0.28, 4: 0.15, 5: 0.10}
        d_easy = E.project_xg(self._p(pos=2), 2, 3, table, 0.28, self.hist)
        d_hard = E.project_xg(self._p(pos=2), 4, 3, table, 0.28, self.hist)
        f_easy = E.project_xg(self._p(pos=4), 2, 3, table, 0.28, self.hist)
        f_hard = E.project_xg(self._p(pos=4), 4, 3, table, 0.28, self.hist)
        self.assertGreater(d_easy - d_hard, 0.9,
                           "defender should gain ~1 pt from an easy fixture")
        self.assertAlmostEqual(f_easy, f_hard, places=6,
                               msg="forwards get nothing from clean sheets")

    def test_flat_cs_table_means_fixtures_do_not_move_defenders(self):
        """Guards the failure mode the previous test exposed."""
        flat = {2: 0.3, 3: 0.3, 4: 0.3, 5: 0.3}
        a = E.project_xg(self._p(pos=2), 2, 3, flat, 0.3, self.hist)
        b = E.project_xg(self._p(pos=2), 4, 3, flat, 0.3, self.hist)
        self.assertAlmostEqual(a, b, places=6)

    def test_defcon_is_not_double_counted(self):
        """defcon_expectation already returns points; adding 2 pts of DEFCON
        must raise the projection by 2, not 4."""
        a = E.project_xg(self._p(_defcon_pts=0.0), 3, 3,
                         self.cs, self.dflt, self.hist)
        b = E.project_xg(self._p(_defcon_pts=2.0), 3, 3,
                         self.cs, self.dflt, self.hist)
        self.assertAlmostEqual(b - a, 2.0, places=6)

    def test_xg_drives_goals_by_position_value(self):
        """Same xG is worth more to a defender (6) than a forward (4)."""
        dv = E.project_xg(self._p(pos=2, xa=0.0), 3, 3,
                          self.cs, self.dflt, self.hist)
        fv = E.project_xg(self._p(pos=4, xa=0.0), 3, 3,
                          self.cs, self.dflt, self.hist)
        self.assertGreater(dv, fv)

    def test_cs_rate_falls_back_when_sample_too_small(self):
        d = make_export()
        d["fixtures_played"] = d["fixtures_played"][:2]
        table, default = E.cs_rate_by_fdr(d)
        self.assertTrue(all(v == default for v in table.values()))

    def test_cs_rate_handles_no_results(self):
        d = make_export()
        d["fixtures_played"] = []
        table, default = E.cs_rate_by_fdr(d)
        self.assertGreater(default, 0)
        self.assertLess(default, 1)

    def test_xg_rate_uses_season_minutes_not_last_four(self):
        """xG is a season total. Dividing by a 4-week window inflates it once
        the season passes GW4 - identical before, badly wrong after."""
        table, hist = {2: .4, 3: .28, 4: .15, 5: .1}, {}
        p = self._p(pos=3, xg=5.0, xa=0.0, minutes=900, mins_last4=360,
                    starts_last4=4, starts=10)
        v = E.project_xg(p, 3, 10, table, 0.28, hist)
        # appearance 2 + goals (5/900*90)*5 + CS .28*1 + bonus .8*.5
        self.assertAlmostEqual(v, 2.0 + 2.5 + 0.28 + 0.4, places=2)

    def test_start_probability_does_not_decay_over_the_season(self):
        """starts_last4 caps at 4, so the denominator must cap at 4 too."""
        table, hist = {3: 0.28}, {}
        vals = []
        for gw in (4, 10, 20, 38):
            p = self._p(pos=3, xg=0.0, xa=0.0, minutes=90 * gw,
                        mins_last4=360, starts_last4=4, starts=gw)
            vals.append(E.project_xg(p, 3, gw, table, 0.28, hist))
        for v in vals[1:]:
            self.assertAlmostEqual(v, vals[0], places=6,
                                   msg="nailed starter decays over the season")

    def test_zero_recent_starts_is_not_treated_as_missing(self):
        """A player who has stopped starting must not fall back to season
        starts - the classic falsy-zero trap."""
        table, hist = {3: 0.28}, {}
        p = self._p(pos=3, xg=1.0, xa=1.0, minutes=900, mins_last4=200,
                    starts_last4=0, starts=5)
        self.assertEqual(E.project_xg(p, 3, 10, table, 0.28, hist), 0.0)

    def test_missing_starts_field_falls_back_to_season(self):
        table, hist = {3: 0.28}, {}
        p = self._p(pos=3, xg=0.0, xa=0.0, minutes=900, mins_last4=360,
                    starts=5)
        p.pop("starts_last4", None)
        self.assertGreater(E.project_xg(p, 3, 10, table, 0.28, hist), 0.0)

    def test_blank_gameweek_gets_no_forecast(self):
        """A team with no fixture must be skipped, not given a default FDR."""
        from datetime import datetime, timedelta, timezone
        tmp = tempfile.mkdtemp()
        try:
            log = os.path.join(tmp, "log.csv")
            d = make_export(blank_team="HUL")
            nxt = d["gameweek"] + 1
            when = datetime.now(timezone.utc) + timedelta(days=3)
            for f in d["fixtures_next6"]:
                if f["event"] == nxt:
                    f["kickoff_time"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
            buf = io.StringIO()
            with redirect_stdout(buf):
                E.record_projections(d, 6, "xg", None, log)
            hull = {p["web_name"] for p in d["all_players"] if p["team"] == "HUL"}
            logged = {r["web_name"] for r in E.read_log(log)}
            self.assertFalse(hull & logged,
                             "forecast a team that has no fixture")
            self.assertTrue(logged, "nothing logged at all")
        finally:
            shutil.rmtree(tmp)

    def test_double_gameweek_sums_both_fixtures(self):
        """The summing lives in record_projections, so the assertion must come
        from the log. Calling project_xg twice and adding the results only
        proves that addition works - it passes with the summing removed."""
        from datetime import datetime, timedelta, timezone

        def logged(double):
            tmp = tempfile.mkdtemp()
            try:
                path = os.path.join(tmp, "log.csv")
                d = make_export(double_team=TEAMS[0] if double else None)
                when = datetime.now(timezone.utc) + timedelta(days=3)
                for f in d["fixtures_next6"]:
                    if f["event"] == d["gameweek"] + 1:
                        f["kickoff_time"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
                buf = io.StringIO()
                with redirect_stdout(buf):
                    E.record_projections(d, 6, "xg", None, path)
                return {r["web_name"]: float(r["predicted"])
                        for r in E.read_log(path)}
            finally:
                shutil.rmtree(tmp)

        one, two = logged(False), logged(True)
        on_team = {p["web_name"] for p in make_export()["all_players"]
                   if p["team"] == TEAMS[0]}
        names = sorted(on_team & set(one) & set(two))
        self.assertTrue(names, "no logged player on the doubled team")
        for nm in names:
            self.assertGreater(
                two[nm], one[nm] * 1.5,
                f"{nm}: double GW logged {two[nm]:.2f} vs single {one[nm]:.2f} "
                f"- the record loop is not summing both fixtures")

    def test_both_models_log_side_by_side(self):
        from datetime import datetime, timedelta, timezone
        tmp = tempfile.mkdtemp()
        try:
            log = os.path.join(tmp, "log.csv")
            d = make_export()
            when = datetime.now(timezone.utc) + timedelta(days=3)
            for f in d["fixtures_next6"]:
                if f["event"] == d["gameweek"] + 1:
                    f["kickoff_time"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
            buf = io.StringIO()
            with redirect_stdout(buf):
                E.record_projections(d, 6, "own", None, log)
                E.record_projections(d, 6, "xg", None, log)
            rows = E.read_log(log)
            self.assertIn("own", {r["source"] for r in rows})
            self.assertIn("xg", {r["source"] for r in rows})
        finally:
            shutil.rmtree(tmp)


class ExportSchema(unittest.TestCase):
    """Guard the contract between fpl_sync.py and fpl_edge.py."""

    REQUIRED = ["gameweek", "standings", "squads", "all_players",
                "fixtures_next6", "chips_used", "transfers", "league_ownership"]

    def test_synthetic_export_has_required_keys(self):
        d = make_export()
        for k in self.REQUIRED:
            self.assertIn(k, d)

    def test_real_export_if_present(self):
        """If a real export is sitting here, check it against the same contract."""
        path = E.newest_export(".")
        if not path:
            self.skipTest("no real export in this folder")
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        for k in self.REQUIRED:
            self.assertIn(k, d, f"{os.path.basename(path)} is missing {k}")
        for name in E.SECTIONS:
            with self.subTest(section=name):
                run(name, d)


class SyncSQL(unittest.TestCase):
    """fpl_sync.py's SQL must actually run against fpl_sync.py's own schema.

    A column-name typo used to reach production because nothing executed the
    export queries until the nightly job did.
    """

    @classmethod
    def setUpClass(cls):
        import ast as _ast
        import sqlite3
        here = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(here, "fpl_sync.py")
        if not os.path.exists(path):
            raise unittest.SkipTest("fpl_sync.py not next to the tests")
        with open(path, encoding="utf-8") as fh:
            cls.src = fh.read()
        ns = {}
        exec(compile(cls.src.split("def main()")[0], "fpl_sync", "exec"), ns)
        cls.ns = ns
        cls.db = sqlite3.connect(":memory:")
        cls.db.executescript(ns["SCHEMA"])
        ns["migrate"](cls.db)
        cls.sqls = []
        for node in _ast.walk(_ast.parse(cls.src)):
            if (isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name)
                    and node.func.id == "q" and len(node.args) >= 2
                    and isinstance(node.args[1], _ast.Constant)
                    and isinstance(node.args[1].value, str)):
                cls.sqls.append(node.args[1].value)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_found_the_queries(self):
        self.assertGreaterEqual(len(self.sqls), 8,
                                "SQL extraction is broken, not the SQL")

    def test_every_export_query_executes(self):
        import sqlite3
        for sql in self.sqls:
            label = " ".join(sql.split())[:60]
            with self.subTest(sql=label):
                try:
                    self.db.execute(sql, tuple([3] * sql.count("?")))
                except sqlite3.Error as e:
                    self.fail(f"{e}\n  {label}...")

    def test_migration_is_idempotent(self):
        before = {r[1] for r in self.db.execute("PRAGMA table_info(players)")}
        self.ns["migrate"](self.db)
        after = {r[1] for r in self.db.execute("PRAGMA table_info(players)")}
        self.assertEqual(before, after)

    def test_insert_arity_matches_schema(self):
        """INSERT ... VALUES (?,?,...) must match the real column count."""
        import re as _re
        for table in ("players", "player_gw"):
            cols = len(list(self.db.execute(f"PRAGMA table_info({table})")))
            m = _re.search(
                r'INSERT OR REPLACE INTO %s VALUES \(%%s\)" %% ",".join\("\?" \* (\d+)\)'
                % table, self.src)
            if m:
                with self.subTest(table=table):
                    self.assertEqual(int(m.group(1)), cols,
                                     f"{table} insert binds {m.group(1)} "
                                     f"values but has {cols} columns")


class RankCorrelation(unittest.TestCase):
    """The ruler every verdict in this project is read from."""

    def test_rho_does_not_depend_on_row_order(self):
        """Ties broken by input order let the export's points-DESC row order
        push form-based rho negative. Shuffling rows must not move the answer."""
        import random
        rng = random.Random(7)
        pred = [rng.choice([0.5, 1.0, 1.0, 2.0, 3.5]) for _ in range(120)]
        act = [rng.choice([0, 1, 1, 2, 2, 2, 3, 6, 8]) for _ in range(120)]
        base = E._spearman(pred, act)
        idx = list(range(120))
        for _ in range(25):
            rng.shuffle(idx)
            self.assertAlmostEqual(
                E._spearman([pred[i] for i in idx], [act[i] for i in idx]),
                base, places=12, msg="rho changed when only the row order did")

    def test_verdict_reads_the_interval_not_just_the_size(self):
        """+0.151 on 224 players was labelled 'noise' though its interval
        excludes zero; a large rho on a handful of players is the reverse."""
        self.assertIn("below the +0.20 bar", E._rho_verdict(0.151, 224))
        self.assertIn("indistinguishable", E._rho_verdict(0.30, 20))
        self.assertIn("indistinguishable", E._rho_verdict(-0.05, 224))

    def test_tied_values_share_their_average_rank(self):
        # ranks of [1, 2, 2, 3] are [0, 1.5, 1.5, 3]: hand-computed rho 3/sqrt(10)
        self.assertAlmostEqual(E._spearman([1, 2, 2, 3], [1, 2, 3, 4]),
                               3 / 10 ** 0.5, places=12)


class Grading(unittest.TestCase):
    """Who gets graded. A forecast that is never scored can never be wrong."""

    @staticmethod
    def _log(d, players, predicted=4.0):
        return [{"made_at": "x", "source": "xg", "event": str(d["gameweek"]),
                 "player_id": str(p["id"]), "web_name": p["web_name"],
                 "predicted": str(predicted)} for p in players]

    @staticmethod
    def _drop_rows(d, names, event):
        d["player_gw_recent"] = [r for r in d["player_gw_recent"]
                                 if not (r["web_name"] in names
                                         and r["event"] == event)]

    @staticmethod
    def _blank(d, team, event):
        d["fixtures_played"] = [f for f in d["fixtures_played"]
                                if not (f["event"] == event
                                        and team in (f["home"], f["away"]))]

    def test_benched_player_is_graded_as_zero(self):
        d = make_export()
        gw, p = d["gameweek"], d["all_players"][5]
        self._drop_rows(d, {p["web_name"]}, gw)
        graded, _ = E.grade_forecasts(d, self._log(d, [p], 4.0))
        self.assertEqual(graded[("xg", gw)], [(4.0, 0)],
                         "a benched player's forecast was skipped, not graded")

    def test_true_blank_is_not_graded(self):
        d = make_export()
        gw, p = d["gameweek"], d["all_players"][5]
        self._drop_rows(d, {p["web_name"]}, gw)
        self._blank(d, p["team"], gw)
        graded, _ = E.grade_forecasts(d, self._log(d, [p]))
        self.assertNotIn(("xg", gw), graded,
                         "a team with no fixture was graded as if benched")

    def test_players_sharing_a_web_name_are_graded_separately(self):
        """17 web_names are shared this season. Keyed by name, both players'
        points were summed and each forecast graded against the total."""
        d = make_export()
        gw = d["gameweek"]
        ids = {p["web_name"]: p["id"] for p in d["all_players"]}
        for r in d["player_gw_recent"]:
            r["player_id"] = ids[r["web_name"]]
        a, b = d["all_players"][3], d["all_players"][4]
        for r in d["player_gw_recent"]:
            if r["web_name"] == b["web_name"]:
                r["web_name"] = a["web_name"]
        b["web_name"] = a["web_name"]
        pts = sorted(sum(r["pts"] for r in d["player_gw_recent"]
                         if r["player_id"] == pid and r["event"] == gw)
                     for pid in (a["id"], b["id"]))
        self.assertNotEqual(pts[0], pts[1], "fixture cannot tell them apart")
        graded, _ = E.grade_forecasts(d, self._log(d, [a, b]))
        self.assertEqual(sorted(x for _, x in graded[("xg", gw)]), pts,
                         "two players sharing a name were graded on their sum")

    def test_backtest_keeps_benched_players_and_drops_blanks(self):
        d = make_export()
        gw = d["gameweek"]
        benched, blanked = d["all_players"][5], d["all_players"][8]
        self.assertNotEqual(benched["team"], blanked["team"])
        self._drop_rows(d, {benched["web_name"], blanked["web_name"]}, gw)
        self._blank(d, blanked["team"], gw)
        pop = {p["web_name"]: p
               for p in E.backtest_population(d, list(range(1, gw)), gw)}
        self.assertIn(benched["web_name"], pop, "benched player dropped")
        self.assertEqual(pop[benched["web_name"]]["actual"], 0)
        self.assertNotIn(blanked["web_name"], pop, "a blank was graded as 0")


class RestDays(unittest.TestCase):
    """BACKLOG A1: a calendar fact, labelled as one."""

    def test_rest_counts_from_the_previous_pl_kickoff(self):
        d = make_export()   # GW3 kicked off 2026-08-23, GW4 2026-09-14
        self.assertEqual(
            E.days_since_last_pl_match(d, TEAMS[0], d["gameweek"] + 1), 22)

    def test_short_turnaround_is_measured(self):
        d = make_export()
        nxt = d["gameweek"] + 1
        f = next(f for f in d["fixtures_next6"]
                 if f["event"] == nxt and TEAMS[0] in (f["home"], f["away"]))
        f["kickoff_time"] = "2026-08-26T19:45:00Z"   # Tuesday after Saturday
        self.assertEqual(E.days_since_last_pl_match(d, TEAMS[0], nxt), 3)

    def test_brief_states_the_limits_of_rest_days(self):
        out = run("brief", make_export())
        self.assertIn("rest", out)
        self.assertIn("not a fatigue measure", out)


def _p1_world():
    """Four teams, one fixture a week each. GW1-3 in the pre export, GW4-5
    results in the post export. Each player pins one reading of the rules."""
    def fx(ev, h, a):
        return {"event": ev, "home": h, "away": a, "h_goals": 1, "a_goals": 0,
                "h_fdr": 3, "a_fdr": 3, "kickoff_time": None}
    pairs = (("AAA", "BBB"), ("CCC", "DDD"))
    pre_fx = [fx(ev, h, a) for ev in (1, 2, 3) for h, a in pairs]
    post_fx = pre_fx + [fx(ev, h, a) for ev in (4, 5) for h, a in pairs]
    spec = {        # id: (team, GW1-3 minutes, GW4 minutes, GW5 minutes)
        1: ("AAA", 270, 90, 90),   # nailed: unflagged, never blanks
        2: ("AAA", 180, 0, 90),    # exactly on the boundary: flagged; benched GW4
        3: ("BBB", 181, 90, 90),   # one minute over: unflagged
        4: ("BBB", 180, 60, 60),   # the 60-minute substitute: flagged, never blanks
        5: ("CCC", 0, 90, 90),     # no GW1-3 minutes: predictor undefined
        6: ("DDD", 270, 90, 0),    # nailed, benched GW5: unflagged, blanks
    }
    pre = {"gameweek": 3, "fixtures_played": pre_fx,
           "all_players": [{"id": i, "team": t, "mins_last4": m}
                           for i, (t, m, _, _) in spec.items()]}
    # post-time minutes are absurd on purpose: if they leak, nobody is flagged
    post = {"gameweek": 5, "fixtures_played": post_fx,
            "all_players": [{"id": i, "team": t, "mins_last4": 999}
                            for i, (t, _, _, _) in spec.items()],
            "player_gw_recent": [
                {"event": ev, "player_id": i, "web_name": f"P{i}", "mins": m,
                 "pts": 2}
                for i, (_, _, m4, m5) in spec.items()
                for ev, m in ((4, m4), (5, m5)) if m > 0]}
    log = [{"source": "xg", "event": "4", "player_id": str(i)} for i in spec]
    return pre, post, log


class P1Evaluation(unittest.TestCase):
    """The frozen P1 evaluation. Each test pins one reading that could
    otherwise be chosen after the result was visible."""

    @staticmethod
    def _by_id(r):
        return {p["id"]: p for p in r["players"]}

    def test_newcombe_matches_the_published_example(self):
        # Newcombe (1998) example: 56/70 vs 48/80, hybrid score: 0.0524 to 0.3339
        d, lo, hi = P1.newcombe(56, 70, 48, 80)
        self.assertAlmostEqual(d, 0.2, places=12)
        self.assertAlmostEqual(lo, 0.0524, places=4)
        self.assertAlmostEqual(hi, 0.3339, places=4)

    def test_interval_does_not_collapse_on_empty_cells(self):
        """The normal approximation gives 0 +- 0 for 0/20 vs 0/30: certainty
        from no events. A thin cell must widen the interval, not erase it."""
        _, lo, hi = P1.newcombe(0, 20, 0, 30)
        self.assertLess(lo, -0.05)
        self.assertGreater(hi, 0.05)

    def test_benched_is_a_blank_but_a_blank_team_drops_the_player(self):
        pre, post, log = _p1_world()
        self.assertTrue(self._by_id(P1.evaluate(pre, post, log))[2]["blank"],
                        "no minutes while his team played must be a blank")
        post["fixtures_played"] = [
            f for f in post["fixtures_played"]
            if not (f["event"] == 5 and "DDD" in (f["home"], f["away"]))]
        r = P1.evaluate(pre, post, log)
        self.assertNotIn(6, self._by_id(r), "a team with no fixture read as a blank")
        self.assertIn(6, r["dropped"][P1.DROP_FIXTURE])

    def test_no_prior_minutes_is_dropped_not_read_as_zero(self):
        r = P1.evaluate(*_p1_world())
        self.assertNotIn(5, self._by_id(r))
        self.assertIn(5, r["dropped"][P1.DROP_PREDICTOR])

    def test_boundary_is_inclusive(self):
        by = self._by_id(P1.evaluate(*_p1_world()))
        self.assertTrue(by[2]["flag"], "180 of 270 must be flagged")
        self.assertFalse(by[3]["flag"], "181 of 270 must not be")

    def test_predictor_comes_from_gw1_3_only(self):
        """The GW5-time window spans GW1-4 and contains GW4's outcome."""
        self.assertTrue(self._by_id(P1.evaluate(*_p1_world()))[4]["flag"])
        with self.assertRaises(ValueError):
            P1.predictor(_p1_world()[1])

    def test_the_60_minute_substitute_is_counted_as_a_cost(self):
        """Flagged at 180 (60 a game), never blanks, never plays every minute.
        'Every available minute' alone would hide him."""
        r = P1.evaluate(*_p1_world())
        p = self._by_id(r)[4]
        self.assertTrue(p["flag"] and not p["blank"] and not p["full"])
        self.assertGreater(r["cost"]["flagged_did_not_blank"],
                           r["cost"]["flagged_every_minute"])

    def test_post_export_without_ids_is_refused(self):
        pre, post, log = _p1_world()
        for row in post["player_gw_recent"]:
            del row["player_id"]
        with self.assertRaises(ValueError):
            P1.evaluate(pre, post, log)

    def test_thin_cells_and_the_power_caveat_are_printed(self):
        out = P1.report(P1.evaluate(*_p1_world()))
        self.assertIn("thin cell", out)
        self.assertIn("UNPROVEN, not disproven", out)

    def test_a_screen_pointing_the_wrong_way_is_a_fail_not_unproven(self):
        pre, post, log = _p1_world()
        pre["all_players"], post["all_players"] = [], []
        post["player_gw_recent"], log[:] = [], []
        for i in range(60):
            pid, flagged = 100 + i, i < 30
            team = ("AAA", "BBB", "CCC", "DDD")[i % 4]
            pre["all_players"].append({"id": pid, "team": team,
                                       "mins_last4": 90 if flagged else 270})
            post["all_players"].append({"id": pid, "team": team})
            log.append({"source": "xg", "event": "4", "player_id": str(pid)})
            if flagged:                 # flagged all play, unflagged all benched
                for ev in (4, 5):
                    post["player_gw_recent"].append(
                        {"event": ev, "player_id": pid, "mins": 90, "pts": 2})
        self.assertTrue(P1.evaluate(pre, post, log)["verdict"]
                        .startswith("FAIL - inverted"))


class OwnModelAtGW18(unittest.TestCase):
    """BACKLOG G3. The first blanks and doubles land around GW18; by then the
    log rows are frozen, so the own branch must already handle them."""

    @staticmethod
    def _record(source, **kw):
        from datetime import datetime, timedelta, timezone
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "log.csv")
            d = make_export(gw=17, **kw)
            when = datetime.now(timezone.utc) + timedelta(days=3)
            for f in d["fixtures_next6"]:
                if f["event"] == d["gameweek"] + 1:
                    f["kickoff_time"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
            with redirect_stdout(io.StringIO()):
                E.record_projections(d, 6, source, None, path)
            return d, {r["web_name"]: float(r["predicted"])
                       for r in E.read_log(path)}
        finally:
            shutil.rmtree(tmp)

    def test_own_model_skips_a_blank(self):
        d, logged = self._record("own", blank_team="HUL")
        hull = {p["web_name"] for p in d["all_players"] if p["team"] == "HUL"}
        self.assertTrue(logged, "nothing logged at all")
        self.assertFalse(hull & set(logged),
                         "own model forecast a team with no fixture")

    def test_own_model_sums_a_double(self):
        _, one = self._record("own")
        _, two = self._record("own", double_team=TEAMS[0])
        on_team = {p["web_name"] for p in make_export(gw=17)["all_players"]
                   if p["team"] == TEAMS[0]}
        names = sorted(on_team & set(one) & set(two))
        self.assertTrue(names, "no logged player on the doubled team")
        for nm in names:
            self.assertGreater(two[nm], one[nm] * 1.5,
                               f"{nm}: own model did not sum both fixtures")


class ExportGrain(unittest.TestCase):
    """player_gw holds one GAMEWEEK total per player. The export must too."""

    def test_double_gameweek_exports_one_row_per_player(self):
        """The fixtures join fanned a double out to two rows, each carrying the
        whole gameweek's points: 12 real points graded as 24."""
        import sqlite3
        ns = {}
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "fpl_sync.py"), encoding="utf-8").read()
        exec(compile(src.split("def main()")[0], "fpl_sync", "exec"), ns)
        db = sqlite3.connect(":memory:")
        db.executescript(ns["SCHEMA"])
        db.executemany("INSERT INTO teams (id,name,short_name,strength) "
                       "VALUES (?,?,?,3)", [(1, "A", "AAA"), (2, "B", "BBB"),
                                            (3, "C", "CCC")])
        db.execute("INSERT INTO players (id,web_name,team_id,position,now_cost)"
                   " VALUES (10,'Doubler',1,3,60)")
        db.executemany("INSERT INTO fixtures (id,event,team_h,team_a,"
                       "team_h_difficulty,team_a_difficulty,finished) "
                       "VALUES (?,?,?,?,2,4,1)",
                       [(1, 1, 1, 2), (2, 1, 3, 1), (3, 2, 1, 3)])
        db.executemany("INSERT INTO player_gw (player_id,event,minutes,"
                       "total_points) VALUES (?,?,?,?)",
                       [(10, 1, 180, 12), (10, 2, 90, 5)])
        tmp = tempfile.mkdtemp()
        cwd = os.getcwd()
        try:
            os.chdir(tmp)
            with redirect_stdout(io.StringIO()):
                ns["export"](db, 2)
            rows = E.load("fpl_export_gw2.json")["player_gw_recent"]
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp)
        gw1 = [r for r in rows if r["event"] == 1]
        self.assertEqual(len(gw1), 1, "a double gameweek exported twice")
        self.assertEqual(gw1[0]["pts"], 12)
        self.assertIsNone(gw1[0]["fdr"],
                          "a gameweek total was attributed to one of two matches")
        gw2 = next(r for r in rows if r["event"] == 2)
        self.assertEqual((gw2["fdr"], gw2["player_id"]), (2, 10))


def _hist_folder(tmp, extra_rows=()):
    """A tiny vaastav-shaped season: two teams, one duplicated row, one double
    gameweek."""
    os.makedirs(os.path.join(tmp, "gws"), exist_ok=True)
    def write(name, rows, cols):
        with open(os.path.join(tmp, name), "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    write("teams.csv",
          [{"id": "1", "name": "Alpha", "short_name": "ALP"},
           {"id": "2", "name": "Beta", "short_name": "BET"}],
          ["id", "name", "short_name"])
    fixtures = [{"id": "1", "event": "1", "team_h": "1", "team_a": "2",
                 "team_h_score": "1", "team_a_score": "0"},
                {"id": "2", "event": "2", "team_h": "2", "team_a": "1",
                 "team_h_score": "2", "team_a_score": "2"},
                {"id": "3", "event": "3", "team_h": "1", "team_a": "2",
                 "team_h_score": "0", "team_a_score": "0"},
                {"id": "4", "event": "3", "team_h": "2", "team_a": "1",
                 "team_h_score": "3", "team_a_score": "1"}]
    write("fixtures.csv", fixtures,
          ["id", "event", "team_h", "team_a", "team_h_score", "team_a_score"])
    cols = ["element", "name", "position", "team", "round", "fixture",
            "opponent_team", "was_home", "minutes", "starts", "total_points",
            "expected_goals", "expected_assists", "bps", "defensive_contribution"]
    def row(el, rnd, fixture, opp, home, mins, pts):
        return {"element": str(el), "name": f"Player {el}", "position": "MID",
                "team": "Alpha", "round": str(rnd), "fixture": str(fixture),
                "opponent_team": str(opp), "was_home": str(home), "minutes": str(mins),
                "starts": "1", "total_points": str(pts), "expected_goals": "0.10",
                "expected_assists": "0.20", "bps": "20",
                "defensive_contribution": "8"}
    rows = [row(10, 1, 1, 2, True, 90, 5),
            row(10, 1, 1, 2, True, 90, 5),          # verbatim duplicate
            row(10, 2, 2, 2, False, 80, 2),
            row(10, 3, 3, 2, True, 90, 6),          # double gameweek, match 1
            row(10, 3, 4, 2, False, 45, 1),         # double gameweek, match 2
            row(11, 1, 1, 2, True, 20, 1)]
    rows.extend(extra_rows)
    write(os.path.join("gws", "merged_gw.csv"), rows, cols)
    return tmp


def _canon(rows, extra_players=()):
    """A canonical slice built straight from row dicts, for harness tests."""
    players = {r["player_id"]: {"player_id": r["player_id"], "name": f"P{r['player_id']}",
                                "pos": 3, "team": "ALP", "chance_next_round": None}
               for r in rows}
    for pid in extra_players:
        players[pid] = {"player_id": pid, "name": f"P{pid}", "pos": 3,
                        "team": "ALP", "chance_next_round": None}
    full = [dict({"starts": 1, "pts": 0, "xg": 0.0, "xa": 0.0, "bps": 0,
                  "defcon": 0, "n_fixtures": 1, "fixtures": []}, **r) for r in rows]
    return E.check_canonical({"source": "test", "season": "test", "through_gw":
                              max(r["event"] for r in full), "players": players,
                              "rows": full, "team_matches": [], "notes": []})


class CanonicalContract(unittest.TestCase):
    """One shape, two adapters. If they drift apart, the model reads zeros from
    one source and reports a finding instead of failing."""

    def test_both_adapters_emit_the_same_contract(self):
        live = E.canonical_from_export(make_export())
        tmp = tempfile.mkdtemp()
        try:
            hist = H.canonical_from_vaastav(_hist_folder(tmp), "2025/26")
        finally:
            shutil.rmtree(tmp)
        self.assertEqual(set(live), set(hist))
        self.assertEqual(set(live), set(E.CANONICAL_FIELDS))
        self.assertEqual(set(live["rows"][0]), set(hist["rows"][0]))
        self.assertEqual(set(live["rows"][0]), set(E.CANONICAL_ROW_FIELDS))
        self.assertEqual(set(next(iter(live["players"].values()))),
                         set(next(iter(hist["players"].values()))))
        self.assertEqual(set(live["team_matches"][0]), set(hist["team_matches"][0]))
        # a player present in both sources: same structure, both usable
        pid_live = live["rows"][0]["player_id"]
        pid_hist = hist["rows"][0]["player_id"]
        self.assertEqual(set(live["rows"][0]) ^ set(hist["rows"][0]), set())
        self.assertIsInstance(pid_live, int)
        self.assertIsInstance(pid_hist, int)

    def test_check_canonical_rejects_a_renamed_field(self):
        c = E.canonical_from_export(make_export())
        c["rows"][0]["expected_goals"] = c["rows"][0].pop("xg")
        with self.assertRaises(ValueError):
            E.check_canonical(c)

    def test_export_without_ids_is_refused(self):
        d = make_export()
        for r in d["player_gw_recent"]:
            del r["player_id"]
        with self.assertRaises(ValueError):
            E.canonical_from_export(d)


class HistoricalAdapter(unittest.TestCase):

    def _canon(self, **kw):
        tmp = tempfile.mkdtemp()
        try:
            return H.canonical_from_vaastav(_hist_folder(tmp, **kw), "2025/26")
        finally:
            shutil.rmtree(tmp)

    def test_dedup_is_loud_and_names_the_player(self):
        """A silent de-dup that started dropping real rows after an upstream
        change would be invisible."""
        c = self._canon()
        note = "\n".join(c["notes"])
        self.assertIn("removed 1 repeated", note)
        self.assertIn("element 10", note)

    def test_duplicate_row_is_not_counted_twice(self):
        c = self._canon()
        gw1 = next(r for r in c["rows"] if r["player_id"] == 10 and r["event"] == 1)
        self.assertEqual((gw1["minutes"], gw1["pts"], gw1["n_fixtures"]), (90, 5, 1))

    def test_double_gameweek_survives_deduplication(self):
        """(element, round) would have deleted it; (element, fixture) keeps it."""
        c = self._canon()
        gw3 = next(r for r in c["rows"] if r["player_id"] == 10 and r["event"] == 3)
        self.assertEqual(gw3["n_fixtures"], 2)
        self.assertEqual((gw3["minutes"], gw3["pts"]), (135, 7))
        self.assertEqual(sorted(f["fixture_id"] for f in gw3["fixtures"]), ["3", "4"])

    def test_missing_file_stops_rather_than_substituting(self):
        tmp = tempfile.mkdtemp()
        try:
            _hist_folder(tmp)
            os.remove(os.path.join(tmp, "teams.csv"))
            with self.assertRaises(FileNotFoundError):
                H.canonical_from_vaastav(tmp)
        finally:
            shutil.rmtree(tmp)


class Reliability(unittest.TestCase):

    @staticmethod
    def _season(rate_of, gws=8, players=10):
        rows = []
        for pid in range(1, players + 1):
            for ev in range(1, gws + 1):
                rows.append({"player_id": pid, "event": ev, "minutes": 90,
                             "xg": rate_of(pid, ev), "pts": 2})
        return _canon(rows)

    def test_split_is_odd_even_not_first_half_second_half(self):
        """Half the players improve after GW4 and half decline, by the same
        amount, so each player's odd and even totals agree while his first and
        second halves disagree. Odd/even measures the player; first/second
        would measure the trend."""
        trend = lambda pid: 5 if pid % 2 == 0 else -5
        c = self._season(lambda pid, ev: 10 * pid + trend(pid) * (1 if ev > 4 else -1))
        r = E.measure_reliability(c, metrics=("xg",))["xg"]
        self.assertGreater(r["r_half"], 0.9,
                           "odd/even halves disagree - wrong split?")
        # the same data split first-half against second-half does not agree
        first, second = [], []
        for pid in range(1, 11):
            first.append(10 * pid - trend(pid))
            second.append(10 * pid + trend(pid))
        self.assertLess(E._spearman(first, second), r["r_half"],
                        "fixture cannot tell the two splits apart")

    def test_constant_metric_is_undefined_not_zero(self):
        c = self._season(lambda pid, ev: 0.5)
        r = E.measure_reliability(c, metrics=("xg",))["xg"]
        self.assertTrue(r["undefined"])
        self.assertIsNone(r["r_half"])
        # the guard, not the correlation, produced that
        self.assertEqual(E._spearman([1, 1, 1, 1], [2, 3, 4, 5]), 0.0)

    def test_minutes_is_not_measured_per_90(self):
        """Per 90 it divides minutes by minutes: the same constant for everyone.
        It is totalled per half over the whole population instead, with players
        who never featured counted as zero."""
        rows = [{"player_id": pid, "event": ev, "minutes": 90 if ev <= pid else 0,
                 "xg": 0.1 * pid, "pts": 2}
                for pid in range(1, 11) for ev in range(1, 9)]
        c = _canon(rows, extra_players=(99,))     # 99 never features at all
        r = E.measure_reliability(c, metrics=("minutes",))["minutes"]
        self.assertFalse(r["undefined"], "minutes measured per 90 and vanished")
        self.assertGreater(r["r_half"], 0.5)
        # a player who features in one half only is counted as zero in the other
        odd_only = [x for x in rows if x["player_id"] == 1]
        self.assertTrue(all(x["minutes"] == 0 for x in odd_only if x["event"] > 1))
        self.assertIn(1, [p for p in c["players"]])

    def test_minutes_population_is_an_explicit_choice(self):
        """Never-featuring players are a block of identical zeros that agrees
        with itself; including them lifted GW1-4 from 0.777 to 0.873."""
        rows = [{"player_id": pid, "event": ev, "minutes": 90 if ev <= pid else 0,
                 "xg": 0.1 * pid, "pts": 2}
                for pid in range(1, 11) for ev in range(1, 9)]
        c = _canon(rows, extra_players=(99,))
        appeared = E.measure_reliability(c, metrics=("minutes",))["minutes"]
        everyone = E.measure_reliability(c, metrics=("minutes",),
                                         population="all")["minutes"]
        self.assertEqual((appeared["n"], everyone["n"]), (10, 11))
        with self.assertRaises(ValueError):
            E.measure_reliability(c, metrics=("minutes",), population="featured")

    def test_spearman_brown_lifts_the_half_correlation(self):
        import random
        rng = random.Random(3)          # noisy enough that r_half is not 1.0
        c = self._season(lambda pid, ev: pid + rng.uniform(0, 60), players=30)
        r = E.measure_reliability(c, metrics=("xg",))["xg"]
        self.assertTrue(0.1 < r["r_half"] < 0.95,
                        f"fixture is degenerate: r_half {r['r_half']}")
        self.assertAlmostEqual(r["r_full"], 2 * r["r_half"] / (1 + r["r_half"]),
                               places=12)
        self.assertGreater(r["r_full"], r["r_half"])
        self.assertAlmostEqual(r["ci"], 1.96 / (r["n"] - 1) ** 0.5, places=12)


class MinutesBaseline(unittest.TestCase):
    """BUILD_SPEC 3.1: P(start) alone is the bar every model must clear."""

    @staticmethod
    def _record(source, gw=3, **kw):
        from datetime import datetime, timedelta, timezone
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "log.csv")
            d = make_export(gw=gw, **kw)
            when = datetime.now(timezone.utc) + timedelta(days=3)
            for f in d["fixtures_next6"]:
                if f["event"] == d["gameweek"] + 1:
                    f["kickoff_time"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
            with redirect_stdout(io.StringIO()):
                E.record_projections(d, 6, source, None, path)
            return d, {r["web_name"]: float(r["predicted"]) for r in E.read_log(path)}
        finally:
            shutil.rmtree(tmp)

    def test_logged_value_is_start_probability_and_nothing_else(self):
        d, logged = self._record("minutes")
        gws = d["gameweek"]
        for p in d["all_players"]:
            if p["web_name"] in logged:
                expected = E.start_probability(p, gws)
                self.assertAlmostEqual(logged[p["web_name"]], round(expected, 3),
                                       places=6,
                                       msg=f"{p['web_name']} carries more than P(start)")

    def test_injury_doubt_scales_it(self):
        d = make_export()
        doubtful = [p for p in d["all_players"]
                    if p.get("chance_next_round") == 50]
        self.assertTrue(doubtful, "fixture has no doubtful player")
        for p in doubtful:
            full = dict(p, chance_next_round=None)
            self.assertAlmostEqual(E.start_probability(p, d["gameweek"]),
                                   E.start_probability(full, d["gameweek"]) * 0.5,
                                   places=12)

    def test_blank_gameweek_gets_no_baseline_forecast(self):
        d, logged = self._record("minutes", gw=17, blank_team="HUL")
        hull = {p["web_name"] for p in d["all_players"] if p["team"] == "HUL"}
        self.assertTrue(logged, "nothing logged at all")
        self.assertFalse(hull & set(logged), "forecast a team with no fixture")

    def test_double_gameweek_counts_twice(self):
        _, one = self._record("minutes", gw=17)
        _, two = self._record("minutes", gw=17, double_team=TEAMS[0])
        on_team = {p["web_name"] for p in make_export(gw=17)["all_players"]
                   if p["team"] == TEAMS[0]}
        names = sorted(on_team & set(one) & set(two))
        self.assertTrue(names, "no logged player on the doubled team")
        for nm in names:
            self.assertGreater(two[nm], one[nm] * 1.5, f"{nm}: double not counted")

    def test_all_four_sources_log_side_by_side(self):
        from datetime import datetime, timedelta, timezone
        tmp = tempfile.mkdtemp()
        try:
            path = os.path.join(tmp, "log.csv")
            d = make_export()
            when = datetime.now(timezone.utc) + timedelta(days=3)
            for f in d["fixtures_next6"]:
                if f["event"] == d["gameweek"] + 1:
                    f["kickoff_time"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
            with redirect_stdout(io.StringIO()):
                for s in ("own", "xg", "minutes"):
                    E.record_projections(d, 6, s, None, path)
            self.assertEqual({r["source"] for r in E.read_log(path)},
                             {"own", "xg", "minutes"})
        finally:
            shutil.rmtree(tmp)


def _model_world(gws=8):
    """Two clubs, every position, one never-starter, alternating results."""
    spec = {   # pid: (pos, team, xg/gw, xa/gw, defcon/gw, starts)
        1: (1, "ALP", 0.0, 0.0, 0, 1), 2: (2, "ALP", 0.10, 0.10, 12, 1),
        3: (2, "ALP", 0.05, 0.05, 6, 1), 4: (3, "ALP", 0.30, 0.20, 10, 1),
        5: (3, "ALP", 0.20, 0.30, 14, 1), 6: (4, "ALP", 0.50, 0.10, 3, 1),
        7: (4, "ALP", 0.40, 0.20, 2, 1), 8: (1, "BET", 0.0, 0.0, 0, 1),
        9: (2, "BET", 0.15, 0.05, 11, 1), 10: (3, "BET", 0.25, 0.25, 9, 1),
        11: (4, "BET", 0.45, 0.15, 4, 1), 12: (3, "BET", 0.10, 0.10, 13, 0),
    }
    rows, players, matches = [], {}, []
    for pid, (pos, team, xg, xa, dc, st) in spec.items():
        players[pid] = {"player_id": pid, "name": f"P{pid}", "pos": pos,
                        "team": team, "chance_next_round": None}
        for ev in range(1, gws + 1):
            jitter = ((pid * 7 + ev * 3) % 5) * 0.02
            rows.append({"player_id": pid, "event": ev, "minutes": 90 if st else 20,
                         "starts": st, "pts": 2 + (pid + ev) % 5, "xg": xg + jitter,
                         "xa": xa, "bps": 10, "defcon": dc + ev % 2,
                         "n_fixtures": 1, "fixtures": []})
    for ev in range(1, gws + 1):
        ga = 0 if ev % 2 else 2
        matches.append({"event": ev, "team": "ALP", "opponent": "BET", "was_home": True,
                        "goals_for": 1, "goals_against": ga, "fixture_id": None})
        matches.append({"event": ev, "team": "BET", "opponent": "ALP", "was_home": False,
                        "goals_for": ga, "goals_against": 1, "fixture_id": None})
    return E.check_canonical({"source": "test", "season": "t", "through_gw": gws,
                              "players": players, "rows": rows,
                              "team_matches": matches, "notes": []})


class ReliabilityModel(unittest.TestCase):
    """BUILD_SPEC 2. Each test pins one scoring rule or one probability."""

    def setUp(self):
        self.c = _model_world()
        self.inp = E.reliability_inputs(self.c)
        self.fx = [("BET", True)]

    def test_blank_is_none_and_double_is_summed(self):
        self.assertIsNone(E.project_reliability(4, self.inp, []))
        one = E.project_reliability(4, self.inp, self.fx)
        two = E.project_reliability(4, self.inp, self.fx + [("BET", False)])
        self.assertAlmostEqual(two, 2 * one, places=9)

    def test_never_starter_projects_to_zero(self):
        self.assertEqual(self.inp["players"][12]["p_start"], 0.0)
        self.assertEqual(E.project_reliability(12, self.inp, self.fx), 0.0)

    def test_goal_value_depends_on_position(self):
        """Same xGI: a defender's goal is worth 6, a forward's 4."""
        inp = dict(self.inp, weights={"xgi": 1.0, "defcon": 1.0})
        for pid in (2, 6):
            inp["players"][pid]["xgi90"] = 0.5
            inp["players"][pid]["p_start"] = 1.0
        d = E.project_reliability(2, inp, self.fx, terms={"xgi"})
        f = E.project_reliability(6, inp, self.fx, terms={"xgi"})
        self.assertAlmostEqual(d - 2.0, 0.5 * (0.62 * 6 + 0.38 * 3), places=9)
        self.assertAlmostEqual(f - 2.0, 0.5 * (0.62 * 4 + 0.38 * 3), places=9)

    def test_clean_sheet_is_poisson_on_the_opponent_and_zero_for_forwards(self):
        inp = self.inp
        self.assertAlmostEqual(E.project_reliability(6, inp, self.fx, terms={"cs"}),
                               2.0 * inp["players"][6]["p_start"], places=12,
                               msg="a forward has no clean-sheet term")
        weak = dict(inp, teams=dict(inp["teams"], BET={"gc_per_match": 1.0,
                                                       "xg_per_match": 0.5}))
        strong = dict(inp, teams=dict(inp["teams"], BET={"gc_per_match": 1.0,
                                                         "xg_per_match": 3.0}))
        self.assertGreater(E.project_reliability(2, weak, self.fx, terms={"cs"}),
                           E.project_reliability(2, strong, self.fx, terms={"cs"}),
                           "clean-sheet probability must fall as opponent xG rises")
        gc = inp["teams"]["ALP"]["gc_per_match"]
        lam = gc * (inp["teams"]["BET"]["xg_per_match"] / inp["league_xg"])
        cs = E.project_reliability(2, inp, self.fx, terms={"cs"}) - 2.0 * inp["players"][2]["p_start"]
        self.assertAlmostEqual(cs, math.exp(-lam) * 4 * inp["players"][2]["p_start"], places=9)

    def test_shrinkage_uses_the_measured_weight(self):
        """Weight 0: everyone in the position sits on the prior. Weight 1: raw."""
        zero = dict(self.inp, weights={"xgi": 0.0, "defcon": 0.0})
        a = E.project_reliability(2, zero, self.fx, terms={"xgi"})
        b = E.project_reliability(3, zero, self.fx, terms={"xgi"})
        self.assertAlmostEqual(a, b, places=12, msg="weight 0 must ignore the observed rate")
        one = dict(self.inp, weights={"xgi": 1.0, "defcon": 1.0})
        self.assertNotAlmostEqual(E.project_reliability(2, one, self.fx, terms={"xgi"}),
                                  E.project_reliability(3, one, self.fx, terms={"xgi"}))

    def test_defcon_is_logistic_on_the_threshold_and_absent_for_gk_and_fwd(self):
        inp = dict(self.inp, weights={"xgi": 1.0, "defcon": 1.0})
        inp["players"][2]["defcon90"] = 10.0          # exactly on the DEF threshold
        ps = inp["players"][2]["p_start"]
        self.assertAlmostEqual(E.project_reliability(2, inp, self.fx, terms={"defcon"}),
                               2.0 * ps + 2.0 * 0.5 * ps, places=9)
        for pid in (1, 6):
            self.assertAlmostEqual(E.project_reliability(pid, inp, self.fx, terms={"defcon"}),
                                   2.0 * inp["players"][pid]["p_start"], places=12)

    def test_model_has_no_points_term(self):
        doubled = dict(self.c, rows=[dict(r, pts=r["pts"] * 2 + 3) for r in self.c["rows"]])
        inp2 = E.reliability_inputs(doubled)
        for pid in self.c["players"]:
            self.assertEqual(E.project_reliability(pid, self.inp, self.fx),
                             E.project_reliability(pid, inp2, self.fx),
                             f"player {pid}: points reached the projection")

    def test_ablation_starts_from_p_start_alone(self):
        ps = self.inp["players"][4]["p_start"]
        self.assertAlmostEqual(E.project_reliability(4, self.inp, self.fx, terms=frozenset()),
                               2.0 * ps, places=12)


class RollingOrigin(unittest.TestCase):
    """HISTORICAL_VALIDATION 3: nothing from the target week reaches a prediction."""

    def test_target_week_outcomes_do_not_change_predictions(self):
        c = _model_world(gws=8)
        rows_a = {r["pid"]: r for r in E.backtest_week(c, 8)}
        leaky = dict(c, rows=[dict(r, xg=r["xg"] + 5, defcon=r["defcon"] + 30,
                                   pts=r["pts"] + 20, starts=0, minutes=0)
                              if r["event"] == 8 else r for r in c["rows"]])
        rows_b = {r["pid"]: r for r in E.backtest_week(leaky, 8)}
        self.assertEqual(set(rows_a), set(rows_b))
        for pid in rows_a:
            self.assertEqual(rows_a[pid]["preds"], rows_b[pid]["preds"],
                             f"player {pid}: the target week leaked into a prediction")
        self.assertNotEqual(rows_a[4]["actual"], rows_b[4]["actual"])

    def test_benched_is_graded_as_zero_and_a_blank_team_is_dropped(self):
        c = _model_world(gws=8)
        c["rows"] = [r for r in c["rows"] if not (r["player_id"] == 4 and r["event"] == 8)]
        by = {r["pid"]: r for r in E.backtest_week(c, 8)}
        self.assertIn(4, by)
        self.assertEqual((by[4]["actual"], by[4]["featured"]), (0.0, False))
        c["team_matches"] = [m for m in c["team_matches"]
                             if not (m["event"] == 8 and m["team"] == "BET")]
        self.assertNotIn(9, {r["pid"] for r in E.backtest_week(c, 8)})

    def test_every_baseline_and_ablation_stage_is_present(self):
        row = E.backtest_week(_model_world(), 8)[0]
        for k in E.BASELINES + tuple(lbl for lbl, _ in E.ABLATION):
            self.assertIn(k, row["preds"])
        self.assertEqual(row["preds"]["bottomup"], row["preds"]["+defcon"])


class BottomupSource(unittest.TestCase):

    def test_logged_value_is_project_reliability(self):
        d, logged = MinutesBaseline._record("bottomup")
        inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=d["gameweek"])
        tick, _ = E.build_ticker(d, 6)
        checked = 0
        for p in d["all_players"]:
            if p["web_name"] not in logged:
                continue
            fx = [(f[1].split()[0], f[1].endswith("(H)"))
                  for f in tick.get(p["team"], []) if f[0] == d["gameweek"] + 1]
            self.assertAlmostEqual(logged[p["web_name"]],
                                   round(E.project_reliability(p["id"], inp, fx), 3),
                                   places=6)
            checked += 1
        self.assertGreater(checked, 10)

    def test_blank_and_double_gameweeks(self):
        d, logged = MinutesBaseline._record("bottomup", gw=17, blank_team="HUL")
        hull = {p["web_name"] for p in d["all_players"] if p["team"] == "HUL"}
        self.assertTrue(logged and not (hull & set(logged)))
        _, one = MinutesBaseline._record("bottomup", gw=17)
        _, two = MinutesBaseline._record("bottomup", gw=17, double_team=TEAMS[0])
        on = {p["web_name"] for p in make_export(gw=17)["all_players"] if p["team"] == TEAMS[0]}
        names = sorted(on & set(one) & set(two))
        self.assertTrue(names)
        for nm in names:
            self.assertGreater(two[nm], one[nm] * 1.5)


class ReliabilityTable(unittest.TestCase):

    def test_interval_is_capped_at_one(self):
        rel = {"minutes": {"n": 5, "r_half": 0.98, "r_full": 0.99, "ci": 0.1,
                           "weight": 0.99, "undefined": False}}
        out = E.reliability_table(rel)
        self.assertIn("1.000", out)
        self.assertNotIn("1.080", out)


def _graded_world():
    """An export plus a log with one graded gameweek, for calibration tests."""
    d = make_export()
    gw = d["gameweek"]
    log = [{"made_at": "x", "source": "xg", "event": str(gw),
            "player_id": str(p["id"]), "web_name": p["web_name"],
            "predicted": str(2.0 + p["id"] % 5)} for p in d["all_players"][:40]]
    return d, gw, log


def _calibration(d, log):
    tmp = tempfile.mkdtemp()
    try:
        path = os.path.join(tmp, "log.csv")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=E.LOG_FIELDS)
            w.writeheader()
            w.writerows(log)
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_calibration(d, 6, path)
        return buf.getvalue()
    finally:
        shutil.rmtree(tmp)


class SettledGuard(unittest.TestCase):
    """Provisional grades are never recorded: the code refuses, and says why."""

    def test_settled_gameweek_is_graded(self):
        d, gw, log = _graded_world()
        out = _calibration(d, log)
        self.assertNotIn("REFUSED", out)
        self.assertTrue("beats const" in out or "loses" in out, "no verdict printed")
        self.assertRegex(out, r"xg\s+%d\s+40" % gw)

    def test_unfinished_fixture_blocks_grading_and_is_named(self):
        d, gw, log = _graded_world()
        f = next(x for x in d["fixtures_status"] if x["event"] == gw)
        f["finished"] = 0
        out = _calibration(d, log)
        self.assertIn(f"REFUSED GW{gw}", out)
        self.assertIn(f"{f['home']} v {f['away']}", out)
        self.assertNotRegex(out, r"xg\s+%d\s+40" % gw, "graded a provisional gameweek")

    def test_data_checked_zero_blocks_even_when_every_match_is_finished(self):
        """Observed on GW5: fixtures 10/10 finished, event finished = 0 and
        data_checked = 0. `finished` is not the settled signal."""
        d, gw, log = _graded_world()
        next(e for e in d["events"] if e["event"] == gw)["data_checked"] = 0
        out = _calibration(d, log)
        self.assertIn(f"REFUSED GW{gw}", out)
        self.assertIn("data_checked = 0", out)
        self.assertNotRegex(out, r"xg\s+%d\s+40" % gw)

    def test_export_without_flags_is_refused_not_trusted(self):
        d, gw, log = _graded_world()
        del d["events"]
        out = _calibration(d, log)
        self.assertIn("REFUSED", out)
        self.assertIn("re-run fpl_sync.py", out)

    def test_other_gameweeks_are_still_graded(self):
        d, gw, log = _graded_world()
        log += [dict(r, event=str(gw - 1)) for r in log]
        next(e for e in d["events"] if e["event"] == gw)["data_checked"] = 0
        out = _calibration(d, log)
        self.assertIn(f"REFUSED GW{gw}", out)
        self.assertRegex(out, r"xg\s+%d\s+40" % (gw - 1))

    def test_definitions_are_printed_with_the_numbers(self):
        out = _calibration(*[_graded_world()[i] for i in (0, 2)])
        for phrase in ("DEFINITIONS", "tie-corrected", "60+ minutes",
                       "graded as 0 points", "data_checked = 1", "const", "n_st"):
            self.assertIn(phrase, out)

    def test_starters_column_counts_only_sixty_minute_players(self):
        d, gw, log = _graded_world()
        benched = d["all_players"][3]
        for r in d["player_gw_recent"]:
            if r["player_id"] == benched["id"] and r["event"] == gw:
                r["mins"] = 20
        graded, _ = E.grade_forecasts(d, log, detail=True)
        rows = graded[("xg", gw)]
        self.assertEqual(sum(1 for _, _, f in rows if not f), 1)
        self.assertEqual(len(rows), 40)


class SyncExportsSettledFlags(unittest.TestCase):

    def test_export_carries_data_checked_and_unfinished_fixtures(self):
        import sqlite3
        ns = {}
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "fpl_sync.py"), encoding="utf-8").read()
        exec(compile(src.split("def main()")[0], "fpl_sync", "exec"), ns)
        db = sqlite3.connect(":memory:")
        db.executescript(ns["SCHEMA"])
        ns["migrate"](db)
        db.executemany("INSERT INTO teams (id,name,short_name,strength) VALUES (?,?,?,3)",
                       [(1, "A", "AAA"), (2, "B", "BBB")])
        db.executemany("INSERT INTO events (id,name,finished,data_checked) VALUES (?,?,?,?)",
                       [(1, "GW1", 1, 1), (2, "GW2", 1, 0)])   # finished != checked
        db.executemany("INSERT INTO fixtures (id,event,team_h,team_a,team_h_difficulty,"
                       "team_a_difficulty,team_h_score,team_a_score,finished) "
                       "VALUES (?,?,?,?,2,2,?,?,?)",
                       [(1, 1, 1, 2, 1, 0, 1), (2, 2, 2, 1, 2, 2, 0)])
        tmp, cwd = tempfile.mkdtemp(), os.getcwd()
        try:
            os.chdir(tmp)
            with redirect_stdout(io.StringIO()):
                ns["export"](db, 2)
            d = E.load("fpl_export_gw2.json")
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp)
        self.assertEqual({e["event"]: e["data_checked"] for e in d["events"]}, {1: 1, 2: 0})
        self.assertEqual([(f["event"], f["finished"]) for f in d["fixtures_status"]],
                         [(1, 1), (2, 0)], "an unfinished fixture must be visible")
        self.assertEqual(E.gameweek_settled(d, 1), (True, []))
        self.assertFalse(E.gameweek_settled(d, 2)[0])


    def test_bootstrap_stores_data_checked_separately_from_finished(self):
        import sqlite3
        ns = {}
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "fpl_sync.py"), encoding="utf-8").read()
        exec(compile(src.split("def main()")[0], "fpl_sync", "exec"), ns)
        ev = lambda i, fin, chk, cur=False: {
            "id": i, "name": f"GW{i}", "deadline_time": "2026-09-01T00:00:00Z",
            "finished": fin, "data_checked": chk, "is_current": cur}
        ns["get"] = lambda path: {"teams": [], "elements": [],
                                  "events": [ev(4, True, True), ev(5, True, False, True)]}
        db = sqlite3.connect(":memory:")
        db.executescript(ns["SCHEMA"])
        ns["migrate"](db)
        with redirect_stdout(io.StringIO()):
            ns["sync_bootstrap"](db)
        self.assertEqual(db.execute("SELECT id, finished, data_checked FROM events "
                                    "ORDER BY id").fetchall(), [(4, 1, 1), (5, 1, 0)])

    def test_migration_adds_data_checked_to_an_old_database(self):
        import sqlite3
        ns = {}
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "fpl_sync.py"), encoding="utf-8").read()
        exec(compile(src.split("def main()")[0], "fpl_sync", "exec"), ns)
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT, "
                   "deadline_time TEXT, finished INTEGER, average_score INTEGER, "
                   "highest_score INTEGER, most_captained INTEGER)")
        db.executescript(ns["SCHEMA"])
        with redirect_stdout(io.StringIO()):
            ns["migrate"](db)
            ns["migrate"](db)                                  # idempotent
        cols = [r[1] for r in db.execute("PRAGMA table_info(events)")]
        self.assertEqual(cols[-1], "data_checked")
        self.assertEqual(len(cols), 8)


class ExportWindow(unittest.TestCase):
    """The export's per-gameweek rows and fixture flags cover the whole season,
    not a six-gameweek window; the last-4 form columns keep their window."""

    @staticmethod
    def _sync_ns():
        ns = {}
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "fpl_sync.py"), encoding="utf-8").read()
        exec(compile(src.split("def main()")[0], "fpl_sync", "exec"), ns)
        return ns

    def _export_at(self, gw):
        import sqlite3
        ns = self._sync_ns()
        db = sqlite3.connect(":memory:")
        db.executescript(ns["SCHEMA"])
        ns["migrate"](db)
        db.executemany("INSERT INTO teams (id,name,short_name,strength) VALUES (?,?,?,3)",
                       [(1, "A", "AAA"), (2, "B", "BBB")])
        db.execute("INSERT INTO players (id,web_name,team_id,position,now_cost,status,"
                   "total_points,minutes,starts) VALUES (7,'Seven',1,3,50,'a',0,0,0)")
        db.executemany("INSERT INTO events (id,name,finished,data_checked) VALUES (?,?,1,1)",
                       [(ev, f"GW{ev}") for ev in range(1, gw + 1)])
        db.executemany("INSERT INTO fixtures (id,event,team_h,team_a,team_h_difficulty,"
                       "team_a_difficulty,team_h_score,team_a_score,finished) "
                       "VALUES (?,?,1,2,2,2,1,0,1)", [(ev, ev) for ev in range(1, gw + 1)])
        db.executemany("INSERT INTO player_gw (player_id,event,minutes,total_points,starts,"
                       "expected_goals,expected_assists,defensive_contribution) "
                       "VALUES (7,?,90,?,1,0.1,0.1,3)", [(ev, ev % 7) for ev in range(1, gw + 1)])
        tmp, cwd = tempfile.mkdtemp(), os.getcwd()
        try:
            os.chdir(tmp)
            with redirect_stdout(io.StringIO()):
                ns["export"](db, gw)
            return E.load(f"fpl_export_gw{gw}.json")
        finally:
            os.chdir(cwd)
            shutil.rmtree(tmp, ignore_errors=True)

    def test_rows_and_fixture_flags_cover_the_whole_season(self):
        for gw in (8, 10, 20, 38):
            with self.subTest(gw=gw):
                d = self._export_at(gw)
                self.assertEqual(sorted({r["event"] for r in d["player_gw_recent"]}),
                                 list(range(1, gw + 1)), "per-gameweek rows are windowed")
                self.assertEqual(sorted({f["event"] for f in d["fixtures_status"]}),
                                 list(range(1, gw + 1)), "fixture flags are windowed")
                c = E.canonical_from_export(d)
                self.assertEqual(sorted({r["event"] for r in c["rows"]}), list(range(1, gw + 1)))

    def test_last_four_form_columns_keep_their_window(self):
        d = self._export_at(10)
        p = next(p for p in d["all_players"] if p["id"] == 7)
        self.assertEqual(p["mins_last4"], 360)
        self.assertEqual(p["starts_last4"], 4)
        self.assertEqual(p["pts_last4"], sum(ev % 7 for ev in range(7, 11)))


class Shipping(unittest.TestCase):
    """Archive, backup and the Drive copy. Loud, recoverable, never the database."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "work")
        os.makedirs(self.src)
        self.files = []
        for name in ("projection_log.csv", "run_2026-09-21.log"):
            p = os.path.join(self.src, name)
            open(p, "w").write(name)
            self.files.append(p)
        self.drive = os.path.join(self.tmp, "drive", "FPL")
        self.outbox = os.path.join(self.tmp, "outbox")
        self.lines = []

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _ship(self, files=None):
        return SHIP.ship(files or self.files, self.drive, self.outbox, self.lines.append)

    def test_every_file_lands_on_drive_and_gets_a_result_line(self):
        os.makedirs(os.path.dirname(self.drive))            # Drive is mounted
        self.assertEqual(self._ship(), 0)
        self.assertEqual(sorted(os.listdir(self.drive)),
                         ["projection_log.csv", "run_2026-09-21.log"])
        self.assertEqual(sum(1 for l in self.lines if l.startswith("SHIP OK")), 2)

    def test_unmounted_drive_holds_in_outbox_and_the_next_run_delivers(self):
        self.assertEqual(self._ship(), 0)                    # Drive root missing
        self.assertEqual(len(os.listdir(self.outbox)), 2)
        self.assertTrue(any("not mounted" in l for l in self.lines))
        self.assertEqual(sum(1 for l in self.lines if l.startswith("SHIP HELD")), 2)
        os.makedirs(os.path.dirname(self.drive))            # Drive comes back
        late = os.path.join(self.src, "fpl_2026-09-22.txt")
        open(late, "w").write("report")
        self.lines.clear()
        self.assertEqual(self._ship([late]), 0)
        self.assertEqual(sorted(os.listdir(self.drive)),
                         ["fpl_2026-09-22.txt", "projection_log.csv", "run_2026-09-21.log"])
        self.assertEqual(os.listdir(self.outbox), [], "outbox not emptied")
        self.assertEqual(sum(1 for l in self.lines if "held in outbox" in l), 2)

    def test_the_database_is_never_shipped(self):
        os.makedirs(os.path.dirname(self.drive))
        db = os.path.join(self.src, "fpl.sqlite")
        open(db, "w").write("x")
        self.assertEqual(self._ship([db]), 1)
        self.assertFalse(os.path.exists(os.path.join(self.drive, "fpl.sqlite")))
        self.assertTrue(any(l.startswith("SHIP REFUSED") for l in self.lines))

    def test_a_missing_file_is_a_visible_failure(self):
        os.makedirs(os.path.dirname(self.drive))
        self.assertEqual(self._ship([os.path.join(self.src, "nope.txt")]), 1)
        self.assertTrue(any(l.startswith("SHIP FAILED") and "nope.txt" in l
                            for l in self.lines))

    def test_archive_keeps_every_day_and_leaves_the_live_export(self):
        live = os.path.join(self.src, "fpl_export_gw5.json")
        arch = os.path.join(self.tmp, "archive")
        for stamp, body in (("2026-09-20", "sunday"), ("2026-09-21", "monday")):
            open(live, "w").write(body)
            SHIP.archive_export(live, arch, stamp)
        self.assertEqual(sorted(os.listdir(arch)),
                         ["fpl_export_gw5_2026-09-20.json", "fpl_export_gw5_2026-09-21.json"])
        self.assertEqual(open(os.path.join(arch, "fpl_export_gw5_2026-09-20.json")).read(),
                         "sunday", "a later run overwrote an earlier day's inputs")
        self.assertEqual(open(live).read(), "monday")
        self.assertEqual(os.path.basename(SHIP.newest_export(self.src)),
                         "fpl_export_gw5.json")

    def test_backup_keeps_the_last_seven(self):
        import sqlite3
        db = os.path.join(self.src, "fpl.sqlite")
        con = sqlite3.connect(db)
        con.execute("create table t (x)")
        con.execute("insert into t values (42)")
        con.commit()
        con.close()
        bdir = os.path.join(self.tmp, "backup")
        for day in range(10, 20):
            SHIP.backup_db(db, bdir, f"2026-09-{day}")
        kept = sorted(os.listdir(bdir))
        self.assertEqual(len(kept), 7)
        self.assertEqual((kept[0], kept[-1]),
                         ("fpl_2026-09-13.sqlite", "fpl_2026-09-19.sqlite"))
        con = sqlite3.connect(os.path.join(bdir, kept[-1]))
        self.assertEqual(con.execute("select x from t").fetchone()[0], 42)
        con.close()


def _recordable_export(**kw):
    """make_export with next gameweek's kickoffs three days ahead."""
    from datetime import datetime, timedelta, timezone
    d = make_export(**kw)
    when = datetime.now(timezone.utc) + timedelta(days=3)
    for f in d["fixtures_next6"]:
        if f["event"] == d["gameweek"] + 1:
            f["kickoff_time"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    return d


@unittest.skipUnless(os.name == "nt", "reproduces a Windows file lock")
class RecordResilience(unittest.TestCase):
    """19 Sep: Excel held projection_log.csv, four records died, exit code 0."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log = os.path.join(self.tmp, "projection_log.csv")
        with redirect_stdout(io.StringIO()):
            E.record_projections(_recordable_export(), 6, "own", None, self.log)
        self.before = open(self.log, encoding="utf-8").read()
        self.waits, self.held, self.real_sleep = [], None, E._sleep
        E._sleep = self.waits.append

    def tearDown(self):
        E._sleep = self.real_sleep
        if self.held and not self.held.closed:
            self.held.close()
        shutil.rmtree(self.tmp)

    def _record(self, source="minutes"):
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = E.record_status(_recordable_export(), 6, source, None, self.log)
        return result, buf.getvalue()

    def test_locked_log_is_retried_three_times_then_fails_visibly(self):
        self.held = open(self.log, "r")                   # what Excel did
        (ok, n, reason), out = self._record()
        self.assertFalse(ok)
        self.assertEqual(self.waits, [5.0, 5.0, 5.0], "not retried 3 times, 5 s apart")
        self.assertIn("locked", reason)
        self.assertIn("retry 3/3", out)
        self.held.close()
        self.assertEqual(open(self.log, encoding="utf-8").read(), self.before,
                         "a failed write changed the log")
        kept = E.read_log(self.log + ".tmp")
        self.assertTrue(any(r["source"] == "minutes" for r in kept),
                        "the forecasts that could not be written were thrown away")

    def test_lock_released_during_a_wait_is_recovered(self):
        self.held = open(self.log, "r")
        E._sleep = lambda s: (self.waits.append(s), self.held.close())
        (ok, n, reason), _ = self._record()
        self.assertTrue(ok, reason)
        self.assertGreater(n, 0)
        self.assertEqual(self.waits, [5.0])
        self.assertIn("minutes", {r["source"] for r in E.read_log(self.log)})
        self.assertFalse(os.path.exists(self.log + ".tmp"))

    def test_a_write_that_dies_halfway_leaves_the_old_log_intact(self):
        real = E.csv.DictWriter.writerows
        def boom(writer, rows):
            real(writer, list(rows)[:3])
            raise RuntimeError("power cut")
        E.csv.DictWriter.writerows = boom
        try:
            with self.assertRaises(RuntimeError), redirect_stdout(io.StringIO()):
                E.record_status(_recordable_export(), 6, "minutes", None, self.log)
        finally:
            E.csv.DictWriter.writerows = real
        self.assertEqual(open(self.log, encoding="utf-8").read(), self.before,
                         "the log was opened for writing and left half-written")

    def test_deadline_passed_is_ok_not_a_failure(self):
        """It happens after every deadline; crying wolf nightly teaches you to
        ignore the line."""
        with redirect_stdout(io.StringIO()):
            ok, n, reason = E.record_status(make_export(), 6, "minutes", None, self.log)
        self.assertEqual((ok, n), (True, 0))
        self.assertIn("deadline passed", reason)

    def test_zero_rows_with_the_deadline_open_is_a_failure(self):
        d = _recordable_export()
        for p in d["all_players"]:
            p["status"] = "i"
        with redirect_stdout(io.StringIO()):
            ok, n, reason = E.record_status(d, 6, "minutes", None, self.log)
        self.assertEqual((ok, n), (False, 0))
        self.assertIn("deadline has not passed", reason)

    def _cli(self, source):
        cwd, argv = os.getcwd(), sys.argv
        export = os.path.join(self.tmp, "fpl_export_gw3.json")
        with open(export, "w", encoding="utf-8") as fh:
            json.dump(_recordable_export(), fh)
        status = os.path.join(self.tmp, "status.tmp")
        buf, code = io.StringIO(), 0
        try:
            os.chdir(self.tmp)
            sys.argv = ["fpl_edge.py", export, "--record", "--source", source,
                        "--status", status]
            with redirect_stdout(buf):
                try:
                    E.main()
                except SystemExit as e:
                    code = e.code or 0
        finally:
            os.chdir(cwd)
            sys.argv = argv
        lines = open(status, encoding="utf-8").read().splitlines()
        return code, buf.getvalue(), lines

    def test_cli_failure_is_one_visible_line_and_a_nonzero_exit(self):
        self.held = open(self.log, "r")
        code, out, lines = self._cli("minutes")
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("RECORD FAIL minutes "), lines)
        self.assertIn(lines[0], out)

    def test_cli_success_line_carries_the_count(self):
        code, out, lines = self._cli("minutes")
        self.assertEqual(code, 0)
        self.assertRegex(lines[0], r"^RECORD OK minutes [1-9]\d*$")


EDGE_STUB = '''import sys
a = sys.argv[1:]
if "--record" in a:
    src, status = a[a.index("--source") + 1], a[a.index("--status") + 1]
    mode = open("MODE").read().strip()
    if mode == "broken" and src == "xg":
        sys.exit(1)                                   # crashed: no status line
    if mode == "broken" and src == "minutes":
        open(status, "a").write("RECORD FAIL minutes locked\\n")
        sys.exit(1)
    open(status, "a").write("RECORD OK " + src + " 5\\n")
    sys.exit(0)
print("EDGE", " ".join(a))
'''


@unittest.skipUnless(os.name == "nt", "runs fpl_run.bat under cmd.exe")
class BatchRecordCheck(unittest.TestCase):
    """The real fpl_run.bat, with stub scripts around it."""

    def _run(self, mode):
        tmp = tempfile.mkdtemp()
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            shutil.copy(os.path.join(here, "fpl_run.bat"), tmp)
            stubs = {"test_fpl.py": "import sys\nsys.exit(0)\n",
                     "fpl_sync.py": "print('sync ran')\n",
                     "fpl_ship.py": "print('SHIP STUB')\n",
                     "fpl_edge.py": EDGE_STUB, "MODE": mode}
            for name, body in stubs.items():
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write(body)
            # absolute path: cmd does not always search the current directory
            r = subprocess.run(["cmd", "/c", os.path.join(tmp, "fpl_run.bat")],
                               cwd=tmp, timeout=180,
                               capture_output=True, text=True, errors="replace")
            logs = [f for f in os.listdir(os.path.join(tmp, "reports"))
                    if f.startswith("run_")]
            log = open(os.path.join(tmp, "reports", logs[0]), errors="replace").read()
            return r.returncode, [l.strip() for l in log.splitlines()], r.stdout
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_every_source_gets_one_line_and_a_silent_crash_is_caught(self):
        code, log, console = self._run("broken")
        summary = log[log.index("record summary:") + 1:]
        per_source = {s: [l for l in summary if l.startswith(f"RECORD ") and
                          l.split()[2] == s] for s in ("own", "xg", "minutes", "bottomup")}
        self.assertEqual({s: len(v) for s, v in per_source.items()},
                         {"own": 1, "xg": 1, "minutes": 1, "bottomup": 1})
        self.assertEqual(per_source["own"][0], "RECORD OK own 5")
        self.assertEqual(per_source["minutes"][0], "RECORD FAIL minutes locked")
        self.assertTrue(per_source["xg"][0].startswith("RECORD FAIL xg "),
                        "a crash with no status line went unreported")
        self.assertTrue(any(l.startswith("EDGE --diff") for l in log),
                        "a failed record stopped the report")
        self.assertIn("SHIP STUB", log)
        self.assertIn("FINISHED WITH ERRORS", log)
        self.assertNotIn("Done", log)
        self.assertEqual(code, 1, "four failures must not exit 0 again")
        self.assertIn("RECORD FAIL xg", console)

    def test_clean_run_says_done_and_exits_zero(self):
        code, log, _ = self._run("clean")
        self.assertEqual(code, 0)
        self.assertEqual([l for l in log if l.startswith("RECORD ")][-4:],
                         [f"RECORD OK {s} 5" for s in ("own", "xg", "minutes", "bottomup")])
        self.assertIn("Done", log)
        self.assertNotIn("FINISHED WITH ERRORS", log)


class StrandedTmp(unittest.TestCase):
    """A pre-deadline write that failed leaves the only copy of that week's
    forecasts in projection_log.csv.tmp. The next run - after the deadline,
    RECORD OK 0 - must promote it, never overwrite it."""

    FROZEN = [{"made_at": "2026-09-17T21:55:18+00:00", "source": "bottomup",
               "event": "9", "player_id": str(900 + i), "web_name": f"Frozen{i}",
               "predicted": "3.1"} for i in range(5)]

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log = os.path.join(self.tmp, "projection_log.csv")
        self.stranded = self.log + ".tmp"
        with redirect_stdout(io.StringIO()):
            E.record_projections(_recordable_export(), 6, "own", None, self.log)
        self.base = E.read_log(self.log)
        self.real_sleep = E._sleep
        E._sleep = lambda s: None

    def tearDown(self):
        E._sleep = self.real_sleep
        shutil.rmtree(self.tmp)

    def _stage(self, newer=True, cut=False):
        rows = self.base + self.FROZEN
        with open(self.stranded, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=E.LOG_FIELDS)
            w.writeheader()
            w.writerows(rows)
        if cut:                                   # die mid-row, as a crash would
            data = open(self.stranded, encoding="utf-8").read()
            at = data.rfind("\n", 0, len(data) // 2) + 12
            open(self.stranded, "w", encoding="utf-8", newline="").write(data[:at])
        t = os.path.getmtime(self.log) + (60 if newer else -60)
        os.utime(self.stranded, (t, t))
        return rows

    def _frozen_in_log(self):
        return sum(1 for r in E.read_log(self.log) if r["web_name"].startswith("Frozen"))

    def test_newer_tmp_is_promoted_before_a_post_deadline_record(self):
        self._stage()
        buf = io.StringIO()
        with redirect_stdout(buf):
            ok, n, reason = E.record_status(make_export(), 6, "minutes", None, self.log)
        self.assertEqual((ok, n), (True, 0), reason)          # deadline passed
        self.assertIn(f"RECOVERED {len(self.base) + 5} rows", buf.getvalue())
        self.assertEqual(self._frozen_in_log(), 5, "the frozen rows were lost")
        self.assertFalse(os.path.exists(self.stranded))

    def test_promotion_happens_before_a_pre_deadline_record_too(self):
        self._stage()
        with redirect_stdout(io.StringIO()):
            ok, n, reason = E.record_status(_recordable_export(), 6, "minutes", None, self.log)
        self.assertTrue(ok, reason)
        self.assertGreater(n, 0)
        after = E.read_log(self.log)
        self.assertEqual(self._frozen_in_log(), 5)
        self.assertIn("minutes", {r["source"] for r in after})

    def test_older_tmp_is_left_alone(self):
        self._stage(newer=False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.record_status(make_export(), 6, "minutes", None, self.log)
        self.assertNotIn("RECOVERED", buf.getvalue())
        self.assertEqual(E.read_log(self.log), self.base)
        self.assertTrue(os.path.exists(self.stranded))

    def test_truncated_tmp_is_never_promoted_and_never_deleted(self):
        self._stage(cut=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            ok, n, reason = E.record_status(_recordable_export(), 6, "minutes", None, self.log)
        self.assertIn("refusing to promote", buf.getvalue())
        self.assertEqual(self._frozen_in_log(), 0, "junk was promoted over the log")
        self.assertTrue(ok, reason)                            # recording continues
        aside = [f for f in os.listdir(self.tmp) if ".tmp.refused-" in f]
        self.assertEqual(len(aside), 1, "the refused .tmp was not preserved")
        self.assertFalse(os.path.exists(self.stranded))

    @unittest.skipUnless(os.name == "nt", "reproduces a Windows file lock")
    def test_locked_log_blocks_recording_rather_than_clobbering_the_tmp(self):
        rows = self._stage()
        held = open(self.log, "r")
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                ok, n, reason = E.record_status(_recordable_export(), 6, "minutes",
                                                None, self.log)
        finally:
            held.close()
        self.assertFalse(ok)
        self.assertIn("unpromoted", reason)
        self.assertEqual(E.read_log(self.stranded), rows,
                         "the stranded forecasts were overwritten by a new write")
        self.assertEqual(E.read_log(self.log), self.base)


class HorizonTest(unittest.TestCase):
    """The pre-registered horizon test (9b43a78): same training, same
    functions as the single-week backtest, summed over GW t..t+H-1."""

    def test_h1_reproduces_the_single_week_backtest(self):
        c = _model_world(gws=8)
        week = {r["pid"]: r for r in E.backtest_week(c, 6)}
        hz = {r["pid"]: r for r in H.horizon_rows(c, 6, hs=(1,))}
        self.assertEqual(set(week), set(hz))
        for pid in week:
            self.assertAlmostEqual(hz[pid]["H"][1]["bottomup"], week[pid]["preds"]["bottomup"], 12)
            self.assertAlmostEqual(hz[pid]["H"][1]["minutes"], week[pid]["preds"]["minutes"], 12)
            self.assertEqual(hz[pid]["H"][1]["actual"], week[pid]["actual"])

    def test_target_weeks_do_not_leak_into_predictions(self):
        c = _model_world(gws=8)
        a = {r["pid"]: r for r in H.horizon_rows(c, 6, hs=(1, 2))}
        leaky = dict(c, rows=[dict(r, xg=r["xg"] + 5, defcon=r["defcon"] + 30,
                                   pts=r["pts"] + 20, starts=0, minutes=0)
                              if r["event"] >= 6 else r for r in c["rows"]])
        b = {r["pid"]: r for r in H.horizon_rows(leaky, 6, hs=(1, 2))}
        self.assertEqual(set(a), set(b))
        for pid in a:
            for Hn in (1, 2):
                for k in ("bottomup", "minutes"):
                    self.assertEqual(a[pid]["H"][Hn][k], b[pid]["H"][Hn][k],
                                     f"{pid} H={Hn} {k}: the target weeks leaked")
        self.assertNotEqual(a[4]["H"][2]["actual"], b[4]["H"][2]["actual"])

    def test_sums_fixtures_counts_blanks_as_zero_and_excludes_no_fixture_teams(self):
        c = _model_world(gws=8)
        # BET has no fixture in GW6 or GW7; ALP still does (a phantom opponent)
        c["team_matches"] = [m for m in c["team_matches"]
                             if not (m["event"] in (6, 7) and m["team"] == "BET")]
        # player 4 (ALP) is benched in both weeks: no rows, team played
        c["rows"] = [r for r in c["rows"] if not (r["player_id"] == 4 and r["event"] in (6, 7))]
        rows = {r["pid"]: r for r in H.horizon_rows(c, 6, hs=(2,))}
        self.assertNotIn(9, rows, "a team with no fixture in the horizon was kept")
        self.assertIn(4, rows, "a benched player was dropped instead of scored 0")
        self.assertEqual(rows[4]["H"][2]["actual"], 0.0)
        inp = E.reliability_inputs(E.canonical_through(c, 5), gws_played=5)
        fx6 = [(m["opponent"], m["was_home"]) for m in c["team_matches"]
               if m["event"] == 6 and m["team"] == "ALP"]
        fx7 = [(m["opponent"], m["was_home"]) for m in c["team_matches"]
               if m["event"] == 7 and m["team"] == "ALP"]
        self.assertAlmostEqual(rows[4]["H"][2]["bottomup"],
                               E.project_reliability(4, inp, fx6) + E.project_reliability(4, inp, fx7), 12)
        self.assertAlmostEqual(rows[4]["H"][2]["minutes"], inp["players"][4]["p_start"] * 2, 12)

    def test_incomplete_horizon_is_skipped(self):
        c = _model_world(gws=8)
        rows = H.horizon_rows(c, 8, hs=(1, 2))
        self.assertTrue(rows)
        self.assertTrue(all(set(r["H"]) == {1} for r in rows), "GW9 does not exist")

    def test_double_gameweek_counts_twice(self):
        c = _model_world(gws=8)
        extra = [{"event": 6, "team": "ALP", "opponent": "BET", "was_home": False,
                  "goals_for": 0, "goals_against": 0, "fixture_id": None},
                 {"event": 6, "team": "BET", "opponent": "ALP", "was_home": True,
                  "goals_for": 0, "goals_against": 0, "fixture_id": None}]
        one = {r["pid"]: r for r in H.horizon_rows(c, 6, hs=(1,))}
        two = {r["pid"]: r for r in H.horizon_rows(dict(c, team_matches=c["team_matches"] + extra), 6, hs=(1,))}
        self.assertAlmostEqual(two[4]["H"][1]["minutes"], 2 * one[4]["H"][1]["minutes"], 12)
        self.assertGreater(two[4]["H"][1]["bottomup"], 1.5 * one[4]["H"][1]["bottomup"])

    def test_report_prints_both_columns_with_intervals_for_every_h_and_position(self):
        import re
        out = H.horizon_report(_model_world(gws=8), hs=(1, 2), first=5)
        self.assertIn("9b43a78", out)
        num = "[+-][0-9][.][0-9]{3}"                       # e.g. +0.335
        cell = f"{num} {num}[.][.]{num}"                    # rho lo..hi
        for Hn in (1, 2):
            block = out.split(f"H = {Hn} ")[1].split("=" * 78)[1]   # the rows
            for pos in ("ALL", "GK", "DEF", "MID", "FWD"):
                rows = re.findall(f"^ +GW *4-7 +{pos} +[0-9]+ +({cell}) +({cell}) *$",
                                  block, re.M)
                self.assertEqual(len(rows), 1, f"H={Hn} {pos}: expected one row with two rho cells")


def _fifteen(d, prefer=None):
    """A legal 15 from the export, preferring players of `prefer` team."""
    ids = []
    for pos, need in ((1, 2), (2, 5), (3, 5), (4, 3)):
        pool = sorted((p for p in d["all_players"] if p["pos"] == pos),
                      key=lambda p: (p["team"] != prefer, p["id"]))
        ids += [p["id"] for p in pool[:need]]
    return ids


class BenchBoost(unittest.TestCase):
    """--section bench_boost: the frozen three-layer rule on one 15."""

    def test_flag_constant_matches_the_frozen_p1_definition(self):
        self.assertEqual(E.FLAG_SHARE_MAX, P1.FLAG_MAX)

    def test_blank_week_gives_no_forecast(self):
        d = make_export(blank_team="HUL")
        t = E.bench_boost_table(d, _fifteen(d, prefer="HUL"))
        nxt = d["gameweek"] + 1
        week = next(w for w in t["weeks"] if w["event"] == nxt)
        playing = {x for f in d["fixtures_next6"] if f["event"] == nxt
                   for x in (f["home"], f["away"])}
        self.assertNotIn("HUL", playing)
        blank = [r for r in week["rows"] if r["team"] not in playing]
        rest = [r for r in week["rows"] if r["team"] in playing]
        self.assertTrue(blank and rest)
        self.assertTrue(any(r["team"] == "HUL" for r in blank))
        self.assertTrue(all(r["proj"] is None for r in blank), "a blank got a forecast")
        self.assertTrue(all(r["proj"] is not None for r in rest))
        self.assertAlmostEqual(week["total"], sum(r["proj"] for r in rest), 9)

    def test_double_counts_twice(self):
        ids = _fifteen(make_export(), prefer=TEAMS[0])
        one = E.bench_boost_table(make_export(), ids)["weeks"][0]
        two = E.bench_boost_table(make_export(double_team=TEAMS[0]), ids)["weeks"][0]
        pairs = [(a, b) for a, b in zip(one["rows"], two["rows"]) if a["team"] == TEAMS[0]]
        self.assertTrue(pairs)
        for a, b in pairs:
            self.assertGreater(b["proj"], 1.5 * a["proj"], f"{a['name']}: double not counted twice")
            self.assertEqual(len(b["fixtures"]), 2)

    def test_fixture_term_moves_gk_def_and_not_mid_fwd(self):
        """Concede more in the past -> a worse clean-sheet probability. That
        reaches GK and DEF through the Poisson term and must not reach MID or
        FWD, who get bare xGI."""
        d = make_export()
        ids = _fifteen(d, prefer=TEAMS[0])
        base = E.bench_boost_table(d, ids)["weeks"][0]
        leakier = make_export()
        for f in leakier["fixtures_played"]:
            if f["home"] == TEAMS[0]:
                f["a_goals"] += 3
            if f["away"] == TEAMS[0]:
                f["h_goals"] += 3
        moved = E.bench_boost_table(leakier, ids)["weeks"][0]
        for a, b in zip(base["rows"], moved["rows"]):
            if a["team"] != TEAMS[0]:
                continue
            if a["pos"] in (1, 2):
                self.assertLess(b["proj"], a["proj"], f"{a['name']} (GK/DEF) did not move")
            else:
                self.assertEqual(b["proj"], a["proj"], f"{a['name']} (MID/FWD) moved")

    def test_flag_is_the_frozen_inclusive_two_thirds(self):
        d = make_export(gw=3)                       # window of 3, 270 minutes
        ids = _fifteen(d)
        by_id = {p["id"]: p for p in d["all_players"]}
        by_id[ids[2]]["mins_last4"] = 180           # 0.6667 -> flagged (inclusive)
        by_id[ids[3]]["mins_last4"] = 181           # 0.6704 -> not flagged
        rows = {r["id"]: r for r in E.bench_boost_table(d, ids)["weeks"][0]["rows"]}
        self.assertTrue(rows[ids[2]]["flag"])
        self.assertFalse(rows[ids[3]]["flag"])
        self.assertAlmostEqual(rows[ids[2]]["share"], 180 / 270, 9)

    def test_default_squad_is_my_fifteen_and_ids_override(self):
        d = make_export()
        mine = E.my_squad_ids(d)
        self.assertEqual(len(mine), 15)
        self.assertEqual(E.bench_boost_table(d)["ids"], mine)
        other = _fifteen(d, prefer="NFO")
        self.assertEqual(E.bench_boost_table(d, other)["ids"], other)
        with self.assertRaises(ValueError):
            E.bench_boost_table(d, [999999] + other[1:])

    def test_gk_def_at_fdr4_counts_only_gk_and_def(self):
        w = E.bench_boost_table(make_export(), _fifteen(make_export()))["weeks"][0]
        expect = sum(1 for r in w["rows"] if r["pos"] in (1, 2) and r["fixtures"]
                     and max(f[2] for f in r["fixtures"]) >= 4)
        any_pos = sum(1 for r in w["rows"] if r["fixtures"] and max(f[2] for f in r["fixtures"]) >= 4)
        self.assertEqual(w["gk_def_fdr4"], expect)
        self.assertNotEqual(expect, any_pos, "fixture cannot tell GK/DEF from everyone")

    def test_fodder_xi_has_the_same_formation_and_lives_within_budget(self):
        t = E.bench_boost_table(make_export(), _fifteen(make_export()))
        for w in t["weeks"]:
            self.assertIsNotNone(w["alt_xi"], f"GW{w['event']}: no fodder XI")
            got = {k: sum(1 for r in w["alt_xi"] if r["pos"] == k) for k in (1, 2, 3, 4)}
            self.assertEqual(got, w["formation"])
            spend = sum(r["price"] for r in w["alt_xi"]) + w["fodder_cost"]
            self.assertLessEqual(spend, t["budget"] + 1e-9)
            self.assertEqual(len(w["fodder"]), 4)

    def test_fodder_cost_comes_out_of_the_xi_budget_when_it_binds(self):
        """With 100m the synthetic pool never touches the ceiling; at 77m it
        does (a top-projection XI wants ~100m; the cheapest legal XI is ~46m),
        and the fodder must be paid for before the XI is bought."""
        d = make_export()
        d["standings"][0]["value"], d["standings"][0]["bank"] = 770, 0
        t = E.bench_boost_table(d, _fifteen(d))
        self.assertAlmostEqual(t["budget"], 77.0, 9)
        for w in t["weeks"]:
            self.assertIsNotNone(w["alt_xi"], f"GW{w['event']}: 77m must still fill an XI")
            xi_spend = sum(r["price"] for r in w["alt_xi"])
            self.assertLessEqual(xi_spend + w["fodder_cost"], 77.0 + 1e-9,
                                 f"GW{w['event']}: spent {xi_spend + w['fodder_cost']:.1f} of 77.0")
            self.assertGreater(xi_spend, 77.0 - w["fodder_cost"] - 6.0,
                               "fixture is not budget-bound - the check proves nothing")

    def test_section_prints_two_labelled_numbers_per_week(self):
        d = make_export()
        out = run("bench_boost", d)
        weeks = len({f["event"] for f in d["fixtures_next6"]})
        self.assertEqual(out.count("XI from this 15"), weeks)
        self.assertEqual(out.count("best XI, same budget, fodder bench"), weeks)
        self.assertIn("all 15 projected", out)
        self.assertIn("GK/DEF at FDR 4+", out)


class Budget(unittest.TestCase):
    """The API's entry value already includes the bank. On the GW4 and GW5
    deadline days, value = sum(prices of the 15) + bank to the tenth."""

    def test_budget_is_team_value_alone(self):
        d = make_export()                       # value 1003, bank 2
        self.assertAlmostEqual(E.bench_boost_table(d, _fifteen(d))["budget"], 100.3, 9)
        out = run("wildcard", d)
        self.assertIn("budget £100.3m", out)
        self.assertNotIn("£100.5m", out)

    def test_real_export_value_is_prices_plus_bank(self):
        """If a real export is sitting here: value - (sum of my 15's prices +
        bank) is price drift since the deadline - at most a tick per player -
        and in particular far smaller than the bank, which value + bank would
        count twice."""
        here = os.path.dirname(os.path.abspath(__file__))
        path = E.newest_export(here)
        if not path:
            self.skipTest("no real export in this folder")
        d = E.load(path)
        me = E.my_name(d)
        st = next(s for s in d["standings"] if s["entry_name"] == me)
        mine = [r for r in d["squads"] if r["entry_name"] == me]
        self.assertEqual(len(mine), 15)
        value, bank = st["value"] / 10, st["bank"] / 10
        gap = value - (sum(r["price"] for r in mine) + bank)
        self.assertLessEqual(abs(gap), 0.1 * 15, f"gap {gap:+.1f} is more than a tick a player")
        if bank >= 0.5:
            self.assertLess(abs(gap), bank, "value + bank would double-count the bank")


class MinutesIsAProbability(unittest.TestCase):
    """B: the minutes source is P(start), not points - rho columns only."""

    def _out(self):
        d, gw, log = _graded_world()
        log += [dict(r, source="minutes", predicted="0.75") for r in log]
        return _calibration(d, log)

    def test_minutes_row_shows_rho_only(self):
        import re
        out = self._out()
        row = re.search(r"^  minutes\s+\d+\s+(\d+)\s+(\S+)\s+(\S+)\s+([+-]?\d\.\d{3})\s+([+-]?\d\.\d{3})\s+\d+\s+(\S+)\s+(.*)$",
                        out, re.M)
        self.assertIsNotNone(row, "no minutes row")
        self.assertEqual((row.group(2), row.group(3), row.group(6)), ("-", "-", "-"),
                         "MAE / const / bias printed for a start probability")
        self.assertIn("rho only", row.group(7))
        self.assertIn("its MAE, const and bias are undefined", out, "the one-line note is missing")

    def test_other_sources_still_print_mae(self):
        import re
        out = self._out()
        self.assertRegex(out, r"(?m)^  xg\s+\d+\s+\d+\s+\d\.\d{2}\s+\d\.\d{2}\s", "xg lost its MAE")
        self.assertRegex(out, r"MINUTES over 1 gameweek\(s\), \d+ forecasts\n    rho ")
        self.assertRegex(out, r"XG over 1 gameweek\(s\), \d+ forecasts\n    MAE ")


class WildcardThreeLayer(unittest.TestCase):
    """sec_wildcard: layer 1 excludes, layer 2 shortlists, layer 3 orders;
    money split per position; XI + captain + bench with six-week sums."""

    @staticmethod
    def _by_id(cands):
        return {c["id"]: c for pos in cands for c in cands[pos]}

    def test_layer_one_excludes_the_frozen_flag_and_the_unavailable(self):
        d = make_export(gw=3)                           # window 3, 270 minutes
        ids = _fifteen(d)
        by_id = {p["id"]: p for p in d["all_players"]}
        by_id[ids[5]]["mins_last4"] = 180               # share 0.6667 -> out
        by_id[ids[6]]["mins_last4"] = 181               # 0.6704 -> in
        by_id[ids[7]]["status"] = "i"
        cands, _, excluded = E.wildcard_candidates(d)
        seen = self._by_id(cands)
        self.assertNotIn(ids[5], seen)
        self.assertIn(ids[6], seen)
        self.assertNotIn(ids[7], seen)
        self.assertGreaterEqual(excluded[f"minutes share <= {E.FLAG_SHARE_MAX}"], 1)

    def test_roles_admit_but_never_rank(self):
        """A three-role midfielder with the lower metric sits below a no-role
        midfielder with the higher one; the same for defenders; the roles are
        still printed beside him in the shortlist and in the XI."""
        d = make_export()
        for p in d["all_players"]:
            p["pens_order"] = p["corners_order"] = p["fk_order"] = None
        mids = [p for p in d["all_players"] if p["pos"] == 3 and p["status"] == "a"]
        norole, threerole = mids[0], mids[1]
        threerole["pens_order"] = threerole["corners_order"] = threerole["fk_order"] = 1
        for r in d["player_gw_recent"]:
            if r["player_id"] == norole["id"]:
                r["xg"], r["defcon"] = 1.2, 0        # the higher metric, no role
            elif r["player_id"] == threerole["id"]:
                r["xg"], r["defcon"] = 0.9, 0        # three roles, the lower metric
        defs = [p for p in d["all_players"] if p["pos"] == 2 and p["status"] == "a"]
        d_norole, d_threerole = defs[0], defs[1]
        d_threerole["pens_order"] = d_threerole["corners_order"] = d_threerole["fk_order"] = 1
        for r in d["player_gw_recent"]:
            if r["player_id"] == d_norole["id"]:
                r["xg"], r["xa"], r["defcon"] = 1.0, 0.5, 15
            elif r["player_id"] == d_threerole["id"]:
                r["xg"], r["xa"], r["defcon"] = 0.0, 0.0, 0
        cands, _, _ = E.wildcard_candidates(d)
        seen = self._by_id(cands)
        self.assertEqual(seen[threerole["id"]]["roles"], ["corners", "fk", "pens"])
        self.assertEqual(seen[norole["id"]]["roles"], [])
        self.assertAlmostEqual(seen[norole["id"]]["p_start"], seen[threerole["id"]]["p_start"], 9)
        self.assertGreater(seen[norole["id"]]["xgi90"], seen[threerole["id"]]["xgi90"])
        order = [c["id"] for c in cands[3]]
        self.assertLess(order.index(norole["id"]), order.index(threerole["id"]),
                        "three roles ranked a midfielder above a higher metric")
        self.assertEqual(order[:2], [norole["id"], threerole["id"]])
        self.assertGreater(seen[d_norole["id"]]["sum6"], seen[d_threerole["id"]]["sum6"])
        dorder = [c["id"] for c in cands[2]]
        self.assertLess(dorder.index(d_norole["id"]), dorder.index(d_threerole["id"]),
                        "three roles ranked a defender above a higher bottomup sum")
        out = run("wildcard", d)
        short = out.split("SHORTLISTS")[1].split("SQUAD")[0]
        line = next(l for l in short.splitlines() if l.strip().startswith(threerole["web_name"][:14]))
        self.assertIn("corners,fk,pens", line, "roles not printed in the shortlist")
        xi_block = out.split("SQUAD")[1].split("BENCH")[0]
        line = next(l for l in xi_block.splitlines()
                    if l.strip().startswith("MID " + threerole["web_name"][:14]))
        self.assertIn("corners,fk,pens", line, "roles not printed beside the XI player")

    def test_mid_ordering_is_expected_appearances_then_xgi_not_points(self):
        d = make_export()
        mids = [p for p in d["all_players"] if p["pos"] == 3 and p["status"] == "a"][:2]
        a, b = mids
        for r in d["player_gw_recent"]:               # P(start) comes from the rows
            if r["player_id"] == b["id"]:
                r["xg"] = 1.2                         # far more xGI ...
                if r["event"] == 3:
                    r["starts"] = 0                   # ... but started two of three
        cands, _, _ = E.wildcard_candidates(d)
        seen = self._by_id(cands)
        self.assertGreater(seen[b["id"]]["sum6"], seen[a["id"]]["sum6"],
                           "fixture cannot tell points from appearances")
        order = [c["id"] for c in cands[3]]
        self.assertLess(order.index(a["id"]), order.index(b["id"]),
                        "a MID was ordered by points, not by P(start) x fixtures")

    def test_mid_ties_on_appearances_break_on_xgi(self):
        d = make_export()
        mids = [p for p in d["all_players"] if p["pos"] == 3 and p["status"] == "a"]
        a, b = mids[2], mids[3]
        for p in (a, b):
            p["pens_order"] = p["corners_order"] = p["fk_order"] = None
        for r in d["player_gw_recent"]:
            if r["player_id"] == b["id"]:
                r["xg"] = 0.9
        cands, _, _ = E.wildcard_candidates(d)
        seen = self._by_id(cands)
        self.assertAlmostEqual(seen[a["id"]]["p_start"], seen[b["id"]]["p_start"], 9)
        order = [c["id"] for c in cands[3]]
        self.assertLess(order.index(b["id"]), order.index(a["id"]))

    def test_squad_is_legal_within_budget_and_clubs(self):
        d = make_export()
        for r in d["player_gw_recent"]:              # rig BHA to top every outfield list
            if r["team"] == "BHA":
                r["xg"], r["xa"], r["defcon"] = 1.5, 0.8, 15
        cands, _, _ = E.wildcard_candidates(d)
        budget = d["standings"][0]["value"] / 10
        squad, spent, split = E.build_three_layer_squad(cands, budget, E.budget_split(d, budget))
        self.assertEqual({k: sum(1 for c in squad if c["pos"] == k) for k in (1, 2, 3, 4)},
                         {1: 2, 2: 5, 3: 5, 4: 3})
        self.assertLessEqual(spent, budget + 1e-9)
        self.assertAlmostEqual(sum(split.values()), budget, 9)
        clubs = {}
        for c in squad:
            clubs[c["team"]] = clubs.get(c["team"], 0) + 1
        self.assertLessEqual(max(clubs.values()), 3, clubs)
        self.assertGreaterEqual(clubs.get("BHA", 0), 3, "the rig did not bite")

    def test_the_build_takes_the_top_of_the_list_not_the_value_per_million_pick(self):
        """The dearest defender, given the best projection in his position,
        tops the DEF list and starts - at the lowest points per pound of any
        XI defender. A value-per-million build would not begin with him."""
        d = make_export()
        defs = [p for p in d["all_players"] if p["pos"] == 2 and p["status"] == "a"]
        dear = max(defs, key=lambda p: (p["price"], p["id"]))
        for r in d["player_gw_recent"]:
            if r["player_id"] == dear["id"]:
                r["xg"], r["xa"], r["defcon"] = 1.0, 0.5, 15
        cands, _, _ = E.wildcard_candidates(d)
        self.assertEqual(cands[2][0]["id"], dear["id"], "the rig did not top the list")
        budget = d["standings"][0]["value"] / 10
        squad, _, _ = E.build_three_layer_squad(cands, budget, E.budget_split(d, budget))
        xi_def = [c for c in squad if c["xi"] and c["pos"] == 2]
        self.assertIn(dear["id"], {c["id"] for c in xi_def}, "the top of the list did not start")
        vpm = {c["id"]: c["sum6"] / c["price"] for c in xi_def}
        self.assertEqual(max(c["price"] for c in xi_def), dear["price"])
        self.assertNotEqual(max(vpm, key=vpm.get), dear["id"], "the rig is the best value in the XI")
        self.assertIn(dear["web_name"][:14], run("wildcard", d).split("SQUAD")[1].split("BENCH")[0])

    def test_split_is_the_current_squad_shape_not_a_global_vpm(self):
        d = make_export()
        split = E.budget_split(d, 100.0)
        me = E.my_name(d)
        spend = {}
        for r in d["squads"]:
            if r["entry_name"] == me:
                spend[r["pos"]] = spend.get(r["pos"], 0) + r["price"]
        total = sum(spend.values())
        for k in (1, 2, 3, 4):
            self.assertAlmostEqual(split[k], 100.0 * spend[k] / total, 9)

    def test_output_has_xi_captain_bench_sums_and_bench_fixtures(self):
        d = make_export()
        out = run("wildcard", d)
        body = out.split("BENCH BOOST SCREEN")[0].split("SQUAD")[1]
        xi_block, bench_block = body.split("BENCH")
        self.assertEqual(sum(1 for l in xi_block.splitlines() if "6wk " in l), 11)
        self.assertEqual(xi_block.count("(C)"), 1)
        bench_lines = [l for l in bench_block.splitlines()
                       if l.strip()[:3] in ("GK", "DEF", "MID", "FWD") or l.strip()[:2] == "GK"]
        self.assertEqual(len(bench_lines), 4, bench_lines)
        later = sorted({f["event"] for f in d["fixtures_next6"]})[2:]
        self.assertIn(f"fixtures GW{later[0]}-{later[-1]}", bench_block)
        for l in bench_lines:                      # one real fixture per later week
            self.assertEqual(l.count(" (H) ") + l.count(" (A) "), len(later), l)
        self.assertIn("XI six-week sum", out)
        self.assertIn("layer 1", out)
        self.assertIn("budget £100.3m", out)


class WildcardCrossPosition(unittest.TestCase):
    """D: no cross-position choice on the mixed-unit sums. Formation and money
    split are parameters; captain and vice come from MID/FWD; every sum is the
    full model, one unit; the bench is the cheapest who pass layer 1."""

    @staticmethod
    def _rig_defenders(d):
        """Defenders project far above everyone else: the sums would pick five.
        Two midfielders keep a little xG so the best MID/FWD is unique."""
        mids = [p for p in d["all_players"] if p["pos"] == 3 and p["status"] == "a"]
        for r in d["player_gw_recent"]:
            if r["pos"] == 2:
                r["xg"], r["xa"], r["defcon"] = 1.0, 0.5, 15
            elif r["pos"] in (3, 4):
                r["xg"], r["xa"] = 0.0, 0.0
            if r["player_id"] == mids[0]["id"]:
                r["xg"] = 0.6
            if r["player_id"] == mids[1]["id"]:
                r["xg"] = 0.3
        return d

    @staticmethod
    def _blocks(out):
        out = out.split("BENCH BOOST SCREEN")[0]          # G: the draft's screen follows
        xi_block, bench_block = out.split("SQUAD")[1].split("BENCH")
        return xi_block, bench_block

    @staticmethod
    def _lines(block):
        return [l for l in block.splitlines() if l.strip()[:3] in ("GK ", "DEF", "MID", "FWD")]

    @staticmethod
    def _sum(line):
        import re
        return float(re.search(r"6wk\s+([\d.]+)", line).group(1))

    @staticmethod
    def _wc(d, formation=None, split=None, horizon=6):
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_wildcard(d, horizon, formation, split)
        return buf.getvalue()

    def test_a_formation_the_sums_would_not_choose_is_honoured(self):
        d = self._rig_defenders(make_export())
        cands, _, _ = E.wildcard_candidates(d)
        squad, _, _ = E.build_three_layer_squad(cands, 300.0, E.budget_split(d, 300.0))
        by_sums = E._best_xi([dict(c, proj=c["sum6"]) for c in squad])
        self.assertEqual(sum(1 for c in by_sums if c["pos"] == 2), 5,
                         "the rig did not make the sums prefer five defenders")
        xi = [c for c in squad if c["xi"]]
        self.assertEqual({k: sum(1 for c in xi if c["pos"] == k) for k in (1, 2, 3, 4)},
                         {1: 1, 2: 4, 3: 3, 4: 3}, "the default 4-3-3 was not honoured")
        club = {}                                    # the top of each list, 3-per-club
        for pos, n in ((1, 1), (2, 4), (3, 3), (4, 3)):
            want = []
            for c in cands[pos]:
                if len(want) == n:
                    break
                if club.get(c["team"], 0) < 3:
                    want.append(c["id"])
                    club[c["team"]] = club.get(c["team"], 0) + 1
            self.assertEqual(sorted(c["id"] for c in xi if c["pos"] == pos), sorted(want),
                             f"{E.POS[pos]}: the XI is not the top of the ordered list")
        out = self._wc(d)
        self.assertIn("XI (4-3-3, --formation)", out)
        out = self._wc(d, "3-5-2")
        xi_lines = self._lines(self._blocks(out)[0])
        self.assertIn("XI (3-5-2, --formation)", out)
        self.assertEqual([sum(1 for l in xi_lines if l.strip().startswith(k))
                          for k in ("DEF", "MID", "FWD")], [3, 5, 2])
        for bad in ("6-2-2", "4-3-2", "4-6-0", "x"):
            with self.assertRaises(ValueError):
                E.parse_formation(bad)

    def test_a_defender_with_the_top_sum_is_never_captain(self):
        d = self._rig_defenders(make_export())
        xi_block, _ = self._blocks(self._wc(d))
        lines = self._lines(xi_block)
        top = max(lines, key=self._sum)
        self.assertTrue(top.strip().startswith("DEF"), "the rig did not put a DEF on top")
        cap = [l for l in lines if "(C)" in l]
        vice = [l for l in lines if "(V)" in l]
        self.assertEqual((len(cap), len(vice)), (1, 1))
        self.assertIn(cap[0].strip()[:3], ("MID", "FWD"))
        self.assertIn(vice[0].strip()[:3], ("MID", "FWD"))
        att = sorted((l for l in lines if l.strip()[:3] in ("MID", "FWD")),
                     key=self._sum, reverse=True)
        self.assertGreater(self._sum(att[0]), self._sum(att[1]), "the rig left a tie")
        self.assertGreater(self._sum(att[1]), self._sum(att[2]), "the rig left a tie")
        self.assertEqual(cap[0], att[0], "the captain is not the best MID/FWD")
        self.assertEqual(vice[0], att[1], "the vice is not the next MID/FWD")
        self.assertIn("captain restricted to MID/FWD: DEF over-spread", xi_block)

    def test_the_fifteen_sums_are_one_unit_the_full_model(self):
        d = make_export()
        cands, weeks, _ = E.wildcard_candidates(d)
        inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=d["gameweek"])
        fx = E.week_fixtures(d)
        by_id = {p["id"]: p for p in d["all_players"]}

        def total(c, terms):
            return sum(x for x in (E.project_week(c["id"], by_id[c["id"]], inp, fx, w, terms)
                                   for w in weeks) if x is not None)

        for pos in (1, 2, 3, 4):
            c = cands[pos][0]
            self.assertAlmostEqual(c["sum6"], total(c, E.ALL_TERMS), 6,
                                   f"{E.POS[pos]}: the sum is not the full model")
        mid = cands[3][0]
        self.assertGreater(mid["sum6"], total(mid, E.three_layer_terms(3)) + 1e-6,
                           "fixture cannot tell the full model from the bare xGI term")
        out = self._wc(d)
        xi_block, bench_block = self._blocks(out)
        xi_vals = [self._sum(l) for l in self._lines(xi_block)]
        bench_vals = [self._sum(l) for l in self._lines(bench_block)]
        self.assertEqual((len(xi_vals), len(bench_vals)), (11, 4))
        import re
        m = re.search(r"XI six-week sum ([\d.]+)\s+bench six-week sum ([\d.]+)\s+fifteen ([\d.]+)", out)
        self.assertIsNotNone(m, "the three totals are not printed")
        self.assertAlmostEqual(float(m.group(1)), sum(xi_vals), delta=0.6)
        self.assertAlmostEqual(float(m.group(2)), sum(bench_vals), delta=0.25)
        self.assertAlmostEqual(float(m.group(3)), float(m.group(1)) + float(m.group(2)), delta=0.11)
        self.assertIn("one unit: full model, all terms", out)

    def test_bench_is_the_cheapest_who_pass_layer_one_with_the_fixture_tiebreak(self):
        d = make_export()
        cheap = sorted((p for p in d["all_players"] if p["pos"] == 2 and p["status"] == "a"),
                       key=lambda p: (p["price"], p["id"]))[:2]
        self.assertEqual(cheap[0]["price"], cheap[1]["price"], "no price tie to break")
        self.assertNotEqual(cheap[0]["team"], cheap[1]["team"])
        for r in d["player_gw_recent"]:              # bottom of the DEF order, never XI
            if r["player_id"] in (cheap[0]["id"], cheap[1]["id"]):
                r["xg"], r["xa"], r["defcon"] = 0.0, 0.0, 0
        weeks = sorted({f["event"] for f in d["fixtures_next6"]})

        def build(blanks):
            dd = json.loads(json.dumps(d))
            dd["fixtures_next6"] = [f for f in dd["fixtures_next6"]
                                    if not any(f["event"] in ws and t in (f["home"], f["away"])
                                               for t, ws in blanks)]
            cands, _, _ = E.wildcard_candidates(dd)
            budget = dd["standings"][0]["value"] / 10
            squad, _, _ = E.build_three_layer_squad(cands, budget, E.budget_split(dd, budget))
            xi_ids = {c["id"] for c in squad if c["xi"]}
            bench = [c for c in squad if not c["xi"]]
            self.assertEqual(sorted(c["pos"] for c in bench), [1, 2, 3, 3])
            in_squad = {c["id"] for c in squad}
            for c in bench:                          # nobody cheaper was legal
                clubs = {}
                for x in squad:
                    if x["id"] != c["id"]:
                        clubs[x["team"]] = clubs.get(x["team"], 0) + 1
                cheaper = [x["name"] for x in cands[c["pos"]]
                           if x["id"] not in in_squad and x["price"] < c["price"] - 1e-9
                           and clubs.get(x["team"], 0) < E.CLUB_MAX]
                self.assertEqual(cheaper, [], f"{E.POS[c['pos']]} bench is not the cheapest")
                self.assertGreater(c["share"], E.FLAG_SHARE_MAX)
            self.assertFalse(xi_ids & {cheap[0]["id"], cheap[1]["id"]}, "the rig reached the XI")
            return next(c["id"] for c in bench if c["pos"] == 2)

        a, b = cheap[0]["id"], cheap[1]["id"]
        ta, tb = cheap[0]["team"], cheap[1]["team"]
        self.assertEqual(build([(tb, weeks[2:3])]), a, "a GW8 blank did not decide the tie")
        self.assertEqual(build([(ta, weeks[2:3])]), b, "the tie-break is not two-sided")
        # two blanks before the later window against one inside it: only the window counts
        self.assertEqual(build([(ta, weeks[:2]), (tb, weeks[3:4])]), a,
                         "a blank before the later window counted against a bench body")

    def test_split_parameter_is_scaled_to_the_budget_and_moves_the_money(self):
        d = make_export()
        even = E.budget_split(d, 100.3, given=E.parse_split("1,1,1,1"))
        for k in (1, 2, 3, 4):
            self.assertAlmostEqual(even[k], 100.3 / 4, 9)
        heavy = E.budget_split(d, 100.3, given=E.parse_split("5,25,50,20.3"))
        self.assertAlmostEqual(heavy[3], 50.0, 9)
        d["standings"][0]["value"] = 800              # £80.0m: the money binds
        out = self._wc(d, None, "1,1,1,1")
        quarter = f"£{80 / 4:.1f}m"
        self.assertIn(f"split by position, --split scaled to the budget: GK {quarter}  DEF {quarter}", out)
        default = self._wc(d)
        self.assertIn("split by position, current squad shape:", default)
        for text in (out, default):
            import re
            m = re.search(r"SQUAD  £([\d.]+)m of £80\.0m", text)
            self.assertIsNotNone(m, "no squad was printed")
            self.assertLessEqual(float(m.group(1)), 80.0, "over budget")
        self.assertNotEqual(self._lines(self._blocks(out)[0]), self._lines(self._blocks(default)[0]),
                            "an even split bought the same XI as the squad-shape split")
        starved = self._wc(d, None, "1,1,1,20")       # GK/DEF/MID shares below their cheapest fill
        self.assertIn("split repaired so every position can buy its cheapest fill", starved)
        self.assertRegex(starved, r"SQUAD  £([\d.]+)m of £80\.0m")
        d["standings"][0]["value"] = 650              # below the cheapest legal 15: refused
        self.assertIn("Could not assemble a legal 15 within £65.0m", self._wc(d))
        for bad in ("1,2,3", "1,2,3,0", "a,b,c,d"):
            with self.assertRaises(ValueError):
                E.parse_split(bad)

    def test_cli_formation_and_split_reach_the_section(self):
        tmp = tempfile.mkdtemp()
        export = os.path.join(tmp, "fpl_export_gw3.json")
        with open(export, "w", encoding="utf-8") as fh:
            json.dump(make_export(), fh)
        argv, saved = sys.argv, (E.WC_FORMATION, E.WC_SPLIT)
        try:
            sys.argv = ["fpl_edge.py", export, "--section", "wildcard",
                        "--formation", "3-4-3", "--split", "1,1,1,1"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                E.main()
            self.assertIn("XI (3-4-3, --formation)", buf.getvalue())
            self.assertIn("--split scaled to the budget", buf.getvalue())
            sys.argv = ["fpl_edge.py", export, "--section", "wildcard", "--formation", "6-2-2"]
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    E.main()
            self.assertIn("not legal", str(cm.exception))
        finally:
            sys.argv = argv
            E.WC_FORMATION, E.WC_SPLIT = saved
            shutil.rmtree(tmp, ignore_errors=True)


def _legal_lineup(d):
    """Re-slot My Team into a legal XI (GK, 4 DEF, 4 MID, 2 FWD) with a bench
    of GK, DEF, MID, FWD. Returns slot -> squad row."""
    me = E.my_name(d)
    mine = [r for r in d["squads"] if r["entry_name"] == me]
    by_pos = {k: [r for r in mine if r["pos"] == k] for k in (1, 2, 3, 4)}
    order = (by_pos[1][:1] + by_pos[2][:4] + by_pos[3][:4] + by_pos[4][:2]
             + by_pos[1][1:] + by_pos[2][4:] + by_pos[3][4:] + by_pos[4][2:])
    for slot, r in enumerate(order, 1):
        r["slot"], r["multiplier"] = slot, (1 if slot <= 11 else 0)
        r["is_captain"] = r["is_vice"] = 0
    return {r["slot"]: r for r in order}


class BenchVsXI(unittest.TestCase):
    """sec_squad: each bench player against the lowest XI player of his own
    position for the next gameweek, in one unit; same-position swaps only."""

    @staticmethod
    def _pid(d, row):
        return next(p["id"] for p in d["all_players"]
                    if (p["web_name"], p["team"]) == (row["web_name"], row["team"]))

    def _rig_rows(self, d, pid, **fields):
        for r in d["player_gw_recent"]:
            if r["player_id"] == pid:
                r.update(fields)

    def test_bench_player_above_the_lowest_xi_of_his_position_is_a_swap(self):
        d = make_export()
        slots = _legal_lineup(d)
        self._rig_rows(d, self._pid(d, slots[14]), xg=1.2, xa=0.6)   # bench MID
        week, rows, _ = E.bench_vs_xi(d)
        self.assertEqual(week, d["gameweek"] + 1)
        self.assertEqual([r["bench"]["slot"] for r in rows], [12, 13, 14, 15])
        r = next(r for r in rows if r["bench"]["slot"] == 14)
        self.assertEqual(r["verdict"], "SWAP")
        xi_mids = [slots[s] for s in (6, 7, 8, 9)]
        inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=d["gameweek"])
        fx = E.week_fixtures(d)
        by_id = {p["id"]: p for p in d["all_players"]}
        proj = {row["web_name"]: E.project_week(self._pid(d, row), by_id[self._pid(d, row)],
                                                inp, fx, week, E.ALL_TERMS) for row in xi_mids}
        lowest = min(proj, key=proj.get)
        self.assertEqual(r["xi"]["name"], lowest, "not compared against the lowest XI MID")
        self.assertAlmostEqual(r["delta"], r["bench"]["proj"] - proj[lowest], 6)
        self.assertGreater(r["delta"], 0)
        out = run("squad", d)
        line = next(l for l in out.splitlines() if l.strip().startswith("MID " + slots[14]["web_name"][:14]))
        self.assertIn(lowest[:14], line)
        self.assertTrue(line.rstrip().endswith("SWAP"), line)
        self.assertIn(f"BENCH vs XI  GW{week}", out)

    def test_a_bench_player_is_never_compared_across_positions(self):
        d = make_export()
        slots = _legal_lineup(d)
        self._rig_rows(d, self._pid(d, slots[13]), xg=1.5, xa=0.8, defcon=15)   # bench DEF
        _, rows, _ = E.bench_vs_xi(d)
        r = next(r for r in rows if r["bench"]["slot"] == 13)
        everyone = [x["proj"] for x in (row["xi"] for row in rows) if x] + [row["bench"]["proj"] for row in rows]
        self.assertEqual(r["bench"]["proj"], max(everyone), "the rig is not the top projection")
        self.assertEqual(r["xi"]["pos"], 2, "a DEF was compared with another position")
        for row in rows:
            if row["xi"]:
                self.assertEqual(row["xi"]["pos"], row["bench"]["pos"])
        self.assertEqual(r["verdict"], "SWAP")

    def test_projections_are_one_unit_the_full_model(self):
        d = make_export()
        slots = _legal_lineup(d)
        week, rows, _ = E.bench_vs_xi(d)
        inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=d["gameweek"])
        fx = E.week_fixtures(d)
        by_id = {p["id"]: p for p in d["all_players"]}
        for r in rows:
            for v in (r["bench"], r["xi"]):
                pid = self._pid(d, {"web_name": v["name"], "team": v["team"]})
                self.assertAlmostEqual(v["proj"], E.project_week(pid, by_id[pid], inp, fx, week, E.ALL_TERMS), 6)
        mid = next(r["bench"] for r in rows if r["bench"]["pos"] == 3)
        pid = self._pid(d, {"web_name": mid["name"], "team": mid["team"]})
        self.assertGreater(mid["proj"], E.project_week(pid, by_id[pid], inp, fx, week) + 1e-6,
                           "fixture cannot tell the full model from the bare xGI term")

    def test_a_blank_xi_player_is_the_one_to_swap(self):
        d0 = make_export()
        slots = _legal_lineup(d0)
        team = slots[3]["team"]                                   # an XI DEF's club
        d = make_export(blank_team=team)
        _legal_lineup(d)
        week, rows, _ = E.bench_vs_xi(d)
        playing = {f[k] for f in d["fixtures_next6"] if f["event"] == week for k in ("home", "away")}
        blank = set(TEAMS) - playing                              # an odd pool blanks two clubs
        self.assertIn(team, blank)
        r = next(r for r in rows if r["bench"]["slot"] == 13)     # bench DEF
        if r["bench"]["team"] in blank:
            self.skipTest("bench DEF shares a blanked club")
        self.assertIsNone(r["xi"]["proj"])
        self.assertIn(r["xi"]["team"], blank)
        self.assertEqual(r["verdict"], "SWAP (XI blank)")
        out = run("squad", d)
        line = next(l for l in out.splitlines() if l.strip().startswith("DEF " + r["bench"]["name"][:14]))
        self.assertIn("BLANK", line)
        self.assertIn("SWAP (XI blank)", line)

    def test_flag_line_names_xi_players_under_the_frozen_flag(self):
        d = make_export(gw=3)                                      # 270 minutes possible
        slots = _legal_lineup(d)
        by_key = {(p["web_name"], p["team"]): p for p in d["all_players"]}
        by_key[(slots[4]["web_name"], slots[4]["team"])]["mins_last4"] = 180    # 0.667: flagged
        by_key[(slots[5]["web_name"], slots[5]["team"])]["mins_last4"] = 181    # not
        by_key[(slots[13]["web_name"], slots[13]["team"])]["mins_last4"] = 100  # bench: not an XI flag
        _, _, flagged = E.bench_vs_xi(d)
        self.assertEqual([x["name"] for x in flagged], [slots[4]["web_name"]])
        out = run("squad", d)
        line = next(l for l in out.splitlines() if "XI under the frozen flag" in l)
        self.assertIn(slots[4]["web_name"], line)
        self.assertNotIn(slots[5]["web_name"], line)
        self.assertNotIn(slots[13]["web_name"], line)


class EffectiveOwnership(unittest.TestCase):
    """sec_eo: effective ownership with captaincy from the latest picks; per-rival
    projected swings; captain cover restricted to MID/FWD in my XI."""

    @staticmethod
    def _row(d, entry, pid):
        p = next(p for p in d["all_players"] if p["id"] == pid)
        return next(r for r in d["squads"] if r["entry_name"] == entry
                    and (r["web_name"], r["team"]) == (p["web_name"], p["team"]))

    @staticmethod
    def _player(players, d, pid):
        p = next(p for p in d["all_players"] if p["id"] == pid)
        return next(x for x in players if (x["name"], x["team"]) == (p["web_name"], p["team"]))

    def test_captain_counts_two_bench_zero_triple_captain_two(self):
        d = make_export(n_entries=4)
        me = E.my_name(d)
        rivals = sorted({r["entry_name"] for r in d["squads"]} - {me})
        cap = self._row(d, me, 31)                         # slot 10: everyone's captain
        self.assertEqual(cap["multiplier"], 2)
        self._row(d, rivals[0], 31)["multiplier"] = 3     # Triple Captain: spent, counts 2
        self._row(d, rivals[1], 31)["multiplier"] = 0     # benched him
        self._row(d, rivals[2], 31)["multiplier"] = 1     # starts him, no armband
        players, rows = E.effective_ownership(d)
        p = self._player(players, d, 31)
        self.assertAlmostEqual(p["eo"], (2 + 0 + 1) / 3, 9)
        self.assertEqual((p["start"], p["capt"], p["my_mult"]), (2, 1, 2))
        self.assertAlmostEqual(p["net"], 2 - 1.0, 9)
        b = self._player(players, d, 33)                  # slot 12: everyone's bench
        self.assertEqual((b["eo"], b["start"], b["my_mult"], b["net"]), (0.0, 0, 0, 0.0))
        self.assertEqual([r["captain"] for r in rows], [cap["web_name"]] * 3)

    def test_net_is_mine_minus_theirs_per_point(self):
        d = make_export(n_entries=4)
        me = E.my_name(d)
        mine = self._row(d, me, 49)                        # a FWD on everyone's bench
        mine["multiplier"] = 1
        players, _ = E.effective_ownership(d)
        self.assertAlmostEqual(self._player(players, d, 49)["net"], 1.0, 9)
        mine["multiplier"] = 2
        players, _ = E.effective_ownership(d)
        self.assertAlmostEqual(self._player(players, d, 49)["net"], 2.0, 9)
        out = run("eo", d)
        block = out.split("YOUR STAKES THEY DON'T MATCH")[1].split("PER RIVAL")[0]
        self.assertIn(mine["web_name"][:15], block)
        self.assertIn("+2.00", block)

    def test_per_rival_swing_is_multiplier_gap_times_the_full_projection(self):
        d = make_export(n_entries=4)
        me = E.my_name(d)
        self._row(d, me, 33)["multiplier"] = 1             # a MID only I start
        self._row(d, me, 30)["multiplier"] = 2             # my armband moves
        self._row(d, me, 31)["multiplier"] = 1             # off the field's captain
        week, proj = E.next_gw_projections(d)
        self.assertEqual(week, d["gameweek"] + 1)
        players, rivals = E.effective_ownership(d)
        me_mult = {(r["web_name"], r["team"]): min(2, r["multiplier"] or 0)
                   for r in d["squads"] if r["entry_name"] == me}
        rows = E.rival_swings(me_mult, rivals, proj)
        inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=d["gameweek"])
        fx = E.week_fixtures(d)
        by_key = {(p["web_name"], p["team"]): p for p in d["all_players"]}
        for r, riv in zip(rows, rivals):
            want = 0.0
            for k in set(me_mult) | set(riv["mult"]):
                p = by_key[k]
                pr = E.project_week(p["id"], p, inp, fx, week, E.ALL_TERMS) or 0.0
                want += (me_mult.get(k, 0) - riv["mult"].get(k, 0)) * pr
            self.assertAlmostEqual(r["swing"], want, 6, r["entry"])
            self.assertAlmostEqual(r["swing"], r["yours"] - r["theirs"], 6)
            self.assertNotEqual(riv["mult"][(self._row(d, me, 31)["web_name"],
                                             self._row(d, me, 31)["team"])], 1)
        row33 = self._row(d, me, 33)
        p33 = by_key[(row33["web_name"], row33["team"])]
        bare = E.project_week(p33["id"], p33, inp, fx, week)
        self.assertGreater(proj[(p33["web_name"], p33["team"])], bare + 1e-6,
                           "fixture cannot tell the full model from the bare xGI term")
        out = run("eo", d)
        self.assertIn(f"PER RIVAL, GW{week}", out)
        self.assertEqual(out.count("their captain"), 1)

    def test_captain_cover_is_mid_fwd_in_my_xi_by_projection(self):
        d = make_export(n_entries=4)
        slots = _legal_lineup(d)
        for r in d["player_gw_recent"]:
            if r["player_id"] in (9, 30, 33):             # XI DEF, XI MID, bench MID: all huge
                r["xg"], r["xa"] = 1.5, 0.8
        week, proj = E.next_gw_projections(d)
        players, _ = E.effective_ownership(d)
        rows = E.captain_cover(d, players, proj)
        names = [c["name"] for c in rows]
        xi_att = [slots[s]["web_name"] for s in range(6, 12)]   # 4 MID + 2 FWD
        self.assertEqual(sorted(names), sorted(xi_att))
        self.assertEqual(names[0], slots[7]["web_name"])         # pid 30 tops the list
        self.assertEqual([c["proj"] for c in rows], sorted((c["proj"] for c in rows), reverse=True))
        d9 = self._row(d, E.my_name(d), 9)
        self.assertGreater(proj[(d9["web_name"], d9["team"])], rows[0]["proj"],
                           "the rig did not put the DEF on top")
        self.assertNotIn(d9["web_name"], names, "a DEF was offered as captain")
        self.assertNotIn(slots[14]["web_name"], names, "a bench player was offered as captain")
        for c in rows:
            self.assertAlmostEqual(c["stake"], 2 - c["eo"], 9)
        capt31 = next(c for c in rows if c["name"] == slots[8]["web_name"])   # the field's captain
        self.assertEqual(capt31["capt"], 3)
        self.assertAlmostEqual(capt31["stake"], 0.0, 9)
        out = run("eo", d)
        block = out.split("CAPTAIN COVER")[1]
        first = next(l for l in block.splitlines()[2:] if l.strip())
        self.assertTrue(first.strip().startswith(names[0][:15]), first)
        self.assertIn("EO changes the variance", out)


class Concentration(unittest.TestCase):
    """F (1): conc, trim90, med90 beside every printed xGI/90 - information
    only. Nothing orders or projects on them."""

    @staticmethod
    def _rows(pid, games):
        return [{"player_id": pid, "event": i + 1, "minutes": m, "xg": g, "xa": 0.0}
                for i, (g, m) in enumerate(games)]

    def test_arithmetic_on_five_games_with_one_spike(self):
        v = E.xgi_rate_variants(self._rows(7, [(0.1, 90), (0.1, 90), (0.1, 90), (0.1, 90), (0.6, 90)]))[7]
        self.assertEqual(v["games"], 5)
        self.assertAlmostEqual(v["raw90"], 1.0 / 450 * 90, 9)
        self.assertAlmostEqual(v["conc"], 0.6, 9)
        self.assertAlmostEqual(v["trim90"], 0.4 / 360 * 90, 9)
        self.assertAlmostEqual(v["med90"], 0.1, 9)
        cells = E.conc_cells(v)
        self.assertEqual(cells, f"{'0.60!':>6}{'0.10':>7}{'0.10':>7}")
        even = E.xgi_rate_variants(self._rows(8, [(0.2, 90), (0.4, 90), (0.1, 90), (0.3, 90)]))[8]
        self.assertAlmostEqual(even["med90"], 0.25, 9)          # even count: mean of the middle two
        self.assertAlmostEqual(even["conc"], 0.4, 9)
        self.assertNotIn("!", E.conc_cells(even))

    def test_blanks_and_the_sixty_minute_gate(self):
        three = E.xgi_rate_variants(self._rows(1, [(0.2, 90), (0.2, 90), (0.5, 90)]))[1]
        self.assertIsNone(three["trim90"], "trim90 needs four games")
        self.assertAlmostEqual(three["med90"], 0.2, 9)
        short = E.xgi_rate_variants(self._rows(2, [(0.2, 45), (0.2, 30), (0.2, 59), (0.1, 20)]))[2]
        self.assertIsNone(short["med90"], "med90 needs a 60-minute game")
        self.assertAlmostEqual(short["raw90"], 0.7 / 154 * 90, 9)
        self.assertAlmostEqual(short["trim90"], 0.5 / 109 * 90, 9)     # best = first 0.2 (max keeps the first)
        zero = E.xgi_rate_variants(self._rows(3, [(0.0, 90), (0.0, 90), (0.0, 90), (0.0, 90)]))[3]
        self.assertIsNone(zero["conc"])
        self.assertEqual(zero["trim90"], 0.0)
        mixed = E.xgi_rate_variants(self._rows(4, [(0.3, 45), (0.3, 90), (0.3, 90), (0.3, 90)]))[4]
        self.assertAlmostEqual(mixed["med90"], 0.3, 9)                 # the 45-minute game is out of med90 ...
        self.assertAlmostEqual(mixed["raw90"], 1.2 / 315 * 90, 9)      # ... and in raw90
        self.assertEqual(E.conc_cells(None), f"{'-':>6}{'-':>7}{'-':>7}")
        self.assertEqual(E.conc_cells(zero), f"{'-':>6}{'0.00':>7}{'0.00':>7}")
        self.assertNotIn(5, E.xgi_rate_variants(self._rows(5, [(0.0, 0), (0.0, 0)])),
                         "a player with no minutes has no rate")

    def _spike_world(self):
        d = make_export(gw=5)
        mids = [p for p in d["all_players"] if p["pos"] == 3 and p["status"] == "a"]
        spike, steady = mids[0], mids[1]
        for p in (spike, steady):
            p["pens_order"] = p["corners_order"] = p["fk_order"] = None
        for r in d["player_gw_recent"]:
            if r["player_id"] == spike["id"]:
                r["xg"], r["xa"] = (3.0 if r["event"] == 1 else 0.0), 0.0
            elif r["player_id"] == steady["id"]:
                r["xg"], r["xa"] = 0.5, 0.0
        return d, spike, steady

    def test_ordering_and_projection_ignore_the_variants(self):
        d, spike, steady = self._spike_world()
        cands, _, _ = E.wildcard_candidates(d)
        seen = {c["id"]: c for c in cands[3]}
        s, t = seen[spike["id"]], seen[steady["id"]]
        self.assertAlmostEqual(s["xgi90"], 3.0 / 450 * 90, 6)
        self.assertAlmostEqual(t["xgi90"], 2.5 / 450 * 90, 6)
        self.assertAlmostEqual(s["var"]["conc"], 1.0, 9)
        self.assertAlmostEqual(s["var"]["trim90"], 0.0, 9)
        self.assertAlmostEqual(t["var"]["trim90"], 0.5, 9)
        self.assertGreater(t["var"]["med90"], s["var"]["med90"])
        self.assertAlmostEqual(s["p_start"], t["p_start"], 9)
        order = [c["id"] for c in cands[3]]
        self.assertLess(order.index(spike["id"]), order.index(steady["id"]),
                        "the ordering left the raw rate")
        self.assertEqual(s["xgi90"], s["var"]["raw90"], "the ordering rate is the raw rate")
        inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=d["gameweek"])
        self.assertAlmostEqual(inp["players"][spike["id"]]["xgi90"], s["var"]["raw90"], 9,
                               "the rate the projection consumes is not the raw rate")

    def test_columns_printed_in_the_shortlists_xi_and_squad_section(self):
        d, spike, steady = self._spike_world()
        out = run("wildcard", d)
        short = out.split("SHORTLISTS")[1].split("SQUAD")[0]
        self.assertIn(f"{'xGI/90':>8}{'conc':>6}{'trim90':>7}{'med90':>7}", short)
        line = next(l for l in short.splitlines() if l.strip().startswith(spike["web_name"][:14]))
        self.assertIn("1.00!", line)
        self.assertTrue(line.rstrip().endswith("0.00"), line)
        xi_block = out.split("SQUAD")[1].split("BENCH")[0]
        line = next(l for l in xi_block.splitlines() if l.strip().startswith("MID " + spike["web_name"][:14]))
        self.assertIn("conc/trim/med", line)
        self.assertIn("1.00!", line)
        self.assertIn("printed, never ordered or projected on", out)
        me = E.my_name(d)
        row = next(r for r in d["squads"] if r["entry_name"] == me)
        for r in d["squads"]:                       # put the spike in my squad
            if r["entry_name"] == me and r["pos"] == 3:
                r["web_name"], r["team"] = spike["web_name"], spike["team"]
                break
        sq = run("squad", d)
        self.assertIn(f"{'xGI/90':>8}{'conc':>6}{'trim90':>7}{'med90':>7}", sq)
        line = next(l for l in sq.splitlines() if spike["web_name"][:14] in l and l[:3] in ("XI ", "BEN"))
        self.assertIn("1.00!", line)
        self.assertRegex(line, r"fdr\s*\d\.\d\s+0\.60\s+1\.00!")
        self.assertIn("nothing orders or projects on them", sq)


class ConcentrationTest(unittest.TestCase):
    """F (2)/(3): the pre-registered harness on synthetic data only."""

    @staticmethod
    def _spiked(gws=8):
        """_model_world with MID 4's xGI concentrated in GW1."""
        c = _model_world(gws)
        for r in c["rows"]:
            if r["player_id"] == 4:
                r["xg"], r["xa"] = (2.0, 1.0) if r["event"] == 1 else (0.05, 0.0)
        return c

    def test_metrics_are_p_start_times_fixtures_times_rate_for_mid_fwd_only(self):
        c = self._spiked()
        rows = {r["pid"]: r for r in H.concentration_rows(c, 6, hs=(1, 2))}
        self.assertTrue(rows and all(r["pos"] in (3, 4) for r in rows.values()))
        self.assertNotIn(2, rows, "a defender was included")
        train = E.canonical_through(c, 5)
        inp = E.reliability_inputs(train, gws_played=5)
        var = E.xgi_rate_variants(train["rows"])
        r4 = rows[4]["H"][2]
        base = inp["players"][4]["p_start"] * 2
        self.assertAlmostEqual(r4["raw"], base * inp["players"][4]["xgi90"], 9)
        self.assertAlmostEqual(r4["trim90"], base * var[4]["trim90"], 9)
        self.assertAlmostEqual(r4["med90"], base * var[4]["med90"], 9)
        self.assertLess(r4["trim90"], r4["raw"], "the spike was not trimmed")
        self.assertEqual(rows[4]["H"][1]["actual"] + 0, sum(r["pts"] for r in c["rows"]
                                                            if r["player_id"] == 4 and r["event"] == 6))
        nfx = {}
        for m in c["team_matches"]:
            if m["event"] in (6, 7):
                nfx[m["team"]] = nfx.get(m["team"], 0) + 1
        for pid, r in rows.items():                 # every row: P(start) x fixtures x rate
            p = inp["players"][pid]
            self.assertAlmostEqual(r["H"][2]["raw"], p["p_start"] * nfx[p["team"]] * (p["xgi90"] or 0.0), 9)
        self.assertIn(12, rows, "the never-starter passes the minutes gate")
        self.assertEqual(inp["players"][12]["p_start"], 0.0)
        self.assertEqual(rows[12]["H"][2]["raw"], 0.0, "a never-starter must carry P(start) = 0")

    def test_an_undefined_variant_falls_back_to_raw(self):
        c = self._spiked()
        rows = {r["pid"]: r for r in H.concentration_rows(c, 4, hs=(1,))}   # 3 training games
        self.assertIsNone(E.xgi_rate_variants(E.canonical_through(c, 3)["rows"])[4]["trim90"])
        self.assertEqual(rows[4]["H"][1]["trim90"], rows[4]["H"][1]["raw"])
        self.assertNotEqual(rows[4]["H"][1]["med90"], rows[4]["H"][1]["raw"])

    def test_target_weeks_do_not_leak_and_incomplete_horizons_are_skipped(self):
        c = self._spiked()
        a = {r["pid"]: r for r in H.concentration_rows(c, 6, hs=(1, 2))}
        leaky = dict(c, rows=[dict(r, xg=r["xg"] + 5, pts=r["pts"] + 20, starts=0, minutes=0)
                              if r["event"] >= 6 else r for r in c["rows"]])
        b = {r["pid"]: r for r in H.concentration_rows(leaky, 6, hs=(1, 2))}
        self.assertEqual(set(a), set(b))
        for pid in a:
            for Hn in (1, 2):
                for k in ("raw", "trim90", "med90"):
                    self.assertEqual(a[pid]["H"][Hn][k], b[pid]["H"][Hn][k], f"{pid} {Hn} {k} leaked")
        last = {r["pid"]: r for r in H.concentration_rows(c, 8, hs=(1, 2))}
        self.assertEqual(set(last[4]["H"]), {1}, "an incomplete horizon was graded")

    def test_paired_bootstrap_is_seeded_paired_and_finds_a_real_gain(self):
        import random
        rng = random.Random(1)
        act = [rng.random() * 10 for _ in range(300)]
        good = [a + rng.gauss(0, 1) for a in act]
        noise = [rng.random() * 10 for _ in act]
        res = H.paired_delta_intervals({"raw": noise, "trim90": good, "med90": list(noise)}, act, B=200)
        again = H.paired_delta_intervals({"raw": noise, "trim90": good, "med90": list(noise)}, act, B=200)
        self.assertEqual(res, again, "not seeded")
        d, lo, hi = res["trim90"]
        self.assertGreater(lo, 0, "a real gain did not exclude zero")
        self.assertGreater(d, 0.5)
        self.assertEqual(res["med90"], (0.0, 0.0, 0.0), "identical predictions must give a zero interval")

    def test_rule_needs_both_positions_above_raw_with_intervals_excluding_zero(self):
        win = {3: (0.30, 0.34, +0.01, +0.07), 4: (0.31, 0.36, +0.02, +0.08)}
        one = {3: (0.30, 0.34, +0.01, +0.07), 4: (0.31, 0.30, -0.05, +0.03)}
        wide = {3: (0.30, 0.34, -0.01, +0.09), 4: (0.31, 0.36, +0.02, +0.08)}
        self.assertEqual(H.concentration_rule({"trim90": win, "med90": one}), "trim90")
        self.assertEqual(H.concentration_rule({"trim90": one, "med90": one}), "raw")
        self.assertEqual(H.concentration_rule({"trim90": wide, "med90": one}), "raw")
        bigger = {3: (0.30, 0.40, +0.05, +0.15), 4: (0.31, 0.36, +0.02, +0.08)}
        self.assertEqual(H.concentration_rule({"trim90": win, "med90": bigger}), "med90")
        self.assertEqual(H.concentration_rule({"trim90": {3: win[3]}, "med90": one}), "raw")

    def test_report_carries_both_horizons_the_pairs_and_the_verdict(self):
        c = self._spiked(gws=12)
        text, verdict, stats = H.concentration_report(c, first=5, B=50)
        by_origin = {t: H.concentration_rows(c, t, hs=(1, 6)) for t in range(5, 13)}

        def pooled(Hn, pos):
            sel = [r["H"][Hn] for t in by_origin for r in by_origin[t]
                   if Hn in r["H"] and r["pos"] == pos]
            return E._spearman([s["raw"] for s in sel], [s["actual"] for s in sel])

        self.assertAlmostEqual(stats["trim90"][3][0], pooled(6, 3), 9, "the verdict is not fed by H = 6")
        self.assertAlmostEqual(stats["med90"][4][0], pooled(6, 4), 9)
        self.assertNotAlmostEqual(pooled(6, 3), pooled(1, 3), 3, "fixture cannot tell H = 1 from H = 6")
        self.assertIn("H = 1 ", text)
        self.assertIn("H = 6 ", text)
        self.assertIn("(decides)", text)
        self.assertIn("(reported only)", text)
        self.assertRegex(text, r"(?m)^    MID  trim90\s+rho [+-]\d\.\d{3} v raw [+-]\d\.\d{3}   delta")
        self.assertRegex(text, r"(?m)^    FWD  med90\s+rho ")
        self.assertEqual(text.count("(decides)"), 1)
        self.assertIn("VERDICT:", text)
        self.assertIn(verdict, ("raw", "trim90", "med90"))
        self.assertIn("Pre-registered 2026-09-24", text)


class BoostOnDraft(unittest.TestCase):
    """G: the wildcard's appended bench_boost block is the existing screen on
    the drafted fifteen - byte-identical to a direct call on the same ids."""

    def test_wildcard_appends_the_screen_for_the_drafted_fifteen(self):
        d = make_export()
        out = run("wildcard", d)
        marker = "BENCH BOOST SCREEN  ("
        self.assertEqual(out.count(marker), 1, "the screen must appear exactly once")
        block = out[out.index(marker):]
        cands, _, _ = E.wildcard_candidates(d)
        budget = d["standings"][0]["value"] / 10
        squad, _, _ = E.build_three_layer_squad(cands, budget, E.budget_split(d, budget))
        ids = [c["id"] for c in squad]
        self.assertEqual(len(ids), 15)
        self.assertNotEqual(sorted(ids), sorted(E.my_squad_ids(d)),
                            "fixture cannot tell the draft from my current 15")
        buf = io.StringIO()
        with redirect_stdout(buf):
            E.sec_bench_boost(d, 6, ids)
        direct = buf.getvalue()
        self.assertEqual(block, direct[direct.index(marker):],
                         "the appended block is not the screen on the drafted ids")
        gw = d["gameweek"]
        for w in range(gw + 1, gw + 7):
            self.assertIn(f"  GW{w}\n", block, f"GW{w} missing from the appended screen")
        self.assertIn("GK/DEF at FDR 4+", block)
        self.assertIn("XI from this 15", block)
        self.assertIn("best XI, same budget, fodder bench", block)
        self.assertIn("BENCH BOOST SCREEN FOR THIS DRAFT", out)
        self.assertLess(out.index("XI six-week sum"), out.index(marker), "the screen must follow the squad")


class SyncNetwork(unittest.TestCase):
    """J: a browser-style User-Agent, three retries with doubling backoff, and
    a sync that says so when a request never succeeded."""

    API = "https://fantasy.premierleague.com/api/"

    @staticmethod
    def _ns(full=False):
        ns = {"__name__": "fpl_sync_under_test"}
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "fpl_sync.py"), encoding="utf-8").read()
        exec(compile(src if full else src.split("def main()")[0], "fpl_sync", "exec"), ns)
        ns["sleeps"] = []
        ns["_sleep"] = ns["sleeps"].append
        return ns

    @staticmethod
    def _reply(payload):
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    def test_user_agent_is_a_browser_not_a_script(self):
        ns, seen = self._ns(), []

        def opener(req, timeout=30):
            seen.append(req)
            return self._reply({"ok": 1})

        ns["_urlopen"] = opener
        self.assertEqual(ns["get"]("bootstrap-static/"), {"ok": 1})
        ua = seen[0].get_header("User-agent")
        self.assertTrue(ua.startswith("Mozilla/5.0 ("), ua)
        self.assertIn("Chrome/", ua)
        self.assertIn("Safari/", ua)
        for tell in ("fpl_sync", "python", "urllib"):
            self.assertNotIn(tell, ua.lower())
        self.assertEqual(seen[0].full_url, self.API + "bootstrap-static/")

    def test_two_failures_then_success_backs_off_two_then_four_seconds(self):
        ns, calls = self._ns(), []

        def opener(req, timeout=30):
            calls.append(req.full_url)
            if len(calls) < 3:
                raise OSError("HTTP Error 503")
            return self._reply({"ok": 2})

        ns["_urlopen"] = opener
        with redirect_stdout(io.StringIO()):
            self.assertEqual(ns["get"]("fixtures/"), {"ok": 2})
        self.assertEqual(len(calls), 3)
        self.assertEqual(ns["sleeps"], [2.0, 4.0, ns["PAUSE"]])
        self.assertEqual(ns["FAILED"], [])

    def test_a_request_that_never_succeeds_gets_three_retries_and_is_counted(self):
        ns, calls = self._ns(), []

        def opener(req, timeout=30):
            calls.append(req.full_url)
            raise OSError("HTTP Error 403: Forbidden")

        ns["_urlopen"] = opener
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertIsNone(ns["get"]("fixtures/"))
        self.assertEqual(len(calls), 4, "one attempt and three retries")
        self.assertEqual(ns["sleeps"], [2.0, 4.0, 8.0])
        self.assertEqual(ns["FAILED"], [self.API + "fixtures/"])
        self.assertIn("! failed", buf.getvalue())

    def _main(self, fixtures_fail):
        ns = self._ns(full=True)
        boot = {"teams": [], "elements": [], "events": [
            {"id": 1, "name": "GW1", "deadline_time": "2026-08-15T10:00:00Z",
             "finished": True, "data_checked": True, "is_current": True}]}

        def opener(req, timeout=30):
            url = req.full_url
            if "bootstrap-static" in url:
                return self._reply(boot)
            if "fixtures" in url:
                if fixtures_fail:
                    raise OSError("HTTP Error 503")
                return self._reply([])
            if "/live/" in url:
                return self._reply({"elements": []})
            if "leagues-classic" in url:
                return self._reply({"standings": {"results": []}})
            raise AssertionError("unexpected request " + url)

        ns["_urlopen"] = opener
        tmp, cwd, argv = tempfile.mkdtemp(), os.getcwd(), sys.argv
        ns["DB_PATH"] = os.path.join(tmp, "t.sqlite")
        try:
            os.chdir(tmp)
            sys.argv = ["fpl_sync.py"]
            code = 0
            with redirect_stdout(io.StringIO()):
                try:
                    ns["main"]()
                except SystemExit as e:
                    code = e.code
            return code, os.path.exists("fpl_export_gw1.json")
        finally:
            os.chdir(cwd)
            sys.argv = argv
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_partial_sync_still_exports_and_exits_nonzero(self):
        code, exported = self._main(fixtures_fail=True)
        self.assertIn("SYNC INCOMPLETE: 1 request", str(code))
        self.assertTrue(exported, "the export was not written from what was fetched")

    def test_a_clean_sync_exits_zero(self):
        code, exported = self._main(fixtures_fail=False)
        self.assertEqual(code, 0)
        self.assertTrue(exported)

    def test_every_endpoint_is_public_no_login_needed(self):
        import re
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "fpl_sync.py"), encoding="utf-8").read()
        paths = set(re.findall(r'(?<![.\w])get\(f?"([^"]+)"\)', src))
        self.assertEqual(paths, {
            "bootstrap-static/", "fixtures/", "event/{gw}/live/", "element-summary/{pid}/",
            "leagues-classic/{LEAGUE_ID}/standings/", "entry/{eid}/history/",
            "entry/{eid}/transfers/", "entry/{eid}/event/{gw}/picks/"},
            "a new endpoint: check that it needs no login before it reaches the runner")
        for needs_login in ("my-team", "/me/", "cookie", "password", "login"):
            self.assertNotIn(needs_login, src.lower())


NIGHTLY_EDGE_STUB = EDGE_STUB.replace(
    'print("EDGE", " ".join(a))',
    'mode = open("MODE").read().strip()\n'
    'if "--watch" in a:\n'
    '    if mode == "nowatch":\n        sys.exit(1)\n'
    '    open(a[a.index("--out") + 1], "w").write("WATCH STUB\\n")\n    sys.exit(0)\n'
    'if mode == "noreport":\n    sys.exit(1)\n'
    'print("EDGE", " ".join(a))')


class NightlyRunner(unittest.TestCase):
    """J: fpl_nightly.py - the steps of fpl_run.bat on any platform, the Drive
    shipping replaced by files the workflow commits; any failure is red."""

    STAMP = "2026-10-05"
    FOUR = ("own", "xg", "minutes", "bottomup")

    @staticmethod
    def _put(path, body):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)

    @staticmethod
    def _get(path):
        with open(path, encoding="utf-8") as fh:
            return fh.read()

    def _world(self, mode="clean", tests=0, sync=0, export=True, edge=None):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        stubs = {"test_fpl.py": f"import sys\nsys.exit({tests})\n",
                 "fpl_sync.py": f"import sys\nprint('sync ran')\nsys.exit({sync})\n",
                 "fpl_edge.py": edge or NIGHTLY_EDGE_STUB, "MODE": mode}
        if export:
            stubs["fpl_export_gw3.json"] = "{}"
        for name, body in stubs.items():
            self._put(os.path.join(tmp, name), body)
        return tmp

    def _run(self, tmp):
        console = []
        code = N.nightly(root=tmp, stamp=self.STAMP, echo=console.append)
        log = self._get(os.path.join(tmp, "logs", f"run_{self.STAMP}.log"))
        return code, [l.strip() for l in log.splitlines()], [l.strip() for l in console]

    def test_clean_run_logs_reports_archives_and_exits_zero(self):
        tmp = self._world()
        real_ship, real_backup, calls = SHIP.ship, SHIP.backup_db, []
        SHIP.ship = lambda *a, **k: calls.append("ship") or 0
        SHIP.backup_db = lambda *a, **k: calls.append("backup_db") or ("", [])
        try:
            code, log, console = self._run(tmp)
        finally:
            SHIP.ship, SHIP.backup_db = real_ship, real_backup
        self.assertEqual(calls, [], "the runner path must never ship to Drive or back up the database")
        self.assertEqual(code, 0, log)
        summary = log[log.index("record summary:") + 1:]
        self.assertEqual(summary[:4], [f"RECORD OK {s} 5" for s in self.FOUR])
        order = [log.index(x) for x in ("running tests ...", "syncing FPL API ...",
                                        "recording forecasts for next GW ...",
                                        "building report ...", "record summary:",
                                        "archiving the export ...")]
        self.assertEqual(order, sorted(order), "the steps ran out of order")
        self.assertIn("sync ran", log)
        self.assertIn("EDGE --diff --out " + os.path.join("reports", f"fpl_{self.STAMP}.txt"), log)
        dated = os.path.join(tmp, "exports", f"fpl_export_gw3_{self.STAMP}.json")
        self.assertEqual(self._get(dated), "{}", "tonight's export was not kept under its date")
        self.assertTrue(log[-1].startswith("Done"), log[-3:])
        self.assertEqual(log, console, "the console and the committed log differ")
        for local_only in ("archive", "backup", "outbox"):
            self.assertFalse(os.path.exists(os.path.join(tmp, local_only)),
                             f"{local_only}/ belongs to the local path")
        self.assertFalse(any("SHIP" in l or "Drive" in l for l in log))

    def test_a_silent_record_crash_is_caught_and_the_run_is_red(self):
        code, log, _ = self._run(self._world(mode="broken"))
        summary = log[log.index("record summary:") + 1:]
        per = {s: [l for l in summary if l.startswith("RECORD ") and l.split()[2] == s]
               for s in self.FOUR}
        self.assertEqual({s: len(v) for s, v in per.items()}, dict.fromkeys(self.FOUR, 1))
        self.assertEqual(per["own"][0], "RECORD OK own 5")
        self.assertEqual(per["minutes"][0], "RECORD FAIL minutes locked")
        self.assertTrue(per["xg"][0].startswith("RECORD FAIL xg python exited"),
                        "a crash with no status line went unreported")
        self.assertTrue(any(l.startswith("EDGE --diff") for l in log),
                        "a failed record stopped the report")
        self.assertTrue(any(l.startswith("ARCHIVE OK") for l in log))
        self.assertEqual(log[-1], "FINISHED WITH ERRORS: record")
        self.assertEqual(code, 1)

    def test_red_tests_block_the_record_but_not_the_report(self):
        code, log, _ = self._run(self._world(tests=1))
        self.assertEqual(code, 1)
        self.assertIn("SKIPPED --record: test suite is red, no forecasts written", log)
        summary = log[log.index("record summary:") + 1:]
        self.assertEqual(summary[:4],
                         [f"RECORD FAIL {s} skipped - test suite is red" for s in self.FOUR])
        self.assertFalse(any(l.startswith("RECORD OK") for l in log),
                         "a forecast was recorded on a red suite")
        self.assertTrue(any(l.startswith("EDGE --diff") for l in log))
        self.assertEqual(log[-1], "FINISHED WITH ERRORS: tests, record")

    def test_sync_failure_continues_on_existing_data_and_is_red(self):
        code, log, _ = self._run(self._world(sync=1))
        self.assertIn("SYNC FAILED - continuing with existing data", log)
        summary = log[log.index("record summary:") + 1:]
        self.assertEqual(summary[:4], [f"RECORD OK {s} 5" for s in self.FOUR])
        self.assertTrue(any(l.startswith("EDGE --diff") for l in log))
        self.assertEqual(log[-1], "FINISHED WITH ERRORS: sync")
        self.assertEqual(code, 1, "on the runner a failed sync must turn the run red")

    def test_report_failure_is_red(self):
        code, log, _ = self._run(self._world(mode="noreport"))
        self.assertIn("EDGE FAILED", log)
        self.assertEqual(log[-1], "FINISHED WITH ERRORS: report")
        self.assertEqual(code, 1)

    def test_watch_file_is_written_after_the_record_and_before_the_report(self):
        tmp = self._world()
        self._put(os.path.join(tmp, "watchlist.txt"), "# two\n109\n82\n")
        code, log, _ = self._run(tmp)
        self.assertEqual(code, 0, log)
        order = [log.index(x) for x in ("recording forecasts for next GW ...",
                                        "writing the watch file ...", "building report ...")]
        self.assertEqual(order, sorted(order), "the watch file must follow the record and precede the report")
        self.assertEqual(self._get(os.path.join(tmp, "reports", f"watch_{self.STAMP}.txt")), "WATCH STUB\n")

    def test_missing_watchlist_is_skipped_not_red(self):
        code, log, _ = self._run(self._world())
        self.assertIn("WATCH skipped: no watchlist.txt", log)
        self.assertEqual(code, 0)

    def test_watch_failure_is_red_but_the_report_still_runs(self):
        tmp = self._world(mode="nowatch")
        self._put(os.path.join(tmp, "watchlist.txt"), "109\n")
        code, log, _ = self._run(tmp)
        self.assertIn("WATCH FAILED", log)
        self.assertTrue(any(l.startswith("EDGE --diff") for l in log))
        self.assertEqual(log[-1], "FINISHED WITH ERRORS: watch")
        self.assertEqual(code, 1)

    def test_fresh_checkout_restores_the_newest_dated_export_per_gameweek(self):
        tmp = self._world(export=False)
        os.makedirs(os.path.join(tmp, "exports"))
        for name, body in (("fpl_export_gw4_2026-09-17.json", "four"),
                           ("fpl_export_gw5_2026-10-01.json", "old five"),
                           ("fpl_export_gw5_2026-10-04.json", "new five"),
                           ("fpl_export_gw5.json", "not dated"), ("notes.txt", "x")):
            self._put(os.path.join(tmp, "exports", name), body)
        code, log, _ = self._run(tmp)
        self.assertEqual(code, 0, log)
        self.assertEqual(self._get(os.path.join(tmp, "fpl_export_gw4.json")), "four")
        self.assertEqual(self._get(os.path.join(tmp, "fpl_export_gw5.json")), "new five")
        self.assertLess(
            log.index("RESTORED     fpl_export_gw5_2026-10-04.json -> fpl_export_gw5.json"),
            log.index("running tests ..."), "the working exports must be back before any step")
        self.assertEqual(self._get(os.path.join(tmp, "exports", f"fpl_export_gw5_{self.STAMP}.json")),
                         "new five")
        self._put(os.path.join(tmp, "fpl_export_gw5.json"), "synced tonight")
        self.assertEqual(N.restore_exports(tmp, lambda line: None), [])
        self.assertEqual(self._get(os.path.join(tmp, "fpl_export_gw5.json")), "synced tonight",
                         "a working export already in place was overwritten")

    def test_no_export_anywhere_fails_the_archive(self):
        code, log, _ = self._run(self._world(export=False))
        self.assertIn("ARCHIVE FAILED: no fpl_export_gw*.json in this folder", log)
        self.assertEqual(log[-1], "FINISHED WITH ERRORS: archive")
        self.assertEqual(code, 1)

    def test_a_second_run_the_same_day_appends_to_the_log(self):
        tmp = self._world()
        self._run(tmp)
        _, log, _ = self._run(tmp)
        self.assertEqual(sum(1 for l in log if l.startswith("==== run ")), 2)

    def _real_world(self):
        here = os.path.dirname(os.path.abspath(__file__))
        tmp = self._world(export=False, edge=self._get(os.path.join(here, "fpl_edge.py")))
        with open(os.path.join(tmp, "fpl_export_gw3.json"), "w", encoding="utf-8") as fh:
            json.dump(self.export, fh)
        with open(os.path.join(tmp, "fpl_export_gw2.json"), "w", encoding="utf-8") as fh:
            json.dump(self.previous, fh)
        return tmp

    def test_the_real_record_and_report_need_no_database(self):
        self.export, self.previous = _recordable_export(), make_export(gw=2)
        tmp = self._real_world()
        code, log, _ = self._run(tmp)
        self.assertEqual(code, 0, log[-12:])
        summary = log[log.index("record summary:") + 1:][:4]
        for s, line in zip(self.FOUR, summary):
            self.assertRegex(line, rf"^RECORD OK {s} [1-9]\d*$")
        rows = E.read_log(os.path.join(tmp, "projection_log.csv"))
        self.assertEqual({r["source"] for r in rows}, set(self.FOUR))
        self.assertGreater(os.path.getsize(os.path.join(tmp, "reports", f"fpl_{self.STAMP}.txt")), 1000)
        self.assertEqual([f for f in os.listdir(tmp) if "sqlite" in f], [],
                         "the record or the report touched a database")
        here = os.path.dirname(os.path.abspath(__file__))
        for name in ("fpl_edge.py", "fpl_nightly.py"):
            self.assertNotIn("import sqlite3", self._get(os.path.join(here, name)),
                             f"{name}: projection_log.csv must never depend on the database")

    @unittest.skipUnless(os.name == "nt", "runs fpl_run.bat under cmd.exe")
    def test_bat_and_nightly_write_the_same_forecasts_and_report(self):
        here = os.path.dirname(os.path.abspath(__file__))
        self.export, self.previous = _recordable_export(), make_export(gw=2)
        bat, run = self._real_world(), self._real_world()
        shutil.copy(os.path.join(here, "fpl_run.bat"), bat)
        self._put(os.path.join(bat, "fpl_ship.py"), "print('SHIP STUB')\n")
        r = subprocess.run(["cmd", "/c", os.path.join(bat, "fpl_run.bat")], cwd=bat,
                           timeout=300, capture_output=True, text=True, errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout)
        reports = [f for f in os.listdir(os.path.join(bat, "reports")) if f.startswith("fpl_")]
        self.assertEqual(len(reports), 1)
        self.assertEqual(N.nightly(root=run, stamp=reports[0][4:-4], echo=lambda line: None), 0)
        with open(os.path.join(bat, "reports", reports[0]), "rb") as fh:
            a = fh.read()
        with open(os.path.join(run, "reports", reports[0]), "rb") as fh:
            b = fh.read()
        self.assertGreater(len(a), 1000)
        self.assertEqual(a, b, "the two paths wrote different reports for the same export")
        key = lambda r: tuple(r[k] for k in E.LOG_FIELDS if k != "made_at")
        la = [key(r) for r in E.read_log(os.path.join(bat, "projection_log.csv"))]
        lb = [key(r) for r in E.read_log(os.path.join(run, "projection_log.csv"))]
        self.assertGreater(len(la), 100)
        self.assertEqual(la, lb, "the two paths recorded different forecasts for the same export")


class NightlyWorkflow(unittest.TestCase):
    """J: the workflow file, the stdlib-only requirements file and the ignore
    rules, pinned as text - there is no YAML parser in the standard library."""

    @staticmethod
    def _read(*parts):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, *parts), encoding="utf-8") as fh:
            return fh.read()

    def test_schedule_runner_and_steps(self):
        y = self._read(".github", "workflows", "nightly.yml")
        self.assertIn('- cron: "40 21 * * *"', y)
        self.assertIn("workflow_dispatch:", y)
        self.assertIn("runs-on: ubuntu-latest", y)
        self.assertIn("actions/setup-python@", y)
        self.assertIn("run: python -m pip install -r requirements.txt", y)
        self.assertIn("run: python fpl_nightly.py", y)
        self.assertLess(y.index("pip install -r requirements.txt"), y.index("run: python fpl_nightly.py"))
        code = "\n".join(l for l in y.splitlines() if not l.strip().startswith("#"))
        for foreign in ("\\", "My Drive", "outbox", "fpl_ship", "fpl_run.bat", "secrets."):
            self.assertNotIn(foreign, code, f"{foreign!r} has no place on the runner")

    def test_outputs_are_committed_back_even_from_a_red_run(self):
        y = self._read(".github", "workflows", "nightly.yml")
        self.assertIn("contents: write", y)
        commit = y[y.index("Commit outputs back"):]
        self.assertIn("if: always()", commit)
        add = next(l for l in commit.splitlines() if l.strip().startswith("git add "))
        self.assertEqual(set(add.split()[2:]),
                         {"projection_log.csv", "fpl.sqlite", "exports", "logs", "reports"})
        self.assertIn('git commit -m "nightly $(date -u +%F) [skip ci]"', commit)
        self.assertIn("git push", commit)
        self.assertLess(y.index("run: python fpl_nightly.py"), y.index("git add "))

    def test_requirements_install_nothing(self):
        lines = [l.strip() for l in self._read("requirements.txt").splitlines() if l.strip()]
        self.assertTrue(lines and all(l.startswith("#") for l in lines),
                        "stdlib only: a package line was added to requirements.txt")

    def test_ignore_and_attribute_rules_fit_two_writers(self):
        ignore = [l.strip() for l in self._read(".gitignore").splitlines()
                  if l.strip() and not l.startswith("#")]
        self.assertNotIn("fpl.sqlite", ignore,
                         "the database holds the only price history: it must be committed")
        self.assertIn("/fpl_export_gw*.json", ignore)
        self.assertNotIn("fpl_export_gw*.json", ignore, "unanchored, this ignores exports/ too")
        for tracked in ("reports/", "exports/", "logs/", "projection_log.csv"):
            self.assertNotIn(tracked, ignore)
        for local in ("archive/", "backup/", "outbox/", "projection_log.csv.tmp",
                      "reports/run_*.log"):
            self.assertIn(local, ignore)
        attrs = self._read(".gitattributes").splitlines()
        self.assertIn("projection_log.csv text eol=crlf", attrs)
        self.assertIn("fpl.sqlite binary", attrs)


class WatchFile(unittest.TestCase):
    """L: watchlist.txt -> reports/watch_<date>.txt - the watched ids and the
    top twelve per position, with the forecasts as recorded, under 15 KB."""

    SEED = [109, 82, 334, 8, 230, 229, 173, 12, 427, 542, 183, 290, 411, 249, 106, 124, 4, 379]

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.d = _recordable_export(blank_team="HUL", double_team="ARS")
        cls.log_path = os.path.join(cls.tmp, "projection_log.csv")
        with redirect_stdout(io.StringIO()):
            for src in ("own", "xg", "minutes", "bottomup"):
                E.record_projections(cls.d, 6, src, None, cls.log_path)
        cls.log = E.read_log(cls.log_path)
        cls.event = cls.d["gameweek"] + 1

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _write(self, name, body):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(body)
        return p

    def _recorded(self, pid):
        return {r["source"]: float(r["predicted"]) for r in self.log
                if int(r["player_id"]) == pid and int(r["event"]) == self.event}

    def test_watchlist_parses_ids_and_refuses_junk(self):
        p = self._write("wl.txt", "# watched\n109\n 82 # keeper\n\n334\n")
        self.assertEqual(E.read_watchlist(p), [109, 82, 334])
        p = self._write("bad.txt", "109\nSaka\n")
        with self.assertRaises(ValueError) as cm:
            E.read_watchlist(p)
        self.assertIn("line 2", str(cm.exception))

    def test_repo_watchlist_holds_the_seed(self):
        here = os.path.dirname(os.path.abspath(__file__))
        self.assertEqual(E.read_watchlist(os.path.join(here, "watchlist.txt")), self.SEED)

    def test_rows_carry_the_recorded_forecasts_fixture_and_news(self):
        d = self.d
        fxall = E.week_fixtures(d)                   # the double's opponent plays twice too
        starter = next(p for p in d["all_players"] if p["status"] == "a" and p["pos"] == 3
                       and len(fxall[p["team"]].get(self.event, [])) == 1)
        doubled = next(p for p in d["all_players"] if p["status"] == "a" and p["team"] == "ARS")
        blanked = next(p for p in d["all_players"] if p["status"] == "a" and p["team"] == "HUL")
        hurt = next(p for p in d["all_players"] if p["status"] == "d")
        hurt["news"] = "Knock -  " + "x" * 100
        rows = E.watch_rows(d, self.log, [starter["id"], doubled["id"], blanked["id"], hurt["id"], 99999])
        self.assertEqual([r["id"] for r in rows], [starter["id"], doubled["id"], blanked["id"], hurt["id"], 99999])
        want = self._recorded(starter["id"])
        self.assertEqual(set(want), {"own", "xg", "bottomup", "minutes"}, "fixture did not record all four")
        r = rows[0]
        self.assertEqual((r["name"], r["team"], r["pos"], r["price"], r["status"], r["chance"]),
                         (starter["web_name"], starter["team"], starter["pos"], starter["price"], "a", None))
        for src in want:
            self.assertEqual(r[src], want[src], f"{src} is not the recorded forecast")
        fx = E.week_fixtures(d)[starter["team"]][self.event]
        self.assertEqual(r["fixture"], f"{fx[0][0]} ({'H' if fx[0][1] else 'A'}) {fx[0][2]}")
        self.assertIn(" + ", rows[1]["fixture"], "a double must show both fixtures")
        self.assertEqual(rows[2]["fixture"], "BLANK")
        self.assertEqual((rows[3]["own"], rows[3]["xg"], rows[3]["bottomup"], rows[3]["minutes"]),
                         (None, None, None, None), "a player with no recorded forecast must read blank")
        self.assertEqual((rows[3]["status"], rows[3]["chance"]), ("d", 50))
        self.assertEqual(rows[3]["news"], "Knock - " + "x" * 100, "news must be whitespace-normalised, not cut here")
        self.assertIsNone(rows[4]["name"])
        text = E.watch_report(d, self.log, [starter["id"], hurt["id"], 99999])
        line = next(l for l in text.splitlines() if l.startswith(f"  {starter['id']:<6}"))
        seg = (f"{want['own']:.1f}".rjust(6) + f"{want['xg']:.1f}".rjust(6)
               + f"{want['bottomup']:.1f}".rjust(6) + f"{want['minutes']:.2f}".rjust(6))
        self.assertIn(seg, line, "own / xg / bottomup / minutes in that order")
        self.assertIn(r["fixture"], line)
        hurt_line = next(l for l in text.splitlines() if l.startswith(f"  {hurt['id']:<6}"))
        self.assertIn(" d   50", hurt_line)
        self.assertTrue(hurt_line.endswith("Knock - " + "x" * 52), "news cut at 60 characters")
        self.assertIn("     -     -     -     -", hurt_line)
        self.assertIn(f"  {99999:<6}(not in export)", text)
        self.assertTrue(text.startswith(f"WATCH  GW{self.event}  export "))
        self.assertIn("forecasts recorded " + self.log[-1]["made_at"][:16], text)

    def test_top_twelve_per_position_by_own(self):
        tops = E.watch_top(self.d, self.log)
        by_pos = {}
        for r in self.log:
            if r["source"] == "own" and int(r["event"]) == self.event:
                p = next(p for p in self.d["all_players"] if p["id"] == int(r["player_id"]))
                by_pos.setdefault(p["pos"], []).append((-float(r["predicted"]), p["id"]))
        for pos in (1, 2, 3, 4):
            want = [pid for _, pid in sorted(by_pos[pos])[:12]]
            self.assertEqual([r["id"] for r in tops[pos]], want, f"{E.POS[pos]}: not the top 12 by own")
            self.assertLessEqual(len(tops[pos]), 12)
        self.assertEqual(len(tops[2]), 12, "twenty defenders must give a full twelve")
        text = E.watch_report(self.d, self.log, [])
        block = text.split("TOP 12 PER POSITION BY OWN")[1]
        self.assertEqual(sum(1 for l in block.splitlines() if l.startswith("  ") and l[2:8].strip().isdigit()),
                         sum(len(tops[pos]) for pos in (1, 2, 3, 4)))

    def test_file_stays_under_15kb(self):
        for p in self.d["all_players"]:
            p["news"] = "Long news " * 12
        normal = E.watch_report(self.d, self.log, self.SEED)
        self.assertLess(len(normal.encode("utf-8")), 15000)
        self.assertNotIn("truncated", normal)
        flood = E.watch_report(self.d, self.log, [p["id"] for p in self.d["all_players"]] * 6)
        self.assertLessEqual(len(flood.encode("utf-8")), 15000, "the watch file must stay under 15 KB")
        self.assertRegex(flood.splitlines()[-1], r"^  \.\.\. truncated to stay under 15 KB \(\d+ lines dropped\)$")
        self.assertGreater(len(flood.splitlines()), 50, "truncation dropped far more than it had to")
        for p in self.d["all_players"]:
            p["news"] = ""

    def test_cli_writes_the_file_from_the_log(self):
        export = self._write("fpl_export_gw3.json", json.dumps(self.d))
        recorded = next(int(r["player_id"]) for r in self.log
                        if r["source"] == "own" and int(r["event"]) == self.event)
        ids = (1, 9, recorded, 49)
        wl = self._write("watchlist.txt", "# mine\n" + "\n".join(str(i) for i in ids) + "\n")
        out = os.path.join(self.tmp, "watch_2026-10-07.txt")
        argv, cwd = sys.argv, os.getcwd()
        try:
            os.chdir(self.tmp)                     # projection_log.csv is read from here
            sys.argv = ["fpl_edge.py", export, "--watch", wl, "--out", out]
            with redirect_stdout(io.StringIO()):
                E.main()
            text = open(out, encoding="utf-8").read()
            self.assertTrue(text.startswith(f"WATCH  GW{self.event}"))
            for pid in ids:
                self.assertTrue(any(l.startswith(f"  {pid:<6}") for l in text.splitlines()), pid)
            want = self._recorded(recorded)          # the forecasts come from projection_log.csv
            line = next(l for l in text.splitlines() if l.startswith(f"  {recorded:<6}"))
            self.assertIn(f"{want['own']:.1f}".rjust(6) + f"{want['xg']:.1f}".rjust(6), line,
                          "the CLI did not read the recorded forecasts")
            bad = self._write("bad.txt", "1\nnope\n")
            sys.argv = ["fpl_edge.py", export, "--watch", bad, "--out", out]
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    E.main()
            self.assertIn("WATCH FAILED", str(cm.exception.code))
            sys.argv = ["fpl_edge.py", export, "--watch", wl]
            with redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    E.main()
        finally:
            sys.argv = argv
            os.chdir(cwd)


class Hygiene(unittest.TestCase):

    def test_one_entry_league_does_not_crash_ownership(self):
        out = run("eo", make_export(n_entries=1))
        self.assertIn("no rivals", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
