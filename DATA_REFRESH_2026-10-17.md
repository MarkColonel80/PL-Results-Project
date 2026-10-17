# Premier League stats and weekend refresh 17 October 2026

Everton’s 0–2 home defeat to Chelsea is loaded, and the current-season results, player reports, lineups and goal events cover all 61 completed games at the refresh cutoff. The six remaining 17–19 October fixtures have refreshed market odds and dated team news on the [weekend page](https://pl-data.colly.me.uk/betting/weekend).

## Coverage

| Layer | Current season coverage | State |
| --- | --- | --- |
| Results and canonical matches | 61 matches | Includes Everton 0–2 Chelsea, 17 October 11:30 UTC |
| Official FPL | 3,942 player rows | Today’s 59 club-player rows use official live final-provisional data |
| Rich player-match reports | 2,440 rows, 61 matches | Forty matchday player records and 22 starters per match |
| Lineups | 2,440 rows, 61 matches | All matches have 22 starters |
| Goal events | 179 goals | Counts reconcile to every final score |
| Understat staging | 1,853 rows, 60 matches | 1,001 map through previously verified provider IDs |
| Understat canonical enrichment | 991 appearances | Zero differences in the six imported advanced metrics |
| Historical Football-Data odds | 60 matches | All games through GW6 |
| Betting team cache | 122 rows, 61 matches | All 20 clubs, complete xG, no source/cache differences |

Understat has not published today’s match detail (`31240`, HTTP 404). Football-Data’s current CSV has 60 results and excludes today. Those two provider layers cannot yet cover Everton–Chelsea. Ten mapped Understat appearances still have no matching canonical appearance and are left unforced. Unmapped Understat players remain in staging without guessed identities.

The approved Transfermarkt dataset remains unchanged at its 5 September release: zero 2026/27 Premier League games, latest match 24 May 2026. This archive is not a live current-season source.

## Sources and identity

- [Official FPL fixtures](https://fantasy.premierleague.com/api/fixtures/) and [event 7 live player stats](https://fantasy.premierleague.com/api/event/7/live/) establish today’s score and fantasy data. FPL’s final-provisional flag is recorded explicitly; an independent completed match report confirms full time.
- Direct Fotmob match reports were audited for all 61 completed fixtures. Today’s [native match report](https://www.fotmob.com/api/data/matchDetails?matchId=5795478) supplies matchday player reports, starting teams and Neto’s two goals. Verified native match identities also cover the previously incomplete GW6 reports.
- Player identity uses Fotmob’s explicit `optaId` matched to the official FPL bootstrap `opta_code`, then existing permanent FPL player codes and season IDs. Added 511 verified Fotmob player crosswalks and 61 native match crosswalks. Names are display/QA only.
- The rich source mirror is pinned at `c9d2e40d6be440e7b5dcecb553dd161bae801b7c`; its two incomplete GW6 player reports and missing current incidents/lineup files are supplemented with direct native records, without relabelling their provenance.
- [Understat league data](https://understat.com/league/EPL/2026) and ten GW6 match reports supplied 315 new staged rows and 163 canonical enrichments. Only existing verified Understat player mappings were used. Provider-specific xG remains labelled as Understat after enrichment.
- [Football-Data current-season CSV](https://www.football-data.co.uk/mmz4281/2627/E0.csv) supplied ten additional historical market records.
- [Transfermarkt published games](https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/games.csv.gz) was checked directly; release commit `e44f186d6f06dd8452aaf54c7921ba66c961f637` and Last-Modified 5 September are recorded in the checkpoint.

## Verified factual corrections

The [official 16 September goal-accreditation appeal](https://www.premierleague.com/en/news/4720022/calvert-lewin-awarded-second-goal-after-leeds-appeal) gives Calvert-Lewin Leeds’ second goal against Newcastle and credits Justin’s assist. The rich football statistics and goal event now reflect the appeal; the official article states that FPL’s gameweek had closed, so previously awarded FPL statistics and points are preserved.

Two previously null Brentford–Chelsea scorer identities now resolve through native Opta IDs to Thiago and Carvalho. Four existing goal events and seven player own-goal fields were reconciled with direct native events. These explicit repairs are listed separately from protected historical rows in the checkpoint.

## Remaining weekend fixtures

Prices below are decimal H/D/A quotes from the [Oddschecker UK Premier League coupon](https://www.oddschecker.com/football/leagues-cups/english/premier-league), observed **17 October at 15:14 UK**. Team news was checked at **15:15 UK**. The saved JSON retains exact fractions, conversions, report URLs and observation times.

| Fixture | Home | Draw | Away |
| --- | ---: | ---: | ---: |
| Newcastle–Villa | 2.40 | 3.80 | 2.9473684211 |
| Bournemouth–Sunderland | 2.1578947368 | 3.60 | 3.60 |
| Brighton–Palace | 1.5454545455 | 4.75 | 6.00 |
| Leeds–United | 2.40 | 3.70 | 3.00 |
| Forest–Arsenal | 6.00 | 4.00 | 1.6666666667 |
| Spurs–Coventry | 1.50 | 4.75 | 7.20 |

The page displays the source-linked news for each club, recovery/travel and surrounding European fixtures, alongside expandable official FPL availability flags. A club’s newer announcement can supersede a softer or older FPL flag; confirmed teams remain pending. News is context and does not alter the model probabilities. Refresh the available price and confirmed teams near kick-off.

## Integrity and validation

All aggregate and form caches were refreshed before recalculating only future GW7 snapshots. The existing formulas, weights and four-match venue minimum are unchanged. Spurs–Coventry remains suppressed because Coventry has only three relevant away games. No schema, RLS or grants changed.

The complete fixture, odds and snapshot records for all 34 kicked-off fixtures match their pre-refresh copies, including Everton–Chelsea and the three 15:00 UK games. All 60 earlier result rows match exactly. Integrity hashes preserve earlier FPL rows, lineups and unaffected player/goal records; only the listed factual repairs and GW6 Understat enrichment differ. Morning investigation records are frozen separately and were not retrospectively rewritten. No bets were placed.

Validation passed: all score/goal counts; all matchday and starter counts; zero FPL point-component mismatches; zero Understat advanced-metric mismatches; zero team-cache differences; anonymous access to all six refreshed future fixtures; weekend review, news parser and value-indicator tests; and the production build. A browser rendered all six news panels, the six refreshed price tables and the 61-match status without console errors.

Saved evidence: `data/full-refresh-2026-10-17-checkpoint.json`, `data/weekend-2026-10-17-news.json` and the frozen `data/weekend-2026-10-17-prerefresh-investigation.json`. Full raw-source and before/after evidence remains on this Mac in `outputs/full-refresh-2026-10-17/` under the active Codex workspace.
