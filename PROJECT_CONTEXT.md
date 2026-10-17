# PL Results Project — Persistent Project Context

_Last updated: 2026-10-17_

This file is the durable handoff/source of truth for continuing the project across ChatGPT conversations. At the start of a new project chat, read this file first, then verify live state in GitHub/Supabase/Vercel before making changes.

## Workflow

- GitHub is source/version history.
- Supabase is database/backend and is directly accessible for SQL/migrations.
- Vercel is deployment/production.
- ChatGPT should inspect and modify connected systems directly rather than asking Mark to shuttle files/data around or use Codex.
- Update this file after material schema/model/product/security milestones.

Connected systems:
- GitHub: `MarkColonel80/PL-Results-Project`, branch `main`
- Supabase project: `PL Results Project`, ref `priibitbnmfetyblzltk`
- Vercel project: `pl-results-project`, production `https://pl-data.colly.me.uk` (existing alias `https://pl-results-project.vercel.app`)

## Full stats and weekend news checkpoint — 2026-10-17

This supersedes the older current-season coverage counts below. Full checkpoint: `DATA_REFRESH_2026-10-17.md`; verification and future snapshots: `data/full-refresh-2026-10-17-checkpoint.json`.

- Added Everton 0–2 Chelsea, the only completed match at the refresh cutoff. Results/canonical matches now cover 61 games. Official FPL has 3,942 rows; today’s 59 rows are explicitly final-provisional. Rich player stats and lineups each have 2,440 rows across all 61 matches, with 22 starters per match. All 179 scored goals have goal events. Previously incomplete Sunderland–Brighton and Coventry–Newcastle are filled from direct Fotmob records.
- Native Fotmob player IDs join only through the explicit Opta ID shared with official FPL and existing permanent player codes. No player-name identity matching. Audited all 61 native match reports, preserving provider provenance. Repaired the official Calvert-Lewin goal appeal, two null Brentford scorer identities and verified own-goal fields; historical FPL points stay as awarded after gameweek closure.
- Understat and historical Football-Data odds now cover all 60 games through GW6: 1,853 staged Understat rows, 1,001 mapped through existing verified IDs and 991 enriched canonical appearances, with zero advanced-metric mismatches. Ten mapped source appearances without a matching canonical appearance remain unforced. Today’s Understat match detail and historical closing odds are not published yet. Transfermarkt’s approved published source still has zero 2026/27 PL matches, latest 24 May 2026; do not manufacture coverage.
- FPL aggregates, team feature and form caches are refreshed. The model has 122 current-season team rows with complete xG and zero cache/source differences. Only six future GW7 snapshots were recalculated using the existing formulas and history rules; Tottenham–Coventry remains LIMITED_HISTORY.
- Six remaining fixtures have fresh H/D/A Oddschecker prices observed 17 October at 15:14 UK and source-linked team news checked at 15:15 UK, including absences, suspension appeals, recovery and European schedules. `/betting/weekend` displays the dated reports and expandable official FPL availability flags; flags may lag club news. Confirmed starting teams are pending. The reports do not adjust probabilities. Payload: `data/weekend-2026-10-17-news.json`.
- The 34 fixtures already kicked off retain their complete saved fixture/odds/snapshot records, including the three 15:00 UK games. All 60 previous match rows remain unchanged. Historical rows outside the explicitly documented source corrections retain matching integrity hashes. No formula, weight, eligibility, schema, RLS or grant changes.
- Morning investigation decisions are frozen separately in `data/weekend-2026-10-17-prerefresh-investigation.json`; this refresh does not retrospectively change them or create selections. No bets were placed. Weekend review/news/value tests and production build pass; a local browser verified six news panels, current odds and the 61-match status with no console errors.

## Weekend and model-input checkpoint — 2026-10-16

This supersedes the older latest-result/odds/fixture counts below. Full checkpoint: `WEEKEND_2026-10-17.md`.

- `/betting/weekend` now contains all ten verified GW7 fixtures for 17–19 October with complete H/D/A Oddschecker coupon prices observed 16 October at 21:56 UK. Price source fractions, decimal conversions, source match IDs and timestamps: `data/weekend-2026-10-17-fixtures.json`.
- Results/canonical matches: 60 completed games through GW6 / 12 October. Each of the 20 clubs has six current-season matches; betting inputs/cache contain 120 complete-xG rows with no discrepancies.
- Added 667 provider-labelled FPL gameweek rows from the established `olbauday/FPL-Core-Insights` mirror at `4ae5ceb679daa4421e9b5e9677ac412e412edff3`, retaining verified permanent player IDs and GW6 club membership. FPL total 3,883 rows; zero point-component mismatches. Direct API fetching was unavailable, so these are labelled with mirror provenance.
- Added 320 rich player-match rows for eight complete games, total 2,315 current-season rows. Sunderland–Brighton and Coventry–Newcastle rich feeds are incomplete and remain staged; the existing FPL xG fallback covers them. Understat, lineup/goal-event tables and Football-Data historical odds were not refreshed as part of this fixture task.
- Seven eligible research forecasts. Fulham–Hull, City–Ipswich and Tottenham–Coventry remain LIMITED_HISTORY: each promoted away side has only three relevant away matches. The minimum stays four. All eligible triples sum to one and the existing anon role reads all ten fixture/snapshot records.
- All 30 older manual fixture/snapshot records, existing GW1–5 match/FPL/rich-player data and frozen v3 forecasts retain exact pre-update hashes. FPL, betting-feature and team-form caches were refreshed; existing pre-match form calculations populated only the new GW6 match rows. Model formulas, weights, eligibility, RLS/grants and app code are unchanged. Guarded pre-kickoff refresh order was preserved.
- Manual fixture IDs 61–70 are not claimed as native provider IDs; match identities use the recorded rich source IDs and exact teams/date. Saved forecast/check evidence: `data/weekend-2026-10-17-checkpoint.json`.
- Review prompts apply to the round, but current squad/Europe/confirmed-team checks and a betting shortlist have not been carried out by this fixture update. Browser automation was unavailable; the existing public data read was verified directly.

## Weekend review checks and learning policy — 2026-10-10

Mark asked what we can learn and put in place for next week following Chelsea–Bournemouth and Arsenal–Leeds. Strengthen assessment and record keeping; do not change probabilities in response to two results.

- `/betting/weekend` now separates mathematical value from a completed assessment: every fixture has a **Before betting — review required** panel and summary link. A green arrow is only the saved probability minus the break-even probability at the saved price.
- Panels show the observation time of saved prices, prompts for squad news/returning players/confirmed teams, Europe/recovery/travel/rotation, manager/squad changes, and recording a decision before the result. News and team selection are not model inputs; these prompts do not claim those checks have been completed.
- Automatic prompts identify partial venue samples and outcomes where one forecast has positive value at the quoted price and the other does not. This concerns the price threshold, not merely which team each view favours. The two views use shared data and are not independent validation.
- A defensive comparison converts each saved Venue8 per-game GA/xGA back to totals over its actual sample. Bournemouth's pre-match away sample was 7 conceded versus 14.4 xGA over 8 games. The panel does not infer goalkeeper skill, significance, regression size or an injury adjustment from this gap.
- For the next round: first complete the results refresh after the final game and verify canonical club names, source/cache agreement, xG completeness and history counts. Preserve all played pre-kickoff snapshots. Publish/refresh only upcoming fixtures using the existing guarded scripts. Then review **all** eligible outcomes, including draws, against actual available prices; suppressed forecasts remain suppressed.
- Shortlisted outcomes require a written check of official/latest club news and the Europe schedule before and after the weekend fixture. Recheck confirmed teams and the price near kick-off. Inspect existing xG-only/longer-history diagnostics when an edge depends on unusually low goals conceded, older seasons or a changed manager. These are sensitivity checks, not validated probability replacements. If a diagnostic crosses the price threshold, flag the fragility rather than choosing the most favourable estimate.
- Record before kick-off: fixture/outcome; both probabilities/model versions; bookmaker and available decimal price with observation time; break-even probability; source links/times for squad/Europe checks; relevant history/finishing/sensitivity concerns; decision (`watch`, `paper selection`, or `pass`) and reason. These records do not assert that Mark placed a bet. Freeze the original record; append later news/price observations with their own timestamps rather than silently replacing it.
- After full time, append result and the settled outcome, plus xG **with provider/provenance** and shot/game-state context where reliable. Score every eligible published H/D/A forecast against the outcome and a same-time no-vig market benchmark; track pre-recorded selections separately with hypothetical equal stakes and observed prices. Report Brier/log-loss, sample size, calibration and price movement over accumulating rounds. Do not count a near miss as a successful prediction or backfill selections after results.
- Shot composition remains research: the September pilot's small improvement and inconsistent recent shot/xGOT feed do not justify promoting a new chance-quality/goalkeeper adjustment. Next useful diagnostics are non-penalty chance size/volume, rebounds, and score state at the time of shots, subject to source reconciliation. Keep provider-specific xG separate; match xG is not a pre-match win probability.
- The 10 October review below is partial: both Bournemouth away-win and Arsenal–Leeds draw outcomes lost. Other weekend games are not evaluated here. See `WEEKEND_2026-10-10.md` for source-linked observations. No bets were placed by the assistant, no results were imported in this change, and formulas/weights/minimum history/saved snapshots are unchanged.
- Implementation: `lib/weekend-review.ts`, `scripts/test_weekend_review.mjs`, `app/betting/weekend/page.tsx`. The prompts apply automatically to each newly published round; club-news checks and future updates still need to be carried out at that time.

## Weekend value review and applied input repair — 2026-10-09

This supersedes any assumption below that complete row/xG coverage also established complete club history in the saved GW6 forecasts.

- Read-only audit found eight clubs split between full and shortened names in GW4/5. All 50 match results and 100 team-xG rows existed, but full-name feature lookups omitted two recent games for those clubs. The approved repair on 9 October at 15:37 UK time restored 20 club labels with five matches each.
- Known club aliases: Bournemouth, Brighton, Leeds, Man City, Man Utd, Newcastle, Nott'm Forest and Spurs. No player-name matching or identity changes are involved.
- A read-only replay reunites these labels before calculating the existing current-spell history windows. It establishes five games for each of 20 clubs and preserves the same seven eligible fixtures. Corrected figures and sensitivity checks: `BETTING_WEEKEND_VALUE_REVIEW_2026-10-09.html`.
- Corrected City away-win probabilities are primary 49.9% / research 44.5%; Bournemouth 42.4% / 39.3%; Forest 51.1% / 41.4%; Brighton 47.9% / 47.4%; United home 56.2% / 58.2%. These now match the live weekend inputs and saved research snapshots exactly. Applied checkpoint and integrity hashes: `data/weekend-2026-10-10-corrected.json`.
- City at 2.40 is the more credible modest value candidate. Bournemouth at 4.75 has the largest apparent gap, but the mixed model rewards 7 away goals conceded versus 14.4 xGA over eight games; six are from last season. Longer history and xG-only diagnostics weaken the signal. Arsenal–Leeds draw at 5.25 is a secondary watch. Forest/Brighton remain conditional; Brentford has conflicting views and United's margin is too small at 1.75. Current club squad checks are incomplete; forecasts do not explicitly account for individual absences.
- Prevention fixes: `scripts/update_season_v5.py` canonicalises known club aliases at import; `scripts/normalize_current_team_names.py` now includes `canonical_matches`. Compilation and whitespace checks pass.
- Mark explicitly approved applying the prepared repair. `scripts/repair_2026_10_09_team_names.sql` ran successfully as one guarded transaction: 14 source match rows, 14 canonical match rows, 318 player-match rows, 318 lineup rows and 41 goal-event rows had known club labels corrected. The feature cache was refreshed; saved forecast refreshes were restricted to IDs 51–60 before kick-off. Post-checks show zero cache/source discrepancies, 20 clubs × five complete-xG matches, seven eligible predictions and the same three LIMITED_HISTORY fixtures. All protected statistics/player IDs, saved odds, 20 played weekend fixture/snapshot records, unrelated future snapshots and frozen v3 forecasts were preserved.
- The weekend summary now includes a `Value vs odds: H / D / A` column using the adjacent 24-match + Venue8 probability. Each match's odds table also shows separate current/research value rows. Green ↑ means a positive gap above the actual price's break-even probability (`p − 1 / odds`), red ↓ negative, grey → break-even; the gap is percentage points, not profit. Missing odds or suppressed forecasts show —. Bookmaker no-vig probabilities remain separately labelled. `scripts/test_betting_value.mjs` covers the margin trap, signs, break-even, rounding and unavailable values; the production build passes.
- Model formulas, weights, eligibility rules and frozen v3 are unchanged. Diagnostic xG-only and Venue18 calculations have not been promoted. Earlier frozen-v3 large-gap betting losses are context, not validation of this comparison candidate.
- Local evidence bundle: `/Users/mark2/Documents/Codex/2026-09-10/i-a/outputs/weekend-value-review-2026-10-09/` (original snapshots, corrected inputs, read-only queries and report). No bets were placed.

## Latest odds checkpoint — 2026-10-09

- All ten 10–12 October Matchweek 6 fixtures now have home, draw and away market odds from the Oddschecker UK Premier League coupon, observed 9 October at 14:56 UK time (`2026-10-09T13:56:57Z`).
- Source fractional prices, full decimal conversions, URL and observation time are saved in `data/weekend-2026-10-10-fixtures.json`; the live Supabase fixture rows match this payload.
- The page's public data query reads ten fixtures with complete market prices and snapshots. Normalised bookmaker probabilities pass the sum-to-one checks.
- All 30 saved model snapshots and the 20 played fixture records retain their exact pre-update hashes. The model still uses results through GW5; the three limited-history fixtures remain suppressed.
- Full round and odds checkpoint: `WEEKEND_2026-10-10.md`.

## Latest results checkpoint — 2026-09-25

This section supersedes the older current-season counts and weekend state below. Full checkpoint: `DATA_REFRESH_2026-09-25.md`.

- Results/canonical fixtures: 50 completed matches through GW5 / 20 September.
- Official FPL: 3,216 rows / 50 fixtures, zero point-component mismatches and 667 current-season players.
- Rich canonical: 1,995 player-match rows / 50 matches; no missing permanent player codes. There are 1,635 derived lineup rows and 110 goal events.
- Two Brentford–Chelsea shot-derived goals have no source scorer identity and remain null rather than guessed.
- Understat: 1,538 staged rows / 50 matches, 836 mapped through verified provider IDs, 828 canonical rows enriched, and zero advanced-metric mismatches. Eight mapped staged appearances lack a canonical appearance and remain unforced.
- Team model/cache: 100 team rows / 50 matches, complete xG coverage. FPL and team-form caches are refreshed.
- Football-Data odds: all 50 completed current-season fixtures imported and mapped.
- Transfermarkt's approved published data still has zero 2026/27 Premier League matches; provenance remains unchanged.
- All saved pre-refresh hashes for GW1–3 FPL, rich player-match, lineup, goal, Understat and odds rows matched after the refresh. All 20 played manual prediction snapshots also remained byte-for-byte stable by hash.
- `/betting/weekend` now contains all ten official Matchweek 6 fixtures for 10–12 October. Seven have 24-match + Venue8 probabilities; Ipswich–Fulham, Hull–Everton and Coventry–Newcastle remain `LIMITED_HISTORY`. Full checkpoint: `WEEKEND_2026-10-10.md`.
- Market prices for the 10–12 October round were added on 9 October; use the latest odds checkpoint above.
- Frozen v3, the Venue8 candidate architecture, identity rules, RLS and grants are unchanged. The Supabase Security Advisor still has zero error/critical findings.

## Shot-composition research checkpoint — 2026-09-10

Mark proposed examining whether the same total xG made from many small chances versus fewer large chances has different predictive value, and whether opponent defence/goalkeeper quality changes that interpretation. The first local historical study is saved in `XG_SHOT_COMPOSITION_RESEARCH_2026-09-10.md`.

- Existing Understat archive contains individual shot events: ten complete seasons (2014/15–2023/24), plus 59 games from 2024/25. One incomplete historical match was excluded.
- Understat match xG is rebound-adjusted: grouping consecutive shots explicitly labelled `lastAction=Rebound` and applying `1-product(1-p)` reproduces 7,715/7,716 non-empty team-match totals within 0.005. Raw shot sums are not interchangeable with these published totals.
- Average non-penalty shot quality is moderately persistent across separate eight-match blocks (correlation 0.402); total non-penalty xG (0.672) and shot volume (0.632) are more persistent.
- A chronological, expanding-season test used 1,360 fixtures from 2020/21–2023/24, with exact frozen v3 predictions as the baseline. Added prior attacking/conceded chance quality slightly improved H/D/A Brier: 0.58509 to 0.58392 against an equally calibrated control; raw frozen v3 scored 0.58450. Blank prediction worsened slightly. An extra attack/defence interaction did not improve on the simple quality addition. Rebound-sequence sensitivity was similar.
- This is a small exploratory signal, not a validated model upgrade. No frozen v3, Venue8 candidate, live prediction, database or deployment changes were made. It does not establish that 0.10 xG chances should be discounted specifically against Arsenal or another named opponent.
- The recent FPL-Core-Insights shot feed failed enough shot/xG/xGOT consistency checks that no forecast rows met the complete-history rule for a goalkeeper pilot. In 2025/26, xGOT reconciled on both sides in 148/380 matches; in 2026/27 through GW3, only 1/30. Reconcile native shot records and establish goalkeeper identities before testing an individual keeper adjustment.
- Do not treat 2025/26 as an untouched holdout. The 43 eligible fixtures from the incomplete 2024/25 archive were reported separately. The current Venue8 candidate was not the comparator in this first study.
- Reproducibility bundle on this Mac: `/Users/mark2/Documents/Codex/2026-09-10/i-a/outputs/PL-Data-Hub-xG-research.zip`. Working scripts/cache: `/Users/mark2/Documents/Codex/2026-09-10/i-a/work/xg-study`. Numerical and temporal leakage checks passed.

## Previous operational checkpoint — 2026-09-08

This section supersedes the older current-season counts and weekend state below. Full checkpoint: `DATA_REFRESH_2026-09-08.md`.

- Production: **https://pl-data.colly.me.uk**; existing Vercel address still works. Use the `pl-data` subdomain only. Mark explicitly does not want this app on the main `colly.me.uk` domain.
- Results/canonical fixtures: 30 completed matches through GW3 / 6 September.
- Official FPL: 1,890 rows / 30 fixtures, zero point-component mismatches.
- Rich canonical: 1,199 rows / 30 matches; no missing permanent player codes.
- Understat: 929 staged rows / 30 matches, 507 mapped, 502 enriched, zero advanced-metric mismatches. Five mapped staged appearances still lack a canonical row and remain unforced.
- Team model/cache: 60 team rows / 30 matches, complete xG coverage. FPL and current team-form caches refreshed.
- Football-Data odds: all 30 completed current-season fixtures imported. Corrected missing team aliases.
- Transfermarkt published PL games still stop at 24 May 2026; zero 2026/27 games despite the newer 5 September repository commit.
- `/betting/weekend`: **upcoming games only**, currently 12–14 September (10 fixtures including Monday Leeds–Newcastle). Mark asked to remove passed games from this page; do not add an archive selector there.
- Seven eligible candidate predictions; Chelsea–Hull, Palace–Ipswich and Coventry–Brighton remain LIMITED_HISTORY.
- Keep played fixture inputs/predictions frozen in Supabase. The 4–6 September state is also in `data/weekend-2026-09-04-frozen.json`.
- Refresh order: load and verify sources → refresh aggregate/current feature caches → `scripts/refresh_upcoming_weekend_snapshot.sql` → `scripts/add_weekend_v3_venue8_comparison.sql`. Both snapshot scripts now restrict updates to fixtures before kick-off. Older diagnostic scripts may update all snapshots; do not run them unfiltered on played games.
- Frozen v3, model architecture, identity rules and existing RLS/grants are unchanged. The 7 September Dixon–Coles and close-game-confidence experiments remain research only.

## Thought to revisit — draw interpretation, 2026-09-08

Mark's hypothesis: some model/market disagreements may point to a greater chance of a draw. Evidence that a favourite may struggle to win does not necessarily establish that the other team is more likely to win; similarly, an underlying xG advantage may produce a competitive draw rather than a decisive result.

- Examples discussed for 12 September: Aston Villa–Nottingham Forest, Tottenham–Everton, and Bournemouth–Brentford.
- Bournemouth's seven draws in its last eight home matches made the distinction particularly relevant, despite the model's favourable xG assessment.
- This is an unproven interpretation to keep alongside the forecasts, not a validated draw signal. Mark explicitly requested no model changes: retain the existing probabilities, weights and frozen snapshots.
- Existing context: `BETTING_DIXON_COLES_EXPERIMENT_2026-09-07.md` found that a fixed draw adjustment was not consistently beneficial across seasons. This note does not overturn that decision or request a new experiment.

## Player identity policy and state

Identity policy is strict and permanent:
- provider-prefixed canonical player codes are prohibited
- automated player-name matching is prohibited as identity evidence
- names may be used only as QA after ID-based matching, except explicitly reviewed manual exceptions
- source-provider IDs belong in mapping tables, not canonical identity

Stable Understat history state:
- staged rows: 106,519
- staged source players: 1,899
- verified mappings: 1,816
- deliberately unresolved source players: 83
- mapped staged rows: 105,041
- mapped staged rows missing live: 0
- advanced metric mismatches: 0
- remaining verified `source_native_identity`: 136, all 2014/15-only
- explicit `manual_name_verified`: 4

## Current season — 2026/27 through Matchweek 2

Detailed refresh checkpoint: `DATA_REFRESH_2026-09-01.md`.

Official FPL current-season state:
- `public.fpl_player_match_stats`: 1,236 rows
- 20 fixtures
- max gameweek 2
- point-component mismatches: 0
- missing teams: 0

Rich canonical player-match state:
- `player_match_stats`: 759 rows across 19 of 20 completed matches
- missing rich player-match source: Aston Villa v Arsenal
- no substitute core appearances were fabricated for that match
- permanent player-code identity remains intact

Team-level betting state remains complete despite the rich-player gap:
- `public.betting_team_match_v2`: 40 team rows / 20 matches
- xG populated for all 40 rows through canonical/FPL fallback architecture

Understat current-season state:
- all 20 completed fixtures mapped exactly by date + teams + score
- 622 staged player-match rows
- 341 rows resolve through pre-existing verified mappings
- 281 remain unresolved and deliberately unguessed
- 313 canonical rows enriched with Understat advanced metrics
- advanced-metric mismatches after update: 0

## Transfermarkt archive

Source: CC0 `dcaribou/transfermarkt-datasets`.

As of 2026-09-01 the published Premier League source contained no 2026/27 data. Do not silently switch provenance merely to manufacture current-season coverage.

2025/26 archive state:
- 380/380 matches
- 11,492 staged appearance rows
- 11,418 linked to canonical player codes
- 74 unresolved rows across 30 source players
- 114 additional players resolved through conservative non-name fingerprint matching with 100% accepted overlap
- rich canonical 2025/26 player-match rows were not overwritten

## Historical market data

`public.historical_market_odds` contains full Football-Data Premier League odds for 2019/20–2025/26 plus completed 2026/27 matches already imported.

Closing no-vig market Brier/log-loss benchmarks:
- 2019/20: 0.60561 / 1.00871
- 2020/21: 0.61851 / 1.02967
- 2021/22: 0.53384 / 0.90077
- 2022/23: 0.57395 / 0.95959
- 2023/24: 0.52969 / 0.89735
- 2024/25: 0.57519 / 0.96725
- 2025/26: 0.60774 / 1.01177

2024/25 has complete xG via FPL fallback in `betting_team_match_v2`; any older statement that 2024/25 lacked xG is superseded.

## Model v3 — validated baseline

Detailed spec: `BETTING_MODEL_V3.md`.
Historical results: `BETTING_MODEL_V3_7_SEASON_RESULTS.md`.

Frozen v3 state:
- `public.betting_model_match_predictions`, `model_version='v3'`
- 2,660 matches across 2019/20–2025/26
- top-pick accuracy 53.4% versus bookmaker favourite 55.0%
- remains the validated baseline; it has NOT been replaced in production

Core v3 architecture:
- up to 30 PL matches per team
- 65% xG + 35% actual goals, xG weighting scaled only for incomplete coverage
- four pseudo-match league shrinkage
- rolling league home/away scoring baseline
- multiplicative attack × opponent defence, exponent 0.75
- PPG10 multiplier strength 0.14
- independent Poisson H/D/A probabilities
- bookmaker odds are comparison only, never fed into the probability
- normal production betting gate requires both clubs to have at least 10 matches in their current PL spell

Important: current reconstructed feature views do not exactly reproduce every cached frozen v3 lambda. Experiments that claim to preserve frozen v3 should use cached frozen lambdas/probabilities where appropriate.

## Model v6 — composite research

Detailed checkpoint: `BETTING_MODEL_V6_COMPOSITE_EXPERIMENT.md`.

Supabase research layers include:
- `public.betting_model_v6_components`
- `public.betting_team_residual_features_v6`
- `public.betting_model_v6_residual_xg_component`

The residual-aware xG30 component trusts at most 25% of a 30-match Goals−xG / GA−xGA residual, shrunk by available sample. It produced a small clean improvement inside v6 but did not solve the 2025/26 instability. v6 remains experimental only.

## Current 24-match + Venue8 research candidate — 2026-09-02

This is the leading new comparison architecture, shown on `/betting/weekend`, but it has NOT replaced v3.

Detailed research checkpoints:
- `BETTING_V3_VENUE8_15_RESIDUAL_EXPERIMENT_2026-09-01.md`
- `BETTING_V3_VENUE8_STRUCTURAL_WINDOW_SWEEP_2026-09-01.md`
- `BETTING_V3_VENUE8_RECENCY_WEIGHTING_2026-09-01.md`
- `BETTING_V3_VENUE8_SHRINKAGE_RELIABILITY_2026-09-01.md`
- `BETTING_V3_24_VENUE8_PPG_ABLATION_2026-09-01.md`

Chosen candidate architecture:
1. Up to 24 previous Premier League matches from the club's current PL spell, equal weight.
2. Overall structural attack/defence uses 65% xG + 35% capped actual goals.
3. Positive freak-result cap is one-sided, match by match: `capped actual = min(actual, xG + 1.0)` for GF and GA. Underperformance is never lifted toward xG.
4. Four pseudo-match shrinkage toward the recent league scoring midpoint.
5. Opponent attack/defence interaction with exponent 0.75.
6. Venue8 uses relevant home matches for the home side and away matches for the away side, current PL spell only.
7. Venue8 attack/defence is 50% raw venue xG + 50% capped actual.
8. Team-specific Venue8 match baseline is then shrunk **50/50 toward the generic league home/away baseline**.
9. Independent Poisson converts expected goals to H/D/A probabilities.
10. **No PPG10 multiplier.** PPG10 is diagnostic only.
11. No extra Goals−xG residual correction at the 15/24 structural stage.
12. No structural recency weighting inside the 24 matches.
13. No adaptive Venue8 reliability switch; tested gates did not validate robustly.

Key model-selection findings:
- structural 24-match window was almost indistinguishable from 30 on development calibration while being more responsive; 24 Brier 0.58137 versus 30 0.58123 before the later Venue8-shrink/PPG ablations
- simple recency weighting inside 24 worsened calibration, so equal weighting remains
- full-strength Venue8 was too volatile; 50% Venue8 / 50% generic venue baseline materially improved calibration
- fine sweep around 50% did not justify tuning to 55%; use the clean 50/50 rule
- no tested reliability gate based on Venue8 extremeness, structural disagreement, cap size, or Venue18 disagreement validated robustly

PPG10 ablation on the final 24 + 50%-Venue8 architecture:
- GW15+ development 2019/20–2024/25, n=1,433:
  - **no PPG:** accuracy 54.36%, Brier 0.57474, log loss 0.96908
  - with PPG10: accuracy 54.08%, Brier 0.57553, log loss 0.97052
- 2025/26 stress check, n=240:
  - no PPG: accuracy 45.00%, Brier 0.63814, log loss 1.05587
  - PPG10: accuracy 47.50%, Brier 0.64193, log loss 1.05815

Probability calibration is the fitting objective; top-pick accuracy is secondary. Therefore PPG10 was removed from this candidate.

## Weekend betting page

Route: `/betting/weekend`.

Two distinct displays now coexist:

### Existing manual weekend rule
- hard eligibility floor: BOTH teams must have at least 4 relevant current-spell venue matches
- 1–3 relevant venue matches on either side => `LIMITED_HISTORY`, no expected goals/probabilities/fair odds/pick
- 4–7 => eligible partial Venue8
- 8 => full Venue8
- venue PPG8 decides unless absolute PPG gap <= 0.30, then capped adjusted venue xG breaks the tie
- overall PPG30 and Venue18 are diagnostics only

### 24-match + Venue8 research comparison
- uses the current candidate architecture above
- displays structural sample, expected goals, H/D/A probabilities, fair odds and top outcome
- does not overwrite the existing manual weekend pick
- PPG10 remains visible only as diagnostic information

Refresh script:
- `scripts/add_weekend_v3_venue8_comparison.sql`
- MUST refresh `public.betting_team_features_v2_cache` before calculating the comparison

Reason: Arsenal v Chelsea exposed a stale-materialized-cache bug. The stale comparison gave Arsenal 76.6%; after refreshing missing current matches it fell to 67.0%. Decomposing the fresh result showed:
- structural-only generic venue baseline: Arsenal ~55.0%
- + 50% Venue8: Arsenal 58.8%, draw 24.2%, Chelsea 17.0%
- + old PPG10: Arsenal 67.0%

That led to the PPG10 ablation and removal. Current Arsenal–Chelsea comparison with fresh data/no PPG is about 58.8 / 24.2 / 17.0, expected goals about 1.66–0.77.

## 2025/26 diagnosis

2025/26 remains an abnormal stress season and must not be tuned away blindly.

On the exact GW15+ sample the league produced a major draw spike without a comparable xG shift. Both v3 and the market materially under-anticipated draws. Bournemouth, Leeds and Brentford accounted for a large concentration of the unusual draw behaviour; removing matches involving those three restored v3 performance near its six-season norm.

Do not use 2025/26 as a pristine holdout anymore: it has now been inspected repeatedly. Use 2019/20–2024/25 for development/model selection and treat 2025/26 as a stress check.

Rejected/unsupported structural additions include:
- Elo-style team rating
- global draw multiplier
- rolling league H/D/A regime correction
- strong short-term recency decay
- adaptive Venue8 reliability gates tested so far

## Supabase security hardening — 2026-09-02

Detailed checkpoint: `SECURITY_HARDENING_2026-09-02.md`.
Reproducible SQL: `scripts/security_hardening_2026_09_02.sql`.

Trigger: Supabase emailed a critical `rls_disabled_in_public` warning. Live inspection confirmed 12 exposed public tables had RLS disabled and browser roles held broad write privileges.

Permanent security rules now:
- all exposed base tables have RLS enabled
- browser roles have SELECT-only access to tables required by the public/read-only app
- internal source mapping tables have no browser grants/policies
- four write-capable `SECURITY DEFINER` maintenance RPCs are not executable by `public`, `anon` or `authenticated`; `service_role` retains execution
- public-facing aggregate views use `security_invoker=true`
- internal/research views and research materialized views are not browser-accessible
- function `search_path` is pinned for the functions flagged by the advisor
- `source_player_match_stats` exposes only five audit metadata columns to browser roles (`source`, `source_player_id`, `player_name`, `season`, `team_name`) under RLS, not full staging rows
- `player_identity_name_audit_v1` is security-invoker
- the player-name audit approval table remains the only intentional browser write path; it permits only SELECT/INSERT/UPDATE and only for an exact already-verified source mapping. It cannot alter canonical mappings or invent mapping keys.

Final Supabase Security Advisor state after hardening:
- **0 ERROR / critical findings**
- no `rls_disabled_in_public`
- no public SECURITY DEFINER write RPC warnings
- no `security_definer_view` errors
- no mutable function-search-path warnings
- no exposed research-materialized-view warnings

Remaining notices are intentional:
- INFO `rls_enabled_no_policy`: `source_game_events`, `source_match_mappings`, `source_player_mappings` — private internal tables, no browser policy by design
- WARN `materialized_view_in_api`: `fpl_player_season_stats_cache`, `fpl_player_team_season_stats_cache` — retained because public security-invoker aggregate views depend on them; they contain aggregate public football/FPL data

Browser-role smoke tests passed after the migration for the player/history/team/insights/Betting Lab aggregate views and the player-name audit read/upsert path.

## Betting research rules

- No look-ahead leakage.
- Every historical prediction uses only information available before kickoff.
- Keep source/model versions explicit.
- Fit probabilities using Brier/log loss; evaluate betting edge/ROI only afterwards.
- Compare model probabilities against no-vig closing market probabilities where available.
- Do not tune a threshold and validate it on the same sample.
- Include all qualifying bets from declared rules; no cherry-picking.
- Do not hard-code bookmaker agreement into the predictive model merely to make ROI look better.
- Model outputs are research probabilities, not guaranteed winners.

## Current modelling direction

1. Keep frozen v3 as the validated baseline.
2. Keep v6 as a separate transparent composite research model.
3. Treat the no-PPG 24-match + 50%-Venue8 architecture as the leading new comparison candidate, not yet production v3.
4. Continue investigating genuine model/market disagreements by decomposing structural, venue and data-freshness effects before adding new features.
5. Do not reintroduce PPG10, residual correction, structural recency weighting or adaptive Venue8 gates without new out-of-sample evidence.
6. Maintain the hard minimum-four relevant venue-history rule on the manual weekend model.
7. Always refresh dependent materialized feature caches after current match data is loaded and before weekend comparison calculations.
8. Preserve the 2026-09-02 Supabase privilege/RLS architecture when adding new tables, views, materialized views or RPCs. New browser-facing objects should be least-privilege by default.

## Current verified headline state — 2026-09-25

- FPL 2026/27: 3,216 rows / 50 fixtures / GW5 complete / zero point-component mismatches
- canonical core player-match stats: 1,995 rows / 50 matches / no missing permanent player codes
- Understat 2026/27 staged: 1,538 rows / 50 matches / 836 mapped through verified IDs
- Understat current-season canonical enrichment: 828 rows / 0 advanced-metric mismatches
- `betting_team_match_v2`: 100 rows / 50 matches / all with xG
- Football-Data 2026/27 odds: 50/50 completed fixtures mapped
- Transfermarkt 2026/27: unavailable from the project's approved published source as of 2026-09-25
- Transfermarkt 2025/26: 11,492 staged rows / 380 matches; 11,418 linked; 74 unresolved across 30 source players
- v3 remains validated production baseline
- v6 remains experimental
- leading comparison candidate is 24-match capped structure + 50%-shrunk Venue8, no PPG10
- weekend comparison refresh includes a mandatory team-feature materialized-view refresh
- ten future Matchweek 6 fixtures are loaded for 10–12 October; seven are model-eligible and all ten have market odds observed on 9 October
- Supabase Security Advisor has 0 ERROR/critical findings after the 2026-09-02 hardening

## Continuation instruction

When Mark asks to continue this project, read this file, then inspect current GitHub/Supabase/Vercel state before acting. Do not ask Mark to repeat project history that can be recovered from connected systems. Preserve both the identity-safety rules and the 2026-09-02 least-privilege Supabase security rules.

