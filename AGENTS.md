# Agent entry point — Sonar

This repo's engineering work is done by AI agents (Claude, Codex, Kimi). Before doing
ANYTHING, read, in order:

1. `orchestration/README.md` — the working protocol (session ritual, model routing, hard rules).
2. `orchestration/STATUS.md` — current state, then pick a ticket per the protocol.
3. `PLAN.md` — architecture plan and rationale.
4. `CLAUDE.md` — repo layout and KiCad conventions (applies to all agents, not just Claude).

## Before you start work: the tier check

Every ticket carries a `tier:` field — `cheap`, `mid`, or `top`. It says what class of
model the work is worth (routing table in `orchestration/README.md`).

**If you are a top-tier / high-reasoning model and the ticket says `tier: cheap`,
stop and say so in your first message**, then offer to hand it back so it can be
re-launched on a cheaper model. Running datasheet lookups and BOM tables on a
reasoning-ultra budget is the single biggest avoidable cost in this project, and the
budget is shared with the tickets that genuinely need deep reasoning (T-008, T-011,
T-015, T-020).

Conversely, if you are a small/fast model holding a `tier: top` ticket, say so and
hand it back rather than guessing at timing analysis or novel HDL.

## Session-size discipline

The protocol (orient → claim → work → close out) should fit in roughly 30–50 k of
context. If you find yourself past ~150 k, you are probably re-deriving context that
the ticket, journal, or PLAN should have carried — fix those files as part of your
close-out so the next session is cheaper.

## Non-negotiables

Never spend money or place orders. Ratified decisions in `orchestration/decisions/`
are binding. Work inside tickets. Log everything — the next agent has no memory of
your session. If one provider hits a rate limit, the work moves to another provider;
this layer is deliberately provider-agnostic.
