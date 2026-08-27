-- Add fast pre-match form diagnostics to public.matches.
-- All values are pre-kickoff and respect the current Premier League spell.
-- Overall 5/10/15 fields were added previously. This migration adds overall 30 plus same-venue 5/10/15.

alter table public.matches
  add column if not exists home_ppg30 numeric,
  add column if not exists home_xgf30 numeric,
  add column if not exists home_xga30 numeric,
  add column if not exists away_ppg30 numeric,
  add column if not exists away_xgf30 numeric,
  add column if not exists away_xga30 numeric,
  add column if not exists home_venue_ppg5 numeric,
  add column if not exists home_venue_xgf5 numeric,
  add column if not exists home_venue_xga5 numeric,
  add column if not exists away_venue_ppg5 numeric,
  add column if not exists away_venue_xgf5 numeric,
  add column if not exists away_venue_xga5 numeric,
  add column if not exists home_venue_ppg10 numeric,
  add column if not exists home_venue_xgf10 numeric,
  add column if not exists home_venue_xga10 numeric,
  add column if not exists away_venue_ppg10 numeric,
  add column if not exists away_venue_xgf10 numeric,
  add column if not exists away_venue_xga10 numeric,
  add column if not exists home_venue_ppg15 numeric,
  add column if not exists home_venue_xgf15 numeric,
  add column if not exists home_venue_xga15 numeric,
  add column if not exists away_venue_ppg15 numeric,
  add column if not exists away_venue_xgf15 numeric,
  add column if not exists away_venue_xga15 numeric;

-- Cached per-team rolling window layer used to make repeated diagnostics cheap.
create materialized view if not exists public.team_form_window_cache as
with base as (
  select tm.match_id, tm.season, tm.gameweek, tm.kickoff_time, tm.team_name, tm.opponent_team,
         tm.was_home, tm.result, tm.xg_for, tm.xg_against, tf.segment_id,
         case when tm.result='W' then 3 when tm.result='D' then 1 else 0 end::numeric pts
  from public.betting_team_match_v2 tm
  join public.betting_team_features_v2 tf
    on tf.match_id=tm.match_id and tf.team_name=tm.team_name
), overall as (
  select b.*,
    count(*) over(partition by team_name,segment_id order by kickoff_time rows between 30 preceding and 1 preceding) on30,
    avg(pts) over(partition by team_name,segment_id order by kickoff_time rows between 30 preceding and 1 preceding) oppg30
  from base b
), venue as (
  select o.*,
    count(*) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 5 preceding and 1 preceding) vn5,
    avg(pts) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 5 preceding and 1 preceding) vppg5,
    avg(xg_for) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 5 preceding and 1 preceding) vxgf5,
    avg(xg_against) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 5 preceding and 1 preceding) vxga5,
    count(*) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 10 preceding and 1 preceding) vn10,
    avg(pts) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 10 preceding and 1 preceding) vppg10,
    avg(xg_for) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 10 preceding and 1 preceding) vxgf10,
    avg(xg_against) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 10 preceding and 1 preceding) vxga10,
    count(*) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 15 preceding and 1 preceding) vn15,
    avg(pts) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 15 preceding and 1 preceding) vppg15,
    avg(xg_for) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 15 preceding and 1 preceding) vxgf15,
    avg(xg_against) over(partition by team_name,segment_id,was_home order by kickoff_time rows between 15 preceding and 1 preceding) vxga15
  from overall o
)
select * from venue;

create unique index if not exists team_form_window_cache_match_team_uq
  on public.team_form_window_cache(match_id,team_name);

-- Backfill recent/live matches from cached team features.
update public.matches m set
  home_ppg30=case when hc.on30>=30 then hc.oppg30 end,
  home_xgf30=case when hf.n30>=30 then hf.xgf30 end,
  home_xga30=case when hf.n30>=30 then hf.xga30 end,
  away_ppg30=case when ac.on30>=30 then ac.oppg30 end,
  away_xgf30=case when af.n30>=30 then af.xgf30 end,
  away_xga30=case when af.n30>=30 then af.xga30 end,
  home_venue_ppg5=case when hc.vn5>=5 then hc.vppg5 end,
  home_venue_xgf5=case when hc.vn5>=5 then hc.vxgf5 end,
  home_venue_xga5=case when hc.vn5>=5 then hc.vxga5 end,
  away_venue_ppg5=case when ac.vn5>=5 then ac.vppg5 end,
  away_venue_xgf5=case when ac.vn5>=5 then ac.vxgf5 end,
  away_venue_xga5=case when ac.vn5>=5 then ac.vxga5 end,
  home_venue_ppg10=case when hc.vn10>=10 then hc.vppg10 end,
  home_venue_xgf10=case when hc.vn10>=10 then hc.vxgf10 end,
  home_venue_xga10=case when hc.vn10>=10 then hc.vxga10 end,
  away_venue_ppg10=case when ac.vn10>=10 then ac.vppg10 end,
  away_venue_xgf10=case when ac.vn10>=10 then ac.vxgf10 end,
  away_venue_xga10=case when ac.vn10>=10 then ac.vxga10 end,
  home_venue_ppg15=case when hc.vn15>=15 then hc.vppg15 end,
  home_venue_xgf15=case when hc.vn15>=15 then hc.vxgf15 end,
  home_venue_xga15=case when hc.vn15>=15 then hc.vxga15 end,
  away_venue_ppg15=case when ac.vn15>=15 then ac.vppg15 end,
  away_venue_xgf15=case when ac.vn15>=15 then ac.vxgf15 end,
  away_venue_xga15=case when ac.vn15>=15 then ac.vxga15 end
from public.team_form_window_cache hc
join public.team_form_window_cache ac on ac.match_id=hc.match_id and ac.was_home=false
join public.betting_team_features_v2 hf on hf.match_id=hc.match_id and hf.was_home=true
join public.betting_team_features_v2 af on af.match_id=hc.match_id and af.was_home=false
where hc.match_id=m.match_id and hc.was_home=true;
