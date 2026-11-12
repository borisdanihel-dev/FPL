"""fpl_xpv.py - the runner's copy of tools/xp_v2.py, the part W3 needs:
S6's blend and live P(sub) rule (W3; prereg/W3.md, Part F item F-B).

Every definition below is copied verbatim from tools/xp_v2.py by its syntax
tree, module aliases kept and pointed at the runner's copies, so the
runner never imports tools/; tests/test_W3.py holds the copies to the
tools. Standard library only.
"""
import fpl_edge as E


WINDOW = 4


def chance_scale(d):
    """player id -> chance_next_round / 100 from the export (None = 100)."""
    return {p["id"]: E.chance_of_playing(p) / 100.0 for p in d.get("all_players", [])}


def xp_candidates(p_start, e_xg, e_bl, p_sub, e_sub):
    """{candidate: xP} for one player from the conditional forecasts."""
    sub_term = p_sub * e_sub
    out = {"blend": p_start * (e_xg + e_bl) / 2 + sub_term,
           "xg_only": p_start * e_xg + sub_term,
           "bl_only": p_start * e_bl + sub_term}
    return out
