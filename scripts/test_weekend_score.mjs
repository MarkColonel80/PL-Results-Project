import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {predictedScore,likelyScorelines,favouredOutcome} from "../lib/weekend-score.ts";

const now=Date.parse("2026-10-24T12:00:00Z");
const kickoff="2026-10-24T14:00:00Z";
const snapshot={home_n8:8,away_n8:8,candidate_home_lambda:1.87,candidate_away_lambda:0.66,candidate_calculated_at:"2026-10-20T15:42:23Z"};
const score=predictedScore(kickoff,snapshot,now);
assert.equal(score.home,1);
assert.equal(score.away,0);
assert.notDeepEqual([score.home,score.away],[Math.round(1.87),Math.round(0.66)]);
assert.ok(Math.abs(score.probability-Math.exp(-2.53)*1.87)<1e-14);
assert.equal(score.tied,false);

// Independently enumerate every relevant score and compare the full joint PMF.
function pmf(lambda,k){let factorial=1;for(let i=2;i<=k;i++)factorial*=i;return Math.exp(-lambda)*lambda**k/factorial;}
for(const h of [0.15,0.999999,1,1.000001,1.87,1.999999,2,2.000001,3,4,4.5]){
 for(const a of [0.15,0.66,1,1.3,2,4.5]){
  const got=predictedScore(kickoff,{...snapshot,candidate_home_lambda:h,candidate_away_lambda:a},now);
  for(let i=0;i<=20;i++)for(let j=0;j<=20;j++)assert.ok(got.probability+1e-14>=pmf(h,i)*pmf(a,j));
  assert.equal(got.tied,Number.isInteger(h)||Number.isInteger(a));
 }
}
const tied=predictedScore(kickoff,{...snapshot,candidate_home_lambda:2,candidate_away_lambda:1},now);
assert.deepEqual([tied.home,tied.away,tied.tied],[1,0,true]);
assert.ok(Math.abs(tied.probability-2*Math.exp(-3))<1e-14);
assert.deepEqual(predictedScore(kickoff,{...snapshot,candidate_home_lambda:"1.865978050087949373",candidate_away_lambda:"0.663488439834149983"},now)?.home,1);
for(const key of ["home_n8","away_n8"])for(const value of [null,0,1,2,3,NaN,Infinity])assert.equal(predictedScore(kickoff,{...snapshot,[key]:value},now),null);
assert.ok(predictedScore(kickoff,{...snapshot,home_n8:4,away_n8:7},now));
for(const key of ["candidate_home_lambda","candidate_away_lambda"])for(const value of [null,undefined,""," ","bad",NaN,Infinity,-1,0,0.149,4.501])assert.equal(predictedScore(kickoff,{...snapshot,[key]:value},now),null);
for(const value of [null,"bad",kickoff,"2026-10-24T13:00:00Z"])assert.equal(predictedScore(kickoff,{...snapshot,candidate_calculated_at:value},now),null);
assert.equal(predictedScore(kickoff,null,now),null);
assert.equal(predictedScore("bad",snapshot,now),null);
assert.equal(predictedScore(kickoff,snapshot,NaN),null);
assert.ok(predictedScore(kickoff,snapshot,Date.parse(kickoff)-1));
assert.equal(predictedScore(kickoff,snapshot,Date.parse(kickoff)),null);
assert.equal(predictedScore(kickoff,snapshot,Date.parse(kickoff)+1),null);

// Frozen real-round regression: two started, two future LIMITED_HISTORY, six scores.
const fixtures=JSON.parse(readFileSync(new URL("../data/weekend-2026-10-23-snapshots.json",import.meta.url),"utf8")).fixtures;
const before=JSON.stringify(fixtures);
const actual=fixtures.map(f=>({id:f.fixture_id,score:predictedScore(f.kickoff_time,f.snapshot,now)}));
assert.deepEqual(actual.filter(f=>f.score).map(f=>f.id).sort((a,b)=>a-b),[73,75,76,78,79,80]);
for(const f of actual.filter(f=>[71,72,74,77].includes(f.id)))assert.equal(f.score,null);
assert.equal(JSON.stringify(fixtures),before,"Derivation must not mutate frozen data");
console.log("Exact-score tests passed: independent PMF grid, ties, full precision, missing/invalid inputs, history gates, kickoff boundary, frozen GW8 and immutability.");

const candidate={...snapshot,candidate_home_prob:0.6,candidate_draw_prob:0.25,candidate_away_prob:0.15};
assert.deepEqual(favouredOutcome(kickoff,candidate,now),{outcomes:["home"],probability:0.6});
assert.deepEqual(favouredOutcome(kickoff,{...candidate,candidate_home_prob:0.4,candidate_draw_prob:0.4,candidate_away_prob:0.2},now),{outcomes:["home","draw"],probability:0.4});
assert.equal(favouredOutcome(kickoff,{...candidate,candidate_home_prob:null},now),null);
assert.equal(favouredOutcome(kickoff,{...candidate,candidate_draw_prob:0.5},now),null);
assert.equal(favouredOutcome(kickoff,{...candidate,candidate_draw_prob:""},now),null);
assert.deepEqual(likelyScorelines(kickoff,{...candidate,candidate_home_lambda:1,candidate_away_lambda:1},now).map(s=>[s.home,s.away,s.tied]),[[0,0,true],[0,1,true],[1,0,true]]);
assert.deepEqual(likelyScorelines(kickoff,{...candidate,candidate_home_lambda:4.5,candidate_away_lambda:4.5},now).map(s=>[s.home,s.away]),[[4,4],[4,5],[5,4]]);
for(const h of [0.15,0.999999,1,1.000001,1.87,1.999999,2,2.000001,3,4,4.5]){
 for(const a of [0.15,0.66,1,1.3,2,4.5]){
  const list=likelyScorelines(kickoff,{...candidate,candidate_home_lambda:h,candidate_away_lambda:a},now);
  assert.equal(list.length,3);
  assert.equal(new Set(list.map(s=>s.home+"-"+s.away)).size,3);
  for(const s of list)assert.ok(Math.abs(s.probability-pmf(h,s.home)*pmf(a,s.away))<1e-14);
  assert.ok(list[0].probability+1e-14>=list[1].probability&&list[1].probability+1e-14>=list[2].probability);
  // Every omitted score must be no more likely than the third selected score.
  for(let i=0;i<=30;i++)for(let j=0;j<=30;j++){
   if(!list.some(s=>s.home===i&&s.away===j))assert.ok(pmf(h,i)*pmf(a,j)<=list[2].probability+1e-14);
  }
 }
}
for(const fn of [likelyScorelines,favouredOutcome]){
 assert.ok(fn(kickoff,candidate,Date.parse(kickoff)-1));
 for(const time of [NaN,Date.parse(kickoff),Date.parse(kickoff)+1])assert.equal(fn(kickoff,candidate,time),null);
 for(const key of ["home_n8","away_n8"])assert.equal(fn(kickoff,{...candidate,[key]:3},now),null);
 assert.equal(fn(kickoff,{...candidate,candidate_calculated_at:kickoff},now),null);
 assert.equal(fn(kickoff,{...candidate,candidate_home_lambda:null},now),null);
}
const chelsea=fixtures.find(f=>f.fixture_id===75);
const chelseaScores=likelyScorelines(chelsea.kickoff_time,chelsea.snapshot,now);
assert.deepEqual(chelseaScores.map(s=>s.home+"–"+s.away),["1–1","1–0","2–1"]);
assert.deepEqual(chelseaScores.map(s=>(100*s.probability).toFixed(1)),["11.7","10.9","9.6"]);
const favourite=favouredOutcome(chelsea.kickoff_time,chelsea.snapshot,now);
assert.deepEqual(favourite.outcomes,["home"]);
assert.equal(favourite.probability,chelsea.snapshot.candidate_home_prob);
assert.equal((100*favourite.probability).toFixed(1),"50.6");
assert.ok(chelseaScores.reduce((total,s)=>total+s.probability,0)<0.33,"Score probabilities must not be rescaled to 100%");
for(const f of fixtures){
 const list=likelyScorelines(f.kickoff_time,f.snapshot,now);
 const outcome=favouredOutcome(f.kickoff_time,f.snapshot,now);
 if([73,75,76,78,79,80].includes(f.fixture_id)){assert.equal(list.length,3);assert.ok(outcome);}
 else {assert.equal(list,null);assert.equal(outcome,null);}
}
assert.equal(JSON.stringify(fixtures),before,"All display derivations must preserve frozen snapshots");
console.log("Top-three and favoured-outcome tests passed: global ranking, ties, original probabilities, valid pre-match inputs, Chelsea draw/win distinction and immutable frozen fixtures.");
