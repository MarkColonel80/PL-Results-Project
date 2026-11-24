BEGIN;
SELECT pg_advisory_xact_lock(1346031407);
DO $verified$ BEGIN
 IF EXISTS(SELECT 1 FROM pl_weekly_private.runs WHERE status='running' AND lease_until>now()) THEN RAISE EXCEPTION 'Active cloud worker — no identity mutation'; END IF;
 IF NOT EXISTS(SELECT 1 FROM pl_weekly_private.runs WHERE run_key='2026-11-24' AND status='failed' AND owner_run='45410010672' AND NOT (receipts ? 'published')) THEN RAISE EXCEPTION 'Expected 24 November failure receipt changed'; END IF;
 IF EXISTS(SELECT 1 FROM public.players WHERE player_code='605845' OR regexp_replace(coalesce(opta_code,''),'^p','')='605845') THEN RAISE EXCEPTION 'Dino Kaiser canonical collision'; END IF;
 IF NOT EXISTS(SELECT 1 FROM public.players WHERE player_code='171422' AND opta_code='p171422' AND first_name='Alan' AND second_name='Browne' AND birth_date='1995-04-15') THEN RAISE EXCEPTION 'Alan Browne existing permanent identity mismatch'; END IF;
 IF EXISTS(SELECT 1 FROM public.player_seasons WHERE season='2026/27' AND (player_id IN('673','674') OR player_code IN('605845','171422'))) THEN RAISE EXCEPTION 'Existing 2026/27 season identity collision'; END IF;
 IF EXISTS(SELECT 1 FROM public.player_source_ids WHERE player_code IN('605845','171422') OR (source='fotmob' AND source_player_id IN('1692749','434498'))) THEN RAISE EXCEPTION 'Existing source identity collision'; END IF;
END $verified$;
INSERT INTO public.players(player_code,first_name,second_name,web_name,birth_date,opta_code,identity_origin_source,identity_origin_source_player_id,identity_created_method)
VALUES('605845','Dino','Kaiser','Kaiser','2007-02-09','p605845','fpl_official','674','official_permanent_code_20261124');
INSERT INTO public.player_seasons(season,player_code,player_id,team_code,team_name,position) VALUES
('2026/27','605845','674','54','Fulham','Goalkeeper'),
('2026/27','171422','673','56','Sunderland','Midfielder');
INSERT INTO public.player_source_ids(source,source_player_id,player_code,mapping_method,verified,source_note) VALUES
('fotmob','1692749','605845','native_opta_id_equals_official_fpl_opta_code',true,'Verified 2026-11-24T14:04:32Z: FPL bootstrap ID 674, permanent code 605845 and official opta_code p605845 equal FotMob native playerStats optaId 605845 for player ID 1692749 in match 5795522. FPL bootstrap SHA256 e1c4374ed3260b4b46b9894d069a4e15f7addf83b6e3fd5367c166275ca2ac5d; FotMob matchDetails SHA256 ed6e4a711a287e74f59b4df1e4344719652124edd6d788b919d9397bdef7faea. Display name not used for matching. https://fantasy.premierleague.com/api/bootstrap-static/ https://www.fotmob.com/api/data/matchDetails?matchId=5795522'),
('fotmob','434498','171422','native_opta_id_equals_official_fpl_opta_code',true,'Verified 2026-11-24T14:04:32Z: FPL bootstrap ID 673, permanent code 171422 and official opta_code p171422 equal FotMob native playerStats optaId 171422 for player ID 434498 in match 5795516. Canonical Alan Browne p171422 pre-existed and was preserved without alteration. FPL bootstrap SHA256 e1c4374ed3260b4b46b9894d069a4e15f7addf83b6e3fd5367c166275ca2ac5d; FotMob matchDetails SHA256 deea95b1375fbbcde1d01a0507ece0900f4b1dc6457a30ca61c1319992418e07. Display name not used for matching. https://fantasy.premierleague.com/api/bootstrap-static/ https://www.fotmob.com/api/data/matchDetails?matchId=5795516');
COMMIT;
