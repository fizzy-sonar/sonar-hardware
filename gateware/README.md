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
- the 512 KiB external-SRAM snapshot fallback (D012): two back-to-back captures
  and a stream-stopped timeout capture drained over UART byte- and CRC-exact
  against a timing-enforcing IS61WV5128BLL model, plus one full 512 KiB window
  (174,762 frames = 524,286 payload bytes) proven bit-exact;
- four behavioral `sonar_top` cases at 3.072/4.8 MHz, with absent or blocked USB,
  delayed triggers, consecutive snapshots, SRAM/UART counter+CRC checks,
  reconnect/reset and TX idle; the FIFO remains at production depth;
- exact 1.536/3.072/4.8 MHz divider arithmetic and the 50 ms standard-mode /
  clock-off / 10 ms ultrasonic startup sequence;
- TX reset/idle safety, rejected/crossed limit violations, complementary drive,
  and a bounded fixed-point NCO/PWM chirp ramp; and
- an exact `sonar_top` <-> XDC port bijection (`sim/check_ports.py`): every
  active `get_ports` name in `constraints/sonar_cmod_a7.xdc` matches a real
  port (bit-exact on buses), and every top-level port is constrained; the
  commented DNP RMII block is excluded.

The final test also elaborates the complete `sonar_top` and each `XILINX` RTL
branch against functional 7-series primitive models. Behavioral tests use those
models too; they do not replace UNISIM/xsim or placed Vivado timing checks.
The suite has 21 checks as of T-023, 2026-09-13. See
[`docs/pre-hardware-readiness.md`](../docs/pre-hardware-readiness.md) for the
remaining commanded-TX, host, implementation and physical gates. SRAM taps are
independent of USB acceptance; UART drain is currently about 46 s/full snapshot.

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

## SRAM snapshot fallback (D012)

`rtl/sram_snapshot.sv` implements the day-one fallback capture path: on a
snapshot trigger (`btn[0]` in `sonar_top`) it streams accepted 3-byte PDM frames
from the `pdm_stream_core` tap through a 16-entry Gray-pointer CDC FIFO into the
Cmod's on-module ISSI IS61WV5128BLL-10BLI (512K x 8), then drains the window
over the on-module FT2232HQ USB-UART bridge (`uart_rxd_out`, 115200 8-N-1) with
the exact 48-byte `SNP1` header and both CRC-32 values. The window is
`SNAPSHOT_FRAMES = 174762` frames = 524,286 bytes (bytes 0..524,285 of the
512 KiB device). The controller runs on a 48 MHz MMCM output and writes one
byte per three clocks (16 MB/s > the 14.4 MB/s ICS worst case) using a
SETUP/PULSE/HOLD microcycle that gives >= 2.6x margin on every cited ISSI -8 ns
grade timing parameter; `sim/is61wv5128bll_model.sv` enforces tWC/tPWE/tSD and
models tAA in the testbench. A stream stop (or CDC overrun, reported on
`capture_error`) ends the capture early and the header honestly reports the
frames actually written.

## What is intentionally still open

This is a simulator milestone, not a bitstream or hardware demonstration:

- The real XDC (`constraints/sonar_cmod_a7.xdc`, T-011 live-verified + the
  verbatim Digilent SRAM/UART MANUAL APPEND section) and `sonar_top` are now
  reconciled: the port list is an exact bijection with the active `get_ports`
  (28 ports / 73 bits; renamed to the pinmap net names, TX mapped per
  `orchestration/tx-limits.md` — `tx_en`=`tx_a`/IN1, `tx_ph`=`tx_b`/IN2,
  `tx_pmode`=1 IN1/IN2 mode, `tx_nsleep`=`tx_active`, `tx_nfault`->`led0_r`),
  gated by `sim/check_ports.py` in `make test`. The old simulator-only
  scaffolding ports (reset/mic_power_good/wake_request/tx_start/.../
  ft_siwu_n) had no pins in the pinmap and were replaced by documented
  internal tie-offs (power-on reset + btn[1] manual reset; TX permanently
  idle until a control plane exists).
- The Vivado host from T-007 is not purchased/selected, so the MMCM/derived-clock
  scaffold (including the new 48 MHz SRAM clock), Xilinx IDDR polarity, BRAM
  inference/utilization, FT245 I/O timing, SRAM set_output_delay budgeting, CDC
  reports, setup/hold constraints on both PDM edges, timing closure, and
  bitstream generation are unverified. The ISSI timing constants cited in
  `rtl/sram_snapshot.sv` and enforced in the model are the standard -8/-10
  grade values; `sim/README.md` carries the per-phase timing-margin analysis
  (>= 2.1x worst case) and the residual "confirm against ISSI PDF" item is a
  CP-C checklist line in the ticket Log.
- `uart_snapshot.sv` remains as the bounded inferred-RAM snapshot proof;
  `sram_snapshot.sv` is the hardware window path. The UART snapshot has not been
  demonstrated on hardware (needs the bitstream + a Cmod).
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
