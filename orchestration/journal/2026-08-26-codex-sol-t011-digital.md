# 2026-08-26 — codex/sol-t011: T-011 digital sheet, pinmap, XDC

## What happened
Built the T-011 digital sheet as a **generated** design: `scripts/gen_digital_sheet.py`
holds the single-source PIN TABLE and emits `orchestration/pinmap.md`,
`sonar-v1-pcb/digital.kicad_sch`, `gateware/constraints/sonar_cmod_a7.xdc`, and patches
`sonar-v1-pcb/sonar.kicad_sch` (DF40 + adc_bus removal + digital sheet block). Re-run
`python3 scripts/gen_digital_sheet.py` to regenerate; the top-sheet patch is idempotent
and verified byte-identical from scratch.

## Things the next agent must know (hard-won, don't re-derive)
- **KiCad negates lib-symbol Y on placement**: sheet pin pos = (X+px, Y−py), pin angle →
  360−a. Verified empirically against kicad-cli ERC coordinates. The generator encodes this.
- Symbols must be snapped to the 1.27 mm grid or ERC throws endpoint_off_grid and treats
  pin/wire contacts as unconnected.
- Power nets with no regulator on-sheet need `power:PWR_FLAG` (+3.3V pending T-012;
  ETH_VDDCR driven by LAN8720A internal reg; block DNP).
- **No network on this machine** (curl/nc fail): the Cmod A7 pio→package-pin mapping is
  transcribed from memory, cross-anchored to T-008's documented clock-capable list.
  Clock-critical nets use only double-sourced CC pins (pio3/5/8/36/43). The T-008 list
  vs recalled mapping disagree (pio16/17 vs 18/19; pio46-48); documented in pinmap.md —
  the second-agent audit must resolve against the live Digilent master XDC.
- **Sandbox blocks all git writes** (`Operation not permitted` on the worktree gitdir,
  approval policy Never) — nothing could be committed; orchestrator must commit the
  worktree. `kicad-cli pcb drc` also aborts (exit 134) in-sandbox on every project,
  including pristine HEAD — environmental, not a regression (no .kicad_pcb touched).

## Verification summary (details in ticket log)
- Digital sheet ERC-clean; project ERC 512→456 messages; DF40 removal cut pin_to_pin
  130→6. +22 isolated_pin_label in legacy array sheets = expected T-010-scope fallout.
- Visual check of sonar-digital.svg: geometry correct.

## Left open
1. T-011 audit session (pinmap vs live Digilent docs; needs network) → then T-011 done.
2. Orchestrator commit of the T-011 worktree.
3. T-020 can start testbench work against the XDC, treating pin numbers as provisional
   until the audit lands.

---

## Addendum — codex/sol-t011-audit (second session, same day): pin audit

- **No network in this sandbox either** (DNS/TCP blocked, escalation denied). The
  mandated live fetch of the Digilent master XDC / reference manual / FT232H /
  LAN8720A datasheets was impossible again; audit ran on independent recall +
  self-consistency + KiCad-10 library symbols + kicad-cli netlist. The live
  60-second fetch remains the only open verification item (pinmap.md header).
- Resolved both flagged discrepancies analytically: T-008's clock-capable list is
  corrupt (pio46/47/48 are DIP power pins → its pio18/19/37/38/40 claims lose
  authority); CC set = IO-name-derived {pio3,5,8,16,17,32,33,34,36,39,42,43,44};
  pio16/17 confirmed MRCC_35. **No net assignments changed** (all clock-critical
  nets were double-sourced). Corrected docs/pdm-capture-contract.md.
- **Found and fixed a real defect**: LAN8720A ref U50 collided with legacy array-
  sheet U50 (SOT-23-5) — ERC-clean but netlist/BOM-ambiguous. Renamed to U60 in
  the generator, regenerated all outputs, re-ran harness: /digital/ ERC section
  still zero violations, project error count unchanged (339).
- Netlist cross-check (parsed build/sonar.net): J40 48/48, J41 20/20, J42 26/26,
  U60 25/25 all match the pin table; J42 channel map matches the capture contract
  all 12 rows; XDC↔table consistent; bank suffixes/IO-names consistent 44/44.
- Uncommitted (policy); orchestrator commits this worktree. Next: the human
  live-fetch check at the top of orchestration/pinmap.md, then T-011 → done.


---

## Addendum 2 — codex/sol-t011 (third session, same day): live-source gate FAILED; repair

- The orchestrator fetched the primary sources live (`/tmp/cmod-a7-master.xdc` +
  reference manual sec. 8 / fig. 8.1) and the gate **FAILED the pin table**: the
  master XDC GPIO section is `pio[01]..pio[48]` SKIPPING `pio15/16/24/25`;
  positions 15/16 are XADC analog-only (3.3V→1V divider), 24 = VU (module 5 V
  in/out), 25 = GND (the only module GND); there is **no 3V3 pin** on the DIP.
  The offline transcription had every net on a *valid package pin* but rows 15–44
  on the *wrong DIP positions* (+2 for 15–21, +4 for 22–44), FT_D2/FT_D3 sat on
  the VU/GND positions, and power pins were invented at 45–48.
- The previous offline audit's "confirmation" and its "T-008 CC list is corrupt"
  resolution were **correlated-recall errors**; reverted. True MRCC/SRCC set from
  the live XDC IO-names = {3,5,8,18,19,36,37,38,40,43,46,47,48} — T-008's
  original list was correct; `docs/pdm-capture-contract.md` restored with an
  honest note.
- Fix (single source = `scripts/gen_digital_sheet.py` PIN TABLE): re-map N→N
  (1–14), N→N+2 (15–21), N→N+4 (22–44); net↔pkg pairings unchanged; positions
  15/16 NC (analog note), 24 = VU ← carrier +5V, 25 = GND; fictional CMOD_3V3
  pin and SJ1/SJ2 jumpers deleted; power strategy revised: **carrier +5V powers
  the module via VU** (don't also power module USB without a backfeed check).
  Regenerated pinmap.md + digital.kicad_sch + sonar_cmod_a7.xdc.
- New reproducible gate: `scripts/check_pinmap_vs_xdc.py` parses the live-fetched
  XDC and asserts 44/44 on position+label+pkg+IO-name+bank+CC. Output:
  `PASS: 44/44 DIP positions match the live master XDC ...; special positions
  15/16/24/25 = [15, 16, 24, 25]; PDM_CLK_FB/FT_CLKOUT/ETH_REF_CLK all
  clock-capable.` True CC set printed: [3,5,8,18,19,36,37,38,40,43,46,47,48].
  Note: PDM_CLK_FB is on pkg W4 (= true pio40, MRCC_34), not W5 as the repair
  brief parenthesized — W5/pio36 (also MRCC_34) now carries FT_RD_N; both CC.
- Verification: `scripts/check.sh` — sonar ERC 455 msgs / 339 err (was 456/339;
  delta = removed SJ/power-flag noise), **/digital/ section: 0 violations**;
  netlist/PDF/SVG/BOM exports all exit 0. Netlist cross-check of build/sonar.net:
  J40 has exactly 46 connected pins (44 I/O + pin24=+5V + pin25=GND), 13/13 spot
  checks PASS incl. 15/16 NC; CMOD_3V3/CMOD_VU gone from netlist. `pcb drc` still
  SIGABRTs (exit 134) on ALL projects incl. untouched ones — environmental
  sandbox issue, unchanged; needs the approved unsandboxed run per T-006.
- Status: T-011 stays **in-progress** until the orchestrator re-verifies. Files
  changed (uncommitted; orchestrator commits): scripts/gen_digital_sheet.py,
  scripts/check_pinmap_vs_xdc.py (new), orchestration/pinmap.md,
  sonar-v1-pcb/digital.kicad_sch, gateware/constraints/sonar_cmod_a7.xdc,
  docs/pdm-capture-contract.md, ticket log, STATUS.md, this journal.
