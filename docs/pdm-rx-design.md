# Sonar v1 PDM receive electrical design

_T-008 provisional electrical baseline for T-011/T-020 review, 2026-08-25. This is
the repo-native schematic specification; no KiCad schematic was edited because
KiCad-open state is unknown. D011's physical part selection remains gated by T-016._

## Provisional baseline -- not an MPN/footprint release

Use 24 × **Syntiant SPH0641LU4H-1** bottom-port PDM microphones at 3.072 MHz,
paired by SELECT state onto 12 data lines. Run microphones, clock buffer, and Cmod
A7 I/O at 3.3 V. Use a TI **CDCLVC1112PWR** 1:12 LVCMOS fanout buffer: eleven
outputs feed the mic pairs (one center-row branch feeds two pairs) and the twelfth
returns the distributed clock to an FPGA clock-capable input.

This fixes a reviewable electrical baseline and lets T-011/T-020/T-021 proceed; it
does **not** release the SPH MPN, its footprint, or a production microphone BOM.
D011 says the part is chosen by the physical T-002/T-008 bake-off. T-016 now owns
that quantitative measurement and human release gate. T-010 depends on T-016 and
must instantiate only the MPN/land-pattern revision in its completed release
record. The two candidate footprints are not assumed compatible or dual-source.

This selection preserves the final D012 architecture: Cmod A7-35T + FT232H raw
continuous streaming, Pico snapshot compatibility, and spare pins for optional DNP
RMII. The default paired mapping saves 12 Cmod pins. No ADC, preamp, analog rail,
or in-fabric DSP is added.

## Why this microphone

| Criterion | SPH0641LU4H-1 | ICS-41352 bake-off alternate |
|---|---|---|
| Lifecycle on 2026-08-25 | Listed in Syntiant's current MEMS portfolio | TDK marks production but NRND and showed no distributor inventory |
| Ultrasonic mode | 3.072–4.8 MHz | 4.1–4.8 MHz |
| Exact chosen-point evidence | Typical response and current both specified at 3.072 MHz | Strong typical response/noise plots at 4.8 MHz |
| Ultrasonic supply current | 845 uA typ, 1.000 mA max at 1.8 V/3.072 MHz | 550 uA typ, 600 uA max at 1.8 V/4.8 MHz |
| SNR / AOP | 64.3 dBA / 120 dB SPL | 64 dBA / 120 dB SPL |
| Timing | `tDD` 18–40 ns; `tDZ` 3–16 ns | enable <=50 ns; disable 5–40 ns |
| Supply | 1.62–3.6 V | 1.65–3.63 V |

SPH0641 is the provisional baseline because its lifecycle is better and it lets the
design use the lowest documented ultrasonic clock and raw-data rate. It also has
an explicit typical 10–80 kHz response curve at that clock. ICS-41352 has better
documented ultrasonic noise and lower current, but its NRND/no-stock status is a
material BOM risk. Neither manufacturer guarantees unit-to-unit 20–40 kHz
flatness. Only the quantitative T-016 gate below may turn this baseline into a
released choice.

The TDK part is not assumed footprint-compatible with the Syntiant part even though
their body size and five signal names are similar. T-016 coupons must use each
candidate's exact manufacturer land pattern. T-010 must use only the winning exact
footprint from T-016's release record; T-014 then confirms an LCSC number or
explicit JLC Global Parts path for that MPN and the clock buffer before CP-C.

## Provisional SPH electrical block

This block is the SPH candidate implementation and the common clock/data topology,
not permission for T-010 to freeze an SPH-only sheet. Both candidates use 3.3 V
VDD/GND/CLK/DATA/SELECT and the same logical pairing, but their exact land patterns,
ultrasonic clock points, startup behavior, and timing constraints remain
candidate-specific. If T-016 releases ICS, update this block and capture contract
to its verified 4.8 MHz implementation before T-010 starts.

```text
3V3_D -- FB1/0R option --+-- 3V3_MIC -- 10uF -- GND
                         |
                         +-- UCLK CDCLVC1112PWR (3.3 V)
                         |     CLKIN <- PDM_CLK_SRC
                         |     1G    <- PDM_CLK_EN (100k pulldown)
                         |     Y0..Y10 -> 10R source footprints -> mic-pair CLK branches
                         |     Y11   -> 10R -> PDM_CLK_FB -> clock-capable FPGA input
                         |
                         +-- MIC00..MIC44, except MIC22

Each mic:
  VDD    -> 3V3_MIC; 100nF C0G/NP0 to GND at the pin
  GND    -> uninterrupted ground plane
  SELECT -> hard tie to GND (even channel) or 3V3_MIC (odd channel)
  CLK    <- pair branch from UCLK
  DATA   --+-- paired DATA net -- 0R isolation footprint -- PDM_D[0..11]
           +-- other mic DATA (opposite SELECT)
```

`FB1` is a footprint option, not a mandatory ferrite: fit 0 ohm initially so the
rail is observable and does not acquire an unverified bead resonance. A ferrite
may be stuffed after impedance/current review. Place 10 uF and 1 uF low-ESR bulk
at the mic-rail entry. The Syntiant datasheet recommends 0.1 uF at every microphone
and says those capacitors should not use Class 2 dielectrics; specify 100 nF C0G/NP0
and do not substitute X5R/X7R without a reviewed change.

UCLK has four VDD pins. Follow TI's rule of one 100 nF high-frequency capacitor per
supply pin with the shortest possible loop, plus 1 uF local bulk. Connect every VDD
and GND pin. TI recommends source matching and gives a 45-ohm typical output
impedance at 3.3 V; populate 10-ohm source resistors at UCLK initially, with layout
footprints permitting 0/10/22/33 ohm tuning. No series resistor belongs between the
two microphone DATA drivers. The post-merge 0-ohm footprint is only for isolation
and probing.

With a 50% input clock, the buffer's 180 ps maximum pulse-skew specification gives
49.945–50.055% duty at 3.072 MHz before board distortion, comfortably inside the
microphone's 48–52% limit. Scope verification at the most heavily loaded branch is
still mandatory because the buffer timing table assumes its stated test load.

Do not populate or enable any pull-up, pull-down, or FPGA internal pull on PDM data.
TDK explicitly prohibits pulls on the shared tri-state line, and the same rule is
required here to avoid biasing Syntiant's half-cycle handoff. SELECT is never left
floating.

### Clock branch allocation

Keep each paired DATA line on the same clock branch. Route the four-mic center-row
branch as a short symmetric split; all other branches feed one pair.

| UCLK output | Loads |
|---|---|
| Y0 | D0: M00, M10 |
| Y1 | D1: M20, M30 |
| Y2 | D2: M01, M11 |
| Y3 | D3: M21, M31 |
| Y4 | D4 + D5: M02, M12, M32, M42 |
| Y5 | D6: M03, M13 |
| Y6 | D7: M23, M33 |
| Y7 | D8: M04, M14 |
| Y8 | D9: M24, M34 |
| Y9 | D10: M40, M41 |
| Y10 | D11: M43, M44 |
| Y11 | `PDM_CLK_FB` only |

The microphone clock-input capacitance is absent from the primary datasheet, so
the four-load branch edge rate cannot be guaranteed analytically. This is missing
primary evidence, not a zero-capacitance assumption. The PCB requirement is <=0.5
ns total clock/data skew allocation and <=3 ns microphone clock rise/fall at every
load. Check UCLK IBIS during layout and confirm the four-load branch on a scope;
split it with a second active buffer only if either check fails.

## Power and logic budget

The only guaranteed 24-microphone calculation is at the datasheet's 1.8 V,
3.072 MHz test condition:

```text
typical: 24 * 0.845 mA = 20.28 mA
maximum: 24 * 1.000 mA = 24.00 mA
```

The selected 3.3 V operating voltage is legal and gives direct Cmod compatibility,
but Syntiant publishes no 3.3 V ultrasonic current maximum. Do not relabel the
24.00 mA figure as a 3.3 V guarantee. For CDCLVC1112 at 3.3 V, TI gives 10 mA
maximum static current. Its published `CPD=6 pF/output` gives 0.73 mA internal
dynamic current for twelve outputs at 3.072 MHz; external-load current cannot be
calculated because microphone clock capacitance is unpublished. Thus the known
reference subtotal is 34.73 mA, plus unknown 3.3 V mic delta and clock-load current.
Allocate **at least 100 mA** to `3V3_MIC` and measure actual current during the
bake-off. The 100 mA is a design allocation with >2x known-reference headroom, not
a component maximum.

At a 3.3 V rail with -5% tolerance, Syntiant DATA high is at least
`3.135 - 0.45 = 2.685 V`; Artix-7 LVCMOS33 requires 2.000 V, leaving 0.685 V.
Syntiant DATA low is at most 0.45 V versus the FPGA's 0.8 V maximum-low threshold,
leaving 0.35 V. A 1.8 V mic rail cannot directly drive a Cmod LVCMOS33 input, so it
is intentionally not used.

## Timing budget against Cmod A7-35T

At 3.072 MHz the half-period is 162.760 ns. Syntiant guarantees data assertion no
later than 40 ns after the launch edge and high-Z no earlier than 3 ns after the
opposite capture edge. AMD DS181 gives `0.01/0.33 ns` direct ILOGIC setup/hold for
the XC7A35T-1 and 48 ps CPG236 package skew. Allocate 0.500 ns to all board-level
buffer/load/route skew (the buffer alone is 50 ps only under equal load):

```text
setup margin = 162.760 - 40 - 0.500 - 0.048 - 0.010 = 122.202 ns
hold margin  =   3.000 -      0.500 - 0.048 - 0.330 =   2.122 ns
```

The fallback ICS-41352 at its worst-case 4.8 MHz point still gives 53.609 ns setup
and 4.122 ns hold with its 50 ns enable/5 ns minimum-disable values. These are
datasheet/board-budget calculations, not a substitute for placed-design timing.
T-020 must put the IDDR in the IOB, create the returned clock, constrain input
delays for both edges, and pass Vivado setup and hold timing. T-011 must reserve an
MRCC/SRCC-capable Cmod pin for `PDM_CLK_FB`.

## PCB acoustic-port and routing rules

1. For the SPH candidate, use the Syntiant manufacturer land pattern. Its package
   drawing labels the acoustic opening 0.325 +/- 0.05 mm, but does not give an
   allowable PCB-hole-to-package-port misregistration tolerance; that remains an
   evidence gap and must not be derived from drawing scale.
2. Drill a 0.50 mm **non-plated** through-hole centered on each package port. This
   is larger than the Syntiant package opening and is inside TDK's independently
   published 0.5–1.0 mm recommendation for the alternate.
3. No paste, solder mask, via, copper pour, trace, silkscreen, adhesive, or test
   point may enter the acoustic opening. Maintain a documented local keepout large
   enough for the exact land pattern and fab drill tolerance; T-010 must not invent
   pad clearance from the diagram scale.
4. Keep the bottom opening flush to the exterior. If an enclosure is added, use one
   short sealed acoustic path with acoustically opaque closed-cell gasket material;
   avoid a trapped cavity or second leak path.
5. Keep all 24 hole diameters, board thickness, solder-mask treatment, and exterior
   geometry identical. TDK warns that port acoustic mass materially changes
   ultrasonic response; geometry consistency is part of calibration integrity.
6. Do not board-wash, ultrasonic-clean, blow into, vacuum over, or insert anything
   into the mic ports. Add a fabrication note and protective handling plan.
7. Route clock on an uninterrupted reference plane, source resistors at UCLK, no
   long stubs, and <=0.5 ns combined clock/data route-skew budget. Keep DATA from a
   pair short before its merge and keep every PDM trace under 15 cm; TDK says longer
   DATA runs may require buffering.

## Quantitative release gate

This is a decision-ready plan, not a completed measurement or authorization to buy
hardware. T-016 implements it at the new CP-BM coupon checkpoint. Agents prepare
the designs, source evidence, order package, runbook, capture configuration, and
analysis; Joshua alone approves/places any order, provides or operates the bench,
ratifies the MPN release, and closes the `needs_human: true` ticket. T-010 cannot
freeze a microphone footprint/BOM until then. T-011, T-012, T-013, T-020, and
T-021 may continue on the common electrical/interface baseline.

### Population, coupons, and fixture

- Test at least **12 functional, non-cherry-picked microphones per MPN** across at
  least three separately assembled four-mic coupons per candidate. Log every
  installed device and assembly failure. Fewer than 12 valid devices for either
  MPN makes the comparison inconclusive unless Joshua ratifies a documented D011
  waiver; inability to source one part does not make the other the winner.
- Use separate exact Syntiant and TDK land patterns. Give both variants the same
  production-intent stack-up, 0.50 mm NPTH, mask, board thickness, decoupling,
  3.3 V rail, and worst-case four-load clock branch. Run SPH at 3.072 MHz, ICS at
  4.8 MHz, and SPH at 4.8 MHz as a clock-rate control. No shared/dual footprint is
  permitted without a separate primary-drawing compatibility proof.
- Mount every coupon in the same indexed fixture with a calibrated reference
  microphone and fixed wideband transmitter. Record candidate MPN, source/lot if
  available, coupon/unit serial, temperature, humidity, fixture pose, clock,
  supply, decimator revision, and calibration provenance. Acquire at least three
  independent reseats per channel, with a time-gated calibrated 20–32 kHz sweep in
  bins no wider than 500 Hz and three TX-off noise records through the same host
  pipeline. The fixture budget must report its expanded `k=2` term for every
  absolute and paired decision bin and integrated-band metric; each must be
  <=1.0 dB. Before/after reference drift must be <=0.5 dB magnitude and <=5 degrees
  phase. Otherwise the comparison is fixture-invalid, not a microphone failure.

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

### Normative response/noise and T-001 thresholds

For each unit, derive complex pressure-to-code response `H_i(f)`. Divide its TX-off
output-noise PSD by `|H_i(f)|^2`, then subtract the simultaneously measured ambient
and acquisition-floor PSD **in linear power** to estimate input-referred receiver
self-noise. If the subtraction is not resolvable within the uncertainty budget,
use the unsubtracted DUT-equivalent noise as the conservative screen value; never
clamp an unresolved result to an optimistic zero. T-001 adds its 30 dB SPL ambient
separately, so the analysis must not count fixture ambient twice. Retain the
per-frequency curves so a resonance/null cannot be hidden by one band average.

Build `N_screen` with the exact estimator above, not a datasheet-typical curve.
Re-run T-001's fixed person/reference case. A candidate passes the link gate only
when both conditions hold:

```text
10 m person margin        >= 24.09 dB  (T-001 27.09 dB minus 3.00 dB)
25 kHz zero-margin range  >= 18.91 m   (T-001 20.18 m with +3.00 dB noise penalty)
```

The same 3.00 dB cap leaves T-001's nominal 10 m small-target margin at >=4.1 dB
instead of its 7.1 dB reference value.

After one scalar gain normalization per unit, use each unit's three-reseat median.
The observed maximum-minus-minimum band-integrated receive-quality spread across
the 12 units must be <=3.0 dB, and no unit's 1 kHz decision bin may be >6.0 dB worse
than its candidate's hierarchical median. Report phase/delay spread. Reseated
response must repeat within 0.5 dB RMS magnitude / 5 degrees RMS phase, with no
single-bin excursion over 1.0 dB / 10 degrees. One candidate's observed unit spread
may not exceed the other's by >1.0 dB. These are sample-screen results, not
population-tolerance estimates.

Use the exact paired `L_band + U95_loss_band` and per-bin
`L[b] + U95_loss[b]` estimators above. The SPH-at-4.8 MHz run is diagnostic and
cannot replace the intended SPH-3.072/ICS-4.8 comparison.

### Hard electrical, load, and port gates

- All 12 units per candidate must start, enter ultrasonic mode, and produce both
  SELECT polarities. At near/far loads, measure clock frequency/duty/rise/fall,
  returned-clock-to-load skew, DATA enable/high-Z timing, and paired handoff.
  Reading plus measurement uncertainty must remain inside that MPN's primary-
  datasheet limits and the T-008 <=0.500 ns board-skew allocation. The four-load
  SPH branch must meet 48–52% duty, <=3 ns edges, `tDD <=40 ns`, and `tDZ >=3 ns`.
  There may be no contention/stuck channel in ten startup/mode-switch cycles. No
  DATA pull is permitted.
- Measure 3.3 V current and clock waveform with four loads. The 24-mic extrapolation
  plus measured clock-tree load must fit the 100 mA allocation with >=25% reserve
  (<=80 mA steady-state design estimate), and observed peak must remain <100 mA,
  or T-012 revises the rail before release. This is characterization, not a
  replacement for the missing SPH 3.3 V maximum or input-capacitance guarantee.
- Inspect 100% of ports. Each as-built 0.50 mm hole must meet the released fab
  drawing, remain non-plated and free of copper/mask/paste/debris, and show no
  aperture clipping under calibrated imaging. Record package-to-hole offset; do
  not invent an SPH allowable misregistration tolerance.
- The measured 10%-THD point must be >=117 dB SPL and no more than 3 dB below ICS.
  Recovery after the direct-TX burst must return response/noise to within 1 dB of
  its pre-burst value in <=250 us. A 250 us–1 ms result forces T-021 to use the
  T-001 1 ms guard and requires conditional human review; >1 ms fails. If the
  calibrated fixture cannot reach 117 dB SPL, mark overload `unverified`, not pass.
  Record the 1%-THD approach and 20–40 kHz response as informative data.

### Explicit pass/fallback rule

1. If SPH passes every hard gate and ICS fails a hard gate in an otherwise valid,
   complete comparison, release SPH and record the ICS failure.
2. If both pass and `L_band + U95_loss_band <=3.0 dB`, release SPH; lifecycle
   breaks a non-material acoustic tie. If
   `3.0 < L_band + U95_loss_band <=6.0 dB`, do not auto-select: present the
   acoustic/lifecycle trade to Joshua in the component-choice record.
3. If SPH fails and ICS passes, or both pass and
   `L_band + U95_loss_band >6.0 dB`, prepare a component-choice decision for
   Joshua that explicitly exposes ICS's NRND/orderability risk. Do not silently
   substitute ICS or retain the 3.072 MHz capture contract.
4. If only one exact MPN is sourceable/testable, the bake-off is inconclusive under
   D011. Joshua must ratify a documented waiver before any release.
5. If neither passes, freeze neither MPN/footprint. Reopen the D011 candidate set
   through a proposed decision and keep T-010 blocked.

The release record must name the exact MPN, footprint revision, a dated D009-
compatible orderable path for at least 30 microphones, source evidence,
clock/configuration, raw dataset and calibration artifact versions, threshold
results, and any ratified waiver. T-014 subsequently maps that released MPN into
the production assembly path; no coupon vendor or spend is assumed here.

### Per-channel calibration artifact

Store a versioned calibration file keyed by board serial and `CH00..CH23` with
complex response over the host's 128 ksample/s grid, measured DC offset, gain,
fractional delay, noise PSD, and validity conditions. First apply the known
162.760 ns odd-channel edge correction, then estimate residual gain/phase relative
to the array median. Regularize magnitude equalization so response nulls do not
amplify noise; retain raw recordings and coefficients so T-021 can reproduce the
calibration.

## Primary sources checked 2026-08-25

- [Syntiant current MEMS portfolio](https://www.syntiant.com/mems) and
  [SPH0641LU4H-1 datasheet hosted for Syntiant](https://static1.squarespace.com/static/6488b0b8150a045d2d112999/t/674f6a2fc6aa4452caafc777/1733259031446/SPH0641LU4H-1_More_Rev_B-1.pdf).
- [TDK ICS-41352 current product page](https://product.tdk.com/en/search/sw_piezo/mic/mems-mic/info?part_no=ICS-41352) and
  [TDK DS-000048 Rev 1.0](https://product.tdk.com/system/files/dam/doc/product/sw_piezo/mic/mems-mic/data_sheet/ds-000048-ics-41352-data-sheet-v1.0.pdf).
- [TI CDCLVC11xx Rev B datasheet](https://www.ti.com/lit/ds/symlink/cdclvc1112.pdf) and
  [CDCLVC1112 product page](https://www.ti.com/product/CDCLVC1112).
- [AMD Artix-7 DS181 v1.27.1](https://docs.amd.com/v/u/en-US/ds181_Artix_7_Data_Sheet),
  [Digilent Cmod A7 reference manual](https://digilent.com/reference/_media/reference/programmable-logic/cmod-a7/cmod_a7_rm.pdf), and
  [Digilent Cmod A7 master XDC](https://github.com/Digilent/digilent-xdc/blob/master/Cmod-A7-Master.xdc).
- [Knowles/Syntiant SiSonic Design Guide AN24](https://www.knowles.com/docs/default-source/default-document-library/sisonic-design-guide.pdf): non-plated bottom-port hole and sealed-path guidance.

Evidence gaps carried forward: no guaranteed SPH0641 20–40 kHz tolerance; no
SPH0641 3.3 V ultrasonic current maximum, clock-input capacitance, or allowable
PCB-hole-to-port misregistration tolerance; malformed revision fields in the
current Syntiant-hosted PDF; and no primary manufacturer evidence of JLC/LCSC
availability. These are explicitly assigned to T-016 characterization, layout
signal-integrity checks, and T-014 rather than silently assumed. Coupon measurements
do not convert missing manufacturer guarantees into specifications.
