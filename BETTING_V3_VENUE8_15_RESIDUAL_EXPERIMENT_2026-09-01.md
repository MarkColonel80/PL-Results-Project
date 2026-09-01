# v3 + Venue8 — 15-match structural cap / residual experiment

_Date: 2026-09-01_

## Goal

Test whether the proposed 15-match structural model should do more than the normal 65% xG / 35% actual-goals blend when a team consistently under- or over-performs xG.

This is research only. Production v3 and `/betting/weekend` are unchanged.

## Evaluation sample

Same apples-to-apples GW15+ sample used in the current v3 + Venue8 work:

- 2019/20–2024/25 development: 1,433 matches
- 2025/26 holdout: 240 matches
- both clubs at least at their 15th league match of that season
- current-PL-spell history only
- both clubs at least 4 relevant Venue8 matches
- all inputs pre-kickoff / leakage-safe

Supabase research input cache: `public.betting_v3_venue8_15_residual_inputs`.

## Common model architecture

All variants keep the same structure:

- overall attack/defence: previous 15 current-spell PL matches
- base mix: 65% xG + 35% actual-goal information
- four pseudo-match league-average shrinkage
- PPG10 adjustment
- team-specific Venue8 baseline
- Venue8 actual goals use the current one-sided `min(actual, xG + 1.0)` cap and a 50/50 xG/capped-actual blend
- 0.75 attack x opponent-defence damping
- independent Poisson H/D/A conversion

## Structural cap test

The previous 15-match model allowed unrestricted actual goals in the 35% structural component.

The cap variant instead applies the same match-level one-sided rule used by Venue8:

`capped actual goals = min(actual goals, xG + 1.0)`

for GF and GA before averaging over the 15-match structural window.

Underperformance is not lifted toward xG.

### Results

Within the identical residual-test reconstruction:

| Variant | Development accuracy | Development Brier | Development log loss | 2025/26 accuracy | 2025/26 Brier | 2025/26 log loss |
|---|---:|---:|---:|---:|---:|---:|
| Raw actual structural 15 | 53.80% | 0.58662 | 0.99099 | 45.83% | 0.65827 | 1.08081 |
| **Capped actual structural 15** | 53.66% | **0.58541** | **0.98857** | 45.83% | **0.65693** | **1.07832** |

The structural cap improves probability calibration on both development and the untouched 2025/26 holdout, while top-pick accuracy is essentially unchanged. This is exactly the behaviour wanted from a robustness guard: it removes some damage from freak scorelines without pretending to be a winner-accuracy optimiser.

## Persistent residual correction

The next variants tested whether xG itself should be corrected when the 15-match sample persistently disagrees with actual results.

The main rule was deliberately one-sided and conservative:

- attack xGF is pulled down only when capped actual GF is below xGF;
- defensive xGA is pushed up only when capped actual GA is above xGA;
- persistent positive attacking overperformance does not lift xGF;
- persistent defensive overperformance does not lower xGA;
- the 35% capped-actual component already carries some realised-performance information.

Weights tested are the fraction of the persistent residual applied to xG before the normal 65/35 structural blend.

| Variant | Development accuracy | Development Brier | Development log loss | 2025/26 accuracy | 2025/26 Brier | 2025/26 log loss |
|---|---:|---:|---:|---:|---:|---:|
| Cap only / 0% residual | 53.66% | **0.58541** | **0.98857** | 45.83% | **0.65693** | **1.07832** |
| 10% residual | 53.73% | 0.58558 | 0.98887 | 45.83% | 0.65712 | 1.07854 |
| 20% residual | 53.80% | 0.58577 | 0.98920 | 45.83% | 0.65733 | 1.07879 |
| 25% residual | 53.66% | 0.58587 | 0.98938 | 45.83% | 0.65743 | 1.07892 |

The pattern is monotonic on the probability metrics: once the structural cap is in place, increasing the 15-match residual correction steadily worsens Brier and log loss. There is no evidence here that a separate persistent xG residual correction adds value at a 15-match horizon.

## Interpretation

The 15-game model already accounts for sustained xG underperformance through the 35% actual-goal component. Once freak positive residuals are capped match-by-match, separately pulling xG toward the same 15-game realised performance appears to double-count that information.

This differs from the earlier v6 residual result, where a heavily shrunk 30-match residual produced a small clean gain. The longer residual window is more stable; 15 matches appears too short to warrant a second correction on top of the actual-goal blend.

## Current conclusion

1. **Adopt the structural `xG + 1.0` actual-goal cap as the preferred research version of the 15-match architecture.** It improves Brier/log loss on both development and 2025/26 holdout.
2. Do **not** add a separate 15-match persistent residual adjustment to xG. Tested 10%, 20% and 25% corrections all worsen calibration versus cap-only.
3. Keep the basic 65% xG / 35% capped-actual blend. This already pulls a persistently underperforming team away from raw xG without overreacting.
4. The exact production choice between 15 and 30 structural history remains open; the prior comparison still showed 30 modestly stronger overall, while 15 is more responsive.
5. Production v3 and `/betting/weekend` remain unchanged until the research architecture is explicitly promoted.

GitHub SQL record: `scripts/add_v3_venue8_15_residual_research_inputs.sql`.
