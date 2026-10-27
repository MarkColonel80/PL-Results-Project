# Post-GW8 review — Tuesday 27 October 2026

## Actual paper outcome

**0 valid paper selections, 0 stake units, 0 profit units; ROI is undefined.** All 29 recorded GW8 ledger events were watch/pass. There are no recorded Saturday/Sunday final selections to settle. Do not manufacture a retrospective pass, stake or selection. The missing matchday final checks are a process gap, not a betting loss or profit.

## Results and frozen forecasts

All ten GW8 results are verified against official FPL and native Fotmob. Seven forecasts met the four-match relevant-venue gate; Ipswich–Forest, Coventry–Fulham and Hull–Brentford were LIMITED_HISTORY and remain unscored for probabilities. Every saved forecast was reviewed, including these explicit exclusions. Historical features, snapshots and probabilities were not changed.

| Fixture | Result |
|---|---|
| Manchester United – AFC Bournemouth | 0–3 |
| Ipswich Town – Nottingham Forest | 1–1 |
| Liverpool – Brighton & Hove Albion | 2–0 |
| Chelsea – Tottenham Hotspur | 0–2 |
| Crystal Palace – Newcastle United | 0–2 |
| Coventry City – Fulham | 0–1 |
| Hull City – Brentford | 1–1 |
| Arsenal – Everton | 2–0 |
| Sunderland – Leeds United | 0–0 |
| Aston Villa – Manchester City | 2–1 |

Scores use mean unscaled three-outcome Brier and natural-log loss; lower is better. Accuracy is the most-probable H/D/A outcome, separate from a correct exact score. Current probabilities are reproduced from frozen inputs using the existing page's 0–8 Poisson truncation; the preceding 28-forecast metrics were reproduced before adding GW8. Research probabilities are the original stored candidate values; market probabilities remove the margin from saved pre-match prices.

| Sample / model | N | Brier | Log loss | Top outcome accuracy |
|---|---:|---:|---:|---:|
| GW8: research | 7 | 0.688827 | 1.121047 | 14.3% |
| GW8: current | 7 | 0.671805 | 1.099895 | 14.3% |
| GW8: market | 7 | 0.664427 | 1.095499 | 42.9% |
| All saved eligible rounds: research | 35 | 0.651266 | 1.072528 | 28.6% |
| All saved eligible rounds: current | 35 | 0.666681 | 1.092500 | 34.3% |
| All saved eligible rounds: market | 35 | 0.628305 | 1.041411 | 45.7% |

The market benchmark beat both models on GW8 and cumulatively. This is 35 eligible forecasts across 50 published fixtures in GW3, GW4, GW6, GW7 and GW8, not a demonstrated betting edge. GW8 had one actual score in the research top three among seven eligible forecasts. Individual forecast scores, forecast/market timestamps, actual results and exclusions are in `data/weekend-2026-10-23-settlement.json`; the filename denotes the forecast weekend archive and includes the complete historical scoring audit.

Model calibration, shrinkage, draw treatment and selection rules remain research questions. No approved model, betting rule, cap, probability weight, history threshold or frozen v3 prediction was changed.

## Next round

See [GW9 provisional review](WEEKEND_2026-10-31.md) for all ten future fixtures, probabilities, scorelines, prices, official availability flags, cup schedule and five watch/five pass reviews. The ledger now has 39 events, preserving the exact first 29. All new official-XI checks are pending. No selections, stakes or settlement events were added.

## Delivery

See [refresh report](DATA_REFRESH_2026-10-27.md) and `data/full-refresh-2026-10-27-checkpoint.json` for source coverage, safety checks, validation and release status.
