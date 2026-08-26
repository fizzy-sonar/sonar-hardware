# Sonar gateware skeleton (T-020 simulator milestone)

This directory is a readable, simulator-first raw PDM capture path for the Cmod
A7-35T. It deliberately keeps all receive DSP on the host:

```text
12 paired PDM wires -> DDR sampler -> 24-bit frames -> 64 KiB async FIFO
                    -> three bytes/frame -> FT245 synchronous FIFO
```

The default is the provisional SPH baseline at 3.072 MHz. The same tests compile
at 4.8 MHz for the ICS alternative; this parameterization does not release either
microphone or change T-016's physical gate.

## Run the portable tests

Icarus Verilog 13 or newer and Make are sufficient; Vivado is not needed:

```sh
cd gateware
make test
```

The suite checks:

- rising/even and falling/odd channel mapping with counter patterns and a
  deterministic first-order sigma-delta sine stimulus at 3.072 and 4.8 MHz;
- exact 73.728 and 115.2 Mb/s payload calculations;
- asynchronous FIFO order, three-byte packing, and an FT245 BFM that asserts
  backpressure;
- one exact `SNR1` header per explicit capture, including all little-endian
  metadata fields and incrementing capture IDs;
- end-to-end byte order and lossless delivery through a long opening stall plus
  pseudo-random `TXE#` backpressure;
- sticky overflow-and-stop behavior, exact accepted-prefix draining, and a clean
  reset/new-capture boundary when the 64 KiB elastic buffer cannot drain;
- the 48-byte `SNP1` UART snapshot format, including both IEEE CRC-32 values;
- exact 1.536/3.072/4.8 MHz divider arithmetic and the 50 ms standard-mode /
  clock-off / 10 ms ultrasonic startup sequence; and
- TX reset/idle safety, rejected/crossed limit violations, complementary drive,
  and a bounded fixed-point NCO/PWM chirp ramp.

The final test also elaborates the complete `sonar_top` and each `XILINX` RTL
branch against compile-only 7-series primitive stubs. Those stubs catch portable
interface/elaboration mistakes; they intentionally do not model primitive timing
or replace UNISIM/xsim and placed Vivado checks.

`rtl/pdm_ddr_sampler.sv` uses a portable behavioral edge model unless `XILINX` is
defined. The Xilinx branch instantiates `IDDR` in `SAME_EDGE_PIPELINED` mode and
requests the frame ordering defined by `docs/pdm-capture-contract.md`.

## Stream format

[`STREAM_FORMAT.md`](STREAM_FORMAT.md) defines the proposed continuous `SNR1`
header, backpressure/overflow behavior, and its exact relationship to the shared
bounded `SNP1` snapshot. Payload bytes are identical in both transports.
`capture_enable` low is the explicit abort/fresh-stream boundary and must span at
least three rising edges in both clock domains. The normal startup controller
holds it low for milliseconds. `capture_overflow` and `capture_stopped` remain
sticky through the low interval and clear only when the next capture starts.

## Vivado project generation

Vivado is not available on macOS. On an x86 Linux/Windows Vivado host:

```sh
cd gateware
vivado -mode batch -source vivado/create_project.tcl
vivado -mode batch -source vivado/build_bitstream.tcl
```

`create_project.tcl` creates a Cmod A7-35T project from repo sources. It uses the
timing-only placeholder XDC when no real pin map exists. `build_bitstream.tcl`
refuses to run until T-011 provides `constraints/sonar_cmod_a7.xdc`; there are no
fabricated `PACKAGE_PIN` values in this branch.

## What is intentionally still open

This is a simulator milestone, not a bitstream or hardware demonstration:

- T-011 must publish the generic-header/Cmod/FT232H pin map, including a
  clock-capable `PDM_CLK_FB`, before the real XDC exists.
- The Vivado host from T-007 is not purchased/selected, so the MMCM/derived-clock
  scaffold, Xilinx IDDR polarity, BRAM inference/utilization, FT245 I/O timing,
  CDC reports, setup/hold constraints on both PDM edges, timing closure, and
  bitstream generation are unverified.
- `uart_snapshot.sv` proves a bounded inferred-RAM snapshot and exact wire format.
  A controller for the Cmod's 512 KiB external SRAM and its board-level UART path
  remains before claiming the full fallback window on hardware.
- TX defaults are conservative generic ceilings only. T-013 must replace them
  with the chosen transducer/DRV8876 voltage, duty, and duration limits before TX
  hardware is enabled.
- The TX chirp control is simulator-only scaffolding until a real control plane
  exists; its generic limits do not release a transducer or hardware drive level.

The portable primary capture path contains no CIC, FIR, beamforming, calibration,
or matched filtering.

For TX simulation, the 24-bit NCO increment is
`round(f_hz * 2^24 / 12_000_000)`. `tx_phase_increment_delta_q8` changes that
increment once per 12 MHz clock in signed Q24.8 units; use zero for a tone or
approximately `round((end_increment - start_increment) * 256 / (cycles - 1))`
for a linear chirp. The runtime limiter stops a ramp before its increment reaches
zero or exceeds the configured ceiling.
