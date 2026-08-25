#!/usr/bin/env python3
"""Shared safety checks for provider -> canonical player identity.

Provider IDs belong in player_source_ids. They must never become the permanent
canonical players.player_code. Names are display/audit metadata only and are never
valid automated identity evidence.
"""

PROVIDER_PREFIXES = ("tm:%", "understat:%", "fotmob:%", "sofascore:%")


def _count_like(sb, table, column, pattern):
    res = sb.table(table).select(column, count="exact").like(column, pattern).limit(1).execute()
    return int(res.count or 0)


def assert_provider_neutral_canonical_ids(sb):
    """Fail fast if a provider-native ID has leaked into players.player_code."""
    bad = {}
    for pattern in PROVIDER_PREFIXES:
        n = _count_like(sb, "players", "player_code", pattern)
        if n:
            bad[pattern[:-1]] = n
    if bad:
        details = ", ".join(f"{prefix} {count}" for prefix, count in sorted(bad.items()))
        raise RuntimeError(
            "Provider-native canonical player IDs detected: " + details + ". "
            "Canonical player_code must be provider-neutral; keep provider IDs in player_source_ids."
        )


def assert_no_name_mapping_methods(sb):
    """Prevent accidental introduction of automated name-based crosswalk methods."""
    # Manual historical exceptions may explicitly contain 'manual_name_verified'; those are allowed.
    rows = (
        sb.table("player_source_ids")
        .select("source,source_player_id,mapping_method")
        .ilike("mapping_method", "%name%")
        .limit(1000)
        .execute().data
        or []
    )
    bad = [r for r in rows if "manual_name_verified" not in str(r.get("mapping_method") or "").lower()]
    if bad:
        sample = bad[:5]
        raise RuntimeError(f"Unexpected name-based automated player mappings found: {sample}")


def assert_identity_invariants(sb):
    assert_provider_neutral_canonical_ids(sb)
    assert_no_name_mapping_methods(sb)
