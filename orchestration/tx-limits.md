# TX waveform limits (T-013) — consumed by T-020 gateware `tx_nco_pwm`

_Authoritative TX drive envelope. The bounded chirp controller in
`gateware/rtl/tx_nco_pwm.sv` rejects out-of-limit requests (`limit_fault`); this file
defines the limits it must enforce and the electrical meaning of its parameters._

## Hardware path (schematic: `sonar-v1-pcb/20kHz-h-bridge.kicad_sch`, "TX Drive")

DRV8876 full bridge, VM = **+12V** boost rail (11.4–12.6 V; sequenced up after 3V3_D,
see `orchestration/rails.md`). Differential full-scale drive = 2·VM = **24 Vpp**
(22.8–25.2 Vpp over rail tolerance). Off-board transducer on **J50** (MKDS 5.08 mm
screw terminal, center-cell cable per D001/D007). R173/R174 = 0R series (0603
inductor EMI option); R175+C288 = DNP snubber provision across the transducer.

| FPGA/gateware | Net | DRV8876 pin | Cmod pin | Notes |
|---|---|---|---|---|
| `tx_a` | TX_EN | EN/IN1 (1) | pio1 / M3 | IN1 PWM pulse, positive half-cycle |
| `tx_b` | TX_PH | PH/IN2 (2) | pio2 / L3 | IN2 PWM pulse, negative half-cycle |
| — | TX_PMODE | PMODE (16) | pio8 / B15 | **drive HIGH** = IN1/IN2 (PWM) interface mode to match tx_a/tx_b |
| — | TX_NSLEEP | nSLEEP (3) | pio48 / V8 | internal pull-down: bridge asleep until FPGA drives it high |

REVIEW-2026-08-26 S3: an earlier revision of this table (and the T-013 on-sheet
text box) said pio44 — wrong per `orchestration/pinmap.md` (pio44/U3 is
ETH_RXD1, an input). Pinmap, the XDC (V8), and this table agree on pio48.
**Open schematic repair (flagged in T-013 Log + STATUS blockers):** the T-013
netlist audit recorded TX_NSLEEP on J40.44 in `digital.kicad_sch`; that global
label must move to J40.48 before CP-C.
| `tx_limit_fault`/nFAULT | TX_NFAULT | nFAULT (4) | pio5 / C15 | open-drain, 10k pull-up (R170) to +3.3V on TX sheet |

Current limit: VREF = +3.3V, R_IPROPI = 1.69 kΩ → trip ≈ 1.95 A; chopping never
engages (transducer currents ~50 mA pk). IMODE strapped to GND (R172).
**Open datasheet-verification items for CP-C** (offline during T-013): PMODE
polarity (high = IN1/IN2 PWM), IMODE=GND mode name, C284 = 47 nF CPH–CPL value
(draft had 22 nF), **confirm the IN1/IN2 truth table against the DRV8876
datasheet (00 = coast/Hi-Z, 11 = brake/low-side, 01/10 = drive) — the S4
idle-behavior text above depends on it**. None affect the safety envelope
below.

## Waveform math (revised 2026-08-26, REVIEW B2)

`tx_nco_pwm` (12 MHz sysclk, PHASE_BITS=24, PWM_BITS=8):
- output frequency `f = 12e6 · phase_increment / 2^24`; chirp via signed
  `phase_increment_delta` (Q8 fractional LSBs per cycle).
- **Duty gating is derived from the NCO phase itself; there is no independent
  PWM carrier.** Within each half-cycle the active output is high only while
  the top PWM_BITS of the sub-half-cycle phase are below `amplitude`, i.e. for
  the first `d = amplitude/256` of every half-cycle. The pre-fix design chopped
  with a free-running 256-clock carrier (46.875 kHz, 21.33 us) that is LONGER
  than a 40 kHz half-cycle (12.5 us): carrier and half-cycle boundaries drifted
  past each other, so 15.7% of half-cycles landed entirely inside the carrier
  on-window and ran at ~100% duty at amplitude=187 — the mean stayed exactly
  on target, so averaged checks passed while the per-half-cycle bound failed
  (REVIEW-2026-08-26 B2).
- **Hard bound (re-derived from the actual arithmetic):** the pulse occupies
  exactly `amplitude/256` of each half-cycle's *phase* range. In clocks,
  `on_clocks ≤ floor(amplitude·T_half/256) + 2` (±1 clock of phase
  quantization at each pulse edge) for ANY frequency or chirp rate. At 40 kHz,
  amplitude 187: target duty 73.05%, worst half-cycle ≤ 74.5% — vs 100%
  pre-fix. Regression: `gateware/sim/tb_tx_duty_bound.sv` runs the reviewer's
  exact config (PHASE_BITS=24, phase_increment=55924, amplitude=187, 12 MHz,
  200k clocks = 1333 half-cycles), an amplitude 0..255 sweep, both chirp
  endpoints (27962/44739) at amplitude 187 and 255, and a 20→32 kHz ramp —
  ZERO half-cycles over the bound; the pre-fix RTL fails it with 594
  half-cycles over bound in the reviewer config alone.
- Differential output **fundamental** peak = **(2·VM/π)·(1 − cos(π·d))**,
  d = amplitude/256. For this phase-gated pulse waveform (pulse width d·T/2
  per half-period) the Fourier result is exact: d=1 → 4·VM/π ≈ 15.3 Vpk
  (30.6 Vpp fundamental-equivalent at VM=12 V). The ±2-clock quantization
  wobble is a 40–80 kHz modulation, <0.1 dB, averaged out by the resonant
  transducer; the amplitude≤187 derivation below keeps its ~0.1 V worst-case
  headroom implicitly (12.70 Vpk vs the 12.73 Vpk target, quantization
  worst-case 12.83 Vpk — accept, and trim at CP-E per the scope check).
- **Duty-chopping never bounds TERMINAL excursion (REVIEW S5).** OUT1/OUT2
  always swing rail-to-rail: J50 sees 0..24 V differential transitions
  (**24 Vpp** at VM=12 V) for ANY nonzero amplitude. The envelope above bounds
  only the fundamental component and is valid only for a transducer that is
  resonant/narrowband at the drive frequency and whose voltage rating is a
  drive (fundamental) figure. If a transducer's Vpp rating is a TERMINAL
  limit, no amplitude setting makes a 12 V bridge safe — use a reduced VM
  setpoint or a series element. v1 default TX path per
  `decisions/D013` (proposed; needs Joshua's ratification at CP-B/CP-C).
- Idle/reset/reject: IN1=IN2=0. In the DRV8876's IN1/IN2 (PWM) interface mode
  (PMODE high) **00 = COAST: both half-bridges Hi-Z** — an earlier revision of
  this line claimed "both half-bridges low-side, transducer at 0 V", which is
  the **11 (brake / low-side slow-decay)** state, not 00 (REVIEW S4).
  Consequence for burst off-intervals: the bridge is open, so the resonant
  element is undriven and floats; its stored energy rings down through the
  transducer's own capacitance and the bridge body diodes rather than being
  actively damped. That is acceptable for the T-001 burst/blind-zone schedule
  (and avoids shoot-through risk from driving a brake state), but terminal
  voltage during ring-down is not clamped to the rails. If active braking is
  ever wanted, drive IN1=IN2=1 during the off-interval (gateware change).

## Enforced envelope (per selected transducer)

| Parameter | MA40S4S (narrowband, D007 default) | Piezo horn tweeter (20–32 kHz chirp) |
|---|---|---|
| Frequency | **40.0 kHz fixed tone only** — `phase_increment = 55924`, `phase_increment_delta = 0` | chirp 20–32 kHz: `phase_increment` 27962–44739; ramp must never exceed 55924 |
| `MAX_PHASE_INCREMENT` | 24'd55924 (40 kHz ceiling) | 24'd55924 |
| `MAX_AMPLITUDE` | **8'd187** (see derivation) | 8'd255 hardware full scale, **but keep ≤187 until the purchased tweeter's Vpp rating is confirmed** |
| `MAX_BURST_CYCLES` | 32'd120000 (10 ms @ 12 MHz); MA40S4S is rated for *continuous* square drive at ≤20 Vpp, so burst repetition is not thermally limited at amplitude ≤187 | 32'd120000 (10 ms); blind-zone schedule per T-001 |
| Absolute voltage ceiling | **20 Vpp continuous square wave** (Murata datasheet Table 1, `sonar-v1-pcb/data_sheets/ultrasonics.pdf`) | TBD from purchased part (T-007 item) |

### MA40S4S amplitude derivation
Full-scale bridge = 24 Vpp > 20 Vpp limit. Fundamental-equivalence against a 20 Vpp
square (fundamental peak (4/π)·10 = 12.73 Vpk):

    (2·12/π)·(1 − cos(π·d)) ≤ 12.73  →  d ≤ 0.732  →  amplitude ≤ 187/256

Conservative (resonant transducer responds to the fundamental); **verify
differential Vpp at J50 with a scope at CP-E bring-up** and trim down if the
measured waveform exceeds 20 Vpp.

## Notes for T-020 / sonar_top.sv
Current generic bounds (`MAX_PHASE_INCREMENT=55924`, `MAX_AMPLITUDE=128`,
`MAX_BURST_CYCLES=120000`) are already inside this envelope; 128 (=15.3 Vpp
fundamental-eq) is the safe bring-up value, 187 the MA40S4S ceiling. Select the
envelope at build/config time by transducer — the gateware limit check is the
enforcement point requested by STATUS.md/T-001.
