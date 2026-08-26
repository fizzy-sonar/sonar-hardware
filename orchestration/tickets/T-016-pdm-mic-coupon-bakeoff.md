---
id: T-016
title: Quantitative PDM microphone coupon bake-off + MPN release
status: in-progress
phase: P2
tier: mid        # coupon EDA package, calibrated analysis, and release report
priority: 1
assignee: codex/terra-t016
depends_on: [T-001, T-002, T-008]
needs_human: true
created: 2026-08-25
updated: 2026-08-26
---
## Goal
Complete the physical SPH0641LU4H-1 versus ICS-41352 bake-off required by D011,
then release exactly one microphone MPN and its manufacturer land pattern for
T-010. T-008's SPH design is only the provisional electrical baseline until this
ticket is done.

## Context
D011 requires the microphone to be selected by the T-002/T-008 bake-off. Primary
datasheets do not guarantee SPH0641 20--32 kHz response/noise, 3.3 V maximum
current, clock-input capacitance, or allowable PCB-port misregistration. The two
candidate footprints are not assumed compatible. The normative fixture, metrics,
and pass/fallback rules are in `docs/pdm-rx-design.md`, section **Quantitative
release gate**.

This ticket creates the only authorized pre-CP-C coupon path, at **CP-BM**. It does
not authorize a purchase. Agents never place orders or spend money.

## Work split and state gate

### Agent-executable before `review`

1. Re-check dated lifecycle and legitimate sourcing for both exact MPNs. Record
   evidence and quantities without representing unavailable stock as orderable.
2. Produce separate candidate coupon designs using each manufacturer's exact land
   pattern: at least three four-mic coupons per candidate (12 installed microphones
   per MPN), production-intent stack-up/port geometry, and the worst four-load
   clock branch. Produce reviewable schematics/layouts, fabrication/assembly files,
   BOM, placement drawing, fixture drawing, and a priced order package. Do not add
   an unverified dual-footprint.
3. Produce acquisition firmware/configuration, raw-data schema, calibration and
   reseating runbook, and deterministic analysis code that emits every metric and
   threshold below. Record calibration-chain uncertainty.
4. Run EDA checks on both coupon variants and synthetic-data tests on the analysis.
   Put exact output in this Log, then move the ticket to `review`.

### Joshua-only at `review`

- Explicitly approve and place/pay for any coupon and microphone orders. An agent
  may prepare the order package but cannot click purchase or authorize spend.
- Provide or operate the calibrated reference microphone, transmitter, fixture,
  oscilloscope, and current-measurement setup; run or supervise the written bench
  procedure. Agents may guide the session and analyze the resulting files.
- Ratify the final MPN/footprint release record. Only Joshua moves this
  `needs_human: true` ticket to `done`.

T-010 remains blocked until all three human actions and the quantitative analysis
are complete. If hardware, calibration, or either exact MPN is unavailable, the
result is `inconclusive`, not an automatic SPH release.

## Quantitative Definition of Done

- **Population:** at least 12 functional, non-cherry-picked microphones of each
  MPN across at least three separately assembled four-mic coupons. Log every
  installed unit and assembly failure. Fewer than 12 valid units for either part
  is inconclusive unless Joshua ratifies a documented D011 bake-off waiver.
- **Acoustic records:** each channel has at least three independent fixture
  reseats, a calibrated time-gated 20--32 kHz sweep in no wider than 500 Hz bins,
  and three TX-off noise records through the same PDM/host decimator. The fixture
  budget must report its expanded `k=2` term for every absolute and paired decision
  bin and integrated-band metric; each must be <=1.0 dB. Before/after reference
  drift must be <=0.5 dB magnitude / 5 degrees phase, or the fixture is invalid.

<!-- T016-U95-ESTIMATOR-BEGIN -->
### Exact v1 screening estimator

The 12 devices per MPN (three coupons × four sites) are a heuristic engineering
screen chosen to expose assembly, four-load-clock, unit, and coupon effects. They
do **not** estimate or qualify a production-population 90th percentile. Population
qualification is outside Sonar v1; it would require a separately justified larger
sample across production lots, assemblies, and environmental corners.

Use indices candidate `c`, coupon `q=1..3`, fixed site `u=1..4`, reseat
`r=1..3`, and decision bin `b`. Predeclare a one-to-one SPH/ICS pairing for the
same `(q,u,r)` fixture block before seeing results, bracket the pair with the same
reference calibration, and alternate acquisition order. Never re-pair to improve a
result. A missing member makes that block incomplete; the release dataset still
needs all 12 valid devices per MPN and three reseats.

Raw response/noise records may use bins <=500 Hz. Form each non-overlapping 1 kHz
decision-bin SNR and the separate 20–32 kHz matched-filter SNR by summing calibrated
signal and noise in **linear power first**, using the same D001 chirp weighting and
host decimator, then convert the ratio to dB. The integrated-band statistic is
formed from the integrated powers; it is not an average of bin dB values.

For any scalar dB screen metric `x[q,u,r]` (evaluated separately for each bin or
for the integrated band), calculate these deterministic hierarchical statistics:

```text
m_unit[q,u] = median_r(x[q,u,r])
m_coupon[q] = median_u(m_unit[q,u])
m           = median_q(m_coupon[q])

R = max_q,u,r |x[q,u,r]    - m_unit[q,u]|   # observed reseat term
V = max_q,u   |m_unit[q,u] - m_coupon[q]|   # observed unit/site term
C = max_q     |m_coupon[q] - m|             # observed coupon term

U95 = U_fixture_k2 + R + V + C
```

`U_fixture_k2` is the fixture/calibration budget's expanded `k=2` term for that
same metric and bin/band; it includes calibration, reference/source bracketing, and
acquisition-floor effects but excludes `R`, `V`, and `C`. It must be reported
and <=1.0 dB everywhere used by a release decision. Add the four nonnegative terms
linearly—do not root-sum-square them—because no independence or distribution is
claimed. `U95` is therefore a conservative v1 **screening guard band**, not a
measured 95% population interval; the name only preserves the selection-rule
notation associated with the stated `k=2` fixture term.

For each candidate's absolute T-001 input, let `x` be its input-referred self-noise
level in dB SPL for the evaluated bin. The screened curve is `N_screen[b] = m[b] +
U95_noise[b]`; feed that curve to T-001, which adds its ambient term separately.
If ambient/floor subtraction is unresolved, use the unsubtracted DUT-equivalent
noise as `x` (a conservative upper screen value), not zero.

For the paired comparison, compute `d[q,u,r,b] = SNR_ICS[q,u,r,b] -
SNR_SPH[q,u,r,b]`; positive loss means SPH is worse. Apply the same hierarchy to
`d`: `L[b]=m[b]` and `U95_loss[b]` is its guard. Compute `L_band` and
`U95_loss_band` again from each paired record's integrated 20–32 kHz SNR; do not
derive them by averaging per-bin losses or guards.

Thresholds consume the guarded values exactly as follows:

```text
absolute link gate: T-001(N_screen[b]) must meet 24.09 dB at 10 m and 18.91 m range
SPH tie/review gate: L_band + U95_loss_band compared with 3.0 dB and 6.0 dB
spectral-hole gate: L[b] + U95_loss[b] <= 6.0 dB in every 1 kHz decision bin
```

Report `m`, `R`, `V`, `C`, `U_fixture_k2`, `U95`, and the guarded value
for every candidate/bin and for the integrated comparison so T-016 analysis is
reproducible.
<!-- T016-U95-ESTIMATOR-END -->

- **Response/noise metric:** for each unit calculate input-referred noise by
  dividing the TX-off output-noise PSD by its calibrated complex pressure-to-code
  response, then subtract simultaneous ambient/acquisition-floor PSD in linear
  power. If subtraction is unresolved, use the unsubtracted DUT-equivalent noise;
  do not clamp it to zero or add T-001's ambient twice. Build `N_screen` with the
  exact estimator above; do not substitute a datasheet-typical curve.
- **T-001 limit:** rerun the reference person case with `N_screen`. A
  candidate passes only if its 10 m margin is >=24.09 dB (no more than 3.00 dB
  below T-001's 27.09 dB reference) and its 25 kHz zero-margin range is >=18.91 m
  (the T-001 result after the same 3.00 dB penalty). The same cap leaves the
  nominal 10 m small-target margin >=4.1 dB from T-001's 7.1 dB reference.
- **Channel spread:** after one scalar gain normalization per unit, use each unit's
  three-reseat median. The observed maximum-minus-minimum band-integrated receive-
  quality spread across the 12 units must be <=3.0 dB, and no unit's 1 kHz decision
  bin may be >6.0 dB worse than its candidate's hierarchical median. Three-reseat
  response must repeat within 0.5 dB RMS magnitude / 5 degrees RMS phase with no
  single-bin excursion >1.0 dB / 10 degrees, and one candidate's observed unit
  spread may not exceed the other's by >1.0 dB. These are sample-screen results,
  not population-tolerance estimates.
- **Relative intended-mode metric:** use the exact paired
  `L_band + U95_loss_band` and per-bin `L[b] + U95_loss[b]` estimators above.
  The SPH 4.8 MHz run is diagnostic only.
- **Electrical/timing:** all 12 units per candidate must start, enter ultrasonic
  mode, and produce both SELECT polarities. At near and far loads, scope clock
  frequency/duty/rise/fall, returned-clock-to-load skew, DATA enable/high-Z timing,
  and paired handoff. Each reading plus measurement uncertainty must remain inside
  that MPN's primary-datasheet limit and the T-008 <=0.500 ns board-skew allocation;
  the four-load SPH branch must also meet 48–52% duty, <=3 ns edges, `tDD <=40 ns`,
  and `tDZ >=3 ns`. Ten startup/mode-switch cycles must show no contention or stuck
  channel. No data pull is allowed.
- **Power/load:** measure 3.3 V coupon current and clock waveform on the four-load
  branch. The 24-mic extrapolation plus measured clock-tree load must fit the
  100 mA rail allocation with >=25% reserve (<=80 mA steady estimate) and observed
  peak <100 mA, or T-012 must revise the rail before release. This characterization
  does not turn the missing SPH 3.3 V manufacturer maximum or input capacitance
  into a guarantee.
- **Port/assembly:** use separate exact land patterns and identical 0.50 mm NPTH,
  stack-up, mask, and exterior geometry. Inspect 100% of ports: the as-built hole
  meets the released fabrication drawing, is non-plated and free of copper/mask/
  paste/debris, and calibrated imaging shows no aperture clipping. Record package-
  to-hole offset. The absent SPH allowable misregistration tolerance remains an
  evidence gap; do not infer dual-source compatibility.
- **Overload/recovery:** measured 10%-THD point is >=117 dB SPL and no more than
  3 dB below ICS. Recovery to within 1 dB of pre-burst response/noise is <=250 us;
  250 us–1 ms requires the T-001 1 ms guard and conditional human review, while
  >1 ms fails. If the calibrated fixture cannot reach 117 dB SPL, mark this gate
  `unverified`, not pass.
- **Source/release:** the winning exact MPN has a dated legitimate path for coupon
  quantity and a D009-compatible orderable path for at least 30 microphones. T-014
  still performs the complete production JLC/LCSC mapping. No footprint or
  production BOM is released from an unverified marketplace listing.

## Explicit selection rule

1. If SPH passes every hard gate and ICS fails a hard gate in an otherwise valid,
   complete comparison, release SPH and record the ICS failure.
2. If both pass and `L_band + U95_loss_band <=3.0 dB`, release SPH; lifecycle
   breaks a non-material acoustic tie. If
   `3.0 < L_band + U95_loss_band <=6.0 dB`, require Joshua's explicit component-
   choice decision.
3. If SPH fails and ICS passes, or both pass and
   `L_band + U95_loss_band >6.0 dB`, prepare a component-choice decision that
   exposes ICS's NRND/orderability risk. Do not silently substitute ICS or change
   the 3.072 MHz contract.
4. If only one part can be sourced/tested, either part is inconclusive under D011;
   Joshua must ratify a documented waiver before it can be released.
5. If neither passes, freeze neither footprint/BOM. Reopen the D011 candidate set
   through a proposed decision and keep T-010 blocked.

The final release record names the MPN, footprint revision, clock rate, calibration
artifact version, source evidence, all threshold results, and any ratified waiver.
If ICS wins, update `docs/pdm-capture-contract.md` and the T-008 timing/current
baseline before T-010 starts.

## Verification

- Coupon EDA/ERC/DRC and fabrication-file checks for both exact footprints.
- Synthetic pass/fail fixtures exercise every analysis threshold and selection
  branch before hardware data is accepted.
- The calibrated raw dataset is complete for 24 candidate devices and all reseats;
  analysis regenerates the release report deterministically.
- `git diff --check` and ticket-dependency audit pass; exact output is pasted here.

## Log
- 2026-08-25 codex/sol-t008: created from the independent T-008 review. No coupon
  vendor/source, price, or spend authorization is implied. Exact next step: an
  agent claims T-016, prepares both coupon/order/test packages, and moves it to
  `review`; Joshua alone buys, supplies bench access/data, ratifies the MPN, and
  closes the ticket.
- 2026-08-25 codex/sol-t008: bounded final-review repair defined `U95` as a
  deterministic hierarchical screening guard over reseat, unit/site, coupon, and
  fixture terms; defined fixed paired SPH/ICS blocks and exact band/bin threshold
  use; and removed any claim that 12 devices qualify a population percentile.
