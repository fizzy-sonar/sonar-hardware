---
id: D013
title: v1 default TX path — piezo horn tweeter (20–32 kHz chirps); MA40S4S 40 kHz gated on a datasheet reading
status: proposed        # proposed | ratified | vetoed | superseded by DXXX
date: 2026-08-26
author: codex/sol-t020
---
## Decision

The v1 default TX configuration is the **piezo horn tweeter driven with
20–32 kHz chirps** (D007's wideband option, the configuration the T-001 link
budget assumes). The MA40S4S 40 kHz tone path remains supported by the
gateware envelope (`orchestration/tx-limits.md`) but is **not** the default,
and its use at 12 V VM is gated on Joshua reading the Murata datasheet to
determine whether the "20 Vpp max" rating is a **terminal** voltage limit or a
**drive/fundamental** figure:

- **If terminal:** a 12 V full bridge is not permitted at ANY amplitude —
  duty-chopping bounds only the fundamental component, while OUT1/OUT2 always
  swing rail-to-rail and J50 sees 24 Vpp transitions for any nonzero duty
  (REVIEW-2026-08-26 S5). Mitigation before enabling MA40S4S: reduced VM
  setpoint on the +12 V boost (e.g. ~10 V → 20 Vpp terminal) or a series
  drop element at R173/R174, plus a re-derived amplitude cap.
- **If fundamental:** the existing envelope stands unchanged (40.0 kHz fixed
  tone, phase_increment 55924, amplitude ≤ 187/256 → ≤20 Vpp
  fundamental-equivalent).

The tweeter path keeps the provisional `MAX_AMPLITUDE = 187` build-time cap
until the purchased part's Vpp rating is confirmed (tx-limits.md), then may
open to 255.

## Why

REVIEW-2026-08-26 B2 demonstrated that averaged envelope checks hide
per-half-cycle excursions, and S5 that no duty setting bounds terminal
voltage — so the safety argument for a narrowband resonant transducer rests
entirely on a datasheet-reading that has not been made. The tweeter is the
D001/D007 reference configuration anyway, needs no 40 kHz resonance for the
chirp band, and its rating check is a single datasheet line at order time
(T-007 item). needs_human: Joshua ratifies at CP-B/CP-C and does the
MA40S4S datasheet reading.

## Consequences / what this forecloses

- Gateware defaults unchanged: `MAX_PHASE_INCREMENT=55924`,
  `MAX_AMPLITUDE=187`, `MAX_BURST_CYCLES=120000` cover both paths.
- MA40S4S bring-up at 12 V VM is blocked until the datasheet reading lands;
  ratifying this decision as-is makes the tweeter the CP-E acoustic
  bring-up target.
- A "terminal" reading adds a small power-tree/series-element change (T-012
  boost setpoint or R173/R174 values) before any MA40S4S session.
