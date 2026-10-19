# Bundle — the Thursday deadline pass (GW8), information only

The chat's ruling of the morning of 2026-10-19, item 6, pasted verbatim
below with the whole ruling. The template rows are filled in when the
bundle tool starts, before any of its code. Offline under `tools/`
(`tools/gw_pass.py` → `tools/out/gw8_pass.txt`); information only, no
bar, no adoption; it composes the live outputs of S5, S7, S8, S9, S6 and
S12 from the newest snapshot in `C:\GIT\FPL-data`.

Template rows, filled on 2026-10-19 before any bundle code (the rulings
below govern where they differ):

- **Item:** bundle (RULING morning 19 Oct item 6; RULING S8 verifier FAIL
  item (d); RULING morning 19 Oct item 3 for the keeper line). Offline,
  information only.
- **Hypothesis:** none. The bundle composes existing live outputs into one
  file for the Thursday deadline pass; it forecasts nothing of its own.
- **Data:** the newest export and the odds snapshots in `C:\GIT\FPL-data`
  (read-only), the projection log's recorded rows (`own`, `minutes`); run
  first on Thursday from Wednesday night's snapshot, refreshed after
  Thursday's nightly. Its output is `tools/out/gw_pass/gw8_pass.txt` with
  `run.txt`.
- **Definitions pinned (the sections, in order):**
  1. S5 `--live` (`odds_lambda.live`): the fixtures' λ and odds-implied
     clean-sheet probabilities, and our GK/DEF lines.
  2. S7 chip table (`chips.live`): the Bench Boost / Free Hit values per
     gameweek and the next-gameweek call.
  3. S8 (`planner.live`): the top 5 plans on Boris's schedule and the two
     exploratory lines (no hits; buffer 3.0), beside the baseline's choice
     (the best one-week move with a free transfer when its gain > 0, else
     roll, never a hit: `planner.baseline_plan` on the same squad, bank,
     pool and xP). Where the planner's top plan differs from the baseline,
     the baseline is the default and the planner is the note (ruling (d)).
  4. S9 (`league.report`): the league report with its captain and
     effective-ownership tables.
  5. own v xp_v2: our XI, bench order and captain chosen by `own` (the
     recorded row for the next gameweek) and by `xp_v2` (`xp_v2.forecast`,
     not recorded), side by side via `chips.xi_and_bench` (captain = the
     highest projection in the XI, ties by the lower id).
  6. The keeper line (ruling item 3): for our keepers, own's P(start) (the
     recorded `minutes` row) beside S12's keeper lock (`minutes_v2.live`,
     not adopted, information).
  A section whose input is missing prints "missing input: ..." and the
  bundle continues; nothing is substituted.
- **Comparison / metrics / bootstrap / pass threshold:** none; information
  only, no bar, no adoption.
- **Acceptance tests:** each section's header present on a toy; the
  side-by-side XI on a hand case (two projections, two XIs, two captains);
  the keeper line on a hand case; a missing section reported, not
  substituted; `run.txt` written; CLI `python tools/gw_pass.py`; nightly
  isolation; tests in `tests/test_bundle.py`; `test_fpl.py` untouched.

## Ruling morning 19 Oct (verbatim)

RULING morning 19 Oct (lane B); chat review of S9, S8, S12, S13, so the item count restarts at 0:
1. Landing today, after Boris tells you W1's real dispatch is green: the landing branch as your state file describes (revert of 32bf218, S4, S7, S5, S6, S9, the Part C line, plus a header-only overrides.csv), full suite, push, ask Boris for the dry-run click.
2. S8: kept as a screen, information only. Add exploratory lines on the same replay (no bar, no adoption): the planner with no hits, and with the hit buffer at 3.0 instead of 1.5.
3. S12: not adopted. The keeper lock is printed beside own's P(start) in the deadline pass's keeper line, as information.
4. S13: shelved; the hit-rate rule stays; revisit at the GW19 checkpoint.
5. S11 download approved: vaastav data/2024-25 merged_gw.csv, fixtures.csv, teams.csv into historical/2024-25/ (gitignored); record URL, fetch time, SHA-256. Then run S11 as ruled.
6. Thursday bundle, information only: tools/out/gw8_pass.txt with S5 --live (odds clean sheets), the S7 chip table, the S8 top 5 (with no-hit and buffer-3.0 lines), the S9 captain and EO table, own v xp_v2 XI, bench and captain side by side, and the keeper-lock line. A first version Thursday from Wednesday night's snapshot, refreshed after Thursday's nightly.
After S11 and the bundle, stop; Steps 14, 15 and 19 get rulings later.
END RULING

## RULING S8 verifier FAIL (verbatim; this item: item (d): the planner's top plan beside the baseline's choice and the no-hit line; the baseline is the default, the planner the note)

RULING S8 verifier FAIL:
(a) The verifier's final-code replay is the S8 result: rerun it yourself on the final code as s8_run3, record it in a new CHANGELOG entry beside the first run's (both kept, the first marked as the buggy generator's), and re-verify. The bar fails either way; nothing is adopted.
(b) Lost-FT charge: the code's reading stands. Using an FT when k are banked forgoes the (k+1)-th banked FT, so the charge is the schedule's (k+1)-th value. Record it as the prereg's reading; no number changes.
(c) Close the five test gaps before the re-verify.
(d) Disposition: the planner stays a screen. In the Thursday bundle, its top plan prints beside the baseline's choice (best one-week move or roll, never a hit) and the no-hit planner line; where they differ, the baseline is the default and the planner is the note.
(e) Provenance, from now on, both lanes: every output folder holds a run.txt with the commit hash it ran on and its start and end times (UTC), written by the tool itself. A report may cite a run only when that commit equals the item's final code. Before the landing, check every recorded number in S4, S5, S6, S7, S9, S12 and S13 against this; rerun only where it does not hold, and list the result in the landing report. Propose the matching CLAUDE.md line in the landing.
Then continue the morning ruling: the landing after W1's green dispatch, S11 after its download, the Thursday bundle.
END RULING

## Amendment 1 (Boris, 2026-10-19 morning, verbatim; named plans beside the top 5)

Boris confirms 1 free transfer for GW8 (the planner's estimate is right). In the Thursday bundle, score these explicitly beside the top 5, same columns: (1) Thiago -> Joao Pedro, (2) roll the transfer, (3) the best single bench upgrade if Bench Boost is played in GW8.
END

Pinned before any code for it (2026-10-19): the three rows are printed in the S8 section under the top-5 table with the same columns
(score, gain, hits, lost FT, weekly dxP, plan), scored by `planner.evaluate` on Boris's schedule, decay 0.85, the planner's squad,
bank, xP weeks, P(start) and the confirmed 1 free transfer (the planner's own estimate; the bundle prints both and flags a
difference). (1) Thiago -> Joao Pedro: the single swap of our player whose web_name normalises to "thiago" for the market player
whose web_name normalises to "joao pedro" (accents and case stripped; a missing or ambiguous name is reported as missing input;
an illegal swap - budget, club cap, GK+DEF cap - is reported with its reason, never scored). (2) Roll: the empty plan, scored as
the planner scores it (gain 0, no hit, the lost-FT value of rolling with 1 banked = 0). (3) The best single bench upgrade under
Bench Boost in GW8: over the four bench slots of our GW8 XI by own (`chips.xi_and_bench` on the GW8 xP: the sub keeper and the
three outfield bench players) as the outgoing player and every affordable same-position market player (status available,
45+ minutes in the last four) as the incoming one, the legal swap with the highest score when GW8 is valued with all 15
counting (the sum of the 15 projections plus the captain's, the captain = the highest projection) and GW9-13 as the planner
values them (the best XI with the captain); the GW8 term of the weekly dxP is that Bench-Boost gain, labelled. Information only.
