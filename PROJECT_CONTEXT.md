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
- Explicit, individually reviewed `manual_name_verified` exceptions are allowed when a player name is sufficiently unique and club/season/provider context makes the identity unambiguous.

## Understat historical-data checkpoint — COMPLETE FOR ALL VERIFIED IDENTITIES

### Staging

`stage_understat_history.py` successfully staged complete Premier League Understat history for 2014/15 through 2023/24.

- 10 complete seasons
- 3,800 / 3,800 fixtures mapped
- 106,519 staged Understat player-match rows
- 1,899 distinct Understat source players
- no automated player-name matching used

### Cross-source identity resolver

The deterministic resolver `scripts/resolve_understat_cross_source.py` reached a stable endpoint after two apply waves (119 + 17):

- Verified Understat mappings: **1,816**
- Staged source players: **1,899**
- Staged players without canonical `player_code`: **83**
- Final dry run: **0** new high-confidence candidates
- Duplicate-target conflicts: **0**
- Ambiguous accepted candidates: **0**

Resolver commit making the process deterministic: `8bc5470567e1303f0f11b89cf33059e49d6d5e73`.

### Automated legacy source-native reconciliation

An older process had created 213 Understat `source_native_identity` mappings on `plp:*` canonical identities. 77 continued past 2014/15; 74 of those had unique high-confidence established canonical identities under the conservative canonical-match/goals/minutes evidence.

Versioned reconciliation: `scripts/reconcile_understat_source_native.sql` (commit `bec85af176a71330c6458e9f342316218f7bf4ee`).

Executed successfully in Supabase:

- reconciled players: **74**
- common matches: min **4**, median **108**, max **306**
- minimum two-sided match coverage: **97.6%**
- worst accepted average minute difference: **1.69**
- zero target conflicts / match collisions / season collisions / unexpected dependencies

### Advanced Understat enrichment

`player_match_stats` preserves the original/base football source for minutes, goals, assists, cards, etc., while Understat supplies advanced fields through the separate `advanced_source` provenance fields.

Versioned repeat-safe enrichment: `scripts/enrich_understat_advanced_metrics.sql` (commit `4c336f5c8f2681d0d27d900d60874f578532aea8`).

Initial enrichment after automated identity reconciliation added **23,313** advanced-metric rows on top of the already-enriched historical base. Exact staged/live audits showed zero xG/xA/shots/key-pass/xGChain/xGBuildup mismatches.

### Missing cross-verified appearances

A guarded promotion script was added as `scripts/promote_understat_missing_verified_rows.sql` (commit `6dc67a5f2791c2c54e42b403ce97a5c6d1ebbde1`). It promotes only missing Understat appearances whose identities are already verified and excludes `source_native_identity` mappings.

It promoted **3** genuine source-gap rows safely.

### Final three manual identity exceptions

After the strict automated work, only three post-2014 legacy source-native identities remained. Mark explicitly agreed that these could be manually set if the names were unique enough, and each was individually reviewed against names, club/season history and provider evidence.

Versioned transaction: `scripts/reconcile_understat_manual_three.sql` (commit `05561830b8f71bc18b9852ceac3f6de2e1bc083c`).

Manual decisions:

1. **Steven Pienaar** — Understat source player `924`
   - old duplicate canonical: `plp:3eb1306793c8468ab41eb988b5e13afb`
   - merged to established canonical: **`7525`**
   - exact unique full name
   - Everton -> Sunderland club/season continuity
   - 2016/17 FPL comparison has the exact same 15-match set and zero goal mismatches

2. **Juan Cuadrado** — Understat `1089` and Transfermarkt `91970`
   - old duplicate canonicals: `plp:8f20bdb0d19c41868c3d9c27693ff2f0` and `plp:062a2582c48b472f9bd76a37e557bcb9`
   - both merged to established canonical: **`66733`**
   - exact unique full name
   - continuous Chelsea identity: 2014/15 Understat -> 2015/16 Transfermarkt -> 2016/17 established canonical

3. **Rushian Hepburn-Murphy** — Understat `1015`
   - kept existing unique canonical: **`plp:60c49e5ec1254a21a99dc224483b85c7`**
   - exact unique full name in `players`
   - Aston Villa in 2014/15 and 2015/16
   - Transfermarkt omitted the source-reported one-minute 2015/16 substitute appearance, so there was no competing identity to merge
   - mapping marked `manual_name_verified`
   - missing 2015/16 appearance promoted directly from Understat

Preflight for the Pienaar/Cuadrado merges found zero `player_match_stats` collisions, zero `player_seasons` collisions and no unexpected dependent-table references.

After these manual identities were unified, `scripts/enrich_understat_advanced_metrics.sql` was rerun and enriched the final **20** exact live matches.

## Final Understat end-to-end audit

Live Supabase audit after all reconciliation/promotion/enrichment:

- staged Understat rows: **106,519**
- staged Understat source players: **1,899**
- verified Understat mappings: **1,816**
- unresolved source players: **83**
- mapped staged rows: **105,041**
- mapped staged rows missing from live `player_match_stats`: **0**
- mapped live rows not carrying `advanced_source='understat'`: **0**
- advanced-metric mismatches against staging: **0**
- remaining `source_native_identity` mappings: **136**
- remaining source-native identities continuing after 2014/15: **0**
- explicitly manual verified crosswalks: **4**

Therefore **every Understat row whose player identity is verified is now represented in live player-match data and has exact Understat advanced metrics/provenance**.

The remaining 83 Understat source players are deliberately unresolved. Their staged rows stay staged and are not forced into canonical/live data.

## Immediate next step

The Understat 2014/15–2023/24 historical pipeline is now complete for all verified identities. Do not spend time forcing the remaining 83 unresolved players unless a future feature specifically requires them.

Next project work should move to the next data/product objective. Before doing so:

1. verify relevant player pages/site behaviour against the live Supabase data through Vercel when needed;
2. keep `scripts/enrich_understat_advanced_metrics.sql`, `scripts/promote_understat_missing_verified_rows.sql`, and the identity reconciliation scripts as the repeat-safe historical-data repair toolkit;
3. preserve the rule that automated player-name matching is prohibited, with individually reviewed `manual_name_verified` exceptions only when explicitly agreed.

## Other historical-source work

A Joseph CC0 historical dataset was audited separately. Its match data did not establish it as a stable player-identity source. No Supabase writes were made from that audit.

## Continuation instruction for future ChatGPT chats

When Mark says this is the **PL Results Project** or asks to continue the Premier League data app work, first read `PROJECT_CONTEXT.md`, then inspect the current GitHub commit and live Supabase/Vercel state as needed. Do not ask Mark to re-explain prior project history that can be recovered from these systems.
