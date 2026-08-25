#!/usr/bin/env python3
"""Import true Premier League player-match stats from the CC0 Transfermarkt dataset.

Default target: 2012/13 through 2023/24. 2024/25 is intentionally excluded because
that source has a known appearance-completeness problem.

Principles:
- exact canonical fixture mapping only; no fuzzy match mapping
- NEVER match players by name
- player identity uses verified source-ID crosswalks, unique DOB+team+position, or
  an exact multi-match FPL fingerprint (minutes/goals/cards; never FPL assists)
- source-only pre-FPL players get a canonical namespaced ID `tm:<source_player_id>`
- unresolved source players stay in the raw staging table and are not promoted
- a season is imported only if every expected PL game maps and every game has at
  least 20 player appearance rows

Usage:
  python3 scripts/import_transfermarkt_history.py
  python3 scripts/import_transfermarkt_history.py --from 2012-13 --to 2023-24
  python3 scripts/import_transfermarkt_history.py --stage-only

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""
import csv
import gzip
import io
import os
import re
import sys
import urllib.request
from collections import defaultdict
from supabase import create_client

BASE = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
SOURCE = "transfermarkt"
UA = "PL-Results-Project transfermarkt-history/1.0"

TEAM_ALIASES = {
    "Bournemouth": "AFC Bournemouth",
    "Brighton and Hove Albion": "Brighton & Hove Albion",
    "Brighton & Hove Albion": "Brighton & Hove Albion",
    "Cardiff": "Cardiff City",
    "Charlton": "Charlton Athletic",
    "Huddersfield": "Huddersfield Town",
    "Hull": "Hull City",
    "Leicester": "Leicester City",
    "Luton Town": "Luton",
    "Manchester Utd": "Manchester United",
    "Man Utd": "Manchester United",
    "Man City": "Manchester City",
    "Newcastle": "Newcastle United",
    "Nottingham Forest": "Nottingham Forest",
    "Nott'm Forest": "Nottingham Forest",
    "Oldham Athletic": "Oldham",
    "QPR": "Queens Park Rangers",
    "Sheffield Wednesday": "Sheffield Wednesday",
    "Sheffield Utd": "Sheffield United",
    "Stoke": "Stoke City",
    "Swindon Town": "Swindon",
    "Tottenham": "Tottenham Hotspur",
    "Tottenham Hotspur": "Tottenham Hotspur",
    "West Brom": "West Bromwich Albion",
    "West Ham": "West Ham United",
    "Wimbledon FC": "Wimbledon",
    "Wolves": "Wolverhampton Wanderers",
}


def label_from_year(y):
    y = int(y)
    return f"{y}/{str(y+1)[-2:]}"


def parse_cli_season(s):
    m = re.match(r"^(\d{4})[-/](\d{2}|\d{4})$", s or "")
    if not m:
        raise SystemExit(f"Bad season {s!r}; use e.g. 2012-13")
    return int(m.group(1))


def I(v, default=None):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def txt(v):
    s = str(v or "").strip()
    return s or None


def canon_team(v):
    s = str(v or "").strip()
    if not s:
        return None
    if s in TEAM_ALIASES:
        return TEAM_ALIASES[s]
    # Team identity may use harmless formatting normalisation; player identity never does.
    if s.endswith(" FC"):
        s = s[:-3].strip()
    return TEAM_ALIASES.get(s, s)


def norm_position(v):
    s = str(v or "").strip().lower()
    if not s:
        return None
    if "goal" in s or s in {"gk", "gkp"}:
        return "GK"
    if "def" in s or "back" in s:
        return "DEF"
    if "mid" in s:
        return "MID"
    if "attack" in s or "forward" in s or "striker" in s or "winger" in s:
        return "FWD"
    return None


def long_position(p):
    return {"GK": "Goalkeeper", "DEF": "Defender", "MID": "Midfielder", "FWD": "Forward"}.get(p)


def starting_type(v):
    return str(v or "").strip().lower() == "starting_lineup"


def iter_gz_csv(name):
    url = f"{BASE}/{name}.csv.gz"
    print(f"Downloading/streaming {name}.csv.gz...")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv,*/*"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        with gzip.GzipFile(fileobj=resp) as gz:
            with io.TextIOWrapper(gz, encoding="utf-8-sig", newline="") as text_stream:
                yield from csv.DictReader(text_stream)


def paged(sb, table, cols, eq=None, gt=None, page=1000):
    out = []
    start = 0
    while True:
        q = sb.table(table).select(cols)
        for k, v in (eq or {}).items():
            q = q.eq(k, v)
        for k, v in (gt or {}).items():
            q = q.gt(k, v)
        rows = q.range(start, start + page - 1).execute().data or []
        out.extend(rows)
        if len(rows) < page:
            break
        start += page
    return out


def batches(rows, n=500):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]


def source_player_code(pid):
    return f"tm:{pid}"


def main():
    start_year, end_year, stage_only = 2012, 2023, False
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--from" and i + 1 < len(args):
            start_year = parse_cli_season(args[i+1]); i += 2
        elif args[i] == "--to" and i + 1 < len(args):
            end_year = parse_cli_season(args[i+1]); i += 2
        elif args[i] == "--stage-only":
            stage_only = True; i += 1
        else:
            raise SystemExit("Usage: python3 scripts/import_transfermarkt_history.py [--from 2012-13] [--to 2023-24] [--stage-only]")
    if end_year < start_year:
        raise SystemExit("--to must not be earlier than --from")
    if end_year >= 2024:
        raise SystemExit("Refusing 2024/25+ in v1: the source has a known 2024/25 appearance completeness issue.")

    target_years = set(range(start_year, end_year + 1))
    target_seasons = {label_from_year(y) for y in target_years}
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
    sb = create_client(url, key)

    # Canonical fixture universe for requested seasons.
    canonical_by_season = {}
    canonical_key = {}
    expected_games = {}
    for season in sorted(target_seasons):
        rows = paged(sb, "canonical_matches", "canonical_match_id,season,match_date,home_team,away_team,home_score,away_score", {"season": season})
        canonical_by_season[season] = rows
        expected_games[season] = len(rows)
        for c in rows:
            k = (season, c.get("match_date"), c.get("home_team"), c.get("away_team"), I(c.get("home_score")), I(c.get("away_score")))
            if k in canonical_key:
                raise RuntimeError(f"Duplicate canonical fixture key: {k}")
            canonical_key[k] = c["canonical_match_id"]

    # Existing verified team/player mappings.
    team_map = {}
    for r in paged(sb, "team_source_ids", "source,source_team_id,team_name,verified", {"source": SOURCE}):
        if r.get("verified"):
            team_map[str(r["source_team_id"])] = r["team_name"]
    player_map = {}
    for r in paged(sb, "player_source_ids", "source,source_player_id,player_code,verified", {"source": SOURCE}):
        if r.get("verified"):
            player_map[str(r["source_player_id"])] = str(r["player_code"])

    # Source games -> exact canonical fixtures. Team IDs learned from exact matches.
    source_games = {}
    source_game_counts = defaultdict(int)
    new_team_map = {}
    new_match_maps = []
    unresolved_games = defaultdict(list)
    for g in iter_gz_csv("games"):
        if g.get("competition_id") != "GB1":
            continue
        y = I(g.get("season"))
        if y not in target_years:
            continue
        season = label_from_year(y)
        gid = str(g.get("game_id") or "")
        if not gid:
            continue
        source_game_counts[season] += 1
        home_id, away_id = str(g.get("home_club_id") or ""), str(g.get("away_club_id") or "")
        home = team_map.get(home_id) or new_team_map.get(home_id) or canon_team(g.get("home_club_name"))
        away = team_map.get(away_id) or new_team_map.get(away_id) or canon_team(g.get("away_club_name"))
        k = (season, txt(g.get("date")), home, away, I(g.get("home_club_goals")), I(g.get("away_club_goals")))
        mid = canonical_key.get(k)
        if not mid:
            unresolved_games[season].append((gid, k))
            source_games[gid] = {"season": season, "match_id": None, "row": g}
            continue
        source_games[gid] = {"season": season, "match_id": mid, "row": g}
        for sid, cname in ((home_id, home), (away_id, away)):
            old = team_map.get(sid) or new_team_map.get(sid)
            if old and old != cname:
                raise RuntimeError(f"Transfermarkt club ID {sid} mapped inconsistently: {old} vs {cname}")
            new_team_map[sid] = cname
        new_match_maps.append({
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
    for b in batches(new_match_maps):
        sb.table("match_source_ids").upsert(b, on_conflict="source,source_match_id").execute()

    # Appearance rows. Keep source names only as metadata; never use them for mapping.
    source_apps = []
    app_count_by_game = defaultdict(int)
    relevant_player_ids = set()
    for a in iter_gz_csv("appearances"):
        if a.get("competition_id") != "GB1":
            continue
        gid = str(a.get("game_id") or "")
        gm = source_games.get(gid)
        if not gm:
            continue
        pid = str(a.get("player_id") or "")
        if not pid:
            continue
        app_count_by_game[gid] += 1
        relevant_player_ids.add(pid)
        source_apps.append({
            "source": SOURCE,
            "source_match_id": gid,
            "source_player_id": pid,
            "season": gm["season"],
            "match_id": gm["match_id"],
            "source_team_id": str(a.get("player_club_id") or "") or None,
            "team_name": team_map.get(str(a.get("player_club_id") or "")),
            "player_name": txt(a.get("player_name")),
            "minutes_played": I(a.get("minutes_played"), 0) or 0,
            "goals": I(a.get("goals"), 0) or 0,
            "assists": I(a.get("assists"), 0) or 0,
            "yellow_cards": I(a.get("yellow_cards"), 0) or 0,
            "red_cards": I(a.get("red_cards"), 0) or 0,
            "data_quality": "source_reported",
        })

    # Strict completeness gate.
    usable_seasons = []
    print("\nTransfermarkt completeness gate")
    print("Season   expected  source  mapped  games>=20 apps  status")
    print("-------  --------  ------  ------  --------------  ------")
    for season in sorted(target_seasons):
        expected = expected_games.get(season, 0)
        games = [gid for gid, gm in source_games.items() if gm["season"] == season]
        mapped = sum(1 for gid in games if source_games[gid]["match_id"])
        with20 = sum(1 for gid in games if app_count_by_game.get(gid, 0) >= 20)
        ok = expected > 0 and len(games) == expected and mapped == expected and with20 == expected
        status = "OK" if ok else "SKIP"
        if ok:
            usable_seasons.append(season)
        print(f"{season:<7}  {expected:>8}  {len(games):>6}  {mapped:>6}  {with20:>14}  {status}")
    if not usable_seasons:
        raise RuntimeError("No requested season passed the strict completeness gate; nothing will be imported.")
    skipped = sorted(target_seasons - set(usable_seasons))
    if skipped:
        print("Skipping incomplete/unmapped seasons: " + ", ".join(skipped))

    usable_set = set(usable_seasons)
    source_apps = [a for a in source_apps if a["season"] in usable_set and a.get("match_id")]
    relevant_player_ids = {a["source_player_id"] for a in source_apps}
    relevant_game_ids = {a["source_match_id"] for a in source_apps}

    # Source player metadata (DOB and broad position are identity evidence; names are not).
    source_players = {}
    for p in iter_gz_csv("players"):
        pid = str(p.get("player_id") or "")
        if pid not in relevant_player_ids:
            continue
        source_players[pid] = {
            "name": txt(p.get("name")),
            "first_name": txt(p.get("first_name")),
            "last_name": txt(p.get("last_name")),
            "birth_date": txt(p.get("date_of_birth")),
            "position": norm_position(p.get("position") or p.get("sub_position")),
            "source_url": txt(p.get("url")),
        }

    # Lineup metadata gives starting status, shirt and match position without names.
    lineup_meta = {}
    print("Streaming game_lineups.csv.gz for starts/shirt numbers...")
    for l in iter_gz_csv("game_lineups"):
        gid = str(l.get("game_id") or "")
        if gid not in relevant_game_ids:
            continue
        pid = str(l.get("player_id") or "")
        if not pid:
            continue
        lineup_meta[(gid, pid)] = {
            "is_starting": starting_type(l.get("type")),
            "shirt_number": I(l.get("number")),
            "position": norm_position(l.get("position")),
        }

    for a in source_apps:
        p = source_players.get(a["source_player_id"], {})
        lm = lineup_meta.get((a["source_match_id"], a["source_player_id"]), {})
        a["birth_date"] = p.get("birth_date")
        a["source_position"] = lm.get("position") or p.get("position")
        a["shirt_number"] = lm.get("shirt_number")
        a["is_starting"] = lm.get("is_starting")
        a["source_url"] = p.get("source_url")
        if not a.get("player_name"):
            a["player_name"] = p.get("name")

    # Canonical player metadata and season memberships for identity matching.
    canonical_players = {str(r["player_code"]): r for r in paged(sb, "players", "player_code,birth_date")}
    season_players = defaultdict(list)
    for season in usable_seasons:
        for ps in paged(sb, "player_seasons", "season,player_code,team_name,position", {"season": season}):
            code = str(ps["player_code"])
            meta = canonical_players.get(code, {})
            season_players[season].append({
                "player_code": code,
                "birth_date": txt(meta.get("birth_date")),
                "team_name": ps.get("team_name"),
                "position": norm_position(ps.get("position")),
            })

    apps_by_player = defaultdict(list)
    for a in source_apps:
        apps_by_player[a["source_player_id"]].append(a)

    # First mapping pass: unique DOB + position + one of the verified season clubs.
    new_player_maps = {}
    for pid, apps in apps_by_player.items():
        if pid in player_map:
            continue
        sp = source_players.get(pid, {})
        dob, pos = sp.get("birth_date"), sp.get("position")
        if not dob or not pos:
            continue
        evidence_sets = []
        by_season = defaultdict(list)
        for a in apps:
            by_season[a["season"]].append(a)
        for season, rows in by_season.items():
            clubs = {r.get("team_name") for r in rows if r.get("team_name")}
            if not clubs:
                continue
            cand = {
                r["player_code"] for r in season_players.get(season, [])
                if r.get("birth_date") == dob and r.get("position") == pos and r.get("team_name") in clubs
            }
            if cand:
                evidence_sets.append(cand)
        if not evidence_sets:
            continue
        candidates = set.intersection(*evidence_sets)
        if len(candidates) == 1:
            code = next(iter(candidates))
            player_map[pid] = code
            new_player_maps[pid] = {
                "source": SOURCE, "source_player_id": pid, "player_code": code,
                "mapping_method": "dob_team_position_unique", "verified": True,
                "source_note": "Unique across Transfermarkt DOB + verified PL club + broad position; no name matching",
            }

    # Second pass: exact FPL fixture fingerprints for unresolved players in 2016/17+.
    # We intentionally do not compare assists because FPL assist rules differ from football assists.
    fpl_match_map = {}
    for season in usable_seasons:
        if int(season[:4]) < 2016:
            continue
        for r in paged(sb, "match_source_ids", "source_match_id,canonical_match_id", {"source": "fpl_fixture", "season": season}):
            try:
                fixture = int(str(r["source_match_id"]).split(":", 1)[1])
                fpl_match_map[(season, fixture)] = r["canonical_match_id"]
            except Exception:
                pass

    fpl_by_player = defaultdict(dict)
    fpl_codes_by_season = defaultdict(set)
    for season in usable_seasons:
        if int(season[:4]) < 2016:
            continue
        rows = paged(sb, "fpl_player_match_stats", "season,fixture_id,player_code,minutes,goals_scored,yellow_cards,red_cards", {"season": season}, {"minutes": 0})
        for r in rows:
            mid = fpl_match_map.get((season, I(r.get("fixture_id"))))
            if not mid:
                continue
            code = str(r["player_code"])
            fpl_by_player[(season, code)][mid] = (
                I(r.get("minutes"), 0) or 0, I(r.get("goals_scored"), 0) or 0,
                I(r.get("yellow_cards"), 0) or 0, I(r.get("red_cards"), 0) or 0,
            )
            fpl_codes_by_season[season].add(code)

    for pid, apps in apps_by_player.items():
        if pid in player_map:
            continue
        by_season = defaultdict(list)
        for a in apps:
            if int(a["season"][:4]) >= 2016:
                by_season[a["season"]].append(a)
        if not by_season:
            continue
        # Candidate codes must fit team + broad position in every evidence season where possible.
        evidence = []
        source_pos = source_players.get(pid, {}).get("position")
        for season, rows in by_season.items():
            clubs = {r.get("team_name") for r in rows if r.get("team_name")}
            cand = {
                r["player_code"] for r in season_players.get(season, [])
                if (not source_pos or r.get("position") == source_pos)
                and (not clubs or r.get("team_name") in clubs)
            }
            if cand:
                evidence.append(cand)
        if not evidence:
            continue
        candidates = set.intersection(*evidence)
        matches = []
        for code in candidates:
            total_comparable = 0
            ok = True
            for season, rows in by_season.items():
                src = {
                    a["match_id"]: (a["minutes_played"], a["goals"], a["yellow_cards"], a["red_cards"])
                    for a in rows if a.get("match_id")
                }
                fp = fpl_by_player.get((season, code), {})
                # Only compare canonical fixtures for which an FPL fixture crosswalk exists.
                universe = {m for (s, _), m in fpl_match_map.items() if s == season}
                src2 = {m: v for m, v in src.items() if m in universe}
                fp2 = {m: v for m, v in fp.items() if m in universe}
                if set(src2) != set(fp2):
                    ok = False; break
                for m, sig in src2.items():
                    total_comparable += 1
                    if fp2.get(m) != sig:
                        ok = False; break
                if not ok:
                    break
            if ok and total_comparable >= 3:
                matches.append(code)
        if len(matches) == 1:
            code = matches[0]
            player_map[pid] = code
            new_player_maps[pid] = {
                "source": SOURCE, "source_player_id": pid, "player_code": code,
                "mapping_method": "exact_multi_match_fingerprint", "verified": True,
                "source_note": "Exact canonical match-set + minutes + goals + cards across >=3 FPL-era appearances; no names/assists used",
            }

    # Third pass: source-only players whose entire PL appearance history ends before FPL began.
    new_canonical_players = []
    for pid, apps in apps_by_player.items():
        if pid in player_map:
            continue
        max_year = max(int(a["season"][:4]) for a in apps)
        if max_year >= 2016:
            continue
        code = source_player_code(pid)
        p = source_players.get(pid, {})
        player_map[pid] = code
        new_canonical_players.append({
            "player_code": code,
            "first_name": p.get("first_name"),
            "second_name": p.get("last_name"),
            "web_name": p.get("name") or code,
            "birth_date": p.get("birth_date"),
        })
        new_player_maps[pid] = {
            "source": SOURCE, "source_player_id": pid, "player_code": code,
            "mapping_method": "source_native_pre_fpl_identity", "verified": True,
            "source_note": "Player has no Transfermarkt PL appearance in FPL era; canonical identity namespaced from stable source ID",
        }

    for b in batches(new_canonical_players):
        sb.table("players").upsert(b, on_conflict="player_code").execute()
    for b in batches(list(new_player_maps.values())):
        sb.table("player_source_ids").upsert(b, on_conflict="source,source_player_id").execute()

    # Add pre-FPL season memberships from verified source IDs. Team is last appearance team by date/game order.
    pre_season_rows = []
    for pid, apps in apps_by_player.items():
        code = player_map.get(pid)
        if not code:
            continue
        grouped = defaultdict(list)
        for a in apps:
            if int(a["season"][:4]) < 2016:
                grouped[a["season"]].append(a)
        for season, rows in grouped.items():
            last = rows[-1]
            pos = source_players.get(pid, {}).get("position") or last.get("source_position")
            pre_season_rows.append({
                "season": season, "player_code": code, "player_id": source_player_code(pid),
                "team_code": last.get("source_team_id"), "team_name": last.get("team_name"),
                "position": long_position(pos),
            })
    # Only insert if absent; never overwrite an FPL-era player_seasons identity.
    for r in pre_season_rows:
        exists = sb.table("player_seasons").select("player_code").eq("season", r["season"]).eq("player_code", r["player_code"]).maybe_single().execute().data
        if not exists:
            sb.table("player_seasons").insert(r).execute()

    # Stage every complete source appearance, whether mapped or not.
    for a in source_apps:
        a["player_code"] = player_map.get(a["source_player_id"])
    for b in batches(source_apps):
        sb.table("source_player_match_stats").upsert(b, on_conflict="source,source_match_id,source_player_id").execute()

    mapped_rows = [a for a in source_apps if a.get("player_code")]
    unresolved_rows = len(source_apps) - len(mapped_rows)
    print(f"\nStaged {len(source_apps)} source player-match rows; {len(mapped_rows)} mapped; {unresolved_rows} unresolved.")
    print(f"New verified player crosswalks: {len(new_player_maps)} ({len(new_canonical_players)} source-native pre-FPL identities).")

    if stage_only:
        print("Stage-only requested: canonical player_match_stats not changed.")
        return

    # Promote verified source rows into true football match stats. Never overwrite rich_core rows.
    promoted = []
    existing_rich_keys = set()
    for season in usable_seasons:
        for r in paged(sb, "player_match_stats", "match_id,player_code,source", {"season": season}):
            if r.get("source") == "rich_core" and r.get("player_code"):
                existing_rich_keys.add((r["match_id"], str(r["player_code"])))
    for a in mapped_rows:
        key2 = (a["match_id"], str(a["player_code"]))
        if key2 in existing_rich_keys:
            continue
        promoted.append({
            "season": a["season"], "gameweek": None, "match_id": a["match_id"],
            "player_id": source_player_code(a["source_player_id"]),
            "player_code": a["player_code"], "player_name": a.get("player_name"),
            "team_name": a.get("team_name"), "minutes_played": a.get("minutes_played"),
            "is_starting": a.get("is_starting"), "goals": a.get("goals", 0), "assists": a.get("assists", 0),
            "xg": None, "xa": None, "shots": None, "shots_on_target": None, "chances_created": None,
            "yellow_cards": a.get("yellow_cards", 0), "red_cards": a.get("red_cards", 0),
            "source": SOURCE, "source_match_id": a["source_match_id"],
            "source_player_id": a["source_player_id"], "data_quality": "source_reported_verified_identity",
        })

    # Repeat-safe: remove only our source rows for imported seasons, leaving richer sources untouched.
    for season in usable_seasons:
        sb.table("player_match_stats").delete().eq("season", season).eq("source", SOURCE).execute()
    for b in batches(promoted):
        sb.table("player_match_stats").insert(b).execute()

    print(f"Promoted {len(promoted)} verified Transfermarkt rows into player_match_stats.")
    print("Imported seasons: " + ", ".join(usable_seasons))
    print("No player name matching was used.")


if __name__ == "__main__":
    main()
