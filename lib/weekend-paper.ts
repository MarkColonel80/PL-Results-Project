export type Probabilities={h:number;d:number;a:number};
export type PaperFixture={fixture_id:number;kickoff_time:string;home_team?:string;away_team?:string};
export type Evidence={checked_at:string;summary:string;source_url:string};
export type PaperEvent={
 id:string;fixture_id:number;kickoff_time:string;recorded_at:string;status:"watch"|"pass"|"paper";reason:string;
 selection?:{outcome:"h"|"d"|"a";stake_units:number;quote:{bookmaker:string;odds:number;observed_at:string;source_url:string;available:boolean};
 forecast:{model_version:string;current_model_version:string;calculated_at:string;home_n8:number;away_n8:number;research:Probabilities;current:Probabilities}};
 checks?:{teams:Evidence&{confirmed:boolean};news:Evidence;schedule:Evidence;sensitivity:Evidence};
};
export type PaperSettlement={decision_id:string;recorded_at:string;completed_at:string;finished:boolean;home_score:number;away_score:number;source_url:string};
export type PaperLedger={version:number;mode:string;unit_stake:number;fixtures:PaperFixture[];events:PaperEvent[];settlements:PaperSettlement[]};
const time=(s:string|undefined)=>s?Date.parse(s):NaN;
const https=(s:string|undefined)=>{try{const u=new URL(s||"");return u.protocol==="https:"&&!u.username&&!u.password}catch{return false}};
const validProbs=(p:Probabilities|undefined)=>!!p&&[p.h,p.d,p.a].every(x=>Number.isFinite(x)&&x>=0&&x<=1)&&Math.abs(p.h+p.d+p.a-1)<1e-6;

// A price gap cannot promote a watch. A paper record must contain pre-match evidence.
export function paperEventIssues(event:PaperEvent,fixture:PaperFixture,now=Date.now()):string[]{
 const issues:string[]=[];const at=time(event.recorded_at);const kickoff=time(fixture.kickoff_time);
 if(event.fixture_id!==fixture.fixture_id||time(event.kickoff_time)!==kickoff)issues.push("Fixture identity has changed");
 if(!Number.isFinite(at)||!Number.isFinite(kickoff)||at>=kickoff||at>now)issues.push("Decision must be recorded before kick-off");
 if(!event.reason?.trim())issues.push("Decision reason missing");
 if(event.status!=="paper")return issues;
 const selection=event.selection;const quote=selection?.quote;const forecast=selection?.forecast;
 if(!selection||!["h","d","a"].includes(selection.outcome)||selection.stake_units!==1)issues.push("Record an outcome and a one-unit paper stake");
 if(!quote?.available||!quote.bookmaker?.trim()||!https(quote.source_url)||!Number.isFinite(quote.odds)||quote.odds<=1||!Number.isFinite(time(quote.observed_at))||time(quote.observed_at)>at)issues.push("Available named-bookmaker quote missing");
 if(!forecast?.model_version?.trim()||!forecast.current_model_version?.trim()||!validProbs(forecast.research)||!validProbs(forecast.current)||!Number.isFinite(time(forecast.calculated_at))||time(forecast.calculated_at)>at)issues.push("Frozen forecasts missing");
 if(!forecast||!Number.isInteger(forecast.home_n8)||!Number.isInteger(forecast.away_n8)||forecast.home_n8<4||forecast.away_n8<4||forecast.home_n8>8||forecast.away_n8>8)issues.push("Minimum venue history not met");
 if(selection&&quote&&forecast&&validProbs(forecast.research)&&["h","d","a"].includes(selection.outcome)&&forecast.research[selection.outcome]<=1/quote.odds)issues.push("No positive price gap in the recorded research forecast");
 const labels={teams:"Confirmed teams",news:"Team news",schedule:"Recovery and Europe",sensitivity:"History and sensitivity"};
 for(const key of ["teams","news","schedule","sensitivity"] as const){
  const evidence=event.checks?.[key];
  if(!evidence?.summary?.trim()||!https(evidence.source_url)||!Number.isFinite(time(evidence.checked_at))||time(evidence.checked_at)>at||(key==="teams"&&!event.checks?.teams.confirmed))issues.push(`${labels[key]} check pending`);
 }
 return issues;
}

export function paperDecision(events:PaperEvent[],fixture:PaperFixture,now=Date.now()){
 const matching=events.filter(e=>e.fixture_id===fixture.fixture_id&&time(e.kickoff_time)===time(fixture.kickoff_time)&&time(e.recorded_at)<=now).sort((a,b)=>time(a.recorded_at)-time(b.recorded_at));
 // Freeze the first valid selection. A later pass cannot erase its stake or loss.
 const selected=matching.find(e=>e.status==="paper"&&paperEventIssues(e,fixture,now).length===0);
 if(selected)return{status:"paper" as const,label:"Paper selection · 1 unit",event:selected,issues:[] as string[]};
 const valid=matching.filter(e=>(e.status==="watch"||e.status==="pass")&&paperEventIssues(e,fixture,now).length===0);const last=valid.at(-1);
 const blocked=matching.filter(e=>e.status==="paper").at(-1);
 return{status:last?.status??"watch",label:last?.status==="pass"?"Pass · no paper stake":"Watch · no paper stake",event:last,issues:blocked?paperEventIssues(blocked,fixture,now):[]};
}

export function paperScorecard(ledger:PaperLedger,now=Date.now()){
 const selections=ledger.fixtures.flatMap(f=>{const d=paperDecision(ledger.events,f,now);return d.status==="paper"&&d.event?.selection?[{fixture:f,event:d.event}]:[]});
 let settled=0,wins=0,profit=0;
 for(const {fixture,event} of selections){
  const result=ledger.settlements.filter(s=>s.decision_id===event.id&&s.finished&&Number.isInteger(s.home_score)&&s.home_score>=0&&Number.isInteger(s.away_score)&&s.away_score>=0&&https(s.source_url)&&time(s.completed_at)>time(fixture.kickoff_time)&&time(s.recorded_at)>=time(s.completed_at)&&time(s.recorded_at)<=now).sort((a,b)=>time(a.recorded_at)-time(b.recorded_at))[0];
  if(!result)continue;
  const outcome=result.home_score>result.away_score?"h":result.home_score===result.away_score?"d":"a";
  const won=event.selection!.outcome===outcome;settled++;if(won)wins++;profit+=won?event.selection!.quote.odds-1:-1;
 }
 return{selections:selections.length,settled,pending:selections.length-settled,wins,staked:selections.length,settledStake:settled,profit,roi:settled?profit/settled:null};
}

type VenueSnapshot={home_n8:number|null;away_n8:number|null;home_vn18:number|null;away_vn18:number|null;
 home_vxgf8:number|null;home_vxga8:number|null;away_vxgf8:number|null;away_vxga8:number|null;
 home_vxgf18:number|null;home_vxga18:number|null;away_vxgf18:number|null;away_vxga18:number|null;
 league_home_goals:number;league_away_goals:number;league_home_xg:number;league_away_xg:number};
function poissonProbabilities(h:number,a:number):Probabilities{
 const hp=[Math.exp(-h)],ap=[Math.exp(-a)];for(let i=1;i<=8;i++){hp.push(hp[i-1]*h/i);ap.push(ap[i-1]*a/i)}
 let ph=0,pd=0,pa=0;for(let i=0;i<=8;i++)for(let j=0;j<=8;j++){const p=hp[i]*ap[j];if(i>j)ph+=p;else if(i===j)pd+=p;else pa+=p}
 const total=ph+pd+pa;return{h:ph/total,d:pd/total,a:pa/total};
}
// Diagnostics of the existing current-model architecture, never replacement forecasts.
export function xgOnlyDiagnostic(s:VenueSnapshot|null,window:8|18):Probabilities|null{
 if(!s)return null;
 const hn=window===8?s.home_n8:s.home_vn18,an=window===8?s.away_n8:s.away_vn18;
 if(hn==null||an==null||hn<(window===8?4:18)||an<(window===8?4:18))return null;
 const values=window===8?[s.home_vxgf8,s.home_vxga8,s.away_vxgf8,s.away_vxga8]:[s.home_vxgf18,s.home_vxga18,s.away_vxgf18,s.away_vxga18];
 if(values.some(x=>x==null||!Number.isFinite(Number(x))||Number(x)<0))return null;
 if(![s.league_home_goals,s.league_away_goals,s.league_home_xg,s.league_away_xg].every(x=>Number.isFinite(Number(x))&&Number(x)>0))return null;
 const [hf,ha,af,aa]=values.map(Number);const clamp=(v:number)=>Math.max(.15,Math.min(4.5,v));
 return poissonProbabilities(clamp(Number(s.league_home_goals)*((hf/Number(s.league_home_xg))*(aa/Number(s.league_home_xg)))**.8),clamp(Number(s.league_away_goals)*((af/Number(s.league_away_xg))*(ha/Number(s.league_away_xg)))**.8));
}
export function fragileOutcomes(reference:Probabilities|null|undefined,alternatives:{label:string;probabilities:Probabilities|null}[],odds:{h:number|null;d:number|null;a:number|null}){
 const flags:string[]=[];if(!reference)return flags;
 for(const key of ["h","d","a"] as const){const price=odds[key];if(price==null||!Number.isFinite(price)||price<=1||reference[key]<=1/price)continue;
  for(const alt of alternatives)if(alt.probabilities&&alt.probabilities[key]<=1/price)flags.push(`${{h:"Home",d:"Draw",a:"Away"}[key]} gap disappears in ${alt.label}`);
 }
 return flags;
}
export function venueHistoryBreakdown(matches:{home_team:string;away_team:string;kickoff_time:string}[]|null,team:string,wasHome:boolean,total:number|null,kickoff:string,calculatedAt:string|undefined){
 if(!matches||total==null||!Number.isInteger(total)||total<0||total>8||!Number.isFinite(time(calculatedAt)))return null;
 const cutoff=Math.min(time(kickoff),time(calculatedAt));const current=Math.min(total,matches.filter(m=>(wasHome?m.home_team:m.away_team)===team&&time(m.kickoff_time)<cutoff).length);
 return{total,current,previous:total-current};
}

// Used before publishing a later ledger: original decisions/results are append-only.
export function ledgerPrefixUnchanged(before:PaperLedger,after:PaperLedger):boolean{
 const same=(a:unknown,b:unknown):boolean=>{
  if(a===b)return true;
  if(Array.isArray(a)&&Array.isArray(b))return a.length===b.length&&a.every((v,i)=>same(v,b[i]));
  if(a&&b&&typeof a==="object"&&typeof b==="object"){
   const aa=a as Record<string,unknown>,bb=b as Record<string,unknown>;const keys=Object.keys(aa);
   return keys.length===Object.keys(bb).length&&keys.every(k=>Object.hasOwn(bb,k)&&same(aa[k],bb[k]));
  }
  return false;
 };
 return before.version===after.version&&before.mode===after.mode&&before.unit_stake===after.unit_stake&&
  before.events.every((e,i)=>same(e,after.events[i]))&&before.settlements.every((e,i)=>same(e,after.settlements[i]))&&
  before.fixtures.every((e,i)=>same(e,after.fixtures[i]));
}
