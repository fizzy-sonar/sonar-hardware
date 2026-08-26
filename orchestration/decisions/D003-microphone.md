---
id: D003
title: Microphone: keep SPV0142LR5H-1; bake off vs modern candidates
status: superseded by D011
date: 2026-08-25
author: claude (fable) — architecture review
---
## Decision
Default mic remains SPV0142LR5H-1 (Syntiant — ex-Knowles SiSonic line, sold to Syntiant 2024; current production). P1 bake-off vs Infineon IM73A135 (analog, 73 dB SNR, 135 dB AOP) and TDK ICS-41350/41352 (documented ultrasonic response; PDM → pairs with Option C). SPU0410LR5H-QB is EOL — do not use.

## Why
Joshua's pick is current production. Response >20 kHz is unspecified, but bottom-port MEMS package resonance (~20–40 kHz) typically boosts our band; per-channel calibration (already planned) absorbs unit variation. Verify via the Knowles/Syntiant ultrasonic app note in T-002.

## Consequences / what this forecloses
Mic footprint/land pattern must be pinned before P3. If the bake-off flips to a PDM mic, D002 flips to Option C (all-digital, no ADCs).
