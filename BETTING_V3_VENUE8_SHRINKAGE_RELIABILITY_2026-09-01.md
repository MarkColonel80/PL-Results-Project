# v3 + Venue8 — shrinkage and reliability tests

_Date: 2026-09-01_

## Goal

Continue from the capped equal-weight 24-match structural candidate and test how much team-specific Venue8 should influence the match baseline, and whether Venue8 weight should vary when the short venue sample looks unreliable.

Production v3 and `/betting/weekend` remain unchanged.

## Base architecture held constant

- 24-match structural attack/defence window, equal weighted.
- Structural actual GF/GA capped match-by-match at `min(actual, xG + 1.0)`.
- Structural attack/defence = 65% xG + 35% capped actual goals.
- Four pseudo-match shrinkage toward the league scoring midpoint.
- PPG10 adjustment retained.
- Team-specific Venue8 uses prior home matches for the home side and prior away matches for the away side.
- Venue8 actual GF/GA use the same one-sided `xG + 1.0` cap.
- Adjusted venue attack/defence = 50% raw venue xG + 50% capped actual goals.
- Opponent interaction damping exponent 0.75.
- Independent Poisson H/D/A probabilities.
- Development sample: 2019/20–2024/25, 1,433 matches.
- Untouched stress-test: 2025/26, 240 matches.

## Venue shrinkage construction

Instead of always replacing the generic league home/away scoring baseline with the full team-specific Venue8 baseline, blend them geometrically.

For home scoring baseline:

`baseline_home = league_home^(1-w) * venue8_home^w`

For away scoring baseline:

`baseline_away = league_away^(1-w) * venue8_away^w`

where `w=0` means no team-specific venue baseline and `w=1` means full Venue8 replacement.

## Coarse fixed-weight results

### Development 2019/20–2024/25

| Venue8 weight | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 0% | 52.48% | 0.58591 | 0.98496 |
| 25% | 53.31% | 0.57836 | 0.97426 |
| **50%** | 54.08% | **0.57553** | **0.97052** |
| 75% | 54.22% | 0.57679 | 0.97345 |
| 100% | 54.15% | 0.58137 | 0.98254 |

Full Venue8 is too aggressive. A substantial but shrunk Venue8 contribution clearly improves probability quality. The broad optimum is around 50%.

### 2025/26 stress-test

| Venue8 weight | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| 0% | 46.67% | 0.64098 | 1.06015 |
| 25% | 46.67% | **0.63993** | **1.05709** |
| **50%** | **47.50%** | 0.64193 | 1.05815 |
| 75% | **47.50%** | 0.64660 | 1.06320 |
| 100% | 46.25% | 0.65352 | 1.07213 |

The stress-test strongly rejects full Venue8 and confirms the need for shrinkage. 25–50% is the robust zone; 50% gives the better top-pick accuracy and remains close on calibration.

## Fine fixed-weight check

| Venue8 weight | Development accuracy | Development Brier | Development log loss | 2025/26 accuracy | 2025/26 Brier | 2025/26 log loss |
|---|---:|---:|---:|---:|---:|---:|
| 40% | 53.80% | 0.57613 | 0.97120 | 47.08% | 0.64079 | 1.05724 |
| 45% | 53.87% | 0.57575 | 0.97072 | **47.92%** | 0.64130 | 1.05761 |
| **50%** | 54.08% | 0.57553 | **0.97052** | 47.50% | 0.64193 | 1.05815 |
| 55% | **54.15%** | **0.57548** | 0.97058 | 47.08% | 0.64267 | 1.05884 |
| 60% | 54.01% | 0.57559 | 0.97090 | 47.50% | 0.64350 | 1.05970 |

55% has a microscopically better development Brier than 50% (`0.00005`), while 50% is simpler and performs better on the untouched stress-test. Do not tune to 55%; retain 50% as the working shrinkage rule.

## Reliability-gate tests

### 1. Venue-baseline extremeness

Measured how far the team-specific Venue8 home/away baselines were from generic league home/away baselines using average absolute log deviation.

Development quartiles did not support a robust monotonic rule. The lowest-divergence quartile tolerated full Venue8, but the other three were generally best around 50%. A rule using 100% Venue8 only in the lowest development quartile improved development Brier slightly to `0.57533`, but worsened the untouched 2025/26 Brier to `0.64480` versus fixed-50 `0.64193`.

Decision: reject this adaptive gate.

### 2. Structural direction versus Venue8 direction

Compared the H-v-A probability direction under no Venue8 (`w=0`) versus full Venue8 (`w=1`).

Development:
- when directions agreed, 50% venue weight was best (Brier `0.56317` on 1,233 matches);
- when directions contradicted, 75% was slightly best (Brier `0.64820` on 200 matches).

2025/26 did not preserve this relationship:
- agreement group was best around 25%;
- contradiction group was best around 50%.

Decision: reject agreement/disagreement as a reliability switch.

### 3. Size of the capped-actual correction

Measured how far adjusted Venue8 attack/defence was pulled from raw venue xG by the capped actual-goal component.

No stable monotonic relationship emerged. A development-derived quartile rule produced only a tiny development improvement and worsened 2025/26 Brier to `0.64523` versus fixed-50 `0.64193`.

Decision: reject this adaptive gate.

### 4. Venue8 versus Venue18 stability

Built a leakage-safe Venue18 comparison using the same one-sided `xG + 1.0` capped actual-goal treatment and measured the divergence between adjusted Venue8 and adjusted Venue18 attack/defence.

Across development quartiles, 50% Venue8 remained the strongest or effectively tied zone even when Venue8 differed materially from Venue18. The second quartile marginally preferred 75%, but there was no monotonic pattern that justified an adaptive rule.

Decision: Venue8-vs-Venue18 divergence is useful diagnostically but does not currently justify changing the model weight.

## Main conclusion

The strongest result from this experiment is simpler than the proposed reliability-gated design:

**Use a fixed 50% team-specific Venue8 / 50% generic league venue-baseline blend.**

This keeps the useful information in recent team-specific home/away performance while preventing eight venue matches from fully replacing the broader structural baseline.

No tested reliability gate produced a development improvement that also survived the untouched 2025/26 stress-test.

## Working research model after this checkpoint

1. Equal-weight 24-match structural attack/defence history.
2. 65% xG + 35% capped actual goals at structural level.
3. One-sided actual-goal cap: `min(actual, xG + 1.0)`.
4. Four pseudo-match league shrinkage.
5. PPG10 adjustment.
6. Venue8 adjusted attack/defence using 50% raw venue xG + 50% capped actual goals.
7. **Shrink the Venue8 match baseline 50/50 toward the generic league home/away scoring baseline.**
8. No structural recency weighting.
9. No extra short-window Goals-minus-xG residual correction.
10. No adaptive Venue8 reliability gate from the signals tested here.
11. Keep 30-match structural history as the statistical benchmark.
12. Production v3 remains unchanged until the candidate is fully validated.

## Supabase research objects

- `public.betting_v3_venue8_fixed_weight_lambdas`
- `public.betting_v3_venue8_fixed_weight_scores`
- `public.betting_v3_venue8_venue18_reliability`
- `public.betting_v3_venue8_fine_weight_lambdas`

These are research-only objects.