---
id: T-019
title: Independent CP-B and CP-BM product-readiness review
status: done
phase: P1
tier: top
priority: 1
assignee: codex
depends_on: []
needs_human: false
created: 2026-09-05
updated: 2026-09-05
---
## Goal
Conduct Joshua's requested independent review of the current review gate and
identify the concrete path to a working sonar prototype/product.

## Scope
Read-only engineering audit of analysis, coupon hardware, gateware/firmware/host
integration and verification. Record findings and next work; do not change design
files, ratify decisions, authorize purchases, or substitute for T-015 CP-C review.

## Definition of Done
Evidence-backed review in orchestration/review/REVIEW-2026-09-05.md with severity,
source references, current verification results, and a prioritized execution path;
ticket, journal and STATUS updated.

## Verification
Run available relevant gateware, host, firmware, coupon and KiCad checks. Inspect
implementation beyond existing tests, distinguish simulation from physical proof,
and check manufacturer sources for critical unresolved electrical assumptions.

## Log
- 2026-09-05 codex: claimed independent top-tier review requested by Joshua.
  Existing dirty sonar-v1-pcb/sonar.kicad_pro belongs to Joshua and is preserved.
- 2026-09-05 codex: delivered `orchestration/review/REVIEW-2026-09-05.md` and
  durable diagnostic probes. Verdict HOLD coupon orders; resume engineering.
  Opened T-022–T-025; T-016 blocked on T-022. No design files changed.
  Verification output:

  ```text
  gateware make test: 17 PASS, including full SRAM window and XDC bijection
  host unittest with pinned NumPy 2.3.2: Ran 5 tests in 2.626s; OK
  Pico host contract/sim and both C tests: exit 0
  bake-off analyzer: SELFTEST: all synthetic threshold and selection-branch checks passed
  pinmap checker: PASS 44/44 (committed XDC snapshot, no fresh fetch)
  geometric coupon verifier: VERIFY: all coupon checks passed
  full filled SPH DRC: Found 82 violations; Found 0 unconnected items
  full filled ICS DRC: Found 92 violations; Found 0 unconnected items
  each coupon: 5 shorting_items (C1-C4 supply-ground, R1 feedback)
  REPRODUCED: stalled USB stops snapshot tap; taps before=9 after=9
  REPRODUCED: transient empty read discards subsequent valid data:
    stream ended after 0 frames; requested 1
  REPRODUCED: chunked vs whole decimator max difference=0.233102
  synthetic ingest benchmark: 3319.154 MB/s (360.15x) => PASS (memory only)
  scripts/check.sh outside sandbox: SUMMARY: all invoked KiCad commands completed successfully.
  ```

  Main ERC remains 346 messages; harness accepts violation exits. DRC in sandbox
  crashed (134); escalated read-only checks completed. Initial local selftest
  lacked matplotlib; dependency-backed rerun passed. Exact commands and source
  citations are in the review. Next action: claim T-022 on mid tier, follow KiCad
  safety protocol, correct complete pin map and physical copper before any order.
