# v3 + Venue8 — 15-match vs 30-match structural history

_Date: 2026-09-01_

## Question

Test Mark's proposal to shorten the overall team-strength history in the new v3 + team-specific Venue8 architecture from 30 matches to 15, while keeping all other team-specific lookbacks at 15 matches or fewer.

This is research only. Production v3 and `/betting/weekend` are unchanged.

## Architecture held constant

Both comparison models use the same construction except for the overall attack/defence history length.

Common elements:
- historical evaluation begins only once both clubs have reached their 15th league match of that season;
- current-PL-spell history only;
- Venue8 home/away split, minimum 4 relevant venue matches;
- venue xG plus one-sided capped actual goals, exactly as in the current weekend method;
- match-level cap: `min(actual goals, xG + 1.0)` for GF and GA;
- underperformance is never lifted toward xG;
- adjusted venue attack/defence = 50% raw xG + 50% capped actual goals;
- team-specific home baseline = `sqrt(home adjusted venue attack * away adjusted venue defence)`;
- team-specific away baseline = `sqrt(away adjusted venue attack * home adjusted venue defence)`;
- overall attack/defence blend = 65% xG + 35% actual goals;
- 4 pseudo-match shrinkage toward recent league scoring level;
- PPG10 adjustment retained, so no team result signal reaches beyond 10 matches;
- attack x opponent-defence damping exponent 0.75;
- independent Poisson H/D/A probabilities.

To honour the strict 'nothing else beyond 15' version, the league scoring normaliser itself is based on the previous 15 completed PL fixtures before kickoff rather than the longer rolling league baseline.

The only difference between the two comparison models is overall team attack/defence history:
- candidate A: up to previous 15 current-spell PL matches;
- candidate B: up to previous 30 current-spell PL matches.

## Aggregate results

### Development — 2019/20 through 2024/25

Same 1,433-match GW15+ / Venue4+ sample:

| Structural history | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 15 matches | 53.80% | 0.58623 | 0.99050 |
| 30 matches | **54.29%** | **0.58250** | **0.98416** |

Cost of shortening 30 -> 15:
- winner accuracy: -0.49 percentage points;
- Brier: +0.00373 (worse);
- log loss: +0.00634 (worse).

### 2025/26 untouched holdout

240 matches:

| Structural history | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 15 matches | 46.25% | 0.65828 | 1.08094 |
| 30 matches | **47.08%** | **0.65548** | **1.07583** |

Cost of shortening 30 -> 15:
- winner accuracy: -0.83 percentage points;
- Brier: +0.00280;
- log loss: +0.00511.

The 2025/26 shared draw/venue instability remains present under both windows. Shortening to 15 does not solve it.

## Season-by-season winner accuracy / Brier

| Season | 15-match | 30-match |
|---|---|---|
| 2019/20 | 53.8% / 0.5970 | **54.6% / 0.5916** |
| 2020/21 | 50.0% / 0.6110 | **51.7% / 0.6023** |
| 2021/22 | **57.3%** / 0.5571 | 56.1% / **0.5549** |
| 2022/23 | 52.1% / 0.6046 | **52.5% / 0.6021** |
| 2023/24 | 56.7% / 0.5693 | **58.3% / 0.5626** |
| 2024/25 | **52.9% / 0.5788** | 52.5% / 0.5818 |
| 2025/26 | 46.3% / 0.6583 | **47.1% / 0.6555** |

15-match history therefore is not uniformly worse. It wins top-pick accuracy in 2021/22 and 2024/25, and beats 30 on Brier in 2024/25. But 30 is better on aggregate and generally better calibrated.

## Interpretation

The penalty for using 15 rather than 30 is smaller than expected. A 15-match structural window is more responsive to current team strength, but gives up some stability.

The aggregate six-season calibration deterioration is real but modest: Brier moves from 0.58250 to 0.58623 and accuracy from 54.29% to 53.80%.

Therefore 15 should not be rejected purely on historical performance. If the modelling objective values current-state responsiveness — transfers, manager changes, tactical shifts, promoted-team adaptation — a roughly half-point accuracy cost may be acceptable. It should be compared next with intermediate windows (for example 18, 20, 24) using development data only, while keeping 2025/26 untouched if an additional holdout decision is needed.

## Current conclusion

- 30 remains statistically better overall.
- 15 is only modestly worse, not dramatically worse.
- 15 does not fix the 2025/26 anomaly.
- Do not change production v3 yet.
- The useful next question is whether an intermediate structural window preserves most of the 30-match calibration while reacting faster than 30.
