# 2026-08-27 — codex/sol-t020: resume audit

## What happened

- Followed the session ritual and resumed the already assigned top-tier T-020.
- Confirmed the supposedly uncommitted T-017 and T-020 work is already integrated
  on `main`; the only pre-existing dirty file is
  `sonar-v1-pcb/sonar.kicad_pro`, which was not touched.
- Re-ran `cd gateware && make clean && make test` from current `main`: all 17
  checks passed. This includes both portable and functional-Xilinx sampler paths
  at both rates (checksum `cff870`), 6,536 TX half-cycles with zero duty-bound
  violations, the full 512 KiB SRAM snapshot round-trip (524,334 bytes bit-exact),
  and the exact `sonar_top`/XDC bijection (28 ports / 73 bits).
- Confirmed the T-016 lock refresh is already landed:
  `UV_CACHE_DIR=/tmp/sonar-uv-cache uv lock --check --offline` resolved six
  packages and exited zero. The default cache path failed only because the
  sandbox cannot write `~/.cache/uv`.
- Repaired stale integration and verification claims in `STATUS.md`; no design
  source changed.

## Live blockers / exact next step

The local host is ARM64, has no `vivado` executable, and exposes no Cmod, Digilent,
FTDI/FT232, Raspberry, or Pico device in the macOS USB inventory. T-020 therefore
stays `in-progress`. Joshua must choose/provide the x86 Vivado host in T-007 and
the dev hardware before the remaining batch synthesis, UNISIM/timing/CDC/BRAM/
SRAM-I/O proofs, and physical FT232H/UART demos can run. The broader board path is
also waiting on Joshua's CP-B/CP-BM decisions documented in
`orchestration/review/JOSHUA-REVIEW-PLAN.md`.
