---
id: D014
title: Use Joshua's existing DE10-Lite for the next bench milestone
status: proposed
date: 2026-09-13
author: codex/T-023
supersedes: D012 (bench platform and toolchain only, if ratified)
---

## Proposal

Joshua now reports owning a DE10-Lite from school. Pause the Cmod purchase and
use the existing board for initial digital/coupon validation, after a bounded
Quartus port and pin/timing audit. This is a recommendation, not a ratification
or a completed port. The current Cmod target remains intact. Final carrier
integration and the Vivado-specific learning goal remain separate decisions.

## Feasibility checked 2026-09-13

[Terasic's specifications](https://www.terasic.com.tw/cgi-bin/page/archive.pl?CategoryNo=218&Language=English&No=1021&PartNo=2)
list a MAX 10 10M50DAF484C7G, 50K logic elements, 1,638 Kbit M9K memory, four
PLLs, 64 MB x16 SDRAM, a 3.3 V 2x20 expansion header, and onboard USB-Blaster
using a standard Type-B connector. These resources make the raw-PDM capture
architecture credible; they do not prove placement/timing or the exact pin map.
The MAX 10 GPIO Lite IP supports hard input DDR on 10M50:
[manufacturer parameter reference](https://docs.altera.com/r/docs/683751/26.1.1/max-10-general-purpose-i/o-user-guide/gpio-lite-ip-parameter-settings?contentId=jlBUoo6~hbjvbVT1hHa3nw).

[Quartus Lite supports MAX 10](https://www.intel.com/content/www/us/en/products/details/fpga/development-tools/quartus-prime/resource.html).
Its supported hosts are Windows/Linux, not native macOS:
[OS support](https://www.altera.com/design/guidance/software/os-support).
Actual school software/computer access is not yet known.

## What transfers and what changes

- Reuse portable packing, stream format, FIFO/control concepts, TX arithmetic,
  host DSP/parsers and existing behavioral tests. Re-verify RAM inference/reset
  behavior on MAX 10; passing Icarus tests is not an Intel implementation result.
- Replace the Xilinx IDDR, MMCM/BUFG/ODDR clock wrapper and Cmod top-level with
  MAX 10 DDR/clock/reset wrappers plus QSF/SDC assignments. Derive an achievable,
  tolerance-correct microphone clock from the actual DE10-Lite oscillator.
  Check returned PDM/FT clocks on appropriate clock-capable pins and both-edge
  setup/hold timing before claiming interface compatibility.
- The DE10-Lite has SDRAM, not the Cmod's asynchronous SRAM. Existing
  `sram_snapshot.sv` cannot drive it. Start with a small on-chip RAM snapshot
  and a debug readout; postpone an SDRAM controller until the basic path works.
  Snapshot length must be budgeted from actual RAM packing, not the 64 MB label.
- USB-Blaster is the configuration/debug connection, not a ready-made
  9.216–14.4 MB/s USB acquisition interface. A JTAG-based memory readback path
  needs implementing and is only a debug proposal. Continuous raw streaming
  still needs the separately configured FT232H plus a verified adapter.
  The Cmod USB-UART fallback is not automatically available on this board.
- Use the coupon header/adapter. DE10-Lite cannot plug into the Cmod DIP socket.
  Its existing USB connector is Type-B; this proposal does not silently satisfy
  or waive an all-USB-C product preference.

## Next milestone if adopted

Create a Quartus board target, prove programming/clock/reset, implement a small
counter-pattern capture and readback, then verify FT232H integrity and attach a
four-microphone coupon. Keep TX disabled until the existing command/wake/fault
work is complete. No board purchases or SDRAM development are prerequisites for
the initial programming/digital test. Existing acoustic, host and production
release gates remain in force.

No Quartus compile, pin assignment, physical board inspection or capture has
been performed. The direct Terasic manual URL did not load; exact wiring must
come from the manual/schematic for the user's board revision, never a guessed
header mapping. This proposal establishes feasibility and avoids an unnecessary
immediate purchase; it does not certify a DE10-Lite implementation.
