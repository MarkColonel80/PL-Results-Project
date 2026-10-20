import ledgerData from "../../../data/weekend-paper-ledger.json";
import forecastScorecard from "../../../data/weekend-forecast-scorecard.json";
import {paperDecision,paperScorecard,xgOnlyDiagnostic,fragileOutcomes,venueHistoryBreakdown,type PaperLedger,type PaperFixture,type Probabilities} from "../../../lib/weekend-paper";
import {weekendReviewWarnings,venueDefenceComparison} from "../../../lib/weekend-review";

const ledger=ledgerData as unknown as PaperLedger;
const pct=(v:number|null|undefined)=>v==null?"—":`${(v*100).toFixed(1)}%`;
const when=(v:string)=>new Intl.DateTimeFormat("en-GB",{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit",timeZone:"Europe/London",timeZoneName:"short"}).format(new Date(v));
const labels={h:"Home",d:"Draw",a:"Away"};
type Fixture=PaperFixture&{home_team:string;away_team:string;market_home_odds:number|null;market_draw_odds:number|null;market_away_odds:number|null};
type Snapshot=NonNullable<Parameters<typeof xgOnlyDiagnostic>[0]>&{calculated_at:string;home_vga8:number|null;away_vga8:number|null};
type CompletedMatch={home_team:string;away_team:string;kickoff_time:string};
export function paperStatus(fixture:PaperFixture){return paperDecision(ledger.events,fixture).label}

export function PaperScorecard(){
 const score=paperScorecard(ledger);
 return <section className="card" aria-labelledby="paper-scorecard-title">
  <h2 id="paper-scorecard-title" style={{marginTop:0}}>Paper-bet scorecard</h2>
  <p>Every selection uses a hypothetical <b>1 unit</b>. Watches and passes have no stake. A round can finish with no paper selections.</p>
  <div style={{overflowX:"auto"}}><table><thead><tr><th>Recorded selections</th><th>Awaiting results</th><th>Settled</th><th>Units committed</th><th>Net result</th><th>Return on settled stakes</th></tr></thead><tbody><tr><td>{score.selections}</td><td>{score.pending}</td><td>{score.settled}</td><td>{score.staked}u</td><td>{score.settled?`${score.profit>0?"+":""}${score.profit.toFixed(2)}u`:"—"}</td><td>{score.roi==null?"—":pct(score.roi)}</td></tr></tbody></table></div>
  <p className="muted" style={{fontSize:13}}>Paper tracking starts with the 23–25 October round. Earlier conditional watchlists are excluded from these stake totals. Selection records retain the original probabilities, price and checks; results are appended after full time.</p>
  <details><summary>All published forecasts — separate scorecard</summary>
   <p className="muted">Through 20 October: {forecastScorecard.eligible} eligible forecasts from {forecastScorecard.published} published fixtures across Matchweeks 3, 4, 6 and 7. These scores cover all eligible forecasts, regardless of whether an outcome looked like value.</p>
   <div style={{overflowX:"auto"}}><table><thead><tr><th>Forecast</th><th>Mean Brier</th><th>Mean log loss</th></tr></thead><tbody>{[["Current weekend view",forecastScorecard.current],["24-match + Venue8 research",forecastScorecard.research],["Saved no-vig market",forecastScorecard.market]].map(([label,value])=>{const v=value as typeof forecastScorecard.current;return <tr key={String(label)}><td>{String(label)}</td><td>{v.brier.toFixed(4)}</td><td>{v.log_loss.toFixed(4)}</td></tr>})}</tbody></table></div>
   <p className="muted" style={{fontSize:13}}>Lower is better. Brier scores all three outcomes; log loss uses natural logarithms. <a href={forecastScorecard.source} target="_blank" rel="noreferrer">Full investigation and source records</a>.</p>
  </details>
 </section>;
}

export function PaperReview({fixture,snapshot,primary,research,matches}:{fixture:Fixture;snapshot:Snapshot|null;primary:Probabilities|null|undefined;research:Probabilities|null|undefined;matches:CompletedMatch[]|null}){
 const state=paperDecision(ledger.events,fixture);const event=state.event;const selection=event?.selection;
 const odds={h:fixture.market_home_odds,d:fixture.market_draw_odds,a:fixture.market_away_odds};
 const d8=xgOnlyDiagnostic(snapshot,8),d18=xgOnlyDiagnostic(snapshot,18);
 const warnings=weekendReviewWarnings(primary,research,odds,snapshot?.home_n8,snapshot?.away_n8);
 warnings.push(...fragileOutcomes(research,[{label:"xG-only Venue8",probabilities:d8},{label:"xG-only Venue18",probabilities:d18}],odds));
 const home=venueHistoryBreakdown(matches,fixture.home_team,true,snapshot?.home_n8??null,fixture.kickoff_time,snapshot?.calculated_at);
 const away=venueHistoryBreakdown(matches,fixture.away_team,false,snapshot?.away_n8??null,fixture.kickoff_time,snapshot?.calculated_at);
 const history=(h:typeof home)=>h?`${h.current} this season + ${h.previous} from earlier seasons (${h.total}/8)` :"History breakdown unavailable";
 const defence=(side:"home"|"away")=>{if(!snapshot)return"Unavailable";const v=venueDefenceComparison(snapshot[`${side}_n8`],snapshot[`${side}_vga8`]==null?null:Number(snapshot[`${side}_vga8`]),snapshot[`${side}_vxga8`]==null?null:Number(snapshot[`${side}_vxga8`]));return v?`${v.conceded.toFixed(1)} conceded vs ${v.xga.toFixed(1)} xGA`:"Unavailable"};
 const diagnosticRows=[{label:"Saved 24-match + Venue8 research",p:research},{label:"Current weekend probability",p:primary},{label:"Current model · xG-only Venue8",p:d8},{label:"Current model · xG-only Venue18",p:d18}];
 return <div id={`review-${fixture.fixture_id}`} style={{marginTop:14,padding:16,border:"1px solid var(--border, #d6dde5)",borderRadius:8,scrollMarginTop:72}}>
  <h3 style={{margin:"0 0 8px"}}>{state.label}</h3>
  <p style={{margin:"6px 0"}}>{event?.reason||"Awaiting a recorded paper-bet review. A positive price gap alone cannot create a selection."}</p>
  {event&&<p className="muted" style={{fontSize:13}}>Decision recorded {when(event.recorded_at)}.</p>}
  {state.issues.length>0&&<p className="negative">Paper selection blocked: {state.issues.join("; ")}.</p>}
  {state.status==="paper"&&selection&&<p><b>{labels[selection.outcome]} · 1 hypothetical unit at {selection.quote.odds.toFixed(2)}</b> with <a href={selection.quote.source_url} target="_blank" rel="noreferrer">{selection.quote.bookmaker}</a>, observed {when(selection.quote.observed_at)}. Frozen research probability {pct(selection.forecast.research[selection.outcome])}.</p>}
  <ul style={{paddingLeft:20}}>
   <li>Confirmed teams: {event?.checks?.teams.confirmed?event.checks.teams.summary:"pending — recheck the starting goalkeeper, striker and key defenders"}.</li>
   <li>Available bookmaker price: {state.status==="paper"?"recorded with the paper selection":"pending — the saved comparison price alone is not a confirmed quote"}.</li>
   <li>Team news, recovery and Europe: {event?.checks?.news&&event.checks.schedule?"review recorded":"review still required before a paper selection"}.</li>
   <li>History and sensitivity: {event?.checks?.sensitivity?event.checks.sensitivity.summary:"review the comparisons below and record any fragility"}.</li>
  </ul>
  {event?.checks&&<div style={{display:"flex",gap:12,flexWrap:"wrap"}}>{Object.entries(event.checks).map(([key,e])=><a key={key} href={e.source_url} target="_blank" rel="noreferrer">{key} evidence</a>)}</div>}
  {warnings.length>0&&<div><b>Signals to review</b><ul style={{paddingLeft:20}}>{warnings.map(w=><li key={w}>{w}</li>)}</ul></div>}
  <div style={{overflowX:"auto",marginTop:12}}><table><thead><tr><th>Venue history at forecast time</th><th>{fixture.home_team} at home</th><th>{fixture.away_team} away</th></tr></thead><tbody><tr><td>Season breakdown</td><td>{history(home)}</td><td>{history(away)}</td></tr><tr><td>Goals conceded vs xGA</td><td>{defence("home")}</td><td>{defence("away")}</td></tr></tbody></table></div>
  <details style={{marginTop:12}}><summary>Probability sensitivity and frozen decision history</summary>
   <div style={{overflowX:"auto",marginTop:10}}><table><thead><tr><th>Estimate</th><th>Home</th><th>Draw</th><th>Away</th></tr></thead><tbody>{diagnosticRows.map(r=><tr key={r.label}><td>{r.label}</td><td>{pct(r.p?.h)}</td><td>{pct(r.p?.d)}</td><td>{pct(r.p?.a)}</td></tr>)}<tr><td>Chance needed at saved odds</td>{(["h","d","a"] as const).map(k=>{const price=odds[k];return <td key={k}>{price!=null&&price>1?pct(1/price):"—"}</td>})}</tr></tbody></table></div>
   <p className="muted" style={{fontSize:13}}>The xG-only rows change the inputs of the current model for a sensitivity check. They are not validated replacements for the research forecast or a confidence interval. Venue18 requires a full 18-match sample for both teams; — means unavailable. Agreement between estimates is not independent confirmation. News and Europe do not change these probabilities.</p>
   {snapshot&&<p className="muted" style={{fontSize:13}}>Current-model inputs saved {when(snapshot.calculated_at)}. Conceding fewer goals than xGA may reflect saving, finishing or variation rather than repeatable defensive strength.</p>}
   <ol style={{paddingLeft:20}}>{ledger.events.filter(e=>e.fixture_id===fixture.fixture_id&&Date.parse(e.kickoff_time)===Date.parse(fixture.kickoff_time)&&Date.parse(e.recorded_at)<=Date.now()).map(e=><li key={e.id}>{when(e.recorded_at)} · {e.status==="paper"?"Paper record":e.status==="pass"?"Pass":"Watch"}: {e.reason}</li>)}</ol>
  </details>
 </div>;
}
