-- Manual weekend venue model: cap each match's actual goal residual vs xG at +/-1.0
-- before averaging the last eight venue matches and blending actual goals 50/50 with raw xG.
-- Applied to Supabase on 2026-08-28 as migration: cap_weekend_goal_xg_residuals_at_one

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
             else r.xg_for::double precision + greatest(-1.0::double precision, least(1.0::double precision, r.goals_for::double precision - r.xg_for::double precision)) end)::double precision as gf_capped,
    avg(case when r.xg_against is null then r.goals_against::double precision
             else r.xg_against::double precision + greatest(-1.0::double precision, least(1.0::double precision, r.goals_against::double precision - r.xg_against::double precision)) end)::double precision as ga_capped
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
             else r.xg_for::double precision + greatest(-1.0::double precision, least(1.0::double precision, r.goals_for::double precision - r.xg_for::double precision)) end)::double precision as gf_capped,
    avg(case when r.xg_against is null then r.goals_against::double precision
             else r.xg_against::double precision + greatest(-1.0::double precision, least(1.0::double precision, r.goals_against::double precision - r.xg_against::double precision)) end)::double precision as ga_capped
  from (
    select b.goals_for,b.goals_against,b.xg_for,b.xg_against
    from public.betting_team_features_v2 b
    where b.team_name=f.away_team and b.was_home=false and b.segment_id=f.away_segment_id and b.kickoff_time<f.kickoff_time
    order by b.kickoff_time desc
    limit 8
  ) r
) av on true;

-- The original analysis view is preserved as an explicit legacy/QA view.
alter view public.betting_manual_weekend_analysis rename to betting_manual_weekend_analysis_uncapped;

create view public.betting_manual_weekend_analysis as
with b as (
  select u.*, c.goal_xg_residual_cap,
         c.home_vgf8_capped,c.home_vga8_capped,c.away_vgf8_capped,c.away_vga8_capped,
         case when u.home_vxgf8 is not null and c.home_vgf8_capped is not null then (u.home_vxgf8+c.home_vgf8_capped)/2.0 end as new_home_adj_xgf8,
         case when u.home_vxga8 is not null and c.home_vga8_capped is not null then (u.home_vxga8+c.home_vga8_capped)/2.0 end as new_home_adj_xga8,
         case when u.away_vxgf8 is not null and c.away_vgf8_capped is not null then (u.away_vxgf8+c.away_vgf8_capped)/2.0 end as new_away_adj_xgf8,
         case when u.away_vxga8 is not null and c.away_vga8_capped is not null then (u.away_vxga8+c.away_vga8_capped)/2.0 end as new_away_adj_xga8
  from public.betting_manual_weekend_analysis_uncapped u
  left join public.betting_manual_weekend_capped_actuals c using (fixture_id)
), l as (
  select b.*,
         case when new_home_adj_xgf8 is not null and new_away_adj_xga8 is not null
              then greatest(0.15::double precision,least(4.5::double precision,lhg*power((new_home_adj_xgf8/nullif(lhxg,0))*(new_away_adj_xga8/nullif(lhxg,0)),0.8))) end as new_adj_home_lambda,
         case when new_away_adj_xgf8 is not null and new_home_adj_xga8 is not null
              then greatest(0.15::double precision,least(4.5::double precision,lag*power((new_away_adj_xgf8/nullif(laxg,0))*(new_home_adj_xga8/nullif(laxg,0)),0.8))) end as new_adj_away_lambda
  from b
), p as (
  select l.*, px.home_prob as new_adj_home_prob, px.draw_prob as new_adj_draw_prob, px.away_prob as new_adj_away_prob
  from l
  left join lateral public.poisson_1x2_probs(l.new_adj_home_lambda,l.new_adj_away_lambda) px(home_prob,draw_prob,away_prob)
    on l.new_adj_home_lambda is not null and l.new_adj_away_lambda is not null
)
select fixture_id,season,kickoff_time,home_team,away_team,
       market_home_odds,market_draw_odds,market_away_odds,market_source,market_snapshot_at,notes,
       home_segment_id,away_segment_id,home_n8,home_vppg8,home_vgf8,home_vga8,home_vxgf8,home_vxga8,
       away_n8,away_vppg8,away_vgf8,away_vga8,away_vxgf8,away_vxga8,
       new_home_adj_xgf8 as home_adj_xgf8,new_home_adj_xga8 as home_adj_xga8,
       new_away_adj_xgf8 as away_adj_xgf8,new_away_adj_xga8 as away_adj_xga8,
       lhg,lag,lhxg,laxg,new_adj_home_lambda as adj_home_lambda,new_adj_away_lambda as adj_away_lambda,
       new_adj_home_prob as adj_home_prob,new_adj_draw_prob as adj_draw_prob,new_adj_away_prob as adj_away_prob,
       abs(coalesce(home_vppg8,0)-coalesce(away_vppg8,0)) as venue_ppg_gap,
       case when home_n8=8 and away_n8=8 and abs(home_vppg8-away_vppg8)<=0.30 then true else false end as use_adjusted_xg_tiebreak,
       case when home_n8<8 or away_n8<8 then 'LIMITED_HISTORY'
            when abs(home_vppg8-away_vppg8)<=0.30 then
              case when new_adj_home_prob>=new_adj_draw_prob and new_adj_home_prob>=new_adj_away_prob then 'H'
                   when new_adj_draw_prob>=new_adj_away_prob then 'D' else 'A' end
            when home_vppg8>away_vppg8 then 'H'
            when away_vppg8>home_vppg8 then 'A' else 'D' end as manual_pick,
       market_home_prob,market_draw_prob,market_away_prob,
       goal_xg_residual_cap,home_vgf8_capped,home_vga8_capped,away_vgf8_capped,away_vga8_capped
from p;

alter table public.betting_manual_weekend_snapshot add column if not exists goal_xg_residual_cap numeric;
alter table public.betting_manual_weekend_snapshot add column if not exists home_vgf8_capped numeric;
alter table public.betting_manual_weekend_snapshot add column if not exists home_vga8_capped numeric;
alter table public.betting_manual_weekend_snapshot add column if not exists away_vgf8_capped numeric;
alter table public.betting_manual_weekend_snapshot add column if not exists away_vga8_capped numeric;

update public.betting_manual_weekend_snapshot s
set goal_xg_residual_cap=c.goal_xg_residual_cap,
    home_vgf8_capped=c.home_vgf8_capped,
    home_vga8_capped=c.home_vga8_capped,
    away_vgf8_capped=c.away_vgf8_capped,
    away_vga8_capped=c.away_vga8_capped,
    calculated_at=now()
from public.betting_manual_weekend_capped_actuals c
where c.fixture_id=s.fixture_id;
