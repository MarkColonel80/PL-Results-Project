#!/usr/bin/env python3
"""Import current-season fixture-level FPL history directly from the official FPL API.

Usage:
  python3 scripts/update_fpl_current.py 2026-27

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from supabase import create_client
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
    from supabase import create_client

API = "https://fantasy.premierleague.com/api"
TEAM_ALIASES = {
    "Bournemouth": "AFC Bournemouth",
    "Brighton": "Brighton & Hove Albion",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Man City": "Manchester City",
    "Man Utd": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Norwich": "Norwich City",
    "Ipswich": "Ipswich Town",
    "Spurs": "Tottenham Hotspur",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
    "West Brom": "West Bromwich Albion",
    "Swansea": "Swansea City",
    "Cardiff": "Cardiff City",
    "Huddersfield": "Huddersfield Town",
    "Sheffield Utd": "Sheffield United",
    "Hull": "Hull City",
    "Stoke": "Stoke City",
}
NULLISH = {"", "none", "null", "nan", "nat", "n/a"}
PLAYER_POSITIONS = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not URL or not KEY:
    raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
sb = create_client(URL, KEY)


def canon_team(v):
    return TEAM_ALIASES.get(v, v) if v else v


def nullable(v):
    if v is None:
        return None
    s = str(v).strip()
    return None if s.lower() in NULLISH else s


def I(v, default=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def F(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def fetch_json(path, retries=4):
    url = API + path
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "PL-Results-Project/1.0",
                    "Accept": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Could not fetch {url}: {last}")


def batches(rows, size=500):
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def season_label(season_dir):
    return season_dir[:4] + "/" + season_dir[-2:]


def component_points(r, pos, season_dir):
    mins = I(r.get("minutes"))
    goals = I(r.get("goals_scored"))
    assists = I(r.get("assists"))
    cs = I(r.get("clean_sheets"))
    saves = I(r.get("saves"))
    ps = I(r.get("penalties_saved"))
    pm = I(r.get("penalties_missed"))
    yc = I(r.get("yellow_cards"))
    rc = I(r.get("red_cards"))
    og = I(r.get("own_goals"))
    gc = I(r.get("goals_conceded"))
    bonus = I(r.get("bonus"))
    dc = I(r.get("defensive_contribution"))
    year = int(season_dir[:4])

    appearance = 2 if mins >= 60 else (1 if mins > 0 else 0)
    goal_rate = (10 if year >= 2024 else 6) if pos == "GK" else {"DEF": 6, "MID": 5, "FWD": 4}.get(pos, 0)
    goal_points = goals * goal_rate
    assist_points = assists * 3
    clean_sheet_points = cs * (4 if pos in {"GK", "DEF"} else (1 if pos == "MID" else 0))
    save_points = saves // 3 if pos == "GK" else 0
    penalty_points = ps * 5 - pm * 2
    card_points = -yc - rc * 3
    own_goal_points = -og * 2
    goals_conceded_points = -(gc // 2) if pos in {"GK", "DEF"} else 0
    defensive_points = 0
    if year >= 2025:
        if pos == "DEF" and dc >= 10:
            defensive_points = 2
        elif pos in {"MID", "FWD"} and dc >= 12:
            defensive_points = 2

    calculated = sum([
        appearance,
        goal_points,
        assist_points,
        clean_sheet_points,
        save_points,
        penalty_points,
        card_points,
        own_goal_points,
        goals_conceded_points,
        defensive_points,
        bonus,
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
        "points_difference": I(r.get("total_points")) - calculated,
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/update_fpl_current.py 2026-27")
    season_dir = sys.argv[1]
    season = season_label(season_dir)

    print(f"=== Live official FPL update: {season} ===")
    bootstrap = fetch_json("/bootstrap-static/")
    fixtures = fetch_json("/fixtures/")

    teams = {I(t.get("id"), -1): canon_team(t.get("name")) for t in bootstrap.get("teams", [])}
    fixture_by_id = {I(f.get("id"), -1): f for f in fixtures}

    elements = []
    ignored_non_players = 0
    for e in bootstrap.get("elements", []):
        pos = PLAYER_POSITIONS.get(I(e.get("element_type"), -1))
        if not pos:
            ignored_non_players += 1
            continue
        elements.append((e, pos))

    canonical = []
    season_rows = []
    meta_by_id = {}
    for e, pos in elements:
        pid = str(I(e.get("id"), -1))
        code = str(I(e.get("code"), -1))
        if pid == "-1" or code == "-1":
            continue
        name = e.get("web_name") or " ".join(x for x in [e.get("first_name"), e.get("second_name")] if x)
        team_name = teams.get(I(e.get("team"), -1))
        meta_by_id[pid] = {"player_code": code, "player_name": name, "position": pos, "team_name": team_name}
        canonical.append({
            "player_code": code,
            "first_name": nullable(e.get("first_name")),
            "second_name": nullable(e.get("second_name")),
            "web_name": name,
            "birth_date": nullable(e.get("birth_date")),
            "opta_code": nullable(e.get("opta_code")),
        })
        season_rows.append({
            "season": season,
            "player_code": code,
            "player_id": pid,
            "team_code": nullable(e.get("team_code")),
            "team_name": team_name,
            "position": {"GK": "Goalkeeper", "DEF": "Defender", "MID": "Midfielder", "FWD": "Forward"}[pos],
        })

    for b in batches(canonical):
        sb.table("players").upsert(b, on_conflict="player_code").execute()
    for b in batches(season_rows):
        sb.table("player_seasons").upsert(b, on_conflict="season,player_code").execute()
    sb.rpc("backfill_player_codes_for_season", {"p_season": season}).execute()
    print(f"Players: {len(meta_by_id)}; ignored non-player elements: {ignored_non_players}")

    def get_history(item):
        e, pos = item
        pid = str(I(e.get("id"), -1))
        return pid, pos, fetch_json(f"/element-summary/{pid}/").get("history", [])

    histories = {}
    print("Fetching official per-fixture player history...")
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(get_history, item) for item in elements]
        done = 0
        for future in as_completed(futures):
            pid, pos, history = future.result()
            histories[pid] = (pos, history)
            done += 1
            if done % 100 == 0 or done == len(futures):
                print(f"  fetched {done}/{len(futures)} players")

    rows = []
    for pid, (pos, history) in histories.items():
        meta = meta_by_id.get(pid)
        if not meta:
            continue
        for r in history:
            fixture_id = I(r.get("fixture"), -1)
            gw = I(r.get("round"), -1)
            if fixture_id < 0 or gw < 0:
                continue
            fixture = fixture_by_id.get(fixture_id, {})
            was_home = bool(r.get("was_home"))
            team_id = I(fixture.get("team_h" if was_home else "team_a"), -1)
            opponent_id = I(r.get("opponent_team"), -1)
            row = {
                "season": season,
                "gameweek": gw,
                "fixture_id": fixture_id,
                "player_code": meta["player_code"],
                "player_id": pid,
                "player_name": meta["player_name"],
                "team_name": teams.get(team_id) or meta["team_name"],
                "position": pos,
                "kickoff_time": nullable(r.get("kickoff_time")),
                "opponent_team": teams.get(opponent_id),
                "was_home": was_home,
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
                "source": "official_fpl_api",
                **component_points(r, pos, season_dir),
            }
            rows.append(row)

    # The official element-summary history is already one row per player+fixture.
    for n, b in enumerate(batches(rows), 1):
        sb.table("fpl_player_match_stats").upsert(b, on_conflict="season,fixture_id,player_code").execute()
        if n % 10 == 0 or n * 500 >= len(rows):
            print(f"  uploaded {min(n * 500, len(rows))}/{len(rows)} fixture rows")

    print("Refreshing FPL aggregate caches...")
    sb.rpc("refresh_fpl_aggregate_caches").execute()

    mismatches = sum(1 for r in rows if r["points_difference"] != 0)
    missing_teams = sum(1 for r in rows if not r["team_name"])
    max_gw = max((r["gameweek"] for r in rows), default=0)
    finished_fixtures = len({r["fixture_id"] for r in rows})
    print(
        f"FPL fixture rows: {len(rows)}; finished fixtures represented: {finished_fixtures}; "
        f"latest GW: {max_gw}; missing team names: {missing_teams}; point-component mismatches: {mismatches}"
    )
    print("Live FPL update complete.")


if __name__ == "__main__":
    main()
