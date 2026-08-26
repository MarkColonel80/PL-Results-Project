# Betting Model v3 — validation checkpoint

_Date: 2026-08-26_

## Why v3 exists

Model v2's largest model-v-market disagreements were often implausible large-underdog bets. Manual review found two structural issues:

1. promoted/returning clubs had insufficient current-Premier-League evidence, and
2. the model did not give enough persistent credit to teams that were consistently getting results.

A separate data bug was also fixed: 2024/25 xG was present in `fpl_player_match_stats` for all 380 matches, but the v2 betting view originally read only `player_match_stats`, where 2024/25 Transfermarkt rows have no xG. The corrected betting layer falls back to FPL xG when canonical/advanced xG is unavailable.

## Frozen v3 specification

Core remains the v2 football model:

- 30-match team attack/defence history
- team signal up to 65% xG and 35% actual goals, scaled down only when xG coverage is incomplete
- 4 pseudo-matches of league-average shrinkage
- rolling league home/away scoring baseline
- damped multiplicative attack × opponent-defence strength, exponent 0.75
- independent Poisson score grid
- no Dixon-Coles correction

v3 additions:

### Last-10 PL points signal

`betting_team_features_v3_cache` stores pre-match points per game over the previous 10 Premier League matches (`ppg10`).

The PPG adjustment strength was selected using **2019/20–2023/24 only**. Tested strengths showed:

- no PPG adjustment: Brier 0.58288, log loss 0.98097
- 0.06: Brier 0.58045, log loss 0.97727
- 0.10: Brier 0.57975, log loss 0.97609
- **0.14: Brier 0.57974, log loss 0.97593**
- 0.18: Brier 0.58039, log loss 0.97679

Frozen PPG strength: **0.14**.

Implementation adjusts the frozen v2 lambdas symmetrically:

- home lambda multiplier: `exp(0.14 * (home_ppg_smoothed - away_ppg_smoothed))`
- away lambda multiplier: `exp(-0.14 * (home_ppg_smoothed - away_ppg_smoothed))`

PPG is shrunk toward 1.35 using four pseudo-matches, so very small samples do not dominate.

### Promoted/returning-team betting gate

The model may still calculate probabilities, but **no betting edge/recommendation is issued if either club has fewer than 10 matches in its current Premier League spell**.

The current-spell segment resets after a long PL absence. This blocks promoted/returning teams until they have played 10 PL matches.

This is a betting eligibility gate, not a statement that their fixtures should be removed from probability modelling.

## Football-Data odds state

`historical_market_odds` now contains:

- 2024/25: 380 matches, complete opening/closing 1X2 and O/U 2.5
- 2025/26: 380 matches, complete opening/closing 1X2 and O/U 2.5
- 2026/27: 10 completed GW1 matches

The user-uploaded 2024/25 CSV had MD5 `fb2274f034494fe61f451c3ad2a39d92`; the official Football-Data URL fetched from Supabase returned the same MD5, confirming an exact file match.

For 2024/25, `historical_market_odds.match_id` remains NULL because that column is FK-linked to the newer `matches` table, whose IDs do not cover older canonical fixture IDs. Back-tests map 2024/25 odds deterministically by season + normalised home/away pairing. Each pairing is unique.

## 2025/26 v3 rerun

All 380 matches:

- Model Brier: **0.61900**
- Closing no-vig market Brier: **0.60774**
- Model log loss: **1.03033**
- Closing market log loss: **1.01177**

Eligible after promoted/returning gate: **352 matches**.

Strongest model-v-market edge per eligible match, flat £1 at average closing odds:

- 0–2%: 32 bets, **-29.0% ROI**
- 2–5%: 132 bets, **+11.8% ROI**
- 5–10%: 133 bets, **+1.2% ROI**
- 10%+: 55 bets, **-30.6% ROI**

The model still does not beat the closing market overall. Large claimed edges remain a warning area.

## 2024/25 independent bookmaker test

This season's bookmaker performance was not used to choose the 0.14 PPG strength or the 10-game gate.

All 380 matches with v3:

- Model Brier: **0.58374**
- Closing no-vig market Brier: **0.57519**
- Model log loss: **0.98054**
- Closing market log loss: **0.96673**

Without the PPG10 correction on the same season:

- Model Brier: **0.58862**
- Model log loss: **0.98851**

So PPG10 improved both calibration measures out-of-sample, although the bookmaker market remained better.

Eligible after promoted/returning gate: **353 matches**.

Strongest edge per eligible match, flat £1 at average closing odds:

- 0–2%: 40 bets, **-22.6% ROI**
- 2–5%: 114 bets, **+5.6% ROI**
- 5–10%: 130 bets, **-5.6% ROI**
- 10%+: 69 bets, **-0.2% ROI**

Using best closing prices instead:

- 0–2%: -17.1%
- 2–5%: **+12.2%**
- 5–10%: -1.2%
- 10%+: **+6.9%**

## Independent validation of the 10-game gate

The 27 blocked 2024/25 fixtures performed poorly at average closing prices:

- blocked 0–2%: 4 bets, +17.5%
- blocked 2–5%: 11 bets, **-26.6%**
- blocked 5–10%: 7 bets, **-32.7%**
- blocked 10%+: 5 bets, **-100.0%**

This supports keeping the promoted/returning-team gate.

## Current interpretation

- PPG10 is a validated improvement to football probability calibration on 2024/25.
- The promoted/returning-team gate is independently supported by 2024/25 betting outcomes.
- The **2–5% edge band is the only band positive at average closing prices in both 2024/25 and 2025/26** under v3.
- Do not optimise the model specifically to that band. 2025/26 influenced the qualitative v3 design, and two seasons are not enough to claim a durable betting edge.
- The closing bookmaker market remains better calibrated than the model overall.
- Large model-market disagreements should continue to receive manual/common-sense scrutiny, especially long-priced underdogs.

## Next modelling work

1. Import additional older bookmaker seasons and run the frozen v3 model unchanged.
2. Evaluate the 2–5% band across more independent seasons.
3. Add a persistent opponent-adjusted team-strength/Elo-style signal rather than relying only on raw PPG.
4. Investigate handicap/double-chance markets when the model thinks an underdog is underrated; the signal may be about match closeness rather than outright-win probability.
5. Keep lineup/injury/transfer information as a known missing input for later versions.
