---
id: D008
title: EDA: KiCad default, gated by a code-first spike
status: ratified
date: 2026-08-25
author: claude (fable) — architecture review
---
## Decision
KiCad remains the working tool, with kicad-cli ERC/DRC/PDF/BOM automation in CI. A bounded, non-blocking spike (T-005) ports the power tree + one AFE tile to diodeinc/pcb (Zener) and issues a go/no-go on doing v1 code-first BEFORE P2 starts. If go, this decision flips via a superseding decision.

## Why
Layout is KiCad either way; Joshua reviews visually; pre-1.0 tool risk lands on his energy budget. But P2 is nearly a rewrite and agents work better in code — the question deserves evidence, not taste.

## Amendment 2026-08-25 (go-ahead)
KiCad confirmed for v1. The T-005 spike is OPTIONAL and NON-GATING — P2 no longer
waits on it; run it only if spare agent capacity exists.

## Consequences / what this forecloses
P2 tickets must not start until T-005 reports (or is explicitly skipped by Joshua at CP-A).
