---
id: D011
title: "RX chain: all-digital PDM ultrasonic microphones (Option C adopted)"
status: ratified
date: 2026-08-25
author: joshua (verbal, via chat) — recorded by claude (fable)
supersedes: D002, D003
---
## Decision
Adopt Option C: 24× digital PDM ultrasonic MEMS microphones wired directly to the
FPGA. No ADCs, no analog preamps, no analog rails. FPGA runs the mics in ultrasonic
mode (~4.8 MHz clock) and decimates (CIC + compensation FIR) to multi-bit samples.
Mic part chosen by the T-002/T-008 bake-off: candidates TDK ICS-41350 / ICS-41352,
Syntiant SPH0641LU4H (lifecycle check required), TDK T5838. Provisional ("for now"):
revisit at CP-B if T-001's model shows the PDM ultrasonic-band noise floor is limiting.

## Why
Minimum-risk board for a time-poor project: deletes 6 ADC chips, 6 opamps, I²C
config, mic bias, and the analog power domain. RX becomes 24 mics + a clock tree +
~12 data lines (mics pair on shared data lines via L/R select). Cost: ~3–6 dB worse
noise in the ultrasonic band, fixed gain, and the decimation filter must exist
before any signal is observable (T-020 grows).

## Consequences / what this forecloses
- T-003 (AFE sim) and T-004 (overload-recovery sim) are superseded; T-008 replaces them.
- Power tree simplifies further: 5 V in → 3.3 VD (+ mic rail 1.8 V if the chosen part
  wants it — T-002 confirms), 12 V TX boost. No 3.3 VA opamp rail.
- Gateware (T-020) gains: PDM clocking incl. ultrasonic mode, per-channel CIC + FIR,
  Verilator TB fed with synthetic PDM streams.
- No analog test points per channel — bring-up observability shifts entirely to the
  FPGA path; T-020's counter/pattern modes become the debug story.
