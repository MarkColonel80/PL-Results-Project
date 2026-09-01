-- Research-only cache for the 2026-09-01 v3 + Venue8 15-match residual experiment.
-- Production v3 and /betting/weekend are unchanged.

create materialized view public.betting_v3_venue8_15_residual_inputs as
with f as (
  select x.*,
         row_number() over(partition by season, team_name order by kickoff_time, match_id) as smn
  from public.betting_team_adaptive_model_features_v4 x
), caps as (
  select match_id,
         team_name,
         avg(case when xg_for is null then goals_for::numeric else least(goals_for::numeric, xg_for + 1) end)
           over(partition by team_name, segment_id order by kickoff_time, match_id rows between 15 preceding and 1 preceding) as cgf15,
         avg(case when xg_against is null then goals_against::numeric else least(goals_against::numeric, xg_against + 1) end)
           over(partition by team_name, segment_id order by kickoff_time, match_id rows between 15 preceding and 1 preceding) as cga15,
         avg(case when xg_for is null then goals_for::numeric else least(goals_for::numeric, xg_for + 1) end)
           over(partition by team_name, segment_id, was_home order by kickoff_time, match_id rows between 8 preceding and 1 preceding) as cgf8,
         avg(case when xg_against is null then goals_against::numeric else least(goals_against::numeric, xg_against + 1) end)
           over(partition by team_name, segment_id, was_home order by kickoff_time, match_id rows between 8 preceding and 1 preceding) as cga8
  from public.betting_team_features_v2_cache
), lg as (
  select match_id,
         .35 * avg(goals_for::numeric) over(order by kickoff_time, match_id rows between 15 preceding and 1 preceding)
           + .65 * avg(xg_for) over(order by kickoff_time, match_id rows between 15 preceding and 1 preceding) as lhome,
         .35 * avg(goals_against::numeric) over(order by kickoff_time, match_id rows between 15 preceding and 1 preceding)
           + .65 * avg(xg_against) over(order by kickoff_time, match_id rows between 15 preceding and 1 preceding) as laway
  from public.betting_team_features_v2_cache
  where was_home
)
select h.season,
       h.match_id,
       h.kickoff_time,
       h.team_name as home_team,
       a.team_name as away_team,
       h.goals_for as hg,
       h.goals_against as ag,
       h.n15 as hn,
       a.n15 as an,
       h.gf15 as hgf,
       h.ga15 as hga,
       h.xgf15 as hxgf,
       h.xga15 as hxga,
       a.gf15 as agf,
       a.ga15 as aga,
       a.xgf15 as axgf,
       a.xga15 as axga,
       hc.cgf15 as hcgf,
       hc.cga15 as hcga,
       ac.cgf15 as acgf,
       ac.cga15 as acga,
       (hv.vxgf8 + hc.cgf8) / 2 as hvatt,
       (hv.vxga8 + hc.cga8) / 2 as hvdef,
       (av.vxgf8 + ac.cgf8) / 2 as avatt,
       (av.vxga8 + ac.cga8) / 2 as avdef,
       (coalesce(h.ppg10b, 1.35) * least(h.n10b, 10) + 1.35 * 4) / (least(h.n10b, 10) + 4) as hps,
       (coalesce(a.ppg10b, 1.35) * least(a.n10b, 10) + 1.35 * 4) / (least(a.n10b, 10) + 4) as aps,
       lg.lhome,
       lg.laway,
       (lg.lhome + lg.laway) / 2 as lmid
from f h
join f a on a.match_id = h.match_id and not a.was_home
join caps hc on hc.match_id = h.match_id and hc.team_name = h.team_name
join caps ac on ac.match_id = a.match_id and ac.team_name = a.team_name
join public.team_form_window8_cache hv on hv.match_id = h.match_id and hv.team_name = h.team_name
join public.team_form_window8_cache av on av.match_id = a.match_id and av.team_name = a.team_name
join lg on lg.match_id = h.match_id
where h.was_home
  and h.season between '2019/20' and '2025/26'
  and h.smn >= 15
  and a.smn >= 15
  and hv.vn8 >= 4
  and av.vn8 >= 4;

create unique index betting_v3_venue8_15_residual_inputs_match_idx
  on public.betting_v3_venue8_15_residual_inputs(match_id);
