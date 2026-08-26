---
id: T-010
title: Rebuild eight_transducer_array sheet
status: backlog
phase: P2
tier: mid        # KiCad schematic edits from a settled design
priority: 1
assignee:
depends_on: [T-002, T-008, T-016]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Rebuild `eight_transducer_array.kicad_sch` as the D011 PDM microphone-array sheet:
released digital microphones, clock fanout/termination, paired DATA nets, 3.3 V mic
rail/decoupling, SELECT straps, and bottom-port keepouts. Delete the superseded
preamp/ADC/TDM path and legacy parallel-bus labels.

## Context
D011/D012 are binding; `docs/pdm-rx-design.md` defines the provisional electrical
topology and logical channel map. **Do not freeze or place a microphone MPN or
footprint until T-016 is done.** T-016's release record supplies the exact MPN,
manufacturer land-pattern revision, clock rate, and any required contract update.
This deliberate dependency lets T-011/T-012/T-013 proceed while the physical
coupon comparison and Joshua-only CP-BM actions are outstanding.

## Definition of Done
Sheet ERC-clean in isolation; only T-016's released MPN/footprint appears; all 24
ports and keepouts follow the released geometry; hierarchical ports and channel
map match T-011; no dangling rails.

## Verification
`scripts/check.sh` ERC section; screenshot/PDF in build/ for CP-C.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 codex/sol-t008: independent T-008 review removed the premature SPH
  footprint freeze. Added T-016 as a hard dependency and rewrote the obsolete
  analog goal/context for D011. No KiCad file was edited.
