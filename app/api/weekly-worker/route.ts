import {NextRequest,NextResponse} from "next/server";
import {verifyWorker} from "../../../lib/weekly-identity";
export const runtime="nodejs";
export const maxDuration=300;
export async function POST(request:NextRequest){
 let identity;
 try{const a=request.headers.get("authorization")||"";if(!a.startsWith("Bearer "))throw new Error();identity=await verifyWorker(a.slice(7));}catch{return NextResponse.json({error:"Worker authentication required"},{status:401});}
 try{
 const text=await request.text();if(text.length>3000000)return NextResponse.json({error:"Payload too large"},{status:413});
 const p=JSON.parse(text);if(!p||typeof p!=="object"||Array.isArray(p))throw new Error("Invalid request");
 if(p.op==="verify_site"){
  const user=process.env.BASIC_AUTH_USERNAME,pass=process.env.BASIC_AUTH_PASSWORD;
  if(!user||!pass)throw new Error("Production authentication not configured");
  const url="https://pl-data.colly.me.uk/betting/weekend";
  const [yes,no]=await Promise.all([fetch(url,{headers:{authorization:"Basic "+Buffer.from(user+":"+pass).toString("base64")},signal:AbortSignal.timeout(20000)}),fetch(url,{redirect:"manual",signal:AbortSignal.timeout(20000)})]);
  if(yes.status!==200||no.status!==401)throw new Error("Production access checks failed");
  return NextResponse.json({authenticated:200,anonymous:401,commit:process.env.VERCEL_GIT_COMMIT_SHA||null,checkedAt:new Date().toISOString()});
 }
 const url=process.env.NEXT_PUBLIC_SUPABASE_URL,key=process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,cap=process.env.PL_WEEKLY_CAPABILITY;
 if(!url||!key||!cap)throw new Error("Worker configuration incomplete");
 const r=await fetch(url+"/rest/v1/rpc/pl_weekly_worker",{method:"POST",headers:{"content-type":"application/json",apikey:key,authorization:"Bearer "+key},body:JSON.stringify({p_capability:cap,p_run:identity.runId,p_op:p.op,p_key:p.key||"",p_data:p.data||{}}),signal:AbortSignal.timeout(270000)});
 const body=await r.json();if(!r.ok)return NextResponse.json({error:body.message||"Worker operation failed"},{status:409});
 return NextResponse.json(body,{headers:{"Cache-Control":"no-store"}});
 }catch(e){return NextResponse.json({error:e instanceof Error?e.message:"Worker failed"},{status:500});}
}
