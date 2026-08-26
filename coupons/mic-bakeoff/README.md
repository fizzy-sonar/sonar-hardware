# T-016 PDM microphone bake-off coupon package

_Coupon package for the SPH0641LU4H-1 vs ICS-41352 quantitative bake-off
(`orchestration/tickets/T-016-pdm-mic-coupon-bakeoff.md`, normative fixture/gate text
in `docs/pdm-rx-design.md` "Quantitative release gate"). Generated 2026-08-26 by
codex/terra-t016. **Nothing here authorizes a purchase; CP-BM is Joshua's gate.**

## Contents

| Path | What |
|---|---|
| `sph-coupon/`, `ics-coupon/` | KiCad 10 projects, one per exact candidate land pattern |
| `generate_coupon.py` | Single data-driven source for both variants (edit + regenerate) |
| `verify_coupon.py` | Geometric verification (needs KiCad-bundled python for pcbnew) |
| `fab_export.py` | Zone fill + gerber/drill/position/SVG export |
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
- 3.3 V rail through JP1 current-break jumper; bulk 10 uF + 1 uF; 100 nF C0G at
  every mic and each used U1 VDD pin.
- J1 2x5 bench header: 1 +3V3_IN, 2 GND, 3 D0, 4 D1, 5 GND, 6 CLK_IN, 7 CLK_EN,
  8 GND, 9 CLK_FB, 10 GND.
- Test points: TP1 +3V3_MIC, TP2 clock near (source end of trunk), TP3 clock far
  (last load), TP4 D0 (bottom side), TP5 D1 (bottom side), TP6 CLK_FBR.
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

## UNVERIFIED item (must close before order)

- **CDCLVC1112PWR pin map** (`BUFFER_PIN_MAP` in `generate_coupon.py`): the TI
  datasheet was not available offline in this session. The symbol/footprint pin
  assignment is a placeholder grid. Confirm against the TI CDCLVC11xx datasheet
  (24-pin TSSOP pinout), fix `BUFFER_PIN_MAP` if needed, regenerate, re-run
  `check_coupons.sh`. Everything else is datasheet-anchored.

## Verification status (this session)

- `verify_coupon.py`: both variants — 0 unconnected after zone fill; min
  different-net copper gap 0.145–0.150 mm (>= 0.127 target); 4x 0.50 mm NPTH at
  the mic centres; J1 pin map and mic pad-1 quadrants asserted.
- `kicad-cli sch erc`: 4 remaining messages per variant, all reviewed waivers:
  2x `pin_to_pin` output-output on the intentional SELECT-paired DATA merge
  (PDM half-cycle tri-state sharing), 2x `power_pin_not_driven` (passive
  net-label power distribution on a bench coupon).
- **`kicad-cli pcb drc` could not run in this sandbox** (SIGABRT on any board,
  including known-good repo boards; the T-006 harness needed approved unsandboxed
  runs). The geometric audit in `verify_coupon.py` substitutes here; **re-run
  `scripts/check.sh`-style `kicad-cli pcb drc` unsandboxed before ordering.**
- Gerber/drill/position export verified end-to-end with zones filled.

## ERC waivers (reviewed)

1. `pin_to_pin` Output↔Output on D0M/D1M — intentional PDM SELECT pairing.
2. `power_pin_not_driven` on +3V3_MIC/GND — labels, not power symbols, by design.
