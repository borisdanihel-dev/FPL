"""fpl_squad.py - the W3 report sections on our squad (prereg/W3.md, Part F
item F-B, parts 2 and 3):

    CAPTAIN   Step 14's captain table for our 15 under xp_v2 as tested
              (mean, P(>=10), P(>=15), p90) and the options within 0.3 xP
              of xp_v2's captain in its XI (S14 amendment 1); information
              only: the captain rule is unchanged and there is no tie-break
    BAN RISK  our players one booking from a ban, by S12's rule: cautions,
              the per-90 booking rate and P(ban for the following gameweek)
    REALISED  from GW8, each gameweek under the lockdown guard: our squad's
              realised official points under own's XI and captain and under
              xp_v2's, from the recorded pre-deadline rows

fpl_sections.py runs them after CHIPS and LEAGUE: a missing input, or any
exception, is one `<SECTION> SKIPPED: <why>` line and check 31's WARN. They
read the newest export, fpl.sqlite read-only, the odds snapshots, the
committed S11 prior and the projection log through fpl_edge.forecasts. The
models are the runner's verbatim copies (fpl_xpv2, fpl_pmf, fpl_mv2,
fpl_xpr). Standard library only; nothing under tools/.
"""
import os
import re
import sqlite3
import subprocess
from collections import defaultdict
from datetime import datetime, timezone

import fpl_bt as BT
import fpl_chips as CH
import fpl_edge as E
import fpl_mv2 as MV
import fpl_pmf as PM
import fpl_realised as RL
import fpl_xpv2 as XL

ENTRY = 3073318                     # 1. FC Kiripolcz
FIRST_GW = 8                        # F-B (3): after each locked-down gameweek from GW8
SOURCES = ("own", "xp_v2")
BUNDLE_GWS = (8,)                   # amendment 1 (C): GW8's xp_v2 from the bundle (the night ruling, point 2)
REPO = os.path.dirname(os.path.abspath(__file__))


class MissingInput(Exception):
    """A required input is missing: reported, never substituted."""


def next_target(d):
    """(the export's next gameweek, its deadline)."""
    target = d["gameweek"] + 1
    dl = E.event_deadline(d, target)
    if dl is None:
        raise MissingInput(f"no deadline or fixtures for GW{target} in the export")
    return target, dl


# ---------------------------------------------------------------------------
# CAPTAIN (part 2): Step 14 passed and was accepted as information
# ---------------------------------------------------------------------------

def xp_v2_captain(squad, xp):
    """(xp_v2's XI, its captain): chips.xi_and_bench under xp_v2, the captain
    the highest xp_v2 in the XI, ties to the lower id (tools/gw_pass.py's
    side_by_side)."""
    xi, _, _ = CH.xi_and_bench([dict(r) for r in squad], xp)
    return xi, max(xi, key=lambda r: (r["proj"], -r["id"]))


def captain(data_dir, out, prior_path=None):
    """The captain table for our 15 and the options within 0.3 xP of xp_v2's
    captain (the highest xp_v2 in xp_v2's XI, ties to the lower id), as
    tools/gw_pass.py's section 7."""
    d, path = CH.newest_export(data_dir)
    target, dl = next_target(d)
    res = XL.live_forecast(d, target, dl, data_dir, XL.load_prior_file(prior_path or XL.PRIOR_FILE))
    sums = PM.live_pmfs(res)
    squad = CH.my_squad(d)
    xi, cap = xp_v2_captain(squad, res["xp"])
    snap = res["snapshot"]
    out(f"  GW{target} from {os.path.basename(path)}: the points distribution of xp_v2 as tested (Step 14, option (a): "
        f"its mean is xp_v2; no saves term); odds " + (f"{snap[0]}" if snap else "none before the deadline (every fixture "
        "on the fallback)") + "; information: the captain rule is unchanged (the highest xp_v2 in the XI) and there is no tie-break")
    PM.captain_table(squad, sums, out)
    options = PM.captain_options([r["id"] for r in xi], cap["id"], {pid: s["xp"] for pid, s in sums.items()})
    PM.print_options(cap["id"], options, sums, {r["id"]: r["name"] for r in squad}, out)
    return {"target": target, "captain": cap["id"], "options": options, "sums": sums}


# ---------------------------------------------------------------------------
# BAN RISK (part 2): S12's rule
# ---------------------------------------------------------------------------

def position_rates(rows, cut):
    """The position mean of the booking rate (prereg/W3.md pins what S12 left
    open): the position's cautions / (minutes / 90), pooled over every player
    of the position in league matches before the cut."""
    keys = MV.rows_key_before(rows, cut)
    mins, ys = defaultdict(float), defaultdict(float)
    for (pid, key), (m, _, y) in rows.played.items():
        if key in keys:
            pos = rows.pos.get(pid)
            mins[pos] += m
            ys[pos] += y
    return {pos: ys[pos] / (mins[pos] / 90.0) for pos in mins if mins[pos] > 0}


def one_from_ban(rows, pid, club, cut):
    """(cautions, the club's next league match number, the band) when one
    more booking in that match bans: S12's suspended_next band moved one
    match on (4 with the next match the 18th or earlier, 9 with it the 31st
    or earlier); None otherwise."""
    total = MV.cautions_before(rows, pid, cut)
    n_next = len(rows.club_matches_before(club, cut)) + 1
    for count, before in MV.CAUTION_BANDS:
        if total == count - 1 and n_next + 1 <= before:
            return total, n_next, (count, before)
    return None


def ban_rows(data_dir, d):
    """S12's Rows for the ban count (amendment 1, (B)): a fixture is a known
    result when FPL marks it finished or finished_provisional (in progress:
    neither, not counted); with {club: [(kickoff, 'HOME-AWAY')]} of the
    counted fixtures that are provisional only. With no provisional fixture
    the rows are fpl_mv2.rows_2627's."""
    db = os.path.join(data_dir, "fpl.sqlite")
    if not os.path.exists(db):
        raise MissingInput(f"{db} is missing")
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        cols = {r[1] for r in c.execute("PRAGMA table_info(fixtures)")}
        fpv = "finished_provisional" if "finished_provisional" in cols else "NULL"
        short = {i: s for i, s in c.execute("select id, short_name from teams")}
        matches, fx_event, prov = defaultdict(list), {}, defaultdict(list)
        for fid, ev, ko, h, a, fin, pv in c.execute(f"select id, event, kickoff_time, team_h, team_a, finished, {fpv} "
                                                    f"from fixtures where event is not null"):
            kot = datetime.fromisoformat(ko.replace("Z", "+00:00"))
            matches[short[h]].append((kot, str(fid), ev)); matches[short[a]].append((kot, str(fid), ev))
            done = bool(fin) or pv == 1
            fx_event[str(fid)] = (ev, short[h], short[a], done)
            if pv == 1 and not fin:
                for club in (short[h], short[a]):
                    prov[club].append((kot, f"{short[h]}-{short[a]}"))
        played = {}
        team_of = {pid: short[t] for pid, t in c.execute("select id, team_id from players")}
        pos = {pid: p for pid, p in c.execute("select id, position from players")}
        for pid, ev, mins, starts, yellow in c.execute("select player_id, event, minutes, starts, yellow from player_gw"):
            club = team_of.get(pid)
            for fid, (e, h, a, done) in fx_event.items():
                if e == ev and done and club in (h, a):
                    played[(pid, fid)] = (mins or 0, 1 if starts else 0, yellow or 0)
        names = {p["id"]: p["web_name"] for p in d["all_players"]}
        known = {fid for fid, (e, h, a, done) in fx_event.items() if done}
        return MV.Rows(matches, played, team_of, pos, names, known), dict(prov)
    finally:
        c.close()


def provisional_note(prov, club, cut):
    """'   provisional: HOME-AWAY not yet marked finished by FPL' for the club's
    counted provisional-only fixtures before the cut, else ''."""
    fx = [hk for ko, hk in sorted(prov.get(club, [])) if ko < cut]
    return f"   provisional: {', '.join(fx)} not yet marked finished by FPL" if fx else ""


def ban_risk(data_dir, out):
    """Our 15 one booking from a ban: cautions, rate90 (S12's booking_rate90
    against the position mean), P(start) as xp_v2 as tested uses it, and
    P(ban for the following gameweek) = min(1, rate90 x P(start))."""
    d, _ = CH.newest_export(data_dir)
    target, dl = next_target(d)
    rows, prov = ban_rows(data_dir, d)
    inp = E.reliability_inputs(E.canonical_through(E.canonical_from_export(d), d["gameweek"]), gws_played=d["gameweek"])
    rates = position_rates(rows, dl)
    out(f"  GW{target} (S12's rule): cautions = yellow cards in league matches before the deadline; one booking from a ban = 4 "
        f"with the club's next league match its 18th or earlier, or 9 with it its 31st or earlier; rate90 = cautions per 90 "
        f"shrunk m/(m+{MV.CRED_K:g}) to the position's pooled rate; P(ban for the following gameweek) = min(1, rate90 x P(start)), "
        f"P(start) as xp_v2 as tested; a result FPL has ended but not yet marked finished counts, labelled provisional")
    hits = 0
    for r in CH.my_squad(d):
        pid = r["id"]
        club = rows.club_of.get(pid)
        if club is None:
            raise MissingInput(f"{r['name']} has no club in fpl.sqlite players")
        band = one_from_ban(rows, pid, club, dl)
        if band is None:
            continue
        hits += 1
        total, n_next, _ = band
        pos = rows.pos.get(pid)
        if pos not in rates:
            raise MissingInput(f"no minutes for position {pos} before the deadline (the position mean)")
        rate = MV.booking_rate90(rows, pid, dl, rates[pos])
        p = inp["players"].get(pid)
        if p is None:
            out(f"  {r['name']:<16}{r['team']:>5}{BT.POS_NAME.get(r['pos'], '?'):>4}  cautions {total}, club match {n_next} next  "
                f"rate90 {rate:.3f}  P(start) n/a (no rows in the export)  P(ban) n/a" + provisional_note(prov, club, dl))
            continue
        out(f"  {r['name']:<16}{r['team']:>5}{BT.POS_NAME.get(r['pos'], '?'):>4}  cautions {total}, club match {n_next} next  "
            f"rate90 {rate:.3f}  P(start) {p['p_start']:.2f}  P(ban) {MV.p_ban_next(rate, p['p_start']):.3f}" + provisional_note(prov, club, dl))
    if not hits:
        out("  none of our 15 is one booking from a ban")
    return hits


# ---------------------------------------------------------------------------
# REALISED (part 3): own v xp_v2 on our squad, from the recorded rows
# ---------------------------------------------------------------------------

def recorded(log_rows, source, event, d_ev):
    """{pid: predicted} of `source` for `event` as every reader takes it,
    fpl_edge.forecasts (the gameweek's last snapshot made before its
    deadline), and that snapshot's made_at: S6c's recorded_own, any source."""
    rows = [r for r in E.forecasts(log_rows, d_ev) if r["source"] == source and int(r["event"]) == event]
    if not rows:
        return {}, None
    return {int(r["player_id"]): float(r["predicted"]) for r in rows}, rows[0]["made_at"]


ROW = re.compile(r"^\s+(\d+)( \* |   )(.+?)\s+(GK|DEF|MID|FWD)\s+(-?\d+\.\d\d)\s+(.+?)\s+(GK|DEF|MID|FWD)\s+(-?\d+\.\d\d)$")
CAP = re.compile(r"\|  xp_v2 as tested (.+) \((-?\d+\.\d\d)\)")
POS = {"GK": 1, "DEF": 2, "MID": 3, "FWD": 4}


def parse_bundle(text):
    """xp_v2's 15 from the bundle's section "OWN v XP_V2 AS TESTED" (the
    right-hand column, slots 1-15: the XI, the bench keeper, the bench) and
    its captain: ([(slot, name, pos)], captain name); None when absent."""
    lines = text.splitlines()
    try:
        i = next(k for k, l in enumerate(lines) if l.startswith("OWN v XP_V2 AS TESTED"))
    except StopIteration:
        return None
    rows, cap = [], None
    for l in lines[i + 1:]:
        if l.startswith("=" * 20) and rows:
            break
        m = ROW.match(l)
        if m:
            rows.append((int(m.group(1)), m.group(6), POS[m.group(7)]))
        c = CAP.search(l) if l.startswith("  captain: ") else None
        if c:
            cap = c.group(1)
    if [s for s, _, _ in rows] != list(range(1, 16)) or cap is None:
        return None
    return rows, cap


def git(repo, *args):
    """stdout of `git -C repo args` as text, None on any failure (no git, no history)."""
    try:
        r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


def bundle_commit(repo, g, deadline):
    """The newest commit touching worklog/gw_pass/gw<g>/gw<g>_pass.txt whose
    committer time is before the deadline, with the file and run.txt at it:
    (commit, text, run_txt or None); None when there is none."""
    path = f"worklog/gw_pass/gw{g}/gw{g}_pass.txt"
    log = git(repo, "log", "--format=%H %cI", "--", path)
    if not log:
        return None
    for line in log.splitlines():
        h, t = line.split()
        if datetime.fromisoformat(t.replace("Z", "+00:00")) < deadline:
            text = git(repo, "show", f"{h}:{path}")
            if text is None:
                return None
            return h, text, git(repo, "show", f"{h}:worklog/gw_pass/gw{g}/run.txt")
    return None


def realised_order(xi, bench, cap_id, actual):
    """realised_on's arithmetic on a given XI, bench order (the keeper first)
    and captain: rule_autosubs on the minutes, the captain doubled."""
    lineup = [{"slot": s, "pos": r["pos"], "id": r["id"], "minutes": actual.get(r["id"], (0, 0))[1]}
              for s, r in enumerate(xi, 1)]
    lineup += [{"slot": s, "pos": r["pos"], "id": r["id"], "minutes": actual.get(r["id"], (0, 0))[1]}
               for s, r in enumerate(bench, 12)]
    pts = sum(actual.get(r["id"], (0.0, 0))[0] for r in xi)
    for cand, gone in E.rule_autosubs(lineup):
        pts += actual.get(cand["id"], (0.0, 0))[0] - actual.get(gone["id"], (0.0, 0))[0]
    return pts + actual.get(cap_id, (0.0, 0))[0]


def bundle_xp_v2(repo, g, deadline, squad, web, actual):
    """GW g's xp_v2 from the bundle (amendment 1, (C)): (points, captain id,
    label) when graded; (None, None, the reason) when the bundle's 15 is not
    ours; None when no commit before the deadline holds the bundle."""
    found = bundle_commit(repo, g, deadline)
    if found is None:
        return None
    h, text, run_txt = found
    m = re.search(r"^commit: ([0-9a-f]{7,40})", run_txt or "", re.M)
    tag = f"GW{g} bundle {h[:7]} (tools {m.group(1)[:7] if m else 'no run.txt at that commit'})"
    parsed = parse_bundle(text)
    if parsed is None:
        return None, None, f"xp_v2 ({tag}): no 15 and captain in its section 5: not graded"
    rows, cap_name = parsed
    by_name = defaultdict(list)
    for r in squad:
        by_name[web.get(r["id"])].append(r)
    ids, bad = [], []
    for slot, name, pos in rows:
        hit = [r for r in by_name.get(name, []) if r["pos"] == pos]
        if len(hit) == 1:
            ids.append(hit[0])
        else:
            bad.append(name)
    ours = {web.get(r["id"]) for r in squad}
    if bad or {r["id"] for r in ids} != {r["id"] for r in squad}:
        only_b = sorted({n for _, n, _ in rows} - ours)
        only_p = sorted(ours - {n for _, n, _ in rows})
        return None, None, (f"xp_v2 ({tag}): the bundle's 15 is not our GW{g} 15 (only in the bundle: {', '.join(only_b) or '-'}; "
                            f"only in our picks: {', '.join(only_p) or '-'}): not graded")
    cap = [r for r in ids[:11] if web.get(r["id"]) == cap_name]
    if len(cap) != 1:
        return None, None, f"xp_v2 ({tag}): its captain {cap_name} is not one of its XI: not graded"
    return realised_order(ids[:11], ids[11:], cap[0]["id"], actual), cap[0]["id"], f"source: {tag}"


def realised(data_dir, out, now=None, entry=ENTRY, first=FIRST_GW, repo=None):
    """Per gameweek from `first` whose deadline has passed: under the lockdown
    guard, our 15 at that gameweek, each source's XI and captain from its
    recorded rows, realised official points with rule_autosubs and the
    captain doubled (S6c's realised_on); the running totals."""
    now = now or datetime.now(timezone.utc)
    repo = repo or REPO
    db_path, log_path = os.path.join(data_dir, "fpl.sqlite"), os.path.join(data_dir, E.LOG_PATH)
    for p in (db_path, log_path):
        if not os.path.exists(p):
            raise MissingInput(f"{p} is missing")
    log_rows = E.read_log(log_path)
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        events = list(db.execute("SELECT id, deadline_time, finished, data_checked FROM events ORDER BY id"))
        d_ev = {"events": [{"event": ev, "deadline_time": dl} for ev, dl, _, _ in events]}
        try:
            web = dict(db.execute("SELECT id, web_name FROM players"))      # names in the print; ids where the table has none
        except sqlite3.Error:
            web = {}
        deadline = {ev: datetime.fromisoformat(dl.replace("Z", "+00:00")) for ev, dl, _, _ in events if dl}
        past = [(ev, chk) for ev, dl, _, chk in events
                if ev >= first and dl and datetime.fromisoformat(dl.replace("Z", "+00:00")) <= now]
        out(f"  from GW{first}: our squad (entry {entry}) under each source's XI and captain from its recorded pre-deadline "
            f"rows; realised official points, rule_autosubs, the captain doubled; graded only when locked down")
        if not past:
            out(f"  no gameweek from GW{first} has passed its deadline yet")
            return []
        recs, tot = [], {s: 0.0 for s in SOURCES}
        n_both = 0
        for g, chk in past:
            n_fx, n_fin = db.execute("SELECT COUNT(*), COALESCE(SUM(finished = 1), 0) FROM fixtures WHERE event = ?",
                                     (g,)).fetchone()
            if not (chk == 1 and n_fx and n_fin == n_fx):
                out(f"  GW{g}: not locked down: not graded (data_checked {chk}, {n_fin} of {n_fx} fixtures finished)")
                recs.append({"gw": g, "graded": False})
                continue
            picks = db.execute("SELECT p.player_id, pl.position FROM picks p JOIN players pl ON pl.id = p.player_id "
                               "WHERE p.entry_id = ? AND p.event = ? ORDER BY p.position", (entry, g)).fetchall()
            if len(picks) != 15:
                out(f"  GW{g}: {len(picks)} picks for entry {entry}, not 15: not graded")
                recs.append({"gw": g, "graded": False})
                continue
            squad = [{"id": pid, "pos": pos} for pid, pos in picks]
            actual = {pid: (float(pts or 0), float(mins or 0)) for pid, pts, mins in db.execute(
                "SELECT player_id, total_points, minutes FROM player_gw WHERE event = ?", (g,))}
            rec, parts = {"gw": g, "graded": True}, []
            for src in SOURCES:
                proj, made = recorded(log_rows, src, g, d_ev)
                if not proj and src == "xp_v2" and g in BUNDLE_GWS:      # amendment 1 (C): the bundle's pre-deadline commit
                    b = bundle_xp_v2(repo, g, deadline[g], squad, web, actual)
                    if b is not None and b[0] is not None:
                        rec[src], rec[src + "_cap"] = b[0], b[1]
                        parts.append(f"{src} {rec[src]:.0f} (captain {web.get(b[1], b[1])}; {b[2]})")
                        continue
                    if b is not None:
                        parts.append(b[2])
                        continue
                if not proj:
                    parts.append(f"{src}: not recorded before the deadline")
                    continue
                rec[src], rec[src + "_cap"] = RL.realised_on(squad, proj, actual)
                parts.append(f"{src} {rec[src]:.0f} (captain {web.get(rec[src + '_cap'], rec[src + '_cap'])}; snapshot {made[:10]})")
            line = f"  GW{g}: " + "; ".join(parts)
            if all(s in rec for s in SOURCES):
                n_both += 1
                for s in SOURCES:
                    tot[s] += rec[s]
                line += f"; xp_v2 - own {rec['xp_v2'] - rec['own']:+.0f}"
            out(line)
            recs.append(rec)
        if n_both:
            out(f"  total over {n_both} gameweek{'s' if n_both > 1 else ''} with both: own {tot['own']:.0f}, xp_v2 {tot['xp_v2']:.0f}, "
                f"xp_v2 - own {tot['xp_v2'] - tot['own']:+.0f}")
        return recs
    finally:
        db.close()
