import assert from "node:assert/strict";
import {createClient} from "@supabase/supabase-js";
assert.match(process.env.VERCEL_GIT_COMMIT_SHA||"",/^[a-f0-9]{40}$/);
for(const k of ["BASIC_AUTH_USERNAME","BASIC_AUTH_PASSWORD","NEXT_PUBLIC_SUPABASE_URL","NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"])assert.ok(process.env[k],"Missing configured verification environment");
const origin="https://pl-data.colly.me.uk";
const authorization="Basic "+Buffer.from(process.env.BASIC_AUTH_USERNAME+":"+process.env.BASIC_AUTH_PASSWORD).toString("base64");
const yes=await fetch(origin+"/betting/weekend",{headers:{authorization},signal:AbortSignal.timeout(20000)});
assert.equal(yes.status,200);const html=await yes.text();
const assets=[...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map(m=>new URL(m[1],origin));
assert.ok(assets.length>0);let code="";
for(const u of assets){assert.equal(u.origin,origin);const r=await fetch(u,{headers:{authorization},signal:AbortSignal.timeout(20000)});assert.equal(r.status,200);code+=await r.text();}
for(const x of ["data-favoured-outcome","data-likely-scorelines","gw11-101-tuesday-20261110","gw11-110-tuesday-20261110"])assert.ok(code.includes(x),"Missing published marker: "+x);
const no=await fetch(origin+"/betting/weekend",{redirect:"manual",signal:AbortSignal.timeout(20000)});assert.equal(no.status,401);assert.match(no.headers.get("www-authenticate")||"",/Basic realm="PL Data Hub"/);
const db=createClient(process.env.NEXT_PUBLIC_SUPABASE_URL,process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY);
const {data,error}=await db.from("betting_manual_fixtures").select("fixture_id,kickoff_time,market_home_odds,market_draw_odds,market_away_odds,market_snapshot_at,notes,betting_manual_weekend_snapshot(*)").gt("kickoff_time",new Date().toISOString()).order("kickoff_time");assert.ifError(error);assert.equal(data.length,10);
assert.deepEqual(data.map(f=>f.fixture_id).sort((a,b)=>a-b),[101,102,103,104,105,106,107,108,109,110]);
for(const f of data){const s=f.betting_manual_weekend_snapshot;assert.ok(s.home_n8>=4&&s.away_n8>=4);assert.equal(s.candidate_model_version,"v3_24_venue8_50_noppg");assert.ok(Date.parse(s.candidate_calculated_at)<Date.parse(f.kickoff_time));assert.ok(f.notes.includes("WEEKEND_NEWS_JSON:"));assert.equal(f.market_home_odds,null);assert.equal(f.market_draw_odds,null);assert.equal(f.market_away_odds,null);assert.equal(f.market_snapshot_at,null);}
const {count,error:err}=await db.from("matches").select("match_id",{count:"exact",head:true}).eq("season","2026/27");assert.ifError(err);assert.equal(count,100);
console.log("FINAL_PL_PRODUCTION_VERIFICATION "+JSON.stringify({checkedAt:new Date().toISOString(),commit:process.env.VERCEL_GIT_COMMIT_SHA,authenticated:200,anonymous:401,gw11Fixtures:10,publishedLedger:true,completedMatches:100,unavailablePricesNull:true}));
