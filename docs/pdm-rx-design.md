# Sonar v1 PDM receive electrical design

_T-008 design draft for T-010/T-011 review, 2026-08-25. This is the repo-native
schematic specification; no KiCad schematic was edited because KiCad-open state is
unknown._

## Decision

Use 24 × **Syntiant SPH0641LU4H-1** bottom-port PDM microphones at 3.072 MHz,
paired by SELECT state onto 12 data lines. Run microphones, clock buffer, and Cmod
A7 I/O at 3.3 V. Use a TI **CDCLVC1112PWR** 1:12 LVCMOS fanout buffer: eleven
outputs feed the mic pairs (one center-row branch feeds two pairs) and the twelfth
returns the distributed clock to an FPGA clock-capable input.

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

SPH0641 wins on lifecycle and lets the design use the lowest documented ultrasonic
clock and raw-data rate. It also has an explicit typical 10–80 kHz response curve
at that clock. ICS-41352 has better documented ultrasonic noise and lower current,
but NRND/no-stock status is too risky for the primary BOM. Neither manufacturer
guarantees unit-to-unit 20–40 kHz flatness, so this is a provisional design-in
choice with the physical bake-off below as its release gate.

The TDK part is not assumed footprint-compatible with the Syntiant part even though
their body size and five signal names are similar. T-010 must use the exact Syntiant
land pattern; an alternate population requires its own verified footprint/coupon.
T-014 must confirm an LCSC number or explicit JLC Global Parts path for the exact
microphone and clock buffer before CP-C.

## Electrical block for T-010

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

1. Use the Syntiant manufacturer land pattern. The package acoustic port is
   0.325 +/- 0.05 mm.
2. Drill a 0.50 mm **non-plated** through-hole centered on each package port. This
   exceeds the Syntiant maximum port diameter and is inside TDK's independently
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

## Physical ICS-41352 versus SPH0641LU4H-1 bake-off

This is a plan, not a completed measurement. It must occur before releasing the mic
footprint/BOM at CP-C.

### Coupons and fixture

- Fabricate two otherwise identical four-mic coupons in the production stack-up,
  one using the exact Syntiant land pattern and one the exact TDK pattern. Use the
  same 0.50 mm NPTH port, mask, board thickness, decoupling, and 3.3 V rail. Run
  SPH0641 at 3.072 MHz (the v1 point), ICS-41352 at 4.8 MHz (its Ultrasonic Mode),
  and SPH0641 again at 4.8 MHz to separate part response from clock-rate effects.
- Mount each coupon in the same indexed fixture at the same height/orientation.
  Use a calibrated reference microphone beside it and a fixed wideband transmitter.
  Record temperature, humidity, coupon serial, channel, clock, supply voltage, and
  fixture position. Swap coupons and repeat to expose placement/systematic error.
- Capture raw PDM through the same host decimator. Use a time-gated logarithmic or
  linear chirp covering 18–45 kHz at several safe SPLs plus TX-off records. No
  response value is inferred outside measured/calibrated transmitter bandwidth.

### Measurements and release rule

For every unit, record complex response (magnitude and phase), input-referred
20–32 and 20–40 kHz noise, sensitivity scatter, 1%/10% THD approach, direct-TX
overload recovery, startup/mode-change behavior, rail current, clock duty/edge rate,
and DATA timing at near/far loads. Run at least three captures after reseating.

SPH0641 remains the release choice if it is orderable through the D009 assembly
path, all digital timing/edge checks pass, and its measured 20–32 kHz array-level
noise/response preserves the T-001 margin without materially worse unit scatter
than ICS-41352. A numeric acoustic pass/fail delta must be set at CP-B after the
calibrated fixture uncertainty is known; this document does not fabricate one from
typical plots. If SPH fails, propose a decision update before substituting the NRND
TDK part.

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
SPH0641 3.3 V ultrasonic current maximum or clock-input capacitance; malformed
revision fields in the current Syntiant-hosted PDF; and no primary manufacturer
evidence of JLC/LCSC availability. These are explicitly assigned to the bake-off,
layout signal-integrity check, and T-014 rather than silently assumed.
