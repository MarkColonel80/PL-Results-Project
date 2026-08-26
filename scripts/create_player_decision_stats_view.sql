-- Read-only product view used by /insights.
-- Combines season-level FPL/football stats with the latest recorded FPL price
-- and derives simple decision-support metrics. It does not alter source data.

create or replace view public.player_decision_stats_v1 as
with latest_fpl as (
  select distinct on (season, player_code)
    season,
    player_code,
    value,
    selected,
    gameweek,
    kickoff_time
  from public.fpl_player_match_stats
  where player_code is not null
  order by season, player_code, gameweek desc nulls last, kickoff_time desc nulls last
)
select
  p.season,
  p.player_code,
  p.player_name,
  p.team_name,
  p.position,
  p.appearances,
  p.starts,
  p.minutes,
  p.goals,
  p.assists,
  p.goal_contributions,
  p.match_xg as xg,
  p.match_xa as xa,
  p.fpl_points,
  l.value as price_tenths,
  l.selected,
  (coalesce(p.match_xg,0) + coalesce(p.match_xa,0))::numeric as xgi,
  case when coalesce(p.minutes,0) > 0 then ((coalesce(p.match_xg,0) + coalesce(p.match_xa,0)) * 90 / p.minutes)::numeric end as xgi_per90,
  (coalesce(p.goals,0) - coalesce(p.match_xg,0))::numeric as goals_minus_xg,
  (coalesce(p.goal_contributions,0) - (coalesce(p.match_xg,0) + coalesce(p.match_xa,0)))::numeric as gi_minus_xgi,
  case when coalesce(p.minutes,0) > 0 then (coalesce(p.fpl_points,0) * 90.0 / p.minutes)::numeric end as fpl_per90,
  case when coalesce(l.value,0) > 0 then (coalesce(p.fpl_points,0) / (l.value / 10.0))::numeric end as points_per_million
from public.player_season_stats p
left join latest_fpl l using (season, player_code)
where p.fpl_points is not null;

grant select on public.player_decision_stats_v1 to anon, authenticated;
