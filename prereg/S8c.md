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

## Amendment 3, point 3 clarified (verbatim below; pinned before its test)

- **The value:** the bundle's xp_v2 XI picker is `chips.xi_and_bench` (via `side_by_side`). It values a player as `pts.get(id, 0.0)` on section 5's forecast. A player xp_v2 does not forecast is therefore used at 0.0. The CSV already writes `repr(0.0)` and the flag `not forecast` in `lambda_source`, so no code changes.
- **The test:** every CSV value equals the value the picker used.
  - For our 15: the values `xi_and_bench` assigned in the bundle's own run, captured as it ran. One of the 15 is made not forecast on the toy.
  - For every other export player: the picker's value, got by putting him in our 15 in place of a player of his position and calling `xi_and_bench` on the same forecast.
  - The test goes red when a not-forecast player is written at any other value.
- `s8c-wip`'s new head is Thursday's bundle commit after the verifier.

Ruling, Tue 20 Oct night, point 3 clarified: xp_v2_all.csv lists every player in the export. A player xp_v2 does not forecast gets the value the bundle's xp_v2 XI picker actually used for him (0 if it treats him as 0), with the flag "not forecast". A test asserts that every CSV value equals the value the picker used. W3's condition becomes "all 15 are in the CSV" (always true for the export's players); "not recorded" only if the CSV is missing or was committed after the deadline.

## Amendment 4: "if he plays" for our flagged players (Ruling, Tue 20 Oct, 21:00 Prague, point 2, verbatim at the end)

Pinned before any of its code. Tools only.

- **Unchanged:** the status gate stays as it is for the picks, the CSV
  and the grading. The CSV's values, the picks and the picker test do not
  change.
- **Who:** every player in our 15 (`chips.my_squad`) whose export status
  is not 'a'. With none, nothing is printed and the bundle's print is
  exactly as before.
- **Where:** an information block at the end of section 5 (OWN v XP_V2),
  after its "slots differ" line. One header line, then two lines per
  player.
  - **The header:** `  information - our players FPL flags (status not
    'a'): the status gate stays for the picks, the CSV and the grading`.
  - **Line 1:** name, club, position, `status <s>`, `chance_next_round <c>`
    (or `none`), and `news "<news>"`.
  - **Line 2:** `if he plays; the picks treat him as 0:`, then xp_v2,
    own, and his place in the captain table, as below.
- **xp_v2 if he plays:** `tools/xp_v2_live.forecast` and `live` gain an
  optional `lift` (default empty). It sets the status gate to True for
  the players in it, and nothing else.
  - Every other input is section 5's: the export, the snapshot, the
    fallback, the prior, P(start), and P(sub) scaled by `chance_scale` as
    now.
  - The block calls `live(..., lift=(pid,))` once per flagged player and
    reads that player's xp_v2, P(start) and P(sub).
  - A test holds every other player's value equal to the run without
    `lift`, and the lifted value to `core` with that one gate flipped.
  - **If the minutes gate (under 45 in the last four) or a blank still
    drops him:** "no xp_v2 even if he plays: <reason>".
- **own if he plays:** own's gate in `fpl_edge.record_status` is the same
  one-line check (`status != "a" or mins_last4 < 45`).
  - So own is the record branch's own computation with the status part
    lifted: `project(p, {team: [f]}, 6, gameweek, positional_priors,
    personal_priors)` summed over his GW8 fixtures (horizon 6, the
    record's default).
  - A test holds this computation to the recorded own row for an
    unflagged player.
- **The captain table place:** his PMF from `points_pmf.live_pmfs` on the
  lifted forecast (the captain table's own summary). He is placed by the
  captain table's own sort (`-mean`, the others' sums as in section 7).
  - The line says "captain table place on that number: k of 15", with
    mean, P(>=10), P(>=15) and p90.
- **Tests:**
  - a flagged squad player on the toy (status d, chance 75, news);
  - the values as above;
  - the rest of the print byte-identical: the print with the block's
    lines removed equals the print with the block switched off;
  - the CSV byte-identical with and without the block;
  - no flagged player, no block.
  - Mutations are shown red.
- **Then:** the full suite; the GW8 read-only run (Haaland); the verifier
  on the diff; report and CHANGELOG on `s8c-wip`. The new head becomes
  the bundle commit. Due Thu 22 Oct 14:00 UTC.

Ruling, Tue 20 Oct, 21:00 Prague (verbatim):

Ruling, Tue 20 Oct, 21:00 Prague.

1. W1b: not tonight; S2b was today's runner change (one per night). Merge Wednesday before 21:00 UTC as planned.
2. Haaland: the live gate (status 'a') sets him to 0 in xp_v2 because FPL flags him 'd', 75%. The gate stays as it is for the picks, the CSV and the grading. Add to the bundle on s8c-wip an information block for every player in our 15 whose status is not 'a': status, chance_next_round, news, and xp_v2 recomputed as if available (the same inputs with only the status gate lifted for that player, P(sub) scaled by chance as now; own too if its gate is the same one-line check), labelled "if he plays; the picks treat him as 0", plus his place in the captain table on that number. The picks, the CSV values and the picker test do not change; test that the rest of the print is byte-identical. The verifier checks the diff. Done by Thu 22 Oct 14:00 UTC; the new head becomes the bundle commit.
3. Record in BUILD_PLAN Part F as F-M (no code): the status gate drops 'd' players entirely whatever their chance. Each week, record what our flagged players actually score; revisit at GW15 with a prereg if the gate is costing points.

## Rulings, Fri 6 Nov morning (Boris's message verbatim)

Rulings, Fri 6 Nov morning. GW10 first: run the GW10 deadline pass (Boris's paste) before anything else. Step 16 resumes after the GW10 deadline (18:30 UTC).
Step 16:
1. Yes: type the 2024/25 and 2025/26 European calendars from the Wikipedia season pages under CC BY-SA (F-I (3)), with the revision id and attribution in each CSV header; the verifier checks every row against its source. After the GW10 deadline.
2. Keep the Elo as built (K 20, home 60, tier starts 1500/1400/1300/1200/1100, non-league 1000).
3. Keep 0.5 per European knockout round for English clubs.
4. Keep the FA Cup third-round rule (the 44 tier-1/2 clubs plus 20 placeholders rated 1250).
Record all four in the prereg verbatim before the single backtest run.
Tuesday's two:
5. The 68 tests that fail with commit signing on: make the tests' temporary repos disable signing locally (git -c commit.gpgsign=false or per-repo config). Tests only, no behaviour change; land with the S8c landing on Sun 8 Nov.
6. runcommit: yes, the log line and the status header on both dry and real runs, plus the commit message on real runs. In the international break after W3 and S8c, prereg first.

## Amendment 5: the landing date (Boris's plan of Sun 8 Nov, item 2, and his rulings of Thu 12 Nov, verbatim)

Recorded before the S8c landing. The landing moved from Sun 8 Nov to Tue 10 Nov
by the plan, then to Fri 13 Nov by the rulings of Thu 12 Nov (Schedule, and
point D(a): `s8c-wip` ready to land, `dry/S8c` pushed once that night's
nightly has finished).

### Boris's plan of Sun 8 Nov (verbatim)

International break plan, Sun 8 Nov (the item count resets to 0 of 6). GW11 deadline Sat 21 Nov 11:00 UTC; GW11 freeze from Fri 20 Nov 05:00 UTC. One runner change per night; no merges without Boris's click.
1. Mon 9 Nov: W3 merge (with the +02:00 committer test, the fetch-depth comment and the captain-without-row test); Boris clicks the real run.
2. Tue 10 Nov: the S8c landing (with the commit-signing test fix); Boris clicks the real run.
3. Wed 11 Nov: runcommit (real runs record their code commit), plus a fix for the nightly report's price-moves section matching players by name (it showed Coventry's Thomas at 5.5 -> 4.0; that was Hull's Thomas).
4. GW10 checkpoint once GW10 is locked (data_checked): BUILD_PLAN Step 20 and F-J: the paired own v xp_v2 metric over GW8-10 from the pre-deadline bundle CSVs and the projection log, the revert rule, and the model re-grade. Report only; no change without Boris.
5. Status gate v2 (F-M, brought forward from GW15): draft the prereg only, no code yet. Proposal: status 'd' = P(start) x chance in the next gameweek and as normal after; 's' = 0 for the known ban length, then as normal (Thiago: GW11-13 out, back GW14); 'i' with an unknown return = 0 for two gameweeks, then scaled by the last known chance. State how it can be checked, given that historical flags aren't archived. Boris rules before any code.
6. Step 16: finish it (type the 2026/27 cup and European CSVs, the verifier's row checks, the single backtest run, the report), then Step 18's prereg (the second-half chip plan).
Thu 19 Nov: the GW11 bundle, with Thiago and Thomas out, on Boris's paste.

### Boris's rulings of Thu 12 Nov (verbatim)

Rulings and tonight's plan, Thu 12 Nov (Boris is here; no runner pushes to master until tonight's nightly has finished; no merges tonight).

Rulings:
1. W3 verifier FAIL (record only): paste Boris's Sun 8 Nov plan text verbatim into prereg/W3.md, marked "recorded after the fact on 12 Nov: the landing moved from Sat 7 Nov to 11 Nov by Boris's plan of Sun 8 Nov". Then re-run the verifier's record check only. No code change. Rule kept: each plan item's text goes into its prereg before acting on it.
2. One night behind: CAPTAIN and BAN RISK must read the current night's export (availability matters before a deadline). CHIPS may stay one night behind, as amendment 3 allows. Fix with a test.
3. False Free Hit flag: CHIPS values every player on one scale. A player with no own forecast counts as 0, with a note, never on a different scale; the FH flag must agree with the base screen in the same report. Fix with a test.
4. Two runs in one day: the S2 rule stands (same-day rows replaced). Note in the report that the scheduled run's xp_v2 rows survive at data 2e0b948.
5. Effort level: note "launched at high, not confirmable" in the report; nothing else.
Schedule (one runner change per night; Boris clicks each real run; all before the GW11 freeze, Fri 20 Nov 05:00 UTC): Fri 13 Nov S8c; Sat 14 Nov runcommit plus the price-moves name fix; Sun 15 Nov points 2 and 3 as one change with two tests.

Tonight, in this order:
A. The W3 record fix (Ruling 1).
B. GW10 checkpoint, report only (BUILD_PLAN Step 20 and F-J). GW10 should now be locked. The paired own v xp_v2 decision metric over GW8-10: each model picks its XI, captain and bench from our actual 15; realised points with autosubs; using the pre-deadline bundle CSVs (gw8 6034baa, gw9 e708c91, gw10 c0c6c3f) and own's last pre-deadline rows from the projection log. Per-week numbers, the mean and its 90% interval, the revert rule's verdict, and the model re-grade (calibration for every source over GW4-10). Post it here for the chat.
C. Status gate v2 prereg draft (break plan item 5). The rule as proposed: 'd' = P(start) x chance in the next gameweek, then normal; 's' = 0 for the known ban length, then normal; 'i' with an unknown return = 0 for two gameweeks, then scaled by the last known chance. Say how it can be checked without archived historical flags, and what it changes for Thiago, Thomas and Calafiori in the GW11 matrix. Draft only; post it here for Boris's ruling tonight.
D. Branch prep for the coming nights: (a) s8c-wip ready to land; push dry/S8c for its automatic dry run once tonight's nightly has finished. (b) A branch with Rulings 2 and 3, their tests and the verifier, ready for Sunday.
E. If there's time: Step 16 (the 2026/27 CSVs, the row checks).
Stop at 6 items; park questions with the exact wording. Also post the status of Step 16.

## Point 5, pinned before its code (Thu 12 Nov; the S8c landing, Fri 13 Nov)

Point 5 of the rulings of Fri 6 Nov (verbatim above): the tests' temporary
repos disable signing locally. Tests only; no runner file changes.

- **Where:** every place the suite creates a non-bare repository that is
  committed to, by the test or by the code under test: `test_fpl.py`
  (NightlyRunner's restore test, `DataGate.setUp`, `Publish._ident` for the
  seed and runner clones, `PrePush.setUp`), `tests/test_S3.py`
  (`ChecksMain.setUp`, `PublishOnAFail.setUp` seed and run clone),
  `tests/test_W1.py` (`OddsAppendOnly.setUp`, `OddsNeverCostsTheNight`'s seed
  and data clone), `tests/test_W1b.py` (`DueGate.setUp`, `Hook.setUp`):
  twelve lines, each `git config commit.gpgsign false` in that repository's
  own config right after its init or clone (the per-repo form the ruling
  allows; it also covers the commits `fpl_publish.py` makes there).
  `tests/test_W3.py`'s `git_commit` already passes `-c commit.gpgsign=false`
  (W3 amendment 3). Bare remotes are not committed to and are left alone.
- **The guard:** `tests/test_S8c_p5.py`: (1) a global config with
  `commit.gpgsign = true` and a signing program that does not exist makes an
  unprotected commit fail, and the per-repo setting makes it pass; (2) one
  test per site, run in a child process under that global config, passes.
- **Measured before and after:** the whole suite under that global config;
  each of the twelve lines left out in turn must turn the guard red (or be
  shown covered by another line, said in the report); the suite bare and
  with the data, by discovery, on `git archive` copies.
- **The landing:** master merged into `s8c-wip` (one CHANGELOG conflict,
  both sides kept); the verifier's pre-check; `dry/S8c` after tonight's
  nightly has committed; the merge Fri 13 Nov before 21:00 UTC with tag
  `pre-S8c`, then Boris's real run.

## Rulings, Thu 12 Nov night (Boris's message verbatim; for this item: its part "S8c landing" (point 2 is Boris's OK for f1f5df2) and the Schedule (Fri 13 Nov))

Rulings, Thu 12 Nov night (chat review: the item count resets to 0 of 6).

FJ, the GW10 checkpoint:
1. xp_v2 stays (revert rule: upper bound +8.00). Fix the report's sentence: own's GW9 tie was settled by the squad's slot order (our actual GW9 line-up), not by id. Add the verifier's figures for a lowest-id tie rule (d = +0, -1, +12, mean +3.67, 90% [-0.67, +8.00]; same verdict). The pinned result stays primary.
2. Add tests/test_FJ.py (the sign of d; the revert verdict on a toy; the tie order), since F-L re-runs this script at GW15. In prereg/FJ.md, pin an explicit, model-neutral tie rule (lowest player id) for the GW15 run, before that run.
3. Parked F-J items: the chip plan for GW11-19 (first-half Bench Boost and Free Hit) comes before the GW11 deadline. Prereg it, run it by Wed 18 Nov, and use S7 on the candidate post-transfer squads plus bb_timing with status gate v2 as information. The 50 squads, S6's rerun, F-E and the DEF re-check go with F-L at GW15.
4. Calibration: before reading anything into fpl_ep's numbers, re-run the calibration on the common player set at GW15 (its 3 gameweeks were scored on a different population). Note own's bias drift (about -1.4 since GW8) in BUILD_PLAN's revisit list.

FM, status gate v2 (Boris's answers to the five questions):
1. 'i' with an unknown return: 0 in weeks t and t+1, then a fixed 50% from t+2.
2. 'i' with a return date in the news: like 's': 0 until that date, then as normal.
3. 's' with no end date: 0 for one gameweek, then as normal.
4. Yes: record the rule under a new source name, xp_v2_g2, with the retrospective check (GW4-10 from our archived nightly exports) as its test and the bar as drafted (90% lower bound of the paired |error| difference above 0). xp_v2 keeps the v1 gate; xp_v2_g2 replaces nothing until it passes and Boris accepts it.
5. Suspended matches count as neither started nor missed in the last-four window.
Timing: code, the check and the verifier on a branch by Tue 17 Nov. The runner records xp_v2_g2 as a new source on Tue 17 Nov (one runner change). Its numbers go into the GW11 bundle as information whatever the check says.

S8c landing (answers to the verifier's decisions):
1. Yes: bring origin/s6f-wip 0b16969, origin/s6e2-wip d87f8aa and origin/s8b-wip cfa7a36 into s8c-wip; the full suite; a short re-check of the new head before the dry run.
2. Boris's OK for f1f5df2 (fpl_xpv2.forecast takes tools/xp_v2_live.forecast's text again, lift=()). Record this ruling verbatim in prereg/S8c.md before the merge.
3. Yes, with the landing: a W3 test on the toy with a status 'd' player, asserting the runner records no xp_v2 for him (tests only).
4. Make ChecksMain.setUp check its commit's exit code so the guard covers the twelfth line.
5. Mode (d): the 21:00 UTC-to-end-of-nightly window applies to master and to dry/* (anything that starts a workflow). Other work branches may be pushed at any time.
6. Add the CHANGELOG entry and report for point 5 and the copy fix to the landing (docs only, inside the re-check). Leave the duplicate W2 amendment 2 entry as recorded (append-only); note it in the S8c report.

Schedule (one runner change per night; Boris clicks each real run; all before the GW11 freeze, Fri 20 Nov 05:00 UTC): Fri 13 S8c (dry run after the re-check, then the merge on Boris's click); Sat 14 runcommit plus the price-moves name fix; Sun 15 W3fix (CAPTAIN/BAN RISK on the current export, CHIPS on one scale); Tue 17 xp_v2_g2 recorded; Wed 18 the chip plan posted; Thu 19 the GW11 bundle on Boris's paste.
Record each part of these rulings verbatim in its prereg before acting on it.

## The re-check work, pinned before its code (rulings of Thu 12 Nov night, S8c points 1, 3, 4, 6)

- **Point 1:** merge `origin/s6f-wip` `0b16969`, `origin/s6e2-wip` `d87f8aa`
  and `origin/s8b-wip` `cfa7a36` into `s8c-wip` (on CHANGELOG conflicts, both
  sides kept).
- **Point 3:** `tests/test_W3.py`: on the W3 toy, one of our players at
  status `d` (chance 50) in the export; the runner's xp_v2 record has no row
  for him (and has one when he is `a`). Tests only.
- **Point 4:** `tests/test_S3.py` `ChecksMain.setUp` checks its commit's exit
  code (`check=True`), so a commit that fails stops the test; the guard
  `tests/test_S8c_p5.py` gains a ChecksMain test, and leaving out each of the
  twelve lines turns it red.
- **Point 6:** the S8c landing's CHANGELOG entry and report
  (`worklog/cc_2026-11-13_S8c_landing.md`) for point 5 and the copy fix, on
  the branch, inside the re-check; the duplicate "W2 amendment 2" entry is
  left as recorded and noted in the report.
- Then the full suite (bare, with the data, with signing on) and the
  verifier's short re-check of the new head; `dry/S8c` only after tonight's
  nightly has committed (point 5: the window covers master and dry/*).
