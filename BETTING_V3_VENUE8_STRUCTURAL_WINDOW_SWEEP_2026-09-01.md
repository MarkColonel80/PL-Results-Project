# v3 + Venue8 — capped structural-window sweep

_Date: 2026-09-01_

## Goal

Continue the v3 + team-specific Venue8 research after confirming that a one-sided match-level `xG + 1.0` cap improves the 15-match structural model and that a separate 15-match Goals-minus-xG residual correction does not.

This experiment asks how much structural history should be used once the same cap is applied consistently to the overall attack/defence layer.

Production v3 and `/betting/weekend` remain unchanged.

## Architecture held constant

All candidates use the same model except for the overall structural attack/defence window.

Common rules:

- historical evaluation only once both clubs have reached at least their 15th league match of that season;
- current Premier League spell only;
- team-specific Venue8: prior home matches for the home side and prior away matches for the away side;
- Venue8 minimum four relevant venue matches;
- venue actual GF/GA capped match-by-match at `min(actual, xG + 1.0)`; underperformance is not lifted;
- adjusted venue attack/defence = 50% raw venue xG + 50% capped actual goals;
- home venue baseline = `sqrt(home adjusted venue attack * away adjusted venue defence)`;
- away venue baseline = `sqrt(away adjusted venue attack * home adjusted venue defence)`;
- structural actual GF/GA are also capped match-by-match at `min(actual, xG + 1.0)`;
- structural attack/defence = 65% xG + 35% capped actual goals;
- four pseudo-match shrinkage toward the league scoring midpoint;
- PPG10 adjustment retained;
- opponent attack/defence interaction damped with exponent 0.75;
- independent Poisson H/D/A probabilities using the existing `public.poisson_1x2_probs` 0–10 score grid.

No separate Goals-minus-xG residual correction is applied. The preceding experiment showed that adding a 10–25% one-sided residual correction on only 15 matches worsened Brier/log loss relative to the cap-only construction.

## Sample

Exact same leakage-safe sample used in the prior GW15+ research:

- 2019/20–2024/25 development: 1,433 matches
- 2025/26 untouched stress-test/holdout: 240 matches

## Aggregate results

### Development — 2019/20 through 2024/25

| Structural window | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 15 | 53.66% | 0.58541 | 0.98857 |
| 18 | 54.15% | 0.58360 | 0.98590 |
| 20 | 53.66% | 0.58253 | 0.98422 |
| 24 | 54.15% | **0.58137** | 0.98254 |
| 30 | **54.43%** | **0.58123** | **0.98195** |

The pure development winner remains 30 matches, but 24 is extremely close:

- Brier gap 24 vs 30: only 0.00014;
- log-loss gap: 0.00059;
- accuracy gap: 0.28 percentage points.

Relative to 15, 24 improves Brier by 0.00404 and accuracy by 0.49 percentage points while remaining six matches more responsive than 30.

### 2025/26 stress-test

| Structural window | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 15 | 45.83% | 0.65693 | 1.07832 |
| 18 | 45.00% | 0.65658 | 1.07771 |
| 20 | 46.67% | 0.65716 | 1.07830 |
| 24 | 46.25% | **0.65352** | **1.07213** |
| 30 | **46.67%** | 0.65375 | 1.07297 |

2025/26 is not used to select the structural window, but it does not contradict the 24-match candidate: 24 is marginally better than 30 on Brier and log loss while 30 is slightly better on top-pick accuracy.

## Season-by-season comparison — 18/20/24/30

| Season | 18 | 20 | 24 | 30 |
|---|---|---|---|---|
| 2019/20 | 54.2% / .5919 | 54.2% / .5913 | 55.0% / .5885 | 55.0% / .5868 |
| 2020/21 | 50.0% / .6079 | 50.0% / .6053 | 50.4% / .6035 | 50.8% / .6031 |
| 2021/22 | 56.5% / .5561 | 54.8% / .5548 | 56.1% / .5563 | 55.6% / .5543 |
| 2022/23 | 53.4% / .6014 | 53.8% / .5983 | 53.0% / .5960 | 53.4% / .5994 |
| 2023/24 | 57.1% / .5688 | 55.8% / .5700 | 56.7% / .5678 | 58.3% / .5658 |
| 2024/25 | 53.8% / .5759 | 53.3% / .5758 | 53.8% / .5765 | 53.3% / .5783 |
| 2025/26 stress-test | 45.0% / .6566 | 46.7% / .6572 | 46.3% / .6535 | 46.7% / .6538 |

Each cell is accuracy / Brier.

30 has the better development Brier in four of the six seasons; 24 is better in two. The aggregate difference is nevertheless tiny, so 24 is not being driven by a single anomalous season.

## Interpretation

- 15 remains viable if maximum responsiveness is the priority, but it gives up measurable calibration.
- 18 recovers winner accuracy but not enough probability calibration.
- 20 improves calibration further but does not improve top-pick accuracy.
- 24 captures almost all of the statistical benefit of 30 while discarding six older matches.
- 30 remains the strict development-data benchmark.
- 24 is therefore the leading responsive structural-window candidate.

The choice between 24 and 30 is now a modelling-objective tradeoff rather than a large historical-performance difference. If current-team responsiveness has real value, 24 has a strong justification because its development calibration is virtually tied with 30 and its 2025/26 stress-test calibration is marginally better.

## Supabase research objects

- `public.betting_v3_venue8_15_residual_inputs`
- `public.betting_v3_venue8_structural_window_inputs`
- `public.betting_v3_venue8_window18_scores`
- `public.betting_v3_venue8_window20_scores`
- `public.betting_v3_venue8_window24_scores`
- `public.betting_v3_venue8_window30_scores`

These are research caches only and do not alter production predictions.

## Current working direction

1. Keep the one-sided `xG + 1.0` cap in both structural actual-goal and Venue8 actual-goal inputs.
2. Do not add a separate 15-match Goals-minus-xG residual adjustment.
3. Treat 30 as the statistical benchmark and 24 as the leading responsive structural candidate.
4. Continue development from the 24-match candidate, while retaining direct 30-match comparisons for each material model change.
5. Do not tune to the 2025/26 stress-test.
