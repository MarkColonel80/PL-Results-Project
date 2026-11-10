begin;
select pg_advisory_xact_lock(1346031407);
do $$ begin
 if exists(select 1 from pl_weekly_private.runs where status='running' and lease_until>now()) then raise exception 'Active worker'; end if;
 if not exists(select 1 from pl_weekly_private.runs where run_key='2026-11-10' and status='failed' and owner_run='42787760318' and not receipts ? 'published') then raise exception 'Recovery receipt changed'; end if;
 if exists(select 1 from players where player_code in ('536108','671103') or regexp_replace(opta_code,'^p','') in ('536108','671103')) then raise exception 'Canonical collision'; end if;
 if exists(select 1 from player_seasons where season='2026/27' and player_id in ('671','672')) then raise exception 'Season collision'; end if;
 if exists(select 1 from player_source_ids where (source='fotmob' and source_player_id in ('1524184','1714552')) or player_code in ('536108','671103')) then raise exception 'Source mapping collision'; end if;
end $$;
insert into players(player_code,first_name,second_name,web_name,birth_date,opta_code,identity_origin_source,identity_origin_source_player_id,identity_created_method) values
('536108','Luca','Gunter','Gunter','2005-03-23','p536108','fpl_official','671','official_permanent_code_20261110'),
('671103','Modou Kéba','Cissé','Cissé','2005-08-04','p671103','fpl_official','672','official_permanent_code_20261110');
insert into player_seasons(season,player_code,player_id,team_code,team_name,position) values
('2026/27','536108','671','6','Tottenham Hotspur','Goalkeeper'),
('2026/27','671103','672','7','Aston Villa','Defender');
insert into player_source_ids(source,source_player_id,player_code,mapping_method,verified,source_note) values
('fotmob','1524184','536108','native_opta_id_equals_official_fpl_opta_code',true,'Verified 2026-11-10T16:53:19Z: official FPL bootstrap id 671 / code 536108 / opta_code p536108 equals FotMob playerStats 1524184 optaId 536108 in match 5795511. Names are display metadata only. Bootstrap SHA256 c51f3e5612125d34da0ef4d6aa158bd9e2da4ced8b31b711e3892396fc777171. https://fantasy.premierleague.com/api/bootstrap-static/ https://www.fotmob.com/api/data/matchDetails?matchId=5795511'),
('fotmob','1714552','671103','native_opta_id_equals_official_fpl_opta_code',true,'Verified 2026-11-10T16:53:20Z: official FPL bootstrap id 672 / code 671103 / opta_code p671103 equals FotMob playerStats 1714552 optaId 671103 in match 5795512. Names are display metadata only. Bootstrap SHA256 c51f3e5612125d34da0ef4d6aa158bd9e2da4ced8b31b711e3892396fc777171. https://fantasy.premierleague.com/api/bootstrap-static/ https://www.fotmob.com/api/data/matchDetails?matchId=5795512');
commit;
