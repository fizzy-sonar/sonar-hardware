---
id: T-003
title: RX AFE design + ngspice simulation
status: superseded
phase: P1
priority: 2
assignee:
depends_on: [T-002]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Pick the real opamp and finalize the RX stage (gain 14–20 dB, high-pass, anti-alias for chosen fs) in `rx_amp_sim/`: AC gain/phase 1 k–100 k, input-referred noise vs mic self-noise, stability (phase margin) with the real SPICE model, PGA interaction with the chosen ADC.

## Context
Decisions D002, D003. Existing sim project `rx_amp_sim/`, SPICE models in `sonar-library/spice-models/`. Gain topology and R_GAIN_* text-vars in `sonar-v1-pcb/quad_rx_pre_amp.kicad_sch`.

## Definition of Done
Final schematic values + MPN documented in `rx_amp_sim/results/afe-report.md` with plots; noise budget shows preamp+ADC ≤ mic self-noise in 20–32 kHz band.

## Verification
ngspice runs are reproducible from checked-in netlists; plots regenerate from a script, not by hand.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 claude (fable): SUPERSEDED by D011 (all-digital PDM mics — no analog AFE). Replacement: T-008.
