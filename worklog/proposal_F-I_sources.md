# F-I — source proposal for Step 16 parts 3–4 and Step 18 (for Boris's OK; nothing downloaded)

Written 20 Oct 2026, Part F item F-I, verbatim:

> F-I. Step 16 parts 3-4 and Step 18: first a source proposal for Boris
> (URL, size, licence, what each gives): cup draws and dates, the 2026/27
> European calendar, club ratings built from football-data results (E0-E3
> and EC). No download before his OK. Then part 3 (cup Monte Carlo), part 4
> (point-in-time backtest 2024/25 and 2025/26, Brier skill >= 0.10 v the
> base rate), then Step 18 (second-half chips, replay 2025/26, gain >= 0 v
> the default order of Part C rule 10). Needed before the GW19 deadline (Fri
> 1 Jan 2027 18:30 UTC).

How this was checked:
- Pages were only read.
- File sizes come from HTTP HEAD requests (Content-Length after the
  redirect), 20 Oct 2026 ~07:10 UTC. No file was fetched.

## 1. Club ratings: football-data.co.uk results, English tiers 1–5

| what | URL (season code SS: 2324, 2425, 2526, 2627) | size (HEAD) |
|---|---|---|
| Premier League | `https://www.football-data.co.uk/mmz4281/SS/E0.csv` | 2425: 197,110 B; 2526: 203,438 B |
| Championship | `.../mmz4281/SS/E1.csv` | 2425: 286,983 B; 2526: 294,390 B |
| League One | `.../mmz4281/SS/E2.csv` | 2425: 286,638 B; 2526: 288,636 B |
| League Two | `.../mmz4281/SS/E3.csv` | 2425: 287,557 B; 2526: 290,077 B |
| National League | `.../mmz4281/SS/EC.csv` | 2425: 276,264 B; 2526: 276,074 B |

- **Proposed:** the seasons 2023/24, 2024/25, 2025/26 and 2026/27 to
  date, 5 files each: 20 files, about 5 MB. E0 2023/24 and 2024/25 are
  already in the repo (S10b).
- **Gives:** every league result with its date (FTHG, FTAG) and
  pre-closing odds. From these, ratings across tiers 1–5, so that a cup
  tie against a lower-league club has a strength. The plan is our own
  rating (S5's time-decayed Dixon-Coles fallback, fitted on all five
  tiers with tier offsets), point-in-time at each date.
- **Licence:**
  - No explicit licence on the download page. Its text says "My data is
    free", and data notes and a legal disclaimer are linked.
  - The disclaimer could not be read today (HTTP 429), so it needs one
    look before the download.
  - The same terms already cover E0 (S5, S10b, approved by ruling).
- The record follows the Step 1 pattern: URL, fetch time and SHA-256 in
  `worklog/downloads_<date>.md`. The files are data only, read with
  `python -I`.

## 2. Cup dates and draws, 2026/27 (FA Cup, Carabao Cup)

| what | source | size | licence |
|---|---|---|---|
| FA Cup round dates | `https://www.thefa.com/competitions/thefacup/round-dates` (official) | one HTML page | "© The FA, all rights reserved"; facts (dates) only |
| Carabao Cup round dates | efl.com (not reached; club sites carry the EFL's dates) | one page | EFL copyright; facts only |
| each round's draw (who plays whom, home/away) | thefa.com / efl.com after each draw (BBC Sport as a cross-check) | one page per draw | copyright; facts only |

- **Proposed:** a hand-kept `cups_2026-27.csv` (competition, round, date,
  home, away, source URL, read at UTC). It is typed from the official
  pages after each draw: facts, a few KB, no scraping.
- **Gives:** which Premier League clubs are still in each cup, and on which
  dates. That is the input to part 3 (P(blank) and P(double) per club and
  gameweek).
- **Read today (to be re-checked on the official pages before use):**
  - FA Cup (official page): R3 9 Jan 2027, R4 13 Feb, R5 6 Mar, QF 3 Apr,
    SF 24 Apr, final 22 May 2027.
  - Carabao Cup (EFL dates as published by clubs): R4 week of 26 Oct
    2026, QF week of 14 Dec, SF1 week of 11 Jan 2027, SF2 week of 1 Feb,
    final 21 Mar 2027.
- **The backtest (part 4) needs 2024/25 and 2025/26 too:**
  - Proposed: the Wikipedia season pages "2024–25 FA Cup", "2024–25 EFL
    Cup", "2025–26 FA Cup", "2025–26 EFL Cup".
  - They are CC BY-SA 4.0: attribution, and share-alike if a derived file
    is published. Each is one HTML page of about 300–500 KB, read once.
    The round dates and ties would be typed into
    `cups_<season>.csv`, with the page revision id.
  - openfootball (public domain) has the leagues but no cup files in its
    england repo, so it does not cover this.

## 3. The 2026/27 European calendar

| what | source | size | licence |
|---|---|---|---|
| Champions League dates | uefa.com fixtures pages (official) | HTML | UEFA copyright; facts only |
| Europa League and Conference League dates | UEFA's "club competition calendar 2026/27" (official page or PDF; URL to be confirmed on uefa.com) | one page / PDF | UEFA copyright; facts only |

- **Proposed:** a hand-kept `europe_2026-27.csv` (competition, stage,
  dates, the English clubs in it, source URL, read at UTC).
- **Gives:** the midweeks taken by English clubs in Europe. Those
  constrain where postponed league matches and cup ties can go (part 3's
  "midweeks free given European fixtures").
- **Read today:**
  - Champions League league phase: 8–10 Sep, 13–14 Oct, 20–21 Oct,
    3–4 Nov, 24–25 Nov, 8–9 Dec 2026, 19–20 Jan, 27 Jan 2027.
  - Champions League knockouts: play-offs 16–17 / 23–24 Feb; R16 9–10 /
    16–17 Mar; QF 6–7 / 13–14 Apr; SF 27–28 Apr / 4–5 May; final 5 Jun
    2027 (Madrid).
  - These come from UEFA's page plus two secondary sources. The Europa
    League and Conference League dates were not found reliably today, so
    UEFA's own calendar is needed.

## 4. Not proposed

- **clubelo.com's CSV API** (`api.clubelo.com/<date>`): Elo for every
  European club. No terms of use were found, and F-I asks for our own
  ratings from football-data, so it is not used.
- **Paid APIs** (Sportradar, TheStatsAPI, matchesio): need keys and
  terms; not needed.

## Decisions for Boris

1. Download the 20 football-data files (2023/24–2026/27, E0–E3 and EC;
   about 5 MB) after one look at its disclaimer page?
2. Keep the 2026/27 cup and European dates and draws as hand-typed CSVs
   from the official pages (facts only, source URL and read time per row),
   rather than any download?
3. For the part 4 backtest, read the four Wikipedia cup pages (2024/25,
   2025/26; CC BY-SA) and type their rounds into CSVs with the revision
   ids?
