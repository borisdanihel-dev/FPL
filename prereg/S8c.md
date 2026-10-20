# S8c — the live planner on xp_v2, no hits (for Thursday's GW8 bundle)

Committed before any S8c code. Tools only: `tools/planner_live.py` and the
bundle's planner section in `tools/gw_pass.py`. No runner change; the
nightly imports neither. Branch `s8c-wip`, off `s15-wip` (it holds S15's
live xp_v2 horizon matrix, S8's planner and the landing's bundle).

## The ruling (Ruling, Tue 20 Oct, point 1, verbatim; the whole ruling at the end)

1. S8b: accepted if its verifier PASSes (a WARN or FAIL: stop and park). From GW8 the no-hit planner on xp_v2 (decay 0.85, Boris's FT schedule) is the default transfer suggestion; the simple rule is printed beside it; hits stay a manual call. CHANGELOG entry before Thu 22 Oct 11:30 UTC.
   Live, tools only (no runner change): S8's planner fed by S15's live xp_v2 horizon matrix (the Odds API snapshot where it prices the fixture, else the fallback; source per fixture printed), 1 FT, no hits. Also print, as information, the same planner with week t's bench at full weight (GW8 Bench Boost). It goes into Thursday's bundle; ready by Thu 22 Oct 14:00 UTC. If it is not ready or the verifier does not pass, the bundle prints S8's planner and the simple rule, and we decide by hand.

## Design (pinned)

- **The matrix:** xp_v2 as tested for weeks target..target+5 from the
  newest export before the deadline (S15's `builder.live_matrix`, unchanged).
  - Per fixture, the Odds API snapshot (newest before the deadline) where
    it prices the fixture, else the fallback fitted on results before the
    deadline.
  - The tool prints every fixture's source, per week.
  - A test holds the tool's matrix to `builder.live_matrix`.
- **The planner:** S8's `rank_plans`, unchanged: our 15 at selling prices,
  bank = budget − selling prices, k = 1 free transfer, `hits_allowed=False`,
  decay 0.85, schedule `boris` (1.5 / 1.0 / 0.6 / 0.3), S8's pool.
  - The market is every player with status 'a' and 45+ minutes in the last
    four (S8's live market).
  - P(start) is the current model's (only S8's hit rule reads it, and hits
    are off).
  - The top 5 plans print in S8's format.
- **The simple rule beside it:** S8's `baseline_plan` on the same matrix
  (the best one-week move with the free transfer when its xP gain > 0, else
  roll), with its week-t gain.
- **The Bench Boost variant (information):** every plan S8 scored is
  re-scored with week t's value = all 15 by xP + the captain (S8's captain
  rule), in place of the XI + captain. Week t's gain is replaced; the other
  weeks, decay and lost-FT value are unchanged. Then it is re-ranked and
  the top 3 print. No other change to S8.
- **Hits:** none suggested (a manual call). The line says so.
- **The bundle (`tools/gw_pass.py`):** the planner section prints this
  planner as the default and the simple rule beside it.
  - If the xp_v2 matrix cannot be built (a missing input), it says so and
    prints S8's own planner (own xP) and the simple rule, as the ruling's
    fallback. Nothing is substituted silently.
  - The rest of the bundle is unchanged (own and xp_v2 for all 15, the
    captain table).

## Tests and checks

- `tests/test_S8c.py`, hermetic, on S6d's toy 2026/27 folder and toy
  history:
  - the matrix equals `builder.live_matrix`, with every fixture's source;
  - the plans equal S8's `rank_plans` with hits off and k = 1;
  - the simple rule equals `baseline_plan`;
  - the Bench Boost re-score by hand;
  - no hit is ever suggested;
  - the bundle's section with and without the matrix (the fallback);
  - isolation.
- Mutations (shown red).
- The full suite before and after.
- A read-only live run against the data folder (GW8).
- The verifier (Fable; Opus xhigh as ruled); the write guard.
- The report in `worklog/cc_<date>_S8c.md` and the CHANGELOG.

## Ruling, Tue 20 Oct (verbatim)

The ruling of Tue 20 Oct, verbatim.

Ruling, Tue 20 Oct (chat review; the item count resets to 0 of 6).

1. S8b: accepted if its verifier PASSes (a WARN or FAIL: stop and park). From GW8 the no-hit planner on xp_v2 (decay 0.85, Boris's FT schedule) is the default transfer suggestion; the simple rule is printed beside it; hits stay a manual call. CHANGELOG entry before Thu 22 Oct 11:30 UTC.
   Live, tools only (no runner change): S8's planner fed by S15's live xp_v2 horizon matrix (the Odds API snapshot where it prices the fixture, else the fallback; source per fixture printed), 1 FT, no hits. Also print, as information, the same planner with week t's bench at full weight (GW8 Bench Boost). It goes into Thursday's bundle; ready by Thu 22 Oct 14:00 UTC. If it is not ready or the verifier does not pass, the bundle prints S8's planner and the simple rule, and we decide by hand.
2. S15: accepted if its verifier PASSes. tools/builder.py is the default for Free Hit and Wildcard builds, with the GK+DEF cap on live and its cost printed, and the three-layer rule's squad printed beside it. CHANGELOG entry. Not used for GW8.
3. S17: information only, not a decision input; no live output before GW20, then labelled "overconfident in the test; below baseline at GW20". Push s17-wip to GitHub (it is not there).
4. F-I: yes to all three. (1) football-data: read the disclaimer first; if it restricts personal non-commercial use, stop and park. 20 files, python -I, URL, fetch time and SHA-256 in worklog/downloads_<date>.md. (2) Hand-typed CSVs from the official pages, source URL and read time per row, draws cross-checked with BBC Sport; the verifier re-checks every row against its source. (3) Wikipedia: OK, CC BY-SA attribution and revision id in each CSV's header. Then Step 16 parts 3-4 and Step 18 in order, preregs verbatim first, done before the GW19 deadline (Fri 1 Jan 2027 18:30 UTC).
5. W3: add finished_provisional to fixtures as an additive column (old rows NULL), appended at the end of the CSV so readers by position don't break. W3 merges by Thu 29 Oct via dry/W3; one runner change that night.

Order, time-bound first:
a. Today: landing-2026-10-19b and s2b-wip after Boris's dry runs, as planned; the real run before 21:00 UTC.
b. Report S8b's and S15's verifiers as soon as they land, not next morning: S8b feeds Thursday.
c. Push s17-wip.
d. The live planner for the bundle (point 1), by Thu 14:00 UTC.
e. Wednesday: W1b as planned.
f. W3: points 2, 3 and 5.
g. F-I downloads, then Step 16 parts 3-4 and Step 18.
Thursday's bundle carries own and xp_v2 for all 15, the captain table and the planner. Same rules: no runner pushes from Thu 22 Oct 11:30 UTC to the GW8 deadline; no merges without Boris; stop at 6 items.
