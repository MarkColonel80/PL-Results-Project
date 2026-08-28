# Betting Model v6 — Composite probability experiment

_Date: 2026-08-28_

## Goal

Build a transparent 1X2 model that can use the full family of currently available leakage-safe team metrics and then determine sensible relative weights from historical Premier League results.

This is an **experimental model**, not a replacement for v3 yet.

## Available component probabilities

Supabase materialized view: `public.betting_model_v6_components`.

For each eligible historical fixture it stores independent Home/Draw/Away probability triples derived from:

- PPG5
- PPG10
- PPG15
- PPG30
- venue PPG8
- xG5 attack/defence
- xG10 attack/defence
- xG15 attack/defence
- xG30 attack/defence
- venue xG8 attack/defence

The venue8 source is the permanent `public.team_form_window8_cache` / `public.team_form_window_cache_with_v8` layer.

The opponent-adjusted structural component is the existing v3 probability output in `public.betting_model_match_predictions` (`model_version='v3'`). It captures attack/defence strength against opposition rather than another raw rolling average.

All component probabilities are generated without future-match information.

## Initial unrestricted weighting results

Using 2019/20–2023/24 first, raw fixed-window optimisation strongly preferred longer histories:

- PPG family: effectively PPG30 only; PPG15 provided only a tiny marginal alternative and PPG5/10 generally added noise.
- xG family: approximately 90% xG30 + 10% xG10.

A first family-level optimum was approximately:

- 40% PPG30
- 10% venue PPG8
- 40% venue xG8
- 9% xG30
- 1% xG10

Development score: about Brier 0.5811 / log loss 0.9789.

However, this did not generalise to 2025/26, so it was not frozen.

## Structural/opponent-adjusted component

Adding v3 as an independent structural component and optimising across 2019/20–2024/25 with a season-stability penalty produced a robust best family blend around:

- 30% PPG30
- 10% overall xG (90% xG30 + 10% xG10)
- 40% venue xG8
- 20% v3 structural/opponent-adjusted probability
- 0% fixed venue PPG8

Six-season average Brier: about 0.5817.

Untouched 2025/26 holdout:

- Brier: **0.63298**
- log loss: **1.05118**
- top-pick accuracy: **48.2%**

Therefore this is not production-ready.

## Every-metric-family constrained version

To test Mark's desired structure literally, the model was regrouped into seven interpretable families and every family was required to contribute at least 10% in a coarse grid search:

1. Long PPG = PPG30
2. Recent PPG = 50% PPG15 + 30% PPG10 + 20% PPG5
3. Long xG = xG30
4. Recent xG = 50% xG15 + 30% xG10 + 20% xG5
5. Venue PPG8
6. Venue xG8
7. v3 structural/opponent-adjusted strength

Best robust 2019/20–2024/25 constrained blend:

- **10% long PPG**
- **10% recent PPG**
- **10% long xG**
- **10% recent xG**
- **10% venue PPG8**
- **30% venue xG8**
- **20% structural/opponent-adjusted v3**

Development metrics:

- average Brier: **0.58268**
- average log loss: **0.98094**
- season Brier SD: **0.00788**
- worst development-season Brier: **0.59512**

Untouched 2025/26 holdout:

- Brier: **0.63180**
- log loss: **1.04965**
- top-pick accuracy: **48.5%**

This is slightly better than the unrestricted robust blend on the holdout but still materially worse than required for production.

## Finishing / defensive xG residual layer

A new persistent residual layer was added after match-level diagnosis showed Crystal Palace repeatedly converting well below its xG.

Supabase:
- `public.betting_team_residual_features_v6`
- `public.betting_model_v6_residual_xg_component`

GitHub migration:
- `scripts/add_betting_residual_features_v6.sql`

Stored leakage-safe residuals:
- finishing residual = goals minus xG over 10/20/30 prior matches
- defensive residual = goals conceded minus xGA over 10/20/30 prior matches

The residual is not treated as fully persistent skill. Development testing preferred the 30-match residual and only a modest correction. The chosen research rule trusts at most **25%** of the observed 30-match residual; that 25% is further shrunk according to prior-match count (`0.25 * min(1, n30/30)`).

Development test of xG30 alone on 1,771 full-history matches:
- no residual adjustment: Brier **0.61555**, log loss **1.02616**
- 20% residual trust: **0.61503 / 1.02542**
- 25% residual trust: **0.61502 / 1.02542**

Untouched 2025/26 full-30-history subset (295 matches):
- no adjustment: **0.63152 / 1.04815**
- 25% residual trust: **0.62999 / 1.04594**

On the full 334-match v6 2025/26 sample, with short histories automatically shrunk, residual-aware xG30 improves versus raw xG30 from Brier **0.63834** to **0.63648**.

Replacing the 10% long-xG family in the every-family composite with residual-aware xG produces 2025/26:
- Brier **0.63174** (previous 0.63180)
- log loss **1.04954** (previous 1.04965)
- top-pick accuracy **48.8%** (previous 48.5%)

This is a small but clean improvement across both development and holdout and is retained as a useful component. It does not solve the broader 2025/26 instability by itself.

## 2025/26 diagnosis

The failure is not caused by one obviously bad component. Individual metrics also deteriorated materially in 2025/26. On the eligible sample:

- PPG30 Brier: 0.63000
- PPG15: 0.63575
- xG30: 0.63834
- xG15: 0.64218
- venue xG8: 0.65238
- venue PPG8: 0.66033
- PPG5: 0.67984

The composite also systematically underpredicted draws in 2025/26:

- actual H/D/A: 41.0% / **28.1%** / 30.8%
- composite average H/D/A: 42.3% / **24.2%** / 33.5%

But this should not be fixed by tuning specifically to 2025/26.

## Additional tests rejected

### Elo-style opponent-adjusted rating

A reusable Supabase evaluator `public.betting_elo_eval(...)` was added for research. A representative K=20 / home-advantage=65 / beta=0.75 setting scored:

- 2019/20–2024/25: Brier 0.59466 / log loss 0.99674 / accuracy 52.3%
- 2025/26: Brier 0.62895 / log loss 1.04481 / accuracy 45.8%

This did not solve the holdout instability and is not currently part of v6.

### Rolling league-regime H/D/A correction

A leakage-safe recent-100 versus prior-300 league outcome-rate correction was tested. Development data preferred **gamma = 0**, i.e. no correction. Rejected.

### Global draw multiplier

A global multiplier on draw probability was tuned on 2019/20–2024/25. Development Brier marginally preferred 0.95, but this made the 2025/26 holdout worse. Rejected.

## Interpretation

- Longer-term PPG and xG are much more reliable than 5-match windows when used as unconditional fixed weights.
- venue xG8 is consistently one of the strongest useful additions.
- venue PPG8 contains useful football context but is noisier as a fixed probability component.
- persistent finishing/defensive over- or underperformance contains some forecasting information, but it should be heavily shrunk rather than treated as fully repeatable skill.
- opponent-adjusted structural strength helps modestly but does not remove the 2025/26 problem.
- forcing every metric family to contribute is feasible with only a small development penalty, but it does not yet create a robust production model.
- 2025/26 should remain a diagnostic holdout rather than something to tune directly against.

## Current v6 candidate weights

For research/display purposes only, the current every-family v6 candidate is:

| Family | Weight |
|---|---:|
| PPG30 | 10% |
| Recent PPG (15/10/5 = 50/30/20) | 10% |
| Residual-aware xG30 | 10% |
| Recent xG (15/10/5 = 50/30/20) | 10% |
| Venue PPG8 | 10% |
| Venue xG8 | 30% |
| Structural/opponent-adjusted v3 | 20% |

Do not promote this to production or use it as a claimed betting edge until the holdout instability is addressed.
