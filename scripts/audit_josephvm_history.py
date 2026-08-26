#!/usr/bin/env python3
"""Read-only audit of Joseph Mohr's CC0 Premier League match/event dataset.

Dataset:
  https://www.kaggle.com/datasets/josephvm/english-premier-league-game-events-and-results

Purpose:
- inspect the real CSV schemas before we design an importer
- audit 2001/02 through 2011/12 fixture coverage against canonical_matches
- report event/commentary coverage
- identify whether stable player IDs are actually present

This script DOES NOT write to Supabase and DOES NOT match players by name.

Usage:
  python3 scripts/audit_josephvm_history.py

Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY only for reading the
canonical fixture universe.
"""

import csv
import io
import os
import pathlib
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime

from supabase import create_client

import import_transfermarkt_history as core

KAGGLE_PAGE = "https://www.kaggle.com/datasets/josephvm/english-premier-league-game-events-and-results"
KAGGLE_DOWNLOAD = "https://www.kaggle.com/api/v1/datasets/download/josephvm/english-premier-league-game-events-and-results"
CACHE = pathlib.Path(__file__).resolve().parents[1] / ".cache" / "josephvm_epl"
ZIP_PATH = CACHE / "english-premier-league-game-events-and-results.zip"
PART_PATH = CACHE / "english-premier-league-game-events-and-results.zip.part"
UA = "PL-Results-Project josephvm-history-audit/1.0"
CHUNK = 1024 * 1024
RETRIES = 8
TARGET_YEARS = set(range(2001, 2012))

# Harmless team-name aliases are allowed for fixture identity. Player names are
# never used for identity.
core.TEAM_ALIASES.update({
    "Bolton": "Bolton Wanderers",
    "Blackburn": "Blackburn Rovers",
    "Birmingham": "Birmingham City",
    "Cardiff": "Cardiff City",
    "Charlton": "Charlton Athletic",
    "Derby": "Derby County",
    "Hull": "Hull City",
    "Leicester": "Leicester City",
    "Man City": "Manchester City",
    "Man United": "Manchester United",
    "Middlesbrough": "Middlesbrough",
    "Newcastle": "Newcastle United",
    "Norwich": "Norwich City",
    "Portsmouth": "Portsmouth",
    "QPR": "Queens Park Rangers",
    "Reading": "Reading",
    "Stoke": "Stoke City",
    "Sunderland": "Sunderland",
    "Tottenham": "Tottenham Hotspur",
    "West Brom": "West Bromwich Albion",
    "West Ham": "West Ham United",
    "Wigan": "Wigan Athletic",
    "Wolves": "Wolverhampton Wanderers",
})


def ensure_zip():
    CACHE.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists() and ZIP_PATH.stat().st_size > 0:
        try:
            with zipfile.ZipFile(ZIP_PATH) as zf:
                if zf.testzip() is None:
                    print(f"Using cached Joseph dataset ZIP ({ZIP_PATH.stat().st_size/1024/1024:.1f} MB)")
                    return ZIP_PATH
        except Exception:
            pass
        ZIP_PATH.unlink(missing_ok=True)

    for attempt in range(1, RETRIES + 1):
        existing = PART_PATH.stat().st_size if PART_PATH.exists() else 0
        headers = {"User-Agent": UA, "Accept": "application/zip,application/octet-stream,*/*"}
        if existing:
            headers["Range"] = f"bytes={existing}-"
        try:
            print(f"Downloading Joseph CC0 dataset (attempt {attempt}/{RETRIES})..." +
                  (f" resuming at {existing/1024/1024:.1f} MB" if existing else ""))
            req = urllib.request.Request(KAGGLE_DOWNLOAD, headers=headers)
            with urllib.request.urlopen(req, timeout=180) as resp:
                status = getattr(resp, "status", None)
                mode = "ab" if existing and status == 206 else "wb"
                with open(PART_PATH, mode) as out:
                    while True:
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        out.write(chunk)
            with zipfile.ZipFile(PART_PATH) as zf:
                bad = zf.testzip()
                if bad is not None:
                    raise RuntimeError(f"Corrupt ZIP member: {bad}")
            PART_PATH.replace(ZIP_PATH)
            print(f"  downloaded {ZIP_PATH.stat().st_size/1024/1024:.1f} MB")
            return ZIP_PATH
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise SystemExit(
                    "Kaggle blocked the unauthenticated download. Download the public dataset ZIP from\n"
                    f"  {KAGGLE_PAGE}\n"
                    f"and save it as\n  {ZIP_PATH}\nthen run again."
                )
            err = exc
        except Exception as exc:
            err = exc
        if attempt == RETRIES:
            raise RuntimeError(f"Could not download Joseph dataset: {err}")
        print(f"  download/read failed: {err}; retrying...")
        time.sleep(min(2 * attempt, 10))
    raise RuntimeError("Could not download Joseph dataset")


def csv_members(zf):
    return [n for n in zf.namelist() if n.lower().endswith(".csv")]


def find_member(zf, basename):
    exact = [n for n in csv_members(zf) if pathlib.PurePosixPath(n).name.lower() == basename.lower()]
    if len(exact) == 1:
        return exact[0]
    return None


def read_rows(zf, member):
    with zf.open(member) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.DictReader(text)
        fields = reader.fieldnames or []
        rows = [{str(k).strip(): v for k, v in row.items() if k is not None} for row in reader]
    return fields, rows


def pick(fields, *candidates):
    low = {str(f).strip().lower(): f for f in fields}
    for c in candidates:
        if c.lower() in low:
            return low[c.lower()]
    return None


def sample_value(row, field):
    if not field:
        return None
    s = str(row.get(field) or "").replace("\n", " ").strip()
    return s[:160] + ("..." if len(s) > 160 else "")


def parse_year(v):
    try:
        return int(float(str(v).strip()))
    except Exception:
        s = str(v or "")
        for y in range(2001, 2022):
            if str(y) in s:
                return y
        return None


def parse_date(v):
    s = str(v or "").strip()
    if not s:
        return None
    # Try ISO first, then common US/UK formats. We do not use fuzzy dates.
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(s[:19] if "%H" in fmt else s, fmt).date().isoformat()
        except Exception:
            pass
    # Common timestamp where date is the first 10 chars.
    if len(s) >= 10 and s[4:5] == "-" and s[7:8] == "-":
        return s[:10]
    return None


def score_int(v):
    return core.I(v)


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY first.")
    sb = create_client(url, key)

    zpath = ensure_zip()
    with zipfile.ZipFile(zpath) as zf:
        members = csv_members(zf)
        print("\nCSV members")
        for n in members:
            info = zf.getinfo(n)
            print(f"  {n} ({info.file_size/1024/1024:.2f} MB)")

        matches_member = find_member(zf, "matches.csv")
        events_member = find_member(zf, "events.csv")
        if not matches_member or not events_member:
            raise SystemExit(f"Could not find matches.csv/events.csv. CSV members: {members}")

        match_fields, matches = read_rows(zf, matches_member)
        event_fields, events = read_rows(zf, events_member)

    print("\nmatches.csv columns")
    print(match_fields)
    print("\nevents.csv columns")
    print(event_fields)

    if matches:
        print("\nFirst matches.csv row (truncated values)")
        for f in match_fields:
            print(f"  {f}: {sample_value(matches[0], f)}")
    if events:
        print("\nFirst events.csv row (truncated values)")
        for f in event_fields:
            print(f"  {f}: {sample_value(events[0], f)}")

    year_col = pick(match_fields, "Year", "year", "Season", "season")
    id_col = pick(match_fields, "game_id", "match_id", "id", "GameID", "MatchID")
    date_col = pick(match_fields, "date", "Date", "match_date", "MatchDate")
    home_col = pick(match_fields, "home_team", "HomeTeam", "home", "Home", "team_h", "h_team")
    away_col = pick(match_fields, "away_team", "AwayTeam", "away", "Away", "team_a", "a_team")
    hg_col = pick(match_fields, "home_score", "HomeScore", "home_goals", "FTHG", "h_goals")
    ag_col = pick(match_fields, "away_score", "AwayScore", "away_goals", "FTAG", "a_goals")

    print("\nDetected match columns")
    print({"year":year_col,"id":id_col,"date":date_col,"home":home_col,"away":away_col,"home_score":hg_col,"away_score":ag_col})

    # Report identity-looking columns without assuming they are valid player IDs.
    identity_like_matches = [f for f in match_fields if any(x in f.lower() for x in ("player", "lineup", "squad", "starter", "sub"))]
    identity_like_events = [f for f in event_fields if any(x in f.lower() for x in ("player", "athlete", "competitor", "id", "scorer", "assist"))]
    print("\nPlayer/lineup-looking match columns")
    print(identity_like_matches)
    print("\nPlayer/ID-looking event columns")
    print(identity_like_events)

    if not all((year_col,id_col,date_col,home_col,away_col,hg_col,ag_col)):
        print("\nSTOP: fixture columns could not all be detected safely. No Supabase writes were made.")
        return

    # Canonical fixture universe 2001/02-2011/12.
    canonical_exact = {}
    expected = {}
    for y in sorted(TARGET_YEARS):
        season = core.label_from_year(y)
        rows = core.paged(sb,"canonical_matches","canonical_match_id,season,match_date,home_team,away_team,home_score,away_score",{"season":season})
        expected[season] = len(rows)
        for c in rows:
            k=(season,str(c.get("match_date")),c.get("home_team"),c.get("away_team"),score_int(c.get("home_score")),score_int(c.get("away_score")))
            canonical_exact[k]=c["canonical_match_id"]

    source_counts=Counter(); mapped_counts=Counter(); unresolved=defaultdict(list); source_ids_by_season=defaultdict(set)
    source_match_to_season={}
    for r in matches:
        y=parse_year(r.get(year_col))
        if y not in TARGET_YEARS:
            continue
        season=core.label_from_year(y)
        mid=str(r.get(id_col) or "").strip()
        d=parse_date(r.get(date_col))
        home=core.canon_team(r.get(home_col)); away=core.canon_team(r.get(away_col))
        hs=score_int(r.get(hg_col)); aas=score_int(r.get(ag_col))
        source_counts[season]+=1
        if mid:
            source_ids_by_season[season].add(mid)
            source_match_to_season[mid]=season
        ck=(season,d,home,away,hs,aas)
        if canonical_exact.get(ck):
            mapped_counts[season]+=1
        else:
            unresolved[season].append(ck)

    event_match_col = pick(event_fields,"game_id","match_id","id","GameID","MatchID")
    events_per_match=Counter()
    if event_match_col:
        for e in events:
            mid=str(e.get(event_match_col) or "").strip()
            if mid in source_match_to_season:
                events_per_match[mid]+=1

    print("\nJoseph source fixture/event audit")
    print("Season   expected  source  exact-mapped  matches>1 event  zero/one event  status")
    print("-------  --------  ------  ------------  ---------------  --------------  ------")
    for y in sorted(TARGET_YEARS):
        season=core.label_from_year(y)
        ids=source_ids_by_season[season]
        gt1=sum(1 for mid in ids if events_per_match[mid]>1) if event_match_col else 0
        low=sum(1 for mid in ids if events_per_match[mid]<=1) if event_match_col else 0
        ok=expected.get(season)==380 and source_counts[season]==380 and mapped_counts[season]==380
        print(f"{season:<7}  {expected.get(season,0):>8}  {source_counts[season]:>6}  {mapped_counts[season]:>12}  {gt1:>15}  {low:>14}  {'FIXTURES OK' if ok else 'CHECK'}")
        if unresolved.get(season):
            print("  unresolved:",unresolved[season][:3],"..." if len(unresolved[season])>3 else "")

    print("\nNo Supabase writes were made. No player-name matching was used.")
    if event_match_col:
        print(f"Event match-ID column detected: {event_match_col}")
    else:
        print("No event match-ID column was detected safely.")
    print("The column lists above are the key output for deciding whether stable player IDs exist.")


if __name__ == "__main__":
    main()
