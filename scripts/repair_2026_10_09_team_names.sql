-- One-time input-name repair for the October 2026 review; model formulas are unchanged.
-- Guards preserve match statistics, player identities, saved prices and all played forecasts.
begin;
-- Keep unrelated future forecasts and all non-name source fields stable as well.
create temporary table weekend_name_repair_guard on commit drop as
select jsonb_build_object(
  'unrelated_snapshots', (select md5(string_agg(to_jsonb(s)::text,'|' order by fixture_id)) from public.betting_manual_weekend_snapshot s where fixture_id not between 51 and 60),
  'matches_non_names', (select md5(string_agg((to_jsonb(m)-'home_team'-'away_team')::text,'|' order by match_id)) from public.matches m where season='2026/27'),
  'lineups_non_names', (select md5(string_agg((to_jsonb(l)-'team_name')::text,'|' order by id)) from public.lineups l where season='2026/27'),
  'goals_non_names', (select md5(string_agg((to_jsonb(g)-'home_team'-'away_team')::text,'|' order by id)) from public.goals g where season='2026/27')
) protected_state;
do $repair$
declare changed integer;
begin
update public.matches t set home_team=coalesce((select canonical from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical) where a.alias=t.home_team),t.home_team),away_team=coalesce((select canonical from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical) where a.alias=t.away_team),t.away_team) where season='2026/27' and (t.home_team in(select alias from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical)) or t.away_team in(select alias from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical)));
get diagnostics changed=row_count;
if changed not in(0,14) then raise exception 'Unexpected matches repair row count: %',changed;end if;
update public.canonical_matches t set home_team=coalesce((select canonical from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical) where a.alias=t.home_team),t.home_team),away_team=coalesce((select canonical from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical) where a.alias=t.away_team),t.away_team) where season='2026/27' and (t.home_team in(select alias from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical)) or t.away_team in(select alias from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical)));
get diagnostics changed=row_count;
if changed not in(0,14) then raise exception 'Unexpected canonical_matches repair row count: %',changed;end if;
update public.player_match_stats t set team_name=coalesce((select canonical from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical) where a.alias=t.team_name),t.team_name) where season='2026/27' and (t.team_name in(select alias from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical)));
get diagnostics changed=row_count;
if changed not in(0,318) then raise exception 'Unexpected player_match_stats repair row count: %',changed;end if;
update public.lineups t set team_name=coalesce((select canonical from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical) where a.alias=t.team_name),t.team_name) where season='2026/27' and (t.team_name in(select alias from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical)));
get diagnostics changed=row_count;
if changed not in(0,318) then raise exception 'Unexpected lineups repair row count: %',changed;end if;
update public.goals t set home_team=coalesce((select canonical from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical) where a.alias=t.home_team),t.home_team),away_team=coalesce((select canonical from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical) where a.alias=t.away_team),t.away_team) where season='2026/27' and (t.home_team in(select alias from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical)) or t.away_team in(select alias from (values ('Bournemouth','AFC Bournemouth'),('Brighton','Brighton & Hove Albion'),('Leeds','Leeds United'),('Man City','Manchester City'),('Man Utd','Manchester United'),('Newcastle','Newcastle United'),('Nott''m Forest','Nottingham Forest'),('Spurs','Tottenham Hotspur')) a(alias,canonical)));
get diagnostics changed=row_count;
if changed not in(0,41) then raise exception 'Unexpected goals repair row count: %',changed;end if;

end $repair$;
-- Run after source imports, and before add_weekend_v3_venue8_comparison.sql.
-- Refresh only fixtures that have not kicked off. Played fixtures stay frozen.

refresh materialized view public.betting_team_features_v2_cache;

with fixtures as (
  select f.*,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.home_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) home_segment,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.away_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) away_segment
  from public.betting_manual_fixtures f where f.fixture_id between 51 and 60 and f.kickoff_time>now()
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

with fx as (
  select f.*,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.home_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) home_segment,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.away_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) away_segment
  from public.betting_manual_fixtures f
  where f.fixture_id between 51 and 60 and f.kickoff_time > now() -- Preserve played fixtures' frozen pre-match predictions.
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

do $verify$
declare after_state jsonb; unrelated_after jsonb; bad_count integer;
begin
-- Keep unrelated future forecasts and all non-name source fields stable as well.
select jsonb_build_object(
  'unrelated_snapshots', (select md5(string_agg(to_jsonb(s)::text,'|' order by fixture_id)) from public.betting_manual_weekend_snapshot s where fixture_id not between 51 and 60),
  'matches_non_names', (select md5(string_agg((to_jsonb(m)-'home_team'-'away_team')::text,'|' order by match_id)) from public.matches m where season='2026/27'),
  'lineups_non_names', (select md5(string_agg((to_jsonb(l)-'team_name')::text,'|' order by id)) from public.lineups l where season='2026/27'),
  'goals_non_names', (select md5(string_agg((to_jsonb(g)-'home_team'-'away_team')::text,'|' order by id)) from public.goals g where season='2026/27')
) into unrelated_after;
if unrelated_after is distinct from (select protected_state from weekend_name_repair_guard) then
  raise exception 'Unrelated forecasts or non-name source fields changed';
end if;
select guard into after_state from (select jsonb_build_object('played_snapshots',(select md5(string_agg(to_jsonb(s)::text,'|' order by s.fixture_id)) from public.betting_manual_weekend_snapshot s join public.betting_manual_fixtures f using(fixture_id) where f.kickoff_time<now()),'played_manual_fixtures',(select md5(string_agg(to_jsonb(f)::text,'|' order by fixture_id)) from public.betting_manual_fixtures f where kickoff_time<now()),'frozen_v3',(select md5(string_agg(to_jsonb(p)::text,'|' order by season,match_id)) from public.betting_model_match_predictions p where model_version='v3'),'source_non_names',(select md5(string_agg((to_jsonb(b)-'team_name'-'opponent_team')::text,'|' order by match_id,was_home)) from public.betting_team_match_v2 b where season='2026/27'),'canonical_non_names',(select md5(string_agg((to_jsonb(c)-'home_team'-'away_team')::text,'|' order by canonical_match_id)) from public.canonical_matches c where season='2026/27'),'player_non_names',(select md5(string_agg((to_jsonb(p)-'team_name')::text,'|' order by id)) from public.player_match_stats p where season='2026/27'),'market',(select md5(string_agg(jsonb_build_array(fixture_id,market_home_odds,market_draw_odds,market_away_odds,market_source,market_snapshot_at)::text,'|' order by fixture_id)) from public.betting_manual_fixtures where fixture_id between 51 and 60)) guard) g;
if after_state->>'market' is distinct from 'b168c5c40a20ed85330349af87799225' then raise exception 'Protected market changed'; end if;
if after_state->>'frozen_v3' is distinct from '598f0fb9d8f8bd89062da3bc70cfd348' then raise exception 'Protected frozen_v3 changed'; end if;
if after_state->>'played_snapshots' is distinct from 'e18ef2b943ab343a7cb986cc94ce8235' then raise exception 'Protected played_snapshots changed'; end if;
if after_state->>'player_non_names' is distinct from 'c04b805baab137aad2bc8425b29f6760' then raise exception 'Protected player_non_names changed'; end if;
if after_state->>'source_non_names' is distinct from '5fcd430da9731c2e379c0bda33963bd1' then raise exception 'Protected source_non_names changed'; end if;
if after_state->>'canonical_non_names' is distinct from '21ccd581293adfaeab4eb491e58f1b40' then raise exception 'Protected canonical_non_names changed'; end if;
if after_state->>'played_manual_fixtures' is distinct from '87b146b81536b5fb7637056e8aa01614' then raise exception 'Protected played_manual_fixtures changed'; end if;
select count(*) into bad_count from(select team_name,count(*) n from public.betting_team_match_v2 where season='2026/27' group by team_name) t where n<>5;
if bad_count<>0 or (select count(distinct team_name) from public.betting_team_match_v2 where season='2026/27')<>20 then raise exception 'Current team history remains split';end if;
if (select count(*) from public.betting_team_match_v2 where season='2026/27')<>100
  or (select count(*) from public.betting_team_match_v2 where season='2026/27' and (not coalesce(xg_available,false) or xg_for is null or xg_against is null))<>0 then
  raise exception 'xG coverage changed';
end if;
end $verify$;
commit;
