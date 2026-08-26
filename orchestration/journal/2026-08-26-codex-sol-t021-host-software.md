# 2026-08-26 — codex/sol-t021: T-021 host software

## What happened
- Reopened the branch's stale T-021 closure after auditing the existing code: the
  prior implementation only used `assert`, had no robust SNR1 streaming parser, no
  storage path, no real geometry-aware beamforming, and tests that proved only a toy
  single-channel convolution.
- Replaced the host package with typed error handling, strict SNP1 snapshot parsing,
  strict SNR1 streaming-header parsing, buffered chunked transport ingestion, and
  explicit sticky-overflow / incomplete-stream surfacing.
- Added raw capture storage (`.npy`) and a channel ring buffer, plus a full
  multichannel DSP reference: CIC + FIR decimation for 24 channels, odd-edge
  half-period correction, per-channel gain calibration, chirp generation, matched
  filtering, and delay-and-sum beamforming for the documented 5x5-minus-center array.
- Added a deterministic synthetic point-target fixture that generates raw packed PDM,
  then verifies end-to-end recovery of range and bearing with noise.
- Added a runnable demo that emits an SVG plot artifact and `.npy` capture, plus an
  in-memory synthetic ingest benchmark against the 9.216 MB/s contract.

## Verification
- `python3 -m pytest -q` could not run in this worktree because `pytest` is not
  installed in the local Python 3.13 environment.
- `PYTHONPATH=host python3 -m unittest discover -s tests -q` passed: 5 tests.
- `python3 host/demo.py` produced `host/artifacts/t021-demo.svg` and reported
  `truth_range_m=4.200`, `estimated_range_m=4.202`, `truth_bearing_deg=12.00`,
  `estimated_bearing_deg=10.00`.
- `python3 host/benchmark.py` reported `4042.582 MB/s` versus the `9.216 MB/s`
  contract in a synthetic in-memory ingest loop.
- `python3 -m py_compile host/sonar_host/*.py host/demo.py host/benchmark.py`
  passed.
- `git diff --check` passed.

## Remaining limits
- Physical FT232H/libusb I/O remains untested.
- The benchmark is synthetic and in-memory by design; it verifies the software ingest
  path shape, not USB hardware behavior.
