# Cloud refresh — 2026-11-10

{
  "reviewedRound": 10,
  "imports": {
    "matches": 0,
    "canonical_matches": 10,
    "match_source_ids": 20,
    "player_match_stats": 400,
    "lineups": 400,
    "goals": 30,
    "fpl_player_match_stats": 672,
    "historical_market_odds": 10
  },
  "coverage_gaps": [
    "Manchester City v Fulham: current comparison prices unavailable",
    "Aston Villa v Sunderland: current comparison prices unavailable",
    "AFC Bournemouth v Nottingham Forest: current comparison prices unavailable",
    "Chelsea v Leeds United: current comparison prices unavailable",
    "Coventry City v Crystal Palace: current comparison prices unavailable",
    "Tottenham Hotspur v Ipswich Town: current comparison prices unavailable",
    "Newcastle United v Arsenal: current comparison prices unavailable",
    "Hull City v Brighton & Hove Albion: current comparison prices unavailable",
    "Liverpool v Manchester United: current comparison prices unavailable",
    "Brentford v Everton: current comparison prices unavailable",
    "Official club press conferences and confirmed XIs pending; FPL flags can lag announcements.",
    "Understat/Transfermarkt historical mapping backlogs not changed by weekly worker; unresolved identities remain excluded.",
    "European public schedules require official club/UEFA confirmation before any paper selection."
  ],
  "run": "https://github.com/MarkColonel80/PL-Results-Project/actions/runs/42787760318"
}

Production verification is recorded in the durable run receipts; publication is not success until that probe passes.

## Completed recovery and production verification

See [the final recovery receipt](TUESDAY_RECOVERY_2026-11-10.md). The zero match count above is the third attempt only: ten matches had already committed on attempt 2. Across the same-date recovery, ten matches were added exactly once; final totals are 100 matches, 4,000 rich player rows, 6,562 FPL rows, 4,000 lineups, 273 goals and 100 historical odds rows. Production and authenticated/anonymous access were verified at 17:09:58 GMT. Detailed identity evidence, the narrowly scoped lookup-performance repair, unchanged-history fingerprints and remaining source gaps are recorded in that receipt.
