---
id: T-010
title: Rebuild eight_transducer_array sheet
status: backlog
phase: P2
priority: 1
assignee:
depends_on: [T-002, T-008]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
**2026-08-25 scope update (D011)**: rebuild as PDM tiles from T-008 (mics + clock + data pairing), NOT preamps/ADCs. Original text below kept for history.

Replace the mixed 8× rx_amp + 1× quad_rx_pre_amp structure with: 8 mics → 2× quad preamp (T-003 values) → 2× ADC (D002), TDM out. Delete the legacy rx_amp path and the parallel-bus labels.

## Context
Defect #1/#2/#5 in PLAN.md §1. Blocked until CP-A ratifies D002 and T-005 reports (D008 gate).

## Definition of Done
Sheet ERC-clean in isolation; hierarchical ports match the new digital sheet (T-011); no dangling rails.

## Verification
`scripts/check.sh` ERC section; screenshot/PDF in build/ for CP-C.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
