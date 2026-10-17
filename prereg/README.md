# prereg/ — pre-registrations

Every work item gets `prereg/<item>.md`, committed **before** any code for it.
The `backtest-verifier` agent checks the order with `git log` and fails the
item if the prereg came later. Copy `TEMPLATE.md`.

What a prereg fixes in advance, and may not change after the results are seen:

- the item id and the hypothesis;
- the data and the sample filter — point-in-time sources only; "starters"
  means forecast P(start) >= 0.8, never realised minutes;
- the comparison;
- **one** primary metric; any secondary metric is marked information only;
- the bootstrap: unit = gameweek, 10,000 resamples, 90% CI;
- the pass threshold;
- the line "no re-tuning after viewing results".

A descriptive or data-pipeline item has no pass/fail metric: its prereg lists
the acceptance tests instead, and the verifier runs checks 1, 2, 5, 6 and 7
plus those tests.

A ruling-only prereg is acceptable for setup and docs items if it lists acceptance tests. Any item that produces a forecast, feature or evaluation metric fills every template row.

The full protocol is in `BUILD_PLAN.md` ("Standing rules") and `CLAUDE.md`
("Work-item protocol").
