"""fpl_xpv2.py - the runner's copy of tools/xp_v2_live.py, the part W3 needs:
the live forecast of xp_v2 as tested (S6d), recorded nightly as
source xp_v2 (W3; prereg/W3.md, Part F item F-B).

Every definition below is copied verbatim from tools/xp_v2_live.py by its syntax
tree, module aliases kept and pointed at the runner's copies, so the
runner never imports tools/; tests/test_W3.py holds the copies to the
tools. Standard library only.
"""
import fpl_edge as E
import fpl_lambda as OL
import fpl_shares as SH
import fpl_xpr as XR
import fpl_xpv as XV
import json
import os
from collections import defaultdict
from datetime import datetime, timezone


POS_CODE = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}


PRIOR_SEASON = "2025-26"            # S11: priors come from last season (BUILD_PLAN.md Step 11)


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted (S6c's
    info_2627 catches it as its own)."""


def core(inp, names, by_round, t, s11_rows, n2s, tot, prior, fixtures_of, lam_team, lam_opp, ict=None, chance=None,
         gate=None):
    """({pid: xp_v2}, {pid: detail}) at origin t. inp: reliability_inputs on
    the training slice; names: pid -> the prior's name; by_round: raw rows
    per round (rounds < t are read); s11_rows, n2s, tot: S11's rows, club
    map and team totals; prior: S11's Prior; fixtures_of(team) -> [(fid,
    {home, away})] of round t; lam_team / lam_opp (fid, team) -> lambda;
    ict: pid -> percentile (None: ict_percentile on by_round); chance: pid ->
    0..1 on P(sub) (None: 1); gate: pid -> bool (None: everyone)."""
    pos_of = {pid: p["pos"] for pid, p in inp["players"].items()}
    p_sub, e_sub = XR.sub_inputs_2526(by_round, t, pos_of)
    ict = XR.ict_percentile(by_round, t) if ict is None else ict
    dc = XR.defcon_rates(by_round, t, pos_of)
    agg = SH.player_sums(s11_rows, n2s, set(range(1, t)), tot)
    pos_start = defaultdict(list)
    for pid, a in agg.items():
        if pid in inp["players"] and a["starts"]:
            pos_start[inp["players"][pid]["pos"]].append(a["start_minutes"] / a["starts"])
    pos_mean_start = {pos: sum(v) / len(v) for pos, v in pos_start.items()}
    out, detail = {}, {}
    for pid, p in inp["players"].items():
        if p["mins_last4"] < XR.GATE_MINS:
            continue
        if gate is not None and not gate.get(pid):
            continue
        fx = fixtures_of(p["team"])
        if not fx:
            continue
        ps = p["p_start"]
        a = agg.get(pid)
        m = a["minutes"] / 90.0 if a else 0.0
        m_start = (a["start_minutes"] / a["starts"]) if a and a["starts"] else pos_mean_start.get(p["pos"], 90.0)
        lam_fx, cs, alloc, how, parts = [], 0.0, {"xg": 0.0, "xa": 0.0}, {}, []
        for fid, f in fx:
            home = p["team"] == f["home"]
            opp = f["away"] if home else f["home"]
            lo = lam_opp(fid, p["team"])
            lam_fx.append((opp, home, lo))
            cs += OL.p_clean_sheet(lo) * E.CS_VALUE.get(p["pos"], 0)
            lt = lam_team(fid, p["team"])
            part = {"opp": opp, "home": home, "lam_opp": lo}             # S14: the fixture's own terms
            for key in ("xg", "xa"):
                s = SH.share_of(a, key) if a else 0.0
                s0, how[key] = prior.prior(names[pid], p["pos"], p["team"], key)
                z = m / (m + prior.k[key])
                part[key] = lt * (z * s + (1 - z) * s0) * (m_start / 90.0)   # per start: S11's forecast without P(start)
                alloc[key] += part[key]
            parts.append(part)
        bl = OL.forecast_lambda(pid, inp, lam_fx)
        e_bl = (bl / ps) if (ps > 0 and bl is not None) else 0.0
        e_xg = XR.xg_half(p["pos"], alloc["xg"], alloc["xa"], cs, dc.get(pid, 0.0), ict.get(pid, 0.5))
        psub = min(1.0, p_sub.get(pid, 0.0) * (1.0 if chance is None else chance.get(pid, 1.0)))
        v = XV.xp_candidates(ps, e_xg, e_bl, psub, e_sub.get(p["pos"], 0.0))["blend"]
        out[pid] = v
        detail[pid] = {"p_start": ps, "e_xg": e_xg, "e_bl": e_bl, "p_sub": psub, "e_sub": e_sub.get(p["pos"], 0.0),
                       "xg": alloc["xg"], "xa": alloc["xa"], "cs": cs, "defcon": dc.get(pid, 0.0), "ict": ict.get(pid, 0.5),
                       "prior": how.get("xg"), "fixtures": parts}
    return out, detail


def export_rows(d):
    """The export's rows (events <= its gameweek) as S6b's raw rows per round
    and as S11's rows: one unit per player-gameweek, the club = the
    player's club in the export, the fixture key = the gameweek."""
    club = {int(p["id"]): p["team"] for p in d["all_players"]}
    pos = {int(p["id"]): p["pos"] for p in d["all_players"]}
    by_round, rows = defaultdict(list), []
    for r in d.get("player_gw_recent") or []:
        if "player_id" not in r:
            raise MissingInput("the export's player_gw_recent has no player_id")
        pid, ev = int(r["player_id"]), int(r["event"])
        if ev > d["gameweek"] or pid not in club:
            continue
        row = {"element": pid, "round": ev, "fixture": str(ev), "team": club[pid], "position": POS_CODE.get(pos[pid], ""),
               "minutes": r.get("mins") or 0, "starts": r.get("starts") or 0, "total_points": r.get("pts") or 0,
               "defensive_contribution": r.get("defcon") or 0, "expected_goals": r.get("xg") or 0,
               "expected_assists": r.get("xa") or 0}
        by_round[ev].append(row)
        rows.append(row)
    return by_round, rows


def ict_live(d):
    """The ICT percentile on season influence + creativity + threat among
    players with minutes > 0 (S6b's ordering, ict_percentile)."""
    one = [{"element": int(p["id"]), "minutes": p.get("minutes") or 0,
            "ict_index": (p.get("influence") or 0) + (p.get("creativity") or 0) + (p.get("threat") or 0)}
           for p in d["all_players"]]
    return XR.ict_percentile({1: one}, 2)


def target_fixtures(d, target):
    """{fid: {home, away, kickoff}} of the target from the export's fixtures_next6."""
    out = {}
    for f in d.get("fixtures_next6") or []:
        if f["event"] == target:
            out[f"{f['home']}-{f['away']}"] = {"home": f["home"], "away": f["away"],
                                               "kickoff": datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))}
    return out


def forecast(d, target, book, model, prior, names):
    """xp_v2 as tested for `target` from one export d (its gameweek is
    target - 1): ({pid: xp_v2}, detail, the sources of the lambdas)."""
    if d["gameweek"] + 1 != target:
        raise MissingInput(f"the export is for GW{d['gameweek'] + 1}, not GW{target}")
    c = E.canonical_through(E.canonical_from_export(d), d["gameweek"])   # the training slice: never the target's rows
    inp = E.reliability_inputs(c, gws_played=d["gameweek"])
    by_round, rows = export_rows(d)
    tot = SH.team_totals(rows, {})
    fx = target_fixtures(d, target)
    if not fx:
        raise MissingInput(f"no fixtures for GW{target} in the export")
    lam = {fid: OL.fixture_lambdas(book, model, f["kickoff"], f["home"], f["away"]) for fid, f in fx.items()}

    def fixtures_of(team):
        return [(fid, f) for fid, f in fx.items() if team in (f["home"], f["away"])]

    def lam_team(fid, team):
        return lam[fid][0]["lambda_home"] if team == fx[fid]["home"] else lam[fid][0]["lambda_away"]

    def lam_opp(fid, team):
        return lam[fid][0]["lambda_away"] if team == fx[fid]["home"] else lam[fid][0]["lambda_home"]
    missing = [pid for pid in inp["players"] if pid not in names]
    if missing:
        raise MissingInput(f"{len(missing)} players have no name for the prior (fpl.sqlite players)")
    gate = {int(p["id"]): p["status"] == "a" for p in d["all_players"]}
    chance = XV.chance_scale(d)                         # S6's live rule on P(sub)
    out, detail = core(inp, names, by_round, target, rows, {}, tot, prior, fixtures_of, lam_team, lam_opp,
                       ict=ict_live(d), chance=chance, gate=gate)
    return out, detail, {fid: src for fid, (_, src) in lam.items()}


# ---------------------------------------------------------------------------
# the runner's entry point (not in tools/xp_v2_live.py): the record reads the
# export, the odds snapshot and the committed prior file, never the database
# ---------------------------------------------------------------------------

PRIOR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "priors", f"s11_prior_{PRIOR_SEASON}.json")


def load_prior_file(path=PRIOR_FILE):
    """The saved S11 state (tools/make_prior.py): raises OSError or ValueError
    when the file is missing or unreadable, KeyError when a part is absent."""
    with open(path, encoding="utf-8") as fh:
        state = json.load(fh)
    for key in ("season", "folder", "by_name_club", "k", "rel", "code_name"):
        if key not in state:
            raise KeyError(f"{os.path.basename(path)} has no {key}")
    if state["season"] != PRIOR_SEASON:
        raise ValueError(f"{os.path.basename(path)} is season {state['season']}, not {PRIOR_SEASON}")
    return state


def export_names(d, code_name):
    """pid -> the name S11's Prior is keyed by, from the export (tools/
    xp_v2_live.py's prior_names, without the database): the player's code
    gives his 2025/26 vaastav name through the prior file, else the 2026/27
    first + second name; and the count reached through code."""
    out, by_code = {}, 0
    for p in d["all_players"]:
        for key in ("code", "first_name", "second_name"):
            if key not in p:
                raise MissingInput(f"the export's all_players has no {key} (the prior's key)")
        code = p["code"]
        n25 = code_name.get(str(code)) if code is not None else None
        if n25 is not None:
            by_code += 1
        out[int(p["id"])] = n25 if n25 is not None else f"{p['first_name']} {p['second_name']}"
    return out, by_code


def live_forecast(d, target, deadline, data_dir, state):
    """xp_v2 as tested for `target` from the export d, the newest odds
    snapshot in data_dir/odds taken before the deadline (none: every fixture
    on the fallback, as tools/xp_v2_live.py's live()), the fallback fitted on
    the export's results before the deadline (W2) and the S11 state: a dict
    as live() returns (xp, detail, sources, snapshot, by_code, d)."""
    names, by_code = export_names(d, state["code_name"])
    snap = OL.newest_snapshot(data_dir, deadline)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    model = OL.fit_fallback(OL.results_before(d, deadline), deadline)
    xp, detail, srcs = forecast(d, target, book, model, SH.Prior(state), names)
    return {"target": target, "deadline": deadline, "xp": xp, "detail": detail, "sources": srcs,
            "snapshot": (os.path.basename(snap[0]), snap[2]) if snap else None, "by_code": by_code, "d": d,
            "season": state["season"]}


def record(d, target, deadline, data_dir, prior_path=None):
    """(rows, note, skipped) for the record: [(id, web_name, value)] of xp_v2
    as tested (live_forecast) for every player with a positive value, rounded
    as every source; a missing prior file or key is a skip (rows empty)."""
    prior_path = prior_path or PRIOR_FILE
    try:
        state = load_prior_file(prior_path)
    except (OSError, ValueError, KeyError) as e:
        return [], f"the S11 prior {os.path.basename(prior_path)} is missing or unreadable ({type(e).__name__}: {e})", True
    try:
        res = live_forecast(d, target, deadline, data_dir, state)
    except (XR.MissingInput, OL.MissingInput, SH.MissingInput) as e:
        return [], str(e), True
    by_id = {p["id"]: p for p in d["all_players"]}
    rows = [(pid, by_id[pid]["web_name"], round(v, 3)) for pid, v in res["xp"].items() if v > 0]
    n_odds = sum(1 for s in res["sources"].values() if s == "odds")
    lam = (f"snapshot {res['snapshot'][0]}, {n_odds} of {len(res['sources'])} fixtures from odds" if res["snapshot"]
           else f"no odds snapshot before the GW{target} deadline: every fixture on the fallback")
    return rows, f"{lam}; prior {res['season'].replace('-', '/')} (S11 file), {res['by_code']} players keyed by code", False
