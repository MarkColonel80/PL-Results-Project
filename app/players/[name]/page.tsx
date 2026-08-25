"use client";
import {useEffect,useState} from "react";
import {useParams,useSearchParams} from "next/navigation";
import {supabase} from "../../../lib/supabase";
export default function Player(){
 const p=useParams(),sp=useSearchParams(),playerId=decodeURIComponent(String(p.name)),season=sp.get("season")||"2025/26";
 const[stat,setStat]=useState<any>(null),[goals,setGoals]=useState<any[]>([]),[assists,setAssists]=useState<any[]>([]),[games,setGames]=useState<any[]>([]);
 useEffect(()=>{(async()=>{const[{data:s},{data:g},{data:a},{data:pm}]=await Promise.all([
  supabase.from("player_season_stats").select("*").eq("season",season).eq("player_id",playerId).maybeSingle(),
  supabase.from("goals").select("*").eq("season",season).eq("player_id",playerId).neq("goal_type","ownGoal").order("minute"),
  supabase.from("goals").select("*").eq("season",season).eq("assist_player_id",playerId).order("minute"),
  supabase.from("player_match_stats").select("match_id,gameweek,minutes_played,is_starting,goals,assists").eq("season",season).eq("player_id",playerId).gt("minutes_played",0).order("gameweek",{ascending:false})
 ]);setStat(s);setGoals(g||[]);setAssists(a||[]);setGames(pm||[])})()},[playerId,season]);
 const name=stat?.player_name||playerId;const show=(v:any)=>v==null?"—":v;
 return <><div className="muted"><a className="textlink" href="/leaders">← Player leaders</a></div><h1>{name}</h1><div className="muted">{stat?.team_name||""} · {season}</div><div className="kpis"><div className="kpi"><b>{show(stat?.appearances)}</b>Appearances</div><div className="kpi"><b>{show(stat?.starts)}</b>Starts</div><div className="kpi"><b>{show(stat?.goals)}</b>Goals</div><div className="kpi"><b>{show(stat?.assists)}</b>Assists</div></div><div className="grid"><section className="card"><h2>Goal events</h2>{goals.length?goals.map((g,i)=><a href={`/matches/${encodeURIComponent(g.match_id)}`} key={i}><div className="goalevent">{g.home_team} v {g.away_team} · <b>{g.minute}{g.added_time?`+${g.added_time}`:""}'</b></div></a>):<p className="muted">No ID-linked goal events loaded.</p>}</section><section className="card"><h2>Assist events</h2>{assists.length?assists.map((g,i)=><a href={`/matches/${encodeURIComponent(g.match_id)}`} key={i}><div className="goalevent">{g.home_team} v {g.away_team} · <b>{g.minute}{g.added_time?`+${g.added_time}`:""}'</b></div></a>):<p className="muted">No ID-linked assist events loaded.</p>}</section></div>{games.length>0&&<section className="card" style={{marginTop:16}}><h2>Appearances</h2><div className="tablewrap"><table><thead><tr><th>GW</th><th>Start?</th><th>Minutes</th><th>Goals</th><th>Assists</th></tr></thead><tbody>{games.map(g=><tr key={g.match_id}><td><a className="textlink" href={`/matches/${encodeURIComponent(g.match_id)}`}>{g.gameweek}</a></td><td>{g.is_starting?"Yes":"No"}</td><td>{g.minutes_played}</td><td>{g.goals}</td><td>{g.assists}</td></tr>)}</tbody></table></div></section>}</>;
}