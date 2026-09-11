"""
test_fpl.py — regression tests for fpl_edge.py

    python test_fpl.py            run everything
    python test_fpl.py -v         verbose

Stdlib only. Builds synthetic exports in a temp folder, so it never touches
your real data and needs no network. Run it after editing either script.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                            # noqa: E402

TEAMS = ["ARS", "BHA", "CHE", "CRY", "HUL", "LIV", "MCI", "MUN", "NEW", "NFO"]
ENTRIES = ["My Team", "Rival A", "Rival B", "Rival C"]
MY_ID = 999
UNICODE_NAMES = ["Muharemović", "Groß", "João Pedro", "Ødegaard", "Horníček"]


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
                             "kickoff_time": f"2026-09-{10+ev:02d}T14:00:00Z"})
        if double_team and ev == gw + 1:
            opp = next(t for t in TEAMS if t != double_team)
            fixtures.append({"event": ev, "home": double_team, "away": opp,
                             "h_fdr": 2, "a_fdr": 2,
                             "kickoff_time": f"2026-09-{10+ev:02d}T18:00:00Z"})

    played = []
    for ev in range(1, gw + 1):
        for a, b in zip(TEAMS[0::2], TEAMS[1::2]):
            played.append({"event": ev, "home": a, "away": b,
                           "h_goals": (ev + len(a)) % 4, "a_goals": ev % 3,
                           "h_fdr": 2 + (ev % 3), "a_fdr": 2 + ((ev + 1) % 3),
                           "kickoff_time": f"2026-08-{20+ev:02d}T14:00:00Z"})

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
            {"event": ev, "web_name": p["web_name"], "team": p["team"],
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


class Hygiene(unittest.TestCase):

    def test_one_entry_league_does_not_crash_ownership(self):
        out = run("eo", make_export(n_entries=1))
        self.assertIn("no rivals", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
