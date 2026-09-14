# Sonar next steps and timeline — 2026-09-14

The next milestone is demonstrated FPGA/USB capture at Joshua's home desk.
The first acoustic milestone is repeatable ranging with a small microphone
coupon. A full 24-channel imager follows measured microphone release; it does
not yet have a defensible delivery date.

## Confirmed constraints

- Keep Vivado and ratified D012/Cmod A7-35T. No DE10-Lite port is selected.
- Home desk only: no scope, bench supply, calibrated ultrasound reference or
  school-lab access may be assumed. Source assembled connections; do not plan
  unapproved home soldering.
- **US$250 first-stage ceiling** for cloud, Cmod, FT232H, cables and adapters.
  Custom microphone boards and test equipment are excluded and need a separate
  quote/decision. Agents do not execute purchases.
- Joshua has **2–4 hands-on hours/week**. Prepare short bench checklists and
  retain machine-readable logs so diagnosis does not depend on recollection.

## Target calendar

Dates assume a usable x86 host this week, continued engineering sessions and
prompt development-board delivery. They are estimates, not booked appointments
or vendor lead-time promises. Re-estimate after the first Vivado run and quotes.

| Target | Engineering work and exit evidence | Joshua's part |
|---|---|---|
| **Sept 14–20: first implementation evidence** | Run Vivado; fix synthesis/fit failures; inspect RAM inference and clocks. Continue T-023 command/timestamp work and prepare counter diagnostics. Retain source-identified reports and actual failures. Recommend the Cmod order after initial fit, pin review and a concrete programming plan; full readout signoff can continue while it ships. | About 30–60 minutes for VM/AMD setup. Place the exact development order after its delivered total is checked. |
| **Sept 21–27: digital test package** | Complete relevant I/O timing, CDC/DRC and vendor-model checks. Fix T-024 idle/EOF/disconnect and stateful DSP. Prepare SRAM/UART and FT232H pattern generation/checking, bridge configuration and assembled wiring. Require reviewed implementation for enabled diagnostic paths; TX remains disabled. | Receive/check modules and cables; one short connection session if delivery permits. |
| **Sept 28–Oct 4: desk capture proof** | Program locally; test clocks/reset, SRAM and UART, then FT232H. Check counters at both candidate rates; deliberately stall/unplug/reconnect/reset. Proposed acceptance: 60 minutes per rate with zero unexplained gaps/corruption in normal operation, bounded memory/disk and explicit error/recovery behavior. | One or two bench sessions totaling 2–4 hours. Long automated tests require little interaction after setup. |
| **First echo target: Oct 12–25, conditional** | Prepare T-025's assembled coupon/adapter/source quote and instrument-access plan while digital work proceeds. With hardware/access available, validate RX channels and TX waveform/recovery, then range a known reflector. Proposed acceptance: 20 acquisitions at 1–3 m, error within 10 cm, saved raw/configuration and actual update rate. | Separate coupon/assembly budget and temporary measurement access through borrowing, rental or a qualified bench service. Run the prepared sequence. |
| **After measured microphone release** | T-016 calibrated bake-off/MPN release, final array schematic/BOM, independent review, layout/DRC/DFM and production order package. CP-BM, CP-C and CP-D remain in force. | Review measured tradeoffs and actual production quote; approve/place any order. |

The digital target has the strongest planning basis. First-echo timing depends
on a safe assembled source/driver, coupon delivery and temporary instrument
access, all unresolved with the current home desk. If those cannot be arranged,
continue digital work and hold acoustic release. A coupon respin or major
timing/USB defect moves the dates; never compress verification to preserve them.
First echo demonstrates ranging, not calibrated mic release or array imaging.

## First-stage allocation, not a shopping quote

| Envelope | Maximum allocation |
|---|---:|
| Temporary cloud host | $10 |
| Cmod A7-35T and USB-C-to-Micro-B data cable | $130 |
| FT232H, assembled headers/adapter and interconnect | $70 |
| Delivery, tax and contingency | $40 |
| **Total ceiling** | **$250** |

These are allocation targets, not verified delivered prices. If assembled FTDI
wiring cannot fit, buy/test Cmod UART/SRAM first and revise the remaining basket.
Never substitute loose headers needing unplanned soldering. Start with USB
module power. This ceiling does not purchase a complete sonar instrument.

## What Joshua needs to provide next

1. **One usable x86 Linux host.** Default: the temporary 4-vCPU/8-GB/160-GB
   Linode in `vivado-validation.md`. Provide SSH hostname and username with
   access through an existing SSH key. A compatible credited host is equally
   usable after architecture/storage/job-limit checks. Dedalus outreach is
   optional and need not delay the first run.
2. **AMD installer/license access.** Complete required account enrollment,
   download authentication and free BASIC license issuance personally. Setup
   and batch builds can then proceed on the host. Do not paste passwords or
   private keys into the repo.
3. **Shipping country and postal/ZIP code** for a delivered basket within the
   ceiling, including assembled connections and all delivery/tax. Joshua places
   orders under the repo protocol.
4. **The already-confirmed 2–4 hours/week once boards arrive.** Instrument
   access and coupon funding will come with a concrete proposal, rather than
   an undefined request to buy a lab.

Local command/status/timestamp and host test work can proceed before cloud
access. Once the host is ready, prioritize real Vivado reports over further
provider comparisons. T-023 owns commands/capture; T-020 implementation and
diagnostics; T-024 host reliability; T-025 the assembled coupon bench. This is
planned ownership, not a claim that background jobs or multiple agents started.

## Home-desk programming and verification limits

openFPGALoader explicitly lists
[`cmoda7_35t` programming support](https://trabucayre.github.io/openFPGALoader/compatibility/board.html)
and a [macOS Homebrew installation](https://trabucayre.github.io/openFPGALoader/guide/install.html).
This is a concrete candidate for loading cloud-built bitstreams through Cmod
USB. Verify the installed board entry, USB access and a volatile diagnostic
load when hardware arrives. No loader installation or programming happened in
this planning session. Full Vivado hardware-debug connectivity is separate.

Counter checks and loopbacks provide functional evidence; they do not measure
electrical timing margin, ringing, clock quality or acoustic response. Keep the
source disabled until its waveform is checked. Current full UART snapshots take
about 46 seconds to drain; first-echo acceptance reports actual cadence and
does not promise a 1 Hz display.
