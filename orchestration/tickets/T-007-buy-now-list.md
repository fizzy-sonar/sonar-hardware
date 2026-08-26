---
id: T-007
title: Buy-now list for Joshua (dev hardware + Vivado host)
status: review
phase: P1
tier: cheap        # web research + price table
priority: 1
assignee: codex/luna-t007
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
- 2026-08-25 codex/luna-t007: Added `orchestration/buy-list.md` with live
  manufacturer/distributor links, exact variants, prices, stock and shipping
  caveats, subtotal, optional LAN8720, and mini-PC versus cloud host comparison.
  Wideband horn is a measurement candidate only; raw TX SPL is not link-budget
  evidence. D012 stale Arty prose is flagged. Joshua choices remain.

## Verification log (2026-08-25)

- Raspberry Pi official page: Pico 2 available from $5; Crowd Supply exact listing
  reported $5, in stock, $8 US shipping.
- Digilent official Cmod page: SKU 410-328-35, $104.00; distributor stock/lead
  time remains a checkout-time check.
- Adafruit 2264: $14.95, in stock, ships today; Mouser showed 772 in stock.
- DigiKey MA40S4S 490-7707-ND: 3,942 in stock, $6.12 each; Not For New Designs,
  20 Vp-p.
- Parts Express GRS PZ1005 292-442: $2.99, in stock; no normalized 20–32 kHz
  response claimed.
- AMD Vivado page confirms Windows/Linux and x86-64 host requirements.
- `git diff --check` passed after edits.
- Repair pass 2026-08-25: corrected MA40S4S/MA40S4R variants and stock state,
  replaced generic links with exact product pages, added exact Waveshare LAN8720,
  Adafruit supply/cable, and official cloud pricing links, and recomputed subtotal
  to $159.12. `git diff --check main...agent/T-007-buy-now-list` passed.
