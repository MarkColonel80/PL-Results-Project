"use client";
import {useEffect,useMemo,useState} from "react";
import {supabase} from "../../lib/supabase";

type Match={id:string,season:string,date:string,home:string,away:string,homeScore:number,awayScore:number,live?:boolean};
const SOURCE="https://raw.githubusercontent.com/AnishKhetani/premier-league-data/main/data/processed/results.csv";
const ALIASES:Record<string,string>={
 "Man City":"Manchester City","Man United":"Manchester United","Tottenham":"Tottenham Hotspur","Nott'm Forest":"Nottingham Forest",
 "Bournemouth":"AFC Bournemouth","Brighton":"Brighton & Hove Albion","Newcastle":"Newcastle United","Leeds":"Leeds United",
 "Leicester":"Leicester City","Norwich":"Norwich City","West Ham":"West Ham United","Wolves":"Wolverhampton Wanderers",
 "West Brom":"West Bromwich Albion","Swansea":"Swansea City","Cardiff":"Cardiff City","Huddersfield":"Huddersfield Town",
 "Hull":"Hull City","Stoke":"Stoke City","Ipswich":"Ipswich Town","Coventry":"Coventry City","Sheffield Weds":"Sheffield Wednesday",
 "QPR":"Queens Park Rangers","Blackburn":"Blackburn Rovers","Bolton":"Bolton Wanderers","Wigan":"Wigan Athletic","Charlton":"Charlton Athletic",
 "Bradford":"Bradford City","Birmingham":"Birmingham City","Derby":"Derby County"
};
const teamName=(s:string)=>ALIASES[s]||s;
const seasonLabel=(s:string)=>s.includes("-")?`${s.slice(0,4)}/${s.slice(-2)}`:s;
const seasonYear=(s:string)=>Number(String(s).slice(0,4))||0;
const niceDate=(d:string)=>{if(!d)return "—";const x=new Date(`${d.slice(0,10)}T12:00:00Z`);return isNaN(x.getTime())?d:x.toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"})};

export default function HeadToHead(){
 const[matches,setMatches]=useState<Match[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
 const[teamA,setTeamA]=useState("Arsenal"),[teamB,setTeamB]=useState("Chelsea"),[fromSeason,setFromSeason]=useState("1993/94"),[toSeason,setToSeason]=useState("2026/27");

 useEffect(()=>{(async()=>{try{
  const [res,{data:live}]=await Promise.all([fetch(SOURCE),supabase.from("matches").select("match_id,season,kickoff_time,home_team,away_team,home_score,away_score").eq("season","2026/27")]);
  if(!res.ok)throw new Error(`Historical results source returned ${res.status}`);
  const text=await res.text();const lines=text.split(/\r?\n/).slice(1);const historical:Match[]=[];
  for(const line of lines){if(!line)continue;const c=line.split(",");if(c.length<8)continue;const [id,season,,date,home,away,hg,ag]=c;const hs=Number(hg),as=Number(ag);if(!season||!home||!away||Number.isNaN(hs)||Number.isNaN(as))continue;historical.push({id,season:seasonLabel(season),date,home:teamName(home),away:teamName(away),homeScore:hs,awayScore:as});}
  const current:Match[]=(live||[]).filter((m:any)=>m.home_score!=null&&m.away_score!=null).map((m:any)=>({id:m.match_id,season:m.season,date:String(m.kickoff_time||"").slice(0,10),home:teamName(m.home_team),away:teamName(m.away_team),homeScore:Number(m.home_score),awayScore:Number(m.away_score),live:true}));
  setMatches([...historical,...current]);
 }catch(e:any){setError(e?.message||"Could not load results history.")}finally{setLoading(false)}})()},[]);

 const teams=useMemo(()=>Array.from(new Set(matches.flatMap(m=>[m.home,m.away]))).sort((a,b)=>a.localeCompare(b)),[matches]);
 const seasons=useMemo(()=>Array.from(new Set(matches.map(m=>m.season))).sort((a,b)=>seasonYear(a)-seasonYear(b)),[matches]);
 const selected=useMemo(()=>matches.filter(m=>teamA&&teamB&&teamA!==teamB&&((m.home===teamA&&m.away===teamB)||(m.home===teamB&&m.away===teamA))&&seasonYear(m.season)>=seasonYear(fromSeason)&&seasonYear(m.season)<=seasonYear(toSeason)).sort((a,b)=>b.date.localeCompare(a.date)),[matches,teamA,teamB,fromSeason,toSeason]);
 const summary=useMemo(()=>selected.reduce((s,m)=>{const aHome=m.home===teamA;const ag=aHome?m.homeScore:m.awayScore,bg=aHome?m.awayScore:m.homeScore;s.aGoals+=ag;s.bGoals+=bg;if(ag>bg)s.aWins++;else if(ag<bg)s.bWins++;else s.draws++;return s},{aWins:0,bWins:0,draws:0,aGoals:0,bGoals:0}),[selected,teamA]);
 const bySeason=useMemo(()=>{const map=new Map<string,Match[]>();for(const m of selected){if(!map.has(m.season))map.set(m.season,[]);map.get(m.season)!.push(m)}return Array.from(map.entries())},[selected]);
 const resultForA=(m:Match)=>{const aHome=m.home===teamA,ag=aHome?m.homeScore:m.awayScore,bg=aHome?m.awayScore:m.homeScore;return ag>bg?"W":ag<bg?"L":"D"};
 const swap=()=>{setTeamA(teamB);setTeamB(teamA)};

 return <>
  <div className="hero"><div><h1>Team head-to-head</h1><div className="muted">Choose any two Premier League clubs and see their meetings from 1993/94 to the current season.</div></div><a className="textlink" href="/history">← Player history</a></div>
  <section className="card" style={{marginBottom:16}}><div className="h2h-controls"><label>Team A<select value={teamA} onChange={e=>setTeamA(e.target.value)}>{teams.map(t=><option key={t}>{t}</option>)}</select></label><button type="button" onClick={swap} className="swapbutton">⇄ Swap</button><label>Team B<select value={teamB} onChange={e=>setTeamB(e.target.value)}>{teams.map(t=><option key={t}>{t}</option>)}</select></label><label>From<select value={fromSeason} onChange={e=>setFromSeason(e.target.value)}>{seasons.map(s=><option key={s}>{s}</option>)}</select></label><label>To<select value={toSeason} onChange={e=>setToSeason(e.target.value)}>{seasons.map(s=><option key={s}>{s}</option>)}</select></label></div></section>

  {loading?<p>Loading more than 30 years of Premier League results…</p>:error?<div className="card"><b>Could not load historical results.</b><div className="muted">{error}</div></div>:teamA===teamB?<div className="card">Choose two different teams.</div>:<>
   <div className="h2h-scorecard"><div><span className="muted">{teamA} wins</span><b>{summary.aWins}</b><small>{summary.aGoals} goals</small></div><div><span className="muted">Meetings</span><b>{selected.length}</b><small>{summary.draws} draws</small></div><div><span className="muted">{teamB} wins</span><b>{summary.bWins}</b><small>{summary.bGoals} goals</small></div></div>
   <section className="card" style={{marginBottom:16}}><h2>Season-by-season meetings</h2>{bySeason.length?bySeason.map(([season,ms])=><div className="h2h-season" key={season}><div className="h2h-season-title"><b>{season}</b><span className="muted">{ms.length} meeting{ms.length===1?"":"s"}</span></div>{ms.map(m=><div className="h2h-result" key={`${m.id}-${m.date}`}><span className={`result-${resultForA(m)}`}>{resultForA(m)}</span><span className="muted">{niceDate(m.date)}</span><span>{m.home}</span><b>{m.homeScore}–{m.awayScore}</b><span>{m.away}</span>{m.live&&<span className="pill">live-season data</span>}</div>)}</div>):<p className="muted">No Premier League meetings found in this season range.</p>}</section>
   <section className="card"><h2>All meetings</h2><div className="tablewrap"><table><thead><tr><th>Season</th><th>Date</th><th>Home</th><th>Score</th><th>Away</th><th>{teamA}</th></tr></thead><tbody>{selected.map(m=><tr key={`${m.id}-table`}><td>{m.season}</td><td>{niceDate(m.date)}</td><td>{m.home}</td><td><b>{m.homeScore}–{m.awayScore}</b></td><td>{m.away}</td><td><span className={`result-${resultForA(m)}`}>{resultForA(m)}</span></td></tr>)}</tbody></table></div></section>
  </>}
  <p className="muted source-note">Historical results: football-data.co.uk-derived cleaned dataset through 2025/26; 2026/27 comes from the live project database.</p>
 </>;
}
