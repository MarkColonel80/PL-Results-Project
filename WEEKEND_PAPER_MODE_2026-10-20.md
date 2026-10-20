# Weekend fixtures in paper mode

The weekend page now treats upcoming picks as paper bets. All ten official Matchweek 8 games for 23–25 October are published, using the existing model and completed results through Matchweek 7. Seven fixtures have eligible probabilities. Ipswich–Forest, Coventry–Fulham and Hull–Brentford remain suppressed because the promoted home clubs have only three relevant home appearances. All ten fixtures currently have a timestamped **watch** decision, with zero paper selections or hypothetical stakes.

## What the page now shows

- A prominent paper-mode notice and a separate paper decision column. Model outcomes remain labelled as model views. Green/red arrows retain the original calculation, renamed **model price gap**, and never create a selection automatically.
- A one-unit paper scorecard with selections, pending/settled results, committed units, net result and return on settled stakes. Earlier conditional watchlists are not converted retrospectively into paper bets.
- A separate all-forecast scorecard: the 28 eligible frozen forecasts across the four previously published rounds, versus the same saved market. The dated baseline is explicit; it is not a paper-profit ledger.
- For every fixture, explicit pending/recorded checks for confirmed teams, an available named-bookmaker quote, team news, recovery/Europe and sensitivity. A recorded watch or pass has no stake.
- Exact counts of current-season versus earlier-season matches within each team's Venue8 sample, using only completed current-season fixtures before the saved calculation time. Missing history stays unavailable.
- xG-only Venue8 and Venue18 probability comparisons under the existing current-model architecture. Venue18 requires 18 relevant appearances per team. These are sensitivity diagnostics, not replacement forecasts or confidence intervals. When a saved research price advantage disappears in a diagnostic, the page flags the affected outcome.
- A timestamped decision history. After a valid paper selection, a later pass cannot erase the selected outcome, original probabilities, price or stake.

## Decision and settlement workflow

The ledger is versioned in `data/weekend-paper-ledger.json`, separate from fixture notes and database forecasts. Updates are made through the established project/GitHub workflow; there is no anonymous write endpoint or browser-only storage. No new database table, permission, schema or authentication change is needed.

Append a `watch`, `pass` or `paper` event with a unique ID, fixture ID, exact kick-off, observation time and reason. Never edit an existing event. A paper selection additionally requires:

1. One H/D/A outcome and exactly one hypothetical unit.
2. A named bookmaker, available decimal quote, source URL and observation time.
3. Frozen current and research probability triples, model identifiers, calculation time and both venue-history counts. Both teams must meet the existing four-match minimum; the recorded research probability must exceed the quote's break-even chance.
4. Confirmed-team evidence, team news, schedule/Europe and history/sensitivity evidence. Each check has a source URL, timestamp and summary.

Every observation, forecast and check must be recorded no later than the decision, and the decision must precede kick-off. Future, late, incomplete and changed-fixture records cannot create a paper selection. The first valid selection remains the selection when later events are appended. Reviewers can accept a fragile signal only by recording the sensitivity review and reason; the page does not silently substitute a more favourable diagnostic probability.

After full time, append a settlement referencing that selection ID, with final scores, completion/recording times, finished status and source URL. Watches and passes are never settled as stakes. A one-unit winner returns `decimal odds − 1`; a loser returns `−1`. Pending records do not enter the settled-return denominator, and duplicate settlements cannot double-count a stake.

Before a later ledger publish, retain the previous committed JSON and run:

```sh
node --experimental-strip-types scripts/validate_weekend_paper.mjs /path/to/previous-ledger.json
node --experimental-strip-types scripts/test_weekend_paper.mjs
```

The optional previous-ledger argument verifies that original fixture metadata, decisions and settlements are unchanged prefixes. Append records rather than replacing them. Update `data/weekend-forecast-scorecard.json` from all eligible frozen forecasts after the next results review; keep its as-of date and eligible/published denominators explicit. The forecast scorecard and paper ledger have separate populations.

## Current round and verification

Fixtures were checked against the [official FPL fixtures API](https://fantasy.premierleague.com/api/fixtures/) on 20 October. Provider IDs and manual review IDs are stored separately in `data/weekend-2026-10-23-fixtures.json`; saved forecast inputs are in `data/weekend-2026-10-23-snapshots.json`. Kick-offs display in Europe/London, including the return to GMT on Sunday 25 October.

Prices and current-round club/Europe/confirmed-team reviews are pending. No check has been marked complete, no bookmaker quote has been invented, and no real-money bet or automatic future update has been scheduled. New paper selections require actual pre-match evidence when those checks are performed.

The new paper tests cover missing teams/quotes/checks, unsafe evidence links, future/late timestamps, insufficient history, invalid probabilities, changed kick-offs, frozen first selections, later passes, win/loss/pending settlement, duplicate settlement handling, append-only history and diagnostic/history limits. Existing value, weekend review, news and round tests pass. The Next.js production build passes. Browser checks confirm the ten fixtures, zero-stake scorecard, pending checks, exact season breakdown and expandable sensitivity comparison.

All 40 prior fixture/snapshot records and frozen model rows retain their original database fingerprints. Existing RLS/grants remain unchanged. The live model formulas, weights and eligibility rules are unchanged; only upcoming snapshots were created with the established refresh scripts.
