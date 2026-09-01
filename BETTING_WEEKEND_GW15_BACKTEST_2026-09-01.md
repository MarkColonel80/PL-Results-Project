# Weekend venue model — GW15+ historical back-test

_Date: 2026-09-01_

## Purpose

Test the current manual weekend venue method historically and compare it with the earlier venue rules and frozen model v3.

The production/manual rule is **not changed by this checkpoint**. This is a research back-test.

## Evaluation window

Primary comparison uses Premier League seasons **2019/20 through 2025/26** so it overlaps the seven-season frozen-v3 history.

“Gameweek 15 onwards” is implemented as **both clubs having reached at least their 15th Premier League match of that season**, rather than filtering the stored `gameweek` label literally. This avoids postponed/rearranged fixture artefacts in historical source gameweek numbering.

Further eligibility:
- both teams must have at least **4 relevant current-spell venue matches** before kickoff;
- home team uses prior home matches only; away team uses prior away matches only;
- maximum venue window is 8;
- venue history is restricted to the club's current Premier League spell (`segment_id`), so stale prior-spell data is not used;
- xG inputs must be available;
- all calculations are leakage-safe and use only matches before kickoff.

Final apples-to-apples sample: **1,673 matches**.

Development/holdout split retained from prior modelling work:
- 2019/20–2024/25 development: **1,433 matches**
- 2025/26 untouched holdout: **240 matches**

## Current capped venue method

For each team over up to its prior eight relevant venue matches:

- venue PPG8 is calculated normally;
- actual goals are capped only for extreme positive goal-vs-xG overperformance at individual-match level:
  - `capped actual = min(actual, xG + 1.0)`
- underperformance is never increased;
- capped actual GF/GA is averaged over the venue window;
- adjusted venue xGF/xGA is a 50/50 blend of raw venue xG and capped actual goals;
- adjusted match lambdas/probabilities use the existing weekend Poisson scaling.

Current manual decision rule:
- PPG8 decides unless the absolute PPG gap is `<= 0.30`;
- when the gap is close, capped adjusted venue xG probability top-pick breaks the tie.

## Seven-season GW15+ exact-sample results

| Rule/model | Top-pick accuracy |
|---|---:|
| Venue PPG8 only | 50.33% |
| Raw venue xG8 only | 51.88% |
| Old uncapped adjusted venue xG8 only | **53.50%** |
| Old PPG8 + uncapped adjusted-xG tie-break | 52.06% |
| New one-sided-capped adjusted venue xG8 only | 53.08% |
| **Current PPG8 + capped adjusted-xG tie-break** | **51.94%** |
| Frozen v3, same 1,673 matches | **53.68%** |

Probability quality on the same exact sample:
- uncapped adjusted venue xG: Brier about **0.59257**, log loss about **0.99447**
- capped adjusted venue xG: Brier **0.59264**, log loss **0.99441**
- frozen v3: Brier **0.58826**, log loss **0.98806**

Interpretation:
- the one-sided cap is almost neutral overall: it slightly improves log loss but very slightly worsens Brier/top-pick accuracy;
- the cap should be viewed as a robustness/calibration safeguard against freak scorelines, not as an accuracy boost;
- v3 remains the stronger standalone probability model on the full seven-season exact sample;
- the current **PPG-primary hybrid is weaker than simply using adjusted venue xG on every eligible fixture**.

## Why the current <=0.30 tie-break rule underperforms

Across the 1,673-match sample:
- matches with PPG gap `<= 0.30`: **452**
- capped adjusted-xG top-pick accuracy on that subset: **44.03%**
- matches with PPG gap `> 0.30`: 1,221
- PPG-primary decision accuracy on that subset: **54.87%**

The close-PPG group is intrinsically hard to predict. Adjusted xG improves on PPG inside many of those close cases, but the group as a whole remains low-accuracy. More importantly, adjusted xG also performs strongly enough outside the close group that restricting it to the tie-break subset gives up useful signal.

## Season-by-season comparison

| Season | N | PPG8 | Capped adj xG | Current hybrid | v3 | Capped Brier | v3 Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019/20 | 240 | 46.7% | 54.6% | 50.8% | 54.2% | 0.5901 | 0.5794 |
| 2020/21 | 238 | 47.1% | 50.8% | 48.3% | 50.8% | 0.6060 | 0.6014 |
| 2021/22 | 239 | 55.2% | 57.7% | 56.9% | 56.9% | 0.5572 | 0.5594 |
| 2022/23 | 236 | 53.4% | 53.8% | 52.5% | 52.1% | 0.5899 | 0.5823 |
| 2023/24 | 240 | 55.8% | 53.8% | 55.0% | 58.8% | 0.5704 | 0.5736 |
| 2024/25 | 240 | 50.4% | 55.8% | 53.3% | 54.6% | 0.5785 | 0.5883 |
| 2025/26 | 240 | 43.8% | 45.0% | 46.7% | 48.3% | 0.6562 | 0.6333 |

The same 2025/26 deterioration seen in v6 appears strongly in the venue model. Do not tune directly to this one season merely to remove the miss.

## Development versus untouched 2025/26 holdout

### 2019/20–2024/25 development — 1,433 matches

- uncapped adjusted venue xG: accuracy **54.78%**, Brier **0.58186**, log loss **0.98007**
- capped adjusted venue xG: accuracy **54.43%**, Brier **0.58200**, log loss **0.98019**
- frozen v3: accuracy **54.57%**, Brier **0.58072**, log loss **0.97725**

The venue model is genuinely competitive with v3 on the six-season development period, but does not clearly beat it on probability quality.

### 2025/26 holdout — 240 matches

- uncapped adjusted venue xG: accuracy **45.83%**, Brier **0.65653**, log loss **1.08043**
- capped adjusted venue xG: accuracy **45.00%**, Brier **0.65616**, log loss **1.07930**
- frozen v3: accuracy **48.33%**, Brier **0.63326**, log loss **1.05262**

The one-sided cap slightly improves Brier/log loss versus the uncapped venue model on the holdout, but not enough to solve the wider 2025/26 failure.

## PPG-gap threshold sensitivity

The current `<= 0.30` threshold is not historically stable enough to tune aggressively.

Development hybrid accuracy by xG-tie-break threshold:
- 0.0 / 0.1: 52.69%
- 0.2 / 0.3: 52.83%
- 0.4: 54.01%
- 0.5: 54.64%
- 0.75: 54.29%
- 1.0: 54.36%
- adjusted xG effectively always: 54.43%

2025/26 holdout:
- 0.0 / 0.1: 45.83%
- 0.2: 46.25%
- 0.3: **46.67%**
- 0.4: 45.42%
- 0.5: 44.17%
- 0.75: 45.00%
- 1.0: 45.00%
- adjusted xG effectively always: 45.00%

A threshold around 0.5 looks best in development but fails badly on the untouched holdout. Therefore do **not** retune the threshold from this sweep.

## Simple v3 + capped venue-xG blend test

A fixed linear probability blend was tested to see whether capped venue xG contributes information not already present in v3.

On development data, adding venue xG materially improves probability calibration:
- 100% v3: Brier 0.58072 / log loss 0.97725
- 80% v3 + 20% capped venue xG: 0.57761 / 0.97303
- 60% v3 + 40% capped venue xG: 0.57619 / 0.97109
- 50% v3 + 50% capped venue xG: **0.57611 / 0.97099**

But the untouched 2025/26 holdout moves the opposite way:
- 100% v3: Brier **0.63326** / log loss **1.05262**
- 90% v3 + 10% capped venue xG: 0.63446 / 1.05393
- 80% v3 + 20% capped venue xG: 0.63589 / 1.05551
- 50% / 50%: 0.64167 / 1.06203

So capped venue xG does contain complementary development-period signal, but the blend is not stable enough to promote. Even a 10% venue addition worsens the untouched holdout.

## Relation to v6

The prior v6 experiment also failed materially in 2025/26. Its documented residual-aware every-family version scored Brier 0.63174 / log loss 1.04954 / 48.8% accuracy on its **different 334-match 2025/26 eligible sample**. That is useful context but is not an exact apples-to-apples comparison with this GW15+ 240-match holdout.

## Current conclusion

1. **Keep GW15+ as the historical evaluation window** for this venue method. Implement it as each club having reached its 15th league match, not literal source gameweek labels.
2. Keep the **minimum 4 venue-match production gate**; by GW15 it is rarely binding, but it prevents early-season nonsense such as Ipswich v Liverpool.
3. Keep the **one-sided xG + 1.0 cap** as a sensible robustness safeguard, but do not claim it improves accuracy.
4. Do **not** promote the current PPG-primary / <=0.30 hybrid as the strongest historical model. On the exact test it scores 51.94%, below capped adjusted xG alone (53.08%) and v3 (53.68%).
5. Do **not** tune the PPG-gap threshold from this dataset; development and holdout disagree strongly.
6. v3 remains the validated baseline.
7. The most promising venue finding is that adjusted venue xG is competitive with v3 over six development seasons and improves a v3 blend in-sample, but this does not survive 2025/26.
8. Next research should investigate **why 2025/26 is a shared failure regime** before changing model weights or thresholds.
