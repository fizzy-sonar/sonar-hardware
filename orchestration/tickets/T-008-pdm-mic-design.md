---
id: T-008
title: PDM mic selection + RX electrical design
status: done
phase: P1
tier: top        # PDM timing/skew analysis, clock-tree design from datasheets
priority: 1
assignee: codex/sol-t008
depends_on: [T-002]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
---
## Goal
Per D011: pick the PDM ultrasonic mic (from T-002's matrix) and design the digital RX:
L/R data-line pairing map (24 mics → ~12 data lines), clock-tree topology (fanout,
buffering, skew tolerance at ~4.8 MHz, ultrasonic-mode clock requirements per
datasheet), mic supply rail + per-mic decoupling/filtering, PCB acoustic port rules.
Define the mic-tile schematic block that T-010 instantiates.

## Context
D011 (ratified). Candidates: ICS-41350/41352, SPH0641LU4H (lifecycle check!), T5838.
The mic's clock frequency and edge discipline set the T-020 CIC input contract —
write `docs/pdm-capture-contract.md` jointly with T-020 (clock rate, which edge each
mic drives, decimation ratio, expected output rate).

## Definition of Done
Provisional electrical MPN baseline chosen with lifecycle/electrical/acoustic
rationale; pairing + clock-tree design documented; reviewable candidate mic-tile
block drafted; `pdm-capture-contract.md` v1 committed; quantitative physical
selection thresholds and the T-016 MPN/footprint release dependency recorded. Per
the independent review, T-008 completion does not itself release a production MPN.

## Verification
Datasheet numbers cited for: ultrasonic-mode clock range, current draw (×24), data
setup/hold vs FPGA input timing at chosen clock. T-020 owns the executable
cross-check and now requires 3.072/4.8 MHz parameter tests; its testbench does not
yet exist, so T-008 records exact constants without claiming a completed TB run.

## Pairing decision (2026-08-25 discussion with Joshua)
Default: L/R pairing, 24 mics -> 12 data lines (the mics' designed stereo mode;
FPGA samples via IDDR). Known deterministic skew: paired mics sample half a PDM
period apart = 104-163 ns = ~56 um acoustic-path equivalent = ~1-2 deg @ 32 kHz —
negligible vs calibration tolerances, and exactly cancellable with a half-sample
shift on odd channels pre-decimation (document in the capture contract).
Alternative on the table: UNPAIRED 24 data lines (Cmod pin budget allows: ~39/52
pins incl. Ethernet provision) — zero skew, single-edge sampling, +12 pins/traces.
T-008 owner: pick one, justify in the Log; electrical care points if paired:
tri-state hand-off gap per datasheet, optional weak pull on shared lines.

## Log
- 2026-08-25 claude (fable): created per D011 (replaces T-003/T-004).
- 2026-08-25 codex/sol-t008: selected current-portfolio SPH0641LU4H-1 as the
  provisional electrical baseline at its manufacturer-characterized 3.072 MHz
  Ultrasonic Mode point. Chose paired
  SELECT-low/SELECT-high capture (12 DATA lines) and defined the fixed 162.760 ns
  odd-channel correction. Designed a 3.3 V mic domain with per-mic 100 nF C0G,
  CDCLVC1112PWR 1:12 fanout, returned sampling clock, startup sequencing, source
  termination footprints, and acoustic-port rules. `docs/pdm-rx-design.md` is the
  reviewable T-010 schematic specification; no KiCad file was edited because the
  KiCad-open state is unknown.
- 2026-08-25 codex/sol-t008: current/timing results: 24 microphones are 20.28 mA
  typical / 24.00 mA maximum only at the datasheet's 1.8 V test condition; the
  chosen legal 3.3 V point has no published current maximum, so the design allocates
  >=100 mA and carries this as an explicit measurement item. With a 0.500 ns board
  skew allocation, SPH0641 gives 122.202 ns setup and 2.122 ns hold margin against
  XC7A35T-1 direct ILOGIC/package numbers. Raw traffic is 73.728 Mb/s (9.216 MB/s);
  host decimation by 24 gives 128 ksample/s/channel. SPH DATA-to-LVCMOS33 DC margins
  are 0.685 V high / 0.350 V low at the stated worst points.
- 2026-08-25 codex/sol-t008: committed `docs/pdm-capture-contract.md` v1 constants
  for T-020/T-009/T-021. The FT232H path remains raw/no-FPGA-DSP per the later D012
  amendment; optional DNP RMII is the only future in-fabric CIC consumer. T-020's
  testbench does not yet exist, so the contract supplies an explicit assertion list
  rather than claiming a nonexistent cross-run.

Verification (exact output):

```text
$ python3 analysis/pdm_rx_timing.py
Sonar v1 PDM RX electrical checks
  SPH0641LU4H-1: half-period=162.760 ns, setup margin=122.202 ns, hold margin=2.122 ns
  ICS-41352 alternate: half-period=104.167 ns, setup margin=53.609 ns, hold margin=4.122 ns
  24 microphones at 1.8 V datasheet condition: 20.28 mA typ
  24 microphones at 1.8 V datasheet condition: 24.00 mA max
  CDCLVC1112 known internal current at 3.3 V: <= 10.73 mA (10 mA static max + calculated CPD term; load current excluded)
  Known reference subtotal: 34.73 mA (not a 3.3 V rail maximum)
  Clock-buffer duty range from 180 ps pulse-skew limit: 49.945% to 50.055%
  Stream: 73.728 Mb/s = 9.216 MB/s; decimate-by-24 => 128000 samples/s/channel
  Paired-edge offset: 162.760 ns = 55.83 um at 343 m/s = 1.875 deg at 32 kHz
  SPH data -> Cmod LVCMOS33 DC margins: HIGH=0.685 V, LOW=0.350 V

$ ruff check analysis/pdm_rx_timing.py
All checks passed!

$ ruff format --check analysis/pdm_rx_timing.py
1 file already formatted

$ python3 -m py_compile analysis/pdm_rx_timing.py
[no output; exit 0]

$ git diff --check
[no output; exit 0]

$ git diff --cached --check
[no output; exit 0]
```

- 2026-08-25 codex/sol-t008 independent-review repair: result was **PASS WITH
  REQUIRED FIXES**. The first commit incorrectly described SPH as a release while
  deferring a qualitative two-coupon bake-off with no authorized pre-CP-C purchase/
  bench path. SPH is now explicitly only the provisional electrical baseline.
  Added quantitative T-001/D011 acoustic, spread, timing, power, port, overload,
  source, and fallback rules; created T-016 (`needs_human: true`) and CP-BM;
  blocked T-010/T-014/CP-C on the release while leaving T-011/T-012/T-013 and P5
  executable. No source, order, spend, measurement, MPN release, or KiCad edit is
  claimed. Remaining primary-evidence gaps are SPH 3.3 V maximum current, clock-
  input capacitance/load, and allowable PCB-port misregistration.

Independent-review repair verification (exact output):

```text
$ python3 analysis/pdm_rx_timing.py
Sonar v1 PDM RX electrical checks
  SPH0641LU4H-1: half-period=162.760 ns, setup margin=122.202 ns, hold margin=2.122 ns
  ICS-41352 alternate: half-period=104.167 ns, setup margin=53.609 ns, hold margin=4.122 ns
  24 microphones at 1.8 V datasheet condition: 20.28 mA typ
  24 microphones at 1.8 V datasheet condition: 24.00 mA max
  CDCLVC1112 known internal current at 3.3 V: <= 10.73 mA (10 mA static max + calculated CPD term; load current excluded)
  Known reference subtotal: 34.73 mA (not a 3.3 V rail maximum)
  Clock-buffer duty range from 180 ps pulse-skew limit: 49.945% to 50.055%
  Stream: 73.728 Mb/s = 9.216 MB/s; decimate-by-24 => 128000 samples/s/channel
  Paired-edge offset: 162.760 ns = 55.83 um at 343 m/s = 1.875 deg at 32 kHz
  SPH data -> Cmod LVCMOS33 DC margins: HIGH=0.685 V, LOW=0.350 V

$ python3 -c '<assert T-001 baseline and +3.00 dB release values>'
T-001 25 kHz person range: baseline=20.180 m; +3.00 dB penalty=18.905 m
T-001 10 m margins after +3.00 dB: person=24.09 dB; small-target=4.1 dB

$ ruff check analysis/pdm_rx_timing.py analysis/link_budget.py
All checks passed!

$ ruff format --check analysis/pdm_rx_timing.py analysis/link_budget.py
2 files already formatted

$ python3 -m py_compile analysis/pdm_rx_timing.py analysis/link_budget.py
[no output; exit 0]

$ <ticket frontmatter/dependency assertions>
Orchestration gate audit passed: T-016 ready/needs_human; T-010, T-014, T-015 depend on T-016; T-011/T-012/T-013 ready.

$ git diff --check
[no output; exit 0]

$ git diff --cached --check
[no output; exit 0]
```

- 2026-08-25 codex/sol-t008 final bounded review repair: the remaining reviewer
  defect was undefined `U95`. `docs/pdm-rx-design.md` and T-016 now carry identical
  executable definitions: fixed SPH/ICS pairing, hierarchical reseat/unit/coupon
  medians and maximum deviations, linear addition with the reported <=1.0 dB
  fixture `k=2` term, and exact absolute/integrated/per-bin threshold use. The
  12-device-per-MPN set is explicitly a heuristic engineering screen, not
  production-population or 90th-percentile qualification. No other scope changed.

Final estimator-focused verification (exact output):

```text
$ <synthetic 3-coupon x 4-unit x 3-reseat hierarchy assertions>
U95 example: m=1.50, R=0.05, V=0.10, C=0.20, U_fixture_k2=0.80, U95=1.15
Integrated guard: 2.65 dB <= 3.00 dB (SPH tie gate)
Per-bin examples: 5.65 dB passes; 6.15 dB fails the 6.00 dB spectral gate

$ cmp <canonical estimator blocks>
Canonical U95 estimator blocks are byte-identical.

$ python3 analysis/pdm_rx_timing.py
[all assertions passed; exact numeric output unchanged from the blocks above]

$ <T-001 20.18 m / 18.91 m assertions>
T-001 threshold assertions passed.

$ ruff check analysis/pdm_rx_timing.py analysis/link_budget.py
All checks passed!

$ ruff format --check analysis/pdm_rx_timing.py analysis/link_budget.py
2 files already formatted

$ python3 -m py_compile analysis/pdm_rx_timing.py analysis/link_budget.py
[no output; exit 0]

$ <T-016 state and T-010 dependency assertions>
Orchestration gate assertions passed.

$ git diff --check
[no output; exit 0]

$ git diff --cached --check
[no output; exit 0]
```
