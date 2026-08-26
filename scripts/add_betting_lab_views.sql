-- Betting Lab model inputs.
-- Uses FPL match-level expected-goal fields so the model has continuous PL coverage from 2016/17 onward.

create or replace view public.betting_team_match_v1 as
with team_fpl as (
  select
    season,
    gameweek,
    kickoff_time,
    team_name,
    opponent_team,
    was_home,
    sum(coalesce(expected_goals,0))::numeric as xg_for,
    sum(coalesce(goals_scored,0))::integer as fpl_goals_for
  from public.fpl_player_match_stats
  group by season,gameweek,kickoff_time,team_name,opponent_team,was_home
), paired as (
  select
    a.*,
    b.xg_for as xg_against
  from team_fpl a
  left join team_fpl b
    on b.season=a.season
   and b.gameweek=a.gameweek
   and b.kickoff_time=a.kickoff_time
   and b.team_name=a.opponent_team
   and b.opponent_team=a.team_name
)
select
  p.season,
  p.gameweek,
  p.kickoff_time,
  p.team_name,
  p.opponent_team,
  p.was_home,
  p.xg_for,
  p.xg_against,
  case when p.was_home then m.home_score else m.away_score end::integer as goals_for,
  case when p.was_home then m.away_score else m.home_score end::integer as goals_against,
  case
    when m.home_score is null or m.away_score is null then null
    when (case when p.was_home then m.home_score else m.away_score end) > (case when p.was_home then m.away_score else m.home_score end) then 'W'
    when (case when p.was_home then m.home_score else m.away_score end) = (case when p.was_home then m.away_score else m.home_score end) then 'D'
    else 'L'
  end as result
from paired p
left join public.matches m
  on m.season=p.season
 and m.gameweek=p.gameweek
 and (
   (p.was_home=true and m.home_team=p.team_name and m.away_team=p.opponent_team)
   or
   (p.was_home=false and m.away_team=p.team_name and m.home_team=p.opponent_team)
 );

grant select on public.betting_team_match_v1 to anon, authenticated;

create or replace view public.betting_player_goal_profile_v1 as
with played as (
  select
    season,
    player_code,
    player_name,
    team_name,
    position,
    kickoff_time,
    minutes,
    goals_scored,
    expected_goals,
    value,
    selected,
    row_number() over(partition by season,player_code order by kickoff_time desc,gameweek desc,fixture_id desc) as recent_rank
  from public.fpl_player_match_stats
  where player_code is not null and minutes > 0
), agg as (
  select
    season,
    player_code,
    (array_agg(player_name order by kickoff_time desc))[1] as player_name,
    (array_agg(team_name order by kickoff_time desc))[1] as team_name,
    (array_agg(position order by kickoff_time desc))[1] as position,
    count(*)::integer as appearances,
    sum(minutes)::integer as minutes,
    sum(coalesce(goals_scored,0))::integer as goals,
    sum(coalesce(expected_goals,0))::numeric as xg,
    case when sum(minutes)>0 then (sum(coalesce(expected_goals,0))*90.0/sum(minutes))::numeric else null end as xg_per90,
    avg(minutes) filter(where recent_rank<=5)::numeric as recent5_avg_minutes,
    sum(minutes) filter(where recent_rank<=5)::integer as recent5_minutes,
    sum(coalesce(expected_goals,0)) filter(where recent_rank<=5)::numeric as recent5_xg,
    count(*) filter(where recent_rank<=5)::integer as recent5_apps,
    (array_agg(value order by kickoff_time desc))[1]::integer as latest_value,
    (array_agg(selected order by kickoff_time desc))[1]::bigint as latest_selected
  from played
  group by season,player_code
)
select * from agg;

grant select on public.betting_player_goal_profile_v1 to anon, authenticated;
