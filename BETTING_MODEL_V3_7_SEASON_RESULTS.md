# Betting Model v3 — seven-season validation

_Date: 2026-08-26_

This file extends `BETTING_MODEL_V3.md` with direct Football-Data.co.uk imports and frozen-v3 testing for 2019/20 through 2025/26.

## Frozen model

No model parameters were changed for these additional season tests.

- 30-match xG/goals core
- up to 65% xG / 35% actual goals
- 4 pseudo-match league-average shrinkage
- rolling home/away league baseline
- damped multiplicative attack/defence exponent 0.75
- PPG10 adjustment strength 0.14
- no betting recommendation if either club has fewer than 10 matches in its current PL spell
- independent Poisson score grid

## Football-Data imports

Supabase now contains complete Football-Data.co.uk opening/closing 1X2 and O/U 2.5 prices for:

- 2019/20 — 380 matches
- 2020/21 — 380 matches
- 2021/22 — 380 matches
- 2022/23 — 380 matches
- 2023/24 — 380 matches
- 2024/25 — 380 matches
- 2025/26 — 380 matches
- 2026/27 — 10 completed GW1 matches

The 2019/20–2021/22 files were fetched directly from Football-Data.co.uk by Supabase HTTP and audited at 380/380 canonical fixture mappings with zero missing opening/closing 1X2 or O/U 2.5 fields.

Official file MD5s:
- 2019/20: `763d5f1a0785bf9e95782a5dfe6bcbde`
- 2020/21: `f8a6fc6922c8108bbba96e5e59f53aaa`
- 2021/22: `488137517348e60f93b950f5a77585f8`

## Added season results

### 2019/20

Calibration:
- Model Brier: 0.58120
- Market Brier: 0.57500
- Model log loss: 0.97853
- Market log loss: 0.97310
- Eligible fixtures: 351

Average closing-price ROI:
- 0–2% edge: 32 bets, +24.3%
- 2–5% edge: 115 bets, +6.9%
- 5–10% edge: 127 bets, +30.7%
- 10%+ edge: 77 bets, -0.5%

### 2020/21

Calibration:
- Model Brier: 0.60115
- Market Brier: 0.59180
- Model log loss: 1.00887
- Market log loss: 0.99611
- Eligible fixtures: 352

Average closing-price ROI:
- 0–2% edge: 40 bets, +17.7%
- 2–5% edge: 108 bets, -7.6%
- 5–10% edge: 133 bets, +20.1%
- 10%+ edge: 71 bets, +13.8%

### 2021/22

Calibration:
- Model Brier: 0.57358
- Market Brier: 0.55412
- Model log loss: 0.96602
- Market log loss: 0.93670
- Eligible fixtures: 351

Average closing-price ROI:
- 0–2% edge: 38 bets, +49.3%
- 2–5% edge: 136 bets, -2.6%
- 5–10% edge: 120 bets, -24.0%
- 10%+ edge: 57 bets, -33.3%

## Seven-season aggregate

Across 2019/20–2025/26, after the 10-match eligibility gate:

| Model edge | Bets | Hit rate | ROI @ avg close | ROI @ best close | Positive seasons |
|---|---:|---:|---:|---:|---:|
| 0–2% | 268 | 32.8% | +0.6% | +8.4% | 3/7 |
| 2–5% | 844 | 33.3% | +3.6% | +11.3% | 4/7 |
| 5–10% | 879 | 30.9% | -2.6% | +4.0% | 3/7 |
| 10%+ | 472 | 26.3% | -10.4% | -3.8% | 1/7 |

Important interpretation:

- The closing bookmaker market remains better calibrated than v3 in every season tested.
- The 10%+ disagreement bucket is clearly harmful overall and positive in only 1/7 seasons at average closing prices.
- The 2–5% band is the best aggregate band, but it is not stable enough to call a durable system: it is positive in only 4/7 seasons.
- The seven-season +3.6% average-close ROI for 2–5% is heavily influenced by 2022/23 (+41.9%). Removing 2022/23 leaves the other six seasons negative overall (approximately -2.6% weighted ROI based on the season-level results).
- Therefore, do not optimise v3 around a fixed edge threshold. The next work should explain *why* the model and market disagree, not simply bet whenever edge exceeds X.

## Current direction

1. Keep the promoted/returning-team 10-match betting gate.
2. Keep PPG10 as a validated calibration improvement.
3. Treat very large model-market disagreement as a warning/manual-review flag rather than stronger confidence.
4. Add an opponent-adjusted persistent team-strength/Elo-style feature.
5. Segment historical disagreements by cause: xG advantage, PPG advantage, attack/defence balance, home/away, price range and underdog/favourite status.
6. Test whether underdog disagreement is more useful in handicap/double-chance markets than outright 1X2.
