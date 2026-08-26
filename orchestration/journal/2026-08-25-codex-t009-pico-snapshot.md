# 2026-08-25 — codex/terra-t009 — T-009 Pico 2 snapshot

## Delivered

- Added `firmware/pico-snapshot/`, a readable Pico SDK CMake project. The design
  separates PIO clock/sample programs, aligned PIO DMA words, ping-pong windows,
  compact 24-bit payload repacking, USB CDC, and packet framing from board GPIO
  choices. T-011 must supply the actual header pin map before that hardware glue can
  be enabled.
- The baseline is the ratified/provisional capture contract: 3.072 MHz, 12 shared
  data lines, 24 logical channels, with even/rising and odd/falling pair ordering.
- Proposed `SNP1` v1 to root for T-021 adoption: fixed 48-byte little-endian header
  with `SNP1`, version/length, flags, capture ID, first frame, clock, channels/lines,
  frame and payload counts, payload CRC-32, header CRC-32, reserved word; followed
  by three little-endian payload bytes per logical frame. T-021 owns canonical
  `docs/packet-format.md`, so this is deliberately a proposal rather than a parallel
  canonical document.
- Added a standard-library-only `uv` Python receiver/simulator. The simulator makes
  sigma-delta PDM for a known 28 kHz tone, preserves paired edge packing, validates
  a frame, decimates by 24, checks tone energy, and writes a PGM spectrogram.

## Measured host proof

```text
synthetic capture: 49152 frames, 147456 payload bytes
channel 0 28000 Hz tone/off-tone power ratio: 287.3 dB
valid SNP1 capture=7 frames=49152 clock=3072000 Hz
```

The C protocol/repack test, Python simulation/CRC test, byte-identical receiver
round-trip, Python compilation, and `git diff --check` passed.

## Throughput / boundary

- Raw contract rate: 9.216 MB/s / 73.728 Mb/s.
- Two windows of 16,384 frames need 224 KiB: 2 × (64 KiB aligned PIO DMA + 48 KiB
  compact CDC payload), leaving about 296 KiB of 520 KiB RP2350 SRAM.
- One 48 KiB compact window captures 5.333 ms. Full-Speed USB's theoretical 1.216
  MB/s drains it no faster than 40.4 ms (49.2 ms at a 1.0 MB/s empirical rate), so
  snapshot duty cycling—not streaming—is required.
- `PICO_SDK_PATH` is unset here. Therefore no Pico firmware configuration/build,
  PIO/DMA timing, GPIO waveform, USB behavior, or microphone capture was tested.
  The repository source tells a board-equipped agent exactly how to build it.
