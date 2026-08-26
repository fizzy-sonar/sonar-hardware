# T-002 parts and lifecycle matrix

Research date: **2026-08-25**. “Qty-30 price” is a planning quote, not a
purchase: `—` means the public page did not expose a reliable price at 30 on
the research date. “Orderable” means a current manufacturer or major
distributor listing; it does **not** imply JLC turnkey support. LCSC/JLC
availability must be rechecked at BOM freeze.

## D011 primary RX rows

| Part | Manufacturer / primary source (dated) | Lifecycle / live availability | Qty-30 price | Ultrasonic-relevant specification | Recommendation |
|---|---|---|---:|---|---|
| ICS-41350 | [TDK/InvenSense product page](https://www.invensense.tdk.com/en-us/products/microphone/ics-41350), [DS-000047](https://invensense.tdk.com/wp-content/uploads/2016/02/ICS-41350-data-sheet-v1.0.pdf) (2026-08-25) | **EOL**, explicitly not for new designs; TDK distributor snapshot showed Digi-Key 7,707 and Mouser 9,687 on 2026-08-19. No LCSC/JLC listing verified. | — | PDM; high-performance clock 4.1–4.8 MHz; SNR 64 dBA; 126 dB SPL AOP; datasheet explicitly says extended response to 40 kHz. | **Fallback only**: excellent fit technically, unacceptable lifecycle risk. |
| ICS-41352 | [TDK product page](https://product.tdk.com/en/search/sw_piezo/mic/mems-mic/info?part_no=ICS-41352), [DS-000048](https://invensense.tdk.com/wp-content/uploads/2016/10/DS-000048-ICS-41352-data-sheet-v1.0.pdf) (2026-08-25) | **Production (NRND)**; TDK page reports no inventory and “Contact Us”; no LCSC/JLC stock verified. | — | PDM, bottom port, 4.1–4.8 MHz high-performance mode, 64 dBA SNR, 120 dB SPL AOP, 550 µA typical. No guaranteed 20–40 kHz flatness in datasheet. | **Primary bake-off candidate**, but NRND means qualify a second source before layout. |
| SPH0641LU4H-1 | [Syntiant MEMS portfolio](https://www.syntiant.com/mems), [Knowles/Syntiant datasheet search](https://www.digikey.com/en/products/detail/syntiant/SPH0641LU4H-1/2816334) (2026-08-25) | Current portfolio listing; distributor stock/qty-30 price was not reliably exposed in the accessible page. No LCSC/JLC listing verified. | — | Digital PDM, bottom port, 1.8 V, SNR 65.5 dBA, AOP 132.5 dB SPL; Syntiant table gives 250/650 µA LP/NP. The family datasheet shows ultrasonic-response plot through 80 kHz, but not a guaranteed tolerance at 25 kHz. | **Best lifecycle/ultrasonic alternate**; T-008 must confirm clock range and 1.8 V rail. |
| T5838 | [TDK product search](https://product.tdk.com/en/search/sw_piezo/mic/mems-mic) (search “T5838”) (2026-08-25) | No current public TDK product page, distributor stock, LCSC, or JLC listing was verified. Treat as unorderable until a manufacturer datasheet/quote is obtained. | — | Candidate named by D011, but no primary datasheet evidence for PDM clock, SNR, AOP, or 20–40 kHz response was found. | **Do not design in** pending primary documentation. |

## D012 platform / support rows

| Part | Primary source | Lifecycle / live availability | Qty-30 price | Relevant specification | Recommendation |
|---|---|---|---:|---|---|
| Cmod A7-35T | [Digilent product page](https://digilent.com/shop/cmod-a7-35t-artix-7-fpga-module/) (2026-08-25) | Official Digilent product, order page live; qty-30 is irrelevant for one-off dev hardware and no JLC turnkey path. | — (listed near $100, verify at checkout) | Artix-7 XC7A35T, DIP-48 module, onboard USB/UART and SRAM; Vivado target. | **Use as primary FPGA learning platform**; buy one spare only through Joshua. |
| FT232H breakout | [FTDI FT232H product](https://ftdichip.com/products/ft232hl/) and [Adafruit breakout](https://www.adafruit.com/product/2264) (2026-08-25) | FTDI silicon active; breakout vendor orderable, not a JLC turnkey board item. | — (breakout listed around $15) | USB 2.0 high-speed; synchronous FIFO mode is the intended raw-PDM egress. | **Use**, with signal-integrity and driver benchmark in T-021. |
| Pico 2 / RP2350 | [Raspberry Pi Pico 2](https://www.raspberrypi.com/products/raspberry-pi-pico-2/) (2026-08-25) | Current Raspberry Pi product; retail orderability visible, not a JLC PCB item. | — (single-board price, not qty-30) | RP2350, PIO + DMA, USB 1.1 FS; snapshot/trickle mode only, not continuous 24-channel raw stream. | **Use for v0 snapshot bring-up**, not replacement for FPGA. |
| LAN8720 module | [Microchip LAN8720A](https://www.microchip.com/en-us/product/lan8720a) (2026-08-25) | Active PHY; module/connector availability varies; DNP provision only. | — | 10/100 RMII PHY; cannot carry raw 74–115 Mb/s with protocol overhead reliably, reserved for decimated stream milestone. | **DNP provision**, no critical-path purchase. |
| DIP-48 socket | [Samtec DIP socket family](https://www.samtec.com/products/dip) (2026-08-25) | Generic active family; exact low-profile, through-hole part and JLC assembly capability require BOM/DFM check. | — | Must fit Cmod A7-35T DIP-48 outline and repeated insertion. | **Specify after mechanical drawing check**; do not substitute SODIMM. |
| SODIMM-200 socket | [TE Connectivity SODIMM socket search](https://www.te.com/en/products/connectors/pcb-connectors/standard-edge-connectors/intersection/sodimm.html) (2026-08-25) | Generic parts exist, but no selected manufacturer/order code or JLC listing established. | — | Superseded by D012 generic header + onboard Cmod DIP-48. | **Reject / remove** from design. |

## Historical-only rows (D011 supersedes analog RX)

TLV320ADC5140 (and ADC3140/PCM1840/CS5368/AK5538 alternatives), SPV0142LR5H-1,
IM73A135, OPA1679 (and OPA1654/TLV9354/OPA4322), DRV8876, and TPS55340 remain
legacy notes from the original analog architecture. They are not candidates for
the D011 RX BOM. DRV8876 and TPS55340 may still be revisited by TX/power tickets;
this ticket does not select them. No analog row is recommended or used to gate
P2.

## Knowles/Syntiant ultrasonic note

[Knowles AN-17](https://www.knowles.com/docs/default-source/default-document-library/an-17-issue01.pdf)
says production testing/specifications commonly stop at 10 kHz, which does not
mean the microphone stops responding there; typical curves are shown to 100 kHz.
It also warns sensitivity falls above 10 kHz while self-noise falls, so usable
SNR can remain high if the receive chain is band-limited appropriately. The
[SiSonic Design Guide / AN24](https://www.knowles.com/docs/default-source/default-document-library/sisonic-design-guide.pdf)
states that open-mesh SiSonic packages can capture approximately 20–80 kHz or
more. These are family/application curves, not a guaranteed SPH0641 production
tolerance at 25 kHz: T-008 must measure normalized response and per-channel
calibration. PDM clock/decimation must preserve the 20–40 kHz band; do not infer
ultrasonic flatness from the audio SNR number.

## Conclusion

Proceed to T-008 with an ICS-41352 versus SPH0641LU4H physical bake-off, while
keeping ICS-41350 only as a readily available EOL experiment. T5838 is blocked by
missing primary evidence. The design should reserve a 1.8 V mic rail for the
Syntiant alternate, retain generic FPGA/platform headers, and flag every mic and
platform line for manual LCSC/JLC quote verification before CP-C. No public page
verified a trustworthy qty-30 price or JLC turnkey status for the rows above.
