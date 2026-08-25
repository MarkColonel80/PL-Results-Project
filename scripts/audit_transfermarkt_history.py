#!/usr/bin/env python3
"""Audit the CC0 Transfermarkt dataset before importing historical PL player stats.

Downloads only public CC0 prepared files, writes nothing to Supabase, and compares
Premier League game/appearance coverage with our canonical match archive.
"""
import csv
import gzip
import os
import pathlib
import re
import time
import urllib.request
from collections import defaultdict
from supabase import create_client

BASE = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
UA = "PL-Results-Project transfermarkt-coverage-audit/1.2"
CACHE = pathlib.Path(__file__).resolve().parents[1] / ".cache" / "transfermarkt"
CHUNK = 1024 * 1024


def _download_cached(name, retries=8):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.csv.gz"
    part = CACHE / f"{name}.csv.gz.part"
    if path.exists() and path.stat().st_size > 0:
        print(f"Using cached {name}.csv.gz ({path.stat().st_size/1024/1024:.1f} MB)")
        return path

    url = f"{BASE}/{name}.csv.gz"
    for attempt in range(1, retries + 1):
        offset = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": UA}
        if offset:
            headers["Range"] = f"bytes={offset}-"
            print(f"Resuming {name}.csv.gz from {offset/1024/1024:.1f} MB (attempt {attempt}/{retries})...")
        else:
            print(f"Downloading {name}.csv.gz (attempt {attempt}/{retries})...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=180) as resp:
                status = getattr(resp, "status", resp.getcode())
                # If the host ignores Range, restart cleanly rather than append a full file.
                if offset and status != 206:
                    offset = 0
                    if part.exists():
                        part.unlink()
                mode = "ab" if offset else "wb"
                expected_response = int(resp.headers.get("Content-Length") or 0)
                content_range = resp.headers.get("Content-Range") or ""
                total = None
                m = re.search(r"/(\d+)$", content_range)
                if m:
                    total = int(m.group(1))
                written = 0
                with part.open(mode) as out:
                    while True:
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        out.write(chunk)
                        written += len(chunk)
                if expected_response and written != expected_response:
                    raise IOError(f"short response: received {written} of {expected_response} bytes")
                size = part.stat().st_size
                if total is not None and size < total:
                    raise IOError(f"partial download: have {size} of {total} bytes")

            # Verify the gzip stream before promoting the partial file to cache.
            with gzip.open(part, "rb") as check:
                while check.read(CHUNK):
                    pass
            part.replace(path)
            print(f"  downloaded {path.stat().st_size/1024/1024:.1f} MB")
            return path
        except Exception as exc:
            if attempt >= retries:
                raise
            kept = part.stat().st_size / 1024 / 1024 if part.exists() else 0
            print(f"  connection interrupted ({exc}); kept {kept:.1f} MB, retrying...")
            time.sleep(min(2 * attempt, 10))
    raise RuntimeError(f"Could not download {name}.csv.gz")


def fetch_gz_csv(name):
    path = _download_cached(name)
    # Stream the decompressed CSV from disk rather than holding the whole file in RAM.
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as text:
        yield from csv.DictReader(text)


def season_label(v):
    try:
        y = int(float(v))
    except (TypeError, ValueError):
        return None
    return f"{y}/{str(y+1)[-2:]}"


def paged(sb, table, cols, page=1000):
    out = []
    start = 0
    while True:
        rows = sb.table(table).select(cols).range(start, start + page - 1).execute().data or []
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

    # Supabase's default response cap is 1,000 rows; page through the full
    # canonical archive so season counts are not calculated from a partial set.
    expected_rows = paged(sb, "canonical_matches", "canonical_match_id,season")
    expected = defaultdict(int)
    for r in expected_rows:
        expected[r["season"]] += 1

    game_season = {}
    game_counts = defaultdict(int)
    for r in fetch_gz_csv("games"):
        if r.get("competition_id") != "GB1":
            continue
        season = season_label(r.get("season"))
        gid = str(r.get("game_id") or "")
        if not season or not gid:
            continue
        game_season[gid] = season
        game_counts[season] += 1

    appearance_rows = defaultdict(int)
    appearance_games = defaultdict(set)
    appearance_players = defaultdict(set)
    appearances_per_game = defaultdict(int)
    for r in fetch_gz_csv("appearances"):
        if r.get("competition_id") != "GB1":
            continue
        gid = str(r.get("game_id") or "")
        season = game_season.get(gid)
        if not season:
            continue
        appearance_rows[season] += 1
        appearance_games[season].add(gid)
        appearances_per_game[gid] += 1
        if r.get("player_id"):
            appearance_players[season].add(str(r["player_id"]))

    seasons = sorted(game_counts, key=lambda s: int(s[:4]))
    print("\nPremier League Transfermarkt coverage")
    print("Season   DB games  TM games  games w/apps  games>=20  min apps  appearances  players  status")
    print("-------  --------  --------  ------------  ---------  --------  -----------  -------  ------")
    usable = []
    warnings = []
    for season in seasons:
        db = expected.get(season, 0)
        games = game_counts[season]
        with_apps = len(appearance_games[season])
        gids = [gid for gid, s in game_season.items() if s == season]
        with20 = sum(1 for gid in gids if appearances_per_game.get(gid, 0) >= 20)
        min_apps = min((appearances_per_game.get(gid, 0) for gid in gids), default=0)
        apps = appearance_rows[season]
        players = len(appearance_players[season])
        complete_games = db > 0 and games == db
        healthy_apps = with_apps == games and with20 == games
        status = "OK" if complete_games and healthy_apps else "CHECK"
        if status == "OK":
            usable.append(season)
        else:
            warnings.append(season)
        print(f"{season:<7}  {db:>8}  {games:>8}  {with_apps:>12}  {with20:>9}  {min_apps:>8}  {apps:>11}  {players:>7}  {status}")

    if seasons:
        print(f"\nSource game coverage: {seasons[0]} to {seasons[-1]}.")
    print(f"Seasons passing conservative completeness test: {len(usable)}")
    if usable:
        print("  " + ", ".join(usable))
    if warnings:
        print("Seasons requiring investigation before import:")
        print("  " + ", ".join(warnings))
    print(f"\nCached source files: {CACHE}")
    print("Audit only: no database rows were changed.")


if __name__ == "__main__":
    main()
