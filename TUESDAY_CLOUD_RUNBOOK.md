# Tuesday cloud execution runbook

Single scheduler: hosted ChatGPT automation 6ad7a14d306c8190b719bd87b6f73e7d, Tuesday 09:00 Europe/London, DST-aware. Never create a second cron, local executor or manual weekly prerequisite. PROJECT_CONTEXT.md is the first read. This operational runbook does not change betting/model rules.

## Preflight and durable stages

1. Read GitHub main SHA, latest checkpoint and immutable ledger. Read current Supabase counts/last completed round, upcoming fixtures and Vercel production SHA before assuming the prior run did nothing. Reconcile partial work first. Acquire only one active cloud workspace for this recovery; inspect existing sessions before creating another.
2. Inspect relevant columns, unique keys and identity metadata through information_schema/pg_catalog before generating SQL. Known pitfalls: betting_manual_fixtures has no season column; match_source_ids uses canonical_match_id (verify schema); historical_market_odds uses source_match_date, not date; pg_indexes uses tablename. Let GENERATED ALWAYS identity IDs populate themselves; never compute max(id)+row_number and never use identity override to force an import.
3. Save source timestamps, before-state fingerprints and the previous ledger in the cloud workspace. Keep a small durable JSON checkpoint per date in GitHub with stage, base SHA, source coverage, affected row ranges, evidence and next action. Distinguish applied database work from published files and verified deployment. Checkpoint stage boundaries; never label a run complete before production readback.
4. Review the full completed round including Monday, using archived probabilities/prices/events. Settle only recorded valid paper stakes. Unfinished games stay pending. No backfilled picks or historical reforecast.
5. Fetch bounded source batches with explicit network timeout and capped retries. Validate provider payload shape and permanent IDs. Optional unavailable sources (e.g. Understat) become explicit gaps, never guessed identities or endless retries. Fail closed if essential approved inputs are absent.
6. Reconcile new source data idempotently, retaining identities/provenance. Refresh only approved aggregate/form/feature caches, in established order. Never rebuild historical research layers to make a weekly run pass.
7. Verify official next fixtures; run existing future-only snapshot SQL and candidate DML with the unchanged four-match gate. Existing schema needs no repeated ALTER. Save timestamped public comparison prices and official news; confirmed teams/executable quotes remain separate requirements. Append provisional watch/pass only.
8. Run existing value, round, news, score, review and paper tests; append-only validator against the previous ledger; new dated-data verification; production build. Compare protected before/after hashes and security metadata. Guard main update with exact expected SHA; re-read and reconcile on conflict, never force.
9. Verify Supabase readback, Vercel exact commit READY and custom-domain alias. Run authenticated 200 and anonymous Basic-auth 401 probes inside Vercel's trusted build environment, using existing secrets in memory only. Never print credentials or weaken authentication.
10. Update PROJECT_CONTEXT and dated review/refresh reports. On no material change, report briefly without duplicate imports/decisions. On a blocker, checkpoint completed stages and give the specific missing prerequisite.

## Cloud workspace lifecycle

Vercel sessions are temporary. Read timeout/createdAt from the session response; do not assume extension is allowed. Request a sufficient supported lifetime at creation. Before its deadline (leave at least five minutes), stop launching long commands, save the stage checkpoint and create a filesystem snapshot using the supported snapshot API. Snapshotting stops the old session. Restore a successor from that snapshot and verify files before continuing. A restart is a workspace replacement, not another recurring schedule. Do not clone/reinstall/reimport blindly after expiry.

Keep command/output batches small. Tool logs can truncate long strings; write detailed audit artifacts in the cloud workspace and retrieve bounded summaries. Poll asynchronous command/deployment completion with their IDs, not by reissuing mutations. Keep required data validation bounded to affected/current-season rows; avoid expensive all-history live forecast recomputation.

## Escalation and reliability boundary

This runbook fixes observed schema and workspace-lifecycle mistakes, not an unknown hosted-automation terminal error. Do not claim a 25-minute ChatGPT limit without terminal logs. Record scheduled time, actual start/end, generic error and cloud session/command IDs separately. A successful manual recovery does not prove unattended execution.

If substantial hosted Work continues to fail, propose the reviewed single-clock durable-worker architecture in TUESDAY_AUTOMATION_2026-11-03.md. It requires approved unattended credentials and a tested dispatch path before activation. Keep the existing task as the sole scheduler; no second schedule may be enabled.
