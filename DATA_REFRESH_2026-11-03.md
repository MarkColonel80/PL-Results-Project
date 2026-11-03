# Tuesday data refresh — 3 November 2026

Cloud-only recovery against GitHub main dc452082e72e5f1f5c78ece5686b5056bf27df63, Supabase priibitbnmfetyblzltk and Vercel prj_8OeSf0K7GBywgASSo5ojRUpYDg84. No local project checkout, local executor, new recurring schedule or model-rule change.

## Reconciliation and completed writes

The earlier partial run had already imported GW9. This recovery checked all ten final results against native Fotmob and official FPL finished status, 400 native player rows (including Opta-code identity bridges and available statistics), 670 FPL rows against the official event-9 feed and ten closing odds triples against Football-Data. Zero discrepancies in these comparisons. Goals total 21, matching summed results; 220 starters across 400 lineup rows. Existing season data remained byte-for-byte unchanged in protected row fingerprints.

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
