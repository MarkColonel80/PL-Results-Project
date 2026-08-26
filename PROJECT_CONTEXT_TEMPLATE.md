# PROJECT_CONTEXT.md Template

Use this file as the starting point for `PROJECT_CONTEXT.md` in every new software/data project.

## Project purpose

- What the project does
- Current goal / success criteria

## Connected systems

- **GitHub:** repository, default branch, access expectations
- **Supabase:** project name/ref, database role in the project
- **Vercel:** project/team, production domain/deployment role

## Standing workflow

- Treat GitHub code + Supabase data + Vercel deployment as one connected project when applicable.
- Prefer direct inspection through connected tools instead of asking Mark to relay dashboard/database/site state.
- Keep this file current throughout the project.
- In every fresh ChatGPT conversation, read this file first and verify live state before making changes.
- Only ask Mark to run local commands when the task genuinely requires his local machine/runtime.

## Architecture / important files

- Key application components
- Important scripts
- Database tables/views/functions
- Deployment/runtime notes

## Safety / data integrity rules

- Important invariants
- What must never be overwritten automatically
- Dry-run/audit requirements
- Identity/mapping rules where relevant

## Current live state

- Data counts/checkpoints
- Current deployment status
- Current branch/commit if relevant

## Decisions already made

- Material design/architecture/data decisions and why

## Completed work

- Significant completed milestones

## Open issues / unresolved questions

- Known bugs
- Ambiguities
- Work deliberately deferred

## Immediate next step

1. Exact next action
2. Verification required
3. What must not be done yet

## Continuation instruction

At the start of any new ChatGPT conversation about this project, read `PROJECT_CONTEXT.md` first, then inspect current GitHub, Supabase and Vercel state as needed. Do not ask Mark to re-explain information recoverable from those systems.
