# Premier League Data Hub V2

Includes season selector, league table, team pages, player pages, player leaders, match details and an incremental updater for 2026/27.

## Run locally
Copy your existing `.env.local` into this folder, then:
```bash
npm install
npm run dev
```

## Update the current season
```bash
export SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="sb_secret_..."
python3 scripts/update_season.py 2026-2027
```
The updater only imports finished games and can be run repeatedly.

## Put it online
Use GitHub + Vercel. Add only these two Vercel environment variables:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
Never put the service-role key in Vercel client variables.
