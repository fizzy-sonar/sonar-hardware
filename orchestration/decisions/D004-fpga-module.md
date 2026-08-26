---
id: D004
title: FPGA: Colorlight i5 SODIMM module, no custom interposer
status: superseded by D012
date: 2026-08-25
author: claude (fable) — architecture review
---
## Decision
Socket a Colorlight i5 (Lattice ECP5-25, DDR2-SODIMM-200 form factor, 2× GbE PHYs on-module) directly on the board. Drop the DF40 B2B custom-interposer plan.

## Why
$30–50, open toolchain (yosys/nextpnr), existing LiteX target incl. Ethernet; deletes all FPGA/DDR/PHY layout risk. i9 is a drop-in bigger option, same pinout.

## Consequences / what this forecloses
Gray-market supply — buy 2–3 up front (T-007). Digital sheet is a SODIMM socket + community-documented pinout (chubby75 / colorlight-i5-tips).
