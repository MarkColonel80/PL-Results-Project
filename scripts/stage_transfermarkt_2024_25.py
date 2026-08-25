#!/usr/bin/env python3
"""Safely stage Transfermarkt Premier League player-match data for 2024/25.

The coverage audit has verified 380/380 Premier League matches and >=20
appearance rows for every match. This script:
- maps fixtures exactly to canonical matches;
- reuses only already-verified Transfermarkt player crosswalks;
- stages all source appearances for later strict identity resolution;
- never matches players by name;
- never writes player_match_stats.
"""
import os
from collections import defaultdict
from supabase import create_client

import import_transfermarkt_history as core
import import_transfermarkt_history_cached as cache

SOURCE = "transfermarkt"
SEASON_YEAR = 2024
SEASON = "2024/25"
core.TEAM_ALIASES["Sunderland AFC"] = "Sunderland"


def batches(rows, n=500):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
    sb = create_client(url, key)

    canonical_rows = core.paged(
        sb, "canonical_matches",
        "canonical_match_id,season,match_date,home_team,away_team,home_score,away_score",
        {"season": SEASON},
    )
    if len(canonical_rows) != 380:
        raise RuntimeError(f"Expected 380 canonical matches for {SEASON}, found {len(canonical_rows)}")
    canonical_key = {
        (
            SEASON, c.get("match_date"), c.get("home_team"), c.get("away_team"),
            core.I(c.get("home_score")), core.I(c.get("away_score")),
        ): c["canonical_match_id"]
        for c in canonical_rows
    }

    team_map = {}
    for r in core.paged(sb, "team_source_ids", "source_team_id,team_name,verified", {"source": SOURCE}):
        if r.get("verified"):
            team_map[str(r["source_team_id"])] = r["team_name"]

    source_games = {}
    new_team_map = {}
    match_maps = []
    for g in cache.cached_iter_gz_csv("games"):
        if g.get("competition_id") != "GB1" or core.I(g.get("season")) != SEASON_YEAR:
            continue
        gid = str(g.get("game_id") or "")
        if not gid:
            continue
        hid = str(g.get("home_club_id") or "")
        aid = str(g.get("away_club_id") or "")
        home = team_map.get(hid) or new_team_map.get(hid) or core.canon_team(g.get("home_club_name"))
        away = team_map.get(aid) or new_team_map.get(aid) or core.canon_team(g.get("away_club_name"))
        key2 = (
            SEASON, core.txt(g.get("date")), home, away,
            core.I(g.get("home_club_goals")), core.I(g.get("away_club_goals")),
        )
        mid = canonical_key.get(key2)
        source_games[gid] = {"match_id": mid}
        if not mid:
            continue
        for sid, name in ((hid, home), (aid, away)):
            old = team_map.get(sid) or new_team_map.get(sid)
            if old and old != name:
                raise RuntimeError(f"Club ID {sid} maps inconsistently: {old} vs {name}")
            new_team_map[sid] = name
        match_maps.append({
            "source": SOURCE, "source_match_id": gid, "canonical_match_id": mid,
            "season": SEASON, "mapping_method": "date_teams_score_verified", "verified": True,
        })

    mapped_games = sum(1 for g in source_games.values() if g.get("match_id"))
    if len(source_games) != 380 or mapped_games != 380:
        raise RuntimeError(f"Fixture gate failed: source={len(source_games)}, mapped={mapped_games}, expected=380")

    if new_team_map:
        rows = [{
            "source": SOURCE, "source_team_id": sid, "team_name": name,
            "mapping_method": "exact_fixture_verified", "verified": True,
            "source_note": "Learned from exact Premier League fixture mapping",
        } for sid, name in new_team_map.items()]
        for b in batches(rows):
            sb.table("team_source_ids").upsert(b, on_conflict="source,source_team_id").execute()
        team_map.update(new_team_map)
    for b in batches(match_maps):
        sb.table("match_source_ids").upsert(b, on_conflict="source,source_match_id").execute()

    apps = []
    app_count = defaultdict(int)
    relevant_pids = set()
    relevant_gids = set(source_games)
    for a in cache.cached_iter_gz_csv("appearances"):
        if a.get("competition_id") != "GB1":
            continue
        gid = str(a.get("game_id") or "")
        gm = source_games.get(gid)
        if not gm:
            continue
        pid = str(a.get("player_id") or "")
        if not pid:
            continue
        app_count[gid] += 1
        relevant_pids.add(pid)
        apps.append({
            "source": SOURCE,
            "source_match_id": gid,
            "source_player_id": pid,
            "season": SEASON,
            "match_id": gm["match_id"],
            "source_team_id": str(a.get("player_club_id") or "") or None,
            "team_name": team_map.get(str(a.get("player_club_id") or "")),
            "player_name": core.txt(a.get("player_name")),
            "minutes_played": core.I(a.get("minutes_played"), 0) or 0,
            "goals": core.I(a.get("goals"), 0) or 0,
            "assists": core.I(a.get("assists"), 0) or 0,
            "yellow_cards": core.I(a.get("yellow_cards"), 0) or 0,
            "red_cards": core.I(a.get("red_cards"), 0) or 0,
            "data_quality": "source_reported",
        })

    with20 = sum(1 for gid in relevant_gids if app_count.get(gid, 0) >= 20)
    min_apps = min((app_count.get(gid, 0) for gid in relevant_gids), default=0)
    print(f"2024/25 completeness: 380 source, {mapped_games} mapped, {with20} games>=20 apps, min apps={min_apps}")
    if with20 != 380:
        raise RuntimeError("2024/25 appearance completeness gate failed; refusing to stage")

    source_players = {}
    for p in cache.cached_iter_gz_csv("players"):
        pid = str(p.get("player_id") or "")
        if pid not in relevant_pids:
            continue
        source_players[pid] = {
            "name": core.txt(p.get("name")),
            "birth_date": core.txt(p.get("date_of_birth")),
            "position": core.norm_position(p.get("position") or p.get("sub_position")),
            "source_url": core.txt(p.get("url")),
        }

    lineup_meta = {}
    for l in cache.cached_iter_gz_csv("game_lineups"):
        gid = str(l.get("game_id") or "")
        if gid not in relevant_gids:
            continue
        pid = str(l.get("player_id") or "")
        if not pid:
            continue
        lineup_meta[(gid, pid)] = {
            "is_starting": core.starting_type(l.get("type")),
            "shirt_number": core.I(l.get("number")),
            "position": core.norm_position(l.get("position")),
        }

    verified = {
        str(r["source_player_id"]): str(r["player_code"])
        for r in core.paged(sb, "player_source_ids", "source_player_id,player_code,verified", {"source": SOURCE})
        if r.get("verified")
    }

    for a in apps:
        p = source_players.get(a["source_player_id"], {})
        lm = lineup_meta.get((a["source_match_id"], a["source_player_id"]), {})
        a["birth_date"] = p.get("birth_date")
        a["source_position"] = lm.get("position") or p.get("position")
        a["shirt_number"] = lm.get("shirt_number")
        a["is_starting"] = lm.get("is_starting")
        a["source_url"] = p.get("source_url")
        if not a.get("player_name"):
            a["player_name"] = p.get("name")
        a["player_code"] = verified.get(a["source_player_id"])

    for b in batches(apps):
        sb.table("source_player_match_stats").upsert(b, on_conflict="source,source_match_id,source_player_id").execute()

    mapped_rows = sum(1 for a in apps if a.get("player_code"))
    mapped_players = len({a["source_player_id"] for a in apps if a.get("player_code")})
    print(f"Staged {len(apps)} rows; {mapped_rows} already mapped; {len(apps)-mapped_rows} unresolved.")
    print(f"Players: {len(relevant_pids)} source; {mapped_players} already mapped.")
    print("No live player_match_stats rows were changed. No player name matching was used.")


if __name__ == "__main__":
    main()
