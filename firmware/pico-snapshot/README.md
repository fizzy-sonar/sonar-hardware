# Pico 2 snapshot capture (T-009)

This is an RP2350 Pico SDK snapshot implementation plus host-only verification. It
does **not** claim that a Pico, microphones, PIO/DMA timing, or USB hardware has
been physically tested.

## Contract and transport

PDM electrical/channel semantics are normative in
[`docs/pdm-capture-contract.md`](../../docs/pdm-capture-contract.md). Each payload
frame is three little-endian bytes. Bit `2*i` is DATA line `i` sampled on the
rising clock for CH-even; bit `2*i+1` is that line sampled on the falling clock for
CH-odd. The paired half-period offset is preserved.

SNP1 is the proposed shared snapshot framing, pending T-021 adoption: a 48-byte
little-endian header followed by `3 * logical_frame_count` bytes.

| Offset | Field |
|---:|---|
| 0 | `SNP1` magic (4 bytes) |
| 4 | version `u8` = 1 |
| 5 | header length `u8` = 48 |
| 6 | flags `u16` = 0 |
| 8 | capture ID `u32` |
| 12 | first ultrasonic logical-frame counter `u64` |
| 20 | actual quantized PDM clock Hz `u32` |
| 24 | channels `u16` = 24; data lines `u16` = 12 |
| 28 | logical-frame count `u32`; payload bytes `u32` |
| 36 | IEEE CRC-32 payload `u32` |
| 40 | IEEE CRC-32 of header bytes 0–39 `u32`; reserved `u32` = 0 |

Flags and the reserved word must be zero. `host/receiver.py` refuses unknown or
invalid framing, lengths, and CRCs before writing output.

`first_logical_frame` counts only complete ultrasonic clock periods emitted by the
one-shot PIO program. The 1.536 MHz standard-mode startup drain is not in that
coordinate system. The 10 ms ultrasonic settling drain does advance it. Every
stopped-low interval is a pause and advances it by zero. The first capture after
reset therefore starts at frame 30,720; later captures are monotonic but not
wall-clock-continuous across pauses.

## RP2350 capture design

`pio/pdm_capture.pio` uses one state machine: side-set generates the PDM clock and
two `IN PINS, 12` instructions sample rising/SELECT-low and falling/SELECT-high
data. Each half-period is five SM cycles and each logical frame is ten. A `PULL`
count makes every standard drain, ultrasonic drain, and capture finite. After
exactly that many frames, the program wraps to `PULL` and stalls with side-set low.
DMA is armed before the SM is enabled. The capture DMA IRQ disables the SM and
uses a PIO masked-pin operation to hold the clock low.

The 150 MHz Pico 2 default system clock represents both requested PDM rates exactly
with the RP2350 PIO 16.8 divider: standard mode is `9 + 196/256` and ultrasonic
mode is `4 + 226/256`, both 0 ppm quantization error. Firmware derives the divider
from live `clk_sys`, rejects error beyond 400 ppm, and puts the actual ultrasonic
rate rounded to the nearest hertz in SNP1 instead of assuming the request was
achieved.

Two RAM buffers alternate between independent one-shot captures. This is not DMA
chaining or a concurrent ping-pong stream. After an IRQ, the completed buffer is
repacked and fully sent over CDC before another `C` command can start the next
standard → ultrasonic-settle → capture sequence. A separate discard DMA channel
writes settling data to one sink and is also armed before its finite PIO run.

Default SRAM allocation is two 16,384-frame windows: 5.333 ms each at 3.072 MHz.
Each needs 64 KiB aligned DMA storage plus a 48 KiB packed CDC buffer: 224 KiB
total, leaving roughly 296 KiB of RP2350's 520 KiB for SDK, USB, and stacks. The
static arrays mark the future Pico Plus 2 PSRAM adapter boundary, but no PSRAM
adapter is implemented. Any such adapter must provide contiguous DMA-safe storage
without changing protocol semantics.

The compile-time bench defaults are `PDM_CLK_GPIO=2` and contiguous data
`PDM_DATA_GPIO_BASE=3` (`GP3..GP14`). Each macro is independently overrideable;
compile-time guards reject out-of-range or overlapping assignments. T-011 owns the
real generic-header pin map, so these defaults are not a board pin release.

USB CDC is owned directly by TinyUSB. The project supplies a single-CDC
`tusb_config.h`, descriptors, `board_init()`/`tusb_init()`, and continuous
`tud_task()` service; Pico SDK USB stdio is not enabled. The write loop services
TinyUSB under backpressure, accepts partial writes, and aborts if CDC disconnects.

At the contract rate:

- Raw payload is 9.216 MB/s / 73.728 Mb/s.
- One 48 KiB packed window takes 5.333 ms to capture.
- USB Full-Speed bulk's theoretical payload ceiling is 1.216 MB/s, so that window
  takes at least 40.4 ms to drain, plus CDC/protocol overhead. Snapshot duty
  cycling is mandatory; this firmware does not stream continuously.

## Run host proof

No Python packages are required. Keep `uv` cache local in restricted environments:

```sh
cd firmware/pico-snapshot
mkdir -p build
UV_CACHE_DIR=build/uv-cache uv run python tests/test_firmware_contract.py
UV_CACHE_DIR=build/uv-cache uv run python tests/test_sim.py
cc -std=c11 -Wall -Wextra -Werror -Iinclude src/capture_core.c src/snapshot_protocol.c src/pdm_dma.c tests/test_protocol.c -o build/test_protocol
./build/test_protocol
cc -std=c11 -Wall -Wextra -Werror -Iinclude src/cdc_transport.c tests/test_cdc_transport.c -o build/test_cdc_transport
./build/test_cdc_transport
UV_CACHE_DIR=build/uv-cache uv run python host/simulate.py
UV_CACHE_DIR=build/uv-cache uv run python host/receiver.py build/synthetic.snp1 build/validated.snp1
```

The source-contract check covers PIO timing, DMA-before-SM order, DMA IRQ stop and
completion handoff, direct TinyUSB ownership, per-command startup, both drains,
PIO-safe low operation, and compile-time pin failures. C tests cover divider
values/error bounds, all 24 edge/channel positions, schema/CRC/unknown flags, and
CDC zero-space/partial-write/disconnect behavior. The simulator produces 16 ms /
49,152 frames of synthetic 28 kHz PDM, decimates channel 0 by 24 to 128 ksample/s,
checks tone recovery, and writes `build/synthetic_spectrogram.pgm`.

For a firmware build, set `PICO_SDK_PATH` to an RP2350-capable Pico SDK and run
`cmake -S . -B build/pico -DPICO_BOARD=pico2 && cmake --build build/pico`.
Override the bench pins only after T-011 publishes the header map. The current
agent environment has no Pico SDK or Pico 2, so PIO assembly, ARM compilation and
linking, enumeration, waveforms, IRQ timing, microphone startup, and measured USB
throughput remain unvalidated.
