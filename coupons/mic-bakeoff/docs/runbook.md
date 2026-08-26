# T-016 bench runbook — calibration, reseat, acquisition

_Normative gates and the exact estimator live in `docs/pdm-rx-design.md`
("Quantitative release gate") and the T-016 ticket; this runbook is the
executable procedure that produces a `pdm-bakeoff-dataset/1` JSON file for
`analysis/pdm_bakeoff.py`. Joshua (or Joshua-supervised) operates the bench at
CP-BM. Agents analyze files; they do not run the bench._

## 0. Pre-bench checklist

1. Assembled coupons: 3 SPH + 3 ICS (4 mics each), logged by serial; every
   installed unit and assembly failure logged (coupon X-ray/AOI notes if
   available).
2. Port inspection BEFORE first power: 100% of the 12 ports per candidate meet
   the fab drawing: 0.50 mm hole, non-plated, free of copper/mask/paste/debris;
   calibrated imaging shows no aperture clipping. Record package-to-hole offset
   per unit (calibrated image, 0.01 mm resolution or better).
3. Calibrated reference microphone with current calibration artifact (dated,
   with stated uncertainty), wideband TX source able to reach >=117 dB SPL at
   the coupon plane (else the overload gate is `unverified` by rule), fixture
   per `fixture-drawing.md`, oscilloscope (>=500 MHz, <=1 ns edge fidelity),
   current measurement (inline DMM or sense amplifier at JP1).
4. Capture host per `../acquisition/capture-config.yaml`; decimator revision
   recorded. SPH coupons run at 3.072 MHz, ICS at 4.8 MHz; one SPH coupon
   additionally at 4.8 MHz as the clock-rate diagnostic.
5. Startup sequence per `docs/pdm-capture-contract.md`: rails settle, 1.536 MHz
   for >=50 ms, glitchless switch to target rate, discard first 10 ms. Ten
   startup/mode-switch cycles per coupon must show no contention/stuck channel.

## 1. Calibration chain (brackets every paired block)

- Reference mic on fixture reference position; sweep 20–32 kHz, <=500 Hz bins,
  time-gated. Record reference response + noise floor of the acquisition chain.
- Record the fixture budget's expanded k=2 term for every absolute and paired
  decision bin and the integrated band. Each must be <=1.0 dB or the comparison
  is fixture-invalid (not a mic failure).
- Repeat the reference measurement AFTER each SPH/ICS pair block; before/after
  reference drift must be <=0.5 dB magnitude / 5 deg phase.
- Pairing: predeclared identity blocks — coupon q, site u, reseat r for SPH and
  ICS are paired BEFORE seeing results; alternate acquisition order (SPH first
  on odd blocks, ICS first on even); never re-pair.

## 2. Per-channel acoustic records

For every channel (4 per coupon) and every reseat (3 independent reseats —
full unmount/remount with fixture pose logged):

1. Calibrated time-gated 20–32 kHz sweep, bins <=500 Hz. Save raw PDM and the
   decimated record.
2. Three TX-off noise records through the same PDM/host decimator (simultaneous
   ambient/acquisition-floor record through the reference channel).
3. Fixture pose, temperature, humidity, clock rate, supply voltage logged.

Gain normalization: one scalar gain per unit (band-integrated), applied by the
bench pipeline; store the applied gain in the record.

## 3. Electrical/timing records (per coupon, scope at TP2 near / TP3 far)

- Clock frequency, duty, rise/fall at TP2 and TP3; returned-clock-to-load skew
  (TP6 vs TP2/TP3); DATA enable/high-Z timing (tDD/tDZ equivalents per MPN
  datasheet) and paired handoff on D0/D1. Every reading recorded WITH its
  measurement uncertainty. SPH four-load branch limits: 48–52% duty, <=3 ns
  edges, tDD <=40 ns, tDZ >=3 ns; board skew allocation <=0.500 ns. ICS limits
  come from the DS-000048 revision on the bench (enter into the dataset's
  `datasheet_limits`).
- Ten startup/mode-switch cycles: log pass/fail per cycle.
- Rail: JP1 opened, measure 3.3 V coupon current at operating clock; extrapolate
  24-mic + clock-tree load; record observed peak. Limits: steady estimate
  <=80 mA, peak <100 mA (T-012 rail gate).

## 4. Overload/recovery

- Raise TX level to find the 10%-THD point (>=117 dB SPL required; no more than
  3 dB below the other candidate). If the fixture cannot reach 117 dB SPL,
  record `unverified` — never mark pass.
- After a direct-TX burst, record time for response/noise to return within 1 dB
  of pre-burst. <=250 us pass; 250 us–1 ms → flag for the T-001 1 ms guard +
  conditional human review; >1 ms fail.

## 5. Dataset assembly and analysis

1. Assemble `dataset.json` per `raw-data-schema.md`. Every metric field carries
   provenance (file hash, calibration artifact version).
2. `python3 analysis/pdm_bakeoff.py --dataset dataset.json --report-json report.json --report-md report.md`
3. The report's gates and selection outcome are reproduced verbatim in the
   T-016 ticket Log. If the outcome is `inconclusive`/`freeze-neither`/
   `joshua-component-choice`/`prepare-ics-decision`, follow the ticket's
   explicit selection rule text — Joshua ratifies any waiver or ICS choice.
4. Only after Joshua ratifies the release record (exact MPN, footprint revision,
   clock rate, calibration artifact version, source evidence, threshold results,
   any waiver) does T-010 unblock.
