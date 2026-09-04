# PL Results Project — Data refresh 2026-09-04

## Scope

Refresh completed on 4 September 2026 before the Matchweek 3 weekend:
- re-check current Transfermarkt source availability
- repair the previously missing Aston Villa v Arsenal rich player-match data
- refresh current weekend Premier League fixtures against the official schedule
- refresh Oddschecker UK 1X2 prices
- refresh the `v3_24_venue8_50_noppg` weekend comparison and its team-feature cache

## Transfermarkt

The project continues to use the CC0 `dcaribou/transfermarkt-datasets` source. The repository's latest published dataset commit is still from 5 Aug 2026 and the project has **0 Transfermarkt staged rows for 2026/27**. No alternative scraper/provenance was substituted.

2025/26 Transfermarkt archive remains unchanged from the 1 Sep checkpoint.

## Aston Villa v Arsenal rich-data repair

The existing rich current-season source (`olbauday/FPL-Core-Insights`) has now published `GW2/playermatchstats.csv` rows for `26-27-prem-aston-villa-vs-arsenal`, which were missing at the 1 Sep refresh.

Loaded into canonical `public.player_match_stats`:
- 40 rich source-reported player-match rows
- 31 players with minutes > 0
- 22 starters
- 1 goal
- 1 assist
- source provenance: `rich_core`

Derived lineup rows were also created for the match because the source does not publish a dedicated lineup file for this fixture.

Existing staged Understat data was then applied as the advanced-metric enrichment layer for the newly created canonical rows:
- 31 staged Understat rows for the fixture
- 24 had existing verified player mappings and were enriched
- 26 canonical match rows now contain xG after rich/Understat combination
- no core minutes/goals/assists were overwritten by Understat

The goal event was restored separately from public match records/FPL match data:
- Bukayo Saka, 59'
- assist Riccardo Calafiori
- final score Aston Villa 0–1 Arsenal

Post-repair 2026/27 canonical state:
- `player_match_stats`: **799 rows / 20 completed matches**
- all 20 completed league matches now have canonical rich player-match coverage

Remaining mapped staged Understat rows without a canonical player-match row: **4**, unchanged identity-edge cases only:
- Matt Grimes — 2 Coventry matches
- Chuba Akpom — 2 Ipswich matches

These remain staged rather than being forced by player-name matching.

## Matchweek 3 fixture refresh

Official Premier League September schedule was checked and the ten existing `betting_manual_fixtures` rows were already correct:

- Fri 4 Sep 20:00 BST — Ipswich Town v Liverpool
- Sat 5 Sep 12:30 — Newcastle United v AFC Bournemouth
- Sat 5 Sep 15:00 — Brentford v Sunderland
- Sat 5 Sep 15:00 — Brighton & Hove Albion v Leeds United
- Sat 5 Sep 15:00 — Fulham v Crystal Palace
- Sat 5 Sep 15:00 — Manchester City v Coventry City
- Sat 5 Sep 15:00 — Nottingham Forest v Tottenham Hotspur
- Sat 5 Sep 17:30 — Hull City v Aston Villa
- Sun 6 Sep 14:00 — Everton v Manchester United
- Sun 6 Sep 16:30 — Arsenal v Chelsea

No fixture/time changes were required.

## Oddschecker UK 1X2 refresh

Prices refreshed from the Oddschecker Premier League coupon at approximately 18:15 BST on 4 Sep 2026.

| Fixture | Home | Draw | Away |
|---|---:|---:|---:|
| Ipswich v Liverpool | 6.00 | 5.00 | 1.53 |
| Newcastle v Bournemouth | 2.15 | 3.80 | 3.40 |
| Nottingham Forest v Tottenham | 2.50 | 3.50 | 3.00 |
| Brentford v Sunderland | 1.666667 | 4.00 | 5.75 |
| Brighton v Leeds | 2.05 | 3.60 | 3.90 |
| Fulham v Crystal Palace | 2.35 | 3.50 | 3.30 |
| Manchester City v Coventry | 1.18 | 9.50 | 19.00 |
| Hull v Aston Villa | 4.20 | 3.75 | 1.928571 |
| Everton v Manchester United | 3.40 | 3.70 | 2.15 |
| Arsenal v Chelsea | 1.73 | 4.10 | 5.25 |

`market_source='Oddschecker UK coupon'` and `market_snapshot_at` was refreshed for all ten rows.

## Weekend model refresh

`public.betting_team_features_v2_cache` was refreshed before recalculating the 24-match comparison, preserving the stale-cache protection introduced after the Arsenal/Chelsea audit.

Current `v3_24_venue8_50_noppg` comparison probabilities:

| Fixture | Home | Draw | Away |
|---|---:|---:|---:|
| Ipswich v Liverpool | LIMITED | LIMITED | LIMITED |
| Newcastle v Bournemouth | 38.55% | 24.66% | 36.79% |
| Nottingham Forest v Tottenham | 43.31% | 31.71% | 24.98% |
| Brentford v Sunderland | 53.24% | 25.51% | 21.25% |
| Brighton v Leeds | 46.30% | 28.32% | 25.38% |
| Fulham v Crystal Palace | 45.22% | 27.40% | 27.38% |
| Manchester City v Coventry | LIMITED | LIMITED | LIMITED |
| Hull v Aston Villa | LIMITED | LIMITED | LIMITED |
| Everton v Manchester United | 30.63% | 28.14% | 41.24% |
| Arsenal v Chelsea | 58.68% | 24.24% | 17.08% |

The three LIMITED fixtures are still suppressed because one side lacks the minimum current-spell Venue8 history; this is intentional.

The existing manual weekend model remains separate and unchanged in logic. Its market no-vig probabilities now reflect the refreshed Oddschecker prices.

## Current verified headline state

- FPL 2026/27: 1,236 rows / 20 fixtures / GW2 complete
- canonical rich player-match: **799 rows / 20 matches — full completed-match coverage**
- Understat current staged: 622 rows / 20 matches
- Transfermarkt 2026/27: unavailable from the approved source; 0 staged rows
- known mapped-Understat-without-canonical rows: 4 (Grimes x2, Akpom x2)
- weekend fixtures: verified current
- weekend Oddschecker 1X2 prices: refreshed 4 Sep 2026
- 24-match + Venue8 comparison: refreshed after materialized-cache refresh
