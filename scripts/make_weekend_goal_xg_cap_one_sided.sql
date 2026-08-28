-- Manual weekend venue review: one-sided +1.0 goal-vs-xG cap.
-- Actual goals are never increased. Only overperformance beyond xG + 1.0 is capped down.

create or replace view public.betting_manual_weekend_capped_actuals as
with fixture_base as (
  select f.fixture_id, f.kickoff_time, f.home_team, f.away_team,
         hs.segment_id as home_segment_id,
         avs.segment_id as away_segment_id
  from public.betting_manual_fixtures f
  left join lateral (
    select b.segment_id
    from public.betting_team_features_v2 b
    where b.team_name = f.home_team and b.kickoff_time < f.kickoff_time
    order by b.kickoff_time desc
    limit 1
  ) hs on true
  left join lateral (
    select b.segment_id
    from public.betting_team_features_v2 b
    where b.team_name = f.away_team and b.kickoff_time < f.kickoff_time
    order by b.kickoff_time desc
    limit 1
  ) avs on true
)
select f.fixture_id,
       1.0::double precision as goal_xg_residual_cap,
       hv.gf_capped as home_vgf8_capped,
       hv.ga_capped as home_vga8_capped,
       av.gf_capped as away_vgf8_capped,
       av.ga_capped as away_vga8_capped
from fixture_base f
left join lateral (
  select
    avg(case when r.xg_for is null then r.goals_for::double precision
             else least(r.goals_for::double precision, r.xg_for::double precision + 1.0::double precision) end)::double precision as gf_capped,
    avg(case when r.xg_against is null then r.goals_against::double precision
             else least(r.goals_against::double precision, r.xg_against::double precision + 1.0::double precision) end)::double precision as ga_capped
  from (
    select b.goals_for,b.goals_against,b.xg_for,b.xg_against
    from public.betting_team_features_v2 b
    where b.team_name=f.home_team and b.was_home=true and b.segment_id=f.home_segment_id and b.kickoff_time<f.kickoff_time
    order by b.kickoff_time desc
    limit 8
  ) r
) hv on true
left join lateral (
  select
    avg(case when r.xg_for is null then r.goals_for::double precision
             else least(r.goals_for::double precision, r.xg_for::double precision + 1.0::double precision) end)::double precision as gf_capped,
    avg(case when r.xg_against is null then r.goals_against::double precision
             else least(r.goals_against::double precision, r.xg_against::double precision + 1.0::double precision) end)::double precision as ga_capped
  from (
    select b.goals_for,b.goals_against,b.xg_for,b.xg_against
    from public.betting_team_features_v2 b
    where b.team_name=f.away_team and b.was_home=false and b.segment_id=f.away_segment_id and b.kickoff_time<f.kickoff_time
    order by b.kickoff_time desc
    limit 8
  ) r
) av on true;

update public.betting_manual_weekend_snapshot s
set goal_xg_residual_cap=c.goal_xg_residual_cap,
    home_vgf8_capped=c.home_vgf8_capped,
    home_vga8_capped=c.home_vga8_capped,
    away_vgf8_capped=c.away_vgf8_capped,
    away_vga8_capped=c.away_vga8_capped,
    calculated_at=now()
from public.betting_manual_weekend_capped_actuals c
where c.fixture_id=s.fixture_id;
