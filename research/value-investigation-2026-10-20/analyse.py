"""Read-only model/market investigation, strict historical replay and fixed tests."""
import json,math,csv
from collections import Counter,defaultdict
from datetime import datetime,timedelta
from pathlib import Path
import numpy as np

ROOT=Path(__file__).parent
ALIASES={'Bournemouth':'AFC Bournemouth','Brighton':'Brighton & Hove Albion','Cardiff':'Cardiff City','Huddersfield':'Huddersfield Town','Leeds':'Leeds United','Leicester':'Leicester City','Luton Town':'Luton','Man City':'Manchester City','Man United':'Manchester United','Man Utd':'Manchester United','Manchester Utd':'Manchester United','Newcastle':'Newcastle United',"Nott'm Forest":'Nottingham Forest','Norwich':'Norwich City','Sheffield Utd':'Sheffield United','Spurs':'Tottenham Hotspur','Tottenham':'Tottenham Hotspur','Ipswich':'Ipswich Town','West Brom':'West Bromwich Albion','West Ham':'West Ham United','Wolves':'Wolverhampton Wanderers'}
def canon(s):return ALIASES.get(s,s)
def load(name):return json.loads((ROOT/name).read_text())
def winner(h,a):return 0 if h>a else 1 if h==a else 2
def probs(h,a,n=10):
 hp=[math.exp(-h)];ap=[math.exp(-a)]
 for i in range(1,n+1):hp.append(hp[-1]*h/i);ap.append(ap[-1]*a/i)
 ps=[0.,0.,0.]
 for i,ph in enumerate(hp):
  for j,pa in enumerate(ap):ps[0 if i>j else 1 if i==j else 2]+=ph*pa
 return [p/sum(ps) for p in ps]
def replay(r,prefix):
 lh,la=r[prefix+'_lhome'],r[prefix+'_laway'];lm=(lh+la)/2
 def shrink(side,x,g):
  n=r[side+'n24'];return ((.65*r[side+x+'24']+.35*r[side+g+'24'])*n+4*lm)/(n+4)
 ha,hd=shrink('h','xgf','cgf'),shrink('h','xga','cga');aa,ad=shrink('a','xgf','cgf'),shrink('a','xga','cga')
 h=max(.15,min(4.5,math.sqrt(lh*math.sqrt(r['hvatt']*r['avdef']))*max(.05,(ha/lm)*(ad/lm))**.75))
 a=max(.15,min(4.5,math.sqrt(la*math.sqrt(r['avatt']*r['hvdef']))*max(.05,(aa/lm)*(hd/lm))**.75))
 return [h,a],probs(h,a)
def market(odds):
 q=[1/o for o in odds];return [p/sum(q) for p in q]
def scores(p,y):
 p=np.asarray(p);y=np.asarray(y);one=np.eye(3)[y]
 return np.sum((p-one)**2,axis=1),-np.log(p[np.arange(len(p)),y])
def metrics(p,y):
 b,l=scores(p,y);return {'n':len(y),'brier':float(np.mean(b)),'log_loss':float(np.mean(l)),'accuracy':float(np.mean(np.argmax(p,axis=1)==y))}
def calibration(p,y):
 p=np.asarray(p);actual=np.eye(3)[y];bins=[]
 for low,high in [(0,.2),(.2,.4),(.4,.6),(.6,.8),(.8,1.000001)]:
  mask=(p>=low)&(p<high)
  if mask.any():bins.append({'low':low,'high':min(high,1),'n':int(mask.sum()),'predicted':float(p[mask].mean()),'observed':float(actual[mask].mean())})
 return bins
def selection(rows,key='p',when='close',rule='all_positive'):
 selections=[]
 for r in rows:
  for i,(prob,o) in enumerate(zip(r[key],r[when+'_odds'])):
   gap=prob-1/o
   if gap<=1e-10:continue
   if rule=='gap_5pp' and gap<.05:continue
   if rule=='odds_at_most4' and o>4:continue
   if rule=='odds_above4' and o<=4:continue
   selections.append({'match_id':r['match_id'],'season':r['season'],'outcome':i,'prob':prob,'market_prob':r[when+'_market'][i],'odds':o,'won':i==r['y'],'expected':prob*o-1,'profit':o-1 if i==r['y'] else -1})
 if not selections:return {'n':0,'matches':0}
 return {'n':len(selections),'matches':len({r['match_id'] for r in selections}),'wins':sum(r['won'] for r in selections),'roi':sum(r['profit'] for r in selections)/len(selections),'profit':sum(r['profit'] for r in selections),'expected_roi':sum(r['expected'] for r in selections)/len(selections),'expected_wins':sum(r['prob'] for r in selections),'observed_win_rate':sum(r['won'] for r in selections)/len(selections),'mean_probability':sum(r['prob'] for r in selections)/len(selections),'mean_market_probability':sum(r['market_prob'] for r in selections)/len(selections),'outcomes':dict(Counter('HDA'[r['outcome']] for r in selections))}
def sigmoid_softmax(logits):
 e=np.exp(logits-logits.max(axis=1,keepdims=True));return e/e.sum(axis=1,keepdims=True)
def objective(theta,lp,y,derivatives=False):
 x=np.zeros((len(lp),3,3));x[:,:,0]=lp;x[:,0,1]=1;x[:,1,2]=1
 q=sigmoid_softmax(np.einsum('nki,i->nk',x,theta));delta=theta-np.array([1.,0.,0.]);loss=float(-np.log(q[np.arange(len(q)),y]).sum()+.5*delta@delta)
 if not derivatives:return loss
 mu=np.einsum('nk,nki->ni',q,x);grad=np.einsum('nk,nki->i',q-np.eye(3)[y],x)+delta
 h=np.einsum('nk,nki,nkj->ij',q,x,x)-mu.T@mu+np.eye(3)
 return loss,grad,h
def calibrate_fit(p,y):
 lp=np.log(np.asarray(p));y=np.asarray(y);theta=np.array([1.,0.,0.]);converged=False
 for it in range(100):
  loss,g,h=objective(theta,lp,y,True)
  if np.linalg.norm(g)<1e-7:converged=True;break
  step=np.linalg.solve(h,g);scale=1.
  for j in range(35):
   candidate=theta-scale*step;candidate[0]=np.clip(candidate[0],.25,4);candidate[1:]=np.clip(candidate[1:],-3,3)
   if objective(candidate,lp,y)<loss:break
   scale*=.5
  else:converged=np.linalg.norm(g)<1e-5;break
  if np.max(np.abs(candidate-theta))<1e-9:theta=candidate;converged=True;break
  theta=candidate
 return theta,{'iterations':it+1,'converged':bool(converged),'parameters':theta.tolist()}
def calibrate_predict(p,theta):
 logits=np.log(np.asarray(p))*theta[0];logits[:,0]+=theta[1];logits[:,1]+=theta[2];return sigmoid_softmax(logits)
def bootstrap_difference(rows,p1,p2,n=2000):
 y=np.array([r['y'] for r in rows]);b1,l1=scores(p1,y);b2,l2=scores(p2,y);groups=defaultdict(list)
 for i,r in enumerate(rows):
  dt=datetime.fromisoformat(r['kickoff_time']);week=(dt.date()-timedelta(days=dt.weekday())).isoformat();groups[week].append(i)
 idxs=[np.array(v) for v in groups.values()];rng=np.random.default_rng(20261020);bd=[];ld=[]
 for _ in range(n):
  ix=np.concatenate([idxs[j] for j in rng.integers(0,len(idxs),len(idxs))]);bd.append(float((b1[ix]-b2[ix]).mean()));ld.append(float((l1[ix]-l2[ix]).mean()))
 return {'delta_brier':float((b1-b2).mean()),'brier_95pct_week_bootstrap':np.quantile(bd,[.025,.975]).tolist(),'delta_log_loss':float((l1-l2).mean()),'log_loss_95pct_week_bootstrap':np.quantile(ld,[.025,.975]).tolist(),'weeks':len(idxs)}

def roi_uncertainty(rows,n=2000):
 groups=defaultdict(lambda:[0.,0])
 for r in rows:
  dt=datetime.fromisoformat(r['kickoff_time']);week=(dt.date()-timedelta(days=dt.weekday())).isoformat()
  for i,(p,o) in enumerate(zip(r['p'],r['close_odds'])):
   if p>1/o:
    groups[week][0]+=o-1 if i==r['y'] else -1;groups[week][1]+=1
 values=np.array(list(groups.values()));rng=np.random.default_rng(20261020);draws=[]
 for _ in range(n):
  v=values[rng.integers(0,len(values),len(values))].sum(axis=0);draws.append(float(v[0]/v[1]))
 return {'roi_95pct_week_bootstrap':np.quantile(draws,[.025,.975]).tolist(),'weeks':len(values),'draws':n,'seed':20261020}

rows=[];mapping=[];replay_max_error=0.
seasons=['2019/20','2020/21','2021/22','2022/23','2023/24','2024/25','2025/26']
for season in seasons:
 d=load('historical-'+season.replace('/','-')+'.json');strict={r['match_id']:{k:(float(v) if k not in ('match_id','season','kickoff_time') and v is not None else v) for k,v in r.items()} for r in load('strict-inputs-'+season.replace('/','-')+'.json')};assert d['canonical_mismatches']==0
 year=int(season[:4]);tag=f'{year%100:02}{(year+1)%100:02}';source={}
 for raw in csv.DictReader((ROOT/'football-data'/f'{tag}.csv').open(encoding='utf-8-sig')):
  date=datetime.strptime(raw['Date'],'%d/%m/%Y').date().isoformat();source[(date,canon(raw['HomeTeam']),canon(raw['AwayTeam']))]=raw
 lookup=defaultdict(list)
 for o in d['odds']:
  raw=source[(o['source_match_date'][:10],canon(o['source_home_team']),canon(o['source_away_team']))]
  if o['home_score'] is not None:assert int(o['home_score'])==int(raw['FTHG']) and int(o['away_score'])==int(raw['FTAG'])
  o['home_score'],o['away_score']=int(raw['FTHG']),int(raw['FTAG'])
  key=(o['season'],o['source_match_date'][:10],canon(o['source_home_team']),canon(o['source_away_team']),int(o['home_score']),int(o['away_score']));lookup[key].append(o)
 for f in d['forecasts']:
  key=(season,f['kickoff_time'][:10],canon(f['home_team']),canon(f['away_team']),f['hg'],f['ag']);candidates=lookup[key]
  if len(candidates)!=1:mapping.append({'id':f['match_id'],'candidates':len(candidates),'key':key});continue
  o=candidates[0];assert o['match_id'] is None or o['match_id']==f['match_id'];r={**f,**strict[f['match_id']]};cl,cp=replay(r,'cached');sl,sp=replay(r,'strict');cached=[f['no_ppg_home_prob'],f['no_ppg_draw_prob'],f['no_ppg_away_prob']]
  err=max(abs(a-b) for a,b in zip(cl,[f['no_ppg_home_lambda'],f['no_ppg_away_lambda']]))+max(abs(a-b) for a,b in zip(cp,cached));replay_max_error=max(replay_max_error,err);assert err<1e-10,(f['match_id'],err)
  r.update(p=sp,cached_p=cached,strict_lambdas=sl,y=winner(f['hg'],f['ag']))
  for when in ['open','close']:
   odds=[o[when+'_'+s+'_avg'] for s in ['home','draw','away']];assert all(x is not None and x>1 for x in odds);r[when+'_odds']=odds;r[when+'_market']=market(odds)
  rows.append(r)
assert not mapping,{'unmatched':len(mapping),'examples':mapping[:5]}
assert len(rows)==1673
dev=[r for r in rows if r['season']<'2025/26'];stress=[r for r in rows if r['season']=='2025/26']
def summary(sample):
 y=[r['y'] for r in sample];p=np.array([r['p'] for r in sample]);m=np.array([r['close_market'] for r in sample]);cached=np.array([r['cached_p'] for r in sample]);s={'n':len(sample),'raw_strict':metrics(p,y),'cached':metrics(cached,y),'market':metrics(m,y),'blends':{},'selection':{},'calibration':{'raw':calibration(p,y),'market':calibration(m,y)}}
 for w in [.25,.5,.75]:s['blends'][str(w)]=metrics(w*p+(1-w)*m,y)
 for when in ['open','close']:
  s['selection'][when]={rule:selection(sample,when=when,rule=rule) for rule in ['all_positive','gap_5pp','odds_at_most4','odds_above4']}
 return s
out={'historical_mapping':{'forecasts':len(rows),'matched_unique':len(rows),'unmatched':mapping,'cached_replay_max_error':replay_max_error,'same_kickoff_contamination':sum(r['same_kickoff_earlier_ids']>0 for r in rows)},'development':summary(dev),'stress_2025_26':summary(stress),'by_season':{s:summary([r for r in rows if r['season']==s]) for s in seasons}}
walk=[];folds=[]
for season in seasons[1:]:
 train=[r for r in rows if r['season']<season];test=[r for r in rows if r['season']==season];theta,info=calibrate_fit([r['p'] for r in train],[r['y'] for r in train]);assert info['converged'],(season,info)
 calibrated=calibrate_predict([r['p'] for r in test],theta)
 for r,p in zip(test,calibrated):r['calibrated']=p.tolist()
 y=[r['y'] for r in test];folds.append({'test_season':season,'training_matches':len(train),'fit':info,'raw':metrics([r['p'] for r in test],y),'calibrated':metrics(calibrated,y),'market':metrics([r['close_market'] for r in test],y),'calibrated_value':selection(test,key='calibrated')})
 if season<'2025/26':walk.extend(test)
out['expanding_season_folds']=folds
out['roi_uncertainty']={'development':roi_uncertainty(dev),'stress_2025_26':roi_uncertainty(stress)}
y=[r['y'] for r in walk];p=np.array([r['p'] for r in walk]);m=np.array([r['close_market'] for r in walk]);c=np.array([r['calibrated'] for r in walk]);out['walk_forward_2020_25']={'raw':metrics(p,y),'market':metrics(m,y),'calibrated':metrics(c,y),'calibration_vs_raw':bootstrap_difference(walk,c,p),'raw_vs_market':bootstrap_difference(walk,p,m),'blend25model_vs_market':bootstrap_difference(walk,.25*p+.75*m,m),'calibrated_value':selection(walk,key='calibrated')}

# Check the calibration derivatives numerically before accepting fitted results.
lp=np.log(p[:9]);yy=np.array(y[:9]);theta=np.array([1.1,.1,-.05]);v,g,h=objective(theta,lp,yy,True);eps=1e-5;numeric=np.array([(objective(theta+np.eye(3)[i]*eps,lp,yy)-objective(theta-np.eye(3)[i]*eps,lp,yy))/(2*eps) for i in range(3)]);assert max(abs(g-numeric))<1e-6

live=load('frozen-inputs.json');actual=live['results'];frozen=[];audit=[]
for f in live['saved']:
 matches=[m for m in actual if m['kickoff_time'][:10]==f['kickoff_time'][:10] and m['home_team']==f['home_team'] and m['away_team']==f['away_team']];assert len(matches)==1,(f['fixture_id'],matches);a=matches[0];s=f['snapshot'];eligible=min(s['home_n8'],s['away_n8'])>=4;rp=[s['candidate_home_prob'],s['candidate_draw_prob'],s['candidate_away_prob']];ko=datetime.fromisoformat(f['kickoff_time']);issues=[]
 if eligible:
  assert all(x is not None and 0<=x<=1 for x in rp) and abs(sum(rp)-1)<1e-10
  for field in ['calculated_at','candidate_calculated_at']:
   if datetime.fromisoformat(s[field])>=ko:issues.append(field+' after kickoff')
 if datetime.fromisoformat(f['market_snapshot_at'])>=ko:issues.append('price after kickoff')
 audit.append({'fixture_id':f['fixture_id'],'eligible':eligible,'issues':issues,'round':a['gameweek']})
 if not eligible:continue
 def clamp(x):return max(.15,min(4.5,x))
 hl=clamp(s['league_home_goals']*((.5*(s['home_vxgf8']+s['home_vgf8_capped'])/s['league_home_xg'])*(.5*(s['away_vxga8']+s['away_vga8_capped'])/s['league_home_xg']))**.8);al=clamp(s['league_away_goals']*((.5*(s['away_vxgf8']+s['away_vgf8_capped'])/s['league_away_xg'])*(.5*(s['home_vxga8']+s['home_vga8_capped'])/s['league_away_xg']))**.8)
 odds=[f['market_home_odds'],f['market_draw_odds'],f['market_away_odds']]
 r={'match_id':a['match_id'],'fixture_id':f['fixture_id'],'season':'2026/27','round':a['gameweek'],'kickoff_time':f['kickoff_time'],'home_team':f['home_team'],'away_team':f['away_team'],'p':rp,'primary':probs(hl,al,8),'close_odds':odds,'open_odds':odds,'close_market':market(odds),'open_market':market(odds),'y':winner(a['home_score'],a['away_score']),'result':[a['home_score'],a['away_score']],'issues':issues}
 frozen.append(r)
valid=[r for r in frozen if not r['issues']]
def frozen_summary(sample):
 if not sample:return {}
 y=[r['y'] for r in sample];return {'n':len(sample),'research':metrics([r['p'] for r in sample],y),'primary':metrics([r['primary'] for r in sample],y),'market':metrics([r['close_market'] for r in sample],y),'research_selection':{rule:selection(sample,rule=rule) for rule in ['all_positive','gap_5pp','odds_at_most4','odds_above4']},'primary_selection':selection(sample,key='primary')}
out['frozen_2026']={'audit':audit,'valid':frozen_summary(valid),'by_round':{str(g):frozen_summary([r for r in valid if r['round']==g]) for g in sorted({r['round'] for r in valid})},'probability_calibration':{'research':calibration([r['p'] for r in valid],[r['y'] for r in valid]),'market':calibration([r['close_market'] for r in valid],[r['y'] for r in valid])},'all_eligible':frozen}
out['latest_two_loss_probability_under_model']=(1-.303120186140758)*(1-.234181321697704)
(ROOT/'results.json').write_text(json.dumps(out,indent=2)+'\n');(ROOT/'matched-historical-replays.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps({'audit':out['historical_mapping'],'frozen':out['frozen_2026']['valid'],'rounds':out['frozen_2026']['by_round'],'dev':{k:v for k,v in out['development'].items() if k not in ('calibration','selection')},'walk_forward':out['walk_forward_2020_25'],'stress':{k:v for k,v in out['stress_2025_26'].items() if k not in ('calibration','selection')}},indent=2))
