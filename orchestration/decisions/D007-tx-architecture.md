---
id: D007
title: TX: DRV8876 h-bridge, transducer off-board
status: ratified
date: 2026-08-25
author: claude (fable) — architecture review
---
_Ratified 2026-08-25: Joshua, "ok. lets go with that" (blanket go-ahead for the standing defaults + the D012 platform ladder)._

## Decision
Keep the DRV8876 driver; the transducer connects via an on-board connector — Murata MA40S4S for 40 kHz narrowband, piezo horn tweeter for 20–32 kHz chirps. 12 V boost rail retained for TX only.

## Why
TX is the least-settled subsystem; a connector makes changing it a cable swap, not a board spin. Also resolves the center-cell size conflict (D001).

## Consequences / what this forecloses
Center cell hosts a connector/hole, not a soldered transducer. TX beam-steering deferred to v2.
