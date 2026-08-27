# Betting Model v4 — adaptive recency / venue experiment

_Date: 2026-08-27_

## Goal

Test Mark's proposal to make the model more responsive to current form and venue-specific strength without throwing away the longer-term signal that performed well in v3.

## Match-table form metrics

`public.matches` now stores pre-match team form for the live/recent fixture table:

- overall PPG, xG-for and xG-against over previous 5 / 10 / 15 / 30 PL matches
- same-venue (home for home team, away for away team) PPG, xG-for and xG-against over previous 5 / 10 / 15 venue matches
- metrics are NULL until the full requested sample exists
- current Premier League spell segmentation is respected, so promoted/returning teams do not inherit old PL history

A helper materialized view `public.team_form_window_cache` provides one pre-match row per team/match with rolling overall and venue windows for faster analysis.

## Pure adaptive-15 experiment

Initial v4 candidate used last 15 as the anchor, with last 10 / last 5 and venue form pulling the estimate when materially different.

This fixed the Chelsea v Brighton 2023/24 example materially, but worsened calibration across all seven tested seasons compared with v3. It was therefore NOT promoted to the live model.

Chelsea v Brighton, GW14 2023/24:
- v3: Chelsea 35.6%, Draw 22.9%, Brighton 41.4%
- pure adaptive-15 candidate: Chelsea 42.6%, Draw 22.5%, Brighton 34.9%

## Longer-term anchor restored + stronger venue pull

Second v4 candidate restores persistent team strength:

- 65% adaptive 15/10/5 signal
- 35% 30-match signal
- if same-venue PPG differs from the anchor by >=0.30, pull 40% toward venue form
- if PPG difference is 0.15–0.29, pull 20% toward venue form
- if same-venue xG/xGA differs by >=0.25, pull 40% toward venue form
- if xG/xGA difference is 0.15–0.24, pull 20% toward venue form
- use venue-15 when available, otherwise venue-10, otherwise venue-5
- keep the v3 65% xG / 35% actual-goals blend, four-match shrinkage, 0.75 attack/defence damping, 0.14 PPG adjustment and Poisson conversion

Materialized test layers:
- `public.betting_team_features_v4_long_venue_test`
- `public.betting_model_v4_long_venue_inputs`

## Seven-season probability calibration

| Season | v3 Brier | v4 Brier | v3 Log loss | v4 Log loss |
|---|---:|---:|---:|---:|
| 2019/20 | 0.58120 | 0.58383 | 0.97853 | 0.98185 |
| 2020/21 | 0.60115 | 0.60262 | 1.00887 | 1.01149 |
| 2021/22 | 0.57358 | **0.56795** | 0.96602 | **0.95862** |
| 2022/23 | 0.58205 | **0.57702** | 0.97658 | **0.96917** |
| 2023/24 | **0.56072** | 0.56254 | **0.94966** | 0.95250 |
| 2024/25 | **0.58374** | 0.58662 | **0.98054** | 0.98410 |
| 2025/26 | **0.61900** | 0.62173 | **1.03033** | 1.03444 |

Seven-season mean:
- v3: Brier **0.58592**, log loss **0.98436**
- v4 long+venue: Brier **0.58604**, log loss **0.98460**

So this version is essentially a statistical tie with v3 overall, while improving some seasons and worsening others.

Chelsea v Brighton GW14 2023/24 under long+venue v4:
- projected goals: Chelsea 1.645, Brighton 1.626
- Chelsea win 38.8%
- Draw 23.1%
- Brighton win 38.0%

This is materially less extreme than v3 but not as Chelsea-positive as the pure adaptive-15 version.

## Current interpretation

- Pure 15-match form is too reactive overall.
- Restoring 30-match strength recovers nearly all lost calibration.
- Stronger venue adjustments are plausible and improve some seasons, but the current threshold/weight choices do not yet outperform v3 overall.
- Keep v3 as the validated baseline for now.
- Keep v4 layers as explicit experiments; do not silently replace the production model until a variant wins across broad out-of-sample testing.
