import assert from "node:assert/strict";
import fs from "node:fs";
import {execFileSync} from "node:child_process";
import {hash,broker,boundedFetch} from "./common.mjs";
import {review,futureArchive} from "./review.mjs";
import {ledgerPrefixUnchanged} from "../../lib/weekend-paper.ts";
const dir="work/weekly";fs.mkdirSync(dir,{recursive:true});
const read=p=>JSON.parse(fs.readFileSync(p,"utf8"));const write=(p,x)=>fs.writeFileSync(p,JSON.stringify(x,null,2)+"\n");
const dispatch=read("data/weekly-dispatch.json"),key=dispatch.date;
assert.match(key,/^2026-\d{2}-\d{2}$/);assert.equal(dispatch.automation_id,"6ad7a14d306c8190b719bd87b6f73e7d");
assert.ok(Math.abs(Date.now()-Date.parse(key+"T09:00:00Z"))<14*86400000,"Dispatch too old");
const gh="https://api.github.com/repos/MarkColonel80/PL-Results-Project";
async function github(path,method="GET",body){return(await boundedFetch(gh+path,{method,headers:{Authorization:"Bearer "+process.env.GH_TOKEN,Accept:"application/vnd.github+json","Content-Type":"application/json"},...(body?{body:JSON.stringify(body)}:{})})).json();}
const receipt=async(stage,value)=>{write(dir+"/"+stage+".json",value);await broker("receipt",key,{stage,value});};
function tests(){execFileSync("python3",["scripts/weekly/test_sources.py"],{stdio:"inherit",timeout:30000});for(const f of ["test_weekend_paper","test_weekend_news","test_weekend_rounds","test_weekend_score","test_weekend_review","test_betting_value","test_weekly_worker"])execFileSync("node",["--experimental-strip-types","scripts/"+f+".mjs"],{stdio:"inherit",timeout:60000});}
let begun=false;
try{
 const start=await broker("begin",key);begun=true;
 if(start.complete){const site=await broker("verify_site",key);write(dir+"/complete.json",{idempotent:true,receipts:start.receipts,site});console.log("Previously completed dispatch: readback passed; no data or ledger changes.");process.exit(0);}
 if(start.receipts?.published?.commit){const published=start.receipts.published.commit;let site;for(let i=0;i<50;i++){site=await broker("verify_site",key);if(site.commit===published)break;await new Promise(r=>setTimeout(r,15000));}assert.equal(site.commit,published,"Published commit still not serving");await receipt("production_verified",{commit:published,site});await broker("finish",key,{success:true});write(dir+"/complete.json",{resumedPublication:published,site});process.exit(0);}
 const before=await broker("read",key);write(dir+"/before.json",before);
 const originalLedger=read("data/weekend-paper-ledger.json");write(dir+"/ledger-before.json",originalLedger);
 const checkpointPath="data/full-refresh-"+key+"-checkpoint.json";
 const checkpoint=fs.existsSync(checkpointPath)?read(checkpointPath):null;
 if(checkpoint?.stage==="production_verified"){
  tests();const site=await broker("verify_site",key);
  const evidence={existingPublishedRefresh:true,matchCount:before.matches.length,futureFixtures:before.fixtures.filter(f=>Date.parse(f.kickoff_time)>Date.now()).length,site};
  await receipt("verified_existing_publication",evidence);
  // Harmless receipt publication proves GITHUB_TOKEN write and Vercel's Git deployment path.
  const head=await github("/git/ref/heads/main");assert.equal(head.object.sha,process.env.GITHUB_SHA);
  const parent=await github("/git/commits/"+head.object.sha);
  const tree=await github("/git/trees","POST",{base_tree:parent.tree.sha,tree:[{path:"data/weekly-worker-acceptance-"+key+".json",mode:"100644",type:"blob",content:JSON.stringify({...evidence,run:process.env.GITHUB_RUN_ID},null,2)+"\\n"}]});
  const commit=await github("/git/commits","POST",{message:"Record cloud-worker acceptance "+key,tree:tree.sha,parents:[head.object.sha]});
  assert.equal((await github("/git/ref/heads/main")).object.sha,head.object.sha);
  await github("/git/refs/heads/main","PATCH",{sha:commit.sha,force:false});await receipt("published",{commit:commit.sha});
  let deployed;for(let i=0;i<50;i++){deployed=await broker("verify_site",key);if(deployed.commit===commit.sha)break;await new Promise(r=>setTimeout(r,15000));}
  assert.equal(deployed.commit,commit.sha,"Worker acceptance publication has not reached production");
  await receipt("production_verified",{commit:commit.sha,site:deployed});await broker("finish",key,{success:true});write(dir+"/complete.json",evidence);console.log(JSON.stringify(evidence));process.exit(0);
 }
 execFileSync("python3",["scripts/weekly/prepare.py"],{stdio:"inherit",timeout:3600000});
 const prepared=read(dir+"/prepared.json");
 const frozenReview=review(before,prepared.completed,originalLedger,prepared.checked_at);
 await receipt("review_frozen",{gameweek:prepared.reviewed_gameweek,results:prepared.completed,scorecard:frozenReview.round,paper:frozenReview.paper});
 for(const [table,rows] of Object.entries(prepared.imports)){
  for(let offset=0;offset<rows.length;offset+=100){
   const chunk=rows.slice(offset,offset+100);const stage="import_"+table+"_"+offset;const digest=hash(chunk);
   // The database independently compares existing facts on every retry.
   const result=await broker("append",key,{table,rows:chunk});await receipt(stage,{sha256:digest,rows:chunk.length,...result});
  }
 }
 await receipt("sources",{preparedHash:hash(prepared),coverage_gaps:prepared.coverage_gaps,evidence:prepared.evidence});
 await broker("upcoming",key,{rows:prepared.upcoming});await receipt("upcoming",{fixtures:prepared.upcoming.length});
 await broker("caches",key);await receipt("caches",{futureOnly:true,model:"v3_24_venue8_50_noppg",minVenue:4});
 const after=await broker("read",key);write(dir+"/after.json",after);
 const future=futureArchive(after.fixtures,prepared,frozenReview.ledger,key);
 assert.ok(ledgerPrefixUnchanged(originalLedger,future.ledger));write("data/weekend-paper-ledger.json",future.ledger);
 const first=prepared.upcoming.map(f=>f.kickoff_time.slice(0,10)).sort()[0];
 const archive="data/weekend-"+first+"-"+key+"-snapshots.json";
 assert.ok(!fs.existsSync(archive),"Immutable dated archive already exists; reconcile publication before retry");
 write(archive,future.archive);
 const report="WEEKEND_REVIEW_"+key+".md";
 const metrics=frozenReview.all;
 write("data/weekend-forecast-scorecard.json",{as_of:key,season:"2026/27",rounds:[...new Set(frozenReview.rows.map(r=>r.gameweek))].sort((a,b)=>a-b),eligible:frozenReview.rows.filter(r=>r.eligible).length,published:frozenReview.rows.length,definitions:"Mean unscaled three-outcome Brier and natural-log loss; lower is better. Frozen pre-match forecasts only.",...metrics,source:"https://github.com/MarkColonel80/PL-Results-Project/blob/main/"+report});
 const lines=["# Tuesday review — "+key,"","Completed full official GW"+prepared.reviewed_gameweek+", including all scheduled Monday matches. Frozen forecasts and recorded paper decisions were reviewed before imports.","",...prepared.completed.map(m=>"- "+m.home_team+" "+m.home_score+"–"+m.away_score+" "+m.away_team),"","## Scorecard","",JSON.stringify({round:frozenReview.round,cumulative:frozenReview.all,paper:frozenReview.paper},null,2),"","## Next official round","",...future.archive.fixtures.map(f=>"- "+f.kickoff_time+" — "+f.home_team+" v "+f.away_team),"","## Coverage gaps","",...prepared.coverage_gaps.map(s=>"- "+s),"","No model, selection, staking or eligibility rules changed. New entries are provisional watches with no stake. Existing decisions and settlements remain append-only.",""];
 fs.writeFileSync(report,lines.join("\n"));
 fs.writeFileSync("DATA_REFRESH_"+key+".md","# Cloud refresh — "+key+"\n\n"+JSON.stringify({reviewedRound:prepared.reviewed_gameweek,imports:Object.fromEntries(Object.entries(prepared.imports).map(([k,v])=>[k,v.length])),coverage_gaps:prepared.coverage_gaps,run:"https://github.com/MarkColonel80/PL-Results-Project/actions/runs/"+process.env.GITHUB_RUN_ID},null,2)+"\n\nProduction verification is recorded in the durable run receipts; publication is not success until that probe passes.\n");
 write(checkpointPath,{date:key,stage:"validated_for_publication",reviewed_round:prepared.reviewed_gameweek,next_round:prepared.next_gameweek,archive,run_id:process.env.GITHUB_RUN_ID,history:"protected by database worker guard",model_rules_changed:false});
 fs.appendFileSync("PROJECT_CONTEXT.md","\n\n## Tuesday cloud refresh "+key+"\n\nSee "+report+", DATA_REFRESH_"+key+".md and "+checkpointPath+". Full round reviewed before append-only source imports; future-only snapshots refreshed. Production verification is retained in the worker receipt and Actions log.\n");
 tests();execFileSync("npm",["run","build"],{stdio:"inherit",timeout:600000});
 await receipt("validated",{archive,ledgerPrefixUnchanged:true,tests:true,build:true});
 const expected=process.env.GITHUB_SHA;const head=await github("/git/ref/heads/main");assert.equal(head.object.sha,expected,"Main changed; reconcile before publication");
 const commit=await github("/git/commits/"+expected);
 const paths=["data/weekend-paper-ledger.json","data/weekend-forecast-scorecard.json",archive,report,"DATA_REFRESH_"+key+".md",checkpointPath,"PROJECT_CONTEXT.md"];
 const tree=await github("/git/trees","POST",{base_tree:commit.tree.sha,tree:paths.map(path=>({path,mode:"100644",type:"blob",content:fs.readFileSync(path,"utf8")}))});
 const saved=await github("/git/commits","POST",{message:"Complete Tuesday PL review and future refresh "+key,tree:tree.sha,parents:[expected]});
 assert.equal((await github("/git/ref/heads/main")).object.sha,expected,"Main advanced during build");
 await github("/git/refs/heads/main","PATCH",{sha:saved.sha,force:false});
 await receipt("published",{commit:saved.sha});
 let site;for(let i=0;i<50;i++){site=await broker("verify_site",key);if(site.commit===saved.sha)break;await new Promise(r=>setTimeout(r,15000));}
 assert.equal(site.commit,saved.sha,"Production did not reach published commit");
 await receipt("production_verified",{commit:saved.sha,site});await broker("finish",key,{success:true});write(dir+"/complete.json",{commit:saved.sha,site,coverage_gaps:prepared.coverage_gaps});
 console.log("Tuesday refresh published and production verified: "+saved.sha);
}catch(e){
 const failure={error:e.message,at:new Date().toISOString(),run:process.env.GITHUB_RUN_ID};
 write(dir+"/failure.json",failure);console.error("Weekly worker stopped: "+e.message);
 if(begun)try{await receipt("failure",failure);await broker("finish",key,{success:false});}catch{}
 process.exitCode=1;
}
