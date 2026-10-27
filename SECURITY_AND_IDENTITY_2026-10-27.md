# Dependency and Understat follow-up — 27 October 2026

The authorized follow-up closes the dependency audit and adds 121 verified Understat crosswalks. All work ran through connected GitHub, Supabase, Vercel cloud execution and public provider sources. Model formulas, weights, history gates, betting rules, paper decisions and frozen forecasts were not changed. The existing Tuesday automation was not edited or duplicated.

## Dependency outcome

Next.js is pinned to 15.5.28. Next-scoped overrides select PostCSS 8.5.32 and Sharp 0.35.5; the generated lockfile also selects source-map-js 1.2.2. This stays on Next 15. A clean `npm ci --ignore-scripts` reproduced the lockfile and `npm audit` reported **zero vulnerabilities**, down from one critical and three high affected packages.

The Next patch alone leaves older declared PostCSS/Sharp ranges, so the scoped overrides are necessary. Native Sharp PNG generation and the full production build passed. See [dependency evidence](data/dependency-remediation-2026-10-27.json) for complete before/after audit responses and advisory links.

## Identity and data outcome

| Measure | Before | After |
|---|---:|---:|
| Verified Understat mappings | 1,816 | 1,937 |
| Unmapped 2026/27 appearances | 1,135 | 374 |
| Unmapped 2026/27 player IDs | 224 | 103 |
| Unmapped GW8 appearances | 145 | 48 |
| 2026/27 core appearances enriched from Understat | 1,312 | 2,073 |
| Existing mapped source rows without core appearance | 14 | 14 |

The 121 new mappings enrich **769 existing appearances: 761 current-season and eight historical**. No core appearances or canonical players were inserted. All old verified mappings are byte-for-byte unchanged.

For 118 mappings, the established match-history/goals/minutes resolver passed unchanged thresholds, with exact team and goal agreement added. Positive-minute appearances are compared: the core feed also contains unused substitutes, whereas these Understat source rows do not. Every accepted match has complete two-sided appearance coverage, at least three appearances and a unique canonical target. Names were QA labels only.

Three shared-history ambiguities required independent evidence: Carl Rushworth (Understat 12760 → canonical 472739), António Silva (14859 → 483067), and Adrien Truffert (8640 → 494521). Existing verified FPL Opta-to-Fotmob links identify the native player IDs; eight native match lineups per player distinguish goalkeeper, central defender and left-back. Native player profiles independently confirm the latter two positions. The audit retains candidate alternatives, native URLs, source hashes and ID bridges.

All 761 current-season additions also have matching official FPL appearance rows and goal totals. Provider minute conventions differ in some rows; all original core/FPL minutes and goals are retained. Only advanced metrics and their Understat provenance were enriched. There are zero source-to-core advanced metric discrepancies.

The 374 unresolved current-season appearances (103 IDs), including 48 from GW8, remain unforced. Fourteen already mapped appearances still lack the corresponding core canonical identity: Matt Grimes, eight rows, and Chuba Akpom, six. These require broader independently verified canonical reconciliation; no existing mapping was rekeyed and no missing appearance was fabricated.

## Integrity and verification

- All 60 manual fixtures, all 60 frozen weekend snapshots, all 2,660 historical v3 forecasts, all pre-existing source mappings and every core player-match field outside the intended advanced-metric columns retain their original hashes.
- Database grants, row-level security settings and policies retain their original hashes.
- Team feature and both form caches were refreshed; each matches its live defining query with zero differences. Published GW9 snapshots remain frozen.
- Six existing unit suites, append-only ledger validation, TypeScript, production build, native Sharp PNG check, the original frozen browser regression and the refreshed live-database browser check passed.
- The live-data browser check shows ten future fixtures, thirty scorelines, eighty completed matches and the dated 35-of-50 scorecard, with no mobile overflow, browser errors or database writes.
- The new offline replay reproduces 118 uniquely resolved mappings and the three cases requiring separate role evidence. It performs no database writes and does not replace the established resolver.
- Implementation [594d8fc](https://github.com/MarkColonel80/PL-Results-Project/commit/594d8fce20ef5f211d6c4ad7e79daa44e3da1eb2) is READY on production deployment `dpl_BrqY2PTGGseR3AA1BbTZ8VSuAm57`. Its production build audit reports zero vulnerabilities. Authenticated production returns 200, anonymous access returns 401, and the published GW9 ledger plus 80 completed / 10 future matches pass verification. No recent error/fatal production logs were returned. See [verification receipt](data/dependency-understat-2026-10-27-verification.json).

Evidence: [mapping audit and before-images](data/understat-reconciliation-2026-10-27.json), [frozen review inputs](data/understat-reconciliation-inputs-2026-10-27.json), [replay script](scripts/review_understat_mappings_20261027.py), [guarded one-time SQL](data/understat-reconciliation-2026-10-27.sql). The SQL was already applied and intentionally rejects duplicate application.
