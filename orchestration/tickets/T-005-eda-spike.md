---
id: T-005
title: EDA spike: diodeinc/pcb (Zener) go/no-go
status: in-progress
phase: P1
tier: mid        # optional spike; tool evaluation
priority: 5
assignee: codex/terra-t005
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-26
---
## Goal
Port `power_supply` + one 4-mic AFE tile to diodeinc/pcb. Judge: (a) BOM coverage for our exact parts, (b) generated KiCad netlist/layout quality, (c) does hand-edited placement survive a `pcb layout` re-run, (d) ERC-equivalent checks, (e) reviewability for Joshua (can he read it in 10 min?). Optionally repeat 1 tile in atopile for comparison (its JLC part picker is relevant to D009).

## Context
Decision D008 — this ticket IS the gate. Spike lives in `spikes/eda-zener/`, never merged into the main design. Time-box: ~2 agent-days.

## Definition of Done
`spikes/eda-zener/REPORT.md` with a clear GO / NO-GO and evidence for (a)–(e). If GO: draft superseding decision D0xx for Joshua.

## Verification
Report exists; build commands in it actually run; verdict stated in the first line.

## Log
- 2026-08-25 claude (fable): demoted to OPTIONAL/NON-GATING per D008 amendment — P2 does not wait on this.
- 2026-08-25 claude (fable): ticket created from architecture review.
