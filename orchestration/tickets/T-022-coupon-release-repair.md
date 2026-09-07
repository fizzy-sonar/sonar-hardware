---
id: T-022
title: Repair coupon electrical and physical release blockers
status: done
phase: P2
tier: mid
priority: 1
assignee: codex
depends_on: []
needs_human: false
created: 2026-09-05
updated: 2026-09-06
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
- 2026-09-06 codex: completed rev B repair and final verification. KiCad was
  closed before regeneration; reload both coupon projects. Preserved Joshua's
  `sonar-v1-pcb/sonar.kicad_pro` edit. Complete TI SCAS895B map independently
  checked against schematic and PCB; rebuilt pin-number routing and supplied
  all five VDD bypasses. Canonical library placement fixes pad orientation,
  annular anchor/port geometry, courtyard drift and TP6; no shorts waived.
  Output summary from `check_coupons.sh` (exit 0; verbatim log in evidence):
  ```text
  regen: byte-identical across two runs
  sph: Found 0 violations / Found 0 unconnected items
  ics: Found 0 violations / Found 0 unconnected items
  PASS sph/ics: all 24 U1 pads vs independent TI map
  PASS sph/ics: schematic/PCB exact pin-net parity (94 pads)
  PASS sph/ics: five 100 nF buffer bypass capacitors
  VERIFY: all coupon checks passed
  SELFTEST: all synthetic threshold and selection-branch checks passed
  SUMMARY: coupon package checks passed
  ```
  Four negative tests per variant pass (wrong U1 power pin, same-footprint short,
  no-net-pad contact, port-filling anchor). Actual separate drills and metric
  CSV/BOM checks pass: 4 acoustic NPTH, 21 body-centroid SMD placements, 23 components.
  Mic port-to-centroid offsets asserted independently; raw origins retained.
  Schematics made readable and rerendered; exact parity/ERC checks pass afterward.
  Independently rendered/inspected all four copper layers, paste and mask per
  variant; hashes and logs saved in `orchestration/review/evidence-2026-09-06-t022/`.
  `scripts/check.sh` exit 0: all invoked KiCad commands completed; main PCB
  baseline remains 175/499/0, NOT a release. Release record and order docs updated;
  T-016 returned to human review. DFM/stock/price/purchase/bench gates remain;
  no purchase, no decision ratification. Next engineering task is T-023.
  Guided review refreshed and checked: 8 steps, 11 items, 71 images, 158/158
  local references resolve, 18/18 required assets; PASS. Final audit: 66 archived
  source/export hashes match current files; all 12 inspected Gerber PNGs unchanged.
- 2026-09-05 codex: claimed implementation after Joshua said continue. Scope is
  both coupon projects and their generator/verification/export documentation.
- 2026-09-05 codex/T-019: created from confirmed pin errors and DRC shorts.
  Start with the manufacturer pin map and actual pad orientation.
