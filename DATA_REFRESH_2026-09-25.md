# PL Results Project — 25 September 2026 refresh

## Completed results loaded

Production Supabase was advanced from Matchweek 3 to Matchweek 5. The twenty fixtures played from 12 to 20 September were checked across the official FPL feed, the rich match source, Understat and Football-Data before loading.

| Dataset | Verified state |
|---|---|
| Results and canonical fixtures | 50 completed matches, through 20 September / GW5 |
| Official FPL player-fixture statistics | 3,216 rows / 50 fixtures; zero point-component mismatches or missing teams |
| Official current player identities | 667 `players` and 667 `player_seasons` rows for 2026/27 |
| Rich canonical player-match statistics | 1,995 rows / 50 matches; zero missing permanent player codes |
| Derived rich lineups and goals | 1,635 lineup rows and 110 goal events |
| Understat staged player-match statistics | 1,538 rows / 50 matches; 836 mapped through verified provider IDs |
| Understat canonical enrichment | 828 enriched rows; zero advanced-metric mismatches |
| Team model inputs / feature cache | 100 team rows / 50 matches; complete xG coverage |
| Football-Data current-season odds | 50 mapped fixtures; source results agree with canonical results |

The refresh added 1,326 official FPL rows, 796 rich player-match rows, 796 derived lineup rows and 56 shot-derived goal events. Two Brentford–Chelsea shot events did not provide an unambiguous scorer identity; their `player_code` remains null rather than being guessed. All rich player-match rows retain permanent FPL player codes.

The twenty new matches have verified `fpl_fixture`, `rich_core` and `understat` match mappings. Understat added 609 staged appearances. Existing verified provider-ID mappings resolved 329 of them, and 326 canonical appearances received advanced metrics. Eight mapped Understat appearances across the current season still have no corresponding canonical appearance row and remain staged. No automated player-name matching or provider-prefixed canonical IDs were introduced.

Understat's published match xG was retained as rebound-adjusted. Raw roster/shot xG sums were used only as source-consistency checks and were not substituted for the published adjusted totals.

## Refresh and preservation checks

Refreshed the official FPL aggregate caches, `betting_team_features_v2_cache`, `team_form_window_cache` and `team_form_window8_cache`, then recalculated the pre-match form fields and ran the guarded weekend snapshot scripts in the required order.

All saved pre-refresh hashes for Matchweeks 1–3 official FPL rows, rich player-match rows, lineups, goals, Understat staging rows and odds still match exactly. The 20 played manual fixture snapshots also retain their exact pre-refresh hash. The match form columns were deliberately recalculated from the refreshed leakage-safe feature views; canonical teams, scores and kick-off details agree across all 50 results.

There are no unplayed manual weekend fixtures in Supabase. The official feed's next Premier League fixture is Arsenal–Leeds on 10 October, so `/betting/weekend` will remain empty until the next fixture-and-odds snapshot is loaded.

The frozen v3 baseline, the Venue8 candidate architecture, database schema and browser grants were not changed. The Supabase Security Advisor remains at zero error/critical findings; its three private-table INFO notices and two intentional public aggregate-cache warnings are unchanged.

## Source status

- Official FPL: live bootstrap, fixtures and element-summary endpoints, captured 25 September 2026
- Rich football data: `olbauday/FPL-Core-Insights` commit `f8a340b6305603bc52428ba7a298798ba087a442`
- Understat: live EPL 2026 league and match XHR data; matches mapped by exact date, teams and score; players mapped only by existing verified source IDs
- Football-Data: current `2627/E0.csv`, with all 50 completed results matching canonical scores
- Transfermarkt: approved `dcaribou/transfermarkt-datasets` source still has no 2026/27 Premier League games; repository/data status remains the 5 September checkpoint
