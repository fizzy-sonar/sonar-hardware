# 2026-08-25 — codex/sol-t008: PDM microphone and RX electrical design

## Session

- Continued the pre-claimed T-008 branch `agent/T-008-pdm-mic-design` in the
  isolated worktree `/private/tmp/sonar-t008`.
- Read the protocol, state, architecture, conventions, roadmap, newest three
  journals, T-008/T-002/T-020, parts matrix, link budget, and all ratified decisions.
- Checked dated primary manufacturer sources for both microphones, the clock
  buffer, Cmod A7, and XC7A35T timing. No purchase, push, merge, branch switch, or
  KiCad schematic edit occurred.

## Delivered

- Selected SPH0641LU4H-1 at 3.072 MHz as the provisional electrical baseline: it
  remains in Syntiant's current portfolio, that clock is its documented Ultrasonic
  Mode lower bound and the exact point of its current/typical-response evidence,
  and it minimizes raw bandwidth. ICS-41352 remains the lower-current, better-
  noise-documented bake-off reference but is NRND with no TDK inventory indication.
- Kept paired capture: 24 microphones on 12 shared DATA nets, even channels sampled
  rising and odd channels falling. The 162.760 ns / 55.83 um pair offset is carried
  explicitly into host calibration instead of being hidden.
- Specified a 3.3 V mic domain, per-mic 100 nF C0G bypass, CDCLVC1112PWR fanout with
  returned clock, startup sequence that does not wake directly into Ultrasonic
  Mode, source-resistor footprints, 0.50 mm non-plated acoustic holes, and handling
  rules. `docs/pdm-rx-design.md` is the reviewable schematic block for T-010.
- Added `docs/pdm-capture-contract.md` v1: 3.072 MHz, 12 lines/24 channels,
  73.728 Mb/s raw, no FPGA decimation on the FT232H path, host decimation 24 to
  128 ksample/s, fixed edge/channel map, startup constants, and T-020 assertions.
- Added deterministic `analysis/pdm_rx_timing.py` for timing, current, bandwidth,
  duty-cycle, pair-offset, and logic-level checks.

## Findings and evidence boundaries

- Timing has 122.202 ns setup and 2.122 ns hold margin using manufacturer output
  timing, a 0.500 ns board-skew allocation, and XC7A35T-1 direct ILOGIC/package
  figures. T-020 must still constrain and pass the placed Vivado design.
- The 24-mic datasheet current is 20.28 mA typical / 24.00 mA maximum only at the
  1.8 V characterization point. Syntiant does not publish a 3.3 V ultrasonic
  maximum or clock-input capacitance. The design therefore allocates at least
  100 mA and requires current/edge measurement; it does not invent missing limits.
- D011's older FPGA-CIC consequence text conflicts with the later D012 raw FT232H
  amendment. The contract follows D012: continuous raw PDM, laptop CIC/FIR, optional
  in-fabric CIC only for future DNP RMII.
- The Syntiant-hosted PDF has malformed revision placeholders. Its tables agree
  with older Knowles Rev B, but this was not represented as current-revision proof.

## Verification

`python3 analysis/pdm_rx_timing.py` passed all assertions and printed the exact
results recorded in the T-008 Log. `ruff check` passed; `ruff format --check`
reported one file already formatted; `python3 -m py_compile` and
`git diff --check` exited zero with no output. No repo-wide KiCad check harness was
available on this branch at verification time.

## Next steps

1. T-010 instantiates the documented tile using the exact Syntiant land pattern;
   T-011 assigns `PDM_CLK_FB` to a clock-capable Cmod pin and preserves the channel
   map.
2. T-020 copies the contract constants into its sampler testbench and proves edge
   ordering plus placed timing. T-021 implements host decimation/calibration.
3. Superseded by the independent-review repair below: T-016 now requires three
   four-mic coupons per MPN, a quantitative sweep, and an explicit CP-BM human gate.

## Independent-review repair

The independent review returned **PASS WITH REQUIRED FIXES**: commit `1b974ce`
had a sound electrical baseline but prematurely treated SPH as the selected tile
while deferring a qualitative two-coupon comparison. There was no `needs_human`
purchase/bench ticket before CP-C, so that sequence could not legally release the
MPN under D011.

The repair keeps SPH/3.072 MHz as a provisional T-011/T-020 baseline and creates
T-016 for the physical decision. The gate now requires 12 non-cherry-picked devices
per candidate, calibrated/reseated 20–32 kHz response and input-referred noise,
<=3 dB T-001 penalty, bounded channel/bin spread, intended-mode comparative SNR,
electrical/timing/current/port/overload checks, and explicit pass/fallback branches.
The SPH and ICS footprints remain separate; compatibility was not inferred.
This explicitly supersedes the earlier session note proposing only two coupons.

T-016 is agent-executable through a checked coupon design, source/order package,
runbook, and analysis suite. It then stops at `review`. At CP-BM Joshua alone must
authorize/place/pay for coupons, provide or operate the calibrated bench, and
ratify the exact MPN/footprint. No coupon source, price, order, or spend is claimed
by this session. T-010 and the production mic BOM wait on that result; T-011,
T-012, T-013, and parameterized T-020 work can proceed.

The review also retained the nonblocking primary-evidence gaps: no SPH 3.3 V
ultrasonic maximum current, no clock-input capacitance/load value, and no published
allowable PCB-hole-to-SPH-port misregistration tolerance. Measurements characterize
the design but do not turn those absences into manufacturer guarantees.

Repair verification re-ran the PDM electrical assertions, independently asserted
T-001's 20.180 m baseline and 18.905 m result after the allowed 3.00 dB penalty,
passed Ruff check/format and Python compilation for both analysis scripts, passed
the ticket status/dependency audit, and passed unstaged/staged diff checks. Exact
output is in the T-008 Log. No KiCad file was edited.
