"use client";
import {useEffect,useMemo,useState} from "react";
import {supabase} from "../../lib/supabase";
import SeasonSelect from "../../components/SeasonSelect";

const sorts:any={contributions:["goal_contributions","G+A"],goals:["goals","Goals"],assists:["assists","Assists"],fpl:["fpl_points","FPL points"],minutes:["minutes","Minutes"],starts:["starts","Starts"],appearances:["appearances","Apps"]};
export default function Leaders(){
 const[season,setSeason]=useState("2025/26"),[rows,setRows]=useState<any[]>([]),[query,setQuery]=useState(""),[sort,setSort]=useState("contributions");
 useEffect(()=>{(async()=>{const{data}=await supabase.from("player_season_stats").select("*").eq("season",season);setRows(data||[])})()},[season]);
 const visible=useMemo(()=>rows.filter(r=>!query||`${r.player_name} ${r.team_name}`.toLowerCase().includes(query.toLowerCase())).sort((a,b)=>(b[sorts[sort][0]]||0)-(a[sorts[sort][0]]||0)||(b.goals||0)-(a.goals||0)),[rows,query,sort]);
 const show=(v:any)=>v==null?"—":v;
 return <><div className="hero"><div><h1>Player leaders</h1><div className="muted">Search players and rank by football or FPL output.</div></div><SeasonSelect season={season} onChange={setSeason}/></div><div className="filterbar"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search player or team…"/><select value={sort} onChange={e=>setSort(e.target.value)}>{Object.entries(sorts).map(([k,v]:any)=><option value={k} key={k}>Sort: {v[1]}</option>)}</select></div><div className="tablewrap"><table><thead><tr><th>#</th><th>Player</th><th>Team</th><th>Apps</th><th>Min</th><th>Goals</th><th>Assists</th><th>G+A</th><th>FPL</th></tr></thead><tbody>{visible.map((r,i)=><tr key={`${r.player_code}-${r.team_name}`}><td>{i+1}</td><td><a href={`/players/${encodeURIComponent(r.player_code)}?season=${encodeURIComponent(season)}`}><b>{r.player_name}</b></a></td><td>{r.team_name?<a href={`/teams/${encodeURIComponent(r.team_name)}?season=${encodeURIComponent(season)}`}>{r.team_name}</a>:"—"}</td><td>{r.appearances}</td><td>{Math.round(Number(r.minutes||0))}</td><td>{show(r.goals)}</td><td>{show(r.assists)}</td><td><b>{show(r.goal_contributions)}</b></td><td>{show(r.fpl_points)}</td></tr>)}</tbody></table></div></>;
}