# Downloads of 20 Oct 2026 (Part F item F-I; Ruling, Tue 20 Oct, point 4 (1))

The ruling: "F-I: yes to all three. (1) football-data: read the disclaimer first; if it restricts personal non-commercial use, stop and park. 20 files, python -I, URL, fetch time and SHA-256 in worklog/downloads_<date>.md."

## The disclaimer, read first

- **Page:** https://football-data.co.uk/disclaimer.php, read 2026-10-20 at
  about 14:16 UTC (the page says "Updated: 20/10/26"). It is linked from
  the England data page, https://www.football-data.co.uk/englandm.php.
- **What it says:** it is a liability disclaimer. Football-Data does not
  guarantee correctness, gives no betting advice and accepts no liability
  for betting losses. Betting where it is not permitted is the user's
  responsibility, and under-18s must not gamble.
- **What it does not say:** nothing restricts personal or non-commercial
  use of the data. The ruling's stop condition does not apply.

## football-data.co.uk, English tiers 1–5, 2023/24–2026/27 (20 files)

Data only:
- Each file was fetched with `curl -L` into its own new empty folder in
  the session scratchpad, 3 s apart. All 20 returned HTTP 200 from
  `https://football-data.co.uk/...` after the redirect.
- A reader run with `python -I` from a separate folder checked each file.
  It is UTF-8 CSV, not HTML; it has Div, Date, HomeTeam, AwayTeam, FTHG,
  FTAG and FTR; and its Div is the file's own. The reader hashed each
  file, copied it to `historical/football-data/<season>/<DIV>.csv` and
  set it read-only.
- `historical/` is gitignored, as the vaastav files are, so these files
  are not committed. This record is the provenance.

The 2026/27 files are the season to date (the newest match is 19 Oct).
They are refreshed the same way when the backtest needs later results,
with a new record.

| file | URL | fetched (UTC) | bytes | matches | dates | SHA-256 |
|---|---|---|---|---|---|---|
| `historical/football-data/2023-24/E0.csv` | https://www.football-data.co.uk/mmz4281/2324/E0.csv | 2026-10-20T14:17:06Z | 172196 | 380 | 11/08/2023 – 19/05/2024 | `b2e057b0ed959f198b0f63d2391c01239f3608e6de5db68edab3f88e04d07ff3` |
| `historical/football-data/2023-24/E1.csv` | https://www.football-data.co.uk/mmz4281/2324/E1.csv | 2026-10-20T14:17:10Z | 251182 | 552 | 04/08/2023 – 04/05/2024 | `5737f6cc95c95092b28317f41d3123e2fb09345434efc1c84bbdf15830849ab3` |
| `historical/football-data/2023-24/E2.csv` | https://www.football-data.co.uk/mmz4281/2324/E2.csv | 2026-10-20T14:17:14Z | 250001 | 552 | 05/08/2023 – 27/04/2024 | `48e5c8d7f3fbb2a0d3ac956f066b129743789b34fe3db41dbcb31363c22fc303` |
| `historical/football-data/2023-24/E3.csv` | https://www.football-data.co.uk/mmz4281/2324/E3.csv | 2026-10-20T14:17:17Z | 250842 | 552 | 05/08/2023 – 27/04/2024 | `10da9da5badeb696d163154b26fa43875bfc9fd96d2ed81c5e4d5958e7d231ef` |
| `historical/football-data/2023-24/EC.csv` | https://www.football-data.co.uk/mmz4281/2324/EC.csv | 2026-10-20T14:17:21Z | 239299 | 552 | 05/08/2023 – 20/04/2024 | `ed369da28084d1eb5a6906f9fd7c3e84364ea4de55734a393b9d9058f12021d0` |
| `historical/football-data/2024-25/E0.csv` | https://www.football-data.co.uk/mmz4281/2425/E0.csv | 2026-10-20T14:17:25Z | 197110 | 380 | 16/08/2024 – 25/05/2025 | `d0c8ce4a96d886cf60cf101f570f4a3893844226f91c7bd769eb568c49edbfa4` |
| `historical/football-data/2024-25/E1.csv` | https://www.football-data.co.uk/mmz4281/2425/E1.csv | 2026-10-20T14:17:28Z | 286983 | 552 | 09/08/2024 – 03/05/2025 | `f34c340446c916374be66bdc2fb25b87ee7f2662712ca009653d03ac705535f9` |
| `historical/football-data/2024-25/E2.csv` | https://www.football-data.co.uk/mmz4281/2425/E2.csv | 2026-10-20T14:17:32Z | 286638 | 552 | 09/08/2024 – 03/05/2025 | `d4c0ebde3806714fe01a43935409e803ca35118d746d635480eaf9574d561c49` |
| `historical/football-data/2024-25/E3.csv` | https://www.football-data.co.uk/mmz4281/2425/E3.csv | 2026-10-20T14:17:36Z | 287557 | 552 | 09/08/2024 – 03/05/2025 | `fd8e1e2483478b14ce7d0cc0317ab4b8fc0abf6e44e76613d855212f8acd760d` |
| `historical/football-data/2024-25/EC.csv` | https://www.football-data.co.uk/mmz4281/2425/EC.csv | 2026-10-20T14:17:40Z | 276264 | 552 | 10/08/2024 – 05/05/2025 | `efe33452b62a1bc283145dacc5fe22d00f94fde475e263389865a4e45c24dd65` |
| `historical/football-data/2025-26/E0.csv` | https://www.football-data.co.uk/mmz4281/2526/E0.csv | 2026-10-20T14:17:43Z | 203438 | 380 | 15/08/2025 – 24/05/2026 | `3e3a8352f9ada6789c508d6ca184424421fed56a30400904a4a327c583407e62` |
| `historical/football-data/2025-26/E1.csv` | https://www.football-data.co.uk/mmz4281/2526/E1.csv | 2026-10-20T14:17:47Z | 294390 | 552 | 08/08/2025 – 02/05/2026 | `98954c319950f19158624b17a154ef1c56eb7b8d169ef317f28f06d11d0b9a74` |
| `historical/football-data/2025-26/E2.csv` | https://www.football-data.co.uk/mmz4281/2526/E2.csv | 2026-10-20T14:17:51Z | 288636 | 552 | 01/08/2025 – 02/05/2026 | `4c96eff8a2f20c5e26015af8609c4f90478ff055f58ab6e137cc3445bf4c67ee` |
| `historical/football-data/2025-26/E3.csv` | https://www.football-data.co.uk/mmz4281/2526/E3.csv | 2026-10-20T14:17:54Z | 290077 | 552 | 02/08/2025 – 02/05/2026 | `eff4fa15cb18857091d1f0666d0b8a6c61eda7a8374feef8f2d8a38244e0e45d` |
| `historical/football-data/2025-26/EC.csv` | https://www.football-data.co.uk/mmz4281/2526/EC.csv | 2026-10-20T14:17:58Z | 276074 | 552 | 09/08/2025 – 25/04/2026 | `2372229d616a57f9df3d9a401cd942df8e1909ba67017b3793c6aceaf0becf76` |
| `historical/football-data/2026-27/E0.csv` | https://www.football-data.co.uk/mmz4281/2627/E0.csv | 2026-10-20T14:18:02Z | 34516 | 70 | 21/08/2026 – 19/10/2026 | `705ef4373f6c4c9ec09b67eb3ca3398d6a770813095efc5d629edb591e4ee41c` |
| `historical/football-data/2026-27/E1.csv` | https://www.football-data.co.uk/mmz4281/2627/E1.csv | 2026-10-20T14:18:05Z | 64162 | 131 | 14/08/2026 – 17/10/2026 | `9b90a914541ae8c21cd138f3ae80576871396a744e1ef17e990f59a0fd8969df` |
| `historical/football-data/2026-27/E2.csv` | https://www.football-data.co.uk/mmz4281/2627/E2.csv | 2026-10-20T14:18:09Z | 56312 | 114 | 15/08/2026 – 17/10/2026 | `26561810728eb229af7743cd18d93be75360e09fefe96668d226e1f6c20d970f` |
| `historical/football-data/2026-27/E3.csv` | https://www.football-data.co.uk/mmz4281/2627/E3.csv | 2026-10-20T14:18:13Z | 62152 | 126 | 15/08/2026 – 17/10/2026 | `4dce5c92e5d2cbb8566b57d7f836c8aa2eaa883647f24822d918890e913986ca` |
| `historical/football-data/2026-27/EC.csv` | https://www.football-data.co.uk/mmz4281/2627/EC.csv | 2026-10-20T14:18:16Z | 74889 | 155 | 08/08/2026 – 10/10/2026 | `1695ef3cb54d5a0ea5715add8e38ea1ae0d0b72f29a1692264f92b39931da46f` |

- E0 2023-24 (`b2e057b0…`) and E0 2024-25 (`d0c8ce4a…`) are byte-identical
  to `tools/odds/E0_2023-24_fetched_2026-10-19.csv` and
  `tools/odds/E0_2024-25_fetched_2026-10-19.csv` (S10b,
  `worklog/downloads_2026-10-19b.md`).
- Columns per file: 98–133. football-data adds odds columns over the
  seasons; the results columns are the same in every file.
