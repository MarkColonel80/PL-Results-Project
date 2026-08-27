# Betting Model v5 — PPG/xG agreement experiment

_Date: 2026-08-27_

## Goal

Test a deliberately separated two-signal approach:

- PPG model describes team strength from results only.
- xG model describes team strength from underlying performance only.
- Do not blend PPG and xG into one strength score.
- Only consider betting when both independent models choose the same 1X2 outcome.
- Ignore the first 15 league matches of each team in each season; a fixture is eligible only when both clubs have already completed 15 league matches that season.

v3 remains untouched and remains the validated baseline.

## Conditional recent-form adjustments

The base window is 15 matches. Shorter windows only nudge the base when materially different.

### PPG

- PPG15 is the base.
- If `abs(PPG10 - PPG15) >= 0.35`, move 20% from PPG15 toward PPG10.
- If `abs(PPG5 - adjusted_PPG) >= 0.50`, move another 15% toward PPG5.
- If same-venue PPG5 differs from the adjusted value by >= 0.40, move 15% toward venue PPG5.

### xG

Attack and defence are adjusted separately.

- xGF15/xGA15 are the bases.
- If 10-match xG differs from the 15-match base by >= 0.30 xG, move 20% toward xG10.
- If 5-match xG differs from the adjusted value by >= 0.40 xG, move 15% toward xG5.
- If same-venue xG differs from the adjusted value by >= 0.35 xG, move 15% toward venue xG5.

## Independent probability models

Parameter selection used 2019/20–2023/24 only, after the per-season 15-match cutoff.

### PPG model

PPG differential adjusts rolling league home/away goal baselines symmetrically:

- home lambda = league home goals × `exp(k × (home adjusted PPG - away adjusted PPG))`
- away lambda = league away goals × `exp(-k × (home adjusted PPG - away adjusted PPG))`

Tested k values: 0.20, 0.25, 0.30, 0.35, 0.40, 0.45.

Best development setting: **k = 0.35**.

At k=0.35 over 1,143 development matches:
- Brier: **0.59368**
- log loss: **0.99573**

### xG model

Adjusted xGF/xGA create independent attack/defence ratios against the rolling league xG baseline. The home and away lambdas use a multiplicative attack × opposition-defence structure with damping `d`.

Tested d values: 0.50, 0.60, 0.70, 0.80, 0.90, 1.00.

Best development setting by Brier: **d = 0.80** (0.90 tied on Brier but had slightly worse log loss).

At d=0.80 over 1,143 development matches:
- Brier: **0.58083**
- log loss: **0.97796**

Both models use independent Poisson score grids to derive Home/Draw/Away probabilities.

## Agreement-only test

Across 2019/20–2025/26 after the per-season 15-match cutoff, simply betting every fixture where the PPG and xG models selected the same 1X2 result produced:

| Season | Bets | Hit rate | ROI @ avg close |
|---|---:|---:|---:|
| 2019/20 | 188 | 53.2% | -7.9% |
| 2020/21 | 174 | 53.4% | -6.6% |
| 2021/22 | 184 | 62.0% | +5.6% |
| 2022/23 | 173 | 56.6% | -1.9% |
| 2023/24 | 180 | 59.4% | -3.0% |
| 2024/25 | 205 | 57.1% | +2.4% |
| 2025/26 | 180 | 50.6% | -9.1% |
| **TOTAL** | **1,284** | **56.1%** | **-2.8%** |

No draw was the top-probability result for both models in this implementation; agreement selections were 856 home and 428 away.

Interpretation: agreement alone improves directional confidence but is not sufficient to create value.

## Agreement + both models independently beat market probability

A stricter betting rule was then tested:

1. PPG and xG models must choose the same 1X2 result.
2. The PPG probability for that result must exceed the Football-Data closing no-vig market probability.
3. The xG probability for that result must independently exceed the same market probability.

Results at average Football-Data closing prices:

| Season | Bets | Hit rate | ROI @ avg close | Avg minimum model edge |
|---|---:|---:|---:|---:|
| 2019/20 | 61 | 37.7% | -15.0% | 8.2pp |
| 2020/21 | 47 | 40.4% | +1.7% | 7.9pp |
| 2021/22 | 43 | 55.8% | +29.3% | 5.8pp |
| 2022/23 | 55 | 45.5% | -0.4% | 7.5pp |
| 2023/24 | 59 | 42.4% | -11.0% | 6.9pp |
| 2024/25 | 71 | 50.7% | +16.7% | 5.8pp |
| 2025/26 | 49 | 38.8% | -8.5% | 5.6pp |
| **TOTAL** | **385** | **44.4%** | **+1.4%** | **6.8pp** |

## Current interpretation

- Separating PPG and xG is useful diagnostically: xG is the stronger probability model, while PPG provides independent confirmation.
- Simple model agreement is not enough; it lost 2.8% at average closing prices.
- Requiring both models independently to see value against the no-vig closing market improves the seven-season aggregate to +1.4%, but results remain unstable by season.
- This is therefore an experiment/filter, not a validated betting system.
- Large apparent edges should still be treated cautiously; the average minimum edge in this filtered set is 6.8pp, yet several seasons remain negative.
- Future work should study disagreement/confirmation strength, price range, favourite/underdog status, and whether requiring a modest minimum edge in both models improves stability without tuning to a single season.
