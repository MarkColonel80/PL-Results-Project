"use client";
import {useEffect,useState} from "react";
import {useParams,useSearchParams} from "next/navigation";
import {supabase} from "../../../lib/supabase";

export default function Player(){
 const p=useParams(),sp=useSearchParams(),playerCode=decodeURIComponent(String(p.name)),season=sp.get("season")||"2026/27";
 const[stat,setStat]=useState<any>(null),[fplSeason,setFplSeason]=useState<any>(null),[goals,setGoals]=useState<any[]>([]),[assists,setAssists]=useState<any[]>([]),[games,setGames]=useState<any[]>([]),[fpl,setFpl]=useState<any[]>([]),[seasons,setSeasons]=useState<any[]>([]),[career,setCareer]=useState<any>(null),[identity,setIdentity]=useState<any>(null);
 useEffect(()=>{(async()=>{
  const[{data:s},{data:fs},{data:id},{data:careerRow}]=await Promise.all([
   supabase.from("football_player_season_stats").select("*").eq("season",season).eq("player_code",playerCode).maybeSingle(),
   supabase.from("fpl_player_season_stats").select("*").eq("season",season).eq("player_code",playerCode).maybeSingle(),
   supabase.from("players").select("first_name,second_name,web_name").eq("player_code",playerCode).maybeSingle(),
   supabase.from("player_career_fpl_stats").select("*").eq("player_code",playerCode).maybeSingle()
  ]);
  setStat(s);setFplSeason(fs);setIdentity(id);setCareer(careerRow);
  const [{data:g},{data:a},{data:pm},{data:fp},{data:history}]=await Promise.all([
   supabase.from("goals").select("*").eq("season",season).eq("player_code",playerCode).or("goal_type.is.null,goal_type.neq.ownGoal").order("minute"),
   supabase.from("goals").select("*").eq("season",season).eq("assist_player_code",playerCode).order("minute"),
   supabase.from("player_match_stats").select("match_id,gameweek,minutes_played,is_starting,goals,assists,xg,xa,shots,shots_on_target,chances_created,key_passes,xg_chain,xg_buildup,source,advanced_source").eq("season",season).eq("player_code",playerCode).gt("minutes_played",0).order("gameweek",{ascending:false}),
   supabase.from("fpl_player_match_stats").select("fixture_id,gameweek,kickoff_time,team_name,opponent_team,was_home,minutes,total_points,appearance_points,goal_points,assist_points,clean_sheet_points,save_points,penalty_points,card_points,own_goal_points,goals_conceded_points,defensive_contribution_points,bonus_points").eq("season",season).eq("player_code",playerCode).gt("minutes",0).order("gameweek",{ascending:false}).order("kickoff_time",{ascending:false}),
   supabase.from("football_player_season_stats").select("season,team_name,appearances,minutes,goals,assists").eq("player_code",playerCode).gt("minutes",0).order("season",{ascending:false})
  ]);
  setGoals(g||[]);setAssists(a||[]);setGames(pm||[]);setFpl(fp||[]);setSeasons(history||[])
 })()},[playerCode,season]);
 const fullName=[identity?.first_name,identity?.second_name].filter(Boolean).join(" ")||identity?.web_name||stat?.player_name||fplSeason?.player_name||career?.player_name||playerCode;
 const show=(v:any)=>v==null?"—":v;
 const metric=(v:any)=>v==null?"—":Number(v).toFixed(2);
 const per90=(v:any)=>Number(stat?.minutes)>0?(Number(v||0)*90/Number(stat.minutes)).toFixed(2):"—";
 const parts=(x:any)=>[
  ["App",x.appearance_points],["Goals",x.goal_points],["Assists",x.assist_points],["CS",x.clean_sheet_points],["Saves",x.save_points],["Pens",x.penalty_points],["Cards",x.card_points],["OG",x.own_goal_points],["GC",x.goals_conceded_points],["Def",x.defensive_contribution_points],["Bonus",x.bonus_points]
 ].filter(([,v])=>v!==0&&v!=null).map(([k,v])=>`${k} ${Number(v)>0?"+":""}${v}`).join(" · ");
 return <>
  <div className="muted"><a className="textlink" href="/history">← FPL history</a></div>
  <h1>{fullName}</h1><div className="muted">{stat?.team_name||fplSeason?.team_name||""} · {season} · Player code {playerCode}</div>
  {stat?<><div className="muted" style={{marginTop:12}}>Football match statistics</div><div className="kpis"><div className="kpi"><b>{show(stat.appearances)}</b>Appearances</div><div className="kpi"><b>{Math.round(Number(stat.minutes||0))}</b>Minutes</div><div className="kpi"><b>{show(stat.goals)}</b>Goals</div><div className="kpi"><b>{show(stat.assists)}</b>Assists</div><div className="kpi"><b>{show(stat.goal_contributions)}</b>G+A</div><div className="kpi"><b>{per90(stat.goal_contributions)}</b>G+A / 90</div></div></>:<section className="card" style={{marginTop:16,marginBottom:16}}><span className="muted">No football player-match data is available for this player in {season} yet.</span></section>}
  {fplSeason&&<section className="card" style={{marginBottom:16}}><h2>FPL · {season}</h2><div className="kpis"><div className="kpi"><b>{fplSeason.fpl_points}</b>FPL points</div><div className="kpi"><b>{fplSeason.appearances}</b>Apps</div><div className="kpi"><b>{fplSeason.goals}</b>Goals</div><div className="kpi"><b>{fplSeason.assists}</b>FPL assists</div><div className="kpi"><b>{fplSeason.bonus}</b>Bonus</div></div><div className="muted">FPL-defined statistics are stored separately from football-provider match statistics.</div></section>}
  {career&&<section className="card" style={{marginBottom:16}}><h2>FPL career</h2><div className="kpis"><div className="kpi"><b>{career.seasons}</b>FPL seasons</div><div className="kpi"><b>{career.appearances}</b>Appearances</div><div className="kpi"><b>{career.goals}</b>Goals</div><div className="kpi"><b>{career.assists}</b>FPL assists</div><div className="kpi"><b>{career.fpl_points}</b>FPL points</div></div><div className="muted">{career.first_season} to {career.latest_season}</div></section>}
  {seasons.length>0&&<section className="card" style={{marginBottom:16}}><h2>Football season history</h2><div className="tablewrap"><table><thead><tr><th>Season</th><th>Team</th><th>Apps</th><th>Min</th><th>G</th><th>A</th></tr></thead><tbody>{seasons.map(x=><tr key={x.season}><td><a className="textlink" href={`/players/${encodeURIComponent(playerCode)}?season=${encodeURIComponent(x.season)}`}>{x.season}</a></td><td>{x.team_name||"—"}</td><td>{x.appearances}</td><td>{Math.round(Number(x.minutes||0))}</td><td>{x.goals}</td><td>{x.assists}</td></tr>)}</tbody></table></div></section>}
  <div className="grid"><section className="card"><h2>Goal events</h2>{goals.length?goals.map((g,i)=><a href={`/matches/${encodeURIComponent(g.match_id)}`} key={`${g.match_id}-${g.incident_index??i}`}><div className="goalevent">{g.home_team} v {g.away_team} · <b>{g.minute}{g.added_time?`+${g.added_time}`:""}'</b></div></a>):<p className="muted">No goal-event detail available for this season.</p>}</section><section className="card"><h2>Assist events</h2>{assists.length?assists.map((g,i)=><a href={`/matches/${encodeURIComponent(g.match_id)}`} key={`${g.match_id}-${g.incident_index??i}`}><div className="goalevent">{g.home_team} v {g.away_team} · <b>{g.minute}{g.added_time?`+${g.added_time}`:""}'</b></div></a>):<p className="muted">No assist-event detail available for this season.</p>}</section></div>
  {fpl.length>0&&<section className="card" style={{marginTop:16}}><h2>FPL by match</h2><div className="tablewrap"><table><thead><tr><th>GW</th><th>Opponent</th><th>Min</th><th>Pts</th><th>Breakdown</th></tr></thead><tbody>{fpl.map(x=><tr key={`${x.fixture_id}-${x.gameweek}`}><td>{x.gameweek}</td><td>{x.was_home?"v":"@"} {x.opponent_team}</td><td>{x.minutes}</td><td><b>{x.total_points}</b></td><td>{parts(x)||"—"}</td></tr>)}</tbody></table></div></section>}
  {games.length>0?<section className="card" style={{marginTop:16}}><h2>Football by match</h2><div className="muted" style={{marginBottom:8}}>Advanced xG/xA, shots and key-pass metrics use Understat where available; base goals, assists and minutes retain their original football-source provenance.</div><div className="tablewrap"><table><thead><tr><th>GW</th><th>Start?</th><th>Min</th><th>G</th><th>A</th><th>xG</th><th>xA</th><th>Shots</th><th>SOT</th><th>Key passes</th><th>Chances</th><th>xGChain</th><th>xGBuildup</th></tr></thead><tbody>{games.map(g=><tr key={g.match_id}><td><a className="textlink" href={`/matches/${encodeURIComponent(g.match_id)}`}>{g.gameweek??"Match"}</a></td><td>{g.is_starting==null?"—":g.is_starting?"Yes":"No"}</td><td>{g.minutes_played}</td><td>{g.goals}</td><td>{g.assists}</td><td>{metric(g.xg)}</td><td>{metric(g.xa)}</td><td>{g.shots??"—"}</td><td>{g.shots_on_target??"—"}</td><td>{g.key_passes??"—"}</td><td>{g.chances_created??"—"}</td><td>{metric(g.xg_chain)}</td><td>{metric(g.xg_buildup)}</td></tr>)}</tbody></table></div></section>:fpl.length>0&&<p className="muted" style={{marginTop:12}}>Football match-performance data is shown only where a football source has been imported.</p>}
 </>;
}
