-- Betting Model v6: persistent finishing / defensive xG residual features
-- Date: 2026-08-28
-- Purpose: preserve rolling Goals-xG and Goals Against-xGA signals without overwriting raw xG.

create materialized view if not exists public.betting_team_residual_features_v6 as
select
  season,
  gameweek,
  match_id,
  kickoff_time,
  team_name,
  opponent_team,
  was_home,
  n10,
  n20,
  n30,
  (gf10 - xgf10)::double precision as finish_resid10,
  (ga10 - xga10)::double precision as defend_resid10,
  (gf20 - xgf20)::double precision as finish_resid20,
  (ga20 - xga20)::double precision as defend_resid20,
  (gf30 - xgf30)::double precision as finish_resid30,
  (ga30 - xga30)::double precision as defend_resid30
from public.betting_team_features_weighted_test
where xgf10 is not null and xga10 is not null
  and xgf20 is not null and xga20 is not null
  and xgf30 is not null and xga30 is not null;

create unique index if not exists betting_team_residual_features_v6_uq
  on public.betting_team_residual_features_v6(match_id, team_name);
create index if not exists betting_team_residual_features_v6_team_time_idx
  on public.betting_team_residual_features_v6(team_name, kickoff_time);

-- Research showed 30-match residuals are more stable than 10/20-match residuals.
-- Development optimum was ~20-25% trust in the residual. We use 25% maximum,
-- automatically shrunk when fewer than 30 prior matches are available.
create materialized view if not exists public.betting_model_v6_residual_xg_component as
with t as (
  select w.match_id,w.season,w.kickoff_time,w.team_name,w.was_home,w.n30,
         w.xgf30::double precision xgf30,w.xga30::double precision xga30,
         w.league_home_goals::double precision lhg,w.league_away_goals::double precision lag,
         w.league_home_xg::double precision lhxg,w.league_away_xg::double precision laxg,
         r.finish_resid30,r.defend_resid30
  from public.betting_team_features_weighted_test w
  join public.betting_team_residual_features_v6 r using(match_id,team_name)
), m as (
  select h.match_id,h.season,h.kickoff_time,
         h.team_name home_team,a.team_name away_team,
         h.xgf30 hxgf,h.xga30 hxga,a.xgf30 axgf,a.xga30 axga,
         h.finish_resid30 home_finish_resid30,h.defend_resid30 home_defend_resid30,
         a.finish_resid30 away_finish_resid30,a.defend_resid30 away_defend_resid30,
         0.25*least(1.0,h.n30/30.0) home_residual_weight,
         0.25*least(1.0,a.n30/30.0) away_residual_weight,
         h.lhg,h.lag,h.lhxg,h.laxg
  from t h join t a on a.match_id=h.match_id and a.was_home=false
  where h.was_home=true
), l as (
  select m.*,
    greatest(0.15,least(4.5,lhg*power(greatest(0.05,
      (greatest(0.05,hxgf+home_residual_weight*home_finish_resid30)/lhxg)*
      (greatest(0.05,axga+away_residual_weight*away_defend_resid30)/lhxg)),0.8))) home_lambda,
    greatest(0.15,least(4.5,lag*power(greatest(0.05,
      (greatest(0.05,axgf+away_residual_weight*away_finish_resid30)/laxg)*
      (greatest(0.05,hxga+home_residual_weight*home_defend_resid30)/laxg)),0.8))) away_lambda
  from m
)
select l.*,p.home_prob,p.draw_prob,p.away_prob
from l cross join lateral public.poisson_1x2_probs(l.home_lambda,l.away_lambda) p;

create unique index if not exists betting_model_v6_residual_xg_component_uq
  on public.betting_model_v6_residual_xg_component(match_id);
