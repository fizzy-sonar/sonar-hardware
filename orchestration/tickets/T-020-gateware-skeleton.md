---
id: T-020
title: Vivado gateware — PDM capture + FT232H streaming (Cmod A7-35T)
status: ready
phase: P5
tier: top        # novel HDL + Vivado constraints + testbenches
priority: 2
assignee:
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Vivado project for the Cmod A7-35T in `gateware/`:
1. Parameterized PDM clock generation + the T-008 12-line/24-channel IDDR sampler.
   Default to provisional SPH at 3.072 MHz and test the ICS 4.8 MHz alternate; T-016
   freezes the production default.
2. Word packer → ~64 KB BRAM elastic FIFO → FT245 synchronous-FIFO interface to the
   FT232H (~40 MB/s; raw stream is 9–14.4 MB/s so no in-fabric DSP — D006).
3. Day-one fallback: UART snapshot mode over the Cmod's own USB (on-module 512 KB
   SRAM window) so bring-up starts before the FT232H is wired.
4. TX chirp generator (NCO → PWM out to DRV8876 lines).
5. Everything scripted: Tcl-driven project generation + batch builds (no GUI-only
   state in the repo); XDC generated from `orchestration/pinmap.md` when it exists
   (placeholder pins until then).
6. Testbenches: Verilator or cocotb+xsim feeding synthetic PDM (sigma-delta model of
   a known tone); FT245 bus-functional model for the FIFO interface.

## Context
D012 (ratified). PREREQUISITE: x86 Vivado host (T-007 item 7) for synthesis; the
testbench layer must run on any machine (Verilator/pytest) so agent work is NOT
blocked on the host. Learning goal: keep the design readable — Joshua reads this
to learn Vivado; comment constraints and CDC decisions.

`docs/pdm-capture-contract.md` v1 is a provisional SPH electrical/sample baseline,
not an MPN release. T-016 may select ICS and require the documented 4.8 MHz /
14.4 MB/s default. Parameterization lets testbench work proceed without prejudging
that human-gated result.

## Definition of Done
`gateware/README.md` reproduces builds from a clean clone; TB proves sampler +
packer + FIFO against synthetic PDM at both 3.072 and 4.8 MHz, including edge/channel
order and 73.728/115.2 Mb/s payload calculations; batch bitstream build succeeds on
the Vivado host; UART snapshot mode demonstrated in sim.

## Verification
`make test` runs the TB suite; build log + utilization/timing summary in the Log.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 claude (fable): rewritten for ratified D012 (was LiteX/ECP5/TDM/UDP).
- 2026-08-25 codex/sol-t008: independent T-008 review made the clock/rate
  parameterization and dual-rate test explicit so TB work can start before T-016's
  physical MPN release without freezing the provisional SPH default.
