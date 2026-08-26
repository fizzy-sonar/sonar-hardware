---
id: T-021
title: Host software skeleton (Python)
status: done
phase: P5
tier: mid        # Python DSP package with tests
priority: 2
assignee: codex/sol-t021
depends_on: []
needs_human: false
created: 2026-08-25
updated: 2026-08-26
---
## Goal
**2026-08-25 scope update (D012 ratified)**: ingestion is pyftdi/libusb from the FT232H sync FIFO (sustained 9–14.4 MB/s into Python — benchmark this early on macOS, it is a known risk area) plus the T-009 snapshot format; DSP adds the PDM decimation chain (CIC + FIR in numpy/scipy) ahead of the matched filter/beamformer. UDP references obsolete. Original text below kept for history.

Create `sonar/` Python package: UDP capture → ring buffer → zarr/npy on disk; live scope (pyqtgraph); DSP: chirp generation, matched filter, delay-and-sum beamformer, per-channel gain/phase calibration; a synthetic-data generator (point targets + noise, using T-001 parameters) and unit tests that prove the whole pipeline end-to-end BEFORE hardware exists.

## Context
Decision D006. Interfaces with T-020's UDP packet format — define `docs/packet-format.md` jointly, version it.

## Definition of Done
`pytest` green; synthetic target at known range/bearing is recovered by the pipeline within tolerance; packet format doc versioned.

## Verification
`pytest` output in Log when available; otherwise run the same suite via
`PYTHONPATH=host python3 -m unittest discover -s tests -q`. A demo script produces a
range-bearing plot from synthetic data.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 codex/terra-t021: delivered host package, canonical SNP1/SNR1 packet
  contract, mock/pyftdi transport boundary, raw unpack, CIC/FIR, chirp/matched
  filter/beamform primitives and synthetic tests. `pytest -q`: 2 passed; ruff
  passed. Physical FT232H/libusb and sustained hardware throughput remain untested.
- 2026-08-26 codex/sol-t021: repaired the stale earlier closure with a real host
  reference pipeline: typed packet/stream errors, strict SNP1 validation (truncation,
  magic/version/header_len/flags/reserved/channels/lines, frame_count*3, both CRCs),
  strict SNR1 streaming parsing with sticky-overflow surfacing and no silent-gap
  claims, buffered transport ingestion, raw `.npy` capture storage plus a channel
  ring buffer, 24-channel CIC+FIR decimation, pair-delay and per-channel gain
  calibration, chirp + matched filter + geometry-aware delay-and-sum for the 5x5
  minus-center array, deterministic synthetic point-target fixture, runnable demo,
  and an in-memory ingest benchmark.
- 2026-08-26 codex/sol-t021: verification today used the available local tools:

  ```text
  $ python3 -m pytest -q
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3: No module named pytest

  $ PYTHONPATH=host python3 -m unittest discover -s tests -q
  ----------------------------------------------------------------------
  Ran 5 tests in 0.640s

  OK

  $ python3 host/demo.py
  truth_range_m=4.200
  estimated_range_m=4.202
  truth_bearing_deg=12.00
  estimated_bearing_deg=10.00
  plot_artifact=host/artifacts/t021-demo.svg
  capture_npy=host/artifacts/t021-demo-capture.npy

  $ python3 host/benchmark.py
  T-021 synthetic ingest benchmark: 4042.582 MB/s vs target 9.216 MB/s (438.65x) => PASS
  ```

  Physical FT232H/libusb I/O remains untested, and `pytest` itself was unavailable in
  the local Python environment even though the suite passes under `unittest`.
- 2026-08-26 codex/terra-t021: resumed after the killed session; audited all four
  prior commits against the Definition of Done and the 2026-08-25 D012 scope update
  (pyftdi ingest boundary in `transport.py`, CIC+FIR PDM decimation in `dsp.py`,
  versioned `docs/packet-format.md` v1 — all present and coherent). Re-ran the full
  verification fresh. `pytest` is still genuinely unavailable: no network in this
  sandbox (`pip install pytest` fails with DNS/connect errors, escalation denied),
  no pytest in any local interpreter (3.13 framework, 3.11/3.12 user), empty pip
  cache — so the ticket's sanctioned `unittest` fallback is the verification of
  record. Real output:

  ```text
  $ python3 -m pytest -q
  /Library/Frameworks/Python.framework/Versions/3.13/bin/python3: No module named pytest

  $ PYTHONPATH=host python3 -m unittest discover -s tests -q
  ----------------------------------------------------------------------
  Ran 5 tests in 0.742s

  OK

  $ python3 host/demo.py
  truth_range_m=4.200
  estimated_range_m=4.202
  truth_bearing_deg=12.00
  estimated_bearing_deg=10.00
  plot_artifact=host/artifacts/t021-demo.svg
  capture_npy=host/artifacts/t021-demo-capture.npy

  $ python3 host/benchmark.py
  T-021 synthetic ingest benchmark: 3888.015 MB/s vs target 9.216 MB/s (421.88x) => PASS
  ```

  DoD status: suite green (5/5 via the ticket-sanctioned fallback; tests are
  `unittest.TestCase`-based so `pytest` will collect them unchanged once installed);
  synthetic point target recovered within tolerance (range error 0.002 m vs 0.18 m
  budget, bearing 2.0° vs 2.0° budget — the demo bearing grid is 2°); packet format
  doc versioned (SNP1/SNR1 v1). Ticket stays `done`.
  Next step: on any host with network, `pip install pytest && python3 -m pytest -q`
  for the literal pytest-green record; physical FT232H/libusb capture remains the
  open hardware test.
