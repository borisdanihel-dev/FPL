# Downloads of 19 Oct 2026, afternoon (RULINGS PART F, item F-C; prereg/S10b.md)

Approved in F-C. Data only: each file was fetched into its own new empty folder,
then placed below; every reader runs `python -I`. The `historical/` files are
gitignored and set read-only; the two football-data files are committed under
`tools/odds/` as S5's are (pre-closing odds only).

## vaastav/Fantasy-Premier-League, pinned to commit `9779cdbc0c07f6c900c2d0c181ddf6bb9c800f88` (as the morning's)

| file | fetched (UTC) | bytes | SHA-256 |
|---|---|---|---|
| `historical/2022-23/merged_gw.csv` | 2026-10-19T17:05:35Z | 4638801 | `b78a6d0456141f9033c32fc4122931baae780ac4a4938683451b1fce7a4fdd15` |
| `historical/2022-23/teams.csv` | 2026-10-19T17:05:37Z | 1711 | `be6a1fe120a61f9c441a0751ca177c933bcbf234c1d28d49b3cd8827ca18066b` |
| `historical/2022-23/players_raw.csv` | 2026-10-19T17:05:38Z | 280362 | `a874c12817bbf4d454e60a5765629742b528d4ad0c2f39f56e4fc89640605f7f` |
| `historical/2023-24/merged_gw.csv` | 2026-10-19T17:05:40Z | 4997188 | `e9c09c8856f1c86b4f920f46ddd5033af83409439dfda53be925df2a3e7c8a9e` |
| `historical/2023-24/teams.csv` | 2026-10-19T17:05:41Z | 1715 | `7795f091ccea17fda0752cb07b935e1515b09a9d3f924147997cbf28139edd49` |
| `historical/2023-24/players_raw.csv` | 2026-10-19T17:05:42Z | 310197 | `43d8cf5efb3d901f2499558c40b392b7f0ee22afe28030f36266ad29024c63d9` |
| `historical/2024-25/merged_gw.csv` | 2026-10-19T17:05:44Z | 5125595 | `5bbbcba6353b4c72ad273adcc8e3aa451946a826564679788f45b1cb3325b84e` |
| `historical/2024-25/teams.csv` | 2026-10-19T17:05:45Z | 1717 | `d10a6db8feca6db9e44a3ba50b15168396667ea387fee9235d6b211c7f598c3b` |
| `historical/2024-25/players_raw.csv` | 2026-10-19T17:05:46Z | 342122 | `75686051b265cbe7755ac71213ecaad21b26ee1cc46a8bafbba19c39ce894b05` |

Each URL is `https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/9779cdbc0c07f6c900c2d0c181ddf6bb9c800f88/data/<season>/<file>`
(`gws/merged_gw.csv` for the merged file).

- 2024-25 `merged_gw.csv` (`5bbbcba6…`) and `teams.csv` (`d10a6db8…`) are byte-identical to the
  copies S11 used; they were already in place and were not replaced.
- `fixtures.csv` for 2022-23, 2023-24 and 2024-25 was not fetched again: the morning's record
  (`worklog/downloads_2026-10-19.md`) holds them (`e783060d…`, `d8521bdb…`, `ce696e18…`).

## football-data.co.uk, Premier League (E0)

| file | URL | fetched (UTC) | bytes | SHA-256 |
|---|---|---|---|---|
| `tools/odds/E0_2023-24_fetched_2026-10-19.csv` | https://www.football-data.co.uk/mmz4281/2324/E0.csv | 2026-10-19T17:05:47Z | 172196 | `b2e057b0ed959f198b0f63d2391c01239f3608e6de5db68edab3f88e04d07ff3` |
| `tools/odds/E0_2024-25_fetched_2026-10-19.csv` | https://www.football-data.co.uk/mmz4281/2425/E0.csv | 2026-10-19T17:05:50Z | 197110 | `d0c8ce4a96d886cf60cf101f570f4a3893844226f91c7bd769eb568c49edbfa4` |
