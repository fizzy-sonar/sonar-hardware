---
id: T-027
title: DE10-Lite clock and capture bench port
status: blocked
phase: P5
tier: top
priority: 1
assignee:
depends_on: []
needs_human: false
created: 2026-09-13
updated: 2026-09-14
---

## Goal
If D014 is adopted, use Joshua's owned DE10-Lite to prove the digital capture
path before another FPGA purchase. Blocked on proposed D014; do not implement
a replacement for ratified D012 without Joshua adopting that change.

**Current direction, 2026-09-14:** Joshua retains his Vivado preference. D014
is not adopted; this port is not selected and must not start. Use the x86
Vivado host path in `docs/vivado-validation.md` for the next implementation work.

## Definition of Done
- Exact board revision, manufacturer QSF/schematic/pin audit, clock-capable PDM
  feedback and FT CLKOUT, I/O voltages, adapter and power plan recorded.
- Quartus target and MAX 10 DDR/clock/reset wrappers; actual oscillator-based
  clock plan meets mic mode/duty/tolerance bounds. No simulated Xilinx model
  used as a synthesis fallback. Current Cmod target preserved.
- Small M9K-based diagnostic capture/readback first; no Cmod SRAM controller
  reused against SDRAM. Memory depth and window budget explicit.
- Counter-pattern tests and Quartus fit/timing/CDC/M9K inference reports;
  concrete programming/readback instructions and a physical evidence checklist.
- Share T-023 command/metadata and T-024 host contracts. No automatic acoustic,
  continuous USB, SDRAM or 1 Hz claim from a short diagnostic capture.

## Verification
Existing portable regressions plus target-specific simulation, real Quartus
reports and counter-checked physical readback. Distinguish completed simulation
and implementation work from remaining physical acceptance.

## Log
- 2026-09-13 codex/T-023: created from Joshua's newly reported DE10-Lite
  ownership. Primary-source feasibility and port boundaries in D014. No port
  started; no additional FPGA purchase recommended while this is evaluated.
