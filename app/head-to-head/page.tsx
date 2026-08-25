"use client";
import {useEffect,useMemo,useState} from "react";
import {supabase} from "../../lib/supabase";

type Match={id:string,season:string,date:string,home:string,away:string,homeScore:number,awayScore:number,live?:boolean};
const seasonYear=(s:string)=>Number(String(s).slice(0,4))||0;
const niceDate=(d:string)=>{if(!d)return "—";const x=new Date(`${d.slice(0,10)}T12:00:00Z`);return isNaN(x.getTime())?d:x.toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"})};

export default function HeadToHead(){
 const[teams,setTeams]=useState<string[]>([]),[seasons,setSeasons]=useState<string[]>([]),[matches,setMatches]=useState<Match[]>([]);
 const[loading,setLoading]=useState(true),[error,setError]=useState("");
 const[teamA,setTeamA]=useState("Arsenal"),[teamB,setTeamB]=useState("Chelsea"),[fromSeason,setFromSeason]=useState(""),[toSeason,setToSeason]=useState("");

 useEffect(()=>{(async()=>{try{
  const[{data:t,error:te},{data:s,error:se}]=await Promise.all([
   supabase.from("premier_league_result_teams").select("team_name").order("team_name"),
   supabase.from("premier_league_result_seasons").select("season").order("season")
  ]);
  if(te)throw te;if(se)throw se;
  const tt=(t||[]).map((x:any)=>String(x.team_name)).filter(Boolean);
  const ss=(s||[]).map((x:any)=>String(x.season)).filter(Boolean).sort((a,b)=>seasonYear(a)-seasonYear(b));
  setTeams(tt);setSeasons(ss);
  if(tt.length){if(!tt.includes(teamA))setTeamA(tt[0]);if(!tt.includes(teamB)||teamB===tt[0])setTeamB(tt.find(x=>x!==tt[0])||tt[0])}
  if(ss.length){setFromSeason(ss[0]);setToSeason(ss[ss.length-1])}
 }catch(e:any){setError(e?.message||"Could not load head-to-head filters.");setLoading(false)}})()},[]);

 useEffect(()=>{if(!teamA||!teamB||teamA===teamB||!fromSeason||!toSeason)return;(async()=>{setLoading(true);setError("");try{
  const{data,error}=await supabase.rpc("get_premier_league_head_to_head",{p_team_a:teamA,p_team_b:teamB,p_from_season:fromSeason,p_to_season:toSeason});
  if(error)throw error;
  setMatches((data||[]).map((m:any)=>({id:m.match_id,season:m.season,date:String(m.match_date||""),home:m.home_team,away:m.away_team,homeScore:Number(m.home_score),awayScore:Number(m.away_score),live:Boolean(m.live_season)})));
 }catch(e:any){setError(e?.message||"Could not load head-to-head results.");setMatches([])}finally{setLoading(false)}})()},[teamA,teamB,fromSeason,toSeason]);

 const summary=useMemo(()=>matches.reduce((s,m)=>{const aHome=m.home===teamA;const ag=aHome?m.homeScore:m.awayScore,bg=aHome?m.awayScore:m.homeScore;s.aGoals+=ag;s.bGoals+=bg;if(ag>bg)s.aWins++;else if(ag<bg)s.bWins++;else s.draws++;return s},{aWins:0,bWins:0,draws:0,aGoals:0,bGoals:0}),[matches,teamA]);
 const bySeason=useMemo(()=>{const map=new Map<string,Match[]>();for(const m of matches){if(!map.has(m.season))map.set(m.season,[]);map.get(m.season)!.push(m)}return Array.from(map.entries())},[matches]);
 const resultForA=(m:Match)=>{const aHome=m.home===teamA,ag=aHome?m.homeScore:m.awayScore,bg=aHome?m.awayScore:m.homeScore;return ag>bg?"W":ag<bg?"L":"D"};
 const swap=()=>{setTeamA(teamB);setTeamB(teamA)};

 return <>
  <div className="hero"><div><h1>Team head-to-head</h1><div className="muted">Choose any two Premier League clubs and see their meetings from the database archive to the current season.</div></div><a className="textlink" href="/history">← Player history</a></div>
  <section className="card" style={{marginBottom:16}}><div className="h2h-controls"><label>Team A<select value={teamA} onChange={e=>setTeamA(e.target.value)}>{teams.map(t=><option key={t}>{t}</option>)}</select></label><button type="button" onClick={swap} className="swapbutton">⇄ Swap</button><label>Team B<select value={teamB} onChange={e=>setTeamB(e.target.value)}>{teams.map(t=><option key={t}>{t}</option>)}</select></label><label>From<select value={fromSeason} onChange={e=>setFromSeason(e.target.value)}>{seasons.map(s=><option key={s}>{s}</option>)}</select></label><label>To<select value={toSeason} onChange={e=>setToSeason(e.target.value)}>{seasons.map(s=><option key={s}>{s}</option>)}</select></label></div></section>

  {error?<div className="card" style={{marginBottom:16}}><b>Could not load results.</b><div className="muted">{error}</div></div>:teamA===teamB?<div className="card">Choose two different teams.</div>:<>
   <div className="h2h-scorecard"><div><span className="muted">{teamA} wins</span><b>{summary.aWins}</b><small>{summary.aGoals} goals</small></div><div><span className="muted">Meetings</span><b>{loading?"…":matches.length}</b><small>{summary.draws} draws</small></div><div><span className="muted">{teamB} wins</span><b>{summary.bWins}</b><small>{summary.bGoals} goals</small></div></div>
   <section className="card" style={{marginBottom:16}}><h2>Season-by-season meetings</h2>{loading?<p className="muted">Loading results from Supabase…</p>:bySeason.length?bySeason.map(([season,ms])=><div className="h2h-season" key={season}><div className="h2h-season-title"><b>{season}</b><span className="muted">{ms.length} meeting{ms.length===1?"":"s"}</span></div>{ms.map(m=><div className="h2h-result" key={`${m.id}-${m.date}`}><span className={`result-${resultForA(m)}`}>{resultForA(m)}</span><span className="muted">{niceDate(m.date)}</span><span>{m.home}</span><b>{m.homeScore}–{m.awayScore}</b><span>{m.away}</span>{m.live&&<span className="pill">live-season data</span>}</div>)}</div>):<p className="muted">No Premier League meetings found in this season range.</p>}</section>
   <section className="card"><h2>All meetings</h2><div className="tablewrap"><table><thead><tr><th>Season</th><th>Date</th><th>Home</th><th>Score</th><th>Away</th><th>{teamA}</th></tr></thead><tbody>{matches.map(m=><tr key={`${m.id}-table`}><td>{m.season}</td><td>{niceDate(m.date)}</td><td>{m.home}</td><td><b>{m.homeScore}–{m.awayScore}</b></td><td>{m.away}</td><td><span className={`result-${resultForA(m)}`}>{resultForA(m)}</span></td></tr>)}</tbody></table></div></section>
  </>}
  <p className="muted source-note">All page data is served from this project's Supabase database. Historical source files are used only by explicit import scripts.</p>
 </>;
}
