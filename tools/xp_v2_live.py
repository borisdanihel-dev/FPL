"""tools/xp_v2_live.py - S6d, the live "xp_v2 as tested" forecast
(prereg/S6d.md; RULING S6b acceptance + lanes merge point 1). Offline;
standard library only; the nightly never imports it.

xp_v2 as tested is S6b's Replay.xp_v2 term by term (tools/xp_v2_replay.py):
P(start) x (E_xg + E_bl) / 2 + P(sub) x E[pts | sub], with S11's shares in
the xg half, S5's bottomup_lambda in the bottomup half and P(start) from
the current minutes model. core() takes the inputs the replay builds and
returns its numbers (a test holds it to Replay.xp_v2 on S6b's inputs);
forecast() builds those inputs from one 2026/27 export:

  - players and P(start): reliability_inputs(canonical_from_export(d));
    gate mins_last4 >= 45 and status 'a' (every live source's gate);
  - S11's shares from the export's rows (one unit per player-gameweek, the
    club = the player's club in the export), S11's Prior on 2025/26 (last
    season), keyed by the 2025/26 name reached through `code`, else the
    2026/27 first + second name;
  - lambda per fixture by S5's fixture_lambdas (the odds book, else the
    labelled fallback fitted on results before the deadline);
  - DEFCON, ICT and the sub term by S6b's functions on the export's rows;
    live, P(sub) x chance_next_round / 100 (S6's live rule).

live() takes the newest export and the newest Odds API snapshot before the
next deadline; retro(g) takes gameweek g's newest pre-deadline export and
S5's 2026/27 football-data book (S6c's GW5-7 information print).

    python tools/xp_v2_live.py [--data DIR] [--hist ROOT] [--out DIR]
"""
import argparse
import csv
import os
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fpl_edge as E                                              # noqa: E402
import backtest as BT                                             # noqa: E402
import chips as CH                                                # noqa: E402
import odds_lambda as OL                                          # noqa: E402
import shares as SH                                               # noqa: E402
import xp_v2 as XV                                                # noqa: E402
import xp_v2_replay as XR                                         # noqa: E402
from console_utf8 import utf8_console                             # noqa: E402
from provenance import Run                                        # noqa: E402

POS_CODE = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}
PRIOR_SEASON = "2025-26"            # S11: priors come from last season (BUILD_PLAN.md Step 11)
FD_NOTE = ("lambda from S5's 2026/27 football-data book (tools/odds/E0_2026-27_fetched_2026-10-18.csv, fetched on 18 Oct; "
           "football-data's pre-closing prices); no Odds API snapshot exists before 19 Oct")


class MissingInput(XR.MissingInput):
    """A required input is missing: reported, never substituted (S6c's
    info_2627 catches it as its own)."""


# ---------------------------------------------------------------------------
# the core: S6b's Replay.xp_v2, term by term
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 2026/27 inputs
# ---------------------------------------------------------------------------

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


def prior_names(db_path, codes_csv, hist_2526):
    """pid (2026/27) -> the name S11's Prior is keyed by: the 2025/26 vaastav
    name reached through code, else the 2026/27 first + second name; and the
    count reached through code."""
    for p in (codes_csv, os.path.join(hist_2526, "players_raw.csv"), os.path.join(hist_2526, "merged_gw.csv")):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing (the prior's key)")
    with open(codes_csv, encoding="utf-8", newline="") as fh:
        code = {int(r["id"]): r["code"] for r in csv.DictReader(fh)}
    with open(os.path.join(hist_2526, "players_raw.csv"), encoding="utf-8", newline="") as fh:
        id25 = {r["code"]: int(r["id"]) for r in csv.DictReader(fh)}
    name25 = {}
    with open(os.path.join(hist_2526, "merged_gw.csv"), encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            name25.setdefault(int(r["element"]), r["name"])
    c = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        full = {pid: f"{fn} {sn}" for pid, fn, sn in c.execute("SELECT id, first_name, second_name FROM players")}
    finally:
        c.close()
    out, by_code = {}, 0
    for pid, nm in full.items():
        n25 = name25.get(id25.get(code.get(pid)))
        if n25 is not None:
            by_code += 1
        out[pid] = n25 if n25 is not None else nm
    return out, by_code


def target_fixtures(d, target):
    """{fid: {home, away, kickoff}} of the target from the export's fixtures_next6."""
    out = {}
    for f in d.get("fixtures_next6") or []:
        if f["event"] == target:
            out[f"{f['home']}-{f['away']}"] = {"home": f["home"], "away": f["away"],
                                               "kickoff": datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))}
    return out


def forecast(d, target, book, model, prior, names, lift=()):
    """xp_v2 as tested for `target` from one export d (its gameweek is
    target - 1): ({pid: xp_v2}, detail, the sources of the lambdas). `lift`:
    players whose status gate is set to True, nothing else changed
    (prereg/S8c.md amendment 4: "if he plays"; empty = the forecast)."""
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
    for pid in lift:
        gate[int(pid)] = True
    chance = XV.chance_scale(d)                         # S6's live rule on P(sub)
    out, detail = core(inp, names, by_round, target, rows, {}, tot, prior, fixtures_of, lam_team, lam_opp,
                       ict=ict_live(d), chance=chance, gate=gate)
    return out, detail, {fid: src for fid, (_, src) in lam.items()}


def load_prior(hist_root):
    folder = os.path.join(hist_root, PRIOR_SEASON)
    for name in ("merged_gw.csv", "teams.csv"):
        if not os.path.exists(os.path.join(folder, name)):
            raise MissingInput(f"{os.path.join(folder, name)} is missing (S11's priors, last season)")
    return SH.Prior(folder)


def _model(fixtures, dl):
    results = [(f["kickoff"], f["home"], f["away"], f["hg"], f["ag"]) for f in fixtures if f["finished"] and f["kickoff"] < dl]
    return OL.fit_fallback(results, dl)


def live(data_dir, hist_root, now=None, lift=()):
    """The deadline pass: the newest export (generated before the next
    deadline), the newest Odds API snapshot before it. Returns a dict with
    the forecast, its detail and the provenance of every input."""
    now = now or datetime.now(timezone.utc)
    name_to_short, deadlines, fixtures, settled, _ = OL.sqlite_tables(data_dir)
    upcoming = sorted((dl, ev) for ev, dl in deadlines.items() if dl > now)
    if not upcoming:
        raise MissingInput("no deadline after now in events")
    dl, target = upcoming[0]
    d, path = CH.newest_export(data_dir)
    gen = datetime.fromisoformat(d["generated"])
    if gen >= dl:
        raise MissingInput(f"{os.path.basename(path)} was generated at or after the GW{target} deadline")
    snap = OL.newest_snapshot(data_dir, dl)
    book = OL.snapshot_book(snap[1])[0] if snap else None
    prior = load_prior(hist_root)
    names, by_code = prior_names(os.path.join(data_dir, "fpl.sqlite"),
                                 os.path.join(hist_root, "2026-27", "elements_positions.csv"),
                                 os.path.join(hist_root, PRIOR_SEASON))
    xp, detail, srcs = forecast(d, target, book, _model(fixtures, dl), prior, names, lift=lift)
    return {"target": target, "deadline": dl, "export": os.path.basename(path), "generated": gen, "xp": xp, "detail": detail,
            "sources": srcs, "snapshot": (os.path.basename(snap[0]), snap[2]) if snap else None, "by_code": by_code,
            "d": d}


def retro(data_dir, g, hist_root, odds_file=None):
    """{pid: xp_v2 as tested} for a past gameweek g: g's newest export
    generated before its deadline, S5's 2026/27 football-data book, the
    fallback fitted on results before the deadline."""
    name_to_short, deadlines, fixtures, settled, _ = OL.sqlite_tables(data_dir)
    dl = deadlines.get(g)
    if dl is None:
        raise MissingInput(f"GW{g}: no deadline in events")
    best = OL.pre_deadline_export(OL.dated_exports(data_dir), dl, g)
    if best is None:
        raise MissingInput(f"GW{g}: no export generated before its deadline")
    path = odds_file or OL.odds_path("2026-27")
    if not os.path.exists(path):
        raise MissingInput(f"{path} is missing (S5's 2026/27 book)")
    book = OL.OddsBook(OL.load_odds(path, name_to_short))
    names, _ = prior_names(os.path.join(data_dir, "fpl.sqlite"), os.path.join(hist_root, "2026-27", "elements_positions.csv"),
                           os.path.join(hist_root, PRIOR_SEASON))
    xp, _, _ = forecast(best[2], g, book, _model(fixtures, dl), load_prior(hist_root), names)
    return xp


def retro_fn(hist_root, odds_file=None):
    """S6c's info_2627 hook: (data_dir, g) -> {pid: xp_v2 as tested}."""
    def fn(data_dir, g):
        try:
            return retro(data_dir, g, hist_root, odds_file)
        except (OL.MissingInput, SH.MissingInput, BT.MissingInput, CH.MissingInput) as e:
            raise MissingInput(str(e))
        except sqlite3.Error as e:                      # a data folder without the tables the print needs
            raise MissingInput(f"fpl.sqlite: {e}")
    fn.note = FD_NOTE
    return fn


# ---------------------------------------------------------------------------
# CLI: the forecast table for the next gameweek
# ---------------------------------------------------------------------------

def prior_label(how):
    """S11's prior labels name 2024/25 (its test season's prior); live, the
    prior season is 2025/26."""
    return (how or "").replace("2024/25", PRIOR_SEASON.replace("-", "/"))


def report(res, out=print, top=25):
    d = res["d"]
    by_id = {int(p["id"]): p for p in d["all_players"]}
    n_odds = sum(1 for s in res["sources"].values() if s == "odds")
    snap = res["snapshot"]
    out(f"XP_V2 AS TESTED  GW{res['target']} (deadline {res['deadline']:%Y-%m-%d %H:%M} UTC) from {res['export']} "
        f"(generated {res['generated']:%Y-%m-%d %H:%M} UTC); odds snapshot "
        + (f"{snap[0]} taken {snap[1]:%Y-%m-%d %H:%M} UTC" if snap else "none before the deadline (every fixture on the fallback)")
        + f"; {n_odds} of {len(res['sources'])} fixtures from odds; priors 2025/26 (S11), {res['by_code']} players keyed by code")
    out(f"  {'player':<18}{'team':>5}{'pos':>4}{'xp_v2':>7}{'P(start)':>9}{'E_xg':>6}{'E_bl':>6}{'P(sub)':>7}  prior")
    for pid, v in sorted(res["xp"].items(), key=lambda kv: -kv[1])[:top]:
        p, x = by_id.get(pid, {}), res["detail"][pid]
        out(f"  {p.get('web_name', pid):<18}{p.get('team', '?'):>5}{BT.POS_NAME.get(p.get('pos'), '?'):>4}{v:7.2f}{x['p_start']:9.2f}"
            f"{x['e_xg']:6.2f}{x['e_bl']:6.2f}{x['p_sub']:7.2f}  {prior_label(x['prior'])}")
    out(f"  {len(res['xp'])} players forecast (status a, 45+ minutes in the last four, a fixture)")


def main(argv=None):
    utf8_console()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(ROOT), "FPL-data"))
    ap.add_argument("--hist", default=os.path.join(ROOT, "historical"), help="the root holding 2025-26/ and 2026-27/")
    ap.add_argument("--out", default=os.path.join(ROOT, "tools", "out", "xp_v2_live"))
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    run = Run("tools/xp_v2_live.py", a.out, argv)
    lines = []

    def out(s=""):
        print(s); lines.append(s)
    try:
        res = live(a.data, a.hist)
        report(res, out)
    except (MissingInput, OL.MissingInput, SH.MissingInput, BT.MissingInput, CH.MissingInput) as e:
        print(f"missing input: {e} - own picks GW8 (ruling point 1); nothing is substituted")
        return 2
    path = os.path.join(a.out, f"xp_v2_live_gw{res['target']}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    run.wrote(path)
    print(f"written: {path}; provenance: {run.close()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
