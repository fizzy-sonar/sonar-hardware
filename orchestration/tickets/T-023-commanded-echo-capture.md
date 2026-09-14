---
id: T-023
title: Integrated commanded TX and USB-independent snapshot capture
status: in-progress
phase: P5
tier: top
priority: 1
assignee: codex
depends_on: []
needs_human: false
created: 2026-09-05
updated: 2026-09-14
---
## Goal
Resolve REVIEW-2026-09-05 R3/R4 through sonar_top. Coordinate ownership with T-020.

## Definition of Done
- Snapshot acquisition survives absent/stalled FT232H and a delayed user trigger;
  streaming overflow remains explicit and recoverable.
- Minimal arm/fire/read/status control on existing interfaces; real TX event
  sample counter, waveform identity, explicit capture boundary and errors.
- Manufacturer-verified driver wake/settle and fault handling. TX remains idle
  until commanded within the selected part limits. No MA40S4S at 12 V; D013
  remains proposed until Joshua ratifies.
- Top-level behavioral tests cover two consecutive measurements, startup,
  absent FT clock, blocked TXE, reconnect, reset and invalid TX configuration.
- Coordinate packet/host contract with T-024. T-020 retains synthesis, timing/CDC,
  utilization and physical gates; do not claim these from simulation.

## Verification
Full gateware suite plus top-level behavioral tests. Convert the T-019 starvation
probe into desired-behavior coverage; prove TX timestamp survives host parsing.

## Log
- 2026-09-05 codex/T-019: created. TX is tied off and fallback stops on main FIFO
  overflow. Simulation work is not blocked on a Vivado purchase.
- 2026-09-13 codex: claimed for Joshua's pre-hardware readiness request. First
  close USB-induced snapshot starvation with behavioral regression coverage;
  audit readout/build/procurement gates and record an actionable purchase and
  bring-up sequence. No hardware is available. Full commanded-TX integration,
  implementation reports and physical evidence must remain explicitly open
  unless actually delivered. T-020 keeps Vivado/physical ownership.

- 2026-09-13 codex close-out: repaired acquisition tap independence and FIFO
  reset/initialization for absent FT clock; four actual-top regressions added.
  Current purchase/bring-up report: docs/pre-hardware-readiness.md; FT232H
  adapter/EEPROM audit: docs/ft232h-bench-preflight.md. FPGA/USB reliability is
  Joshua's clarified concern. No hardware is available. Ticket remains
  in-progress: arm/fire/read/status, driver wake/fault/limits, real TX sample
  timestamp and host contract still required. Next: add the actual control and
  event metadata path without changing the approved architecture.

  Verification (real output excerpts; full logs in
  orchestration/review/evidence-2026-09-13-t023/):

```text
$ make -C gateware test
PASS SRAM snapshot full 512 KiB window bytes=524334 bit-exact
PASS top snapshot 3072000 Hz FT_PRESENT=0: delayed/two captures, SRAM/UART counter+CRC, reconnect/reset, TX idle
PASS top snapshot 3072000 Hz FT_PRESENT=1: delayed/two captures, SRAM/UART counter+CRC, reconnect/reset, TX idle
PASS top snapshot 4800000 Hz FT_PRESENT=0: delayed/two captures, SRAM/UART counter+CRC, reconnect/reset, TX idle
PASS top snapshot 4800000 Hz FT_PRESENT=1: delayed/two captures, SRAM/UART counter+CRC, reconnect/reset, TX idle
PASS sonar_top <-> XDC port bijection: 28 ports / 73 bits exact (active get_ports only, DNP block excluded)
exit=0; total PASS lines=21

$ vvp build/t023-mutation   # old USB-gated tap, negative control
FATAL: gateware/sim/tb_top_snapshot.sv:122: snapshot length 48, want 240
       Time: 5891855200  Scope: tb_top_snapshot.capture
exit=1 (expected)

$ PYTHONPATH=host uv run --offline python -m unittest discover -s tests -v
----------------------------------------------------------------------
Ran 5 tests in 0.564s

OK

$ PYTHONPATH=host uv run --offline python orchestration/review/evidence-2026-09-05/probe_host.py
REPRODUCED: transient empty read discards subsequent valid data: stream ended after 0 frames; requested 1
REPRODUCED: chunked vs whole decimator max difference=0.233102

$ bash scripts/check.sh
SUMMARY: all invoked KiCad commands completed successfully.
exit=0 (baseline violations accepted; not main-board release)

$ verify T-022 source/export SHA256 manifests
  {"match": 66, "missing": 0, "changed": 0}
```

- 2026-09-13 inventory follow-up: Joshua owns a DE10-Lite from school. Checked
  Terasic resources, MAX 10 DDR support and Quartus availability against primary
  sources, and inspected the current Xilinx/Cmod wrappers. Feasible bench
  alternative, not a drop-in target. D014 proposed; T-027 port blocked pending
  adoption. Pause Cmod procurement. No RTL changed, no Quartus build/pin audit
  or physical verification performed. Document links and git diff --check pass;
  earlier tests remain applicable to unchanged RTL, not to a DE10-Lite port.

- 2026-09-14 Vivado/branch follow-up: Joshua prefers Vivado and has a Raspberry
  Pi, can run a local VM or arrange Linode. Retained ratified D012/Cmod; D014
  remains unadopted and T-027 blocked/not selected. Added
  `docs/vivado-validation.md`: supported x86 Linux host, current free BASIC
  license scope, 8 GB cloud sizing, source archive/hashes, exact existing batch
  entry point, evidence retrieval and incomplete I/O/timing/CDC signoff gates.
  No Vivado run, VM/account creation or remote transfer performed. Existing
  simulation/host evidence is still applicable: source SHA256 manifest 44/44
  matches; local Markdown links 9/9 and `git diff --check` pass. No RTL, XDC or
  KiCad changes in this follow-up. Full tests were not repeated for documentation
  changes; prior 21/21 gateware and 5/5 host outcomes are retained with their
  physical-validation limits. Branch was required by orchestration/README step
  4; main was an ancestor (0 main-only / 2 branch-only commits before this
  follow-up). Close out with a local fast-forward of the committed checkpoint
  onto main, preserving the user's uncommitted sonar.kicad_pro edit. T-023
  remains in progress; implementation execution belongs to T-020 once SSH and
  Vivado are available, and commanded-TX work can continue independently.

- 2026-09-14 cloud-pricing follow-up: Joshua asked about Dedalus credits and
  comparable services, then requested project-specific pricing assumptions.
  Added `docs/cloud-compute-pricing.md` with source-linked rates, computed
  72-hour/monthly cases, recurring versus introductory credits, storage quotas
  and an unsent Dedalus email. Key boundary: no provider has run Vivado for us;
  credits do not resolve quotas, x86/OS support or licensing. No accounts,
  messages, uploads or spend. Arithmetic computed with Python; documentation
  checks recorded in the session journal. RTL/constraints unchanged.
