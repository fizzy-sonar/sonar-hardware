# T-022 coupon rev B repair — 2026-09-05/06

## Scope and safety

Joshua said continue after the independent review. Claimed T-022 on main
(`08f83c1`), worked on `agent/T-022-coupon-release-repair`. No KiCad editor running
before regeneration (checked again on 2026-09-06). Both coupon projects/libraries
changed on disk; reload. Preserved the user's existing main-project `.kicad_pro`
edit. No remote publication, purchase, spending or decision ratification.

## Delivered

- Complete TI SCAS895B PW-24 pin map and all routed supply/output connections
  corrected; independently asserted without importing the generator's map.
- 0603 pad spacing/orientation fixed through canonical library placement using
  KiCad transforms. Acoustic annular-pad anchor moved into the ring; no copper or
  paste disk in the port. Courtyards/silk collisions repaired, TP6 after R1, fifth
  buffer bypass C11 added and all five bypasses placed by supply pins.
- Full DRC required by runner and exporter; deterministic regeneration fails
  closed. Independent ERC-participant, net-parity, same-footprint/no-net copper,
  effective-polygon and four negative regression checks per variant.
- Actual metric placement CSV and separate NPTH/PTH drill files; no bare test
  pads in BOM/placement. 21 SMD placements, 23 BOM components per board. Source
  and export SHA256 manifests. Independent Gerber inspection tool and snapshots.
- Final assembly review caught acoustic-port versus package-centre origins.
  `-pos.csv` now offsets SPH (0,+0.971 mm) and ICS (+0.710,0 mm) in PCB top view;
  raw `-origin-pos.csv` is retained. Independent checks assert both coordinate
  conventions. Supplier-specific rotations still require assembly DFM approval.
- Visual review also found the inherited schematic label layout unreadable.
  Spread components into groups, widened mic symbols, moved reference/value
  fields outside bodies and put the heading on the page. Re-rendered and reran
  exact net-parity/ERC checks; no electrical connectivity changes intended.

## Evidence

`coupons/mic-bakeoff/docs/T-022-release-verification.md` records the complete pin
table, commands, rule scope, outputs and remaining DFM gates. Durable reports,
logs, manifests and images: `orchestration/review/evidence-2026-09-06-t022/`.

- Coupon runner exit 0; regeneration twice byte-identical; both DRC 0/0/0;
  94-pad exact schematic/PCB parity; exact four ERC waivers; negative tests pass.
- Actual Gerber rendering (Gerbonara 1.6.3/librsvg) and drill/CSV/BOM audit exit 0.
  Visually inspected all twelve copper/paste/mask layer renders. Explicit white
  background is required in librsvg (SVG CSS background alone rendered transparent).
- Repo harness exit 0 with unchanged existing main DRC 175/499/0 and ERC 346;
  legacy rx_amp_sim/txrx_dev DRC 1/0/0 each. Not a clean main-board release.
- Ruff pinned 0.14.0. KiCad DRC needs approved host access on this Mac. The
  2026-09-05 session paused when approval service usage quota was exhausted;
  resumed with explicit user continue on 2026-09-06 and reran verification.
- Guided review regenerated/checker PASS: 8 steps, 11 items, 71 images,
  158/158 local links, 18/18 required assets. Inspected both final schematics.
  All 66 archived source/export hashes match current files; all 12 actual Gerber
  inspection PNGs remain byte-identical after the presentation-only changes.

## Handoff

T-022 done; T-016 back at CP-BM human review. Rev A exports are obsolete. Remaining
DFM checks include mic/U1 assembly rotation, negative-Y absolute-mm placement,
NPTH/annular stencil/no-wash handling, 1 oz outer copper and small reference-label
legibility. Prices/stock not refreshed; physical performance not tested.

Next engineering work: T-023 (top) independent fallback + commanded/timestamped
echo capture, then T-024 live processing and T-025 executable first-echo bench
proposal. Main PCB is still legacy/not for approval. Keep the review gate honest:
coupon electrical readiness is not an integrated-product demonstration.
