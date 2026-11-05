"""tools/cup_mc.py - Step 16 part 3: the cup Monte Carlo (BUILD_PLAN.md Step 16
point 3; prereg/S16.md, parts 3-4 and its amendment of 5 Nov).

For every Premier League club and every gameweek after an origin: P(blank) and
P(double), from an Elo over the five English tiers, the cup brackets as known at
the origin, the blank rounds and a table of free midweeks. Every constant is the
prereg's. Offline; the runner never imports it. Standard library only. It reads
downloaded files, so it runs with `python -I`.
"""
import csv
import io
import os
import random
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calendar_2627 import uk_offset                   # noqa: E402

UTC = timezone.utc
CUPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cups")

K = 20.0
HOME = 60.0
TIER_START = {1: 1500.0, 2: 1400.0, 3: 1300.0, 4: 1200.0, 5: 1100.0}
NON_LEAGUE = 1000.0
PLACEHOLDER = 1250.0                                  # amendment, item 1 (question 4)
ELIMINATION = 0.5                                     # an English club at each European knockout stage (question 3)
N = 20000
SEED = 20261021
DIVISIONS = {"E0": 1, "E1": 2, "E2": 3, "E3": 4, "EC": 5}
ROUNDS = {"EFL Cup": ("R2", "R3", "R4", "QF", "SF", "F"), "FA Cup": ("R3", "R4", "R5", "QF", "SF", "F")}
NEUTRAL = {("FA Cup", "SF"), ("FA Cup", "F"), ("EFL Cup", "SF"), ("EFL Cup", "F")}     # H = 0: Wembley, or the two-legged semi-final
BLANK_ROUNDS = (("FA Cup", "QF"), ("FA Cup", "SF"), ("EFL Cup", "F"))
FA_EXEMPT_TIERS = (1, 2)
FA_R3_CLUBS = 64
ORIGIN_GWS = (10, 15, 20, 25, 30)
CUP_COLUMNS = ("competition", "round", "draw_date", "tie_date", "home", "away", "home_tier", "away_tier",
               "neutral", "legs", "result", "winner", "source_url", "read_at_utc")


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


# ---------------------------------------------------------------------------
# the hand-typed files
# ---------------------------------------------------------------------------

def _rows(path):
    """The rows of a CSV whose comment lines start with #."""
    with io.open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(ln for ln in fh if not ln.startswith("#")))


def read_cups(path):
    """Every tie of a cup CSV. A row without its source or read time is refused."""
    ties = []
    for i, r in enumerate(_rows(path), 1):
        missing = [c for c in CUP_COLUMNS if c not in r]
        if missing:
            raise MissingInput(f"{path}: no column {missing[0]}")
        if not (r["source_url"] or "").strip() or not (r["read_at_utc"] or "").strip():
            raise MissingInput(f"{path}: tie {i} ({r['home']} v {r['away']}) has no source or read time")
        dates = [date.fromisoformat(d) for d in r["tie_date"].split(";")]
        ties.append({"competition": r["competition"], "round": r["round"], "draw": date.fromisoformat(r["draw_date"]),
                     "dates": dates, "home": r["home"], "away": r["away"], "neutral": r["neutral"] == "1",
                     "legs": int(r["legs"]), "winner": r["winner"],
                     "tiers": {r["home"]: int(r["home_tier"]), r["away"]: int(r["away_tier"])}})
    return ties


def read_names(path):
    """{cup name: {"football_data": name or "", "fpl": name or ""}}. An empty
    football_data is a club below the five tiers."""
    out = {}
    for r in _rows(path):
        if r["cup_name"] in out:
            raise MissingInput(f"{path}: {r['cup_name']} twice")
        out[r["cup_name"]] = {"football_data": r["football_data"], "fpl": r["fpl_name"]}
    return out


def read_round_dates(path):
    """{(season, competition, round): [date per leg]} (amendment, item 2)."""
    out = defaultdict(list)
    for r in sorted(_rows(path), key=lambda r: int(r["leg"])):
        if not (r["source"] or "").strip():
            raise MissingInput(f"{path}: {r['season']} {r['competition']} {r['round']} has no source")
        out[(r["season"], r["competition"], r["round"])].append(date.fromisoformat(r["date"]))
    return dict(out)


def _date(text):
    d, m, y = text.strip().split("/")
    return date(int(y) + 2000 if len(y) == 2 else int(y), int(m), int(d))


def read_results(root, seasons):
    """[(date, tier, home, away, FTR)] from football-data's league files, by date
    and then the file's own order. Only data is read."""
    out = []
    for season in seasons:
        for div, tier in DIVISIONS.items():
            path = os.path.join(root, season, div + ".csv")
            if not os.path.exists(path):
                raise MissingInput(f"no {path}")
            with io.open(path, encoding="utf-8-sig", newline="") as fh:
                for i, r in enumerate(csv.DictReader(fh)):
                    if (r.get("FTR") or "") in ("H", "D", "A"):
                        out.append((_date(r["Date"]), tier, i, r["HomeTeam"], r["AwayTeam"], r["FTR"]))
    out.sort(key=lambda x: x[:3])
    return [(d, t, h, a, ftr) for d, t, _, h, a, ftr in out]


# ---------------------------------------------------------------------------
# the ratings and a tie
# ---------------------------------------------------------------------------

def p_home(r_home, r_away, h=HOME):
    return 1.0 / (1.0 + 10.0 ** (-(r_home + h - r_away) / 400.0))


def elo(results, before):
    """{football-data name: rating} from the league results dated before `before`.
    A club starts at its tier's rating at its first appearance; ratings carry over
    seasons, so promotion and relegation link the tiers."""
    r = {}
    score = {"H": 1.0, "D": 0.5, "A": 0.0}
    for d, tier, home, away, ftr in results:
        if d >= before:
            continue
        rh, ra = r.setdefault(home, TIER_START[tier]), r.setdefault(away, TIER_START[tier])
        delta = K * (score[ftr] - p_home(rh, ra))
        r[home], r[away] = rh + delta, ra - delta
    return r


def club_ratings(ties, names, ratings, extra=()):
    """{cup name: rating} for every club in `ties` and `extra`. A club in no league
    file before the origin is 1000; a club missing from names.csv stops the run."""
    out = {}
    for club in {c for t in ties for c in (t["home"], t["away"])} | set(extra):
        if club not in names:
            raise MissingInput(f"{club} is not in names.csv")
        out[club] = ratings.get(names[club]["football_data"], NON_LEAGUE)
    return out


# ---------------------------------------------------------------------------
# one cup, as known at the origin
# ---------------------------------------------------------------------------

def cup_state(ties, competition, origin):
    """[(round, drawn, ties)] in order. A round counts as drawn only if its draw is
    dated before the origin and every tie of the round before it has been played
    before the origin (amendment, item 3)."""
    state, prev_played = [], True
    for rnd in ROUNDS[competition]:
        here = [t for t in ties if t["competition"] == competition and t["round"] == rnd]
        drawn = bool(here) and all(t["draw"] < origin for t in here) and prev_played
        state.append((rnd, drawn, here if drawn else []))
        prev_played = drawn and all(t["dates"][-1] < origin for t in here)
    return state


def simulate_cup(state, competition, rating, field, origin, rng):
    """{round: clubs in it} for one simulation. A played tie takes its winner; an
    unplayed one Elo's probability; a round not drawn is drawn at random among the
    clubs left, the first drawn at home. `field` is the first round's clubs if it
    has no draw."""
    out, alive = {}, None
    for rnd, drawn, here in state:
        h = 0.0 if (competition, rnd) in NEUTRAL else HOME
        winners = []
        if drawn:
            out[rnd] = {c for t in here for c in (t["home"], t["away"])}
            for t in here:
                if t["dates"][-1] < origin:
                    winners.append(t["winner"])
                else:
                    ht = 0.0 if (t["neutral"] or t["legs"] == 2) else HOME
                    winners.append(t["home"] if rng.random() < p_home(rating[t["home"]], rating[t["away"]], ht) else t["away"])
        else:
            clubs = list(alive if alive is not None else field)
            if len(clubs) not in (2, 4, 8, 16, 32, 64):       # e.g. a round where more clubs enter, not yet drawn
                raise MissingInput(f"{competition} {rnd}: {len(clubs)} clubs known at the origin")
            rng.shuffle(clubs)
            out[rnd] = set(clubs)
            for a, b in zip(clubs[0::2], clubs[1::2]):
                winners.append(a if rng.random() < p_home(rating[a], rating[b], h) else b)
        alive = winners
    return out


def fa_field(origin_clubs_by_tier, names):
    """Amendment, item 1: the FA Cup's third round before its draw. The clubs of
    tiers 1 and 2 (as cup names) and placeholders for the other places."""
    reverse = {v["football_data"]: k for k, v in names.items() if v["football_data"]}
    clubs = []
    for tier in FA_EXEMPT_TIERS:
        for fd in origin_clubs_by_tier[tier]:
            if fd not in reverse:
                raise MissingInput(f"{fd} (tier {tier}) is not in names.csv")
            clubs.append(reverse[fd])
    if len(clubs) >= FA_R3_CLUBS:
        raise MissingInput(f"FA Cup R3: {len(clubs)} exempt clubs")
    return sorted(clubs), [f"qualifier {i:02d}" for i in range(1, FA_R3_CLUBS - len(clubs) + 1)]


def clubs_by_tier(results, season_start, before):
    """{tier: sorted football-data names} seen in the season's league results."""
    out = defaultdict(set)
    for d, tier, home, away, _ in results:
        if season_start <= d < before:
            out[tier].update((home, away))
    return {t: sorted(v) for t, v in out.items()}


# ---------------------------------------------------------------------------
# the season's calendar
# ---------------------------------------------------------------------------

def uk_date(t):
    return (t + uk_offset(t)).date()


class Season:
    """The original fixture list (10-id blocks), the windows and the midweeks.

    `fixtures`: [(id, event or None, kickoff UTC or None, home cup name, away cup name)]."""

    def __init__(self, name, fixtures):
        self.name = name
        self.original = defaultdict(list)                  # gw -> [(id, home, away)]: the published schedule
        self.days = defaultdict(set)                       # gw -> UK dates of its fixtures, in their id block
        self.actual = defaultdict(int)                     # (club, gw) -> fixtures by `event`: the outcome
        kick = defaultdict(list)
        league_day = defaultdict(set)                      # UK date -> clubs with a fixture there, in its block
        for fid, event, ko, home, away in fixtures:
            block = (fid - 1) // 10 + 1
            self.original[block].append((fid, home, away))
            if event is not None:
                self.actual[(home, event)] += 1
                self.actual[(away, event)] += 1
            if event == block and ko is not None:
                kick[block].append(ko)
                self.days[block].add(uk_date(ko))
                league_day[uk_date(ko)].update((home, away))
        self.clubs = sorted({c for rows in self.original.values() for _, h, a in rows for c in (h, a)})
        self.gws = sorted(self.original)
        self.deadline = {g: min(kick[g]) - timedelta(minutes=90) for g in self.gws if kick[g]}
        missing = [g for g in self.gws if g not in self.deadline]
        if missing:
            raise MissingInput(f"{name}: no fixture left in the id block of GW{missing[0]}")
        self.base = defaultdict(int)
        for g, rows in self.original.items():
            for _, h, a in rows:
                self.base[(h, g)] += 1
                self.base[(a, g)] += 1
        self.midweeks = []                                 # (Tuesday, gw of its Wednesday noon, clubs with a league fixture)
        days = sorted(league_day)
        tue = days[0] - timedelta(days=(days[0].weekday() - 1) % 7)
        while tue <= days[-1]:
            before = [tue - timedelta(days=i) for i in range(1, 5)]        # Friday to Monday just before
            after = [tue + timedelta(days=i) for i in range(3, 7)]         # Friday to Monday just after
            if any(d in league_day for d in before) and any(d in league_day for d in after):
                wed = datetime(tue.year, tue.month, tue.day, 12, tzinfo=UTC) + timedelta(days=1)
                gw = self.window(wed)
                if gw is not None:
                    busy = set().union(*(league_day.get(tue + timedelta(days=i), set()) for i in range(3)))
                    self.midweeks.append((tue, gw, busy))
            tue += timedelta(days=7)

    def window(self, t):
        held = [g for g, dl in self.deadline.items() if dl <= t]
        return max(held) if held else None

    def blank_gw(self, day):
        """The gameweek whose fixtures, in their id block, kick off on UK day `day`; None without one (amendment, item 5)."""
        hit = [g for g in self.gws if day in self.days[g]]
        return hit[0] if hit else None


# ---------------------------------------------------------------------------
# the Monte Carlo
# ---------------------------------------------------------------------------

def european_busy(europe, rng_draw):
    """{Tuesday: clubs busy that midweek} for one simulation. `europe` is
    [{"date", "clubs", "knockout": None or the knockout stage from 0, "competition"}].
    A club plays the first knockout stage and goes out at each with probability 0.5."""
    out = defaultdict(set)
    reach = {}
    for row in europe:
        tue = row["date"] - timedelta(days=(row["date"].weekday() - 1) % 7)
        if row["date"].weekday() not in (1, 2, 3):
            continue
        for club in row["clubs"]:
            if row["knockout"] is None:
                out[tue].add(club)
            else:
                key = (club, row["competition"])
                if key not in reach:
                    stages = 0
                    while stages < 8 and rng_draw() >= ELIMINATION:
                        stages += 1
                    reach[key] = stages
                if reach[key] >= row["knockout"]:
                    out[tue].add(club)
    return out


def simulate(season, ties, rating, field, round_dates, origin_gw, n=N, seed=SEED, europe=()):
    """({(club, gw): P(blank)}, {(club, gw): P(double)}) for every club and every
    gameweek after the origin's, on the original schedule as known at the origin."""
    origin = uk_date(season.deadline[origin_gw])
    rng = random.Random(seed)
    states = {c: cup_state(ties, c, origin) for c in ROUNDS}
    rounds_on = {}                                         # blank rounds in a later gameweek: (competition, round) -> (date, k)
    for c, r in BLANK_ROUNDS:
        if (season.name, c, r) not in round_dates:
            raise MissingInput(f"round_dates.csv has no {season.name} {c} {r}")
        day = round_dates[(season.name, c, r)][0]
        k = season.blank_gw(day)
        if k is not None and k > origin_gw:
            rounds_on[(c, r)] = (day, k)
    midweek_rounds = defaultdict(list)                     # Tuesday -> [(competition, round)] dated that Tuesday to Thursday
    for (sn, c, r), days in round_dates.items():
        if sn == season.name:
            for day in days:
                if day.weekday() in (1, 2, 3):
                    midweek_rounds[day - timedelta(days=day.weekday() - 1)].append((c, r))
    later = {k: [m for m in season.midweeks if m[1] > k] for _, k in rounds_on.values()}
    earlier = {k: [m for m in reversed(season.midweeks) if m[1] < k and m[0] > origin] for _, k in rounds_on.values()}
    blank, double = defaultdict(int), defaultdict(int)
    for key, b in season.base.items():
        blank[key] += n if b == 0 else 0
        double[key] += n if b >= 2 else 0
    for _ in range(n):
        sim = {c: simulate_cup(states[c], c, rating, field.get(c, ()), origin, rng) for c in ROUNDS}
        euro = european_busy(europe, rng.random) if europe else {}
        postponed = {}
        for (c, r), (day, k) in rounds_on.items():
            clubs = sim[c].get(r, ())
            for fid, home, away in season.original[k]:
                if home in clubs or away in clubs:
                    postponed[(k, fid)] = (home, away)
        if not postponed:
            continue
        delta = defaultdict(int)
        placed = defaultdict(set)

        def free(m, home, away):
            tue, _, league = m
            for club in (home, away):
                if club in league or club in placed[tue] or club in euro.get(tue, ()):
                    return False
                if any(club in sim[c].get(r, ()) for c, r in midweek_rounds.get(tue, ())):
                    return False
            return True

        for (k, fid), (home, away) in sorted(postponed.items()):
            delta[(home, k)] -= 1
            delta[(away, k)] -= 1
            slot = next((m for m in later[k] if free(m, home, away)), None) or next((m for m in earlier[k] if free(m, home, away)), None)
            if slot is not None:                           # with no free midweek, no double is predicted
                placed[slot[0]].update((home, away))
                delta[(home, slot[1])] += 1
                delta[(away, slot[1])] += 1
        for key, d in delta.items():
            b = season.base[key]
            blank[key] += (b + d == 0) - (b == 0)
            double[key] += (b + d >= 2) - (b >= 2)
    gws = [g for g in season.gws if g > origin_gw]
    return ({(c, g): blank[(c, g)] / n for c in season.clubs for g in gws},
            {(c, g): double[(c, g)] / n for c in season.clubs for g in gws})
