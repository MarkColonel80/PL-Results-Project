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

`resolve_understat_cross_source.py` initially found 1,680 existing verified mappings plus 119 new high-confidence candidates. The 119 were applied successfully.

A second dry run surfaced 17 more candidates and exposed an order-dependence problem in the resolver. ChatGPT fixed the resolver directly in GitHub (commit `8bc5470567e1303f0f11b89cf33059e49d6d5e73`) by making pagination/iteration deterministic, holding existing claims fixed during scoring, and resolving duplicate-target conflicts after provisional scoring. Evidence thresholds were not weakened.

Two consecutive dry runs of the fixed resolver were identical and returned 17 final high-confidence candidates with zero duplicate-target conflicts and zero ambiguity. Those 17 were applied successfully.

The next dry run then reached the stable endpoint:

- Existing verified Understat mappings: **1,816**
- Provisional high-confidence candidates: **0**
- Duplicate-target conflicts: **0 targets / 0 source players**
- New high-confidence candidates: **0**
- Unresolved with fewer than 3 overlap appearances: **50**
- Ambiguous after composite uniqueness: **0**

Live Supabase state at this point:

- Verified Understat mappings: **1,816**
- Staged rows: **106,519**
- Staged source players: **1,899**
- Staged players without canonical `player_code`: **83**

No live `player_match_stats` rows were changed by the resolver. Identity invariants passed.

### Legacy source-native identity issue discovered before promotion

Before promoting/enriching more Understat rows, ChatGPT audited the live canonical overlap and found an older identity convention that must be reconciled first.

There are **213** verified Understat mappings with `mapping_method = source_native_identity`. These are `plp:*` canonical identities created before the later cross-source identity base was available.

- 136 of those players only appear in 2014/15 and can legitimately remain source-native.
- 77 continue into 2015/16 or later.
- **74 of those 77 now have exactly one high-confidence established canonical identity** under the same strict match-history/goals/minutes evidence rules.
- The 74 have **zero target conflicts** with another Understat source player.
- The 74 have **zero `player_match_stats` row collisions** when re-keying the existing 2014/15 Understat rows.
- The 74 have **zero `player_seasons` collisions**.
- Dependency audit found old-code references only in the expected tables: 74 `players`, 74 `player_seasons`, 74 `player_source_ids`, 1,990 `player_match_stats`, and 11,720 `source_player_match_stats`. No old-code references were found in FPL match stats, goals, lineups, ratings, provider IDs, source events, or source-player mappings.

This legacy identity split explains much of the apparent mismatch between staged Understat rows and the Transfermarkt-backed live rows in later seasons. Do **not** promote missing Understat rows until these 74 legacy duplicate identities are reconciled.

ChatGPT added a versioned transactional reconciliation script to GitHub:

- `scripts/reconcile_understat_source_native.sql`
- GitHub commit: `bec85af176a71330c6458e9f342316218f7bf4ee`

The SQL recomputes the evidence, enforces conflict/collision/dependency safety gates, re-keys staging/live 2014/15 rows and season membership to the established canonical identity, updates the Understat crosswalk method/note, removes the now-unreferenced duplicate `plp:*` canonical player rows, and runs inside a single transaction.

**Important: this reconciliation SQL has NOT yet been executed against Supabase.**

## Immediate next step

1. Execute/review `scripts/reconcile_understat_source_native.sql` against Supabase as a single transaction.
2. Verify that it reconciles the expected **74** legacy identities and that the transaction safety checks all pass.
3. Re-run the Understat resolver afterwards; it should still return zero new high-confidence candidates.
4. Re-audit `(match_id, player_code)` overlap between mapped Understat staging rows and `player_match_stats`.
5. Only after the canonical identity split is fixed should Understat advanced metrics be enriched/promoted further. Preserve existing base football-source provenance (e.g. Transfermarkt/rich-core); Understat should supply advanced xG/xA/shots/key-pass/xGChain/xGBuildup provenance where identities align, not blindly replace richer base rows.

## Current live Understat advanced-metric state

The live database already has Understat advanced metrics on many canonical rows:

- 2014/15 is currently populated directly from Understat and has `advanced_source = understat` on all 10,428 live rows.
- 2015/16 through 2023/24 are primarily Transfermarkt-backed base rows; many already have `advanced_source = understat`, while some do not.

Therefore the next enrichment step must be an **incremental reconciliation/enrichment**, not a wholesale Understat replacement import.

## Other historical-source work

A Joseph CC0 historical dataset was audited separately. Its `matches.csv` contains fixture/results fields and lineup-shaped columns, but early rows have blank lineup values; `events.csv` exposes match `id` and event text rather than stable player IDs. The audit did not establish Joseph as a player-identity source. No Supabase writes were made from that audit.

## Continuation instruction for future ChatGPT chats

When Mark says this is the **PL Results Project** or asks to continue the Premier League data app work, first read `PROJECT_CONTEXT.md`, then inspect the current GitHub commit and live Supabase/Vercel state as needed. Do not ask Mark to re-explain prior project history that can be recovered from these systems.
