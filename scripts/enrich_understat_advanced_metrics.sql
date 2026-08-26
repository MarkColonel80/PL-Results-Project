-- Enrich existing canonical player_match_stats rows with verified Understat advanced metrics.
--
-- DATA reconciliation only; no schema changes.
-- Base football provenance and core stats (minutes/goals/assists/cards/etc.) are never changed.
-- Only exact (season, canonical match_id, verified player_code) matches are eligible.
-- Missing live appearances are deliberately NOT inserted here and require separate review.
-- Repeat-safe: rerunning should report 0 newly_enriched_rows after a successful first run.

begin;

-- Safety: an existing Understat enrichment must agree exactly with the staged source fields.
do $$
begin
  if exists (
    select 1
    from player_match_stats p
    join source_player_match_stats s
      on s.source = 'understat'
     and s.season = p.season
     and s.match_id = p.match_id
     and s.player_code = p.player_code
    where p.advanced_source = 'understat'
      and (
        p.xg is distinct from s.xg
        or p.xa is distinct from s.xa
        or p.shots is distinct from s.shots
        or p.key_passes is distinct from s.key_passes
        or p.xg_chain is distinct from s.xg_chain
        or p.xg_buildup is distinct from s.xg_buildup
      )
  ) then
    raise exception 'Existing Understat advanced metrics disagree with staged source data';
  end if;
end $$;

create temp table understat_enrichment_targets on commit drop as
select
  p.id as player_match_stats_id,
  s.source_match_id,
  s.source_player_id,
  s.xg,
  s.xa,
  s.shots,
  s.key_passes,
  s.xg_chain,
  s.xg_buildup
from player_match_stats p
join source_player_match_stats s
  on s.source = 'understat'
 and s.season = p.season
 and s.match_id = p.match_id
 and s.player_code = p.player_code
where s.player_code is not null
  and p.advanced_source is null;

-- Safety: do not overwrite a non-Understat advanced source if one is introduced later.
do $$
begin
  if exists (
    select 1
    from player_match_stats p
    join source_player_match_stats s
      on s.source='understat'
     and s.season=p.season
     and s.match_id=p.match_id
     and s.player_code=p.player_code
    where s.player_code is not null
      and p.advanced_source is not null
      and p.advanced_source <> 'understat'
  ) then
    raise exception 'A matching live row already has a different advanced_source';
  end if;
end $$;

update player_match_stats p
set
  xg = t.xg,
  xa = t.xa,
  shots = t.shots,
  key_passes = t.key_passes,
  xg_chain = t.xg_chain,
  xg_buildup = t.xg_buildup,
  advanced_source = 'understat',
  advanced_source_match_id = t.source_match_id,
  advanced_source_player_id = t.source_player_id
from understat_enrichment_targets t
where p.id = t.player_match_stats_id;

-- Postcondition: every target must now carry the exact staged metrics and Understat provenance.
do $$
begin
  if exists (
    select 1
    from understat_enrichment_targets t
    join player_match_stats p on p.id=t.player_match_stats_id
    where p.advanced_source <> 'understat'
       or p.advanced_source_match_id is distinct from t.source_match_id
       or p.advanced_source_player_id is distinct from t.source_player_id
       or p.xg is distinct from t.xg
       or p.xa is distinct from t.xa
       or p.shots is distinct from t.shots
       or p.key_passes is distinct from t.key_passes
       or p.xg_chain is distinct from t.xg_chain
       or p.xg_buildup is distinct from t.xg_buildup
  ) then
    raise exception 'Understat enrichment postcondition failed';
  end if;
end $$;

select count(*) as newly_enriched_rows from understat_enrichment_targets;

commit;
