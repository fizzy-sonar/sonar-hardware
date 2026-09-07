---
id: T-026
title: Five-minute decision review and FPGA readout proof plan
status: done
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
- Readable responsive/printable, read-only review; answers stay in the existing
  conversation, with no copy/paste workflow or forms (Joshua's explicit update).
  No automatic approvals or ticket mutations; structural/link/content tests.
- Verify required repo checks, log evidence, update STATUS/journal, commit.

## Log
- 2026-09-06 codex: claimed at Joshua's request. Cheaper agents handle bounded
  artifacts; coordinator retains engineering judgement. T-023/24/25 not implemented.
- 2026-09-06 codex: three Luna/medium artifact agents supplied fresh probes,
  concise brief, and two factual SVGs. Root reviewed source and integrated a
  static decision-first page. Joshua rejected copying: removed all new forms,
  JavaScript and export workflow; answers stay in chat, one immediate hardware
  question. No HDL/design changes or approvals.
- Verification: gateware 17/17 PASS; pinned Python 3.14.2 / NumPy 2.3.2 host
  unittest 5/5 PASS; starvation and host probes reproduce known defects.
  `scripts/check_fast_review.py`: local 20 / portable 19 references resolve,
  one question; missing/stale source-hash negative checks PASS. Ruff checks and
  formatting PASS; shell syntax and diff whitespace PASS. Full appendix
  generator/checker: 8 steps, 11 historical review items, 71 images, 158 links,
  18 required assets PASS. `bash scripts/check.sh` exits 0 outside sandbox,
  accepting existing ERC/DRC baselines, not declaring the main PCB clean.
- Publishing: existing new owner-only Site registered once; registry persists
  at `orchestration/review/site/.openai/hosting.json`. Only curated static output
  is in the separate ignored source checkout. External source push failed in
  sandbox (DNS), then permission review denied escalation because payload and
  destination lacked explicit authorization. Stopped without workaround; no
  source uploaded, version saved or Site deployed. User informed and approval
  requested asynchronously. Optional remote publication remains on hold; local
  deliverable is complete and does not require it.
- Closeout: source hash coverage expanded to all current gateware/host/test
  code, constraints/build scripts, probes and dependency lock; no design source
  changed between tests and hashing. Page verifies snapshot freshness. Root
  implementation commit `15eb055`; no root-repository push. Existing KiCad
  used-designator reorder preserved. Browser visual QA not performed (not
  requested); SVG XML and page structure/link checks pass.
