"""tests/test_S16_part3.py - Step 16 parts 3-4: the cup Monte Carlo and its backtest
(prereg/S16.md, parts 3-4 and its amendment of 5 Nov). Hermetic: toys in memory or a
temporary folder. The real backtest is never run here. The last class checks the
hand-typed tables against the local historical files when they exist (not on the runner)."""
import csv
import io
import itertools
import os
import shutil
import sys
import tempfile
import unittest
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from unittest import mock

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tools"))

import blank_double as BD                             # noqa: E402
import cup_backtest as C                              # noqa: E402
import cup_mc as M                                    # noqa: E402

UTC = timezone.utc
HIST = os.environ.get("FPL_HISTORICAL", C.HIST)      # the local files, gitignored: a scratch checkout names them
SAT = date(2026, 8, 15)                               # a Saturday
SEASON = "2026-27"
NO_LEAGUE_DAY = date(2026, 6, 1)
LONG_AGO = SAT - timedelta(days=30)
CLUBS = ("A", "B", "C", "D", "E", "F")
WEEKLY = [("A", "C"), ("B", "D"), ("E", "F")]


def sat(gw, gaps=()):
    """Gameweek gw's Saturday: one a week, `gaps` the gameweeks followed by a two-week break."""
    return SAT + timedelta(days=7 * (gw - 1 + 2 * sum(1 for g in gaps if g < gw)))


def toy_season(gws=7, rows=None, gaps=(), day_of=None):
    """Weekly fixtures at 15:00 UTC; `rows` overrides a gameweek's fixtures, `day_of` its day."""
    fixtures = []
    for g in range(1, gws + 1):
        d = (day_of or {}).get(g, sat(g, gaps))
        for i, (h, a) in enumerate((rows or {}).get(g, WEEKLY)):
            fixtures.append(((g - 1) * 10 + 1 + i, g, datetime(d.year, d.month, d.day, 15, tzinfo=UTC), h, a))
    return M.Season(SEASON, fixtures)


def tie(comp, rnd, home, away, draw=LONG_AGO, day=LONG_AGO + timedelta(days=1), winner="", neutral=False, legs=1):
    return {"competition": comp, "round": rnd, "draw": draw, "dates": [day] if isinstance(day, date) else list(day), "home": home,
            "away": away, "neutral": neutral, "legs": legs, "winner": winner, "tiers": {}}


def played(comp, upto=None):
    """Every round of `comp` before `upto` (all of them without one), played long ago by clubs outside the league."""
    out = []
    for rnd in M.ROUNDS[comp]:
        if rnd == upto:
            break
        out.append(tie(comp, rnd, "Zed", "Yak", winner="Zed"))
    return out


def dates(**kw):
    """The round dates: none of the blank rounds on a league day unless given."""
    out = {(SEASON, c, r): [NO_LEAGUE_DAY] for c, r in M.BLANK_ROUNDS}
    for key, days in kw.items():
        c, r = key.split("_")
        out[(SEASON, {"FA": "FA Cup", "EFL": "EFL Cup"}[c], r)] = list(days)
    return out


RATING = defaultdict(lambda: 1500.0)


def final_ab(gw, gaps=()):
    """The EFL Cup final, A v B, on gameweek gw's Saturday; the FA Cup all played long ago."""
    return (played("FA Cup") + played("EFL Cup", "F")
            + [tie("EFL Cup", "F", "A", "B", day=sat(gw, gaps), neutral=True)]), dates(EFL_F=[sat(gw, gaps)])


class Ratings(unittest.TestCase):

    def test_the_update_by_hand(self):
        e = 1 / (1 + 10 ** (-60 / 400))
        r = M.elo([(date(2024, 8, 10), 1, "H", "A", "H")], date(2024, 8, 11))
        self.assertAlmostEqual(r["H"], 1500 + 20 * (1 - e), places=9)
        self.assertAlmostEqual(r["A"], 1500 - 20 * (1 - e), places=9)
        r = M.elo([(date(2024, 8, 10), 1, "H", "A", "D")], date(2024, 8, 11))
        self.assertAlmostEqual(r["H"], 1500 + 20 * (0.5 - e), places=9)
        r = M.elo([(date(2024, 8, 10), 1, "H", "A", "A")], date(2024, 8, 11))
        self.assertAlmostEqual(r["A"], 1500 + 20 * e, places=9)

    def test_the_tier_starts_and_the_carry_over(self):
        for tier, start in ((1, 1500), (2, 1400), (3, 1300), (4, 1200), (5, 1100)):
            r = M.elo([(date(2024, 8, 10), tier, "H", "A", "D")], date(2024, 8, 11))
            self.assertAlmostEqual(r["H"] + r["A"], 2 * start, places=9)                   # zero-sum from the tier's start
        rows = [(date(2024, 8, 10), 2, "P", "Q", "H"), (date(2025, 8, 10), 1, "P", "R", "H")]    # promoted: P keeps its rating
        one = M.elo(rows[:1], date(2030, 1, 1))["P"]
        e = M.p_home(one, 1500)
        self.assertAlmostEqual(M.elo(rows, date(2030, 1, 1))["P"], one + 20 * (1 - e), places=9)

    def test_a_result_on_or_after_the_origin_is_not_read(self):
        rows = [(date(2024, 8, 10), 1, "H", "A", "H"), (date(2024, 8, 17), 1, "H", "A", "A")]
        self.assertEqual(M.elo(rows, date(2024, 8, 17)), M.elo(rows[:1], date(2024, 8, 17)))
        self.assertEqual(M.elo(rows, date(2024, 8, 10)), {})

    def test_a_club_in_no_league_file_is_1000_and_an_unknown_name_stops(self):
        names = {"Town": {"football_data": "", "fpl": ""}, "City": {"football_data": "CityFD", "fpl": ""},
                 "New": {"football_data": "NotYet", "fpl": ""}}
        r = M.club_ratings([tie("FA Cup", "R3", "Town", "City"), tie("FA Cup", "R3", "New", "City")], names, {"CityFD": 1432.0})
        self.assertEqual((r["Town"], r["City"], r["New"]), (1000.0, 1432.0, 1000.0))
        with self.assertRaisesRegex(M.MissingInput, "Rovers is not in names.csv"):
            M.club_ratings([tie("FA Cup", "R3", "Rovers", "City")], names, {})


class ATie(unittest.TestCase):

    def test_the_probability(self):
        self.assertAlmostEqual(M.p_home(1500, 1500), 1 / (1 + 10 ** (-60 / 400)), places=12)
        self.assertEqual(M.p_home(1500, 1500, 0), 0.5)
        self.assertAlmostEqual(M.p_home(1700, 1500, 0), 1 / (1 + 10 ** (-0.5)), places=12)
        self.assertAlmostEqual(M.p_home(1500, 1600, 60) + M.p_home(1600, 1500, -60), 1.0, places=12)

    def winner(self, state, comp, field=()):
        """The next round's clubs, with a generator that draws 0.55 and shuffles nothing: home wins only if P(home) > 0.55."""
        class Rng:
            def random(self):
                return 0.55

            def shuffle(self, x):
                pass
        return M.simulate_cup(state, comp, RATING, field, SAT, Rng())

    def test_h_is_60_at_a_home_ground_and_0_at_a_neutral_venue_or_in_two_legs(self):
        later = SAT + timedelta(days=9)
        for t, home_wins in ((tie("EFL Cup", "QF", "A", "B", day=later), True),                       # P(home) 0.585
                             (tie("EFL Cup", "QF", "A", "B", day=later, neutral=True), False),         # P(home) 0.5
                             (tie("EFL Cup", "SF", "A", "B", day=(later, later + timedelta(days=7)), legs=2), False)):
                state = [(t["round"], True, [t, dict(t, home="C", away="D")]), ("F", False, [])]
                self.assertEqual("A" in self.winner(state, "EFL Cup")["F"], home_wins, t)

    def test_a_round_not_drawn_has_the_first_club_at_home_except_at_a_neutral_round(self):
        state = [("R4", False, []), ("R5", False, [])]
        self.assertEqual(self.winner(state, "FA Cup", ("A", "B", "C", "D"))["R5"], {"A", "C"})          # home: 0.585
        state = [("SF", False, []), ("F", False, [])]
        self.assertEqual(self.winner(state, "FA Cup", ("A", "B", "C", "D"))["F"], {"B", "D"})           # Wembley: 0.5


class Bracket(unittest.TestCase):

    def test_four_clubs_exact_against_the_monte_carlo(self):
        import random
        rating = {"P": 1700.0, "Q": 1600.0, "R": 1500.0, "S": 1350.0}
        clubs = list(rating)
        pairings = (("P", "Q", "R", "S"), ("P", "R", "Q", "S"), ("P", "S", "Q", "R"))
        reach, won = defaultdict(float), defaultdict(float)
        for a, b, c, d in pairings:                                                        # neutral rounds: each of 3 pairings
            for w1, l1 in ((a, b), (b, a)):
                for w2, l2 in ((c, d), (d, c)):
                    p = M.p_home(rating[w1], rating[l1], 0) * M.p_home(rating[w2], rating[l2], 0) / 3
                    reach[w1] += p
                    reach[w2] += p
                    won[w1] += p * M.p_home(rating[w1], rating[w2], 0)
                    won[w2] += p * M.p_home(rating[w2], rating[w1], 0)
        self.assertAlmostEqual(sum(reach.values()), 2.0, places=12)
        self.assertAlmostEqual(sum(won.values()), 1.0, places=12)
        n = 60000
        rng = random.Random(1)
        state = [("SF", False, []), ("F", False, [])]
        got = defaultdict(int)
        for _ in range(n):
            sim = M.simulate_cup(state, "FA Cup", rating, clubs, SAT, rng)
            for c in sim["F"]:
                got[c] += 1
        for c in clubs:
            self.assertAlmostEqual(got[c] / n, reach[c], delta=0.006, msg=c)

    def test_a_field_that_does_not_halve_stops(self):
        import random
        with self.assertRaisesRegex(M.MissingInput, "FA Cup R3: 6 clubs"):
            M.simulate_cup([("R3", False, [])], "FA Cup", RATING, list("ABCDEF"), SAT, random.Random(1))

    def test_a_played_tie_takes_its_winner(self):
        import random
        state = [("SF", True, [tie("FA Cup", "SF", "A", "B", winner="B"), tie("FA Cup", "SF", "C", "D", winner="C")]), ("F", False, [])]
        sim = M.simulate_cup(state, "FA Cup", RATING, (), SAT, random.Random(1))
        self.assertEqual(sim["F"], {"B", "C"})


class WhatIsKnown(unittest.TestCase):

    def test_a_draw_on_the_origins_day_is_not_known(self):
        rows = [tie("EFL Cup", "R2", "A", "B", draw=SAT - timedelta(days=9), day=SAT - timedelta(days=8), winner="A"),
                tie("EFL Cup", "R3", "A", "C", draw=SAT, day=SAT + timedelta(days=3), winner="A")]
        state = dict((r, d) for r, d, _ in M.cup_state(rows, "EFL Cup", SAT))
        self.assertEqual((state["R2"], state["R3"]), (True, False))
        state = dict((r, d) for r, d, _ in M.cup_state(rows, "EFL Cup", SAT + timedelta(days=1)))
        self.assertTrue(state["R3"])

    def test_a_draw_waits_for_the_round_before_it_to_be_played(self):
        rows = [tie("EFL Cup", "R2", "A", "B", draw=SAT - timedelta(days=9), day=SAT + timedelta(days=2), winner="A"),      # R2 not played yet
                tie("EFL Cup", "R3", "A", "C", draw=SAT - timedelta(days=1), day=SAT + timedelta(days=8), winner="A")]      # names R2's winner
        state = dict((r, d) for r, d, _ in M.cup_state(rows, "EFL Cup", SAT))
        self.assertEqual((state["R2"], state["R3"]), (True, False))

    def test_a_two_legged_tie_is_played_only_after_its_second_leg(self):
        import random
        rating = {"A": 3000.0, "B": 1000.0, "C": 3000.0, "D": 1000.0}
        legs = (SAT - timedelta(days=7), SAT + timedelta(days=7))
        rows = [tie("EFL Cup", "SF", "A", "B", day=legs, winner="B", legs=2), tie("EFL Cup", "SF", "C", "D", day=legs, winner="D", legs=2)]
        state = [("SF", True, rows), ("F", False, [])]
        self.assertEqual(M.simulate_cup(state, "EFL Cup", rating, (), SAT, random.Random(1))["F"], {"A", "C"})        # between the legs: Elo
        later = SAT + timedelta(days=8)
        self.assertEqual(M.simulate_cup(state, "EFL Cup", rating, (), later, random.Random(1))["F"], {"B", "D"})      # after them: the winners
        final = tie("EFL Cup", "F", "B", "D", draw=SAT - timedelta(days=1), day=SAT + timedelta(days=30), neutral=True)
        known = dict((r, d) for r, d, _ in M.cup_state(played("EFL Cup", "SF") + rows + [final], "EFL Cup", SAT))
        self.assertEqual((known["SF"], known["F"]), (True, False))                           # a final's row waits for the second leg
        known = dict((r, d) for r, d, _ in M.cup_state(played("EFL Cup", "SF") + rows + [final], "EFL Cup", later))
        self.assertTrue(known["F"])

    def test_a_tie_on_the_origins_day_is_not_played(self):
        import random
        rating = {"A": 3000.0, "B": 1000.0, "C": 3000.0, "D": 1000.0}
        rows = [tie("EFL Cup", "R2", "A", "B", day=SAT, winner="B"), tie("EFL Cup", "R2", "C", "D", day=SAT, winner="D")]
        state = M.cup_state(rows, "EFL Cup", SAT)[:1] + [("R3", False, [])]
        self.assertEqual(M.simulate_cup(state, "EFL Cup", rating, (), SAT, random.Random(1))["R3"], {"A", "C"})     # Elo, not the row's winner
        state = M.cup_state(rows, "EFL Cup", SAT + timedelta(days=1))[:1] + [("R3", False, [])]
        self.assertEqual(M.simulate_cup(state, "EFL Cup", rating, (), SAT + timedelta(days=1), random.Random(1))["R3"], {"B", "D"})

    def test_later_rows_never_move_a_forecast(self):
        season = toy_season()
        rd = dates(EFL_F=[sat(5)])
        wed = sat(3) + timedelta(days=4)
        rows = played("FA Cup") + played("EFL Cup", "SF") + [tie("EFL Cup", "SF", "A", "E", day=wed), tie("EFL Cup", "SF", "B", "F", day=wed)]
        one = M.simulate(season, rows, RATING, {}, rd, 1, n=2000, seed=7)
        self.assertGreater(one[0][("A", 5)], 0.0)
        later = rows + [tie("EFL Cup", "F", "A", "B", draw=sat(2), day=sat(5), winner="A", neutral=True)]      # a draw after the origin, with its winner
        self.assertEqual(one, M.simulate(season, later, RATING, {}, rd, 1, n=2000, seed=7))
        changed = [dict(t, winner="E") if t["round"] == "SF" else t for t in rows]              # an unplayed tie's winner is never read
        self.assertEqual(one, M.simulate(season, changed, RATING, {}, rd, 1, n=2000, seed=7))


class TheBlankRule(unittest.TestCase):

    def test_inclusion_exclusion_on_a_toy_fixture_list(self):
        rating = dict(A=1600.0, X=1400.0, C=1500.0, Y=1500.0, M=1500.0, N=1500.0, O=1500.0, P=1500.0, Zed=1500.0, Yak=1500.0)
        qf = sat(2) + timedelta(days=4)
        rows = played("EFL Cup") + played("FA Cup", "QF") + [
            tie("FA Cup", "QF", "A", "X", day=qf), tie("FA Cup", "QF", "C", "Y", day=qf), tie("FA Cup", "QF", "M", "N", day=qf), tie("FA Cup", "QF", "O", "P", day=qf)]
        season = toy_season(rows={3: [("A", "C"), ("B", "D"), ("E", "F")], 4: [("A", "E"), ("B", "D"), ("C", "F")]})
        p_blank, _ = M.simulate(season, rows, rating, {}, dates(FA_SF=[sat(3)]), 1, n=30000, seed=3)
        pa, pc = M.p_home(1600, 1400), M.p_home(1500, 1500)
        either = 1 - (1 - pa) * (1 - pc)
        self.assertAlmostEqual(p_blank[("A", 3)], either, delta=0.01)
        self.assertAlmostEqual(p_blank[("C", 3)], either, delta=0.01)                       # A v C: postponed if either is in the round
        self.assertEqual((p_blank[("B", 3)], p_blank[("D", 3)]), (0.0, 0.0))
        self.assertEqual(p_blank[("A", 4)], 0.0)

    def test_a_club_with_no_fixture_in_a_block_blanks(self):
        season = toy_season(rows={3: [("A", "C"), ("B", "D")]})                              # E and F have none in GW3
        rows, _ = final_ab(3)
        p_blank, _ = M.simulate(season, rows, RATING, {}, dates(), 1, n=20)
        self.assertEqual((p_blank[("E", 3)], p_blank[("F", 3)], p_blank[("A", 3)]), (1.0, 1.0, 0.0))

    def test_the_targets_are_every_club_and_only_gameweeks_after_the_origin(self):
        rows, rd = final_ab(3)
        season = toy_season()
        p_blank, p_double = M.simulate(season, rows, RATING, {}, rd, 2, n=10)
        want = {(c, g) for c in CLUBS for g in range(3, 8)}
        self.assertEqual((set(p_blank), set(p_double)), (want, want))

    def test_a_round_on_no_league_day_causes_no_blank(self):
        rows, _ = final_ab(3)
        p_blank, p_double = M.simulate(toy_season(), rows, RATING, {}, dates(EFL_F=[sat(3) + timedelta(days=1)]), 1, n=50)
        self.assertEqual(max(p_blank.values()), 0.0)
        self.assertEqual(max(p_double.values()), 0.0)

    def test_a_round_in_the_origins_gameweek_or_earlier_causes_no_blank(self):
        rows, rd = final_ab(3)
        p_blank, p_double = M.simulate(toy_season(), rows, RATING, {}, rd, 3, n=50)
        self.assertEqual(max(p_blank.values()), 0.0)
        self.assertEqual(max(p_double.values()), 0.0)                                        # known postponements are not used: no replay follows

    def test_a_kickoff_after_midnight_uk_is_the_next_uk_day(self):
        ko = datetime(2026, 8, 15, 23, 30, tzinfo=UTC)                                      # BST: 00:30 on the 16th
        season = M.Season(SEASON, [(1, 1, ko, "A", "B"), (11, 2, ko + timedelta(days=7), "A", "B")])
        self.assertEqual(season.blank_gw(date(2026, 8, 16)), 1)
        self.assertIsNone(season.blank_gw(date(2026, 8, 15)))


class TheDoubleRule(unittest.TestCase):

    def run_(self, gw=3, season=None, europe=(), rd=None, extra=(), origin=1, n=40):
        rows, r = final_ab(gw)
        return M.simulate(season or toy_season(), rows + list(extra), RATING, {}, rd or r, origin, n=n, europe=europe)

    def test_the_first_free_midweek_in_a_later_window(self):
        p_blank, p_double = self.run_()
        for c in "ABCD":
            self.assertEqual(p_blank[(c, 3)], 1.0, c)                                       # both clubs of each fixture
            self.assertEqual(p_double[(c, 3)], 0.0, c)                                      # the midweek right after is GW3's window
            self.assertEqual(p_double[(c, 4)], 1.0, c)
            self.assertEqual(p_double[(c, 5)], 0.0, c)
        for c in "EF":
            self.assertEqual(p_blank[(c, 3)] + p_double[(c, 4)], 0.0, c)

    def test_a_league_midweek_is_not_free(self):
        tue = sat(4) + timedelta(days=3)
        season = toy_season(day_of={5: tue, 6: sat(5), 7: sat(6)})                          # GW5 on the Tuesday after GW4
        _, p_double = self.run_(season=season)
        self.assertEqual(p_double[("A", 5)], 0.0)                                           # that midweek is busy for everyone
        self.assertEqual(p_double[("A", 6)], 1.0)                                           # the next is in GW6's window

    def test_a_thursday_league_fixture_is_busy_too(self):
        thu = sat(4) + timedelta(days=5)
        season = toy_season(day_of={5: thu, 6: sat(5), 7: sat(6)})
        _, p_double = self.run_(season=season)
        self.assertEqual(p_double[("A", 4)], 0.0)                                            # that midweek's window is still GW4's
        self.assertEqual(p_double[("A", 6)], 1.0)

    def test_with_no_later_midweek_the_last_before_it_after_the_origin(self):
        season = toy_season(gws=7)
        _, p_double = self.run_(gw=7, season=season)
        self.assertEqual(p_double[("A", 6)], 1.0)
        self.assertEqual(p_double[("A", 5)], 0.0)

    def test_the_fallback_stays_after_the_origin(self):
        season = toy_season(gws=7)
        p_blank, p_double = self.run_(gw=7, season=season, origin=6)                         # the Tuesday after GW6's Saturday is after the origin
        self.assertEqual(p_double[("A", 7)], 0.0)
        self.assertEqual(p_blank[("A", 7)], 1.0)

    def test_with_no_free_midweek_no_double_and_the_blank_stands(self):
        season = toy_season(gws=7)
        every = [{"date": sat(g) + timedelta(days=4), "clubs": ["A"], "knockout": None, "competition": "CL"} for g in range(1, 8)]
        p_blank, p_double = self.run_(season=season, europe=every)
        self.assertEqual(p_blank[("A", 3)], 1.0)
        self.assertEqual(max(v for (c, _), v in p_double.items() if c == "A"), 0.0)
        self.assertEqual(p_double[("B", 4)], 1.0)                                            # B's fixture is unaffected

    def test_a_placed_replay_makes_its_clubs_busy(self):
        season = toy_season(rows={3: [("A", "C"), ("A", "D"), ("B", "E")]})
        p_blank, p_double = self.run_(season=season)
        self.assertEqual(p_blank[("A", 3)], 1.0)                                             # both of A's fixtures
        self.assertEqual(p_double[("A", 3)], 0.0)                                            # A's base double in GW3 is gone
        self.assertEqual((p_double[("A", 4)], p_double[("A", 5)]), (1.0, 1.0))               # one a midweek
        self.assertEqual((p_double[("C", 4)], p_double[("D", 5)]), (1.0, 1.0))

    def test_a_midweek_in_a_break_is_not_a_candidate(self):
        gaps = (4,)
        season = toy_season(gaps=gaps)
        rows, rd = final_ab(3, gaps)
        _, p_double = M.simulate(season, rows, RATING, {}, rd, 1, n=40)
        self.assertEqual(p_double[("A", 4)], 0.0)                                            # the week after GW4 leads into the break
        self.assertEqual(p_double[("A", 5)], 1.0)
        tuesdays = [m[0] for m in season.midweeks]
        self.assertNotIn(sat(4, gaps) + timedelta(days=3), tuesdays)
        self.assertNotIn(sat(4, gaps) + timedelta(days=10), tuesdays)
        self.assertIn(sat(3, gaps) + timedelta(days=3), tuesdays)

    def test_a_european_match_moves_the_replay(self):
        wed = sat(4) + timedelta(days=4)
        europe = [{"date": wed, "clubs": ["A"], "knockout": None, "competition": "CL"}]
        _, p_double = self.run_(europe=europe)
        self.assertEqual((p_double[("A", 4)], p_double[("A", 5)]), (0.0, 1.0))
        self.assertEqual((p_double[("C", 4)], p_double[("C", 5)]), (0.0, 1.0))
        self.assertEqual(p_double[("B", 4)], 1.0)

    def test_a_european_match_outside_tuesday_to_thursday_does_not(self):
        europe = [{"date": sat(4) + timedelta(days=6), "clubs": ["A"], "knockout": None, "competition": "CL"}]   # that week's Friday
        _, p_double = self.run_(europe=europe)
        self.assertEqual(p_double[("A", 4)], 1.0)

    def test_a_european_knockout_stage_goes_out_at_one_half(self):
        wed = sat(4) + timedelta(days=4)
        for stage, want in ((0, 0.0), (1, 0.5), (2, 0.75)):
            europe = [{"date": wed, "clubs": ["A"], "knockout": stage, "competition": "CL"}]
            _, p_double = self.run_(europe=europe, n=6000)
            self.assertAlmostEqual(p_double[("A", 4)], want, delta=0.03, msg=stage)

    def test_a_cup_round_that_midweek_moves_only_the_clubs_still_in_it(self):
        wed = sat(4) + timedelta(days=4)
        rows = played("FA Cup", "R5") + [tie("FA Cup", "R5", "A", "E", day=wed - timedelta(days=30), winner="A")] + played("EFL Cup", "F")
        rows = [t for t in rows if not (t["competition"] == "FA Cup" and t["round"] in ("QF", "SF", "F"))]
        rows += [tie("EFL Cup", "F", "A", "B", day=sat(3), neutral=True)]
        rows += [tie("FA Cup", r, "Zed", "Yak", winner="Zed") for r in ("QF", "SF", "F")]
        rd = dates(EFL_F=[sat(3)], FA_R5=[wed])
        _, p_double = M.simulate(toy_season(), rows, RATING, {}, rd, 1, n=40)
        self.assertEqual((p_double[("A", 4)], p_double[("A", 5)]), (0.0, 1.0))               # A is in that round
        self.assertEqual(p_double[("B", 4)], 1.0)


class TheCalendar(unittest.TestCase):

    def test_a_deadline_reads_only_fixtures_left_in_their_block(self):
        k = datetime(2026, 8, 15, 15, tzinfo=UTC)
        season = M.Season(SEASON, [(1, 1, k, "A", "B"), (2, 5, k - timedelta(days=3), "C", "D"),      # id block 1, moved to GW5
                                   (11, 2, k + timedelta(days=7), "A", "C"), (12, 2, k + timedelta(days=7), "B", "D")])
        self.assertEqual(season.deadline[1], k - timedelta(minutes=90))
        self.assertEqual(season.original[1], [(1, "A", "B"), (2, "C", "D")])                 # the published schedule
        self.assertEqual(season.actual[("C", 1)], 0)                                         # the outcome: by event
        self.assertEqual(season.actual[("C", 5)], 1)
        self.assertEqual(season.base[("C", 1)], 1)

    def test_the_counts_equal_part_1s_on_a_toy(self):
        k = datetime(2026, 8, 15, 15, tzinfo=UTC)
        rows = [(1, 1, k, 1, 2), (2, 3, k, 3, 4), (11, 2, k + timedelta(days=7), 1, 3), (12, 2, k + timedelta(days=7), 2, 4), (21, 3, k + timedelta(days=14), 1, 4)]
        season = M.Season(SEASON, [(i, e, ko, str(h), str(a)) for i, e, ko, h, a in rows])
        n, _, teams, events = BD.counts([(e, h, a) for _, e, _, h, a in rows])
        for (e, t), v in n.items():
            self.assertEqual(season.actual[(str(t), e)], v, (e, t))

    def test_a_block_left_empty_stops(self):
        k = datetime(2026, 8, 15, 15, tzinfo=UTC)
        with self.assertRaisesRegex(M.MissingInput, "GW1"):
            M.Season(SEASON, [(1, 2, k, "A", "B"), (11, 2, k, "C", "D")])


class TheFACupField(unittest.TestCase):

    def setUp(self):
        self.tier1 = [f"P{i:02d}" for i in range(20)]
        self.tier2 = [f"C{i:02d}" for i in range(24)]
        self.names = {c: {"football_data": c + " FD", "fpl": ""} for c in self.tier1 + self.tier2}
        self.names.update({c: {"football_data": c, "fpl": ""} for c in "ABCDEF"})

    def test_the_field_reads_only_this_seasons_results_before_the_origin(self):
        rows = [(date(2026, 6, 30), 1, "Old", "Older", "H"), (date(2026, 7, 1), 1, "P", "Q", "H"),
                (date(2026, 8, 14), 2, "R", "S", "H"), (date(2026, 8, 15), 2, "T", "U", "H")]
        self.assertEqual(M.clubs_by_tier(rows, date(2026, 7, 1), date(2026, 8, 15)), {1: ["P", "Q"], 2: ["R", "S"]})

    def test_a_club_from_last_season_is_not_in_the_field(self):
        self.names["Old"] = {"football_data": "Old FD", "fpl": ""}
        _, _, _, field, _, _ = self.forecast(sat(1), extra=[(date(2026, 5, 1), 1, "Old FD", self.tier1[0] + " FD", "D")])
        self.assertEqual(len(field["FA Cup"]), 64)
        self.assertNotIn("Old", field["FA Cup"])

    def test_44_exempt_clubs_and_20_placeholders(self):
        by_tier = {1: [c + " FD" for c in self.tier1], 2: [c + " FD" for c in self.tier2], 3: ["Lower FD"]}
        clubs, placeholders = M.fa_field(by_tier, self.names)
        self.assertEqual((len(clubs), len(placeholders)), (44, 20))
        self.assertEqual(set(clubs), set(self.tier1 + self.tier2))
        self.assertTrue(all(q.startswith("qualifier ") for q in placeholders))

    def test_a_tier_1_or_2_club_missing_from_the_names_stops(self):
        with self.assertRaisesRegex(M.MissingInput, "Lost FD"):
            M.fa_field({1: ["Lost FD"], 2: []}, self.names)

    def forecast(self, r3_draw, extra=()):
        k = sat(1)
        results = [(k - timedelta(days=7), 1, a + " FD", b + " FD", "D") for a, b in zip(self.tier1[0::2], self.tier1[1::2])]
        results += [(k - timedelta(days=7), 2, a + " FD", b + " FD", "D") for a, b in zip(self.tier2[0::2], self.tier2[1::2])]
        results = list(extra) + results
        season = toy_season()
        fa = [tie("FA Cup", "R3", "A", "B", draw=r3_draw, day=sat(6) + timedelta(days=30))]
        with mock.patch.object(M, "simulate", return_value=({}, {})) as sim:
            C.forecast(season, fa + played("EFL Cup"), dict(self.names, Zed={"football_data": "", "fpl": ""}, Yak={"football_data": "", "fpl": ""}),
                       results, dates(), 1, n=1)
        return sim.call_args.args

    def test_before_the_draw_the_field_is_used(self):
        _, _, rating, field, _, _ = self.forecast(sat(1))                                    # the draw on the origin's day: not known
        self.assertEqual(len(field["FA Cup"]), 64)
        self.assertEqual(rating["qualifier 20"], 1250.0)
        self.assertEqual(rating["P00"], 1500 + 20 * (0.5 - M.p_home(1500, 1500)))

    def test_after_the_draw_no_placeholder(self):
        _, _, rating, field, _, _ = self.forecast(sat(1) - timedelta(days=1))
        self.assertEqual(field, {})
        self.assertFalse([c for c in rating if c.startswith("qualifier")])


class TheScore(unittest.TestCase):

    def rec(self, season, gw, kind, p, base, y):
        return (season, 10, gw, "A", kind, p, base, y)

    def test_the_brier_skill_score_by_hand(self):
        recs = [self.rec("2024-25", 11, "blank", 0.5, 0.25, 1), self.rec("2024-25", 12, "double", 0.0, 0.25, 0)]
        self.assertAlmostEqual(C.bss(recs), 1 - 0.25 / 0.625, places=12)
        self.assertIsNone(C.bss([self.rec("2024-25", 11, "blank", 0.5, 0.0, 0)]))

    def test_the_records_score_by_event(self):
        k = datetime(2026, 8, 15, 15, tzinfo=UTC)
        season = M.Season(SEASON, [(1, 1, k, "A", "B"), (11, 2, k + timedelta(days=7), "A", "B"), (12, 2, k + timedelta(days=9), "A", "B")])
        recs = C.records(season, {("A", 1): 0.2}, {("A", 2): 0.3}, 0, 0.01, 0.02)
        self.assertEqual(recs, [(SEASON, 0, 1, "A", "blank", 0.2, 0.01, 0), (SEASON, 0, 2, "A", "double", 0.3, 0.02, 1)])

    def test_the_base_rate_is_point_in_time_and_leaves_out_events_above_38(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        def write(season, rows):
            os.makedirs(os.path.join(tmp, season))
            with open(os.path.join(tmp, season, "fixtures.csv"), "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(("event", "team_h", "team_a"))
                w.writerows(rows)
        write("2018-19", [(1, 1, 2), (1, 3, 4), (2, 1, 2), (2, 1, 3), (40, 1, 2)])           # event 2: team 1 double, team 4 blank
        write("2019-20", [(1, 1, 2), (1, 3, 4), (2, 3, 4)])                                  # blanks in event 2: teams 1, 2
        self.assertEqual(C.base_rates(tmp, "2019-20"), (1 / 8, 1 / 8))                       # a later season never read
        with self.assertRaises(M.MissingInput):
            C.base_rates(tmp, "2018-19")

    def test_the_bootstrap_is_over_season_and_gameweek_and_reproducible(self):
        recs = [self.rec("2024-25", 11 + i, "blank", 0.1 * (i % 3), 0.2, i % 2) for i in range(12)]
        a = C.bootstrap(recs, b=500)
        self.assertEqual(a, C.bootstrap(recs, b=500))
        self.assertLess(a[0], a[1])
        one_block = [self.rec("2024-25", 11, "blank", 0.1 * (i % 3), 0.2, i % 2) for i in range(12)]
        low, high = C.bootstrap(one_block, b=50)
        self.assertEqual(low, high)                                                          # a single block never varies
        two = [self.rec("2024-25", 11, "blank", 0.0, 0.2, 0), self.rec("2025-26", 11, "blank", 1.0, 0.2, 0)]
        low, high = C.bootstrap(two, b=200)
        self.assertLess(low, high)                                                           # the same gameweek of two seasons: two blocks

    def test_the_interval_is_the_sorted_draws_at_the_two_floors(self):
        import random
        recs = [self.rec("2024-25", 11 + i, "blank", 0.1 * (i % 3), 0.2, i % 2) for i in range(12)]
        blocks = {}
        for r in recs:
            blocks[(r[0], r[2])] = ((r[5] - r[7]) ** 2, (r[6] - r[7]) ** 2)
        values, rng, draws = list(blocks.values()), random.Random(M.SEED), []
        for _ in range(400):
            picks = rng.choices(values, k=len(values))
            draws.append(1 - sum(p[0] for p in picks) / sum(p[1] for p in picks))
        draws.sort()
        self.assertEqual(C.bootstrap(recs, b=400), (draws[20], draws[380]))

    def test_the_prereg_s_constants(self):
        self.assertEqual((M.K, M.HOME, M.N, M.SEED, M.ORIGIN_GWS), (20.0, 60.0, 20000, 20261021, (10, 15, 20, 25, 30)))
        self.assertEqual((C.BOOTSTRAP, C.BINS, C.PASS_BSS), (10000, 10, 0.10))
        self.assertEqual(M.BLANK_ROUNDS, (("FA Cup", "QF"), ("FA Cup", "SF"), ("EFL Cup", "F")))
        self.assertEqual((M.FA_EXEMPT_TIERS, M.FA_R3_CLUBS), ((1, 2), 64))

    def test_the_reliability_bins(self):
        recs = [self.rec("2024-25", 11, "blank", p, 0.1, y) for p, y in ((0.05, 0), (0.05, 1), (1.0, 1))]
        self.assertEqual(C.reliability(recs), [(0, 2, 0.05, 0.5), (9, 1, 1.0, 1.0)])

    def test_pass_and_fail_at_the_bar(self):
        self.assertEqual(C.PASS_BSS, 0.10)
        lines = []
        good = [self.rec("2024-25", 11, "blank", 1.0, 0.5, 1), self.rec("2025-26", 12, "double", 0.0, 0.5, 0)]
        self.assertEqual(C.report(good, lines.append), 1.0)
        self.assertIn("PASS", lines[0])
        lines = []
        bad = [self.rec("2024-25", 11, "blank", 0.0, 0.5, 1), self.rec("2025-26", 12, "double", 1.0, 0.5, 0)]
        C.report(bad, lines.append)
        self.assertIn("FAIL", lines[0])


class TheFiles(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, name, text):
        path = os.path.join(self.tmp, name)
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return path

    HEAD = ",".join(M.CUP_COLUMNS) + "\n"

    def test_a_cup_row_without_a_source_or_read_time_is_refused(self):
        row = "FA Cup,R3,2025-01-01,2025-01-10,A,B,1,1,0,1,1-0,A,{},{}\n"
        good = self.write("c.csv", "# comment\n" + self.HEAD + row.format("https://x", "2026-01-01T00:00:00Z"))
        ties = M.read_cups(good)
        self.assertEqual((ties[0]["home"], ties[0]["dates"], ties[0]["winner"]), ("A", [date(2025, 1, 10)], "A"))
        for src, read in (("", "2026-01-01T00:00:00Z"), ("https://x", " ")):
            bad = self.write("b.csv", self.HEAD + row.format(src, read))
            with self.assertRaisesRegex(M.MissingInput, "no source or read time"):
                M.read_cups(bad)

    def test_two_legs_read_both_dates(self):
        row = "EFL Cup,SF,2025-01-01,2025-01-10;2025-02-05,A,B,1,1,0,2,1-0;0-0;1-0,A,https://x,2026-01-01T00:00:00Z\n"
        t = M.read_cups(self.write("c.csv", self.HEAD + row))[0]
        self.assertEqual((t["dates"], t["legs"]), ([date(2025, 1, 10), date(2025, 2, 5)], 2))

    def test_a_missing_column_is_refused(self):
        with self.assertRaisesRegex(M.MissingInput, "no column"):
            M.read_cups(self.write("c.csv", "competition,round\nFA Cup,R3\n"))

    def test_the_names_refuse_a_duplicate(self):
        with self.assertRaisesRegex(M.MissingInput, "twice"):
            M.read_names(self.write("n.csv", "cup_name,football_data,fpl_name\nA,A,A\nA,B,B\n"))

    def test_the_round_dates_refuse_a_row_without_a_source(self):
        with self.assertRaisesRegex(M.MissingInput, "no source"):
            M.read_round_dates(self.write("r.csv", "season,competition,round,leg,date,source\n2024-25,FA Cup,QF,1,2025-03-29,\n"))
        got = M.read_round_dates(self.write("r.csv", "season,competition,round,leg,date,source\n2024-25,EFL Cup,SF,2,2025-02-05,x\n2024-25,EFL Cup,SF,1,2025-01-07,x\n"))
        self.assertEqual(got[("2024-25", "EFL Cup", "SF")], [date(2025, 1, 7), date(2025, 2, 5)])

    def test_the_league_files_read_both_date_forms_and_skip_a_row_without_a_result(self):
        os.makedirs(os.path.join(self.tmp, "2024-25"))
        for div in M.DIVISIONS:
            body = "Date,HomeTeam,AwayTeam,FTR\n"
            if div == "E0":
                body += "17/08/2024,A,B,H\n10/08/24,C,D,D\n24/08/2024,A,C,\n"
            self.write(os.path.join("2024-25", div + ".csv"), body)
        self.assertEqual(M.read_results(self.tmp, ["2024-25"]),
                         [(date(2024, 8, 10), 1, "C", "D", "D"), (date(2024, 8, 17), 1, "A", "B", "H")])
        with self.assertRaisesRegex(M.MissingInput, "no "):
            M.read_results(self.tmp, ["2023-24"])

    def test_the_real_backtest_refuses_without_its_flag(self):
        out = os.path.join(self.tmp, "out")
        self.assertEqual(C.main(["--out", out, "--hist", self.tmp]), 2)
        self.assertFalse(os.path.exists(out))


class TheCommittedTables(unittest.TestCase):
    """The hand-typed tables: against each other always, against the local historical files where they exist."""

    def ties(self, season):
        return M.read_cups(os.path.join(M.CUPS, f"cups_{season}.csv"))

    def test_the_round_dates_are_the_cup_csvs_earliest_tie_dates(self):
        rd = M.read_round_dates(os.path.join(M.CUPS, "round_dates.csv"))
        for season in C.SEASONS:
            legs = defaultdict(lambda: defaultdict(list))
            for t in self.ties(season):
                for i, d in enumerate(t["dates"]):
                    legs[(t["competition"], t["round"])][i].append(d)
            for (comp, rnd), by_leg in legs.items():
                self.assertEqual(rd[(season, comp, rnd)], [min(by_leg[i]) for i in sorted(by_leg)], (season, comp, rnd))

    def test_every_blank_round_has_a_date(self):
        rd = M.read_round_dates(os.path.join(M.CUPS, "round_dates.csv"))
        for season, (comp, rnd) in itertools.product(C.SEASONS, M.BLANK_ROUNDS):
            self.assertIn((season, comp, rnd), rd)

    def test_the_names_are_complete_for_the_cup_csvs(self):
        names = M.read_names(os.path.join(M.CUPS, "names.csv"))
        for season in C.SEASONS:
            for t in self.ties(season):
                self.assertIn(t["home"], names)
                self.assertIn(t["away"], names)
        self.assertEqual(len({v["fpl"] for v in names.values() if v["fpl"]}), sum(1 for v in names.values() if v["fpl"]))

    def test_a_rounds_clubs_came_through_the_round_before(self):
        for season in C.SEASONS:
            ties = self.ties(season)
            for comp, rounds in M.ROUNDS.items():
                for a, b in zip(rounds, rounds[1:]):
                    winners = {t["winner"] for t in ties if t["competition"] == comp and t["round"] == a}
                    if not winners:
                        continue
                    if (comp, a) == ("EFL Cup", "R2"):                                       # the European clubs enter at R3
                        continue
                    clubs = {c for t in ties if t["competition"] == comp and t["round"] == b for c in (t["home"], t["away"])}
                    self.assertEqual(clubs, winners, (season, comp, b))

    @unittest.skipUnless(os.path.isdir(os.path.join(HIST, "football-data")), "no local historical files")
    def test_the_names_and_tiers_agree_with_the_league_files(self):
        names = M.read_names(os.path.join(M.CUPS, "names.csv"))
        for season in C.SEASONS:
            start = date(int(season[:4]), 7, 1)
            results = M.read_results(os.path.join(HIST, "football-data"), [season])
            tiers = {}
            for _, tier, home, away, _ in results:
                tiers[home] = tiers[away] = tier
            for t in self.ties(season):
                for club, tier in t["tiers"].items():
                    fd = names[club]["football_data"]
                    if tier <= 5:
                        self.assertEqual(tiers.get(fd), tier, (season, club, fd))
                    else:
                        self.assertNotIn(fd, tiers, (season, club, fd))
            clubs = M.clubs_by_tier(results, start, date(int(season[:4]) + 1, 7, 1))
            self.assertEqual((len(clubs[1]), len(clubs[2])), (20, 24))
            self.assertEqual(M.fa_field(clubs, names)[1], [f"qualifier {i:02d}" for i in range(1, 21)])

    @unittest.skipUnless(os.path.isdir(os.path.join(HIST, "football-data")), "no local historical files")
    def test_the_team_table_scores_every_fixture_as_the_league_file_does(self):
        """The FPL ids through names.csv reproduce football-data's E0, score for score. No model is run."""
        names = M.read_names(os.path.join(M.CUPS, "names.csv"))
        for season in C.SEASONS:
            with io.open(os.path.join(HIST, "football-data", season, "E0.csv"), encoding="utf-8-sig", newline="") as fh:
                e0 = {(r["HomeTeam"], r["AwayTeam"]): (int(r["FTHG"]), int(r["FTAG"])) for r in csv.DictReader(fh) if r.get("HomeTeam")}
            with io.open(os.path.join(HIST, season, "fixtures.csv"), encoding="utf-8", newline="") as fh:
                score = {int(r["id"]): (int(float(r["team_h_score"])), int(float(r["team_a_score"]))) for r in csv.DictReader(fh)}
            rows = C.load_fixtures(HIST, season, names)
            self.assertEqual(len(rows), 380)
            for fid, _, _, home, away in rows:
                self.assertEqual(e0[(names[home]["football_data"], names[away]["football_data"])], score[fid], (season, fid))

    @unittest.skipUnless(os.path.isdir(os.path.join(HIST, "football-data")), "no local historical files")
    def test_the_season_counts_equal_part_1s_and_each_origin_is_ready(self):
        """The id-block rule against part 1's counts, on the real files; the windows and the midweeks exist. No model is run."""
        names = M.read_names(os.path.join(M.CUPS, "names.csv"))
        for season in C.SEASONS:
            s = M.Season(season, C.load_fixtures(HIST, season, names))
            self.assertEqual(s.gws, list(range(1, 39)))
            self.assertTrue(all(len(s.original[g]) == 10 for g in s.gws))
            n, _, teams, events = BD.counts(BD.read_fixtures(os.path.join(HIST, season, "fixtures.csv")))
            self.assertEqual(sum(n.values()), sum(s.actual.values()))
            self.assertEqual(sorted(s.actual.values()), sorted(v for v in n.values() if v))
            self.assertGreater(len(s.midweeks), 3)
            deadlines = [s.deadline[g] for g in s.gws]
            self.assertEqual(deadlines, sorted(deadlines))
            for g in M.ORIGIN_GWS:
                self.assertLess(s.deadline[g], s.deadline[g + 1])


if __name__ == "__main__":
    unittest.main()
