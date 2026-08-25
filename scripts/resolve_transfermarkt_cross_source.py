#!/usr/bin/env python3
"""Run the permanent Transfermarkt -> canonical player resolver in Supabase.

The database function reconstructs canonical FPL fixture identity from season/date/
team/opponent/home-away evidence rather than trusting historical FPL fixture IDs.
It never uses player names for identity. Cards are not hard-matched because providers
encode second-yellow dismissals differently; identity is based on high match-history
coverage, goals, minute-pattern fit, one-to-one uniqueness, and DOB where available.

Provider IDs are never allowed to become canonical player_code values. Historical
manual name-verified exceptions are permitted only when explicitly labelled as such;
automated name-based mapping methods are rejected by the shared invariant checks.

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""
import os
from supabase import create_client

from identity_invariants import assert_identity_invariants

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if not url or not key:
    raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")

sb = create_client(url, key)
assert_identity_invariants(sb)

rows = sb.rpc("resolve_transfermarkt_cross_source").execute().data or []
if not rows:
    raise SystemExit("Resolver returned no summary row.")
r = rows[0]

# Catch any future regression immediately after resolver execution as well.
assert_identity_invariants(sb)

print(f"Newly resolved: {r.get('newly_resolved', 0)}")
print(f"Remaining FPL-era unresolved: {r.get('remaining_fpl_era', 0)}")
print(f"Remaining pre-FPL source-native: {r.get('remaining_pre_fpl', 0)}")
print(f"Transfermarkt rows linked to canonical players: {r.get('linked_row_pct', 0)}%")
print("Identity invariants: OK (no provider-native canonical IDs; no automated name matching)")
