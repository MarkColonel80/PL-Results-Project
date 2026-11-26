# GW12 odds and provisional value research — Thursday 26 November 2026

UK comparison prices **observed 2026-11-26T23:54:58Z** for the Premier League fixtures 27–29 November. Sources: [Oddschecker UK](https://www.oddschecker.com/football/english/premier-league), cross-checked with [BetVictor's named-bookmaker public 1X2 page](https://www.betvictor.com/en-gb/sports/240/meetings/6323610/all). Prices may move, come from different bookmakers, and are **not confirmed executable** at one named bookmaker.

## Saved 1X2 comparison odds

| Kick-off (GMT) | Fixture | Home | Draw | Away |
| --- | --- | ---: | ---: | ---: |
| 11-27 20:00 | Nottingham Forest – Chelsea | 2.60 | 3.50 | 2.90 |
| 11-28 15:00 | Leeds United – Coventry City | 1.51 | 4.75 | 6.60 |
| 11-28 15:00 | Manchester United – Brentford | 2.15 | 3.80 | 3.40 |
| 11-28 17:30 | Ipswich Town – Aston Villa | 3.80 | 3.90 | 2.00 |
| 11-29 12:00 | Everton – Liverpool | 4.75 | 3.90 | 1.80 |
| 11-29 14:05 | Brighton & Hove Albion – Newcastle United | 1.60 | 4.50 | 5.75 |
| 11-29 14:05 | Crystal Palace – Hull City | 1.95 | 3.90 | 4.30 |
| 11-29 14:05 | Fulham – AFC Bournemouth | 2.75 | 3.55 | 2.64 |
| 11-29 14:05 | Sunderland – Tottenham Hotspur | 3.90 | 3.50 | 2.10 |
| 11-29 16:30 | Arsenal – Manchester City | 2.00 | 3.80 | 3.85 |

All ten quoted triples are now stored in `betting_manual_fixtures` with observation time/source. Pre-match predictions were calculated **2026-11-24 14:06:56 GMT** and were not recalculated today. Existing records are read via the page's standard Supabase query.

## Leading positive price gaps (research model only)

| Fixture | Outcome | Odds | Saved chance | Model gap vs break-even | xG-only sensitivity |
| --- | --- | ---: | ---: | ---: | --- |
| Everton v Liverpool | home | 4.75 | 36.1% | +15.0pp | Yes |
| Ipswich Town v Aston Villa | home | 3.80 | 40.2% | +13.9pp | Yes (18-match unavailable) |
| Sunderland v Tottenham Hotspur | home | 3.90 | 37.6% | +11.9pp | Yes |
| Nottingham Forest v Chelsea | home | 2.60 | 49.3% | +10.8pp | No |
| Crystal Palace v Hull City | away | 4.30 | 30.5% | +7.3pp | Yes (18-match unavailable) |
| Leeds United v Coventry City | draw | 4.75 | 26.0% | +5.0pp | Yes (18-match unavailable) |
| Sunderland v Tottenham Hotspur | draw | 3.50 | 33.0% | +4.4pp | Yes |
| Brighton & Hove Albion v Newcastle United | home | 1.60 | 65.2% | +2.7pp | No |

This table is **not a list of approved paper selections** and not a validated profitability claim. All are from comparison prices. Threshold odds = reciprocal of the saved research probability; a positive simple gap is not proof of an exploitable edge. The cumulative research Brier score is `0.6258` on 65 eligible frozen forecasts, while the saved no-vig market scores `0.6231` (lower is better).

### Prioritised provisional watches and risk review

1. **Everton home v Liverpool (4.75):** research 36.1%; model gap +15.0 percentage points. Current view 31.5%, xG8 33.2%, xG18 27.8%: all remain positive at the aggregated price. But Everton officially lost captain James Tarkowski to suspension; Liverpool report Gakpo out, Gravenberch uncertain and Munoz needing assessment following Wednesday's Champions League fixture. BetVictor's own displayed home price was **3.60**, around the most conservative sensitivity break-even price. [Everton FC](https://www.evertonfc.com/players/injuries--suspensions) / [Liverpool FC](https://www.liverpoolfc.com/news/liverpools-injury-list-suspensions-and-availability).
2. **Ipswich home v Aston Villa (3.80):** research 40.2%, +13.9pp; current 34.3%, xG8 32.1%. Five relevant Ipswich home matches, with **no full Venue18**, meaning higher model uncertainty. Davis fitness remains uncertain; Villa have Onana/Ruggeri out and travelled to Galatasaray on Tuesday, with Cash's return to verify. Public BetVictor displayed **3.10**, below even the xG8-only sensitivity break-even. [Villa FC](https://www.avfc.co.uk/news/2026/november/23/prematch-team-news-for-galatasaray-encounter/) / [Ipswich injury listing](https://www.premierinjuries.com/teams/ipswich-town).
3. **Sunderland home v Spurs (3.90):** research 37.6%, +11.9pp; current 31.0%, xG8 and xG18 both 39.9%. All comparisons remain positive at the aggregate price. Thursday Europa League participation shortens recovery; Xhaka and Brobbey were out Thursday but are under review for Sunday. BetVictor publicly displayed **3.20**, marginally below the current-view sensitivity break-even (~3.23). [Sunderland AFC](https://www.safc.com/news/2026/november/25/le-bris-provides-team-news-ahead-of-jagiellonia/).
4. **Nottingham Forest home v Chelsea (2.60):** research 49.3%, +10.8pp and current view 43.1%, xG8 46.9%. But xG18 is only 35.2%, **below** the 38.5% chance needed at 2.60; this is a fragile price gap. Chelsea confirm Caicedo available while Joao Pedro and Lacroix are out. Friday kickoff means review of named-bookmaker prices and teams is time-sensitive. [Chelsea FC](https://www.chelseafc.com/en/news/article/xabi-alonso-confirms-chelsea-team-news-for-nottingham-forest).
5. **Hull away v Crystal Palace (4.30):** research 30.5%, +7.3pp, current 35.4%, xG8 31.3%; but Hull has only five relevant away matches, no full Venue18. Palace have Mateta/Pino suspended and Sarr injured, but Hull also report absences. Thursday Europe/recovery remains a concern. Not preferred over more fully sampled watches. [Palace update](https://ca.sports.yahoo.com/news/frank-team-news-sarrs-commitment-190738489.html).

### Selection gates and preserved rules

- **No new paper bets.** The pre-existing 69 events have no paper selections or settlements. No outcomes were converted from a watch/pass into a one-unit stake.
- Current official starting XIs, directly available **named-bookmaker** quotes, final club news, recent European recovery/minutes and history/sensitivity checks are still prerequisites. Do not invent or backfill a selection.
- BetVictor odds are posted publicly but are shorter than the aggregators' maximum prices; they are not treated as confirmation that a different advertised maximum is available to this user. Notably the three largest apparent opportunities are not decisively robust at the BetVictor example price.
- Last 24 Nov refresh has **110 completed results, 4,400 rich player rows and 7,236 FPL rows**; historical model and feature caches unchanged. Understat mapping and Transfermarkt gaps remain.
- Previous fixture MD5 47aae8f7d6d835df6427c9c590d7bcb9, all snapshots 02f355d01a6ed0c7eb2f23ed4e8b7867, frozen v3 f3097c1d21be5443c3c6790ece2c29dd and existing security policy fingerprints 988e388d687556eb705513d4864307bc retained. Only GW12 quote/source/time and five appended news records changed (GW12 MD5 6f0774c2bd71afcc8b27b8d0a07122ce -> dca9a2f13b4845e7e74d9e4fd88b5fd4). Prior notes retained verbatim; frontend reads the latest valid `WEEKEND_NEWS_JSON:` record for five fixtures. Rest of the original Tuesday news remains dated as such.
- Existing Tuesday schedule `6ad7a14d306c8190b719bd87b6f73e7d` is unchanged; no new workflow, model, selection, staking or eligibility rule was introduced.

Machine-readable evidence: [GW12 late-November comparison record](data/weekend-2026-11-26-price-value-review.json). GitHub commit/deployment checks are recorded separately.
