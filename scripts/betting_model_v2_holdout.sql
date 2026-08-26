-- Betting Model v2 — FROZEN 2025/26 holdout evaluation
-- Frozen before inspecting 2025/26 bookmaker performance.
-- Development/tuning sample: 2019/20 through 2023/24 only.
-- 2024/25 is allowed as pre-holdout football history but has no xG and is never coerced to zero.
--
-- Frozen specification:
--   * 30-match team attack/defence history
--   * team signal: xG weight up to 65%, actual goals take the remainder
--   * xG weight scales down automatically when xG coverage is partial/missing
--   * 4 pseudo-matches of league-average shrinkage
--   * rolling league home/away scoring baseline
--   * damped multiplicative attack x opponent-defence strength, exponent 0.75
--   * independent Poisson score grid, no Dixon-Coles correction
--
-- Holdout result (380 matches, 2025/26):
--   Model v2 Brier 0.61905, log loss 1.03208, top-pick accuracy 49.5%
--   No-vig closing market Brier 0.60774, log loss 1.01177, top-pick accuracy 49.5%
--   Model v1 reference: Brier 0.6245, log loss 1.0400
--
-- Strongest model-v-market edge per match, flat £1 stake at Football-Data closing prices:
--   0–2%:   18 bets,  -6.7% avg-close ROI,  -2.6% best-close ROI
--   2–5%:  125 bets, +19.9% avg-close ROI, +25.5% best-close ROI
--   5–10%: 161 bets, -27.8% avg-close ROI, -23.8% best-close ROI
--   10%+:   76 bets, -14.7% avg-close ROI,  -8.3% best-close ROI
--
-- The 2–5% bucket is an observed holdout result, NOT a parameter to tune against this season.
-- It must be validated on additional untouched seasons before being treated as a betting signal.

with paired as (
  select h.season,h.gameweek,h.match_id,h.kickoff_time,h.team_name home_team,h.opponent_team away_team,
         h.goals_for hg,h.goals_against ag,
         h.n30 hn,h.gf30 hgf,h.ga30 hga,h.xgf30 hxgf,h.xga30 hxga,h.nxg30 hnxg,
         a.n30 an,a.gf30 agf,a.ga30 aga,a.xgf30 axgf,a.xga30 axga,a.nxg30 anxg,
         h.league_home_goals,h.league_away_goals,h.league_home_xg,h.league_away_xg,
         h.league_matches,h.league_home_xg_n,h.league_away_xg_n,
         o.close_home_avg,o.close_draw_avg,o.close_away_avg,o.close_home_max,o.close_draw_max,o.close_away_max
  from betting_team_features_v2_cache h
  join betting_team_features_v2_cache a on a.match_id=h.match_id and a.was_home=false
  join historical_market_odds o on o.match_id=h.match_id and o.season='2025/26' and o.source='football-data.co.uk'
  where h.was_home=true and h.season='2025/26'
), rates as (
 select *,
   least(0.65,0.65*coalesce(league_home_xg_n::numeric/nullif(league_matches,0),0)) lhxw,
   least(0.65,0.65*coalesce(league_away_xg_n::numeric/nullif(league_matches,0),0)) laxw,
   case when hn>0 then least(0.65,0.65*coalesce(hnxg::numeric/nullif(hn,0),0)) else 0 end hxw,
   case when an>0 then least(0.65,0.65*coalesce(anxg::numeric/nullif(an,0),0)) else 0 end axw
 from paired
), blended as (
 select *,
   (1-lhxw)*league_home_goals + lhxw*coalesce(league_home_xg,league_home_goals) lhome,
   (1-laxw)*league_away_goals + laxw*coalesce(league_away_xg,league_away_goals) laway,
   case when hn>0 then (1-hxw)*hgf + hxw*coalesce(hxgf,hgf) end hatt_raw,
   case when hn>0 then (1-hxw)*hga + hxw*coalesce(hxga,hga) end hdef_raw,
   case when an>0 then (1-axw)*agf + axw*coalesce(axgf,agf) end aatt_raw,
   case when an>0 then (1-axw)*aga + axw*coalesce(axga,aga) end adef_raw
 from rates
), lamb as (
 select *,
   greatest(0.15,least(4.5,lhome * power(
      (((coalesce(hatt_raw,(lhome+laway)/2)*hn + ((lhome+laway)/2)*4)/(hn+4))/((lhome+laway)/2)) *
      (((coalesce(adef_raw,(lhome+laway)/2)*an + ((lhome+laway)/2)*4)/(an+4))/((lhome+laway)/2)),0.75))) hl,
   greatest(0.15,least(4.5,laway * power(
      (((coalesce(aatt_raw,(lhome+laway)/2)*an + ((lhome+laway)/2)*4)/(an+4))/((lhome+laway)/2)) *
      (((coalesce(hdef_raw,(lhome+laway)/2)*hn + ((lhome+laway)/2)*4)/(hn+4))/((lhome+laway)/2)),0.75))) al
 from blended
), cells as (
 select l.*,gs.h,gs.a,
   exp(-hl)*power(hl,gs.h)/factorial(gs.h)::numeric * exp(-al)*power(al,gs.a)/factorial(gs.a)::numeric p
 from lamb l
 cross join lateral (select h,a from generate_series(0,8) h cross join generate_series(0,8) a) gs
), model as (
 select season,gameweek,match_id,kickoff_time,home_team,away_team,hg,ag,
        close_home_avg,close_draw_avg,close_away_avg,close_home_max,close_draw_max,close_away_max,
        sum(p) filter(where h>a)/sum(p) ph,
        sum(p) filter(where h=a)/sum(p) pd,
        sum(p) filter(where h<a)/sum(p) pa
 from cells
 group by season,gameweek,match_id,kickoff_time,home_team,away_team,hg,ag,
          close_home_avg,close_draw_avg,close_away_avg,close_home_max,close_draw_max,close_away_max
), scored as (
 select *,
   (1/close_home_avg)/((1/close_home_avg)+(1/close_draw_avg)+(1/close_away_avg)) mh,
   (1/close_draw_avg)/((1/close_home_avg)+(1/close_draw_avg)+(1/close_away_avg)) md,
   (1/close_away_avg)/((1/close_home_avg)+(1/close_draw_avg)+(1/close_away_avg)) ma
 from model
)
select * from scored order by kickoff_time,match_id;
