# v3 team-specific Venue8 baseline experiment

_Date: 2026-09-01_

## Goal

Test Mark's proposed change to frozen v3: keep v3's validated long-term/opponent-adjusted structure, but replace some or all of the generic rolling Premier League home/away scoring baseline with a team-specific baseline derived from the relevant teams' previous eight venue matches.

This is a research experiment only. The production v3 model and `/betting/weekend` rule are unchanged.

## Evaluation sample

Same apples-to-apples historical window used in the 2026-09-01 weekend-model back-test:

- seasons 2019/20 through 2025/26
- both clubs have reached at least their 15th Premier League match of the season
- both clubs have at least 4 relevant current-spell venue matches before kickoff
- home club uses prior home matches only; away club prior away matches only
- maximum Venue8 history = 8
- no stale prior-PL-spell venue data
- all inputs are pre-kickoff / leakage-safe

Sample:
- 2019/20–2024/25 development: 1,433 matches
- untouched 2025/26 holdout: 240 matches

## Venue8 actual-goal adjustment

Use the current one-sided weekend rule exactly.

For each historical venue match:

`capped actual goals = min(actual goals, xG + 1.0)`

for both goals scored and goals conceded.

Underperformance is not increased.

Over the available venue sample, up to eight matches:

- adjusted venue attack = 50% raw venue xGF + 50% capped actual GF
- adjusted venue defence = 50% raw venue xGA + 50% capped actual GA

This is intended to stop an extreme finishing/defensive scoreline from dominating a short venue sample while still allowing actual goals to contribute information.

## Team-specific venue baseline

The natural candidate uses a geometric home-attack/opponent-defence combination:

`home venue baseline = sqrt(home adjusted venue attack * away adjusted venue defence)`

`away venue baseline = sqrt(away adjusted venue attack * home adjusted venue defence)`

The geometric combination was marginally better calibrated than a simple arithmetic mean in development testing.

## Preserving frozen-v3 structure

Do not reconstruct or retune v3's 30-match/opponent-strength/PPG machinery.

Instead use the cached frozen-v3 expected goals in `public.betting_model_match_predictions` and isolate the multiplier that v3 applied to its old generic league home/away baseline:

`v3 structural home factor = frozen v3 home lambda / old rolling league home baseline`

`v3 structural away factor = frozen v3 away lambda / old rolling league away baseline`

Then substitute/blend the new team-specific Venue8 baseline:

`new lambda = v3 structural factor * blended baseline`

where

`blended baseline = (1-w) * old league baseline + w * team-specific Venue8 baseline`.

Thus `w=0` is frozen v3 and `w=1` is a full replacement of the generic home/away baseline while leaving the rest of frozen v3 intact.

## Development results — 2019/20 through 2024/25

| Venue-baseline weight | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 0% — frozen v3 | 54.57% | 0.58072 | 0.97725 |
| 25% | 54.78% | 0.57518 | 0.96908 |
| 50% | 54.64% | 0.57249 | 0.96495 |
| 75% | 54.29% | **0.57232** | **0.96484** |
| 100% — full replacement | **54.85%** | 0.57435 | 0.96885 |

The idea adds clear probability signal across the six-season development set. The best development probability calibration is around 50–75% Venue8 baseline weight. Full replacement also beats frozen v3 on development Brier/log loss and slightly on top-pick accuracy.

## Untouched 2025/26 holdout

| Venue-baseline weight | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 0% — frozen v3 | **48.33%** | **0.63326** | **1.05262** |
| 25% | 46.67% | 0.63475 | 1.05306 |
| 50% | 46.67% | 0.63791 | 1.05570 |
| 75% | 46.25% | 0.64260 | 1.06058 |
| 100% — full replacement | 46.67% | 0.64869 | 1.06777 |

The holdout moves in the opposite direction. Even a 25% Venue8 substitution is slightly worse than frozen v3, and full replacement is materially worse.

Therefore do not promote or tune the weight using 2025/26.

## 2025/26 draw-heavy-club split

The prior diagnosis found that Bournemouth, Leeds and Brentford accounted for an extraordinary amount of the 2025/26 draw anomaly.

On the 67 GW15+ matches involving at least one of those teams:

- frozen v3: 32.84% accuracy / Brier 0.70712
- 50% capped Venue8 baseline: 34.33% / 0.72000
- 75%: 35.82% / 0.72889
- 100%: 35.82% / 0.73917

The Venue8 substitution can pick a few more winners in that group but becomes less well calibrated because it still cannot anticipate the extraordinary draw rate.

On the other 173 2025/26 matches:

- frozen v3: **54.34%** accuracy / Brier **0.60466**
- 50% capped Venue8 baseline: 51.45% / 0.60612
- 75%: 50.29% / 0.60919
- 100%: 50.87% / 0.61365

So the 2025/26 failure is not only the three draw-heavy clubs for this venue-baseline construction. Outside that anomaly, frozen v3's broader strength signal still chose winners better than the venue-adjusted versions.

## One-sided cap observations

Season-level capped-versus-raw comparisons are mixed, as expected from a robustness adjustment rather than an accuracy optimiser.

The one-sided cap is notably helpful in several later development seasons, including 2022/23, 2023/24 and 2024/25, and it reduces the damage in the draw-heavy 2025/26 subset. It is not universally better in every season.

Keep the cap as a football-sensible guard against extreme scoreline residuals; do not tune the cap threshold to maximise this back-test.

## Conclusion

1. The concept is **promising**: team-specific Venue8 attack/defence contains real information that improves frozen-v3 probability calibration over 2019/20–2024/25.
2. A complete replacement of the generic league baseline is too aggressive to promote because it deteriorates materially on untouched 2025/26.
3. The development optimum lies around a 50–75% Venue8 baseline contribution, but this must not be frozen from this sweep because the holdout rejects it.
4. Retain the current one-sided `xG + 1.0` actual-goal cap and 50/50 xG/capped-actual construction for this research branch.
5. Keep frozen v3 as the validated production baseline.
6. The next useful test is to identify a **pre-match reliability/shrinkage rule** for Venue8 — i.e. when team-specific venue evidence deserves meaningful weight and when v3's long-term/opponent-adjusted baseline should dominate — rather than choosing one unconditional venue weight for every match.
