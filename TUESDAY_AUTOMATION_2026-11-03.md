# Tuesday automation investigation — 3 November 2026

Automation 6ad7a14d306c8190b719bd87b6f73e7d remains the single enabled Tuesday 09:00 Europe/London task. UI readback showed next run 10 November 09:00 GMT and Repeat enabled; no duplicate task was created. The original task instructions already authorize cloud writes/tests/publication, so missing user authorization is not supported as a cause.

## Evidence and limits

User-supplied scheduler timings: expected 09:00; actual start 09:57:56; generic failure 10:22:58 (25m02s execution, 57m56s dispatch delay). The available scheduler UI exposes edit/pause/run/delete, but no terminal exception or engine trace. No evidence establishes a hosted 25-minute execution cap.

Vercel metadata shows six earlier temporary sessions beginning 09:02:15, 09:23:28, 09:29:50, 09:50:40, 09:59:06 and 10:21:00 GMT. Five had 1,200,000ms lifetimes and one 2,400,000ms; observed stops were at those lifetimes, with no requestedStopAt. This confirms expiring workspaces and repeated recovery. Several precede the reported scheduled run and cannot be attributed to it. The final 10:21 session did not expire at 10:22:58, so workspace expiry alone does not prove the scheduler's terminal failure.

Supabase logs queried specifically for 09:57:56–10:22:58 contain 14 PostgreSQL entries and five errors: undefined-column SQLSTATE 42703 at 09:58:53, 10:02:05, 10:02:10 and 10:12:18; generated-identity SQLSTATE 428C9 at 10:13:30 from explicitly inserting computed player_match_stats IDs. These support schema-assumption/import mistakes. Subsequent 400 native GW9 rows were successfully inserted 10:14:24–10:15:05, so the failed insert was recovered. No connection-outage or timeout error appears in the returned database window; missing service/host logs mean this is not proof that every connection succeeded.

At recovery start, Supabase already held 90 matches and GW9's 400 player records, 670 FPL records, 400 lineups, 21 goals, ten historical odds records and next-round fixture identities. GitHub/production still reflected 27 October; future snapshots were absent. Therefore the run made partial data progress but did not finish publication. This recovery verified those records and completed the remaining data stages without replaying the imports.

## Supported remediation

The checked-in cloud runbook adds schema/identity preflight, bounded provider retries, stage checkpoints, partial-state reconciliation, explicit workspace-deadline handling with snapshot/restore, exact-SHA publication guards and separate deployment verification. No model/selection/staking/eligibility change is involved.

The existing automation instructions were updated in place at 12:14 GMT to read this runbook and use these controls. Saved UI readback confirms the operational prefix and next run 10 November 09:00 GMT. Schedule/timezone and its original substantive safeguards remain unchanged. Final activation/readback status is recorded in PROJECT_CONTEXT and the publication checkpoint. This is hardening of supported failure modes, not a proven repair of the hosted scheduler's unknown terminal error.

## Viable durable-worker option — approval and credentials required; NOT activated

Keep this automation as the only Tuesday clock. Its small job would dispatch a cloud worker with an idempotency key based on the reviewed round, receive a durable run URL, and report status. It would no longer hold the entire import/review/build session open.

The worker would use a single concurrency lock, persisted stage records, bounded retries and resumable source batches. Stages: discover/validate sources; review frozen forecasts and valid paper stakes; reconcile imports/caches; create future-only snapshots and provisional news/price records; validate append-only/data contracts; build/guarded GitHub update; deploy and verify. Each stage records input/output hashes and completion before the next starts. Repeated dispatch returns or resumes the same run. No additional cron is enabled.

A dispatch-only GitHub Actions workflow or durable Vercel worker is suitable, but the interactive connected-tool grants used here are not established unattended worker credentials. Before implementation/activation, approve the destination and least-privilege access: GitHub contents write restricted to this repository with expected-SHA checks; database writes restricted to approved import/upcoming/caches operations (not frozen history/security); deployment rights restricted to this Vercel project; existing Basic-auth probes run only in the trusted Vercel environment. Do not copy personal broad tokens or publish a service-role key. Changes to database roles/grants or new persistent credentials need separate approval because they expand unattended access.

Acceptance: forced provider timeout leaves an honest coverage gap; interrupted import resumes without duplicate records; repeated dispatch is a no-op after completion; concurrent run is rejected/resumed; history/security fingerprints stay fixed; failed validation prevents publication; exact commit/domain and 200/401 probes pass; then one observed unattended Tuesday run completes. Until those pass, label recurring reliability unproven. No extra local/cloud schedule, workflow or credential was installed by this recovery.

## Approved implementation progress

The user explicitly approved the scoped cloud worker after reviewing this proposal. Implemented GitHub Actions dispatch-only workflow, GitHub OIDC broker, private database run receipts/lease and restricted RPC. Capability is production-only and sensitive; database stores only its SHA-256 hash. No new recurrence was added.

Confirmed and repaired a separate future-import defect: the manual-fixture identity sequence was 33 while the largest existing fixture ID was 100. It is now aligned to 100, so database-generated IDs start after existing records. Existing fixture IDs were untouched.

The initial worker preview failed TypeScript compilation because DOM and Node crypto JSON-web-key types differed. The explicit Node crypto type fixes it; cloud build and replacement preview passed. This was a new staging-build defect, not a diagnosis of the earlier scheduled failure.

Database transactional tests passed for rejected credentials, exclusive lease, repeated existing imports, rejection of historical changes/unapproved table operations, receipts and completed-run no-op. The test transaction was rolled back. Source adapter exercised all ten GW9 results, 400 native player rows, 400 lineups, 21 goals, 670 official fixture-level FPL rows and ten historical odds rows without production mutation; scorecard regression matches all 45 eligible historical forecasts and zero paper stakes. End-to-end live dispatch status will be recorded after the test run.

## Live acceptance and activation

The live dispatch acceptance succeeded in Actions run 41645179443. GitHub OIDC authenticated the worker; Supabase retained its lease/receipts; GITHUB_TOKEN published receipt commit 553c20f45f8a98af5afe2a36ade69e20afa9f844; Vercel dpl_5ZLXCCevFMLtZ1mBnG4Q9zUk53Gm reached READY. The exact commit passed authenticated 200 / anonymous 401 checks at 13:33:31 GMT. No source, forecast or paper rows were replayed.

At 13:35 GMT the SAME hosted task was updated in place to dispatch the worker. Saved UI confirms next run 10 November 2026 at 09:00 GMT, weekly Tuesday, United Kingdom Time, never-ending. Original substantive instructions remain in the prompt. No duplicate schedule or manual weekly Work prerequisite was added. Repeat-dispatch no-op acceptance is being checked.

The original hosted terminal error and dispatch delay remain unproven. Full unattended execution against a newly completed round awaits 10 November. Unknown player identities, reschedules, source corrections and older missing data stop for explicit reconciliation. Optional price/club/Europe coverage gaps remain visible. No model, selection, staking or eligibility rule changed.

Acceptance run: https://github.com/MarkColonel80/PL-Results-Project/actions/runs/41645179443

Supabase flags the new public SECURITY DEFINER RPC as callable by anon. This is intentional: every operation first checks the approved production-only 256-bit capability, whose hash is private. The capability is never passed to GitHub Actions or clients; GitHub uses short-lived OIDC through the broker. Previous grants, policies and function settings retain their original fingerprint.
