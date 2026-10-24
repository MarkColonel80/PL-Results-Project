// Run only in this project's trusted Vercel production build environment.
// Uses existing application credentials in memory; never prints or persists them.
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createClient} from "@supabase/supabase-js";
import {likelyScorelines,favouredOutcome} from "../lib/weekend-score.ts";
const origin="https://pl-data.colly.me.uk";
const username=process.env.BASIC_AUTH_USERNAME;
const password=process.env.BASIC_AUTH_PASSWORD;
assert.ok(username&&password,"Application authentication must be configured in the cloud runner");
const headers={Authorization:"Basic "+Buffer.from(username+":"+password).toString("base64")};
const response=await fetch(origin+"/betting/weekend",{headers,redirect:"manual",signal:AbortSignal.timeout(20000)});
assert.equal(response.status,200,"Authenticated live weekend page must return 200");
const html=await response.text();
const scripts=[...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map(m=>m[1]).filter(path=>path.startsWith("/_next/static/"));
assert.ok(scripts.length>0,"Live page must include application assets");
const assets=await Promise.all(scripts.map(async path=>{
 const response=await fetch(origin+path,{redirect:"manual",signal:AbortSignal.timeout(20000)});
 assert.equal(response.status,200,"Live application asset must load");
 return response.text();
}));
const code=assets.join("\n");
for(const marker of ["data-favoured-outcome","data-likely-scorelines","How to read the outcome and scorelines","Three likeliest scorelines","No prediction — LIMITED_HISTORY","not rounded expected goals"])assert.ok(code.includes(marker),"Live application is missing score display marker");
const denied=await fetch(origin+"/betting/weekend",{redirect:"manual",signal:AbortSignal.timeout(20000)});
assert.equal(denied.status,401,"Anonymous access must remain protected");
assert.match(denied.headers.get("www-authenticate")||"",/Basic realm="PL Data Hub"/);
const supabase=createClient(process.env.NEXT_PUBLIC_SUPABASE_URL,process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);
const now=Date.now();
const {data,error}=await supabase.from("betting_manual_fixtures").select("fixture_id,kickoff_time,home_team,away_team,betting_manual_weekend_snapshot(*)").gt("kickoff_time",new Date(now).toISOString()).order("kickoff_time");
assert.ifError(error);
assert.ok(data.length>0,"Expected future fixtures during this publication");
const frozen=JSON.parse(readFileSync(new URL("../data/weekend-2026-10-23-snapshots.json",import.meta.url),"utf8")).fixtures;
const results=data.map(f=>{
 const s=f.betting_manual_weekend_snapshot;
 const saved=frozen.find(x=>x.fixture_id===f.fixture_id)?.snapshot;
 if(saved)for(const key of ["candidate_home_lambda","candidate_away_lambda","candidate_home_prob","candidate_draw_prob","candidate_away_prob"]){
  assert.equal(s[key]===null?null:Number(s[key]),saved[key]===null?null:Number(saved[key]),"Frozen candidate must be preserved");
 }
 const scores=likelyScorelines(f.kickoff_time,s,now);
 const favourite=favouredOutcome(f.kickoff_time,s,now);
 const eligible=s&&s.home_n8>=4&&s.away_n8>=4;
 assert.equal(Boolean(scores),Boolean(eligible),"All eligible future frozen forecasts must have scorelines");
 assert.equal(Boolean(favourite),Boolean(eligible),"All eligible future frozen forecasts must have a favoured outcome");
 if(scores)assert.equal(scores.length,3);
 return {fixtureId:f.fixture_id,fixture:f.home_team+" v "+f.away_team,favourite,scores:scores?.map(score=>({score:score.home+"–"+score.away,probability:score.probability}))??null};
});
console.log(JSON.stringify({verification:"Authenticated live page, deployed score assets, anonymous 401, real anonymous data reads and frozen candidate equality passed",checkedAt:new Date(now).toISOString(),futureFixtures:data.length,predictions:results.filter(r=>r.scores).length,results}));
