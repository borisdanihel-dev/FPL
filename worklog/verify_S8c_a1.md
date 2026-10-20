# Verifier report: S8c amendment 1 (the cap flag, the two test gaps)

Verifier: backtest-verifier, model Fable 5.1 (claude-fable-5-1), instructions
read from `.claude/agents/backtest-verifier.md` on disk first. 20 Oct 2026,
13:20-13:40 UTC.

Item: the single commit `52b2a65` on `s8c-wip`, on top of `ca96b6a` (S8c,
verified PASS in `worklog/verify_S8c.md`). Prereg: `prereg/S8c.md` on master,
"Amendment 1" section, commit `9ed7919`. Scope verified: points 2 and 3 of
"Ruling, Tue 20 Oct afternoon"; point 1 is procedure (checked only that the
diff does not contradict it: no runner file, no worklog/gw_pass output in the
commit, nothing that would move the bundle off `s8c-wip`).

Everything I ran was read-only against `C:\GIT\FPL-data` (at `63e6a44`,
clean before and after; I did not pull) and `C:\GIT\FPL\historical`. No
dispatch, no API call, no push, no `fpl_sync.py`, no `--record`, no
`fpl_nightly.py`. Scratch: `scratchpad/v8c_a1/` only. This file is the only
write in any worktree; it is not committed.

## Prereg before code

- `9ed7919` (prereg amendment 1) author/committer 2026-10-20 15:03:40 +0200.
- `52b2a65` (the code) author/committer 2026-10-20 15:17:14 +0200.
- `git log -- prereg/S8c.md` on master: `de8ca68`, then `9ed7919`; nothing
  after. `git diff 9ed7919 HEAD -- prereg/S8c.md` is empty; `git status`
  shows the file unmodified. The amendment text is the committed text.
- The prereg lives on master, not on `s8c-wip` (`9ed7919` is not an
  ancestor of `52b2a65`); the commit message names "prereg master 9ed7919".
  Ordering by time holds. PASS.

## The diff (`git diff ca96b6a 52b2a65`)

7 files, +278/-13: `tools/capflag.py` (new, 38 lines), `tools/builder.py`
(+1 import, 2 flag sites), `tools/gw_pass.py` (+1 import, 5 flag sites),
`tools/planner.py` (+1 import, 3 flag sites), `tools/planner_live.py` (+1
import, 4 flag sites), `tests/test_S8c.py` (+6 tests), `tests/test_S15.py`
(+2 tests). No runner file (`fpl_*.py`, `checks.py`, `test_fpl.py`,
`.github/`, `requirements.txt`): PASS. No CHANGELOG or worklog in the commit
(those follow the verifier per the protocol).

## Check 1: point 3, the cap flag against the pinned design

**The rule** (`tools/capflag.py`): `breaks(rows)` counts `team` over rows
with `pos in (1, 2)` and returns `sorted((club, n))` for `n > 2`; `after(squad,
outs, ins)` = squad minus the ids in `outs` plus `ins`; `flag(rows)` =
`"   breaks the cap: " + ", ".join(f"{club} {n}")` (three spaces, ", "-joined,
sorted by club) or `""`; `move_flag(squad, outs, ins) = flag(after(...))`.
Matches the design word for word (more than 2 GK+DEF of one club among the
15; a move judged on our 15 minus outs plus ins; the exact text). PASS.

**Every pinned location carries it** (read in the diff and the full files):

| pinned location | code | flagged on |
|---|---|---|
| planner_live: top 5 | `plan()` loop over `scored[:TOP]` | `move_flag(squad, ev outs, ins)` |
| planner_live: DEFAULT | `out(f"  DEFAULT: ...") + move_flag(...)` | our 15 after `scored[0]` |
| planner_live: simple rule | `+ move_flag(squad, simple[0], simple[1])` before the "; on the planner's score" tail | our 15 after the rule's move |
| planner_live: Bench Boost top 3 | loop over `bb[:TOP_BB]` | `move_flag` |
| planner.py live: each schedule's top plans | `plan = (...) + move_flag(squad, ...)` | per plan |
| planner.py live: decay alternative in brackets | `flags.append(... + move_flag(squad, alt[0] outs, ins))` | each alternative, where named |
| planner.py live: exploratory lines | `plan = ... + move_flag(...)` then the "score ..." tail | per line |
| gw_pass section 3: BASELINE | `baseline_note` returns `plan_text(b_outs, b_ins) + move_flag(inp["squad"], ...)` | |
| gw_pass section 3: planner top plan, planner no hits | `p_text`, `n_text` with `move_flag`; precedence `(A + B) if top else "none"` is correct | |
| gw_pass section 3: named plans | `plan = (... or "roll") + move_flag(inp["squad"], ev outs, ins)`; `ev is None` rows `continue` before it | |
| gw_pass section 5: our 15 summary line | `"... (slots 1-11, the bench order and the captain)" + CF.flag(squad)`, `squad = CH.my_squad(d)` | |
| builder live: formation line | `+ CF.flag(sq_on)` | the builder's 15 |
| builder live: the rule's "beside it" line | `+ CF.flag(rsq)` (the `full` branch; the "no full squad" branch prints no squad) | the rule's 15 |

`squad` at every move site is `CH.my_squad(d)` (rows with `id, team, pos`);
`rsq` and `sq_on` carry `team` and `pos`. A "roll" is judged on our 15
unchanged, which is the design's "squad after it". PASS.

**Anything missed?** I read every `out(` in `gw_pass.bundle`, `chips.live`,
`planner.live`, `planner_live.plan` and `builder.live`. Unflagged prints:
`chips.live` (chip values and XI totals as numbers; no squad), `league.report`
(rivals), the keeper line, `points_pmf.captain_table`/`print_options` (our
players' distributions), `xp_v2_live.report` (not printed in the bundle),
the builder's per-player rows and the rule's per-position rows (the squad's
flag is on its summary line, as pinned), and the lambda source lines. Every
one is on the design's "not flagged" list or prints no squad and suggests
no move. The builder's `--bb` and `--wildcard` modes share `live()` and so
flag their squads too. Nothing missed. PASS.

**Print only.** The GW8 runs at `ca96b6a` (clean `git archive` copy) and at
`52b2a65` (the item worktree, clean, `run.txt` commit `52b2a65...`, 0
modified files), both with `--out` under `v8c_a1/`:

| output | ca96b6a vs 52b2a65 |
|---|---|
| `planner_live_gw8.txt` | byte-identical (sha256 `7a95f1b8...`) |
| `gw8_pass.txt` | byte-identical (sha256 `b95a3a80...`; both runs in the same minute, so the "generated" stamp matches too); 0 flags |
| `builder_freehit.txt` | one line differs, line 20, the rule's "beside it" line, by the suffix `   breaks the cap: ARS 3` only |

Every score, gain, rank, plan, formation, spend and objective is identical.
PASS.

**The GW8 flags are right.** Independent check (`v8c_a1/capcheck.py`, run
with `python -I` on `fpl_export_gw7.json`, my own count, not `capflag`):
our 15's GK+DEF by club = BHA 1, LEE 1, ARS 1, EVE 2, COV 1, BRE 1 (keeps
the cap, so section 5 is rightly unflagged). Every printed move in
`planner_live_gw8.txt` and `gw8_pass.txt` (Branthwaite/Tarkowski/Thomas/
Muharemović -> De Cuyper or Vuskovic (BHA, 1 -> 2), Tarkowski -> Gabriel
(ARS, 1 -> 2), the two-move plans, Thiago -> João Pedro, Haaland ->
Kostoulas / Calvert-Lewin) leaves every club at <= 2: no flag expected, none
printed. The three-layer rule's squad holds Raya (GK ARS), Gabriel and
Calafiori (DEF ARS) = ARS 3: flagged, correctly. The builder's own squad
holds Gabriel and Calafiori only (ARS 2): unflagged, correctly. PASS.

**Reproduction of the main session's runs.** My `52b2a65` outputs equal the
main session's in `scratchpad/s8c_a1_live/`: `planner_live_gw8.txt` sha256
`7a95f1b8...` and `builder_freehit.txt` sha256 `02e0e1c6...` identical;
`gw8_pass.txt` differs only in the "generated 13:20 UTC" vs "13:25 UTC"
stamp on line 1. Their `run.txt` files name commit `52b2a65`, 0 modified
files. PASS.

## Check 2: point 2, the two gaps (tests only)

- `tests/test_S8c.py::UnpricedFixture.test_the_unpriced_fixture_prints_fallback`:
  a toy snapshot pricing only the first of week t's fixtures; asserts week t's
  sources are exactly one "odds" and the rest "fallback", that the sources
  equal `builder.live_matrix(...)[4]`, and that the printed `lambdas GW<t>`
  line is the sources joined and contains " fallback". Kills m6 (every
  source printed "odds"): my mutation m14 below, RED.
- `tests/test_S15.py::Live.test_the_rule_under_bench_boost`: `B.live(..., "bb")`;
  asserts `rule_value == objective(rule, weeks_xp, 1.0, True)` to 1e-9 and
  that it differs from `objective(..., False)` by more than 1e-6. Kills n4
  (the rule scored without `bench_full`): my mutation m15 below, RED.
- No tool code changed for point 2 (the diff's tool hunks are the flag sites
  and imports only). PASS.

## Check 3: clean-checkout suites

`git archive` of each commit into `v8c_a1/before` and `v8c_a1/after`;
`ODDS_API_KEY` unset in the environment (`env -u`); `python -m unittest
discover -p "test*.py"`.

| run | result |
|---|---|
| ca96b6a, bare | Ran 756 tests in 292.4s, OK (skipped=10) |
| 52b2a65, bare | Ran 764 tests in 270.8s, OK (skipped=10) |
| 52b2a65, `FPL_DATA_DIR=C:\GIT\FPL-data` | Ran 764 tests in 271.3s, OK (skipped=3) |

+8 = the 6 new tests in `test_S8c.py` (5 -> 11) and 2 in `test_S15.py`
(15 -> 17). The item's tests pass in the bare archive with no data folder
and were also run alone from a clean copy by the mutation harness (11 and
17 tests): hermetic (tempfile toys, S6d's toy season). PASS.

## Check 4: runner path

- `git diff --name-only ca96b6a 52b2a65` filtered on `fpl_*.py`, `checks.py`,
  `test_fpl.py`, `.github/`, `requirements`: empty.
- `tests/test_S3.py::FastTrack.test_the_nightly_imports_nothing_under_tools_or_analysis`
  parses every top-level `.py` with `ast` and rejects any import of a module
  name under `tools/` (it lists the folder, so `capflag` is included) and
  any `sys.path` insert naming tools; it passed in all three suites. A grep of
  `fpl_*.py` and `checks.py` for `tools`/`capflag` imports: none. PASS.

## Check 5: mutations (own choosing, clean copies under `v8c_a1/mut`)

| id | mutation | result |
|---|---|---|
| m1 | capflag `CAP = 2` -> `3` | RED (5 failures, S8c + S15) |
| m2 | capflag join `", "` -> `"; "` | RED |
| m3 | capflag `after()` keeps the outs (`gone = set()`) | RED |
| m4 | capflag `GKDEF = (1, 2)` -> `(1,)` | RED (6 failures) |
| m5 | planner_live DEFAULT line unflagged | RED |
| m6 | planner_live Bench Boost lines unflagged | RED |
| m7 | planner.py decay alternative unflagged | RED |
| m8 | planner.py exploratory lines unflagged | RED |
| m9 | gw_pass BASELINE unflagged | RED |
| m10 | gw_pass named plans unflagged | RED |
| m11 | gw_pass section 5 (our 15) unflagged | RED |
| m12 | builder rule's "beside it" line unflagged | RED |
| m13 | builder formation line unflagged | RED |
| m14 | point 2: every source printed "odds" | RED |
| m15 | point 2: the rule scored with `bench_full=False` | RED |
| m16 | capflag `sorted(...)` replaced by Counter order | survived |

m16 is a coverage note only: the code does sort, and the helper test's
two-club case ("ARS 4, LIV 3") happens to insert ARS before LIV, so Counter
order equals sorted order there. Not a defect in the output; optional to
tighten (a case whose insertion order is not alphabetical). 15 of 16 red,
including four on `capflag.py` and nine on flag sites. PASS.

## Check 6: secrets

The diff `ca96b6a..52b2a65` grepped for `apiKey=`, `Authorization`,
`api_key`, `ODDS_API_KEY` and 32+-character alphanumerics: no match. The
seven files hold no key, URL with a key, or header. PASS.

## Point 1 (procedure)

Nothing in the diff touches the bundle's provenance or output path; the
tools still write `run.txt` naming the commit they ran on (my runs: commit
`52b2a65`, 0 modified tracked files). Nothing contradicts the ruling.

## Not applicable

Check 1 of the agent file (point-in-time leak: truncation, timestamp audit,
shift probe) and the recording path: the item produces no forecast, feature
or metric and touches nothing the nightly runs; `projection_log.csv` is not
read or written by any changed file. The prereg has no pass/fail metric;
the item's own acceptance checks (the diff, the suite, the GW8 runs, the
flag prints) are the checks above.

## Write guard, my side

`git status --short` after all runs: item worktree clean (this file apart,
untracked); master unchanged (`worklog/verify_W1b_pre.md` untracked as
before I started); `C:\GIT\FPL-data` clean at `63e6a44`.

VERDICT: PASS. The prereg amendment (`9ed7919`, 15:03) precedes the code
(`52b2a65`, 15:17) and is unedited since; the cap flag matches the pinned
rule and text and sits on every pinned line and on no other, judged on our
15 after each move; the GW8 outputs at ca96b6a and 52b2a65 are byte-identical
except the one rule line gaining "   breaks the cap: ARS 3", which my
independent count confirms (and confirms every unflagged move keeps the
cap); the two gap tests kill exactly the earlier m6 and n4 mutations with no
tool change; clean-checkout suites 756 -> 764 OK bare and with the data
folder; no runner file in the diff and the nightly imports nothing under
tools/; 15 of 16 mutations red (the survivor a sort-order coverage note);
no secrets.
