# Sonar v1 power rails (T-012)

_Tree: USB-C (VBUS, power-only, 900 mA budget) / XT60 bench input → FB1 (120R) →
power_mux (2× DZDH0401DW-7 + AO3415 ideal diodes, OR-ed) → **5V** (global net, VMUX)
→ AP63301 buck → **+3.3V** (3V3_D) → FB2 → **3V3_MIC**; 5V → TPS55340 boost → **+12V**
(TX only). Pruned per D002/D011: no 3.3 VA, no ±10 V, no 2.75/2.5/2.8 V, no −12 V
(sheets deleted 2026-08-26)._

## Rails table (bring-up runbook format)

| Rail (net) | Source / regulator | Allocation (design) | Consumers | Test point | Bring-up check |
|---|---|---|---|---|---|
| 5V (`5V`, VMUX) | USB-C VBUS or XT60 via ideal-diode mux | USB-C 900 mA max; XT60 bench unlimited | 3V3_D buck input, 12V boost input, SJ2 DNP option (Cmod VU) | TP80 (+5V), TP5 (VMUX, top sheet) | Power via USB-C only: expect 4.75–5.25 V at TP80. Repeat on XT60 alone. Both: whichever is higher wins; no back-feed (measure the *other* input stays ~0 V). |
| +3.3V (`+3.3V`, 3V3_D) | AP63301WU-7 buck from 5V (R161/R162 = 31.6k/10k, VFB 0.8 V → 3.33 V; L4 2.2 µH) | 500 mA alloc; expected load ≈ 150 mA | digital sheet (+3.3V: headers, LAN8720A block DNP, clock buffer), 3V3_MIC branch, LEDs; SJ1 DNP option (Cmod 3V3) | TP82 (+3.3V) | Rails up with 5V (EN pulled to Vin via R160). Expect 3.20–3.40 V at TP82, < 30 mVpp ripple. |
| 3V3_MIC (`3V3_MIC`) | +3.3V via FB2 — **fit 0R 0603 initially** (120R @ 100 MHz ferrite BLM18KG121TN1D is the reviewed option); 10 µF + 1 µF bulk at rail entry | **≥100 mA alloc (T-008)**; known-reference subtotal 34.7 mA (24 mics max 24 mA @ 1.8 V + CDCLVC1112) + uncharacterized 3.3 V deltas | T-010 mic array: 24× PDM mics + CDCLVC1112 clock fanout | TP86 (3V3_MIC) | Measure actual mic-rail current at FB2 during T-016 bake-off / first power-up; revisit allocation if > 100 mA. |
| +12V (`+12V`) | TPS55340 boost from 5V (600 kHz, R139; FB 86.6k/10k → 12.0 V; COMP = R163 10k + C261 4.7nF **datasheet starting point — verify loop stability at bring-up**) | 350 mA spec (~4 W, from George's sheet notes); TX bursts exceed USB-C budget → use XT60 for TX work | DRV8876 TX h-bridge VM (T-013 done: U62, see tx-limits.md) | TP81 (+12V) | **Sequencing:** boost EN (R164) pulled to +3.3V → +12V rises only after 3V3_D is up. Expect 11.4–12.6 V at TP81 only when 3V3_D present. |

## Notes
- Cmod A7 / FT232H / Pico 2 are self-powered from their own USB (T-011 decision);
  SJ1/SJ2 DNP jumpers are rework options, never paralleled-regulator hacks.
- Grounds: single GND net; boost PGND joins GND through net tie NT1.
- USB-C inrush: 10 µF budget on VBUS — bulk caps sit after FB1/mux, not on VBUS.
- Sourcing gap for T-014: R161 31.6k 0603 1% has no LCSC/MPN yet (symbol flagged).
- `sonar.kicad_pcb` still carries footprints of the deleted sheets' parts; resync at P3.
