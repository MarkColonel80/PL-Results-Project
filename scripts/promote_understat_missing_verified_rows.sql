-- Promote missing Understat appearances only when the Understat player ID already has
-- a verified NON-source-native canonical identity.
--
-- This is deliberately separate from advanced-metric enrichment. It fills genuine
-- base-source gaps without using player names and refuses legacy source_native_identity
-- rows until those identities are independently reconciled.
-- Repeat-safe: a second run should insert 0 rows.

begin;

create temp table understat_missing_verified on commit drop as
select s.*
from source_player_match_stats s
join player_source_ids psi
  on psi.source='understat'
 and psi.source_player_id=s.source_player_id
 and psi.player_code=s.player_code
 and psi.verified
where s.source='understat'
  and s.player_code is not null
  and s.match_id is not null
  and psi.mapping_method <> 'source_native_identity'
  and not exists (
    select 1 from player_match_stats p
    where p.season=s.season
      and p.match_id=s.match_id
      and p.player_code=s.player_code
  );

-- Safety: every promoted identity must be a real canonical players row and must
-- not use a provider-native player_code prefix.
do $$
begin
  if exists (
    select 1
    from understat_missing_verified t
    left join players p on p.player_code=t.player_code
    where p.player_code is null
       or t.player_code like 'understat:%'
       or t.player_code like 'tm:%'
       or t.player_code like 'fotmob:%'
       or t.player_code like 'sofascore:%'
  ) then
    raise exception 'Missing/invalid canonical identity in Understat promotion target';
  end if;
end $$;

insert into player_match_stats (
  season, gameweek, match_id, player_id, player_code, player_name, team_name,
  minutes_played, is_starting, goals, assists, xg, xa, shots, shots_on_target,
  chances_created, yellow_cards, red_cards, own_goals, key_passes, xg_chain,
  xg_buildup, source, source_match_id, source_player_id, data_quality,
  advanced_source, advanced_source_match_id, advanced_source_player_id
)
select
  t.season,
  null,
  t.match_id,
  'understat:' || t.source_player_id,
  t.player_code,
  t.player_name,
  t.team_name,
  t.minutes_played,
  t.is_starting,
  coalesce(t.goals,0),
  coalesce(t.assists,0),
  t.xg,
  t.xa,
  t.shots,
  null,
  null,
  coalesce(t.yellow_cards,0),
  coalesce(t.red_cards,0),
  coalesce(t.own_goals,0),
  t.key_passes,
  t.xg_chain,
  t.xg_buildup,
  'understat',
  t.source_match_id,
  t.source_player_id,
  'source_reported_verified_cross_source_identity',
  'understat',
  t.source_match_id,
  t.source_player_id
from understat_missing_verified t;

-- Postcondition: every target now exists exactly once in the live base.
do $$
begin
  if exists (
    select 1
    from understat_missing_verified t
    left join lateral (
      select count(*) as n
      from player_match_stats p
      where p.season=t.season and p.match_id=t.match_id and p.player_code=t.player_code
    ) x on true
    where x.n <> 1
  ) then
    raise exception 'Understat missing-row promotion postcondition failed';
  end if;
end $$;

select count(*) as promoted_missing_verified_rows from understat_missing_verified;

commit;
