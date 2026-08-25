"use client";
import {useEffect,useMemo,useState} from "react";
import {supabase} from "../../lib/supabase";
import SeasonSelect from "../../components/SeasonSelect";

const sorts:any={contributions:["goal_contributions","G+A"],goals:["goals","Goals"],assists:["assists","Assists"],minutes:["minutes","Minutes"],starts:["starts","Starts"],appearances:["appearances","Apps"]};
export default function Leaders(){
 const[season,setSeason]=useState("2026/27"),[rows,setRows]=useState<any[]>([]),[query,setQuery]=useState(""),[sort,setSort]=useState("contributions"),[loading,setLoading]=useState(true),[goalSummary,setGoalSummary]=useState<any>(null);
 useEffect(()=>{let cancelled=false;(async()=>{setLoading(true);const[{data:leaders},{data:summary}]=await Promise.all([
   supabase.rpc("get_football_player_season_leaders",{p_season:season}),
   supabase.rpc("get_season_goal_summary",{p_season:season})
  ]);if(cancelled)return;setRows((leaders||[]).filter((r:any)=>Number(r.appearances||0)>0));setGoalSummary(summary?.[0]||null);setLoading(false)})();return()=>{cancelled=true}},[season]);
 const visible=useMemo(()=>rows.filter(r=>!query||`${r.player_name} ${r.team_name}`.toLowerCase().includes(query.toLowerCase())).sort((a,b)=>(Number(b[sorts[sort][0]])||0)-(Number(a[sorts[sort][0]])||0)||(Number(b.goals)||0)-(Number(a.goals)||0)),[rows,query,sort]);
 const show=(v:any)=>v==null?"—":v;
 const ownGoals=Number(goalSummary?.own_goals||0),matchGoals=Number(goalSummary?.match_goals||0),playerGoals=Number(goalSummary?.credited_player_goals||0);
 return <><div className="hero"><div><h1>Player leaders</h1><div className="muted">Football match statistics only. FPL points and FPL-defined assists are kept separately.</div>{goalSummary&&matchGoals>0&&<div className="recordline" style={{marginTop:8}}><b>{matchGoals} league goals</b><span>= {playerGoals} player goals{ownGoals?` + ${ownGoals} own goal${ownGoals===1?"":"s"}`:""}</span></div>}</div><SeasonSelect season={season} onChange={setSeason} includeFootballHistory/></div><div className="filterbar"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search player or team…"/><select value={sort} onChange={e=>setSort(e.target.value)}>{Object.entries(sorts).map(([k,v]:any)=><option value={k} key={k}>Sort: {v[1]}</option>)}</select></div>{loading?<div className="card"><span className="muted">Loading leaders…</span></div>:visible.length===0?<div className="card"><span className="muted">No football player-match data is available for this season yet.</span></div>:<div className="tablewrap"><table><thead><tr><th>#</th><th>Player</th><th>Team</th><th>Apps</th><th>Min</th><th>Goals</th><th>Assists</th><th>G+A</th></tr></thead><tbody>{visible.map((r,i)=><tr key={`${r.player_code}-${r.team_name}`}><td>{i+1}</td><td><a href={`/players/${encodeURIComponent(r.player_code)}?season=${encodeURIComponent(season)}`}><b>{r.player_name}</b></a></td><td>{r.team_name?<a href={`/teams/${encodeURIComponent(r.team_name)}?season=${encodeURIComponent(season)}`}>{r.team_name}</a>:"—"}</td><td>{r.appearances}</td><td>{Math.round(Number(r.minutes||0))}</td><td>{show(r.goals)}</td><td>{show(r.assists)}</td><td><b>{show(r.goal_contributions)}</b></td></tr>)}</tbody></table></div>}</>;
}
