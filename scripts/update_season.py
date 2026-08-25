#!/usr/bin/env python3
import csv,io,os,sys,urllib.parse,urllib.request,subprocess
from collections import defaultdict
try: from supabase import create_client
except ImportError:
 subprocess.check_call([sys.executable,"-m","pip","install","supabase"]);from supabase import create_client
if len(sys.argv)<2: raise SystemExit("Usage: python3 scripts/update_season.py 2026-2027")
SEASON_DIR=sys.argv[1];SEASON_LABEL=SEASON_DIR[:4]+"/"+SEASON_DIR[-2:]
URL=os.environ.get("SUPABASE_URL");KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not URL or not KEY: raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
sb=create_client(URL,KEY);BASE="https://raw.githubusercontent.com/olbauday/FPL-Core-Insights/main"
def url(path):return BASE+"/"+"/".join(urllib.parse.quote(p,safe="") for p in path.split("/"))
def fetch(path,optional=False):
 try:
  req=urllib.request.Request(url(path),headers={"User-Agent":"pl-data-updater/2.0"})
  with urllib.request.urlopen(req,timeout=60) as r:return list(csv.DictReader(io.StringIO(r.read().decode("utf-8-sig"))))
 except Exception:
  if optional:return []
  raise
def I(v):
 try:return int(float(v))
 except:return None
def truth(v):return str(v).lower()=="true"
teams=fetch(f"data/{SEASON_DIR}/teams.csv");team_by_code={str(r["code"]):r.get("fotmob_name") or r.get("name") for r in teams}
all_matches={};all_lineups=[];all_incidents=[]
for gw in range(1,39):
 root=f"data/{SEASON_DIR}/By Tournament/Premier League/GW{gw}";fx=fetch(root+"/fixtures.csv",True)
 if not fx:continue
 for m in fx:
  if m.get("match_id") and truth(m.get("finished")):all_matches[m["match_id"]]=m
 all_lineups+=fetch(root+"/lineups.csv",True);all_incidents+=fetch(root+"/incidents.csv",True)
finished=set(all_matches);formations=defaultdict(dict)
for r in all_lineups:
 if r.get("match_id") in finished and r.get("formation"):formations[r["match_id"]][r.get("team_side")]=r.get("formation")
match_rows=[]
for mid,m in all_matches.items():
 hc=str(I(m.get("home_team")) or m.get("home_team",""));ac=str(I(m.get("away_team")) or m.get("away_team",""))
 match_rows.append({"match_id":mid,"season":SEASON_LABEL,"gameweek":I(m.get("gameweek")),"kickoff_time":m.get("kickoff_time"),"home_team":team_by_code.get(hc,hc),"away_team":team_by_code.get(ac,ac),"home_score":I(m.get("home_score")),"away_score":I(m.get("away_score")),"home_formation":formations[mid].get("home"),"away_formation":formations[mid].get("away"),"match_url":("https://www.fotmob.com"+m["match_url"]) if m.get("match_url","").startswith("/") else m.get("match_url")})
if match_rows:sb.table("matches").upsert(match_rows,on_conflict="match_id").execute()
for mid in finished:
 sb.table("lineups").delete().eq("match_id",mid).execute();sb.table("goals").delete().eq("match_id",mid).execute()
seen=set();line_rows=[]
for r in all_lineups:
 mid=r.get("match_id")
 if mid not in finished:continue
 k=(mid,r.get("team_side"),r.get("player_id"),r.get("player_name"))
 if k in seen:continue
 seen.add(k);line_rows.append({"match_id":mid,"season":SEASON_LABEL,"gameweek":I(all_matches[mid].get("gameweek")),"team_name":team_by_code.get(str(r.get("team_code")),str(r.get("team_code",""))),"team_side":r.get("team_side"),"player_id":r.get("player_id"),"player_name":r.get("player_name"),"position":r.get("position"),"jersey_number":I(r.get("jersey_number")),"is_starting":truth(r.get("is_starting")),"formation":r.get("formation"),"lineup_status":r.get("lineup_status")})
for i in range(0,len(line_rows),500):sb.table("lineups").insert(line_rows[i:i+500]).execute()
goal_rows=[];seen=set()
for r in all_incidents:
 mid=r.get("match_id")
 if mid not in finished or str(r.get("incident_type","")).lower()!="goal":continue
 k=(mid,r.get("incident_index"))
 if k in seen:continue
 seen.add(k);m=all_matches[mid];hc=str(I(m.get("home_team")) or m.get("home_team",""));ac=str(I(m.get("away_team")) or m.get("away_team",""))
 goal_rows.append({"match_id":mid,"season":SEASON_LABEL,"gameweek":I(m.get("gameweek")),"home_team":team_by_code.get(hc,hc),"away_team":team_by_code.get(ac,ac),"minute":I(r.get("minute")),"added_time":I(r.get("added_time")),"team_side":r.get("team_side"),"player_name":r.get("player_name"),"assist_player_name":r.get("assist_player_name"),"goal_type":r.get("goal_type"),"home_score":I(r.get("home_score")),"away_score":I(r.get("away_score"))})
for i in range(0,len(goal_rows),500):sb.table("goals").insert(goal_rows[i:i+500]).execute()
print(f"Updated {SEASON_LABEL}: {len(match_rows)} finished matches, {len(line_rows)} lineup rows, {len(goal_rows)} goals.")
