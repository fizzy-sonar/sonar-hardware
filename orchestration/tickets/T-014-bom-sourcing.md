---
id: T-014
title: Full BOM with LCSC mapping
status: backlog
phase: P2
tier: cheap        # BOM table + LCSC stock lookup
priority: 2
assignee:
depends_on: [T-010, T-011, T-012, T-013]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Export full BOM; map every line to LCSC part number or explicit Global-Parts/consign flag; snapshot stock + price; roll up cost.

## Context
Decision D009; parts matrix from T-002.

## Definition of Done
`orchestration/bom.md` (or csv) 100% mapped; total cost vs budget in PLAN.md §5; unsourceable parts escalated.

## Verification
Re-run stock check on a second day before CP-D; both snapshots in Log.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
