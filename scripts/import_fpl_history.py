#!/usr/bin/env python3
"""Import official FPL fixture-level history from vaastav/Fantasy-Premier-League.

Usage:
  python3 scripts/import_fpl_history.py 2025-26
  python3 scripts/import_fpl_history.py --all

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""
import csv
import io
import os
import sys
import urllib.parse
import urllib.request
import subprocess

try:
    from supabase import create_client
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
    from supabase import create_client

ALL_SEASONS = [f"{y}-{str(y+1)[-2:]}" for y in range(2016, 2027)]
BASE = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master"

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not URL or not KEY:
    raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
sb = create_client(URL, KEY)


def raw_url(path):
    return BASE + "/" + "/".join(urllib.parse.quote(p, safe="") for p in path.split("/"))


def fetch_csv(path, optional=False):
    try:
        req = urllib.request.Request(raw_url(path), headers={"User-Agent": "pl-data-fpl-history/1.0"})
        with urllib.request.urlopen(req, timeout=120) as response:
            text = response.read().decode("utf-8-sig")
        return list(csv.DictReader(io.StringIO(text)))
    except Exception as exc:
        if optional:
            return []
        raise RuntimeError(f"Could not fetch {path}: {exc}") from exc


def I(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def F(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def truth(value):
    return str(value).strip().lower() in {"true", "1", "yes"}


def season_label(season_dir):
    return season_dir[:4] + "/" + season_dir[-2:]


def position_from_type(value):
    return {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}.get(I(value, -1), "")


def display_name(row):
    return row.get("web_name") or " ".join(
        x for x in [row.get("first_name"), row.get("second_name")] if x
    )


def component_points(row, position, season_dir):
    minutes = I(row.get("minutes"))
    goals = I(row.get("goals_scored"))
    assists = I(row.get("assists"))
    clean_sheets = I(row.get("clean_sheets"))
    saves = I(row.get("saves"))
    penalties_saved = I(row.get("penalties_saved"))
    penalties_missed = I(row.get("penalties_missed"))
    yellow = I(row.get("yellow_cards"))
    red = I(row.get("red_cards"))
    own_goals = I(row.get("own_goals"))
    goals_conceded = I(row.get("goals_conceded"))
    bonus = I(row.get("bonus"))
    defensive = I(row.get("defensive_contribution"))
    start_year = int(season_dir[:4])

    appearance = 2 if minutes >= 60 else (1 if minutes > 0 else 0)
    if position == "GK":
        goal_rate = 10 if start_year >= 2024 else 6
    else:
        goal_rate = {"DEF": 6, "MID": 5, "FWD": 4}.get(position, 0)
    goal_points = goals * goal_rate
    assist_points = assists * 3
    clean_sheet_points = clean_sheets * (4 if position in {"GK", "DEF"} else (1 if position == "MID" else 0))
    save_points = saves // 3 if position == "GK" else 0
    penalty_points = penalties_saved * 5 - penalties_missed * 2
    card_points = -yellow - (red * 3)
    own_goal_points = -(own_goals * 2)
    goals_conceded_points = -(goals_conceded // 2) if position in {"GK", "DEF"} else 0
    defensive_points = 0
    if start_year >= 2025:
        if position == "DEF" and defensive >= 10:
            defensive_points = 2
        elif position in {"MID", "FWD"} and defensive >= 12:
            defensive_points = 2
    calculated = sum([
        appearance, goal_points, assist_points, clean_sheet_points, save_points,
        penalty_points, card_points, own_goal_points, goals_conceded_points,
        defensive_points, bonus,
    ])
    return {
        "appearance_points": appearance,
        "goal_points": goal_points,
        "assist_points": assist_points,
        "clean_sheet_points": clean_sheet_points,
        "save_points": save_points,
        "penalty_points": penalty_points,
        "card_points": card_points,
        "own_goal_points": own_goal_points,
        "goals_conceded_points": goals_conceded_points,
        "defensive_contribution_points": defensive_points,
        "bonus_points": bonus,
        "calculated_points": calculated,
        "points_difference": I(row.get("total_points")) - calculated,
    }


def batches(rows, size=500):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def import_season(season_dir):
    label = season_label(season_dir)
    print(f"\n=== {label} ===")
    players_raw = fetch_csv(f"data/{season_dir}/players_raw.csv")
    teams_raw = fetch_csv(f"data/{season_dir}/teams.csv", True)
    team_by_id = {str(I(r.get("id"), -1)): r.get("name") for r in teams_raw if r.get("id")}

    id_meta = {}
    canonical_rows = []
    season_rows = []
    for r in players_raw:
        pid = str(I(r.get("id"), -1))
        code = str(I(r.get("code"), -1))
        if pid == "-1" or code == "-1":
            continue
        pos = position_from_type(r.get("element_type"))
        team_id = str(I(r.get("team"), -1))
        team_name = team_by_id.get(team_id)
        name = display_name(r)
        id_meta[pid] = {"player_code": code, "name": name, "position": pos, "team_name": team_name}
        canonical_rows.append({
            "player_code": code,
            "first_name": r.get("first_name"),
            "second_name": r.get("second_name"),
            "web_name": name,
        })
        season_rows.append({
            "season": label,
            "player_code": code,
            "player_id": pid,
            "team_code": str(r.get("team_code") or "") or None,
            "team_name": team_name,
            "position": {"GK": "Goalkeeper", "DEF": "Defender", "MID": "Midfielder", "FWD": "Forward"}.get(pos, pos),
        })

    for batch in batches(canonical_rows):
        sb.table("players").upsert(batch, on_conflict="player_code").execute()
    for batch in batches(season_rows):
        sb.table("player_seasons").upsert(batch, on_conflict="season,player_code").execute()
    print(f"Players: {len(canonical_rows)}")

    gw_rows = fetch_csv(f"data/{season_dir}/gws/merged_gw.csv", True)
    if not gw_rows:
        print("No merged_gw.csv found; trying individual gameweeks.")
        gw_rows = []
        for gw in range(1, 39):
            rows = fetch_csv(f"data/{season_dir}/gws/gw{gw}.csv", True)
            for r in rows:
                r["GW"] = gw
            gw_rows.extend(rows)

    out = []
    skipped = 0
    for r in gw_rows:
        pid = str(I(r.get("element"), -1))
        meta = id_meta.get(pid)
        if not meta:
            skipped += 1
            continue
        fixture_id = I(r.get("fixture"), -1)
        gw = I(r.get("GW") or r.get("round"), -1)
        if fixture_id < 0 or gw < 0:
            skipped += 1
            continue
        position = r.get("position") or meta["position"]
        if position in {"Goalkeeper", "Defender", "Midfielder", "Forward"}:
            position = {"Goalkeeper": "GK", "Defender": "DEF", "Midfielder": "MID", "Forward": "FWD"}[position]
        opp_id = str(I(r.get("opponent_team"), -1))
        points = component_points(r, position, season_dir)
        row = {
            "season": label,
            "gameweek": gw,
            "fixture_id": fixture_id,
            "player_code": meta["player_code"],
            "player_id": pid,
            "player_name": r.get("name") or meta["name"],
            "team_name": r.get("team") or meta["team_name"],
            "position": position,
            "kickoff_time": r.get("kickoff_time") or None,
            "opponent_team": team_by_id.get(opp_id, r.get("opponent_team") or None),
            "was_home": truth(r.get("was_home")),
            "minutes": I(r.get("minutes")),
            "total_points": I(r.get("total_points")),
            "goals_scored": I(r.get("goals_scored")),
            "assists": I(r.get("assists")),
            "clean_sheets": I(r.get("clean_sheets")),
            "goals_conceded": I(r.get("goals_conceded")),
            "own_goals": I(r.get("own_goals")),
            "penalties_saved": I(r.get("penalties_saved")),
            "penalties_missed": I(r.get("penalties_missed")),
            "yellow_cards": I(r.get("yellow_cards")),
            "red_cards": I(r.get("red_cards")),
            "saves": I(r.get("saves")),
            "bonus": I(r.get("bonus")),
            "bps": I(r.get("bps")),
            "defensive_contribution": I(r.get("defensive_contribution"), None),
            "clearances_blocks_interceptions": I(r.get("clearances_blocks_interceptions"), None),
            "recoveries": I(r.get("recoveries"), None),
            "tackles": I(r.get("tackles"), None),
            "expected_goals": F(r.get("expected_goals")),
            "expected_assists": F(r.get("expected_assists")),
            "expected_goal_involvements": F(r.get("expected_goal_involvements")),
            "expected_goals_conceded": F(r.get("expected_goals_conceded")),
            "value": I(r.get("value"), None),
            "selected": I(r.get("selected"), None),
            "transfers_in": I(r.get("transfers_in"), None),
            "transfers_out": I(r.get("transfers_out"), None),
            **points,
        }
        out.append(row)

    for n, batch in enumerate(batches(out), start=1):
        sb.table("fpl_player_match_stats").upsert(batch, on_conflict="season,fixture_id,player_code").execute()
        if n % 10 == 0:
            print(f"  uploaded {min(n * 500, len(out))}/{len(out)} FPL rows")

    mismatches = sum(1 for r in out if r["points_difference"] != 0)
    print(f"FPL fixture rows: {len(out)}; skipped: {skipped}; point-component mismatches: {mismatches}")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/import_fpl_history.py 2025-26 | --all")
    seasons = ALL_SEASONS if sys.argv[1] == "--all" else [sys.argv[1]]
    for season in seasons:
        import_season(season)
    print("\nFPL history import complete.")


if __name__ == "__main__":
    main()
