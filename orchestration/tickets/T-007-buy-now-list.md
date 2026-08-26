---
id: T-007
title: Buy-now list for Joshua (dev hardware + Vivado host)
status: ready
phase: P1
tier: cheap        # web research + price table
priority: 1
assignee:
depends_on: []
needs_human: true
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Produce a click-ready purchase list with live links + prices (D012 ladder):
1. Raspberry Pi Pico 2 (or Pimoroni Pico Plus 2 w/ 8 MB PSRAM) — snapshot v0
2. Digilent Cmod A7-35T (DigiKey/Mouser; verify price ~$100–130 and stock; buy 1,
   note lead time for a 2nd)
3. Adafruit FT232H breakout (~$15)
4. LAN8720 RMII PHY module (~$4, optional, for the later Ethernet milestone)
5. Murata MA40S4S TX/RX pair + a wideband piezo horn tweeter
6. Bench USB-PD supply, cables, USB hub
7. **Vivado host** — present both options with prices for Joshua to pick:
   used x86 mini-PC (~$150–250, one-time, agents reach it via SSH/tailscale) vs
   cloud VM (x86, ≥16 GB RAM, ~120 GB disk; est. $/mo). Vivado does NOT run on macOS.
Target: ≤ $200 excluding the Vivado host.

## Context
D012 (ratified). Early ordering unblocks T-009 immediately and T-020 on real HW.

## Definition of Done
`orchestration/buy-list.md` with vendor links, prices, totals, and the Vivado-host
comparison; status → review for Joshua to purchase.

## Verification
Every link checked live on the day of writing; date stamped.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 claude (fable): rewritten for ratified D012 (Pico 2 + Cmod A7-35T +
  FT232H; i5 dropped; Arty demoted; Vivado host added). Earlier i5 guidance obsolete.
