-- Fix Betting Model v2 xG source coverage.
-- Canonical player_match_stats remain preferred where xG exists (Understat/rich_core).
-- FPL expected_goals is used as a fallback when canonical player_match_stats has no xG,
-- notably restoring complete 2024/25 xG coverage.

create or replace view public.betting_team_match_v2 as
with canonical_team_stats as (
  select season, match_id, team_name,
         min(gameweek) as gameweek,
         sum(xg) filter (where xg is not null) as xg,
         count(*) filter (where xg is not null)::integer as xg_player_rows
  from public.player_match_stats
  group by season, match_id, team_name
),
fpl_team_stats as (
  select season,
         kickoff_time::date as match_date,
         team_name,
         opponent_team,
         bool_or(was_home) as was_home,
         min(gameweek) as gameweek,
         sum(expected_goals) as xg,
         count(*) filter (where expected_goals is not null)::integer as xg_player_rows
  from public.fpl_player_match_stats
  group by season, kickoff_time::date, team_name, opponent_team
),
match_base as (
  select c.season,
         coalesce(h.gameweek, a.gameweek, fh.gameweek, fa.gameweek) as gameweek,
         c.canonical_match_id as match_id,
         c.match_date,
         c.home_team,
         c.away_team,
         c.home_score,
         c.away_score,
         coalesce(h.xg, fh.xg) as home_xg,
         coalesce(a.xg, fa.xg) as away_xg
  from public.canonical_matches c
  left join canonical_team_stats h
    on h.season=c.season and h.match_id=c.canonical_match_id and h.team_name=c.home_team
  left join canonical_team_stats a
    on a.season=c.season and a.match_id=c.canonical_match_id and a.team_name=c.away_team
  left join fpl_team_stats fh
    on fh.season=c.season and fh.match_date=c.match_date and fh.team_name=c.home_team and fh.opponent_team=c.away_team and fh.was_home
  left join fpl_team_stats fa
    on fa.season=c.season and fa.match_date=c.match_date and fa.team_name=c.away_team and fa.opponent_team=c.home_team and not fa.was_home
)
select season,gameweek,match_id,match_date::timestamptz as kickoff_time,
       home_team as team_name,away_team as opponent_team,true as was_home,
       home_score as goals_for,away_score as goals_against,
       home_xg as xg_for,away_xg as xg_against,
       (home_xg is not null and away_xg is not null) as xg_available,
       case when home_score is null or away_score is null then null
            when home_score>away_score then 'W'
            when home_score=away_score then 'D' else 'L' end as result
from match_base
union all
select season,gameweek,match_id,match_date::timestamptz as kickoff_time,
       away_team as team_name,home_team as opponent_team,false as was_home,
       away_score as goals_for,home_score as goals_against,
       away_xg as xg_for,home_xg as xg_against,
       (away_xg is not null and home_xg is not null) as xg_available,
       case when home_score is null or away_score is null then null
            when away_score>home_score then 'W'
            when away_score=home_score then 'D' else 'L' end as result
from match_base;

refresh materialized view public.betting_team_features_v2_cache;
