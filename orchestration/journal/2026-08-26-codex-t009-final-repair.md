# 2026-08-26 — codex/t009-final-repair — T-009 final repair

## Scope and correction

Independently audited the completed T-009 branch against D011/D012 and the PDM
capture contract. This entry supersedes the 2026-08-25 journal's architecture
description: the implementation is not separate clock/sample state machines,
chained DMA, or continuous ping-pong. It is one finite DDR side-set state machine,
one discard DMA channel, and two capture buffers alternated between commands.

No main-branch, KiCad, backup, purchase, remote, or physical-hardware action was
taken. Joshua's dirty `sonar-v1-pcb/sonar.kicad_pro` was not touched.

## Firmware repair

- Removed mic startup before the command loop. Each accepted `C` alone performs a
  finite 50 ms standard drain, a finite 10 ms ultrasonic drain, and one capture.
- Replaced the open-ended six-cycle PIO loop with an explicitly counted ten-cycle
  loop. High and low are five cycles each; rising and falling data are sampled two
  cycles after their corresponding edge. After the requested frame count it wraps
  to `PULL` and stalls low, preventing unowned post-DMA frames.
- Armed both capture and discard DMA before enabling the SM. The capture IRQ clears
  DMA status, disables the SM, drives clock low through a PIO masked operation, and
  publishes the completed buffer. An explicit active flag prevents command re-arm.
- Built each DMA channel config from that channel's own SDK default. Reusing the
  capture channel's default for discard had silently encoded `CHAIN_TO=capture`,
  so the old settling completion could launch an unarmed capture DMA operation.
- Quantized the live system clock to the PIO 16.8 divider. At 150 MHz, standard is
  `9+196/256` and ultrasonic is `4+226/256`, both exact/0 ppm. Runtime rejects more
  than 400 ppm and SNP1 reports actual rather than requested Hz.
- Defined `first_logical_frame` only in ultrasonic-clock periods. Ultrasonic settle
  and captured frames advance it; standard startup and stopped-low pauses do not.
- Added independent GP2 clock / GP3..14 bench defaults, compile-time range/overlap
  failures, and explicit data GPIO input directions. T-011 still owns board pins.
- Removed Pico stdio USB ownership. Direct TinyUSB now supplies its own config,
  descriptors, board/stack initialization, task loop, and host-tested CDC writer
  for backpressure, partial writes, disconnect, and invalid counts.
- Made C and Python packet validation agree on version, zero flags/reserved,
  dimensions, lengths, header CRC, and payload CRC. Corrected the PIO-word bit-map
  comment and reformatted C/Python for reviewability.

## Verification and boundaries

Warning-clean host C tests passed for divider math/error bounds, all 24 DDR channel
positions, SNP1 schema/CRC/unknown flags, and CDC backpressure behavior. Python
source-contract tests passed for PIO cycles, pin compile failures, DMA-before-SM,
IRQ stop/completion, per-command drains, PIO-low behavior, and TinyUSB ownership.
The deterministic 49,152-frame synthetic capture recovered the 28 kHz tone at
287.3 dB over the 45 kHz probe and the receiver output matched byte-for-byte. Ruff,
Python compilation, and diff checks passed.

The repository KiCad harness reproduced its known sandbox-only DRC exit 134, then
passed on the approved unsandboxed rerun: all ERC/DRC commands returned their
accepted baseline exit 5 and every netlist/PDF/SVG/BOM export returned 0. No KiCad
source was changed.

`PICO_SDK_PATH` remains unset; CMake produced the repository's explicit missing-SDK
error. Therefore PIO assembly, RP2350 compilation/linking, Pico USB enumeration,
GPIO clock/duty/edge waveforms, DMA IRQ timing, microphone startup/capture, PSRAM,
and measured Full-Speed CDC throughput remain physical integration blockers, not
validated results.
