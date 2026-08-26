---
id: T-005
title: EDA spike: diodeinc/pcb (Zener) go/no-go
status: review
phase: P1
tier: mid        # optional spike; tool evaluation
priority: 5
assignee: codex/terra-t005
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-26
---
## Goal
Port `power_supply` + one 4-mic AFE tile to diodeinc/pcb. Judge: (a) BOM coverage for our exact parts, (b) generated KiCad netlist/layout quality, (c) does hand-edited placement survive a `pcb layout` re-run, (d) ERC-equivalent checks, (e) reviewability for Joshua (can he read it in 10 min?). Optionally repeat 1 tile in atopile for comparison (its JLC part picker is relevant to D009).

## Context
Decision D008 — this ticket IS the gate. Spike lives in `spikes/eda-zener/`, never merged into the main design. Time-box: ~2 agent-days.

## Definition of Done
`spikes/eda-zener/REPORT.md` with a clear GO / NO-GO and evidence for (a)–(e). If GO: draft superseding decision D0xx for Joshua.

## Verification
Report exists; build commands in it actually run; verdict stated in the first line.

## Log
- 2026-08-25 claude (fable): demoted to OPTIONAL/NON-GATING per D008 amendment — P2 does not wait on this.
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-26 codex/terra-t005: spike executed on branch agent/T-005-eda-spike; deliverable
  `spikes/eda-zener/REPORT.md` — **VERDICT: NO-GO for v1** (verdict in first line of report).
  Evidence: `pcb import` on power_supply.kicad_sch → empty 9-line Board() stub (0 components)
  + `Error: Part group 12V has PCB footprints but no schematic symbol instances`; on
  quad_rx_pre_amp.kicad_sch → `Error: Failed to parse KiCad netlist — Ambiguous KiCad component
  identities` (multi-instance hierarchical sheet unsupported: refdes C177/MK33/R352/R356/TP98
  each map to 4 instance paths); on sonar.kicad_pro → `Error: KiCad DRC failed — kicad-cli
  execution failed` (importer hard-depends on kicad-cli, which SIGABRTs in sandbox).
  `pcb build/info/bom/test/sync` all fail `Operation not permitted (os error 1)` — root-caused
  to sandbox denying hardlinks (`ln` → EPERM) and toolchain-dir writes (probe → EPERM); pcbc
  vendors deps via hardlinks. Network blocked (DNS fails); no registry cache on machine →
  BOM/component-registry criteria (a) evaluable only from bundled stdlib: generics cover
  R/C/L/FB/crystal/LED/TVS but NOT AP63301WU-7/quad op-amp/our ICs; OperationalAmplifier is
  deprecated, Single-only. Hand-authored port in `spikes/eda-zener/hand-port/` (pcb.toml,
  ap63301.zen, power_supply.zen, rx_preamp_channel.zen) passes `pcb fmt` (syntax only — NEVER
  built/evaluated). (b)(c)(d-runtime) have NO runtime evidence — sandbox-blocked, not faked.
  Status → review (not done): per "unverified work is not done", the NO-GO rests on
  offline-decisive evidence (importer + registry architecture) but build/layout/BOM were
  never executable; orchestrator can confirm in 30 min on an unsandboxed+networked host:
  `cd spikes/eda-zener/hand-port && pcb build .` then close. Git: sandbox blocks worktree
  .git writes — ALL changes left uncommitted for the orchestrator; no push/merge attempted.
