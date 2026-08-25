#!/usr/bin/env python3
"""Reconcile rich match score rows with detailed goal events and canonical match IDs.

This is deliberately conservative: a score is changed only when the goal-event feed
contains cumulative home/away scores and its final event is internally consistent.
"""
import os
from collections import defaultdict
from supabase import create_client


def _n(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def reconcile_match_scores(season: str):
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
    sb = create_client(url, key)

    matches = sb.table("matches").select(
        "match_id,season,kickoff_time,home_team,away_team,home_score,away_score"
    ).eq("season", season).execute().data or []
    goals = sb.table("goals").select(
        "match_id,minute,added_time,incident_index,home_score,away_score"
    ).eq("season", season).execute().data or []

    by_match = defaultdict(list)
    for g in goals:
        if g.get("match_id"):
            by_match[g["match_id"]].append(g)

    corrected = 0
    skipped_inconsistent = 0
    for m in matches:
        events = by_match.get(m["match_id"], [])
        valid = [g for g in events if _n(g.get("home_score")) is not None and _n(g.get("away_score")) is not None]
        if not valid:
            continue
        valid.sort(key=lambda g: (
            _n(g.get("minute")) or 0,
            _n(g.get("added_time")) or 0,
            _n(g.get("incident_index")) or 0,
        ))
        last = valid[-1]
        hs, aws = _n(last.get("home_score")), _n(last.get("away_score"))
        # A normal goal-event feed increments the cumulative score exactly once per row.
        # Refuse to self-heal if that invariant does not hold.
        if hs is None or aws is None or hs + aws != len(events):
            skipped_inconsistent += 1
            continue
        if _n(m.get("home_score")) != hs or _n(m.get("away_score")) != aws:
            sb.table("matches").update({"home_score": hs, "away_score": aws}).eq(
                "match_id", m["match_id"]
            ).execute()
            m["home_score"], m["away_score"] = hs, aws
            corrected += 1

    # Keep every rich match represented by one canonical fixture identity.
    canonical = []
    rich_ids = []
    for m in matches:
        canonical.append({
            "canonical_match_id": m["match_id"],
            "season": season,
            "match_date": (m.get("kickoff_time") or "")[:10] or None,
            "home_team": m.get("home_team"),
            "away_team": m.get("away_team"),
            "home_score": _n(m.get("home_score")),
            "away_score": _n(m.get("away_score")),
        })
        rich_ids.append({
            "source": "rich_core",
            "source_match_id": m["match_id"],
            "canonical_match_id": m["match_id"],
            "season": season,
            "mapping_method": "source_primary",
            "verified": True,
        })
    if canonical:
        sb.table("canonical_matches").upsert(canonical, on_conflict="canonical_match_id").execute()
        sb.table("match_source_ids").upsert(rich_ids, on_conflict="source,source_match_id").execute()

    # For archived seasons, remap the archive ID to the rich canonical ID only on an
    # exact season/date/teams/final-score match. No fuzzy team or score matching.
    archive = sb.table("historical_matches").select(
        "match_id,season,match_date,home_team,away_team,home_score,away_score"
    ).eq("season", season).execute().data or []
    exact = {}
    for m in matches:
        k = (
            (m.get("kickoff_time") or "")[:10], m.get("home_team"), m.get("away_team"),
            _n(m.get("home_score")), _n(m.get("away_score")),
        )
        exact[k] = m["match_id"]
    remapped = 0
    for h in archive:
        k = (
            h.get("match_date"), h.get("home_team"), h.get("away_team"),
            _n(h.get("home_score")), _n(h.get("away_score")),
        )
        mid = exact.get(k)
        if not mid:
            continue
        sb.table("match_source_ids").upsert({
            "source": "results_archive",
            "source_match_id": h["match_id"],
            "canonical_match_id": mid,
            "season": season,
            "mapping_method": "date_teams_score_verified",
            "verified": True,
        }, on_conflict="source,source_match_id").execute()
        remapped += 1

    print(
        f"Match scores checked for {season}: {corrected} corrected; "
        f"{skipped_inconsistent} inconsistent goal feeds left untouched; "
        f"{len(canonical)} canonical rich matches synced; {remapped} archive mappings verified."
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 scripts/reconcile_match_scores.py 2025/26")
    reconcile_match_scores(sys.argv[1])
