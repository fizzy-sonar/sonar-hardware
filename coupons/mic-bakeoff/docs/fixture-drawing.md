# T-016 fixture drawing + uncertainty budget template

_Text drawing; units mm. The fixture is an indexed plate that holds one coupon
and the calibrated reference microphone at fixed, repeatable positions relative
to a fixed wideband transmitter. Machined or 3D-printed rigid plate is fine;
what matters is repeatability, logged pose, and the uncertainty budget._

## Geometry (top view; coupon inserted from below, ports flush to plate face)

```
                 fixed wideband TX (20–40 kHz capable, >=117 dB SPL at plane)
                            T
                            |
                            | 300 mm on-axis
                            |
        ┌───────────────────┴───────────────────┐
        |           coupon under test            |
        |  M1  M2  M3  M4   (ports face T)       |
        └────────────────────────────────────────┘
                            |
        reference mic R at  | 300 mm, same axis, 20 mm off-axis from coupon
                            | centre line (fixed)
```

- Coupon plate: pockets machined to the 70x30 coupon outline with two dowel pins
  in the M2 mounting holes for indexed reseating; coupon clamped by two M2
  screws with washers outside the mic row. Port side faces the TX with a flush
  1.0 mm counterbore around the mic row only (no trapped cavity; no gasket
  contact on the ports).
- TX fixed on the same plate stand; distance TX→coupon plane 300±1 mm, on-axis
  to the coupon centre. Reference mic at the same distance, 20 mm off-axis.
- Both TX and reference are stationary during a block; only the coupon reseats.
- Ambient: quiet room, temperature/humidity logged per record.

## Uncertainty budget template (fill with bench values; every k=2 term <= 1.0 dB)

| Term | Standard unc. (dB) | k=2 (dB) | Evidence |
|---|---|---|---|
| Reference mic calibration (20–32 kHz) |  |  | cal artifact id |
| TX level drift over a paired block |  |  | before/after log |
| Fixture pose/reseat geometry |  |  | repeat measurements |
| Acquisition floor / gain linearity |  |  | loopback record |
| Time-gating leakage |  |  | gate sweep test |
| **Combined RSS** |  | **must be <= 1.0 dB** | |

Report `U_fixture_k2` separately for: each absolute noise decision bin, each
absolute SNR bin, the integrated band, each paired loss bin, and the paired band
(`fixture.u_fixture_k2_db` in the dataset). If any exceeds 1.0 dB the analyzer
raises fixture-invalid.
