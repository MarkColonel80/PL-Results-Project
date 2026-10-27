# Full refresh — Tuesday 27 October 2026

Completed through connected GitHub, Supabase, Vercel cloud execution and public providers. No Mac project checkout or build was used.

## Imported and reconciled

| Data | Added GW8 | Current 2026/27 total |
|---|---:|---:|
| Completed league results | 10 | 80 |
| Rich player-match rows | 400 | 3,200 |
| Lineup records | 400 | 3,200 |
| Goal events | 19 | 222 |
| Official FPL player-GW rows | 669 | 5,220 |
| Understat source rows | 303 | 2,461 |
| Historical market odds | 10 | 80 |

All twenty clubs now have eight completed league matches. Each GW8 match has 40 rich/lineup records and exactly 22 starters. Official FPL final scores, teams, kickoff times and finished/data-checked flags agree with native Fotmob and the rich mirror. Goals include own-goal handling from native events. FPL component points reconcile exactly for every imported player.

The rich mirror was pinned at commit `8c890d37c2fabfe5548f18c2bb347c3cfc96e091` in [FPL-Core-Insights](https://github.com/olbauday/FPL-Core-Insights/tree/8c890d37c2fabfe5548f18c2bb347c3cfc96e091/data/2026-2027/By%20Tournament/Premier%20League/GW8). Its player-match export had 397 rows; complete native Fotmob reports supplied 400 verified rows. The native report IDs are 5795485–5795494; exact match/provider mappings are retained in the source-check audit.

[Official FPL](https://fantasy.premierleague.com/api/fixtures/) provided finished fixtures, [GW8 live player data](https://fantasy.premierleague.com/api/event/8/live/) and [identity metadata](https://fantasy.premierleague.com/api/bootstrap-static/). Missing event-specific transfer/price metadata was left absent rather than backfilled with today's prices.

[Understat](https://understat.com/league/EPL/2026) supplied match IDs 31250–31259 through its league/match JSON endpoints. Of 303 source rows, 158 have existing verified mappings and 156 enrich matching new core appearances. **145 identities remain unresolved; two verified IDs lack a matching core appearance and were not forced.** All source rows are staged with provenance. Advanced-field mismatch check across mapped staged/core appearances is zero.

[Football-Data](https://www.football-data.co.uk/mmz4281/2627/E0.csv), last modified 26 October 23:12 GMT, supplies ten historical match-odds records. Date, exact team aliases and final scores were checked; raw rows are preserved.

The approved [Transfermarkt games feed](https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/games.csv.gz) returned HTTP 200 and was parsed, but contains **zero 2026/27 PL games** (latest PL game 24 May 2026; feed last modified 5 September). It cannot add current-season transfer/attendance/referee/manager context. This remains an explicit source availability limit.

## Identity and historical safety

- Permanent player codes only. Three new Fotmob crosswalks were established by exact provider Opta ID = official FPL opta_code, never by name. One existing canonical player, Sharman-Lowe (FPL 669 / permanent code 499857), gained the missing season row.
- Forty match-source crosswalks were added, ten each for rich source, Fotmob, FPL and Understat. Internal manual fixture IDs are not provider IDs: several GW8 FPL IDs differ. Exact mappings and provenance are in `data/full-refresh-2026-10-27-source-checks.json`.
- Existing 50 manual fixtures, 50 saved snapshots, 2,660 frozen v3 predictions and all GW1–7 current-season matches/player/FPL data retain their exact pre-import hashes. Earlier goals, lineups, canonical matches, historical odds and Understat staging hashes also match.
- All 220 public database objects' RLS/grants and all 26 policies are unchanged. No schema changes, name matching, invented provider codes or model/betting rule changes were made.

## Caches and forward publication

FPL aggregate caches, team-feature cache, form-window cache and form-window8 cache were refreshed after import. Team-feature cache has 160 current-season team rows and zero differences from its source view. Existing pre-match form updates were restricted to new GW8 matches. Historical research caches were not rebuilt.

The existing future-only snapshot SQL and existing candidate comparison update published ten GW9 snapshots from completed inputs. All ten meet the unchanged four-match venue minimum and are timestamped before kickoff. Old 50 snapshots remain byte-for-byte equivalent by database JSON hash. New diagnostic fields are included through the existing authorized snapshot pipeline; no global retrospective diagnostic update was run.

See [frozen-forecast review](WEEKEND_REVIEW_2026-10-27.md) and [dated GW9 watch/pass report](WEEKEND_2026-10-31.md). The ledger has 39 events, with its first 29 unchanged. No valid GW8 selections existed; nothing was bet or falsely settled.

## Verification and release

Six existing value/weekend/round/news/paper/score suites passed; the 39-event append-only ledger validator passed; TypeScript passed; the production build completed in Vercel cloud execution. Existing Chromium regression tests passed for frozen scores, matching summary/detail, kickoff and focus removal, mobile width and read-only requests.

A live-database GW9 browser check reached ten forecast cards and thirty scorelines; its subsequent wording assertion used an incorrect expected coverage phrase. That test is not claimed as fully passed yet. The temporary execution session reached its service time limit; no project data were lost. Final browser and authenticated production checks will be recorded in the release checkpoint.

The unchanged build emitted existing CSS compatibility warnings. The package audit reported three high and one critical advisory; this data-update task did not upgrade dependencies. A dependency remediation is separate from model/rule changes.

Publication verification is pending in this commit; consult `data/full-refresh-2026-10-27-checkpoint.json` for the final release receipt. Existing Tuesday cloud automation `6ad7a14d306c8190b719bd87b6f73e7d` and other existing recurring jobs were neither duplicated nor modified; their scheduler execution state was not independently inspected.
