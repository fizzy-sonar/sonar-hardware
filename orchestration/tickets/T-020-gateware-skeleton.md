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
- 2026-08-26 codex/sol-t020 (session 3): implemented the 512 KiB on-module
  SRAM snapshot fallback (D012 "UART snapshot via the Cmod's own USB"), the
  remaining agent-doable item from the session-2 list.
  - `rtl/sram_snapshot.sv`: start-triggered capture streams the accepted-frame
    tap (new `tap_frame_*` outputs on `pdm_stream_core`) through a 16x32
    Gray-pointer CDC FIFO into the IS61WV5128BLL-10BLI, then drains over
    `uart_tx` with the exact 48-byte SNP1 v1 header (counts/CRCs computed from
    the completed capture, so timeout/overrun truncation is described honestly;
    capture IDs increment per capture). One byte per three 48 MHz clocks
    (16 MB/s > 14.4 MB/s ICS worst case) with SETUP/PULSE/HOLD write
    microcycles: >= 2.6x margin on the cited ISSI -8 ns grade parameters
    (tWC 8 / tPWE 6 / tSD 5.5 / tHD 0 ns; tAA/tDOE 8/5 ns reads vs 41.7 ns).
  - `sim/is61wv5128bll_model.sv`: behavioral 512Kx8 model enforcing tWC/tPWE/
    tSD/address-setup/bus-driven checks and modeling tAA=8 ns read delay.
    NOTE: sandbox has no network; the cited ISSI numbers are the standard
    -8/-10 grade datasheet values and must be re-verified against the live PDF
    on the Vivado host (marked TODO(host) in both files).
  - `sim/tb_sram_snapshot.sv`: (a) two back-to-back 16-frame captures plus a
    stream-stopped timeout (zero-frame) capture, each byte- and CRC-exact,
    capture IDs 5/6/7; (b) one full 512 KiB window: 174,762 frames, 524,334
    bytes drained and checked bit-exact (pattern + both CRC-32s).
  - Integration: `pdm_clock_7series` gains a 48 MHz MMCM CLKOUT2 (/16) +
    BUFG for the SRAM/UART domain; `sonar_top` instantiates `sram_snapshot`
    triggered by `btn[0]`, status on `led[0]`/`led[1]`, UART on
    `uart_rxd_out` (J18). New ports use the master-XDC names.
  - `constraints/sonar_cmod_a7.xdc`: appended the 30 SRAM pins
    (MemAdr[0..18], MemDB[0..7], RamCEn/RamOEn/RamWEn) copied EXACTLY from the
    live master XDC plus `uart_rxd_out` J18; all are dedicated on-module
    bank-14 nets with zero overlap against the 44 DIP pins (verified; the
    appended section is marked MANUAL APPEND so XDC regeneration keeps it).
    `scripts/check_pinmap_vs_xdc.py` still PASSes 44/44.
  - `cd gateware && make clean && make test`: **11/11 PASS** (Icarus 13.0);
    only the three known benign Icarus `@*` warnings in `uart_snapshot.sv`.
    Real output:

        PASS SRAM snapshot SNP1 round-trip: two back-to-back 16-frame captures + timeout-empty header, CRCs verified
        PASS SRAM snapshot full 512 KiB window bytes=524334 bit-exact

  - **Ticket stays in-progress (human gates).** Remaining, exactly:
    1. Vivado host (T-007 item 7): batch build, utilization/timing/CDC,
       UNISIM IDDR polarity + BRAM inference proofs, SRAM set_output_delay
       budgeting, live ISSI datasheet re-check of the model constants.
    2. `sonar_top` port-name reconciliation vs the pinmap XDC (pre-existing:
       `sys_clk_12mhz`/`pdm_data`/`ft_data`/`ft_clk`/`tx_a`/`tx_b` vs
       `sysclk`/`pdm_d`/`ft_d`/`ft_clkout`/`tx_en`/`tx_ph`), including a
       reviewed TX_EN/TX_PH mapping, before the bitstream can bind.
    3. Hardware demo: FT232H streaming + btn0-triggered SRAM snapshot over
       the Cmod's own USB-UART.
    4. T-013-released TX limits; future control plane (uart_txd_in J17 left
       unconstrained deliberately).
    Sandbox unchanged: no git writes; all work left uncommitted for the
    orchestrator.
- 2026-08-26 codex/sol-t020 (session 4): completed the two remaining
  agent-doable items.
  1. PORT-NAME RECONCILIATION (done): `sonar_top`'s port list is now an exact
     bijection with the active `get_ports` of the real XDC (28 ports / 73
     bits; the commented DNP RMII block excluded). Pinmap stayed authoritative
     (XDC names were already correct) so the RTL side was fixed: renames
     `sys_clk_12mhz`->`sysclk`, `pdm_data`->`pdm_d`, `pdm_clk_buffer_oe`->
     `pdm_clk_en`, `ft_data`->`ft_d`, `ft_clk`->`ft_clkout`. TX_EN/TX_PH
     mapping per `orchestration/tx-limits.md` (authoritative, T-013):
     `tx_en`=`tx_a` (EN/IN1, positive half-cycle), `tx_ph`=`tx_b` (PH/IN2,
     negative half-cycle), `tx_pmode`=1 (IN1/IN2 PWM interface mode; CP-C
     datasheet verify item), `tx_nsleep`=`tx_active`, `tx_nfault` mirrored on
     `led0_r`. The simulator-only scaffolding ports without pins (reset,
     mic_power_good, wake_request, tx_start/increments/amplitude/burst,
     capture status outs, ft_siwu_n) were replaced by documented internal
     tie-offs: 16-cycle power-on reset + btn[1] manual reset, control plane
     TODO constants (TX permanently idle, driver asleep), status on the
     on-module RGB LED (led0_b=overflow, led0_g=stopped). New gate:
     `gateware/sim/check_ports.py` (negative-tested both directions) wired
     into `make test` as check 12.
  2. SRAM TIMING EVIDENCE (done): the TODO(host) constants question is
     replaced by a per-phase timing-margin analysis in `gateware/sim/README.md`
     (cycles + ns per phase at the 48 MHz snapshot clock vs standard -8/-10
     grade tRC/tWC/tAA/tWP/tOE/tSD/tHD; worst margin 2.1x on tAA at a -10
     grade, >= 2.6x vs the on-module -10BLI/Digilent 8 ns rating). Also
     corrected an off-by-2x comment: reads budget one full clock (20.833 ns)
     of address/OE# access, not 41.7 ns (41.7/62.5 ns is the cycle time).
     The model still enforces tWC/tPWE/tSD in sim.
     **CP-C checklist: confirm the model's SRAM timing constants against the
     ISSI IS61WV5128BLL datasheet PDF.**
  - Verification: `cd gateware && make clean && make test` 12/12 PASS
    (Icarus 13.0), including
    `PASS sonar_top <-> XDC port bijection: 28 ports / 73 bits exact (active
    get_ports only, DNP block excluded)`; only the three known benign Icarus
    `@*` warnings in `uart_snapshot.sv`. `scripts/check_pinmap_vs_xdc.py`
    still PASSes 44/44 (XDC untouched).
  - **Ticket stays in-progress (human gates remain), exactly:**
    1. Vivado host (T-007 item 7): batch build, utilization/timing/CDC,
       UNISIM IDDR polarity + BRAM inference proofs, SRAM set_output_delay
       board-skew budgeting (~12.8 ns slack at the binding tAA corner).
    2. Hardware demo: FT232H streaming + btn0-triggered SRAM snapshot over
       the Cmod's own USB-UART.
    3. CP-C items: confirm SRAM constants vs ISSI PDF; PMODE polarity
       (tx-limits.md); T-013-released TX limits now wired as the MA40S4S
       envelope (amplitude 187/256).
    4. Future control plane to un-tie the internal TX/wake scaffolding.
  - Rules honored: no commit/merge/push; all changes uncommitted on
    agent/T-020-gateware for the orchestrator.
