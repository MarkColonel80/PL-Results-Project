# Dixon–Coles score-layer experiment — 2026-09-07

## Purpose

Test whether the current `v3_24_venue8_50_noppg` research candidate should replace independent Poisson score conversion with a Dixon–Coles low-score correlation adjustment.

The team-strength architecture was held completely fixed:
- 24-match equal-weight structural history
- 65% xG + 35% one-sided capped actual goals
- four pseudo-match shrinkage
- opponent interaction exponent 0.75
- Venue8 50% xG + 50% capped actual
- 50/50 Venue8-to-generic-venue shrinkage
- no PPG multiplier

Only the final H/D/A probability conversion was changed.

## Dixon–Coles adjustment

For home expected goals `lambda_h`, away expected goals `lambda_a`, and correlation parameter `rho`, the standard low-score correction is applied only to 0-0, 0-1, 1-0 and 1-1.

Because the correction conserves total probability exactly, the H/D/A probabilities can be updated directly from the independent Poisson probabilities using:

- `delta = exp(-(lambda_h + lambda_a)) * lambda_h * lambda_a * rho`
- `P(H)_DC = P(H)_Poisson + delta`
- `P(D)_DC = P(D)_Poisson - 2*delta`
- `P(A)_DC = P(A)_Poisson + delta`

Therefore:
- negative `rho` increases low-score draw probability
- positive `rho` reduces low-score draw probability

## Development sample

Source: `public.betting_v3_venue8_ppg_ablation_gw15`.

Development/model-selection sample:
- seasons 2019/20–2024/25
- n = 1,433
- GW15+ full-history candidate sample

2025/26 is retained only as a stress check and is not used to choose the parameter.

## Aggregate rho sweep

A grid from -0.20 to +0.10 in 0.005 increments was evaluated by Brier score and log loss.

Baseline independent Poisson (`rho=0`):
- Brier: 0.574742
- log loss: 0.969079
- top-pick accuracy: 54.36%

Best aggregate area was around `rho=+0.07` to `+0.075`:
- `rho=+0.07`: Brier 0.574363 / log loss 0.968476 / accuracy 54.43%
- `rho=+0.075`: Brier 0.574363 / log loss 0.968486 / accuracy 54.43%

The development sample's actual draw rate was 22.05%. Independent Poisson was slightly too draw-heavy; the positive-rho fit moves average predicted draw probability down toward the observed rate.

This is the opposite of the initial hypothesis prompted by the draw-heavy Matchweek 3 weekend.

## Season-by-season fixed +0.07 comparison

| Season | Poisson Brier | DC +0.07 Brier | Poisson log loss | DC +0.07 log loss | Actual draw rate |
|---|---:|---:|---:|---:|---:|
| 2019/20 | 0.579948 | 0.580137 | 0.976167 | 0.976019 | 22.50% |
| 2020/21 | 0.603454 | 0.602187 | 1.014395 | 1.011065 | 21.43% |
| 2021/22 | 0.558063 | 0.556880 | 0.943004 | 0.940875 | 20.50% |
| 2022/23 | 0.570494 | 0.569807 | 0.960948 | 0.960440 | 22.46% |
| 2023/24 | 0.567794 | 0.567958 | 0.962757 | 0.963439 | 22.08% |
| 2024/25 | 0.568796 | 0.569290 | 0.957337 | 0.959123 | 23.33% |

The fixed positive correction helps clearly in 2020/21–2022/23, is mixed/neutral in 2019/20, and is slightly worse in 2023/24–2024/25.

## Leave-one-season-out validation

For each development season, `rho` was fitted on the other five seasons only and then scored on the held-out season.

Chosen training rhos and held-out deltas:

| Holdout | Fitted rho | Δ Brier vs Poisson | Δ log loss vs Poisson |
|---|---:|---:|---:|
| 2019/20 | +0.085 | +0.000323 | +0.000011 |
| 2020/21 | +0.055 | -0.001061 | -0.002739 |
| 2021/22 | +0.055 | -0.000990 | -0.001783 |
| 2022/23 | +0.065 | -0.000663 | -0.000518 |
| 2023/24 | +0.080 | +0.000240 | +0.000887 |
| 2024/25 | +0.090 | +0.000757 | +0.002545 |

Combined leave-one-season-out result across all 1,433 matches:
- Poisson Brier: 0.574742
- LOO Dixon–Coles Brier: 0.574512
- improvement: 0.000230
- Poisson log loss: 0.969079
- LOO Dixon–Coles log loss: 0.968818
- improvement: 0.000261
- Poisson top-pick accuracy: 54.36%
- LOO Dixon–Coles top-pick accuracy: 54.43%

The out-of-sample improvement is real in aggregate but extremely small and not season-stable.

## Regime instability

If rho is fitted separately within each season, the Brier-optimal values vary materially:

- 2019/20: +0.015
- 2020/21: +0.150 (grid boundary)
- 2021/22: +0.150 (grid boundary)
- 2022/23: +0.100
- 2023/24: +0.015
- 2024/25: -0.015
- 2025/26: -0.150 (grid boundary)

This is strong evidence that low-score/draw behaviour changes by league season/regime rather than being a stable structural property that one fixed Dixon–Coles parameter can solve.

## 2025/26 stress check

2025/26 actual draw rate on the 240-match GW15+ sample was 31.25%.

| Score layer | Brier | Log loss | Avg predicted draw |
|---|---:|---:|---:|
| DC -0.07 | 0.635757 | 1.051247 | 26.50% |
| Poisson | 0.638141 | 1.055866 | 24.88% |
| DC +0.07 | 0.641323 | 1.062170 | 23.26% |

A negative draw-boosting rho helps the abnormal 2025/26 season; the development-fitted positive rho makes it worse.

This reinforces the regime-dependence diagnosis and is not a reason to tune the main model to 2025/26.

## Matchweek 3 2026/27 diagnostic

Seven fixtures were eligible for the 24-match + Venue8 candidate. Five finished as draws.

| Score layer | Brier | Log loss | Avg predicted draw | Actual draw rate |
|---|---:|---:|---:|---:|
| DC -0.07 | 0.704246 | 1.144569 | 28.87% | 71.43% |
| Poisson | 0.727137 | 1.181846 | 27.14% | 71.43% |
| DC +0.07 | 0.750931 | 1.222196 | 25.41% | 71.43% |

A negative rho would have helped this weekend, but that is hindsight on seven matches and conflicts with the six-season development fit.

## Decision

**Do not replace independent Poisson in the live 24-match + Venue8 candidate.**

Reasons:
1. Aggregate Dixon–Coles improvement is tiny.
2. Leave-one-season-out improvement is only about 0.00023 Brier and 0.00026 log loss.
3. The sign and magnitude of the optimal rho vary substantially by season.
4. The 2025/26 draw spike and 2026/27 Matchweek 3 both prefer negative rho, while much of the development sample prefers positive rho.
5. A fixed parameter would therefore risk encoding the wrong draw regime.

Keep independent Poisson as the current score layer.

The useful research conclusion is that draw/finishing compression appears to be **regime-dependent**. If revisited, the next defensible experiment would be a fully leakage-safe, pre-match regime estimator using only prior league information, and it should have to beat Poisson out of sample. Previous simple rolling draw-regime corrections have already been rejected, so this should not be pursued unless a materially better specification is available.
