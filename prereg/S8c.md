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

## Amendment 1: the bundle from s8c-wip, two test gaps, the cap flag (Ruling, Tue 20 Oct afternoon, verbatim)

Ruling, Tue 20 Oct afternoon.

1. Thursday's bundle (and Friday's refresh) runs from s8c-wip's final commit, not master. Its output is committed to master under worklog/gw_pass/gw8/ (worklog only, no runner files) before the GW8 deadline, with the s8c-wip commit in its provenance file. s8c-wip lands on master after the deadline, dry run first: Sun 25 Oct (Saturday is W2's night).
2. Yes: tests for both verifier gaps (a fixture with no odds price; the rule's score under Bench Boost) on s8c-wip, tests only, mutations red, by Wed 21 Oct 20:00 UTC.
3. Yes: every printed squad or suggested move that breaks the GK+DEF 2-per-club cap gets a flag on its line (e.g. "breaks the cap: ARS 3"). Print only; no rule changes. Re-run the suite and the GW8 read-only run; the verifier checks the diff. Done by Wed 21 Oct 20:00 UTC.
4. The S8b and S15 CHANGELOG entries go on master today, docs only.

Then: W1b on Wednesday as planned, then W3 (points 2, 3, 5), then F-I. Same rules: no runner pushes from Thu 22 Oct 11:30 UTC to the GW8 deadline; no merges without Boris; stop at 6 items.

### Design for amendment 1 (pinned before any of its code)

**Point 1, the bundle.**
- Thursday's bundle and Friday's refresh run `tools/gw_pass.py` from
  `s8c-wip`'s final commit: the commit after points 2 and 3, once their
  verifier passes. The data is `C:\GIT\FPL-data`, pulled, read-only.
- The output (the bundle text and its `run.txt`, which names that
  commit) is committed to master under `worklog/gw_pass/gw8/` before the
  GW8 deadline (Fri 23 Oct 17:30 UTC). That commit holds worklog files
  only.
- `s8c-wip` lands on master on Sun 25 Oct, after a dry run.

**Point 2, the two verifier gaps (tests only, on `s8c-wip`).**
- *A fixture with no odds price:* a toy whose odds snapshot prices only
  some of week t's fixtures.
  - The planner prints "fallback" for each unpriced fixture and "odds"
    for the others.
  - The printed counts equal `builder.live_matrix`'s sources.
  - The test goes red when every source is printed as "odds" (the
    verifier's m6).
- *The rule's score under Bench Boost:* for `--bb`, the rule's objective
  is scored with week t's bench at full weight (`bench_full=True`).
  - It equals `builder.objective(rule, weeks_xp, 1.0, True)`.
  - On the toy it differs from the score with `bench_full=False`.
  - The test goes red when the rule is scored without `bench_full` (the
    verifier's n4).

**Point 3, the cap flag (print only).**
- *When it applies:* a squad breaks the cap when one club has more than
  2 goalkeepers and defenders among its 15.
- *Moves:* a suggested move is judged on the squad after it: our 15,
  minus the players out, plus the players in.
- *The flag:* "breaks the cap: ARS 3", appended to the line it belongs
  to, after three spaces.
  - Several clubs are joined by ", ", sorted by club.
  - A line that names more than one squad or move (S8's decay
    alternative in brackets) flags each where it is named.
- *Where:*
  - `tools/planner_live.py`: the top 5 plans, the DEFAULT line, the
    simple rule's line, and the Bench Boost top 3.
  - `tools/planner.py` live (S8's planner, printed in the bundle as
    information): each schedule's top plans, the decay alternative in
    brackets, and the exploratory lines.
  - `tools/gw_pass.py` section 3: the BASELINE, "planner top plan" and
    "planner, no hits" lines, and the named plans.
  - `tools/gw_pass.py` section 5: our 15 (shown as the XI and bench) is
    flagged on its summary line ("... slots differ; ...") if our current
    squad breaks the cap.
  - `tools/builder.py` live: the builder's squad (its "formation ...;
    spent ..." line) and the three-layer rule's "beside it" line.
- *Not flagged:* lines that print no squad and suggest no move. These are
  S7's chip values (no squad is printed), S9's league and
  effective-ownership lines (rivals' squads, not suggestions), the keeper
  line, the captain table, and the builder's `--test` A/B (aggregates
  only).
- *No rule changes:* no ranking, legality, budget, score or plan changes.
  A squad or move that keeps the cap prints exactly as before.
- *Tests:* each location flagged on a case that breaks the cap and
  unflagged on one that keeps it, the flag's text included; mutations
  shown red.
- *Checks:* the full suite before and after; the GW8 read-only runs
  (`planner_live.py`, `builder.py --freehit`, the bundle) re-run.
- *The verifier* checks the diff and the cap-flag prints.
- *Report and CHANGELOG:* `worklog/cc_<date>_S8c_a1.md` and a CHANGELOG
  entry on `s8c-wip`.
- *Deadline:* Wed 21 Oct 20:00 UTC.

## Amendment 2: the bundle commit stays as verified (Ruling, Tue 20 Oct evening, point 1, verbatim)

`s8c-wip` `71c9d17` is the commit Thursday's bundle and Friday's refresh run from. The sorted-clubs flag test (the amendment-1 verifier's one survivor) is added when `s8c-wip` lands on Sun 25 Oct.

Ruling, Tue 20 Oct evening.

1. No new test now: s8c-wip 71c9d17 stays the commit Thursday's bundle runs from, exactly as verified. Add the sorted-clubs flag test when s8c-wip lands on Sun 25 Oct.
2. Yes: a Fable verifier on S2b's after-measurement (worklog/cc_2026-10-20_S2b_after.md) tonight; it blocks nothing.

Then tonight, on branches only: W3 points 2, 3 and 5 on w3-wip (merge by Thu 29 Oct via dry/W3), then the F-I downloads and Step 16's prereg. Wednesday: W1b as planned; tell Boris when his dry-run click is needed. Same rules: no runner pushes 21:00 UTC to the end of the nightly; no merges without Boris; stop at 6 items.

## Amendment 3: the bundle writes xp_v2_all.csv (Ruling, Tue 20 Oct night, point 3, verbatim at the end)

Pinned before any of its code. Tools only (`tools/gw_pass.py`); no runner
file.

- **The file:** in the same run, `tools/gw_pass.py` writes
  `xp_v2_all.csv` into its output folder (`--out`; on Thursday that is
  `worklog/gw_pass/gw8/`). `run.txt` records it with its SHA-256.
- **The rows:** one per player in the export's `all_players`, sorted by
  id.
  - **Players xp_v2 forecasts:** the forecast from section 5's run
    (`xp_v2_live.live`).
  - **Players it does not forecast:** the gate (status not 'a', under 45
    minutes in the last four, or no fixture). They are listed with
    `xp_v2` 0, which is the bundle's own rule ("0 in the choice"), with
    `p_start` empty and `lambda_source` `not forecast`.
  - Haaland is such a player on GW8 (status d). Without his row, "all 15
    are in the CSV" would fail while he is in our squad.
  - **This choice is open for Boris.** The alternative is to list only
    forecast players.
- **The columns:** `id, name, team, position, xp_v2, p_start,
  lambda_source`.
  - `name` is the export's web_name; `team` the club's short name;
    `position` GK, DEF, MID or FWD.
  - `xp_v2` and `p_start` are written in Python's `repr` of the float, so
    they round-trip exactly.
  - `lambda_source` is each of the club's GW8 fixtures' source (`odds`
    or `fallback`) in kickoff order, joined by `;`.
- **No print changes:** `gw8_pass.txt` stays byte-identical with and
  without the CSV (a test). If section 5 cannot run (a missing input), no
  CSV is written. The print already says why, and nothing is substituted.
- **Tests:** the rows equal `xp_v2_live.live`'s forecast and detail on the
  toy; the not-forecast rows; the round trip; the print byte-identical
  with and without the writer; the CSV in `run.txt`. Mutations are shown
  red.
- **Then:** the full suite; the GW8 read-only run; the verifier on the
  diff; report and CHANGELOG on `s8c-wip`.
  - The new head replaces `71c9d17` as the commit Thursday's bundle runs
    from.
  - Due by Thu 22 Oct 14:00 UTC.

Ruling, Tue 20 Oct night (verbatim):

Ruling, Tue 20 Oct night.

1. S2b after-report: yes. Correct the four slips in the report; add an amending CHANGELOG entry; the original entry stays as written.
2. Yes: appended last in the table is what was meant.
3. Change the GW8 grading so it does not depend on Friday's timing. The export cannot see a pending transfer before the deadline, so a refresh after Boris's transfer would still print the old 15.
   - s8c-wip: the bundle also writes worklog/gw_pass/gw8/xp_v2_all.csv from the same run: every player it forecasts, with id, name, team, position, xp_v2 for GW8, P(start) and the lambda source. Test that the printed output is byte-identical with and without the CSV. The verifier checks the diff. Done by Thu 22 Oct 14:00 UTC; the new head is the commit Thursday's bundle runs from.
   - w3-wip: REALISED takes the actual GW8 15 from the post-deadline picks, own from the projection log, and xp_v2 from that CSV; each model picks its XI and captain from those 15. The condition "the bundle's 15 equals the GW8 squad" is replaced by "all 15 are in the CSV"; otherwise "not recorded".
4. Committer time: OK, and the bundle's run.txt end time must also be before the deadline. Both are required.
5. Yes: the item count resets to 0 of 6. Wednesday: point 3, then W1b as planned (tell Boris when his dry-run click is needed, before 21:00 UTC), then Step 16's prereg. Same rules: branches only; no merges without Boris; no runner pushes 21:00 UTC to the end of the nightly or from Thu 22 Oct 11:30 UTC to the GW8 deadline.
