# Bundle — the Thursday deadline pass (GW8), information only

The chat's ruling of the morning of 2026-10-19, item 6, pasted verbatim
below with the whole ruling. The template rows are filled in when the
bundle tool starts, before any of its code. Offline under `tools/`
(`tools/gw_pass.py` → `tools/out/gw8_pass.txt`); information only, no
bar, no adoption; it composes the live outputs of S5, S7, S8, S9, S6 and
S12 from the newest snapshot in `C:\GIT\FPL-data`.

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
