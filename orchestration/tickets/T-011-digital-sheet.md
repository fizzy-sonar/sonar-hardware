---
id: T-011
title: Digital sheet — Cmod A7-35T socket, FT232H, headers
status: in-progress
phase: P2
tier: top        # pin-budget audit across 3 interfaces; highest-consequence errors
priority: 1
assignee: codex/sol-t011
depends_on: [T-002, T-008]
needs_human: false
created: 2026-08-25
updated: 2026-08-26
---
## Goal
Create `digital.kicad_sch` per D012 (ratified):
1. DIP-48 socket for the Cmod A7-35T (module powers itself from its own USB; decide
   and document the board↔module power strategy).
2. FT232H interface: header matching the Adafruit breakout (sync-FIFO signals:
   8 data + RXF#/TXE#/RD#/WR#/CLKOUT/OE# ≈ 13 + power), routed to Cmod pins.
3. Generic PDM header (data lines + clocks + GND interleave) — doubles as the
   ribbon attachment for the Pico 2 v0 (only one platform attached at a time; note
   contention rule in the sheet).
4. DNP Ethernet provision: LAN8720-class RMII footprint + MagJack + 50 MHz osc on
   9 spare Cmod pins.
5. TX control lines to the h-bridge sheet; LEDs; test points.
6. Remove the DF40 B2B connectors and all `adc_bus_*` labels from the top sheet.

## Context
D011, D012 (both ratified). Pin budget audit: array ~16–20 + FT232H ~13 + RMII 9
≤ 44 DIP + 8 PMOD. Every FPGA signal lands in `orchestration/pinmap.md` — the
authoritative pin table T-020's XDC is generated from.

## Definition of Done
ERC-clean; pinmap.md committed; contention rule documented; DF40/adc_bus removed.

## Verification
`scripts/check.sh` ERC section; pinmap cross-checked against the Cmod A7 reference
manual by a second agent session.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 claude (fable): rewritten for ratified D012 (was SODIMM/i5).
- 2026-08-25 codex/sol-t008: marked ready after T-002/T-008 completion. The common
  paired interface and clock-capable feedback pin can proceed before T-016; keep
  the mic clock parameterized until the physical MPN release.
- 2026-08-26 codex/sol-t011: digital sheet + pinmap + XDC delivered on branch
  agent/T-011-digital-sheet (working tree; **sandbox blocked all git writes** —
  `git add`/`git commit` fail with `Operation not permitted` on the worktree
  gitdir, approval policy Never; ORCHESTRATOR MUST COMMIT: `git add -A` in the
  sonar-t011 worktree covers it).
  Deliverables:
  - `orchestration/pinmap.md` - authoritative pin table, GENERATED from the PIN
    TABLE in `scripts/gen_digital_sheet.py` (single source of truth; also emits
    the schematic and XDC - regenerate, don't hand-edit outputs).
  - `sonar-v1-pcb/digital.kicad_sch` - J40 DIP-48 socket (Conn_02x24_Counter_
    Clockwise + DIP-48_W15.24mm_Socket fp), J41 FT232H 1x20 header (sync-FIFO
    C0=RXF#,C1=TXE#,C2=RD#,C3=WR#,C4=SIWU,C5=CLKOUT,C6=OE#), J42 2x13 PDM header
    (GND-interleaved, Pico 2 ribbon point, contention rule on-sheet), DNP RMII
    block (U50 LAN8720A + J43 HR911105A + X1 50 MHz + straps/RBIAS/decoupling),
    TX control global labels for T-013, 7 test points, +3.3V power LED, SJ1/SJ2
    DNP power-option jumpers, PWR_FLAGs. Sheet block added to top sheet (no sheet
    pins - all cross-sheet nets are global labels by design, see pinmap.md).
  - `sonar-v1-pcb/sonar.kicad_sch` - DF40 U1 (both units) and all 51 adc_bus_*
    labels removed plus the 49 bus_entries and 131 in-region wire/bus/label
    graphics (deterministic patcher in the generator; verified byte-identical
    from-scratch vs incremental). Legacy array-sheet read_out_bus/adc_busy
    interface fallout (+22 isolated_pin_label warnings inside legacy sub-sheets)
    is EXPECTED and belongs to T-010's array-sheet rework.
  - `gateware/constraints/sonar_cmod_a7.xdc` - T-020 baseline: all 44 DIP pins,
    on-module sysclk/LEDs/BTN, create_clock for sysclk/pdm_clk_fb/ft_clkout
    (eth_ref_clk commented), DNP RMII block commented.
  Decisions made (documented in pinmap.md + on-sheet text):
  - Power strategy: Cmod self-powered from own USB; grounds common; CMOD_3V3/
    CMOD_VU no-connect by default; SJ1/SJ2 DNP rework options; FT232H and Pico 2
    self-powered. +3.3V rail source = T-012 (PWR_FLAG placeholder).
  - Contention rule: Cmod in J40 XOR Pico 2 ribbon on J42, never both.
  - Pin budget 44/44 used: PDM 15 (pio10-21 data on bank 35; SRC=pio9, EN=pio7,
    FB=pio36), FT232H 14 (pio22-34 + CLKOUT=pio43), RMII 10, TX 5. Clock-critical
    nets on double-sourced clock-capable pins only: PDM_CLK_FB=pio36 (MRCC_34),
    FT_CLKOUT=pio43 (SRCC_34), ETH_REF_CLK=pio3 (MRCC_16).
  PROVENANCE RISK (flagged loudly in pinmap.md/XDC/schematic): no network on this
  machine, so pio->package-pin mapping is transcribed from memory of the Digilent
  Cmod-A7-Master.xdc, cross-anchored to T-008's documented clock-capable list.
  Known discrepancy (pio16/17 vs pio18/19, pio46-48 power-vs-CC) documented in
  pinmap.md for the auditor.
  Verification (real output, this machine, kicad-cli 10.0.1):
  - `scripts/check.sh`: ERC/netlist/PDF/SVG/BOM all exit as expected; sonar ERC
    report: baseline 512 msgs (352 err) -> now 456 msgs (339 err); **the
    /digital/ sheet section contains ZERO violations**.
  - Legacy deltas vs baseline: pin_to_pin 130->6, pin_not_connected 39->26,
    net_not_bus_member 2->0 (DF40 removal wins); isolated_pin_label 1->23
    (expected T-010-scope fallout); different_unit_net 42->42 total (renamed
    instance attribution only).
  - `pcb drc` aborts (exit 134) in this sandbox on ALL projects incl. pristine
    HEAD copies -> environmental, needs the approved-unsandboxed run per T-006;
    T-011 changed no .kicad_pcb files.
  - SVG render of digital.kicad_sch visually inspected (build/sonar-svg/
    sonar-digital.svg): all stubs/labels/power symbols land on pins.
  Remaining (NOT done):
  1. Second-agent audit of pinmap.md vs the live Digilent Cmod-A7-Master.xdc +
     Cmod A7 reference manual (ticket Verification step; needs network). If the
     audit moves any pin, edit the PIN TABLE in scripts/gen_digital_sheet.py and
     re-run it (regenerates schematic+XDC+pinmap; top-sheet patch is idempotent).
  2. Orchestrator: commit the worktree (git writes were sandbox-blocked).
  3. Joshua: KiCad files changed on disk - reload before opening (STATUS noted).
  Exact next step: launch the T-011 audit session (cheap tier + network), then
  move T-011 to done and unblock T-020's pin constraints.
