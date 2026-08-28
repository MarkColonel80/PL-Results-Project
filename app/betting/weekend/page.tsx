"use client";

import {useEffect,useMemo,useState} from "react";
import Link from "next/link";
import {supabase} from "../../../lib/supabase";

type Snapshot={home_n8:number|null;away_n8:number|null;home_n30:number|null;away_n30:number|null;home_ppg30:number|null;away_ppg30:number|null;home_vn18:number|null;away_vn18:number|null;home_vppg18:number|null;away_vppg18:number|null;home_vxgf18:number|null;home_vxga18:number|null;away_vxgf18:number|null;away_vxga18:number|null;home_vppg8:number|null;away_vppg8:number|null;home_vgf8:number|null;home_vga8:number|null;home_vxgf8:number|null;home_vxga8:number|null;away_vgf8:number|null;away_vga8:number|null;away_vxgf8:number|null;away_vxga8:number|null;goal_xg_residual_cap:number|null;home_vgf8_capped:number|null;home_vga8_capped:number|null;away_vgf8_capped:number|null;away_vga8_capped:number|null;league_home_goals:number;league_away_goals:number;league_home_xg:number;league_away_xg:number;calculated_at:string};
type Fixture={fixture_id:number;kickoff_time:string;home_team:string;away_team:string;market_home_odds:number|null;market_draw_odds:number|null;market_away_odds:number|null;market_source:string|null;market_snapshot_at:string|null;notes:string|null;betting_manual_weekend_snapshot:Snapshot|null};

const N=(v:number|null|undefined)=>v==null?null:Number(v);
const fmt=(v:number|null|undefined,d=2)=>v==null||!Number.isFinite(Number(v))?"—":Number(v).toFixed(d);
const pct=(v:number|null|undefined)=>v==null?"—":`${(v*100).toFixed(1)}%`;
const fair=(p:number|null|undefined)=>p==null||p<=0?"—":(1/p).toFixed(2);
const clamp=(v:number,min:number,max:number)=>Math.max(min,Math.min(max,v));
function trend(v8:number|null|undefined,v18:number|null|undefined,n18:number|null|undefined,lowerBetter=false){if(n18!==18||v8==null||v18==null)return"";const d=(Number(v8)-Number(v18))*(lowerBetter?-1:1);return d>.02?"↑":d<-.02?"↓":"→"}
function poisson(lambda:number,max=8){const a=[Math.exp(-lambda)];for(let i=1;i<=max;i++)a[i]=a[i-1]*lambda/i;return a}
function probs(hl:number,al:number){const hp=poisson(hl),ap=poisson(al);let h=0,d=0,a=0;for(let i=0;i<hp.length;i++)for(let j=0;j<ap.length;j++){const p=hp[i]*ap[j];if(i>j)h+=p;else if(i===j)d+=p;else a+=p}const t=h+d+a;return{h:h/t,d:d/t,a:a/t}}
function market(h:number|null,d:number|null,a:number|null){if(!h||!d||!a)return null;const x=1/h,y=1/d,z=1/a,t=x+y+z;return{h:x/t,d:y/t,a:z/t}}
function outcome(p:{h:number;d:number;a:number}){return p.h>=p.d&&p.h>=p.a?"Home":p.d>=p.a?"Draw":"Away"}
function dayTime(v:string){return new Intl.DateTimeFormat("en-GB",{weekday:"short",day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",timeZone:"Europe/London"}).format(new Date(v))}

export default function WeekendVenueReview(){
 const[rows,setRows]=useState<Fixture[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
 useEffect(()=>{(async()=>{const{data,error}=await supabase.from("betting_manual_fixtures").select("fixture_id,kickoff_time,home_team,away_team,market_home_odds,market_draw_odds,market_away_odds,market_source,market_snapshot_at,notes,betting_manual_weekend_snapshot(*)").order("kickoff_time");if(error)setError(error.message);else setRows((data||[]) as unknown as Fixture[]);setLoading(false)})()},[]);
 const cards=useMemo(()=>rows.map(f=>{const s=f.betting_manual_weekend_snapshot;const m=market(N(f.market_home_odds),N(f.market_draw_odds),N(f.market_away_odds));if(!s)return{f,s:null,m,calc:null};const full=s.home_n8===8&&s.away_n8===8;const hgf=s.home_vgf8_capped??s.home_vgf8,hga=s.home_vga8_capped??s.home_vga8,agf=s.away_vgf8_capped??s.away_vgf8,aga=s.away_vga8_capped??s.away_vga8;const ahf=s.home_vxgf8!=null&&hgf!=null?(Number(s.home_vxgf8)+Number(hgf))/2:null;const aha=s.home_vxga8!=null&&hga!=null?(Number(s.home_vxga8)+Number(hga))/2:null;const aaf=s.away_vxgf8!=null&&agf!=null?(Number(s.away_vxgf8)+Number(agf))/2:null;const aaa=s.away_vxga8!=null&&aga!=null?(Number(s.away_vxga8)+Number(aga))/2:null;let p=null,hl=null,al=null;if(ahf!=null&&aha!=null&&aaf!=null&&aaa!=null){hl=clamp(Number(s.league_home_goals)*Math.pow((ahf/Number(s.league_home_xg))*(aaa/Number(s.league_home_xg)),.8),.15,4.5);al=clamp(Number(s.league_away_goals)*Math.pow((aaf/Number(s.league_away_xg))*(aha/Number(s.league_away_xg)),.8),.15,4.5);p=probs(hl,al)}const gap=s.home_vppg8!=null&&s.away_vppg8!=null?Math.abs(Number(s.home_vppg8)-Number(s.away_vppg8)):null;const close=full&&gap!=null&&gap<=.30;const decision=!full?"Limited PL venue history":close&&p?`${outcome(p)} — adjusted venue xG tie-break`:(Number(s.home_vppg8)>Number(s.away_vppg8)?"Home — venue PPG":"Away — venue PPG");return{f,s,m,calc:{ahf,aha,aaf,aaa,hl,al,p,gap,close,decision}}}),[rows]);
 if(loading)return <p>Loading weekend review…</p>;
 if(error)return <section className="card"><b>Could not load weekend review</b><div className="negative">{error}</div></section>;
 return <>
  <div className="hero"><div><h1>Weekend venue review</h1><div className="muted">Manual early-season check: venue PPG8 decides unless the venue PPG gap is ≤ 0.30. Only then does adjusted venue xG8 break the tie.</div></div><Link href="/betting">← Betting Lab</Link></div>
  <section className="card"><b>Adjusted venue xG rule</b><div className="muted" style={{marginTop:6}}>For each of the eight venue matches, actual goals scored and conceded are capped only when they exceed that match&apos;s xG by more than 1.0 goal: capped actual = min(actual, xG + 1.0). Underperformance is left unchanged, so the capped figure can never be higher than the actual figure. Those capped actual-goal averages are then blended 50/50 with raw venue xG: adjusted xGF8 = (xGF8 + capped actual GF8) ÷ 2, with the same rule for xGA. This stops unusually flattering scorelines dominating an eight-match sample while still allowing actual goals to add information beyond xG. Overall PPG30 and venue18 PPG/xGF/xGA are diagnostic only and do not affect any calculation or pick. On full 18-match venue samples, arrows beside the venue8 PPG/xG figures show whether the last eight are better ↑, worse ↓, or broadly unchanged → versus the last 18; for xGA, lower is better. All prices below are decimal odds; bookmaker probabilities are no-vig estimates from the Oddschecker 1X2 prices.</div></section>
  <div style={{display:"grid",gap:14}}>{cards.map(({f,s,m,calc})=><section className="card" key={f.fixture_id}>
   <div style={{display:"flex",justifyContent:"space-between",gap:12,alignItems:"flex-start",flexWrap:"wrap"}}><div><div className="muted">{dayTime(f.kickoff_time)}</div><h2 style={{margin:"4px 0"}}>{f.home_team} <span className="muted">v</span> {f.away_team}</h2></div><div><b>{calc?.decision||"—"}</b>{calc?.gap!=null&&<div className="muted">Venue PPG gap {fmt(calc.gap,3)}{calc.close?" · xG tie-break active":""}</div>}</div></div>
   {!s?<p>No snapshot.</p>:<>
    <div style={{overflowX:"auto",marginTop:10}}><table><thead><tr><th>Venue review</th><th>{f.home_team}</th><th>{f.away_team}</th></tr></thead><tbody>
     <tr><td>Venue8 matches available</td><td>{s.home_n8}</td><td>{s.away_n8}</td></tr><tr><td><b>PPG8</b></td><td><b>{fmt(s.home_vppg8,3)} {trend(s.home_vppg8,s.home_vppg18,s.home_vn18)}</b></td><td><b>{fmt(s.away_vppg8,3)} {trend(s.away_vppg8,s.away_vppg18,s.away_vn18)}</b></td></tr>
     <tr><td>Venue PPG18 (comparison only)</td><td>{fmt(s.home_vppg18,3)}</td><td>{fmt(s.away_vppg18,3)}</td></tr><tr><td>Venue18 sample</td><td>{s.home_vn18==null?"—":`${s.home_vn18}/18`}</td><td>{s.away_vn18==null?"—":`${s.away_vn18}/18`}</td></tr>
     <tr><td>Overall PPG30 (diagnostic only)</td><td>{fmt(s.home_ppg30,3)}</td><td>{fmt(s.away_ppg30,3)}</td></tr><tr><td>Overall PPG sample</td><td>{s.home_n30==null?"—":`${s.home_n30}/30`}</td><td>{s.away_n30==null?"—":`${s.away_n30}/30`}</td></tr>
     <tr><td>Actual GF8</td><td>{fmt(s.home_vgf8)}</td><td>{fmt(s.away_vgf8)}</td></tr><tr><td>Capped actual GF8 (+1 xG max)</td><td>{fmt(s.home_vgf8_capped)}</td><td>{fmt(s.away_vgf8_capped)}</td></tr><tr><td>Raw xGF8</td><td>{fmt(s.home_vxgf8)} {trend(s.home_vxgf8,s.home_vxgf18,s.home_vn18)}</td><td>{fmt(s.away_vxgf8)} {trend(s.away_vxgf8,s.away_vxgf18,s.away_vn18)}</td></tr><tr><td>Raw xGF18 (comparison only)</td><td>{fmt(s.home_vxgf18)}</td><td>{fmt(s.away_vxgf18)}</td></tr><tr><td><b>Adjusted xGF8</b></td><td><b>{fmt(calc?.ahf)}</b></td><td><b>{fmt(calc?.aaf)}</b></td></tr>
     <tr><td>Actual GA8</td><td>{fmt(s.home_vga8)}</td><td>{fmt(s.away_vga8)}</td></tr><tr><td>Capped actual GA8 (+1 xG max)</td><td>{fmt(s.home_vga8_capped)}</td><td>{fmt(s.away_vga8_capped)}</td></tr><tr><td>Raw xGA8</td><td>{fmt(s.home_vxga8)} {trend(s.home_vxga8,s.home_vxga18,s.home_vn18,true)}</td><td>{fmt(s.away_vxga8)} {trend(s.away_vxga8,s.away_vxga18,s.away_vn18,true)}</td></tr><tr><td>Raw xGA18 (comparison only)</td><td>{fmt(s.home_vxga18)}</td><td>{fmt(s.away_vxga18)}</td></tr><tr><td><b>Adjusted xGA8</b></td><td><b>{fmt(calc?.aha)}</b></td><td><b>{fmt(calc?.aaa)}</b></td></tr>
    </tbody></table></div>
    {calc?.p&&<div style={{overflowX:"auto",marginTop:12}}><table><thead><tr><th>Adjusted xG match view</th><th>Home</th><th>Draw</th><th>Away</th></tr></thead><tbody><tr><td>Expected goals</td><td>{fmt(calc.hl)}</td><td>—</td><td>{fmt(calc.al)}</td></tr><tr><td>1X2 probability</td><td>{pct(calc.p.h)}</td><td>{pct(calc.p.d)}</td><td>{pct(calc.p.a)}</td></tr></tbody></table></div>}
   </>}
   <div style={{overflowX:"auto",marginTop:12}}><table><thead><tr><th>Odds comparison (decimal)</th><th>Home</th><th>Draw</th><th>Away</th></tr></thead><tbody>
    <tr><td>Our fair odds</td><td>{fair(calc?.p?.h)}</td><td>{fair(calc?.p?.d)}</td><td>{fair(calc?.p?.a)}</td></tr>
    <tr><td>Oddschecker odds</td><td>{fmt(f.market_home_odds)}</td><td>{fmt(f.market_draw_odds)}</td><td>{fmt(f.market_away_odds)}</td></tr>
    <tr><td>Our probability</td><td>{pct(calc?.p?.h)}</td><td>{pct(calc?.p?.d)}</td><td>{pct(calc?.p?.a)}</td></tr>
    <tr><td>Bookmaker no-vig probability</td><td>{pct(m?.h)}</td><td>{pct(m?.d)}</td><td>{pct(m?.a)}</td></tr>
   </tbody></table></div>
   <div className="muted" style={{marginTop:8}}>Market: {f.market_source||"—"}{f.market_snapshot_at?` · snapshot ${dayTime(f.market_snapshot_at)}`:""}. Goal/xG overperformance cap: +{fmt(s?.goal_xg_residual_cap,1)}.</div>
  </section>)}</div>
 </>
}
