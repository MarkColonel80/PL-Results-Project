#!/usr/bin/env python3
import sys
from update_season_v5 import main
from normalize_current_team_names import normalize_current_team_names

if __name__=="__main__":
    season_dir=sys.argv[1] if len(sys.argv)>1 else None
    main()
    if season_dir:
        season=season_dir[:4]+"/"+season_dir[-2:]
        normalize_current_team_names(season)
