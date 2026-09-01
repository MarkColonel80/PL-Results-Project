# v3 + Venue8 — structural recency-weighting test

_Date: 2026-09-01_

## Goal

Continue from the capped structural-window sweep, where an equal-weight 24-match structural window emerged as the leading responsive candidate and 30 matches remained the statistical benchmark.

This experiment tests whether the 24 structural matches should receive a small recency bias rather than equal weight.

Production v3 and `/betting/weekend` remain unchanged.

## Architecture held constant

The model is unchanged except for weighting within the 24-match overall structural history.

Common rules:

- historical evaluation only once both clubs have reached at least their 15th league match of that season;
- current Premier League spell only;
- team-specific Venue8 remains unchanged;
- Venue8 minimum four relevant venue matches;
- venue actual GF/GA capped match-by-match at `min(actual, xG + 1.0)`;
- adjusted venue attack/defence = 50% raw venue xG + 50% capped actual goals;
- structural actual GF/GA capped match-by-match at `min(actual, xG + 1.0)`;
- structural attack/defence = 65% xG + 35% capped actual goals;
- four pseudo-match shrinkage toward the league scoring midpoint;
- PPG10 adjustment retained;
- opponent attack/defence interaction damped with exponent 0.75;
- independent Poisson H/D/A probabilities;
- no separate Goals-minus-xG residual correction.

## Recency candidates

The 24 structural matches were split into three eight-match blocks, newest to oldest.

Tested weights:

- equal 24 benchmark: `1.0 / 1.0 / 1.0`
- very gentle: `1.1 / 1.0 / 0.9`
- gentle: `1.2 / 1.0 / 0.8`
- moderate: `1.4 / 1.0 / 0.6`
- strong: `1.6 / 1.0 / 0.4`

Weights are applied identically to structural xGF, xGA, capped GF and capped GA. The existing four-match league-average shrinkage still uses the actual number of prior matches rather than treating recency weighting as extra observations.

## Sample

Same leakage-safe sample as the structural-window sweep:

- 2019/20–2024/25 development: 1,433 matches
- 2025/26 untouched stress-test: 240 matches

## Development results — 2019/20 through 2024/25

| Structural weighting | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| equal 24 | 54.15% | **0.58137** | **0.98254** |
| 1.1 / 1.0 / 0.9 | 54.36% | 0.58164 | 0.98299 |
| 1.2 / 1.0 / 0.8 | 54.36% | 0.58196 | 0.98355 |
| 1.4 / 1.0 / 0.6 | **54.43%** | 0.58279 | 0.98498 |
| 1.6 / 1.0 / 0.4 | 54.22% | 0.58384 | 0.98683 |
| equal 30 benchmark | **54.43%** | **0.58123** | **0.98195** |

A mild recency bias can improve top-pick accuracy by a few tenths of a percentage point, but every recency-weighted 24-match version worsens Brier and log loss relative to equal-weight 24. Stronger recency weighting progressively worsens probability calibration.

## 2025/26 stress-test

| Structural weighting | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| equal 24 | 46.25% | **0.65352** | **1.07213** |
| 1.1 / 1.0 / 0.9 | 46.25% | 0.65401 | 1.07306 |
| 1.2 / 1.0 / 0.8 | 46.67% | 0.65453 | 1.07403 |
| 1.4 / 1.0 / 0.6 | 46.67% | 0.65563 | 1.07612 |
| 1.6 / 1.0 / 0.4 | **47.08%** | 0.65683 | 1.07839 |
| equal 30 benchmark | 46.67% | 0.65375 | 1.07297 |

2025/26 was not used to choose the weighting. It reinforces the development conclusion: stronger recency weighting can occasionally move more top picks to the realised winner, but probability calibration becomes worse.

## Decision

Do **not** add structural recency weighting.

The research objective prioritises Brier/log loss over raw top-pick accuracy. On that criterion:

1. Equal-weight 24 remains the leading responsive structural candidate.
2. Equal-weight 30 remains the strict statistical benchmark.
3. Even a very gentle `1.1 / 1.0 / 0.9` weighting does not improve calibration.
4. The small accuracy gains from recency weighting are not sufficient justification for adding complexity while worsening probability quality.

This is useful negative evidence: the gain from shortening 30 to 24 appears to come from discarding the oldest six matches, not from continuously upweighting the newest matches within the retained history.

## Supabase research object

- `public.betting_v3_venue8_recency24_inputs`

This materialized research input stores the 1.2/1.0/0.8, 1.4/1.0/0.6 and 1.6/1.0/0.4 weighted structural features. The 1.1/1.0/0.9 case was evaluated exactly from the equal-24 and 1.2-weighted sufficient statistics. No production prediction tables or manual weekend views were changed.

## Working direction

- Continue from equal-weight 24, capped structural strength.
- Keep equal-weight 30 beside it as the benchmark.
- Do not add a structural recency-decay parameter.
- Do not tune against 2025/26.
