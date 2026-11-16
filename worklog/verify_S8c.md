# Verifier report: S8c (the live no-hit planner on xp_v2) and S15 amendment 2 (the rule's squad beside the builder's)

Verifier: backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high, as
`.claude/agents/backtest-verifier.md` (read from disk first; it matches the
loaded instructions). Run 2026-10-20 ~11:45-12:05 UTC. Item worktree
`C:/Users/Boris/AppData/Local/Temp/claude/C--GIT-FPL/442a647f-7693-4ced-b840-0df7f5bfd943/scratchpad/s8c`
(branch s8c-wip, HEAD 518f69e, status clean before and after). All scratch
under `.../scratchpad/v8c/`. Real data `C:\GIT\FPL-data` at e1154dd (pulled
--ff-only: already up to date), read-only; no API called, no workflow
dispatched, nothing pushed, nothing written outside `v8c/` and this file.

Both items are tools-only decision calculators with no pre-registered
pass/fail metric: checks 1, 2, 5, 6, 7 and the items' own acceptance tests,
plus the caller's seven points.

## Prereg before code, rulings verbatim and unedited

| | prereg commit (master) | first code commit | order |
|---|---|---|---|
| S8c | de8ca68, 2026-10-20 13:23:54 +0200 | 7773a58, 13:27:42 +0200 | prereg first: PASS |
| S15 amendment 2 | 5c90e08, 13:32:27 +0200 | 615b35b, 13:42:33 +0200 | prereg first: PASS |

`git diff de8ca68 master -- prereg/S8c.md` and `git diff 5c90e08 master --
prereg/S15.md`: both empty; `git diff master 518f69e -- prereg/`: empty. The
rulings are in the preregs verbatim ("Ruling, Tue 20 Oct", points 1-5 and
the order a-g, in both files; the S8c file carries point 1 at the top and
the whole ruling at the end). No ruling is missing: check 4 (as far as it
applies) PASS.

## Caller's point 1: the design as pinned in prereg/S8c.md

Read of `tools/planner_live.py` (168 lines, new), the `tools/gw_pass.py`
hunk (15 lines) and `tests/test_S8c.py`, against the pinned design:

- **The matrix** is `builder.live_matrix(data_dir, hist_root, 6)` called
  directly (`live_inputs`), unchanged (`tools/builder.py` is not touched by
  7773a58/50e89dd). The per-fixture source list is rebuilt by
  `fixture_sources` with the same `OL.fixture_lambdas(book, model, ...)`
  call on the same snapshot book and fallback model; printed per week
  ("lambdas GW8: ARS-EVE odds, ..."). On the real data the tool's 60
  sources aggregate to exactly `live_matrix`'s counter: week t odds 10,
  later weeks odds 10, fallback 40. PASS.
- **The planner** is `PL.rank_plans(squad, bank, market, weeks_xp, 1,
  p_start, 0.85, PL.SCHEDULES["boris"], hits_allowed=False)`:
  `FREE_TRANSFERS = 1`, `DECAY = PL.DECAY` (0.85), schedule "boris" =
  (1.5, 1.0, 0.6, 0.3), the 15 from `CH.my_squad` at selling prices, bank =
  `E.selling_budget` − selling prices, the market = status 'a' and
  mins_last4 >= 45 (identical to `PL.live`'s). `tools/planner.py` is
  unchanged by the item. PASS.
- **The simple rule** = `PL.baseline_plan(squad, bank, pool, weeks_xp[0], 1)`
  on the same pool and week t's matrix, printed beside the default with its
  planner score and week-t gain. PASS.
- **The Bench Boost variant**: `bb_value` = sum of all 15 by xP + the
  captain (the highest top of a position, S8's rule in `xi_value`);
  `bb_rescore` replaces only `gains[0]` (score − gains[0] + g0; decay^0 = 1),
  keeps gains[1:] and `lost`, re-sorts with S8's key, prints the top 3 under
  "information". PASS.
- **No hit**: with k = 1 and `hits_allowed=False`, `evaluate` returns None
  for every two-transfer plan; on the real data all 326 scored plans have
  hits = 0 and used <= 1; the header says "no hits (a hit stays a manual
  call)". PASS.
- **The bundle**: section 3 (renamed "TRANSFER PLANNER: THE XP_V2 NO-HIT
  DEFAULT, S8 AND THE BASELINE") calls `PLV.plan` first, then prints
  "below, information: S8's planner on own xP ..." and S8's own planner,
  baseline and named plans unchanged. On any exception it prints "the xp_v2
  planner: missing input: ..." (or "failed: <type>") and "the ruling's
  fallback (Ruling, Tue 20 Oct, point 1): S8's planner and the simple rule
  below, and the decision by hand", then S8's planner and the baseline;
  nothing substituted. The toy test exercises both paths (removing
  `hist/2025-26`). The other sections are untouched. Real run (read-only,
  `v8c/out/gw_pass/gw8_pass.txt`): section 3 prints the xp_v2 planner
  (default Branthwaite -> De Cuyper), the simple rule (Tarkowski -> Gabriel),
  the BB top 3, then S8's own planner. PASS.
- Two wording changes beyond the planner section, both consistent with the
  ruling and noted for the record: the bundle's first line now says "the
  transfer default from GW8 is the no-hit planner on xp_v2 (section 3, ...)"
  instead of "the baseline is the default where the planner differs" (the
  old line would have contradicted point 1), and the section title. The
  prereg said "The rest of the bundle is unchanged"; the sections' content
  is unchanged. Cosmetic: the top-5 table drops S8's "hits" column (always
  0 here) and the "£...m" price format; the prereg says "print in S8's
  format". Information only; no numbers affected.

## Caller's point 2: S15 amendment 2 as pinned

- `live_rule(d, weeks_xp, target, budget)`: `rule_candidates` (S15's port,
  unchanged) on the live export's players with the live xp_v2 matrix as the
  GK/DEF six-week sum, `played` from `fixtures_played` over the last four
  rounds exactly as the frozen `wildcard_candidates` computes it, then
  `rule_squad(cands, budget)` = the frozen `E.build_three_layer_squad(cands,
  budget, quota_split(budget), (4, 3, 3), QUOTA)` unchanged (`fpl_edge.py`
  has zero diff against origin/master). Budget = the live `E.selling_budget`
  (bank + selling prices); the rule's rows carry `all_players` prices
  (current), as pinned "at current prices". PASS.
- Independent check on the real export (my `v8c/verify_live.py`): the
  port's admitted sets per position equal the frozen `E.wildcard_candidates`'
  (19/71/80/19 players; the same three exclusion counts 200/92/187); MID and
  FWD order identical; GK and DEF order equals my own sum of the matrix over
  the fixture weeks; my own call of `E.build_three_layer_squad` on the
  port's candidates returns the same 15 and spend 87.2. The rule's objective
  on the builder's objective, by my own independent implementation
  (formations enumerated, captain, S7 bench weights 0.30/0.10/0.03 and 0.03):
  61.9817 for --freehit (decay 1.0) and 72.3907 for --bb (bench full),
  equal to the tool's. Builder 65.934 (my objective of the builder's 15:
  65.934); builder − rule +3.95; builder legal with the cap on; the cap
  costs 0.00. The --bb pair: 80.5416 vs 72.3907, +8.15. PASS.
- The rule as a start: `starts = [own 15] + [rule 15 if full]`, and
  `build()` keeps a start only when `legal(s, budget, gkdef_cap)` - so the
  rule is a start for the cap-on build only when legal with the cap on, as
  pinned. On GW8 the rule's squad has three ARS among GK+DEF (Raya, Gabriel,
  Calafiori), so it is not cap-legal and was a start for the cap-off build
  only; the invariant builder >= rule holds anyway (65.93 >= 61.98). A
  short squad is reported ("no full squad (n players passed its layers);
  nothing is substituted") and is not a start (tested). PASS.
- **The header line.** `--wildcard`/`--freehit`: "the default for Free Hit
  and Wildcard builds (Ruling, Tue 20 Oct, point 2; not used for GW8)";
  `--bb`: "information only (the ruling makes the builder the default for
  Free Hit and Wildcard only)". Point 2 of the ruling, verbatim: "S15:
  accepted if its verifier PASSes. tools/builder.py is the default for Free
  Hit and Wildcard builds, with the GK+DEF cap on live and its cost printed,
  and the three-layer rule's squad printed beside it. CHANGELOG entry. Not
  used for GW8." The header matches point 2 and does not go beyond it: it
  names exactly the two builds the ruling names, keeps "not used for GW8",
  and leaves --bb as information (the ruling does not name Bench Boost
  builds; the amendment's design keeps "--bb" in brackets). The acceptance
  is conditional on S15's verifier PASS, which `worklog/verify_S15.md`
  (b22ee1c) records.
- One basis note, as pinned, not a defect: the builder's market prices our
  own players at selling prices (budget = bank + selling), while the rule's
  rows are at current prices (prereg: "at current prices"), so the same
  player can show two prices (Calafiori 5.9 in the builder's table, 6.0 in
  the rule's; also Barry 5.6/5.7). Because selling <= current, a rule start
  is judged conservatively; if a rule start ever wins the local search, its
  unswapped own players would print at current prices and "spent" would be
  on that basis. On GW8 the rule start was not cap-legal, so the printed
  builder squad is on the selling basis throughout.

## Check 1: point-in-time (caller's point 3)

- **1b timestamp audit (decides): PASS.** Target GW8, deadline
  2026-10-23T17:30Z (fpl.sqlite events). Export
  `fpl_export_gw7_2026-10-19.json.gz`, generated 2026-10-19T22:05:17Z,
  gameweek 7 = target − 1 (`live_matrix` refuses otherwise). Odds snapshot
  `odds_2026-10-19T2205Z.json.gz`, taken 2026-10-19T22:05Z, the newest of
  the two in `odds/` (both 19 Oct, none after the deadline). The fallback
  model fits on `finished = 1` fixtures with kickoff < deadline: 60
  results, max kickoff 2026-10-12T19:00Z (GW6); 0 finished fixtures with
  kickoff >= the deadline. Export rows max round 7 (2158 rows);
  `fixtures_played` max event 6; `canonical_through(gameweek 7)`; priors
  from `historical/2025-26` (last season); `ict_live`, `chance_scale`,
  status gate from the same export. P(start) from the same export's
  `reliability_inputs`. Every input predates the deadline.
- **1a truncation (decides): PASS by identity.** There is one live origin
  (GW8); the data folder at e1154dd holds nothing dated after the deadline,
  so the rebuild from pre-deadline inputs is the tool's own path. My
  re-run reproduces the implementer's numbers exactly (below). The
  matrix's historical truncation was decided in S15's verification; this
  item calls `live_matrix` unchanged (held by `test_the_matrix_is_s15s...`).
- **1c shift probe:** not applicable (no correlation metric).

## Check 2: clean-checkout suites (caller's point 4)

`git archive` of 518f69e into `v8c/clean/` and of 79ae71b (the branch
before the first S8c commit) into `v8c/before/`; `ODDS_API_KEY` and
`FPL_DATA_DIR` removed from the environment; `python -m unittest discover
-p "test*.py"` (Python 3.14):

| run | result |
|---|---|
| before (79ae71b), bare | Ran 727 tests, OK (skipped=10) |
| after (518f69e), bare | Ran 756 tests, OK (skipped=10) |
| after (518f69e), FPL_DATA_DIR=C:\GIT\FPL-data | Ran 756 tests, OK (skipped=3) |

+29 = 5 (`tests/test_S8c.py`) + 3 new in `tests/test_S15.py` (12 → 15) + 21
(`tests/test_S2b.py`, from the merge of origin/master at 518f69e).

Hermetic: both files also pass from a foreign cwd (`v8c/hermetic/`, empty
before and after), with TZ=Asia/Tokyo, LANG=LC_ALL=C, HOME pointed at that
empty folder, FPL_DATA_DIR unset: test_S8c 5 OK, test_S15 15 OK. They read
only `tempfile` folders built by S6d's toy helpers, mock `selling_budget`,
and reference no `FPL-data`, `FPL_DATA_DIR`, `expanduser` or absolute path
(grep empty). PASS.

## Check 3: the implementer's numbers reproduced

My own runs from the s8c worktree at 518f69e (provenance `run.txt`: commit
518f69e..., modified tracked files 0; outputs `v8c/out/planner_live/
planner_live_gw8.txt` sha256 d049..., `v8c/out/builder_fh/
builder_freehit.txt` sha256 95e8...):

- `builder.py --freehit`: builder 65.93, without the cap 65.93, the cap
  costs 0.00; rule objective 61.98, spent 87.2; builder − rule +3.95 - the
  main session's numbers exactly (65.93 / 0.00 / 61.98 / 87.2 / +3.95).
- `planner_live.py`: bank 1.9; default Branthwaite -> De Cuyper (BHA, 5.2),
  score 4.17, gain 5.17, lost FT 1.00; the simple rule Tarkowski -> Gabriel
  (ARS, 7.9), score 2.88, week-t gain +2.18; BB top 3: Branthwaite -> De
  Cuyper 4.21 (+0.62), Tarkowski -> De Cuyper 4.01 (+0.57), Haaland ->
  Gonzalo 3.63 (+4.38).
- Independent recomputation (`v8c/verify_live.py`, my own XI optimiser,
  pool, legality, FT-value, BB value and ranking, with `rank_plans` not
  called): the same 326 plans (roll + every legal single swap over the top
  25 per position), max |score, lost, weekly gain| difference 3.6e-14, the
  same top-5 order, the same simple rule (+2.1783), the same BB top 3 (max
  score difference 4.7e-14) with weeks t+1.. and lost FT unchanged. Within
  1e-6: PASS. (Haaland is status 'd' in the export, so the gate gives him 0
  xP in every week; that is why a BB swap out of him shows +4.38 - the
  gate's rule, not a defect.)

## Check 5: recording path and runner isolation (caller's point 5)

`git diff origin/master 518f69e -- 'fpl_*.py' checks.py test_fpl.py .github
requirements*.txt`: 0 lines. The three item commits touch only
`tools/planner_live.py`, `tools/gw_pass.py`, `tools/builder.py`,
`tests/test_S8c.py`, `tests/test_S15.py`. The isolation test passes; my
stronger probe (import fpl_nightly, fpl_ship, fpl_edge, fpl_sync, fpl_gate,
fpl_publish, checks in the clean tree, then list every loaded module whose
`__file__` is under `tools/`) prints `[]`. Nothing in the item writes to the
projection log or the data folder: `git -C C:\GIT\FPL-data status` is clean
after my runs; the tools write only under `--out`. The recording path did
not move: PASS (no regeneration needed; the runner's code is byte-identical
to master).

## Check 6: mutations (caller's point 6), in `v8c/mut/` (restored after each; diff to clean empty)

| mutation | result |
|---|---|
| m1 planner_live: `hits_allowed=True` | RED (test_the_plans_are_s8s_with_no_hits_and_one_ft) |
| m2 planner_live: `FREE_TRANSFERS = 2` | RED (same) |
| m3 planner_live: BB value without the captain | RED (BenchBoost.test_by_hand) |
| m4 planner_live: the simple rule on `weeks_xp[1]` | RED (50e89dd's assertion) |
| m5 gw_pass: the fallback line dropped | RED (test_the_bundle_section_and_its_fallback) |
| m6 planner_live: every fixture's source printed as "odds" | survived |
| n1 builder: the rule at 100.0 instead of the live budget | RED (test_rule_keeps_to_the_live_budget) |
| n2 builder: the rule's squad not a start | RED (test_wildcard_freehit_bb) |
| n3 builder: builder − rule against the cap-off build | RED (test_the_difference_is_against_the_cap_on_build) |
| n4 builder: the rule's objective never bench-full (--bb) | survived |
| n5 builder: the rule sees no fixtures | RED (4 tests) |

At least two per item red (5 of 6 for S8c, 4 of 5 for S15 amendment 2):
PASS. The two survivors are coverage gaps of the toy, not defects of the
output, and both are verified correct on the real data above: m6 survives
because S6d's toy data has 3 fixtures, all priced by the snapshot, and no
later weeks (`live_matrix` sources on the toy: {('week t', 'odds'): 3}), so
the per-fixture source label cannot be told from a constant there; n4
survives because no test pins the rule's objective to the mode's
`bench_full` (the tests compare the printed line to `res["rule_value"]`,
which is self-referential). Suggested, not required: a toy fixture outside
the snapshot and a later week; an assertion `rule_value ==
B.objective(rule, weeks, decay, bench_full)` per mode.

## Check 7: secrets

grep over the five changed files and over my outputs (`planner_live_gw8.txt`,
`builder_freehit.txt`, `gw8_pass.txt`, the three `run.txt`) for
`apiKey=`, `Authorization`, `api_key`, `Bearer` and 32+ hex runs: nothing
but SHA-256 and commit hashes. None of the three tools reads `os.environ`
or opens a socket (grep for urllib/requests/http/socket/ODDS_API_KEY:
empty). The runs were made with `ODDS_API_KEY` removed from the
environment. PASS.

## Items' own acceptance tests (prereg "Tests and checks")

S8c: the matrix equals `builder.live_matrix` with every fixture's source
(yes, within the toy's limits above); the plans equal `rank_plans` with
hits off and k = 1 (yes, plus the call's arguments asserted); the simple
rule equals `baseline_plan` on week t (yes); the Bench Boost re-score by
hand (yes); no hit ever suggested (hits == 0 and used <= 1 asserted on
every scored plan); the bundle's section with and without the matrix (yes);
isolation (yes). S15 amendment 2: the rule a start, the line and its
difference against the cap-on build, 15 at 2/5/5/3 within the budget, a
tight budget, the short-squad path (yes, all five). The read-only live run
against the data folder at GW8 reproduced above. Remaining per the prereg
and for the main session: the report, the CHANGELOG entry (before Thu 22
Oct 11:30 UTC per point 1), the write guard.

## Decisions for the chat (none blocking)

1. Two toy-coverage gaps (m6, n4) - optional test additions.
2. The builder's live print mixes selling prices (builder's own players)
   and current prices (the rule's rows), as pinned; whether the rule's line
   should also say when its squad is not cap-legal (GW8: three ARS among
   GK+DEF) is a wording choice, not in the prereg.
3. The bundle's first line and section title were reworded for the ruling;
   the prereg's "rest of the bundle unchanged" holds for every section's
   content.

VERDICT: PASS - both preregs were committed before their code and are
unedited with the ruling verbatim; the planner is S8's `rank_plans`
unchanged on S15's `live_matrix` unchanged with k = 1, no hits, decay 0.85
and Boris's schedule, the simple rule and the Bench Boost re-score as
pinned, the bundle prints it as the default with the ruling's fallback and
nothing substituted; the rule's squad comes from the frozen
`build_three_layer_squad` on the frozen candidates with the live matrix
and budget, and the header matches point 2 without going beyond it; every
input predates the GW8 deadline; the clean suites pass 727 -> 756 bare and
with the data folder, the item's tests are hermetic; my independent
recomputation matches the tool to 1e-13 and the implementer's live numbers
exactly; the runner path is byte-identical to master and imports nothing
under tools/; 9 of 11 mutations red (the two survivors are toy-coverage
gaps verified correct on the real data); no secrets.
