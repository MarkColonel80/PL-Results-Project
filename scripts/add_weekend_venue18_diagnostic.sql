alter table public.betting_manual_weekend_snapshot
  add column if not exists home_vn18 int,
  add column if not exists away_vn18 int,
  add column if not exists home_vppg18 numeric,
  add column if not exists away_vppg18 numeric,
  add column if not exists home_vxgf18 numeric,
  add column if not exists home_vxga18 numeric,
  add column if not exists away_vxgf18 numeric,
  add column if not exists away_vxga18 numeric;

with fixture_segments as (
  select f.fixture_id,f.home_team,f.away_team,f.kickoff_time,
    (select b.segment_id
       from public.betting_team_features_v2 b
      where b.team_name=f.home_team and b.kickoff_time<f.kickoff_time
      order by b.kickoff_time desc limit 1) as home_segment_id,
    (select b.segment_id
       from public.betting_team_features_v2 b
      where b.team_name=f.away_team and b.kickoff_time<f.kickoff_time
      order by b.kickoff_time desc limit 1) as away_segment_id
  from public.betting_manual_fixtures f
), diagnostic as (
  select fs.fixture_id,
         hv.n as home_vn18,hv.ppg as home_vppg18,hv.xgf as home_vxgf18,hv.xga as home_vxga18,
         av.n as away_vn18,av.ppg as away_vppg18,av.xgf as away_vxgf18,av.xga as away_vxga18
  from fixture_segments fs
  left join lateral (
    select count(*)::int as n,
           avg(case when r.result='W' then 3 when r.result='D' then 1 else 0 end)::float as ppg,
           avg(r.xg_for)::float as xgf,
           avg(r.xg_against)::float as xga
    from (
      select b.result,b.xg_for,b.xg_against
      from public.betting_team_features_v2 b
      where b.team_name=fs.home_team
        and b.segment_id=fs.home_segment_id
        and b.was_home=true
        and b.kickoff_time<fs.kickoff_time
      order by b.kickoff_time desc
      limit 18
    ) r
  ) hv on true
  left join lateral (
    select count(*)::int as n,
           avg(case when r.result='W' then 3 when r.result='D' then 1 else 0 end)::float as ppg,
           avg(r.xg_for)::float as xgf,
           avg(r.xg_against)::float as xga
    from (
      select b.result,b.xg_for,b.xg_against
      from public.betting_team_features_v2 b
      where b.team_name=fs.away_team
        and b.segment_id=fs.away_segment_id
        and b.was_home=false
        and b.kickoff_time<fs.kickoff_time
      order by b.kickoff_time desc
      limit 18
    ) r
  ) av on true
)
update public.betting_manual_weekend_snapshot s
set home_vn18=d.home_vn18,
    away_vn18=d.away_vn18,
    home_vppg18=d.home_vppg18,
    away_vppg18=d.away_vppg18,
    home_vxgf18=d.home_vxgf18,
    home_vxga18=d.home_vxga18,
    away_vxgf18=d.away_vxgf18,
    away_vxga18=d.away_vxga18,
    calculated_at=now()
from diagnostic d
where d.fixture_id=s.fixture_id;
