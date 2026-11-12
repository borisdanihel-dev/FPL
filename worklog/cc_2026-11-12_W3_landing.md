# W3 landing — the merge, the dry run and the two real runs

Report, Thu 12 Nov 2026 (main session, Opus 5.5). Item 1 of
Boris's "International break plan, Sun 8 Nov": "W3 merge (with the +02:00
committer test, the fetch-depth comment and the captain-without-row test);
Boris clicks the real run." The plan arrived Wed 11 Nov with nothing done
Mon 9 or Tue 10 Nov, so the runner items moved two days: W3 Wed 11, S8c
Thu 12, runcommit Fri 13 (one runner change a night, all before the GW11
freeze, Fri 20 Nov 05:00 UTC).

## The merge (prereg/S2.md point 6)

- Code: `w3-wip` `62bda73` (W3 amendment 3, verifier PASS twice,
  `worklog/verify_W3_a3.md`: the merge's verifier pre-check). Master had
  moved since by preregs, worklog and the state file only, so `47ac1ea` is
  the merge of master `b44e796` into `w3-wip`;
  `git diff 62bda73 47ac1ea` outside `prereg/`, `worklog/` and
  `CHANGELOG.md` is empty.
- The three additions the plan names are in the merged code:
  - the +02:00 committer test, `tests/test_W3.py:732`
    `test_a_committer_date_at_plus_02_00_is_read_as_its_instant`;
  - the fetch-depth comment, `.github/workflows/nightly.yml:84-85` (the full
    history: REALISED reads GW8's bundle at its last commit before the
    deadline);
  - the captain-without-row test, `tests/test_W2fix.py:88`
    `test_captain_with_no_player_gw_row_counts_as_0_minutes`.
- Tag `pre-W3` → `b44e796` (master before the merge). Pushed Wed 11 Nov
  11:41:58 UTC (the secret-scan run on the push: success).
- Suite by discovery on `git archive` copies:
  - before (master `b44e796`): 755 OK bare (10 skipped), 755 OK with
    `FPL_DATA_DIR=C:\GIT\FPL-data` (3 skipped);
  - after (`47ac1ea`): 787 OK bare (11 skipped), 787 OK with the data
    (4 skipped).

## The dry run (`dry/W3` → `data-dryrun-W3` `64a58c8`, Wed 11 Nov 11:39 UTC)

- STATUS WARN 27/30: check 17 (the old 2026-11-05 price-date gap), check
  30 (odds: a dry run has no key) and check 31 (CAPTAIN SKIPPED).
- Check 28: 787 tests green. Check 29: xp_v2 301, 482 prior players keyed by
  code.
- Against the last real data commit `6ca6cd5`: nothing else moved but the
  expected (xp_v2 rows, the W3 sections, CHIPS reading the newer archive).
- Check 31 is a first-night effect. The report sections run before the
  night's export is archived, so they read the previous night's archive.
  That one came from pre-W3 code, which does not export `code` (0 of 672
  players); W3's own archive has it for 672 of 672.

## The real runs on `47ac1ea`

Boris did not click on Wed 11 Nov, so the first real run on W3 was the
scheduled nightly; his dispatch came Thu 12 Nov.

### Scheduled nightly (run 43141722407, 02:29–02:32 UTC Thu 12 Nov, data `2e0b948`)

- STATUS WARN 28/30: check 17 (the 2026-11-05 gap, as every night since)
  and check 31 (CAPTAIN SKIPPED, the first-night effect, as forecast).
- Check 28: 787 tests green. Check 29: own 300, xg 278, minutes 278,
  bottomup 278, fpl_ep 672, bottomup_lambda 278, xp_v2 300 (10 of 10
  fixtures from odds; prior 2025/26, 482 players keyed by code). Check 30:
  odds OK (credits used 48, remaining 452).
- Sections: LEAGUE as before; BAN RISK GW11 Groß P(ban) 0.350, Thiago 0.000
  (P(start) 0.00); REALISED GW8 own 41 v xp_v2 41 (captain Haaland both;
  xp_v2 from the GW8 bundle `6034baa`), GW9 own 72 and GW10 own 62 with no
  xp_v2 row before those deadlines.

### Boris's dispatch (run 43272346801, 17:42:58 UTC Thu 12 Nov, data `6f9ecb8` at 17:46:08 UTC)

- dry_run unticked; the data branch moved `2e0b948` → `6f9ecb8` (author
  github-actions[bot], `nightly 2026-11-12 [skip ci]`); odds with the key
  (credits used 52, remaining 448).
- STATUS WARN 29/30: only check 17, the old 2026-11-05 gap.
- **Check 31 OK:** "report sections: CHIPS 34 lines, LEAGUE 58 lines, CAPTAIN
  20 lines, BAN RISK 3 lines, REALISED 5 lines". The forecast held: the
  sections read the 11-12 archive, written by W3 code, so CAPTAIN ran.
- Check 28: 787 tests green. Check 29: own 299, xg 277, minutes 277,
  bottomup 277, fpl_ep 672, bottomup_lambda 277, xp_v2 299 (10 of 10
  fixtures from odds; 482 prior players keyed by code). Checks 18–20:
  projection-log growth by source as above, 0 duplicate keys, 0 of 55,421
  rows at or after their deadline.
- CAPTAIN GW11 (information; the captain rule is unchanged): Gabriel xp_v2
  5.62 (P≥10 0.140), Haaland 5.59 (P≥10 0.166), within 0.3 xP of each
  other; Thiago and Thomas have no xp_v2 forecast. BAN RISK and REALISED as
  in run 1.

## Final verifier

`worklog/verify_W3_final.md`, Fable 5.2 (`claude-fable-5-2`), launched at high, not confirmable (Ruling 5 of Thu 12 Nov).

- **First run: FAIL on check 4 only** (the record). `prereg/W3.md` said "W3 merges Sat 7 Nov"; the plan of Sun 8 Nov that moved it was in no prereg. My slip: the plan's item text should have gone into the prereg before the merge. (The first attempt stopped on an API connection error before writing anything; the resumed run wrote the report.)
- Every code and data check passed:
  - both real runs ran `47ac1ea` (GitHub run objects: `schedule` and `workflow_dispatch`, both success; 787 tests); both were real (data commits by github-actions[bot], odds credits used);
  - the merged code is `62bda73`'s; the three plan additions are present and ran `ok` in both runs;
  - check 31's first-night skip is confirmed from the archives (`code` for 0 of 672 players in the 11-11 archive, 672 of 672 in both 11-12 archives); rebuilding each run's sections from the exports it saw reproduces each report block exactly;
  - CAPTAIN's 13 rows equal the offline tool (`==` on every float); BAN RISK recomputed from SQL (Groß rate90 0.3498, P(ban) 0.350; Thiago P(start) 0.00, status `s`); REALISED GW8 own 41 v xp_v2 41 with its own XI picker;
  - every xp_v2 row of both runs is GW11, before its deadline, rebuilt exactly from the archived inputs; planted later results and a post-deadline snapshot move nothing;
  - the six older sources are row for row what pre-W3 code produces on the same inputs (2,084 rows in run 1, 2,079 in run 2);
  - no regression against `6ca6cd5`; no secret; mutations 10 of 10 red.
- **The record fix** (Ruling 1 of Thu 12 Nov): `a4cb2df` appends amendment 4 to `prereg/W3.md` under the ruled marker line, with the plan of Sun 8 Nov and the rulings of Thu 12 Nov verbatim; no code.
- **Rerun of check 4: PASS.** The marker line is byte-identical to the ruling; `a4cb2df` touches only `prereg/` and the verifier file; every ruling the landing acted on is on file (after the fact, as Ruling 1 accepts). The verifier did not compare the pasted text with the chat: its agent file forbids reading transcripts (RULING S0c point 1), and I should not have asked. That the text is verbatim rests on Boris's own read of `prereg/W3.md` amendment 4.
- **The verifier's decisions for the chat, and Boris's rulings on them (Thu 12 Nov):**
  - the export lag in CAPTAIN and BAN RISK: Ruling 2, fixed in W3fix (Sun 15 Nov);
  - the false Free Hit flag in CHIPS: Ruling 3, fixed in W3fix;
  - two runs in one day: Ruling 4, the S2 rule stands (same-day rows replaced). **The scheduled run's xp_v2 rows (made 02:31:54 UTC) survive at data `2e0b948`**; the dispatch's replaced them at `6f9ecb8`, and the 11-12 archive name now holds the dispatch's export;
  - the effort level: Ruling 5, "launched at high, not confirmable".

## Write guard

After the first run: `git status` showed `worklog/verify_W3_final.md` alone (untracked); the data worktree clean at `6f9ecb8`. After the rerun: only `worklog/verify_W3_final.md` modified (146 insertions, 1 deletion); the data worktree clean. Both clean.

## Closing

- `dry/W3` and `data-dryrun-W3` deleted after the verifier PASS
  (`git push origin --delete dry/W3 data-dryrun-W3`; a deletion, never a
  force-push).
- Correction for `prereg/runcommit.md`: it gives the GW11 freeze as Thu 19
  Nov 05:00 UTC; the right time is Fri 20 Nov 05:00 UTC (30 hours before Sat
  21 Nov 11:00 UTC), as Boris's plan says. The note goes into the prereg when
  runcommit starts (a frozen entry is amended, never edited).
- Next, by the rulings of Thu 12 Nov: S8c Fri 13 Nov (with point 5); runcommit and the price-moves name fix Sat 14 Nov; W3fix (Rulings 2 and 3) Sun 15 Nov; each a runner change with Boris's real run, all before the GW11 freeze (Fri 20 Nov 05:00 UTC).
