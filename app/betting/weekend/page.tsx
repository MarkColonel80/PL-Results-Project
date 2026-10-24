"use client";

import {useEffect,useMemo,useState} from "react";
import Link from "next/link";
import {supabase} from "../../../lib/supabase";
import {defaultWeekend,groupWeekendFixtures,weekendLabel} from "../../../lib/weekend-rounds";
import {favouredOutcome,likelyScorelines} from "../../../lib/weekend-score";
import {bettingValue} from "../../../lib/betting-value";
import {parseWeekendNews} from "../../../lib/weekend-review";
import {PaperReview,PaperScorecard,paperStatus} from "./paper-review";

type Snapshot={home_n8:number|null;away_n8:number|null;home_n30:number|null;away_n30:number|null;home_ppg30:number|null;away_ppg30:number|null;home_vn18:number|null;away_vn18:number|null;home_vppg18:number|null;away_vppg18:number|null;home_vxgf18:number|null;home_vxga18:number|null;away_vxgf18:number|null;away_vxga18:number|null;home_vppg8:number|null;away_vppg8:number|null;home_vgf8:number|null;home_vga8:number|null;home_vxgf8:number|null;home_vxga8:number|null;away_vgf8:number|null;away_vga8:number|null;away_vxgf8:number|null;away_vxga8:number|null;goal_xg_residual_cap:number|null;home_vgf8_capped:number|null;home_vga8_capped:number|null;away_vgf8_capped:number|null;away_vga8_capped:number|null;league_home_goals:number;league_away_goals:number;league_home_xg:number;league_away_xg:number;calculated_at:string;candidate_model_version:string|null;candidate_home_n24:number|null;candidate_away_n24:number|null;candidate_home_n10:number|null;candidate_away_n10:number|null;candidate_home_ppg10:number|null;candidate_away_ppg10:number|null;candidate_home_lambda:number|null;candidate_away_lambda:number|null;candidate_home_prob:number|null;candidate_draw_prob:number|null;candidate_away_prob:number|null;candidate_calculated_at:string|null};
type Fixture={fixture_id:number;kickoff_time:string;home_team:string;away_team:string;market_home_odds:number|null;market_draw_odds:number|null;market_away_odds:number|null;market_source:string|null;market_snapshot_at:string|null;notes:string|null;betting_manual_weekend_snapshot:Snapshot|null};

const MIN_VENUE_MATCHES=4;

function TeamNews({fixture}:{fixture:Fixture}){
 const news=parseWeekendNews(fixture.notes);
 if(!news)return null;
 return <div style={{marginTop:16,padding:16,border:"1px solid var(--border, #d6dde5)",borderRadius:8}}>
  <h3 style={{margin:"0 0 6px"}}>Team news and schedule</h3>
  <div className="muted" style={{fontSize:13}}>Checked {dayTime(news.checkedAt)} · {news.teams}</div>
  <p><b>{fixture.home_team}:</b> {news.home}</p>
  <p><b>{fixture.away_team}:</b> {news.away}</p>
  <p><b>Recovery and Europe:</b> {news.schedule}</p>
  {news.availability.length>0&&<details><summary>Official FPL availability flags</summary>
   {news.availability.map((line,i)=><p key={i} className="muted">{line}</p>)}
   <p className="muted" style={{fontSize:13}}>Flags can lag club announcements. A possible return or an expected return date does not confirm availability.</p>
  </details>}
  <div style={{fontSize:13,display:"flex",gap:12,flexWrap:"wrap"}}>{news.sources.map(s=><a key={s.url} href={s.url} target="_blank" rel="noreferrer">{s.label}</a>)}</div>
  <p className="muted" style={{fontSize:13,marginBottom:0}}>Recheck confirmed teams and an available price near kick-off. These reports do not adjust the model probabilities.</p>
 </div>;
}
const N=(v:number|null|undefined)=>v==null?null:Number(v);
const fmt=(v:number|null|undefined,d=2)=>v==null||!Number.isFinite(Number(v))?"—":Number(v).toFixed(d);
const pct=(v:number|null|undefined)=>v==null?"—":`${(v*100).toFixed(1)}%`;
const fair=(p:number|null|undefined)=>p==null||p<=0?"—":(1/p).toFixed(2);
const clamp=(v:number,min:number,max:number)=>Math.max(min,Math.min(max,v));
function trend(v8:number|null|undefined,v18:number|null|undefined,n18:number|null|undefined,lowerBetter=false){if(n18!==18||v8==null||v18==null)return"";const d=(Number(v8)-Number(v18))*(lowerBetter?-1:1);return d>.02?"↑":d<-.02?"↓":"→"}
function compare(v8:number|null|undefined,v18:number|null|undefined,n18:number|null|undefined,lowerBetter=false){if(v8==null)return"—";if(n18!==18||v18==null)return `${fmt(v8,3)} · no full 18-match sample`;return `${fmt(v8,3)} ${trend(v8,v18,n18,lowerBetter)} vs ${fmt(v18,3)}`}
function poisson(lambda:number,max=8){const a=[Math.exp(-lambda)];for(let i=1;i<=max;i++)a[i]=a[i-1]*lambda/i;return a}
function probs(hl:number,al:number){const hp=poisson(hl),ap=poisson(al);let h=0,d=0,a=0;for(let i=0;i<hp.length;i++)for(let j=0;j<ap.length;j++){const p=hp[i]*ap[j];if(i>j)h+=p;else if(i===j)d+=p;else a+=p}const t=h+d+a;return{h:h/t,d:d/t,a:a/t}}
function market(h:number|null,d:number|null,a:number|null){if(!h||!d||!a)return null;const x=1/h,y=1/d,z=1/a,t=x+y+z;return{h:x/t,d:y/t,a:z/t}}
function outcome(p:{h:number;d:number;a:number}){return p.h>=p.d&&p.h>=p.a?"Home":p.d>=p.a?"Draw":"Away"}
function dayTime(v:string){return new Intl.DateTimeFormat("en-GB",{weekday:"short",day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",timeZone:"Europe/London"}).format(new Date(v))}

function ValueIndicator({probability,odds}:{probability:number|null|undefined;odds:number|null|undefined}){
 const value=bettingValue(probability,N(odds));
 if(!value)return <span className="muted">—</span>;
 const status=value.direction==="positive"?"Positive model price gap — paper review required":value.direction==="negative"?"Negative model price gap":"Break-even";
 const explanation=`${status}: our probability ${pct(probability)}, chance needed at these odds ${pct(value.breakEvenProbability)}. Difference in percentage points.`;
 return <span className={value.direction==="neutral"?"muted":value.direction} style={{fontWeight:700}} title={explanation} aria-label={explanation}><span aria-hidden="true">{value.direction==="positive"?"↑":value.direction==="negative"?"↓":"→"}</span> {value.label}</span>;
}

function ValueOutcomes({probabilities,fixture}:{probabilities:{h:number;d:number;a:number}|null|undefined;fixture:Fixture}){
 return <div style={{display:"flex",gap:12}}>
  <span><span className="muted">H </span><ValueIndicator probability={probabilities?.h} odds={fixture.market_home_odds}/></span>
  <span><span className="muted">D </span><ValueIndicator probability={probabilities?.d} odds={fixture.market_draw_odds}/></span>
  <span><span className="muted">A </span><ValueIndicator probability={probabilities?.a} odds={fixture.market_away_odds}/></span>
 </div>;
}


function favouriteText(favourite:NonNullable<ReturnType<typeof favouredOutcome>>,fixture:Fixture){
 const labels=favourite.outcomes.map(outcome=>outcome==="home"?fixture.home_team+" win":outcome==="away"?fixture.away_team+" win":"Draw");
 return `${labels.length>1?"Joint favourites: ":""}${labels.join(" / ")} · ${pct(favourite.probability)}${labels.length>1?" each":""}`;
}

function LikelyScorelines({scores}:{scores:NonNullable<ReturnType<typeof likelyScorelines>>}){
 return <ol style={{margin:"4px 0",paddingLeft:24}}>{scores.map(score=><li key={`${score.home}-${score.away}`} style={{whiteSpace:"nowrap"}}><b>{score.home}–{score.away}</b> · {pct(score.probability)}{score.tied?<span className="muted"> · equal probability</span>:null}</li>)}</ol>;
}

export default function WeekendVenueReview(){
 const[allRows,setAllRows]=useState<Fixture[]>([]),[selectedRound,setSelectedRound]=useState("");
 const[now,setNow]=useState<number|null>(null);
 const[loading,setLoading]=useState(true),[error,setError]=useState("");
 const[completedMatches,setCompletedMatches]=useState<{home_team:string;away_team:string;kickoff_time:string}[]|null>(null);
 const[dataStatus,setDataStatus]=useState<{count:number;gameweek:number;date:string}|null>(null);
 useEffect(()=>{let active=true;(async()=>{try{
  const [fixtures,latest]=await Promise.all([
   supabase.from("betting_manual_fixtures").select("fixture_id,kickoff_time,home_team,away_team,market_home_odds,market_draw_odds,market_away_odds,market_source,market_snapshot_at,notes,betting_manual_weekend_snapshot(*)").gte("kickoff_time",new Date().toISOString()).order("kickoff_time"),
   supabase.from("matches").select("gameweek,kickoff_time,home_team,away_team",{count:"exact"}).eq("season","2026/27").not("home_score","is",null).not("away_score","is",null).order("kickoff_time",{ascending:false})
  ]);
  if(!active)return;
  if(fixtures.error)throw fixtures.error;
  const data=(fixtures.data||[]) as unknown as Fixture[];
  setAllRows(data);setSelectedRound(defaultWeekend(data));
  if(!latest.error&&latest.data?.[0]){setDataStatus({count:latest.count||0,gameweek:latest.data[0].gameweek,date:latest.data[0].kickoff_time});setCompletedMatches(latest.data);}
 }catch(err){if(active)setError(err instanceof Error?err.message:String((err as {message?:string}).message||err));}finally{if(active)setLoading(false);}})();return()=>{active=false};},[]);
 // Remove kicked-off fixtures even if the page stays open or resumes from sleep.
 useEffect(()=>{
  let timer:ReturnType<typeof setTimeout>;
  const refresh=()=>{
   clearTimeout(timer);
   const time=Date.now();
   setNow(time);
   const next=allRows.map(f=>Date.parse(f.kickoff_time)).filter(t=>t>time).sort((a,b)=>a-b)[0];
   timer=setTimeout(refresh,next==null?60000:Math.min(60000,next-time));
  };
  refresh();
  window.addEventListener("focus",refresh);
  document.addEventListener("visibilitychange",refresh);
  return()=>{clearTimeout(timer);window.removeEventListener("focus",refresh);document.removeEventListener("visibilitychange",refresh)};
 },[allRows]);
 const rounds=useMemo(()=>groupWeekendFixtures(allRows.filter(f=>now!==null&&Date.parse(f.kickoff_time)>now)),[allRows,now]);
 const rows=useMemo(()=>rounds.find(r=>r.key===selectedRound)?.rows||[],[rounds,selectedRound]);
 const marketPending=rows.some(f=>f.market_home_odds==null||f.market_draw_odds==null||f.market_away_odds==null);
 const cards=useMemo(()=>rows.map(f=>{const s=f.betting_manual_weekend_snapshot;const scores=likelyScorelines(f.kickoff_time,s,now??NaN);const favourite=favouredOutcome(f.kickoff_time,s,now??NaN);const m=market(N(f.market_home_odds),N(f.market_draw_odds),N(f.market_away_odds));if(!s)return{f,s:null,m,scores,favourite,calc:null};const eligible=(s.home_n8??0)>=MIN_VENUE_MATCHES&&(s.away_n8??0)>=MIN_VENUE_MATCHES;const hgf=s.home_vgf8_capped??s.home_vgf8,hga=s.home_vga8_capped??s.home_vga8,agf=s.away_vgf8_capped??s.away_vgf8,aga=s.away_vga8_capped??s.away_vga8;const ahf=s.home_vxgf8!=null&&hgf!=null?(Number(s.home_vxgf8)+Number(hgf))/2:null;const aha=s.home_vxga8!=null&&hga!=null?(Number(s.home_vxga8)+Number(hga))/2:null;const aaf=s.away_vxgf8!=null&&agf!=null?(Number(s.away_vxgf8)+Number(agf))/2:null;const aaa=s.away_vxga8!=null&&aga!=null?(Number(s.away_vxga8)+Number(aga))/2:null;let p=null,hl=null,al=null;if(eligible&&ahf!=null&&aha!=null&&aaf!=null&&aaa!=null){hl=clamp(Number(s.league_home_goals)*Math.pow((ahf/Number(s.league_home_xg))*(aaa/Number(s.league_home_xg)),.8),.15,4.5);al=clamp(Number(s.league_away_goals)*Math.pow((aaf/Number(s.league_away_xg))*(aha/Number(s.league_away_xg)),.8),.15,4.5);p=probs(hl,al)}const gap=s.home_vppg8!=null&&s.away_vppg8!=null?Math.abs(Number(s.home_vppg8)-Number(s.away_vppg8)):null;const close=eligible&&gap!=null&&gap<=.30;const decision=!eligible?`No model pick — minimum ${MIN_VENUE_MATCHES} venue matches required`:close&&p?`${outcome(p)} — adjusted venue xG tie-break`:(Number(s.home_vppg8)>Number(s.away_vppg8)?"Home — venue PPG":Number(s.away_vppg8)>Number(s.home_vppg8)?"Away — venue PPG":"Draw — venue PPG");const candidateP=s.candidate_home_prob!=null&&s.candidate_draw_prob!=null&&s.candidate_away_prob!=null?{h:Number(s.candidate_home_prob),d:Number(s.candidate_draw_prob),a:Number(s.candidate_away_prob)}:null;const candidateDecision=candidateP?outcome(candidateP):`No comparison score — minimum ${MIN_VENUE_MATCHES} current-spell venue matches required`;return{f,s,m,scores,favourite,calc:{eligible,ahf,aha,aaf,aaa,hl,al,p,gap,close,decision,candidateP,candidateDecision}}}),[rows,now]);
 if(loading)return <p>Loading weekend review…</p>;
 if(error)return <section className="card"><b>Could not load weekend review</b><div className="negative">{error}</div></section>;
 return <>
  <div className="hero"><div><h1>Weekend fixtures · paper bets</h1><div className="muted">Compare forecasts with saved prices, review uncertain signals and follow the recorded paper decisions for each fixture.</div></div><Link href="/betting">← Betting Lab</Link></div>
  <section className="card" style={{borderLeft:"4px solid #b7791f"}}><h2 style={{marginTop:0}}>Paper-bet mode</h2><p>No real-money bets are recorded here. Green arrows show mathematical price gaps; they do not establish a reliable betting edge. A watch becomes a one-unit paper selection only after confirmed teams, an available named-bookmaker price, news, schedule and sensitivity checks have been recorded before kick-off.</p><p className="muted" style={{marginBottom:0}}>There is no automatic best bet. A pass or a weekend with no selections is valid.</p></section>
  <PaperScorecard/>
  <section className="card">
   <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:16,flexWrap:"wrap"}}>
    <div><h2 style={{margin:"0 0 6px"}}>{weekendLabel(rows)}</h2><div className="muted">{rows.length} fixtures · All kick-off times are UK time</div></div>
   </div>
   {dataStatus&&<p className="muted">Results loaded through Matchweek {dataStatus.gameweek}: {dataStatus.count} completed matches, latest {dayTime(dataStatus.date)}.</p>}
   {marketPending&&rows.length>0&&<p className="muted">Market odds are pending. An available bookmaker quote must be recorded before a paper selection. Forecast timestamps and history are shown in each fixture.</p>}
   {!rows.length&&<p>No upcoming fixtures have been published for review yet.</p>}
   {cards.length>0&&<div style={{overflowX:"auto",marginTop:12}}><table><thead><tr><th>Kick-off (UK)</th><th>Fixture</th><th>Favoured outcome</th><th>Three likeliest scorelines (home–away)</th><th>24-match + Venue8: H / D / A</th><th>Model price gap: H / D / A</th><th>Paper decision</th></tr></thead><tbody>{cards.map(({f,calc,scores,favourite})=><tr key={f.fixture_id}><td>{dayTime(f.kickoff_time)}</td><td><a href={`#fixture-${f.fixture_id}`}>{f.home_team} v {f.away_team}</a></td><td data-favoured-outcome={f.fixture_id}>{favourite?<b>{favouriteText(favourite,f)}</b>:calc&&!calc.eligible?"No forecast — LIMITED_HISTORY":"No outcome forecast available"}</td><td data-likely-scorelines={f.fixture_id}>{scores?<LikelyScorelines scores={scores}/>:calc&&!calc.eligible?"No prediction — LIMITED_HISTORY":"No scorelines available"}</td><td>{calc?.candidateP?`${pct(calc.candidateP.h)} / ${pct(calc.candidateP.d)} / ${pct(calc.candidateP.a)}`:"Limited history"}</td><td><ValueOutcomes probabilities={calc?.candidateP} fixture={f}/></td><td><a href={`#review-${f.fixture_id}`}>{paperStatus(f)}</a></td></tr>)}</tbody></table></div>}
   {cards.length>0&&<p className="muted" style={{fontSize:13}}>Model price gap uses the 24-match + Venue8 probability minus the break-even chance at the saved price (1 ÷ odds). ↑ Green means a positive mathematical gap, ↓ red negative, → break-even. Differences are percentage points (pp), not expected profit or a recommendation. Paper selections require the recorded checks below. — means no forecast or price is available.</p>}
  </section>
  <section className="card"><b>How to read the outcome and scorelines</b><p><b>Favoured outcome</b> is the highest saved home/draw/away probability from the 24-match + Venue8 research candidate. Each outcome combines many possible scores; a favourite can have less than a 50% chance.</p><p><b>Three likeliest scorelines</b> are ranked by their individual probabilities under the same candidate&apos;s independent Poisson distribution, using frozen expected goals. A 1–1 score can lead this list while a home or away win is favoured overall. These are not rounded expected goals, and the three percentages do not add up to 100% because other scores remain possible.</p><p className="muted" style={{marginBottom:0}}>All scores are home–away. Equal probabilities use fewer total goals first, then fewer home goals; only three scores are listed even when more are tied. No new forecast is shown for LIMITED_HISTORY, unavailable pre-match inputs or fixtures that have kicked off. These are research forecasts, not paper selections.</p></section>
  <section className="card"><b>Adjusted venue xG rule</b><div className="muted" style={{marginTop:6}}>A hard minimum of <b>4 relevant venue matches per team</b> applies before the current weekend model produces expected goals, H/D/A probabilities, fair odds or a pick. Samples of 4–7 matches are eligible partial Venue8 samples; 8 is the full window. Actual goals are capped only when they exceed match xG by more than 1.0 goal: capped actual = min(actual, xG + 1.0), then blended 50/50 with raw venue xG. The separate <b>24-match + Venue8 comparison</b> uses the research candidate: equal-weight 24-match structural strength, 65% xG + 35% capped actual goals, four pseudo-match shrinkage, the same capped Venue8 inputs, and a 50/50 geometric shrink of the team-specific Venue8 baseline back toward the generic league home/away baseline. <b>PPG10 is diagnostic only and is not used in this comparison probability.</b> It does not replace the current weekend-rule pick. All prices below are decimal odds; bookmaker probabilities use the latest saved 1X2 market prices when available.</div></section>
  <div style={{display:"grid",gap:14}}>{cards.map(({f,s,m,calc,scores,favourite})=><section className="card" key={f.fixture_id} id={`fixture-${f.fixture_id}`}>
   <div style={{display:"flex",justifyContent:"space-between",gap:12,alignItems:"flex-start",flexWrap:"wrap"}}><div><div className="muted">{dayTime(f.kickoff_time)}</div><h2 style={{margin:"4px 0"}}>{f.home_team} <span className="muted">v</span> {f.away_team}</h2></div><div><div className="muted">Model view · not a paper selection</div><b>{calc?.decision||"—"}</b>{calc?.eligible&&calc?.gap!=null&&<div className="muted">Venue PPG gap {fmt(calc.gap,3)}{calc.close?" · xG tie-break active":""}</div>}</div></div>
   <div data-forecast-detail={f.fixture_id} style={{marginTop:12,padding:14,border:"1px solid var(--border, #d6dde5)",borderRadius:8}}>
    <div className="muted" style={{fontSize:13}}>24-match + Venue8 research forecast</div>
    <div data-favoured-outcome-detail={f.fixture_id} style={{marginTop:6}}><b>Favoured outcome: </b>{favourite?<strong>{favouriteText(favourite,f)}</strong>:<span className="muted">{calc&&!calc.eligible?"No forecast — LIMITED_HISTORY":"No outcome forecast available"}</span>}</div>
    <div data-likely-scorelines-detail={f.fixture_id} style={{marginTop:10}}><b>Three likeliest scorelines (home–away)</b>{scores?<><LikelyScorelines scores={scores}/><div className="muted" style={{fontSize:13}}>Each percentage is for that exact score. Other scores remain possible.</div></>:<p className="muted">{calc&&!calc.eligible?"No prediction — LIMITED_HISTORY (minimum 4 venue matches per team).":"No scorelines available from a valid frozen pre-match forecast."}</p>}</div>
   </div>
   <PaperReview fixture={f} snapshot={s} primary={calc?.p} research={calc?.candidateP} matches={completedMatches}/>
    <TeamNews fixture={f}/>
   {!s?<p>No snapshot.</p>:<>
    <div style={{marginTop:12}}><b>Calculation inputs</b><div className="muted" style={{marginTop:4}}>These figures feed the current weekend calculation only when both teams meet the 4-match minimum.</div></div>
    <div style={{overflowX:"auto",marginTop:8}}><table><thead><tr><th>Venue8 calculation</th><th>{f.home_team}</th><th>{f.away_team}</th></tr></thead><tbody>
     <tr><td>Matches available</td><td>{s.home_n8}</td><td>{s.away_n8}</td></tr><tr><td><b>PPG8</b></td><td><b>{fmt(s.home_vppg8,3)}</b></td><td><b>{fmt(s.away_vppg8,3)}</b></td></tr>
     <tr><td>Actual GF8</td><td>{fmt(s.home_vgf8)}</td><td>{fmt(s.away_vgf8)}</td></tr><tr><td>Capped actual GF8 (+1 xG max)</td><td>{fmt(s.home_vgf8_capped)}</td><td>{fmt(s.away_vgf8_capped)}</td></tr><tr><td>Raw xGF8</td><td>{fmt(s.home_vxgf8)}</td><td>{fmt(s.away_vxgf8)}</td></tr><tr><td><b>Adjusted xGF8</b></td><td><b>{fmt(calc?.ahf)}</b></td><td><b>{fmt(calc?.aaf)}</b></td></tr>
     <tr><td>Actual GA8</td><td>{fmt(s.home_vga8)}</td><td>{fmt(s.away_vga8)}</td></tr><tr><td>Capped actual GA8 (+1 xG max)</td><td>{fmt(s.home_vga8_capped)}</td><td>{fmt(s.away_vga8_capped)}</td></tr><tr><td>Raw xGA8</td><td>{fmt(s.home_vxga8)}</td><td>{fmt(s.away_vxga8)}</td></tr><tr><td><b>Adjusted xGA8</b></td><td><b>{fmt(calc?.aha)}</b></td><td><b>{fmt(calc?.aaa)}</b></td></tr>
    </tbody></table></div>

    <div style={{marginTop:14}}><b>Diagnostics only — not used in current weekend calculation</b><div className="muted" style={{marginTop:4}}>Overall PPG30 and venue8-versus-venue18 comparisons are shown only to help judge whether recent venue form looks unusually hot or cold. ↑ means the last 8 are better than the last 18, ↓ worse, → broadly unchanged. For xGA, lower is better.</div></div>
    <div style={{overflowX:"auto",marginTop:8}}><table><thead><tr><th>Diagnostic</th><th>{f.home_team}</th><th>{f.away_team}</th></tr></thead><tbody>
     <tr><td>Overall PPG30</td><td>{fmt(s.home_ppg30,3)} {s.home_n30==null?"":`(${s.home_n30}/30)`}</td><td>{fmt(s.away_ppg30,3)} {s.away_n30==null?"":`(${s.away_n30}/30)`}</td></tr>
     <tr><td>Venue PPG8 vs PPG18</td><td>{compare(s.home_vppg8,s.home_vppg18,s.home_vn18)}</td><td>{compare(s.away_vppg8,s.away_vppg18,s.away_vn18)}</td></tr>
     <tr><td>Venue xGF8 vs xGF18</td><td>{compare(s.home_vxgf8,s.home_vxgf18,s.home_vn18)}</td><td>{compare(s.away_vxgf8,s.away_vxgf18,s.away_vn18)}</td></tr>
     <tr><td>Venue xGA8 vs xGA18</td><td>{compare(s.home_vxga8,s.home_vxga18,s.home_vn18,true)}</td><td>{compare(s.away_vxga8,s.away_vxga18,s.away_vn18,true)}</td></tr>
     <tr><td>Venue18 sample</td><td>{s.home_vn18==null?"—":`${s.home_vn18}/18`}</td><td>{s.away_vn18==null?"—":`${s.away_vn18}/18`}</td></tr>
    </tbody></table></div>

    {calc?.p&&<div style={{overflowX:"auto",marginTop:12}}><table><thead><tr><th>Current adjusted xG match view</th><th>Home</th><th>Draw</th><th>Away</th></tr></thead><tbody><tr><td>Expected goals</td><td>{fmt(calc.hl)}</td><td>—</td><td>{fmt(calc.al)}</td></tr><tr><td>1X2 probability</td><td>{pct(calc.p.h)}</td><td>{pct(calc.p.d)}</td><td>{pct(calc.p.a)}</td></tr></tbody></table></div>}

    <div style={{marginTop:14}}><b>24-match + Venue8 comparison</b><div className="muted" style={{marginTop:4}}>Research comparison only. Structural strength uses up to 24 matches from the team&apos;s current PL spell; Venue8 is shrunk 50/50 toward the generic league home/away baseline. PPG10 is shown as context but is not used in the probability. The top outcome below does not replace the current weekend-rule pick above.</div></div>
    <div style={{overflowX:"auto",marginTop:8}}><table><thead><tr><th>Research candidate</th><th>{f.home_team}</th><th>Draw</th><th>{f.away_team}</th></tr></thead><tbody>
     <tr><td>Structural history</td><td>{s.candidate_home_n24==null?"—":`${s.candidate_home_n24}/24`}</td><td>—</td><td>{s.candidate_away_n24==null?"—":`${s.candidate_away_n24}/24`}</td></tr>
     <tr><td>PPG10 diagnostic — not used</td><td>{fmt(s.candidate_home_ppg10,3)} {s.candidate_home_n10==null?"":`(${s.candidate_home_n10}/10)`}</td><td>—</td><td>{fmt(s.candidate_away_ppg10,3)} {s.candidate_away_n10==null?"":`(${s.candidate_away_n10}/10)`}</td></tr>
     <tr><td>Expected goals</td><td>{fmt(s.candidate_home_lambda)}</td><td>—</td><td>{fmt(s.candidate_away_lambda)}</td></tr>
     <tr><td>1X2 probability</td><td>{pct(calc?.candidateP?.h)}</td><td>{pct(calc?.candidateP?.d)}</td><td>{pct(calc?.candidateP?.a)}</td></tr>
     <tr><td>Fair odds</td><td>{fair(calc?.candidateP?.h)}</td><td>{fair(calc?.candidateP?.d)}</td><td>{fair(calc?.candidateP?.a)}</td></tr>
     <tr><td><b>Top outcome</b></td><td colSpan={3}><b>{calc?.candidateDecision||"—"}</b></td></tr>
    </tbody></table></div>
   </>}
   <div style={{overflowX:"auto",marginTop:12}}><table><thead><tr><th>Odds comparison (decimal)</th><th>Home</th><th>Draw</th><th>Away</th></tr></thead><tbody>
    <tr><td>Current weekend fair odds</td><td>{fair(calc?.p?.h)}</td><td>{fair(calc?.p?.d)}</td><td>{fair(calc?.p?.a)}</td></tr>
    <tr><td>24-match + Venue8 fair odds</td><td>{fair(calc?.candidateP?.h)}</td><td>{fair(calc?.candidateP?.d)}</td><td>{fair(calc?.candidateP?.a)}</td></tr>
    <tr><td>Market odds</td><td>{fmt(f.market_home_odds)}</td><td>{fmt(f.market_draw_odds)}</td><td>{fmt(f.market_away_odds)}</td></tr>
    <tr><td>Current weekend probability</td><td>{pct(calc?.p?.h)}</td><td>{pct(calc?.p?.d)}</td><td>{pct(calc?.p?.a)}</td></tr>
    <tr><td>24-match + Venue8 probability</td><td>{pct(calc?.candidateP?.h)}</td><td>{pct(calc?.candidateP?.d)}</td><td>{pct(calc?.candidateP?.a)}</td></tr>
    <tr><td>Bookmaker no-vig probability</td><td>{pct(m?.h)}</td><td>{pct(m?.d)}</td><td>{pct(m?.a)}</td></tr>
    <tr><td>Chance needed at market odds</td><td>{pct(bettingValue(0,N(f.market_home_odds))?.breakEvenProbability)}</td><td>{pct(bettingValue(0,N(f.market_draw_odds))?.breakEvenProbability)}</td><td>{pct(bettingValue(0,N(f.market_away_odds))?.breakEvenProbability)}</td></tr>
    <tr><td><b>Current model price gap</b></td><td><ValueIndicator probability={calc?.p?.h} odds={f.market_home_odds}/></td><td><ValueIndicator probability={calc?.p?.d} odds={f.market_draw_odds}/></td><td><ValueIndicator probability={calc?.p?.a} odds={f.market_away_odds}/></td></tr>
    <tr><td><b>24-match + Venue8 price gap</b></td><td><ValueIndicator probability={calc?.candidateP?.h} odds={f.market_home_odds}/></td><td><ValueIndicator probability={calc?.candidateP?.d} odds={f.market_draw_odds}/></td><td><ValueIndicator probability={calc?.candidateP?.a} odds={f.market_away_odds}/></td></tr>
   </tbody></table></div>
   <div className="muted" style={{marginTop:8}}>Market: {f.market_source||"pending nearer kick-off"}{f.market_snapshot_at?` · snapshot ${dayTime(f.market_snapshot_at)}`:""}. Goal/xG overperformance cap: +{fmt(s?.goal_xg_residual_cap,1)}.{s?.candidate_calculated_at?` Research comparison calculated ${dayTime(s.candidate_calculated_at)}.`:""}</div>
  </section>)}</div>
 </>
}
