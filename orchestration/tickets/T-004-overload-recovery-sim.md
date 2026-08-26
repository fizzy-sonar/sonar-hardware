---
id: T-004
title: TX-blast overload recovery simulation
status: superseded
phase: P1
priority: 3
assignee:
depends_on: [T-003]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Transient sim: 124 dB-SPL-equivalent input burst into the final AFE; measure time to settle within 1 LSB-equivalent. Target < 200 µs. Evaluate clamp/limiter options if it fails.

## Context
Center TX (D001/D007) couples maximally into all 24 mics; recovery time + chirp length set the blind zone (see T-001 output).

## Definition of Done
Result + chosen mitigation documented in the T-003 report; blind-zone number handed to T-001's table.

## Verification
Transient netlist checked in; settle-time measurement scripted.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 claude (fable): SUPERSEDED by D011 (all-digital PDM mics — no analog AFE). Replacement: T-008.
