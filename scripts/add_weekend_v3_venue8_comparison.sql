-- Adds and refreshes the research-only v3_24_venue8_50_noppg comparison on the manual weekend snapshot.
-- This does not alter the existing weekend PPG8/xG tie-break pick.
-- PPG10 is retained in the snapshot as a diagnostic only and does not affect the candidate probability.
-- Refresh the feature cache first so newly loaded league matches cannot be omitted from the comparison.

refresh materialized view public.betting_team_features_v2_cache;

alter table public.betting_manual_weekend_snapshot
  add column if not exists candidate_model_version text,
  add column if not exists candidate_home_n24 integer,
  add column if not exists candidate_away_n24 integer,
  add column if not exists candidate_home_n10 integer,
  add column if not exists candidate_away_n10 integer,
  add column if not exists candidate_home_ppg10 numeric,
  add column if not exists candidate_away_ppg10 numeric,
  add column if not exists candidate_home_lambda numeric,
  add column if not exists candidate_away_lambda numeric,
  add column if not exists candidate_home_prob numeric,
  add column if not exists candidate_draw_prob numeric,
  add column if not exists candidate_away_prob numeric,
  add column if not exists candidate_calculated_at timestamptz;

with fx as (
  select f.*,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.home_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) home_segment,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.away_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) away_segment
  from public.betting_manual_fixtures f
), inp as (
  select f.fixture_id,
    hs.n24 home_n24,hs.xgf24 home_xgf24,hs.xga24 home_xga24,hs.cgf24 home_cgf24,hs.cga24 home_cga24,
    axs.n24 away_n24,axs.xgf24 away_xgf24,axs.xga24 away_xga24,axs.cgf24 away_cgf24,axs.cga24 away_cga24,
    hp.n10 home_n10,hp.ppg10 home_ppg10,ap.n10 away_n10,ap.ppg10 away_ppg10,
    hv.n8 home_n8,hv.xgf8 home_vxgf8,hv.xga8 home_vxga8,hv.cgf8 home_vcgf8,hv.cga8 home_vcga8,
    av.n8 away_n8,av.xgf8 away_vxgf8,av.xga8 away_vxga8,av.cgf8 away_vcgf8,av.cga8 away_vcga8,
    lg.lhome,lg.laway
  from fx f
  left join lateral (
    select count(*)::int n24,avg(xg_for) xgf24,avg(xg_against) xga24,
      avg(case when xg_for is null then goals_for::numeric else least(goals_for::numeric,xg_for+1) end) cgf24,
      avg(case when xg_against is null then goals_against::numeric else least(goals_against::numeric,xg_against+1) end) cga24
    from (select * from public.betting_team_features_v2_cache b where b.team_name=f.home_team and b.segment_id=f.home_segment and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 24) q
  ) hs on true
  left join lateral (
    select count(*)::int n24,avg(xg_for) xgf24,avg(xg_against) xga24,
      avg(case when xg_for is null then goals_for::numeric else least(goals_for::numeric,xg_for+1) end) cgf24,
      avg(case when xg_against is null then goals_against::numeric else least(goals_against::numeric,xg_against+1) end) cga24
    from (select * from public.betting_team_features_v2_cache b where b.team_name=f.away_team and b.segment_id=f.away_segment and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 24) q
  ) axs on true
  left join lateral (
    select count(*)::int n10,avg(case when goals_for>goals_against then 3 when goals_for=goals_against then 1 else 0 end)::numeric ppg10
    from (select * from public.betting_team_features_v2_cache b where b.team_name=f.home_team and b.segment_id=f.home_segment and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 10) q
  ) hp on true
  left join lateral (
    select count(*)::int n10,avg(case when goals_for>goals_against then 3 when goals_for=goals_against then 1 else 0 end)::numeric ppg10
    from (select * from public.betting_team_features_v2_cache b where b.team_name=f.away_team and b.segment_id=f.away_segment and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 10) q
  ) ap on true
  left join lateral (
    select count(*)::int n8,avg(xg_for) xgf8,avg(xg_against) xga8,
      avg(case when xg_for is null then goals_for::numeric else least(goals_for::numeric,xg_for+1) end) cgf8,
      avg(case when xg_against is null then goals_against::numeric else least(goals_against::numeric,xg_against+1) end) cga8
    from (select * from public.betting_team_features_v2_cache b where b.team_name=f.home_team and b.segment_id=f.home_segment and b.was_home and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 8) q
  ) hv on true
  left join lateral (
    select count(*)::int n8,avg(xg_for) xgf8,avg(xg_against) xga8,
      avg(case when xg_for is null then goals_for::numeric else least(goals_for::numeric,xg_for+1) end) cgf8,
      avg(case when xg_against is null then goals_against::numeric else least(goals_against::numeric,xg_against+1) end) cga8
    from (select * from public.betting_team_features_v2_cache b where b.team_name=f.away_team and b.segment_id=f.away_segment and not b.was_home and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 8) q
  ) av on true
  left join lateral (
    select 0.35*avg(goals_for::numeric)+0.65*avg(xg_for) lhome,
      0.35*avg(goals_against::numeric)+0.65*avg(xg_against) laway
    from (select * from public.betting_team_features_v2_cache b where b.was_home and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 15) q
  ) lg on true
), calc as (
  select *, (lhome+laway)/2 lmid,
    ((0.65*home_xgf24+0.35*home_cgf24)*home_n24+((lhome+laway)/2)*4)/(home_n24+4) hatt,
    ((0.65*home_xga24+0.35*home_cga24)*home_n24+((lhome+laway)/2)*4)/(home_n24+4) hdef,
    ((0.65*away_xgf24+0.35*away_cgf24)*away_n24+((lhome+laway)/2)*4)/(away_n24+4) aatt,
    ((0.65*away_xga24+0.35*away_cga24)*away_n24+((lhome+laway)/2)*4)/(away_n24+4) adef,
    (home_vxgf8+home_vcgf8)/2 hvatt,(home_vxga8+home_vcga8)/2 hvdef,
    (away_vxgf8+away_vcgf8)/2 avatt,(away_vxga8+away_vcga8)/2 avdef
  from inp
), lam as (
  select *,
    case when home_n8>=4 and away_n8>=4 and home_n24>0 and away_n24>0 then greatest(0.15,least(4.5,
      sqrt(lhome*sqrt(hvatt*avdef))*power(greatest(0.05,(hatt/lmid)*(adef/lmid)),0.75))) end home_lambda,
    case when home_n8>=4 and away_n8>=4 and home_n24>0 and away_n24>0 then greatest(0.15,least(4.5,
      sqrt(laway*sqrt(avatt*hvdef))*power(greatest(0.05,(aatt/lmid)*(hdef/lmid)),0.75))) end away_lambda
  from calc
), scored as (
  select l.fixture_id,l.home_n24,l.away_n24,l.home_n10,l.away_n10,l.home_ppg10,l.away_ppg10,l.home_lambda,l.away_lambda,
    p.home_prob,p.draw_prob,p.away_prob
  from lam l
  left join lateral public.poisson_1x2_probs(l.home_lambda::double precision,l.away_lambda::double precision) p
    on l.home_lambda is not null and l.away_lambda is not null
)
update public.betting_manual_weekend_snapshot s
set candidate_model_version='v3_24_venue8_50_noppg',
    candidate_home_n24=x.home_n24,
    candidate_away_n24=x.away_n24,
    candidate_home_n10=x.home_n10,
    candidate_away_n10=x.away_n10,
    candidate_home_ppg10=x.home_ppg10,
    candidate_away_ppg10=x.away_ppg10,
    candidate_home_lambda=x.home_lambda,
    candidate_away_lambda=x.away_lambda,
    candidate_home_prob=x.home_prob,
    candidate_draw_prob=x.draw_prob,
    candidate_away_prob=x.away_prob,
    candidate_calculated_at=now()
from scored x
where x.fixture_id=s.fixture_id;
