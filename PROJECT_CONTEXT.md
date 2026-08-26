# PL Results Project — Persistent Project Context

_Last updated: 2026-08-26_

This file is the durable handoff/source of truth for continuing the project across ChatGPT conversations. At the start of a new project chat, read this file first, then verify live state in GitHub/Supabase/Vercel before making changes.

## Connected systems

- **GitHub:** `MarkColonel80/PL-Results-Project`, default branch `main`. ChatGPT has direct read/write access and should normally make code changes itself rather than asking Mark to use Codex or manually edit files.
- **Supabase:** project `PL Results Project`, ref `priibitbnmfetyblzltk`. ChatGPT has direct database access and should query live state itself whenever database facts matter.
- **Vercel:** project `pl-results-project`, project id `prj_8OeSf0K7GBywgASSo5ojRUpYDg84`, team `Colly` / `team_AVL2QNde5NnMKvlgXcjw0hhf`. It is linked to the GitHub repository. ChatGPT can inspect deployments, logs and deployed-site state directly.

## Working style / responsibility

- Treat **GitHub code + Supabase data + Vercel deployment** as one connected project.
- Prefer direct inspection and changes through connected tools instead of asking Mark to copy files, use Codex, inspect dashboards, or relay database/site state.
- Only ask Mark to run a local Mac command when the action genuinely requires his local checkout/runtime or credentials unavailable through the connected systems.
- Before any risky write, inspect the relevant code/data first. Prefer dry-run/audit stages where available.
- Do not use automated player-name matching as canonical identity evidence unless explicitly agreed; stable IDs and cross-source evidence are preferred.

## Current Understat historical-data checkpoint

### Staging

`stage_understat_history.py` successfully staged complete Premier League Understat history for 2014/15 through 2023/24.

- 10 complete seasons
- 3,800 / 3,800 fixtures mapped
- 106,519 staged Understat player-match rows
- 1,899 distinct Understat source players
- No live `player_match_stats` rows changed by staging
- No player-name matching used

### Identity resolution already applied

`resolve_understat_cross_source.py` initially found:

- Existing verified Understat mappings: 1,680
- New high-confidence candidates: 119
- Minimum two-sided match coverage: 100%
- Candidate common games: min 4, median 101, max 274
- Worst accepted average minute difference: 1.94
- Ambiguous after composite uniqueness: 0

Those **119 mappings were applied** successfully.

Live Supabase state verified afterwards:

- Verified Understat mappings: **1,799**
- Staged rows: **106,519**
- Staged source players: **1,899**
- Staged players with canonical `player_code`: **1,799**
- Staged players without canonical `player_code`: **100**

The apply changed only Understat crosswalks/staged identity fields; it did **not** change live `player_match_stats`. Identity invariants passed.

### Resolver determinism issue discovered

A second dry run after applying the 119 unexpectedly produced 17 additional candidates. Review showed the resolver could be order-dependent because:

1. paginated Supabase reads used `range()` without explicit ordering; and
2. provisional mappings greedily claimed canonical targets during iteration.

ChatGPT updated `scripts/resolve_understat_cross_source.py` directly in GitHub on `main` (commit `8bc5470567e1303f0f11b89cf33059e49d6d5e73`) to make resolution deterministic while preserving the scoring thresholds. The updated design uses deterministic query ordering, sorted source-player processing, a fixed snapshot of existing verified claims, provisional resolution first, and duplicate-target conflict handling.

**Important:** the 17 second-wave candidates have NOT been applied.

## Immediate next step

1. Ensure the local checkout has the updated resolver (`git pull`) if running locally.
2. Run `python3 scripts/resolve_understat_cross_source.py` twice in dry-run mode against the unchanged database.
3. Confirm the two outputs are identical.
4. Review any remaining high-confidence candidates/duplicate-target conflicts before another `--apply`.
5. Only after identity resolution is stable should work proceed to a separately validated Understat enrichment/promotion step for `player_match_stats`.

## Other historical-source work

A Joseph CC0 historical dataset was audited separately. Its `matches.csv` contains fixture/results fields and lineup-shaped columns, but early rows have blank lineup values; `events.csv` exposes match `id` and event text rather than stable player IDs. The audit did not establish Joseph as a player-identity source. No Supabase writes were made from that audit.

## Continuation instruction for future ChatGPT chats

When Mark says this is the **PL Results Project** or asks to continue the Premier League data app work, first read `PROJECT_CONTEXT.md`, then inspect the current GitHub commit and live Supabase/Vercel state as needed. Do not ask Mark to re-explain prior project history that can be recovered from these systems.
