---
id: T-009
title: Pico 2 snapshot-mode capture firmware (v0)
status: done
phase: P5
tier: mid        # RP2350 PIO/DMA firmware + host receiver
priority: 1
assignee: codex/terra-t009
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
- 2026-08-25 codex/terra-t009: completed the sim-allowed DoD on
  `agent/T-009-pico-snapshot-fw`. Added `firmware/pico-snapshot/`: Pico SDK CMake
  source with separate PIO clock/sample definitions, ping-pong DMA-window design,
  SRAM-safe default (two 16,384-frame capture windows; 224 KiB temporary+packed
  buffer allocation), CDC framing, and an explicit Pico Plus 2 PSRAM boundary.
  Actual header GPIO assignment and final PIO/DMA configuration remain T-011
  hardware integration work; no hardware result is claimed.
- 2026-08-25 codex/terra-t009: proposed the shared little-endian `SNP1` v1 frame
  to T-021/root: 48-byte magic/version/header-length/flags/capture-ID/frame-counter/
  clock/channel+line count/frame+payload lengths/payload CRC-32/header CRC-32 header,
  followed by lossless 3-byte logical PDM frames. CH00..CH23 map directly to the
  contract's rising/falling paired-edge order. T-021 owns canonical
  `docs/packet-format.md` and may ratify or amend this proposal.
- 2026-08-25 codex/terra-t009: host verification passed with no third-party Python
  dependencies (`uv` project): C protocol/repacking test; Python framing/CRC test;
  deterministic 49,152-frame (16.000 ms, 147,456-byte) synthetic GPIO-independent
  28 kHz PDM capture; decimation by 24 to 128 ksample/s; 28 kHz versus 45 kHz
  power ratio 287.3 dB; and CDC receiver validation/byte-identical saved output.
  `git diff --check` passed. `PICO_SDK_PATH` is unset in this environment, therefore
  firmware CMake configuration/build could not be run; the source includes an
  offline import file and states the exact SDK build command. No physical hardware,
  PIO/DMA timing, USB throughput, or microphone capture has been validated.
