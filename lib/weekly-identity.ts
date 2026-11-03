import {createPublicKey,verify} from "node:crypto";
const ISS="https://token.actions.githubusercontent.com";
export const AUD="pl-results-project-weekly";
export function validateClaims(c:Record<string,unknown>,now=Math.floor(Date.now()/1000)){
 if(c.iss!==ISS||c.aud!==AUD||c.repository!=="MarkColonel80/PL-Results-Project"||String(c.repository_id)!=="1346031407"||c.ref!=="refs/heads/main"||c.workflow_ref!=="MarkColonel80/PL-Results-Project/.github/workflows/pl-weekly-cloud.yml@refs/heads/main"||c.runner_environment!=="github-hosted"||!["push","workflow_dispatch"].includes(String(c.event_name))||!/^\d+$/.test(String(c.run_id))||!Number.isFinite(c.exp)||!Number.isFinite(c.nbf)||!Number.isFinite(c.iat)||Number(c.exp)<=now||Number(c.nbf)>now+30||Number(c.iat)>now+30||Number(c.exp)-Number(c.iat)>900)throw new Error("Untrusted worker identity");
 return {runId:String(c.run_id),sha:String(c.sha)};
}
let cache:{at:number;keys:JsonWebKey[]}|undefined;
export async function verifyWorker(token:string){
 if(token.length>12000)throw new Error("Invalid token");
 const parts=token.split(".");if(parts.length!==3)throw new Error("Invalid token");
 const header=JSON.parse(Buffer.from(parts[0],"base64url").toString());
 if(header.alg!=="RS256"||header.typ!=="JWT"||typeof header.kid!=="string")throw new Error("Invalid token");
 if(!cache||Date.now()-cache.at>300000){const r=await fetch(ISS+"/.well-known/jwks",{signal:AbortSignal.timeout(10000)});if(!r.ok)throw new Error("Identity service unavailable");cache={at:Date.now(),keys:(await r.json()).keys};}
 const jwk=cache.keys.find(k=>(k as JsonWebKey&{kid:string}).kid===header.kid);
 if(!jwk||!verify("RSA-SHA256",Buffer.from(parts[0]+"."+parts[1]),createPublicKey({key:jwk,format:"jwk"}),Buffer.from(parts[2],"base64url")))throw new Error("Invalid signature");
 return validateClaims(JSON.parse(Buffer.from(parts[1],"base64url").toString()));
}
