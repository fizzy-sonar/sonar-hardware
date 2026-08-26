---
id: T-001
title: Link-budget / minimum-detectable-signal model
status: done
phase: P1
tier: mid        # physics + numpy modelling; ordinary code with plots
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
- 2026-08-25 codex: claimed T-001 on `main` and completed substantive work on
  `agent/T-001-link-budget-model`. Added `analysis/link_budget.py`, the sourced
  `analysis/link_budget.md`, five deterministic PNG plots, and three CSV tables.
  Parallel research covered ISO 9613-1 absorption, manufacturer microphone-noise
  data, transmitter normalization, target strength, and chirp scheduling; two
  independent acceptance passes checked the implementation and DoD.
- 2026-08-25 codex: anchor sanity check reproduces +39.80 dB at 10 m (the PLAN's
  rounded +40 dB). Reference case at 20 C / 50% RH uses alpha=0.732 dB/m,
  provisional 104 dB SPL wideband TX, and the digitized typical ICS-41352 curve:
  +27.09 dB person margin at 10 m and 20.18 m zero-margin range. The ICS-41352
  mic-only penalty versus IM73A135 is +2.34 dB over 20-32 kHz, but only +0.15 dB
  after adding the stated ambient noise; D011 is not nominally SNR-gated. Main
  residual risks are the uncalibrated wideband TX, small-target margin, correlated
  room noise/reverberation, and port-dependent mic response. MA40S4S has no
  published SPL below 30 kHz and a 12 V full bridge exceeds its continuous-square
  Vpp limit; carry that constraint into T-013.
- 2026-08-25 codex: required verification output:

  ```text
  $ python3 analysis/link_budget.py
  Sonar v1 link-budget outputs generated
    Anchor margin at 10 m: 39.80 dB
    24-channel array gain: 13.80 dB
    Scenario pulse-compression gain: 18.99 dB
    Scenario absorption at 25 kHz (20 C, 50% RH): 0.732 dB/m
    Primary Option C person margin at 10 m: 27.09 dB
    Primary Option C person zero-margin range: 20.18 m
    ICS-41352 mic-only / ambient-context penalty over 20-32 kHz: 2.34 / 0.15 dB
    12.0 kHz range resolution: 0.0143 m
    6.6 ms chirp + 1 ms guard blind zone: 1.307 m
    Output directory: .../analysis/generated
  ```

  `ruff check analysis/link_budget.py` passed; `ruff format --check` reported the
  file already formatted; `python3 -m py_compile analysis/link_budget.py` and
  `git diff --check` passed. A fresh output directory matched all eight committed
  artifacts byte-for-byte. Non-finite CLI input is rejected with exit status 2.
