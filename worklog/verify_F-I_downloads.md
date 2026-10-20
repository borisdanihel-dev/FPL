# Verifier report: F-I part (1), the football-data downloads

Verifier: backtest-verifier, model Fable 5.1 (claude-fable-5-1), effort high.
Agent file read from disk first (`.claude/agents/backtest-verifier.md`, 20 Oct); where it
differs from the loaded instructions, the file on disk governs. Run 20 Oct 2026, ~16:25-16:40 UTC.

Item: data acquisition only (no model, no runner code, no metric). Record under test:
`worklog/downloads_2026-10-20.md`, commit aab64bf on branch `fi-wip` (worktree
`.../scratchpad/fi`). Nothing was re-fetched from football-data's data folders; the only
pages I read were `disclaimer.php`, `englandm.php` and `notes.txt`, saved to my scratch
folder (`.../scratchpad/vfi/pages/`) and read by my own scripts run with `python -I`
(`.../scratchpad/vfi/scripts/check_fd.py`, `page_text.py`). Every downloaded CSV was
opened only by `check_fd.py` under `python -I`, paths passed as arguments; nothing was
executed, sourced or piped from any download folder.

## Prereg / ruling

- There is no `prereg/F-I.md`. The ruling is verbatim in `prereg/S8c.md` line 74 and
  `prereg/S15.md` line 212 on master (both read directly): "F-I: yes to all three. (1)
  football-data: read the disclaimer first; if it restricts personal non-commercial use,
  stop and park. 20 files, python -I, URL, fetch time and SHA-256 in
  worklog/downloads_<date>.md. ..." Identical to the text in the launch message and to
  the quote at the top of the record.
- Committed before the item: the ruling landed in de8ca68 (20 Oct 13:23:54 +0200) and
  5c90e08 (13:32:27 +0200); the proposal is 6761980 (09:09:09 +0200); the record is
  aab64bf (16:18:59 +0200). Order holds. PASS.

## Check 1. The disclaimer (and the site's data notes)

- `https://football-data.co.uk/disclaimer.php`: HTTP 200, "Updated: 20/10/26". The body is
  one section, "Liability Disclaimer", five paragraphs: no guarantee of correctness; not
  betting advice; no liability for betting losses; use for information only where betting
  is not permitted, local law is the user's responsibility; under-18s must not gamble;
  advertised bookmaker offers carry their own terms. Word counts in that section:
  commercial 0, personal 0, licen- 0, copyright 0, permission 0, redistribut- 0. It
  restricts nothing about personal non-commercial use. The record's summary ("a liability
  disclaimer ... nothing restricts personal or non-commercial use") is accurate. The
  ruling's stop condition does not apply.
- `https://www.football-data.co.uk/englandm.php`: HTTP 200. The page links the disclaimer
  (`disclaimer.php`) and `Notes.txt` (`notes.txt`); its only usage sentence is "My data is
  free, but for those who want a subscription API service, I am now partnering with
  TheStatsAPI."
- `https://www.football-data.co.uk/notes.txt`: HTTP 200, 7,686 bytes, 201 lines. It is a
  column key ("Key to results data", "Match Statistics", odds abbreviations). No licence,
  terms, copyright or usage restriction anywhere in it (the only "free" hits are "Free
  Kicks Conceded").
- Note, not a defect: the site states no explicit licence; it says the data is free and
  restricts nothing. The ruling asked only whether personal non-commercial use is
  restricted; it is not.
- PASS.

## Check 2. The record against the files

Recomputed by `check_fd.py` for all 20 rows (output: `.../scratchpad/vfi/check_fd.out`):

- Raw download `dl_fd/<SS>_<DIV>/<DIV>.csv` and placed
  `C:\GIT\FPL\historical\football-data\<season>\<DIV>.csv`: SHA-256 identical to each
  other and to the record's column, bytes identical to the record, the fetch log
  (`fd_fetch_log.tsv`) and the file length: 20 of 20.
- Match count (non-blank data rows) and first/last Date equal the record: 20 of 20
  (e.g. 2023-24 E0 380, 11/08/2023 - 19/05/2024; 2026-27 E0 70, 21/08/2026 - 19/10/2026,
  the chronological maximum date is also 19/10/2026, as the record says).
- URL pattern: every row is `https://www.football-data.co.uk/mmz4281/<SSSS>/<DIV>.csv`
  with the season code and DIV matching the row's path: 20 of 20. The log's effective
  URL after redirect is `https://football-data.co.uk/...` with HTTP 200: 20 of 20.
- Fetch times: the record's times equal the log's, strictly increasing, 14:17:06Z to
  14:18:16Z (3-4 s apart). The raw files' mtimes (UTC) are 14:17:07 to 14:18:17, each
  within 1 s after its logged time; the placed copies are 14:18:38 (after the last fetch,
  i.e. the reader ran once all 20 were down).
- Read-only: all 20 placed files are `-r--r--r--` and carry the Windows R attribute
  (`attrib`): 20 of 20.
- Byte identity with S10b: `historical/football-data/2023-24/E0.csv` ==
  `tools/odds/E0_2023-24_fetched_2026-10-19.csv` (sha b2e0...), and 2024-25 E0 ==
  `E0_2024-25_fetched_2026-10-19.csv` (sha d0c8...), both True, read from the s8c
  worktree.
- The reader's generated rows (`scratchpad/fd_rows.md`) are byte-identical to the
  record's table (diff empty). Columns 98-133 as the record says (98, 106, 112, 114, 120,
  124, 132, 133 across files).
- PASS: no discrepancy on any of the 20 rows.

## Check 3. The reader

`scratchpad/scripts_fd/read_fd.py` (2,168 bytes, in its own folder, separate from
`dl_fd/`). It opens each file with `open(src, "rb")`, decodes as UTF-8 (strict), asserts
the HTTP code was 200 and the logged size equals the byte length, asserts `"<html"` is not
in the first 2,000 characters, parses with `csv.reader`, asserts all of Div, Date, HomeTeam,
AwayTeam, FTHG, FTAG, FTR are in the header, asserts the set of Div values is exactly the
file's own DIV, copies with `shutil.copyfile`, sets `S_IREAD` only, and re-hashes the
placed copy against the raw hash. No `exec`, `import`, `subprocess`, `os.system` or shell
use anywhere; nothing in the download folders is a `.py` or anything but the 20 CSVs. My
own `-I` reader repeated all of those validations independently and they hold on all 20
files. Minor nit, not a defect: the decode line's two branches are identical
(`utf-8-sig` either way). PASS.

## Check 4. Completeness and what was committed

- Download root `scratchpad/dl_fd/` holds exactly 20 files, one per folder:
  {2324,2425,2526,2627} x {E0,E1,E2,E3,EC}. Nothing else downloaded there (the older
  `scratchpad/dl/` is S10b's, 19 Oct). Placed tree: exactly the same 20 under four
  season folders.
- These are exactly the 20 files the ruling ("20 files") and the proposal
  (`worklog/proposal_F-I_sources.md` on fi-wip, section 1: "2023/24, 2024/25, 2025/26 and
  2026/27 to date, 5 files each: 20 files") name.
- `git show aab64bf --stat`: one file, `worklog/downloads_2026-10-20.md`, +63. The commit
  is only on `fi-wip` and `origin/fi-wip` (`git branch -a --contains`); not on master.
  `git diff --stat master...fi-wip`: only the two worklog files (record and proposal).
  The fi worktree is clean (`git status --short --ignored` empty before this report).
- `git check-ignore -v` on master: `.gitignore:17:historical/` matches
  `historical/football-data/2023-24/E0.csv`; the placed files cannot be committed.
- No runner file references `historical/football-data` (grep over `*.py`/`*.yml`: only
  `tools/` and a test string mention "football-data", all pre-existing). PASS.

## Check 5. Secrets

The record and the reader: no `apiKey=`, `api_key`, `Authorization`, `Bearer`, `secret`,
`token`; the only long hex strings are the twenty 64-hex SHA-256 values (not keys). The
URLs carry no query strings. PASS.

## Agent-file checks not applicable to this item

- 1 (point-in-time), 3 (evaluation re-run), 4 (metric/threshold): no forecast, feature or
  metric is produced; nothing to leak-test. The 2026/27 files are season-to-date results
  (newest 19 Oct, before today's fetch) and are data for later items, which will carry
  their own point-in-time checks.
- 2 (clean-checkout test run): no code changed, so before == after by construction. One
  run of `python -m unittest discover -p "test*.py"` in the fi worktree at aab64bf:
  614 tests, OK (skipped=10), 257 s (`.../scratchpad/vfi/suite_fi.txt`).
- 5 (recording path): `master...fi-wip` changes no code, so the projection log cannot
  have moved; nothing regenerated.
- 6 (mutation): no new logic in the repo; the reader is a scratch script that is not
  committed. N/A.

## Written by this run

Only this file, `worklog/verify_F-I_downloads.md` in the fi worktree (not committed), plus
my scratch folder `.../scratchpad/vfi/` (two scripts, three saved pages, two outputs).
Nothing pushed, nothing dispatched, no source or data file touched.

VERDICT: PASS. The disclaimer is a liability disclaimer with no restriction on personal
non-commercial use (the site says "My data is free"; notes.txt is a column key only), so
the ruling's stop condition does not apply; all 20 rows of the record reconcile exactly
with the raw downloads and the read-only placed files (SHA-256, bytes, match counts,
first/last dates, URL pattern, fetch times), the two E0 files are byte-identical to the
S10b copies, the reader validates what the record claims and executes nothing from the
download folders, exactly the 20 named files exist and only the record was committed
(historical/ is gitignored on master), and no secret appears in anything the item added.
