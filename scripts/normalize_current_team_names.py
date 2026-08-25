#!/usr/bin/env python3
import os
from supabase import create_client

ALIASES={
    "Bournemouth":"AFC Bournemouth",
    "Brighton":"Brighton & Hove Albion",
    "Leeds":"Leeds United",
    "Man City":"Manchester City",
    "Man Utd":"Manchester United",
    "Newcastle":"Newcastle United",
    "Nott'm Forest":"Nottingham Forest",
    "Spurs":"Tottenham Hotspur",
}

def canon(v):
    return ALIASES.get(v,v)

def normalize_current_team_names(season):
    url=os.environ.get("SUPABASE_URL"); key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    sb=create_client(url,key)

    # Small season-scoped read/updates keep the logic simple and make future
    # rich-source aliases consistent with the canonical FPL/history names.
    for table,cols in {
        "matches":["match_id","home_team","away_team"],
        "lineups":["id","team_name"],
        "player_match_stats":["id","team_name"],
        "goals":["id","home_team","away_team"],
        "player_seasons":["player_code","team_name"],
    }.items():
        rows=sb.table(table).select(",".join(cols)).eq("season",season).execute().data or []
        for r in rows:
            patch={}
            for c in cols:
                if c.endswith("team") or c=="team_name":
                    nv=canon(r.get(c))
                    if nv!=r.get(c): patch[c]=nv
            if not patch: continue
            q=sb.table(table).update(patch)
            if table=="matches": q=q.eq("match_id",r["match_id"])
            elif table=="player_seasons": q=q.eq("season",season).eq("player_code",r["player_code"])
            else: q=q.eq("id",r["id"])
            q.execute()
    print(f"Canonical team names checked for {season}.")

if __name__=="__main__":
    import sys
    if len(sys.argv)!=2: raise SystemExit("Usage: python3 scripts/normalize_current_team_names.py 2026/27")
    normalize_current_team_names(sys.argv[1])
