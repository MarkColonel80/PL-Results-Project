# Close-game confidence / game-state experiment — 2026-09-07

## Purpose

Test the hypothesis that when Premier League teams are structurally fairly close, recent evidence of confidence/decisiveness may add predictive information beyond underlying xG/team strength.

The live `v3_24_venue8_50_noppg` candidate was left unchanged throughout.

## Historical proxy test: recent results in close-score games

Because detailed historical goal-state event timing is only complete from 2025/26 onward, the six-season development test first used a deliberately simple proxy:

- current match considered close when base home-vs-away win probability gap was <= 10pp, 15pp or 20pp
- for each team, look back at the last 4, 6 or 8 same-season matches that finished within one goal
- encode those historical close-score results as +1 win / 0 draw / -1 loss
- shrink the recent score toward neutral with four pseudo-observations
- adjust only home-vs-away relative probability in the current close match; leave the draw probability structurally untouched before renormalisation
- test small adjustment strengths (`beta`) from 0 to 0.50

Development sample remained the current 24-match + Venue8 GW15+ research sample, seasons 2019/20–2024/25, n=1,433.

Best in-sample development combination was approximately:
- current close threshold: 20 percentage points
- recent close-score window: 6
- beta: 0.15
- Brier 0.574553 vs base 0.574742
- log loss 0.968890 vs base 0.969079

The apparent gain was tiny.

### Season-by-season fixed-rule result

For the simple 20pp / last-6 / beta 0.15 version:

- 2019/20: Brier improved by 0.000435
- 2020/21: worsened by 0.000034
- 2021/22: worsened by 0.000928
- 2022/23: improved by 0.000226
- 2023/24: improved by 0.001495
- 2024/25: worsened by 0.000070
- 2025/26 stress season: improved by 0.000564

This was mixed and not sufficiently stable.

### Leave-one-season-out validation

A stricter test allowed the close threshold, history window and beta to be chosen only on the other five development seasons, then applied untouched to the held-out season.

Held-out Brier deltas vs base:

- 2019/20: +0.000122 (worse)
- 2020/21: +0.001101 (worse)
- 2021/22: +0.001780 (worse)
- 2022/23: -0.000226 (better)
- 2023/24: +0.000157 (worse)
- 2024/25: +0.000641 (worse)

Combined leave-one-season-out result across 1,433 matches:
- base Brier: 0.574742
- adjusted Brier: 0.575338
- delta: +0.000597 (worse)
- base log loss: 0.969079
- adjusted log loss: 0.969981
- delta: +0.000902 (worse)

**Decision:** reject recent close-score result form as a confidence feature. It behaves like noisy result form and does not generalise.

## Rich game-state exploratory test — 2025/26 only

The 2025/26 event dataset contains sufficient goal-state history for all 380 league matches, including goalless matches. This allowed a more direct exploratory proxy for the behaviour Mark described.

For each team, before each close structural matchup, the last eight same-season games were used to estimate three heavily shrunk behaviours:

1. **Comeback salvage:** after conceding first, did the team recover a draw or win?
2. **Lead conversion:** after scoring first, did the team win?
3. **Late response:** after minute 70, did the team score from a non-winning position to get level or go ahead?

Each rate was shrunk with four pseudo-observations toward the leakage-safe league-to-date rate. The three rates were averaged into a simple exploratory confidence index.

The test was restricted to the 111 2025/26 GW15+ candidate matches where the base home-vs-away win-probability gap was <=20 percentage points.

### Directional evidence

Splitting matches into thirds by home-minus-away confidence index:

- bottom third: average confidence differential -0.108; actual signed result underperformed base expectation by about -0.069
- middle third: average confidence differential +0.004; actual signed result outperformed base by about +0.061
- top third: average confidence differential +0.113; actual signed result outperformed base by about +0.128

Overall correlation between confidence differential and result residual was positive but weak: about +0.094.

### Small fixed probability adjustment

Without optimising beta to this season, modest positive adjustments moved the 111-match close-subset scores in the expected direction:

| Beta | Brier | Log loss | Top-pick accuracy |
|---:|---:|---:|---:|
| 0.00 (base) | 0.645368 | 1.068412 | 41.44% |
| 0.10 | 0.644754 | 1.067630 | 41.44% |
| 0.15 | 0.644469 | 1.067268 | 41.44% |
| 0.20 | 0.644198 | 1.066926 | 41.44% |

This is interesting directional evidence, but it is **one season only** and therefore not valid model-selection evidence.

## Interpretation

Two distinct ideas should not be confused:

- **Recent close-game result form** is not robust and is rejected.
- **Actual game-state behaviour** (recovering after conceding, converting leads, late equalising/go-ahead responses) is more aligned with the football hypothesis and showed a small promising signal in the one season where full event history exists.

The second idea is worth collecting prospectively, but not yet worth adding to the live probability model.

## Decision

**No live model change.**

Keep `v3_24_venue8_50_noppg` unchanged.

Continue accumulating current-season event data and revisit once multiple full seasons of comparable goal-state data are available, or if an older reliable event source can be added without compromising provenance. A future test should remain close-match-only, heavily shrunk, leakage-safe, and must beat the base model out of sample before promotion.
