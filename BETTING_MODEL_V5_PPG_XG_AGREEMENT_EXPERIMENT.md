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

Adjusted xGF/xGA create independent attack/defence ratios against the rolling league scoring baseline. The home and away lambdas use a multiplicative attack × opposition-defence structure with damping `d`.

Tested d values: 0.50, 0.60, 0.70, 0.80, 0.90, 1.00.

Best development setting by Brier: **d = 0.80** (0.90 tied on Brier but had slightly worse log loss).

At d=0.80 over 1,143 development matches:
- Brier: **0.58083**
- log loss: **0.97796**

Both models use independent Poisson score grids to derive Home/Draw/Away probabilities.

## Corrected cached evaluation

The v5 inputs and independent PPG/xG probabilities are now persisted in Supabase so repeated threshold analysis does not rebuild rolling features and Poisson grids.

An initial cache attempt incorrectly divided `league_home_goals` and `league_away_goals` by `league_matches` even though those fields were already per-match averages. That output was discarded. The cache was corrected and all probabilities regenerated before the results below.

The corrected historical input layer also calculates the 5/10/15 PPG and xG windows **within each season**, rather than carrying prior-season matches into the 15-game test. Odds are mapped by exact season + canonical home/away team pairing.

## Minimum edge from BOTH independent models

For an agreed selection, `minimum edge` means the smaller of:

- PPG model probability minus closing no-vig market probability; and
- xG model probability minus closing no-vig market probability.

So a 2pp threshold means **both** independent models must rate the same selection at least 2 percentage points above the bookmaker market.

Across 2019/20–2025/26:

| Minimum edge required from both | Bets | Hit rate | ROI @ avg close |
|---|---:|---:|---:|
| >= 0pp | 342 | 44.2% | **+5.7%** |
| >= 1pp | 304 | 43.4% | **+6.4%** |
| >= 2pp | 275 | 42.5% | **+6.4%** |
| >= 3pp | 250 | 41.2% | **+5.3%** |
| >= 4pp | 223 | 40.4% | **+4.9%** |
| >= 5pp | 196 | 38.8% | **+3.1%** |
| >= 7.5pp | 132 | 32.6% | **-7.2%** |
| >= 10pp | 91 | 27.5% | **-13.9%** |

The 1–2pp range gives the best aggregate ROI, but the relationship is not monotonic: large dual-model edges become materially worse, consistent with earlier v3 findings that very large disagreement with the market is often a warning rather than stronger confidence.

## Season stability

Season-level ROI at selected thresholds:

| Season | >=0pp | >=1pp | >=2pp | >=3pp | >=5pp |
|---|---:|---:|---:|---:|---:|
| 2019/20 | -2.2% | -2.3% | -7.3% | -5.1% | -18.4% |
| 2020/21 | +14.4% | +14.6% | +19.6% | +12.5% | +9.3% |
| 2021/22 | +35.9% | +33.4% | +32.9% | +34.6% | +36.8% |
| 2022/23 | +16.0% | +13.8% | +12.1% | +17.0% | +32.7% |
| 2023/24 | **-46.1%** | **-61.2%** | **-65.4%** | **-72.4%** | **-73.8%** |
| 2024/25 | +21.1% | +24.6% | +25.1% | +24.2% | +23.3% |
| 2025/26 | -10.6% | -4.8% | +0.4% | -0.4% | -17.2% |

The main instability is 2023/24, which is catastrophically negative at every threshold and gets worse as the required dual-model edge rises. This needs diagnosis before any threshold is promoted as a betting rule.

## Current interpretation

- Separating PPG and xG remains useful: xG is the stronger probability model while PPG provides independent confirmation.
- Requiring both models to choose the same side and independently beat the market produces a positive seven-season aggregate in the corrected cache.
- The best aggregate range is around a modest **1–2 percentage-point minimum edge from both models**, not large edges.
- Do **not** choose 1% or 2% as a production betting threshold yet. Results are too season-dependent, especially because 2023/24 is extremely poor.
- Very large dual-model disagreement is again harmful: 7.5%+ and 10%+ minimum edges lose materially.
- The next priority is to explain 2023/24 by outcome type, odds range, teams and whether PPG/xG agreement systematically backed long-priced underdogs or missed a league/regime change.
