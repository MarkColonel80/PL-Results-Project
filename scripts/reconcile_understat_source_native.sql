-- Reconcile legacy Understat source_native_identity players to established canonical players.
--
-- This is a DATA reconciliation, not a schema migration.
-- It deliberately uses no player names. Candidate identity is established from
-- canonical match history + goals + provider-tolerant minutes using the same
-- conservative thresholds as resolve_understat_cross_source.py.
--
-- Expected first-run checkpoint (2026-08-26): 74 reconciliations.
-- Repeat-safe: after a successful run the candidate temp table should contain 0 rows.

begin;

create temp table understat_native_reconcile on commit drop as
with native as (
    select source_player_id, player_code as current_code
    from player_source_ids
    where source = 'understat'
      and verified
      and mapping_method = 'source_native_identity'
),
u as (
    select
        s.source_player_id,
        n.current_code,
        s.season,
        s.match_id,
        coalesce(s.goals, 0) as goals,
        coalesce(s.minutes_played, 0) as minutes
    from source_player_match_stats s
    join native n using (source_player_id)
    where s.source = 'understat'
      and s.season >= '2015/16'
      and s.match_id is not null
),
u_seasons as (
    select distinct source_player_id, season from u
),
source_counts as (
    select source_player_id, count(distinct match_id) as source_count
    from u
    group by source_player_id
),
common as (
    select
        u.source_player_id,
        u.current_code,
        p.player_code as candidate_code,
        count(distinct u.match_id) as common_count,
        sum(case when coalesce(p.goals, 0) <> u.goals then 1 else 0 end) as goal_mismatches,
        avg(abs(coalesce(p.minutes_played, 0) - u.minutes)) as avg_min_diff,
        avg(case when abs(coalesce(p.minutes_played, 0) - u.minutes) <= 2 then 1.0 else 0.0 end) as within2
    from u
    join player_match_stats p
      on p.match_id = u.match_id
     and p.source <> 'understat'
     and p.player_code is not null
     and p.player_code <> u.current_code
    group by u.source_player_id, u.current_code, p.player_code
),
candidate_counts as (
    select
        c.source_player_id,
        c.candidate_code,
        count(distinct p.match_id) as candidate_count
    from (select distinct source_player_id, candidate_code from common) c
    join u_seasons us on us.source_player_id = c.source_player_id
    join player_match_stats p
      on p.season = us.season
     and p.player_code = c.candidate_code
     and p.source <> 'understat'
    group by c.source_player_id, c.candidate_code
),
scored as (
    select
        c.*,
        sc.source_count,
        cc.candidate_count,
        c.common_count::numeric / sc.source_count as source_coverage,
        c.common_count::numeric / cc.candidate_count as candidate_coverage
    from common c
    join source_counts sc using (source_player_id)
    join candidate_counts cc using (source_player_id, candidate_code)
),
passing as (
    select *
    from scored
    where common_count >= 3
      and source_coverage >= 0.95
      and candidate_coverage >= 0.95
      and goal_mismatches <= greatest(1, ceil(common_count * 0.01))
      and (
          (within2 >= 0.97 and avg_min_diff <= 1.5)
          or (
              common_count = source_count
              and common_count = candidate_count
              and avg_min_diff <= 2.0
          )
      )
),
unique_source as (
    select source_player_id
    from passing
    group by source_player_id
    having count(*) = 1
),
unique_target as (
    select candidate_code
    from passing
    group by candidate_code
    having count(*) = 1
)
select
    p.source_player_id,
    p.current_code,
    p.candidate_code,
    p.common_count,
    p.source_count,
    p.candidate_count,
    p.source_coverage,
    p.candidate_coverage,
    p.goal_mismatches,
    p.avg_min_diff,
    p.within2
from passing p
join unique_source us using (source_player_id)
join unique_target ut using (candidate_code)
order by p.source_player_id;

-- Safety gates. Any unexpected state aborts the entire transaction.
do $$
begin
    if exists (
        select 1
        from understat_native_reconcile r
        join player_source_ids other
          on other.source = 'understat'
         and other.verified
         and other.player_code = r.candidate_code
         and other.source_player_id <> r.source_player_id
    ) then
        raise exception 'Understat reconciliation target already claimed by another source player';
    end if;

    if exists (
        select 1
        from understat_native_reconcile r
        join player_match_stats old
          on old.player_code = r.current_code
        where old.source <> 'understat'
    ) then
        raise exception 'Legacy source-native player_code is referenced by a non-Understat live match row';
    end if;

    if exists (
        select 1
        from understat_native_reconcile r
        join player_match_stats old
          on old.player_code = r.current_code
        join player_match_stats target
          on target.match_id = old.match_id
         and target.player_code = r.candidate_code
    ) then
        raise exception 'player_match_stats collision detected for reconciliation target';
    end if;

    if exists (
        select 1
        from understat_native_reconcile r
        join player_seasons old
          on old.player_code = r.current_code
        join player_seasons target
          on target.season = old.season
         and target.player_code = r.candidate_code
    ) then
        raise exception 'player_seasons collision detected for reconciliation target';
    end if;

    if exists (
        select 1
        from understat_native_reconcile r
        join player_source_ids x on x.player_code = r.current_code
        where not (x.source = 'understat' and x.source_player_id = r.source_player_id)
    ) then
        raise exception 'Legacy source-native player_code has an unexpected player_source_ids reference';
    end if;

    if exists (select 1 from understat_native_reconcile r join player_provider_ids x on x.player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join fpl_player_match_stats x on x.player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join goals x on x.player_code = r.current_code or x.assist_player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join lineups x on x.player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join player_match_ratings x on x.player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join source_game_events x on x.player_code = r.current_code or x.assist_player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join source_player_mappings x on x.player_code = r.current_code)
    then
        raise exception 'Legacy source-native player_code has an unexpected dependency outside the audited tables';
    end if;

    if exists (
        select 1
        from understat_native_reconcile r
        left join players old on old.player_code = r.current_code
        left join players target on target.player_code = r.candidate_code
        where old.player_code is null or target.player_code is null
    ) then
        raise exception 'Missing old or target canonical players row';
    end if;
end $$;

-- Re-key the source-faithful staging rows first.
update source_player_match_stats s
set player_code = r.candidate_code,
    data_quality = 'source_reported_verified_cross_source_identity'
from understat_native_reconcile r
where s.source = 'understat'
  and s.source_player_id = r.source_player_id
  and s.player_code = r.current_code;

-- 2014/15 is currently live from Understat for these legacy identities.
update player_match_stats p
set player_code = r.candidate_code,
    data_quality = 'source_reported_verified_cross_source_identity'
from understat_native_reconcile r
where p.source = 'understat'
  and p.player_code = r.current_code;

-- Preserve the 2014/15 membership row but move it onto the established identity.
update player_seasons ps
set player_code = r.candidate_code
from understat_native_reconcile r
where ps.player_code = r.current_code;

-- Replace the provider crosswalk itself with the established canonical identity.
update player_source_ids psi
set player_code = r.candidate_code,
    mapping_method = 'canonical_match_history_goals_minutes_v1_reconciled_source_native',
    verified = true,
    source_note = 'Reconciled legacy source_native_identity without player-name matching; >=95% two-sided canonical match-history coverage, goals near-exact, provider-tolerant minute pattern, unique one-to-one target.'
from understat_native_reconcile r
where psi.source = 'understat'
  and psi.source_player_id = r.source_player_id
  and psi.player_code = r.current_code;

-- The old plp:* rows are now unreferenced duplicate canonical identities.
delete from players p
using understat_native_reconcile r
where p.player_code = r.current_code;

-- Postconditions: no old codes may remain in the tables touched above.
do $$
begin
    if exists (select 1 from understat_native_reconcile r join source_player_match_stats x on x.player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join player_match_stats x on x.player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join player_seasons x on x.player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join player_source_ids x on x.player_code = r.current_code)
       or exists (select 1 from understat_native_reconcile r join players x on x.player_code = r.current_code)
    then
        raise exception 'Old source-native player_code still referenced after reconciliation';
    end if;
end $$;

select
    count(*) as reconciled_players,
    min(common_count) as min_common_games,
    percentile_disc(0.5) within group (order by common_count) as median_common_games,
    max(common_count) as max_common_games,
    min(least(source_coverage, candidate_coverage)) as minimum_two_sided_coverage,
    max(avg_min_diff) as worst_average_minute_difference
from understat_native_reconcile;

commit;
