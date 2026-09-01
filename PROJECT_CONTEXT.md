# PL Results Project — Persistent Project Context

_Last updated: 2026-09-01_

This file is the durable handoff/source of truth for continuing the project across ChatGPT conversations. At the start of a new project chat, read this file first, then verify live state in GitHub/Supabase/Vercel before making changes.

## Workflow

- GitHub is source/version history.
- Supabase is database/backend and is directly accessible for SQL/migrations.
- Vercel is deployment/production.
- ChatGPT should inspect and modify connected systems directly rather than asking Mark to shuttle files/data around or use Codex.
- Update this file after material schema/model/product milestones.

Connected systems:
- GitHub: `MarkColonel80/PL-Results-Project`, branch `main`
- Supabase project: `PL Results Project`, ref `priibitbnmfetyblzltk`
- Vercel project: `pl-results-project`, production `https://pl-results-project.vercel.app`

## Historical/player identity state

Understat Premier League history has been staged and identity-resolved.

Stable final identity state:
- staged Understat rows: 106,519
- staged source players: 1,899
- verified Understat mappings: 1,816
- deliberately unresolved source players: 83
- mapped staged rows: 105,041
- mapped staged rows missing live: 0
- advanced metric mismatches: 0
- remaining verified `source_native_identity`: 136, all 2014/15-only
- explicit `manual_name_verified`: 4

Identity policy:
- provider-prefixed canonical player codes are prohibited
- automated player-name matching is prohibited as identity evidence
- names may be used only as QA after ID-based matching, except explicitly reviewed manual exceptions

## Current-season data — 2026/27 through Matchweek 2

Detailed refresh checkpoint: `DATA_REFRESH_2026-09-01.md`.

Official FPL current-season state after GW2:
- `public.fpl_player_match_stats`: 1,236 rows
- 20 distinct fixtures
- max gameweek 2
- GW2 write: 626 player-fixture rows across all 10 fixtures
- point-component mismatches: 0
- missing teams: 0

Identity remains permanent `player_code`; season-local FPL IDs are metadata only.

Rich current match/player feed:
- all 10 completed GW2 match rows were recognised
- 360 GW2 `player_match_stats` rows were published by the rich source
- canonical `player_match_stats` currently covers 19 of the 20 completed 2026/27 matches, 759 rows total
- the missing rich player-match source file is `26-27-prem-aston-villa-vs-arsenal`
- no substitute core appearances were fabricated for Villa–Arsenal
- missing permanent player codes: 0
- missing teams: 0

Team-level betting data remains complete despite the Villa–Arsenal rich-player source gap:
- `public.betting_team_match_v2`: 40 team rows / 20 matches
- xG populated for all 40 rows through the existing fallback architecture

Understat current-season state:
- all 20 completed matches mapped exactly by date + teams + score
- 622 staged `source_player_match_stats` rows
- 1,816 existing verified Understat player-ID mappings loaded
- 341 staged current-season rows resolve through pre-existing verified provider-ID mappings
- 281 staged rows remain unresolved and were deliberately left unresolved; no automated player-name mapping was used
- 313 existing canonical `player_match_stats` rows enriched with Understat `xg`, `xa`, `shots`, `key_passes`, `xg_chain`, and `xg_buildup`
- `advanced_source='understat'` provenance written with source match/player IDs
- post-update advanced-metric mismatches: 0
- Understat enrichment did not overwrite core minutes/goals/assists/cards

Mapped staged Understat rows without a matching canonical player-match row: 28 total:
- 24 are Villa–Arsenal and are explained by the missing rich player-match source file
- 2 are Matt Grimes across Coventry's first two matches
- 2 are Chuba Akpom across Ipswich's first two matches

The Grimes/Akpom cases use older source-native canonical identities and do not yet have enough current PL overlap for the conservative cross-source resolver. They remain staged only; do not use names to force a mapping.

## Transfermarkt archive/state

The project uses the CC0 `dcaribou/transfermarkt-datasets` source. Its published Premier League `games` data currently runs through season `2025` (2025/26). The source snapshot checked on 2026-09-01 was last modified on 5 Aug 2026 and contained 0 games for season 2026 / 2026/27.

Therefore no 2026/27 Transfermarkt player-match data has been imported. This is a source-availability limitation, not a database failure. Do not silently switch to a different Transfermarkt scraper/provenance just to manufacture current-season coverage.

### 2025/26 Transfermarkt archive refresh — completed 2026-09-01

The newly available complete 2025/26 archive was audited and staged.

Strict completeness gate:
- 380/380 Premier League matches present
- 11,492 player appearance rows
- every match has at least 20 source appearance rows
- minimum appearances per match: 24
- maximum appearances per match: 34

Exact fixture mapping:
- 380/380 Transfermarkt matches mapped to canonical matches by exact date + teams + score
- no fuzzy fixture mapping was needed

Player identity/staging:
- 11,492 rows staged in `public.source_player_match_stats`
- 9,063 rows initially linked through pre-existing verified Transfermarkt provider-ID mappings
- 2,429 rows initially unresolved
- a 2025/26 canonical match-history fingerprint pass resolved 114 additional source players without using names
- accepted mappings required at least 3 common games, >=95% two-sided overlap, goals/minutes agreement, and one-to-one composite uniqueness
- all 114 accepted mappings actually had 100% overlap
- common-game count: min 3, average 20.7, max 38
- worst accepted average minute difference: 0.67 minutes

Final 2025/26 Transfermarkt staging state:
- 11,418 / 11,492 rows linked to canonical player codes
- 74 rows remain unresolved
- those 74 rows represent 30 source players and remain staged only rather than being guessed by name
- rich `player_match_stats` for 2025/26 were not overwritten; Transfermarkt remains a source/crosswalk layer for that season

Identity safety checks after the refresh:
- no Transfermarkt/Understat provider-prefixed canonical IDs were introduced into `players`
- every mapped 2025/26 staged Transfermarkt code exists in canonical `players`
- only the project's previously explicit manual-name-verified exceptions remain; this refresh introduced no automated name-based player mapping

## Betting data

### Historical bookmaker odds

`public.historical_market_odds` contains full Football-Data Premier League odds for 2019/20 through 2025/26, plus completed 2026/27 matches already imported.

Closing no-vig 1X2 market Brier/log-loss benchmarks:
- 2019/20: 0.60561 / 1.00871
- 2020/21: 0.61851 / 1.02967
- 2021/22: 0.53384 / 0.90077
- 2022/23: 0.57395 / 0.95959
- 2023/24: 0.52969 / 0.89735
- 2024/25: 0.57519 / 0.96725
- 2025/26: 0.60774 / 1.01177

### xG coverage correction

2024/25 has complete xG via `fpl_player_match_stats`. `betting_team_match_v2` falls back to FPL team-level xG where canonical player-match xG is absent. Any earlier statement that 2024/25 lacked xG is superseded.

## Model v3 — validated baseline

Detailed spec: `BETTING_MODEL_V3.md`.
Historical results: `BETTING_MODEL_V3_7_SEASON_RESULTS.md`.

Predictions are cached in `public.betting_model_match_predictions` with `model_version='v3'` for 2,660 matches across 2019/20–2025/26.

v3 top-pick accuracy over all seven seasons: 53.4% versus bookmaker favourite 55.0%.

v3 remains the validated baseline and has not been replaced.

## Model v5 — PPG/xG agreement experiment

Detailed checkpoint: `BETTING_MODEL_V5_PPG_XG_AGREEMENT_EXPERIMENT.md`.

Main lesson: short venue5 was too volatile; stronger venue context helped, but outsider/away reversals remained unstable. Mark prefers a shorter venue window than 15 if possible.

## Venue8 metrics — permanent database layer

Supabase:
- `public.team_form_window8_cache`
- `public.team_form_window_cache_with_v8`

Stored metrics:
- `vn8`
- `vppg8`
- `vxgf8`
- `vxga8`

GitHub SQL: `scripts/add_team_form_window8_cache.sql`.

Venue xG8 has been one of the strongest useful additions in subsequent model fitting.

## Model v6 — composite probability experiment

Detailed checkpoint: `BETTING_MODEL_V6_COMPOSITE_EXPERIMENT.md`.

Supabase component cache:
- `public.betting_model_v6_components`

It stores independent H/D/A probabilities from PPG5/10/15/30, xG5/10/15/30, venue PPG8 and venue xG8. Existing v3 probabilities are used as a separate structural/opponent-adjusted component.

Current every-family research blend before residual adjustment:
- 10% PPG30
- 10% recent PPG = 50/30/20 of PPG15/10/5
- 10% xG30
- 10% recent xG = 50/30/20 of xG15/10/5
- 10% venue PPG8
- 30% venue xG8
- 20% v3 structural/opponent-adjusted probability

Original untouched 2025/26 result:
- Brier 0.63180
- log loss 1.04965
- top-pick accuracy 48.5%

v6 remains experimental only and must not replace v3 yet.

### Finishing / defensive xG residual layer — permanent research component

Added after match-level diagnosis showed that some teams, notably Crystal Palace in 2025/26 examples, persistently converted below xG.

Supabase:
- `public.betting_team_residual_features_v6`
- `public.betting_model_v6_residual_xg_component`

GitHub SQL:
- `scripts/add_betting_residual_features_v6.sql`

Stored leakage-safe metrics:
- Goals minus xG over 10/20/30 prior matches
- Goals Against minus xGA over 10/20/30 prior matches

Testing showed the 30-match residual is more stable than 10/20-match residuals. The chosen research rule trusts at most 25% of the 30-match residual, shrunk for shorter histories as `0.25 * min(1, n30/30)`.

Development xG30 test on 1,771 full-history matches:
- no residual: Brier 0.61555 / log loss 1.02616
- 25% residual: 0.61502 / 1.02542

2025/26 full-30-history subset (295 matches):
- no residual: 0.63152 / 1.04815
- 25% residual: 0.62999 / 1.04594

On the full 334-match 2025/26 v6 sample, residual-aware xG30 improves raw xG30 Brier from 0.63834 to 0.63648.

Replacing the 10% long-xG family in the every-family composite with residual-aware xG gives:
- Brier 0.63174
- log loss 1.04954
- top-pick accuracy 48.8%

This is a small but clean improvement and is retained. It does not solve the wider 2025/26 instability alone.

## Manual weekend venue review — updated 2026-09-01

A separate manual early-season review workflow exists at `/betting/weekend`. It intentionally bypasses the normal 15-match-season betting gate because it is for human real-time checking, not automatic production recommendations.

Current rule under test:
- **Hard eligibility floor: both teams must have at least 4 relevant current-spell venue matches before the weekend model is allowed to predict.** If either `home_n8 < 4` or `away_n8 < 4`, the model returns `LIMITED_HISTORY` and suppresses expected goals, H/D/A probabilities, fair odds and the model pick.
- Samples of 4–7 matches are eligible partial Venue8 samples. A sample of 8 is the full Venue8 window.
- Keep venue PPG8 and venue xG8 separate.
- Before actual goals are allowed to influence xG, cap only extreme positive goal-vs-xG residuals at individual-match level: `capped actual goals = min(actual goals, xG + 1.0)` for both goals scored and goals conceded.
- Underperformance versus xG is left unchanged. The capped actual value can therefore never be higher than the real actual value.
- Average those capped actual GF/GA values across the available venue sample, up to eight matches.
- Blend the capped actual average 50/50 with raw venue xG: `adj xGF8 = (xGF8 + capped actual GF8)/2`, and similarly for xGA.
- The +1.0 overperformance cap is the current chosen threshold. A tighter +0.8 threshold was discussed but has not been adopted.
- Once both teams meet the 4-match minimum, venue PPG8 decides the result unless the absolute home-v-away venue PPG gap is <= 0.30.
- Only when the PPG gap is close does adjusted venue xG8 act as the tie-break/result signal.
- Promoted/returning sides use only their current PL spell. Stale prior-spell venue data is not used to bypass the 4-match minimum.

Reason for the minimum-four rule: Ipswich v Liverpool on 4 Sep 2026 exposed the failure mode. Ipswich had only one relevant PL home match, a 2–1 win over Sunderland, which made `home_vppg8 = 3.0` and caused the raw probability calculation to imply an unrealistic Ipswich advantage. The minimum-four gate was therefore made hard rather than merely descriptive. Supabase `public.betting_manual_weekend_analysis` now returns null expected-goal/probability outputs and `LIMITED_HISTORY` when either team has fewer than four venue matches. Frontend `app/betting/weekend/page.tsx` applies the same rule. GitHub SQL: `scripts/set_weekend_minimum_venue_history.sql`.

A separate **overall PPG30 diagnostic** is displayed for each team. It is calculated from up to the last 30 completed Premier League matches in the team’s current PL spell, with the sample count shown explicitly. It is display-only: it does not alter the venue PPG decision, adjusted xG, expected goals, probabilities, fair odds or manual pick. This was added after Liverpool v Nottingham Forest showed an ~18-point model/market home-win disagreement. For that fixture the diagnostic is Liverpool 1.533 PPG30 versus Forest 1.300 PPG30. GitHub SQL: `scripts/add_weekend_ppg30_diagnostic.sql`.

A separate **venue18 diagnostic** is also displayed for PPG, xGF and xGA. It uses up to the last 18 completed Premier League matches at the relevant venue status (home for the home team, away for the away team), restricted to the team’s current PL spell. It is comparison-only and does not alter any calculation or pick. When a full 18-match venue sample exists, the page shows an arrow beside the venue8 PPG/xGF/xGA value: `↑` if the last eight are better than the last 18, `↓` if worse, and `→` when within 0.02. For xGA lower is treated as better. GitHub SQL: `scripts/add_weekend_venue18_diagnostic.sql`.

Liverpool v Nottingham Forest is the immediate diagnostic example:
- Liverpool home PPG8 1.875 vs PPG18 1.833 — broadly similar/slightly hotter recently.
- Liverpool home xGF8 1.666 vs xGF18 1.709 — slightly weaker attacking xG recently.
- Liverpool home xGA8 1.445 vs xGA18 1.152 — materially worse defensive xG recently.
- Forest away PPG8 1.625 vs PPG18 1.278 — materially hotter recent away results.
- Forest away xGF8 1.282 vs xGF18 0.997 — materially hotter recent away chance creation.
- Forest away xGA8 2.035 vs PPG18 1.711 — materially worse recent away defensive xG.
This supports the working diagnosis that Forest’s venue8 attack/results are unusually strong relative to their broader away baseline, while their recent away defensive xG is not strong.

Reason for the cap: a freak flattering scoreline should not dominate an eight-match sample. Nottingham Forest's last eight PL away matches were the immediate example: raw actual GF8 was 2.375 and raw xGF8 1.282; after capping only match-level overperformance beyond xG + 1.0, capped actual GF8 is 1.899 and adjusted xGF8 becomes about 1.590 instead of about 1.829 under the old uncapped 50/50 rule. Bournemouth exposed why the earlier symmetric ±1.0 implementation was wrong for this purpose: it increased actual GF when the team underperformed xG. Under the corrected one-sided rule Bournemouth's actual GF8 and capped actual GF8 are both 1.625.

Historical top-pick test quoted before the new cap was introduced, on 2,342 matches with complete venue8 histories:
- venue PPG8 only: 49.7% overall; 46.4% in 2025/26
- raw venue xG8 only: 51.5%; 46.4%
- old uncapped adjusted venue xG8 only: 52.4%; 47.0%
- venue PPG8 with old uncapped adjusted-xG tie-break at gap <= 0.30: 51.3%; 49.1%

Those adjusted-xG historical figures must now be treated as legacy until the one-sided +1.0 capped version is back-tested on the same sample.

Supabase tables/views:
- `public.betting_manual_fixtures`
- `public.betting_manual_weekend_analysis` — current capped-actual analysis with hard minimum-four venue-history gate
- `public.betting_manual_weekend_analysis_uncapped` — preserved legacy view for QA/comparison
- `public.betting_manual_weekend_capped_actuals` — current one-sided +1.0 rule
- `public.betting_manual_weekend_snapshot`

The current snapshot stores `goal_xg_residual_cap`, `home_vgf8_capped`, `home_vga8_capped`, `away_vgf8_capped`, `away_vga8_capped`, diagnostic `home_n30`, `away_n30`, `home_ppg30`, `away_ppg30`, and venue18 diagnostic `home_vn18`, `away_vn18`, `home_vppg18`, `away_vppg18`, `home_vxgf18`, `home_vxga18`, `away_vxgf18`, `away_vxga18`. GitHub migrations: `scripts/update_weekend_adjusted_xg_cap.sql` (superseded symmetric rule), `scripts/make_weekend_goal_xg_cap_one_sided.sql` (current cap rule), `scripts/add_weekend_ppg30_diagnostic.sql` (display-only PPG30 diagnostic), `scripts/add_weekend_venue18_diagnostic.sql` (display-only venue18 comparison), and `scripts/set_weekend_minimum_venue_history.sql` (hard minimum-four prediction gate).

The 2026/27 Matchweek-2 weekend snapshot includes all ten fixtures from 28–31 Aug 2026. 1X2 prices were captured from the Oddschecker UK coupon on 28 Aug 2026 and are displayed with no-vig implied probabilities. The page shows venue PPG8, venue18 comparison/sample and trend arrows, overall PPG30 diagnostic/sample, raw actual GF/GA, capped actual GF/GA, raw xGF/xGA, adjusted xGF/xGA, adjusted match expected goals and probabilities where eligible, market odds/probabilities, and the manual rule decision.

## 2025/26 diagnosis

All internal metric families deteriorate in 2025/26, not just one weight. The composite also underpredicts draws:
- actual H/D/A on eligible sample: 41.0 / 28.1 / 30.8%
- composite average: 42.3 / 24.2 / 33.5%

Do not tune directly to 2025/26 just to remove this miss.

Additional rejected structural tests:
- Elo-style team rating
- rolling league H/D/A regime correction
- global draw multiplier

Reusable research function exists in Supabase: `public.betting_elo_eval(...)`.

## Current modelling direction

1. Keep v3 as baseline.
2. Keep v6 as the transparent all-metrics probability research model.
3. Use residual-aware xG30 rather than raw xG30 in the 10% long-xG family for current v6 research.
4. In the manual weekend diagnostic, enforce a hard minimum of 4 relevant venue matches for BOTH teams before any expected goals, H/D/A probabilities, fair odds or pick are produced. Treat 4–7 as partial Venue8 and 8 as the full window.
5. In the manual weekend diagnostic, cap only actual-goal overperformance beyond xG + 1.0 before the 50/50 actual/xG blend; never increase actual goals because of xG underperformance. Keep venue PPG and adjusted venue xG separate.
6. Show overall current-spell PPG30 and current-spell venue18 PPG/xGF/xGA as diagnostics only; do not feed them into the weekend probabilities or picks until separately tested.
7. Use the venue18 comparison to identify when venue8 is a hot/cold spell rather than silently anchoring the model to the longer window.
8. Back-test the one-sided +1.0 capped rule against the old uncapped adjusted-xG rule before treating it as historically validated.
9. Do not choose weights from ROI; fit probabilities using Brier/log loss, then evaluate betting edge separately.
10. Investigate match-level disagreements with the bookmaker to identify genuinely missing football context rather than fitting shock results.
11. Do not hard-code bookmaker agreement into the predictive model merely to make historical ROI look better.

## Betting research rules

- No look-ahead leakage.
- Every historical prediction uses only information available before kickoff.
- Keep source/model versions explicit.
- Compare model probabilities against no-vig closing market probabilities when evaluating betting edge.
- Do not tune a threshold and validate it on the same sample.
- Include all qualifying bets from declared rules; no cherry-picking.
- Model outputs are research probabilities, not guaranteed winners.

## Security / temporary helpers

Temporary read/audit/staging Edge Functions used during the 2026-09-01 refresh were locked after use with JWT verification and inert handlers. Reusable production data remains in normal Supabase tables; no public unauthenticated Transfermarkt or Understat staging helper was intentionally left open.

## Current verified headline state — 2026-09-01

- FPL 2026/27: 1,236 rows / 20 fixtures / GW2 complete
- canonical core player-match stats: 759 rows / 19 matches; Villa–Arsenal rich-player source pending
- Understat 2026/27 staged: 622 rows / 20 matches
- Understat current-season canonical enrichment: 313 rows / 0 advanced-metric mismatches
- `betting_team_match_v2`: 40 rows / 20 matches / all with xG
- Transfermarkt 2026/27: unavailable from the project's published source as of 2026-09-01
- Transfermarkt 2025/26: 11,492 staged rows / 380 matches; 11,418 linked rows; 74 unresolved rows across 30 source players
- v3 remains the validated betting baseline
- v6 remains experimental
- weekend model now has a hard minimum-four current-spell venue-history gate before any prediction/probabilities/fair odds are produced
- immediate modelling task: back-test the one-sided `xG + 1.0` capped weekend adjusted-xG rule on the historical venue8 sample and compare it against the old uncapped rule

## Continuation instruction

When Mark asks to continue this project, read this file, then inspect current GitHub/Supabase/Vercel state before acting. Do not ask Mark to repeat project history that can be recovered from connected systems.