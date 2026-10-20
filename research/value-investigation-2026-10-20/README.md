# Reproduce the 20 October value investigation

The protocol, amended timing audit, numerical results, exact replay script, regression query and SHA-256 input manifest are versioned here. The full input/output bundle is saved on the project Mac:

`/Users/mark2/Documents/Codex/2026-09-10/i-a/outputs/PL-Data-Hub-value-investigation-2026-10-20.zip`

Extract it, then run `python3 -m pip install numpy==2.3.5` in a suitable research environment and `python3 analyse.py` from the extracted directory. The Mac's bundled Python runtime already has the required NumPy version. The script reads frozen JSON and CSV files only and writes `results.json`, `matched-historical-replays.json` and its printed summary. It does not connect to or change Supabase. Compare input hashes with `manifest.json` before replaying. Global output aggregates use deterministic bootstrap seed 20261020.

Run `python3 scripts/test_research_league_prior.py` from the repository to emit the synthetic read-only PostgreSQL regression query for the actual league-prior CTE. Execute only the emitted SELECT. All four checks should be true. Do not run the source CREATE MATERIALIZED VIEW file against the existing relation; rebuilding the research dependency chain is separate work.

The versioned report explains the distinction between archived cached scores, strict replay, previously inspected stress data, mechanical retrospective selections, actual watchlist records and prospective paper selections. No new model has been promoted.
