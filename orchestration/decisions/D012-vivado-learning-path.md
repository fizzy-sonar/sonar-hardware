---
id: D012
title: "FPGA platform: Vivado-class board for learning; array board FPGA-agnostic"
status: ratified
date: 2026-08-25
author: claude (fable), from Joshua's stated learning goal
supersedes: D004 (if ratified)
---
_Ratified 2026-08-25: Joshua, "ok. lets go with that" (blanket go-ahead for the standing defaults + the D012 platform ladder)._

## Decision
Joshua wants industry-standard FPGA tooling experience. Proposal:
1. The sonar board exposes RX/TX on a **generic pin header** (~16–20 slow signals:
   ~12 PDM data @ 4.8 MHz, 2–4 clocks, TX control, power/GND) instead of a SODIMM
   socket — D011 made this possible; the FPGA no longer needs to live on the board.
2. Primary dev platform (2026-08-25 rev 2, Joshua's find): **Digilent Cmod A7-35T**
   (~$100 — verify; official, in production, DIP-48 form → sockets directly ON the
   sonar board) + **FT232H breakout** (~$15, official FTDI) in synchronous-FIFO mode:
   ~40 MB/s USB 2.0 HS egress — streams RAW 115 Mb/s PDM continuously, all DSP on
   the laptop, no CIC and no Ethernet stack in gateware (~50 lines of HDL for the
   FIFO). Progression: day-one UART snapshot mode (on-module 512 KB SRAM ≈ 50 ms /
   8 m windows), then FT232H streaming. Same Vivado/XDC/ILA/timing-closure learning
   as an Arty; defers only DDR(MIG) + Ethernet-MAC IP experience — the two biggest
   beginner time sinks. Cmod S7 rejected in favor of A7 (same tools, less BRAM,
   smaller tutorial base). Arty A7-100T ($249) demoted to alternative — choose it
   only if MIG/Ethernet IP learning is wanted NOW. PYNQ-Z2 spotty stock; QMTech/
   EBAZ4205 unofficial.
3. **Platform ladder (2026-08-25 rev, addressing platform-risk fear)**: buy BOTH
   a Pico 2 (~$5, snapshot-mode v0 — guarantees the project is never blocked and
   validates mics/clock-tree/Python pipeline at 1–2 Hz) AND the Arty A7-100T
   (official, supported, continuous streaming, the Vivado learning platform).
   The Colorlight i5 is DROPPED from the plan: industrial-grade but zero official
   support (community-reverse-engineered pinout, gray-market supply, silent board
   revisions) — its $50 price no longer justifies being the one unsupported
   component in the system. All platforms attach via the same generic PDM header,
   so this choice never touches the PCB.

## Amendment 2026-08-25: RP2350 snapshot mode (optional v0)
RP2350 evaluated at Joshua's suggestion. Verdict: cannot stream (USB is Full-Speed,
12 Mb/s vs 19–74 Mb/s needed; no Ethernet) and 24-ch software CIC is hero-code —
NOT a replacement for the FPGA. BUT pulsed operation fits a snapshot mode: PIO+DMA
captures the raw 115 Mb/s PDM burst to RAM (520 KB SRAM = 36 ms = 6 m listen window;
8 MB PSRAM variant = 0.55 s), then trickles it out over USB between pings; ALL
processing on the laptop. ~1–2 Hz imaging for ~$5–10. Adopt as optional v0
bring-up device hanging off the same generic PDM header (socket or ribbon);
tickets T-009 (snapshot firmware) to be written only if Joshua opts in.

## Amendment 2026-08-25 (b): Ethernet provision + bandwidth correction
- CORRECTION: raw PDM is 24 mics × 3.072–4.8 MHz = **74–115 Mb/s** (earlier ~58 Mb/s
  figure under-counted). 100M Ethernet carries only the DECIMATED stream
  (24×16b×100–128 kHz ≈ 38–49 Mb/s, needs in-fabric CIC); raw needs FT232H
  (~320 Mb/s) or GbE. FT232H remains the day-one egress.
- Pin budget allows Ethernet: Cmod A7-35T has 44 DIP + 8 PMOD ≈ 52 pins; array uses
  ~16–20; RMII PHY adds 9. T-011 shall place an RMII PHY (LAN8720-class) + MagJack
  as DNP footprints on spare socket pins — a later populate-and-learn milestone
  (MAC + UDP + CIC in Vivado), never a respin. Not on the v1 critical path.

## Why
Learning value is now an explicit project goal. Verilog/digital design/verification
transfer from any board, but Vivado literacy (XDC constraints, IP Integrator, AXI,
ILA debugging, timing closure) only comes from using Vivado, and that is what
industry runs (AMD ≈ half the market; Lattice is a niche third).

## Consequences
- **Vivado does not run on macOS.** Requires an x86 Linux/Windows host: used mini-PC
  (~$150–250) or a cloud VM (~100 GB disk). Agents drive Vivado headless via Tcl on
  that host — slower iteration than yosys/nextpnr; CI needs that machine reachable.
- Cost: $249 board + build host vs $50 i5 kit.
- T-007 buy list, T-011 digital sheet (header, not SODIMM), T-020 gateware
  (Vivado project + XDC + AXI-stream pipeline; keep a Verilator-testable core) all
  rescope on ratification.
