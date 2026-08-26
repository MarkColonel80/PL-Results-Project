# PL Results Project — Persistent Project Context

_Last updated: 2026-08-26_

This file is the durable handoff/source of truth for continuing the project across ChatGPT conversations. At the start of a new project chat, read this file first, then verify live state in GitHub/Supabase/Vercel before making changes.

## Global workflow preference

This is a standing preference that applies beyond this specific project:

- For software/data projects, prefer a three-system workflow of **GitHub for source code/version history, Supabase for database/backend data, and Vercel for deployment/production-site verification** when those services are suitable and connected.
- At the **start of every new project**, create and maintain a `PROJECT_CONTEXT.md` file in the project GitHub repository.
- `PROJECT_CONTEXT.md` is the durable cross-chat handoff/source of truth: architecture, connected services, important decisions, data checkpoints, safety rules, completed work, unresolved issues, and the exact next step.
- Update this file after material code/data/schema/deployment/debugging milestones.
- In a new project conversation, read this file first, then verify current GitHub/Supabase/Vercel state before making changes.

## Connected systems

- **GitHub:** `MarkColonel80/PL-Results-Project`, default branch `main`. ChatGPT has direct read/write access and should normally make code changes itself rather than asking Mark to use Codex or manually edit files.
- **Supabase:** project `PL Results Project`, ref `priibitbnmfetyblzltk`. ChatGPT has direct database access and should query live state itself whenever database facts matter.
- **Vercel:** project `pl-results-project`, project id `prj_8OeSf0K7GBywgASSo5ojRUpYDg84`, team `Colly` / `team_AVL2QNde5NnMKvlgXcjw0hhf`. It is linked to the GitHub repository. ChatGPT can inspect deployments, logs and deployed-site state directly.

## Working style / responsibility

- Treat **GitHub code + Supabase data + Vercel deployment** as one connected project.
- Prefer direct inspection and changes through connected tools instead of asking Mark to copy files, use Codex, inspect dashboards, or relay database/site state.
- Only ask Mark to run a local Mac command when the action genuinely requires his local checkout/runtime or credentials unavailable through the connected systems.
- Before risky writes, inspect code/data first and prefer dry-run/audit stages.
- Do not use automated player-name matching as canonical identity evidence unless explicitly agreed. Stable IDs and cross-source evidence are preferred.

## Understat historical-data checkpoint

### Staging

`stage_understat_history.py` successfully staged complete Premier League Understat history for 2014/15 through 2023/24.

- 10 complete seasons
- 3,800 / 3,800 fixtures mapped
- 106,519 staged Understat player-match rows
- 1,899 distinct Understat source players
- No player-name matching used

### Cross-source identity resolver

The deterministic resolver `scripts/resolve_understat_cross_source.py` reached a stable endpoint after two apply waves (119 + 17):

- Verified Understat mappings: **1,816**
- Staged source players: **1,899**
- Staged players without canonical `player_code`: **83**
- Final dry run: **0** new high-confidence candidates
- Duplicate-target conflicts: **0**
- Ambiguous accepted candidates: **0**

Resolver commit making the process deterministic: `8bc5470567e1303f0f11b89cf33059e49d6d5e73`.

### Legacy source-native reconciliation

An older process had created 213 Understat `source_native_identity` mappings on `plp:*` canonical identities. 77 continued past 2014/15; 74 of those now had unique high-confidence established canonical identities under the same conservative canonical-match/goals/minutes evidence.

Preflight for those 74 found:

- zero target conflicts
- zero `player_match_stats` collisions
- zero `player_seasons` collisions
- no unexpected dependent-table references

Versioned reconciliation: `scripts/reconcile_understat_source_native.sql` (commit `bec85af176a71330c6458e9f342316218f7bf4ee`).

The transaction was executed successfully in Supabase:

- reconciled players: **74**
- common matches: min **4**, median **108**, max **306**
- minimum two-sided match coverage: **97.6%**
- worst accepted average minute difference: **1.69**

After reconciliation:

- verified Understat mappings remain **1,816** (identities were re-keyed, not added)
- remaining `source_native_identity` mappings: **139**
- only **3** remaining source-native players continue beyond 2014/15; the other 136 are 2014/15-only source-native identities
- unresolved staged Understat players remain **83**

### Advanced Understat enrichment

The live database already had 81,704 rows carrying `advanced_source='understat'`. Audit proved those rows matched staging exactly for xG, xA, shots, key passes, xGChain and xGBuildup: **0 field mismatches**.

After the legacy identity reconciliation, a further **23,313** exact `(season, match_id, player_code)` live rows became safely enrichable.

Versioned enrichment: `scripts/enrich_understat_advanced_metrics.sql` (commit `4c336f5c8f2681d0d27d900d60874f578532aea8`).

It was executed successfully and only updates advanced fields/provenance; it does **not** alter base minutes/goals/assists/cards/source provenance.

Postconditions:

- additional enriched rows: **23,313**
- exact live matches still waiting for enrichment: **0**
- advanced-metric mismatches against staging: **0**

### Missing live Understat appearances

After reconciliation/enrichment there were 24 mapped staged Understat appearances with no corresponding live `player_match_stats` row.

These split into:

- **3** rows for an already cross-verified established canonical player whose Transfermarkt source simply has no 2019/20 staged rows for those matches
- **21** rows belonging to the three remaining post-2014 legacy `source_native_identity` players

A guarded promotion was added as `scripts/promote_understat_missing_verified_rows.sql` (commit `6dc67a5f2791c2c54e42b403ce97a5c6d1ebbde1`). It promotes only missing Understat rows whose player mapping is verified and **not** `source_native_identity`.

It was executed successfully:

- promoted missing cross-verified rows: **3**
- legacy source-native rows promoted: **0**

Current live endpoint:

- total `player_match_stats` rows carrying `advanced_source='understat'`: **105,020**
- exact matching live rows still waiting for Understat enrichment: **0**
- mapped staged Understat rows still not live: **21**
- those 21 rows belong to exactly **3** remaining legacy source-native players

## Remaining three legacy post-2014 source-native players

These are deliberately held out of further live promotion until identity evidence improves. Player names may be displayed for audit but must not be used as automated identity evidence.

- Understat source player `924`: 28 staged rows across 2014/15–2016/17, with 15 missing live rows in 2016/17 plus 4 missing in 2015/16. FPL-era audit found canonical code `7525` has the exact same 15-match set in 2016/17 and zero goal mismatches, but average minute difference is ~2.87 minutes and only 40% are within 2 minutes. This is strong evidence but **outside the current automatic minute threshold**, so no identity change has been applied.
- Understat source player `1089`: 13 staged rows through 2015/16; only one later missing live row. Current cross-source evidence is insufficient for an automatic merge.
- Understat source player `1015`: 2 staged rows through 2015/16; only one later missing live row. Current cross-source evidence is insufficient for an automatic merge.

Do not loosen global identity thresholds merely to force these three mappings. Prefer additional stable-ID/team/DOB/provider evidence or leave them source-native.

## Immediate next step

1. Keep the current 21 rows out of live `player_match_stats` while their three legacy identities remain unresolved under strict rules.
2. Investigate additional non-name evidence for source player `924` first (exact FPL match set is promising): team membership, provider IDs, DOB/position where available, or another stable cross-source dataset.
3. Investigate `1089` and `1015` only if similarly strong stable evidence becomes available; otherwise leave them source-native.
4. Once any identity is safely reconciled, rerun `scripts/promote_understat_missing_verified_rows.sql` and `scripts/enrich_understat_advanced_metrics.sql` (both repeat-safe) to pick up newly eligible rows.
5. Verify resulting player pages/site data through Supabase/Vercel after any further promotion.

## Other historical-source work

A Joseph CC0 historical dataset was audited separately. Its match data did not establish it as a stable player-identity source. No Supabase writes were made from that audit.

## Continuation instruction for future ChatGPT chats

When Mark says this is the **PL Results Project** or asks to continue the Premier League data app work, first read `PROJECT_CONTEXT.md`, then inspect the current GitHub commit and live Supabase/Vercel state as needed. Do not ask Mark to re-explain prior project history that can be recovered from these systems.
