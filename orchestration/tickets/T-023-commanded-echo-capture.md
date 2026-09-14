---
id: T-023
title: Integrated commanded TX and USB-independent snapshot capture
status: in-progress
phase: P5
tier: top
priority: 1
assignee: codex
depends_on: []
needs_human: false
created: 2026-09-05
updated: 2026-09-13
---
## Goal
Resolve REVIEW-2026-09-05 R3/R4 through sonar_top. Coordinate ownership with T-020.

## Definition of Done
- Snapshot acquisition survives absent/stalled FT232H and a delayed user trigger;
  streaming overflow remains explicit and recoverable.
- Minimal arm/fire/read/status control on existing interfaces; real TX event
  sample counter, waveform identity, explicit capture boundary and errors.
- Manufacturer-verified driver wake/settle and fault handling. TX remains idle
  until commanded within the selected part limits. No MA40S4S at 12 V; D013
  remains proposed until Joshua ratifies.
- Top-level behavioral tests cover two consecutive measurements, startup,
  absent FT clock, blocked TXE, reconnect, reset and invalid TX configuration.
- Coordinate packet/host contract with T-024. T-020 retains synthesis, timing/CDC,
  utilization and physical gates; do not claim these from simulation.

## Verification
Full gateware suite plus top-level behavioral tests. Convert the T-019 starvation
probe into desired-behavior coverage; prove TX timestamp survives host parsing.

## Log
- 2026-09-13 codex: claimed for Joshua's pre-hardware readiness request. First
  close USB-induced snapshot starvation with behavioral regression coverage;
  audit readout/build/procurement gates and record an actionable purchase and
  bring-up sequence. No hardware is available. Full commanded-TX integration,
  implementation reports and physical evidence must remain explicitly open
  unless actually delivered. T-020 keeps Vivado/physical ownership.
- 2026-09-05 codex/T-019: created. TX is tied off and fallback stops on main FIFO
  overflow. Simulation work is not blocked on a Vivado purchase.
