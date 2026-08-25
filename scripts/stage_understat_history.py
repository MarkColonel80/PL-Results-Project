#!/usr/bin/env python3
"""Stage MIT-licensed Understat per-match data for Premier League history.

Source dataset:
  https://www.kaggle.com/datasets/codytipton/player-stats-per-game-understat

The public Kaggle dataset contains Understat provider IDs and match-level player
statistics from 2014/15 through 2024/25. This importer deliberately DOES NOT use
names to establish player identity.

What this script does:
- downloads/caches the public Kaggle ZIP (or reuses a manually downloaded ZIP)
- maps Understat fixtures to canonical Premier League fixtures by exact
  season/date/teams/score
- learns Understat team IDs only from those exact fixture matches
- requires every requested season to have all expected fixtures mapped and every
  fixture to have at least 20 player rows
- stages player rows in source_player_match_stats with provider-native IDs and
  advanced fields (xG/xA/shots/key passes/xGChain/xGBuildup)
- writes verified match/team source-ID crosswalks
- DOES NOT create player crosswalks and DOES NOT write player_match_stats

Player identity is resolved later from provider IDs + match-history fingerprints.
Names are display metadata only.

Usage:
  python3 scripts/stage_understat_history.py
  python3 scripts/stage_understat_history.py --from 2014-15 --to 2024-25

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""

import csv
import io
import os
import pathlib
import re
import time
import urllib.error
import urllib.request
import zipfile
from collections import defaultdict

from supabase import create_client

import import_transfermarkt_history as core

SOURCE = "understat"
KAGGLE_PAGE = "https://www.kaggle.com/datasets/codytipton/player-stats-per-game-understat"
KAGGLE_DOWNLOAD = "https://www.kaggle.com/api/v1/datasets/download/codytipton/player-stats-per-game-understat"
CACHE = pathlib.Path(__file__).resolve().parents[1] / ".cache" / "understat_kaggle"
ZIP_PATH = CACHE / "player-stats-per-game-understat.zip"
PART_PATH = CACHE / "player-stats-per-game-understat.zip.part"
UA = "PL-Results-Project understat-history/1.0"
CHUNK = 1024 * 1024
RETRIES = 8

# Understat uses shortened club labels in some seasons. Team-name normalisation is
# permitted for fixture identity; player names are never used for identity.
core.TEAM_ALIASES.update({
    "Bournemouth": "AFC Bournemouth",
    "Brighton": "Brighton & Hove Albion",
    "Huddersfield": "Huddersfield Town",
    "Hull": "Hull City",
    "Leicester": "Leicester City",
    "Manchester United": "Manchester United",
    "Manchester City": "Manchester City",
    "Newcastle United": "Newcastle United",
    "Norwich": "Norwich City",
    "QPR": "Queens Park Rangers",
    "Sheffield United": "Sheffield United",
    "Stoke": "Stoke City",
    "Swansea": "Swansea City",
    "Tottenham": "Tottenham Hotspur",
    "West Brom": "West Bromwich Albion",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
})


def F(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def sid(v):
    n = core.I(v)
    return str(n) if n is not None else None


def season_year(v):
    s = str(v or "").strip()
    m = re.match(r"^(\d{4})", s)
    return int(m.group(1)) if m else None


def parse_args():
    start, end = 2014, 2024
    args = os.sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--from" and i + 1 < len(args):
            start = core.parse_cli_season(args[i + 1]); i += 2
        elif args[i] == "--to" and i + 1 < len(args):
            end = core.parse_cli_season(args[i + 1]); i += 2
        else:
            raise SystemExit("Usage: python3 scripts/stage_understat_history.py [--from 2014-15] [--to 2024-25]")
    if start < 2014 or end > 2024 or end < start:
        raise SystemExit("Understat staging currently supports 2014/15 through 2024/25.")
    return start, end


def ensure_zip():
    CACHE.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists() and ZIP_PATH.stat().st_size > 0:
        try:
            with zipfile.ZipFile(ZIP_PATH) as zf:
                bad = zf.testzip()
                if bad is None:
                    print(f"Using cached Understat dataset ZIP ({ZIP_PATH.stat().st_size/1024/1024:.1f} MB)")
                    return ZIP_PATH
        except Exception:
            pass
        ZIP_PATH.unlink(missing_ok=True)

    for attempt in range(1, RETRIES + 1):
        existing = PART_PATH.stat().st_size if PART_PATH.exists() else 0
        headers = {"User-Agent": UA, "Accept": "application/zip,application/octet-stream,*/*"}
        if existing:
            headers["Range"] = f"bytes={existing}-"
        try:
            print(f"Downloading public Understat dataset (attempt {attempt}/{RETRIES})..." +
                  (f" resuming at {existing/1024/1024:.1f} MB" if existing else ""))
            req = urllib.request.Request(KAGGLE_DOWNLOAD, headers=headers)
            with urllib.request.urlopen(req, timeout=180) as resp:
                status = getattr(resp, "status", None)
                mode = "ab" if existing and status == 206 else "wb"
                if mode == "wb":
                    existing = 0
                with open(PART_PATH, mode) as out:
                    while True:
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        out.write(chunk)
            with zipfile.ZipFile(PART_PATH) as zf:
                bad = zf.testzip()
                if bad is not None:
                    raise RuntimeError(f"Corrupt ZIP member: {bad}")
            PART_PATH.replace(ZIP_PATH)
            print(f"  downloaded {ZIP_PATH.stat().st_size/1024/1024:.1f} MB")
            return ZIP_PATH
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise SystemExit(
                    "Kaggle blocked the unauthenticated download. Download the public dataset ZIP from\n"
                    f"  {KAGGLE_PAGE}\n"
                    f"and save it as\n  {ZIP_PATH}\nthen run this command again."
                )
            err = exc
        except Exception as exc:
            err = exc
        kept = PART_PATH.stat().st_size if PART_PATH.exists() else 0
        if attempt == RETRIES:
            raise RuntimeError(f"Could not download Understat dataset: {err}")
        print(f"  download/read failed: {err}; kept {kept/1024/1024:.1f} MB, retrying...")
        time.sleep(min(2 * attempt, 10))
    raise RuntimeError("Could not download Understat dataset")


def find_member(zf, needle):
    matches = [n for n in zf.namelist() if n.lower().endswith(".csv") and needle in pathlib.PurePosixPath(n).name.lower()]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one CSV matching {needle!r}; found {matches}")
    return matches[0]


def iter_member_rows(zf, member):
    with zf.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        for row in csv.DictReader(text):
            yield {str(k).strip(): v for k, v in row.items() if k is not None}


def is_epl_game(row):
    league = str(row.get("league") or "").strip().lower()
    lid = core.I(row.get("league_id"))
    return lid == 1 or league in {"epl", "premier league", "english premier league"}


def batches(rows, n=500):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]


def main():
    start_year, end_year = parse_args()
    target_years = set(range(start_year, end_year + 1))
    target_seasons = {core.label_from_year(y) for y in target_years}

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
    sb = create_client(url, key)

    # Canonical fixture universe.
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
                season, str(c.get("match_date")), c.get("home_team"), c.get("away_team"),
                core.I(c.get("home_score")), core.I(c.get("away_score")),
            )
            if k in canonical_key:
                raise RuntimeError(f"Duplicate canonical fixture key: {k}")
            canonical_key[k] = c["canonical_match_id"]

    zpath = ensure_zip()
    with zipfile.ZipFile(zpath) as zf:
        games_member = find_member(zf, "general_game_stats")
        lineup_member = find_member(zf, "lineup_stats")
        print(f"Using {games_member}")
        print(f"Using {lineup_member}")

        # Exact source-match mapping. Team IDs are learned only after an exact fixture match.
        source_games = {}
        match_maps = []
        team_maps = {}
        source_counts = defaultdict(int)
        mapped_counts = defaultdict(int)
        unresolved = defaultdict(list)

        for g in iter_member_rows(zf, games_member):
            y = season_year(g.get("season"))
            if y not in target_years or not is_epl_game(g):
                continue
            season = core.label_from_year(y)
            gid = sid(g.get("id") or g.get("match_id"))
            if not gid:
                continue
            home = core.canon_team(g.get("team_h") or g.get("h_team"))
            away = core.canon_team(g.get("team_a") or g.get("a_team"))
            date = str(g.get("date") or "")[:10]
            hs = core.I(g.get("h_goals"))
            aas = core.I(g.get("a_goals"))
            hid = sid(g.get("h_id"))
            aid = sid(g.get("a_id"))
            source_counts[season] += 1
            ck = (season, date, home, away, hs, aas)
            mid = canonical_key.get(ck)
            source_games[gid] = {
                "season": season, "match_id": mid,
                "home_team": home, "away_team": away,
                "home_team_id": hid, "away_team_id": aid,
            }
            if not mid:
                unresolved[season].append(ck)
                continue
            mapped_counts[season] += 1
            match_maps.append({
                "source": SOURCE, "source_match_id": gid, "canonical_match_id": mid,
                "season": season, "mapping_method": "date_teams_score_verified", "verified": True,
            })
            for stid, name in ((hid, home), (aid, away)):
                if not stid or not name:
                    continue
                old = team_maps.get(stid)
                if old and old != name:
                    raise RuntimeError(f"Understat team ID {stid} maps inconsistently: {old} vs {name}")
                team_maps[stid] = name

        # Scan lineups once; retain only requested EPL matches.
        staged = []
        per_game_rows = defaultdict(int)
        players = set()
        duplicate_keys = set()
        seen = set()
        for r in iter_member_rows(zf, lineup_member):
            gid = sid(r.get("match_id") or r.get("id"))
            gm = source_games.get(gid)
            if not gm or not gm.get("match_id"):
                continue
            pid = sid(r.get("player_id"))
            if not pid:
                continue
            key0 = (gid, pid)
            if key0 in seen:
                duplicate_keys.add(key0)
                continue
            seen.add(key0)

            team_id = sid(r.get("team_id"))
            side = str(r.get("h_a") or "").strip().lower()
            team_name = team_maps.get(team_id)
            if not team_name:
                if side == "h":
                    team_name = gm["home_team"]
                elif side == "a":
                    team_name = gm["away_team"]
            pos = str(r.get("position") or "").strip() or None
            mins = core.I(r.get("time"), 0) or 0
            is_start = bool(mins > 0 and str(pos or "").strip().lower() not in {"sub", "substitute", "subs"})
            per_game_rows[gid] += 1
            players.add(pid)
            staged.append({
                "source": SOURCE,
                "source_match_id": gid,
                "source_player_id": pid,
                "season": gm["season"],
                "match_id": gm["match_id"],
                "player_code": None,
                "source_team_id": team_id,
                "team_name": team_name,
                "player_name": core.txt(r.get("player")),
                "birth_date": None,
                "source_position": pos,
                "shirt_number": None,
                "is_starting": is_start,
                "minutes_played": mins,
                "goals": core.I(r.get("goals"), 0) or 0,
                "own_goals": core.I(r.get("own_goals"), 0) or 0,
                "assists": core.I(r.get("assists"), 0) or 0,
                "yellow_cards": core.I(r.get("yellow_card"), 0) or 0,
                "red_cards": core.I(r.get("red_card"), 0) or 0,
                "xg": F(r.get("xG")),
                "xa": F(r.get("xA")),
                "shots": core.I(r.get("shots"), 0) or 0,
                "key_passes": core.I(r.get("key_passes"), 0) or 0,
                "xg_chain": F(r.get("xGChain")),
                "xg_buildup": F(r.get("xGBuildup")),
                "data_quality": "source_reported_mit_dataset",
                "source_url": KAGGLE_PAGE,
            })

        # Completeness gate: no writes unless all requested seasons pass.
        bad = []
        print("\nUnderstat Premier League completeness gate")
        print("Season   expected  source  mapped  games>=20  min rows  player rows  players  status")
        print("-------  --------  ------  ------  ---------  --------  -----------  -------  ------")
        for season in sorted(target_seasons):
            gids = [gid for gid, gm in source_games.items() if gm["season"] == season]
            expected = expected_games.get(season, 0)
            mapped = mapped_counts.get(season, 0)
            counts = [per_game_rows.get(gid, 0) for gid in gids if source_games[gid].get("match_id")]
            ge20 = sum(1 for n in counts if n >= 20)
            min_rows = min(counts) if counts else 0
            season_rows = [r for r in staged if r["season"] == season]
            season_players = len({r["source_player_id"] for r in season_rows})
            ok = expected > 0 and source_counts[season] == expected and mapped == expected and ge20 == expected
            if not ok:
                bad.append(season)
            print(f"{season:<7}  {expected:>8}  {source_counts[season]:>6}  {mapped:>6}  {ge20:>9}  {min_rows:>8}  {len(season_rows):>11}  {season_players:>7}  {'OK' if ok else 'STOP'}")
            if unresolved.get(season):
                print(f"  unresolved fixtures: {unresolved[season][:3]}" + (" ..." if len(unresolved[season]) > 3 else ""))

        if duplicate_keys:
            raise RuntimeError(f"Duplicate Understat player-match keys found: {len(duplicate_keys)}")
        if bad:
            raise SystemExit("Refusing to stage because completeness failed: " + ", ".join(bad))

        # Writes begin only after the complete audit passes.
        for b in batches(list(team_maps.items())):
            rows = [{
                "source": SOURCE, "source_team_id": stid, "team_name": name,
                "mapping_method": "exact_fixture_verified", "verified": True,
                "source_note": "Learned from exact season/date/teams/score Premier League fixture mapping",
            } for stid, name in b]
            sb.table("team_source_ids").upsert(rows, on_conflict="source,source_team_id").execute()
        for b in batches(match_maps):
            sb.table("match_source_ids").upsert(b, on_conflict="source,source_match_id").execute()

        # Preserve any verified player mapping from an earlier run.
        existing = {}
        for r in core.paged(sb, "player_source_ids", "source_player_id,player_code,verified", {"source": SOURCE}):
            if r.get("verified"):
                existing[str(r["source_player_id"])] = str(r["player_code"])
        for r in staged:
            r["player_code"] = existing.get(r["source_player_id"])
        for n, b in enumerate(batches(staged), 1):
            sb.table("source_player_match_stats").upsert(
                b, on_conflict="source,source_match_id,source_player_id"
            ).execute()
            if n % 20 == 0 or n * 500 >= len(staged):
                print(f"  staged {min(n*500, len(staged))}/{len(staged)} player-match rows")

    mapped_players = len({r["source_player_id"] for r in staged if r.get("player_code")})
    print(f"\nStaged {len(staged)} Understat player-match rows across {len(target_seasons)} seasons.")
    print(f"Source players: {len(players)}; already verified to canonical identity: {mapped_players}.")
    print("No live player_match_stats rows were changed. No player name matching was used.")


if __name__ == "__main__":
    main()
