-- Manual reconciliation for the final three legacy Understat identities.
--
-- This is intentionally a MANUAL identity exception. Automated player-name matching
-- remains prohibited. These three identities were individually reviewed against the
-- canonical player table, club/season history and provider evidence.
--
-- Approved manual decisions (2026-08-26):
--   Understat 924   Steven Pienaar          -> canonical 7525
--   Understat 1089  Juan Cuadrado           -> canonical 66733
--   Transfermarkt 91970 Juan Cuadrado       -> canonical 66733
--   Understat 1015  Rushian Hepburn-Murphy  -> keep existing unique canonical
--                                             plp:60c49e5ec1254a21a99dc224483b85c7,
--                                             mark manually verified and promote the
--                                             source-only 2015/16 one-minute appearance.
--
-- Evidence summary:
-- - Pienaar: unique exact full name; Everton -> Sunderland season continuity;
--   2016/17 FPL comparison has the exact same 15-match set and zero goal mismatches.
-- - Cuadrado: unique exact full name across the duplicate identities; all three
--   identities form continuous Chelsea seasons (2014/15 Understat, 2015/16
--   Transfermarkt, 2016/17 established canonical).
-- - Hepburn-Murphy: unique exact full name in players; Aston Villa in both seasons;
--   Transfermarkt omitted his one-minute 2015/16 substitute appearance, so there is
--   no competing canonical identity to merge.
--
-- Repeat-safe. All writes are inside one transaction and guarded by collision and
-- dependency checks.

begin;

create temp table manual_identity_merges (
  old_code text primary key,
  new_code text not null,
  expected_name text not null
) on commit drop;

insert into manual_identity_merges(old_code,new_code,expected_name) values
  ('plp:3eb1306793c8468ab41eb988b5e13afb','7525','steven pienaar'),
  ('plp:8f20bdb0d19c41868c3d9c27693ff2f0','66733','juan cuadrado'),
  ('plp:062a2582c48b472f9bd76a37e557bcb9','66733','juan cuadrado');

-- Manual identity safety gates.
do $$
begin
  if exists (
    select 1
    from manual_identity_merges m
    left join players old on old.player_code=m.old_code
    left join players target on target.player_code=m.new_code
    where old.player_code is null or target.player_code is null
  ) then
    raise exception 'Missing old or target player row for manual identity reconciliation';
  end if;

  -- Both sides must display the reviewed full name. web_name may be surname-only on
  -- established FPL identities, so first_name + second_name is checked as well.
  if exists (
    select 1
    from manual_identity_merges m
    join players old on old.player_code=m.old_code
    join players target on target.player_code=m.new_code
    where lower(trim(coalesce(nullif(concat_ws(' ',old.first_name,old.second_name),''),old.web_name,''))) <> m.expected_name
       or lower(trim(coalesce(nullif(concat_ws(' ',target.first_name,target.second_name),''),target.web_name,''))) <> m.expected_name
  ) then
    raise exception 'Reviewed player name no longer matches expected manual identity';
  end if;

  if exists (
    select 1
    from manual_identity_merges m
    join player_match_stats old on old.player_code=m.old_code
    join player_match_stats target
      on target.player_code=m.new_code and target.match_id=old.match_id
  ) then
    raise exception 'player_match_stats collision detected in manual identity merge';
  end if;

  if exists (
    select 1
    from manual_identity_merges m
    join player_seasons old on old.player_code=m.old_code
    join player_seasons target
      on target.player_code=m.new_code and target.season=old.season
  ) then
    raise exception 'player_seasons collision detected in manual identity merge';
  end if;

  -- The preflight dependency audit established that old codes are referenced only
  -- in these expected identity/history tables. Abort if that changes.
  if exists (select 1 from manual_identity_merges m join fpl_player_match_stats x on x.player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join goals x on x.player_code=m.old_code or x.assist_player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join lineups x on x.player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join player_match_ratings x on x.player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join player_provider_ids x on x.player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join source_game_events x on x.player_code=m.old_code or x.assist_player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join source_player_mappings x on x.player_code=m.old_code)
  then
    raise exception 'Unexpected dependency found for old manual-merge player_code';
  end if;
end $$;

-- Re-key source-faithful staging and live history. Base football provenance is left
-- unchanged; the manual decision is recorded on player_source_ids.
update source_player_match_stats s
set player_code=m.new_code,
    data_quality=case
      when s.source='understat' then 'source_reported_manual_name_verified_identity'
      else s.data_quality
    end
from manual_identity_merges m
where s.player_code=m.old_code;

update player_match_stats p
set player_code=m.new_code
from manual_identity_merges m
where p.player_code=m.old_code;

update player_seasons ps
set player_code=m.new_code
from manual_identity_merges m
where ps.player_code=m.old_code;

update player_source_ids psi
set player_code=m.new_code,
    mapping_method='manual_name_verified',
    verified=true,
    source_note='Manual exception approved after individual review: unique exact full name plus club/season continuity and supporting provider match-history evidence. This is not automated name matching.'
from manual_identity_merges m
where psi.player_code=m.old_code;

delete from players p
using manual_identity_merges m
where p.player_code=m.old_code;

-- Rushian Hepburn-Murphy: retain the existing canonical identity, but convert its
-- Understat crosswalk from source-native to an explicitly reviewed manual identity.
do $$
declare
  rush_code constant text := 'plp:60c49e5ec1254a21a99dc224483b85c7';
  n integer;
begin
  select count(*) into n
  from players p
  where lower(trim(coalesce(nullif(concat_ws(' ',p.first_name,p.second_name),''),p.web_name,'')))='rushian hepburn-murphy';
  if n <> 1 then
    raise exception 'Rushian Hepburn-Murphy name is no longer unique in players (count=%)', n;
  end if;

  if not exists (
    select 1 from player_source_ids
    where source='understat' and source_player_id='1015' and player_code=rush_code and verified
  ) then
    raise exception 'Expected Understat 1015 Rushian identity crosswalk is missing';
  end if;

  if exists (
    select 1 from source_player_match_stats
    where source='understat' and source_player_id='1015'
      and (player_code<>rush_code or team_name<>'Aston Villa' or season not in ('2014/15','2015/16'))
  ) then
    raise exception 'Rushian staged history no longer matches reviewed Aston Villa seasons';
  end if;
end $$;

update player_source_ids
set mapping_method='manual_name_verified',
    verified=true,
    source_note='Manual exception approved after individual review: unique exact full name and Aston Villa season continuity. Transfermarkt omits the source-reported one-minute 2015/16 substitute appearance. This is not automated name matching.'
where source='understat'
  and source_player_id='1015'
  and player_code='plp:60c49e5ec1254a21a99dc224483b85c7';

update source_player_match_stats
set data_quality='source_reported_manual_name_verified_identity'
where source='understat' and source_player_id='1015';

-- Add the 2015/16 membership if it is not already present.
insert into player_seasons(season,player_code,player_id,team_code,team_name,position)
select distinct
  s.season,
  s.player_code,
  'understat:' || s.source_player_id,
  s.source_team_id,
  s.team_name,
  null
from source_player_match_stats s
where s.source='understat'
  and s.source_player_id='1015'
  and s.season='2015/16'
  and not exists (
    select 1 from player_seasons ps
    where ps.season=s.season and ps.player_code=s.player_code
  );

-- Promote only the reviewed source-only 2015/16 appearance, mirroring the existing
-- 2014/15 Understat row shape and retaining Understat for both base and advanced
-- provenance because no richer live football row exists for this appearance.
insert into player_match_stats(
  season,gameweek,match_id,player_id,player_name,team_name,minutes_played,is_starting,
  goals,assists,xg,xa,shots,shots_on_target,chances_created,player_code,source,
  source_match_id,source_player_id,yellow_cards,red_cards,data_quality,own_goals,
  key_passes,xg_chain,xg_buildup,advanced_source,advanced_source_match_id,
  advanced_source_player_id
)
select
  s.season,
  null,
  s.match_id,
  'understat:' || s.source_player_id,
  s.player_name,
  s.team_name,
  s.minutes_played,
  s.is_starting,
  coalesce(s.goals,0),
  coalesce(s.assists,0),
  s.xg,
  s.xa,
  s.shots,
  null,
  null,
  s.player_code,
  'understat',
  s.source_match_id,
  s.source_player_id,
  coalesce(s.yellow_cards,0),
  coalesce(s.red_cards,0),
  'source_reported_manual_name_verified_identity',
  coalesce(s.own_goals,0),
  s.key_passes,
  s.xg_chain,
  s.xg_buildup,
  'understat',
  s.source_match_id,
  s.source_player_id
from source_player_match_stats s
where s.source='understat'
  and s.source_player_id='1015'
  and s.season='2015/16'
  and not exists (
    select 1 from player_match_stats p
    where p.match_id=s.match_id and p.player_code=s.player_code
  );

-- Postconditions.
do $$
begin
  if exists (select 1 from manual_identity_merges m join players x on x.player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join player_source_ids x on x.player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join player_seasons x on x.player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join player_match_stats x on x.player_code=m.old_code)
     or exists (select 1 from manual_identity_merges m join source_player_match_stats x on x.player_code=m.old_code)
  then
    raise exception 'Old duplicate player_code remains after manual reconciliation';
  end if;

  if not exists (
    select 1 from player_match_stats
    where match_id='1516-astonvilla-newcastle'
      and player_code='plp:60c49e5ec1254a21a99dc224483b85c7'
      and source='understat'
  ) then
    raise exception 'Reviewed Rushian 2015/16 appearance was not promoted';
  end if;
end $$;

select
  (select count(*) from player_source_ids where mapping_method='manual_name_verified' and verified) as total_manual_verified_crosswalks,
  (select count(*) from player_match_stats where advanced_source='understat') as total_understat_enriched_rows;

commit;
