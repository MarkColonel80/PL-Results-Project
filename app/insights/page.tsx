"use client";

import {useEffect,useMemo,useState} from "react";
import {supabase} from "../../lib/supabase";

type Row={season:string;player_code:string;player_name:string;team_name:string|null;position:string|null;appearances:number|null;starts:number|null;minutes:number|null;goals:number|null;assists:number|null;goal_contributions:number|null;xg:number|null;xa:number|null;fpl_points:number|null;price_tenths:number|null;selected:number|null;xgi:number|null;xgi_per90:number|null;goals_minus_xg:number|null;gi_minus_xgi:number|null;fpl_per90:number|null;points_per_million:number|null};

type Mode="threat"|"buy-low"|"overperform"|"value"|"points";
const seasons=Array.from({length:11},(_,i)=>`${2016+i}/${String(17+i).padStart(2,"0")}`).reverse();
const N=(v:any)=>Number(v)||0;
const fmt=(v:any,d=2)=>v==null?"—":Number(v).toFixed(d);
const money=(v:any)=>v==null?"—":`£${(Number(v)/10).toFixed(1)}m`;
const modeInfo:Record<Mode,{label:string;desc:string}>={
 threat:{label:"Underlying threat",desc:"Highest xG + xA per 90"},
 "buy-low":{label:"Buy-low signals",desc:"Chance output ahead of goals + assists"},
 overperform:{label:"Overperformers",desc:"Goals + assists furthest ahead of xGI"},
 value:{label:"FPL value",desc:"Most FPL points per £1m"},
 points:{label:"FPL points",desc:"Highest total FPL score"}
};

function sortRows(rows:Row[],mode:Mode){
 return [...rows].sort((a,b)=>{
  if(mode==="threat")return N(b.xgi_per90)-N(a.xgi_per90);
  if(mode==="buy-low")return N(a.gi_minus_xgi)-N(b.gi_minus_xgi);
  if(mode==="overperform")return N(b.gi_minus_xgi)-N(a.gi_minus_xgi);
  if(mode==="value")return N(b.points_per_million)-N(a.points_per_million);
  return N(b.fpl_points)-N(a.fpl_points);
 });
}

export default function Insights(){
 const[season,setSeason]=useState("2025/26"),[rows,setRows]=useState<Row[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
 const[mode,setMode]=useState<Mode>("threat"),[position,setPosition]=useState("all"),[team,setTeam]=useState("all"),[minMinutes,setMinMinutes]=useState(900),[query,setQuery]=useState("");
 useEffect(()=>{(async()=>{setLoading(true);setError("");const{data,error}=await supabase.from("player_decision_stats_v1").select("*").eq("season",season);if(error)setError(error.message);else setRows((data||[]) as Row[]);setLoading(false)})()},[season]);
 const teams=useMemo(()=>Array.from(new Set(rows.map(r=>r.team_name).filter(Boolean) as string[])).sort(),[rows]);
 const filtered=useMemo(()=>rows.filter(r=>N(r.minutes)>=minMinutes&&(position==="all"||String(r.position||"").toLowerCase().startsWith(position))&&(team==="all"||r.team_name===team)&&(!query||`${r.player_name} ${r.team_name||""}`.toLowerCase().includes(query.toLowerCase()))),[rows,minMinutes,position,team,query]);
 const visible=useMemo(()=>sortRows(filtered,mode).slice(0,250),[filtered,mode]);
 const leaders=useMemo(()=>({
  threat:sortRows(filtered,"threat")[0],
  buy:sortRows(filtered,"buy-low")[0],
  over:sortRows(filtered,"overperform")[0],
  value:sortRows(filtered,"value")[0]
 }),[filtered]);
 const setSeasonSafe=(s:string)=>{setSeason(s);setMinMinutes(s==="2026/27"?60:900)};
 return <>
  <div className="hero"><div><h1>Player Insights</h1><div className="muted">Turn FPL points and underlying football data into decisions: threat, regression and value.</div></div><div><span className="muted">Season </span><select value={season} onChange={e=>setSeasonSafe(e.target.value)}>{seasons.map(s=><option key={s}>{s}</option>)}</select></div></div>

  <div className="kpis">
   <button className="kpi" onClick={()=>setMode("threat")} style={{textAlign:"left",color:"inherit",background:mode==="threat"?"#eef2ff":"#fff",borderColor:mode==="threat"?"#94a3b8":"#e2e8f0"}}><span className="muted">Underlying threat</span><b>{leaders.threat?.player_name||"—"}</b><span>{leaders.threat?`${fmt(leaders.threat.xgi_per90)} xGI/90`:""}</span></button>
   <button className="kpi" onClick={()=>setMode("buy-low")} style={{textAlign:"left",color:"inherit",background:mode==="buy-low"?"#eef2ff":"#fff",borderColor:mode==="buy-low"?"#94a3b8":"#e2e8f0"}}><span className="muted">Buy-low signal</span><b>{leaders.buy?.player_name||"—"}</b><span>{leaders.buy?`${fmt(Math.max(0,-N(leaders.buy.gi_minus_xgi)))} xGI ahead`:""}</span></button>
   <button className="kpi" onClick={()=>setMode("overperform")} style={{textAlign:"left",color:"inherit",background:mode==="overperform"?"#eef2ff":"#fff",borderColor:mode==="overperform"?"#94a3b8":"#e2e8f0"}}><span className="muted">Overperformance</span><b>{leaders.over?.player_name||"—"}</b><span>{leaders.over?`+${fmt(leaders.over.gi_minus_xgi)} GI vs xGI`:""}</span></button>
   <button className="kpi" onClick={()=>setMode("value")} style={{textAlign:"left",color:"inherit",background:mode==="value"?"#eef2ff":"#fff",borderColor:mode==="value"?"#94a3b8":"#e2e8f0"}}><span className="muted">FPL value</span><b>{leaders.value?.player_name||"—"}</b><span>{leaders.value?`${fmt(leaders.value.points_per_million,1)} pts/£m`:""}</span></button>
  </div>

  <section className="card" style={{marginBottom:16}}>
   <div className="section-title"><div><h2>{modeInfo[mode].label}</h2><div className="muted">{modeInfo[mode].desc}. These are signals to investigate, not predictions.</div></div><select value={mode} onChange={e=>setMode(e.target.value as Mode)}><option value="threat">Underlying threat</option><option value="buy-low">Buy-low signals</option><option value="overperform">Overperformers</option><option value="value">FPL value</option><option value="points">FPL points</option></select></div>
   <div className="analytics-filters" style={{gridTemplateColumns:"minmax(180px,1fr) 150px 190px 190px"}}><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search player or team…"/><select value={position} onChange={e=>setPosition(e.target.value)}><option value="all">All positions</option><option value="goal">Goalkeepers</option><option value="def">Defenders</option><option value="mid">Midfielders</option><option value="for">Forwards</option></select><select value={team} onChange={e=>setTeam(e.target.value)}><option value="all">All teams</option>{teams.map(t=><option key={t}>{t}</option>)}</select><select value={minMinutes} onChange={e=>setMinMinutes(Number(e.target.value))}><option value={0}>No minutes minimum</option><option value={60}>60+ minutes</option><option value={450}>450+ minutes</option><option value={900}>900+ minutes</option><option value={1800}>1,800+ minutes</option></select></div>
  </section>

  {loading?<p>Loading insights…</p>:error?<section className="card"><b>Could not load insights</b><div className="negative">{error}</div></section>:<section className="card">
   <div className="section-title"><div><h2>{visible.length.toLocaleString("en-GB")} players</h2><div className="muted">Price is the latest FPL price recorded in the selected season. Negative GI−xGI means underlying chance involvement exceeded actual returns.</div></div></div>
   <div className="tablewrap"><table><thead><tr><th>#</th><th>Player</th><th>Team</th><th>Pos</th><th>Price</th><th>Min</th><th>FPL</th><th>xG</th><th>xA</th><th>xGI/90</th><th>G−xG</th><th>GI−xGI</th><th>Pts/£m</th></tr></thead><tbody>{visible.map((r,i)=><tr key={r.player_code}><td>{i+1}</td><td><a className="textlink" href={`/players/${encodeURIComponent(r.player_code)}?season=${encodeURIComponent(season)}`}>{r.player_name}</a></td><td>{r.team_name||"—"}</td><td>{r.position||"—"}</td><td>{money(r.price_tenths)}</td><td>{Math.round(N(r.minutes)).toLocaleString("en-GB")}</td><td><b>{r.fpl_points??"—"}</b></td><td>{fmt(r.xg)}</td><td>{fmt(r.xa)}</td><td><b>{fmt(r.xgi_per90)}</b></td><td className={N(r.goals_minus_xg)>0?"positive":N(r.goals_minus_xg)<0?"negative":""}>{N(r.goals_minus_xg)>0?"+":""}{fmt(r.goals_minus_xg)}</td><td className={N(r.gi_minus_xgi)>0?"positive":N(r.gi_minus_xgi)<0?"negative":""}>{N(r.gi_minus_xgi)>0?"+":""}{fmt(r.gi_minus_xgi)}</td><td>{fmt(r.points_per_million,1)}</td></tr>)}</tbody></table></div>
  </section>}
  <section className="card" style={{marginTop:16}}><h2>How to read this</h2><div className="grid"><div><b>xGI/90</b><div className="muted">Expected goals + expected assists per 90. A simple measure of attacking opportunity.</div></div><div><b>G−xG</b><div className="muted">Finishing versus chance quality. Large positives can flag unsustainable finishing; negatives can flag missed chances.</div></div><div><b>GI−xGI</b><div className="muted">Actual goals + assists minus expected involvement. Negative values are the buy-low/regression-upward list.</div></div><div><b>Pts/£m</b><div className="muted">Season FPL points divided by the latest price recorded in that season.</div></div></div></section>
 </>;
}
