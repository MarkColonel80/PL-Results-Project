#!/usr/bin/env python3
"""Robust fixture-level FPL history importer.

Usage:
  python3 scripts/import_fpl_history_v2.py 2016-17
  python3 scripts/import_fpl_history_v2.py --all

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""
import csv, io, os, sys, time, urllib.parse, urllib.request, urllib.error, subprocess
try:
    from supabase import create_client
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
    from supabase import create_client

ALL_SEASONS=[f"{y}-{str(y+1)[-2:]}" for y in range(2016,2027)]
BASE="https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master"
TEAM_ALIASES={
    "Bournemouth":"AFC Bournemouth","Brighton":"Brighton & Hove Albion","Leeds":"Leeds United",
    "Leicester":"Leicester City","Man City":"Manchester City","Man Utd":"Manchester United",
    "Newcastle":"Newcastle United","Nott'm Forest":"Nottingham Forest","Norwich":"Norwich City",
    "Ipswich":"Ipswich Town","Spurs":"Tottenham Hotspur","West Ham":"West Ham United",
    "Wolves":"Wolverhampton Wanderers","West Brom":"West Bromwich Albion","Swansea":"Swansea City",
    "Cardiff":"Cardiff City","Huddersfield":"Huddersfield Town","Sheffield Utd":"Sheffield United",
    "Hull":"Hull City","Stoke":"Stoke City"
}
URL=os.environ.get("SUPABASE_URL"); KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not URL or not KEY: raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
sb=create_client(URL,KEY)

def raw_url(path):
    return BASE+"/"+"/".join(urllib.parse.quote(p,safe="") for p in path.split("/"))

def decode_csv(data):
    try: text=data.decode("utf-8-sig")
    except UnicodeDecodeError: text=data.decode("latin-1")
    return list(csv.DictReader(io.StringIO(text)))

def fetch_csv(path, missing_ok=False, retries=3):
    url=raw_url(path)
    last=None
    for attempt in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"pl-data-fpl-history/2.1","Accept":"text/csv,*/*"})
            with urllib.request.urlopen(req,timeout=120) as response:
                return decode_csv(response.read())
        except urllib.error.HTTPError as exc:
            if exc.code==404 and missing_ok: return []
            last=exc
        except Exception as exc:
            last=exc
        if attempt<retries-1: time.sleep(1.5*(attempt+1))
    if missing_ok and isinstance(last, urllib.error.HTTPError) and last.code==404: return []
    raise RuntimeError(f"Could not fetch {path}: {last}")

def I(v,default=0):
    try:return int(float(v))
    except (TypeError,ValueError):return default

def F(v,default=None):
    try:return float(v)
    except (TypeError,ValueError):return default

def truth(v):return str(v).strip().lower() in {"true","1","yes"}
def label(s):return s[:4]+"/"+s[-2:]
def pos_type(v):return {1:"GK",2:"DEF",3:"MID",4:"FWD"}.get(I(v,-1),"")
def display(r):return r.get("web_name") or " ".join(x for x in [r.get("first_name"),r.get("second_name")] if x)
def canon_team(v):return TEAM_ALIASES.get(v,v) if v else v
def batches(rows,n=500):
    for i in range(0,len(rows),n):yield rows[i:i+n]

def component_points(r,pos,season_dir):
    mins=I(r.get("minutes")); goals=I(r.get("goals_scored")); assists=I(r.get("assists")); cs=I(r.get("clean_sheets"))
    saves=I(r.get("saves")); ps=I(r.get("penalties_saved")); pm=I(r.get("penalties_missed")); yc=I(r.get("yellow_cards")); rc=I(r.get("red_cards"))
    og=I(r.get("own_goals")); gc=I(r.get("goals_conceded")); bonus=I(r.get("bonus")); dc=I(r.get("defensive_contribution")); year=int(season_dir[:4])
    appearance=2 if mins>=60 else (1 if mins>0 else 0)
    goal_rate={"GK":10,"DEF":6,"MID":5,"FWD":4}.get(pos,0)
    gp=goals*goal_rate; ap=assists*3
    csp=cs*(4 if pos in {"GK","DEF"} else (1 if pos=="MID" else 0))
    svp=saves//3 if pos=="GK" else 0
    pp=ps*5-pm*2; cp=-yc-rc*3; ogp=-og*2
    gcp=-(gc//2) if pos in {"GK","DEF"} else 0
    dcp=2 if year>=2025 and ((pos=="DEF" and dc>=10) or (pos in {"MID","FWD"} and dc>=12)) else 0
    calc=sum([appearance,gp,ap,csp,svp,pp,cp,ogp,gcp,dcp,bonus])
    return {"appearance_points":appearance,"goal_points":gp,"assist_points":ap,"clean_sheet_points":csp,"save_points":svp,"penalty_points":pp,"card_points":cp,"own_goal_points":ogp,"goals_conceded_points":gcp,"defensive_contribution_points":dcp,"bonus_points":bonus,"calculated_points":calc,"points_difference":I(r.get("total_points"))-calc}

def season_gw_rows(season_dir):
    merged=fetch_csv(f"data/{season_dir}/gws/merged_gw.csv",missing_ok=True)
    if merged:
        print(f"Using merged_gw.csv ({len(merged)} rows)")
        return merged
    print("No merged_gw.csv found; loading individual gameweeks.")
    rows=[]; found=[]
    for gw in range(1,39):
        path=f"data/{season_dir}/gws/gw{gw}.csv"
        part=fetch_csv(path,missing_ok=True)
        if not part: continue
        found.append(gw)
        for r in part:r["GW"]=gw
        rows.extend(part)
    print(f"Found gameweeks: {found[0] if found else 'none'}-{found[-1] if found else 'none'}; raw GW rows: {len(rows)}")
    return rows

def import_season(season_dir):
    season=label(season_dir); print(f"\n=== {season} ===")
    players_raw=fetch_csv(f"data/{season_dir}/players_raw.csv")
    teams_raw=fetch_csv(f"data/{season_dir}/teams.csv",missing_ok=True)
    master_teams=fetch_csv("data/master_team_list.csv")
    team_by_id={str(I(r.get("team"),-1)):canon_team(r.get("team_name")) for r in master_teams if r.get("season")==season_dir and r.get("team")}
    for r in teams_raw:
        if r.get("id"):
            team_by_id[str(I(r.get("id"),-1))]=canon_team(r.get("name"))
    if not team_by_id:
        raise RuntimeError(f"No team mapping found for {season}")
    print(f"Team mapping: {len(team_by_id)} clubs")

    id_meta={}; canonical=[]; season_rows=[]
    for r in players_raw:
        pid=str(I(r.get("id"),-1)); code=str(I(r.get("code"),-1))
        if pid=="-1" or code=="-1": continue
        pos=pos_type(r.get("element_type")); team_name=team_by_id.get(str(I(r.get("team"),-1))); nm=display(r)
        id_meta[pid]={"player_code":code,"name":nm,"position":pos,"team_name":team_name}
        canonical.append({"player_code":code,"first_name":r.get("first_name"),"second_name":r.get("second_name"),"web_name":nm,"birth_date":r.get("birth_date") or None,"opta_code":r.get("opta_code") or None})
        season_rows.append({"season":season,"player_code":code,"player_id":pid,"team_code":str(r.get("team_code") or "") or None,"team_name":team_name,"position":{"GK":"Goalkeeper","DEF":"Defender","MID":"Midfielder","FWD":"Forward"}.get(pos,pos)})
    for b in batches(canonical): sb.table("players").upsert(b,on_conflict="player_code").execute()
    for b in batches(season_rows): sb.table("player_seasons").upsert(b,on_conflict="season,player_code").execute()
    sb.rpc("backfill_player_codes_for_season",{"p_season":season}).execute()
    print(f"Players: {len(canonical)}; rich-data player codes backfilled where available")

    gw_rows=season_gw_rows(season_dir)
    if not gw_rows:
        raise RuntimeError(f"No gameweek rows found for {season}. Historical files exist, so refusing to silently continue.")

    out=[]; skipped_no_player=0; skipped_bad_fixture=0
    for r in gw_rows:
        pid=str(I(r.get("element"),-1)); meta=id_meta.get(pid)
        fixture=I(r.get("fixture"),-1); gw=I(r.get("GW") or r.get("round"),-1)
        if not meta:
            skipped_no_player+=1; continue
        if fixture<0 or gw<0:
            skipped_bad_fixture+=1; continue
        pos=r.get("position") or meta["position"]
        if pos in {"Goalkeeper","Defender","Midfielder","Forward"}: pos={"Goalkeeper":"GK","Defender":"DEF","Midfielder":"MID","Forward":"FWD"}[pos]
        opp=team_by_id.get(str(I(r.get("opponent_team"),-1)),r.get("opponent_team") or None)
        out.append({
            "season":season,"gameweek":gw,"fixture_id":fixture,"player_code":meta["player_code"],"player_id":pid,
            "player_name":r.get("name") or meta["name"],"team_name":canon_team(r.get("team")) or meta["team_name"],"position":pos,
            "kickoff_time":r.get("kickoff_time") or None,"opponent_team":canon_team(opp),"was_home":truth(r.get("was_home")),
            "minutes":I(r.get("minutes")),"total_points":I(r.get("total_points")),"goals_scored":I(r.get("goals_scored")),"assists":I(r.get("assists")),
            "clean_sheets":I(r.get("clean_sheets")),"goals_conceded":I(r.get("goals_conceded")),"own_goals":I(r.get("own_goals")),
            "penalties_saved":I(r.get("penalties_saved")),"penalties_missed":I(r.get("penalties_missed")),"yellow_cards":I(r.get("yellow_cards")),
            "red_cards":I(r.get("red_cards")),"saves":I(r.get("saves")),"bonus":I(r.get("bonus")),"bps":I(r.get("bps")),
            "defensive_contribution":I(r.get("defensive_contribution"),None),"clearances_blocks_interceptions":I(r.get("clearances_blocks_interceptions"),None),
            "recoveries":I(r.get("recoveries"),None),"tackles":I(r.get("tackles"),None),"expected_goals":F(r.get("expected_goals")),
            "expected_assists":F(r.get("expected_assists")),"expected_goal_involvements":F(r.get("expected_goal_involvements")),
            "expected_goals_conceded":F(r.get("expected_goals_conceded")),"value":I(r.get("value"),None),"selected":I(r.get("selected"),None),
            "transfers_in":I(r.get("transfers_in"),None),"transfers_out":I(r.get("transfers_out"),None),**component_points(r,pos,season_dir)
        })
    for n,b in enumerate(batches(out),1):
        sb.table("fpl_player_match_stats").upsert(b,on_conflict="season,fixture_id,player_code").execute()
        if n%10==0: print(f"  uploaded {min(n*500,len(out))}/{len(out)} FPL rows")
    mismatches=sum(1 for r in out if r["points_difference"]!=0)
    missing_teams=sum(1 for r in out if not r["team_name"])
    print(f"FPL fixture rows: {len(out)}; skipped missing player: {skipped_no_player}; skipped bad fixture: {skipped_bad_fixture}; missing team names: {missing_teams}; point-component mismatches: {mismatches}")

def main():
    if len(sys.argv)!=2: raise SystemExit("Usage: python3 scripts/import_fpl_history_v2.py 2016-17 | --all")
    seasons=ALL_SEASONS if sys.argv[1]=="--all" else [sys.argv[1]]
    for s in seasons: import_season(s)
    print("\nFPL history import complete.")

if __name__=="__main__": main()
