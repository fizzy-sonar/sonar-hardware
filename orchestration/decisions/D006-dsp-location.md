---
id: D006
title: DSP: all on the laptop for v1
status: ratified
date: 2026-08-25
author: claude (fable) — architecture review
---
_Ratified 2026-08-25: Joshua, "ok. lets go with that" (blanket go-ahead for the standing defaults + the D012 platform ladder)._

## Decision
FPGA only configures ADCs, deserializes TDM, packetizes, and times TX. All signal processing (matched filter, beamforming, calibration) in Python on the host.

## Why
Audio-rate math; laptop iteration speed >> gateware iteration speed. FPGA DSP only when a real-time standalone use case exists.

## Consequences / what this forecloses
Gateware stays small (fits ECP5-25 trivially); host pipeline must be proven on simulated data before boards arrive (T-021).
