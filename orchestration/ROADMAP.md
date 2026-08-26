# ROADMAP — phases and checkpoints

Full rationale in `/PLAN.md`. This file tracks execution. A phase may start only when
its entry gate is satisfied. Human checkpoints (CP-x) are the only places Joshua is
required; everything else is agent work.

| Phase | Scope (tickets) | Entry gate | Exit gate |
|---|---|---|---|
| **P1** Analysis & RX design | T-001, T-002, T-006, T-007, T-008 (T-005 optional) | — (open now) | Link budget + PDM RX design reviewed at **CP-B**; parts confirmed orderable |
| **P2** Schematic rework | T-010…T-015 | T-002 + T-008 done (CP-A: done 2026-08-25) | ERC = 0 errors; BOM 100% sourced; review doc approved at **CP-C** |
| **P3** Layout | T-030… (write at P2 exit) | CP-C | DRC clean, JLC DFM pass, Joshua layout review |
| **P4** Order | T-040… | **CP-D** (money gate) | Boards + parts ordered by Joshua |
| **P5** Gateware, firmware & host SW | T-009, T-020, T-021 | — (parallel, open now; Vivado synthesis waits on host from T-007) | PDM capture TB-proven; snapshot fw demoed; host pipeline passes synthetic-data tests; bring-up runbook written |
| **P6** Bring-up & validation | T-060… (write during P5) | Boards in hand | Validation ladder rungs 1–9 logged at **CP-E** bench sessions |

## Human checkpoints

- **CP-A — Ratify decisions**: DONE 2026-08-25 (registry: 8 ratified, 4 superseded).
- **CP-B — Analysis review** (end P1): read link-budget + sim results; approve AFE values.
- **CP-C — Schematic sign-off** (end P2): review generated PDFs + review doc.
- **CP-D — Spend approval** (end P3): approve JLC order (~$400–600) and part buys. Agents prepare carts; Joshua clicks.
- **CP-E — Bench sessions** (P6): Joshua at the bench running agent-written runbooks; agents on-call for debug.

Checkpoint outcomes get recorded as a journal entry plus edits to the affected
decisions/tickets.
