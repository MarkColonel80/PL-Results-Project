# Tuesday recovery receipt — 10 November 2026

The existing 10 November run completed successfully on attempt 3 at 17:09:59 GMT. [GitHub Actions run](https://github.com/MarkColonel80/PL-Results-Project/actions/runs/42787760318) · [Successful evidence artifact](https://github.com/MarkColonel80/PL-Results-Project/actions/runs/42787760318/artifacts/13786685092) · [Weekend page](https://pl-data.colly.me.uk/betting/weekend)

## Verified identity reconciliation

| FPL season ID | Permanent canonical code | Official Opta code | FotMob ID | Display name |
|---|---|---|---|---|
| 671 | 536108 | p536108 | 1524184 | Luca Gunter |
| 672 | 671103 | p671103 | 1714552 | Modou Kéba Cissé |

Official FPL bootstrap IDs and Opta codes matched the native FotMob playerStats Opta IDs in matches 5795511 and 5795512. Neither canonical identity nor a conflicting source/season mapping existed. Added exactly two players, two 2026/27 season links and two verified FotMob mappings. Names were display metadata only. The original failure was reproduced from its saved before-state; all 400 native GW10 rows and all 672 bootstrap identities passed after these explicit additions. Full source timestamps/hashes, readback and SQL are in [verification evidence](data/tuesday-2026-11-10-verification.json) and [identity SQL](data/identity-reconciliation-2026-11-10.sql).

The Python fail-closed identity assertion and database permanent-ID/conflict checks remain intact.

## Same-date recovery and operational repair

The dispatch date, automation ID, dispatch blob and workflow were unchanged. Retries used the same Actions run and original main SHA 3944e4f81f6a923a4aaf55f701062aab0c387c86. No active or successful duplicate was started.

Attempt 2 passed identity validation, reviewed GW10 and committed ten results, ten canonical matches and twenty fixture-source mappings. Its first player batch hit an upstream reset while the database scanned historical JSON rows; that player transaction subsequently rolled back. After confirming no active database operation remained, the existing lookup was given redundant predicates on its text identity columns so existing indexes can be used. All original JSON comparisons, capability/lease/date/season checks, allowed tables, conflict rejection, history guards and permissions remain. No index or broader grant was added.

Eight allowlisted table lookups returned the same existing rows with both predicates. A representative new-player lookup changed from a full scan to an index scan (0.160 ms measured). Invalid capability rejection and function security metadata were checked. The exact source repair is recorded in scripts/pl_weekly_worker.sql. Attempt 3 safely recognised the committed results/mappings and completed the remaining stages.

## Results and coverage

| Season layer | Before | After | Added across recovery |
|---|---:|---:|---:|
| Completed matches | 90 | 100 | 10 |
| Rich player rows | 3,600 | 4,000 | 400 |
| FPL fixture rows | 5,890 | 6,562 | 672 |
| Lineups | 3,600 | 4,000 | 400 |
| Goal events | 243 | 273 | 30 |
| Historical odds | 90 | 100 | 10 |
| Understat staged rows | 2,461 | 2,461 | 0 |

All ten GW10 matches have 40 native player rows and 22 starters; 30 goal events equal summed final scores. All 672 FPL rows resolve to permanent identities and have zero point-component discrepancies. Approved caches now contain 200 current-season team rows for 100 matches, with no missing xG.

The generated refresh report's “matches: 0” describes attempt 3 only: attempt 2 had already committed all ten. The total successful recovery added ten exactly once.

## Review and next round

Ten eligible GW10 forecasts: research Brier 0.531117, current view 0.533422, saved market 0.548058; lower is better. Cumulatively, 55 of 70 archived forecasts are eligible: research 0.622962, current 0.639920, market 0.608595. The market remains ahead over the cumulative sample.

The five watched fixtures produced two winning watched outcomes (Brighton and Sunderland); Arsenal draw/Hull, Palace and Manchester United watches did not win. These were watches, not stakes. There were zero valid recorded paper selections, zero settlements to add, zero stake/profit and undefined ROI. No retrospective selection was created.

Ten official GW11 fixtures on 21–23 November have fresh future-only snapshots. Every side has at least five relevant venue matches, exceeding the unchanged minimum four. Ten provisional watches extend the ledger from 49 to 59 events; all original events and settlements are unchanged.

## Source gaps and proposed research

- Understat returned its maintenance page (“We will come back soon”) at 17:01 GMT, without fixture/player data. GW9/GW10 Understat coverage and earlier unresolved mappings remain explicit gaps.
- The approved Transfermarkt bundle still ends at 24 May 2026 for the PL and contains no 2026/27 rows.
- The Football-Data future coupon fetched at 17:08 GMT supplied no GW11 comparison quotes. All ten prices remain null, with no fabricated observation time. Historical GW10 odds were available and imported.
- Official FPL availability was fetched at 17:07 GMT. Club press conferences, confirmed XIs, executable named-bookmaker prices and official Europe/international workload confirmation remain pending. Availability flags are provisional.

No model change is justified by this single improved round. Suggested, unapplied research: assess calibration and sensitivity stability on a larger forward sample using frozen forecasts and saved prices, with a separate evaluation period. Do not tune draw, injury, goalkeeper, market-blend, staking or eligibility adjustments to GW10.

## Validation and production

Source tests and seven existing unit suites passed, along with TypeScript and the production build. Additional checks passed for the 49-event ledger prefix, all ten dated forecasts/news records, explicit missing-price handling and exact official fixture identity/timing. The older dated checker assumes every fixture has a price; this recovery used its forecast/news/ledger assertions with the already-approved nullable-price contract.

All 70 played fixture/snapshot records match the durable history guard. All 2,660 frozen v3 predictions, previous player/season/source mappings, GW1–9 source rows and public permission/policy fingerprints are unchanged.

Worker publication used a non-forced guarded child commit: 085297ed98425a6d1236eea4cf0f03713a517091. Vercel production deployment dpl_6cA7YXpupPxAZuaZvikCcTKE7r8Q reached READY and was assigned to pl-data.colly.me.uk. The exact commit passed authenticated HTTP 200 and anonymous Basic-auth HTTP 401 at 17:09:58.720 GMT. The durable 2026-11-10 receipt is complete.

This follow-up commit records the evidence and reconciles the query repair into source control. No further data import or forecast recalculation is part of that documentation publication. The sole Tuesday 09:00 Europe/London automation, frozen v3, model/selection/staking/eligibility rules and existing access protection remain unchanged. No real bet or third-party message was sent. All execution used cloud services.

## Final evidence retention and readback

The durable report, source hashes, mapping SQL, Supabase receipts and all three Actions artifacts are retained in connected cloud services. The temporary diagnostic workspace expired before its optional filesystem snapshot could be saved; its raw scratch cache is not claimed as retained. A read-only trusted-build check, scripts/verify_tuesday_recovery_live.mjs, verifies authenticated/anonymous production access, deployed GW11 ledger markers, live fixture identities and missing-price handling with credentials held only in the production build environment.
