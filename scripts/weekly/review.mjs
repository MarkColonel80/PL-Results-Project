import assert from "node:assert/strict";
import {paperDecision,paperScorecard,ledgerPrefixUnchanged,xgOnlyDiagnostic} from "../../lib/weekend-paper.ts";
import {likelyScorelines,favouredOutcome} from "../../lib/weekend-score.ts";
export function current(s){
 if(!s||s.home_n8<4||s.away_n8<4)return null;
 const vals=[["home_vxgf8","home_vgf8_capped","home_vgf8"],["home_vxga8","home_vga8_capped","home_vga8"],["away_vxgf8","away_vgf8_capped","away_vgf8"],["away_vxga8","away_vga8_capped","away_vga8"]].map(([x,c,g])=>s[x]==null||(s[c]??s[g])==null?null:(Number(s[x])+Number(s[c]??s[g]))/2);
 if(vals.some(x=>x==null))return null;
 const [hf,ha,af,aa]=vals,clamp=x=>Math.max(.15,Math.min(4.5,x));
 const h=clamp(Number(s.league_home_goals)*((hf/Number(s.league_home_xg))*(aa/Number(s.league_home_xg)))**.8),a=clamp(Number(s.league_away_goals)*((af/Number(s.league_away_xg))*(ha/Number(s.league_away_xg)))**.8);
 const hp=[Math.exp(-h)],ap=[Math.exp(-a)];for(let i=1;i<=8;i++){hp.push(hp[i-1]*h/i);ap.push(ap[i-1]*a/i);}
 let ph=0,pd=0,pa=0;for(let i=0;i<=8;i++)for(let j=0;j<=8;j++){const p=hp[i]*ap[j];if(i>j)ph+=p;else if(i===j)pd+=p;else pa+=p;}
 const t=ph+pd+pa;return {h:ph/t,d:pd/t,a:pa/t};
}
const metrics=rows=>{if(!rows.length)return {n:0,brier:null,log_loss:null,accuracy:null};return {n:rows.length,brier:rows.reduce((n,r)=>n+["h","d","a"].reduce((x,k)=>x+(r.p[k]-(r.y===k?1:0))**2,0),0)/rows.length,log_loss:rows.reduce((n,r)=>n-Math.log(Math.max(1e-15,r.p[r.y])),0)/rows.length,accuracy:rows.filter(r=>["h","d","a"].reduce((a,b)=>r.p[a]>=r.p[b]?a:b)===r.y).length/rows.length};};
export function review(state,completed,ledger,at){
 const next=structuredClone(ledger);const rows=[];const results=[...state.matches,...completed];const seen=new Set();
 for(const f of state.fixtures){
  const m=results.find(m=>m.home_team===f.home_team&&m.away_team===f.away_team&&Date.parse(m.kickoff_time)===Date.parse(f.kickoff_time)&&m.home_score!=null&&m.away_score!=null);if(!m||seen.has(f.fixture_id))continue;seen.add(f.fixture_id);
  const s=f.snapshot;const eligible=!!s&&s.home_n8>=4&&s.away_n8>=4&&Date.parse(s.candidate_calculated_at)<Date.parse(f.kickoff_time);
  const y=m.home_score>m.away_score?"h":m.home_score===m.away_score?"d":"a";const odds=[f.market_home_odds,f.market_draw_odds,f.market_away_odds].map(Number),sum=odds.reduce((s,x)=>s+1/x,0);
  rows.push({fixture_id:f.fixture_id,gameweek:m.gameweek,home_team:f.home_team,away_team:f.away_team,score:[m.home_score,m.away_score],eligible,y,research:eligible?{h:Number(s.candidate_home_prob),d:Number(s.candidate_draw_prob),a:Number(s.candidate_away_prob)}:null,current:eligible?current(s):null,market:eligible&&odds.every(x=>x>1)&&Date.parse(f.market_snapshot_at)<Date.parse(f.kickoff_time)?{h:1/odds[0]/sum,d:1/odds[1]/sum,a:1/odds[2]/sum}:null});
  const lf=ledger.fixtures.find(x=>x.fixture_id===f.fixture_id);if(!lf)continue;
  const decision=paperDecision(ledger.events,lf,Date.parse(at));if(decision.status!=="paper"||!decision.event||ledger.settlements.some(x=>x.decision_id===decision.event.id))continue;
  assert.ok(Date.parse(at)>Date.parse(lf.kickoff_time));
  next.settlements.push({decision_id:decision.event.id,recorded_at:at,completed_at:at,finished:true,home_score:m.home_score,away_score:m.away_score,source_url:"https://fantasy.premierleague.com/api/fixtures/"});
 }
 const score=list=>Object.fromEntries(["research","current","market"].map(k=>[k,metrics(list.filter(x=>x[k]).map(x=>({p:x[k],y:x.y})))]));
 assert.ok(ledgerPrefixUnchanged(ledger,next));
 const gw=Math.max(...completed.map(x=>x.gameweek));
 return {ledger:next,rows,round:score(rows.filter(x=>x.gameweek===gw)),all:score(rows),paper:paperScorecard(next,Date.parse(at)),gameweek:gw};
}
export function futureArchive(fixtures,prepared,ledger,key){
 const after=structuredClone(ledger),at=new Date().toISOString();
 const rows=fixtures.filter(f=>prepared.upcoming.some(u=>u.home_team===f.home_team&&u.away_team===f.away_team&&Date.parse(u.kickoff_time)===Date.parse(f.kickoff_time))).map(f=>{
  assert.ok(Date.parse(f.kickoff_time)>Date.now());assert.ok(f.snapshot,"Missing refreshed snapshot");
  if(!after.fixtures.some(x=>x.fixture_id===f.fixture_id))after.fixtures.push({fixture_id:f.fixture_id,kickoff_time:f.kickoff_time,home_team:f.home_team,away_team:f.away_team});
  if(!after.events.some(x=>x.fixture_id===f.fixture_id))after.events.push({id:"gw"+prepared.next_gameweek+"-"+f.fixture_id+"-tuesday-"+key.replaceAll("-",""),fixture_id:f.fixture_id,kickoff_time:f.kickoff_time,recorded_at:at,status:"watch",reason:"Provisional source review only. Confirmed starting teams, available bookmaker quote, club news and sensitivity review remain pending. No selection or paper stake."});
  return {...f,current:current(f.snapshot),diagnostics:{venue8:xgOnlyDiagnostic(f.snapshot,8),venue18:xgOnlyDiagnostic(f.snapshot,18)},scores:likelyScorelines(f.kickoff_time,f.snapshot,Date.parse(at)),favourite:favouredOutcome(f.kickoff_time,f.snapshot,Date.parse(at))};
 });
 assert.equal(rows.length,prepared.upcoming.length);assert.ok(ledgerPrefixUnchanged(ledger,after));
 return {ledger:after,archive:{checked_at:at,season:"2026/27",gameweek:prepared.next_gameweek,fixtures:rows,coverage_gaps:prepared.coverage_gaps}};
}
