-- Security hardening applied 2026-09-02 after Supabase advisor warning.
-- Goal: browser roles can read required public app data but cannot mutate it;
-- internal identity/source mapping tables and write-capable maintenance RPCs are not public.

-- Enable RLS on previously exposed public tables.
alter table public.betting_manual_fixtures enable row level security;
alter table public.betting_manual_weekend_snapshot enable row level security;
alter table public.betting_model_match_predictions enable row level security;
alter table public.betting_model_v5_agreement_inputs enable row level security;
alter table public.betting_model_v5_agreement_predictions enable row level security;
alter table public.fpl_player_match_stats enable row level security;
alter table public.player_match_ratings enable row level security;
alter table public.player_match_stats enable row level security;
alter table public.player_seasons enable row level security;
alter table public.players enable row level security;
alter table public.source_match_mappings enable row level security;
alter table public.source_player_mappings enable row level security;

-- Remove all browser-role privileges first.
revoke all on table public.betting_manual_fixtures from anon, authenticated;
revoke all on table public.betting_manual_weekend_snapshot from anon, authenticated;
revoke all on table public.betting_model_match_predictions from anon, authenticated;
revoke all on table public.betting_model_v5_agreement_inputs from anon, authenticated;
revoke all on table public.betting_model_v5_agreement_predictions from anon, authenticated;
revoke all on table public.fpl_player_match_stats from anon, authenticated;
revoke all on table public.player_match_ratings from anon, authenticated;
revoke all on table public.player_match_stats from anon, authenticated;
revoke all on table public.player_seasons from anon, authenticated;
revoke all on table public.players from anon, authenticated;
revoke all on table public.source_match_mappings from anon, authenticated;
revoke all on table public.source_player_mappings from anon, authenticated;

-- Restore SELECT only for tables intentionally consumed by the browser app.
grant select on table public.betting_manual_fixtures to anon, authenticated;
grant select on table public.betting_manual_weekend_snapshot to anon, authenticated;
grant select on table public.betting_model_match_predictions to anon, authenticated;
grant select on table public.betting_model_v5_agreement_inputs to anon, authenticated;
grant select on table public.betting_model_v5_agreement_predictions to anon, authenticated;
grant select on table public.fpl_player_match_stats to anon, authenticated;
grant select on table public.player_match_ratings to anon, authenticated;
grant select on table public.player_match_stats to anon, authenticated;
grant select on table public.player_seasons to anon, authenticated;
grant select on table public.players to anon, authenticated;

-- Read-only RLS policies.
drop policy if exists betting_manual_fixtures_read on public.betting_manual_fixtures;
create policy betting_manual_fixtures_read on public.betting_manual_fixtures for select to anon, authenticated using (true);

drop policy if exists betting_manual_weekend_snapshot_read on public.betting_manual_weekend_snapshot;
create policy betting_manual_weekend_snapshot_read on public.betting_manual_weekend_snapshot for select to anon, authenticated using (true);

drop policy if exists betting_model_match_predictions_read on public.betting_model_match_predictions;
create policy betting_model_match_predictions_read on public.betting_model_match_predictions for select to anon, authenticated using (true);

drop policy if exists betting_model_v5_agreement_inputs_read on public.betting_model_v5_agreement_inputs;
create policy betting_model_v5_agreement_inputs_read on public.betting_model_v5_agreement_inputs for select to anon, authenticated using (true);

drop policy if exists betting_model_v5_agreement_predictions_read on public.betting_model_v5_agreement_predictions;
create policy betting_model_v5_agreement_predictions_read on public.betting_model_v5_agreement_predictions for select to anon, authenticated using (true);

drop policy if exists fpl_player_match_stats_read on public.fpl_player_match_stats;
create policy fpl_player_match_stats_read on public.fpl_player_match_stats for select to anon, authenticated using (true);

drop policy if exists player_match_ratings_read on public.player_match_ratings;
create policy player_match_ratings_read on public.player_match_ratings for select to anon, authenticated using (true);

drop policy if exists player_match_stats_read on public.player_match_stats;
create policy player_match_stats_read on public.player_match_stats for select to anon, authenticated using (true);

drop policy if exists player_seasons_read on public.player_seasons;
create policy player_seasons_read on public.player_seasons for select to anon, authenticated using (true);

drop policy if exists players_read on public.players;
create policy players_read on public.players for select to anon, authenticated using (true);

-- source_match_mappings and source_player_mappings intentionally have no browser policies/grants.

-- Lock internal SECURITY DEFINER maintenance RPCs away from browser roles.
revoke execute on function public.merge_player_metadata(jsonb) from public, anon, authenticated;
revoke execute on function public.promote_transfermarkt_football_history() from public, anon, authenticated;
revoke execute on function public.resolve_transfermarkt_fpl_identity() from public, anon, authenticated;
revoke execute on function public.resolve_transfermarkt_season_identity() from public, anon, authenticated;

grant execute on function public.merge_player_metadata(jsonb) to service_role;
grant execute on function public.promote_transfermarkt_football_history() to service_role;
grant execute on function public.resolve_transfermarkt_fpl_identity() to service_role;
grant execute on function public.resolve_transfermarkt_season_identity() to service_role;

-- Second pass: make browser-facing aggregate views obey caller RLS/privileges.
alter view public.football_player_season_stats set (security_invoker=true);
alter view public.football_player_team_season_stats set (security_invoker=true);
alter view public.fpl_player_season_stats set (security_invoker=true);
alter view public.player_career_fpl_stats set (security_invoker=true);
alter view public.player_season_stats set (security_invoker=true);
alter view public.player_decision_stats_v1 set (security_invoker=true);
alter view public.betting_team_match_v1 set (security_invoker=true);
alter view public.betting_player_goal_profile_v1 set (security_invoker=true);

-- Internal/research views use invoker semantics and are not selectable by browser roles.
alter view public.betting_team_match_v2 set (security_invoker=true);
alter view public.player_career_stats set (security_invoker=true);
alter view public.player_team_season_stats set (security_invoker=true);
alter view public.player_match_ratings_comparison set (security_invoker=true);
alter view public.team_form_window_cache_with_v8 set (security_invoker=true);
alter view public.betting_manual_weekend_capped_actuals set (security_invoker=true);
alter view public.betting_manual_weekend_analysis_uncapped set (security_invoker=true);
alter view public.betting_manual_weekend_analysis set (security_invoker=true);

revoke all privileges on public.betting_team_match_v2 from anon, authenticated;
revoke all privileges on public.player_career_stats from anon, authenticated;
revoke all privileges on public.player_team_season_stats from anon, authenticated;
revoke all privileges on public.player_match_ratings_comparison from anon, authenticated;
revoke all privileges on public.team_form_window_cache_with_v8 from anon, authenticated;
revoke all privileges on public.betting_manual_weekend_capped_actuals from anon, authenticated;
revoke all privileges on public.betting_manual_weekend_analysis_uncapped from anon, authenticated;
revoke all privileges on public.betting_manual_weekend_analysis from anon, authenticated;

-- Research materialized views are internal. Keep only the two FPL aggregate caches
-- public because security-invoker public views depend on them.
do $$
declare r record;
begin
  for r in
    select schemaname, matviewname
    from pg_matviews
    where schemaname='public'
      and matviewname not in ('fpl_player_season_stats_cache','fpl_player_team_season_stats_cache')
  loop
    execute format('revoke all privileges on %I.%I from anon, authenticated', r.schemaname, r.matviewname);
  end loop;
end $$;

-- Pin function lookup paths to prevent mutable search_path/object shadowing warnings.
alter function public.canonicalize_fpl_player_name() set search_path = public, pg_temp;
alter function public.enforce_provider_neutral_player_code() set search_path = public, pg_temp;
alter function public.betting_poisson_1x2(double precision,double precision) set search_path = public, pg_temp;
alter function public.poisson_1x2_probs(double precision,double precision) set search_path = public, pg_temp;
alter function public.betting_elo_eval(numeric,numeric,numeric,text[]) set search_path = public, pg_temp;

-- Secure the player-name audit path without exposing full source staging rows.
-- The audit view needs only five source metadata columns.
revoke all privileges on public.source_player_match_stats from anon, authenticated;
grant select (source, source_player_id, player_name, season, team_name)
  on public.source_player_match_stats to anon, authenticated;

drop policy if exists source_player_match_stats_audit_metadata_read on public.source_player_match_stats;
create policy source_player_match_stats_audit_metadata_read
  on public.source_player_match_stats
  for select
  to anon, authenticated
  using (source in ('understat','transfermarkt'));

alter view public.player_identity_name_audit_v1 set (security_invoker=true);

-- The existing audit UI writes approval metadata directly. Limit that write surface to
-- SELECT/INSERT/UPDATE only, and only for an exact already-verified source mapping.
revoke all privileges on public.player_identity_name_audit_reviews from anon, authenticated;
grant select, insert, update on public.player_identity_name_audit_reviews to anon, authenticated;

drop policy if exists audit_reviews_insert on public.player_identity_name_audit_reviews;
drop policy if exists audit_reviews_update on public.player_identity_name_audit_reviews;
drop policy if exists audit_reviews_read on public.player_identity_name_audit_reviews;

create policy audit_reviews_read
  on public.player_identity_name_audit_reviews
  for select
  to anon, authenticated
  using (true);

create policy audit_reviews_insert
  on public.player_identity_name_audit_reviews
  for insert
  to anon, authenticated
  with check (
    exists (
      select 1
      from public.player_source_ids psi
      where psi.source = player_identity_name_audit_reviews.source
        and psi.source_player_id = player_identity_name_audit_reviews.source_player_id
        and psi.player_code = player_identity_name_audit_reviews.player_code
        and psi.verified = true
    )
  );

create policy audit_reviews_update
  on public.player_identity_name_audit_reviews
  for update
  to anon, authenticated
  using (
    exists (
      select 1
      from public.player_source_ids psi
      where psi.source = player_identity_name_audit_reviews.source
        and psi.source_player_id = player_identity_name_audit_reviews.source_player_id
        and psi.player_code = player_identity_name_audit_reviews.player_code
        and psi.verified = true
    )
  )
  with check (
    exists (
      select 1
      from public.player_source_ids psi
      where psi.source = player_identity_name_audit_reviews.source
        and psi.source_player_id = player_identity_name_audit_reviews.source_player_id
        and psi.player_code = player_identity_name_audit_reviews.player_code
        and psi.verified = true
    )
  );
