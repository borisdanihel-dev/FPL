# verify_W2fix — check 31: the vice-captain promoted when the captain played 0 minutes

**VERDICT: PASS**

Verifier: Claude Code backtest-verifier agent, model Fable 5.1 (claude-fable-5-1), effort high (as `.claude/agents/backtest-verifier.md` on disk says; read first). Run on Tue 3 Nov 2026, scratch folder `C:/Users/Boris/AppData/Local/Temp/claude/C--GIT-FPL/442a647f-7693-4ced-b840-0df7f5bfd943/scratchpad/verify_w2fix` (`old/` = git archive of d2e1b43, `new/` = git archive of 8c7a34a, `mut/` = a copy of new for mutations, `real/` = a copy of w2fix_real, data 0c61ea1). Every command ran with `env -u ODDS_API_KEY`. No file in C:/GIT/FPL, C:/GIT/FPL-data, C:/GIT/FPL-b, W2FIX (apart from this report) or w2fix_before was written.

Reason, in one paragraph: the prereg d2e1b43 (17:00:39 +0100) precedes the one code commit 8c7a34a (17:04:21 +0100), the diff is exactly what the prereg pins (vice from `picks.is_vice`, minutes summed over `player_gw` rows with no row = 0, the vice takes `expected_multiplier(position, True, chip)` only when the captain's minutes are 0, nothing else in `load`'s outputs touched) and the two modules are AST-identical definition by definition; the real database confirms the finding (entry 18931 GW8, captain 165 on 0 minutes at position 13 x0, vice 411 x2 at position 10, the only 0-minute captain in 63 entry-gameweeks with exactly one captain and one vice each); the new rule can only accept, where the old one stopped, a vice in the XI stored at the captain's multiplier under a 0-minute captain, which is FPL's rule, and every case the prereg names as a limit still stops; the suite goes 752 OK -> 755 OK; the new tests are hermetic, cover both modules, are red on the old code (2 of 3) and the four pinned mutations plus two of mine go red; on the real data the old code prints the SKIPPED line and the new code prints CHIPS OK 35 lines, LEAGUE OK 51 lines, exactly as reported; the projection log is untouched by the item (the recording path does not import `fpl_league`, and the log hash is unchanged after the section runs); no secrets. One coverage note (not a failure): a mutation of mine that treats a missing `player_gw` row as "played" survives the tests, because every test inserts a row for the captain; the real data has no pick without a row, so the path is unexercised today.

## (a) Protocol

- `git -C W2FIX log`: `d2e1b43 2026-11-03 17:00:39 +0100 W2fix prereg` then `8c7a34a 2026-11-03 17:04:21 +0100 W2fix: the multiplier check promotes the vice-captain ...`. The prereg precedes the code. PASS.
- `git status --short` in W2FIX: clean. `git diff d2e1b43 8c7a34a --stat`: `fpl_league.py` (+11/-4), `tools/league.py` (+11/-4), `tests/test_W2fix.py` (new, 90 lines). Nothing else.
- The diff against the prereg's pinned fix, line by line:
  - `load`: `vice = {(eid, ev): pid ... from picks where is_vice = 1}`; `minutes = defaultdict(int)`; `minutes[(pid, ev)] += m or 0` over every `player_gw` row (a double summed; no row = 0 via `.get(..., 0)`). As pinned.
  - `check_multipliers(gw, picks, vice, minutes)`: `caps = [pid ... if cap]`; `promoted = vice.get((eid, ev)) if caps and minutes.get((caps[0], ev), 0) == 0 else None`; `want = expected_multiplier(pos, cap or pid == promoted, chip)`. The promoted vice gets the captain's rule: x2 / x3 in the XI, the bench rule (0, or 1 under bboost) on the bench. As pinned.
  - `expected_multiplier` unchanged; the picks tuples, the chain, the variance and scores untouched (`data["picks"]` still `(pid, pos, mult, cap)` from the same query; the return dict unchanged).
- The two modules, definition by definition (`ast.dump` of every top-level def/class): runner 19 defs, tools 20 (the extra one is `main`), differing = []. The W2 copy test `tests.test_W2.test_byte_identical_to_the_tools` passes on 8c7a34a (it compares the two modules' section outputs on the toy league, not the bytes). PASS.
- Prereg contents: Boris's message of Tue 3 Nov is in `prereg/W2fix.md` verbatim (the ruling text), the finding, the pinned fix, the tests and the mutations, "No re-tuning after viewing results". Primary metric n/a (a data-pipeline fix): descriptive-item checks apply.

## (b) Correctness against FPL's rules

Real database (`real/fpl.sqlite`, read-only, `python -I -X utf8`):
```
entry 18931 GW8 chip: [(None,)]
  (411, 10, 2, 0, 1, 'Haaland', '90')        <- vice, XI, x2
  (165, 13, 0, 1, 0, 'João Pedro', '0')      <- captain, bench 13, x0
entry-gameweeks: 63;  cap/vice counts per entry-gw not (1,1): []
events in picks: (1, 9); settled (data_checked=1, finished=1): [1..8]
captains on 0 minutes: [(18931, 8, 165, 13, 0, 0)]   <- the only one
vices on 0 minutes: [(4866471, 8, 165, 0), (2322726, 8, 165, 0)]   <- their captains played; no promotion; the new code accepts them (vice x1)
captain and vice the same player: 0; null minutes rows: 0; doubles (>1 row per player-event): 0
bboost: [(881799,1),(18931,1),(2322726,1)]; 3xc: [(881799,3),(5826302,3),(18931,3),(8690100,3),(4866471,7),(3073318,7)]
captain mult 1 in XI: []; vice mult > 1: [(18931, 8, 411, 2)]; captain with no player_gw row: []; picks without a player_gw row: 0
```
- The rule "captain 0 minutes in the gameweek (all fixtures summed, a blank = 0) -> the vice gets the captain's multiplier" is FPL's: the captaincy transfers to the vice when the captain plays 0 minutes in the gameweek. Summing `player_gw` rows is right for a double (0 in one match, played in the other = played). Only settled gameweeks are checked (`if ev in settled` when picks are loaded), so the minutes are final.
- Where the new rule accepts and the old stopped: only a vice in the XI stored at `CHIP_MULT.get(chip, 2)` while the captain has 0 minutes, which is exactly the transferred armband. It cannot accept a wrong multiplier silently anywhere else: the captain's own row and every other row keep the old rule, and a promoted vice on the bench keeps the bench rule.
- The prereg's stated limits, traced through the code: a captain on 0 minutes left in the XI (no substitute, or a Bench Boost week) is stored by FPL at x1 while the rule still wants x2 -> `MissingInput` -> check 31 WARN, no number printed; a vice on 0 minutes too: in the XI FPL stores x2 and the rule wants x2 (accepted; correct, the armband transfers whatever the vice's minutes), on the bench the bench rule (accepted). Neither case is in the data. The rule never guesses.
- Downstream: `league_eo` sums `w * mult` from the stored picks (`data["picks"]`, unchanged by the item), so for the GW10 table the entry 18931 contribution is Haaland x2 and João Pedro x0, the multipliers as applied, which is S9's pre-registered definition ("sum of w_j x multiplier_j from each rival's last settled picks"); `captain_history` and `our_xi` use our own picks and own xP, not the multipliers or the vice. Nothing downstream reads `is_vice`. The item was right not to touch them (the prereg pins `data["picks"]` unchanged). PASS.

## (c) The tests

- `tests/test_W2fix.py`: `tempfile.mkdtemp()` per case, `shutil.rmtree` after; the toy league from `tests.test_S9.toy_league`; no `os.environ`, `subprocess`, git, timezone or locale use (grep: only `tempfile`, `mkdtemp`, `rmtree`). Both modules: `modules()` imports `fpl_league` and `tools/league` (`sys.path` has `tools`). Hermetic. PASS.
- On 8c7a34a: `python -m unittest tests.test_W2fix tests.test_W2 tests.test_S9` -> `Ran 24 tests ... OK`.
- On d2e1b43 with the new test copied in: `FAILED (failures=2)`: `test_captain_0_minutes_vice_promoted_x2` ("entry 222 GW4 player 17: multiplier 2 but the rule says 1 (chip None)' is not None : fpl_league") and `test_triple_captain_vice_promoted_x3` ("multiplier 3 but the rule says 1 (chip 3xc)"); `test_no_promotion_when_the_captain_played` passes on the old code (the guard). As reported.
- Mutations in `mut/` (both modules edited each time, restored and diffed identical afterwards; `tests.test_W2fix`):
  - M1 no promotion (`promoted = None`): FAILED (failures=2). Red.
  - M2 promotion ignoring the chip (`expected_multiplier(pos, True, None)` for the vice): FAILED (1: x3 test). Red.
  - M3 promotion whatever the captain's minutes (`if caps else None`): FAILED (1: no-promotion test). Red.
  - M4 only one double's fixture counted (`=` instead of `+=`): FAILED (1: no-promotion test, the (30, 0) double). Red.
  - M5 (mine) no row = played (`.get(..., 1)`): OK, 3 tests pass. Survives: every test inserts a `player_gw` row for the captain, so "no row = 0 minutes" is pinned in the prereg but not tested. In the real data no pick lacks a row for its event (0 of 945). A coverage note for a later item, not a failure of this one (the prereg's four mutations are the acceptance; all four are red).
  - M6 (mine) the promoted vice always x2 whatever the chip or slot: FAILED (1: x3 test). Red.
  - M7 (mine) the vice looked up on the wrong gameweek (`ev - 1`): FAILED (failures=3). Red.
  Check 6 PASS.

## (d) The real data

`fpl_sections.sections(real, now=2026-11-03 16:00 UTC)`, my own copy of w2fix_real:
```
=== old (d2e1b43)
CHIPS -> CHIPS OK 35 lines
LEAGUE -> LEAGUE SKIPPED: entry 18931 GW8 player 411: multiplier 2 but the rule says 1 (chip None)
=== new (8c7a34a)
CHIPS -> CHIPS OK 35 lines
LEAGUE -> LEAGUE OK 51 lines
   | LEAGUE  2026-11-03: settled through GW8, 30 gameweeks left; coming deadline GW10 (GW9 played, not yet settled); points net of hits; B=10000, 90% CI, seed 20261018; information only
   |   scores from the totals chain (RULING S9 decisions, point 2): every stored row equals the chain
   |   pooled sigma_d = 18.30 [12.23, 20.04] points a gameweek (root mean square over rivals); our sigma = 16.17 [7.75, 19.77]; without chip weeks sigma_d = 15.30 [7.21, 17.98]
   |   variance line = sigma_d x sqrt(n) = 100.2 points
   |   rival                   n         sigma_j [90%]        sigma_dj [90%]    rho   gap        P(above j) [90%]  line
   |   ReturnOfTheDjedi FC     8    22.96 [13.0, 28.3]    20.17 [11.5, 24.2]   0.51    42    0.338 [0.265, 0.351]  inside
   |   Bruno Dos Tres          8    21.18 [12.8, 25.0]    18.75 [10.9, 23.0]   0.52    50    0.309 [0.228, 0.324]  inside
   |   Skori FC                8    23.21 [11.7, 30.0]     22.08 [6.6, 28.3]   0.42   -26    0.602 [0.594, 0.651]  inside
   |   No More Mr. Rice Guy    8     24.18 [5.8, 29.7]     12.47 [7.9, 14.8]   0.88    20    0.421 [0.383, 0.428]  inside
   |   Revelstoke FC           8    20.33 [10.5, 26.2]    20.19 [11.4, 25.1]   0.41    31    0.379 [0.322, 0.389]  inside
   |   PyroNeniZlocin          8     13.85 [8.6, 16.2]     14.16 [7.2, 18.0]   0.56   -86    0.805 [0.783, 0.900]  inside
   |   threat set (rivals ahead of us): ReturnOfTheDjedi FC w=0.259, Bruno Dos Tres w=0.271, No More Mr. Rice Guy w=0.227, Revelstoke FC w=0.243
```
The fixed check passes every stored pick of the 8 settled gameweeks (LEAGUE OK means `check_multipliers` raised nothing over all 56 settled entry-gameweeks x 15 picks). Matches the main session's (5). PASS.

## Checks of the agent file

1. Point-in-time: n/a as a forecast check (the item produces no forecast, feature or metric; the LEAGUE section is information only). The new inputs are the final minutes of settled gameweeks (picks are loaded only for `ev in settled`, settled = data_checked and every fixture finished), keyed (player, event) to the same gameweek as the picks; the item adds no input that a forecast reads. The projection log is read-only here (`E.read_log`). PASS (nothing to leak).
2. Clean-checkout suites (`python -m unittest discover -p "test*.py"`, bare, from git archives): before (d2e1b43) `Ran 752 tests in 243.5s OK (skipped=10)`, after (8c7a34a) `Ran 755 tests in 240.9s OK (skipped=10)`. PASS.
3. Re-run of the pre-registered evaluation: n/a (no metric); the acceptance tests and the real-data section run are reproduced above. PASS.
4. Metric/filter/bootstrap/threshold: n/a per the prereg; the ruling (Boris's message) is in the prereg verbatim; the fix was pinned before the code; no re-tuning (one code commit). PASS.
5. Recording path: the diff touches no recording code (`fpl_edge.py` imports no `fpl_league`; `fpl_league` is imported only by `fpl_sections.py` and the two tests; `fpl_league.py` opens nothing for writing). SHA-256 of `projection_log.csv` after the old and new section runs on my copy = a4145758... = w2fix_real = C:/GIT/FPL-data, byte-identical. PASS.
6. Mutation spot-check: four pinned mutations red, two of mine red, one of mine (no-row path) survives; see (c). PASS with the coverage note.
7. Secrets: `grep -i "apikey=\|api_key\|authorization\|bearer\|ODDS_API"` over `fpl_league.py`, `tools/league.py`, `tests/test_W2fix.py`, `prereg/W2fix.md`: no match. PASS.

VERDICT: PASS
