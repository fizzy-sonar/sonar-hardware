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
updated: 2026-08-26
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
- 2026-08-25 codex/terra-t009: initial implementation and host proof. Its claims
  of separate clock/sample state machines and ping-pong/chained behavior were
  inaccurate and are superseded by the 2026-08-26 repair below.
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
- 2026-08-26 codex/t009-final-repair: independently audited and repaired the
  firmware-critical path. The actual design is one finite side-set PIO SM with two
  DDR reads and ten cycles/frame, exact one-shot frame counts, a discard DMA sink,
  and two capture buffers alternated between commands. It is not two SMs, chained
  DMA, continuous ping-pong, or streaming. Every accepted `C` runs 50 ms standard
  mode, 10 ms ultrasonic settling, then one capture; there is no pre-command mic
  startup. DMA is live before the SM, the DMA IRQ stops the SM and holds clock low
  through PIO, and another command cannot re-arm an active or unsent capture.
  Capture and discard channels now each start from their own SDK default config;
  this prevents the discard channel from inheriting `CHAIN_TO=capture` and
  accidentally launching an unarmed capture at the end of a settling drain.
- 2026-08-26 codex/t009-final-repair: direct TinyUSB now has exclusive CDC
  ownership (`board_init`, `tusb_init`, descriptors/config, `tud_task`); Pico stdio
  USB and `stdio_init_all` are absent. The host-tested CDC loop handles zero TX
  space, partial writes, disconnect, and invalid writer counts. C and Python SNP1
  readers agree on zero flags/reserved, lengths, payload CRC, and header CRC.
- 2026-08-26 codex/t009-final-repair: default Pico 2 `clk_sys=150 MHz` gives exact
  16.8 dividers `9+196/256` (1.536 MHz) and `4+226/256` (3.072 MHz), both 0 ppm.
  Firmware derives the live actual rate, rejects error beyond 400 ppm, and reports
  actual Hz. `first_logical_frame` is exclusively an ultrasonic-period counter:
  settling and captures advance it; standard-mode drains and stopped-low pauses do
  not. Independent compile-time GPIO guards and explicit data-input direction were
  added; GP2/GP3..14 remain bench defaults, not T-011's board pin release.
- 2026-08-26 codex/t009-final-repair verification: both warning-clean C test
  binaries passed; source-contract and Python simulation tests passed; the 49,152-
  frame synthetic capture/receiver round trip was byte-identical; recovered 28 kHz
  tone/off-tone power was 287.3 dB; Ruff check/format, Python compilation, and
  `git diff --check` passed. CMake stopped as expected with the explicit
  `PICO_SDK_PATH` error because no SDK is installed. No PIO assembly, ARM build,
  Pico enumeration, waveform, IRQ timing, physical mic, or measured USB-throughput
  validation is claimed.
- 2026-08-26 codex/t009-final-repair: repository `scripts/check.sh` first reproduced
  the known sandbox-only macOS DRC aborts (exit 134), then passed fully in the
  approved unsandboxed run: ERC/DRC baseline exits were 5 and every export exited
  0. No KiCad source was edited.
