# T-023 readout reliability and pre-hardware progress — 2026-09-13

Joshua asked what must happen before buying hardware/boards, whether Sonar should
work and whether it is bring-up-able. He has no hardware and clarified that the
ASIC concern means FPGA/USB capture reliability. Oriented through protocol,
STATUS/PLAN/CLAUDE/roadmap/journals and decisions. T-023 is top-tier integration
work, appropriate to this session. Fast-forwarded main over the two completed
T-026 commits, committed claim `2acee6e`, and branched
`agent/T-023-commanded-echo-capture`. Existing sonar.kicad_pro edit preserved.

## Delivered

- Snapshot tap now observes active PDM acquisition independently of USB acceptance.
  Primary-stream overflow remains sticky and stops the incomplete stream.
- New actual-top regression uncovered clock-absent FIFO pointer initialization.
  Pointer configuration values and asynchronous reset assertion remove that
  dependency; RAM accesses remain synchronous/reset-free for inference. Read data
  is specified only under rd_valid. Vivado inference/CDC proof is still required.
- Four actual-top tests: both 3.072/4.8 MHz and absent/blocked FT clock paths, delayed
  trigger after production FIFO capacity is exhausted, two consecutive snapshots,
  SRAM model and UART counter/CRC checks, USB reconnect, reset, another snapshot,
  TX idle. Time-compressed UI/startup/UART and 64-frame windows; actual rates/FIFO
  capacity. Restoring the old tap makes the test fail, header only.
- `docs/pre-hardware-readiness.md`: staged buy/hold decision, proof ladder, current
  evidence and missing contracts. `docs/ft232h-bench-preflight.md`: source-audited
  Adafruit-to-Cmod adapter map and required FIFO EEPROM setup before mode 0x40.
  Current host constructor does not verify the EEPROM prerequisite.
- Found/quantified UART drain >=45.55 s/full snapshot; cannot promise 1 Hz using
  this default. Budget actual clock-derived sample rates, finite USB stalls,
  source/driver and calibrated-lab access before coupon procurement. No new
  architecture, waiver, full-band TX part or calibrated measurement is approved.
- Live primary/vendor checks: Cmod $104/1,180 shown, Adafruit $14.95/in stock,
  FTDI FIFO mode prerequisites/pins, Adafruit schematic, AMD x86 OS support,
  Syntiant ultrasonic specs and TDK NRND. FTDI direct PDF returned 403; primary
  search-indexed text used, transparently documented. Adafruit public schematic
  downloaded into ignored build/ and XML nets inspected. No third-party project
  was executed. The old buy list now points to the scoped current recommendation.

## Verification

Durable logs: orchestration/review/evidence-2026-09-13-t023/.

- `make -C gateware test`: exit 0, 21 PASS lines, including existing complete
  512 KiB SRAM test and four new top cases. XDC 28 ports / 73 bits unchanged.
- Negative control with only old accepting-gated tap restored in an ignored
  temporary source: exit 1, `snapshot length 48, want 240`.
- `PYTHONPATH=host uv run --offline python -m unittest discover -s tests -v`:
  5/5 OK; required approval to use existing uv cache. Host diagnostic probe still
  reproduces idle EOF and 0.233102 chunk/whole decimator difference.
- `bash scripts/check.sh`: approved host run exit 0, existing ERC/DRC baseline
  violations accepted as designed. Not main-board electrical release.
- T-022 source/export manifests: 66 matches, 0 missing, 0 changed. No coupon
  regenerated; retained prior DRC evidence, no new physical/DFM claim.

## Exact next work

T-023 remains in progress: implement UART or other real arm/fire/read/status
control, TX fault/wake/limits, sample-aligned event metadata and complete/error
capture boundaries, prove host parser round trip and top-level failure/restart
cases. No bitstream exists here. T-020 owns implementation/report gates. T-024
must fix live transport/DSP and expose integrity/overflow; T-025 must produce an
executable coupon bench and quote with assembly/adapter/TX/equipment included.

Retain current platform pending proof. Development hardware can precede acoustic
validation; production PCB cannot. Cmod Micro-B conflicts with a strict all-USB-C
rule, so do not silently substitute a board or assume that preference was waived.
No purchase, spend, external publication, message or ratification performed.
