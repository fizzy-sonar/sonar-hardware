---
id: T-022
title: Repair coupon electrical and physical release blockers
status: ready
phase: P2
tier: mid
priority: 1
assignee:
depends_on: []
needs_human: false
created: 2026-09-05
updated: 2026-09-05
---
## Goal
Resolve REVIEW-2026-09-05 R1/R2 so T-016 can return to CP-BM review.

## Definition of Done
- Verify all CDCLVC1112PWR pins from TI SCAS895B; correct generator, schematic,
  routing, symbol/footprint assets and exports for both variants. Audit hard-coded
  pad-number routing too. Follow KiCad-open safety protocol.
- Fix 0603 pad orientation/shorts, TP6 clearance, port copper/paste/anchor geometry,
  courtyard and applicable DRC rules. Filled-board DRC: zero errors/unconnected
  except individually justified exceptions; no shorts may be waived.
- Independent manufacturer-pin assertions, same-footprint different-net copper
  checks and no-net pad checks catch the reviewed failures. Inspect actual
  copper, mask, paste, drill and placement exports.
- Update order package and T-016 evidence; remove the engineering hold only after
  verifying repaired artifacts. This ticket does not authorize ordering.

## Verification
Coupon suite plus actual `kicad-cli pcb drc --refill-zones --severity-all
--exit-code-violations`; no sandbox-crash substitution. Record independent pin
mapping, source revision, hashes and full outputs.

## Log
- 2026-09-05 codex/T-019: created from confirmed pin errors and DRC shorts.
  Start with the manufacturer pin map and actual pad orientation.
