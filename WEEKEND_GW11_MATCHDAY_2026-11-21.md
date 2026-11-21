# GW11 match-day odds and team-news refresh — 21 November 2026

**Database update saved:** 2026-11-21T11:04:02Z (GMT), before the first Saturday kick-off. Matches 101–110 only. The official 21–23 November GW11 kick-offs were matched by teams, date and manual fixture IDs.

## Saved public comparison odds

These are **best advertised cross-bookmaker 1X2 prices**, not guaranteed executable named-bookmaker quotes or a complete matched-bookmaker market. The source updates continuously; these are the observed values at 2026-11-21T11:04:02Z. No selection or real-money bet follows from a green price gap.

| UK kickoff | Fixture | Home | Draw | Away |
| --- | --- | ---: | ---: | ---: |
| 11-21 12:30 GMT | Manchester City v Fulham | 1.42 | 5.80 | 8.80 |
| 11-21 15:00 GMT | Aston Villa v Sunderland | 1.82 | 4.07 | 5.00 |
| 11-21 15:00 GMT | AFC Bournemouth v Nottingham Forest | 2.00 | 3.73 | 4.30 |
| 11-21 15:00 GMT | Chelsea v Leeds United | 2.10 | 3.75 | 3.97 |
| 11-21 15:00 GMT | Coventry City v Crystal Palace | 2.60 | 3.72 | 2.96 |
| 11-21 15:00 GMT | Tottenham Hotspur v Ipswich Town | 1.55 | 4.88 | 6.60 |
| 11-21 17:30 GMT | Newcastle United v Arsenal | 6.40 | 4.41 | 1.62 |
| 11-22 14:00 GMT | Hull City v Brighton & Hove Albion | 7.00 | 4.60 | 1.56 |
| 11-22 16:30 GMT | Liverpool v Manchester United | 1.76 | 4.50 | 4.75 |
| 11-23 20:00 GMT | Brentford v Everton | 2.24 | 3.82 | 3.55 |

Sources: [OddStorm public Premier League comparison](https://www.oddstorm.com/odds/league/325-england-premier-league); [official November fixture amendments](https://www.premierleague.com/en/news/4725574). OddStorm also displayed an apparent duplicate Brentford–Everton row on Sunday; only the **official Monday 23 November 20:00** entry was used.

## New match-day team-news context

The 20 November [official PL predicted-lineups review](https://www.premierleague.com/en/news/4764715) covers all 20 clubs and embeds managers' availability comments; the [official injury register](https://www.premierleague.com/en/latest-player-injuries/) showed a 21 November 10:10 GMT update. Every original 17 November FPL note remains in the database, followed by a dated 21 November append-only news record for the same fixture. The UI shows the last valid record.

- **Manchester City–Fulham:** Khusanov/Nunes doubts; Guehi likely available; Semenyo out; Smith Rowe out; Cairney fit; attacking starter undecided.
- **Aston Villa–Sunderland:** Cash out; Wan-Bissaka available, Manzambi fit; Brobbey and Xhaka out; Ballard, Mundle, Diarra out.
- **AFC Bournemouth–Nottingham Forest:** Kroupi ready; Alex Scott gradual return; Hudson-Odoi/Dominguez out; Schlager/Williams doubts.
- **Chelsea–Leeds United:** Joao Pedro/Lacroix/Hato out; Caicedo, Acheampong, Martinez fit; Manager reports no new injuries; Stach, Okafor, Rodon available.
- **Coventry City–Crystal Palace:** Bobby Thomas training but doubtful; Yirenkyi uncertain; Mateta suspended; Sarr/Tomiyasu out; Larsen status unclear; new manager.
- **Tottenham Hotspur–Ipswich Town:** Savio/Maddison/Bergvall/Udogie available; Tel/Tosin out; Manager reports all 27 fit; XI choices open.
- **Newcastle United–Arsenal:** Joelinton out; Ramsey returns from ban; Livramento in squad; Saliba fit; Zubimendi out; Saka out for longer.
- **Hull City–Brighton & Hove Albion:** Mendy/Belloumi fit; Crooks ban served; Andres likely fit; Kadioglu back; Minteh fine; Azeez available.
- **Liverpool–Manchester United:** Van Dijk/Gravenberch/Frimpong/Szoboszlai expected available; Maguire/Dorgu available; Heaven doubtful; Martinez returns; Rashford unavailable.
- **Brentford–Everton:** Thiago three-match ban; Hickey/Collins out; Grealish available; midfield and wing selection uncertain.

This is the **post-international-break** round. Exact individual international travel/minutes and late team/Europe/rotation conditions are not comprehensively verified. The Premier League's lineups are *predictions*, not confirmed starting XIs. No price has been verified as available to a user at a named bookmaker. These requirements stay pending for paper selection; the earlier 59 ledger events and zero selections are untouched.

## Protection, tests and coverage

- Existing result database: **100 completed matches, 4,000 rich player rows and 6,562 FPL rows** through GW10; no GW11 matches had kicked off at observation.
- Original archived fixture rows <=100 unchanged (MD5 `38aab9fd924c6cb615b3bc992f4ad253`).
- All saved manual snapshots unchanged (MD5 `3bcd71ab79adbb978d86ffcd254ab046`); their GW11 candidates retain 17 November 09:01:21 GMT calculations and the unchanged four-match minimum.
- Frozen v3 unchanged (MD5 `f3097c1d21be5443c3c6790ece2c29dd`); public policies unchanged (26, MD5 `988e388d687556eb705513d4864307bc`).
- GW11 fixture records changed from MD5 `896fc68bc2649402642cbbde14a16bbb` to `23d5ec3af54294627c15f897ea9a1c88`, exclusively the comparison prices, observation time/source and appended news. Prior notes retained verbatim.
- Full DB readback verified all ten triples preceded the correct kickoff, ten valid current news JSON records and ten source-linked records.
- Existing model, staking, eligibility, history and paper selection rules unchanged. No researched-model cache rebuild. Understat mapping backlog and current-season Transfermarkt source gap remain as before.
- Relevant unit tests, TypeScript and build are run separately in the cloud sandbox. Deployment and authenticated live-domain checks must be verified separately; database readback is not proof of production deployment.

Machine-readable audit: [data/weekend-2026-11-21-matchday-odds-news.json](data/weekend-2026-11-21-matchday-odds-news.json). No Tuesday automation or GitHub Actions scheduling change.
