# v3 24-match + Venue8 — PPG10 ablation

_Date: 2026-09-01_

## Trigger

Arsenal v Chelsea on the weekend comparison page showed Arsenal at 76.6% while the market was around 55%. The discrepancy was investigated stage by stage.

## Data freshness bug

`public.betting_team_features_v2_cache` is a materialized view. The comparison refresh had not refreshed it after the latest 2026/27 team-match rows were loaded.

Consequences for Arsenal v Chelsea:
- Arsenal's 31 Aug 2026 1-0 win at Aston Villa was missing from the comparison inputs.
- Chelsea's 30 Aug 2026 4-3 win over Brighton was missing from the comparison inputs.
- stale comparison probability: Arsenal 76.6%.
- after refreshing the feature cache and recalculating with the original PPG10 layer: Arsenal 67.0%, draw 20.8%, Chelsea 12.2%.

The refresh script now starts with:

`refresh materialized view public.betting_team_features_v2_cache;`

so future manual weekend comparison refreshes cannot silently omit newly loaded league matches.

## Arsenal v Chelsea decomposition after cache refresh

Fresh-data stages:
- 24-match structural model with generic venue baseline and no PPG10: Arsenal about 55.0%.
- add the tested 50% team-specific Venue8 baseline: Arsenal 58.8%, draw 24.2%, Chelsea 17.0%.
- add the old PPG10 adjustment: Arsenal 67.0%, draw 20.8%, Chelsea 12.2%.

The remaining model/market disagreement after the cache refresh was therefore primarily caused by PPG10, not the 24-match structural strength.

Fresh PPG10 inputs were Arsenal 2.40 versus Chelsea 1.00. Early in 2026/27 these still contained substantial prior-season result history.

## Early-season PPG10 test — prior season carry versus alternatives

Leakage-safe sample:
- development: 2019/20–2024/25, 698 eligible matches where both sides were within their first 14 league matches of the season and both had at least four current-spell relevant venue matches available;
- stress check: 2025/26, 118 matches.

Everything except PPG treatment was held fixed:
- equal-weight up-to-24-match current-spell structural history;
- 65% xG + 35% actual goals capped at `min(actual, xG + 1.0)`;
- four pseudo-match league shrinkage;
- capped Venue8;
- 50/50 geometric Venue8-to-generic-league venue baseline shrink;
- 0.75 opponent interaction damping;
- Poisson H/D/A probabilities.

Variants:
1. `carry`: old PPG10 from current PL spell, allowing prior-season carryover.
2. `season_only`: current-season PPG10 only, with the existing four pseudo-match 1.35 shrinkage.
3. `phased`: current-season PPG signal additionally phased in by current-season sample size.
4. `no_ppg`: no separate result-form multiplier.

### Early-season aggregate

Development 2019/20–2024/25:

| Variant | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| carry | 52.29% | 0.60045 | 1.00833 |
| season only | 52.01% | 0.59960 | 1.00714 |
| phased | 52.15% | 0.59909 | 1.00636 |
| **no PPG** | 51.29% | **0.59529** | **1.00005** |

The carry-over rule is worst on calibration. No PPG is clearly best on Brier/log loss, although carry-over happens to have one percentage point more top-pick accuracy.

2025/26 stress check:

| Variant | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| carry | 52.54% | 0.59360 | 1.00158 |
| season only | 54.24% | 0.59193 | 0.99829 |
| phased | 52.54% | **0.59107** | **0.99709** |
| no PPG | **55.08%** | 0.59374 | 1.00065 |

2025/26 does not support prior-season carryover either. It prefers current-season-only phased PPG on calibration, while no PPG has the best top-pick accuracy.

### Early-season development season-by-season

No PPG has better Brier than carry-over in five of six development seasons:
- 2019/20: carry 0.58690 vs no PPG 0.59017 — carry better.
- 2020/21: carry 0.60306 vs no PPG 0.60150 — no PPG better.
- 2021/22: carry 0.62811 vs no PPG 0.61781 — no PPG materially better.
- 2022/23: carry 0.60586 vs no PPG 0.60087 — no PPG better.
- 2023/24: carry 0.58464 vs no PPG 0.57767 — no PPG better.
- 2024/25: carry 0.59456 vs no PPG 0.58420 — no PPG materially better.

Simple switch rules such as no PPG for N matches and then current-season PPG did not beat the all-no-PPG development calibration. This argues against adding an early-season threshold parameter merely to rescue PPG.

## GW15+ PPG10 ablation

Because early-season results raised the possibility that PPG10 is redundant in the newer model, the same 24-match + 50%-Venue8 candidate was tested on the established GW15+ research sample with and without PPG10.

Development 2019/20–2024/25, 1,433 matches:

| Variant | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| **no PPG** | **54.36%** | **0.57474** | **0.96908** |
| PPG10 | 54.08% | 0.57553 | 0.97052 |

2025/26 stress check, 240 matches:

| Variant | Accuracy | Brier | Log loss |
|---|---:|---:|---:|
| no PPG | 45.00% | **0.63814** | **1.05587** |
| PPG10 | **47.50%** | 0.64193 | 1.05815 |

The 2025/26 PPG version gets more top picks right but has worse probability quality. The project has consistently prioritised Brier/log loss when fitting probabilities, with top-pick accuracy secondary.

GW15+ season-by-season is mixed, but aggregate probability quality favours no PPG. PPG10 therefore does not justify its extra parameter/layer in this candidate architecture.

## Decision

Remove the separate PPG10 probability adjustment from the **24-match + Venue8 research comparison model**.

Retain PPG10 on the weekend page as a diagnostic only so unusual result-form differences remain visible to the human reviewer.

New comparison model version:

`v3_24_venue8_50_noppg`

Working candidate:
1. up to 24 equal-weight matches from the current PL spell;
2. 65% xG + 35% capped actual goals;
3. one-sided actual-goal cap `min(actual, xG + 1.0)`;
4. four pseudo-match league shrinkage;
5. opponent attack/defence interaction with exponent 0.75;
6. capped team-specific Venue8 attack/defence;
7. 50/50 geometric shrink of Venue8 baseline toward generic league home/away baseline;
8. **no separate PPG10 probability multiplier**;
9. independent Poisson H/D/A probabilities;
10. minimum four current-spell relevant venue matches for each side before the comparison is scored.

## Current Arsenal v Chelsea comparison

After cache refresh and PPG10 removal:
- expected goals: Arsenal 1.662, Chelsea 0.766;
- Arsenal win 58.79%;
- draw 24.17%;
- Chelsea win 17.04%;
- Arsenal fair odds about 1.70.

This is much closer to the market than the stale 76.6% output and is generated without hard-coding bookmaker agreement.

## Supabase research objects

- `public.betting_v3_early_ppg_inputs`
- `public.betting_v3_early_ppg_scores`
- `public.betting_v3_venue8_ppg_ablation_gw15`

Production v3 remains unchanged. The manual weekend PPG8/tie-break model also remains unchanged. Only the separate 24-match + Venue8 comparison candidate was updated.
