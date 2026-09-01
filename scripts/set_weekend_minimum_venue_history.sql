-- Manual weekend venue review: require at least four relevant venue matches
-- for BOTH teams before producing expected goals, H/D/A probabilities,
-- fair odds, or a model pick. Samples of 4-7 remain partial Venue8 samples.

do $$
declare
  ddl text;
begin
  select pg_get_viewdef('public.betting_manual_weekend_analysis'::regclass, true) into ddl;

  ddl := replace(ddl,
    'home_n8 = 8 AND away_n8 = 8 AND abs(home_vppg8 - away_vppg8) <= 0.30::double precision',
    'home_n8 >= 4 AND away_n8 >= 4 AND abs(home_vppg8 - away_vppg8) <= 0.30::double precision');

  ddl := replace(ddl,
    'home_n8 < 8 OR away_n8 < 8',
    'home_n8 < 4 OR away_n8 < 4');

  ddl := replace(ddl,
    'new_adj_home_lambda AS adj_home_lambda,',
    'CASE WHEN home_n8 >= 4 AND away_n8 >= 4 THEN new_adj_home_lambda ELSE NULL::double precision END AS adj_home_lambda,');

  ddl := replace(ddl,
    'new_adj_away_lambda AS adj_away_lambda,',
    'CASE WHEN home_n8 >= 4 AND away_n8 >= 4 THEN new_adj_away_lambda ELSE NULL::double precision END AS adj_away_lambda,');

  ddl := replace(ddl,
    'new_adj_home_prob AS adj_home_prob,',
    'CASE WHEN home_n8 >= 4 AND away_n8 >= 4 THEN new_adj_home_prob ELSE NULL::double precision END AS adj_home_prob,');

  ddl := replace(ddl,
    'new_adj_draw_prob AS adj_draw_prob,',
    'CASE WHEN home_n8 >= 4 AND away_n8 >= 4 THEN new_adj_draw_prob ELSE NULL::double precision END AS adj_draw_prob,');

  ddl := replace(ddl,
    'new_adj_away_prob AS adj_away_prob,',
    'CASE WHEN home_n8 >= 4 AND away_n8 >= 4 THEN new_adj_away_prob ELSE NULL::double precision END AS adj_away_prob,');

  execute 'create or replace view public.betting_manual_weekend_analysis as ' || ddl;
end $$;
