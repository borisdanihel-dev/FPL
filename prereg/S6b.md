# S6b — the xp_v2 past-season test (2025/26 re-scored under 2026/27 rules)

The chat's ruling, pasted verbatim on 2026-10-19 (received after the landing of
S4, S7, S5, S6 and S9 and the adoption of S11). Queued after S8's record and
re-verification; it needs Step 10 (lane A, landing today) on master for the
re-scoring. The template rows are filled in when the item starts, before any
S6b code, and this file is never edited after any of its evaluation numbers
exist. Offline under `tools/`; point-in-time S4 harness with `hist_pit` clubs;
provenance `run.txt`; verifier on Fable; the usual tests and mutations.

## Ruling (verbatim)

RULING S6b (xp_v2 past-season test), queued after S8; needs Step 10 on master (landing today):
1. Season 2025/26 GW5-38, re-scored under 2026/27 rules by Step 10; point-in-time S4 harness, hist_pit clubs, provenance run.txt.
2. Comparator own_proxy = project_reliability (the rebuildable source used in S7 and S8); state exactly which own inputs it lacks. Candidate = xp_v2 as frozen in S6 (equal blend), with S5's bottomup_lambda in the bottomup half and S11's shares in the xg half; P(start) from the current minutes model.
3. Primary, decision-based: on S7's 50 squads (seed 7), fixed squads, no transfers, no chips, each model picks its best legal XI and captain every gameweek; realised points with rule_autosubs and the captain doubled. Per gameweek, the mean over squads of (xp_v2 - own_proxy); block bootstrap over gameweeks (B = 10,000, fixed seed), 90%. Pass: lower bound > 0. Print the mean per gameweek and per season.
4. Secondary, printed only: per-GW Spearman among starters and MAE among starters, paired.
5. On PASS, adoption needs Boris's acceptance in chat. The chat would then propose switching XI and captain to xp_v2 from the next deadline, with own printed beside it and the live GW7-10 numbers checked at the GW10 checkpoint.
Prereg first with this ruling verbatim, verifier on Fable, usual tests and mutations.
END RULING
