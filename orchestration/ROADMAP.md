# ROADMAP — phases and checkpoints

Full rationale in `/PLAN.md`. This file tracks execution. A phase may start only when
its entry gate is satisfied. Human checkpoints (CP-x) are the only places Joshua is
required; everything else is agent work.

| Phase | Scope (tickets) | Entry gate | Exit gate |
|---|---|---|---|
| **P1** Analysis & RX design | T-001, T-002, T-006, T-007, T-008 (T-005 optional) | — (open now) | Link budget + provisional PDM RX baseline and quantitative mic gate reviewed at **CP-B**; physical MPN release moves to T-016 |
| **P2** Schematic rework + mic release | T-010…T-016 | T-002 + T-008 done (CP-A: done 2026-08-25); T-010 alone waits on T-016 | T-016 MPN/footprint released at **CP-BM**; ERC = 0 errors; BOM 100% sourced; review doc approved at **CP-C** |
| **P3** Layout | T-030… (write at P2 exit) | CP-C | DRC clean, JLC DFM pass, Joshua layout review |
| **P4** Order | T-040… | **CP-D** (money gate) | Boards + parts ordered by Joshua |
| **P5** Gateware, firmware & host SW | T-009, T-020, T-021 | — (parallel, open now; Vivado synthesis waits on host from T-007) | PDM capture TB-proven; snapshot fw demoed; host pipeline passes synthetic-data tests; bring-up runbook written |
| **P6** Bring-up & validation | T-060… (write during P5) | Boards in hand | Validation ladder rungs 1–9 logged at **CP-E** bench sessions |

## Human checkpoints

- **CP-A — Ratify decisions**: DONE 2026-08-25 (registry: 8 ratified, 4 superseded).
- **CP-B — Analysis review** (end P1): review T-001 and T-008, approve or amend
  the quantitative microphone gate. This checkpoint does not claim the physical
  bake-off is complete and does not authorize a purchase.
- **CP-BM — Microphone coupon + release** (during P2): after an agent prepares
  T-016's coupon design, sourcing/order package, runbook, and analysis, Joshua
  explicitly authorizes/places any coupon order, provides or operates the calibrated
  bench, and ratifies the final MPN/footprint. T-016 stays `review` until all three
  human actions are complete; no production mic freeze occurs earlier.
- **CP-C — Schematic sign-off** (end P2): review generated PDFs + review doc.
- **CP-D — Production spend approval** (end P3): approve the main JLC order
  (~$400–600) and production part buys. Agents prepare carts; Joshua clicks. The
  separate, earlier coupon spend is authorized only at CP-BM.
- **CP-E — Bench sessions** (P6): Joshua at the bench running agent-written runbooks; agents on-call for debug.

Checkpoint outcomes get recorded as a journal entry plus edits to the affected
decisions/tickets.
