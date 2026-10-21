# Provenance — run.txt in every output folder (both lanes)

RULING S8 verifier FAIL item (e), pasted verbatim below with the whole
ruling. From 2026-10-19 every output folder of a tool holds a `run.txt`
with the commit hash it ran on and its start and end times (UTC), written
by the tool itself (`tools/provenance.py`); a report may cite a run only
when that commit equals the item's final code. Before the landing the
recorded numbers of S4, S5, S6, S7, S9, S12 and S13 are checked against
this and rerun only where it does not hold; the result goes in the landing
report with a proposed CLAUDE.md line.

## Ruling (verbatim)

RULING S8 verifier FAIL:
(a) The verifier's final-code replay is the S8 result: rerun it yourself on the final code as s8_run3, record it in a new CHANGELOG entry beside the first run's (both kept, the first marked as the buggy generator's), and re-verify. The bar fails either way; nothing is adopted.
(b) Lost-FT charge: the code's reading stands. Using an FT when k are banked forgoes the (k+1)-th banked FT, so the charge is the schedule's (k+1)-th value. Record it as the prereg's reading; no number changes.
(c) Close the five test gaps before the re-verify.
(d) Disposition: the planner stays a screen. In the Thursday bundle, its top plan prints beside the baseline's choice (best one-week move or roll, never a hit) and the no-hit planner line; where they differ, the baseline is the default and the planner is the note.
(e) Provenance, from now on, both lanes: every output folder holds a run.txt with the commit hash it ran on and its start and end times (UTC), written by the tool itself. A report may cite a run only when that commit equals the item's final code. Before the landing, check every recorded number in S4, S5, S6, S7, S9, S12 and S13 against this; rerun only where it does not hold, and list the result in the landing report. Propose the matching CLAUDE.md line in the landing.
Then continue the morning ruling: the landing after W1's green dispatch, S11 after its download, the Thursday bundle.
END RULING
