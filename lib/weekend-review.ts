type Probabilities = {h:number;d:number;a:number};
type Odds = {h:number|null;d:number|null;a:number|null};

export const WEEKEND_NEWS_MARKER="\nWEEKEND_NEWS_JSON:";
export type ReviewedWeekendNews={
 checkedAt:string;home:string;away:string;schedule:string;teams:string;
 availability:string[];sources:{label:string;url:string}[];
};

// Keep legacy fixture provenance intact; only display a validated news record.
export function parseWeekendNews(notes:string|null|undefined):ReviewedWeekendNews|null{
 if(!notes||notes.length>40000)return null;
 const at=notes.lastIndexOf(WEEKEND_NEWS_MARKER);
 if(at<0)return null;
 try{
  const value:unknown=JSON.parse(notes.slice(at+WEEKEND_NEWS_MARKER.length));
  if(!value||typeof value!=="object"||Array.isArray(value))return null;
  const n=value as Record<string,unknown>;
  const strings=["checkedAt","home","away","schedule","teams"] as const;
  if(strings.some(k=>typeof n[k]!=="string"||(n[k] as string).length>2000))return null;
  if(!Number.isFinite(Date.parse(n.checkedAt as string)))return null;
  if(!Array.isArray(n.availability)||n.availability.length>4||
     n.availability.some(x=>typeof x!=="string"||x.length>3000))return null;
  if(!Array.isArray(n.sources)||n.sources.length>10)return null;
  const sources:{label:string;url:string}[]=[];
  for(const entry of n.sources){
   if(!entry||typeof entry!=="object"||Array.isArray(entry))return null;
   const s=entry as Record<string,unknown>;
   if(typeof s.label!=="string"||s.label.length>100||typeof s.url!=="string"||s.url.length>1000)return null;
   const url=new URL(s.url);
   if(url.protocol!=="https:"||url.username||url.password)return null;
   sources.push({label:s.label,url:url.href});
  }
  return{checkedAt:n.checkedAt as string,home:n.home as string,away:n.away as string,
   schedule:n.schedule as string,teams:n.teams as string,availability:n.availability as string[],sources};
 }catch{return null;}
}

function positiveValue(probability:number,odds:number|null):boolean|null{
 if(!Number.isFinite(probability)||probability<0||probability>1||
    odds==null||!Number.isFinite(odds)||odds<=1)return null;
 return (probability-1/odds)*100>1e-9;
}

// These are review prompts, never probability adjustments or betting approval.
export function weekendReviewWarnings(
 primary:Probabilities|null|undefined,
 comparison:Probabilities|null|undefined,
 odds:Odds,
 homeMatches:number|null|undefined,
 awayMatches:number|null|undefined,
):string[]{
 if(homeMatches==null||awayMatches==null||homeMatches<4||awayMatches<4){
  return ["Limited venue history — no model bet assessment"];
 }
 const warnings:string[]=[];
 if(homeMatches<8||awayMatches<8)warnings.push("Partial venue history — fewer than 8 matches for at least one team");
 if(primary&&comparison){
  const labels={h:"Home",d:"Draw",a:"Away"};
  for(const key of ["h","d","a"] as const){
   const current=positiveValue(primary[key],odds[key]);
   const research=positiveValue(comparison[key],odds[key]);
   if(current!=null&&research!=null&&current!==research){
    warnings.push(`${labels[key]} price — the two forecasts disagree about positive value`);
   }
  }
 }
 return warnings;
}

export function venueDefenceComparison(
 matches:number|null|undefined,
 concededPerMatch:number|null|undefined,
 xgaPerMatch:number|null|undefined,
):{matches:number;conceded:number;xga:number}|null{
 if(matches==null||!Number.isInteger(matches)||matches<1||matches>8||
    concededPerMatch==null||xgaPerMatch==null||
    !Number.isFinite(concededPerMatch)||!Number.isFinite(xgaPerMatch)||
    concededPerMatch<0||xgaPerMatch<0)return null;
 return{matches,conceded:matches*concededPerMatch,xga:matches*xgaPerMatch};
}
