# Premier League Data Hub V2

Includes season selector, league table, team pages, player pages, player leaders, match details, cross-season FPL history, team head-to-head history and incremental current-season updates.

## Data architecture rule
The production website reads application data from Supabase only. Do not fetch third-party football/FPL datasets directly from browser pages or runtime UI code.

External sources are used only by explicit import/update scripts that copy data into Supabase first. This keeps the site independent of third-party runtime availability and gives us one controlled database layer for joins, identity and historical analysis.

## Run locally
Copy your existing `.env.local` into this folder, then:
```bash
npm install
npm run dev
```

## Data identity
Players are identified permanently by the FPL `code` / `player_code`. The FPL `id` / `player_id` is stored as a season-local ID only. Names are display fields and are not used to join player statistics.

## Historical Premier League results
Historical league results are stored in Supabase in `historical_matches`. The `all_premier_league_results` view merges that archive with live/current rows from `matches`, while `get_premier_league_head_to_head(...)` powers the Head-to-head page without downloading an external results file in the browser.

Import or refresh the historical archive with:
```bash
python3 scripts/import_premier_league_results.py
```

The importer currently reads the cleaned Premier League results source, normalises team names, and upserts the archive into Supabase. It is safe to run again when the source is updated.

## Update rich match data
```bash
export SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="sb_secret_..."
python3 scripts/update_season.py 2026-2027
```
The updater only imports finished Premier League games and can be run repeatedly.

## Historical FPL archive
Fixture-level FPL history is stored from 2016/17 through the most recently archived completed season, including official points, minutes, goals, assists, clean sheets, cards, saves, bonus/BPS and point-component breakdowns.

Use the robust historical importer:
```bash
python3 scripts/import_fpl_history_v2.py 2025-26
```

Or resume/import a range:
```bash
python3 scripts/import_fpl_history_v2.py --from 2024-25
```

## Current-season FPL fixture data
The historical archive can lag during an active season. For the live season use the official FPL API updater, which reads each player's official per-fixture history and writes it to Supabase:
```bash
python3 scripts/update_fpl_current.py 2026-27
```

This keeps official FPL fixture points separate from the richer football match-stat source while linking both by permanent `player_code`.

## Put it online
Use GitHub + Vercel. Add these Vercel environment variables:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`

The Basic Auth variables protect the web app. Keep all secret values in Vercel environment variables and never commit them to GitHub.
Never put the Supabase service-role key in Vercel client variables.
