# T-016 sourcing evidence (dated)

_Re-check attempted 2026-08-26 by codex/terra-t016: **this session's sandbox had
no network access** (DNS resolution fails), so no new distributor data could be
fetched. The dated evidence below is carried forward from T-002's parts matrix
(2026-08-25, web-checked then) and T-008. Re-verify stock/price at order time;
nothing below represents unavailable stock as orderable._

## SPH0641LU4H-1 (Syntiant)

- Lifecycle: listed in Syntiant's current MEMS portfolio (checked 2026-08-25,
  https://www.syntiant.com/mems).
- Distributor page: DigiKey SPH0641LU4H-1
  (https://www.digikey.com/en/products/detail/syntiant/SPH0641LU4H-1/2816334) —
  stock/qty-30 price was not reliably exposed to the 2026-08-25 audit; verify at
  order time. No LCSC/JLC turnkey listing verified (T-014's production job).
- Datasheet (local primary copy used for the land pattern): Knowles Rev B
  2015-04-06; the Syntiant-hosted PDF has malformed revision fields (noted in
  T-008), tables match Knowles Rev B.

## ICS-41352 (TDK)

- Lifecycle: TDK product page lists production but **NRND**, no inventory,
  "Contact Us" (checked 2026-08-25,
  https://product.tdk.com/en/search/sw_piezo/mic/mems-mic/info?part_no=ICS-41352).
  No LCSC/JLC stock verified.
- Datasheet: DS-000048 Rev 1.0 (local primary copy used for the land pattern).
- **Risk**: if coupon quantity is not legitimately orderable, rule 4 applies:
  the bake-off is inconclusive unless Joshua ratifies a documented D011 waiver.

## CDCLVC1112PWR (TI)

- Pin map repaired and verified under T-022 using live TI SCAS895B, section 5
  (2026-09-05); see [release record](T-022-release-verification.md). All 24 actual
  pads and schematic symbol names checked independently. Stock/pricing were not
  refreshed in this repair session and still require an order-time check.

## D009 compatibility note

The release record must name a dated, legitimate order path for coupon quantity
plus at least 30 microphones. T-014 performs the full production JLC/LCSC
mapping; nothing here releases a production BOM from a marketplace listing.
