# T-016 PDM microphone bake-off coupon package

_Coupon package for the SPH0641LU4H-1 vs ICS-41352 quantitative bake-off
(`orchestration/tickets/T-016-pdm-mic-coupon-bakeoff.md`, normative fixture/gate text
in `docs/pdm-rx-design.md` "Quantitative release gate"). Rev B repaired and
verified 2026-09-06 under T-022. **Nothing here authorizes a purchase; CP-BM is Joshua's gate.**_

## Contents

| Path | What |
|---|---|
| `sph-coupon/`, `ics-coupon/` | KiCad 10 projects, one per exact candidate land pattern |
| `generate_coupon.py` | Single data-driven source for both variants (edit + regenerate) |
| `place_library_footprints.py` | Places canonical library geometry using KiCad transforms |
| `verify_coupon.py` | Geometric verification (needs KiCad-bundled python for pcbnew) |
| `fab_export.py` | Zone fill + gerber/drill/position/SVG export |
| `inspect_fab.py` | Actual drill/CSV/BOM checks, hashes, optional independent Gerber rendering |
| `docs/T-022-release-verification.md` | Manufacturer pin audit, repair evidence and remaining DFM gates |
| `check_coupons.sh` | One-command verification + export runner |
| `docs/order-package.md` | BOMs, quantities, JLCPCB order parameters, pricing table |
| `docs/sourcing-evidence.md` | Dated lifecycle/sourcing evidence for both exact MPNs |
| `docs/runbook.md` | Calibration, reseat, and bench measurement procedure |
| `docs/fixture-drawing.md` | Fixture geometry and uncertainty-budget template |
| `docs/raw-data-schema.md` | `pdm-bakeoff-dataset/1` JSON schema consumed by `analysis/pdm_bakeoff.py` |
| `acquisition/capture-config.yaml` | Bench capture configuration (contract constants) |

## Coupon design (both variants)

- Four candidate microphones (M1..M4, 12 mm pitch) on one CDCLVC1112PWR clock
  output (Y0 through R0 = 10 ohm): the production worst-case four-load branch.
- M1/M3 SELECT low, M2/M4 SELECT high; DATA merged pairwise (D0 = M1+M2,
  D1 = M3+M4) through 0-ohm isolation footprints R13/R14. **No pulls on D0/D1.**
- Returned clock Y1 through R1 to J1 pin 9 (`CLK_FB`) for skew measurement.
- 3.3 V rail through JP1 current-break jumper; bulk 10 uF + 1 uF; 100 nF X7R 0603
  at every mic and all five U1 VDD pins (C5–C8 + C11; dielectric changed from C0G 2026-08-26,
  REVIEW S11: 100 nF C0G is not manufacturable in 0603; X7R DC-bias droop at the
  3.3 V rail is acceptable — these are digital PDM mics whose PSRR covers residual
  rail noise, and the 10 uF + 1 uF bulk caps carry the low-frequency load).
- J1 2x5 bench header: 1 +3V3_IN, 2 GND, 3 D0, 4 D1, 5 GND, 6 CLK_IN, 7 CLK_EN,
  8 GND, 9 CLK_FB, 10 GND.
- Test points: TP1 +3V3_MIC, TP2 clock near (source end of trunk), TP3 clock far
  (last load), TP4 D0 (bottom side), TP5 D1 (bottom side), TP6 CLK_FB (after R1).
- Four 0.50 mm **NPTH** acoustic ports centred on the package ports; identical
  stack-up/mask/exterior geometry on both variants; no copper/mask/paste in the
  port (fenced by the annular GND pad and drill). Fab note on Cmts.User;
  no-wash handling note in silk.
- 70 x 30 mm, 4-layer 1.6 mm (JLC04161H-7628 intent: F.Cu signal / In1 GND /
  In2 3V3_MIC / B.Cu signal+GND), ENIG, four M2 mounting holes.

## Land-pattern provenance (verified against local primary datasheets 2026-08-26)

- **SPH0641LU4H-1**: Knowles Rev B (2015-04-06). Example land pattern (sheet 10,
  PCB-side view) + pin table (sheet 9): 1 DATA, 2 SELECT, 3 GND ring, 4 CLOCK,
  5 VDD. Pads 0.725 x 0.522 mm; columns +/-0.8375 mm; rows +1.513/+2.335 mm from
  port centre; ring Ø1.625/Ø1.025; port Ø0.325±0.05; body 3.50x2.65x0.98.
- **ICS-41352**: TDK DS-000048 Rev 1.0. Pin configuration Figure 3 ("Top View,
  Terminal Side Down" = PCB-side view) + Figure 16 land dimensions + Figure 18
  bottom view: 1 DATA, 2 SELECT, 3 GND ring, 4 CLK, 5 VDD. Pads 0.522 x 0.725 mm
  at (1.252/2.074, ±0.8375) mm from the port; ring Ø1.625/Ø1.025; port Ø0.375;
  PCB hole 0.5-1.0 mm recommended; body 3.50x2.65x0.98.
- The two footprints are **not** compatible (pad arrangement transposed and
  differently numbered); no shared/dual footprint is used, per the ticket.
- DFM note for Joshua: the ICS datasheet's Figure 16 pad *numbering* must be
  read together with Figure 3 (Figure 16's pads are unlabeled); this package
  follows Figure 3's explicit PCB-side view. Ask JLC DFM to confirm pick-and-place
  rotation against the pin-1 corner mark before assembly.

## Verification status — 2026-09-06, KiCad 10.0.1

- CDCLVC1112PWR complete PW-24 pin table independently checked against TI
  SCAS895B section 5. Both schematic symbols and all 24 actual PCB pads pass;
  schematic/PCB pin-net parity is exact for all 94 numbered pads per variant.
- Full zone-refilled KiCad DRC: **0 violations, 0 unconnected pads, 0 footprint
  errors on BOTH variants**. No short or clearance violations waived. See the
  [release record](docs/T-022-release-verification.md) for rule scope and raw logs.

- `verify_coupon.py`: both variants — 0 unconnected after zone fill; min
  different-net copper gap 0.145–0.150 mm (>= 0.127 target); 4x 0.50 mm NPTH at
  the mic centres; J1 pin map and mic pad-1 quadrants asserted.
- `kicad-cli sch erc`: 4 remaining messages per variant, all reviewed waivers:
  2x `pin_to_pin` output-output on the intentional SELECT-paired DATA merge
  (PDM half-cycle tri-state sharing), 2x `power_pin_not_driven` (passive
  net-label power distribution on a bench coupon).
- Negative tests reject a wrong U1 supply pin, a same-footprint short, a no-net
  pad touching ground, and a copper/paste anchor filling an acoustic aperture.
- Actual Gerbers visually inspected using an independent renderer. Separate
  PTH/NPTH drills, 21 body-centroid SMD placements in genuine metric CSV and 23 BOM components
  checked; bare test pads are not assembly components. Five 100 nF buffer bypasses.
- Generator output is byte-identical across two runs. Full DRC is now mandatory
  in the runner and exporter; a sandbox crash fails the check, never substitutes
  a custom audit. Run with approved host access on macOS if needed:

```sh
UV_CACHE_DIR=build/uv-cache uv run --with matplotlib --with ruff==0.14.0 \
  bash coupons/mic-bakeoff/check_coupons.sh
UV_CACHE_DIR=build/uv-cache uv run --with gerbonara==1.6.3 \
  python coupons/mic-bakeoff/inspect_fab.py --render
```

Requires KiCad 10 (including its `pcbnew` Python), `rg`, and `rsvg-convert` for
optional Gerber rendering. Set `KICAD_PYTHON` for non-default installs. Close
the coupon projects before regeneration and reload after changes.

## ERC waivers (reviewed)

1. `pin_to_pin` Output↔Output on D0M/D1M — intentional PDM SELECT pairing.
2. `power_pin_not_driven` on +3V3_MIC/GND — labels, not power symbols, by design.
