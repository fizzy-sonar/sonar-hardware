# Sonar v1 dev-hardware buy list (review only)

**2026-09-13 purchase-readiness update:** use
[`docs/pre-hardware-readiness.md`](../docs/pre-hardware-readiness.md) before this
historical basket. Cmod 410-328-35 is now $104 USD (1,180 shown in stock); Adafruit
2264 is $14.95/in stock. Other prices below were not refreshed. Cmod uses Micro-B,
so the listed USB-C cable alone is insufficient. FT232H needs assembled headers,
an adapter, verified FIFO EEPROM setup and physical throughput proof; see
[`ft232h-bench-preflight.md`](../docs/ft232h-bench-preflight.md). The current basket
omits a complete coupon TX driver/calibrated bench. Hold the main PCB; it is legacy.

**Checked 2026-08-25 (USD, before tax/shipping).** These are links for Joshua to
review and click; no carts, accounts, or orders were created. Shipping, tax, and
cross-border duties can move the total. “In stock” is the page state checked on
the date above, not a guarantee at checkout.

## Critical path

| Qty | Item / exact variant | Vendor link | Unit | Status / caveat |
|---:|---|---|---:|---|
| 1 | Raspberry Pi **Pico 2** (non-W, RP2350, 4 MB flash) | [Raspberry Pi product page](https://www.raspberrypi.com/products/raspberry-pi-pico-2/) | $5.00 | Official page says available from $5; reseller selection is region-dependent. Crowd Supply has the exact board at $5, in stock, but lists $8 US shipping: [listing](https://www.crowdsupply.com/raspberry-pi/raspberry-pi-pico-2). Snapshot-only, not raw continuous streaming. |
| 1 | **Digilent Cmod A7-35T**, SKU 410-328-35 | [DigiKey 1286-1130-ND](https://www.digikey.com/en/products/detail/digilent-inc/410-328-35/6133793) | $99.00 | DigiKey is an authorized distributor; checked listing showed active part and stock (regional page showed 894). Confirm US/Canada stock and freight at checkout. |
| 1 | **Adafruit FT232H Breakout 2264** (USB-C revision) | [Adafruit](https://www.adafruit.com/product/2264) | $14.95 | In stock / ships today on checked page. Includes 16-pin headers. Intended FT245 synchronous-FIFO experiment; verify wiring and driver throughput in T-021. |
| 1 | Murata **MA40S4S** 40-kHz transmitter | [DigiKey 490-7707-ND](https://www.digikey.com/en/products/detail/murata-electronics/MA40S4S/4358147) | $6.12 | 3,942 in stock when checked; NFND; 20 Vp-p rated. Narrowband reference only. |
| 1 | Murata **MA40S4R** 40-kHz receiver | [DigiKey 490-7706-ND](https://www.digikey.com/en/products/detail/MA40S4R/490-7706-ND/4358146) | $6.11 | **0 in stock**, 540 expected 2026-10-05 when checked; NFND. This is a backorder/lead-time item, not confirmed available. |
| 1 | Wideband candidate: **GRS PZ1005 piezo horn tweeter**, Parts Express 292-442 | [Exact product page](https://www.parts-express.com/GRS-PZ1005-3-1-4-Piezo-Horn-Tweeter-Similar-to-KSN1005A-292-442) | $2.99 | In stock. Published response is **4–27 kHz**, so it does not cover 27–32 kHz. Full-band TX remains unresolved; measure before any link-budget use. |
| 1 | Official Raspberry Pi 5.1 V / 3 A USB-C supply | [Adafruit product 4298](https://www.adafruit.com/product/4298) | $14.95 | In stock when checked; exact regional plug selection and shipping required. Dev-board power only. |
| 1 | USB-C data cable | [Adafruit product 4199](https://www.adafruit.com/product/4199) | $9.95 | In stock; USB 3.1 Gen 4, 1 m, all data pins. Add 0.1-in jumper leads locally if needed. |
| 1 | Powered USB hub | — | $0 | Omit from subtotal; use Joshua’s existing hub or add an exact model after port count is known. |

**Planning subtotal:** **$159.12** before tax/shipping, using Pico $5 + Cmod $99 +
FT232H $14.95 + MA40S4S $6.12 + MA40S4R $6.11 + PZ1005 $2.99 + supply $14.95 +
cable $9.95. The receiver is backordered; subtotal is therefore not a fully
available basket. Shipping/tax can exceed $200.

## Optional Ethernet milestone (do not block purchase)

The board reserves DNP RMII footprints. Optional exact module: [Waveshare LAN8720
ETH Board SKU 8583](https://www.waveshare.com/product/lan8720-eth-board.htm), $8.99,
listed by Waveshare (checked page). Verify ship-to region and stock before buying;
module pinout/oscillator/magnetics must match the carrier. RMII is for decimated
data and cannot replace FT232H for raw PDM.

## Vivado host choice (excluded from the $200 subtotal)

Vivado does not run natively on macOS. AMD documents Windows/Linux 64-bit support
and memory recommendations on its [Vivado system page](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado/vivado-buy.html).

| Option | Budget | What Joshua must choose |
|---|---:|---|
| Used x86 mini-PC meeting precise criterion: N100/8th-gen i5+, 16 GB RAM, 512 GB SSD | $150–250 one-time target | Search eBay/Back Market for that exact spec; require returns, seller rating, and at least 30-day warranty/protection. Verify x86-64, supported Windows/Linux, SSD space, and SSH/Tailscale before accepting. |
| Cloud x86 VM, 4–8 vCPU, 16–32 GB RAM, ≥120 GB disk | estimate $35–80/month active use | Use [AWS EC2 On-Demand pricing](https://aws.amazon.com/ec2/pricing/on-demand/) and [AWS calculator](https://calculator.aws/) to price an x86 instance plus EBS gp3 disk in Joshua’s region; exact monthly total depends on hours and disk. Cloud cannot directly see local Cmod USB/JTAG without USB-over-IP. |

## Human choices and stop conditions

1. Confirm Cmod A7-35T distributor stock/lead time and whether a spare is worth
   the single-source risk.
2. Pick Pico 2 reseller/ship-to country; do not substitute Pico 2 W or a PSRAM
   board unless T-009 explicitly needs it.
3. Pick a Vivado host (mini-PC versus cloud) and confirm the intended 2025.x/2026.x
   release’s supported OS before setup.
4. Treat the GRS horn and MA40S4S as measurement fixtures. Neither provides a
   normalized 20–32 kHz TX SPL curve; do not use raw advertised TX SPL as
   link-budget evidence.

## Architecture consistency note

D012’s original ladder paragraph still says “buy BOTH ... Arty A7-100T”; its later
amendment and current PLAN/STATUS ratify **Pico 2 + Cmod A7-35T**, with Arty
demoted. This list follows the newer authoritative amendment and flags the stale
Arty prose rather than silently rewriting a ratified decision.
