# Data refresh — 2026-09-01

This records the current-season refresh performed after Premier League Matchweek 2 (28–31 Aug 2026), plus the newly available 2025/26 Transfermarkt archive refresh.

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

The project's Transfermarkt CC0 source (`dcaribou/transfermarkt-datasets`) was checked directly. Its published Premier League `games` data currently runs through season `2025` (2025/26). The source snapshot was last modified on 5 Aug 2026 and currently has **0 games for season 2026 / 2026/27**.

Therefore no 2026/27 Transfermarkt player-match data was imported. This is a source-availability limitation, not a database failure. Do not silently switch to a different Transfermarkt scraper/provenance just to manufacture a current-season refresh.

### Newly imported 2025/26 Transfermarkt archive

The source now contains complete 2025/26 data, so that season was audited and staged to close the project's previous Transfermarkt gap.

Strict completeness gate:
- 380/380 Premier League matches present
- 11,492 player appearance rows
- every match has at least 20 source appearance rows
- minimum appearances per match: 24
- maximum appearances per match: 34

Exact source match mapping:
- 380/380 Transfermarkt matches mapped to canonical matches by exact date + teams + score
- no fuzzy fixture mapping was needed

Player identity/staging:
- 11,492 rows staged in `public.source_player_match_stats`
- 9,063 rows initially linked through pre-existing verified Transfermarkt provider-ID mappings
- 2,429 rows initially unresolved
- a 2025/26 canonical match-history fingerprint pass then resolved 114 additional source players without using names
- accepted new mappings required at least 3 common games, >=95% two-sided overlap, goals/minutes agreement, and one-to-one composite uniqueness
- all 114 accepted mappings actually had 100% overlap
- common-game count: min 3, average 20.7, max 38
- worst accepted average minute difference: 0.67 minutes

Final 2025/26 Transfermarkt staging state:
- 11,418 / 11,492 rows linked to canonical player codes
- 74 rows remain unresolved
- those 74 rows represent 30 source players and remain staged only rather than being guessed by name
- the rich `player_match_stats` rows for 2025/26 were not overwritten; Transfermarkt remains a source/crosswalk layer for that season

Identity safety checks after the refresh:
- no Transfermarkt/Understat provider-prefixed canonical IDs were introduced into `players`
- every mapped 2025/26 staged Transfermarkt code exists in canonical `players`
- only the project's previously explicit manual-name-verified exceptions remain; this refresh introduced no automated name-based player mapping

## Security / temporary helpers

Temporary read/audit/staging Edge Functions used during the investigation were locked after use with JWT verification and inert handlers. The reusable production data remains in normal Supabase tables; no public unauthenticated Transfermarkt or Understat staging helper was intentionally left open.

## Current verified headline state

- FPL 2026/27: 1,236 rows / 20 fixtures / GW2 complete
- canonical core player-match stats: 759 rows / 19 matches; Villa–Arsenal rich-player source pending
- Understat 2026/27 staged: 622 rows / 20 matches
- Understat current-season canonical enrichment: 313 rows / 0 advanced-metric mismatches
- `betting_team_match_v2`: 40 rows / 20 matches / all with xG
- Transfermarkt 2026/27: unavailable from the project's published source as of 2026-09-01
- Transfermarkt 2025/26: 11,492 staged rows / 380 matches; 11,418 linked rows; 74 unresolved rows across 30 source players
