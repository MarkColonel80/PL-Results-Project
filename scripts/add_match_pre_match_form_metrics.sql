-- Add leakage-safe pre-match team form metrics directly to public.matches.
--
-- Each match stores HOME and AWAY values for the team's previous 5, 10 and
-- 15 Premier League matches in its current continuous PL spell:
--   PPG = points per game
--   xGF = expected goals for per game
--   xGA = expected goals against per game
--
-- A metric is NULL until the team has the full requested number of prior PL
-- matches in its current spell. This prevents a promoted/returning team from
-- inheriting stale PL history from an earlier spell and keeps the meaning of
-- e.g. ppg10 unambiguous: exactly the previous 10 matches, all pre-kickoff.

alter table public.matches
  add column if not exists home_ppg5 numeric,
  add column if not exists home_xgf5 numeric,
  add column if not exists home_xga5 numeric,
  add column if not exists away_ppg5 numeric,
  add column if not exists away_xgf5 numeric,
  add column if not exists away_xga5 numeric,
  add column if not exists home_ppg10 numeric,
  add column if not exists home_xgf10 numeric,
  add column if not exists home_xga10 numeric,
  add column if not exists away_ppg10 numeric,
  add column if not exists away_xgf10 numeric,
  add column if not exists away_xga10 numeric,
  add column if not exists home_ppg15 numeric,
  add column if not exists home_xgf15 numeric,
  add column if not exists home_xga15 numeric,
  add column if not exists away_ppg15 numeric,
  add column if not exists away_xgf15 numeric,
  add column if not exists away_xga15 numeric;

with base as (
  select
    match_id,
    season,
    gameweek,
    kickoff_time,
    team_name,
    was_home,
    segment_id,
    xg_for,
    xg_against,
    case
      when goals_for > goals_against then 3
      when goals_for = goals_against then 1
      else 0
    end as pts
  from public.betting_team_features_v2
), roll as (
  select *,
    count(*) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 5 preceding and 1 preceding
    ) as n5,
    avg(pts::numeric) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 5 preceding and 1 preceding
    ) as ppg5,
    avg(xg_for) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 5 preceding and 1 preceding
    ) as xgf5,
    avg(xg_against) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 5 preceding and 1 preceding
    ) as xga5,

    count(*) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 10 preceding and 1 preceding
    ) as n10,
    avg(pts::numeric) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 10 preceding and 1 preceding
    ) as ppg10,
    avg(xg_for) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 10 preceding and 1 preceding
    ) as xgf10,
    avg(xg_against) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 10 preceding and 1 preceding
    ) as xga10,

    count(*) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 15 preceding and 1 preceding
    ) as n15,
    avg(pts::numeric) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 15 preceding and 1 preceding
    ) as ppg15,
    avg(xg_for) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 15 preceding and 1 preceding
    ) as xgf15,
    avg(xg_against) over (
      partition by team_name, segment_id order by kickoff_time
      rows between 15 preceding and 1 preceding
    ) as xga15
  from base
), per_match as (
  select
    match_id,
    max(case when was_home and n5 = 5 then ppg5 end) as home_ppg5,
    max(case when was_home and n5 = 5 then xgf5 end) as home_xgf5,
    max(case when was_home and n5 = 5 then xga5 end) as home_xga5,
    max(case when not was_home and n5 = 5 then ppg5 end) as away_ppg5,
    max(case when not was_home and n5 = 5 then xgf5 end) as away_xgf5,
    max(case when not was_home and n5 = 5 then xga5 end) as away_xga5,

    max(case when was_home and n10 = 10 then ppg10 end) as home_ppg10,
    max(case when was_home and n10 = 10 then xgf10 end) as home_xgf10,
    max(case when was_home and n10 = 10 then xga10 end) as home_xga10,
    max(case when not was_home and n10 = 10 then ppg10 end) as away_ppg10,
    max(case when not was_home and n10 = 10 then xgf10 end) as away_xgf10,
    max(case when not was_home and n10 = 10 then xga10 end) as away_xga10,

    max(case when was_home and n15 = 15 then ppg15 end) as home_ppg15,
    max(case when was_home and n15 = 15 then xgf15 end) as home_xgf15,
    max(case when was_home and n15 = 15 then xga15 end) as home_xga15,
    max(case when not was_home and n15 = 15 then ppg15 end) as away_ppg15,
    max(case when not was_home and n15 = 15 then xgf15 end) as away_xgf15,
    max(case when not was_home and n15 = 15 then xga15 end) as away_xga15
  from roll
  group by match_id
)
update public.matches m
set
  home_ppg5 = p.home_ppg5,
  home_xgf5 = p.home_xgf5,
  home_xga5 = p.home_xga5,
  away_ppg5 = p.away_ppg5,
  away_xgf5 = p.away_xgf5,
  away_xga5 = p.away_xga5,
  home_ppg10 = p.home_ppg10,
  home_xgf10 = p.home_xgf10,
  home_xga10 = p.home_xga10,
  away_ppg10 = p.away_ppg10,
  away_xgf10 = p.away_xgf10,
  away_xga10 = p.away_xga10,
  home_ppg15 = p.home_ppg15,
  home_xgf15 = p.home_xgf15,
  home_xga15 = p.home_xga15,
  away_ppg15 = p.away_ppg15,
  away_xgf15 = p.away_xgf15,
  away_xga15 = p.away_xga15
from per_match p
where m.match_id = p.match_id;
