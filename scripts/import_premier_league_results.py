#!/usr/bin/env python3
import csv
import io
import os
import subprocess
import sys
import urllib.request

try:
    from supabase import create_client
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase"])
    from supabase import create_client

SOURCE = "https://raw.githubusercontent.com/AnishKhetani/premier-league-data/main/data/processed/results.csv"
ALIASES = {
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Man Utd": "Manchester United",
    "Tottenham": "Tottenham Hotspur",
    "Nott'm Forest": "Nottingham Forest",
    "Bournemouth": "AFC Bournemouth",
    "Brighton": "Brighton & Hove Albion",
    "Newcastle": "Newcastle United",
    "Leeds": "Leeds United",
    "Leicester": "Leicester City",
    "Norwich": "Norwich City",
    "West Ham": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
    "West Brom": "West Bromwich Albion",
    "Swansea": "Swansea City",
    "Cardiff": "Cardiff City",
    "Huddersfield": "Huddersfield Town",
    "Hull": "Hull City",
    "Stoke": "Stoke City",
    "Ipswich": "Ipswich Town",
    "Coventry": "Coventry City",
    "Sheffield Weds": "Sheffield Wednesday",
    "QPR": "Queens Park Rangers",
    "Blackburn": "Blackburn Rovers",
    "Bolton": "Bolton Wanderers",
    "Wigan": "Wigan Athletic",
    "Charlton": "Charlton Athletic",
    "Bradford": "Bradford City",
    "Birmingham": "Birmingham City",
    "Derby": "Derby County",
}


def canonical_team(name: str) -> str:
    value = (name or "").strip()
    return ALIASES.get(value, value)


def season_label(value: str) -> str:
    value = (value or "").strip()
    if len(value) == 7 and value[4] == "-":
        return f"{value[:4]}/{value[-2:]}"
    return value


def batches(rows, size=500):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")

    print("Downloading Premier League results archive...")
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "pl-data-results-import/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        text = response.read().decode("utf-8-sig")

    rows = []
    skipped = 0
    for r in csv.DictReader(io.StringIO(text)):
        try:
            home_score = int(r["fthg"])
            away_score = int(r["ftag"])
        except (TypeError, ValueError, KeyError):
            skipped += 1
            continue

        match_id = (r.get("match_id") or "").strip()
        season = season_label(r.get("season") or "")
        match_date = (r.get("date") or "").strip()
        home_team = canonical_team(r.get("home_team") or "")
        away_team = canonical_team(r.get("away_team") or "")
        if not all([match_id, season, match_date, home_team, away_team]):
            skipped += 1
            continue

        rows.append(
            {
                "match_id": match_id,
                "season": season,
                "match_date": match_date,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "result": (r.get("ftr") or "").strip() or None,
                "source": "AnishKhetani/premier-league-data",
            }
        )

    if not rows:
        raise SystemExit("No valid historical result rows were found; refusing to continue.")

    sb = create_client(url, key)
    print(f"Prepared {len(rows)} matches; skipped {skipped} invalid rows.")
    for i, batch in enumerate(batches(rows), start=1):
        sb.table("historical_matches").upsert(batch, on_conflict="match_id").execute()
        done = min(i * 500, len(rows))
        if done % 5000 == 0 or done == len(rows):
            print(f"  uploaded {done}/{len(rows)} matches")

    seasons = sorted({r["season"] for r in rows})
    teams = sorted({r["home_team"] for r in rows} | {r["away_team"] for r in rows})
    print(
        f"Premier League results import complete: {len(rows)} matches, "
        f"{len(seasons)} seasons ({seasons[0]} to {seasons[-1]}), {len(teams)} clubs."
    )


if __name__ == "__main__":
    main()
