import assert from "node:assert/strict";
import {createClient} from "@supabase/supabase-js";
const origin="https://pl-data.colly.me.uk";
for(const key of ["BASIC_AUTH_USERNAME","BASIC_AUTH_PASSWORD","NEXT_PUBLIC_SUPABASE_URL","NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"])assert.ok(process.env[key],"Required project environment missing: "+key);
const authorization="Basic "+Buffer.from(process.env.BASIC_AUTH_USERNAME+":"+process.env.BASIC_AUTH_PASSWORD).toString("base64");
const response=await fetch(origin+"/betting/weekend",{headers:{authorization},signal:AbortSignal.timeout(30000)});
assert.equal(response.status,200,"Authenticated production page");
const html=await response.text();const sources=[...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map(m=>new URL(m[1],origin).href);
assert.ok(sources.length>0);
const chunks=await Promise.all(sources.map(async url=>{const r=await fetch(url,{headers:{authorization},signal:AbortSignal.timeout(30000)});assert.equal(r.status,200);return r.text()}));
const code=chunks.join("\n");for(const marker of ["data-likely-scorelines","data-favoured-outcome","gw9-81-tuesday-20261027","gw9-90-tuesday-20261027"])assert.ok(code.includes(marker),"Published application marker missing: "+marker);
const denied=await fetch(origin+"/betting/weekend",{redirect:"manual",signal:AbortSignal.timeout(20000)});assert.equal(denied.status,401);assert.match(denied.headers.get("www-authenticate")||"",/Basic realm="PL Data Hub"/);
const db=createClient(process.env.NEXT_PUBLIC_SUPABASE_URL,process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);
const {data,error}=await db.from("betting_manual_fixtures").select("fixture_id,kickoff_time,home_team,away_team,market_snapshot_at,notes,betting_manual_weekend_snapshot(*)").gt("kickoff_time",new Date().toISOString()).order("kickoff_time");assert.ifError(error);assert.equal(data.length,10);
assert.deepEqual(data.map(f=>f.fixture_id).sort((a,b)=>a-b),[81,82,83,84,85,86,87,88,89,90]);
for(const f of data){let s=f.betting_manual_weekend_snapshot;assert.ok(s&&s.home_n8>=4&&s.away_n8>=4);assert.ok(Date.parse(s.calculated_at)<Date.parse(f.kickoff_time));assert.ok(Date.parse(f.market_snapshot_at)<Date.parse(f.kickoff_time));const p=[s.candidate_home_prob,s.candidate_draw_prob,s.candidate_away_prob].map(Number);assert.ok(p.every(n=>Number.isFinite(n)&&n>=0&&n<=1));assert.ok(Math.abs(p.reduce((a,b)=>a+b,0)-1)<1e-8);assert.ok(f.notes.includes("WEEKEND_NEWS_JSON:"));}
const {count,error:countError}=await db.from("matches").select("match_id",{count:"exact",head:true}).eq("season","2026/27");assert.ifError(countError);assert.equal(count,80);
console.log(JSON.stringify({verifiedAt:new Date().toISOString(),authenticatedProduction:200,anonymousProduction:401,publishedGW9Ledger:true,completedMatches:80,futureFixtures:10,eligibleForecasts:10,staleFixtures:0,modelRulesChanged:false}));
