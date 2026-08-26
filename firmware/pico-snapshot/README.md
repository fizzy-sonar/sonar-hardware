# Pico 2 snapshot capture (T-009)

This is an RP2350 Pico SDK snapshot-mode implementation and a host-only proof. It
does **not** claim that a Pico, microphones, DMA timing, or USB hardware has been
physically tested.

## Contract and transport

PDM electrical/channel semantics are normative in
[`docs/pdm-capture-contract.md`](../../docs/pdm-capture-contract.md). A payload
logical frame is 3 little-endian bytes. Its bit `CH00..CH23` is the matching channel
in that document: bit `2*i` is DATA line `i` sampled on rising clock; bit `2*i+1`
is sampled on falling clock. Thus the paired half-period offset is preserved.

SNP1 is the proposed shared snapshot framing (pending T-021 adoption): a 48-byte,
little-endian header followed by `3 * logical_frame_count` bytes of raw frames.

| Offset | Field |
|---:|---|
| 0 | `SNP1` magic (4 bytes) |
| 4 | version `u8` = 1 |
| 5 | header length `u8` = 48 |
| 6 | flags `u16` = 0 |
| 8 | capture ID `u32` |
| 12 | first logical-frame counter `u64` |
| 20 | PDM clock Hz `u32` |
| 24 | channels `u16` = 24; data lines `u16` = 12 |
| 28 | logical-frame count `u32`; payload bytes `u32` |
| 36 | IEEE CRC-32 payload `u32` |
| 40 | IEEE CRC-32 of header bytes 0–39 `u32`; reserved `u32` = 0 |

`host/receiver.py` refuses unknown/invalid framing and CRCs before writing output.

## RP2350 layout

`pio/pdm_capture.pio` specifies separate clock and edge-sampling PIO state machines.
The final board integration must set the actual generic-header GPIO base pins (T-011
owns that pin map), configure the two PIO programs and chained DMA descriptors, and
perform the required 2x12-bit PIO-word → 3-byte frame packing. `src/main.c` keeps
that hardware-dependent pin/DMA glue isolated while the packetization core is pure C.

Default SRAM buffering is two 16,384-frame windows: 5.333 ms each at 3.072 MHz.
Each needs 64 KiB aligned DMA storage (a 32-bit PIO word/frame) plus a 48 KiB packed
CDC buffer: 224 KiB total for both, leaving roughly 296 KiB of RP2350's 520 KiB for
SDK/USB/stacks. `dma_words`/`window` are the explicit Pico Plus 2 PSRAM adapter
boundary: an adapter may supply two contiguous, DMA-safe windows without changing
protocol, capture, or host code.

At the contract rate:

- Raw rate: `3,072,000 frames/s * 3 B = 9,216,000 B/s` (73.728 Mb/s).
- One 48 KiB packed window: 5.333 ms capture; PIO/DMA performs 3.072 M aligned
  32-bit writes/s (12.288 MB/s temporary SRAM bandwidth) before 24-bit repacking.
- USB Full-Speed bulk theoretical limit is 1.216 MB/s. A 48 KiB window therefore
  drains in **at least 40.4 ms** (plus CDC/protocol overhead), so it cannot stream.
  At an empirical 1.0 MB/s it drains in 49.2 ms; two 48 KiB windows support a
  capture burst but not continuous operation. A 520 KiB SRAM allocation holds
  56.4 ms raw (not 36 ms; the latter assumes 14.4 MB/s / 4.8 MHz).

## Run host proof

No Python packages are required; use the pinned project interpreter:

```sh
cd firmware/pico-snapshot
uv run python tests/test_sim.py
cc -std=c11 -Wall -Wextra -Werror -Iinclude src/snapshot_protocol.c tests/test_protocol.c -o build/test_protocol
./build/test_protocol
uv run python host/simulate.py
uv run python host/receiver.py build/synthetic.snp1 build/validated.snp1
```

The simulator produces 16 ms / 49,152 logical frames of synthetic 28 kHz PDM,
checks the CRC/framing, decimates channel 0 by 24 to 128 ksample/s, verifies tone
energy against 45 kHz, and writes `build/synthetic_spectrogram.pgm`.

For firmware build, set `PICO_SDK_PATH` to an RP2350-capable Pico SDK and run
`cmake -S . -B build/pico -DPICO_BOARD=pico2 && cmake --build build/pico`.
