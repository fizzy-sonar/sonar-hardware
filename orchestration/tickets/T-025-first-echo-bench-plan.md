---
id: T-025
title: First-echo acceptance and executable coupon bench plan
status: ready
phase: P5
tier: mid
priority: 2
assignee:
depends_on: []
needs_human: true
created: 2026-09-05
updated: 2026-09-05
---
## Goal
Prepare REVIEW-2026-09-05's concrete first-echo bench proposal within existing
decisions. No purchases, requirement changes or decision ratifications.

## Definition of Done
- Propose measurable demo target/range/accuracy/repeat-count/update-rate and saved
  raw evidence. Distinguish range resolution from angular separation, and first
  echo from calibrated T-016 microphone release.
- Specify coupon-to-capture wiring, four-channel mapping into actual firmware,
  clock/decimation configuration and window for both candidates.
- Concrete wideband TX part/drive proposal with primary-source ratings and an
  output measurement plan; MA40S4S stays disabled at 12 V (R7).
- Identify calibrated mic, scope, source, fixture, adapter and host access;
  refresh exact availability and complete cost, including access alternatives.
- Executable acquisition-to-dataset procedure, not YAML alone; coordinate code
  with T-023/T-024. State exactly what Joshua must operate/provide.
- Present any decision amendments for Joshua; do not weaken the release gate.

## Verification
Dry-run commands/schema with explicitly synthetic data; calculate target window
and sample rate at each candidate clock. End at review for Joshua's choices.

## Log
- 2026-09-05 codex/T-019: created. Pico default 5.333 ms window needs revision
  or a defined delayed-acquisition sequence for a 1–3 m demonstration.
