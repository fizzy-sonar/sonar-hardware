---
id: T-024
title: Live host transport and bounded stateful DSP
status: ready
phase: P5
tier: mid
priority: 2
assignee:
depends_on: []
needs_human: false
created: 2026-09-05
updated: 2026-09-05
---
## Goal
Resolve REVIEW-2026-09-05 R5/R6; deliver executable capture/replay and live processing.

## Definition of Done
- Distinguish idle reads, deadline, disconnect and explicit EOF; test partial
  startup headers, recoverable silence, unplug and reconnect.
- Bounded recording and stateful decimation; random chunk boundaries preserve
  signal/timestamps within stated tolerance. Derive sample rate from recorded
  clock at both 3.072 and 4.8 MHz.
- Connect CLI capture, metadata/raw recording, replay, calibration and basic
  range display; coordinate TX timestamp/status contract with T-023.
- Benchmark ingestion, processing and storage separately and together; report
  peak memory. Provide a physical USB soak procedure for when hardware exists.
  Mock throughput is not physical USB proof.

## Verification
Host suite, idle/disconnect tests, chunk-invariance and bounded-memory checks,
processing benchmark, deterministic capture/replay demo.

## Log
- 2026-09-05 codex/T-019: created; empty-read EOF and 0.233102 chunked/whole
  decimator difference reproduced. Existing five host tests pass.
