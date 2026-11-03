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

## Approved durable worker

The user approved this architecture and its scoped unattended access in this chat. The existing Tuesday task is the sole clock; it writes data/weekly-dispatch.json. A dispatch-only GitHub Actions workflow executes bounded source imports/reviews/tests and guarded publication, with a private database lease, stage receipts and historical forecast guards. Repeated completed-date dispatches are readback-only. No cron or second automation is configured.

GitHub uses its repository-scoped GITHUB_TOKEN plus short-lived OIDC. The Vercel broker verifies repository ID, main, workflow, event and token expiry. A production-only sensitive capability permits only restricted database operations; its hash is private. Existing Basic-auth probes run in Vercel. No broad personal token or service-role key was introduced.

## Approved implementation progress

The user explicitly approved the scoped cloud worker after reviewing this proposal. Implemented GitHub Actions dispatch-only workflow, GitHub OIDC broker, private database run receipts/lease and restricted RPC. Capability is production-only and sensitive; database stores only its SHA-256 hash. No new recurrence was added.

Confirmed and repaired a separate future-import defect: the manual-fixture identity sequence was 33 while the largest existing fixture ID was 100. It is now aligned to 100, so database-generated IDs start after existing records. Existing fixture IDs were untouched.

The initial worker preview failed TypeScript compilation because DOM and Node crypto JSON-web-key types differed. The explicit Node crypto type fixes it; cloud build and replacement preview passed. This was a new staging-build defect, not a diagnosis of the earlier scheduled failure.

Database transactional tests passed for rejected credentials, exclusive lease, repeated existing imports, rejection of historical changes/unapproved table operations, receipts and completed-run no-op. The test transaction was rolled back. Source adapter exercised all ten GW9 results, 400 native player rows, 400 lineups, 21 goals, 670 official fixture-level FPL rows and ten historical odds rows without production mutation; scorecard regression matches all 45 eligible historical forecasts and zero paper stakes. End-to-end live dispatch status will be recorded after the test run.

## Live acceptance and activation

The live dispatch acceptance succeeded in Actions run 41645179443. GitHub OIDC authenticated the worker; Supabase retained its lease/receipts; GITHUB_TOKEN published receipt commit 553c20f45f8a98af5afe2a36ade69e20afa9f844; Vercel dpl_5ZLXCCevFMLtZ1mBnG4Q9zUk53Gm reached READY. The exact commit passed authenticated 200 / anonymous 401 checks at 13:33:31 GMT. No source, forecast or paper rows were replayed.

At 13:35 GMT the SAME hosted task was updated in place to dispatch the worker. Saved UI confirms next run 10 November 2026 at 09:00 GMT, weekly Tuesday, United Kingdom Time, never-ending. Original substantive instructions remain in the prompt. No duplicate schedule or manual weekly Work prerequisite was added. Repeat dispatch [41646005513](https://github.com/MarkColonel80/PL-Results-Project/actions/runs/41646005513) passed; its log confirms readback only with no data or ledger changes.

The original hosted terminal error and dispatch delay remain unproven. Full unattended execution against a newly completed round awaits 10 November. Unknown player identities, reschedules, source corrections and older missing data stop for explicit reconciliation. Optional price/club/Europe coverage gaps remain visible. No model, selection, staking or eligibility rule changed.

Acceptance run: https://github.com/MarkColonel80/PL-Results-Project/actions/runs/41645179443

Supabase flags the new public SECURITY DEFINER RPC as callable by anon. This is intentional: every operation first checks the approved production-only 256-bit capability, whose hash is private. The capability is never passed to GitHub Actions or clients; GitHub uses short-lived OIDC through the broker. Previous grants, policies and function settings retain their original fingerprint.
