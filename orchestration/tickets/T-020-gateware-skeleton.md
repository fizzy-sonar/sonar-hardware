---
id: T-020
title: Vivado gateware — PDM capture + FT232H streaming (Cmod A7-35T)
status: in-progress
phase: P5
tier: top        # novel HDL + Vivado constraints + testbenches
priority: 2
assignee: codex/sol-t020
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-26
---
## Goal
Vivado project for the Cmod A7-35T in `gateware/`:
1. Parameterized PDM clock generation + the T-008 12-line/24-channel IDDR sampler.
   Default to provisional SPH at 3.072 MHz and test the ICS 4.8 MHz alternate; T-016
   freezes the production default.
2. Word packer → ~64 KB BRAM elastic FIFO → FT245 synchronous-FIFO interface to the
   FT232H (~40 MB/s; raw stream is 9–14.4 MB/s so no in-fabric DSP — D006).
3. Day-one fallback: UART snapshot mode over the Cmod's own USB (on-module 512 KB
   SRAM window) so bring-up starts before the FT232H is wired.
4. TX chirp generator (NCO → PWM out to DRV8876 lines).
5. Everything scripted: Tcl-driven project generation + batch builds (no GUI-only
   state in the repo); XDC generated from `orchestration/pinmap.md` when it exists
   (placeholder pins until then).
6. Testbenches: Verilator or cocotb+xsim feeding synthetic PDM (sigma-delta model of
   a known tone); FT245 bus-functional model for the FIFO interface.

## Context
D012 (ratified). PREREQUISITE: x86 Vivado host (T-007 item 7) for synthesis; the
testbench layer must run on any machine (Verilator/pytest) so agent work is NOT
blocked on the host. Learning goal: keep the design readable — Joshua reads this
to learn Vivado; comment constraints and CDC decisions.

`docs/pdm-capture-contract.md` v1 is a provisional SPH electrical/sample baseline,
not an MPN release. T-016 may select ICS and require the documented 4.8 MHz /
14.4 MB/s default. Parameterization lets testbench work proceed without prejudging
that human-gated result.

## Definition of Done
`gateware/README.md` reproduces builds from a clean clone; TB proves sampler +
packer + FIFO against synthetic PDM at both 3.072 and 4.8 MHz, including edge/channel
order and 73.728/115.2 Mb/s payload calculations; batch bitstream build succeeds on
the Vivado host; UART snapshot mode demonstrated in sim.

## Verification
`make test` runs the TB suite; build log + utilization/timing summary in the Log.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 claude (fable): rewritten for ratified D012 (was LiteX/ECP5/TDM/UDP).
- 2026-08-25 codex/sol-t008: independent T-008 review made the clock/rate
  parameterization and dual-rate test explicit so TB work can start before T-016's
  physical MPN release without freezing the provisional SPH default.
- 2026-08-26 codex/sol-t020: recovered the uncommitted simulator draft and built
  the portable T-020 milestone in `gateware/`. The raw path is returned-clock
  IDDR -> 24-bit logical frames -> 16,384x32 Gray-pointer async FIFO -> 3-byte LE
  packer -> registered write-only FT232H synchronous FIFO. `SNR1` v1 is exactly
  one 32-byte header per explicit capture (all fields checked, capture IDs
  increment); no byte is emitted at reset alone. `capture_enable` low is a
  coordinated fresh-stream boundary. Overflow is sticky through that boundary,
  stops the producer without overwrite/continuation, and drains the exact
  already-accepted prefix while capture remains asserted.
- 2026-08-26 codex/sol-t020: `cd gateware && make test` PASS under Icarus Verilog
  13.0: 3.072/4.8 MHz edge/channel mapping with 73.728/115.2 Mb/s calculations;
  async FIFO/packer/registered FT245 BFM; end-to-end 100-frame exact delivery
  through a long plus pseudo-random `TXE#` stall pattern; forced 8-frame FIFO
  overflow/exact-prefix drain/sticky status/new capture ID; exact two-capture
  SNR1 headers; 60-byte UART `SNP1` with both CRCs; exact clock-plan arithmetic,
  50 ms + switch-off + 10 ms startup, and bounded fixed-point TX chirp safety.
  The final Icarus step also elaborates `sonar_top` plus the `XILINX` branches
  against compile-only primitive stubs. Only three benign Icarus array-
  sensitivity warnings occur in the small UART inferred-memory mux.
- 2026-08-26 codex/sol-t020: **ticket remains in-progress.** No `vivado` binary or
  x86 Vivado host is available, and T-011 has not published
  `constraints/sonar_cmod_a7.xdc`. Therefore there is no bitstream, utilization,
  placed timing/CDC report, UNISIM IDDR polarity proof, BRAM inference proof, or
  hardware FT232H/UART demonstration. The Tcl build intentionally refuses an
  unpinned bitstream. The full 512 KiB external-SRAM UART controller/control
  plane and T-013 hardware TX limits also remain future integration work.
- 2026-08-26 codex/sol-t020 (session 2): resumed after the prior session was
  killed mid-work with everything uncommitted. Assessed via `git status`/diff,
  the journal, and this Log; committed the recovered work in four logical
  commits (RTL, testbench suite + Makefile, docs, Vivado Tcl/placeholder XDC +
  `.gitignore`). Re-ran the ticket Verification from a clean build on this
  machine (`cd gateware && make clean && make test`, Icarus Verilog 13.0
  stable). Real output:

      PASS sampler/tone rate=3072000Hz frames=80 payload=73728000b/s
      PASS sampler/tone rate=4800000Hz frames=80 payload=115200000b/s
      PASS async FIFO/packer/FT245 backpressure bytes=24
      PASS core SNR1 + 100 exact frames survive long/random TXE# stalls
      PASS overflow stops and drains exact 8-frame prefix; capture restart increments SNR1 ID
      PASS SNR1 exact 32-byte headers start once per capture and hold under backpressure
      PASS UART SNP1 snapshot bytes=60 CRCs verified
      PASS exact 1.536/3.072/4.8MHz plan, 50ms+10ms startup, and bounded TX chirp safety
      PASS XILINX primitive branches and sonar_top elaborate with compile-only stubs

  (only the three known benign Icarus `@*` array-sensitivity warnings in
  `rtl/uart_snapshot.sv`; `git diff --check` clean.)
- 2026-08-26 codex/sol-t020 (session 2): **ticket remains in-progress, DoD
  unmet.** Remaining, with exact unblockers:
  1. Batch bitstream build + utilization/timing/CDC reports — blocked on the
     x86 Vivado host (T-007 item 7; Joshua purchase/host decision). Unblock:
     host exists, then `vivado -mode batch -source vivado/create_project.tcl`
     and `vivado -mode batch -source vivado/build_bitstream.tcl` per
     `gateware/README.md`.
  2. Real `constraints/sonar_cmod_a7.xdc` — blocked on T-011's audited pin map
     (incl. clock-capable `PDM_CLK_FB`). The Tcl intentionally refuses an
     unpinned bitstream; no fabricated `PACKAGE_PIN` values exist.
  3. UNISIM IDDR polarity and BRAM-inference proofs, FT245 I/O timing — need
     the Vivado host from (1).
  4. Hardware FT232H streaming + UART snapshot demonstration — needs boards
     (T-007 buy list) after (1) and (2).
  5. Full 512 KiB external-SRAM snapshot controller + control plane, and
     T-013-released TX limits — future integration tickets.
  Sandbox note: this session's environment could not write the shared git dir,
  so the commits were authored into a scratch git dir and exported as
  `t020-gateware-commits.bundle` at the worktree root. Land them with:
  `git fetch /private/tmp/sonar-t020/t020-gateware-commits.bundle \
    agent/T-020-gateware:agent/T-020-gateware` from the main checkout.
