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
