# Data refresh — 2026-09-01

This records the current-season refresh performed after Premier League Matchweek 2 (28–31 Aug 2026).

## Official FPL

The current-season official FPL updater was run for GW2.

Live Supabase state after refresh:
- `public.fpl_player_match_stats`, season `2026/27`: 1,236 rows
- 20 distinct fixtures
- max gameweek 2
- GW2 write: 626 player-fixture rows across all 10 fixtures
- point-component mismatches: 0
- missing teams: 0

Identity remains permanent `player_code`; season-local FPL IDs remain metadata only.

## Rich current match/player feed

The GW2 rich feed was refreshed from the existing FPL-Core-Insights path.

Live Supabase state after refresh:
- 10 finished GW2 match rows were recognised
- 360 GW2 `player_match_stats` rows were published by the source
- missing permanent player codes: 0
- missing teams: 0

Important source gap:
- the rich source has not yet published player-match rows for `26-27-prem-aston-villa-vs-arsenal`
- therefore `player_match_stats` currently has 19 of the 20 completed 2026/27 matches (759 rows total)
- no substitute core appearances were fabricated for Villa–Arsenal
- team-level betting data is still complete: `betting_team_match_v2` has 40 team rows / 20 matches and xG is populated for all 40 rows through the existing fallback architecture

## Understat current season

Understat's live 2026/27 league/match endpoints were verified through all 20 completed matches.

Current-season Understat staging in Supabase:
- 20 completed matches mapped exactly by date + teams + score
- 622 staged `source_player_match_stats` rows
- 1,816 existing verified Understat player-ID mappings were loaded
- 341 staged current-season rows resolve through those pre-existing verified provider-ID mappings
- 281 staged rows remain unresolved and were left unresolved; no automated player-name mapping was used

Enrichment:
- 313 existing canonical `player_match_stats` rows were enriched with Understat `xg`, `xa`, `shots`, `key_passes`, `xg_chain`, and `xg_buildup`
- `advanced_source='understat'` provenance was written with source match/player IDs
- post-update advanced-metric mismatches: 0
- core minutes/goals/assists/cards were not overwritten by the Understat enrichment

Mapped staged rows without a matching canonical player-match row: 28 total:
- 24 are Villa–Arsenal, explained by the missing rich player-match source file
- 2 are Matt Grimes across Coventry's first two matches
- 2 are Chuba Akpom across Ipswich's first two matches

The Grimes/Akpom cases use older source-native canonical identities and do not yet have enough current PL overlap for the conservative cross-source resolver. They remain staged only; do not use names to force a mapping.

## Transfermarkt

The project's Transfermarkt CC0 source (`dcaribou/transfermarkt-datasets`) was checked directly.

Published Premier League seasons currently present in its `games` table run through season `2025` (2025/26), with 380 games for that season. There are currently **0 games for season 2026 / 2026/27** in that published source.

Therefore no 2026/27 Transfermarkt player-match data was imported. This is a source-availability limitation, not a database failure. Do not silently switch to a different Transfermarkt scraper/provenance just to manufacture a current-season refresh.

Existing live Transfermarkt source coverage in Supabase remains through 2024/25. A future task may separately audit/import the newly published 2025/26 Transfermarkt season using the strict exact-fixture + >=20-appearance completeness gate before promotion.

## Security / temporary helpers

Temporary read/audit Edge Functions used during the investigation were locked after use. The reusable production data remains in normal Supabase tables; no public unauthenticated staging helper was intentionally left open.

## Current verified headline state

- FPL 2026/27: 1,236 rows / 20 fixtures / GW2 complete
- canonical core player-match stats: 759 rows / 19 matches; Villa–Arsenal rich-player source pending
- Understat 2026/27 staged: 622 rows / 20 matches
- Understat current-season canonical enrichment: 313 rows / 0 advanced-metric mismatches
- `betting_team_match_v2`: 40 rows / 20 matches / all with xG
- Transfermarkt 2026/27: unavailable from the project's published source as of 2026-09-01
