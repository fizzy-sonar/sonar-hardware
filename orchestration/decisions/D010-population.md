---
id: D010
title: Population: fully populate; validate per 8-ch group in software
status: ratified
date: 2026-08-25
author: claude (fable) — architecture review
---
_Ratified 2026-08-25: Joshua, "ok. lets go with that" (blanket go-ahead for the standing defaults + the D012 platform ladder)._

## Decision
Assemble all 24 channels on the first run. 'Single row first' is a software/bring-up strategy (validate one 8-channel electrical group at a time), not a partial-assembly strategy.

## Why
Marginal parts cost of the extra 16 channels is <$100 — less than a second assembly setup.

## Consequences / what this forecloses
Bring-up runbook (P5) is written per-group; a bad group is diagnosable without blocking the others.
