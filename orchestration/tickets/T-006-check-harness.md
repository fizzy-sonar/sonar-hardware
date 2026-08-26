---
id: T-006
title: kicad-cli check harness + CI
status: done
phase: P1
tier: cheap        # shell scripting against kicad-cli
priority: 2
assignee: codex/luna-t006
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
- 2026-08-25 codex/luna-t006: Added `scripts/check.sh` and usage documentation.
  It discovers PATH or macOS KiCad 10 kicad-cli, runs top-level hierarchical ERC,
  DRC, netlist, PDF/SVG, and BOM exports into ignored `build/`. Missing tool is a
  harness failure (exit 2); design-command violations are reported without failing
  the harness (exit 0), preserving baseline for P2.
- Host KiCad 10 was found at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.
  `bash -n scripts/check.sh` passed. Baseline ERC reports: sonar 512 (352 errors,
  160 warnings), rx_amp_sim
  32 (10 errors, 22 warnings), txrx_dev 76 (9 errors, 67 warnings). DRC commands
  aborted with KiCad exit 134 in the sandbox; the repaired harness reports these
  as hard tool failures and exits 1. ERC/DRC exit 5 is soft-accepted as the
  observed baseline violation code. In two approved unsandboxed macOS runs,
  overall exit was 0 both times with identical summaries: all ERC and DRC commands
  returned baseline code 5 and all exports returned 0. DRC baselines were sonar
  175 violations + 499 unconnected pads + 0 footprint errors; rx_amp_sim 1 + 0 +
  0; txrx_dev 1 + 0 + 0. `XDG_CACHE_HOME=build/xdg-cache` remains enabled.
