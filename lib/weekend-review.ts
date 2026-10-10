type Probabilities = {h:number;d:number;a:number};
type Odds = {h:number|null;d:number|null;a:number|null};

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
