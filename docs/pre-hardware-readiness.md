# Before buying Sonar hardware — 2026-09-13

**Update after Joshua's hardware inventory correction:** he owns a DE10-Lite
from school. **Pause the Cmod purchase.** That board is a credible alternative
for the next bench milestone, with a Quartus/board-interface port required.
See [proposed D014](../orchestration/decisions/D014-owned-de10-lite-bench.md).
The buying recommendation below predates this correction; no platform switch
or DE10-Lite implementation is yet approved or verified.

**Buy development capability; hold the main sonar PCB.** The architecture is a
credible experiment and has a staged bring-up path. A working ultrasonic imager,
its range and its update rate are not validated. Buying a development board does
not require first proving the acoustic design; ordering the production array does.
Joshua reports no hardware and clarified that his concern is **FPGA/USB capture
reliability**, rather than a future ASIC. No purchase, account, remote upload or decision
ratification was performed in this session.

## Decision in three stages

| Stage | Recommendation | What must be true first |
|---|---|---|
| FPGA development | Buy one **Cmod A7-35T, 410-328-35**, plus a USB-C-to-Micro-B **data** cable. Arrange a supported x86 Vivado machine. | Accept the module's Micro-B connector for the bench; it is not USB-C. No custom PCB needed to learn/program/test SRAM and UART. |
| Readout + acoustic experiment | Prepare rev B coupon assembly and the USB-C FT232H experiment. | Exact assembled headers/adapters, current parts/assembly quote, supplier DFM, safe TX driver/source, and executable coupon acquisition plan. Plan access to calibrated instruments before funding the full mic bake-off. |
| Main 24-channel PCB | **Hold.** The existing PCB is legacy; P3 layout has not started. | Mic release, completed schematic/ERC, sourced BOM, independent design review/CP-C, layout/DRC/DFM, then CP-D spend approval. |

Live check: [DigiKey Cmod listing](https://www.digikey.com/en/products/detail/digilent-inc/410-328-35/6133793)
showed **$104 USD, 1,180 in stock**, before shipping/tax/possible tariffs.
[Adafruit 2264](https://www.adafruit.com/product/2264) showed **$14.95, in stock**.
Those two boards total $118.95, not a complete bench budget. The Adafruit headers
are supplied loose: obtain assembly service if keeping D009's no-home-soldering
workflow. Cables, adapter, coupon assembly, TX, supply and lab access are additional.
Do not reuse the old $159.12 basket as a complete or current system quote.
Joshua previously preferred USB-C throughout: a C-to-Micro-B cable only fixes the
host end. If connector uniformity is a hard constraint even on the development
module, hold that purchase for a D012 amendment; no platform substitution is
silently approved here.

For the build host, prefer borrowed university/lab x86 hardware before another
computer purchase. A local x86 Linux/Windows machine makes JTAG/ILA easier than a
cloud-only host. [AMD's current supported OS list](https://docs.amd.com/r/en-US/ug973-vivado-release-notes-install-license/Supported-Operating-Systems)
is x86-64 Windows/Linux; native Apple Silicon/macOS is not supported. A cloud build
still needs an explicitly tested local programming/debug path. No account or paid
VM is needed for the remaining simulation work.

The optional Pico is useful only with a real SDK build, assembled headers and an
explicit four-channel capture configuration. It is not an already proven escape
route. Its current 24-channel default window is 5.333 ms, shorter than a 1 m
round-trip echo before any TX/recovery allowance. Do not buy a second platform to
avoid finishing the first one's acquisition software.

## Is the readout choice sound?

The main answer is to retain the FPGA/USB architecture for the experiment and
require digital counter-pattern evidence before the production PCB. There is no
custom ASIC in v1. The relevant silicon is the microphone's internal
analog buffer/sigma-delta converter, the Artix FPGA and the FT232H USB bridge.
This review covers both possible meanings of “ASIC readout”; a future custom ASIC
would need a separate requirements/architecture decision.

**PDM microphone:** keeping D011 is reasonable for the coupon experiment. It
removes a substantial external analog chain. A one-bit PDM stream is an
oversampled signal requiring filtering; it does not imply one-bit final acoustic
resolution. But fixed gain means clipping cannot be repaired downstream, and
calibration cannot restore a deep sensitivity null or missing SNR. Measure complex
20–32 kHz response, input-referred noise, channel phase/repeatability, direct-TX
overload and recovery, port effects and clock handoff on the actual assembly.

The [SPH manufacturer datasheet](https://static1.squarespace.com/static/6488b0b8150a045d2d112999/t/674f6a2fc6aa4452caafc777/1733259031446/SPH0641LU4H-1_More_Rev_B-1.pdf)
supports ultrasonic operation and gives a typical response curve, but its
64.3 dBA SNR and 120 dB overload numbers are measured at 1 kHz. They do not
guarantee the desired ultrasonic noise or overload performance. The alternative
[ICS-41352 remains Production (NRND)](https://product.tdk.com/en/search/sw_piezo/mic/mems-mic/info?part_no=ICS-41352).
If sourcing prevents the two-part comparison, the existing release rule requires
a proposed waiver or replacement candidate; absence of an alternate is not a pass.

**FPGA:** the clock/data rates and resource scale are plausible for the Cmod.
[Digilent documents](https://digilent.com/reference/_media/reference/programmable-logic/cmod-a7/cmod_a7_rm.pdf)
225 KB block RAM, 512 KB external SRAM, USB-JTAG and USB-UART for the 35T.
The primary FIFO requests 64 KiB before implementation packing. That is an
architecture sanity check, not a synthesis/utilization or timing result. Vivado is
absent locally. Existing XDC pins are audited, but PDM delays on both edges,
FT245 setup/hold, SRAM I/O timing, generated clocks, CDC constraints and BRAM
inference still need actual implementation reports. In particular, Gray-pointer
CDC needs reviewed skew/max-delay treatment; blanket clock false paths alone
are not evidence of correctness.

**USB bridge:** FT232H silicon supports the intended synchronous FIFO mode.
[FTDI advertises up to 40 MB/s](https://ftdichip.com/products/ft232hq/), versus
9.216 or 14.4 MB/s required here. This is sufficient nominal bandwidth, but not
a measured macOS/Python pipeline. The Adafruit schematic exposes the needed pins;
EEPROM configuration, physical wiring and throughput remain to be proved. See
[the concrete adapter/configuration checklist](ft232h-bench-preflight.md).

## Work closed in this session

T-023 now takes snapshots before USB flow control. USB FIFO overflow remains
sticky, while the independent SRAM capture continues to receive PDM frames.
FIFO pointers have explicit configuration-time values and asynchronous reset
assertion, so an absent USB clock cannot leave the other domain dependent on
undefined/stale pointer state. RAM accesses remain synchronous without a RAM reset;
Vivado must still verify block RAM inference. Read data is valid only with
`rd_valid`.

New `tb_top_snapshot.sv` exercises actual `sonar_top` at 3.072/4.8 MHz, with FT
clock absent from boot or present with TXE blocked. It waits beyond the real
16,384-frame FIFO capacity before pressing the snapshot button, checks two
consecutive 64-frame snapshots through the timing-checking SRAM model and UART,
verifies counters/CRCs, then reconnects USB, resets, and checks another snapshot.
TX must remain asleep throughout. Startup/button/UART durations are compressed;
this is digital simulation, not an acoustic or board model.

All **21 gateware checks** and **5 host tests** pass. Restoring the old USB-gated
tap makes the new regression fail: `snapshot length 48, want 240` (header only).
The full 512 KiB SRAM component test also passes. The repository KiCad harness
passes its existing-baseline rules; it still accepts main-board violations and
does not certify a production design. Durable logs are in
`orchestration/review/evidence-2026-09-13-t023/`.

## What still prevents a useful measurement

| Gap | Exact next deliverable | Owner |
|---|---|---|
| TX is still tied off; no real TX time origin | Arm/fire/read/status, waveform identity, sample-aligned event timestamp, manufacturer wake delay/fault/invalid-config handling; parser round trip and top-level tests | T-023, still in progress |
| Live host mistakes idle for EOF; DSP resets at chunk boundaries | Idle/deadline/disconnect handling, bounded recording, stateful decimator, replay and actual combined DSP/disk throughput | T-024 |
| No implemented FPGA evidence | Supported-host synthesis and place/route, checked timing/CDC/I/O/BRAM reports, bitstream tied to source revision | T-020 |
| No executable acoustic bench | Assembled adapter, clock-aware four-channel mapping, acquisition CLI/dataset, rated TX part/driver and instrument access | T-025 |
| Microphone performance and main array not released | Calibrated T-016 data and human MPN release, then T-010/014/015 and layout | T-016 onward |

The host diagnostic probe still reproduces both outstanding failures after the
five baseline host tests pass. Do not interpret those five tests as live ingest
validation. The pre-existing full review records the remaining defects in detail.
The rev B coupon source/export manifests still match **66/66** files from the
T-022 release verification; no coupon was regenerated or modified here. This is
an integrity check of prior release evidence, not a new acoustic/DFM approval.

## Details that would otherwise surprise us at the bench

- **UART update rate:** at the current 48 MHz / 417 divisor, a full SNP1 snapshot
  needs at least `(524286+48)*10*417/48e6 = 45.55 s` just for serial drain.
  About one update per second requires validated faster UART, a smaller/channel-
  reduced record or FT232H streaming. Do not promise 1 Hz from today's fallback.
- **Window and disk budget:** SRAM holds 56.89 ms at 3.072 MHz, 36.41 ms at
  4.8 MHz. Raw recording is 0.553/0.864 GB per minute respectively. The USB FIFO
  covers only 5.333/3.413 ms of stalled service. A burst/host scheduling delay
  longer than that must produce an explicit incomplete capture, never silent gaps.
- **Actual clock:** decimation by 24 gives 128 kHz or 200 kHz, not a fixed 128 kHz.
  The coupon YAML still incorrectly supplies only 128 kHz. Nominal clock choices
  sit at published mode boundaries; T-025 must budget oscillator/divider error
  and select a supported in-range operating point or obtain manufacturer guidance.
  A nominal number without tolerance is not a frequency-limit proof.
- **TX procurement is incomplete:** the listed GRS PZ1005 is specified only to
  [27 kHz](https://www.parts-express.com/GRS-PZ1005-3-1-4-Piezo-Horn-Tweeter-Similar-to-KSN1005A-292-442),
  not the 32 kHz band edge. Buying it does not validate the assumed transmit SPL.
  A separate rated driver/source is needed to test coupons without the main PCB.
  Keep MA40S4S disabled at 12 V: the 24 Vpp bridge excursion exceeds its 20 Vpp
  input rating. PWM duty does not reduce terminal peaks. D013 remains proposed.
- **Assembly and power:** explicitly include the coupon's THT headers/shunt in
  assembly and check mating-pin orientation. The Cmod's DIP VU is a power rail,
  not 3.3 V. Follow Digilent's warning against an external VU supply while USB
  is attached; on the eventual carrier, use the documented R420 isolation.
  Prove reset/unconfigured TX remains off before attaching a transducer.
- **Measurement access:** basic electrical bring-up and a visible echo are
  separate from calibrated microphone release. The current release gate needs
  ultrasound reference/source calibration, overload capability and sub-ns skew
  evidence (the runbook specifies a >=500 MHz scope). Borrow/book appropriate
  lab equipment before buying an expensive scope that cannot close those gates.
- **Imaging expectations:** a 27.6–32 mm aperture is only a few wavelengths.
  Uniform-aperture beamwidth scale at 25 kHz is about 22–25 degrees, even though
  ideal 12 kHz-bandwidth range resolution is 1.43 cm. At 32 kHz, pitch 6.9–8 mm
  exceeds lambda/2 = 5.36 mm; validate off-axis/grating-lobe behavior and define
  field of view before layout approval. These are calculated scales, not a
  measured point-spread function or angular accuracy guarantee.

## Bring-up ladder and evidence to retain

1. On Cmod alone: power/enumerate, program a source-identified bitstream, verify
   clock/reset, exercise SRAM address/data patterns and save CRC-checked UART
   output. TX off. No microphone board is needed yet.
2. Prove digital readout using a known pattern at both required raw rates. Save
   long counter-checked captures; exercise blocked host, unplug/reconnect and
   reset. For FT232H, measure USB + disk + DSP together on the actual laptop.
3. On one coupon: inspect ports/power, measure clock and shared-data handoff,
   verify every channel/polarity and repeat startup. Save raw plus actual clock.
4. Validate the TX terminal waveform with a suitable load/probe, then source SPL
   across the band. Measure direct leakage and recovery; derive a safe blanking
   interval from that evidence.
5. Proposed first echo: known reflector at 1–3 m, 20 consecutive acquisitions,
   range error <=10 cm, explicit failures and replayable raw/configuration.
   Report actual update rate; 1 Hz remains a target, not acceptance claimed today.
   Listen at least 17.5 ms after the TX reference for 3 m, plus the chosen chirp,
   delay and recovery allowances. A coupon proves ranging, not array imaging.
6. Run the existing calibrated multi-coupon bake-off, ratify the MPN, complete
   the main board, then measure bearing, two-target separation, room clutter,
   sidelobes and range on the full array.

**Engineering judgment:** I expect the digital readout to be achievable on this
platform; these repairs remove a concrete obstacle to bring-up. I cannot yet
claim useful full-band TX, microphone release, 10 m imaging or a reliable live
demo. None of those uncertainties is resolved by ordering the legacy main PCB.
