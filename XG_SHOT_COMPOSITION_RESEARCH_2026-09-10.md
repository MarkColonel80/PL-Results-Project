# PL Data Hub — shot composition research

10 September 2026. Exploratory research; production forecasts and database unchanged.

**Finding:** teams have recognisable chance-quality profiles, but the first predictive test supports only a small additional signal. Average chance quality slightly improved win/draw/loss probability scores; it did not improve predictions of whether a team would fail to score. This is useful diagnostic information, with insufficient evidence to replace or modify the live model.

## What was tested

The question was whether similar total xG can arise from materially different attacking patterns, and whether those patterns help forecast the next match. The study used the project's existing Understat archive, the exact frozen v3 predictions exported read-only from Supabase, and the existing recent FPL-Core-Insights shot feed for a separate goalkeeper-data audit.

The historical archive covers 3,800 matches across ten complete seasons, 2014/15–2023/24, plus 59 matches from 2024/25. It contains 98,236 shot events excluding own goals across that full range. One incomplete match, Sheffield United–Everton on 26 December 2020, was excluded. All 1,959 historical matches overlapping frozen v3 mapped by exact season, date, teams and final score; no approximate or player-name matches were needed.

The protocol was written before forecast evaluation. Later data-audit amendments were recorded before any performance results were calculated.

## Teams do have different profiles

Across 398 pairs of separate eight-match blocks, covering 200 team-seasons, the correlation between the earlier and later blocks was:

| Measure | Correlation |
|---|---:|
| Total non-penalty xG per game | 0.672 |
| Shots per game | 0.632 |
| Average xG per shot | 0.402 |
| Average xG per rebound-adjusted sequence | 0.413 |
| Share of xG from chances below 0.10 | 0.304 |
| Share of xG from chances at least 0.30 | 0.229 |

Chance quality is moderately persistent, but total xG and shot volume are more stable. A team's share of particularly large chances is considerably noisier. These are descriptive correlations, not probabilities or proof of causation.

For a concrete historical example, in **2023/24**, excluding penalties and own-goal events:

| Team | Shots per match | Average xG per shot | Non-penalty xG per match |
|---|---:|---:|---:|
| Brentford | 12.39 | 0.134 | 1.66 |
| Brighton & Hove Albion | 14.63 | 0.105 | 1.54 |

This illustrates fewer, better chances versus more, smaller chances. Their total xG is not identical, and this example is descriptive; it was not used to select a model or threshold.

## Did it improve forecasts?

The main test comprised **1,360 matches from 2020/21–2023/24**. Training began with 2019/20 and expanded using only earlier seasons. Each team's features used at most its previous 24 matches in its current continuous Premier League spell, with at least ten prior games. Windows containing an invalid source match were excluded. Promoted/relegated spells were handled separately.

The added inputs were the team's prior average non-penalty shot quality and the opposing team's prior average conceded-shot quality. Four league-average matches were used for shrinkage. The interaction test added their product. A sensitivity test replaced shots with explicitly identified rebound sequences. Standardisation and coefficient fitting used training seasons only; a fixed ridge penalty was used without a parameter search.

All methods below were tested on exactly the same fixtures. **Lower scores are better.**

| Method | H/D/A Brier | H/D/A log loss | Goal-count deviance | Blank Brier |
|---|---:|---:|---:|---:|
| Existing frozen v3 | 0.58450 | 0.98314 | 1.16525 | 0.18107 |
| v3 with fitted calibration only | 0.58509 | 0.98398 | 1.16645 | 0.18127 |
| Calibration + average chance quality | 0.58392 | 0.98205 | 1.16454 | 0.18157 |
| Quality + attack/defence interaction | 0.58409 | 0.98234 | 1.16477 | 0.18169 |
| Calibration + rebound-sequence quality | 0.58411 | 0.98236 | 1.16484 | 0.18150 |

The blank models were fitted separately from the goal-rate models, so their zero-goal probabilities need not equal the zero-goal probabilities implied by the H/D/A calculation.

Average chance quality improved H/D/A Brier from 0.58509 to 0.58392 against the equally calibrated control, about **0.20%**. Relative to the existing frozen v3, the improvement was about **0.10%**, from 0.58450 to 0.58392. This is a small gain.

The chance-quality model improved H/D/A probability scores against the calibrated control in all four seasons, and against raw frozen v3 in three of four. The extra attack/defence interaction did not improve on the simpler quality model. Handling rebound sequences gave a similar, slightly smaller aggregate gain.

| Test season | Matches | Control H/D/A Brier | With quality | Difference |
|---|---:|---:|---:|---:|
| 2020/21 | 306 | 0.60667 | 0.60588 | -0.00078 |
| 2021/22 | 350 | 0.57674 | 0.57568 | -0.00106 |
| 2022/23 | 353 | 0.58215 | 0.57999 | -0.00217 |
| 2023/24 | 351 | 0.57757 | 0.57695 | -0.00062 |

Calendar-week block bootstrap estimates (2,000 resamples) put the quality-versus-control H/D/A Brier difference at -0.00117, with an indicative 95% interval of -0.00232 to -0.00006. The interval for improvement in goal-count deviance crosses zero. Blank prediction was slightly worse overall: 0.18127 to 0.18157 against the calibrated control, and 0.18107 to 0.18157 against raw v3. The quality model's top-pick accuracy was 53.16%, versus 53.90% for frozen v3; accuracy was secondary to probability calibration.

These intervals are exploratory, not adjusted for multiple comparisons, and shared teams and overlapping historical windows create dependence beyond calendar weeks. This study also sits within the project's already-examined development seasons. The small secondary-metric improvements are not a clean independent validation of a new production model.

The 2024/25 archive fragment supplied a separate 43-match eligible check. Its H/D/A Brier improved from 0.58320 to 0.57921 against the calibrated control, while blank prediction worsened. That fragment is too small and early-season-specific to establish robustness. No 2025/26 stress-season forecast claim is made because the recent shot data did not meet the coverage rules.

## Rebounds explain an important xG distinction

Understat's raw shot probabilities do not always add to the displayed team xG. A shot followed by attempts explicitly labelled `lastAction=Rebound` forms a sequence. Applying `1 - product(1 - p)` to each such sequence reproduces **7,715 of 7,716 non-empty team-match totals** within 0.005. The sole exception is the incomplete match identified above. Zero-shot sides are handled as zero, not omitted.

For example, Swansea's 28th-minute sequence against Chelsea on 8 August 2015 contained chances around 0.312, 0.556 and 0.511. Their raw sum is about 1.379, while the chance of at least one goal in that sequence is about 0.851. Later attempts depended on earlier ones not scoring. Treating all three as independent opportunities available regardless of the earlier outcome would misrepresent the attack.

The primary features use explicitly labelled raw non-penalty shot quality; the sequence sensitivity excludes any complete sequence containing a penalty. Neither replaces the frozen baseline's xG values.

## Defence and goalkeeper conclusion

The simple matchup extension did not establish that a nominal 0.10 chance should receive a special multiplier against strong or weak opposition. It also does not isolate individual goalkeeper ability. A properly contextualised shot-stopping measure still requires trustworthy post-shot data and goalkeeper identity.

The pinned recent source includes per-shot xGOT and match-level xGOT, but consistency checks exposed a material limitation:

- For 2025/26, only **148 of 380 matches** passed xGOT reconciliation on both sides, including checks for missing on-target values. Forty matches had shot-derived score discrepancies and four had shot-count discrepancies. Strict combined shot/xG/score validation passed 111 matches.
- For 2026/27 through GW3, only **one of 30 matches** passed the same xGOT reconciliation on both sides. Eight had shot-count discrepancies. Strict combined shot/xG/score validation also passed one match.
- These gaps left no forecast rows satisfying the predefined complete-history rule for the recent pilot. No goalkeeper effect was fitted or claimed. Some xG differences can reflect rebound conventions, but unexplained shortfalls and xGOT discrepancies cannot safely be repaired by assuming that explanation.

The natural next data task is to reconcile the recent shot feed with its native match records and establish consistent goalkeeper identifiers. It is not necessary to alter existing live forecasts to investigate that.

## Recommendation and limits

Keep chance composition as a research/diagnostic view: volume, average quality, high-quality share, penalties and rebound sequences. Keep frozen v3 and the current Venue8 candidate unchanged. The study found a small probability-calibration signal but did not validate the proposed reduction in blanks or the individual goalkeeper adjustment.

Before any promotion, test against the current Venue8 candidate directly, obtain a complete later-season sample from a consistent provider, and require a meaningful gain on genuinely future or untouched data. Provider xG may have been revised retrospectively; the tests enforce chronological match inputs but cannot certify historical provider-model versions. Game state, red cards, shooter composition and changing tactics were not separately controlled. This study tests simple average-quality additions, not every possible distributional or tactical model.

## Reproducibility and verification

The accompanying `PL-Data-Hub-xG-research.zip` contains the protocol, scripts, source extracts, frozen baseline export, source manifest, full results, per-fixture predictions and numerical checks. It does not contain credentials. The original all-league Kaggle ZIP is omitted; only the EPL extracts needed to reproduce this study are included.

Verification passed: stopping input history at 31 December 2022 reproduced all 2,288 earlier feature rows exactly; changing test-season goals did not change fitted predictions; every model used the same fixtures; all 7,015 reported H/D/A probability rows summed to one; numerical distribution checks passed. No production database writes, model refreshes, deployments or GitHub pushes were performed.

Sources:

- [Cody Tipton's Understat player/game archive](https://www.kaggle.com/datasets/codytipton/player-stats-per-game-understat), the same archive used by the existing project importer. Downloaded ZIP SHA-256: `2d77fa250bdac756bdb15cc14bb1b6c2e3a8f925acd32f120318fb015245c4c0`.
- [Understat Chelsea–Swansea match](https://understat.com/match/86), checked against the archive's published match total.
- [FPL-Core-Insights pinned source](https://github.com/olbauday/FPL-Core-Insights/tree/f15bf7b6dea6cb441c2dc1ad9a02e4d9749cc68f), retrieved at commit `f15bf7b6dea6cb441c2dc1ad9a02e4d9749cc68f`; individual downloaded-file hashes are in the bundle.
- Frozen v3: read-only export of `public.betting_model_match_predictions` from the project's Supabase database on 10 September 2026. Project source checkpoint: `905a890861330242a215735cd14a268a35563183`.
