---
id: T-009
title: Pico 2 snapshot-mode capture firmware (v0)
status: ready
phase: P5
tier: mid        # RP2350 PIO/DMA firmware + host receiver
priority: 1
assignee:
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
RP2350 firmware: PIO clocks the mics (3.072–4.8 MHz per T-008 contract), samples the
PDM data lines to RAM via DMA (SRAM baseline; PSRAM if Pico Plus 2), triggers a
capture window on command (later: synced to TX ping), then ships the raw buffer to
the laptop over USB CDC. Host-side: tiny Python receiver that stores raw windows in
the same file format T-021 consumes. Works first with 1–2 mic breakout boards, then
the real array via the board's PDM header.

## Context
D012 ladder rung 1 — guarantees echo data exists regardless of FPGA progress, and
exercises the exact mic clocking + Python decimation the Cmod path will use.
Interface contract: `docs/pdm-capture-contract.md` (T-008/T-020 shared).

## Definition of Done
Firmware + receiver in `firmware/pico-snapshot/`; loopback-tested in sim or with a
GPIO-generated synthetic PDM pattern; capture → Python decimation → spectrogram of a
known tone demonstrated (hardware step waits on T-007 purchases).

## Verification
Synthetic-pattern capture matches expected bitstream exactly; throughput math
(window length vs RAM, USB drain time) measured and logged.

## Log
- 2026-08-25 claude (fable): created per ratified D012.
