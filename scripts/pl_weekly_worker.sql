create schema if not exists pl_weekly_private;
revoke all on schema pl_weekly_private from public,anon,authenticated;
create table pl_weekly_private.capability(singleton boolean primary key default true check(singleton), secret_hash text not null);
create table pl_weekly_private.runs(run_key text primary key, owner_run text not null, status text not null, lease_until timestamptz not null, created_at timestamptz not null default now(), updated_at timestamptz not null default now(), protected_state jsonb not null, receipts jsonb not null default '{}'::jsonb);
revoke all on all tables in schema pl_weekly_private from public,anon,authenticated;
create function pl_weekly_private.protected_state(p_before timestamptz) returns jsonb language sql stable set search_path='' as $$
select jsonb_build_object(
'fixtures',(select coalesce(jsonb_object_agg(f.fixture_id,to_jsonb(f)),'{}') from public.betting_manual_fixtures f where f.kickoff_time<=p_before),
'snapshots',(select coalesce(jsonb_object_agg(s.fixture_id,to_jsonb(s)),'{}') from public.betting_manual_weekend_snapshot s join public.betting_manual_fixtures f using(fixture_id) where f.kickoff_time<=p_before)
);
$$;
revoke all on function pl_weekly_private.protected_state(timestamptz) from public,anon,authenticated;
create function public.pl_weekly_worker(p_capability text,p_run text,p_op text,p_key text,p_data jsonb default '{}'::jsonb) returns jsonb
language plpgsql security definer set search_path='' set statement_timeout='240s' as $$
declare rr pl_weekly_private.runs%rowtype; r jsonb; old jsonb; t text; cols text; vals text; predicates text; k text; keys text[]; n int:=0; answer jsonb; allowed text[]; before_at timestamptz;
begin
 if not exists(select 1 from pl_weekly_private.capability where secret_hash=encode(extensions.digest(p_capability,'sha256'),'hex')) then raise exception 'Worker capability rejected'; end if;
 if p_run !~ '^[0-9]+$' then raise exception 'Invalid run'; end if;
 if p_op='read' then
 return jsonb_build_object(
 'matches',(select coalesce(jsonb_agg(to_jsonb(m)),'[]') from public.matches m where season='2026/27'),
 'identities',(select coalesce(jsonb_agg(jsonb_build_object('player_id',s.player_id,'player_code',s.player_code,'team_name',s.team_name,'opta_code',p.opta_code)),'[]') from public.player_seasons s join public.players p using(player_code) where s.season='2026/27'),
 'fixtures',(select coalesce(jsonb_agg(to_jsonb(f)||jsonb_build_object('snapshot',to_jsonb(s))),'[]') from public.betting_manual_fixtures f left join public.betting_manual_weekend_snapshot s using(fixture_id) where f.season='2026/27'),
 'counts',(select jsonb_object_agg(q.t,q.n) from (select 'matches' t,count(*) n from public.matches where season='2026/27' union all select 'pms',count(*) from public.player_match_stats where season='2026/27' union all select 'fpl',count(*) from public.fpl_player_match_stats where season='2026/27')q));
 end if;
 if p_key !~ '^2026-[0-9]{2}-[0-9]{2}$' or abs(current_date-p_key::date)>14 then raise exception 'Dispatch outside approved season/date window'; end if;
 perform pg_advisory_xact_lock(1346031407);
 select * into rr from pl_weekly_private.runs where run_key=p_key for update;
 if p_op='begin' then
  if found and rr.status='complete' then return jsonb_build_object('complete',true,'receipts',rr.receipts); end if;
  if exists(select 1 from pl_weekly_private.runs where status='running' and lease_until>now() and owner_run<>p_run) then raise exception 'Another worker holds the lease'; end if;
  if rr.run_key is null then
   insert into pl_weekly_private.runs(run_key,owner_run,status,lease_until,protected_state) values(p_key,p_run,'running',now()+interval '110 minutes',pl_weekly_private.protected_state(now()));
  else
   update pl_weekly_private.runs set owner_run=p_run,status='running',lease_until=now()+interval '110 minutes',updated_at=now() where run_key=p_key;
  end if;
  return jsonb_build_object('complete',false,'receipts',coalesce(rr.receipts,'{}'));
 end if;
 if rr.run_key is null or rr.owner_run<>p_run or rr.status<>'running' or rr.lease_until<now() then raise exception 'Active worker lease required'; end if;
 if rr.protected_state<>pl_weekly_private.protected_state(rr.created_at) then raise exception 'Protected forecast history changed'; end if;
 if p_op='receipt' then
  if p_data->>'stage' !~ '^[a-z_0-9-]{1,80}$' then raise exception 'Invalid stage'; end if;
  update pl_weekly_private.runs set receipts=jsonb_set(receipts,array[p_data->>'stage'],p_data->'value'),updated_at=now(),lease_until=now()+interval '110 minutes' where run_key=p_key;
 elsif p_op='finish' then
  update pl_weekly_private.runs set status=case when p_data->>'success'='true' then 'complete' else 'failed' end,updated_at=now(),lease_until=now() where run_key=p_key;
 elsif p_op='append' then
  t=p_data->>'table';
  keys=case t when 'matches' then array['match_id'] when 'canonical_matches' then array['canonical_match_id'] when 'match_source_ids' then array['source','source_match_id'] when 'player_match_stats' then array['season','match_id','player_id'] when 'fpl_player_match_stats' then array['season','fixture_id','player_code'] when 'lineups' then array['season','match_id','player_id'] when 'goals' then array['season','match_id','incident_index'] when 'historical_market_odds' then array['season','source','source_match_date','source_home_team','source_away_team'] else null end;
  if keys is null or jsonb_array_length(p_data->'rows')>800 then raise exception 'Unsupported import'; end if;
  select array_agg(column_name::text) into allowed from information_schema.columns where table_schema='public' and table_name=t and column_name not in('id','created_at','updated_at') and is_identity='NO';
  for r in select value from jsonb_array_elements(p_data->'rows') loop
   if r->>'season'<>'2026/27' or r->>'season' is null then raise exception 'Season mismatch'; end if;
   if exists(select 1 from jsonb_object_keys(r) x where not x=any(allowed)) then raise exception 'Unexpected import column'; end if;
   if exists(select 1 from unnest(keys)x where r->>x is null) then raise exception 'Missing import identity'; end if;
   if t='matches' and ((r->>'kickoff_time')::timestamptz>now() or (r->>'kickoff_time')::timestamptz<now()-interval '21 days' or (r->>'home_score')::int<0 or (r->>'away_score')::int<0) then raise exception 'Invalid completed match'; end if;
   if t='canonical_matches' and not exists(select 1 from public.matches m where m.match_id=r->>'canonical_match_id' and m.home_team=r->>'home_team' and m.away_team=r->>'away_team' and m.home_score=(r->>'home_score')::int and m.away_score=(r->>'away_score')::int and m.kickoff_time::date=(r->>'match_date')::date) then raise exception 'Canonical identity mismatch'; end if;
   if t in('player_match_stats','lineups','goals','historical_market_odds') and not exists(select 1 from public.matches m where m.match_id=r->>'match_id' and m.season='2026/27' and m.kickoff_time between now()-interval '21 days' and now()) then raise exception 'Match outside import scope'; end if;
   if t in('player_match_stats','fpl_player_match_stats','lineups') and not exists(select 1 from public.player_seasons s where s.season='2026/27' and s.player_id=r->>'player_id' and s.player_code=r->>'player_code') then raise exception 'Permanent player identity not verified'; end if;
   if t='fpl_player_match_stats' and not exists(select 1 from public.matches m where m.season='2026/27' and m.kickoff_time=(r->>'kickoff_time')::timestamptz and m.kickoff_time between now()-interval '21 days' and now() and ((m.home_team=r->>'team_name' and m.away_team=r->>'opponent_team') or(m.away_team=r->>'team_name' and m.home_team=r->>'opponent_team'))) then raise exception 'FPL fixture not matched'; end if;
   select string_agg(format('to_jsonb(x)->>%L=$1->>%L',x,x),' and ') into predicates from unnest(keys)x;
   execute format('select to_jsonb(x) from public.%I x where %s',t,predicates) into old using r;
   if old is not null then
    -- Existing source facts/identities are append-only. A correction needs explicit review.
    if exists(select 1 from jsonb_each(r)e where e.key not in('source','data_quality','mapping_method','source_url','raw_row') and e.value is distinct from old->e.key) then raise exception 'Existing % record differs; review required',t; end if;
   else
    select string_agg(format('%I',x),','),string_agg(format('x.%I',x),',') into cols,vals from jsonb_object_keys(r)x;
    execute format('insert into public.%I(%s) select %s from jsonb_populate_record(null::public.%I,$1)x',t,cols,vals,t) using r;
    n=n+1;
   end if;
  end loop;
 elsif p_op='upcoming' then
  if jsonb_array_length(p_data->'rows')>20 then raise exception 'Too many future fixtures'; end if;
  for r in select value from jsonb_array_elements(p_data->'rows') loop
   if r->>'season'<>'2026/27' or (r->>'kickoff_time')::timestamptz<=now() or (r->>'kickoff_time')::timestamptz>now()+interval '40 days' then raise exception 'Future fixture required'; end if;
   select to_jsonb(f) into old from public.betting_manual_fixtures f where season='2026/27' and home_team=r->>'home_team' and away_team=r->>'away_team';
   if old is not null and (old->>'kickoff_time')::timestamptz<>(r->>'kickoff_time')::timestamptz then raise exception 'Reschedule requires preserving original ledger identity'; end if;
   if old is null then
    insert into public.betting_manual_fixtures(season,kickoff_time,home_team,away_team,notes) values('2026/27',(r->>'kickoff_time')::timestamptz,r->>'home_team',r->>'away_team',r->>'notes');
   end if;
   update public.betting_manual_fixtures set market_home_odds=(r->>'market_home_odds')::numeric,market_draw_odds=(r->>'market_draw_odds')::numeric,market_away_odds=(r->>'market_away_odds')::numeric,market_source=r->>'market_source',market_snapshot_at=(r->>'market_snapshot_at')::timestamptz,
   notes=split_part(coalesce(notes,''),E'\nWEEKEND_NEWS_JSON:',1)||E'\nWEEKEND_NEWS_JSON:'||(r->'news')::text
   where season='2026/27' and home_team=r->>'home_team' and away_team=r->>'away_team' and kickoff_time>now();
  end loop;
 elsif p_op='caches' then
  perform public.refresh_fpl_aggregate_caches();
  refresh materialized view public.team_form_window_cache;
  refresh materialized view public.team_form_window8_cache;
  -- Run after source imports, and before add_weekend_v3_venue8_comparison.sql.
-- Refresh only fixtures that have not kicked off. Played fixtures stay frozen.

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


  with fx as (
  select f.*,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.home_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) home_segment,
    (select b.segment_id from public.betting_team_features_v2_cache b where b.team_name=f.away_team and b.kickoff_time<f.kickoff_time order by b.kickoff_time desc,b.match_id desc limit 1) away_segment
  from public.betting_manual_fixtures f
  where f.kickoff_time > now() -- Preserve played fixtures' frozen pre-match predictions.
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

 else raise exception 'Unsupported worker operation'; end if;
 if rr.protected_state<>pl_weekly_private.protected_state(rr.created_at) then raise exception 'Protected history violation'; end if;
 return jsonb_build_object('ok',true,'inserted',n);
end;
$$;
revoke all on function public.pl_weekly_worker(text,text,text,text,jsonb) from public,authenticated;
grant execute on function public.pl_weekly_worker(text,text,text,text,jsonb) to anon;
