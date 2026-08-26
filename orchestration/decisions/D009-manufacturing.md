---
id: D009
title: Manufacturing: JLCPCB full turnkey, LCSC-first parts
status: ratified
date: 2026-08-25
author: claude (fable) — architecture review
---
_Ratified 2026-08-25: Joshua, "ok. lets go with that" (blanket go-ahead for the standing defaults + the D012 platform ladder)._

## Decision
JLCPCB fabrication + assembly; part selection prefers LCSC stock; unstocked parts (likely the mics) via JLC Global Parts pre-order. No home soldering, no consignment shipping. PCBWay consignment is the fallback.

## Why
Joshua has no bench assembly equipment; turnkey removes the entire logistics problem. LCSC-first constrains the BOM early, when it's cheap.

## Consequences / what this forecloses
Every part in the P2 BOM carries an LCSC number or an explicit Global-Parts/consign flag (T-014).
