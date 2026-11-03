# Tuesday data refresh — 3 November 2026

Cloud-only recovery against GitHub main dc452082e72e5f1f5c78ece5686b5056bf27df63, Supabase priibitbnmfetyblzltk and Vercel prj_8OeSf0K7GBywgASSo5ojRUpYDg84. No local project checkout, local executor, new recurring schedule or model-rule change.

## Reconciliation and completed writes

The earlier partial run had already imported GW9. This recovery checked all ten final results against native Fotmob and official FPL finished status, 400 native player rows (including Opta-code identity bridges and available statistics), 670 FPL rows against the official event-9 feed and ten closing odds triples against Football-Data. The initial verification recorded zero discrepancies; the later native event-timeline audit below supersedes that statement for three yellow-card fields. Goals total 21, matching summed results; 220 starters across 400 lineup rows. The initial recovery left season data unchanged; the three later verified native-card corrections are recorded below.

Season totals: 90 matches, 3,600 player-stat rows, 5,890 FPL rows, 3,600 lineups, 243 goal events, 90 historical odds rows, 2,461 Understat staged rows and 670 player-season identities. The GW9 FPL source tag from the earlier import still says unchecked; the dated external audit now verifies it against the current official feed without rewriting provenance. FPL remains subject to subsequent official corrections.

Refreshed fpl_player_season_stats_cache, fpl_player_team_season_stats_cache, team_form_window_cache, team_form_window8_cache and betting_team_features_v2_cache using the existing approved definitions. The feature cache includes all 20 GW9 team rows, each with xG for/against. New future-only snapshots 91–100 use unchanged existing SQL and candidate DML. Ten forecasts pass the minimum-four gate; partial histories are explicitly labelled.

Updated only future fixture rows 91–100 with comparison odds observed 12:08:45 GMT and official news checked 12:10:06 GMT. Added the dated archives and ten provisional ledger records (five watches/five passes, no stakes); no historic decisions or settlements changed.

## Preservation checks

All 60 played manual fixtures: hash 104e77d53e93277f637b1ffed6aa3092 unchanged. All 60 pre-existing snapshots: 40228cdeee2e58456b1a2668387e338d unchanged. Frozen v3 input rows: 12,714, hash 4cc75bfac5bd678bb765966945033af1 unchanged. Public policy/grant/security metadata fingerprint d0357bbab1f575f1f36385e73ccd1cf0 unchanged.

Hash convention: md5 of concatenated sorted per-row md5(to_jsonb(row)::text); relevant row ranges and current-season layer hashes are in the checkpoint. Fingerprints are integrity checks, not security credentials.

## Tests and publication

Existing value/review/round/news/paper/score tests and append-only validator pass: 49 total timestamped decisions, first 39 unchanged. Clean dependency install audit reports zero vulnerabilities. Next.js 15.5.28 production build passes (18.579s), including type checking, with existing CSS autoprefixer warnings only. The dated-data validator passed; it checks actual new records, parsed news, saved probabilities, model identity, forecast timing, likely scores and ledger contract.

Production publication/readback is a separate final stage; consult data/full-refresh-2026-11-03-checkpoint.json and the final verification addendum for exact commit/deployment/access status. Never infer successful production deployment from database writes or a local build alone.

## Unresolved coverage

Understat league and match requests timed out repeatedly during this recovery; no GW9 Understat import was fabricated. Last verified baseline remains 374 unresolved appearances/103 IDs and 14 mapped-but-missing core appearances from 27 October, plus unimported GW9 coverage. Transfermarkt public bundle contains no current 2026/27 GB1 rows (latest 24 May 2026); no identity guesses or transfers inferred.

All 20 clubs have fresh official FPL injury/suspension flags; the Liverpool club update adds Gravenberch's European absence. Later weekend press conferences and confirmed XIs are pending, as are executable bookmaker quotes. Cross-provider closing prices exist but matched-bookmaker CLV is unavailable. These limitations do not authorize changing model weights, eligibility or staking.

See [round review](WEEKEND_REVIEW_2026-11-03.md), [next fixtures](WEEKEND_2026-11-06.md) and [automation evidence](TUESDAY_AUTOMATION_2026-11-03.md).

## Production verification — 13:00 GMT

Main commit 4161f36e533c2bc88ac1e096b3b427d865bde58f built successfully on Vercel and was assigned to pl-data.colly.me.uk. Trusted production verification at 13:00:06.771 GMT confirmed authenticated HTTP 200, anonymous HTTP 401 with the existing Basic realm, published GW10 ledger markers, 90 matches, ten eligible future fixtures and no stale fixtures. Verified deployment: dpl_Adg8mMBAq5DtizMWkYPhsq4DuZHt (same commit). No secrets were retrieved or logged.

The temporary validation workspace expired after testing; a later optional filesystem snapshot returned sandbox_stopped. Tests and published files/checkpoints were already preserved; raw temporary downloads were not retained. The subsequent worker-development workspace uses automatic cloud snapshot persistence.

The approved cloud worker is now active. Live dispatch 41645179443 passed through GitHub, Supabase and Vercel; repeat dispatch 41646005513 passed without duplicate data or decisions. The existing scheduled task now dispatches it and remains enabled Tuesday 09:00 Europe/London, next 10 November. See TUESDAY_AUTOMATION_2026-11-03.md.


## Native card corrections — 13:40 GMT

Verified FotMob event IDs show two cautions leading to dismissal for Martínez, Alderete and Jacob Ramsey. Corrected native player_match_stats.yellow_cards from 0 to 2 in exactly three rows. FPL retains its official 0-yellow/1-red scoring representation. No goals, xG, identity, provenance, forecasts, initial ledger events or prior paper settlements changed. Full before/after field and event evidence is in data/source-corrections-2026-11-03.json. All 400 native rows, 400 lineups and 21 goals now match the source adapter; existing Own Goal capitalization is preserved. Corrected native row hash: 9dede6602d8231ac7d22ffa1a86b6d9c. All other season-layer hashes and the 60 frozen forecasts/12,714 frozen inputs remain unchanged.
