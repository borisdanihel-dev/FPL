# Session state — the one session (C:\GIT\FPL)

The lanes merged on 19 Oct (RULING S6b acceptance + lanes merge, verbatim in
`prereg/S6b.md` on `lane-b`): one session in `C:\GIT\FPL` does runner and
offline work, and this is the one state file. Lane B's handover is the top
of `worklog/SESSION_STATE_B.md` on `origin/lane-b`. Updated at the end of
every item, before the push. A fresh session reads `CLAUDE.md`,
`BUILD_PLAN.md` and this file, then waits for the next instruction.

- **NOW (20 Oct, 14:45 UTC on): "Ruling, Tue 20 Oct night"** (verbatim in
  `prereg/S8c.md` amendment 3, `prereg/W3.md` amendment 2, `prereg/S2b.md`,
  master `6e7c918`, and the scratchpad `ruling_20oct_night.txt`). The
  item count reset to 0 of 6.
  - **Point 1 done:** S2b's after-report is corrected, with an amending
    CHANGELOG entry (master `8df892a`).
  - **Point 2:** "appended last in the table" is confirmed.
  - **Point 3, s8c-wip** (`ea95cf6`, pushed):
    - the bundle also writes `xp_v2_all.csv`: every export player, those
      not forecast at 0 with "not forecast" (the design choice, open for
      Boris);
    - the print is byte-identical with and without the CSV;
    - mutations 8 of 8; suite 764 → 767 bare;
    - GW8 run: 668 rows, Haaland "not forecast".
    - Verifier running.
    - **The new head is Thursday's bundle commit** once it passes (due
      Thu 14:00 UTC).
  - **Points 3–4, w3-wip** (`bbe770a`, pushed):
    - REALISED reads the CSV at the newest commit whose committer time and
      `run.txt` end are both before the deadline, with the SHA-256 as
      `run.txt` records it;
    - our actual GW8 15; `realised_on` for both models; one of the 15
      missing gives "not recorded";
    - mutations 8 of 8; the real CSV reads end to end.
    - Suite and verifier running.
  - **Next (Wednesday):** W1b (tell Boris the dry-run time, before 21:00
    UTC), then Step 16's prereg.

- (Earlier) **NOW (20 Oct, 13:45 UTC on): "Ruling, Tue 20 Oct evening"** (verbatim
  in `prereg/S8c.md` amendment 2, `prereg/S2b.md`, `prereg/W3.md`
  amendment 1, and the scratchpad `ruling_20oct_evening.txt`).
  - **Point 1:** `s8c-wip` `71c9d17` stays the bundle commit; the
    sorted-clubs test is added at the Sun 25 Oct landing.
  - **Point 2:** the S2b after-measurement verifier: **WARN**
    (`worklog/verify_S2b_after.md`, master `f9dc78c`). Its four report
    defects are not corrected yet: they wait for Boris (an amending
    CHANGELOG line, report corrections):
    - the P(above) range −0.069, not −0.067;
    - the fetch-time end 13:01:33;
    - the xG/xA/ruleset cells not listed;
    - S6d's live forecast missing from the list (20 of the top 25 move,
      max 0.03).
  - **W3 amendment 1** (prereg master `0596125`; `w3-wip` `d3ea9c6` takes
    master, then `aea1f42`, pushed):
    - `fixtures.finished_provisional` is appended last;
    - BAN RISK counts provisional results, labelled;
    - REALISED grades GW8's xp_v2 from the bundle's pre-deadline commit
      (git history; the nightly checkout gains `fetch-depth: 0`), only if
      the bundle's 15 is our GW8 15.
    - Mutations 14 of 15 red; the survivor is equivalent.
    - Suite 737 → 748 bare.
    - On the real data copy: BAN RISK lists Thiago (4 cautions, P(ban)
      0.444).
    - **Verifier PASS** (`worklog/verify_W3_a1.md`): the frozen-clock log
      is byte-identical, and 10 of its 10 mutations went red.
    - Report and CHANGELOG are on `w3-wip` `191b0b0`. The merge is by Thu
      29 Oct via `dry/W3`.
    - Open: the "CSV" reading; the 15-equality guard (Friday's refresh
      after Boris's transfer); committer time as "timestamped".
  - **F-I (1) done:** the disclaimer was read (a liability text, no
    restriction). The 20 files are fetched, read with `python -I`, and
    placed read-only under `historical/football-data/`. The record is
    `worklog/downloads_2026-10-20.md` on `fi-wip` `aab64bf`; verifier PASS
    (`worklog/verify_F-I_downloads.md`, `fi-wip` `eceae17`).
  - **Item count: 6 of 6** since "Ruling, Tue 20 Oct": S2b, S8b, S8c, S8c
    amendment 1, W3 amendment 1, F-I downloads.
    - Step 16's prereg (parts 3–4) and W1b (Wednesday) wait for a chat
      review.
    - Step 16 needs decisions the plan leaves open: the bracket model,
      the blank and double rules, and the 2024/25–2025/26 European
      calendars for the backtest.

- (Earlier) **NOW (20 Oct, 13:00 UTC on): "Ruling, Tue 20 Oct afternoon"**
  (verbatim in `prereg/S8c.md` amendment 1, master `9ed7919`, and the
  scratchpad `ruling_20oct_afternoon.txt`).
  - **Points:**
    1. Thursday's bundle and Friday's refresh run from `s8c-wip`'s final
       commit. The output goes to master under `worklog/gw_pass/gw8/`
       before the deadline, with that commit in `run.txt`. `s8c-wip` lands
       Sun 25 Oct, dry run first.
    2. Tests for the two verifier gaps;
    3. the cap flag on every printed squad or move. Points 2 and 3 are due
       Wed 21 Oct 20:00 UTC.
    4. The S8b and S15 CHANGELOG entries go on master (done, `684cd3f`).
  - **Then:** W1b Wednesday, W3 (points 2, 3, 5), then F-I.
  - **Done:**
    - the real nightly dispatch (Boris, 12:59 UTC): data `63e6a44`, STATUS
      OK 29/29, 73 calls. S2b's after-measurement is in
      `worklog/cc_2026-10-20_S2b_after.md`, and the "S2b done" CHANGELOG
      entry is on master `f61d267`.
    - S8c amendment 1 code `52b2a65` on `s8c-wip` (pushed): new
      `tools/capflag.py`; flags in planner_live, S8's planner, the bundle
      and builder; the two gap tests; mutations 19 of 19. GW8 read-only:
      only the rule's line is flagged (ARS 3).
    - **S8c amendment 1 done:** suite 756 → 764, bare and with the data.
      Verifier PASS (`worklog/verify_S8c_a1.md`, Fable 5.1); 15 of its 16
      mutations went red, and the survivor is a sort-order coverage note.
      Report and CHANGELOG are on `s8c-wip` **`71c9d17`, the final commit
      for Thursday's bundle**.
  - **Item count since "Ruling, Tue 20 Oct":** 4 of 6 (S2b, S8b, S8c with
    S15 amendment 2, S8c amendment 1).
  - **Open for Boris:**
    - a post-dispatch verifier for S2b?
    - a sort-order test for the cap flag?
  - **Next:** W1b on Wednesday 21 Oct, on Boris's word.
  - **Thursday (bundle):** from the s8c worktree at the final commit:
    `git -C C:\GIT\FPL-data pull --ff-only`, `--restore`, then
    `python tools/gw_pass.py --out <dir>`. Copy the output and `run.txt` to
    master `worklog/gw_pass/gw8/` and commit (worklog only) before Fri
    17:30 UTC.

- (Earlier) **NOW (20 Oct, 11:00 UTC on): "Ruling, Tue 20 Oct"** (verbatim in
  `prereg/S8c.md` and the scratchpad `ruling_20oct.txt`). The item count
  reset to 0 of 6.
  - **Order:**
    - a. the landing and S2b today, the real run before 21:00 UTC;
    - b. report S8b's and S15's verifiers at once;
    - c. push `s17-wip`;
    - d. the live planner for the bundle by Thu 14:00 UTC;
    - e. W1b Wednesday;
    - f. W3 points 2, 3 and 5;
    - g. the F-I downloads, then Step 16 parts 3–4 and Step 18.
  - **Rules:** no runner pushes from Thu 22 Oct 11:30 UTC to the GW8
    deadline; no merges without Boris; stop at 6.
  - **Done:**
    - Boris's dry runs were green at 10:52 and 10:56 UTC: landing at
      `4f1c240`, s2b-wip at `a00ccc7`. The S2b dry run: WARN 28/29 (only
      ODDS SKIPPED in the dry run); check 22 equal for 42 entry-gameweeks.
    - **Landed:** master fast-forwarded to `8d0a50b` (the landing branch
      + master's docs); tag `pre-landing2` at `ce51207`; suite 687 OK,
      bare and runner-like.
    - `s17-wip` pushed (`90b62d4`; the earlier push had failed).
    - **S15 verifier PASS** → accepted (point 2); `s15-wip` `b22ee1c` with
      report and CHANGELOG.
    - **S15 amendment 2** (prereg master `5c90e08`): the rule's squad
      beside the builder's in live, on `s8c-wip` `615b35b`; mutations 6
      of 6. The header now names the acceptance (`--bb` stays
      information), which is a decision for the chat. Live GW8 `--freehit`:
      builder 65.93, rule 61.98 (spent 87.2), +3.95.
    - **S8c (point 1, the live planner)** built on `s8c-wip` (`7773a58`,
      `50e89dd`; prereg master `de8ca68`). It has the GW8 bundle section;
      mutations 11 of 11. Read-only live run on GW8: default Branthwaite →
      De Cuyper; simple rule Tarkowski → Gabriel. `s8c-wip` `518f69e`
      takes master `ce357fb`.
    - **S2b verifier PASS** on the dry run and the delta
      (`worklog/verify_S2b.md`, `s2b-wip` `434df0b`). Tag `pre-S2b` =
      `5c90e08`. **Merged:** master `ce357fb`; suite 708 OK, bare and with
      the data. Pushed 11:45 UTC. The untracked `verify_S2b_pre.md` (an
      older draft) was moved to the scratchpad `aside/`.
    - **S8b verifier PASS** → accepted (point 1): `s8b-wip` `cfa7a36` with
      report, verifier file and CHANGELOG. +19.58 [+1.28, +38.70].
      Reported to Boris 11:50 UTC. Open: land the S8b and S15 CHANGELOG
      entries on master before Thu 11:30 UTC?
    - **S8c done** (with S15 amendment 2): verifier PASS
      (`worklog/verify_S8c.md`, Fable 5.1); `s8c-wip` `ca96b6a` with report
      and CHANGELOG; suite 727 → 756, bare and with the data. Ready for
      Thursday's bundle. Open: run the bundle from `s8c-wip`, or land it
      before Thu 11:30 UTC (a dry run, because the nightly runs `tests/`)?
      Also open: tests for the verifier's two survivors, and whether to
      print when the rule's squad is not cap-legal.
  - **In progress:**
    - **waiting on Boris:** the real nightly dispatch of master `ce357fb`
      before 21:00 UTC. It is the first real re-fetch of GW1-6 (expect 73
      calls). After it: `s2b_measure.py` (copied to the scratchpad) on
      `e1154dd` against the new data commit, then the CHANGELOG entry
      "S2b done".

- (Earlier) **NOW (20 Oct morning on): the night ruling ("Ruling, Mon 19 Oct",
  verbatim in `prereg/S6e2.md` amendment 1, `prereg/S8b.md`,
  `prereg/S15.md`, `prereg/S17.md`, and the scratchpad
  `ruling_19oct_night.txt`).** The item count reset to 0 of 6.
  - Order: the S6e2 fix → F-F → F-G → F-H → F-I (a proposal doc only).
  - Branches only. On master only preregs and this file, plus F-L in
    BUILD_PLAN, as ruled. No merges, landings or dispatch requests.
  - Points 1–3 (W3) are recorded, but their code has not started:
    - point 2: GW8 graded from the bundle file if its commit is before the
      deadline;
    - point 3: ban risk counts `finished_provisional` fixtures, labelled.
    W3 needs both before its merge (by Thu 29 Oct), and Thursday's bundle
    must carry own + xp_v2 for all 15 plus the captain table.
  - **Items:**
    1. **S6e2 DONE** (`s6e2-wip` `d87f8aa`): fix re-verified PASS; the FAIL
       stands; the keeper-saves line closed.
    2. **S8b (F-F)** (`s8b-wip` `7580cf2`): **PASS**. Planner (no hits)
       − baseline +19.58 per squad-season [+1.28, +38.70]; 2024/25, a 4 h
       10 min run. Mutations 13 of 14 (b2 equivalent). Verifier running.
    3. **S15 (F-G)** (`s15-wip` `91f401d`): **PASS**. Builder − rule
       +33.31 window points per date [+25.29, +41.54]; ≥ the rule on
       0.78 of dates; projected ≥ on every date; 68 dates. The first run
       crashed on 2024/25's AM rows (fixed before any result). Mutations
       18 of 18. Verifier running.
    4. **S17 (F-H) DONE** (`s17-wip` `90b62d4`): Brier skill +0.084
       [−0.022, +0.169] → PASS on the point estimate (bar ≥ 0.05). GW20
       −0.075, GW26 +0.241, GW32 +0.209; overconfident deciles. Verifier
       PASS (Fable 5.1); its 3 survivors closed. Information only;
       adoption needs Boris.
    - W3 point 3 needs `finished_provisional`, which the sync does not
      store: a fixtures migration in W3.
    5. **F-I proposal** on `fi-wip` (`worklog/proposal_F-I_sources.md`):
       nothing downloaded; three questions for Boris in it.
  - F-L is recorded in BUILD_PLAN Part F (`6ae5923`).
  - Nightly 21:40 UTC 19 Oct: STATUS OK 28/28; 614 tests; own 281,
    xg/minutes/bottomup 261, fpl_ep 668; odds 20 events, 484 credits.
  - Tuesday dry runs: not clicked as of 07:10 UTC; the last data-dryrun
    commit is 19 Oct 10:58.

- (Earlier) **NOW (19 Oct evening on): RULING 19 Oct evening.** It is verbatim in
  `prereg/W2.md` (amendment 2), `prereg/W3.md` and `prereg/S6f.md`, and in
  the scratchpad `ruling_19oct_evening.txt`. The item count restarted at 0.
  - Tonight, in order: F-B (W3) off `w2-wip`, then F-D (S6f), then S6e2,
    then F-F and F-G as far as the harness allows. No merges or landings.
    Park anything that needs Boris here, with the exact question.
  - Tuesday after 00:00 UTC Boris clicks the dry runs of
    `landing-2026-10-19b` and `s2b-wip`.
  - Items since the review: W2a2 (1), W3 (2), S6f (3). Stop after 6.
  - **W2 amendment 2 DONE** on `w2-wip` `eb9a143`: any exception inside a
    section ends SKIPPED with check 31's WARN; verifier PASS (Fable 5.1).
    The flag rule stays event 2.
  - **W3 (F-B) DONE** on `w3-wip` `5e8105d` (verifier PASS, Fable 5.1;
    its surviving mutation closed in `3fe1076`). The parked questions
    below hold, plus: "BAN RISK follows S12's rule (cautions in fixtures
    FPL has marked finished); tonight GW7 is still finished = 0, so
    Thiago's 4th caution is not counted. Count kicked-off fixtures
    (provisional) instead, or keep S12's rule?" Thiago IS on 4 cautions
    (GW4-7): a GW8 booking bans him for GW9.
    (Built on `w3-wip` `09b3a50`, off `w2-wip` + the landing; prereg
    master `ccb5882`.)
    - xp_v2 is the seventh source, from an AST port of xp_v2_live's
      closure, with the S11 prior in the committed
      `priors/s11_prior_2025-26.json` (`tools/make_prior.py`) and the
      export carrying code, first_name and second_name.
    - New sections: CAPTAIN, BAN RISK and REALISED.
    - Real GW8: identical to the tool (285 players); the six other sources
      are unchanged.
    - Suite 699 → 716; mutations 19 of 19.
    - **Parked for Boris (W3, before its merge):** "The runner has no
      historical/ folder and its record never opens the database, so last
      season's S11 prior travels as priors/s11_prior_2025-26.json (109 KB,
      derived from vaastav 2025/26, SHA-256s recorded), and the export
      gains code, first_name and second_name. OK to merge it this way?"
      Also: "GW8's xp_v2 is not in the log (W3 merges after GW8): grade
      GW8's xp_v2 from the bundle file worklog/gw_pass/gw8/ (labelled), or
      leave it 'not recorded'?"
  - **S6f (F-D) BUILT, the test FAILS its bar** on `s6f-wip` `483a8a6`
    (prereg master `3c955b5`); verifier running.
    - 2024/25 GW5-38, DEFCON removed on both sides: xp_v2 − own_rebuilt
      −0.396 per squad per gameweek [−0.864, +0.045] (season −13.5).
    - S6b's xp_v2 − own_proxy +0.357 [+0.177, +0.548]; own_rebuilt −
      own_proxy +0.754.
    - Per F-D, this does not revert GW8+ by itself; it goes to the chat,
      and the GW10 revert rule governs.
    - **Parked for Boris:** "S6f fails on 2024/25 (xp_v2 below own_rebuilt
      by 0.40 a squad-gameweek, CI [−0.86, +0.05]) while S6c passed the
      switch on 2025/26. GW8 stays on xp_v2 as ruled unless you say
      otherwise; the GW10 revert rule decides."
  - **S6f DONE** on `s6f-wip` `0b16969`: verifier PASS (Fable 5.1); its
    own loop reproduced the primary within 1e-6. Correction in the report:
    own_proxy (secondary only) keeps a logistic DEFCON floor with count 0
    (secondary +0.357 with, +0.373 without); the primary's sides are
    exactly 0.
  - **STOPPED: S6e2's verifier WARNs** (`s6e2-wip` `7f0b148`, verify file
    committed, nothing else changed). Every reported number stands (the
    run's mu ≤ 8.43; FAIL reproduced independently), but
    `floor_points` can loop forever for some mu ≥ 12.765. **Parked for
    Boris:** "Fix floor_points (stop when the pmf has underflowed or bound
    j; tests at mu 120 and 12.765), re-verify, and then file S6e2's report
    and CHANGELOG? The recorded FAIL does not change." The report draft is
    the scratchpad `cc_2026-10-19_S6e2.md`.
  - **S6e2 BUILT, the test FAILS its bar** on `s6e2-wip` `d80644c`
    (prereg master `f485223`; off `s6f-wip` + `s6e-wip`).
    - 2024/25 keeper points (xp_v2 + Σ E[floor(S/3)] − xp_v2): +0.024
      [−0.016, +0.066]; MAE +0.305 (worse).
    - Choice differs 0.05; E[floor(S/3)] 0.767 v E[S]/3 1.100.
    - Not adopted.
  - **F-F (S8b) and F-G (Step 15) PARKED for Boris, the exact question:**
    "Both need xp_v2 for gameweeks t+1..t+5 at origin t; S6b's replay and
    the live forecast define only the next gameweek. Everything carries
    over except the fixture lambda: football-data's prices are pre-closing,
    so for weeks after t they were not known at the origin. Proposed: the
    odds-implied lambda for week t (as S6b), and the fallback fitted on
    results before the origin for t+1..t+5. Live, that is the Odds API
    snapshot where it prices the fixture, else the fallback. OK, or the
    fallback for all six weeks?" Neither is started.
  - Items since the review: W2a2, W3, S6f, S6e2 = 4 of 6.

- (Earlier) **NOW (19 Oct, 16:00 UTC on): W2, then Part F, overnight** (Boris, verbatim):

  > 2. Start W2 now on its own branch off master, as prereg/W2.md lays out; it merges Saturday 24 Oct after the GW8 deadline, outside 9d. Stop W2 at a clean point when Tuesday's S2b and landing work is due (after 00:00 UTC, once Boris has clicked the dry runs).
  > 3. If W2 is done before then: continue with Part F in order (F-C and F-D are offline, so they may run before F-B; F-B builds on W2 and must merge by Thu 29 Oct). Overnight, park anything that needs Boris in the state file with the exact question and move to the next item; no merges or landings without him.

  Verifier rule until the Fable reset, Tue 20 Oct 08:00 Prague (Boris,
  verbatim): "keep running the verifier on Fable past 80%, up to its limit;
  if a Fable run is refused for the usage limit, fall back to Opus at xhigh
  and say so in the report. After the reset, the normal rule returns (Fable
  unless the weekly bar is above 80%)."

  Point 1 of the same message ("your reading stands, every other XI player
  within 0.3 xP of the captain") is in `prereg/S14.md`.

  **W2 progress** (`w2-wip` off master `6a94467`, worked in the scratch
  worktree `<session scratchpad>/w2`; scripts in the scratchpad:
  `patch_w2a.py`, `make_fpl_lambda.py`, `patch_w2b*.py`, `check_w2a.py`,
  `check_w2b.py`):
  - **(a) done** `4d48697`: `fetched_at_utc` on transfers, chips,
    standings and player_history; `players.code`; `standings.label_error`
    flags the seven event-2 rows (total off the GW2 `entry_gw` chain), kept
    byte for byte; the export skips `label_error = 1`. On a copy of the
    real database: 7 flagged, 42 kept, the export identical to master's.
    The positional inserts became named-column inserts.
  - **(b) done** `aa5352a`: `fpl_lambda.py` (S5's live functions copied by
    AST from `tools/odds_lambda.py`; the fallback's results come from the
    export, so the record never opens the database); `record_status`
    source `bottomup_lambda`; no snapshot → RECORD SKIP (WARN in check 29).
    `SOURCES` gain it in `fpl_nightly.py` and `checks.py`; test_W1, test_S3
    and test_fpl learn the sixth source. Real data: identical to the tool for
    264 players; the five other sources identical to master.
  - **(c) done** `451ade6` (+ test `109e58a`): `fpl_chips.py`,
    `fpl_league.py`, `fpl_bt.py` and `fpl_pit.py` (the AST closure of the
    tools, verbatim, aliases kept; scratchpad `make_sections.py`);
    `fpl_sections.py` appends CHIPS and LEAGUE to the night's report;
    `<SECTION> SKIPPED:` and `SECTIONS FAILED` are WARNs in the new check
    31, never a red night. Real data: identical to the tools (37 and 69
    lines).
  - Suite 614 → 625 bare. A runner-like run (`FPL_DATA_DIR`) was in
    progress; stand-in zones not run (no zone data on this PC; the dry
    run's Linux image covers it). Mutations 17 of 17. Verifier on Fable
    running at about 17:00 UTC; then the report
    `worklog/cc_2026-10-19_W2.md` and CHANGELOG (with the label_error note)
    on `w2-wip`.
  - **Dry run:** after W1b is live, push `dry/W2` (allowed in the GW8
    freeze, RULING 19 Oct afternoon point 3); else Boris's manual dispatch.
  - **W2 DONE on `w2-wip` `d0ac3f5`** (about 17:30 UTC): verifier PASS
    (Fable 5.1, `worklog/verify_W2.md` on the branch); suite 625 bare and
    625 runner-like; report `worklog/cc_2026-10-19_W2.md` and CHANGELOG on
    the branch. Its notes: the standings flag rule must stay limited to
    event 2 (other events' snapshots differ by 2–11 points too, worth an S9
    look). Not merged: Saturday after the GW8 deadline, after a dry run.
    Before merging, `w2-wip` takes master (S2b, W1b, the landing; expect
    conflicts in `fpl_sync.py`, `checks.py`, `test_fpl.py`, `tests/`). Tag
    `pre-W2`, merge, Boris's real dispatch.
  - **Items since the last chat review** (Boris's W2 + Part F message):
    W2 = 1 of 6.
  - **S10b DONE** on `s10b-wip` `a454e09` (verifier PASS, Fable 5.1;
    report `worklog/cc_2026-10-19_S10b.md` and CHANGELOG on the branch;
    suite 692). Not landed: it rides with a later landing (offline; tests/
    changes need a green dry run). Items since the last chat review: W2,
    S10b = 2 of 6.
  - **F-D (S6f) PARKED for Boris, the exact question:** "2023/24 and
    2024/25 have no defensive-action counts, so DEFCON is missing both in
    the models' inputs (bottomup's defcon90 and xp_v2's DEFCON hit rate read
    0) and in the outcomes (the 2026/27 re-score's DEFCON points are 0,
    flagged). F-D compares xp_v2 with own_rebuilt on those outcomes. Run it
    with DEFCON missing on both sides (stated as a limitation), or score the
    outcomes without the DEFCON category at all, or wait for a source of the
    counts?" Without an answer, F-D is not started; F-E goes first.
  - **F-E (S6e) built** on `s6e-wip` (off the landing branch + master;
    prereg master `16f6605`; code `87f6282`; scratch worktree `s6e`).
    2025/26 test **FAIL** on its bar: keeper points xp_v2 + saves − xp_v2
    −0.101 [−0.197, −0.007] per squad per gameweek (season −3.4); keeper
    MAE +0.393 [+0.340, +0.444] (worse); the choice differs in 0.13 of
    squad-gameweeks; k from 2024/25 split-half. For the chat (not tuned):
    the ruled E[saves]/3 overstates E[floor(saves/3)], which may explain
    part of the MAE rise. Not adopted. 2024/25 run not done (needs the
    harness generalised; shared with the parked F-D).
  - **S6e DONE** on `s6e-wip` `85f288b` (about 18:10 UTC): verifier PASS
    (Fable 5.1, `worklog/verify_S6e.md`): the item is done correctly and
    the model's FAIL is recorded. 12 of the verifier's 19 mutations went
    red; the 7 survivors were test gaps, and three are closed in `e08660e`
    (tests only; my mutations 6 of 6). Suite 692. Report
    `worklog/cc_2026-10-19_S6e.md` and CHANGELOG on the branch. Not
    landed: offline, with s10b-wip in a later landing (tests/ changes need
    a green dry run). Items since the last chat review: W2, S10b, S6e = 3
    of 6.
  - **STOPPED after S6e** (Part F: "Stop on a FAIL"). Open for Boris:
    (1) the F-D question above; (2) S6e: should a discretised term,
    E[floor(saves/3)] from a Poisson on E[saves], get its own
    pre-registered test at the GW10 checkpoint? (3) Next if he says go:
    F-F (S8b) and F-G (Step 15) both test 2024/25, so they need the same
    harness generalisation as F-D and F-E's 2024/25 run; F-B (W3) can be
    built on `w2-wip` now and merged by Thu 29 Oct.
  - **F-C / S10b built** on `s10b-wip` (scratch worktree `s10b`; prereg
    master `c0116fe`; downloads `5918f02` with the record
    `worklog/downloads_2026-10-19b.md`; landing merged `4ddea35`; code
    `a2902f9`). Reproduction PASS: 2023-24 11,086 of 11,086, 2024-25
    11,431 of 11,431 (exact). Neither season had a goalkeeper goal, so the GK
    goal value is untested. Re-scores in `tools/out/rules_<season>/` (28,742
    and 26,919 rows; DEFCON missing, flagged). 2025/26 path byte-identical to
    Step 10. Mutations 8 of 8. Still to do: the full suite, the verifier
    (Fable), the report `cc_2026-10-19_S10b.md`, CHANGELOG, push. Then
    F-D (S6f).
  - (Earlier plan) **Part F, F-C first** (Step 10b, offline): prereg
    `prereg/S10b.md` with F-C's text verbatim. The downloads are approved
    in F-C (record the URL, fetch time and SHA-256; data only; read with
    `python -I`): vaastav `data/2022-23`, `2023-24`, `2024-25`
    (`merged_gw.csv`, `fixtures.csv`, `teams.csv`, `players_raw.csv`) and
    football-data E0 2023-24 and 2024-25. Then F-D (S6f), F-E (S6e), then
    F-B (W3, merge by Thu 29 Oct).
  - Then: mutations for all three pieces, the full suite four ways (bare,
    runner-like, stand-in zones, hermetic), a frozen-clock regeneration,
    the verifier, the report, CHANGELOG (with the label_error note). No
    merge: Saturday after the deadline, after `w2-wip` takes master with
    S2b and W1b (expect conflicts in `fpl_sync.py`, `checks.py`,
    `test_fpl.py` and tests with S2b's changes).
  Before the landing: merge master into `landing-2026-10-19b` (docs only
  since its verification) so master can fast-forward.

- **CURRENT (19 Oct, about 16:00 UTC), after RULING S14 (Boris accepts) + Part F:**
  - S14 accepted as information (`prereg/S14.md`, master `677f34e`): the
    captain table prints in the GW8 bundle; the captain rule is unchanged;
    the table is shown beside any options within 0.3 xP, with no
    tie-break. GW10 items: the thin 15+ tail and keepers near zero
    (saves).
  - **S14 amendment 1** (prereg `3de32ff`, code `282f7e4` on the landing
    branch): section 7 lists the options within 0.3 xP of xp_v2's captain
    (today Saka 6.00, option Calafiori 5.83). Mutations 6 of 6; verifier
    PASS (Fable 5.1); suite 687; records `354cfe0`. Landing branch tip
    after this file: lane B's items, S6c, S6d, S14 and amendment 1, for
    Tuesday's dry run.
  - **RULINGS PART F** are verbatim in BUILD_PLAN.md "Part F - queued
    rulings". Each item's text goes verbatim into its prereg before its
    code. Order after the GW8 queue: F-B (W3, merge by Thu 29 Oct), F-C,
    F-D, F-E, F-F, F-G, F-H, F-I; F-J at the GW10 checkpoint (about 9 Nov);
    F-K parked.
  - **F-A, effective now:** 12 dry runs per UTC day, manual and
    push-triggered together. The text is in `prereg/W1b.md`; W1b's cap
    constant goes to 12 when W1b is worked on Wednesday.
- **Earlier (19 Oct, about 15:30 UTC), after RULING 19 Oct afternoon:**
  - The ruling is verbatim in `prereg/S14.md`, `W2.md`, `S16.md`, `S2.md`,
    `S2b.md` (master `fc56fd5`) and `S6c.md` and `S6d.md` (landing branch
    `5fda195`). BUILD_PLAN Step 20 holds the GW10 item "xp_v2 + saves". The
    lane-B handover note now says 2025/26 priors.
  - Point 6, done (landing branch `aac4b66`, reports and CHANGELOG): the
    GW5–7 retro uses the actual post-wildcard 15, official points (sums
    equal `entry_gw`: GW5 60, GW6 49) and no autosubs, by FPL or the rule.
    The gap is selection: GW6 own 59 (Verbruggen +7, Thomas +2, Tarkowski
    captain +1), xp_v2 61 (+ Rudoni +3); GW5 both 54. GW6
    `points_on_bench` 11 v 22 flagged for S2b.
  - **S14 done** on `s14-wip` (prereg rows master `15e18fa`, code
    `0def550`, report `4aab84d`): `tools/points_pmf.py`, bundle section 7
    (captain table). Test PASS on both conditions: Brier +0.00118 [+0.00070,
    +0.00178]; 10+ hauls 403.6 predicted v 449 (−10.1%). Thin tails: 15+
    predicted 47 v 75. Verifier PASS (Fable 5.1); suite 676 → 686;
    mutations 18 of 18. Information only until Boris accepts.
  - **Landing 2** (`landing-2026-10-19b`, tip `3ea0459` plus this file):
    lane B's items, S6c, S6d, S14, the provenance line, the
    reconciliation; 686 tests. **Tuesday after 00:00 UTC:** Boris's
    dry-run click on it and on `s2b-wip`; on green and outside 9d,
    fast-forward master to the landing branch, then merge master into
    `s2b-wip` and `w1b-wip`.
  - **Items since the last chat review** (RULING 19 Oct afternoon): S14 =
    1 of 6.
  - **Scratch worktrees left:** `landing` and `s2b` in the session
    scratchpad (the branches are pushed).
  - **Next by queue:** S2b Tuesday (dry run, merge before 21:00 UTC,
    Boris's real dispatch, after-measurement incl. GW6
    `points_on_bench`); W1b Wednesday; the GW8 bundle Thursday about 18:00
    Prague and Friday morning (`worklog/gw_pass/gw8/`); W2 in the gaps
    (dry/W2 pushes allowed in the freeze, point 3).
  - Dry runs move to Tuesday after 00:00 UTC (point 5): the landing branch
    and `s2b-wip`.
- **Earlier (19 Oct, about 13:30 UTC):**
  - **S6c done** on `s6c-wip` (`d662656` prereg, `11c262c` + `28d0578`
    code, `247edb9` report): xp_v2 − own_rebuilt +0.515 [+0.213, +0.816]
    per squad per gameweek → **GW8 SWITCH STANDS**; verifier PASS (Fable
    5.1); suite 652 → 660. Report `worklog/cc_2026-10-19_S6c.md`.
  - **S6d (queue item 2) done** on `s6d-wip` (prereg `9fa7ab1`, code
    `4d2d1c7` + `a1595e4`, test gap `822d324`, report `6c0feef`; S6c
    merged in `c98487b`): `tools/xp_v2_live.py` (xp_v2 as tested live; its
    core equals S6b's `Replay.xp_v2` exactly on 2025/26), the bundle's
    section 5 (own v xp_v2 as tested, the default from GW8; own picks GW8
    when it is missing) and the keepers' xp_v2, the GW5–7 live column (GW5
    +0, GW6 +2). Verifier PASS (Fable 5.1); suite 660 → 667; mutations 15
    of 16 red, 1 equivalent. Report `worklog/cc_2026-10-19_S6d.md` (on the
    branch until the landing).
  - **S2b step 1 done early:** master merged into `s2b-wip` (`0d94be9`,
    clean, 635 tests OK). Tuesday: the dry run (Boris), then the rest.
  - **Items since the last chat review:** S6c, S6d = 2 of 6.
  - **Landing 2 ready:** `landing-2026-10-19b` = master + `s6d-wip` (lane
    B's S8, S11, S12, S13, S6b, the bundle, provenance; S6c; S6d) + the
    CLAUDE.md provenance line + SESSION_STATE_B.md marked closed; 676 tests
    OK; provenance check in `worklog/cc_2026-10-19_landing2.md` (on the
    branch). Needs Boris's dry-run click; on green and outside 9d (never
    21:00 UTC to the end of the nightly; the GW8 window opens Thu 22 Oct
    11:30 UTC) fast-forward master to it. Until then master takes only
    this file, merged into the landing branch at once (docs only).
  - **Scratch worktrees (superseded, see CURRENT)** (session scratchpad, registered in this repo):
    `s6d` (s6d-wip), `s2b` (s2b-wip at `0d94be9`), `landing`
    (landing-2026-10-19b). A fresh session can remove them with `git
    worktree remove`; the branches are pushed.
  - **Waiting on the chat:** Step 14's mean-match question
    (`prereg/S14.md`); the live prior season (S6d report, decision 1).
  - **Open for the chat:** (1) S6d's prior season: 2025/26 for the live
    forecast (BUILD_PLAN Step 11, "priors come from last season"); lane
    B's handover named 2024/25. (2) Step 14: xp_v2 has no saves term and
    no goals-conceded term in its xg half, so a PMF with saves at their
    measured rate cannot match xp_v2's mean within 0.05 for keepers;
    question in the S6d report.
  - **Next:** the landing branch (lane-b items + `s6c-wip` + `s6d-wip` +
    the CLAUDE.md provenance line) needs one dry run (it changes `tests/`):
    Boris's click, Tuesday with S2b's or Wednesday's; land before Thursday
    11:30 UTC.
- **Merged session, 19 Oct 12:50 UTC (Boris's queue, in order):**
  1. S6c today, on `s6c-wip` off `origin/lane-b`, as ruled in
     `prereg/S6b.md`.
  2. The live "xp_v2 as tested" forecast (S11 shares in the xg half,
     bottomup_lambda, current minutes model) in `tools/gw_pass.py`, beside
     own: XI, bench and captain. Required for the GW8 switch.
  3. S2b Tuesday: dry run, merge before 21:00 UTC, Boris's real dispatch.
  4. The landing of lane B's items (S8, S11, S12, S13, S6b, S6c, the
     bundle, the CLAUDE.md provenance line): Tuesday or Wednesday, one dry
     run, before Thursday 11:30 UTC.
  5. W1b Wednesday.
  6. Step 14 (RULING Step 14, Boris 19 Oct; prereg first), by Thursday
     afternoon so the bundle can print it.
  7. The GW8 bundle: Thursday about 18:00 Prague and Friday morning after
     the nightly; files under `worklog/gw_pass/gw8/`.
  8. W2 in the gaps (merge Saturday after the deadline, `prereg/W2.md`).
  Verifier: Fable unless its weekly bar is above 80% (then Opus xhigh);
  Fable resets Tuesday 08:00. Stop after 6 items without a chat review.

- **CURRENT, for a fresh lane A session (19 Oct; the old session ended here by
  RULING W2 standings + lanes merge).** Read
  `CLAUDE.md`, `BUILD_PLAN.md` and this file, then wait for Boris.
  - **Master:** the commit carrying this file (`git log -1 --
    worklog/SESSION_STATE_A.md`), 614 tests green. No W2 code exists yet;
    `w2-wip` is not created. Landed 19 Oct: W1, S16 part 2,
    S10, S16 part 1 and its void-round amendment; lane B's S4, S5, S6, S7
    and S9.
  - **Untracked here on purpose:** `worklog/verify_S2b_pre.md` (on
    `s2b-wip`) and `worklog/verify_W1b_pre.md` (on `w1b-wip`). Move each
    aside before merging its branch.
  - **Tuesday 20 Oct, S2b** (`s2b-wip` `de65e1b`, verifier PASS on
    `19b303c`):
    1. merge master into `s2b-wip` (master moved a lot), full suite;
    2. Boris dispatches the dry run (manual; W1b is not live), then read back;
    3. the Fable verifier on the dry run and the delta;
    4. tag `pre-S2b`; merge before 21:00 UTC; Boris's real dispatch. That is
       the first real re-fetch of GW1-6: expect 48 extra calls;
    5. the after-measurement with `s2b_measure.py`, including lane B's S4,
       S5, S6 and S9 numbers on the after-database (they are on master now).
  - **Wednesday 21 Oct, W1b** (`w1b-wip` `1118948`, verifier PASS on
    `a9248d1`; the 04:00 close and the missing-deadline WARN since):
    1. merge master into `w1b-wip`. `BUILD_PLAN.md` changed on master in lane
       B's landing; check Part E merges cleanly;
    2. the verifier on the delta `28092d8..`;
    3. the last manual dry run (Boris);
    4. tag `pre-W1b`, merge, real dispatch, final verifier.
    Then lanes ask for dry runs by pushing `dry/<item>`.
  - **W2** (RULING W2 build; prereg `prereg/W2.md`, master `08d6a95`, with
    acceptance tests per piece). Build on `w2-wip` off master; merge Saturday
    24 Oct after the GW8 deadline, outside 9d. Suggested order, small to
    large:
    - **(a) `fpl_sync.py`:**
      - `fetched_at_utc` on `transfers`, `chips`, `standings`,
        `player_history` (`picks` comes from S2b);
      - `players.code`;
      - **the standings, per RULING W2 standings (19 Oct, prereg/W2.md,
        replacing acceptance test 4):** do not rewrite the seven mislabelled
        event-2 rows; keep them byte for byte.
        - Add `standings.label_error` (0/1) by migration, and set it to 1 on
          those seven rows, with a CHANGELOG note.
        - Make every reader skip `label_error = 1`. Find them first: the
          export, checks, `fpl_edge` and lane B's tools.
        - GW2 league rank stays "not recorded".
        - No row is removed, so the gate's grow-only holds.
    - **(b) `bottomup_lambda` as a sixth source:** port the forecast from
      `tools/odds_lambda.py`. Find the function S5 adopted: its live mode
      takes W1's newest odds snapshot before the next deadline, the mean
      price across bookmakers, h2h without h2h_lay and totals at 2.5.
      - Prove byte-identical numbers against the tool on the same snapshot.
      - RECORD SKIP, a WARN, without an odds file.
    - **(c) Report sections CHIPS and LEAGUE:** port `tools/chips.py` `live()`
      with the part of `tools/backtest.py` Harness that `residual_pools`
      uses, and `tools/league.py` `report()`. Byte-identical against the
      tools on the same data folder, seeds and resamples. A missing input
      gives `<SECTION> SKIPPED:` and a new check 31 WARN.
    - Never import `tools/` from the runner (the existing test).
    - Lane B owns `tools/`: copy, do not edit their files.
    - Open question: the runner freeze for the GW8 deadline runs from 22 Oct
      11:30Z to the deadline, 23 Oct 17:30Z. Do pushes to `dry/W2` count?
      Ask before pushing one inside it.
- **Monday 19 Oct, end of day (11:05 UTC):** RULING lane A open points, 19
  Oct, is verbatim in `prereg/S16.md`, `S10.md` and `W1.md`.
  - **S16 part 1 landed** (`53b5246`, CHANGELOG `4d3e9b5`).
  - **The void-round amendment landed** (`dc4bc28`): 2022-23 GW7 is labelled
    "void round" and kept outside the base rates, with both counts printed.
  - **CHANGELOG** records the goalkeeper-goal discrepancy (`game_config` 10,
    frozen `bottomup` 6) and check 30 strict.
  - **Landed today:** W1, S16 part 2, S10, S16 part 1 and its amendment.
    Master `dc4bc28`, 614 tests.
  - **Next:**
    - Tuesday S2b: merge master into `s2b-wip` (it has moved: W1, lane B's
      landing, S10, S16), then the dry run, the verifier on the dry run and
      the delta, tag `pre-S2b`, merge before 21:00 UTC, real dispatch,
      after-measurement.
    - Wednesday W1b: merge master into `w1b-wip` first (`BUILD_PLAN.md`
      changed on master), then the delta verifier, the last manual dry run,
      tag, merge, real dispatch, final verifier.
  - **Parked:** Step 16 parts 3-4 (missing inputs).
- **Monday 19 Oct, later (RULING lane A 19 Oct midday, verbatim in prereg/S16.md):**
  - **S10 landed** on master `349e1a7`, merge `63906e6`.
    - Measurement PASS: 11,361 of 11,361; verifier PASS; landing dry run
      `415c9a9`.
    - It had merged lane B's landing of S4, S5, S6, S7 and S9 (`6bd378b`)
      first.
  - **Downloads are data, never code:** now a rule in `CLAUDE.md` (both lanes).
    The 06:45 UTC incident is in CHANGELOG (`47142a3`).
  - **S16 part 1** (blank and double history, 2018/19 on, from the `event`
    field): built on `s16-wip` (`2ed24d6` code, `0bec736` report).
    - Reproduction PASS, 2024-25 and 2025-26; verifier PASS.
    - Waits for one green dry run of `s16-wip`, then the CHANGELOG entry and
      the merge.
  - **Open for the chat:**
    - 2022-23 GW7: the whole-round blank reads as an unused number, so
      2022-23 counts 22 blanks against 42 doubles;
    - the goalkeeper goal: 6 in the frozen `bottomup` model, 10 in
      `game_config`;
    - check 30's "any of three" reading.
  - **Next, by plan:**
    - S2b on Tuesday: the dry run of `s2b-wip`, the verifier on the dry run
      and the delta, tag `pre-S2b`, merge before 21:00 UTC, real dispatch,
      after-measurement;
    - W1b on Wednesday: merge master into `w1b-wip` first. `BUILD_PLAN.md`
      changed on master in lane B's landing; W1b's Part E text must merge
      cleanly.
- **Monday 19 Oct (RULING morning 19 Oct, verbatim in the W1, S2b, W1b, S16
  and S10 preregs):**
  - **W1 done.**
    - Merged `20309df` (tag `pre-W1` = `5b38b41`).
    - Real dispatch, run 39208578261: data `bd724ca`, STATUS OK 28/28, first
      real odds file, `fpl_ep` 668, credits 488 left.
    - Final verifier PASS (`worklog/verify_W1.md`); report and CHANGELOG
      `9f03bcf`.
  - **S16 part 2 landed.** Merge `f2820e3`, after its green dry run
    (`data-dryrun` `24881f1`); CHANGELOG `086a237`.
  - **W1b updated** on `w1b-wip` `1118948`:
    - the 21:30 window closes at 04:00;
    - a missing deadline row is a WARN, and the run goes on;
    - 541 tests; mutations 29 of 29 red.
    Still to do: the delta verifier, then the last manual dry run after S2b
    lands, then the merge Wednesday.
  - **Downloads done** (`worklog/downloads_2026-10-19.md`):
    `players_raw.csv` for 2025-26, and `fixtures.csv` for 2018-19 to 2024-25.
    - There is an incident record in that file: a shell heredoc ran the
      downloaded CSVs as commands. Checked: no effect, hashes intact.
  - **Step 10:** prereg `55f3476`; built next on `s10-wip`.
  - **Step 16 part 1: parked.** Vaastav has no `fixtures.csv` for 2016-17 or
    2017-18, and no deadlines file for any season. Question:
    - Without deadlines, the history can only take each fixture's FPL
      `event` field.
    - What is the reference for "reproduce the 2024/25 and 2025/26 events
      exactly"? If it is kickoff mapped to gameweek by deadline, the
      deadlines need a source: vaastav's `2018-19/raw.json` covers one season
      only, so another archive would need your approval.
  - **Findings for the chat:**
    - The live `game_config` gives a goalkeeper goal 10 points. The frozen
      `bottomup` model's `GOAL_VALUE` uses 6; not changed (model-change
      protocol).
    - Check 30's "any of three headers" reading is still not ruled.
- **Night of 18/19 Oct: RULING lane A night work** (verbatim, recorded once):

  > Keep working until morning without Boris, on branches only:
  > 1. W1b (automatic dry runs, as already ruled) on w1b-wip off w1-wip: prereg on master first (docs only), then code, tests, mutations, push w1b-wip. No dry run until Boris is up; W1b merges the day after W1 (one wiring merge a day).
  > 2. Step 10, the rule normaliser, on s10-wip off master: everything except the hist_pit re-measure (that waits for S4 on master). Prereg first. Offline under tools/, reading C:\GIT\FPL-data read-only. Its tests live in tests/, which the nightly now runs, so it lands only after a green dry run of its landing branch, same rule as lane B.
  > 3. If time remains: Step 16 part 1 (blank/double history 2016/17-2025/26, offline) on s16-wip, prereg first.
  > Never tonight: anything on master except preregs and SESSION_STATE_A.md; dispatch requests; touching lane-b. A download or decision that needs Boris: park it in SESSION_STATE_A.md and move to the next item. Stop after 6 items without a chat review. Morning: one report block per item, then the Monday W1 order: confirm the 03:17 run, tag pre-W1, merge, Boris's real dispatch, final verifier. Lane B lands S4+S7+S5+S6 after W1's real dispatch is green.

  Addition (Boris, same night, verbatim): "after Step 16 part 1, do part 2
  (the 2026/27 calendar mapper: cup dates to gameweeks by deadline). Parts 3-4
  only if every input already exists locally (Elo may be built from archived
  results); a missing input (e.g. the European fixture calendar) is parked with
  the list of what is needed, no downloads without Boris. Order tonight: S2b,
  W1b, Step 10, Step 16 parts 1-2."

  RULING S2b (same night) has priority over this queue: verbatim in
  `prereg/S2b.md`, on `s2b-wip` off `w1-wip`. It lands Tuesday before 21:00 UTC,
  after W1 (Monday); W1b moves to Wednesday.
- **Night work, done** (19 Oct, 01:00 UTC). Three items were built and
  verified, all on branches; master got preregs and this file only. All
  write guards were clean.
  - **S2b:** on `s2b-wip` at `de65e1b`.
    - `19b303c` is the code. `316652a` closes gh.log (test only), and
      `de65e1b` adds the report (`worklog/cc_2026-10-19_S2b.md`) and the
      verifier copy.
    - Code-level verifier on `19b303c`: **PASS**.
    - Rehearsal on a scratch copy against the live API: 73 calls, then 25.
      entry_gw points move in GW3 (7 of 7 managers), GW4 (6 of 7) and GW6
      (5 of 7); player_gw points don't move.
    - Check 22 after: 42 of 42 equal. The calibration is identical before and after.
    - Tuesday:
      - the dry run of `s2b-wip`, read back;
      - the verifier on the dry run and on the delta `19b303c..de65e1b`;
      - tag `pre-S2b`, merge before 21:00 UTC;
      - Boris's real dispatch, the first real run, which re-fetches GW1-6;
      - the after-measurement, including lane B's S4, S5, S6 and S9 numbers.
  - **S16 part 2 (calendar mapper):** on `s16-wip` at `4acdb0f`.
    - `5dcead7` is the code; `4acdb0f` adds the report and the verifier copy.
    - Verifier **PASS**; 471 tests green; mutations 9 of 9 red.
    - The mapping:
      - Carabao Cup final -> GW30;
      - FA Cup QF -> GW30 (in the international gap);
      - FA Cup SF -> GW32 or GW33 (GW33's deadline is that day);
      - FA Cup final -> GW36.
    - Lands only after a green dry run of its landing branch: a manual dry run
      of `s16-wip`, or `dry/S16` once W1b is live. Then the CHANGELOG entry and
      the merge.
  - **W1b:** on `w1b-wip` at `28092d8`.
    - `a9248d1` is the code; `28092d8` adds the report and the verifier copy.
    - Code-level verifier: **PASS**. 527 tests; mutations 25 of 25 red, and the
      verifier's own 29 red.
    - Merges Wednesday after one last manual dry run (Boris), the verifier on
      it, tag `pre-W1b`, Boris's real dispatch and the final verifier.
    - No `dry/` branch exists, and none was pushed.
- **Parked for Boris:**
  - **W1b (answered).** The four questions were answered by RULING W1b.
  - **S3 report (Boris, 19 Oct, verbatim lines):** record in
    `worklog/cc_2026-10-18_S3.md` on Monday, since master takes only preregs
    and this file tonight. The 18:45 UTC dispatch was nightly #21,
    workflow_dispatch on master `1af9644`, Success, 58 s:
    - `Is this run due:  DUE          not the backup cron`
    - `Weekly backup:    BACKUP skipped: a manual dispatch backs up only with force_backup ticked`
    - `Failure issue:    ALERT none: the run is green and no issue is open`

    The same log shows GATE OK (integrity ok, 14 tables, price_history 25882
    rows, frozen forecasts unchanged) and SECRETS OK. That outstanding item
    is closed.
  - **Low priority, whenever lane A next touches test_fpl.py:** the
    BackupStep tests left gh.log open (ResourceWarning: unclosed file,
    test_fpl.py:5419). Done on `s2b-wip` (`316652a`): 5 warnings before, 0
    after, no behaviour change. It lands with S2b.
  - **Step 10 (rule normaliser): not started. Four inputs or decisions are
    missing, and no code was written:**
    1. The 2025/26 scoring table, which the reproduction test needs ("re-scoring
       2025/26 under the 2025/26 rules reproduces official points within ±1 for
       ≥ 99%"). No official 2025/26 table is in the repository or the local
       data. Which source should it be?
       - (a) The live API's `bootstrap-static` `game_config` (2026/27), taken
         as the 2025/26 points table on the claim that points rules did not
         change. HISTORICAL_VALIDATION.md says goals, assists and appearance
         points are unchanged and names only BPS changes. The reproduction
         test then checks that claim.
       - (b) A 2025/26 table Boris supplies, for example an archived copy of
         the rules page.
    2. The cross-season key `code`, needed for position reclassifications:
       - `fpl.sqlite` `players` has no `code` column; the sync checks the field
         but does not store it.
       - `historical/2025-26` carries only the 2025/26 element id (`merged_gw.csv`)
         and names (`cleaned_players.csv`).
       Which source?
       - (a) Download vaastav `data/2025-26/players_raw.csv` (has `id` and
         `code`). A download, so it needs your approval.
       - (b) Store `code` in the sync. That is a runner change, its own item.
    3. BPS under 2026/27: two of the three changed components are not in
       `merged_gw.csv`: times tackled (the removed −1) and big-chance saves (the
       GK rework). Only CBI (1 per 2 → 1 per 3) can be recomputed, so 2026/27
       bonus cannot be re-derived. Choose one:
       - (a) a partial BPS with the CBI term, the rest reported missing;
       - (b) no BPS re-score until the data exists.
    4. "Rescale assists": which rule?
       - (a) a 2026/27 change in assist points (the 2026/27 `game_config` would
         show it);
       - (b) the wider 2025/26 assist definitions applied to older seasons,
         which is a Step 16 or older-season matter.
    Older seasons than 2025/26 are not local either (vaastav download).
  - **Step 16 parts 1, 3 and 4: missing inputs, parked** (part 2 is built on
    `s16-wip`):
    - Part 1, the history 2016/17-2025/26: archived fixtures with FPL's gameweek
      per fixture exist locally only for 2025/26 (`historical/2025-26/fixtures.csv`).
      Needed: vaastav `data/<season>/fixtures.csv` for 2016-17 to 2024-25
      (9 files), plus each season's deadlines (vaastav `gws/` or the events).
      Its unit test needs 2024/25 as well as 2025/26.
    - Part 3, the cup Monte Carlo needs three inputs:
      - "to qualify" odds history, or results to build Elo from. Neither is
        local; FA Cup Elo needs lower-league clubs too.
      - the 2026/27 European fixture calendar (UEFA dates), not local;
      - a table of free midweeks, to build from that calendar.
    - Part 4, the backtest on 2024/25 and 2025/26: needs part 3 and both
      seasons' cup draws and dates.
- **Monday 19 Oct, first task: done at 03:50 UTC** (RULING S3 dispatch result),
  read from git and the public Actions API (no token):
  - **Tonight's scheduled nightly**, run 39170094238, started 21:57:24Z (cron
    21:40): every step success, including Weekly backup and Failure issue.
    - Data commit `9da6ff1` (21:58:09Z).
    - `status.txt`: STATUS OK 27/27. Checks 9 (element key set, 109 keys
      unchanged) and 26 (heartbeat, 3.2 h) are now active and OK. 22 and 27
      SKIP as designed. 28: 459 tests; 29: four sources.
  - **Release `backup-2026-10-18`:** at `9da6ff1`, with `fpl.sqlite` 1,896,448
    bytes and `fpl.sql` 2,543,677 (the tip's sizes). Releases kept: 2 of 8.
  - **The 03:17 backup run**, run 39196048636, started 03:43:37Z on master
    `cd3087e`, green in 14 s. Only "Is this run due" ran; Install, Nightly
    run, Commit, Weekly backup and Failure issue were all skipped. That is
    the designed not-due path: the nightly had written `status.txt`. No
    commit (data still `9da6ff1`), no release. Its log line itself needs a
    token (HTTP 403 without one).
  - The cancelled dispatch 39166214887 (18 Oct 21:04:45Z) stopped at "Set up
    job", so no dry run was used by it.
- **Rehearsal of the week's landings** (scratch only, nothing pushed): master
  `cd3087e`, then `w1-wip`, `s2b-wip`, `w1b-wip` and `s16-wip`, merged in
  that order, gives no conflict (git auto-merged test_fpl.py and
  tests/test_S3.py). 560 tests are green bare, runner-like, with stand-in
  zones and hermetically.
- **Current item:** W1 (wiring: fpl_ep and the Odds API collector), on
  `w1-wip` (`ab047c3`); prereg `prereg/W1.md` (`7efc2b2`, decisions `91b10c7`,
  odds storage `249be76`; on w1-wip: master merged in `021656c`, pre-check
  decisions `23c1e1e`). Odds are raw gzip files in `odds/` on data, append-only;
  no odds table; check 24 names files over 50 MB. Suite 499, green normally and
  hermetically.
  - RULING W1 pre-check decisions applied on w1-wip `ab047c3` (18 Oct, after the pre-check):
    - the API only when `GITHUB_ACTIONS` is "true", else
      `ODDS SKIPPED (not in GitHub Actions)` and exit 0;
    - check 30 WARNs `credits unknown` when any of x-requests-used,
      -remaining or -last is missing;
    - no action on bookmakers outside uk/eu.
    Four new tests, red on `d928ebe` (14 failures), green on `ab047c3`. Suite
    495 -> 499 bare, runner-like, with stand-in zones and hermetically. Mutations
    P1, P1b, P2 and P2b are red, and W15 was re-pointed and is red. A frozen-clock regeneration is
    byte-identical between `d928ebe` and `ab047c3`.
  - RULING W1 decisions applied:
    - 4 credits a night, about 124 a month;
    - `odds_live` dispatch input, so a dry run skips the API unless it is ticked;
    - every odds problem is a WARN only;
    - check 30 WARNs below 60 credits;
    - no `ep_next` is `RECORD SKIP fpl_ep` (a WARN), and missing players are counted.
    `ODDS_API_KEY` is confirmed by Boris, re-entered 20:15 UTC on 18 Oct.
  - Tests 459 -> 495, green normally and hermetically. Mutations: 15 of 18
    (3 obsolete after the storage change) + 10 + 11, all red.
  - Second dry run `bf91cf5` (`d928ebe`, `odds_live` ticked) ruled green
    (RULING W1 dry run 2, 18 Oct): STATUS OK 28/28, odds file 10,472 bytes,
    fpl.sqlite unchanged at 1,896,448 bytes, 492 credits left.
  - Verifier pre-check: **PASS** (Fable 5.1, effort high), in
    `worklog/verify_W1_pre.md`. That file stays untracked until Monday. The write guard
    is clean: only that file changed; lane-b moved by lane B's own pushes.
    Its four observations went to the chat, and the first three were ruled in
    RULING W1 pre-check decisions:
    - a local `python fpl_odds.py` with the key set was a real run;
    - missing credits headers gave `remaining None` and an OK check 30;
    - non-uk/eu bookmaker keys appear in the answer;
    - w1-wip's own `prereg/W1.md` predated the two rulings. Master was merged
      into w1-wip in `021656c`, so it now carries all three.
  - Dry run 3 of `ab047c3` (`odds_live` unticked), moved to the night of 18 Oct by
    Boris: data-dryrun `f7c5706` on `9da6ff1`. Green:
    - 499 tests; `+ players.ep_next`; `ODDS SKIPPED (dry run)`, no `odds/`;
      five RECORD OK (fpl_ep 668);
    - STATUS WARN 27/28, the only WARN being check 30's dry-run skip;
    - the 1077 same-day GW8 rows of the four frozen sources changed `made_at` only,
      with 0 predicted values changed against master's code;
    - GATE OK, with an identical fpl.sql.
  - Verifier re-check on the delta: **PASS** (Fable 5.1, effort high), in
    `worklog/verify_W1_recheck.md`, untracked until Monday. The write guard
    (git status, git diff) is clean. One ref move, not attributed: `C:\GIT\FPL-data` was
    pulled (fast-forward e8629f0 -> 9da6ff1) at 22:37:57 UTC, 33 s after the
    guard snapshot. The verifier says it did not touch it; lane B pulls FPL-data
    by its protocol and was active then.
  - Next, Monday morning, in order:
    - confirm tonight's nightly and the 03:17 run (the first task above);
    - commit `verify_W1_pre.md`, `verify_W1_recheck.md` and this file;
    - tag `pre-W1`, then merge (at most one wiring merge a day, never in a freeze window);
    - Boris's real dispatch;
    - the final verifier, the report and CHANGELOG.
    It lands by Wed 21 Oct 20:00 UTC.
- **S3: done** (18 Oct). Merged `1af9644` (tag `pre-S3` = `3ce5a08`); real
  dispatch `e8629f0` STATUS WARN 24/25, ruled green (the WARN is check 3, a
  new FPL player); final verifier PASS (`worklog/verify_S3.md`). Report
  `worklog/cc_2026-10-18_S3.md`. Open S3 decisions are listed there.
- **S2: closed** (RULING FAST-TRACK: "S2 is closed"). On master since `9b4a462`
  and `50abf60`; final verifier PASS (`worklog/verify_S2.md`); report
  `worklog/cc_2026-10-18_S2.md`. Revert tags `pre-S2` (`1cddca9`) and
  `pre-S2-backup` (`2bee604`). Two S2 checks still fall to lane A:
  1. Tonight's scheduled nightly (18 Oct, 21:40 UTC). It confirms S1 and S2
     together and should make `backup-2026-10-18`. If it fails, revert to
     `pre-S2` first, then investigate.
  2. After GW7 locks down (Tue 20 Oct or later): the GW7 before/after
     calibration comparison, reported with the GW7 grading (S2 amendment 2,
     point 1). If it differs, revert to `pre-S2` first.
- **Open for the chat:**
  - reverting to `pre-S2` after the GW8 deadline would grade GW8's several
    snapshots together (S2 final decision 1);
  - `CLAUDE.md` items b and g still name `worklog/SESSION_STATE.md`, which is
    now an index pointing to the two lane files.
- **Queue (FAST-TRACK item 8, as amended on 18/19 Oct):**
  - W1: merge Monday.
  - S2b: lands Tuesday.
  - W1b: ruled 19 Oct, built on `w1b-wip`, merges Wednesday.
  - Step 10.
  - W2: after the GW8 deadline.
  - Step 16.
  - W3, Steps 17-18, W4.
  - **Step 10 addition** (RULING Step 10 addition, 18 Oct, verbatim; also in
    BUILD_PLAN.md Step 10): once lane B has merged tools/hist_pit.py, re-measure the earlier 2025/26 findings that used fpl_hist.canonical_from_vaastav (the horizon test H=6, the F test, backtest_2025-26 and concentration_2025-26) with the point-in-time club map. Descriptive only: report old against new side by side; no rule changes unless a pre-registered test calls for one.
  - **W2 addition** (RULING W1 dry run 2 + W2 addition, 18 Oct, verbatim; goes
    into `prereg/W2.md` before any W2 code): Add to W2 (after the GW8 deadline): record bottomup_lambda nightly as a sixth source from the night's odds file (S5 adopted it as an input). The runner never imports tools/, so the formula moves into the runner path, tested to give byte-identical numbers to lane B's tools/odds_lambda.py on the same snapshot.
- **Models (FAST-TRACK amendment 1):** lane A's main session stays on Opus
  5.5; the verifier runs on Fable for every item, falling back to Opus at
  xhigh only if the Fable weekly bar is above 80% before its reset. Each
  report names the models used.
- **Dry runs used:** 18 Oct: 6 of 6.
- **Untracked in C:\GIT\FPL on purpose:**
  - `worklog/verify_W1_pre.md` and `worklog/verify_W1_recheck.md`: committed
    on master Monday, with W1;
  - `worklog/verify_S2b_pre.md`, `verify_S16.md` and `verify_W1b_pre.md`: also
    committed on `s2b-wip`, `s16-wip` and `w1b-wip`. Remove each untracked
    copy before merging its branch (the merge brings it).
- **What needs Boris, in order:**
  1. **Monday morning:**
     - lane A confirms the 03:17 run;
     - commit the W1 verifier files and the S3 log lines;
     - tag `pre-W1`, merge W1;
     - **Boris's real dispatch of master**, then the final W1 verifier.
  2. **Dry-run clicks:**
     - a manual dry run of `s16-wip`, any day, to land S16;
     - **Tuesday:** the dry run of `s2b-wip`, then after the merge the real
       dispatch;
     - **Wednesday:** the last manual dry run of `w1b-wip`, then after the
       merge the real dispatch.
  3. **Readings to confirm:**
     - W1b (a), the cap and windows on manual dry runs too;
     - W1b (b), the 21:30 window closing at 03:17; the verifier suggests about
       04:00 to cover the backup run;
     - check 30 "any of three headers", which the verifier agreed with;
     - S2b's three report decisions.
  4. **Step 10:** the four questions above, among them the source of the
     2025/26 scoring table and the `code` key (a download).
  5. **Step 16 parts 1, 3 and 4:** approval for the downloads listed above.
  6. **Who pulled `C:\GIT\FPL-data` at 22:37:57 UTC on 18 Oct** (lane B?).
  7. **Earlier open decisions:** the S3 report list; `pre-S2` after GW8; and
     CLAUDE.md b and g, which still name SESSION_STATE.md.
- **Last pushed commit:** the commit carrying this version of the file (`git
  log -1 -- worklog/SESSION_STATE_A.md`).
- **Runner freeze window (9d):** not active. Runner-path changes are never
  pushed between 21:00 UTC and the end of that night's nightly run, nor within
  30 hours of a deadline. Next deadline GW8 2026-10-23T17:30Z; the window
  opens 2026-10-22T11:30Z. Source: `fpl.sqlite` `events.deadline_time`.
