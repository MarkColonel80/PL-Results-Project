"use client";
import {useEffect,useMemo,useState} from "react";
import {supabase} from "../../lib/supabase";

const seasons=Array.from({length:11},(_,i)=>`${2016+i}/${String(17+i).padStart(2,"0")}`).reverse();
const rankMetrics=[
 ["fpl_points","FPL points"],["goals","Goals"],["assists","Assists"],["ga","Goals + assists"],
 ["fpl90","FPL / 90"],["goals90","Goals / 90"],["assists90","Assists / 90"],["ga90","G+A / 90"],
 ["minutes","Minutes"],["appearances","Appearances"],["seasons","Seasons"]
];
const compareMetrics=[["fpl_points","FPL points"],["goals","Goals"],["assists","Assists"],["goal_contributions","G+A"],["minutes","Minutes"]];
const chartMetrics=[["fpl_points","FPL points"],["goals","Goals"],["assists","Assists"],["goal_contributions","G+A"]];
const N=(v:any)=>Number(v)||0;
const per90=(v:any,m:any)=>N(m)>0?N(v)*90/N(m):0;
const careerValue=(r:any,k:string)=>k==="ga"?N(r.goals)+N(r.assists):k==="fpl90"?per90(r.fpl_points,r.minutes):k==="goals90"?per90(r.goals,r.minutes):k==="assists90"?per90(r.assists,r.minutes):k==="ga90"?per90(N(r.goals)+N(r.assists),r.minutes):N(r[k]);
const seasonValue=(r:any,k:string)=>N(r?.[k]);
const fmt=(v:number,k:string)=>k.endsWith("90")?v.toFixed(2):Math.round(v).toLocaleString("en-GB");

export default function History(){
 const[rows,setRows]=useState<any[]>([]),[query,setQuery]=useState(""),[metric,setMetric]=useState("fpl_points"),[minMinutes,setMinMinutes]=useState(0);
 const[selectedCode,setSelectedCode]=useState(""),[career,setCareer]=useState<any[]>([]),[chartMetric,setChartMetric]=useState("fpl_points");
 const[seasonA,setSeasonA]=useState("2024/25"),[seasonB,setSeasonB]=useState("2025/26"),[compareMetric,setCompareMetric]=useState("fpl_points"),[compareMode,setCompareMode]=useState("rise"),[compareRows,setCompareRows]=useState<any[]>([]);

 useEffect(()=>{(async()=>{const{data}=await supabase.from("player_career_fpl_stats").select("*");const r=data||[];setRows(r);if(r.length&&!selectedCode)setSelectedCode(r[0].player_code)})()},[]);
 useEffect(()=>{if(!selectedCode){setCareer([]);return}(async()=>{const{data}=await supabase.from("player_season_stats").select("season,player_code,player_name,team_name,appearances,minutes,goals,assists,goal_contributions,fpl_points").eq("player_code",selectedCode).order("season");setCareer((data||[]).filter(x=>N(x.minutes)>0))})()},[selectedCode]);
 useEffect(()=>{(async()=>{const[{data:a},{data:b}]=await Promise.all([
  supabase.from("player_season_stats").select("season,player_code,player_name,team_name,appearances,minutes,goals,assists,goal_contributions,fpl_points").eq("season",seasonA),
  supabase.from("player_season_stats").select("season,player_code,player_name,team_name,appearances,minutes,goals,assists,goal_contributions,fpl_points").eq("season",seasonB)
 ]);const A=new Map((a||[]).filter(x=>N(x.minutes)>0).map(x=>[x.player_code,x]));const out=(b||[]).filter(x=>N(x.minutes)>0&&A.has(x.player_code)).map(x=>{const old:any=A.get(x.player_code);return{player_code:x.player_code,player_name:x.player_name||old.player_name,a:old,b:x,delta:seasonValue(x,compareMetric)-seasonValue(old,compareMetric)}});setCompareRows(out)})()},[seasonA,seasonB,compareMetric]);

 const visible=useMemo(()=>rows.filter(r=>N(r.minutes)>=minMinutes&&(!query||String(r.player_name||"").toLowerCase().includes(query.toLowerCase()))).sort((a,b)=>careerValue(b,metric)-careerValue(a,metric)||(N(b.fpl_points)-N(a.fpl_points))).slice(0,300),[rows,query,metric,minMinutes]);
 const comparison=useMemo(()=>[...compareRows].sort((a,b)=>compareMode==="rise"?b.delta-a.delta:a.delta-b.delta).slice(0,30),[compareRows,compareMode]);
 const selected=rows.find(r=>r.player_code===selectedCode);const chartMax=Math.max(1,...career.map(r=>seasonValue(r,chartMetric)));
 const leader=(k:string)=>[...rows].sort((a,b)=>careerValue(b,k)-careerValue(a,k))[0];
 const topPts=leader("fpl_points"),topGoals=leader("goals"),topAssists=leader("assists");

 return <>
  <div className="hero"><div><h1>Premier League player history</h1><div className="muted">All-time FPL-era rankings, per-90 analysis and season comparisons from 2016/17 onward.</div></div><a className="textlink" href="/head-to-head">Team head-to-head →</a></div>
  <div className="kpis"><div className="kpi"><b>{topPts?.fpl_points??"—"}</b>{topPts?.player_name||""}<span className="muted"> · FPL points</span></div><div className="kpi"><b>{topGoals?.goals??"—"}</b>{topGoals?.player_name||""}<span className="muted"> · goals</span></div><div className="kpi"><b>{topAssists?.assists??"—"}</b>{topAssists?.player_name||""}<span className="muted"> · assists</span></div></div>

  <section className="card" style={{marginBottom:16}}><h2>All-time rankings</h2><div className="analytics-filters"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search player…"/><select value={metric} onChange={e=>setMetric(e.target.value)}>{rankMetrics.map(([k,l])=><option key={k} value={k}>Rank by: {l}</option>)}</select><select value={minMinutes} onChange={e=>setMinMinutes(Number(e.target.value))}><option value={0}>No minutes minimum</option><option value={450}>450+ minutes</option><option value={900}>900+ minutes</option><option value={1800}>1,800+ minutes</option><option value={2700}>2,700+ minutes</option></select></div>
   <div className="tablewrap"><table><thead><tr><th>#</th><th>Player</th><th>Seasons</th><th>Range</th><th>Apps</th><th>Min</th><th>G</th><th>A</th><th>G+A</th><th>FPL</th><th>{rankMetrics.find(x=>x[0]===metric)?.[1]}</th></tr></thead><tbody>{visible.map((r,i)=><tr key={r.player_code}><td>{i+1}</td><td><button className="linkbutton" onClick={()=>setSelectedCode(r.player_code)}>{r.player_name}</button> <a className="tiny-link" href={`/players/${encodeURIComponent(r.player_code)}?season=${encodeURIComponent(r.latest_season)}`}>open ↗</a></td><td>{r.seasons}</td><td>{r.first_season}–{r.latest_season}</td><td>{r.appearances}</td><td>{N(r.minutes).toLocaleString("en-GB")}</td><td>{r.goals}</td><td>{r.assists}</td><td>{N(r.goals)+N(r.assists)}</td><td>{r.fpl_points}</td><td><b>{fmt(careerValue(r,metric),metric)}</b></td></tr>)}</tbody></table></div>
  </section>

  {selected&&<section className="card" style={{marginBottom:16}}><div className="section-title"><div><h2>{selected.player_name} career chart</h2><div className="muted">Click another player in the rankings to replace this chart.</div></div><select value={chartMetric} onChange={e=>setChartMetric(e.target.value)}>{chartMetrics.map(([k,l])=><option value={k} key={k}>{l}</option>)}</select></div><div className="career-bars">{career.map(r=>{const v=seasonValue(r,chartMetric);return <div className="career-bar-row" key={r.season}><a href={`/players/${encodeURIComponent(selectedCode)}?season=${encodeURIComponent(r.season)}`}>{r.season}</a><div className="career-bar-track"><span style={{width:`${Math.max(2,v/chartMax*100)}%`}}/></div><b>{Math.round(v)}</b><span className="muted career-team">{r.team_name||""}</span></div>})}</div></section>}

  <section className="card"><h2>Compare two seasons</h2><div className="muted" style={{marginBottom:12}}>Shows players who recorded Premier League minutes in both selected seasons. Delta is Season B minus Season A.</div><div className="compare-controls"><label>Season A<select value={seasonA} onChange={e=>setSeasonA(e.target.value)}>{seasons.map(s=><option key={s}>{s}</option>)}</select></label><label>Season B<select value={seasonB} onChange={e=>setSeasonB(e.target.value)}>{seasons.map(s=><option key={s}>{s}</option>)}</select></label><label>Metric<select value={compareMetric} onChange={e=>setCompareMetric(e.target.value)}>{compareMetrics.map(([k,l])=><option value={k} key={k}>{l}</option>)}</select></label><label>Order<select value={compareMode} onChange={e=>setCompareMode(e.target.value)}><option value="rise">Biggest increase</option><option value="fall">Biggest decrease</option></select></label></div><div className="tablewrap"><table><thead><tr><th>#</th><th>Player</th><th>{seasonA}</th><th>{seasonB}</th><th>Delta</th><th>Teams</th></tr></thead><tbody>{comparison.map((r,i)=><tr key={r.player_code}><td>{i+1}</td><td><a className="textlink" href={`/players/${encodeURIComponent(r.player_code)}?season=${encodeURIComponent(seasonB)}`}>{r.player_name}</a></td><td>{Math.round(seasonValue(r.a,compareMetric))}</td><td>{Math.round(seasonValue(r.b,compareMetric))}</td><td className={r.delta>0?"positive":r.delta<0?"negative":""}><b>{r.delta>0?"+":""}{Math.round(r.delta)}</b></td><td>{r.a.team_name||"—"} → {r.b.team_name||"—"}</td></tr>)}</tbody></table></div></section>
 </>;
}
