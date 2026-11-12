# S8c landing — the branch ready to land (Thu 12 Nov night; the merge Fri 13 Nov on Boris's click)

Main session, Opus 5.5. Item 1 of 6 since the chat review of Thu 12 Nov night.
Rulings, verbatim in `prereg/S8c.md`: point 5 of Fri 6 Nov (the tests' repos
disable signing), amendment 5 (the date, Boris's plan of Sun 8 Nov and his
rulings of Thu 12 Nov), the rulings of Thu 12 Nov night (S8c points 1–6 and
the Schedule: Fri 13 Nov). Runner work: the dry run, Boris's real run and the
freeze windows apply.

## What lands (`s8c-wip` over master)

- The offline items already on `s8c-wip`, each verified before: S10b, S6e,
  S6f, S6e2, S8b, S15 and S8c with its amendments 1–4 (tools and their tests;
  no runner file).
- `33304d8`: master `99c9161` merged in; one CHANGELOG conflict, both sides
  kept, master's first (101 + 7 + 7 = 115 entries).
- `f5cc8b3`: point 5 (pinned in `prereg/S8c.md` `97ded86` before it).
- `f1f5df2`: `fpl_xpv2.forecast` takes `tools/xp_v2_live.forecast`'s text
  again (Boris's OK, Thu 12 Nov night, S8c point 2).
- `ad34c9b`, `3405e94`, `f917dd1`: the final commits of S6f (`0b16969`),
  S6e2 (`d87f8aa`) and S8b (`cfa7a36`) (S8c point 1). The tools are unchanged;
  they bring S6f's two test lines, the S6f and S6e2 CHANGELOG entries, and
  the three items' reports and verifier files (S6f PASS, S6e2 a1 PASS, S8b
  PASS). S8b's entry was already on the branch, so its merge changes no
  CHANGELOG line. 117 entries.
- `4245b80`: S8c points 3 and 4 (tests only).
- This report and the CHANGELOG entry (point 6, docs only).

Outside `tools/`, `tests/`, `test_fpl.py`, `prereg/`, `worklog/` and
`CHANGELOG.md` the landing changes one file, `fpl_xpv2.py`.

## Point 5: the tests' repos disable signing

- Twelve per-repo `commit.gpgsign false` lines, one where each test
  repository is created: `test_fpl.py` (NightlyRunner `_data_repo`,
  `DataGate.setUp`, `Publish._ident` for the seed and runner clones,
  `PrePush.setUp`), `tests/test_S3.py` (`ChecksMain.setUp`, `PublishOnAFail`
  seed and run clone), `tests/test_W1.py` (`OddsAppendOnly.setUp`,
  `OddsNeverCostsTheNight` seed and data clone), `tests/test_W1b.py`
  (`DueGate.setUp`, `Hook.setUp`). `test_W1b.PushRunPublishes` inherits
  `Publish`'s helpers.
- The guard, `tests/test_S8c_p5.py`: a global config with `commit.gpgsign =
  true` and a signing program that does not exist breaks an unprotected
  commit; one test per site (ten sites) passes under it in a child process.
- **Measured** (by discovery, on `git archive` copies, `GIT_CONFIG_GLOBAL`
  pointing at that config):
  - before (`33304d8`): 852 run, 69 not passing — `test_fpl` DataGate 28,
    Publish 11, PrePush 6, NightlyRunner 2; `test_S3` PublishOnAFail 4;
    `test_W1` OddsAppendOnly 3, OddsNeverCostsTheNight 1; `test_W1b` DueGate
    9, Hook 2, PushRunPublishes 2 (the 68 of 3 Nov); and `test_W3.Copies` 1,
    the merge break below, not signing;
  - after: 855 OK (11 skipped).
- **Each line left out in turn:** on `f5cc8b3` the guard went red for 11 of
  the 12. The twelfth, ChecksMain's, stayed green because that helper did not
  check its commit's exit code. Point 4 of Thu 12 Nov night: `ChecksMain.setUp`
  now checks it and the guard covers it; with that line left out on
  `4245b80` the guard is red. 12 of 12.

## The merge break and the copy fix

- S8c amendment 4 added `lift=()` to `tools/xp_v2_live.forecast`; W3's
  runner copy `fpl_xpv2.forecast` must be its verbatim text
  (`tests/test_W3.py` Copies), so the merged tree failed Copies in every run:
  the nightly's gate would have gone red and blocked `--record`.
- `f1f5df2` copies the tools text. The runner's one caller passes no `lift`.
  xp_v2 recorded on two copies of the data (`6f9ecb8`) with master's code and
  with the branch's gives the same 299 GW11 rows (event, player, value); the
  pre-check verifier found all seven sources, the watch file and the report
  byte-identical.

## S8c point 3: the record keeps the status gate

`tests/test_W3.py` `StatusGateInTheRecord`: on the W3 toy, one of our players
at status `d` (chance 50) gets no xp_v2 row from the runner's record and no
other row moves. With the gate lifted in `fpl_xpv2.live_forecast` (the
pre-check verifier's probe) the test is red.

## Suites

- master `273100b`: 787 OK.
- the final code head `4245b80`: 855 OK (11 skipped) bare, 855 OK (4 skipped) with
  `FPL_DATA_DIR`, 855 OK (11 skipped) with signing on globally.

## The pre-check

- First run (`worklog/verify_S8c_landing.md` on master, Fable 5.2, launched
  at high, not confirmable): **FAIL** on two items — the three items' final
  commits were missing, and `f1f5df2` had no ruling. Every measured claim
  reproduced. Write guard clean. Boris's answers: S8c points 1–6 of Thu 12
  Nov night, all done above.
- Re-check of the new head: to follow (`worklog/verify_S8c_landing.md`, appended).

## Notes

- The duplicate "W2 amendment 2" entry in master's CHANGELOG (entries 80 and
  95) is left as recorded (append-only), as Boris ruled (S8c point 6).
- Mode (d), as Boris ruled (S8c point 5): the 21:00 UTC window covers master
  and `dry/*`; `dry/S8c` is pushed only after tonight's nightly has
  committed. `s8c-wip` (a work branch) may be pushed at any time.

## Next

`dry/S8c` after tonight's nightly; read back `data-dryrun-S8c` against the
last real data commit; tag `pre-S8c`; the merge Fri 13 Nov before 21:00 UTC
on Boris's click; his real run; the final verifier; delete `dry/S8c` and
`data-dryrun-S8c`.
