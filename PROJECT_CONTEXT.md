# PL Results Project — Persistent Project Context

_Last updated: 2026-08-28_

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
4. Do not choose weights from ROI; fit probabilities using Brier/log loss, then evaluate betting edge separately.
5. Treat 2025/26 as an untouched diagnostic/holdout when testing new structures.
6. Investigate match-level disagreements with the bookmaker to identify genuinely missing football context rather than fitting shock results.
7. Do not hard-code bookmaker agreement into the predictive model merely to make historical ROI look better.

## Betting research rules

- No look-ahead leakage.
- Every historical prediction uses only information available before kickoff.
- Keep source/model versions explicit.
- Compare model probabilities against no-vig closing market probabilities when evaluating betting edge.
- Do not tune a threshold and validate it on the same sample.
- Include all qualifying bets from declared rules; no cherry-picking.
- Model outputs are research probabilities, not guaranteed winners.

## Continuation instruction

When Mark asks to continue this project, read this file, then inspect current GitHub/Supabase/Vercel state before acting. Do not ask Mark to repeat project history that can be recovered from connected systems.
