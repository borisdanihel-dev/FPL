"""tools/gate_v2.py - status gate v2, the rule behind the source xp_v2_g2 (prereg/FM.md, BUILD_PLAN Part F item F-M;
Boris's five answers of Thu 12 Nov night, his answers of Mon 16 Nov; the design pinned in prereg/FM.md before this
code). Offline; standard library only; the nightly never imports it. xp_v2 (the v1 gate) and
tools/xp_v2_live.core are not edited: v2 changes only which players core values in each week, their P(start), their
P(sub) scale and, for a double gameweek split by a return date, the fixtures it sees.

The rule, per player, per week u of the horizon (t = the next gameweek), from the status in the origin's export:
  a                         as v1
  d, chance c               u = t: the gate lifted, P(start) x c and P(sub) x c; u > t: as normal
  s, "Suspended until <D>"  0 for every club fixture kicking off before D; as normal from the first on or after it
  s, no date                u = t: 0; u > t: as normal
  i, "Expected back <D>"    like s with a date
  i, return unknown         u = t and t+1: 0; from t+2: P(start) x 0.5 and P(sub) x 0.5
  u, n                      0
"As normal" is status a with no flag: chance 100. Point 5: suspended gameweeks count as neither started nor missed -
the window is the last four gameweeks in which the player was not suspended, for the starts and for the 45-minute
gate alike; a player is suspended in gameweek e when the newest archived export generated before e's deadline has
him at status s. A gameweek with no archived export before its deadline is unknown: taken as not suspended, and
counted (never guessed silently).
"""
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2 as XV                                                # noqa: E402
import xp_v2_live as XL                                           # noqa: E402

SOURCE = "xp_v2_g2"
MONTHS = {m: i for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1)}
DATED = re.compile(r"(?:Suspended until|Expected back) (\d{1,2}) (" + "|".join(MONTHS) + r")\b")
HALF = 0.5                                  # answer 1: a fixed 50% from t+2 for 'i' with an unknown return


class MissingInput(XL.MissingInput):
    """A required input is missing: reported, never substituted."""


def return_date(news, generated):
    """The date in "Suspended until 5 Dec" / "Expected back 28 Nov", in the first year that puts it on or after the
    export's generated date; None when the news names no date in either form."""
    m = DATED.search(news or "")
    if not m:
        return None
    day, mon, gen = int(m.group(1)), MONTHS[m.group(2)], generated.date()
    for year in (gen.year, gen.year + 1):
        try:
            when = date(year, mon, day)
        except ValueError:
            continue
        if when >= gen:
            return when
    return None


def kind(p, generated):
    """(kind, return date or None, chance 0..1) of one export row: 'a', 'd', 'dated' (s or i with a date),
    's' (no date), 'i' (return unknown) or 'out' (u, n, anything else)."""
    st = p.get("status")
    if st == "a":
        return "a", None, None
    if st == "d":
        return "d", None, E.chance_of_playing(p) / 100.0
    if st in ("s", "i"):
        when = return_date(p.get("news"), generated)
        if when is not None:
            return "dated", when, None
        return st, None, None
    return "out", None, None


def week_plan(k, when, chance, u, t, kickoffs):
    """For a player of kind k in week u (t = the next gameweek): (mode, kept fixture ids or None). mode is 'v1',
    'out', 'normal', 'lifted' (P(start) and P(sub) x chance) or 'half'. kickoffs: {fid: kickoff datetime} of the
    club's fixtures in week u (a dated return keeps the fixtures kicking off on or after the date)."""
    if k == "a":
        return "v1", None
    if k == "d":
        return ("lifted", None) if u == t else ("normal", None)
    if k == "dated":
        kept = sorted(fid for fid, ko in kickoffs.items() if ko.date() >= when)
        if not kept:
            return "out", None
        return "normal", (None if len(kept) == len(kickoffs) else kept)
    if k == "s":
        return ("out", None) if u == t else ("normal", None)
    if k == "i":
        return ("out", None) if u in (t, t + 1) else ("half", None)
    return "out", None


def suspensions(exports, deadlines, upto):
    """({pid: {gameweeks suspended}}, {gameweeks unknown}) for gameweeks 1..upto: suspended in e when the newest
    export generated before e's deadline has the player at status 's'; e is unknown when there is no such export.
    exports: OL.dated_exports(...) [(generated, path, d)]; deadlines: {event: datetime}."""
    out, unknown = defaultdict(set), set()
    for e in range(1, upto + 1):
        dl = deadlines.get(e)
        best = None
        for gen, _, d in exports:
            if dl is not None and gen < dl:
                best = d
        if best is None:
            unknown.add(e)
            continue
        for p in best["all_players"]:
            if p.get("status") == "s":
                out[p["id"]].add(e)
    return out, unknown


def window(rows, gws, suspended):
    """{pid: (starts, minutes, n gameweeks)} over each player's last min(4, gws) gameweeks up to gws in which he was
    not suspended (point 5). rows: canonical rows (player_id, event, starts, minutes), one or more per gameweek."""
    per = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))
    for r in rows:
        if r["event"] <= gws:
            a = per[r["player_id"]][r["event"]]
            a[0] += r["starts"] or 0
            a[1] += r["minutes"] or 0
    out = {}
    for pid in set(per) | set(suspended):
        sus = suspended.get(pid, set())
        ws = [e for e in range(gws, 0, -1) if e not in sus][:min(4, gws)]
        out[pid] = (sum(per[pid][e][0] for e in ws if e in per[pid]),
                    sum(per[pid][e][1] for e in ws if e in per[pid]), len(ws))
    return out


def origin_inputs(d, c_rows, gws, suspended):
    """The per-player inputs v2 needs beside v1's: {pid: (p_start as normal (chance 100), minutes in the window)}
    under point 5, for every player whose window holds a suspended gameweek or who is flagged; others are v1's."""
    win = window(c_rows, gws, suspended)
    out = {}
    for p in d["all_players"]:
        pid = p["id"]
        s, m, n = win.get(pid, (0, 0.0, min(4, gws)))
        out[pid] = (min(1.0, s / max(1, n)), m)
    return out


def matrix(d, target, weeks_n, book, model, prior, names, rule="v1", suspended=None):
    """xp_v2 as tested for weeks target..target+weeks_n-1 from one export d (its gameweek is target - 1), as
    builder.live_matrix builds it (v1), or under status gate v2 (rule 'v2'; suspended: {pid: {gameweeks}}, point 5).
    Returns ([{pid: xP}] per week, {pid: [mode per week]} for v2)."""
    if d["gameweek"] + 1 != target:
        raise MissingInput(f"the export is for GW{d['gameweek'] + 1}, not GW{target}")
    c = E.canonical_through(E.canonical_from_export(d), d["gameweek"])
    inp = E.reliability_inputs(c, gws_played=d["gameweek"])
    by_round, rows = XL.export_rows(d)
    tot = SH.team_totals(rows, {})
    gate1 = {int(p["id"]): p["status"] == "a" for p in d["all_players"]}
    chance1 = XV.chance_scale(d)
    ict = XL.ict_live(d)
    gen = datetime.fromisoformat(d["generated"])
    kinds = {p["id"]: kind(p, gen) for p in d["all_players"]}
    norm = origin_inputs(d, c["rows"], d["gameweek"], suspended or {}) if rule == "v2" else {}
    weeks, modes = [], defaultdict(list)
    for u in range(target, target + weeks_n):
        fx = XL.target_fixtures(d, u)
        lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}

        def fixtures_of(team, fx=fx, keep=None):
            return [(fid, f) for fid, f in fx.items() if team in (f["home"], f["away"]) and (keep is None or fid in keep)]

        def lam_team(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_home"] if team == fx[fid]["home"] else lam[fid][0]["lambda_away"]

        def lam_opp(fid, team, fx=fx, lam=lam):
            return lam[fid][0]["lambda_away"] if team == fx[fid]["home"] else lam[fid][0]["lambda_home"]

        def run(inp_u, gate_u, chance_u, fo=fixtures_of):
            return XL.core(inp_u, names, by_round, target, rows, {}, tot, prior, fo, lam_team, lam_opp,
                           ict=ict, chance=chance_u, gate=gate_u)[0]
        if rule == "v1":
            weeks.append(run(inp, gate1, chance1))
            continue
        players = dict(inp["players"])
        gate_u, chance_u, split = dict(gate1), dict(chance1), {}
        for p in d["all_players"]:
            pid = p["id"]
            k, when, ch = kinds[pid]
            kick = {fid: f["kickoff"] for fid, f in fixtures_of(p["team"])}
            mode, keep = week_plan(k, when, ch, u, target, kick)
            modes[pid].append(mode if keep is None else "normal (split)")
            if pid not in players:
                continue
            ps, mins = norm.get(pid, (None, None))
            q = dict(players[pid])
            if ps is not None:
                q["mins_last4"] = mins                       # point 5: the window without suspended gameweeks
            if mode == "v1":
                if ps is not None:
                    q["p_start"] = ps * chance1.get(pid, 1.0)
                players[pid] = q
                continue
            if mode == "out":
                gate_u[pid] = False
                continue
            scale = {"normal": 1.0, "lifted": ch, "half": HALF}[mode]
            q["p_start"] = ps * scale
            players[pid] = q
            gate_u[pid] = True
            chance_u[pid] = scale
            if keep is not None:
                split[pid] = keep
        inp_u = dict(inp, players=players)
        for pid in split:
            gate_u[pid] = False                              # valued below on its kept fixtures only
        xp = run(inp_u, gate_u, chance_u)
        for pid, keep in split.items():
            team = players[pid]["team"]
            only = {q: (q == pid) for q in gate_u}
            xp.update(run(inp_u, only, chance_u, fo=lambda tm, keep=keep: fixtures_of(tm, keep=set(keep))
                          if tm == team else []))
        weeks.append(xp)
    return weeks, dict(modes)


def origin(data_dir, g, exports=None):
    """The inputs at gameweek g's deadline, point-in-time: the newest dated export generated before it, the newest
    Odds API snapshot before it, the fallback fitted on results before it. (d, path, deadline, book, model)."""
    _, deadlines, fixtures, _, _ = OL.sqlite_tables(data_dir)
    dl = deadlines.get(g)
    if dl is None:
        raise MissingInput(f"GW{g}: no deadline in events")
    exports = OL.dated_exports(data_dir) if exports is None else exports
    best = OL.pre_deadline_export(exports, dl, g)
    if best is None:
        raise MissingInput(f"GW{g}: no export generated before its deadline")
    snap = OL.newest_snapshot(data_dir, dl)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    return best[2], best[1], dl, book, XL._model(fixtures, dl), (os.path.basename(snap[0]) if snap else None)


def modes_count(modes):
    """Counter of (week index, mode) for the printed summary."""
    return Counter((i, m) for ms in modes.values() for i, m in enumerate(ms))
