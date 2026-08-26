---
id: T-002
title: Part availability & lifecycle audit
status: done
phase: P1
tier: cheap        # web research + datasheet lookup + table building
priority: 1
assignee: codex/t002
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
For every candidate part, confirm: lifecycle status (esp. the ex-Knowles→Syntiant mic line), LCSC/JLC stock or Global-Parts orderability, price @ qty 30, and datasheet link. Parts: TLV320ADC5140 (alts ADC3140, PCM1840, CS5368, AK5538); mics SPV0142LR5H-1, IM73A135, ICS-41350/41352, SPH0641LU4H; opamps OPA1679 (alts OPA1654, TLV9354, OPA4322); DRV8876; TPS55340; Colorlight i5; SODIMM-200 socket; DF40 removal check. Also pull the Knowles/Syntiant ultrasonic-response app note (AN-17 family) and extract what it says about SiSonic response 20–40 kHz.

## Context
**2026-08-25 scope update (D011)**: PDM ultrasonic mics (ICS-41350/41352, SPH0641LU4H, T5838) are now the PRIMARY mic rows — include ultrasonic-mode specs (clock range, band, SNR) per part. Audio-ADC + opamp + analog-mic rows remain as fallback documentation only.

Decisions D002, D003, D009. This gates T-003 (opamp/ADC choice) and CP-B.

## Definition of Done
`orchestration/parts-matrix.md`: table of part / status / source / stock / price / notes, plus a RECOMMENDED column, plus the app-note findings paragraph. Flag anything not orderable through JLC turnkey.

## Verification
Matrix committed; every row has a dated source link; recommendation defensible in one paragraph each.

## Log
- 2026-08-25 claude (fable): D012 ratified — ADC/opamp rows now historical-only (skip unless trivial); add rows: Cmod A7-35T, FT232H breakout, LAN8720 module, Pico 2 / Pico Plus 2, DIP-48 socket.
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 codex/luna: delivered `orchestration/parts-matrix.md`. Audited D011 primary PDM rows (ICS-41350/41352, SPH0641LU4H, T5838), D012 platform rows, SODIMM rejection, and historical analog rows. Added dated manufacturer/vendor links, lifecycle/orderability observations, ultrasonic specs, recommendations, and Knowles AN-17/AN24 findings. Public qty-30 prices and LCSC/JLC turnkey status were not reliably exposed; matrix flags these for CP-C recheck. Verification: `git diff --check` passed; all matrix rows contain dated source links.
