-- Reproducible research-only Dixon-Coles evaluation for v3_24_venue8_50_noppg.
-- No production objects are changed.
-- Source lambdas/probabilities: public.betting_v3_venue8_ppg_ablation_gw15.

-- 1) Aggregate development rho sweep: 2019/20-2024/25.
with rhos as (
  select (g/1000.0)::double precision as rho
  from generate_series(-200,100,5) g
), base as (
  select season,hg,ag,
         no_ppg_home_lambda::double precision lh,
         no_ppg_away_lambda::double precision la,
         no_ppg_home_prob::double precision ph,
         no_ppg_draw_prob::double precision pd,
         no_ppg_away_prob::double precision pa
  from public.betting_v3_venue8_ppg_ablation_gw15
  where season between '2019/20' and '2024/25'
), scored as (
  select r.rho,b.*,
         ph + exp(-(lh+la))*lh*la*r.rho as dph,
         pd - 2*exp(-(lh+la))*lh*la*r.rho as dpd,
         pa + exp(-(lh+la))*lh*la*r.rho as dpa
  from base b cross join rhos r
), agg as (
  select rho,count(*) n,
    avg((dph-(case when hg>ag then 1 else 0 end))^2 +
        (dpd-(case when hg=ag then 1 else 0 end))^2 +
        (dpa-(case when hg<ag then 1 else 0 end))^2) brier,
    avg(-ln(case when hg>ag then dph when hg=ag then dpd else dpa end)) logloss,
    avg(case when (case when dph>=dpd and dph>=dpa then 'H' when dpd>=dph and dpd>=dpa then 'D' else 'A' end)=
                  (case when hg>ag then 'H' when hg=ag then 'D' else 'A' end) then 1.0 else 0.0 end) accuracy,
    avg(dpd) avg_draw_prob,
    avg(case when hg=ag then 1.0 else 0.0 end) actual_draw_rate
  from scored
  where dph>0 and dpd>0 and dpa>0
  group by rho
)
select * from agg order by brier limit 20;

-- 2) Fixed rho comparison by season, including 2025/26 stress season.
with params(rho,label) as (
  values (0.0::double precision,'Poisson'),
         (0.07::double precision,'DC +0.07'),
         (-0.07::double precision,'DC -0.07')
), base as (
  select season,hg,ag,
         no_ppg_home_lambda::double precision lh,
         no_ppg_away_lambda::double precision la,
         no_ppg_home_prob::double precision ph,
         no_ppg_draw_prob::double precision pd,
         no_ppg_away_prob::double precision pa
  from public.betting_v3_venue8_ppg_ablation_gw15
), s as (
  select p.label,p.rho,b.*,
         ph+exp(-(lh+la))*lh*la*p.rho dph,
         pd-2*exp(-(lh+la))*lh*la*p.rho dpd,
         pa+exp(-(lh+la))*lh*la*p.rho dpa
  from base b cross join params p
)
select season,label,count(*) n,
       avg((dph-(case when hg>ag then 1 else 0 end))^2+
           (dpd-(case when hg=ag then 1 else 0 end))^2+
           (dpa-(case when hg<ag then 1 else 0 end))^2) brier,
       avg(-ln(case when hg>ag then dph when hg=ag then dpd else dpa end)) logloss,
       avg(dpd) avg_draw_prob,
       avg(case when hg=ag then 1.0 else 0.0 end) actual_draw_rate
from s
where dph>0 and dpd>0 and dpa>0
group by season,label
order by season,label;

-- 3) Leave-one-season-out rho fit on development seasons.
with seasons as (
  select unnest(array['2019/20','2020/21','2021/22','2022/23','2023/24','2024/25']) holdout
), rhos as (
  select (g/1000.0)::double precision rho from generate_series(-150,150,5) g
), base as (
  select season,hg,ag,
         no_ppg_home_lambda::double precision lh,
         no_ppg_away_lambda::double precision la,
         no_ppg_home_prob::double precision ph,
         no_ppg_draw_prob::double precision pd,
         no_ppg_away_prob::double precision pa
  from public.betting_v3_venue8_ppg_ablation_gw15
  where season between '2019/20' and '2024/25'
), expanded as (
  select s.holdout,r.rho,b.*,
         ph+exp(-(lh+la))*lh*la*r.rho dph,
         pd-2*exp(-(lh+la))*lh*la*r.rho dpd,
         pa+exp(-(lh+la))*lh*la*r.rho dpa
  from seasons s cross join rhos r cross join base b
), train_scores as (
  select holdout,rho,
         avg((dph-(case when hg>ag then 1 else 0 end))^2+
             (dpd-(case when hg=ag then 1 else 0 end))^2+
             (dpa-(case when hg<ag then 1 else 0 end))^2) brier
  from expanded
  where season<>holdout and dph>0 and dpd>0 and dpa>0
  group by holdout,rho
), chosen as (
  select distinct on (holdout) holdout,rho
  from train_scores
  order by holdout,brier,rho
), test as (
  select e.*,c.rho chosen_rho
  from expanded e
  join chosen c on c.holdout=e.holdout and c.rho=e.rho
  where e.season=e.holdout
)
select holdout,chosen_rho,count(*) n,
       avg((ph-(case when hg>ag then 1 else 0 end))^2+
           (pd-(case when hg=ag then 1 else 0 end))^2+
           (pa-(case when hg<ag then 1 else 0 end))^2) poisson_brier,
       avg((dph-(case when hg>ag then 1 else 0 end))^2+
           (dpd-(case when hg=ag then 1 else 0 end))^2+
           (dpa-(case when hg<ag then 1 else 0 end))^2) dc_brier,
       avg(-ln(case when hg>ag then ph when hg=ag then pd else pa end)) poisson_logloss,
       avg(-ln(case when hg>ag then dph when hg=ag then dpd else dpa end)) dc_logloss
from test
group by holdout,chosen_rho
order by holdout;

-- 4) 2026/27 Matchweek 3 diagnostic on the seven candidate-eligible fixtures.
-- These results are intentionally literal frozen outcomes for the diagnostic only.
with actuals(fixture_id,hg,ag) as (
  values (2,2,2),(3,0,0),(4,1,1),(5,1,1),(6,2,3),(9,2,2),(10,2,1)
), params(rho,label) as (
  values (-0.07::double precision,'DC -0.07'),
         (0.0::double precision,'Poisson'),
         (0.07::double precision,'DC +0.07')
), base as (
  select s.fixture_id,a.hg,a.ag,
         s.candidate_home_lambda::double precision lh,
         s.candidate_away_lambda::double precision la,
         s.candidate_home_prob::double precision ph,
         s.candidate_draw_prob::double precision pd,
         s.candidate_away_prob::double precision pa
  from public.betting_manual_weekend_snapshot s
  join actuals a using(fixture_id)
), scored as (
  select p.label,p.rho,b.*,
         ph+exp(-(lh+la))*lh*la*p.rho dph,
         pd-2*exp(-(lh+la))*lh*la*p.rho dpd,
         pa+exp(-(lh+la))*lh*la*p.rho dpa
  from base b cross join params p
)
select label,count(*) n,
       avg((dph-(case when hg>ag then 1 else 0 end))^2+
           (dpd-(case when hg=ag then 1 else 0 end))^2+
           (dpa-(case when hg<ag then 1 else 0 end))^2) brier,
       avg(-ln(case when hg>ag then dph when hg=ag then dpd else dpa end)) logloss,
       avg(dpd) avg_draw_prob,
       avg(case when hg=ag then 1.0 else 0.0 end) actual_draw_rate
from scored
group by label
order by min(rho);
