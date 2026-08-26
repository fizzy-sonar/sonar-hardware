---
id: T-013
title: Connect the h-bridge; TX connector
status: backlog
phase: P2
priority: 3
assignee:
depends_on: [T-002]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Give 20kHz-h-bridge.kicad_sch real hierarchical ports (defect #4), wire control lines to the digital sheet, add the off-board TX connector + optional series-L/snubber footprints (DNP-able).

## Context
Decisions D007, D001 (center cell hosts connector/hole).

## Definition of Done
ERC-clean; drive path traceable top-sheet → DRV8876 → connector.

## Verification
check.sh ERC.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
