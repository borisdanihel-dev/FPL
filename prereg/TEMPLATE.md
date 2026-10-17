# <item id> — <title>

Committed before any code for this item.

- **Item:** <id> (BUILD_PLAN.md Step <n>)
- **Hypothesis:** <what is expected, in one or two sentences>
- **Data and sample filter:** <sources; every input point-in-time; season and
  gameweeks; "starters" = forecast P(start) >= 0.8, never realised minutes>
- **Comparison:** <the new source or rule against what>
- **Primary metric (one):** <exactly one>
- **Secondary metrics (information only):** <or "none">
- **Bootstrap:** unit = gameweek, 10,000 resamples, 90% CI.
- **Pass threshold:** <stated as a number, with the CI condition>
- **Acceptance tests (descriptive or data-pipeline items, instead of a metric):**
  <or "n/a">

No re-tuning after viewing results.
