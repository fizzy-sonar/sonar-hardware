# Sonar v1 — 60-second review brief

**2026-09-13 update:** this brief is historical. T-023 has repaired USB-induced
snapshot starvation and added actual-top tests (21 total checks pass). TX control,
host defects, Vivado and hardware proof remain open. Joshua has no hardware;
the current answer and buying sequence are in
[`docs/pre-hardware-readiness.md`](../../docs/pre-hardware-readiness.md).

## Bottom line

The project is ready for bounded integration engineering, not a hardware-readiness
claim. T-022 repaired both coupon variants: full DRC is 0 violations / 0
unconnected / 0 footprint errors, with independent pin, net, Gerber and negative
checks ([release evidence](../../coupons/mic-bakeoff/docs/T-022-release-verification.md)).
That does **not** approve purchase, acoustic performance, or a production microphone.

The FPGA suite's 17/17 PASS proves simulator behavior for component-level paths;
it does not validate a bitstream, timing closure, USB transport, microphone, TX,
or the whole commanded-echo path. The current `sonar_top` still has TX tied off,
and the integrated SRAM tap can stop when the USB stream stalls
([full review](REVIEW-2026-09-05.md)).

## Immediate question for Joshua

Which hardware is actually available now: Cmod A7, FT232H, Pico, an x86 Vivado
host, and any required bench instruments? Availability determines the shortest
executable path; no ownership is assumed here.

## Recommended first milestone

Use a repeatable, recorded echo from a known reflector at 1–3 m, with explicit
failure reporting and repeatability, as the first engineering target. This is a
recommendation for execution—not a request for approval or ratification—and is
an acquisition proof, not product performance, 10 m range, or a production
microphone release. No purchase decision is requested today; optional bench
access details can wait until they are relevant.

## Recommended next engineering sequence

1. **T-023 (top):** make snapshot capture independent of FT232H acceptance;
   add arm/fire/read/status, TX fault/wake handling, a deterministic TX/sample
   timestamp, and two-consecutive-capture top-level tests. Keep stream overflow
   explicit and recoverable ([ticket](../tickets/T-023-commanded-echo-capture.md)).
2. **T-024:** fix idle-read versus EOF, then implement bounded recording and
   stateful chunk-invariant DSP; measure ingest, processing, storage and combined
   memory/throughput separately ([ticket](../tickets/T-024-live-host-pipeline.md)).
3. **In parallel, T-020 + T-023/T-024:** run the Vivado host build early—XDC,
   synthesis, timing/CDC, and SRAM I/O constraints—while integration work
   proceeds. The simulator's deferred constraints are not a physical proof.
4. **T-025:** turn the first-echo proposal into an executable wiring/acquisition
   procedure, with a measured TX part/drive envelope and recorded raw evidence
   ([ticket](../tickets/T-025-first-echo-bench-plan.md)).
5. On suitable hardware, run one repeatable 1–3 m reflector demo; only then use
   calibrated coupon data for the microphone release gate. T-020's current
   timing margin is a calculation/model, not a placed-device proof
   ([T-020 notes](../../gateware/sim/README.md)).

## Five core risks

| Risk | Evidence status | Consequence / next proof |
|---|---|---|
| SRAM fallback dies after USB stall (FIFO fills in calculated ~5.33 ms at 3.072 MHz) | **Proven in simulation; calculated timing** | T-023 USB-independent capture and restart test. |
| No commanded, timestamped TX measurement (`start=0`) | **Proven by source inspection; unverified physically** | T-023 arm/fire/status and top-level timestamp test. |
| Host empty read is treated as EOF; DSP resets at block boundaries | **Proven by host probes** | T-024 idle/disconnect and chunk-invariance tests. |
| FPGA timing, CDC, Xilinx primitives, SRAM I/O and USB are unverified | **Unverified; simulator/model evidence only** | Vivado build, reports and hardware capture. |
| Acoustic mic/TX performance and first-echo range are unverified | **Unverified; link-budget numbers are calculations** | T-025 bench measurement, then T-016 calibrated bake-off. |

The current small windows are calculations, not product claims: the Pico default
window is 5.333 ms (~0.915 m round-trip range from a TX-aligned start), and the
Cmod SRAM window is 56.89 ms (~9.76 m under the same assumptions). A first-echo
demo is not a production microphone release.

## Do not ask Joshua to decide yet

Do not ask him to choose a new FPGA architecture, ratify a replacement packet
format, accept 17/17 as whole-path validation, approve MA40S4S at 12 V, or sign
off the microphone MPN/production board. Those are engineering/proof obligations
owned by T-023/T-024/T-025 and later CP-C/CP-BM gates; Joshua's input is needed
only for actual hardware/access, purchase authority, and ratification gates.
