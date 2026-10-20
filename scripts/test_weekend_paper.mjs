import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {paperDecision,paperEventIssues,paperScorecard,ledgerPrefixUnchanged,xgOnlyDiagnostic,fragileOutcomes,venueHistoryBreakdown} from "../lib/weekend-paper.ts";

const fixture={fixture_id:73,kickoff_time:"2026-10-24T14:00:00Z",home_team:"Arsenal",away_team:"Everton"};
const now=Date.parse("2026-10-25T18:00:00Z");
const evidence={checked_at:"2026-10-24T13:05:00Z",summary:"Reviewed before kick-off",source_url:"https://www.arsenal.com/"};
const selected={id:"test-paper",fixture_id:73,kickoff_time:fixture.kickoff_time,recorded_at:"2026-10-24T13:10:00Z",status:"paper",reason:"Paper test with the final teams and an available quote",
 selection:{outcome:"h",stake_units:1,quote:{bookmaker:"Test bookmaker",odds:2.5,observed_at:"2026-10-24T13:08:00Z",source_url:"https://bookmaker.example/fixture",available:true},forecast:{model_version:"v3_24_venue8_50_noppg",current_model_version:"weekend_ppg8_xg8_cap1_min4",calculated_at:"2026-10-23T10:00:00Z",home_n8:8,away_n8:8,research:{h:.5,d:.25,a:.25},current:{h:.52,d:.24,a:.24}}},
 checks:{teams:{...evidence,confirmed:true},news:evidence,schedule:evidence,sensitivity:evidence}};
assert.deepEqual(paperEventIssues(selected,fixture,now),[]);
assert.equal(paperDecision([selected],fixture,now).status,"paper");
const watch={id:"watch",fixture_id:73,kickoff_time:fixture.kickoff_time,recorded_at:"2026-10-23T12:00:00Z",status:"watch",reason:"Waiting for teams"};
assert.equal(paperDecision([watch],fixture,now).status,"watch");
assert.equal(paperDecision([],fixture,now).status,"watch");
for(const change of [
 e=>e.checks.teams.confirmed=false,e=>delete e.checks.teams,e=>delete e.checks.schedule,
 e=>delete e.checks.sensitivity,e=>e.selection.quote.available=false,e=>e.selection.quote.bookmaker="",
 e=>e.selection.quote.source_url="javascript:alert(1)",e=>e.selection.quote.source_url="https://user:password@example.com",
 e=>e.selection.quote.observed_at="2026-10-24T13:11:00Z",e=>e.selection.forecast.calculated_at="2026-10-24T13:11:00Z",
 e=>e.recorded_at=fixture.kickoff_time,e=>e.recorded_at="2026-10-24T14:01:00Z",
 e=>e.selection.forecast.home_n8=3,e=>e.selection.forecast.research.h=.2,
 e=>e.selection.stake_units=5,e=>e.selection.quote.odds=1,e=>e.selection.forecast.current_model_version="",
 e=>e.selection.forecast.research={h:.3,d:.3,a:.4},
]){const bad=structuredClone(selected);change(bad);assert.ok(paperEventIssues(bad,fixture,now).length);assert.notEqual(paperDecision([watch,bad],fixture,now).status,"paper");}
assert.notEqual(paperDecision([selected],{...fixture,kickoff_time:"2026-10-24T15:00:00Z"},now).status,"paper");
assert.equal(paperDecision([selected],fixture,Date.parse("2026-10-24T12:00:00Z")).status,"watch");
const pass={...watch,id:"later-pass",status:"pass",recorded_at:"2026-10-24T13:15:00Z",reason:"Later change"};
assert.equal(paperDecision([watch,selected,pass],fixture,now).event.id,selected.id,"A pass cannot erase a valid selection");
const later={...selected,id:"later-paper",recorded_at:"2026-10-24T13:20:00Z"};
assert.equal(paperDecision([later,selected],fixture,now).event.id,selected.id,"The first valid selection stays frozen");
const ledger={version:1,mode:"paper",unit_stake:1,fixtures:[fixture],events:[watch,selected,pass],settlements:[]};
assert.deepEqual(paperScorecard(ledger,now),{selections:1,settled:0,pending:1,wins:0,staked:1,settledStake:0,profit:0,roi:null});
const result={decision_id:selected.id,finished:true,completed_at:"2026-10-24T16:00:00Z",recorded_at:"2026-10-24T17:00:00Z",home_score:2,away_score:1,source_url:"https://www.premierleague.com/en/matches"};
assert.equal(paperScorecard({...ledger,settlements:[result]},now).profit,1.5);
assert.equal(paperScorecard({...ledger,settlements:[{...result,home_score:0,away_score:1}]},now).profit,-1);
assert.equal(paperScorecard({...ledger,settlements:[result,result]},now).settled,1);
assert.equal(paperScorecard({...ledger,settlements:[{...result,finished:false}]},now).settled,0);
assert.equal(paperScorecard({...ledger,events:[watch,pass],settlements:[result]},now).selections,0);
assert.equal(ledgerPrefixUnchanged(ledger,{...ledger,events:[...ledger.events,later]}),true);
assert.equal(ledgerPrefixUnchanged(ledger,{...ledger,events:[watch,pass]}),false);
assert.equal(ledgerPrefixUnchanged(ledger,{...ledger,events:[watch,{...selected,reason:"Rewritten"},pass]}),false);
const snapshot={home_n8:8,away_n8:8,home_vn18:18,away_vn18:18,home_vxgf8:1.5,home_vxga8:1.1,away_vxgf8:1.2,away_vxga8:1.3,home_vxgf18:1.4,home_vxga18:1.2,away_vxgf18:1.3,away_vxga18:1.4,league_home_goals:1.5,league_away_goals:1.2,league_home_xg:1.5,league_away_xg:1.2};
for(const window of [8,18]){const p=xgOnlyDiagnostic(snapshot,window);assert.ok(p);assert.ok(Math.abs(p.h+p.d+p.a-1)<1e-12);}
assert.equal(xgOnlyDiagnostic({...snapshot,away_vn18:17},18),null);
assert.equal(xgOnlyDiagnostic({...snapshot,home_n8:3},8),null);
assert.equal(xgOnlyDiagnostic({...snapshot,home_vxga8:null},8),null);
assert.equal(xgOnlyDiagnostic({...snapshot,league_home_xg:0},8),null);
assert.deepEqual(fragileOutcomes({h:.5,d:.25,a:.25},[{label:"longer sample",probabilities:{h:.39,d:.31,a:.3}}],{h:2.5,d:3,a:3}),["Home gap disappears in longer sample"]);
const matches=[{home_team:"Arsenal",away_team:"Everton",kickoff_time:"2026-10-10T12:00:00Z"},{home_team:"Arsenal",away_team:"Chelsea",kickoff_time:"2026-10-23T12:00:00Z"}];
assert.deepEqual(venueHistoryBreakdown(matches,"Arsenal",true,8,fixture.kickoff_time,"2026-10-20T12:00:00Z"),{total:8,current:1,previous:7});
assert.equal(venueHistoryBreakdown(null,"Arsenal",true,8,fixture.kickoff_time,"2026-10-20T12:00:00Z"),null);
const live=JSON.parse(readFileSync(new URL("../data/weekend-paper-ledger.json",import.meta.url)));
assert.equal(live.mode,"paper");assert.equal(live.unit_stake,1);assert.equal(live.fixtures.length,10);
assert.equal(new Set(live.events.map(e=>e.id)).size,live.events.length);
for(const f of live.fixtures)assert.equal(paperDecision(live.events,f).status,"watch");
assert.equal(paperScorecard(live).selections,0,"No synthetic or retrospectively created paper stakes");
console.log("Paper review: pre-match gates, frozen selections, honest settlement, history cutoffs and diagnostic limits passed.");
