# Premier League Data Hub V2

Includes season selector, league table, team pages, player pages, player leaders, match details, cross-season FPL history and incremental current-season updates.

## Run locally
Copy your existing `.env.local` into this folder, then:
```bash
npm install
npm run dev
```

## Data identity
Players are identified permanently by the FPL `code` / `player_code`. The FPL `id` / `player_id` is stored as a season-local ID only. Names are display fields and are not used to join player statistics.

## Update rich match data
```bash
export SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="sb_secret_..."
python3 scripts/update_season.py 2026-2027
```
The updater only imports finished Premier League games and can be run repeatedly.

## Import historical FPL data
Fixture-level FPL history is available from 2016/17 onward, including official points, minutes, goals, assists, clean sheets, cards, saves, bonus/BPS and point-component breakdowns.

Import one season:
```bash
python3 scripts/import_fpl_history.py 2025-26
```

Import every available season from 2016/17 onward:
```bash
python3 scripts/import_fpl_history.py --all
```

## Put it online
Use GitHub + Vercel. Add these Vercel environment variables:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`

The Basic Auth variables protect the web app. Keep all secret values in Vercel environment variables and never commit them to GitHub.
Never put the Supabase service-role key in Vercel client variables.
