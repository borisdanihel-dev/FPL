# verify_S14_amend1 — S14 amendment 1: the options within 0.3 xP of xp_v2's captain (section 7)

Verifier: backtest-verifier, run on Fable 5.1 (claude-fable-5-1), effort high; instructions read
from `.claude/agents/backtest-verifier.md` in the worktree first (identical to the loaded
instructions). Date 2026-10-19. Worktree `…\scratchpad\landing`, branch `landing-2026-10-19b`,
HEAD `282f7e4`, tree clean at the start and at the end (the only file I wrote in it is this one).
Everything that writes ran in my own scratch copies under `…\scratchpad\verify_s14a\`
(`before` = `git archive 6e26f70`, the delta's parent; `after` = `git archive 282f7e4`; `mut` = a
third copy of 282f7e4 for the mutations; `data_before` / `data_after` = copies of the three data
files). `C:\GIT\FPL-data` (`bd724ca`, 0 modified files, read only, `git status` clean afterwards);
no git pull, fetch, commit, push or checkout anywhere; `C:\GIT\FPL-b` untouched. The delta is a
descriptive display item (no new forecast or metric), so checks 1, 2, 5, 6, 7 and the amendment's
own acceptance tests apply; S14 itself was verified at `0def550` (`worklog/verify_S14.md`).

## Prereg ordering — PASS

`git log -- prereg/S14.md`: `677f34e` (17:26:34 +0200, "RULING S14 (Boris accepts) + Part F"
verbatim, points 1-3) and `3de32ff` (17:26:55, "Amendment 1", the display pinned). The delta's only
code commit `282f7e4` is at 17:30:36 and touches exactly `tests/test_S14.py` (+46), `tools/gw_pass.py`
(+17/−1), `tools/points_pmf.py` (+27). `git diff --stat 0def550 6e26f70` lists only BUILD_PLAN,
CHANGELOG, prereg/S14.md, prereg/W1b.md and worklog files: no code moved between S14's verified
commit and the delta's parent. The ruling text is in `prereg/S14.md` verbatim; the amendment pins
where (section 7 after the table), the captain (section 5's: highest xp_v2 in the XI, ties to the
lower id), the options (every other XI player with xp_v2 ≥ captain − 0.3, inclusive), what prints
(xp_v2, mean, P≥10, P≥15, p90; the rule unchanged; no tie-break; information), the no-option line,
the missing-input case and the acceptance tests. The prereg was not edited after the code.

## Check 1: point-in-time — PASS (no number moved)

The delta produces no new forecast, feature or metric: `points_pmf.py`'s diff is purely additive
(`CAPTAIN_BAND`, `captain_options`, `print_options` after `live_pmfs`; nothing above line 492
changed), `gw_pass.py` stores section 5's side-by-side and appends lines to section 7. Shown on the
live data: `python tools/gw_pass.py --data C:\GIT\FPL-data --hist <worktree>/historical` from the
`before` and the `after` copies — `diff` of the two bundles is exactly the three appended lines
(233a234,236: the "within 0.3 xP" header, `captain Saka`, `option Calafiori`); every other line,
S5's λ, the chips, the planner, the league, section 5's XI/bench/captain, the keeper line and all
15 rows of the captain table, is identical. The `after` bundle equals the worktree's committed run
(`tools/out/gw_pass/gw8_pass.txt`, run.txt commit `282f7e4`, 0 modified files, sha256 8901a76e…)
in every line but line 1's generation timestamp (sha256 of lines 2+ cd4a54c2… for both). No
"missing input" or failed section. Inputs are those S14's check 1b audited: export
`fpl_export_gw7_2026-10-19.json.gz` and odds `odds_2026-10-19T0613Z.json.gz`, both before the GW8
deadline 2026-10-23 17:30 UTC. Truncation test and shift probe: not applicable (nothing is
rebuilt or correlated); the inputs of the band are section 5's own numbers.

## Amendment acceptance tests and the claims — PASS

My script `verify_s14a/check_options.py` (log `check_options.log`) recomputes the rule from the raw
pieces, not through `captain_band`: `CH.xi_and_bench` on `XL.live`'s xp_v2 gives the XI, the captain
= max by (xp_v2, −id), the options = the XI others with xp_v2 ≥ captain − 0.3 − 1e-12, sorted by
(−xp_v2, id). Live GW8: XI Saka 6.00146, Calafiori 5.82687, Haaland 5.68387, Mbeumo 5.66718,
Muharemović 4.94468, Thiago 4.75761, Groß 4.43149, Barry 4.17080, Rudoni 3.69790, Tarkowski 3.69254,
Kelleher 3.51377; bench Verbruggen, Thomas, Branthwaite, Slater. Captain Saka (mine = `captain_band`
= section 5's xp_v2 captain; own's captain is Haaland, not taken). Options: Calafiori alone (gap
0.17459); Haaland is out by 0.01759 (gap 0.31759) and Mbeumo by 0.03428 — the band is on the exact
xp_v2, not the two-decimal display (6.00 − 5.68 = 0.32 either way). The captain is not his own
option; the options are a subset of xp_v2's XI; own's XI differs (own starts Verbruggen,
Branthwaite, Thomas, none inside the band, so the live case cannot distinguish the two columns —
the hand test in `CaptainOptions` does, see below). `sums[pid]["xp"]` equals the live xp_v2 exactly
(max |diff| 0.0 over our 15). The printed lines' mean, P≥10, P≥15 and p90 equal the table's
formatted values for Saka (6.00 / 0.186 / 0.052 / 12) and Calafiori (5.83 / 0.134 / 0.032 / 12),
and the xp_v2 column equals `f"{xp:.2f}"`. The worktree's committed `gw8_pass.txt` carries the same
section 5 captain line (`|  xp_v2 as tested Saka (`) and the same section 7 lines.

The tests the amendment lists all exist in `tests/test_S14.py` and pass: `CaptainOptions
.test_the_band_edges_and_the_lines` (xp {1: 6.00, 2: 5.70, 3: 5.69, 4: 6.00, 5: 3.0}: 5.70 in,
5.69 out, the tied 4 listed, the captain never listed, a player outside the XI (id 9 at 9.9) never
listed; the empty band; the line order captain/option/option and the table's numbers; the
"no option within 0.3 xP" line; a 15-man hand case where own would start and captain other
players — `side_by_side` + `captain_band` take xp_v2's captain (8) and only xp_v2's XI, with own's
starters 10 and 11 inside the band and benched by xp_v2 excluded); `LiveAndBundle` asserts section
7's one `captain` line names section 5's xp_v2 captain and every `option` has xp_v2 ≥ captain − 0.3;
the no-forecast path still prints only the missing-input line. `CAPTAIN_BAND == 0.3` is asserted.

Note on wording: the ruling says the table "is shown beside any two options within 0.3 xP"; the
amendment pins "every other player of that XI whose xp_v2 is at least the captain's minus 0.3",
and the code lists every such player (not at most two). The amendment was committed before the
code, so it is the pinned reading; I flag the difference for the chat only. Live it makes no
difference (one option).

## Check 2: clean-checkout test run — PASS

`python -m unittest discover -p "test*.py" -s . -t .` (no `FPL_DATA_DIR`) in the scratch copies:
- before (`6e26f70`, the delta's parent): **686 tests OK (skipped=10)**, 414 s;
- after (`282f7e4`): **687 tests OK (skipped=10)**, 413 s.
Delta +1 = `CaptainOptions.test_the_band_edges_and_the_lines`; the section-7 assertions ride in the
existing `LiveAndBundle` test. Matches the claimed 686 → 687.

## Check 5: recording path — PASS

`diff -rq before after`: only `tests/test_S14.py`, `tools/gw_pass.py`, `tools/points_pmf.py`; no
runner file changed. Demonstrated anyway: scratch copies of `fpl_export_gw7.json`, `fpl.sqlite` and
`projection_log.csv` (sha256 3e387855…, 7,502 lines); `fpl_edge.py --record --source` own, xg,
minutes, bottomup, fpl_ep under the `before` code and under the `after` code: both record 275 /
260 / 260 / 260 GW8 forecasts (fpl_ep skipped: no ep_next), both logs 7,479 data rows and identical
in every column but `made_at`. The real `projection_log.csv` and `C:\GIT\FPL-data` were not touched.
`xp_v2_live` is not in the delta; the before/after bundles' section 5 and the captain table being
identical shows the live xp_v2 and the PMFs did not move.

## Check 6: mutation spot-check — PASS (8 of 8 red)

In the `mut` copy, one line at a time, `python -m unittest tests.test_S14` (11 tests, ~7 s), the
original restored and shown green and byte-identical afterwards (`verify_s14a/mutate.py`,
`mutations.log`):
1. band edge `>=  top − band − 1e-12` → `> top − band + 1e-12` (0.30 excluded): FAILED (1);
2. the captain listed as his own option (`pid != cap_id` removed): FAILED (1);
3. `CAPTAIN_BAND` 0.3 → 0.4: FAILED (1);
4. `captain_band` takes own's captain (`sbs["captain"][0]`): FAILED (2: CaptainOptions and the bundle);
5. `captain_band` takes own's XI column (`a` instead of `b`): FAILED (1);
6. options sorted ascending (`-xp` → `xp`): FAILED (1);
7. section 7 never prints the options (`if sbs is not None` → `if False`): FAILED (1, the bundle);
8. the no-option line reworded: FAILED (1).

## Check 7: secrets — PASS

The three files of `282f7e4` and the added lines of its diff contain no API key, no URL with
`apiKey=`, no Authorization header, no `http`, token, secret or `ODDS_API` string. Nothing I ran
wrote to the worktree (other than this file), to `C:\GIT\FPL` or to `C:\GIT\FPL-data`.

## Notes (not verdict items)

- The ruling's "any two options" versus the amendment's "every other player … within 0.3": see the
  wording note above; the pinned amendment governs and the code follows it.
- The band compares exact xp_v2 values; a player can print as 0.30 below the captain at two
  decimals and still be outside (not the case live: Haaland prints 5.68 against 6.00).
- No CHANGELOG entry for the amendment exists at `282f7e4`; per the protocol it follows this
  verdict.
- Both suite runs skip 10 (S14's report said 9): the extra skip is the same under both codes, so
  not the delta's.

VERDICT: PASS

Reason: the ruling and the amendment that pins the display were committed (`677f34e`, `3de32ff`)
before the delta's only code commit `282f7e4`, which touches just the two tools files and the test;
the code is purely additive and on the live data the before/after bundles differ only by the three
appended section-7 lines, every S14 and S6d number unchanged, and the after bundle equals the
worktree's committed run but for the timestamp; my own recomputation from the raw pieces gives
captain Saka (section 5's xp_v2 captain, not own's Haaland) and the single option Calafiori (gap
0.175; Haaland 0.318 and Mbeumo 0.334 outside), with the printed numbers equal to the table's; the
amendment's acceptance tests exist and pass, the suite goes 686 → 687 OK, the recording path is
identical under both codes in every column but `made_at`, eight of eight mutations go red, and no
secrets are present.
