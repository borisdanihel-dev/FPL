# FPL Plan — 1. FC Kiripolcz

Written after GW3. Rank 6/7, 204 pts, 39 behind. All four first-half chips intact.
Deadlines are **Prague time**, computed from actual kickoffs. TV picks can move
fixtures, so re-check inside the app on the day.

---

## Commands

Run from `C:\Users\Boris\Documents\FPL`

| Command | When |
|---|---|
| `fpl_run.bat` | Automated daily. Don't touch it. |
| `python fpl_edge.py --brief` | Deadline day. 20-line check. |
| `python fpl_edge.py --diff` | After a gameweek settles. What changed. |
| `python fpl_edge.py --section wildcard --horizon 6` | Wildcard planning. |
| `python fpl_edge.py --section backtest` | After each GW. Did the model call it? |
| `python fpl_edge.py --section defcon` | DEFCON hit rate, not just averages. |
| `python fpl_sync.py --refetch` | One-off. Backfills historical gameweeks. |
| `python fpl_edge.py --out reports\manual.txt` | Full report. |

Reports land in `reports\`. Upload `fpl_export_gwN.json` — not the report — when
you want analysis.

---

## Timeline

### GW4 — deadline **Sat 12 Sep, 14:30**
Note the day: **Saturday, not Friday.** First kickoff is 16:00 Prague.

- **Transfer: ROLL.** Nothing is broken, and anything you buy gets deleted at GW6.
- **Captain: decide on the day.** Haaland is away at Old Trafford (FDR 4);
  João Pedro is home to Hull (FDR 2). The only week this month where the
  obvious captain isn't obviously right. You own both.
- Man Utd v Man City puts Bruno and Haaland in the same match. Nothing to do
  about it, but expect a volatile week either way.
- Friday evening: `python fpl_edge.py --brief` and check the FLAGGED block.

### GW5 — deadline **Fri 18 Sep, 19:30**

- **Transfer: ROLL again**, unless news forces it. You then carry 2 FT through
  the wildcard — saved transfers survive the chip.
- **Captain: Haaland.** City are home to Sunderland, FDR 2.
- After the gameweek settles (Mon 21 Sep), run `fpl_run.bat` and upload the
  export. That's the dataset the wildcard gets drafted from.

### Break — 21 Sep to 9 Oct
No Premier League on 26 Sep or 3 Oct. Merged September/October window.

- Leave the daily task running. Prices still move; `price_changes_7d` will have
  weeks of history by now.
- `python fpl_edge.py --section wildcard --horizon 6` — run it repeatedly as
  international injuries land.
- Watch for players picking up knocks on international duty. This is the
  single biggest risk window of the first half.

### GW6 — deadline **Sat 10 Oct, 12:00**

- **Chip: WILDCARD.**
- **Warning: GW6 is Liverpool v Man City.** Pick a side deliberately or accept
  that your premium spend cancels out in week one of the new squad.
- Draft against **GW7 onward**, not GW6.
- **Build a playable bench**, not £4.0m fodder — GW8's Bench Boost depends on it.
  The `bench proj` line in the wildcard output is your estimate of what the
  chip is worth. Below ~12 pts/GW, it isn't worth playing.

### GW7 — deadline **Sat 17 Oct, 12:00**

- **Chip: TRIPLE CAPTAIN, Haaland.** City home to Ipswich, FDR 2 — the only
  soft home fixture City have in the window.
- One chip per gameweek, which is why this can't share a week with Bench Boost.

### GW8 — deadline **Fri 23 Oct, 19:30**

- **Chip: BENCH BOOST**, conditional on the bench projection.
- City are away at Villa (FDR 4) that week, so don't expect a Haaland haul.
- If the bench isn't worth it, defer. There's room before GW19.

### GW9 — deadline **Sat 31 Oct, 12:00**
Clocks change 25 Oct; the deadline is 11:00 UTC from here on.

---

## Chips

| Chip | Plan | Expires |
|---|---|---|
| Wildcard | GW6 | GW19 deadline, 2 Jan 2027 |
| Triple Captain | GW7, Haaland v Ipswich | same |
| Bench Boost | GW8 if bench projects well | same |
| Free Hit | **Insurance. Hard cutoff GW16–17.** | same |

Free Hit has no obvious first-half use — blanks usually land after GW20. Hold it
for an injury crisis. But it does not carry over, so if nothing has forced it by
GW16, spend it on the best available week rather than losing it.

**Rivals' chips:** Lukáš and Alex have only WC + FH left. Simon has no Triple
Captain. Jan has no Bench Boost. Honza has no Triple Captain. You and Ratul hold
all four. Four of them spent a Triple Captain on a 9-point Haaland in GW3.

---

## When to break the plan

1. **Injury or suspension to an XI player** → spend the free transfer. This is
   the only routine reason.
2. **Calafiori hooked before the hour twice more** → he's a wildcard swap for
   Gabriel or Raya, not a free transfer. Don't burn an FT on him.
3. **Three or more XI players flagged before GW5** → bring the wildcard forward.
   Fewer than three, hold to GW6.
4. **Never take a −4 before the wildcard.** Any hit you take is buying a player
   you delete three weeks later.
5. **Don't chase last week's hauls.** The `--brief` upgrade shortlist ranks on
   form × fixtures, which over three gameweeks is mostly noise. Use it to
   surface names, not to make the call.

---

## Weekly routine

- **Daily** — automated, ignore it.
- **Deadline day** — `python fpl_edge.py --brief`, check FLAGGED, set captain
  and bench order in the app.
- **Monday after** — `fpl_run.bat`, then `python fpl_edge.py --section backtest`
  to see whether the projection called the week, then upload
  `fpl_export_gwN.json`.

Run the sync a day after the last match of a gameweek, not an hour after.
Bonus points settle late; 15 players had their totals change between two runs
40 minutes apart on GW3 night.
