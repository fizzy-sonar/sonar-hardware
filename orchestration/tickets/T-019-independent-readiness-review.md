---
id: T-019
title: Independent CP-B and CP-BM product-readiness review
status: in-progress
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
