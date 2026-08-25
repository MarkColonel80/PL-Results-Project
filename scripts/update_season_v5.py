#!/usr/bin/env python3
import csv,io,os,sys,urllib.parse,urllib.request,subprocess
from collections import defaultdict,Counter
try:
 from supabase import create_client
except ImportError:
 subprocess.check_call([sys.executable,"-m","pip","install","supabase"])
 from supabase import create_client

BASE="https://raw.githubusercontent.com/olbauday/FPL-Core-Insights/main"

def I(v,default=None):
 try:return int(float(v))
 except:return default

def F(v,default=None):
 try:return float(v)
 except:return default

def truth(v):return str(v).strip().lower()=="true"
def display_name(r):return r.get("web_name") or " ".join(x for x in [r.get("first_name"),r.get("second_name")] if x)
def batches(rows,n=500):
 for i in range(0,len(rows),n):yield rows[i:i+n]

def main():
 if len(sys.argv)<2:raise SystemExit("Usage: python3 scripts/update_season.py 2026-2027")
 season_dir=sys.argv[1];season=season_dir[:4]+"/"+season_dir[-2:]
 url=os.environ.get("SUPABASE_URL");key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
 if not url or not key:raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
 sb=create_client(url,key)
 def raw(path):return BASE+"/"+"/".join(urllib.parse.quote(p,safe="") for p in path.split("/"))
 def fetch(path,optional=False):
  try:
   req=urllib.request.Request(raw(path),headers={"User-Agent":"pl-data-updater/5.0"})
   with urllib.request.urlopen(req,timeout=60) as r:return list(csv.DictReader(io.StringIO(r.read().decode("utf-8-sig"))))
  except Exception:
   if optional:return []
   raise

 teams=fetch(f"data/{season_dir}/teams.csv")
 team_by_code={str(r["code"]):r.get("fotmob_name") or r.get("name") for r in teams}
 season_players=fetch(f"data/{season_dir}/players.csv")
 player_by_id={str(r.get("player_id")):r for r in season_players if r.get("player_id")}
 canonical=[];season_rows=[]
 for r in season_players:
  code=str(r.get("player_code") or "");pid=str(r.get("player_id") or "")
  if not code or not pid:continue
  canonical.append({"player_code":code,"first_name":r.get("first_name"),"second_name":r.get("second_name"),"web_name":display_name(r)})
  tc=str(r.get("team_code") or "")
  season_rows.append({"season":season,"player_code":code,"player_id":pid,"team_code":tc or None,"team_name":team_by_code.get(tc,tc or None),"position":r.get("position")})
 for b in batches(canonical):sb.table("players").upsert(b,on_conflict="player_code").execute()
 for b in batches(season_rows):sb.table("player_seasons").upsert(b,on_conflict="season,player_code").execute()

 all_matches={};all_lineups=[];all_incidents=[];all_shots=[];all_pms=[]
 for gw in range(1,39):
  root=f"data/{season_dir}/By Tournament/Premier League/GW{gw}"
  fx=fetch(root+"/fixtures.csv",True)
  if not fx:continue
  print("GW",gw)
  for m in fx:
   if m.get("match_id") and truth(m.get("finished")):all_matches[m["match_id"]]=m
  for r in fetch(root+"/lineups.csv",True):r["__gw"]=gw;all_lineups.append(r)
  for r in fetch(root+"/incidents.csv",True):r["__gw"]=gw;all_incidents.append(r)
  for r in fetch(root+"/shots.csv",True):r["__gw"]=gw;all_shots.append(r)
  gw_players=fetch(root+"/players.csv",True);meta={}
  for r in gw_players:
   pid=str(r.get("player_id") or "")
   if pid:meta[pid]={"player_code":str(r.get("player_code") or ""),"name":display_name(r),"team_code":str(r.get("team_code") or "")}
  for r in fetch(root+"/playermatchstats.csv",True):
   rr=dict(r);pid=str(r.get("player_id") or "");base=player_by_id.get(pid,{})
   rr["__gw"]=gw;rr["__meta"]=meta.get(pid,{"player_code":str(base.get("player_code") or ""),"name":display_name(base),"team_code":str(base.get("team_code") or "")})
   all_pms.append(rr)

 finished=set(all_matches)
 formations=defaultdict(dict)
 for r in all_lineups:
  if r.get("match_id") in finished and r.get("formation"):formations[r["match_id"]][r.get("team_side")]=r.get("formation")
 match_rows=[];match_names={}
 for mid,m in all_matches.items():
  hc=str(I(m.get("home_team")) or m.get("home_team","") );ac=str(I(m.get("away_team")) or m.get("away_team","") )
  hn=team_by_code.get(hc,hc);an=team_by_code.get(ac,ac);match_names[mid]=(hn,an)
  match_rows.append({"match_id":mid,"season":season,"gameweek":I(m.get("gameweek")),"kickoff_time":m.get("kickoff_time"),"home_team":hn,"away_team":an,"home_score":I(m.get("home_score")),"away_score":I(m.get("away_score")),"home_formation":formations[mid].get("home"),"away_formation":formations[mid].get("away"),"match_url":("https://www.fotmob.com"+m["match_url"]) if m.get("match_url","").startswith("/") else m.get("match_url")})
 if match_rows:sb.table("matches").upsert(match_rows,on_conflict="match_id").execute()

 # Player-match stats are the richest reliable current-season source and also power the lineup fallback.
 pms_by_key={};pms_extra={}
 for r in all_pms:
  mid=r.get("match_id");pid=str(r.get("player_id") or "")
  if mid not in finished or not pid:continue
  meta=r.get("__meta") or {};base=player_by_id.get(pid,{})
  mins=F(r.get("minutes_played"),0) or 0;start_min=F(r.get("start_min"),None);tc=str(meta.get("team_code") or base.get("team_code") or "")
  code=str(meta.get("player_code") or base.get("player_code") or "");tn=team_by_code.get(tc,tc or None);nm=meta.get("name") or display_name(base) or pid
  row={"season":season,"gameweek":I(all_matches[mid].get("gameweek"),r.get("__gw")),"match_id":mid,"player_id":pid,"player_code":code or None,"player_name":nm,"team_name":tn,"minutes_played":mins,"is_starting":bool(mins>0 and start_min==0),"goals":I(r.get("goals"),0) or 0,"assists":I(r.get("assists"),0) or 0,"xg":F(r.get("xg")),"xa":F(r.get("xa")),"shots":I(r.get("total_shots")),"shots_on_target":I(r.get("shots_on_target")),"chances_created":I(r.get("chances_created"))}
  pms_by_key[(mid,pid)]=row;pms_extra[(mid,pid)]={"team_code":tc,"position":base.get("position")}
 pms_rows=list(pms_by_key.values())
 pms_matches={r["match_id"] for r in pms_rows}
 for mid in pms_matches:sb.table("player_match_stats").delete().eq("match_id",mid).execute()
 for b in batches(pms_rows):sb.table("player_match_stats").insert(b).execute()

 # Prefer dedicated lineup data; otherwise reconstruct matchday players/starters from start_min + minutes.
 line_rows=[];seen=set();actual_lineup_matches=set()
 for r in all_lineups:
  mid=r.get("match_id")
  if mid not in finished:continue
  actual_lineup_matches.add(mid);pid=str(r.get("player_id") or "");base=player_by_id.get(pid,{})
  k=(mid,r.get("team_side"),pid,r.get("player_name"))
  if k in seen:continue
  seen.add(k)
  line_rows.append({"match_id":mid,"season":season,"gameweek":I(all_matches[mid].get("gameweek")),"team_name":team_by_code.get(str(r.get("team_code")),str(r.get("team_code","") )),"team_side":r.get("team_side"),"player_id":pid or None,"player_code":str(base.get("player_code") or "") or None,"player_name":r.get("player_name") or display_name(base),"position":r.get("position") or base.get("position"),"jersey_number":I(r.get("jersey_number")),"is_starting":truth(r.get("is_starting")),"formation":r.get("formation"),"lineup_status":r.get("lineup_status") or "source"})
 derived_lineups=0
 for (mid,pid),p in pms_by_key.items():
  if mid in actual_lineup_matches:continue
  hn,an=match_names.get(mid,(None,None));side="home" if p.get("team_name")==hn else ("away" if p.get("team_name")==an else None)
  ex=pms_extra.get((mid,pid),{})
  line_rows.append({"match_id":mid,"season":season,"gameweek":p.get("gameweek"),"team_name":p.get("team_name"),"team_side":side,"player_id":pid,"player_code":p.get("player_code"),"player_name":p.get("player_name"),"position":ex.get("position"),"jersey_number":None,"is_starting":p.get("is_starting",False),"formation":None,"lineup_status":"derived_from_player_match_stats"});derived_lineups+=1
 line_matches={r["match_id"] for r in line_rows}
 for mid in line_matches:sb.table("lineups").delete().eq("match_id",mid).execute()
 for b in batches(line_rows):sb.table("lineups").insert(b).execute()

 # Prefer incident feed. If absent, derive goal minute/scorer/side from shot outcomes; never guess assists.
 goal_rows=[];actual_goal_matches=set();seen=set()
 for r in all_incidents:
  mid=r.get("match_id")
  if mid not in finished or str(r.get("incident_type","")).lower()!="goal":continue
  actual_goal_matches.add(mid);ix=I(r.get("incident_index"));k=(mid,ix)
  if k in seen:continue
  seen.add(k);m=all_matches[mid];hc=str(I(m.get("home_team")) or m.get("home_team","") );ac=str(I(m.get("away_team")) or m.get("away_team","") )
  pid=str(r.get("player_id") or "");aid=str(r.get("assist_player_id") or "")
  goal_rows.append({"match_id":mid,"season":season,"gameweek":I(m.get("gameweek")),"incident_index":ix,"home_team":team_by_code.get(hc,hc),"away_team":team_by_code.get(ac,ac),"minute":I(r.get("minute")),"added_time":I(r.get("added_time")),"team_side":r.get("team_side"),"player_id":pid or None,"player_code":str(player_by_id.get(pid,{}).get("player_code") or "") or None,"player_name":r.get("player_name") or display_name(player_by_id.get(pid,{})),"assist_player_id":aid or None,"assist_player_code":str(player_by_id.get(aid,{}).get("player_code") or "") or None,"assist_player_name":r.get("assist_player_name"),"goal_type":r.get("goal_type"),"home_score":I(r.get("home_score")),"away_score":I(r.get("away_score"))})

 shots_by_match=defaultdict(list)
 for r in all_shots:
  mid=r.get("match_id")
  if mid in finished and str(r.get("outcome","")).lower()=="goal" and mid not in actual_goal_matches:shots_by_match[mid].append(r)
 shot_score_mismatches=[];missing_scorers=0
 for mid,shots in shots_by_match.items():
  m=all_matches[mid];hn,an=match_names[mid]
  shots.sort(key=lambda r:(I(r.get("minute"),0) or 0,I(r.get("added_time"),0) or 0,I(r.get("shot_index"),0) or 0))
  home=away=0
  # Known scorer counts let us fill a missing shot scorer only when the residual ID is unambiguous.
  known=Counter(str(I(s.get("player_id"))) for s in shots if I(s.get("player_id")) is not None)
  residual_by_side={"home":[],"away":[]}
  for (pmid,pid),p in pms_by_key.items():
   if pmid!=mid:continue
   side="home" if p.get("team_name")==hn else ("away" if p.get("team_name")==an else None)
   if not side:continue
   residual=max(0,(p.get("goals") or 0)-known.get(pid,0));residual_by_side[side].extend([pid]*residual)
  missing_by_side=Counter("home" if truth(s.get("is_home")) else "away" for s in shots if I(s.get("player_id")) is None)
  fill={}
  for side,n in missing_by_side.items():
   vals=residual_by_side[side]
   if len(vals)==n and len(set(vals))==1:fill[side]=list(vals)
  for s in shots:
   side="home" if truth(s.get("is_home")) else "away"
   if side=="home":home+=1
   else:away+=1
   rawpid=I(s.get("player_id"));pid=str(rawpid) if rawpid is not None else ""
   if not pid and fill.get(side):pid=fill[side].pop(0)
   if not pid:missing_scorers+=1
   base=player_by_id.get(pid,{})
   situation=str(s.get("situation") or "").lower();goal_type="penalty" if situation=="penalty" else None
   goal_rows.append({"match_id":mid,"season":season,"gameweek":I(m.get("gameweek")),"incident_index":I(s.get("shot_index")),"home_team":hn,"away_team":an,"minute":I(s.get("minute")),"added_time":I(s.get("added_time")),"team_side":side,"player_id":pid or None,"player_code":str(base.get("player_code") or "") or None,"player_name":display_name(base) or None,"assist_player_id":None,"assist_player_code":None,"assist_player_name":None,"goal_type":goal_type,"home_score":home,"away_score":away})
  if home!=I(m.get("home_score"),home) or away!=I(m.get("away_score"),away):shot_score_mismatches.append(mid)
 goal_matches={r["match_id"] for r in goal_rows}
 for mid in goal_matches:sb.table("goals").delete().eq("match_id",mid).execute()
 for b in batches(goal_rows):sb.table("goals").insert(b).execute()

 actual_line_count=sum(1 for r in line_rows if r.get("lineup_status")!="derived_from_player_match_stats")
 derived_goal_count=sum(len(v) for k,v in shots_by_match.items())
 print(f"Updated {season}: {len(match_rows)} finished matches, {len(line_rows)} lineup rows ({actual_line_count} source / {derived_lineups} derived), {len(pms_rows)} player-match rows, {len(goal_rows)} goals ({len(goal_rows)-derived_goal_count} incident / {derived_goal_count} shot-derived).")
 if shot_score_mismatches:print("WARNING: shot-derived goal counts did not match final score for:",", ".join(shot_score_mismatches))
 if missing_scorers:print(f"WARNING: {missing_scorers} shot-derived goals still have no unambiguous scorer ID.")
 if derived_goal_count:print("Note: shot-derived goal events do not include assister IDs because the current source does not provide them.")

if __name__=="__main__":main()
