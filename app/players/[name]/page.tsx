"use client";
import {useEffect,useState} from "react";
import {useParams,useSearchParams} from "next/navigation";
import {supabase} from "../../../lib/supabase";
export default function Player(){
 const p=useParams(),sp=useSearchParams(),playerCode=decodeURIComponent(String(p.name)),season=sp.get("season")||"2025/26";
 const[stat,setStat]=useState<any>(null),[goals,setGoals]=useState<any[]>([]),[assists,setAssists]=useState<any[]>([]),[games,setGames]=useState<any[]>([]),[fpl,setFpl]=useState<any[]>([]),[career,setCareer]=useState<any[]>([]);
 useEffect(()=>{(async()=>{
  const{data:s}=await supabase.from("player_season_stats").select("*").eq("season",season).eq("player_code",playerCode).maybeSingle();
  setStat(s);const localId=s?.player_id;
  const [{data:g},{data:a},{data:pm},{data:fp},{data:cs}]=await Promise.all([
   localId?supabase.from("goals").select("*").eq("season",season).eq("player_id",localId).neq("goal_type","ownGoal").order("minute"):Promise.resolve({data:[]}),
   localId?supabase.from("goals").select("*").eq("season",season).eq("assist_player_id",localId).order("minute"):Promise.resolve({data:[]}),
   localId?supabase.from("player_match_stats").select("match_id,gameweek,minutes_played,is_starting,goals,assists,xg,xa").eq("season",season).eq("player_id",localId).gt("minutes_played",0).order("gameweek",{ascending:false}):Promise.resolve({data:[]}),
   supabase.from("fpl_player_match_stats").select("fixture_id,gameweek,kickoff_time,team_name,opponent_team,was_home,minutes,total_points,appearance_points,goal_points,assist_points,clean_sheet_points,save_points,penalty_points,card_points,own_goal_points,goals_conceded_points,defensive_contribution_points,bonus_points").eq("season",season).eq("player_code",playerCode).gt("minutes",0).order("gameweek",{ascending:false}),
   supabase.from("player_season_stats").select("season,team_name,appearances,minutes,goals,assists,fpl_points").eq("player_code",playerCode).order("season",{ascending:false})
  ]);
  setGoals(g||[]);setAssists(a||[]);setGames(pm||[]);setFpl(fp||[]);setCareer(cs||[])
 })()},[playerCode,season]);
 const name=stat?.player_name||playerCode;const show=(v:any)=>v==null?"—":v;
 const parts=(x:any)=>[
  ["App",x.appearance_points],["Goals",x.goal_points],["Assists",x.assist_points],["CS",x.clean_sheet_points],["Saves",x.save_points],["Pens",x.penalty_points],["Cards",x.card_points],["OG",x.own_goal_points],["GC",x.goals_conceded_points],["Def",x.defensive_contribution_points],["Bonus",x.bonus_points]
 ].filter(([,v])=>v!==0&&v!=null).map(([k,v])=>`${k} ${Number(v)>0?"+":""}${v}`).join(" · ");
 return <><div className="muted"><a className="textlink" href="/leaders">← Player leaders</a></div><h1>{name}</h1><div className="muted">{stat?.team_name||""} · {season}</div><div className="kpis"><div className="kpi"><b>{show(stat?.appearances)}</b>Appearances</div><div className="kpi"><b>{Math.round(Number(stat?.minutes||0))}</b>Minutes</div><div className="kpi"><b>{show(stat?.goals)}</b>Goals</div><div className="kpi"><b>{show(stat?.assists)}</b>Assists</div><div className="kpi"><b>{show(stat?.fpl_points)}</b>FPL points</div></div>
 {career.length>1&&<section className="card" style={{marginBottom:16}}><h2>Across seasons</h2><div className="tablewrap"><table><thead><tr><th>Season</th><th>Team</th><th>Apps</th><th>Min</th><th>G</th><th>A</th><th>FPL</th></tr></thead><tbody>{career.map(x=><tr key={x.season}><td><a className="textlink" href={`/players/${encodeURIComponent(playerCode)}?season=${encodeURIComponent(x.season)}`}>{x.season}</a></td><td>{x.team_name||"—"}</td><td>{x.appearances}</td><td>{Math.round(Number(x.minutes||0))}</td><td>{x.goals}</td><td>{x.assists}</td><td>{x.fpl_points??"—"}</td></tr>)}</tbody></table></div></section>}
 <div className="grid"><section className="card"><h2>Goal events</h2>{goals.length?goals.map((g,i)=><a href={`/matches/${encodeURIComponent(g.match_id)}`} key={i}><div className="goalevent">{g.home_team} v {g.away_team} · <b>{g.minute}{g.added_time?`+${g.added_time}`:""}'</b></div></a>):<p className="muted">No goal events.</p>}</section><section className="card"><h2>Assist events</h2>{assists.length?assists.map((g,i)=><a href={`/matches/${encodeURIComponent(g.match_id)}`} key={i}><div className="goalevent">{g.home_team} v {g.away_team} · <b>{g.minute}{g.added_time?`+${g.added_time}`:""}'</b></div></a>):<p className="muted">No assist events.</p>}</section></div>
 {fpl.length>0&&<section className="card" style={{marginTop:16}}><h2>FPL by match</h2><div className="tablewrap"><table><thead><tr><th>GW</th><th>Opponent</th><th>Min</th><th>Pts</th><th>Breakdown</th></tr></thead><tbody>{fpl.map(x=><tr key={x.fixture_id}><td>{x.gameweek}</td><td>{x.was_home?"v":"@"} {x.opponent_team}</td><td>{x.minutes}</td><td><b>{x.total_points}</b></td><td>{parts(x)||"—"}</td></tr>)}</tbody></table></div></section>}
 {games.length>0&&<section className="card" style={{marginTop:16}}><h2>Match performance</h2><div className="tablewrap"><table><thead><tr><th>GW</th><th>Start?</th><th>Min</th><th>G</th><th>A</th><th>xG</th><th>xA</th></tr></thead><tbody>{games.map(g=><tr key={g.match_id}><td><a className="textlink" href={`/matches/${encodeURIComponent(g.match_id)}`}>{g.gameweek}</a></td><td>{g.is_starting?"Yes":"No"}</td><td>{g.minutes_played}</td><td>{g.goals}</td><td>{g.assists}</td><td>{g.xg??"—"}</td><td>{g.xa??"—"}</td></tr>)}</tbody></table></div></section>}</>;
}