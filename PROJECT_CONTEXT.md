# PL Results Project — Persistent Project Context

_Last updated: 2026-08-26_

This file is the durable handoff/source of truth for continuing the project across ChatGPT conversations. At the start of a new project chat, read this file first, then verify live state in GitHub/Supabase/Vercel before making changes.

## Global workflow preference

- For software/data projects use **GitHub for source/version history, Supabase for database/backend, and Vercel for deployment/production verification** when appropriate.
- ChatGPT should inspect and modify these connected systems directly rather than asking Mark to shuttle files/data around or use Codex.
- Only ask Mark to run a local command when the connected execution environment genuinely cannot perform the action.
- Keep this file updated after material code/data/schema/deployment milestones.

## Connected systems

- **GitHub:** `MarkColonel80/PL-Results-Project`, branch `main`.
- **Supabase:** `PL Results Project`, ref `priibitbnmfetyblzltk`.
- **Vercel:** project `pl-results-project`, id `prj_8OeSf0K7GBywgASSo5ojRUpYDg84`, team `Colly` / `team_AVL2QNde5NnMKvlgXcjw0hhf`.
- Production domain: `https://pl-results-project.vercel.app` (protected by the project's existing Basic Auth).

## Player identity / historical data state

### Understat

Understat Premier League history 2014/15–2023/24 has been staged, identity-resolved and enriched.

Final stable state:
- staged rows: **106,519**
- source players: **1,899**
- verified mappings: **1,816**
- unresolved source players: **83** (deliberately left unresolved)
- mapped staged rows: **105,041**
- mapped rows missing live: **0**
- mapped live rows missing Understat advanced metrics: **0**
- advanced-metric mismatches: **0**
- remaining `source_native_identity` mappings: **136**, all 2014/15-only
- manual verified crosswalks: **4**

Important scripts/commits:
- deterministic resolver: `scripts/resolve_understat_cross_source.py`, commit `8bc5470567e1303f0f11b89cf33059e49d6d5e73`
- legacy reconciliation: `scripts/reconcile_understat_source_native.sql`, commit `bec85af176a71330c6458e9f342316218f7bf4ee`
- advanced enrichment: `scripts/enrich_understat_advanced_metrics.sql`, commit `4c336f5c8f2681d0d27d900d60874f578532aea8`
- missing verified rows: `scripts/promote_understat_missing_verified_rows.sql`, commit `6dc67a5f2791c2c54e42b403ce97a5c6d1ebbde1`
- final manual reconciliation: `scripts/reconcile_understat_manual_three.sql`, commit `05561830b8f71bc18b9852ceac3f6de2e1bc083c`

Manual exceptions reviewed by Mark:
- Steven Pienaar Understat `924` -> canonical `7525`
- Juan Cuadrado Understat `1089` and Transfermarkt `91970` -> canonical `66733`
- Rushian Hepburn-Murphy Understat `1015` kept unique canonical `plp:60c49e5ec1254a21a99dc224483b85c7`

Identity rules remain:
- automated player-name matching is prohibited as identity evidence;
- stable IDs / match-history evidence are preferred;
- individually reviewed `manual_name_verified` exceptions are allowed when explicitly agreed.

## Player-name QA page

Route: **`/audit/player-names`**.

Purpose: names are used only as a post-match sanity audit of already-resolved identities.

Current audit universe:
- Transfermarkt verified mappings: **2,275**, with FPL name: **1,750**
- Understat verified mappings: **1,816**, with FPL name: **1,538**
- total mappings with an FPL name to compare: **3,288**

Persistent approval table: `public.player_identity_name_audit_reviews`.
- Mark can tick **Correct**.
- approval persists in Supabase.
- `approved_at` records exact approval date/time.
- default page view hides approved rows, leaving the remaining investigation queue.

## Product/UI direction

Mark decided to prioritise making the existing data useful before paying for another provider such as Sportmonks.

### Player Insights

Route: **`/insights`**.

Purpose: decision-oriented player analysis rather than generic stat tables.

Current modes:
- underlying threat (xGI/90)
- buy-low / underperformance signals
- overperformance signals
- FPL value (points per £m)
- FPL points

Supports season/team/position/minimum-minutes filters and player drill-down.

Supabase view: `public.player_decision_stats_v1`.

## Betting Lab — CURRENT PRODUCT MILESTONE

Mark wants the project to explore whether our data can find bookmaker mispricing for:
- home/draw/away
- goals markets
- goalscorers
- player-specific opponent effects
- situations where two players historically perform differently when facing each other / appearing in opposing sides

Route: **`/betting`**.
Main navigation now includes **Betting Lab**.

Latest production navigation deployment:
- Vercel deployment `dpl_9atpLiMwHjzpnQrf3DswtCxHnAMa`
- state **READY**
- commit `b64003f18b7667a62c45dd46ea03bd872a08427f`

Betting page implementation commit:
- `fd96be2670b7dc01caf7ddd3d73bb31c10c8ba4a`

### Betting Lab data views

Versioned in `scripts/add_betting_lab_views.sql`.
Latest commit after early-season roster fix:
- `362325b29ff6ee5876fdd4b571c9dd064817cc0d`

Supabase views:

1. `public.betting_team_match_v1`
   - team-level match xG aggregated from FPL player match xG
   - continuous FPL-era coverage from 2016/17 onward
   - home/away, opponent, xG for/against, actual goals/result
   - 2025/26 audit: 760 team-match rows, 20 teams, no missing xG
   - 2026/27 after GW1: 20 team-match rows, 20 teams, no missing xG

2. `public.betting_player_goal_profile_v1`
   - registered season roster from FPL rows, including current players with zero appearances
   - actual appearance minutes/goals/xG
   - xG/90
   - recent-five average minutes and xG
   - latest FPL price/ownership
   - early-season fix deliberately separates registration from played-match form so unplayed current players are not omitted from scorer consideration

### Match model

Current model is deliberately transparent/research-oriented:
- FPL match xG is the core team input
- blends selected season with previous season
- previous-season observations have lower recency weight
- home/away attack and defence strengths are calculated separately
- small samples shrink toward league home/away xG averages
- independent Poisson score model produces:
  - home/draw/away probabilities + fair odds
  - expected goals
  - most likely score
  - Over 2.5 probability/fair odds
  - BTTS probability/fair odds

2026/27 future fixtures are not yet present in `matches`; the page therefore lets the user select any home/away pairing. Once future fixtures are loaded, this modelling layer can be reused without redesign.

### Manual bookmaker comparison

The Match Model accepts user-entered decimal H/D/A prices from any bookmaker.
- calculates implied probabilities
- removes 1X2 overround
- compares no-vig market probabilities with our model
- displays probability-point edge and our fair price

This makes the page useful before an automated live odds API is purchased.

### Goalscorer model

Anytime goalscorer section currently uses:
- blended current/previous-season xG/90
- a modest recent-five xG component
- expected minutes blended from recent appearances / prior history
- matchup multiplier derived from team projected goals vs team baseline xG
- Poisson `P(score >= 1)` to produce player goal probability and fair odds

User can enter a bookmaker scorer price beside a player; page shows raw model EV. This is not margin-adjusted because a single scorer price does not reveal the full scorer-market overround.

Current limitations explicitly shown in UI:
- no explicit penalty-taker adjustment yet
- no confirmed-lineup/injury adjustment yet

### Opponent effects

Player-v-team explorer uses canonical FPL player histories.
For each opponent it displays:
- matches
- minutes
- goals
- xG
- raw xG/90
- sample-size-adjusted xG/90
- opponent uplift/downturn versus the player's career baseline

Small samples are shrunk toward career baseline so a couple of lucky games do not become a false “bogey team” signal.

### Player-v-player comparison

Current dataset does not contain true individual duel events.
The Betting Lab therefore includes a deliberately labelled **shared-match comparison**, not a duel statistic:
- finds fixtures where both selected players appeared for opposing sides
- compares each player's goals and xG/90 in those shared matches

Do not describe this as “player A beat player B”. True duel analysis would require event/duel data from another source later.

### Leakage-safe back-test

The Back-test tab rebuilds each historical prediction using only:
- matches before that kickoff in the selected season
- plus the previous season

It reports:
- sample size
- top-pick 1X2 accuracy
- multiclass Brier score
- log loss
- average probability assigned to the actual result
- recent individual predictions

This is deliberately pre-market. It validates calibration before claiming betting edge.

## Historical bookmaker odds — schema ready, importer versioned, DATA NOT YET IMPORTED

Football-Data.co.uk currently publishes free Premier League CSVs specifically for quantitative betting-system testing. Since 2019/20 the files include opening and closing sets of odds; older seasons have pre-closing odds, with some Pinnacle closing 1X2 history further back.

Supabase table created:
- `public.historical_market_odds`

Schema file:
- `scripts/add_historical_market_odds.sql`
- commit `e2c0429f231bf7bcdb6a4172521dc81c622d7759`

Fields include:
- season/source/date/source teams
- optional canonical `match_id`
- opening average/max H/D/A
- closing average/max H/D/A
- opening/closing average Over/Under 2.5
- raw source row JSON
- source URL/import timestamp

Importer:
- `scripts/import_football_data_odds.py`
- commit `3a89100cc928aee6ba6b650a612c8570efc0cd5e`

Importer behaviour:
- DRY RUN by default; `--apply` writes
- downloads EPL `E0.csv` by season
- supports 2016/17 onward by default
- harmless team-name normalisation only
- maps fixture identity by season + canonical home/away teams + exact date, with unique +/-1 day fallback
- does not use player names
- stores raw row as well as normalised odds fields
- upserts repeat-safely into `historical_market_odds`

Important execution note:
- the current ChatGPT container session had no outbound DNS access to fetch the CSV, so the importer was **not executed** and `historical_market_odds` should currently be treated as empty until verified otherwise.
- Do not claim historical market back-testing is complete yet.

## Exact next steps

1. **Run and audit `scripts/import_football_data_odds.py`** in an execution environment with outbound web access and Supabase credentials.
2. Require near-complete canonical fixture mapping for each Premier League season before using odds in model evaluation.
3. Build `model vs market` back-test using closing market probabilities first:
   - strip 1X2 overround
   - compare our probability vs no-vig market probability
   - bucket by model edge (e.g. 0–2%, 2–5%, 5–10%, 10%+)
   - report sample size, calibration, closing-line value and hypothetical flat-stake ROI
   - never tune thresholds on the same sample without out-of-sample validation.
4. Add opening-v-closing movement analysis after closing-price baseline is working.
5. Add future fixture ingestion to `matches` so `/betting` can automatically show the upcoming slate rather than manual team selectors.
6. Only after model/market back-testing shows useful signal should we consider paying for live bookmaker odds or richer event data (e.g. Sportmonks).

## Betting-model safety / research rules

- Treat outputs as statistical research signals, not guaranteed winners.
- Avoid look-ahead leakage: every historical prediction must only use data available before kickoff.
- Compare against no-vig market probabilities where possible rather than raw `1/odds` alone.
- Keep model input provenance explicit.
- Do not silently overwrite historical source data when improving models; version modelling changes.
- When later evaluating ROI, include all qualifying bets from the declared rules rather than cherry-picking examples.

## Other historical-source work

A Joseph CC0 dataset was audited separately and did not establish itself as a useful stable player-identity source. No Supabase writes were made from that audit.

## Continuation instruction

When Mark asks to continue the **PL Results Project**, first read this file, then inspect current GitHub/Supabase/Vercel state. Do not ask Mark to re-explain project history that can be recovered from these systems.
