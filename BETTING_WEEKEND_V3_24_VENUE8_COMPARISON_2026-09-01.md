# Weekend betting page — 24-match + Venue8 research comparison

_Date: 2026-09-01_

## Purpose

Add the current leading v3 + Venue8 research candidate to `/betting/weekend` as a side-by-side comparison without changing the existing manual weekend PPG8 / adjusted-xG tie-break rule.

## Research candidate shown on the page

Model version: `v3_24_venue8_50`

- equal-weight prior 24-match structural attack/defence history within the team’s current Premier League spell;
- structural actual GF/GA capped match-by-match at `min(actual, xG + 1.0)`;
- structural strength = 65% xG + 35% capped actual goals;
- four pseudo-match shrinkage toward the recent league scoring midpoint;
- PPG10 retained with the existing 1.35 / four-pseudo-match shrinkage;
- team-specific Venue8 uses home-only history for the home team and away-only history for the away team;
- Venue8 actual GF/GA use the same one-sided `xG + 1.0` cap;
- adjusted Venue8 attack/defence = 50% raw venue xG + 50% capped actual goals;
- the match-specific Venue8 scoring baseline is then geometrically shrunk 50/50 toward the generic recent league home/away scoring baseline;
- structural opponent interaction uses exponent 0.75;
- independent Poisson H/D/A probabilities;
- minimum four current-spell relevant venue matches for both teams before a comparison score is shown.

This is the fixed-50 Venue8 shrinkage candidate selected after the 2019/20–2024/25 development tests and 2025/26 stress test. It remains research-only and does not replace validated production v3 or the current manual weekend rule.

## Supabase implementation

`public.betting_manual_weekend_snapshot` now stores:

- `candidate_model_version`
- `candidate_home_n24`, `candidate_away_n24`
- `candidate_home_n10`, `candidate_away_n10`
- `candidate_home_ppg10`, `candidate_away_ppg10`
- `candidate_home_lambda`, `candidate_away_lambda`
- `candidate_home_prob`, `candidate_draw_prob`, `candidate_away_prob`
- `candidate_calculated_at`

Reusable refresh SQL:

- `scripts/add_weekend_v3_venue8_comparison.sql`

Run that script again after the manual fixture/snapshot set is refreshed so the research comparison is recalculated from pre-kickoff history.

## Frontend

Updated:

- `app/betting/weekend/page.tsx`

Each fixture card now shows a separate **24-match + Venue8 comparison** section containing:

- 24-match structural sample counts;
- raw PPG10 and sample counts;
- candidate expected goals;
- H/D/A probabilities;
- candidate fair odds;
- candidate top outcome.

The final odds table also displays current-weekend probabilities/fair odds, the 24-match + Venue8 probabilities/fair odds, Oddschecker prices, and no-vig bookmaker probabilities side by side.

The existing manual weekend decision remains the card headline and is unchanged.

## Current Matchweek-3 snapshot check

The current snapshot produces candidate probabilities for seven of the ten fixtures. It deliberately suppresses the comparison for:

- Ipswich Town v Liverpool — Ipswich current PL spell has only one prior match in the source cache / one relevant home match;
- Manchester City v Coventry City — Coventry current PL spell has only one prior match / one relevant away match;
- Hull City v Aston Villa — Hull current PL spell has only one prior match / one relevant home match.

This confirms stale prior Premier League spells are not being reused to bypass the current-spell history rule.

## Deployment

Frontend commit: `8d2e97d0a63ab3b7c142dfec61af79bfeab9ee4e`.

The Vercel production deployment for that commit reached `READY` (`dpl_EnKK4ksj7nm5cnos6sYSXwWXhnat`). The production route is protected by the project's existing Basic Auth, so unauthenticated fetches correctly return HTTP 401.
