"""fpl_lambda.py - bottomup_lambda in the runner path (W2 piece b;
prereg/W2.md, RULING W2 build point 2 and the W2 addition). S5's live
forecast, recorded nightly as a sixth source: the newest Odds API snapshot
taken before the next deadline (W1's odds/ folder), the mean price across
bookmakers for h2h (h2h_lay out) and totals at 2.5, power de-margin, the
Poisson lambdas, the time-decayed fallback fitted on the export's results
before the deadline for a fixture without odds (the record never opens the
database), and bottomup's terms with the GK/DEF
clean sheet and goals conceded from the opponent's lambda.

Every function below is copied verbatim from tools/odds_lambda.py (lane B's
S5, adopted), so the runner never imports tools/; tests/test_W2.py holds the
two to byte-identical numbers on the same snapshot and export.
Standard library only.
"""
import glob
import gzip
import json
import math
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

import fpl_edge as E

XI = 0.0065                 # Dixon-Coles decay per day


MIN_WEIGHTED = 4.0          # below this weighted match count the fallback uses the league average


MAX_GOALS = 15


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def demargin_proportional(odds):
    q = [1.0 / o for o in odds]
    s = sum(q)
    return [x / s for x in q]


def demargin_power(odds, tol=1e-12):
    """p_i = q_i^k with k solved by bisection so that sum p_i = 1."""
    q = [1.0 / o for o in odds]
    lo, hi = 0.5, 3.0
    for _ in range(200):
        k = (lo + hi) / 2
        s = sum(x ** k for x in q)
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            lo = k
        else:
            hi = k
    return [x ** k for x in q]


def poisson_pmf(lam, k):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_cdf(lam, k):
    return sum(poisson_pmf(lam, i) for i in range(k + 1))


def lambda_total(p_under, tol=1e-10):
    """Total goals lambda with P(0, 1 or 2 goals) = p_under, by bisection."""
    if not 0.0 < p_under < 1.0:
        raise ValueError(f"P(under 2.5) must be in (0, 1), got {p_under}")
    lo, hi = 1e-6, 15.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if poisson_cdf(mid, 2) > p_under:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2


def p_home_win(lam_h, lam_a, n=MAX_GOALS):
    ph = [poisson_pmf(lam_h, i) for i in range(n + 1)]
    pa = [poisson_pmf(lam_a, j) for j in range(n + 1)]
    return sum(ph[i] * pa[j] for i in range(n + 1) for j in range(i))


def split_lambda(total, p_home, tol=1e-10):
    """(lambda_home, lambda_away) with lambda_home + lambda_away = total and
    P(home win) = p_home under independent Poisson, by bisection."""
    lo, hi = 1e-6, total - 1e-6
    for _ in range(200):
        mid = (lo + hi) / 2
        if p_home_win(mid, total - mid) < p_home:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    lh = (lo + hi) / 2
    return lh, total - lh


def lambdas_from_odds(o_h, o_d, o_a, o_over, o_under, method="power"):
    """{lambda_home, lambda_away, p_home, p_under, method} from five odds."""
    dm = demargin_power if method == "power" else demargin_proportional
    p_h, _, _ = dm([o_h, o_d, o_a])
    _, p_under = dm([o_over, o_under])
    total = lambda_total(p_under)
    lh, la = split_lambda(total, p_h)
    return {"lambda_home": lh, "lambda_away": la, "p_home": p_h, "p_under": p_under, "method": method}


def p_clean_sheet(lam_opp):
    return math.exp(-lam_opp)


def expected_gc_penalty(lam_opp, n=MAX_GOALS):
    """E[floor(GC / 2)] under Poisson(lambda_opp): the goals-conceded points a
    GK or DEF loses, in expectation."""
    return sum(poisson_pmf(lam_opp, k) * (k // 2) for k in range(n + 1))


class OddsBook:
    """Odds by (date, home, away), matched to a fixture by its kickoff date
    (the same day, else the day before or after)."""

    def __init__(self, rows):
        self.by_key = {(r["date"], r["home"], r["away"]): r for r in rows}

    def find(self, kickoff, home, away):
        d0 = kickoff.date() if isinstance(kickoff, datetime) else kickoff
        for delta in (0, -1, 1):
            r = self.by_key.get((d0 + timedelta(days=delta), home, away))
            if r is not None:
                return r
        return None


def fit_fallback(results, deadline, xi=XI, iters=20):
    """results: [(kickoff datetime/date, home, away, home_goals, away_goals)];
    only results with kickoff before `deadline` are used, weighted
    exp(-xi x days before the deadline). Returns {"m", "hf", "att", "def",
    "n"} - multiplicative strengths by alternating weighted updates; a team
    with fewer than MIN_WEIGHTED weighted matches keeps strength 1."""
    dl = deadline.date() if isinstance(deadline, datetime) else deadline
    used = []
    for ko, h, a, hg, ag in results:
        kd = ko.date() if isinstance(ko, datetime) else ko
        if kd < dl and hg is not None and ag is not None:
            used.append((math.exp(-xi * (dl - kd).days), h, a, float(hg), float(ag)))
    if not used:
        return {"m": 1.3, "hf": 1.0, "att": {}, "def": {}, "n": {}}
    wsum = sum(w for w, *_ in used)
    m = sum(w * (hg + ag) for w, _, _, hg, ag in used) / (2 * wsum)
    home_goals = sum(w * hg for w, _, _, hg, _ in used)
    away_goals = sum(w * ag for w, _, _, _, ag in used)
    hf = home_goals / away_goals if away_goals > 0 else 1.0
    teams = {t for _, h, a, _, _ in used for t in (h, a)}
    n = {t: sum(w for w, h, a, _, _ in used if t in (h, a)) for t in teams}
    att = {t: 1.0 for t in teams}
    dfc = {t: 1.0 for t in teams}
    sh, sa = math.sqrt(hf), 1 / math.sqrt(hf)
    for _ in range(iters):
        new_att = {}
        for t in teams:
            if n[t] < MIN_WEIGHTED:
                new_att[t] = 1.0
                continue
            num = sum(w * (hg if h == t else ag) for w, h, a, hg, ag in used if t in (h, a))
            den = sum(w * m * (dfc[a] * sh if h == t else dfc[h] * sa) for w, h, a, _, _ in used if t in (h, a))
            new_att[t] = num / den if den else 1.0
        att = new_att
        new_def = {}
        for t in teams:
            if n[t] < MIN_WEIGHTED:
                new_def[t] = 1.0
                continue
            num = sum(w * (ag if h == t else hg) for w, h, a, hg, ag in used if t in (h, a))
            den = sum(w * m * (att[a] * sa if h == t else att[h] * sh) for w, h, a, _, _ in used if t in (h, a))
            new_def[t] = num / den if den else 1.0
        dfc = new_def
    return {"m": m, "hf": hf, "att": att, "def": dfc, "n": n}


def fallback_lambdas(model, home, away):
    m, hf = model["m"], model["hf"]
    att, dfc = model["att"], model["def"]
    lh = m * att.get(home, 1.0) * dfc.get(away, 1.0) * math.sqrt(hf)
    la = m * att.get(away, 1.0) * dfc.get(home, 1.0) / math.sqrt(hf)
    return {"lambda_home": lh, "lambda_away": la, "method": "fallback"}


def fixture_lambdas(book, model, kickoff, home, away, method="power"):
    """(lambdas, source): the odds row's lambdas, else the fallback's."""
    r = book.find(kickoff, home, away) if book is not None else None
    if r is not None:
        o = r["odds"]
        return lambdas_from_odds(o["H"], o["D"], o["A"], o["over"], o["under"], method), "odds"
    return fallback_lambdas(model, home, away), "fallback"


def lambda_terms(pos, ps, lam_opp):
    """The GK/DEF clean-sheet and goals-conceded terms under lambda_opp, in
    points; None for MID/FWD (their terms are bottomup's own)."""
    if pos not in (1, 2) or ps <= 0:
        return None
    return ps * (p_clean_sheet(lam_opp) * E.CS_VALUE[pos] - expected_gc_penalty(lam_opp))


def forecast_lambda(pid, inp, fixtures):
    """bottomup_lambda for one player: fixtures = [(opp, was_home, lambda_opp)].
    MID/FWD: project_reliability unchanged. GK/DEF: every term but the
    clean sheet, plus lambda_terms per fixture."""
    if not fixtures:
        return None
    p = inp["players"].get(pid)
    if p is None:
        return None
    pairs = [(opp, home) for opp, home, _ in fixtures]
    if p["pos"] not in (1, 2):
        return E.project_reliability(pid, inp, pairs, E.ALL_TERMS)
    base = E.project_reliability(pid, inp, pairs, E.ALL_TERMS - {"cs"})
    if not base:
        return base
    return base + sum(lambda_terms(p["pos"], p["p_start"], lam) or 0.0 for _, _, lam in fixtures)


API_TEAMS = {
    "Arsenal": "ARS", "Aston Villa": "AVL", "Bournemouth": "BOU", "AFC Bournemouth": "BOU",
    "Brentford": "BRE", "Brighton and Hove Albion": "BHA", "Brighton & Hove Albion": "BHA", "Brighton": "BHA",
    "Burnley": "BUR", "Chelsea": "CHE", "Coventry City": "COV", "Coventry": "COV", "Crystal Palace": "CRY",
    "Everton": "EVE", "Fulham": "FUL", "Hull City": "HUL", "Hull": "HUL", "Ipswich Town": "IPS", "Ipswich": "IPS",
    "Leeds United": "LEE", "Leeds": "LEE", "Liverpool": "LIV", "Manchester City": "MCI", "Man City": "MCI",
    "Manchester United": "MUN", "Man Utd": "MUN", "Man United": "MUN", "Newcastle United": "NEW", "Newcastle": "NEW",
    "Nottingham Forest": "NFO", "Nott'm Forest": "NFO", "Sunderland": "SUN", "Tottenham Hotspur": "TOT",
    "Tottenham": "TOT", "Spurs": "TOT", "West Ham United": "WHU", "West Ham": "WHU",
    "Wolverhampton Wanderers": "WOL", "Wolves": "WOL",
}


TOTALS_LINE = 2.5


_STAMP = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[T_ ]?(\d{2})[-:]?(\d{2})(?:[-:]?(\d{2}))?)?")


def snapshot_time(path, payload):
    """When the snapshot was taken, UTC: a fetch-time field in the payload
    (fetched_at / fetched_at_utc / fetch_time / taken_at / generated), else
    the timestamp in the file name (a date alone counts as the end of that
    UTC day, so it is never read as earlier than it was), else None."""
    if isinstance(payload, dict):
        for k in ("fetched_at", "fetched_at_utc", "fetch_time", "taken_at", "generated"):
            v = payload.get(k)
            if v:
                try:
                    t = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
                    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
    m = _STAMP.search(os.path.basename(path))
    if not m:
        return None
    d = date.fromisoformat(m.group(1))
    if m.group(2) is None:
        return datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc)
    return datetime(d.year, d.month, d.day, int(m.group(2)), int(m.group(3)), int(m.group(4) or 0), tzinfo=timezone.utc)


def snapshot_events(payload):
    """The list of events in a snapshot: the payload itself when it is a
    list, else the first list under a known key."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for k in ("events", "data", "response", "odds"):
            if isinstance(payload.get(k), list):
                return payload[k]
    raise MissingInput("the odds snapshot holds no event list")


def newest_snapshot(data_dir, deadline):
    """(path, payload, taken) for the newest odds/*.json.gz (or .json) taken
    before `deadline`; None when there is none."""
    files = glob.glob(os.path.join(data_dir, "odds", "*.json.gz")) + glob.glob(os.path.join(data_dir, "odds", "*.json"))
    best = None
    for f in files:
        op = gzip.open if f.endswith(".gz") else open
        try:
            with op(f, "rt", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, ValueError) as e:
            raise MissingInput(f"cannot read {f}: {e}")
        taken = snapshot_time(f, payload)
        if taken is None:
            raise MissingInput(f"{f}: no fetch time in the file or its name")
        if taken < deadline and (best is None or taken > best[2]):
            best = (f, payload, taken)
    return best


def aggregate_event(ev):
    """One event -> {date, home, away, odds, n_h2h, n_totals, commence} or
    None when any of the five prices is missing. Mean decimal price across
    bookmakers per outcome: h2h (h2h_lay excluded) and totals at 2.5."""
    home, away = ev.get("home_team"), ev.get("away_team")
    hs, as_ = API_TEAMS.get(home), API_TEAMS.get(away)
    if hs is None or as_ is None:
        raise MissingInput(f"odds snapshot: team {home if hs is None else away!r} is not in the team table")
    sums = defaultdict(float)
    counts = defaultdict(int)
    for b in ev.get("bookmakers") or []:
        for mk in b.get("markets") or []:
            if mk.get("key") == "h2h":
                got = {}
                for o in mk.get("outcomes") or []:
                    if o.get("name") == home:
                        got["H"] = o.get("price")
                    elif o.get("name") == away:
                        got["A"] = o.get("price")
                    elif str(o.get("name", "")).lower() == "draw":
                        got["D"] = o.get("price")
                if all(isinstance(got.get(k), (int, float)) and got[k] > 1 for k in ("H", "D", "A")):
                    for k in ("H", "D", "A"):
                        sums[k] += got[k]
                    counts["h2h"] += 1
            elif mk.get("key") == "totals":
                got = {}
                for o in mk.get("outcomes") or []:
                    if o.get("point") == TOTALS_LINE:
                        if str(o.get("name", "")).lower() == "over":
                            got["over"] = o.get("price")
                        elif str(o.get("name", "")).lower() == "under":
                            got["under"] = o.get("price")
                if all(isinstance(got.get(k), (int, float)) and got[k] > 1 for k in ("over", "under")):
                    for k in ("over", "under"):
                        sums[k] += got[k]
                    counts["totals"] += 1
    if not counts["h2h"] or not counts["totals"]:
        return None
    odds = {k: sums[k] / counts["h2h"] for k in ("H", "D", "A")}
    odds.update({k: sums[k] / counts["totals"] for k in ("over", "under")})
    commence = datetime.fromisoformat(str(ev.get("commence_time", "")).replace("Z", "+00:00")) if ev.get("commence_time") else None
    return {"date": commence.date() if commence else None, "home": hs, "away": as_, "odds": odds, "cols": "api",
            "n_h2h": counts["h2h"], "n_totals": counts["totals"], "commence": commence}


def snapshot_book(payload):
    """(OddsBook, aggregated events, skipped) from a snapshot payload."""
    rows, skipped = [], []
    for ev in snapshot_events(payload):
        agg = aggregate_event(ev)
        if agg is None or agg["date"] is None:
            skipped.append(f"{ev.get('home_team')} v {ev.get('away_team')}")
            continue
        rows.append(agg)
    return OddsBook(rows), rows, skipped


def rebuild_2627(d, target, book, model, method="power"):
    """bottomup (as record_status builds it) and bottomup_lambda from one
    pre-deadline export, for the next gameweek `target`. Returns
    {pid: (bottomup, lambda, p_start, pos, source)}; a blank gives no row."""
    tick, _ = E.build_ticker(d, 6)
    inp = E.reliability_inputs(E.canonical_from_export(d), gws_played=d["gameweek"])
    out = {}
    for p in d["all_players"]:
        if p["status"] != "a" or (p.get("mins_last4") or 0) < 45:
            continue
        fx = []
        for f in tick.get(p["team"], []):
            if f[0] != target:
                continue
            opp, home = f[1].split()[0], f[1].endswith("(H)")
            ko = kickoff_of(d, target, p["team"], opp, home)
            lam, src = fixture_lambdas(book, model, ko, p["team"] if home else opp, opp if home else p["team"], method)
            fx.append((opp, home, lam["lambda_away"] if home else lam["lambda_home"], src))
        if not fx:
            continue
        pairs = [(o, h) for o, h, _, _ in fx]
        proj = E.project_reliability(p["id"], inp, pairs)
        if not proj:
            continue
        lam_proj = forecast_lambda(p["id"], inp, [(o, h, l) for o, h, l, _ in fx])
        pp = inp["players"][p["id"]]
        out[p["id"]] = (proj, lam_proj, pp["p_start"], pp["pos"], ",".join(s for _, _, _, s in fx))
    return out


def kickoff_of(d, event, team, opp, home):
    for f in d.get("fixtures_next6") or []:
        if f["event"] == event and ((home and f["home"] == team and f["away"] == opp) or (not home and f["away"] == team and f["home"] == opp)):
            return datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
    raise MissingInput(f"GW{event}: no kickoff for {team} v {opp} in the export")


# ---------------------------------------------------------------------------
# the runner's entry point (not in tools/odds_lambda.py)
# ---------------------------------------------------------------------------

def results_before(d, deadline):
    """Finished results kicked off before the deadline, from the export's
    fixtures_played (finished = 1, as fpl.sqlite's fixtures that
    tools/odds_lambda.py's live() reads; the record never opens the
    database): (kickoff, home, away, home goals, away goals)."""
    out = []
    for f in d.get("fixtures_played") or []:
        k = datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
        if k < deadline:
            out.append((k, f["home"], f["away"], f["h_goals"], f["a_goals"]))
    return out


def bottomup_lambda(d, target, deadline, data_dir):
    """(rows, note, skipped) for the record: [(id, web_name, value)] of
    bottomup_lambda for `target` from the export d, the newest odds snapshot
    in data_dir/odds taken before the deadline and the fallback fitted on
    results before it; skipped (a RECORD SKIP, rows empty) when there is no
    snapshot."""
    snap = newest_snapshot(data_dir, deadline)
    if snap is None:
        return [], f"no odds snapshot before the GW{target} deadline under {os.path.join(data_dir, 'odds')}", True
    book = snapshot_book(snap[1])[0]
    model = fit_fallback(results_before(d, deadline), deadline)
    reb = rebuild_2627(d, target, book, model)
    by_id = {p["id"]: p for p in d["all_players"]}
    rows = [(pid, by_id[pid]["web_name"], round(v[1], 3)) for pid, v in reb.items() if v[1]]
    n_odds = sum(1 for v in reb.values() if "odds" in v[4].split(","))
    return rows, f"snapshot {os.path.basename(snap[0])}, {n_odds} of {len(reb)} players with odds-priced fixtures", False
