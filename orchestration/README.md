# Orchestration — how agents work in this repo

This directory is the coordination layer for the Sonar v1 project. **All engineering
work is done by AI agents** (Claude, Codex, Kimi); the only human is Joshua, who has
~2–4 h/week and acts through the checkpoints defined in `ROADMAP.md`. If you are an
agent, this file is your protocol. Architecture context lives in `/PLAN.md`.

## Map

| Path | What it is |
|---|---|
| `STATUS.md` | Living snapshot: current phase, active work, blockers, next actions. **Read first, update last.** |
| `ROADMAP.md` | Phases P1–P6 with entry/exit gates and the human checkpoints (CP-A…CP-E) |
| `decisions/` | Decision registry (D001…). `proposed` → Joshua ratifies → `ratified`. Ratified decisions are binding. |
| `tickets/` | One file per unit of work. The frontmatter is the state machine. |
| `journal/` | One file per working session, append-only. The project's memory. |

## Session protocol (every agent, every session)

1. **Orient**: read `STATUS.md`, then `ROADMAP.md`, then skim the newest 2–3 `journal/` entries. Read `/PLAN.md` if you haven't in this context.
2. **Pick work**: continue a ticket already assigned to you, else pick the highest-priority ticket with `status: ready` whose `depends_on` are all `done`. Never work outside a ticket — if the work has no ticket, write the ticket first.
3. **Claim it**: set `status: in-progress`, `assignee: <your name, e.g. codex/claude/kimi>`, bump `updated:`. Commit that claim to `main` immediately (small, so two agents don't collide).
4. **Branch**: substantive work happens on `agent/<ticket-id>-<slug>` (e.g. `agent/T-003-afe-sim`). Doc/status/ticket-metadata edits may go straight to `main`. Never force-push, never rewrite history, never push to remotes unless already configured.
5. **Work** to the ticket's Definition of Done. Follow repo conventions in `/CLAUDE.md` (no edits under `*-backups/`, `.history/`; never commit `.kicad_prl`).
6. **Verify**: run the ticket's Verification commands (and `scripts/check.sh` once it exists). Paste real output into the ticket's Log. Unverified work is not done.
7. **Close out** (even mid-task): append a dated entry to the ticket Log (what you did, what's left, exact next step); update `STATUS.md`; add/extend today's `journal/` entry; commit. Assume the next session is a different agent with zero memory — write for them.

## Hard rules

- **Never spend money or place orders.** Purchases, board orders, and account signups are Joshua-only; tickets that end in a purchase produce a ready-to-click list and set `needs_human: true`.
- **Ratified decisions are binding.** To deviate, write a new `decisions/` file with `status: proposed` that supersedes the old one, mark the ticket `blocked`, and surface it in `STATUS.md`. Do not quietly implement a different architecture.
- **Escalate, don't guess**, on: anything irreversible, deleting non-generated files, scope changes, or contradictions between documents (flag them — newest ratified decision wins).
- **KiCad file safety**: hand-editing `.kicad_sch`/`.kicad_pcb` while KiCad has the project open loses the edits. Before a schematic-editing session, check `STATUS.md` for a "KiCad open" note from Joshua; after editing, note in STATUS that files changed on disk so Joshua reloads before opening.
- One ticket `in-progress` per agent at a time.

## Definition of "done" for any ticket

Deliverable exists in the repo (not just described), verification output is in the
ticket Log, ticket `status: done`, `STATUS.md` and journal updated. Tickets with
`needs_human: true` go to `status: review` instead — only Joshua moves those to `done`.
