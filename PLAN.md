# Sonar v1 — Architecture & Execution Plan (v2)

_v2: 2026-08-25, after Joshua's go-ahead. The **authoritative decision registry is
`orchestration/decisions/` (D001–D012)**; execution state is `orchestration/STATUS.md`
+ `tickets/`. This file is the coherent architecture narrative. Agents: start at
`/AGENTS.md`, not here._

## 1. Locked architecture (all ratified)

- **Function**: in-air sonar imager, 20–32 kHz chirps centered ~25 kHz (D001), with a
  secondary audio-band beamforming use. Matched-filter + delay-and-sum processing.
- **Array** (D001): 5×5 grid, center cell reserved for TX, = 24 RX channels; pitch
  6.9–8 mm (λ/2 @ 25 kHz = 6.9 mm); bottom-port mics with acoustic ports through the PCB.
- **RX** (D011): 24 digital **PDM ultrasonic MEMS mics** straight to the FPGA — no
  ADCs, no preamps, no analog rails. Candidates: TDK ICS-41350/41352, Syntiant
  SPH0641LU4H (lifecycle check), TDK T5838 — T-002 audits, T-008 picks. Default
  wiring: L/R-paired → 12 data lines + shared clock tree (T-008 may pick 24 unpaired;
  the pair skew is a deterministic half PDM period ≈ 56 µm acoustic — negligible /
  exactly correctable).
- **Digital platform** (D012): ladder on one FPGA-agnostic header —
  1. **Pico 2 (RP2350)** snapshot v0: PIO+DMA captures raw windows (520 KB ≈ 36 ms ≈
     6 m; PSRAM variant ≈ 0.55 s), trickles over USB; ~1–2 Hz imaging; days of work.
  2. **Cmod A7-35T** (official Digilent, DIP-48 — sockets ON the board) +
     **FT232H** in FT245 sync-FIFO mode: ~40 MB/s USB 2.0 HS carries the full raw
     PDM stream (24 × 3.072–4.8 MHz = 9–14.4 MB/s) **continuously**; FPGA does clocking,
     IDDR sampling, packing, a ~64 KB elastic FIFO — zero DSP. This is also Joshua's
     Vivado learning platform. Day-one fallback: UART snapshot via the Cmod's own USB.
  3. **Ethernet milestone (later, optional)**: DNP RMII PHY + MagJack footprints on
     spare pins; populate ~$3 of parts and learn MAC/UDP/CIC-in-fabric. 100M carries
     only the decimated stream (raw needs the FT232H). Never a respin.
  - Dropped: Colorlight i5 (unsupported gray market), custom FPGA interposer, GbE/LiteX.
  - **Vivado requires an x86 Linux/Windows host** (not macOS) — mini-PC or cloud VM,
    Joshua picks via T-007.
- **DSP** (D006): **everything on the laptop in Python** — decimation (CIC+FIR),
  calibration, matched filter, beamforming. Raw recording ≈ 0.9 GB/min; decimate on
  ingest for long captures.
- **TX** (D007): DRV8876 h-bridge, transducer **off-board via connector** (MA40S4S @
  40 kHz narrowband, piezo horn tweeter for 20–32 kHz chirps); 12 V boost rail, TX only.
- **Power** (T-012 done): USB-C(power-only)/XT60 → ideal-diode mux → 5 V →
  3.3 VD buck (+3.3V) with a filtered 3V3_MIC branch (≥100 mA, T-008 — 3.3 V chosen
  over 1.8 V for direct LVCMOS33 compatibility), 12 V TX boost. All other rails
  from the old tree deleted. Rail table: `orchestration/rails.md`.
- **EDA** (D008): KiCad + `kicad-cli` ERC/DRC/PDF/BOM in CI. diodeinc-pcb spike
  optional, non-gating (T-005). **Mfg** (D009): JLCPCB full turnkey, LCSC-first,
  Global Parts for the rest — no home soldering. **Population** (D010): all 24
  channels assembled; validate per 8-ch group in software.

## 2. Board contents (v1)

24 PDM mics (5×5−center) · clock buffer/fanout · DIP-48 socket (Cmod) · FT232H
breakout header · generic PDM header (Pico v0 ribbon; one platform attached at a
time) · DNP RMII PHY + MagJack + 50 MHz osc · DRV8876 + TX connector · USB-C 5 V +
XT60 + mux · 3.3 V regs + 3V3_MIC branch + 12 V boost · LEDs, test points. ~4-layer,
roughly 150 placements. Authoritative pin table: `orchestration/pinmap.md` (T-011).

```
mics ──12 data + clk──► FPGA (IDDR → pack → 64KB FIFO) ──FT245──► FT232H ──USB2 HS──► laptop
 ▲                        │  also: TX chirp NCO→PWM → DRV8876 → transducer      (Python: CIC,
 └── shared 3.072–4.8 MHz clock tree                                        cal, matched filter,
                                                                              beamforming)
```

## 3. Execution

Phases/gates: `orchestration/ROADMAP.md`. Open now: **P1** (T-001 link-budget model,
T-002 parts audit, T-006 kicad-cli harness, T-007 buy list, then T-008 PDM RX design)
and **P5** (T-009 Pico snapshot fw, T-020 Vivado gateware, T-021 host software).
**P2** schematic rework unlocks after T-002 + T-008, except T-010's microphone
MPN/footprint freeze waits on the quantitative T-016 coupon release. Human
checkpoints: CP-B analysis/gate review, CP-BM coupon purchase + calibrated mic
release, CP-C schematic sign-off, CP-D production spend approval, CP-E bring-up
bench sessions (CP-A done 2026-08-25).

Key analysis anchor (T-001 to formalize): sonar-equation margin ≈ 90 − 40·log10(r) − r
dB → ~+40 dB on a person at 10 m; architecture is not SNR-gated; model sets TX drive
and the chirp-length↔blind-zone schedule, and is the CP-B trigger for revisiting D011
if PDM ultrasonic noise disappoints.

## 4. Budget (v2)

| Item | Est. |
|---|---|
| Dev hardware (Pico 2, Cmod A7-35T, FT232H, PHY module, transducers, PSU/cables) | ~$200 |
| Vivado host (used x86 mini-PC one-time, or cloud VM monthly) | $0–250 |
| 2× assembled boards (4-layer, ~150 placements, JLC turnkey) | $250–400 |
| **First hardware in hand** | **≈ $450–650 (+host)** |
| v1.1 respin reserve | $400 |

## 5. Risks & watch items

1. **Mic ultrasonic response unspecified** — T-008 defines the provisional SPH
   electrical baseline and quantitative acceptance thresholds; T-016 physically
   compares SPH/ICS coupons and gates the final MPN/footprint. Per-channel
   calibration absorbs only variation inside that release envelope.
2. **PDM noise in the ultrasonic band** (D011's known cost, ~3–6 dB) — T-001
   quantifies; CP-B is the revisit gate.
3. **Sustained USB ingest on macOS** (9–14.4 MB/s through pyftdi into Python) —
   T-021 benchmarks this early; fallback is smaller capture duty cycles.
4. **Cmod A7-35T single-source** — buy early (T-007); note lead time for a spare.
5. **No analog observability** (no per-channel test points) — T-020's pattern/counter
   modes and the UART snapshot path are the debug story; build them first.
