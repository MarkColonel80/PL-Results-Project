import assert from "node:assert/strict";
import fs from "node:fs";
import {pathToFileURL} from "node:url";
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE_PATH?pathToFileURL(process.env.PLAYWRIGHT_MODULE_PATH).href:"playwright");
const frozen=JSON.parse(fs.readFileSync(new URL("../data/weekend-2026-10-31-snapshots.json",import.meta.url),"utf8"));
const browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
try{
 const options={viewport:{width:1280,height:900}};if(process.env.BASIC_AUTH_USERNAME&&process.env.BASIC_AUTH_PASSWORD)options.httpCredentials={username:process.env.BASIC_AUTH_USERNAME,password:process.env.BASIC_AUTH_PASSWORD};
 const page=await browser.newPage(options),errors=[],writes=[];let responses=[];
 page.on("pageerror",e=>errors.push(e.message));
 page.on("request",r=>{if(r.url().includes("/rest/v1/")&&!["GET","HEAD","OPTIONS"].includes(r.method()))writes.push(r.method())});
 page.on("response",r=>{if(r.url().includes("/rest/v1/"))responses.push(r)});
 await page.goto((process.env.BASE_URL||"http://127.0.0.1:3000")+"/betting/weekend");
 await page.locator("[data-favoured-outcome='90']").waitFor();
 assert.equal(await page.locator("[data-likely-scorelines]").count(),10);
 for(const f of frozen.fixtures){
  assert.ok(Date.parse(f.kickoff_time)>Date.now(),"This dated verification must run before GW9 starts");
  assert.equal(await page.locator("[data-likely-scorelines='"+f.fixture_id+"'] li").count(),3);
  assert.deepEqual(await page.locator("[data-likely-scorelines='"+f.fixture_id+"'] li").allTextContents(),await page.locator("[data-likely-scorelines-detail='"+f.fixture_id+"'] li").allTextContents());
 }
 const matchResponse=responses.find(r=>new URL(r.url()).pathname.endsWith("/matches"));assert.ok(matchResponse);const matches=await matchResponse.json();assert.equal(matches.length,80);assert.equal(Math.max(...matches.map(m=>m.gameweek)),8);
 assert.equal(await page.locator("#fixture-71,#fixture-80").count(),0);
 await page.getByText("All published forecasts — separate scorecard",{exact:true}).click();
 const text=await page.locator("body").innerText();
 assert.match(text,/Through 27 October: 35 eligible forecasts from 50 published fixtures across Matchweeks 3, 4, 6, 7, 8/);
 assert.match(text,/Provisional Manchester United away watch/);assert.match(text,/Palmer/);
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+2),false,"Mobile document overflow");
 assert.deepEqual(errors,[]);assert.deepEqual(writes,[]);
 console.log(JSON.stringify({verifiedAt:new Date().toISOString(),liveDatabaseBrowser:"PASS",futureCards:10,scorelines:30,completedMatches:80,previousCards:0,scorecardDate:"2026-10-27",eligibleArchived:35,publishedArchived:50,mobileOverflow:false,browserErrors:0,databaseWrites:0}));
}finally{await browser.close()}
