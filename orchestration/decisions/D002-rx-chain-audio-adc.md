---
id: D002
title: RX chain: audio-class ADC, single-supply analog
status: superseded by D011
date: 2026-08-25
author: claude (fable) — architecture review
---
## Decision
Mic → one gain/anti-alias stage → TLV320ADC5140-class 4-ch audio ADC (6 chips, TDM, shared MCLK/FSYNC, I²C config), everything on 3.3/5 V. Replaces the 3× ADS8568 ±10 V parallel-bus chain.

## Why
Mic signals are mV-level with a 124 dB SPL overload point; ±10 V rails and a ±12 V-input SAR buy nothing. Audio ADC has built-in PGA + mic bias, costs ~$3 vs ~$25, and collapses the power tree from ~7 converters to 4 rails. Sigma-delta group delay is constant across a shared clock and calibrates out of TOF.

## Consequences / what this forecloses
Deletes sheets: 5_to_10_boost, inverting_buck_boost, -10v_negative_ldo, 2.75V_ldo, 12v_to_10v_ldo, and the parallel adc_bus_a/b/c topology. fs 192 kHz default (to 768 kHz available); the old 450 kSPS figure was an ADS8568 property, not a requirement.
