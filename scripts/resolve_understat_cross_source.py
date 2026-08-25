#!/usr/bin/env python3
"""Resolve staged Understat player IDs to canonical players without name matching.

This is deliberately separate from stage_understat_history.py. Staging remains a
source-faithful import; this script owns identity decisions.

Evidence rules learned from the Transfermarkt reconciliation:
- canonical match IDs are the identity backbone; never trust historical FPL fixture IDs
- player names are NEVER automated identity evidence
- cards are not hard identity evidence because providers encode them differently
- require high whole-history match overlap plus goals and minute-pattern agreement
- allow small provider minute differences rather than requiring exact equality
- require one-to-one uniqueness; ambiguous candidates remain unresolved
- provider IDs live in player_source_ids, never in players.player_code
- do not invent a new canonical player merely because a provider player is unresolved

The resolver is DRY-RUN by default. Use --apply only after reviewing the staged
Understat completeness report and this resolver's candidate summary.

This script only creates Understat player crosswalks and updates staged rows. It does
NOT promote Understat rows into player_match_stats; enrichment/promotion is a separate
validated step.

Usage:
  python3 scripts/resolve_understat_cross_source.py
  python3 scripts/resolve_understat_cross_source.py --apply

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
"""

import math
import os
import sys
from collections import defaultdict

from supabase import create_client

from identity_invariants import assert_identity_invariants

SOURCE = "understat"
MIN_COMMON = 3
MIN_COVERAGE = 0.95
MIN_WITHIN_2 = 0.97
STRICT_AVG_MIN_DIFF = 1.5
EXACT_SET_AVG_MIN_DIFF = 2.0
UNIQUENESS_MINUTE_GAP = 5.0
PAGE = 1000


def I(v, default=0):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return default


def paged(sb, table, columns, eq=None):
    out = []
    start = 0
    while True:
        q = sb.table(table).select(columns)
        for k, v in (eq or {}).items():
            q = q.eq(k, v)
        rows = q.range(start, start + PAGE - 1).execute().data or []
        out.extend(rows)
        if len(rows) < PAGE:
            return out
        start += PAGE


def season_start(season):
    try:
        return int(str(season)[:4])
    except ValueError:
        return -1


def score_candidate(source_rows, candidate_rows):
    """Return conservative match-history score, or None if evidence fails."""
    src = {r["match_id"]: r for r in source_rows if r.get("match_id")}
    dst = {r["match_id"]: r for r in candidate_rows if r.get("match_id")}
    if not src or not dst:
        return None

    common_ids = set(src) & set(dst)
    common = len(common_ids)
    if common < MIN_COMMON:
        return None

    source_coverage = common / len(src)
    candidate_coverage = common / len(dst)
    if source_coverage < MIN_COVERAGE or candidate_coverage < MIN_COVERAGE:
        return None

    goal_mismatches = sum(I(src[m].get("goals")) != I(dst[m].get("goals")) for m in common_ids)
    goal_tolerance = max(1, math.ceil(common * 0.01))
    if goal_mismatches > goal_tolerance:
        return None

    diffs = [abs(I(src[m].get("minutes_played")) - I(dst[m].get("minutes_played"))) for m in common_ids]
    avg_diff = sum(diffs) / common
    within2 = sum(d <= 2 for d in diffs) / common
    exact_match_sets = set(src) == set(dst)
    minute_ok = (
        (within2 >= MIN_WITHIN_2 and avg_diff <= STRICT_AVG_MIN_DIFF)
        or (exact_match_sets and avg_diff <= EXACT_SET_AVG_MIN_DIFF)
    )
    if not minute_ok:
        return None

    return {
        "common": common,
        "source_coverage": source_coverage,
        "candidate_coverage": candidate_coverage,
        "goal_mismatches": goal_mismatches,
        "avg_min_diff": avg_diff,
        "within2": within2,
        "exact_match_sets": exact_match_sets,
    }


def clearly_unique(top, second):
    if second is None:
        return True
    a, b = top[1], second[1]
    if a["common"] > b["common"]:
        return True
    if a["goal_mismatches"] < b["goal_mismatches"]:
        return True
    if a["avg_min_diff"] <= STRICT_AVG_MIN_DIFF and (b["avg_min_diff"] - a["avg_min_diff"]) >= UNIQUENESS_MINUTE_GAP:
        return True
    return False


def main():
    apply = "--apply" in sys.argv[1:]
    unknown = [a for a in sys.argv[1:] if a != "--apply"]
    if unknown:
        raise SystemExit("Usage: python3 scripts/resolve_understat_cross_source.py [--apply]")

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
    sb = create_client(url, key)
    assert_identity_invariants(sb)

    staged = paged(
        sb, "source_player_match_stats",
        "source,source_match_id,source_player_id,season,match_id,player_code,minutes_played,goals,data_quality",
        {"source": SOURCE},
    )
    staged = [r for r in staged if r.get("source_player_id") and r.get("match_id")]
    if not staged:
        raise SystemExit("No staged Understat player-match rows found. Run stage_understat_history.py first.")

    existing = paged(
        sb, "player_source_ids",
        "source,source_player_id,player_code,mapping_method,verified",
        {"source": SOURCE},
    )
    existing_map = {
        str(r["source_player_id"]): str(r["player_code"])
        for r in existing if r.get("verified") and r.get("source_player_id") and r.get("player_code")
    }
    claimed_targets = {code: pid for pid, code in existing_map.items()}

    by_source = defaultdict(list)
    for r in staged:
        by_source[str(r["source_player_id"])].append(r)

    # Use the established football base as cross-source evidence. 2014/15 currently has
    # no trusted live base, so those rows cannot create an automatic identity by themselves.
    staged_seasons = sorted({r["season"] for r in staged if season_start(r.get("season")) >= 2015})
    base = []
    for season in staged_seasons:
        rows = paged(
            sb, "player_match_stats",
            "season,match_id,player_code,minutes_played,goals,source",
            {"season": season},
        )
        base.extend(r for r in rows if r.get("player_code") and r.get("match_id") and r.get("source") != SOURCE)

    base_by_match = defaultdict(list)
    base_by_player_season = defaultdict(list)
    for r in base:
        code = str(r["player_code"])
        base_by_match[r["match_id"]].append(code)
        base_by_player_season[(code, r["season"])].append(r)

    resolved = {}
    audit = []
    ambiguous = 0
    too_little_overlap = 0

    for pid, all_rows in by_source.items():
        if pid in existing_map:
            continue
        source_rows = [r for r in all_rows if season_start(r.get("season")) >= 2015]
        if len(source_rows) < MIN_COMMON:
            too_little_overlap += 1
            continue

        seasons = {r["season"] for r in source_rows}
        candidate_codes = set()
        for r in source_rows:
            candidate_codes.update(base_by_match.get(r["match_id"], ()))

        ranked = []
        for code in candidate_codes:
            owner = claimed_targets.get(code)
            if owner and owner != pid:
                continue
            candidate_rows = []
            for season in seasons:
                candidate_rows.extend(base_by_player_season.get((code, season), ()))
            score = score_candidate(source_rows, candidate_rows)
            if score:
                ranked.append((code, score))

        ranked.sort(
            key=lambda item: (
                -item[1]["common"],
                item[1]["goal_mismatches"],
                item[1]["avg_min_diff"],
                -min(item[1]["source_coverage"], item[1]["candidate_coverage"]),
            )
        )
        if not ranked:
            continue
        if not clearly_unique(ranked[0], ranked[1] if len(ranked) > 1 else None):
            ambiguous += 1
            continue

        code, score = ranked[0]
        if code in claimed_targets and claimed_targets[code] != pid:
            ambiguous += 1
            continue
        resolved[pid] = code
        claimed_targets[code] = pid
        audit.append((pid, code, score))

    print("Understat cross-source resolver")
    print(f"Staged rows: {len(staged):,}")
    print(f"Staged source players: {len(by_source):,}")
    print(f"Existing verified Understat mappings: {len(existing_map):,}")
    print(f"New high-confidence candidates: {len(resolved):,}")
    print(f"Unresolved with <{MIN_COMMON} overlap appearances: {too_little_overlap:,}")
    print(f"Ambiguous after composite uniqueness: {ambiguous:,}")
    if audit:
        common = [x[2]["common"] for x in audit]
        overlaps = [min(x[2]["source_coverage"], x[2]["candidate_coverage"]) for x in audit]
        avgdiff = [x[2]["avg_min_diff"] for x in audit]
        print(f"Candidate common games: min {min(common)}, median {sorted(common)[len(common)//2]}, max {max(common)}")
        print(f"Minimum two-sided match coverage: {min(overlaps)*100:.1f}%")
        print(f"Worst accepted average minute difference: {max(avgdiff):.2f}")

    if not apply:
        print("DRY RUN ONLY: no player crosswalks or staged rows changed. Review this output, then rerun with --apply.")
        return

    mapping_rows = []
    for pid, code in resolved.items():
        mapping_rows.append({
            "source": SOURCE,
            "source_player_id": pid,
            "player_code": code,
            "mapping_method": "canonical_match_history_goals_minutes_v1",
            "verified": True,
            "source_note": (
                "No player-name matching. >=95% two-sided canonical match-history coverage; "
                "goals near-exact; provider-tolerant minute pattern; cards excluded; one-to-one unique."
            ),
        })
    for i in range(0, len(mapping_rows), 500):
        sb.table("player_source_ids").upsert(
            mapping_rows[i:i+500], on_conflict="source,source_player_id"
        ).execute()

    for pid, code in resolved.items():
        (
            sb.table("source_player_match_stats")
            .update({"player_code": code, "data_quality": "source_reported_verified_cross_source_identity"})
            .eq("source", SOURCE)
            .eq("source_player_id", pid)
            .execute()
        )

    assert_identity_invariants(sb)
    print(f"Applied {len(resolved):,} new Understat player crosswalks.")
    print("No live player_match_stats rows were changed.")
    print("Identity invariants: OK (provider-neutral canonical IDs; no automated name matching)")


if __name__ == "__main__":
    main()
