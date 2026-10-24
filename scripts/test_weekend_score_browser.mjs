import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {pathToFileURL} from "node:url";
const {chromium}=await import(process.env.PLAYWRIGHT_MODULE_PATH?pathToFileURL(process.env.PLAYWRIGHT_MODULE_PATH).href:"playwright");
const base=process.env.BASE_URL||"http://127.0.0.1:3000";
const fixtures=JSON.parse(readFileSync(new URL("../data/weekend-2026-10-23-snapshots.json",import.meta.url),"utf8")).fixtures.map(({snapshot,...fixture})=>({...fixture,betting_manual_weekend_snapshot:snapshot}));
const browser=await chromium.launch({headless:true,args:["--no-sandbox"]});
try{
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 const errors=[];
 page.on("pageerror",error=>errors.push(error.message));
 const writes=[];
 page.on("request",request=>{if(!["GET","HEAD","OPTIONS"].includes(request.method())&&request.url().includes("/rest/v1/"))writes.push(request.url());});
 await page.clock.install({time:new Date("2026-10-24T13:59:59Z")});
 await page.route("**/rest/v1/**",async route=>{
  const resource=new URL(route.request().url()).pathname.split("/").pop();
  assert.ok(["betting_manual_fixtures","matches"].includes(resource),"Unexpected database read: "+resource);
  await route.fulfill({status:200,contentType:"application/json",headers:{"content-range":"0-0/70"},body:JSON.stringify(resource==="betting_manual_fixtures"?fixtures:[])});
 });
 await page.goto(base+"/betting/weekend");
 await page.locator("[data-predicted-score='73']").waitFor();
 assert.equal(await page.locator("[data-predicted-score]").count(),8);
 assert.equal(await page.locator("#fixture-71, #fixture-72").count(),0);
 assert.match(await page.locator("[data-predicted-score='73']").innerText(),/1–0/);
 assert.match(await page.locator("[data-predicted-score-detail='73']").innerText(),/Arsenal 1–0 Everton/);
 for(const id of [75,76,78,79,80])assert.match(await page.locator("[data-predicted-score='"+id+"']").innerText(),/1–1/);
 for(const id of [74,77]){
  assert.match(await page.locator("[data-predicted-score='"+id+"']").innerText(),/No prediction — LIMITED_HISTORY/);
  assert.equal(await page.locator("[data-predicted-score='"+id+"'] b").count(),0);
 }
 assert.match(await page.locator("body").innerText(),/not rounded expected goals/);
 await page.clock.runFor(1000);
 assert.equal(await page.locator("#fixture-73, #fixture-74").count(),0,"Kickoff timer must remove fixtures without reload");
 assert.equal(await page.locator("[data-predicted-score]").count(),6);
 await page.clock.setSystemTime(new Date("2026-10-24T17:00:00Z"));
 await page.evaluate(()=>window.dispatchEvent(new Event("focus")));
 assert.equal(await page.locator("#fixture-75").count(),0,"Resuming a suspended tab must remove started fixture");
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.locator("[data-predicted-score]").count(),5);
 assert.equal(await page.locator("[data-predicted-score-detail='78']").isVisible(),true);
 assert.deepEqual(errors,[]);
 assert.deepEqual(writes,[]);
 console.log("Browser checks passed: eight future fixtures, six modal scores, two LIMITED_HISTORY, matching summary/detail, exact kickoff removal, focus resume, mobile and read-only requests.");
}finally{await browser.close();}
