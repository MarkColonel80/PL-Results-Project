# Weekend value review 17 to 19 October 2026

Both leading value ideas lost: Forest–Arsenal draw at 4.00 and Palace to win at Brighton at 6.00. Hypothetical equal one-unit stakes would have lost two units. These were conditional watchlist ideas, with no recorded promotion to paper selections or confirmed bets; their losing outcomes remain recorded without retrospective exclusions.

## Settled watchlist

| Pre-match idea | Saved odds | Result | Settlement |
| --- | ---: | --- | --- |
| First watch: Forest–Arsenal draw | 4.00 | Forest 0–1 Arsenal | Lost |
| Second, conditional: Palace win at Brighton | 6.00 | Brighton 5–0 Palace | Lost |
| Alternative in that same match: Brighton–Palace draw | 4.75 | Brighton 5–0 Palace | Lost |
| Lower priority: United win at Leeds | 3.00 | Leeds 1–1 United | Lost |

The morning investigation’s earlier Brentford-win watch at 2.50 also lost, 1–2. It is separate from the later two-item shortlist. The later review passed the Leeds–United draw because its small price advantage failed some sensitivity checks; the eventual 1–1 is not backfilled as a selection. The Brighton–Palace draw was an alternative, not an independent additional primary pick.

The original timestamped [watchlist](data/weekend-2026-10-17-watchlist.json) is preserved exactly. The [settlement](data/weekend-2026-10-17-settlement.json) retains both forecast views, prices, results, metric definitions and its original SHA-256 fingerprint. All 40 database fixture/snapshot records remain unchanged.

## What happened in the two main games

Forest–Arsenal was a low-scoring game: Understat reports **0.75–0.92 xG**, and Arsenal scored in the 80th minute. That fits the low-total premise but is a losing draw bet. Gibbs-White was absent and Milenković was on the bench, making the pre-match availability concerns relevant. There is no recorded final-lineup follow-up; none is invented after the result. [Opta match report](https://theanalyst.com/articles/nottingham-forest-vs-arsenal-stats-premier-league-10-2026).

Palace were comprehensively beaten. Brighton led 3–0 after ten minutes; the native report records 17–5 shots and 9–1 on target. Understat reports **2.25–0.63 xG**. Benítez started in goal with Henderson absent, and Mateta came on in the 61st minute. Those were live pre-match uncertainties, but they do not create an unrecorded decision to pass. [Match report](https://www.skysports.com/football/brighton-and-hove-albion-vs-crystal-palace/report/559506).

The xG figures above are published Understat match totals, not summed mixed-provider player xG or replacement pre-match probabilities. The 5–0 score includes an own goal and early score-state changes; it is not five expected goals.

## Every eligible forecast

All seven eligible frozen H/D/A forecasts are scored against their actual outcomes and the no-vig market probabilities from the same saved pre-match fixture records. Fulham–Hull, City–Ipswich and Spurs–Coventry remain excluded because their forecasts were suppressed for limited history.

| Forecast | Matches | Mean Brier score | Mean log loss | Top outcome correct |
| --- | ---: | ---: | ---: | ---: |
| Current weekend view | 7 | 0.6475 | 1.0601 | 3/7 |
| 24-match + Venue8 research | 7 | 0.5700 | 0.9583 | 3/7 |
| Saved market, no-vig | 7 | **0.5056** | **0.8731** | **4/7** |

Lower scores are better. Brier is the unscaled sum over three outcomes, averaged across matches; log loss uses natural logarithms. The market performed better than either model this round. Seven matches do not establish calibration or long-term profitability. Shared inputs also mean the two model views are not independent validation.

Research’s most likely outcomes were correct for Bournemouth, Brighton and Arsenal. That does not rescue the value ideas: forecasts can favour one result while a price comparison suggests another outcome is underpriced.

## Prices and process

Football-Data’s average closing prices were 4.16 for the Forest–Arsenal draw and 6.62 for Palace away. The earlier watchlist used Oddschecker coupon prices of 4.00 and 6.00. Different bookmaker pools and aggregation mean this is not a matched-bookmaker closing-line comparison. Neither conditional idea has a recorded executable quote or lineup-based promotion to a paper selection.

For future reviews, retain the existing requirement to check confirmed teams and an available price, then record an explicit watch, paper selection or pass before kick-off. A large mathematical price gap with unresolved squad concerns should remain conditional. Keep the original assessment and append any later decision with its own timestamp. These results do not justify changing weights or choosing whichever diagnostic would have predicted them best.

## Complete round

Everton 0–2 Chelsea; Brentford 1–2 Liverpool; Fulham 1–0 Hull; City 3–2 Ipswich; Newcastle 0–1 Villa; Bournemouth 2–0 Sunderland; Brighton 5–0 Palace; Leeds 1–1 United; Forest 0–1 Arsenal; Spurs 3–1 Coventry. [Official results](https://www.premierleague.com/en/matches/premier-league/2026-27/matchweek-7).
