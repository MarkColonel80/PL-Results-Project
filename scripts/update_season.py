#!/usr/bin/env python3
import csv,io,os,sys,urllib.parse,urllib.request,subprocess
from collections import defaultdict
try:
 from supabase import create_client
except ImportError:
 subprocess.check_call([sys.executable,"-m","pip","install","supabase"])
 from supabase import create_client

if len(sys.argv)<2: raise SystemExit("Usage: python3 scripts/update_season.py 2026-2027")
SEASON_DIR=sys.argv[1]
SEASON_LABEL=SEASON_DIR[:4]+"/"+SEASON_DIR[-2:]
URL=os.environ.get("SUPABASE_URL");KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not URL or not KEY: raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
sb=create_client(URL,KEY)
BASE="https://raw.githubusercontent.com/olbauday/FPL-Core-Insights/main"

def url(path): return BASE+"/"+"/".join(urllib.parse.quote(p,safe="") for p in path.split("/"))
def fetch(path,optional=False):
 try:
  req=urllib.request.Request(url(path),headers={"User-Agent":"pl-data-updater/4.0"})
  with urllib.request.urlopen(req,timeout=60) as r:
   return list(csv.DictReader(io.StringIO(r.read().decode("utf-8-sig"))))
 except Exception:
  if optional:return []
  raise

def I(v,default=None):
 try:return int(float(v))
 except:return default

def F(v,default=None):
 try:return float(v)
 except:return default

def truth(v):return str(v).lower()=="true"
def display_name(r): return r.get("web_name") or " ".join(x for x in [r.get("first_name"),r.get("second_name")] if x)

teams=fetch(f"data/{SEASON_DIR}/teams.csv")
team_by_code={str(r["code"]):r.get("fotmob_name") or r.get("name") for r in teams}
season_players=fetch(f"data/{SEASON_DIR}/players.csv")
player_by_id={str(r.get("player_id")):r for r in season_players if r.get("player_id")}

canonical=[];season_rows=[]
for r in season_players:
 code=str(r.get("player_code") or "");pid=str(r.get("player_id") or "")
 if not code or not pid: continue
 canonical.append({"player_code":code,"first_name":r.get("first_name"),"second_name":r.get("second_name"),"web_name":display_name(r)})
 tc=str(r.get("team_code") or "")
 season_rows.append({"season":SEASON_LABEL,"player_code":code,"player_id":pid,"team_code":tc or None,"team_name":team_by_code.get(tc,tc or None),"position":r.get("position")})
for i in range(0,len(canonical),500): sb.table("players").upsert(canonical[i:i+500],on_conflict="player_code").execute()
for i in range(0,len(season_rows),500): sb.table("player_seasons").upsert(season_rows[i:i+500],on_conflict="season,player_code").execute()

all_matches={};all_lineups=[];all_incidents=[];all_pms=[]
for gw in range(1,39):
 root=f"data/{SEASON_DIR}/By Tournament/Premier League/GW{gw}"
 fx=fetch(root+"/fixtures.csv",True)
 if not fx:continue
 print("GW",gw)
 for m in fx:
  if m.get("match_id") and truth(m.get("finished")):all_matches[m["match_id"]]=m
 all_lineups+=fetch(root+"/lineups.csv",True)
 all_incidents+=fetch(root+"/incidents.csv",True)
 gw_players=fetch(root+"/players.csv",True)
 player_meta={}
 for r in gw_players:
  pid=str(r.get("player_id") or "")
  if not pid:continue
  player_meta[pid]={"player_code":str(r.get("player_code") or ""),"name":display_name(r),"team_code":str(r.get("team_code") or "")}
 for r in fetch(root+"/playermatchstats.csv",True):
  rr=dict(r);pid=str(r.get("player_id") or "");base=player_by_id.get(pid,{})
  rr["__gw"]=gw
  rr["__meta"]=player_meta.get(pid,{"player_code":str(base.get("player_code") or ""),"name":display_name(base),"team_code":str(base.get("team_code") or "")})
  all_pms.append(rr)

finished=set(all_matches)
formations=defaultdict(dict)
for r in all_lineups:
 if r.get("match_id") in finished and r.get("formation"):formations[r["match_id"]][r.get("team_side")]=r.get("formation")

match_rows=[]
for mid,m in all_matches.items():
 hc=str(I(m.get("home_team")) or m.get("home_team",""));ac=str(I(m.get("away_team")) or m.get("away_team",""))
 match_rows.append({"match_id":mid,"season":SEASON_LABEL,"gameweek":I(m.get("gameweek")),"kickoff_time":m.get("kickoff_time"),"home_team":team_by_code.get(hc,hc),"away_team":team_by_code.get(ac,ac),"home_score":I(m.get("home_score")),"away_score":I(m.get("away_score")),"home_formation":formations[mid].get("home"),"away_formation":formations[mid].get("away"),"match_url":("https://www.fotmob.com"+m["match_url"]) if m.get("match_url","").startswith("/") else m.get("match_url")})
if match_rows:sb.table("matches").upsert(match_rows,on_conflict="match_id").execute()

for mid in finished:
 sb.table("lineups").delete().eq("match_id",mid).execute()
 sb.table("goals").delete().eq("match_id",mid).execute()
 sb.table("player_match_stats").delete().eq("match_id",mid).execute()

seen=set();line_rows=[]
for r in all_lineups:
 mid=r.get("match_id")
 if mid not in finished:continue
 pid=str(r.get("player_id") or "");meta=player_by_id.get(pid,{})
 k=(mid,r.get("team_side"),pid,r.get("player_name"))
 if k in seen:continue
 seen.add(k)
 line_rows.append({"match_id":mid,"season":SEASON_LABEL,"gameweek":I(all_matches[mid].get("gameweek")),"team_name":team_by_code.get(str(r.get("team_code")),str(r.get("team_code",""))),"team_side":r.get("team_side"),"player_id":pid or None,"player_code":str(meta.get("player_code") or "") or None,"player_name":r.get("player_name"),"position":r.get("position"),"jersey_number":I(r.get("jersey_number")),"is_starting":truth(r.get("is_starting")),"formation":r.get("formation"),"lineup_status":r.get("lineup_status")})
for i in range(0,len(line_rows),500):sb.table("lineups").insert(line_rows[i:i+500]).execute()

pms_by_key={}
for r in all_pms:
 mid=r.get("match_id");pid=str(r.get("player_id") or "")
 if mid not in finished or not pid:continue
 meta=r.get("__meta") or {};mins=F(r.get("minutes_played"),0) or 0;start_min=F(r.get("start_min"),None)
 team_code=str(meta.get("team_code") or "")
 code=str(meta.get("player_code") or player_by_id.get(pid,{}).get("player_code") or "")
 pms_by_key[(mid,pid)]={"season":SEASON_LABEL,"gameweek":I(all_matches[mid].get("gameweek"),r.get("__gw")),"match_id":mid,"player_id":pid,"player_code":code or None,"player_name":meta.get("name") or display_name(player_by_id.get(pid,{})) or pid,"team_name":team_by_code.get(team_code,team_code or None),"minutes_played":mins,"is_starting":bool(mins>0 and start_min==0),"goals":I(r.get("goals"),0) or 0,"assists":I(r.get("assists"),0) or 0,"xg":F(r.get("xg")),"xa":F(r.get("xa")),"shots":I(r.get("total_shots")),"shots_on_target":I(r.get("shots_on_target")),"chances_created":I(r.get("chances_created"))}
pms_rows=list(pms_by_key.values())
for i in range(0,len(pms_rows),500):sb.table("player_match_stats").insert(pms_rows[i:i+500]).execute()

goal_rows=[];seen=set()
for r in all_incidents:
 mid=r.get("match_id")
 if mid not in finished or str(r.get("incident_type","")).lower()!="goal":continue
 incident_index=I(r.get("incident_index"));k=(mid,incident_index)
 if k in seen:continue
 seen.add(k);m=all_matches[mid];hc=str(I(m.get("home_team")) or m.get("home_team",""));ac=str(I(m.get("away_team")) or m.get("away_team",""))
 pid=str(r.get("player_id") or "");aid=str(r.get("assist_player_id") or "")
 goal_rows.append({"match_id":mid,"season":SEASON_LABEL,"gameweek":I(m.get("gameweek")),"incident_index":incident_index,"home_team":team_by_code.get(hc,hc),"away_team":team_by_code.get(ac,ac),"minute":I(r.get("minute")),"added_time":I(r.get("added_time")),"team_side":r.get("team_side"),"player_id":pid or None,"player_code":str(player_by_id.get(pid,{}).get("player_code") or "") or None,"player_name":r.get("player_name"),"assist_player_id":aid or None,"assist_player_code":str(player_by_id.get(aid,{}).get("player_code") or "") or None,"assist_player_name":r.get("assist_player_name"),"goal_type":r.get("goal_type"),"home_score":I(r.get("home_score")),"away_score":I(r.get("away_score"))})
for i in range(0,len(goal_rows),500):sb.table("goals").insert(goal_rows[i:i+500]).execute()
print(f"Updated {SEASON_LABEL}: {len(match_rows)} finished matches, {len(line_rows)} lineup rows, {len(pms_rows)} player-match rows, {len(goal_rows)} goals.")
