---
id: T-008
title: PDM mic selection + RX electrical design
status: in-progress
phase: P1
tier: top        # PDM timing/skew analysis, clock-tree design from datasheets
priority: 1
assignee: codex/sol-t008
depends_on: [T-002]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Per D011: pick the PDM ultrasonic mic (from T-002's matrix) and design the digital RX:
L/R data-line pairing map (24 mics → ~12 data lines), clock-tree topology (fanout,
buffering, skew tolerance at ~4.8 MHz, ultrasonic-mode clock requirements per
datasheet), mic supply rail + per-mic decoupling/filtering, PCB acoustic port rules.
Define the mic-tile schematic block that T-010 instantiates.

## Context
D011 (ratified). Candidates: ICS-41350/41352, SPH0641LU4H (lifecycle check!), T5838.
The mic's clock frequency and edge discipline set the T-020 CIC input contract —
write `docs/pdm-capture-contract.md` jointly with T-020 (clock rate, which edge each
mic drives, decimation ratio, expected output rate).

## Definition of Done
Mic MPN chosen with rationale; pairing + clock-tree design documented; mic-tile
schematic block drafted; pdm-capture-contract.md v1 committed.

## Verification
Datasheet numbers cited for: ultrasonic-mode clock range, current draw (×24), data
setup/hold vs FPGA input timing at chosen clock. Cross-checked by T-020's testbench
parameters.

## Pairing decision (2026-08-25 discussion with Joshua)
Default: L/R pairing, 24 mics -> 12 data lines (the mics' designed stereo mode;
FPGA samples via IDDR). Known deterministic skew: paired mics sample half a PDM
period apart = 104-163 ns = ~56 um acoustic-path equivalent = ~1-2 deg @ 32 kHz —
negligible vs calibration tolerances, and exactly cancellable with a half-sample
shift on odd channels pre-decimation (document in the capture contract).
Alternative on the table: UNPAIRED 24 data lines (Cmod pin budget allows: ~39/52
pins incl. Ethernet provision) — zero skew, single-edge sampling, +12 pins/traces.
T-008 owner: pick one, justify in the Log; electrical care points if paired:
tri-state hand-off gap per datasheet, optional weak pull on shared lines.

## Log
- 2026-08-25 claude (fable): created per D011 (replaces T-003/T-004).
