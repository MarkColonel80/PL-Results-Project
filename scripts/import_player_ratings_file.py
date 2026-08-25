#!/usr/bin/env python3
"""Import authorised FotMob/Sofascore player-match rating exports into Supabase.

This script does NOT fetch provider websites/APIs. It only imports a local CSV supplied
through an authorised/licensed route.

Required CSV columns:
  provider, provider_match_id, provider_player_id, season, rating

Optional columns:
  match_id, player_code, provider_player_name, provider_team_id,
  provider_team_name, provider_position, match_date, shirt_number,
  is_starting, minutes, rating_scale_min, rating_scale_max, source_url

Identity rules:
- Never match a player by name.
- Existing verified provider-player crosswalks are used automatically.
- A new player crosswalk may be created only from canonical match + verified provider
  team ID + shirt number when exactly one lineup player matches.
- Provider names are stored only as audit/display metadata.
"""
import csv
import os
import sys
from collections import defaultdict
from supabase import create_client

PROVIDERS = {"fotmob", "sofascore"}


def text(v):
    s = str(v or "").strip()
    return s or None


def integer(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def number(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def boolean(v):
    s = str(v or "").strip().lower()
    if s in {"1", "true", "yes", "y"}:
        return True
    if s in {"0", "false", "no", "n"}:
        return False
    return None


def batches(rows, n=500):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/import_player_ratings_file.py /path/to/ratings.csv")
    path = sys.argv[1]
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
    sb = create_client(url, key)

    with open(path, newline="", encoding="utf-8-sig") as f:
        raw = list(csv.DictReader(f))
    if not raw:
        raise SystemExit("Ratings file is empty.")
    required = {"provider", "provider_match_id", "provider_player_id", "season", "rating"}
    missing = required - set(raw[0])
    if missing:
        raise SystemExit("Missing required CSV columns: " + ", ".join(sorted(missing)))

    providers = {str(r.get("provider") or "").strip().lower() for r in raw}
    bad_providers = sorted(providers - PROVIDERS)
    if bad_providers:
        raise SystemExit("Unsupported provider(s): " + ", ".join(bad_providers))

    # Load only small crosswalk tables; these are intentionally independent of names.
    player_maps = {}
    for r in sb.table("player_provider_ids").select(
        "provider,provider_player_id,player_code,verified"
    ).execute().data or []:
        if r.get("verified"):
            player_maps[(r["provider"], str(r["provider_player_id"]))] = str(r["player_code"])

    team_maps = {}
    for r in sb.table("team_provider_ids").select(
        "provider,provider_team_id,team_name,verified"
    ).execute().data or []:
        if r.get("verified"):
            team_maps[(r["provider"], str(r["provider_team_id"]))] = r["team_name"]

    match_maps = {}
    for r in sb.table("match_provider_ids").select(
        "provider,provider_match_id,match_id,verified"
    ).execute().data or []:
        if r.get("verified"):
            match_maps[(r["provider"], str(r["provider_match_id"]))] = r["match_id"]

    # Cache lineups lazily per canonical rich match only when shirt-number verification is possible.
    lineup_cache = {}
    def lineup_rows(match_id):
        if match_id not in lineup_cache:
            lineup_cache[match_id] = sb.table("lineups").select(
                "match_id,team_name,jersey_number,player_code"
            ).eq("match_id", match_id).execute().data or []
        return lineup_cache[match_id]

    out = []
    new_player_maps = {}
    new_match_maps = {}
    invalid = 0
    unresolved_players = set()
    unresolved_matches = set()

    for idx, r in enumerate(raw, start=2):
        provider = str(r.get("provider") or "").strip().lower()
        pmatch = text(r.get("provider_match_id"))
        pplayer = text(r.get("provider_player_id"))
        season = text(r.get("season"))
        rating = number(r.get("rating"))
        if provider not in PROVIDERS or not pmatch or not pplayer or not season or rating is None or not (0 <= rating <= 10):
            invalid += 1
            print(f"Skipping invalid row {idx}")
            continue

        supplied_match = text(r.get("match_id"))
        match_id = match_maps.get((provider, pmatch)) or supplied_match
        if supplied_match and (provider, pmatch) not in match_maps:
            new_match_maps[(provider, pmatch)] = {
                "provider": provider,
                "provider_match_id": pmatch,
                "match_id": supplied_match,
                "season": season,
                "mapping_method": "authorised_file_supplied",
                "verified": True,
                "source_note": "Canonical match ID supplied in authorised ratings import file",
            }
            match_maps[(provider, pmatch)] = supplied_match
            match_id = supplied_match
        if not match_id:
            unresolved_matches.add((provider, pmatch))

        supplied_code = text(r.get("player_code"))
        player_code = player_maps.get((provider, pplayer)) or supplied_code
        if supplied_code and (provider, pplayer) not in player_maps:
            new_player_maps[(provider, pplayer)] = {
                "provider": provider,
                "provider_player_id": pplayer,
                "player_code": supplied_code,
                "mapping_method": "authorised_file_supplied",
                "verified": True,
                "source_note": "Canonical player_code supplied in authorised ratings import file",
            }
            player_maps[(provider, pplayer)] = supplied_code
            player_code = supplied_code

        # No-name automatic identity: verified team ID + shirt number in a known canonical match.
        if not player_code and match_id:
            pteam = text(r.get("provider_team_id"))
            shirt = integer(r.get("shirt_number"))
            team_name = team_maps.get((provider, pteam)) if pteam else None
            if team_name and shirt is not None:
                candidates = {
                    str(x["player_code"])
                    for x in lineup_rows(match_id)
                    if x.get("player_code")
                    and x.get("team_name") == team_name
                    and integer(x.get("jersey_number")) == shirt
                }
                if len(candidates) == 1:
                    player_code = next(iter(candidates))
                    new_player_maps[(provider, pplayer)] = {
                        "provider": provider,
                        "provider_player_id": pplayer,
                        "player_code": player_code,
                        "mapping_method": "match_team_shirt_verified",
                        "verified": True,
                        "source_note": f"Unique canonical lineup match {match_id}, team {team_name}, shirt {shirt}",
                    }
                    player_maps[(provider, pplayer)] = player_code

        if not player_code:
            unresolved_players.add((provider, pplayer))

        out.append({
            "provider": provider,
            "provider_match_id": pmatch,
            "provider_player_id": pplayer,
            "season": season,
            "match_id": match_id,
            "player_code": player_code,
            "rating": rating,
            "rating_scale_min": number(r.get("rating_scale_min")),
            "rating_scale_max": number(r.get("rating_scale_max")),
            "source_url": text(r.get("source_url")),
            "provider_player_name": text(r.get("provider_player_name")),
            "provider_team_id": text(r.get("provider_team_id")),
            "provider_team_name": text(r.get("provider_team_name")),
            "provider_position": text(r.get("provider_position")),
            "match_date": text(r.get("match_date")),
            "shirt_number": integer(r.get("shirt_number")),
            "is_starting": boolean(r.get("is_starting")),
            "minutes": integer(r.get("minutes")),
        })

    # Validate explicit player codes before creating crosswalks.
    candidate_codes = {x["player_code"] for x in new_player_maps.values() if x.get("player_code")}
    valid_codes = set()
    if candidate_codes:
        codes = list(candidate_codes)
        for b in batches(codes, 200):
            rows = sb.table("players").select("player_code").in_("player_code", b).execute().data or []
            valid_codes.update(str(x["player_code"]) for x in rows)
    bad_codes = candidate_codes - valid_codes
    if bad_codes:
        raise SystemExit("Ratings file supplied unknown player_code value(s): " + ", ".join(sorted(bad_codes)[:20]))

    if new_match_maps:
        sb.table("match_provider_ids").upsert(list(new_match_maps.values()), on_conflict="provider,provider_match_id").execute()
    if new_player_maps:
        sb.table("player_provider_ids").upsert(list(new_player_maps.values()), on_conflict="provider,provider_player_id").execute()
    for b in batches(out):
        sb.table("player_match_ratings").upsert(
            b, on_conflict="provider,provider_match_id,provider_player_id"
        ).execute()

    mapped = sum(1 for x in out if x.get("player_code"))
    matched_matches = sum(1 for x in out if x.get("match_id"))
    print(
        f"Ratings import complete: {len(out)} rows; {mapped} player-mapped; "
        f"{matched_matches} match-mapped; {len(new_player_maps)} new verified player crosswalks; "
        f"{len(new_match_maps)} new verified match crosswalks; {invalid} invalid rows skipped."
    )
    if unresolved_players:
        print(f"Unresolved provider player IDs: {len(unresolved_players)} (stored without player_code; no name matching used).")
    if unresolved_matches:
        print(f"Unresolved provider match IDs: {len(unresolved_matches)} (stored without canonical match_id).")


if __name__ == "__main__":
    main()
