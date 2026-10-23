# GW8 Friday afternoon price recheck and publication receipt

Observation: **2026-10-23T14:55:44Z**, 23 October 2026, Europe/London. This appends to the [morning market review](WEEKEND_GW8_FRIDAY_MARKET_REVIEW_2026-10-23.md) and preserves every earlier report, quote and ledger event.

A final [public Oddschecker coupon](https://www.oddschecker.com/football/leagues-cups/english/premier-league) check found Brighton had moved from3.25 to3.40 and Spurs from4.8462 to4.60; Palace remains3.00. These are public comparison prices, not verified available named-bookmaker quotes.

| Watch | Decimal | Break-even | Frozen research | Gap | Weakest diagnostic cushion |
|---|---:|---:|---:|---:|---:|
| Spurs away | 4.60 | 21.74% | 24.79% | +3.05pp | +1.47pp |
| Palace home | 3.00 | 33.33% | 43.46% | +10.12pp | +2.51pp |
| Brighton away | 3.40 | 29.41% | 38.22% | +8.81pp | +3.37pp |

Frozen research H/D/A remains Palace43.4554/24.6661/31.8785%, Liverpool36.0104/25.7721/38.2175%, Chelsea50.6073/24.6041/24.7886%. Current and both xG-only sensitivity triples remain those verified in the morning report. No forecasts or weights changed. All three remain watches, zero units.

All ten future fixtures receive the later coupon observation in [the afternoon audit JSON](data/weekend-2026-10-23-friday-afternoon-review.json). Sunderland home is now3.10, so its research gap has narrowed to roughly+1.79pp; its prior pass remains. Seven non-focus fixtures still have no newly completed team-news/XI review. The23→26 morning ledger and this26→29 extension both preserve original events. News evidence retains its actual earlier check times; no new official medical clearance was verified.

## Verified publication receipt for the initial update

- GitHub main: [1ec2bc3](https://github.com/MarkColonel80/PL-Results-Project/commit/1ec2bc323defa8f7daaba30a9d0432ec69b1737f).
- Vercel production: [deployment GM6G5C9o8J2LjeYKedrdtUwnfnFT](https://vercel.com/colly3/pl-results-project/GM6G5C9o8J2LjeYKedrdtUwnfnFT), READY, matching commit, assigned to[pl-data.colly.me.uk](https://pl-data.colly.me.uk/betting/weekend); build about65seconds.
- Supabase: all10 updated rows read back exactly; anonymous role sees all10 fixtures and snapshots.
- Original50 snapshot,2,660 frozen-model and40 earlier-fixture hashes unchanged, as recorded in both audit files. No schema, privileges, model or historic result changes.
- Existing paper/news/value/round tests and previous-commit append-only validator passed in cloud Node24. The afternoon extension also passed previous-commit append-only validation and all five existing checks before advancing main.
- Error/fatal runtime query returned no logs in the30-minute inspection window. That is limited server-side evidence, not a complete browser test. The generic web fetch failed; the Vercel connector's share link and an ordinary cloud HTTP request returned401. Drain inspection returned404. No protection was disabled.

The later price revision is committed separately and its final deployment is reported in the completion message; this receipt identifies the initial deployment explicitly rather than assigning a future commit to it.

Saturday24October16:30BST and Sunday25October13:00GMT cloud checks are unchanged. XIs, fresh named-bookmaker quote/time/URL, current team news, recovery and full sensitivity review remain mandatory before a final paper decision. A pass is valid.
