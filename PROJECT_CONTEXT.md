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

`public.historical_market_odds` now contains full Football-Data Premier League odds for:
- 2019/20
- 2020/21
- 2021/22
- 2022/23
- 2023/24
- 2024/25
- 2025/26

plus completed 2026/27 matches already imported.

Closing no-vig 1X2 market Brier/log-loss benchmarks by full season:
- 2019/20: 0.60561 / 1.00871
- 2020/21: 0.61851 / 1.02967
- 2021/22: 0.53384 / 0.90077
- 2022/23: 0.57395 / 0.95959
- 2023/24: 0.52969 / 0.89735
- 2024/25: 0.57519 / 0.96725
- 2025/26: 0.60774 / 1.01177

### xG coverage correction

2024/25 does have complete xG via `fpl_player_match_stats`. `betting_team_match_v2` was corrected to fall back to FPL team-level xG when canonical player-match xG is absent. Any earlier statement that 2024/25 lacked xG is superseded.

## Model v3 — validated baseline

Detailed spec: `BETTING_MODEL_V3.md`.
Historical results: `BETTING_MODEL_V3_7_SEASON_RESULTS.md`.

Key ideas:
- precomputed 30-match attack/defence strength
- 65% xG / 35% goals where xG coverage is complete, xG weight scales with coverage
- shrinkage to rolling league average
- league home/away scoring baselines
- damped multiplicative attack x opposition-defence structure
- recent PPG10 adjustment
- independent Poisson 1X2 probabilities
- promoted/returning team betting gate

Predictions are cached in `public.betting_model_match_predictions` with `model_version='v3'` for 2,660 matches across 2019/20–2025/26.

v3 top-pick accuracy over all seven seasons: 53.4% versus bookmaker favourite 55.0%.

v3 remains the validated baseline and has not been replaced.

## Model v5 — PPG/xG independent agreement experiment

Detailed checkpoint: `BETTING_MODEL_V5_PPG_XG_AGREEMENT_EXPERIMENT.md`.

Concept:
- PPG and xG are separate probability models
- both use adaptive 15/10/5 and venue adjustments
- only consider a side when both models agree
- historical inputs/probabilities are cached in Supabase

The apparent aggregate betting edge was unstable by season, especially 2023/24. Investigation showed many failures were aggressive outsider/away picks against strong home priors.

Important diagnostic finding:
- short venue5 was too volatile
- longer venue windows helped explain failures
- Mark prefers a shorter venue window than 15 if possible

## Venue8 metrics — permanent database layer

Added 2026-08-28.

Supabase:
- `public.team_form_window8_cache`
- `public.team_form_window_cache_with_v8`

Stored metrics:
- `vn8`
- `vppg8`
- `vxgf8`
- `vxga8`

Existing venue5/10/15 metrics remain available for comparison.

GitHub SQL: `scripts/add_team_form_window8_cache.sql`.

Venue8 testing showed it is a useful compromise: substantially more stable than venue5 without requiring a 15-match venue history. Venue xG8 has been particularly useful in subsequent model fitting.

## Model v6 — composite probability experiment

Detailed checkpoint: `BETTING_MODEL_V6_COMPOSITE_EXPERIMENT.md`.

Supabase component cache:
- `public.betting_model_v6_components`

It stores independent Home/Draw/Away probability triples from:
- PPG5/10/15/30
- xG5/10/15/30 attack/defence
- venue PPG8
- venue xG8 attack/defence

The existing v3 probability is used as a separate structural/opponent-adjusted component.

### Main fitting result

Unrestricted fixed-weight searches strongly prefer longer histories:
- PPG30 dominates shorter PPG windows
- xG30 dominates, with a small xG10 contribution
- venue xG8 is one of the strongest additional components
- venue PPG8 is useful context but noisy as a large unconditional fixed weight

### Current every-family v6 candidate

To honour the aim of using all metric families, the current experimental constrained blend is:
- 10% long PPG = PPG30
- 10% recent PPG = 50% PPG15 + 30% PPG10 + 20% PPG5
- 10% long xG = xG30
- 10% recent xG = 50% xG15 + 30% xG10 + 20% xG5
- 10% venue PPG8
- 30% venue xG8
- 20% v3 structural/opponent-adjusted probability

Development 2019/20–2024/25:
- average Brier 0.58268
- average log loss 0.98094
- season Brier SD 0.00788
- worst development-season Brier 0.59512

Untouched 2025/26 holdout:
- Brier 0.63180
- log loss 1.04965
- top-pick accuracy 48.5%

Therefore v6 is **experimental only** and must not replace v3 yet.

### 2025/26 diagnosis

All internal metric families deteriorate in 2025/26, not just one weight. The composite also underpredicts draws:
- actual H/D/A on eligible sample: 41.0 / 28.1 / 30.8%
- composite average: 42.3 / 24.2 / 33.5%

Do not tune directly to 2025/26 just to remove this miss.

Additional structural tests:
- Elo-style team rating: did not solve holdout instability
- rolling league H/D/A regime correction: development preferred no correction
- global draw multiplier: marginal development change but worsened holdout

Reusable research function currently exists in Supabase: `public.betting_elo_eval(...)`.

## Current modelling direction

1. Keep v3 as baseline.
2. Keep v6 as the transparent all-metrics probability research model.
3. Do not choose weights from ROI; fit probabilities using Brier/log loss, then evaluate betting edge separately.
4. Treat 2025/26 as an untouched diagnostic/holdout when testing new structures.
5. Investigate structural features that may generalise across changing league regimes rather than adding more fixed short-form weight.
6. Do not hard-code bookmaker agreement into the predictive model merely to make historical ROI look better.

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
