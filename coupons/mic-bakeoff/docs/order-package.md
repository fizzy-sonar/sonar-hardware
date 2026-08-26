# T-016 order package (CP-BM; Joshua clicks, agent never spends)

_All prices unverified this session (offline sandbox; no distributor pages
reachable). Fill the price column at order time from the distributor pages
linked in `sourcing-evidence.md`. Quantities include assembly-loss margin:
12 valid units per MPN required, so 4 coupons worth (16) ordered per MPN._

## Mic + buffer purchases (distributor of Joshua's choice)

| Item | MPN | Qty | Unit price | Ext. | Evidence |
|---|---|---:|---|---|---|
| SPH mic | Syntiant SPH0641LU4H-1 | 16 | $___ | $___ | sourcing-evidence.md |
| ICS mic | TDK ICS-41352 | 16 | $___ | $___ | sourcing-evidence.md |
| Clock buffer | TI CDCLVC1112PWR | 8 | $___ | $___ | TI/JLC Global Parts |

Note: ICS-41352 was NRND with no visible distributor inventory on 2026-08-25 —
if it cannot be bought in coupon quantity, the bake-off is inconclusive by rule
4 and Joshua decides on a documented D011 waiver; do not substitute silently.

## Coupon fabrication/assembly (JLCPCB, 2 variants x 3 assembled + 2 spares)

| Parameter | Value |
|---|---|
| Boards | 5 per variant (3 for test, 2 margin) |
| Layers / thickness | 4 / 1.6 mm (JLC04161H-7628 stackup intent) |
| Dimensions | 70 x 30 mm |
| Surface | ENIG |
| Acoustic holes | 4x 0.50 mm **non-plated** per board — see fab note on Cmts.User |
| Min track/space used | 0.20 / 0.145 mm (within JLC 4L minimums) |
| Vias | 0.6/0.3 mm (one 0.5/0.25 at U1 pin 11) |
| Assembly | SMD both variants fully assembled; headers (J1, JP1) THT |
| Files | `build/t016/<variant>-coupon-fab/gerbers/` + `-pos.csv` + BOM below |
| Stencil | annular GND-ring paste per footprint; keep paste out of the ports |
| Handling | no board wash / ultrasonic clean; nothing into the ports |

## BOM per coupon (from kicad-cli export; see build/t016/<v>-bom.csv)

| Ref | Part | Qty/coupon |
|---|---|---:|
| M1..M4 | variant MPN (SPH0641LU4H-1 or ICS-41352) | 4 |
| U1 | CDCLVC1112PWR (TSSOP-24) — **pin map UNVERIFIED, see README** | 1 |
| C1..C8 | 100 nF C0G/NP0 0603 (NOT X5R/X7R) | 8 |
| C9 | 1 uF 0603 | 1 |
| C10 | 10 uF 0603 | 1 |
| R0, R1 | 10 ohm 0603 1% | 2 |
| R12 | 100 kohm 0603 | 1 |
| R13, R14 | 0 ohm 0603 | 2 |
| J1 | 2x05 2.54 mm header | 1 |
| JP1 | 1x02 2.54 mm jumper + shunt | 1 |

## Pre-order checklist (Joshua, ~15 min)

1. Confirm CDCLVC1112PWR pin map against the TI datasheet; fix
   `BUFFER_PIN_MAP` in `generate_coupon.py` if needed; regenerate; re-run
   `check_coupons.sh`.
2. Re-run `kicad-cli pcb drc` on both coupons unsandboxed (sandboxed runs
   SIGABRT — see README verification status) and confirm no new violations.
3. At JLC DFM review: confirm mic pick-and-place rotation against each
   datasheet's pin-1 corner mark (ICS: Figure 3 is the PCB-side view used here).
4. Re-check stock + price for both exact MPNs (evidence file is dated
   2026-08-25/26; stock moves).
5. Then, and only then: place the orders.
