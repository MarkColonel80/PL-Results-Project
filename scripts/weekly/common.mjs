import {createHash} from "node:crypto";
export const origin="https://pl-data.colly.me.uk";
export const hash=x=>createHash("sha256").update(typeof x==="string"?x:JSON.stringify(x)).digest("hex");
export async function boundedFetch(url,options={},attempts=3){
 let last;
 for(let i=0;i<attempts;i++){try{const r=await fetch(url,{...options,signal:AbortSignal.timeout(options.timeout??30000)});if(!r.ok){const e=new Error("HTTP "+r.status+" from "+new URL(url).hostname);if(r.status<500&&r.status!==429)throw Object.assign(e,{permanent:true});throw e;}return r;}catch(e){last=e;if(e.permanent)throw e;if(i+1<attempts)await new Promise(r=>setTimeout(r,1000*(i+1)));}}
 throw last;
}
export async function broker(op,key,data={}){
 const oidc=new URL(process.env.ACTIONS_ID_TOKEN_REQUEST_URL);oidc.searchParams.set("audience","pl-results-project-weekly");
 const jwt=await(await boundedFetch(oidc,{headers:{Authorization:"Bearer "+process.env.ACTIONS_ID_TOKEN_REQUEST_TOKEN}})).json();
 const r=await fetch(origin+"/api/weekly-worker",{method:"POST",headers:{Authorization:"Bearer "+jwt.value,"Content-Type":"application/json"},body:JSON.stringify({op,key,data}),signal:AbortSignal.timeout(295000)});
 const body=await r.json();if(!r.ok)throw new Error(body.error||"Worker operation rejected");return body;
}
