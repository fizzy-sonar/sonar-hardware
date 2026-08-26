---
id: D001
title: Operating band: 20–32 kHz chirps, 25 kHz center
status: ratified
date: 2026-08-25
author: claude (fable) — architecture review
---
_Ratified 2026-08-25: Joshua, "ok. lets go with that" (blanket go-ahead for the standing defaults + the D012 platform ladder)._

## Decision
Primary band 20–32 kHz linear chirps centered ~25 kHz; keep the chain usable to 40 kHz. Array geometry: 5×5 grid with the center cell removed for TX (24 RX channels), pitch 6.9–8 mm (λ/2 @ 25 kHz = 6.9 mm).

## Why
Just above audible; wideband enough to chirp (matched-filter processing gain); MEMS mics retain sensitivity there; dual-use for audio/voice beamforming. 5×5−1 gives a symmetric 2D aperture with monostatic center TX.

## Consequences / what this forecloses
A 10 mm MA40S4S does not fit a 6.9 mm center cell — TX must be off-board (D007), rear-mounted through a hole, an SMD transducer, or pitch widened to ~8 mm. Sub-decision left open for P3.
