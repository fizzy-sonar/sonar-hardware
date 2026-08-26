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
| — | TX_NSLEEP | nSLEEP (3) | pio44 / V8 | internal pull-down: bridge asleep until FPGA drives it high |
| `tx_limit_fault`/nFAULT | TX_NFAULT | nFAULT (4) | pio5 / C15 | open-drain, 10k pull-up (R170) to +3.3V on TX sheet |

Current limit: VREF = +3.3V, R_IPROPI = 1.69 kΩ → trip ≈ 1.95 A; chopping never
engages (transducer currents ~50 mA pk). IMODE strapped to GND (R172).
**Open datasheet-verification items for CP-C** (offline during T-013): PMODE
polarity (high = IN1/IN2 PWM), IMODE=GND mode name, C284 = 47 nF CPH–CPL value
(draft had 22 nF). None affect the safety envelope below.

## Waveform math

`tx_nco_pwm` (12 MHz sysclk, PHASE_BITS=24, PWM_BITS=8):
- output frequency `f = 12e6 · phase_increment / 2^24`; chirp via signed
  `phase_increment_delta` (Q8 fractional LSBs per cycle).
- duty `d = amplitude / 256`: EN-chopping within each half-period.
- Differential output fundamental peak = **(2·VM/π)·(1 − cos(π·d))**
  (d=1 → 4·VM/π ≈ 15.3 Vpk = 30.6 Vpp fundamental-equivalent at VM=12 V).
- Idle/reset/reject: IN1=IN2=0 → both half-bridges low-side, transducer at 0 V. Safe.

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
