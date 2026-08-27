---
id: T-017
title: Zener deep port — registry/datasheet modules, real pcb build
status: in-progress
phase: P1
tier: mid        # tool spike with network; scripting + datasheet transcription
priority: 4
assignee: codex/terra-t017
depends_on: [T-005]
needs_human: false
created: 2026-08-27
updated: 2026-08-27
---
## Goal
T-005's NO-GO was driven by an offline sandbox (registry unreachable, ICs
unwritable). Joshua has now explicitly authorized pulling from the pcb package
registry AND hand-defining modules from datasheets. Give diodeinc/pcb (Zener) a
fair, full evaluation: port real Sonar v1 circuit blocks to `.zen` and make
`pcb build` actually succeed.

## Context
- T-005 spike artifacts: `spikes/eda-zener/` (REPORT.md, hand-port/, imports).
- Port targets (pick 2, in this order): (a) the RX preamp channel hand-port —
  complete it by defining `quad_opamp.zen` from the datasheet; (b) the T-012
  power supply sheet (`sonar-v1-pcb/power_supply.kicad_sch`, AP63301 buck +
  mic-rail filter). Optional stretch: TX h-bridge (DRV8876).
- Datasheets: `sonar-v1-pcb/data_sheets/`, manufacturer sites (network OK).
- `pcb` CLI is installed at ~/.local/bin/pcb on this host. Registry access is
  authorized by Joshua (2026-08-27). Network use is limited to package/datasheet
  fetches — no accounts, no purchases.
- D008 (KiCad remains the v1 EDA) is NOT being overturned; this spike informs v2.

## Definition of Done
`spikes/eda-zener/deep-port/` contains the ported `.zen` blocks; `pcb build`
succeeds and produces netlist + BOM; a comparison notes parity/gaps vs the KiCad
originals (pin counts, net spot-check); REPORT.md gains a "Deep port (T-017)"
verdict section with GO / NO-GO / GO-WITH-CONDITIONS and the evidence.

## Verification
Real `pcb build` output pasted in the ticket Log; BOM/netlist artifacts exist.

## Log
- 2026-08-27 claude/orchestrator: created at Joshua's direction ("push it
  further, port it, ok to pull from registry or define from datasheet").
