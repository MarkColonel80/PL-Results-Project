-- Adds persistent venue-specific rolling metrics over the previous 8 same-venue matches.
-- Safe addition: leaves existing team_form_window_cache and its dependents intact.

create materialized view public.team_form_window8_cache as
with base as (
  select
    tm.match_id,
    tm.season,
    tm.gameweek,
    tm.kickoff_time,
    tm.team_name,
    tm.opponent_team,
    tm.was_home,
    tm.xg_for,
    tm.xg_against,
    tf.segment_id,
    case when tm.result='W' then 3 when tm.result='D' then 1 else 0 end::numeric as pts
  from public.betting_team_match_v2 tm
  join public.betting_team_features_v2 tf
    on tf.match_id=tm.match_id and tf.team_name=tm.team_name
), venue as (
  select
    b.*,
    count(*) over (
      partition by b.team_name,b.segment_id,b.was_home
      order by b.kickoff_time
      rows between 8 preceding and 1 preceding
    )::int as vn8,
    avg(b.pts) over (
      partition by b.team_name,b.segment_id,b.was_home
      order by b.kickoff_time
      rows between 8 preceding and 1 preceding
    ) as vppg8,
    avg(b.xg_for) over (
      partition by b.team_name,b.segment_id,b.was_home
      order by b.kickoff_time
      rows between 8 preceding and 1 preceding
    ) as vxgf8,
    avg(b.xg_against) over (
      partition by b.team_name,b.segment_id,b.was_home
      order by b.kickoff_time
      rows between 8 preceding and 1 preceding
    ) as vxga8
  from base b
)
select match_id,season,gameweek,kickoff_time,team_name,opponent_team,was_home,segment_id,vn8,vppg8,vxgf8,vxga8
from venue;

create unique index team_form_window8_cache_match_team_uidx
  on public.team_form_window8_cache(match_id,team_name);

create view public.team_form_window_cache_with_v8 as
select
  c.*,
  v.vn8,
  v.vppg8,
  v.vxgf8,
  v.vxga8
from public.team_form_window_cache c
left join public.team_form_window8_cache v
  on v.match_id=c.match_id and v.team_name=c.team_name;
