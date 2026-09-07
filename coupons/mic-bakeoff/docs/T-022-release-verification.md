# Rev B coupon repair verification — T-022

Verified 2026-09-06, Codex, KiCad 10.0.1. This closes the electrical/physical
R1/R2 engineering hold from [the independent review](../../../orchestration/review/REVIEW-2026-09-05.md).
It does **not** approve purchases, establish acoustic performance, release a
production microphone, or sign off the unfinished main PCB.

## Independent manufacturer audit

Primary source: [TI SCAS895B, February 2017, section 5 (PW-24 column)](https://www.ti.com/lit/ds/symlink/cdclvc1112.pdf),
fetched 2026-09-05. The checker has its own transcription, not an import of the
generator table. It checks the schematic pin names AND actual board pad nets.

| Pin | TI function | Coupon net |
|---:|---|---|
| 1 | CLKIN | CLK_IN |
| 2 | 1G | CLK_EN |
| 3 | Y0 | CLK_Y0 → R0 → four-mic CLK_ST branch |
| 4 | GND | GND |
| 5 | VDD | +3V3_MIC |
| 6 | Y4 | unconnected |
| 7 | GND | GND |
| 8 | Y6 | unconnected |
| 9 | VDD | +3V3_MIC |
| 10 | Y9 | unconnected |
| 11 | GND | GND |
| 12 | Y11 | unconnected |
| 13 | VDD | +3V3_MIC |
| 14 | Y10 | unconnected |
| 15 | GND | GND |
| 16 | Y8 | unconnected |
| 17 | Y7 | unconnected |
| 18 | VDD | +3V3_MIC |
| 19 | Y5 | unconnected |
| 20 | GND | GND |
| 21 | Y2 | unconnected |
| 22 | VDD | +3V3_MIC |
| 23 | Y3 | unconnected |
| 24 | Y1 | CLK_FBR → R1 → CLK_FB / TP6 / J1.9 |

All five supply terminals have a nearby 100 nF bypass, following TI section 10:
C5→22, C6→13, C7→5, C8→9, C11→18. C9/C10 remain 1 µF/10 µF bulk capacitors.
The 1G pull-down remains R12; no DATA pull resistors were introduced.

## Repairs and verification boundaries

- Both PCB instances are placed from the same canonical footprint libraries
  using KiCad's transforms. Rotated 0603 pads no longer touch. Pad centres are
  1.6 mm apart; pad size is 0.9 × 1.0 mm before rotation.
- Schematic symbol fields are outside the bodies, mic symbols are widened and
  components are spaced into readable groups. Net parity and exact ERC waiver
  checks rerun after the presentation changes; pin connections are unchanged.
- The mic GND custom pad now has a 0.1 mm anchor inside the annulus, not a disk
  filling the aperture. Copper and paste retain Ø1.625/Ø1.025 mm annular geometry;
  actual effective polygons are sampled through the clear interior. Four Ø0.50 mm
  acoustic drills per board remain NPTH. Copper Gerbers show clear ports on all
  four layers; paste shows open rings; mask plots show the central drill opening.
- All supply/ground pad routing was rebuilt from the corrected map. TP6 is
  outside U1 and correctly measures the returned clock **after** R1.
- Coupon rules explicitly use 0.127 mm copper clearance and 0.25 mm minimum
  through-hole drill, rather than inherited 0.2 mm routing defaults. Minimum
  audited outer-layer different-net gaps are SPH 0.150 mm and ICS 0.145 mm.
  There are no added per-item DRC exclusions or waived shorts. The full reports
  include KiCad's default ignored-check list; do not interpret zero DRC as an
  exhaustive fabricator DFM certification.
- Full DRC is mandatory both in the suite and before fab export. Failure or a
  sandbox abort stops the workflow. The independent geometry checker includes
  same-footprint and no-net pads; four in-memory negative tests per variant prove
  that wrong U1 power assignment, same-footprint short, no-net-pad contact, and a
  port-filling anchor are rejected. The source files are not mutated by these tests.
- Exact schematic/PCB net parity: **94 numbered pads per variant**. ERC retains
  exactly four reviewed messages (same types AND pin participants): two paired
  DATA output joins and two bench-power-not-driven reports. No blanket count-only
  acceptance of arbitrary ERC messages remains.
- Genuine metric CSV now contains **21 SMD components** per board, with rotation
  assertions. BOM has **23 components** including the two THT headers. Bare copper
  test points are excluded. Separate PTH/NPTH drill files and their exact acoustic
  coordinates are checked. The obsolete generated mixed-plating drill file is
  removed by the exporter; it can be regenerated from the historical source.
- Assembly `-pos.csv` uses **package centres**, not acoustic-port anchors. In PCB
  top-view coordinates SPH body centre = port + (0, 0.971 mm), ICS = port +
  (0.710 mm, 0), from the footprint's manufacturer body drawing. The independent
  export checker asserts these offsets; CSV Y has the opposite sign. Raw
  `-origin-pos.csv` is retained for traceability, not placement. Any future mic
  rotation or bottom-side placement fails the transform until explicitly audited.

## Commands and durable evidence

Run from the repository root, with coupon projects closed:

```sh
UV_CACHE_DIR=build/uv-cache uv run --with matplotlib --with ruff==0.14.0 \
  bash coupons/mic-bakeoff/check_coupons.sh
UV_CACHE_DIR=build/uv-cache uv run --with gerbonara==1.6.3 \
  python coupons/mic-bakeoff/inspect_fab.py --render
bash scripts/check.sh
```

All exited **0**. On this Mac full DRC requires approved host access. The first
command regenerates twice and requires byte-identical sources, runs fresh ERC,
netlist/BOM exports, filled-board DRC, independent/negative checks, fabrication
export checks, analyzer self-tests, pinned Ruff and whitespace checks.

Both full DRC reports: **0 violations / 0 unconnected pads / 0 footprint errors**.
The main repository harness completed with its **existing** baselines: sonar ERC
346; sonar DRC 175/499/0; rx_amp_sim and txrx_dev DRC 1/0/0 each. Main-board
violations are not fixed or approved by this ticket; Joshua's project edit is preserved.

Durable logs, DRC/ ERC reports, source/export SHA256 manifests and actual Gerber
inspection images are under
[`orchestration/review/evidence-2026-09-06-t022/`](../../../orchestration/review/evidence-2026-09-06-t022/).
Gerbonara 1.6.3 + librsvg rendered the actual copper/paste/mask Gerbers, independently
of KiCad's board SVGs; all twelve images were visually inspected. Export timestamps
change hashes on later runs; source regeneration itself is byte-identical.

## Remaining CP-BM / DFM gates

Joshua retains purchase/bench/MPN-release authority. Refresh stock, lifecycle and
quotes for the exact MPNs; no prices or availability were refreshed by T-022.
Have the assembler confirm mic/U1 pin-1 rotation and the absolute-mm negative-Y
CSV convention; do not treat KiCad's raw rotations as supplier-normalized angles.
Confirm NPTH acoustic holes, annular stencil, no washing, port tolerances, stackup
and tooling/panelization. Request **1 oz outer copper**, not 2 oz.

[JLCPCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities), checked
2026-09-05, support the intended track/space and drill sizes for multilayer 1 oz.
However, the coupon's 0.8 mm / 0.12 mm reference legends are below the published
1.0 mm / 0.15 mm legibility recommendation. Ask DFM to enlarge or omit the small
reference legends as appropriate; do not silently alter pads, ports or nets.
This cosmetic assembly-review item does not re-open the resolved electrical short
findings. Confirm the final manufacturing preview before approving a purchase.

First-power testing remains current-limited with no microphones assumed good.
Measure supply current, clock-enable behavior, four-load waveform/skew and DATA
sharing, then execute T-016's calibrated acoustic bake-off. T-023/T-024/T-025 still
own the integrated capture, live processing and first-echo demonstration gaps.
