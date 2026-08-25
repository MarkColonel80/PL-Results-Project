"use client";
import {useEffect,useMemo,useState} from "react";
import {useParams,useSearchParams} from "next/navigation";
import {supabase} from "../../../lib/supabase";

export default function Team(){
 const p=useParams(),sp=useSearchParams(),team=decodeURIComponent(String(p.team)),season=sp.get("season")||"2026/27";
 const[stats,setStats]=useState<any>(null),[matches,setMatches]=useState<any[]>([]),[players,setPlayers]=useState<any[]>([]);
 useEffect(()=>{(async()=>{const[{data:s},{data:recentMatches},{data:historicalMatches},{data:pl}]=await Promise.all([
  supabase.from("team_season_stats").select("*").eq("season",season).eq("team",team).maybeSingle(),
  supabase.from("matches").select("*").eq("season",season).or(`home_team.eq.${team},away_team.eq.${team}`).order("kickoff_time",{ascending:false}),
  supabase.from("canonical_matches").select("*").eq("season",season).or(`home_team.eq.${team},away_team.eq.${team}`).order("match_date",{ascending:false}),
  supabase.from("football_player_team_season_stats").select("*").eq("season",season).eq("team_name",team)
 ]);
 const mm=(recentMatches&&recentMatches.length)?recentMatches:(historicalMatches||[]).map((m:any)=>({match_id:m.canonical_match_id,season:m.season,kickoff_time:m.match_date,home_team:m.home_team,away_team:m.away_team,home_score:m.home_score,away_score:m.away_score,gameweek:null,historical:true}));
 const derived=mm.length?mm.reduce((a:any,m:any)=>{const home=m.home_team===team,gf=home?m.home_score:m.away_score,ga=home?m.away_score:m.home_score;a.goals_for+=gf;a.goals_against+=ga;if(gf>ga)a.won++;else if(gf<ga)a.lost++;else a.drawn++;return a},{won:0,drawn:0,lost:0,goals_for:0,goals_against:0,points:0,goal_difference:0}):null;
 if(derived){derived.points=derived.won*3+derived.drawn;derived.goal_difference=derived.goals_for-derived.goals_against;}
 setStats(s||derived);setMatches(mm);setPlayers(pl||[])})()},[team,season]);
 const result=(m:any)=>{const home=m.home_team===team,gf=home?m.home_score:m.away_score,ga=home?m.away_score:m.home_score;return gf>ga?"W":gf<ga?"L":"D"};
 const homeGames=matches.filter(m=>m.home_team===team),awayGames=matches.filter(m=>m.away_team===team);
 const record=(arr:any[])=>arr.reduce((a,m)=>{a[result(m)]++;return a},{W:0,D:0,L:0} as any);
 const homeRecord=record(homeGames),awayRecord=record(awayGames);
 const recent=matches.slice(0,5).map(result),historical=matches.some(m=>m.historical);
 const topScorers=useMemo(()=>[...players].sort((a,b)=>(b.goals||0)-(a.goals||0)||(b.assists||0)-(a.assists||0)).slice(0,8),[players]);
 const topCreators=useMemo(()=>[...players].sort((a,b)=>(b.assists||0)-(a.assists||0)||(b.goals||0)-(a.goals||0)).slice(0,8),[players]);
 const playerLink=(x:any)=>`/players/${encodeURIComponent(x.player_code||x.player_id)}?season=${encodeURIComponent(season)}`;
 const dateLabel=(m:any)=>m.gameweek!=null?`GW ${m.gameweek}`:m.kickoff_time?new Date(m.kickoff_time).toLocaleDateString("en-GB",{day:"2-digit",month:"short"}):"";
 return <>
  <div className="muted"><a className="textlink" href={historical?"/leaders":`/?season=${encodeURIComponent(season)}`}>← {historical?"Leaders":"Dashboard"}</a></div>
  <div className="team-title"><div><h1>{team}</h1><div className="muted">Premier League · {season}</div></div><div className="form-row">{recent.map((r,i)=><span className={`form-badge form-${r}`} key={i}>{r}</span>)}</div></div>
  {stats&&<div className="kpis"><div className="kpi"><b>{stats.points}</b>Points</div><div className="kpi"><b>{stats.won}-{stats.drawn}-{stats.lost}</b>W-D-L</div><div className="kpi"><b>{stats.goals_for}</b>Goals for</div><div className="kpi"><b>{stats.goals_against}</b>Goals against</div><div className="kpi"><b>{stats.goal_difference}</b>Goal difference</div></div>}
  <div className="grid" style={{marginBottom:16}}><section className="card"><h2>Home record</h2><div className="recordline"><b>{homeRecord.W}</b> wins <b>{homeRecord.D}</b> draws <b>{homeRecord.L}</b> losses</div></section><section className="card"><h2>Away record</h2><div className="recordline"><b>{awayRecord.W}</b> wins <b>{awayRecord.D}</b> draws <b>{awayRecord.L}</b> losses</div></section></div>
  <div className="grid"><section className="card"><h2>Results</h2>{matches.length?matches.map(m=><a href={`/matches/${encodeURIComponent(m.match_id)}`} key={m.match_id}><div className="team-result-row"><span className={`result-${result(m)}`}>{result(m)}</span><span className="muted">{dateLabel(m)}</span><span>{m.home_team} <b>{m.home_score}–{m.away_score}</b> {m.away_team}</span></div></a>):<span className="muted">No results available for this season.</span>}</section><section className="stack">{players.length>0?<><div className="card"><h2>Top scorers</h2><div className="muted" style={{marginBottom:8}}>Football match statistics</div><div className="tablewrap"><table><thead><tr><th>Player</th><th>G</th><th>A</th><th>Min</th></tr></thead><tbody>{topScorers.map(x=><tr key={`${x.player_code}-${x.team_name}`}><td><a className="textlink" href={playerLink(x)}>{x.player_name}</a></td><td><b>{x.goals}</b></td><td>{x.assists}</td><td>{Math.round(Number(x.minutes||0))}</td></tr>)}</tbody></table></div></div><div className="card"><h2>Top creators</h2><div className="tablewrap"><table><thead><tr><th>Player</th><th>A</th><th>G</th><th>Min</th></tr></thead><tbody>{topCreators.map(x=><tr key={`${x.player_code}-${x.team_name}`}><td><a className="textlink" href={playerLink(x)}>{x.player_name}</a></td><td><b>{x.assists}</b></td><td>{x.goals}</td><td>{Math.round(Number(x.minutes||0))}</td></tr>)}</tbody></table></div></div></>:<div className="card"><span className="muted">No football player-match data is available for this season yet.</span></div>}</section></div>
 </>;
}
