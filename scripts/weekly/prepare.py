#!/usr/bin/env python3
"""Bounded public-provider adapters. No credentials, database or model writes."""
import ast,concurrent.futures,csv,datetime as dt,hashlib,io,json,pathlib,re,time,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[2]; OUT=ROOT/'work/weekly'; OUT.mkdir(parents=True,exist_ok=True)
SEASON='2026/27'; API='https://fantasy.premierleague.com/api'
ALIASES={'Bournemouth':'AFC Bournemouth','Brighton':'Brighton & Hove Albion','Coventry':'Coventry City','Hull':'Hull City','Ipswich':'Ipswich Town','Leeds':'Leeds United','Man City':'Manchester City','Man Utd':'Manchester United','Man United':'Manchester United','Newcastle':'Newcastle United',"Nott'm Forest":'Nottingham Forest','Nott\u2019m Forest':'Nottingham Forest','Spurs':'Tottenham Hotspur','Tottenham':'Tottenham Hotspur'}
canon=lambda x:ALIASES.get(x,x)
now=lambda:dt.datetime.now(dt.timezone.utc)
stamp=lambda:now().isoformat()
date=lambda s:dt.datetime.fromisoformat(s.replace('Z','+00:00'))
evidence=[];gaps=[]
def fetch(url,optional=False,as_json=True):
 error=None
 for attempt in range(3):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'PL-Results-Project weekly research/1.0','Accept':'application/json,text/csv,text/html'})
   with urllib.request.urlopen(req,timeout=20) as res:raw=res.read(12000000)
   if len(raw)>=12000000:raise ValueError('Provider payload too large')
   evidence.append({'url':url,'fetched_at':stamp(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
   return json.loads(raw) if as_json else raw.decode('utf-8-sig')
  except Exception as e:
   error=e
   if isinstance(e,urllib.error.HTTPError) and e.code not in [429,500,502,503,504]:break
   if attempt<2:time.sleep(attempt+1)
 if optional:gaps.append(url+': '+type(error).__name__);return None
 raise RuntimeError('Essential provider failed: '+url+' ('+type(error).__name__+')')
def pool(fn,items,n=8):
 with concurrent.futures.ThreadPoolExecutor(max_workers=n) as ex:return list(ex.map(fn,items))
def match_id(h,a):return '26-27-prem-'+re.sub('[^a-z0-9]+','-',h.lower()).strip('-')+'-vs-'+re.sub('[^a-z0-9]+','-',a.lower()).strip('-')
# Reuse the repository's approved FPL point-component implementation without its client setup.
tree=ast.parse((ROOT/'scripts/update_fpl_current.py').read_text())
scope={}
for name in ['I','component_points']:
 node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name==name)
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<approved FPL components>','exec'),scope)
component_points=scope['component_points']
def native_rows(d,f,teams,players):
 g=d['general'];c=d['content'];line=c['lineup'];ps=c['playerStats'];events=c['matchFacts']['events']['events']
 h,a=teams[f['team_h']],teams[f['team_a']];mid=match_id(h,a)
 assert all(x.get('card') in ['Yellow','Red','YellowRed'] for x in events if x.get('type')=='Card'),'Unknown card source contract'
 assert g['finished'] and g['leagueId']==47 and canon(g['homeTeam']['name'])==h and canon(g['awayTeam']['name'])==a
 assert date(g['matchTimeUTCDate'])==date(f['kickoff_time'])
 assert [x['score'] for x in d['header']['teams']]==[f['team_h_score'],f['team_a_score']]
 byopta={str(e['opta_code']).removeprefix('p'):e for e in players.values() if e.get('opta_code')}
 mapid={}
 for pid,p in ps.items():
  e=byopta.get(str(p.get('optaId','')))
  if not e:raise ValueError('Unmapped permanent Opta player '+str(p.get('optaId'))+'; no name-based merge')
  mapid[str(pid)]=e
 out={'player_match_stats':[],'lineups':[],'goals':[]}
 for side,team in [('home',h),('away',a)]:
  part=line[side+'Team'];assert len(part['starters'])==11
  for starting,group in [(True,part['starters']),(False,part.get('subs',[]))]:
   for p in group:
    pid=str(p['id']);e=mapid.get(pid)
    if not e:raise ValueError('Lineup player lacks verified provider bridge')
    assert teams[e['team']]==team
    base={'season':SEASON,'gameweek':f['event'],'match_id':mid,'player_id':str(e['id']),'player_code':str(e['code']),'player_name':e['web_name'],'team_name':team}
    stats={v['key']:v['stat']['value'] for group2 in ps[pid]['stats'] for v in group2['stats'].values() if v.get('key') and 'value' in v.get('stat',{})}
    own=sum(1 for x in events if x.get('type')=='Goal' and str(x.get('playerId',x.get('player',{}).get('id')))==pid and x.get('ownGoal'))
    cards=[x for x in events if str(x.get('playerId',x.get('player',{}).get('id')))==pid]
    row={**base,'source':'fotmob_native_verified_opta','source_match_id':str(g['matchId']),'source_player_id':pid,'data_quality':'source_reported','is_starting':starting,'minutes_played':stats.get('minutes_played',0),'goals':stats.get('goals',0),'assists':stats.get('assists',0),'xg':stats.get('expected_goals'),'xa':stats.get('expected_assists'),'shots':stats.get('total_shots'),'shots_on_target':stats.get('ShotsOnTarget',0) if stats.get('total_shots') is not None else None,'chances_created':stats.get('chances_created'),'yellow_cards':sum(x.get('type')=='Card' and x.get('card') in ['Yellow','YellowRed'] for x in cards),'red_cards':sum(x.get('type')=='Card' and x.get('card') in ['Red','YellowRed'] for x in cards),'own_goals':own}
    out['player_match_stats'].append(row)
    out['lineups'].append({**base,'team_side':side,'position':{1:'GKP',2:'DEF',3:'MID',4:'FWD'}[e['element_type']],'is_starting':starting,'jersey_number':int(p['shirtNumber']) if p.get('shirtNumber') else None,'formation':part.get('formation'),'lineup_status':'fotmob_official_lineup_opta_id_verified'})
 for x in events:
  if x.get('type')!='Goal' or x.get('isPenaltyShootoutEvent'):continue
  p=mapid[str(x.get('playerId',x['player']['id']))]
  assist=x.get('assistPlayerId');ap=mapid.get(str(assist)) if assist else None
  out['goals'].append({'season':SEASON,'gameweek':f['event'],'match_id':mid,'home_team':h,'away_team':a,'minute':x['time'],'added_time':x.get('overloadTime'),'team_side':'home' if x['isHome'] else 'away','player_id':str(p['id']),'player_code':str(p['code']),'player_name':p['web_name'],'assist_player_id':str(ap['id']) if ap else None,'assist_player_code':str(ap['code']) if ap else None,'assist_player_name':ap['web_name'] if ap else None,'goal_type':x.get('goalDescription'),'home_score':x['newScore'][0],'away_score':x['newScore'][1],'incident_index':x['eventId']})
 return out
def main():
 state=json.loads((OUT/'before.json').read_text())
 b,fx,league=pool(lambda u:fetch(u),[API+'/bootstrap-static/',API+'/fixtures/','https://www.fotmob.com/api/data/leagues?id=47&ccode3=GBR&season=2026%2F2027'],3)
 teams={t['id']:canon(t['name']) for t in b['teams']}
 assert len(teams)==20 and len(fx)==380
 players={e['id']:e for e in b['elements'] if e['element_type'] in [1,2,3,4]}
 rounds=sorted(set(f['event'] for f in fx if f['event']))
 complete=[gw for gw in rounds if all(f['finished'] and f.get('finished_provisional',True) for f in fx if f['event']==gw)]
 assert complete,'No full completed round'
 gw=max(complete)
 old={m['match_id']:m for m in state['matches']}
 finished=[f for f in fx if f['finished'] and (f['event']==gw or match_id(teams[f['team_h']],teams[f['team_a']]) not in old)]
 if any(date(f['kickoff_time'])<now()-dt.timedelta(days=21) and match_id(teams[f['team_h']],teams[f['team_a']]) not in old for f in finished):raise ValueError('Missing older results need audited recovery outside the 21-day import scope')
 reviewrounds=set(f['event'] for f in finished)
 assert max(date(f['kickoff_time']) for f in finished)<now(),'Round includes future fixture'
 # Include Monday by checking the whole official event, never Saturday/Sunday alone.
 nextgw=next((r for r in rounds if r>gw and any(not f['finished'] for f in fx if f['event']==r)),None)
 upcoming=[f for f in fx if f['event']==nextgw and f['kickoff_time'] and date(f['kickoff_time'])>now()]
 assert upcoming,'No future official round'
 for f in fx:
  if f.get('started') and not f['finished'] and date(f['kickoff_time'])<now():gaps.append('Unfinished/postponed official fixture '+str(f['id'])+' remains pending')
 index={(canon(m['home']['name']),canon(m['away']['name'])):m for m in league['fixtures']['allMatches']}
 old={m['match_id']:m for m in state['matches']};rows={t:[] for t in ['matches','canonical_matches','match_source_ids','player_match_stats','lineups','goals','fpl_player_match_stats','historical_market_odds']}
 native=[]
 for f in finished:
  h,a=teams[f['team_h']],teams[f['team_a']];mid=match_id(h,a);m=index[(h,a)]
  if mid in old:
   assert [old[mid]['home_score'],old[mid]['away_score']]==[f['team_h_score'],f['team_a_score']],'Official result correction requires review'
  native.append((f,m))
 def parse(pair):
  f,m=pair;d=fetch('https://www.fotmob.com/api/data/matchDetails?matchId='+str(m['id']))
  stats=native_rows(d,f,teams,players);h,a=teams[f['team_h']],teams[f['team_a']];mid=match_id(h,a)
  match={'match_id':mid,'season':SEASON,'gameweek':f['event'],'kickoff_time':f['kickoff_time'],'home_team':h,'away_team':a,'home_score':f['team_h_score'],'away_score':f['team_a_score'],'home_formation':d['content']['lineup']['homeTeam'].get('formation'),'away_formation':d['content']['lineup']['awayTeam'].get('formation'),'match_url':'https://www.fotmob.com'+m['pageUrl']}
  return f,m,match,stats
 for f,m,match,stats in pool(parse,native,4):
  if match['match_id'] not in old:
   rows['matches'].append(match)
  rows['canonical_matches'].append({'canonical_match_id':match['match_id'],'season':SEASON,'match_date':f['kickoff_time'][:10],'home_team':match['home_team'],'away_team':match['away_team'],'home_score':match['home_score'],'away_score':match['away_score']})
  for source,sid in [('fotmob',m['id']),('fpl_fixture',SEASON+':'+str(f['id']))]:rows['match_source_ids'].append({'source':source,'source_match_id':str(sid),'canonical_match_id':match['match_id'],'season':SEASON,'mapping_method':'exact_teams_date_verified','verified':True})
  for t,rr in stats.items():rows[t].extend(rr)
 known={x['player_id']:x for x in state['identities']}
 for row in rows['player_match_stats']:
  p=known.get(row['player_id'])
  assert p and p['player_code']==row['player_code'],'New permanent FPL identity needs explicit reconciliation'
 # Official per-fixture history supports double gameweeks without assigning aggregated stats twice.
 def history(e):
  d=fetch(API+'/element-summary/'+str(e['id'])+'/');return e,[r for r in d['history'] if r['round'] in reviewrounds]
 fixturebyid={f['id']:f for f in finished};posnames={1:'GK',2:'DEF',3:'MID',4:'FWD'}
 intfields='minutes total_points goals_scored assists clean_sheets goals_conceded own_goals penalties_saved penalties_missed yellow_cards red_cards saves bonus bps defensive_contribution clearances_blocks_interceptions recoveries tackles value selected transfers_in transfers_out'.split()
 floatfields='expected_goals expected_assists expected_goal_involvements expected_goals_conceded'.split()
 for e,hist in pool(history,players.values()):
  for s in hist:
   f=fixturebyid.get(s['fixture'])
   if not f:continue
   home=bool(s['was_home']);pos=posnames[e['element_type']]
   row={'season':SEASON,'gameweek':f['event'],'fixture_id':f['id'],'player_code':str(e['code']),'player_id':str(e['id']),'player_name':e['web_name'],'team_name':teams[f['team_h'] if home else f['team_a']],'position':pos,'kickoff_time':f['kickoff_time'],'opponent_team':teams[f['team_a'] if home else f['team_h']],'was_home':home,'source':'official_fpl_api'}
   for k in intfields:row[k]=int(s[k]) if s.get(k) is not None else None
   for k in floatfields:row[k]=float(s[k]) if s.get(k) is not None else None
   row.update(component_points(s,pos,'2026-27'));assert row['points_difference']==0
   rows['fpl_player_match_stats'].append(row)
 assert set(r['fixture_id'] for r in rows['fpl_player_match_stats'])==set(fixturebyid),'Incomplete FPL round'
 closing=fetch('https://www.football-data.co.uk/mmz4281/2627/E0.csv',optional=True,as_json=False)
 if closing:
  for r in csv.DictReader(io.StringIO(closing)):
   if not r.get('Date'):continue
   d=dt.datetime.strptime(r['Date'],'%d/%m/%Y').date().isoformat()
   f=next((f for f in finished if f['kickoff_time'][:10]==d and teams[f['team_h']]==canon(r['HomeTeam']) and teams[f['team_a']]==canon(r['AwayTeam'])),None)
   if not f:continue
   assert [int(r['FTHG']),int(r['FTAG'])]==[f['team_h_score'],f['team_a_score']]
   row={'season':SEASON,'competition':'Premier League','source':'football-data.co.uk','source_match_date':d,'source_kickoff_time':r.get('Time'),'source_home_team':r['HomeTeam'],'source_away_team':r['AwayTeam'],'match_id':match_id(teams[f['team_h']],teams[f['team_a']]),'source_url':'https://www.football-data.co.uk/mmz4281/2627/E0.csv','raw_row':r}
   for prefix,source in [('open','Avg'),('close','AvgC')]:
    for outcome,label in [('home','H'),('draw','D'),('away','A')]:
     row[prefix+'_'+outcome+'_avg']=float(r[source+label]) if r.get(source+label) else None
   rows['historical_market_odds'].append(row)
 coupon=fetch('https://www.football-data.co.uk/fixtures.csv',optional=True,as_json=False)
 prices=list(csv.DictReader(io.StringIO(coupon))) if coupon else []
 euro=[]
 for lid in [42,73,10216]:
  d=fetch('https://www.fotmob.com/api/data/leagues?id='+str(lid)+'&ccode3=GBR&season=2026%2F2027',optional=True)
  if d:
   for m in d.get('fixtures',{}).get('allMatches',[]):
    at=m['status'].get('utcTime')
    if at and now()-dt.timedelta(days=2)<=date(at)<=max(date(f['kickoff_time']) for f in upcoming):
     euro.append({'home':canon(m['home']['name']),'away':canon(m['away']['name']),'kickoff':at,'source':'https://www.fotmob.com'+m['pageUrl']})
 upcomingrows=[]
 for f in upcoming:
  h,a=teams[f['team_h']],teams[f['team_a']]
  pricesfound=[p for p in prices if canon(p.get('HomeTeam'))==h and canon(p.get('AwayTeam'))==a and p.get('Date') and dt.datetime.strptime(p['Date'],'%d/%m/%Y').date().isoformat()==f['kickoff_time'][:10]]
  quote=pricesfound[0] if len(pricesfound)==1 else {}
  flags=lambda tid:[e['web_name']+': '+e['news'] for e in players.values() if e['team']==tid and e.get('news')]
  hf,af=flags(f['team_h']),flags(f['team_a'])
  es=[m for m in euro if (m['home'] in [h,a] or m['away'] in [h,a]) and date(m['kickoff'])<date(f['kickoff_time'])]
  schedule='; '.join(m['home']+' v '+m['away']+' '+m['kickoff'] for m in es) or 'No midweek fixture identified in fetched public schedules; absence is not confirmed clearance.'
  news={'checkedAt':stamp(),'home':'; '.join(hf)[:1900] or 'No FPL flags in fetched feed; fitness is not confirmed.','away':'; '.join(af)[:1900] or 'No FPL flags in fetched feed; fitness is not confirmed.','schedule':schedule[:1900]+'. Recheck minutes, injuries and rotation after Europe. No probability adjustment.','teams':'Tuesday provisional review. Confirmed XIs, executable named-bookmaker quote and latest club press conferences remain pending.','availability':[(h+' — '+('; '.join(hf) or 'No flags'))[:2900],(a+' — '+('; '.join(af) or 'No flags'))[:2900]],'sources':[{'label':'Official FPL availability','url':API+'/bootstrap-static/'},{'label':'Official FPL fixtures','url':API+'/fixtures/'}]+[{'label':'Public European fixture schedule','url':m['source']} for m in es[:6]]}
  row={'season':SEASON,'kickoff_time':f['kickoff_time'],'home_team':h,'away_team':a,'official_fixture_id':f['id'],'notes':'Official FPL fixture '+str(f['id'])+'; verified permanent fixture identity.','news':news,'market_source':'Football-Data public comparison averages; not executable quotes' if quote else None,'market_snapshot_at':stamp() if quote else None}
  for key,source in [('home','AvgH'),('draw','AvgD'),('away','AvgA')]:row['market_'+key+'_odds']=float(quote[source]) if quote.get(source) else None
  if any(row['market_'+k+'_odds'] is None for k in ['home','draw','away']):gaps.append(h+' v '+a+': current comparison prices unavailable')
  upcomingrows.append(row)
 gaps.extend(['Official club press conferences and confirmed XIs pending; FPL flags can lag announcements.','Understat/Transfermarkt historical mapping backlogs not changed by weekly worker; unresolved identities remain excluded.','European public schedules require official club/UEFA confirmation before any paper selection.'])
 result={'checked_at':stamp(),'reviewed_gameweek':gw,'next_gameweek':nextgw,'completed':[{'official_fixture_id':f['id'],'gameweek':f['event'],'match_id':match_id(teams[f['team_h']],teams[f['team_a']]),'home_team':teams[f['team_h']],'away_team':teams[f['team_a']],'kickoff_time':f['kickoff_time'],'home_score':f['team_h_score'],'away_score':f['team_a_score'],'finished':True} for f in finished],'imports':rows,'upcoming':upcomingrows,'evidence':evidence,'coverage_gaps':gaps}
 (OUT/'prepared.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(json.dumps({'completedRound':gw,'nextRound':nextgw,'imports':{t:len(r) for t,r in rows.items()},'gaps':len(gaps)}))
if __name__=='__main__':main()
