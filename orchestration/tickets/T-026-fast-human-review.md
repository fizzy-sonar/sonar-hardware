---
id: T-026
title: Five-minute decision review and FPGA readout proof plan
status: in-progress
phase: P5
tier: top
priority: 1
assignee: codex
depends_on: [T-019, T-022]
needs_human: false
created: 2026-09-06
updated: 2026-09-06
---
## Goal
Joshua has almost no review time and explicitly requested cheaper subagents for
artifacts, an easier review surface, and a candid discussion of FPGA/core risks.
Reduce human review to consequential decisions, not technical rubber-stamping.

## Scope and delegation
- Top-tier coordinator: independently assess FPGA evidence, prioritize next steps,
  integrate a decision-first review surface, verify accuracy and handoff.
- Cheap artifact subtask A: rerun existing readout tests/probes and inventory
  evidence with source references; no novel HDL or timing sign-off.
- Cheap artifact subtask B: short decision brief + risk/proof data from current
  sources; no architecture changes or decision ratification.
- Cheap artifact subtask C: standalone explanatory SVGs/printable review assets;
  no website checkout or hosting edits by subagents.
- Preserve user edits; no hardware/code fixes, purchases, external messages or
  account signups. Any remote review publication remains private and contains
  only curated review material, not the whole repository.

## Definition of Done
- A 60-second summary and <=5-minute review path, no more than three human
  questions, with explicit recommended next steps and deferred decisions.
- FPGA readout diagram, measured/calculated/simulated/unverified distinctions,
  known blockers and executable proof ladder, linked to evidence.
- Reuse existing actual artifacts; full review remains accessible as appendix.
- Readable responsive/printable review, saved/exportable human notes with no
  automatic approvals or ticket mutations; structural/link/content tests.
- Verify required repo checks, log evidence, update STATUS/journal, commit.

## Log
- 2026-09-06 codex: claimed at Joshua's request. Cheaper agents handle bounded
  artifacts; coordinator retains engineering judgement. T-023/24/25 not implemented.
