# 2026-08-25 — codex: T-001 link-budget model

## Session setup

- Read the required protocol/state/architecture/conventions, ROADMAP, newest journal,
  and the ratified decisions relevant to T-001.
- Preserved the prior Claude session's orchestration baseline as commit `9c62924`,
  explicitly excluding Joshua's pre-existing `sonar-v1-pcb/sonar.kicad_pro` change.
- Claimed T-001 on `main` in commit `7757bae`, then worked on
  `agent/T-001-link-budget-model`.
- Used parallel read-only research for atmospheric absorption/sonar conventions,
  manufacturer microphone data, and TX/target/chirp assumptions. Two additional
  read-only agents independently audited the code and ticket acceptance.

## Delivered

- `analysis/link_budget.py`: parameterized ISO 9613-1 absorption; point-target sonar
  equation; transmitter voltage/frequency models; target strengths; manufacturer-
  derived/provisional microphone noise curves; linear-power noise integration;
  matched-filter/array gain; blind-zone/range-resolution calculations; max-range
  root solving; CLI and internal sanity checks.
- `analysis/link_budget.md`: sourced assumptions, results, plots, limitations, and
  scheduler recommendations.
- Deterministic generated artifacts:
  - five PNG plots (absorption, microphone delta, person margin, max range, blind zone)
  - three CSVs (microphone-band summary, max-range summary, blind-zone schedule)
- `.gitignore`: Python bytecode/cache exclusions for the new analysis script.

## Findings

- The exact PLAN anchor is +39.80 dB at 10 m (rounded +40 dB) and about 30.5 m to
  zero margin.
- ISO 9613-1 gives 0.732 dB/m one-way at 25 kHz, 20 C, and 50% RH; the PLAN's
  0.5 dB/m is plausible but condition-specific. The difference costs 4.63 dB
  round-trip at 10 m.
- Provisional reference case (104 dB SPL wideband source, person TS=-10 dB,
  ICS-41352 typical curve, 30 dB SPL/8 kHz ambient, 12 kHz x 6.6 ms chirp):
  +27.09 dB at 10 m and 20.18 m zero-margin range.
- ICS-41352 versus IM73A135 over 20-32 kHz: +2.34 dB microphone-only, but +0.15 dB
  after the stated ambient noise. T5838's typical curve is quieter than the analog
  estimate. D011 is not nominally SNR-gated; keep the physical bake-off because
  curves are typical/provisional and port geometry matters.
- At 25 kHz the small-object (TS=-30 dB) zero-margin range is 12.35 m, so small
  targets are much closer to the design limit than people.
- MA40S4S is a narrow 40 kHz part. Murata publishes no SPL below 30 kHz, and the
  12 V full bridge's 24 Vpp exceeds its 20 Vpp continuous-square limit. T-013 must
  enforce the actual chosen transducer's waveform limit.
- No exact normalized wideband candidate response exists yet. The 104 dB SPL model
  is a calibrated-class placeholder with +/-10 dB uncertainty and must be replaced
  by a one-metre sweep.
- Default blind-zone schedule at 12 kHz bandwidth spans 0.129 m for a 0.5 ms chirp
  plus 0.25 ms guard through 1.548 m for an 8 ms chirp plus 1 ms guard. These are
  conservative blanked-RX values; separate TX/RX may permit leakage cancellation.

## Verification

```text
$ python3 analysis/link_budget.py
Sonar v1 link-budget outputs generated
  Anchor margin at 10 m: 39.80 dB
  24-channel array gain: 13.80 dB
  Scenario pulse-compression gain: 18.99 dB
  Scenario absorption at 25 kHz (20 C, 50% RH): 0.732 dB/m
  Primary Option C person margin at 10 m: 27.09 dB
  Primary Option C person zero-margin range: 20.18 m
  ICS-41352 mic-only / ambient-context penalty over 20-32 kHz: 2.34 / 0.15 dB
  12.0 kHz range resolution: 0.0143 m
  6.6 ms chirp + 1 ms guard blind zone: 1.307 m
  Output directory: .../analysis/generated
```

- `ruff check analysis/link_budget.py` — passed.
- `ruff format --check analysis/link_budget.py` — already formatted.
- `python3 -m py_compile analysis/link_budget.py` — passed.
- `git diff --check` — passed.
- Fresh-directory generation matched every committed PNG/CSV byte-for-byte.
- `--drive-v-rms nan` is rejected by argparse with exit status 2; the audit's
  non-finite-input range bug is closed.
- Both independent audits accepted numerical consistency and DoD coverage after
  evidence labels/proxy uncertainties were corrected.

## Exact next steps

1. Pick T-002 (next priority-1 ready ticket). Confirm lifecycle/orderability and
   exact ultrasonic-mode specs for T5838, ICS-41352/41350, and SPH0641LU4H.
2. T-008 should use the named proxy uncertainties from the CSV, select the mic,
   and define the physical bake-off/calibration that replaces the provisional curves.
3. T-007 should not treat an unnormalized wideband-piezo SPL claim as link-budget
   evidence; purchase candidates for measurement, without agents spending money.
4. T-013 must honor the selected transducer's waveform/voltage limit and add a
   controllable amplitude/duty strategy.
5. CP-B should revisit D011 only if measured mic/port noise or correlated room noise
   consumes the documented person margin; small-target performance remains a
   separate sensitivity decision.

No KiCad design file was edited in this session. Joshua's existing
`sonar-v1-pcb/sonar.kicad_pro` modification remains untouched.
