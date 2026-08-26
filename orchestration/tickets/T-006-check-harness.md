---
id: T-006
title: kicad-cli check harness + CI
status: ready
phase: P1
priority: 2
assignee:
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Create `scripts/check.sh`: ERC on all schematics, DRC on the PCB, netlist + PDF/SVG export to `build/` (gitignored), BOM export. Add a GitHub Actions workflow if a runner with kicad-cli is feasible; otherwise document local usage. Record the CURRENT error baseline (do not fix errors here — that's P2).

## Context
Repo has KiCad 10 projects (`sonar-v1-pcb/sonar.kicad_pro`). PDFs are how Joshua reviews from his phone; ERC-zero is a P2 exit gate (ROADMAP).

## Definition of Done
`./scripts/check.sh` runs end-to-end on a clean checkout; baseline error counts recorded in the Log; exports land in `build/`.

## Verification
Run it twice; identical output; paste summary in Log.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
