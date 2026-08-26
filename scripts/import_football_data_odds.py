#!/usr/bin/env python3
"""Import Premier League historical market odds from Football-Data.co.uk.

Default behaviour is DRY RUN. Use --apply to upsert rows into
public.historical_market_odds.

The source publishes free EPL CSV files for quantitative betting-system testing.
This importer keeps the raw source row, normalises TEAM names only, and maps a
source fixture to our canonical match_id by season + home/away teams + exact
match date, with a unique +/-1-day fallback for source date drift.

Usage:
  python3 scripts/import_football_data_odds.py
  python3 scripts/import_football_data_odds.py --from 2016-17 --to 2026-27
  python3 scripts/import_football_data_odds.py --from 2019-20 --to 2025-26 --apply

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY only when --apply is used.
"""

import csv
import io
import json
import os
import pathlib
import sys
import urllib.request
from datetime import datetime, timedelta

from supabase import create_client
import import_transfermarkt_history as core

SOURCE = "football-data.co.uk"
UA = "PL-Results-Project football-data-odds/1.0"
CACHE = pathlib.Path(__file__).resolve().parents[1] / ".cache" / "football_data_odds"

core.TEAM_ALIASES.update({
    "Bournemouth": "AFC Bournemouth",
    "Brighton": "Brighton & Hove Albion",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Tottenham": "Tottenham Hotspur",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
})


def F(v):
    try:
        if v is None or str(v).strip() == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def first(row, *keys):
    for key in keys:
        if key in row:
            value = F(row.get(key))
            if value is not None:
                return value
    return None


def source_url(year):
    folder = f"{year % 100:02d}{(year + 1) % 100:02d}"
    return f"https://www.football-data.co.uk/mmz4281/{folder}/E0.csv"


def parse_date(value):
    s = str(value or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognised Football-Data date: {s!r}")


def parse_time(value):
    s = str(value or "").strip()
    if not s:
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).time().isoformat()
        except ValueError:
            pass
    return None


def download_csv(year):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"E0_{year}_{year+1}.csv"
    if path.exists() and path.stat().st_size > 100:
        return path
    url = source_url(year)
    print(f"Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/csv,*/*"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    path.write_bytes(data)
    return path


def load_rows(year):
    path = download_csv(year)
    data = path.read_bytes()
    text = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            pass
    if text is None:
        raise RuntimeError(f"Could not decode {path}")
    return list(csv.DictReader(io.StringIO(text)))


def paged(sb, table, cols, eq=None, page=1000):
    out, start = [], 0
    while True:
        q = sb.table(table).select(cols)
        for k, v in (eq or {}).items():
            q = q.eq(k, v)
        rows = q.range(start, start + page - 1).execute().data or []
        out.extend(rows)
        if len(rows) < page:
            return out
        start += page


def batches(rows, n=400):
    for i in range(0, len(rows), n):
        yield rows[i:i+n]


def canonical_match_index(matches):
    index = {}
    for m in matches:
        if not m.get("kickoff_time"):
            continue
        d = datetime.fromisoformat(str(m["kickoff_time"]).replace("Z", "+00:00")).date()
        key = (m["season"], d, m["home_team"], m["away_team"])
        index[key] = m["match_id"]
    return index


def resolve_match(index, season, d, home, away):
    exact = index.get((season, d, home, away))
    if exact:
        return exact, "exact_date"
    hits = []
    for delta in (-1, 1):
        mid = index.get((season, d + timedelta(days=delta), home, away))
        if mid:
            hits.append(mid)
    if len(set(hits)) == 1:
        return hits[0], "unique_date_plus_minus_one"
    return None, None


def convert_row(row, season, year, match_index):
    d = parse_date(row.get("Date"))
    home_source = str(row.get("HomeTeam") or "").strip()
    away_source = str(row.get("AwayTeam") or "").strip()
    home = core.canon_team(home_source)
    away = core.canon_team(away_source)
    match_id, _ = resolve_match(match_index, season, d, home, away)
    return {
        "season": season,
        "competition": "Premier League",
        "source": SOURCE,
        "source_match_date": d.isoformat(),
        "source_kickoff_time": parse_time(row.get("Time")),
        "source_home_team": home_source,
        "source_away_team": away_source,
        "match_id": match_id,
        "open_home_avg": first(row, "AvgH", "BbAvH"),
        "open_draw_avg": first(row, "AvgD", "BbAvD"),
        "open_away_avg": first(row, "AvgA", "BbAvA"),
        "open_home_max": first(row, "MaxH", "BbMxH"),
        "open_draw_max": first(row, "MaxD", "BbMxD"),
        "open_away_max": first(row, "MaxA", "BbMxA"),
        "close_home_avg": first(row, "AvgCH"),
        "close_draw_avg": first(row, "AvgCD"),
        "close_away_avg": first(row, "AvgCA"),
        "close_home_max": first(row, "MaxCH"),
        "close_draw_max": first(row, "MaxCD"),
        "close_away_max": first(row, "MaxCA"),
        "open_over25_avg": first(row, "Avg>2.5", "BbAv>2.5"),
        "open_under25_avg": first(row, "Avg<2.5", "BbAv<2.5"),
        "close_over25_avg": first(row, "AvgC>2.5"),
        "close_under25_avg": first(row, "AvgC<2.5"),
        "raw_row": row,
        "source_url": source_url(year),
    }


def parse_args():
    start, end, apply = 2016, 2026, False
    args, i = sys.argv[1:], 0
    while i < len(args):
        if args[i] == "--from" and i + 1 < len(args):
            start = core.parse_cli_season(args[i+1]); i += 2
        elif args[i] == "--to" and i + 1 < len(args):
            end = core.parse_cli_season(args[i+1]); i += 2
        elif args[i] == "--apply":
            apply = True; i += 1
        else:
            raise SystemExit("Usage: import_football_data_odds.py [--from 2016-17] [--to 2026-27] [--apply]")
    if end < start:
        raise SystemExit("--to must not be before --from")
    return start, end, apply


def main():
    start, end, apply = parse_args()
    sb = None
    matches = []
    if apply:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise SystemExit("--apply requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        sb = create_client(url, key)
        matches = paged(sb, "matches", "match_id,season,kickoff_time,home_team,away_team")
    else:
        # Dry-run fixture mapping is available when credentials happen to be set,
        # but the source file can still be audited without database access.
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if url and key:
            sb = create_client(url, key)
            matches = paged(sb, "matches", "match_id,season,kickoff_time,home_team,away_team")
    match_index = canonical_match_index(matches)

    all_rows = []
    for year in range(start, end + 1):
        season = core.label_from_year(year)
        source_rows = load_rows(year)
        converted = [convert_row(r, season, year, match_index) for r in source_rows if r.get("Date") and r.get("HomeTeam") and r.get("AwayTeam")]
        mapped = sum(1 for r in converted if r["match_id"])
        with_open = sum(1 for r in converted if r["open_home_avg"] and r["open_draw_avg"] and r["open_away_avg"])
        with_close = sum(1 for r in converted if r["close_home_avg"] and r["close_draw_avg"] and r["close_away_avg"])
        print(f"{season}: rows={len(converted)} mapped={mapped} opening_1x2={with_open} closing_1x2={with_close}")
        all_rows.extend(converted)

    print(f"Total rows: {len(all_rows)}; mapped to canonical fixtures: {sum(1 for r in all_rows if r['match_id'])}")
    if not apply:
        print("DRY RUN ONLY: no historical_market_odds rows changed. Rerun with --apply after reviewing counts.")
        return

    assert sb is not None
    for batch in batches(all_rows):
        sb.table("historical_market_odds").upsert(
            batch,
            on_conflict="season,source,source_match_date,source_home_team,source_away_team",
        ).execute()
    print(f"Applied {len(all_rows)} historical odds rows.")


if __name__ == "__main__":
    main()
