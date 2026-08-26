---
id: T-015
title: P2 design review package
status: backlog
phase: P2
tier: top        # adversarial cross-review — MUST be a different model family than the author
priority: 4
assignee:
depends_on: [T-010, T-011, T-012, T-013, T-014, T-016]
needs_human: true
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Cross-review the reworked schematics with an agent that did NOT author them
(different model preferred): power budget, digital PDM/channel map, pin conflicts,
T-016 MPN/footprint release, and compliance with all ratified D001–D012 decisions.
Produce the CP-C review doc with rendered PDFs.

## Context
ROADMAP CP-C entry.

## Definition of Done
`orchestration/reviews/p2-review.md` + PDFs; all findings either fixed or explicitly waived; status → review for Joshua.

## Verification
ERC zero errors proven in the doc; reviewer states model/agent identity in Log.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 codex/sol-t008: added explicit T-016 dependency; CP-C cannot approve
  a design whose microphone MPN/footprint is still provisional.
