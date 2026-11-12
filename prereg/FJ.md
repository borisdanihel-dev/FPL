# FJ — the GW10 checkpoint (BUILD_PLAN Step 20, Part F item F-J), report only

Committed before any computation for this item. Offline, report only: no
model, runner or decision changes without Boris (plan item 4: "Report only;
no change without Boris").

## The rulings (verbatim)

### BUILD_PLAN Part F, F-J (RULINGS PART F, 19 Oct 2026)

F-J. GW10 checkpoint (Step 20), after GW10 locks down (about Mon 9 Nov): (1) the revert rule on GW8-10, per squad-gameweek paired differences on our squad and 50 squads sampled from 2026/27 GW1 ownership, using the recorded pre-deadline rows; (2) S6's validation rerun (cut 6); (3) F-E adoption if it passed; (4) every source's accuracy report and drift; (5) the DEF calibration re-check; (6) a chip plan for GW11-19.

### The revert rule (RULING S6b acceptance + lanes merge, point 3, 19 Oct; `prereg/S6b.md`)

3. Revert rule, fixed now: at the GW10 checkpoint, if the live paired decision metric over GW8-10 has its 90% upper bound below 0, own returns.

### Boris's plan of Sun 8 Nov (verbatim; its item 4 is this item)

International break plan, Sun 8 Nov (the item count resets to 0 of 6). GW11 deadline Sat 21 Nov 11:00 UTC; GW11 freeze from Fri 20 Nov 05:00 UTC. One runner change per night; no merges without Boris's click.
1. Mon 9 Nov: W3 merge (with the +02:00 committer test, the fetch-depth comment and the captain-without-row test); Boris clicks the real run.
2. Tue 10 Nov: the S8c landing (with the commit-signing test fix); Boris clicks the real run.
3. Wed 11 Nov: runcommit (real runs record their code commit), plus a fix for the nightly report's price-moves section matching players by name (it showed Coventry's Thomas at 5.5 -> 4.0; that was Hull's Thomas).
4. GW10 checkpoint once GW10 is locked (data_checked): BUILD_PLAN Step 20 and F-J: the paired own v xp_v2 metric over GW8-10 from the pre-deadline bundle CSVs and the projection log, the revert rule, and the model re-grade. Report only; no change without Boris.
5. Status gate v2 (F-M, brought forward from GW15): draft the prereg only, no code yet. Proposal: status 'd' = P(start) x chance in the next gameweek and as normal after; 's' = 0 for the known ban length, then as normal (Thiago: GW11-13 out, back GW14); 'i' with an unknown return = 0 for two gameweeks, then scaled by the last known chance. State how it can be checked, given that historical flags aren't archived. Boris rules before any code.
6. Step 16: finish it (type the 2026/27 cup and European CSVs, the verifier's row checks, the single backtest run, the report), then Step 18's prereg (the second-half chip plan).
Thu 19 Nov: the GW11 bundle, with Thiago and Thomas out, on Boris's paste.

### Boris's rulings of Thu 12 Nov (verbatim; point B is this item)

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

## The method, pinned before computing

- **Lockdown guard:** GW8, GW9 and GW10 are graded only if their event has
  `data_checked = 1` and every fixture `finished = 1` in `fpl.sqlite` (data
  worktree, pulled). If GW10 is not locked down, nothing is computed for it
  and the item stops.
- **Our actual 15:** entry 3073318's 15 picks for each gameweek (`picks`).
- **xp_v2:** `worklog/gw_pass/gw<g>/xp_v2_all.csv` at the bundle commits the
  ruling names: GW8 `6034baa`, GW9 `e708c91`, GW10 `c0c6c3f`. Each is checked
  as W3's REALISED checks GW8's (`fpl_squad.bundle_csv`): committed before the
  deadline, its `run.txt` ending before the deadline and recording the CSV's
  SHA-256. If the reader picks a different commit than the ruling names, or a
  check fails, the gameweek is reported as such, not substituted.
- **own:** its last snapshot made before each deadline in `projection_log.csv`
  (`fpl_squad.recorded`, i.e. `fpl_edge.forecasts`).
- **Each model's choice and its points:** `fpl_realised.realised_on` at master
  `47ac1ea`, unchanged (S6c's definition, W3's REALISED): the XI by the model's
  xP (`fpl_chips.xi_and_bench`, a missing forecast is 0), the bench in
  forecast order, `rule_autosubs` on realised minutes, the captain (highest
  xP in the XI, ties to the lower id) doubled. No vice promotion, no chips:
  both models are scored the same way on the same 15.
- **The metric (primary, one):** per gameweek, d = realised(xp_v2) −
  realised(own) on our 15; the mean over GW8–10.
- **Interval:** `fpl_bt.bootstrap_mean` (the runner's copy of
  `tools/backtest.py`): unit = gameweek, B = 10,000, seed 20261018, 90%
  percentile interval, as S6b. With three gameweeks the interval is coarse;
  it is printed as it comes.
- **The revert rule's verdict:** own returns if the 90% upper bound is below
  0; otherwise xp_v2 stays. Reported only; Boris decides.
- **The re-grade:** the official calibration, `fpl_edge.py --section
  calibration` (run from the data worktree after `fpl_nightly.py --restore`),
  for every source over GW4–10, printed as it comes. No source is changed.
- **Not in tonight's ruling (point B), so not computed tonight and parked:**
  F-J's 50 squads sampled from 2026/27 GW1 ownership, (2) S6's validation
  rerun, (3) F-E, (4) drift beyond the calibration section, (5) the DEF
  re-check, (6) the chip plan.
- **Provenance:** the script and its output go under
  `worklog/checkpoint_gw10/`, with a `run.txt` written by
  `tools/provenance.py`; only a run on a clean commit with 0 modified files
  is cited.
