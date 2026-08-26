---
id: T-021
title: Host software skeleton (Python)
status: done
phase: P5
tier: mid        # Python DSP package with tests
priority: 2
assignee: codex/terra-t021
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
**2026-08-25 scope update (D012 ratified)**: ingestion is pyftdi/libusb from the FT232H sync FIFO (sustained 9–14.4 MB/s into Python — benchmark this early on macOS, it is a known risk area) plus the T-009 snapshot format; DSP adds the PDM decimation chain (CIC + FIR in numpy/scipy) ahead of the matched filter/beamformer. UDP references obsolete. Original text below kept for history.

Create `sonar/` Python package: UDP capture → ring buffer → zarr/npy on disk; live scope (pyqtgraph); DSP: chirp generation, matched filter, delay-and-sum beamformer, per-channel gain/phase calibration; a synthetic-data generator (point targets + noise, using T-001 parameters) and unit tests that prove the whole pipeline end-to-end BEFORE hardware exists.

## Context
Decision D006. Interfaces with T-020's UDP packet format — define `docs/packet-format.md` jointly, version it.

## Definition of Done
`pytest` green; synthetic target at known range/bearing is recovered by the pipeline within tolerance; packet format doc versioned.

## Verification
`pytest` output in Log; a demo script produces a range-bearing plot from synthetic data.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 codex/terra-t021: delivered host package, canonical SNP1/SNR1 packet
  contract, mock/pyftdi transport boundary, raw unpack, CIC/FIR, chirp/matched
  filter/beamform primitives and synthetic tests. `pytest -q`: 2 passed; ruff
  passed. Physical FT232H/libusb and sustained hardware throughput remain untested.
