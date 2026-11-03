# W2fix — check 31: the vice-captain promoted when the captain played 0 minutes

Committed before any code for this item.

- **Item:** W2fix (a runner fix to W2's S9 LEAGUE section; BUILD_PLAN.md Part E, W2)
- **Hypothesis:** the LEAGUE section has skipped since 26 Oct because the
  multiplier check has no vice-captain rule. FPL doubles the vice when the
  captain plays 0 minutes; the check calls that a mismatch.
- **Data and sample filter:** `fpl.sqlite`, read-only: `picks` (with
  `is_vice`), `player_gw` (minutes) and `entry_gw` (the chip). Every settled
  gameweek of the league's 7 entries.
- **Comparison:** the multiplier rule before and after, on every stored pick.
- **Primary metric (one):** n/a (a data-pipeline fix).
- **Secondary metrics (information only):** none.
- **Bootstrap:** n/a.
- **Pass threshold:** n/a.
- **Acceptance tests (descriptive or data-pipeline items, instead of a metric):**
  see "Tests" below.

No re-tuning after viewing results.

## Boris's message, Tue 3 Nov (verbatim)

Tue 3 Nov, after a week's pause (the item count resets to 0 of 6). GW10 deadline Fri 6 Nov 18:30 UTC; freeze from Thu 5 Nov 12:30 UTC.
1. Tonight's one runner change (Boris's OK given here): fix check 31. The LEAGUE section has skipped since 26 Oct: "entry 18931 GW8 player 411: multiplier 2 but the rule says 1 (chip None)". Confirm from the data that it is a vice-captain promoted when the captain played 0 minutes. Fix it in tools/league.py and its runner copy fpl_league.py, with tests for: captain 0 minutes and vice promoted to x2; the same under a triple captain (x3); no promotion when the captain played. Verifier on the diff; push dry/W2fix for the automatic dry run; on green, tag pre-W2fix, merge, push before 21:00 UTC, and tell Boris when his real run is needed. Not done by 20:30 UTC: park it to Wednesday.
2. W2 loose ends: the final verifier on a live nightly, the "W2 done" CHANGELOG entry, delete dry/W2 and data-dryrun-W2.
3. Prepare, no merge: bring w3-wip and s8c-wip up to date with master (full suites, bare and with the data), so W3 can merge Sat 7 Nov after the GW10 deadline and the S8c landing Sun 8 Nov.
Same rules: no other merges without Boris; park questions with the exact wording; stop at 6 items.

## What the data shows (data `0c61ea1`, the 2 Nov nightly; read-only)

- **Entry 18931 (ReturnOfTheDjedi FC), GW8, chip none:**
  - The captain, João Pedro (165), played 0 minutes. The stored picks are
    after FPL's automatic substitutions, so he sits at bench position 13
    with multiplier 0.
  - The vice, Haaland (411), played 90 minutes and has multiplier 2 at
    position 10.
  - This is the vice-captain promoted, as Boris read it.
- **Across every stored pick** (63 entry-gameweeks, GW1–9):
  - each has exactly one captain and one vice;
  - this is the only gameweek with a captain on 0 minutes.
- **The rule today:**
  - `expected_multiplier(position, is_captain, chip)` gives a bench slot
    (position > 11) 0, or 1 under a Bench Boost;
  - it gives the captain in the XI `CHIP_MULT.get(chip, 2)` (3 under a
    Triple Captain), and anyone else 1;
  - it never reads `is_vice` or minutes.

## The fix (pinned)

- `load` reads two more things:
  - the vice of each (entry, gameweek), from `picks.is_vice`;
  - each player's minutes per gameweek: the sum over his `player_gw` rows
    (a double counts both; no row = 0 minutes).
- **The promotion:** when the captain of a settled gameweek played 0
  minutes, the vice takes the captain's rule, `expected_multiplier(position,
  True, chip)`.
  - In the XI that is ×2, or ×3 under a Triple Captain.
  - On the bench it is the bench rule, unchanged.
- **Everything else is unchanged:**
  - the captain's own row and every other row;
  - the tuples in `data["picks"]` that the rest of the module reads;
  - the chain, the variance, the scores.
- The same change goes into `tools/league.py` and `fpl_league.py`, so the
  verbatim copy holds (the W2 copy test).
- **A stated limit:** a captain on 0 minutes left in the XI (no
  substitute), and a vice on 0 minutes as well, are not in the data.
  - The rule does not guess at them.
  - A mismatch there still stops the section with its message (check 31
    WARNs). It never prints a wrong number.

## Tests (`tests/test_W2fix.py`, hermetic, both modules)

1. The captain on 0 minutes, autosubbed to the bench (multiplier 0); the vice
   ×2: the section loads.
2. The same under a Triple Captain: the vice ×3 loads.
3. The captain played: no promotion. The vice at ×2 still stops with the
   message, and the vice at ×1 loads.
- Red on the old code. Mutations shown red:
  - no promotion;
  - promotion ignoring the chip;
  - promotion whatever the captain's minutes;
  - only one double's fixture counted.

## Then

- The full suite before and after, bare and with the data; the verifier on
  the diff; the write guard.
- `dry/W2fix` for the automatic dry run: `data-dryrun-W2fix` must show check
  31 OK.
- On green, before 21:00 UTC: tag `pre-W2fix`, merge, push; tell Boris when
  his real run is needed.
- Not done by 20:30 UTC: parked to Wednesday.
- Report `worklog/cc_2026-11-03_W2fix.md`, the verifier's
  `worklog/verify_W2fix.md`, the CHANGELOG, the state file.
