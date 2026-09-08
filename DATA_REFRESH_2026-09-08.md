# PL Results Project — 8 September 2026 refresh

## Data loaded before the next-round calculations

The database was still at Matchweek 2. Imported the ten completed Matchweek 3 games, verifying the rich feed against the official FPL fixture dates, teams and scores.

| Dataset | Verified state |
|---|---|
| Results and canonical fixtures | 30 completed matches, through 6 September / GW3 |
| Official FPL player-fixture statistics | 1,890 rows / 30 fixtures; zero point-component mismatches or missing teams |
| Rich canonical player-match statistics | 1,199 rows / 30 matches; zero missing permanent player codes |
| Understat staged player-match statistics | 929 rows / 30 matches; 507 mapped through existing verified provider IDs |
| Understat canonical enrichment | 502 enriched rows; zero advanced-metric mismatches |
| Team model inputs / feature cache | 60 team rows / 30 matches; complete xG coverage |
| Football-Data current-season odds | 30 matched fixtures; source scores agree with canonical results |

The rich import added 400 source-reported player-match rows, 400 derived lineup rows and 23 shot-derived goal events for GW3. Shot-derived events do not invent assister IDs. Earlier rich and enriched appearances were preserved.

Understat added 307 staged rows, 166 resolving through existing verified IDs, and enriched 165 existing canonical rows. Five mapped staged rows still have no matching canonical appearance; they remain staged. No new player-name matching or provider-prefixed canonical IDs were introduced.

Refreshed the FPL aggregate caches, `betting_team_features_v2_cache`, `team_form_window_cache` and `team_form_window8_cache`. Research experiments and the frozen v3 baseline were not regenerated.

### Transfermarkt availability

The approved CC0 `dcaribou/transfermarkt-datasets` repository has a newer commit (`e44f186d6f06dd8452aaf54c7921ba66c961f637`, 5 September), but its published `games.csv.gz` still contains **zero Premier League games for season 2026**. Its latest PL game date is 24 May 2026. Therefore current-season Transfermarkt coverage remains unavailable; provenance was not changed.

## Upcoming fixtures: 12–14 September

Verified all ten fixtures and UK kick-off times against the official FPL API and [Premier League schedule](https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-202627-premier-league-season/). Includes Leeds–Newcastle on Monday evening. The [Oddschecker UK coupon](https://www.oddschecker.com/football/english/premier-league) was refreshed on 8 September; precise observation time and fractional source prices are stored with each fixture.

Source fixture/odds payload: `data/weekend-2026-09-12-fixtures.json`.

| Fixture | Home | Draw | Away |
|---|---:|---:|---:|
| Aston Villa–Nottingham Forest | 40.06% | 26.26% | 33.69% |
| Bournemouth–Brentford | 45.41% | 24.59% | 30.00% |
| Chelsea–Hull | LIMITED | LIMITED | LIMITED |
| Crystal Palace–Ipswich | LIMITED | LIMITED | LIMITED |
| Liverpool–Fulham | 51.72% | 24.83% | 23.45% |
| Tottenham–Everton | 33.41% | 27.33% | 39.26% |
| Sunderland–Arsenal | 17.92% | 27.74% | 54.34% |
| Coventry–Brighton | LIMITED | LIMITED | LIMITED |
| Manchester United–Manchester City | 37.56% | 24.96% | 37.49% |
| Leeds–Newcastle | 43.75% | 27.08% | 29.16% |

These are the unchanged `v3_24_venue8_50_noppg` research candidate probabilities. Rounding may make displayed totals differ slightly from 100%. All eligible probabilities sum to one within tolerance. The three suppressed fixtures each have a promoted side with only one relevant venue match; the minimum remains four.

Manual snapshot inputs were independently compared with the existing analysis view: ten fixtures, zero mismatches. The candidate remains separate from the manual rule and frozen v3.

## Page and preservation

- `/betting/weekend` shows only upcoming fixtures, defaulting to the next saved round. Passed matches are filtered out at the Supabase query; there is no past-round selector.
- Added an overview with UK times, candidate probabilities, and links to each fixture's detailed analysis.
- Shows the latest completed-match coverage from Supabase.
- The old 4–6 September fixtures and prediction snapshots remain unchanged in Supabase, with an additional repository copy at `data/weekend-2026-09-04-frozen.json`.
- `scripts/refresh_upcoming_weekend_snapshot.sql` refreshes the feature cache and updates only fixtures before kick-off. Run it after data imports and before `scripts/add_weekend_v3_venue8_comparison.sql`.
- The candidate refresh now also excludes fixtures that have kicked off. Do not rerun older unguarded snapshot/diagnostic update scripts across played fixtures.
- Fixed missing Football-Data team aliases for Leeds, Hull, Ipswich and Coventry.

## Validation

- Production build and TypeScript checks passed; weekend grouping tests passed, including Monday fixtures, British Summer Time and year boundaries.
- Browser verification against live Supabase data showed exactly ten upcoming fixture cards and ten overview links, no old fixtures, and no browser errors. The Leeds overview link scrolled to the correct match detail.
- The 4–6 September fixture rows and frozen snapshots were compared before and after refresh and were unchanged.

## Hosting

Added **`pl-data.colly.me.uk`** to the existing Vercel production project. Cloudflare CNAME `pl-data` points to `25de94253d3db80a.vercel-dns-017.com`, DNS only, automatic TTL. Vercel verified the domain and issued HTTPS. The existing Basic Auth gate returns 401 to unauthenticated requests, as intended.

The apex `colly.me.uk`, the `forme` subdomain, email records, and the existing `pl-results-project.vercel.app` address were not changed.

## Sources

- Official FPL: `https://fantasy.premierleague.com/api/bootstrap-static/`, `/api/fixtures/`, `/api/element-summary/{id}/`
- Rich football data: `olbauday/FPL-Core-Insights`, existing `data/2026-2027/By Tournament/Premier League/GW3` files
- Understat: live EPL 2026 league data and match rosters; exact date/team/score fixture mapping, existing verified player-ID crosswalks only
- Football-Data: `https://www.football-data.co.uk/mmz4281/2627/E0.csv`
- Transfermarkt: approved published CC0 `games.csv.gz`, inspected directly
