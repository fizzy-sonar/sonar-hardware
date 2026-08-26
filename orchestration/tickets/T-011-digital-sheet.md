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
