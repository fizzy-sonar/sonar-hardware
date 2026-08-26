---
id: T-001
title: Link-budget / minimum-detectable-signal model
status: in-progress
phase: P1
priority: 1
assignee: codex
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Build `analysis/link_budget.py`: sonar-equation margin(r) = SL + TS − 40·log10(r) − 2αr − NL + PG − DT, parameterized over frequency (20–40 kHz), humidity (absorption α), chirp length/BW, target strength (person / wall / small object), mic noise curves for Option B (SPV0142 / IM73A135 analog) AND Option C (ICS-41350 / SPH0641 PDM incl. shaped quantization-noise rise), and TX candidates (MA40S4S vs piezo tweeter, SPL vs drive). Outputs: max-range plots per target, blind zone vs chirp length, B-vs-C SNR delta in context.

## Context
**2026-08-25 note (D011)**: Option C is now adopted — model its noise curve as primary; the B-vs-C delta output doubles as the CP-B check on whether D011 should be revisited.

PLAN.md §P1.0 has the hand-calc anchor: SL 110 dB SPL@1 m, TS(person) −10 dB, α(25 kHz)≈0.5 dB/m, NL≈30 dB SPL in 8 kHz band, PG = 13.8 + 19, DT 13 → margin ≈ 90 − 40log10(r) − r dB (~+40 dB @ 10 m, zero ≈ 30 m). Decisions D001, D002, D003, D007.

## Definition of Done
Script + a short `analysis/link_budget.md` with plots and conclusions; reproduces the hand-calc anchor within a few dB and states whether architecture choice is SNR-gated; blind-zone vs chirp table feeds the P5 chirp scheduler.

## Verification
`python3 analysis/link_budget.py` runs clean and writes plots; numbers sanity-checked against the anchor in the Log.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
