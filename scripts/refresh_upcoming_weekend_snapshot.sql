-- Run after source imports, and before add_weekend_v3_venue8_comparison.sql.
-- Refresh only fixtures that have not kicked off. Played fixtures stay frozen.
begin;
refresh materialized view public.betting_team_features_v2_cache;

with fixtures as (
  select f.*,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.home_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) home_segment,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.away_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) away_segment
  from public.betting_manual_fixtures f where f.kickoff_time>now()
), sides as (
  select f.fixture_id,f.kickoff_time,v.*
  from fixtures f cross join lateral (values
    ('home',f.home_team,true,f.home_segment),
    ('away',f.away_team,false,f.away_segment)
  ) v(side,team_name,was_home,segment_id)
), inputs as (
  select f.fixture_id,f.side,v.*,o.*
  from sides f
  cross join lateral (
    select count(*) filter(where rn<=8)::int n8,
      avg(ppg) filter(where rn<=8) ppg8,
      avg(goals_for) filter(where rn<=8) gf8,avg(goals_against) filter(where rn<=8) ga8,
      avg(xg_for) filter(where rn<=8) xgf8,avg(xg_against) filter(where rn<=8) xga8,
      avg(case when xg_for is null then goals_for else least(goals_for,xg_for+1) end) filter(where rn<=8) cgf8,
      avg(case when xg_against is null then goals_against else least(goals_against,xg_against+1) end) filter(where rn<=8) cga8,
      count(*)::int n18,avg(ppg) ppg18,avg(xg_for) xgf18,avg(xg_against) xga18
    from (select b.*,row_number() over(order by b.kickoff_time desc,b.match_id desc) rn,
      case when result='W' then 3 when result='D' then 1 else 0 end ppg
      from public.betting_team_features_v2_cache b
      where b.team_name=f.team_name and b.segment_id=f.segment_id and b.was_home=f.was_home and b.kickoff_time<f.kickoff_time
      order by b.kickoff_time desc,b.match_id desc limit 18) q
  ) v
  cross join lateral (
    select count(*)::int n30,avg(case when result='W' then 3 when result='D' then 1 else 0 end) ppg30
    from (select b.result from public.betting_team_features_v2_cache b
      where b.team_name=f.team_name and b.segment_id=f.segment_id and b.kickoff_time<f.kickoff_time
      order by b.kickoff_time desc,b.match_id desc limit 30) q
  ) o
)
insert into public.betting_manual_weekend_snapshot (
  fixture_id,home_n8,away_n8,home_vppg8,away_vppg8,
  home_vgf8,home_vga8,home_vxgf8,home_vxga8,away_vgf8,away_vga8,away_vxgf8,away_vxga8,
  league_home_goals,league_away_goals,league_home_xg,league_away_xg,
  goal_xg_residual_cap,home_vgf8_capped,home_vga8_capped,away_vgf8_capped,away_vga8_capped,
  home_n30,away_n30,home_ppg30,away_ppg30,
  home_vn18,away_vn18,home_vppg18,away_vppg18,home_vxgf18,home_vxga18,away_vxgf18,away_vxga18,calculated_at
)
select f.fixture_id,h.n8,a.n8,h.ppg8,a.ppg8,h.gf8,h.ga8,h.xgf8,h.xga8,a.gf8,a.ga8,a.xgf8,a.xga8,
  l.hg,l.ag,l.hxg,l.axg,1,h.cgf8,h.cga8,a.cgf8,a.cga8,h.n30,a.n30,h.ppg30,a.ppg30,
  h.n18,a.n18,h.ppg18,a.ppg18,h.xgf18,h.xga18,a.xgf18,a.xga18,now()
from fixtures f join inputs h on h.fixture_id=f.fixture_id and h.side='home'
join inputs a on a.fixture_id=f.fixture_id and a.side='away'
cross join lateral (
  select coalesce(avg(goals_for) filter(where was_home),1.5) hg,
    coalesce(avg(goals_for) filter(where not was_home),1.2) ag,
    coalesce(avg(xg_for) filter(where was_home),1.5) hxg,
    coalesce(avg(xg_for) filter(where not was_home),1.2) axg
  from public.betting_team_features_v2_cache b
  where b.kickoff_time<f.kickoff_time and b.kickoff_time>=f.kickoff_time-interval '400 days'
) l
on conflict (fixture_id) do update set
  home_n8=excluded.home_n8,away_n8=excluded.away_n8,home_vppg8=excluded.home_vppg8,away_vppg8=excluded.away_vppg8,
  home_vgf8=excluded.home_vgf8,home_vga8=excluded.home_vga8,home_vxgf8=excluded.home_vxgf8,home_vxga8=excluded.home_vxga8,
  away_vgf8=excluded.away_vgf8,away_vga8=excluded.away_vga8,away_vxgf8=excluded.away_vxgf8,away_vxga8=excluded.away_vxga8,
  league_home_goals=excluded.league_home_goals,league_away_goals=excluded.league_away_goals,
  league_home_xg=excluded.league_home_xg,league_away_xg=excluded.league_away_xg,
  goal_xg_residual_cap=excluded.goal_xg_residual_cap,
  home_vgf8_capped=excluded.home_vgf8_capped,home_vga8_capped=excluded.home_vga8_capped,
  away_vgf8_capped=excluded.away_vgf8_capped,away_vga8_capped=excluded.away_vga8_capped,
  home_n30=excluded.home_n30,away_n30=excluded.away_n30,home_ppg30=excluded.home_ppg30,away_ppg30=excluded.away_ppg30,
  home_vn18=excluded.home_vn18,away_vn18=excluded.away_vn18,home_vppg18=excluded.home_vppg18,away_vppg18=excluded.away_vppg18,
  home_vxgf18=excluded.home_vxgf18,home_vxga18=excluded.home_vxga18,away_vxgf18=excluded.away_vxgf18,away_vxga18=excluded.away_vxga18,
  calculated_at=excluded.calculated_at;
commit;
