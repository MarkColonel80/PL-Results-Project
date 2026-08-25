#!/usr/bin/env python3
"""Repair early Transfermarkt staging after the first safe-stage pass.

This script fixes the pre-FPL career test by using the Transfermarkt season field
rather than calendar year. It never matches players by name and never writes
player_match_stats.

It reuses the cached games/appearances files, identifies Transfermarkt players
whose Premier League career genuinely ends before 2016/17, creates a namespaced
canonical identity tm:<source_player_id>, records the verified source crosswalk,
and updates staged source rows only.
"""
import os
from collections import defaultdict
from supabase import create_client

import import_transfermarkt_history as core
import import_transfermarkt_history_cached as cache

SOURCE = "transfermarkt"
EARLY_SEASONS = {"2012/13", "2013/14", "2015/16"}


def batches(rows, n=500):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]


def paged(sb, table, cols, eq=None, page=1000):
    out = []
    start = 0
    while True:
        q = sb.table(table).select(cols)
        for k, v in (eq or {}).items():
            q = q.eq(k, v)
        rows = q.range(start, start + page - 1).execute().data or []
        out.extend(rows)
        if len(rows) < page:
            break
        start += page
    return out


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
    sb = create_client(url, key)

    # Source game -> source season. FPL era begins with the 2016/17 season,
    # whose Transfermarkt season value is 2016.
    game_season = {}
    for g in cache.cached_iter_gz_csv("games"):
        if g.get("competition_id") != "GB1":
            continue
        gid = str(g.get("game_id") or "")
        y = core.I(g.get("season"))
        if gid and y is not None:
            game_season[gid] = y

    fpl_era_source_players = set()
    for a in cache.cached_iter_gz_csv("appearances"):
        if a.get("competition_id") != "GB1":
            continue
        gid = str(a.get("game_id") or "")
        if game_season.get(gid, -1) >= 2016:
            pid = str(a.get("player_id") or "")
            if pid:
                fpl_era_source_players.add(pid)

    existing = {
        str(r["source_player_id"]): str(r["player_code"])
        for r in paged(sb, "player_source_ids", "source_player_id,player_code", {"source": SOURCE})
    }

    staged = []
    for season in sorted(EARLY_SEASONS):
        staged.extend(paged(
            sb,
            "source_player_match_stats",
            "season,source_player_id,player_name,birth_date,source_position",
            {"source": SOURCE, "season": season},
        ))

    meta = {}
    for r in staged:
        pid = str(r.get("source_player_id") or "")
        if not pid:
            continue
        m = meta.setdefault(pid, {
            "player_name": r.get("player_name"),
            "birth_date": r.get("birth_date"),
            "source_position": r.get("source_position"),
        })
        if not m.get("player_name") and r.get("player_name"):
            m["player_name"] = r.get("player_name")
        if not m.get("birth_date") and r.get("birth_date"):
            m["birth_date"] = r.get("birth_date")
        if not m.get("source_position") and r.get("source_position"):
            m["source_position"] = r.get("source_position")

    new_ids = [
        pid for pid in sorted(meta)
        if pid not in existing and pid not in fpl_era_source_players
    ]

    player_rows = []
    map_rows = []
    for pid in new_ids:
        code = core.source_player_code(pid)
        m = meta[pid]
        player_rows.append({
            "player_code": code,
            "first_name": None,
            "second_name": None,
            "web_name": m.get("player_name") or code,
            "birth_date": m.get("birth_date"),
        })
        map_rows.append({
            "source": SOURCE,
            "source_player_id": pid,
            "player_code": code,
            "mapping_method": "source_native_pre_fpl_identity",
            "verified": True,
            "source_note": "No Transfermarkt Premier League appearance in season 2016/17 or later; stable source ID; no name matching",
        })

    for b in batches(player_rows):
        sb.table("players").upsert(b, on_conflict="player_code").execute()
    for b in batches(map_rows):
        sb.table("player_source_ids").upsert(b, on_conflict="source,source_player_id").execute()

    updated = 0
    for pid in new_ids:
        code = core.source_player_code(pid)
        resp = (
            sb.table("source_player_match_stats")
            .update({"player_code": code})
            .eq("source", SOURCE)
            .eq("source_player_id", pid)
            .execute()
        )
        updated += len(resp.data or [])

    print(f"Created {len(new_ids)} additional source-native pre-FPL identities.")
    print(f"Updated {updated} staged player-match rows with canonical player codes.")
    print("No live player_match_stats rows were changed. No player name matching was used.")


if __name__ == "__main__":
    main()
