import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {parseWeekendNews} from "../lib/weekend-review.ts";
import {likelyScorelines,favouredOutcome} from "../lib/weekend-score.ts";
import {paperEventIssues,paperScorecard} from "../lib/weekend-paper.ts";
const path=process.argv[2];assert.ok(path,"Pass a dated snapshots JSON archive");
const a=JSON.parse(readFileSync(path,"utf8"));
const l=JSON.parse(readFileSync("data/weekend-paper-ledger.json","utf8"));
assert.ok(a.fixtures.length>0);assert.equal(new Set(a.fixtures.map(f=>f.fixture_id)).size,a.fixtures.length);
for(const f of a.fixtures){
 const s=f.snapshot;const at=Date.parse(a.checked_at);
 assert.ok(Date.parse(f.kickoff_time)>at);assert.ok(Date.parse(s.calculated_at)<=at);assert.ok(Date.parse(s.candidate_calculated_at)<=at);
 assert.ok(s.home_n8>=4&&s.away_n8>=4);
 assert.equal(s.candidate_model_version,"v3_24_venue8_50_noppg");
 const p=[s.candidate_home_prob,s.candidate_draw_prob,s.candidate_away_prob].map(Number);
 assert.ok(p.every(x=>Number.isFinite(x)&&x>=0&&x<=1));assert.ok(Math.abs(p.reduce((x,y)=>x+y)-1)<1e-8);
 assert.ok([f.market_home_odds,f.market_draw_odds,f.market_away_odds].every(x=>Number.isFinite(x)&&x>1));
 assert.ok(Date.parse(f.market_snapshot_at)<=at);
 assert.ok(parseWeekendNews(f.notes));const scores=likelyScorelines(f.kickoff_time,s,at);assert.ok(scores);
 assert.deepEqual(scores.map(({probability,...x})=>x),f.scores.map(({probability,...x})=>x));
 // Permit machine-precision Math.exp differences between JavaScript runtimes.
 scores.forEach((x,i)=>assert.ok(Math.abs(x.probability-f.scores[i].probability)<1e-14));
 assert.deepEqual(favouredOutcome(f.kickoff_time,s,at),f.favourite);
 const events=l.events.filter(e=>e.fixture_id===f.fixture_id);assert.ok(events.length);
 for(const e of events)assert.deepEqual(paperEventIssues(e,f),[]);
}
console.log(JSON.stringify({datedArchive:path,fixtures:a.fixtures.length,newsAndForecastContracts:"passed",paper:paperScorecard(l)}));
