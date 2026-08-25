#!/usr/bin/env python3
"""Safely stage early Premier League Transfermarkt player-match data.

Targets 2012/13 through 2016/17. Uses exact fixture identity only, fixes known
team aliases, quarantines any season failing the >=20 appearances-per-match gate,
and NEVER matches players by name.

Identity rules:
- reuse existing verified Transfermarkt -> canonical player crosswalks;
- for players whose entire Transfermarkt PL appearance history ends before
  2016/17, create a namespaced canonical identity `tm:<source_player_id>`;
- players reaching the FPL era remain unresolved until the database fingerprint
  resolver verifies them.

This script stages source rows only. It never writes player_match_stats.
"""
import os
from collections import defaultdict
from supabase import create_client

import import_transfermarkt_history as core
import import_transfermarkt_history_cached as cache

SOURCE = "transfermarkt"
TARGET_YEARS = set(range(2012, 2017))
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

    target_seasons = {core.label_from_year(y) for y in TARGET_YEARS}

    canonical_key = {}
    expected_games = {}
    for season in sorted(target_seasons):
        rows = core.paged(
            sb, "canonical_matches",
            "canonical_match_id,season,match_date,home_team,away_team,home_score,away_score",
            {"season": season},
        )
        expected_games[season] = len(rows)
        for c in rows:
            k = (
                season, c.get("match_date"), c.get("home_team"), c.get("away_team"),
                core.I(c.get("home_score")), core.I(c.get("away_score")),
            )
            canonical_key[k] = c["canonical_match_id"]

    team_map = {}
    for r in core.paged(sb, "team_source_ids", "source_team_id,team_name,verified", {"source": SOURCE}):
        if r.get("verified"):
            team_map[str(r["source_team_id"])] = r["team_name"]

    source_games = {}
    new_team_map = {}
    match_maps = []
    source_counts = defaultdict(int)
    for g in cache.cached_iter_gz_csv("games"):
        if g.get("competition_id") != "GB1":
            continue
        y = core.I(g.get("season"))
        if y not in TARGET_YEARS:
            continue
        season = core.label_from_year(y)
        gid = str(g.get("game_id") or "")
        if not gid:
            continue
        source_counts[season] += 1
        hid, aid = str(g.get("home_club_id") or ""), str(g.get("away_club_id") or "")
        home = team_map.get(hid) or new_team_map.get(hid) or core.canon_team(g.get("home_club_name"))
        away = team_map.get(aid) or new_team_map.get(aid) or core.canon_team(g.get("away_club_name"))
        k = (
            season, core.txt(g.get("date")), home, away,
            core.I(g.get("home_club_goals")), core.I(g.get("away_club_goals")),
        )
        mid = canonical_key.get(k)
        source_games[gid] = {"season": season, "match_id": mid}
        if not mid:
            continue
        for sid, name in ((hid, home), (aid, away)):
            old = team_map.get(sid) or new_team_map.get(sid)
            if old and old != name:
                raise RuntimeError(f"Club ID {sid} maps inconsistently: {old} vs {name}")
            new_team_map[sid] = name
        match_maps.append({
            "source": SOURCE, "source_match_id": gid, "canonical_match_id": mid,
            "season": season, "mapping_method": "date_teams_score_verified", "verified": True,
        })

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

    target_apps = []
    app_count = defaultdict(int)
    future_fpl_era_players = set()
    for a in cache.cached_iter_gz_csv("appearances"):
        if a.get("competition_id") != "GB1":
            continue
        y = core.I(a.get("date", "")[:4]) if a.get("date") else None
        # Prefer source game season for target rows; for future-career detection the
        # appearance dataset date is sufficient and avoids retaining all later games.
        if y is not None and y >= 2016:
            pid0 = str(a.get("player_id") or "")
            if pid0:
                future_fpl_era_players.add(pid0)
        gid = str(a.get("game_id") or "")
        gm = source_games.get(gid)
        if not gm:
            continue
        pid = str(a.get("player_id") or "")
        if not pid:
            continue
        app_count[gid] += 1
        target_apps.append({
            "source": SOURCE,
            "source_match_id": gid,
            "source_player_id": pid,
            "season": gm["season"],
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

    usable = []
    print("\nEarly Transfermarkt completeness gate")
    print("Season   expected  source  mapped  games>=20 apps  status")
    print("-------  --------  ------  ------  --------------  ------")
    for season in sorted(target_seasons):
        gids = [gid for gid, gm in source_games.items() if gm["season"] == season]
        expected = expected_games.get(season, 0)
        mapped = sum(1 for gid in gids if source_games[gid].get("match_id"))
        with20 = sum(1 for gid in gids if app_count.get(gid, 0) >= 20)
        ok = expected > 0 and len(gids) == expected and mapped == expected and with20 == expected
        if ok:
            usable.append(season)
        print(f"{season:<7}  {expected:>8}  {len(gids):>6}  {mapped:>6}  {with20:>14}  {'OK' if ok else 'SKIP'}")

    usable_set = set(usable)
    target_apps = [a for a in target_apps if a["season"] in usable_set and a.get("match_id")]
    relevant_pids = {a["source_player_id"] for a in target_apps}
    relevant_gids = {a["source_match_id"] for a in target_apps}

    source_players = {}
    for p in cache.cached_iter_gz_csv("players"):
        pid = str(p.get("player_id") or "")
        if pid not in relevant_pids:
            continue
        source_players[pid] = {
            "name": core.txt(p.get("name")),
            "first_name": core.txt(p.get("first_name")),
            "last_name": core.txt(p.get("last_name")),
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

    verified = {}
    for r in core.paged(sb, "player_source_ids", "source_player_id,player_code,verified", {"source": SOURCE}):
        if r.get("verified"):
            verified[str(r["source_player_id"])] = str(r["player_code"])

    new_players = []
    new_maps = []
    for pid in sorted(relevant_pids):
        if pid in verified:
            continue
        if pid in future_fpl_era_players:
            continue
        code = core.source_player_code(pid)
        p = source_players.get(pid, {})
        new_players.append({
            "player_code": code,
            "first_name": p.get("first_name"),
            "second_name": p.get("last_name"),
            "web_name": p.get("name") or code,
            "birth_date": p.get("birth_date"),
        })
        new_maps.append({
            "source": SOURCE, "source_player_id": pid, "player_code": code,
            "mapping_method": "source_native_pre_fpl_identity", "verified": True,
            "source_note": "No Transfermarkt Premier League appearance from 2016/17 onward; stable source ID; no name matching",
        })
        verified[pid] = code

    for b in batches(new_players):
        sb.table("players").upsert(b, on_conflict="player_code").execute()
    for b in batches(new_maps):
        sb.table("player_source_ids").upsert(b, on_conflict="source,source_player_id").execute()

    for a in target_apps:
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

    for b in batches(target_apps):
        sb.table("source_player_match_stats").upsert(b, on_conflict="source,source_match_id,source_player_id").execute()

    # Add historical season memberships for already verified identities.
    by_player_season = defaultdict(list)
    for a in target_apps:
        if a.get("player_code"):
            by_player_season[(a["player_code"], a["season"])].append(a)
    added_memberships = 0
    for (code, season), rows in by_player_season.items():
        exists = sb.table("player_seasons").select("player_code").eq("season", season).eq("player_code", code).maybe_single().execute().data
        if exists:
            continue
        last = rows[-1]
        pos = source_players.get(last["source_player_id"], {}).get("position") or last.get("source_position")
        sb.table("player_seasons").insert({
            "season": season, "player_code": code,
            "player_id": core.source_player_code(last["source_player_id"]),
            "team_code": last.get("source_team_id"),
            "team_name": last.get("team_name"),
            "position": core.long_position(pos),
        }).execute()
        added_memberships += 1

    mapped = sum(1 for a in target_apps if a.get("player_code"))
    print(f"\nStaged {len(target_apps)} early source player-match rows; {mapped} already mapped; {len(target_apps)-mapped} unresolved.")
    print(f"Created {len(new_maps)} source-native pre-FPL player identities and {added_memberships} historical player-season memberships.")
    print("No live player_match_stats rows were changed. No player name matching was used.")


if __name__ == "__main__":
    main()
