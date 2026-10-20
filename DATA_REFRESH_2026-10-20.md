# Premier League stats refresh 20 October 2026

All ten 17–19 October results are loaded. Every club now has seven current-season matches, and results, rich player reports, lineups, goals, Understat staging and historical market odds cover all **70 completed games**. The betting/form and FPL aggregate caches are refreshed.

| Layer | Current season state |
| --- | --- |
| Results and canonical matches | 70 each |
| Player-season identities | 668 |
| Rich player-match reports | 2,800 rows across 70 matches |
| Lineups | 2,800 rows; 22 starters for every match |
| Goal events | 203; counts match every final score |
| Official FPL | 4,551 rows across all 70 fixtures |
| Understat staging | 2,158 rows across 70 matches; 1,168 verified mapped rows |
| Understat canonical enrichment | 1,156 appearances; zero metric differences |
| Football-Data historical odds | All 70 matches |
| Team feature cache | 140 rows, all 20 clubs with seven games; complete xG |

## Sources and changes

- The [official FPL fixtures](https://fantasy.premierleague.com/api/fixtures/) mark all ten GW7 fixtures finished. The [bootstrap](https://fantasy.premierleague.com/api/bootstrap-static/) still marks the gameweek `finished=false` and `data_checked=false`. The 668 [GW7 live rows](https://fantasy.premierleague.com/api/event/7/live/) therefore retain `official_fpl_api_post_match_gw_unchecked` provenance; fantasy statistics can still be revised.
- Added nine result/canonical rows, 360 rich player rows, 360 lineup rows and 24 goals. All ten native Fotmob reports reconcile to official teams, dates, scores, 40 matchday player records and 22 starters. Player identities use explicit native Opta IDs linked to official FPL codes, never names.
- Sunderland’s Tutierov has an existing permanent canonical code `604211`. Added the official 2026/27 player-season record with FPL element ID `668`; no new guessed identity was created. Eleven further verified Fotmob player crosswalks and 28 fixture/provider crosswalks were added.
- The established rich mirror is pinned at `bc3335bca96caae08ef2057526498c7c7e0ea1f6`, published 20 October at 12:51 UTC. Direct native reports preserve Fotmob provenance.
- Added 609 previously missing GW7 FPL rows and refreshed the 59 provisional Everton–Chelsea rows. Twenty-six existing rows have revised xG, expected goals conceded, BPS or defensive statistics; previously recorded total points are unchanged. Every imported scoring-component total reconciles.
- Added 305 staged Understat appearances and 165 canonical enrichments across all ten GW7 matches. Today’s completed coverage closes the provider-publication gaps recorded on 17 October. Twelve verified mapped Understat rows lack a matching canonical appearance and remain unforced; unresolved provider identities remain staged.
- Added ten [Football-Data historical odds](https://www.football-data.co.uk/mmz4281/2627/E0.csv) records, including opening/closing market averages and original rows.
- Transfermarkt’s approved [published games](https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/games.csv.gz) returned HTTP 304 against the 5 September checkpoint. It still has zero 2026/27 PL matches, latest 24 May 2026; repository head remains `e44f186d6f06dd8452aaf54c7921ba66c961f637`.

## Integrity and verification

All 40 saved manual fixtures, odds records and pre-match snapshots retain their exact hashes. No forecast refresh was run on the completed round. All 61 previously stored result rows, all GW1–6 FPL/player/Understat data, earlier lineups/goals and historical odds remain unchanged. Everton–Chelsea’s previously stored rich core data is preserved while its advanced fields receive the new verified Understat enrichment.

The existing pre-match form calculations populate only the nine new result rows, using preceding matches. All 20 clubs have seven current-season feature rows. There are zero source/cache differences, missing xG rows, FPL point-component mismatches or Understat advanced-metric mismatches. Anonymous application access returns all 70 results, 2,800 rich player rows, 4,551 FPL rows, 2,800 lineup rows and 203 goals.

A local production build of the unchanged app, reading the live database, displayed every club on seven games, all ten new round scores and Forest–Arsenal’s result, scorer, assist and lineups without console errors. No app code, formula, weight, history eligibility, schema, RLS or grants changed.

The [value review](WEEKEND_REVIEW_2026-10-17.md) settles the original watchlist and scores all seven eligible forecasts. The original assessments remain frozen; no actual bets are assumed. Detailed counts, source state and integrity evidence: [refresh checkpoint](data/full-refresh-2026-10-20-checkpoint.json).
