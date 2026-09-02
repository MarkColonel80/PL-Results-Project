# PL Results Project — Persistent Project Context

_Last updated: 2026-09-02_

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
- Vercel project: `pl-results-project`, production `https://pl-results-project.vercel.app`

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

## Current verified headline state — 2026-09-02

- FPL 2026/27: 1,236 rows / 20 fixtures / GW2 complete
- canonical core player-match stats: 759 rows / 19 matches; Villa–Arsenal rich-player source pending
- Understat 2026/27 staged: 622 rows / 20 matches
- Understat current-season canonical enrichment: 313 rows / 0 advanced-metric mismatches
- `betting_team_match_v2`: 40 rows / 20 matches / all with xG
- Transfermarkt 2026/27: unavailable from the project's published source as of 2026-09-01
- Transfermarkt 2025/26: 11,492 staged rows / 380 matches; 11,418 linked; 74 unresolved across 30 source players
- v3 remains validated production baseline
- v6 remains experimental
- leading comparison candidate is 24-match capped structure + 50%-shrunk Venue8, no PPG10
- weekend comparison refresh includes a mandatory team-feature materialized-view refresh
- Supabase Security Advisor has 0 ERROR/critical findings after the 2026-09-02 hardening

## Continuation instruction

When Mark asks to continue this project, read this file, then inspect current GitHub/Supabase/Vercel state before acting. Do not ask Mark to repeat project history that can be recovered from connected systems. Preserve both the identity-safety rules and the 2026-09-02 least-privilege Supabase security rules.
