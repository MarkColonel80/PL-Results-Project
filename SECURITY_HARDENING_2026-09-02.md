# Supabase security hardening — 2026-09-02

## Trigger

Supabase Security Advisor emailed a critical `rls_disabled_in_public` warning for PL Results Project. Live inspection confirmed the issue was real: 12 tables in the exposed `public` schema had RLS disabled and the `anon` / `authenticated` roles held broad table privileges including INSERT, UPDATE and DELETE.

## Immediate RLS fix

RLS was enabled on the 12 affected tables:
- `betting_manual_fixtures`
- `betting_manual_weekend_snapshot`
- `betting_model_match_predictions`
- `betting_model_v5_agreement_inputs`
- `betting_model_v5_agreement_predictions`
- `fpl_player_match_stats`
- `player_match_ratings`
- `player_match_stats`
- `player_seasons`
- `players`
- `source_match_mappings`
- `source_player_mappings`

The ten browser-data tables were changed to SELECT-only for `anon` / `authenticated`, with explicit RLS SELECT policies. `source_match_mappings` and `source_player_mappings` are internal and now have no browser grants or policies.

Post-migration verification confirmed all 12 tables have RLS enabled; the ten public-data tables have SELECT but no INSERT/UPDATE/DELETE for browser roles; the two internal mapping tables have no browser access.

## Internal write RPCs

The advisor sweep exposed four `SECURITY DEFINER` maintenance functions callable by the browser roles:
- `merge_player_metadata(jsonb)`
- `promote_transfermarkt_football_history()`
- `resolve_transfermarkt_fpl_identity()`
- `resolve_transfermarkt_season_identity()`

Their definitions were inspected and they can write canonical players, historical player-match rows and identity mappings. EXECUTE was revoked from `public`, `anon` and `authenticated`, and retained for `service_role`.

## Security-definer views

Frontend dependencies were audited before changing view security.

Public browser-facing views were converted to `security_invoker=true` and tested under the actual `anon` database role:
- `football_player_season_stats`
- `football_player_team_season_stats`
- `fpl_player_season_stats`
- `player_career_fpl_stats`
- `player_season_stats`
- `player_decision_stats_v1`
- `betting_team_match_v1`
- `betting_player_goal_profile_v1`

Internal/research views were also switched to security-invoker but all browser privileges were revoked:
- `betting_team_match_v2`
- `player_career_stats`
- `player_team_season_stats`
- `player_match_ratings_comparison`
- `team_form_window_cache_with_v8`
- `betting_manual_weekend_capped_actuals`
- `betting_manual_weekend_analysis_uncapped`
- `betting_manual_weekend_analysis`

The public frontend smoke test succeeded after these changes.

## Research materialized views

Browser access was revoked from public research materialized views. Two FPL aggregate caches remain selectable because the public security-invoker aggregate views depend on them:
- `fpl_player_season_stats_cache`
- `fpl_player_team_season_stats_cache`

These two are the only remaining `materialized_view_in_api` security-advisor warnings and contain aggregate public football/FPL data rather than write-capable or secret data.

## Function search paths

The following functions had their `search_path` pinned to `public, pg_temp`:
- `canonicalize_fpl_player_name()`
- `enforce_provider_neutral_player_code()`
- `betting_poisson_1x2(double precision,double precision)`
- `poisson_1x2_probs(double precision,double precision)`
- `betting_elo_eval(numeric,numeric,numeric,text[])`

This cleared the mutable-search-path advisor warnings.

## Player-name audit path

`player_identity_name_audit_v1` originally needed owner privileges because it reads internal `source_player_match_stats`. Rather than leave it security-definer, the source staging table now exposes only the five metadata columns needed by the audit page to browser roles:
- `source`
- `source_player_id`
- `player_name`
- `season`
- `team_name`

RLS restricts that read to Understat and Transfermarkt rows. The audit view is now security-invoker.

The existing audit page directly upserts approval metadata using the browser Supabase client. To preserve this workflow while limiting risk, `player_identity_name_audit_reviews` now grants only SELECT/INSERT/UPDATE and its INSERT/UPDATE policies require the submitted `(source, source_player_id, player_code)` to match an already verified row in `player_source_ids`. DELETE is not granted. A real anonymous-role audit read and approval upsert were tested inside a transaction and rolled back successfully.

This approval flag remains the only intentional browser write path discovered in the current application; it cannot alter canonical identity mappings or invent a new mapping key.

## Final Security Advisor state

After all migrations, Supabase Security Advisor reports:
- **0 ERROR / critical findings**
- no `rls_disabled_in_public` findings
- no publicly executable SECURITY DEFINER write functions
- no `security_definer_view` errors
- no mutable function `search_path` warnings
- no exposed research materialized-view warnings

Remaining notices only:

### INFO — RLS enabled, no policy
- `source_game_events`
- `source_match_mappings`
- `source_player_mappings`

This is intentional: these are private internal tables and absence of a browser policy denies browser access.

### WARN — materialized view in API
- `fpl_player_season_stats_cache`
- `fpl_player_team_season_stats_cache`

These are intentionally retained as public-read aggregate caches because security-invoker public views depend on them.

## Reproducibility

The complete SQL is stored at:
- `scripts/security_hardening_2026_09_02.sql`

The live Supabase migrations were applied as:
- first-pass RLS/public-write lock-down
- `security_advisor_second_pass`
- `secure_player_identity_audit_path`

No betting model logic or production data values were intentionally changed by this security work.
