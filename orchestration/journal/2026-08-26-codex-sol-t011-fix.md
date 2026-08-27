# 2026-08-26 codex/sol-t011-fix — REVIEW-2026-08-26 B1/S1/S2/S9 repair

Scope: exactly review sections B1, S1, S2, S9 (read from the main repo's
orchestration/review/REVIEW-2026-08-26.md). digital.kicad_sch / XDC / pinmap.md
are GENERATED — all schematic/constraint fixes went into
scripts/gen_digital_sheet.py, then outputs were regenerated.

## What changed
- **B1 (blocker):** PINS row 24 net `+5V` → `5V` (unified on the power tree's
  global net). J40.24 now wires to `5V_CMOD`; new **R420 (0R 0603, populated by
  default, DNP-capable)** connects 5V_CMOD → 5V (the review-mandated series
  element for the module-USB backfeed question). Stale PWR_FLAG #FLG403 +
  #PWR791 DELETED (it had masked the orphan net from ERC). Sheet notes updated.
- **S1:** write_xdc() is read-modify-write: if the XDC exists, everything from
  the `## ---…` + `## MANUAL APPEND` marker onward is preserved verbatim.
  Proved by regenerating twice → byte-identical XDC; manual section (30 SRAM
  pins + uart_rxd_out) intact (83 set_property lines total).
- **S2:** orchestration/rails.md rewritten to the real v1 strategy: carrier 5V
  powers the Cmod via VU through R420 (populated by default); stale
  "self-powered / SJ1 SJ2 DNP" text deleted (FT232H + Pico 2 still self-powered);
  backfeed caveat is now an explicit bring-up procedure (DNP/lift R420 before
  connecting the Cmod's USB while carrier 5V is live); 5V rail budget gained the
  missing Cmod allocation ~200–400 mA typ, honestly marked as an unmeasured
  assumption to verify at bring-up.
- **S9:** R411 (10k 0603) pull-up FT_SIWU (J41.15) → +3.3V.
- scripts/check_pinmap_vs_xdc.py: special-position net whitelist updated
  `+5V` → `5V` (intentional rename).

## Verification (kicad-cli 10.0.1, this machine)
- Netlist (build/sonar.net), verbatim:
  - `5V` (15 nodes): C140.1, C161.1, C162.1, C174.1, L2.1, Q1.2, Q2.2, R160.1,
    **R420.2**, TP5.1, TP80.1, **U35.3** (AP63301 buck VIN), U37.4, U38.4,
    **U61.3** (TPS55340 boost VIN).
  - `5V_CMOD` (2 nodes): **J40.24**, R420.1.
  - `FT_SIWU` (2 nodes): J41.15, R411.2; R411.1 on +3.3V.
  - `+5V`: ABSENT. Note: the series 0R splits the net by KiCad rules, so J40.24
    reaches the buck/boost inputs *through* the populated R420 — the B1 intent
    (no orphan, module powered from the carrier tree) is met.
- ERC --severity-all: project 346 msgs (276 err/70 warn, all pre-existing
  array/TX/lib-table scope); **/digital/ section: ZERO**.
- scripts/check_pinmap_vs_xdc.py: PASS 44/44 vs committed live master XDC.
- XDC regen-twice diff: byte-identical (S1 proof).
- `kicad-cli pcb drc`: NOT run — SIGABRTs (exit 134) in this sandbox on all
  projects including pristine ones; known environmental issue (T-006/STATUS).
  Re-run unsandboxed; ERC is the gate.

## Gotchas for the next agent
- Edit scripts/gen_digital_sheet.py, never the generated outputs.
- The XDC MANUAL APPEND section is safe across regeneration now — but only if
  the `## MANUAL APPEND` marker comment is preserved by whoever edits it.
- rails.md `5V` row carries the Cmod allocation assumption; measure at bring-up.
- Nothing committed (no commits/merge/push per instructions); orchestrator
  integrates.
