"""tests/test_FJ.py - the GW10 checkpoint's script, worklog/checkpoint_gw10/checkpoint.py (prereg/FJ.md).

Boris's rulings of Thu 12 Nov night, FJ point 2 (verbatim in prereg/FJ.md): "Add tests/test_FJ.py (the sign of d;
the revert verdict on a toy; the tie order), since F-L re-runs this script at GW15."
Standard library only; no data, no network.
"""
import csv
import hashlib
import importlib.util
import io
import os
import re
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
_spec = importlib.util.spec_from_file_location("fj_checkpoint", os.path.join(ROOT, "worklog", "checkpoint_gw10", "checkpoint.py"))
CK = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CK)
import fpl_bt as BT                                               # noqa: E402
import fpl_chips as CH                                            # noqa: E402
import fpl_edge as E                                              # noqa: E402
import fpl_realised as RL                                         # noqa: E402

# a legal 15 in slot order (1 GK, 2 DEF, 3 MID, 4 FWD): three defenders without an own forecast (counted 0) tie for
# the third DEF place; in slot order the first of them is id 230 (slot 3), by id it is 8 (slot 14), as in GW9
SQUAD = [{"id": i, "pos": p} for i, p in (
    (11, 1), (21, 2), (230, 2), (22, 2), (31, 3), (32, 3), (33, 3), (34, 3), (35, 3), (41, 4), (42, 4),
    (12, 1), (43, 4), (8, 2), (173, 2))]
OWN = {11: 2.0, 12: 1.0, 21: 3.0, 22: 2.0, 31: 3.0, 32: 3.0, 33: 3.0, 34: 3.0, 35: 3.0, 41: 4.0, 42: 3.5, 43: 0.5}
ACTUAL = {i: (2.0, 90.0) for i in OWN}
ACTUAL.update({230: (9.0, 90.0), 8: (6.0, 90.0), 173: (0.0, 0.0)})


def xi_ids(squad, proj, tie):
    return {r["id"] for r in CK.choice(CK.ordered(squad, tie), proj, ACTUAL)[0]}


class TieOrder(unittest.TestCase):
    def test_slot_order_follows_the_picks_and_id_order_the_lower_id(self):
        self.assertIn(230, xi_ids(SQUAD, OWN, "slot"))
        self.assertNotIn(8, xi_ids(SQUAD, OWN, "slot"))
        self.assertIn(8, xi_ids(SQUAD, OWN, "id"))
        self.assertNotIn(230, xi_ids(SQUAD, OWN, "id"))
        slot = CK.score(SQUAD, OWN, OWN, ACTUAL, "slot")
        by_id = CK.score(SQUAD, OWN, OWN, ACTUAL, "id")
        self.assertEqual(slot[0] - by_id[0], 9.0 - 6.0)              # the tied defender's points, nothing else
        self.assertEqual([r["id"] for r in CK.ordered(SQUAD, "id")], sorted(r["id"] for r in SQUAD))
        self.assertEqual(CK.ordered(SQUAD, "slot"), SQUAD)
        with self.assertRaises(ValueError):
            CK.ordered(SQUAD, "name")

    def test_the_default_is_the_pinned_slot_order(self):
        self.assertEqual(CK.score(SQUAD, OWN, OWN, ACTUAL), CK.score(SQUAD, OWN, OWN, ACTUAL, "slot"))


class SignOfD(unittest.TestCase):
    def test_d_is_xp_v2_minus_own(self):
        self.assertEqual(CK.paired([41, 72, 62], [41, 68, 74]), [0, -4, 12])
        xp = {**OWN, 43: 5.0, 42: 0.4}                         # xp_v2 starts 43, who scores 12; own starts 42 (2)
        actual = {**ACTUAL, 43: (12.0, 90.0)}
        own_pts, _, v2_pts, cap_v2 = CK.score(SQUAD, OWN, xp, actual)
        self.assertEqual(cap_v2, 43)                                  # the highest xp_v2 in its XI, doubled
        d = CK.paired([own_pts], [v2_pts])[0]
        self.assertGreater(d, 0)
        self.assertEqual(d, v2_pts - own_pts)


class RevertVerdict(unittest.TestCase):
    def test_own_returns_only_when_the_upper_bound_is_below_zero(self):
        self.assertEqual(CK.verdict({"lo": -9.0, "hi": -0.01}), "own returns")
        self.assertEqual(CK.verdict({"lo": -9.0, "hi": 0.0}), "xp_v2 stays")
        self.assertEqual(CK.verdict({"lo": -2.67, "hi": 8.0}), "xp_v2 stays")
        self.assertEqual(CK.verdict({"lo": -9.0, "hi": 8.0}), "xp_v2 stays")    # never read off the lower bound

    def test_on_toy_gameweeks(self):
        worse = BT.bootstrap_mean([-5, -3, -4])
        self.assertLess(worse["hi"], 0)
        self.assertEqual(CK.verdict(worse), "own returns")
        gw10 = BT.bootstrap_mean([0, -4, 12])
        self.assertAlmostEqual(gw10["lo"], -8 / 3)
        self.assertEqual(gw10["hi"], 8.0)
        self.assertEqual(CK.verdict(gw10), "xp_v2 stays")


class GW15TieRule(unittest.TestCase):
    """The GW15 tie rule across positions (Boris, Mon 16 Nov, FJ point 3 (ii); prereg/FJ.md): when two
    formation-legal XIs have equal sums, the one whose sorted player-id list is lexicographically smallest."""

    # 2 GK, 5 DEF, 5 MID, 3 FWD; the last XI place is a tie between DEF id 5 and FWD id 300 (the verifier's toy)
    TOY = [{"id": i, "pos": p} for i, p in ((1, 1), (2, 1), (10, 2), (11, 2), (12, 2), (5, 2), (13, 2), (20, 3), (21, 3),
                                            (22, 3), (23, 3), (24, 3), (30, 4), (31, 4), (300, 4))]
    PROJ = {1: 5.0, 2: 1.0, 10: 6.0, 11: 6.0, 12: 6.0, 5: 2.0, 13: 0.5, 20: 6.0, 21: 6.0, 22: 6.0, 23: 6.0, 24: 1.0,
            30: 6.0, 31: 6.0, 300: 2.0}

    def test_a_tie_across_positions_goes_to_the_smallest_sorted_ids(self):
        xi, bench, gk = CK.xi_lex(self.TOY, self.PROJ)
        ids = {r["id"] for r in xi}
        self.assertIn(5, ids)
        self.assertNotIn(300, ids)
        self.assertEqual([r["id"] for r in bench], [300, 24, 13])           # forecast order, then the lower id
        self.assertEqual(gk["id"], 2)
        for order in (self.TOY, list(reversed(self.TOY)), sorted(self.TOY, key=lambda r: -r["id"])):
            self.assertEqual({r["id"] for r in CK.xi_lex(order, self.PROJ)[0]}, ids)   # input order never matters
        self.assertNotIn(5, {r["id"] for r in E._best_xi([dict(r, proj=self.PROJ[r["id"]]) for r in self.TOY])},
                         "the toy no longer shows _best_xi's first-formation tie")
        _, bench, _ = CK.xi_lex(self.TOY, {**self.PROJ, 24: 0.5})
        self.assertEqual([r["id"] for r in bench], [300, 13, 24])           # equal forecasts on the bench: lower id first

    def test_sums_are_compared_exactly(self):
        self.assertNotEqual(0.1 + 0.2, 0.3)                                 # as floats they differ
        self.assertEqual(CK._exact(0.1) + CK._exact(0.2), CK._exact(0.3))  # as the decimals written, a tie
        self.assertEqual(CK._exact(float("2.1500")), CK._exact(2.15))
        # the comparison xi_lex uses (W3fix point 4, Boris, Thu 19 Nov night: the float-sum mutant)
        a, b = [{"id": 1}, {"id": 2}], [{"id": 3}, {"id": 4}]
        val = {1: CK._exact(0.1), 2: CK._exact(0.2), 3: CK._exact(0.3), 4: CK._exact(0.0)}
        self.assertEqual(CK.xi_key(a, val)[0], CK.xi_key(b, val)[0])          # a tie, exactly
        self.assertLess(CK.xi_key(a, val), CK.xi_key(b, val))                  # settled by the smaller sorted ids

    def test_xi_lex_hands_its_key_exact_values(self):
        """W3fix answer 1 (Boris, Fri 27 Nov): every value xi_lex hands xi_key is a Fraction, and xi_key ranks every
        formation-legal XI - so a float sum inside xi_lex (values built as floats, or an inline float key that
        bypasses xi_key) is caught here, not only one inside xi_key."""
        from fractions import Fraction
        from itertools import combinations
        calls = []
        real = CK.xi_key

        def spy(xi, val):
            calls.append(all(isinstance(v, Fraction) for v in val.values()) and all(r["id"] in val for r in xi))
            return real(xi, val)

        legal = sum(1 for c in combinations(self.TOY, 11) if CK.legal(c))
        with mock.patch.object(CK, "xi_key", side_effect=spy):
            for proj in (self.PROJ, {k: v for k, v in self.PROJ.items() if k != 300},
                         {k: v + 0.1 for k, v in self.PROJ.items()}):
                del calls[:]
                CK.xi_lex(self.TOY, proj)
                self.assertEqual(len(calls), legal)
                self.assertTrue(all(calls))

    def test_a_missing_forecast_counts_zero(self):
        proj = {k: v for k, v in self.PROJ.items() if k != 300}               # FWD 300 has no forecast
        proj[5], proj[24] = 0.5, 0.0                                           # DEF 5 at 0.5: 300 at 1 would start instead
        ids = {r["id"] for r in CK.xi_lex(self.TOY, proj)[0]}
        self.assertIn(5, ids)
        self.assertNotIn(300, ids)

    def test_realised_lex_equals_realised_on_whenever_the_xis_agree(self):
        import random
        rng = random.Random(20261116)
        agree = 0
        for _ in range(300):
            proj = {r["id"]: round(rng.uniform(0, 8), 2) for r in SQUAD}
            actual = {r["id"]: (float(rng.randint(0, 12)), float(rng.choice([0, 0, 30, 90, 90, 90]))) for r in SQUAD}
            lex = {r["id"] for r in CK.xi_lex(SQUAD, proj)[0]}
            on = {r["id"] for r in CH.xi_and_bench([dict(r) for r in SQUAD], proj)[0]}
            if lex == on:
                agree += 1
                self.assertEqual(CK.realised_lex(SQUAD, proj, actual), RL.realised_on(SQUAD, proj, actual))
        self.assertGreater(agree, 250)

    def test_the_id_run_uses_the_rule(self):
        pts = {r["id"]: (2.0, 90.0) for r in self.TOY}
        pts[5], pts[300] = (10.0, 90.0), (0.0, 90.0)
        own_pts, _, _, _ = CK.score(self.TOY, self.PROJ, self.PROJ, pts, "id")
        self.assertEqual(own_pts, CK.realised_lex(self.TOY, self.PROJ, pts)[0])
        self.assertEqual(own_pts - CK.score(self.TOY, self.PROJ, self.PROJ, pts, "slot")[0], 10.0 - 0.0)


# --- the end-to-end test of main() (Boris, Mon 16 Nov, FJ point 3 (i); prereg/FJ.md) ------------------------------

DEADLINES = {8: "2026-10-23T17:30:00Z", 9: "2026-10-31T11:00:00Z", 10: "2026-11-07T11:00:00Z"}
BAD = {**OWN, 230: 0.0, 8: 0.0, 173: 5.0}           # starts 173, who plays no minutes in GW8 and GW10 and scores 1 in GW9
GOOD = {**OWN, 230: 0.0, 8: 0.0, 173: 0.0}


def week_actual(g):
    a = dict(ACTUAL)
    if g == 9:
        a[173] = (1.0, 90.0)
    if g == 10:
        a[230], a[8] = (4.0, 90.0), (1.0, 90.0)
    return a


def git(repo, *args, when=None):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.path.join(repo, "..", "empty.gitconfig"))
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, env=env)
    if r.returncode:
        raise AssertionError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


def build_toy(tmp, weeks, unlocked=()):
    """data/ (fpl.sqlite, projection_log.csv) and code/ (a git repo with each week's bundle committed before its
    deadline). weeks: {g: (own, xp)}; our picks in SQUAD's slot order; returns (data, code, {g: bundle commit})."""
    data, code = os.path.join(tmp, "data"), os.path.join(tmp, "code")
    os.makedirs(data)
    os.makedirs(code)
    open(os.path.join(tmp, "empty.gitconfig"), "w").close()
    c = sqlite3.connect(os.path.join(data, "fpl.sqlite"))
    c.executescript("""
      create table events(id integer, deadline_time text, finished integer, data_checked integer);
      create table fixtures(id integer, event integer, finished integer);
      create table players(id integer, position integer, web_name text);
      create table picks(entry_id integer, event integer, player_id integer, position integer);
      create table player_gw(player_id integer, event integer, total_points integer, minutes integer);
    """)
    c.executemany("insert into events values (?,?,?,?)",
                  [(g, DEADLINES[g], 1, 0 if g in unlocked else 1) for g in sorted(weeks)])
    c.executemany("insert into fixtures values (?,?,?)", [(g * 10 + k, g, 1) for g in weeks for k in (1, 2)])
    c.executemany("insert into players values (?,?,?)", [(r["id"], r["pos"], f"P{r['id']}") for r in SQUAD])
    for g in weeks:
        c.executemany("insert into picks values (?,?,?,?)", [(CK.ENTRY, g, r["id"], s) for s, r in enumerate(SQUAD, 1)])
        c.executemany("insert into player_gw values (?,?,?,?)",
                      [(pid, g, int(p), int(m)) for pid, (p, m) in week_actual(g).items()])
    c.commit()
    c.close()
    rows = []
    for g, (own, _) in weeks.items():
        made = DEADLINES[g].replace("17:30:00Z", "12:00:00+00:00").replace("11:00:00Z", "08:00:00+00:00")
        rows += [{"made_at": made, "source": "own", "event": str(g), "player_id": str(pid), "web_name": f"P{pid}",
                  "predicted": str(v)} for pid, v in own.items()]
    with open(os.path.join(data, "projection_log.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    git(code, "init", "-q")
    git(code, "config", "user.name", "toy")
    git(code, "config", "user.email", "toy@example.invalid")
    git(code, "config", "commit.gpgsign", "false")
    bundles = {}
    for g, (_, xp) in sorted(weeks.items()):
        folder = os.path.join(code, "worklog", "gw_pass", f"gw{g}")
        os.makedirs(folder)
        body = "id,xp_v2\n" + "".join(f"{pid},{v}\n" for pid, v in xp.items())
        with open(os.path.join(folder, "xp_v2_all.csv"), "w", encoding="utf-8", newline="") as fh:
            fh.write(body)
        when = DEADLINES[g].replace("17:30:00Z", "10:00:00+00:00").replace("11:00:00Z", "06:00:00+00:00")
        with open(os.path.join(folder, "run.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(f"tool: tools/gw_pass.py\ncommit: abcdef1\nend_utc: {when}\noutputs:\n"
                     f"  xp_v2_all.csv  sha256 {hashlib.sha256(body.encode('utf-8')).hexdigest()}\n")
        git(code, "add", "-A")
        git(code, "commit", "-q", "-m", f"bundle gw{g}", when=when)
        bundles[g] = git(code, "rev-parse", "HEAD")
    return data, code, bundles


class MainEndToEnd(unittest.TestCase):
    """main() on toy gameweeks: the printed numbers against realised_on run directly, the sign of d, the verdict,
    which model is which, the slot order of the picks, the run's tie rule, and the two guards."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_main(self, weeks, tie=None, unlocked=(), bundle=None):
        data, code, bundles = build_toy(self.tmp, weeks, unlocked)
        out = os.path.join(self.tmp, "out")
        argv = ["--code", code, "--data", data, "--out", out] + (["--tie", tie] if tie else [])
        with mock.patch.object(CK, "CODE", code), mock.patch.object(CK, "GWS", tuple(sorted(weeks))), \
                mock.patch.object(CK, "BUNDLE", bundle or {g: h[:7] for g, h in bundles.items()}), \
                redirect_stdout(io.StringIO()):
            CK.main(argv)
        with open(os.path.join(out, "checkpoint.txt"), encoding="utf-8") as fh:
            return fh.read()

    @staticmethod
    def expected(weeks, tie="slot"):
        """Per week (own, xp_v2) realised points straight from fpl_realised (slot) or xi_lex's rule (id)."""
        out = []
        for g, (own, xp) in sorted(weeks.items()):
            if tie == "slot":
                out.append((RL.realised_on(SQUAD, own, week_actual(g))[0], RL.realised_on(SQUAD, xp, week_actual(g))[0]))
            else:
                sq = sorted(SQUAD, key=lambda r: r["id"])
                out.append((CK.realised_lex(sq, own, week_actual(g))[0], CK.realised_lex(sq, xp, week_actual(g))[0]))
        return out

    def summary(self, text, weeks):
        got = {}
        for line in text.splitlines():
            m = re.match(r"^  (\d+)\s+(\d+)\s+(\d+)\s+([+-]\d+)   ", line)
            if m and int(m.group(1)) in weeks:
                got[int(m.group(1))] = tuple(int(x) for x in m.groups()[1:])
        return [got[g] for g in sorted(weeks)]

    def test_xp_v2_worse_every_week_own_returns(self):
        weeks = {g: (OWN, BAD) for g in (8, 9, 10)}
        text = self.run_main(weeks)
        want = self.expected(weeks)
        d = [v - o for o, v in want]
        self.assertTrue(all(x < 0 for x in d), d)                        # the toy: xp_v2 worse every week
        self.assertEqual(self.summary(text, weeks), [(o, v, v - o) for o, v in want])
        boot = BT.bootstrap_mean(d)
        self.assertIn(f"mean d = {boot['mean']:+.2f} a gameweek, 90% [{boot['lo']:+.2f}, {boot['hi']:+.2f}]", text)
        self.assertIn(f"Upper bound {boot['hi']:+.2f}: own returns.", text)
        self.assertIn("this run 'slot'", text)

    def test_mixed_weeks_xp_v2_stays_and_the_other_rule_is_information(self):
        weeks = {8: (OWN, BAD), 9: (BAD, GOOD), 10: (BAD, GOOD)}
        text = self.run_main(weeks)
        want = self.expected(weeks)
        d = [v - o for o, v in want]
        boot = BT.bootstrap_mean(d)
        self.assertTrue(boot["lo"] < 0 < boot["hi"], boot)                # read off the upper bound, never the lower
        self.assertEqual(self.summary(text, weeks), [(o, v, v - o) for o, v in want])
        self.assertIn(f"Upper bound {boot['hi']:+.2f}: xp_v2 stays.", text)
        alt = self.expected(weeks, "id")
        self.assertNotEqual(alt, want, "the toy must tell the two tie rules apart")
        self.assertIn(f"information, the other order 'id': own {', '.join(f'{o:.0f}' for o, _ in alt)}, "
                      f"xp_v2 {', '.join(f'{v:.0f}' for _, v in alt)}", text)

    def test_the_id_run_on_request(self):
        weeks = {8: (OWN, BAD), 9: (BAD, GOOD), 10: (BAD, GOOD)}
        text = self.run_main(weeks, tie="id")
        want = self.expected(weeks, "id")
        self.assertNotEqual(want, self.expected(weeks))
        self.assertEqual(self.summary(text, weeks), [(o, v, v - o) for o, v in want])
        self.assertIn("this run 'id'", text)

    def test_a_week_not_locked_down_stops(self):
        with self.assertRaises(CK.MissingInput):
            self.run_main({g: (OWN, BAD) for g in (8, 9, 10)}, unlocked=(9,))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out", "checkpoint.txt")))

    def test_a_bundle_other_than_the_ruled_one_stops(self):
        with self.assertRaises(CK.MissingInput):
            self.run_main({g: (OWN, BAD) for g in (8, 9, 10)}, bundle={8: "0000000", 9: "0000000", 10: "0000000"})
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out", "checkpoint.txt")))


if __name__ == "__main__":
    unittest.main()
