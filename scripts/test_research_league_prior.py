"""Emit a read-only PostgreSQL regression query for the actual research CTE.

Run: python3 scripts/test_research_league_prior.py > /tmp/league-prior-test.sql
Execute the emitted SELECT in PostgreSQL; all four checks must return true.
The source CREATE MATERIALIZED VIEW is never executed.
"""
from pathlib import Path

source = (Path(__file__).parent / "add_v3_venue8_15_residual_research_inputs.sql").read_text()
start = source.index("), lg as (") + 3
end = source.index("\n)\nselect h.season", start) + 2
league_cte = source[start:end].replace("public.betting_team_features_v2_cache", "synthetic")
print("""with synthetic as (
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
), """ + league_cte + """
select count(*)=2 as both_simultaneous_targets_present,
  bool_and(abs(lhome-1)<1e-12) as excludes_simultaneous_future_and_sixteenth_home,
  bool_and(abs(laway-2)<1e-12) as excludes_simultaneous_future_and_sixteenth_away,
  count(distinct (lhome, laway))=1 as lexical_ids_do_not_change_baseline
from lg where match_id in ('a-simultaneous','z-simultaneous');""")
