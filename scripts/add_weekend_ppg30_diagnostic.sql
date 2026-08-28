alter table public.betting_manual_weekend_snapshot
  add column if not exists home_n30 int,
  add column if not exists away_n30 int,
  add column if not exists home_ppg30 numeric,
  add column if not exists away_ppg30 numeric;

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
         hp.n as home_n30,hp.ppg as home_ppg30,
         ap.n as away_n30,ap.ppg as away_ppg30
  from fixture_segments fs
  left join lateral (
    select count(*)::int as n,
           avg(case when r.result='W' then 3 when r.result='D' then 1 else 0 end)::float as ppg
    from (
      select b.result
      from public.betting_team_features_v2 b
      where b.team_name=fs.home_team
        and b.segment_id=fs.home_segment_id
        and b.kickoff_time<fs.kickoff_time
      order by b.kickoff_time desc
      limit 30
    ) r
  ) hp on true
  left join lateral (
    select count(*)::int as n,
           avg(case when r.result='W' then 3 when r.result='D' then 1 else 0 end)::float as ppg
    from (
      select b.result
      from public.betting_team_features_v2 b
      where b.team_name=fs.away_team
        and b.segment_id=fs.away_segment_id
        and b.kickoff_time<fs.kickoff_time
      order by b.kickoff_time desc
      limit 30
    ) r
  ) ap on true
)
update public.betting_manual_weekend_snapshot s
set home_n30=d.home_n30,
    away_n30=d.away_n30,
    home_ppg30=d.home_ppg30,
    away_ppg30=d.away_ppg30,
    calculated_at=now()
from diagnostic d
where d.fixture_id=s.fixture_id;
