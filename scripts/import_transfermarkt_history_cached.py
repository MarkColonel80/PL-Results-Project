#!/usr/bin/env python3
"""Run the Transfermarkt historical importer using resilient local caching.

This wrapper reuses .cache/transfermarkt files created by the coverage audit and
adds resumable/retrying downloads for any additional Transfermarkt source files.
All identity/import rules remain in import_transfermarkt_history.py.
"""
import csv
import gzip
import io
import pathlib
import time
import urllib.request

import import_transfermarkt_history as core

CACHE = pathlib.Path(__file__).resolve().parents[1] / ".cache" / "transfermarkt"
CHUNK = 1024 * 1024
RETRIES = 8


def ensure_cached(name):
    CACHE.mkdir(parents=True, exist_ok=True)
    final = CACHE / f"{name}.csv.gz"
    part = CACHE / f"{name}.csv.gz.part"

    # Accept an existing cache only if it is a valid gzip file.
    if final.exists() and final.stat().st_size > 0:
        try:
            with gzip.open(final, "rb") as fh:
                fh.read(1)
            print(f"Using cached {name}.csv.gz ({final.stat().st_size/1024/1024:.1f} MB)")
            return final
        except Exception:
            final.unlink(missing_ok=True)

    url = f"{core.BASE}/{name}.csv.gz"
    for attempt in range(1, RETRIES + 1):
        existing = part.stat().st_size if part.exists() else 0
        headers = {"User-Agent": core.UA, "Accept": "text/csv,*/*"}
        if existing:
            headers["Range"] = f"bytes={existing}-"
        try:
            print(f"Downloading {name}.csv.gz (attempt {attempt}/{RETRIES})..." + (f" resuming at {existing/1024/1024:.1f} MB" if existing else ""))
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=180) as resp:
                status = getattr(resp, "status", None)
                # If Range was ignored, restart rather than append a duplicate file.
                mode = "ab" if existing and status == 206 else "wb"
                if mode == "wb":
                    existing = 0
                with open(part, mode) as out:
                    while True:
                        chunk = resp.read(CHUNK)
                        if not chunk:
                            break
                        out.write(chunk)
            with gzip.open(part, "rb") as fh:
                while fh.read(CHUNK):
                    pass
            part.replace(final)
            print(f"  downloaded {final.stat().st_size/1024/1024:.1f} MB")
            return final
        except Exception as exc:
            kept = part.stat().st_size if part.exists() else 0
            if attempt == RETRIES:
                raise
            print(f"  connection/read failed: {exc}; kept {kept/1024/1024:.1f} MB, retrying...")
            time.sleep(min(2 * attempt, 10))
    raise RuntimeError(f"Could not download {name}")


def cached_iter_gz_csv(name):
    path = ensure_cached(name)
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as fh:
        yield from csv.DictReader(fh)


if __name__ == "__main__":
    core.iter_gz_csv = cached_iter_gz_csv
    core.main()
