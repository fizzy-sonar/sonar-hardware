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

