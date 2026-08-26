# PL Results Project — Persistent Project Context

_Last updated: 2026-08-26_

This file is the durable handoff/source of truth for continuing the project across ChatGPT conversations. At the start of a new project chat, read this file first, then verify live state in GitHub/Supabase/Vercel before making changes.

## Global workflow preference

This is a standing preference that applies beyond this specific project:

- For software/data projects, prefer a three-system workflow of **GitHub for source code/version history, Supabase for database/backend data, and Vercel for deployment/production-site verification** when those services are suitable and connected.
- At the **start of every new project**, create and maintain a `PROJECT_CONTEXT.md` file in the project GitHub repository.
- `PROJECT_CONTEXT.md` should be the durable cross-chat handoff/source of truth: record architecture, connected services, important decisions, data state/checkpoints, safety rules, completed work, unresolved issues, and the exact next step.
- Update `PROJECT_CONTEXT.md` whenever a material project milestone, decision, schema/data change, deployment change, or debugging discovery occurs, so a fresh ChatGPT conversation can continue without Mark re-explaining the project.
- In a new project conversation, read `PROJECT_CONTEXT.md` first, then verify the current live state in GitHub/Supabase/Vercel before making changes.

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

### Identity resolution

`resolve_understat_cross_source.py` initially found:

- Existing verified Understat mappings: 1,680
- New high-confidence candidates: 119
- Minimum two-sided match coverage: 100%
- Candidate common games: min 4, median 101, max 274
- Worst accepted average minute difference: 1.94
- Ambiguous after composite uniqueness: 0

Those **119 mappings were applied** successfully, bringing verified mappings to 1,799.

A second dry run then surfaced 17 more candidates, which exposed a determinism issue in the resolver: paginated Supabase reads had no explicit ordering and provisional mappings greedily claimed canonical targets during iteration.

ChatGPT updated `scripts/resolve_understat_cross_source.py` directly in GitHub on `main` (commit `8bc5470567e1303f0f11b89cf33059e49d6d5e73`) to make resolution deterministic while preserving all evidence thresholds. The updated design uses deterministic query ordering, sorted source-player processing, a fixed snapshot of existing verified claims, provisional resolution first, and duplicate-target conflict handling.

Two consecutive dry runs of the fixed resolver were identical:

- Existing verified mappings: 1,799
- Provisional high-confidence candidates: 17
- Duplicate-target conflicts: 0 targets / 0 source players
- Final new high-confidence candidates: 17
- Unresolved with fewer than 3 overlap appearances: 50
- Ambiguous after composite uniqueness: 0
- Candidate common games: min 8, median 66, max 264
- Minimum two-sided match coverage: 100%
- Worst accepted average minute difference: 2.00

Those **17 mappings were then applied successfully**.

Live Supabase state verified after the apply:

- Verified Understat mappings: **1,816**
- Staged rows: **106,519**
- Staged source players: **1,899**
- Staged players without canonical `player_code`: **83**

No live `player_match_stats` rows were changed by identity resolution. Identity invariants passed (provider-neutral canonical IDs; no automated name matching).

## Immediate next step

1. Run `python3 scripts/resolve_understat_cross_source.py` once more in dry-run mode.
2. Review whether any additional high-confidence candidates appear now that the 17 have become fixed verified claims. Because existing claims can remove competing candidates, a later deterministic pass can legitimately surface further mappings.
3. If additional candidates appear, review/apply only if the same strict evidence and zero-conflict conditions hold.
4. When the resolver reaches a stable dry run with no further acceptable mappings, treat the remaining unresolved players as unresolved rather than forcing name-based matches.
5. Only then proceed to a separately validated Understat enrichment/promotion step for `player_match_stats`.

## Other historical-source work

A Joseph CC0 historical dataset was audited separately. Its `matches.csv` contains fixture/results fields and lineup-shaped columns, but early rows have blank lineup values; `events.csv` exposes match `id` and event text rather than stable player IDs. The audit did not establish Joseph as a player-identity source. No Supabase writes were made from that audit.

## Continuation instruction for future ChatGPT chats

When Mark says this is the **PL Results Project** or asks to continue the Premier League data app work, first read `PROJECT_CONTEXT.md`, then inspect the current GitHub commit and live Supabase/Vercel state as needed. Do not ask Mark to re-explain prior project history that can be recovered from these systems.
