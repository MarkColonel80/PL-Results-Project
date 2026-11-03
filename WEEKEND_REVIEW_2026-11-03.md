# Post-weekend review — 3 November 2026

Reviewed at 2026-11-03T12:10:06Z. Full GW9 (31 October–2 November), including Monday's Newcastle–Everton fixture, verified finished against official FPL and native Fotmob reports. This review uses the immutable pre-match 27 October archive; no played prediction was recalculated.

| Fixture | Result | Recorded Tuesday decision |
|---|---:|---|
| Chelsea v Manchester United | 2–0 | watch |
| AFC Bournemouth v Leeds United | 2–0 | watch |
| Brentford v Nottingham Forest | 2–0 | pass |
| Coventry City v Sunderland | 3–1 | pass |
| Hull City v Ipswich Town | 2–2 | watch |
| Manchester City v Brighton & Hove Albion | 0–1 | watch |
| Tottenham Hotspur v Crystal Palace | 2–0 | watch |
| Aston Villa v Fulham | 1–1 | pass |
| Liverpool v Arsenal | 0–1 | pass |
| Newcastle United v Everton | 0–1 | pass |

## Frozen forecast scorecard

All ten GW9 forecasts were eligible. Mean unscaled three-outcome Brier and natural-log loss; lower is better. Market probabilities normalize the archived 27 October H/D/A prices, not later closing prices.

| Forecast | GW9 Brier | GW9 log loss | GW9 top-outcome accuracy | Cumulative Brier | Cumulative log loss |
|---|---:|---:|---:|---:|---:|
| research | 0.615744 | 1.023246 | 50.0% | 0.643372 | 1.061576 |
| current | 0.652755 | 1.070527 | 40.0% | 0.663587 | 1.087617 |
| market | 0.600143 | 1.006224 | 50.0% | 0.622047 | 1.033592 |

Cumulative: 45 eligible of 60 published forecasts across rounds 3, 4, 6, 7, 8 and 9. Research top-outcome accuracy 15/45; current 16/45; saved market 21/45. Research top-three exact scores hit 3/10 this round. These small samples do not establish profitability; market still leads both proper scores.

## Paper ledger and watches

Zero valid recorded paper selections, zero settled/pending stakes, zero units staked, zero profit; ROI undefined (not 0% or a winning return). Existing 39 events and all original fixture/settlement entries are preserved. No settlement event was invented.

The five watches were United away (lost 0–2), Bournemouth home (won 2–0), Hull home (drew 2–2: a home-win watch did not win), Brighton away (won 1–0), Palace away (lost 0–2). Two winning watched outcomes are not two winning paper bets. Arsenal and Everton won from pass fixtures; neither can be backfilled.

No subsequent pre-kickoff ledger record confirms official XIs plus a named, available bookmaker quote and the required checks. Post-match lineups are now verified but cannot supply retrospective selection evidence. Cup/Europe minutes, injuries or rotation may be context; this dataset does not establish them as the cause of any result. The recorded Hull partial-history warning and earlier sensitivity warnings remain applicable.

## Closing-price coverage

All ten Football-Data GW9 closing-average/maximum triples match the current public CSV (fetched 3 November; source Last-Modified 09:45:04 GMT). For the watches, later cross-provider closing averages/maxima were: United 3.07/4.00 (saved coupon 4.10), Bournemouth 2.05/2.12 (2.15), Hull 2.88/3.00 (2.625), Brighton 4.36/4.50 (4.60), Palace 4.91/5.75 (6.00).

These are different providers/price constructions, without matched bookmaker/executable observation timestamps. They are contextual movement only, not comparable bet-level CLV, proof that a saved price remained available, or retrospective profit. Full sourced close data are in the dated settlement archive.

## Findings and proposals

The supported process failure is incomplete publication after partial imports; the cloud recovery reconciled existing records rather than duplicating them. Model variance alone is not a data defect. Preserve the current models, minimum-four venue gate, one-unit paper contract and all selection rules.

Proposal only: collect comparable named-bookmaker opening/closing quotes and pre-kickoff evidence consistently, then evaluate calibration and sensitivity on a larger frozen out-of-sample set. Any thresholds, weighting, eligibility or staking changes require Mark's approval first. No such change is applied here.

Sources: [official FPL fixtures](https://fantasy.premierleague.com/api/fixtures/), [FPL GW9 live statistics](https://fantasy.premierleague.com/api/event/9/live/), native Fotmob match reports 5795495–5795504, [Football-Data CSV](https://www.football-data.co.uk/mmz4281/2627/E0.csv). Next round: [6–8 November review](WEEKEND_2026-11-06.md). Operational investigation: [Tuesday reliability](TUESDAY_AUTOMATION_2026-11-03.md).
