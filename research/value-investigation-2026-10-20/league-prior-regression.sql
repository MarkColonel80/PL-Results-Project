with synthetic as (
  -- The 16th previous row is an outlier and must be outside the 15-match window.
  select 'prior-' || lpad(i::text, 2, '0') match_id,
    timestamptz '2026-10-01 15:00:00+00' - i * interval '1 day' kickoff_time,
    true was_home,
    case when i=16 then 999 else 1 end::numeric goals_for,
    case when i=16 then 999 else 2 end::numeric goals_against,
    case when i=16 then 999 else 1 end::numeric xg_for,
    case when i=16 then 999 else 2 end::numeric xg_against
  from generate_series(1,16) i
  union all
  select id, timestamptz '2026-10-01 15:00:00+00', true,
    99::numeric, 88::numeric, 77::numeric, 66::numeric
  from (values ('a-simultaneous'), ('z-simultaneous')) t(id)
  union all
  select 'future', timestamptz '2026-10-02 15:00:00+00', true, 999,999,999,999
), lg as (
  -- Match IDs cannot establish availability between simultaneous fixtures.
  -- Date-only timestamps conservatively exclude the entire same-date block.
  select target.match_id, prior.lhome, prior.laway
  from synthetic target
  left join lateral (
    select .35 * avg(goals_for::numeric) + .65 * avg(xg_for) as lhome,
           .35 * avg(goals_against::numeric) + .65 * avg(xg_against) as laway
    from (
      select b.goals_for, b.goals_against, b.xg_for, b.xg_against
      from synthetic b
      where b.was_home and b.kickoff_time < target.kickoff_time
      order by b.kickoff_time desc, b.match_id desc
      limit 15
    ) q
  ) prior on true
  where target.was_home
)
select count(*)=2 as both_simultaneous_targets_present,
  bool_and(abs(lhome-1)<1e-12) as excludes_simultaneous_future_and_sixteenth_home,
  bool_and(abs(laway-2)<1e-12) as excludes_simultaneous_future_and_sixteenth_away,
  count(distinct (lhome, laway))=1 as lexical_ids_do_not_change_baseline
from lg where match_id in ('a-simultaneous','z-simultaneous');
