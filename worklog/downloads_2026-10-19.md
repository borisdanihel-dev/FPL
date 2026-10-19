# Downloads of 19 Oct 2026 (RULING morning 19 Oct, points 2-3)

Copied from `historical/DOWNLOADS_2026-10-19.txt`, which is gitignored and sits
beside the files. The files themselves live under `historical/`, also gitignored
and set read-only.

## vaastav/Fantasy-Premier-League, pinned to commit `9779cdbc0c07f6c900c2d0c181ddf6bb9c800f88` (point 2)

| file | fetched (UTC) | bytes | SHA-256 |
|---|---|---|---|
| `historical/2025-26/players_raw.csv` | 2026-10-19T06:24:06Z | 380363 | `412ce0172016f8f98f25177dc6de9f3cd2a8ec7a6135f9aa638d7fdee784d67b` |
| `historical/2018-19/fixtures.csv` | 2026-10-19T06:24:08Z | 636313 | `f50cbc202ea89289e359a74c2e82e988965f063f4016bbe49426d3de483cc046` |
| `historical/2019-20/fixtures.csv` | 2026-10-19T06:24:10Z | 668794 | `81851c3c55373c443aa6b7062be85d5710d61ab784239e9810655b343728e0ed` |
| `historical/2020-21/fixtures.csv` | 2026-10-19T06:24:11Z | 660303 | `75ca4859c7898bff9c73055337651893c041e596462d08935f2a6964c437f65d` |
| `historical/2021-22/fixtures.csv` | 2026-10-19T06:24:13Z | 668973 | `9fc11cc675ff49dd5b8858211aa5cbe08375e064810536931e0ac38c060dee64` |
| `historical/2022-23/fixtures.csv` | 2026-10-19T06:24:15Z | 696260 | `e783060da73700d4ec6fd12acec4568524eac8bb3ba3ccd8ce68a374dadba8f8` |
| `historical/2023-24/fixtures.csv` | 2026-10-19T06:24:17Z | 712532 | `d8521bdbb80edb5141bc17df71bf6026275f2e56fd6a6dc6041b3ae23a39ce6a` |
| `historical/2024-25/fixtures.csv` | 2026-10-19T06:24:19Z | 751413 | `ce696e187569ca7c45da2562811d3c38f525b58e65575531be37bebd0769ee28` |

Each file's URL is
`https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/9779cdbc0c07f6c900c2d0c181ddf6bb9c800f88/data/<season>/<file>`.

Not downloaded, because vaastav has no such file:
- `fixtures.csv` for 2016-17 and 2017-18;
- a gameweek-deadlines file for any season (the `gws/` folders hold only
  per-gameweek player CSVs, `merged_gw.csv` and xP files).

Step 16 part 1 is parked on both (`worklog/SESSION_STATE_A.md`).

## The FPL API: the live `game_config` (point 3, Q1) and the 2026/27 positions

| file | source | fetched (UTC) | bytes | SHA-256 |
|---|---|---|---|---|
| (not kept) | `https://fantasy.premierleague.com/api/bootstrap-static/` | 2026-10-19T06:17:43Z | 1783844 | `4a3da66e490f4dbcae3a7eb4d9a3a551c7fd855a6305834adc5d660d328bc825` |
| `historical/2026-27/game_config.json` | `game_config` of the bootstrap above | 2026-10-19T06:17:43Z | 2978 | `a72a99083f5b29988b8f53eaa9ad557b250a8c3c5fff7d091968ce38bc0f69ff` |
| `historical/2026-27/elements_positions.csv` | `id, code, element_type, web_name` of its 668 elements | 2026-10-19T06:17:43Z | 14000 | `ac3dc891f3e11e4dbdae147bb6bf455fd61ff7d1813f2a1f4a1ebf85174ffd2c` |

## Incident, 19 Oct about 06:45 UTC

A command of mine used an unquoted shell heredoc. Bash took backtick-quoted
names in it as command substitutions, ran the local manifest as a script,
and through it ran `players_raw.csv` and the seven `fixtures.csv` files line
by line as shell commands.

**What it did:**
- 3,423 lines ended "command not found";
- `players_raw.csv` stopped at line 749 on an unbalanced quote, and the
  manifest at line 13 on a syntax error;
- the only shell metacharacters in the files are 162 `&` inside URL query
  strings. What followed each was a variable assignment (`utm_medium=...`),
  not a command.

**Checked after:**
- no file was created or changed in the repository;
- all ten files match the SHA-256 above;
- no real command ran.

From then on: quoted heredocs or the file-writing tool only.
