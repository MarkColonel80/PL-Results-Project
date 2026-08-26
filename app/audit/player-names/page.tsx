"use client";

import {useEffect,useMemo,useState} from "react";
import {supabase} from "../../../lib/supabase";

type AuditRow={
 source:string;
 source_player_id:string;
 player_code:string;
 mapping_method:string|null;
 source_note:string|null;
 canonical_name:string|null;
 canonical_web_name:string|null;
 fpl_name:string|null;
 fpl_season:string|null;
 fpl_team:string|null;
 source_name:string|null;
 source_name_variants:string|null;
 source_first_season:string|null;
 source_last_season:string|null;
 source_teams:string|null;
 source_rows:number|null;
 canonical_first_season:string|null;
 canonical_last_season:string|null;
 canonical_teams:string|null;
 manual_name_verified:boolean|null;
 source_native_identity:boolean|null;
};

type ScoredRow=AuditRow&{score:number;status:"good"|"review"|"different"|"missing";comparisonName:string};

function normalise(value:string|null|undefined){
 return String(value||"")
  .normalize("NFD").replace(/[\u0300-\u036f]/g,"")
  .toLowerCase()
  .replace(/['’`-]/g," ")
  .replace(/[^a-z0-9 ]+/g," ")
  .replace(/\s+/g," ")
  .trim();
}

function levenshtein(a:string,b:string){
 if(a===b)return 0;
 if(!a.length)return b.length;
 if(!b.length)return a.length;
 let prev=Array.from({length:b.length+1},(_,i)=>i);
 for(let i=1;i<=a.length;i++){
  const cur:number[]=[i];
  for(let j=1;j<=b.length;j++)cur[j]=Math.min(cur[j-1]+1,prev[j]+1,prev[j-1]+(a[i-1]===b[j-1]?0:1));
  prev=cur;
 }
 return prev[b.length];
}

function nameSimilarity(rawA:string|null|undefined,rawB:string|null|undefined){
 const a=normalise(rawA),b=normalise(rawB);
 if(!a||!b)return 0;
 if(a===b)return 1;
 const compactA=a.replace(/ /g,""),compactB=b.replace(/ /g,"");
 if(compactA===compactB)return .995;
 const ta=a.split(" ").filter(Boolean),tb=b.split(" ").filter(Boolean);
 const sa=[...ta].sort().join(" "),sb=[...tb].sort().join(" ");
 if(sa===sb)return .99;
 const maxLen=Math.max(compactA.length,compactB.length);
 const charScore=maxLen?1-levenshtein(compactA,compactB)/maxLen:0;
 const sortedMax=Math.max(sa.length,sb.length);
 const sortedScore=sortedMax?1-levenshtein(sa,sb)/sortedMax:0;
 const setA=new Set(ta),setB=new Set(tb);
 const intersection=[...setA].filter(x=>setB.has(x)).length;
 const union=new Set([...ta,...tb]).size;
 const tokenScore=union?intersection/union:0;
 const shorter=compactA.length<=compactB.length?compactA:compactB;
 const longer=compactA.length>compactB.length?compactA:compactB;
 const contains=shorter.length>=4&&longer.includes(shorter)?0.93:0;
 const lastA=ta.at(-1)||"",lastB=tb.at(-1)||"";
 const firstA=ta[0]||"",firstB=tb[0]||"";
 const surnameInitial=lastA.length>=3&&lastA===lastB&&Boolean(firstA[0])&&firstA[0]===firstB[0]?0.94:0;
 const surnameOnly=lastA.length>=4&&lastA===lastB?0.83:0;
 return Math.max(charScore,sortedScore*.98,tokenScore*.92,contains,surnameInitial,surnameOnly);
}

function scoreRow(r:AuditRow):ScoredRow{
 const comparisonName=r.fpl_name||r.canonical_name||"";
 const variants=String(r.source_name_variants||r.source_name||"").split(" | ").filter(Boolean);
 const score=variants.length?Math.max(...variants.map(v=>nameSimilarity(v,comparisonName))):0;
 const status=!r.source_name||!comparisonName?"missing":score>=.88?"good":score>=.70?"review":"different";
 return {...r,score,status,comparisonName};
}

function statusLabel(s:ScoredRow["status"]){return s==="good"?"Looks similar":s==="review"?"Review":s==="different"?"Very different":"Missing name"}
function badgeStyle(s:ScoredRow["status"]){
 const base={display:"inline-block",padding:"4px 8px",borderRadius:999,fontSize:12,fontWeight:700} as const;
 if(s==="good")return {...base,background:"#dcfce7",color:"#166534"};
 if(s==="review")return {...base,background:"#fef3c7",color:"#92400e"};
 if(s==="different")return {...base,background:"#fee2e2",color:"#991b1b"};
 return {...base,background:"#e2e8f0",color:"#475569"};
}

async function loadAll(){
 const out:AuditRow[]=[];
 const pageSize=1000;
 for(let from=0;;from+=pageSize){
  const {data,error}=await supabase.from("player_identity_name_audit_v1").select("*").order("source").order("source_player_id").range(from,from+pageSize-1);
  if(error)throw error;
  const batch=(data||[]) as AuditRow[];
  out.push(...batch);
  if(batch.length<pageSize)break;
 }
 return out;
}

export default function PlayerNameAudit(){
 const[rows,setRows]=useState<AuditRow[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
 const[source,setSource]=useState("all"),[status,setStatus]=useState("needs-review"),[scope,setScope]=useState("fpl"),[query,setQuery]=useState("");
 useEffect(()=>{loadAll().then(setRows).catch(e=>setError(String(e?.message||e))).finally(()=>setLoading(false))},[]);
 const scored=useMemo(()=>rows.map(scoreRow),[rows]);
 const fplRows=useMemo(()=>scored.filter(r=>r.fpl_name),[scored]);
 const counts=useMemo(()=>({
  total:fplRows.length,
  good:fplRows.filter(r=>r.status==="good").length,
  review:fplRows.filter(r=>r.status==="review").length,
  different:fplRows.filter(r=>r.status==="different").length,
  manual:fplRows.filter(r=>r.manual_name_verified).length
 }),[fplRows]);
 const visible=useMemo(()=>scored.filter(r=>{
  if(source!=="all"&&r.source!==source)return false;
  if(scope==="fpl"&&!r.fpl_name)return false;
  if(scope==="canonical"&&!r.comparisonName)return false;
  if(status==="needs-review"&&!(r.status==="review"||r.status==="different"||r.status==="missing"))return false;
  if(status!=="all"&&status!=="needs-review"&&r.status!==status)return false;
  if(query){const q=query.toLowerCase();const hay=[r.source_name,r.fpl_name,r.canonical_name,r.source_teams,r.canonical_teams,r.player_code,r.source_player_id].join(" ").toLowerCase();if(!hay.includes(q))return false}
  return true;
 }).sort((a,b)=>a.score-b.score||a.source.localeCompare(b.source)||String(a.source_name||"").localeCompare(String(b.source_name||""))),[scored,source,status,scope,query]);

 return <>
  <div className="hero"><div><h1>Player identity name audit</h1><div className="muted">Post-match QA only: identities were matched without names. This page checks whether the provider names look consistent with the matched FPL/canonical player.</div></div><a className="textlink" href="/history">FPL history →</a></div>
  <div className="kpis"><div className="kpi"><b>{counts.total.toLocaleString("en-GB")}</b>Matched mappings with FPL names</div><div className="kpi"><b>{counts.review}</b>Review</div><div className="kpi"><b>{counts.different}</b>Very different</div><div className="kpi"><b>{counts.manual}</b>Manual name-verified</div></div>
  <section className="card" style={{marginBottom:16}}>
   <div className="muted" style={{marginBottom:12}}>Similarity is deliberately only an audit signal. A low score does not automatically mean the ID mapping is wrong; nicknames, shortened names and transliteration can legitimately differ.</div>
   <div style={{display:"grid",gridTemplateColumns:"minmax(220px,1fr) repeat(3,minmax(150px,190px))",gap:8}}>
    <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search player, team or code…"/>
    <select value={source} onChange={e=>setSource(e.target.value)}><option value="all">Both providers</option><option value="transfermarkt">Transfermarkt</option><option value="understat">Understat</option></select>
    <select value={status} onChange={e=>setStatus(e.target.value)}><option value="needs-review">Needs review</option><option value="different">Very different only</option><option value="review">Review only</option><option value="good">Looks similar</option><option value="missing">Missing names</option><option value="all">All</option></select>
    <select value={scope} onChange={e=>setScope(e.target.value)}><option value="fpl">FPL-name matches only</option><option value="canonical">Include canonical-only</option></select>
   </div>
  </section>
  {loading?<p>Loading audit…</p>:error?<section className="card"><b>Could not load audit</b><div className="muted" style={{marginTop:6}}>{error}</div></section>:<section className="card">
   <div className="section-title"><div><h2>{visible.length.toLocaleString("en-GB")} rows shown</h2><div className="muted">Worst similarity first. Open the player page to inspect the matched career.</div></div></div>
   <div className="tablewrap"><table><thead><tr><th>Flag</th><th>Score</th><th>Provider</th><th>Provider name</th><th>FPL name</th><th>Canonical name</th><th>Provider context</th><th>Canonical context</th><th>Method</th><th>Player</th></tr></thead><tbody>{visible.map(r=><tr key={`${r.source}:${r.source_player_id}`}>
    <td><span style={badgeStyle(r.status)}>{statusLabel(r.status)}</span>{r.manual_name_verified&&<div><span className="pill">manual</span></div>}</td>
    <td><b>{Math.round(r.score*100)}%</b></td>
    <td>{r.source==="transfermarkt"?"Transfermarkt":"Understat"}<div className="muted" style={{fontSize:11}}>ID {r.source_player_id}</div></td>
    <td><b>{r.source_name||"—"}</b>{r.source_name_variants&&r.source_name_variants!==r.source_name&&<div className="muted" style={{fontSize:11,maxWidth:240,whiteSpace:"normal"}}>Variants: {r.source_name_variants}</div>}</td>
    <td><b>{r.fpl_name||"—"}</b>{r.fpl_season&&<div className="muted" style={{fontSize:11}}>{r.fpl_season}{r.fpl_team?` · ${r.fpl_team}`:""}</div>}</td>
    <td>{r.canonical_name||"—"}</td>
    <td style={{whiteSpace:"normal",minWidth:180}}>{r.source_teams||"—"}<div className="muted" style={{fontSize:11}}>{r.source_first_season||"?"}–{r.source_last_season||"?"} · {Number(r.source_rows||0)} rows</div></td>
    <td style={{whiteSpace:"normal",minWidth:180}}>{r.canonical_teams||"—"}<div className="muted" style={{fontSize:11}}>{r.canonical_first_season||"?"}–{r.canonical_last_season||"?"}</div></td>
    <td style={{whiteSpace:"normal",maxWidth:260}}>{r.mapping_method||"—"}{r.source_native_identity&&<div><span className="pill">source-native</span></div>}</td>
    <td><a className="textlink" href={`/players/${encodeURIComponent(r.player_code)}${r.fpl_season?`?season=${encodeURIComponent(r.fpl_season)}`:""}`}>Open ↗</a><div className="muted" style={{fontSize:11}}>{r.player_code}</div></td>
   </tr>)}</tbody></table></div>
  </section>}
 </>;
}
