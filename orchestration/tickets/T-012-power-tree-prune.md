---
id: T-012
title: Prune power tree to four rails
status: done
phase: P2
tier: mid        # KiCad power-tree edits
priority: 2
assignee: codex/terra-t012
depends_on: [T-002]
needs_human: false
created: 2026-08-25
updated: 2026-08-26
---
## Goal
**2026-08-25 scope update (D011)**: rails are now 5 V, 3.3 VD, optional mic rail (1.8 V?) per T-008, 12 V TX. No 3.3 VA opamp rail. Original text below kept for history.

Keep: mux (finish it), 5 V, 3.3 VA (LDO), 3.3 VD, 12 V TX boost. Delete sheets: 5_to_10_boost, inverting_buck_boost(_OLD), -10v_negative_ldo, 2.75V_ldo, 12v_to_10v_ldo, 5V_in_adjustable_buck. Add sequencing/bulk caps; rails documented with expected current in the bring-up runbook format.

## Context
Decision D002 consequences list; defect #3 (rail mismatch).

## Definition of Done
power_supply.kicad_sch is a complete, ERC-clean tree; every rail consumed somewhere; a rails table in `orchestration/rails.md`.

## Verification
check.sh ERC; rails table reviewed at CP-C.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 codex/sol-t008: marked ready after T-002 completion. Use T-008's
  provisional 3.3 V / >=100 mA mic-rail allocation; T-016 may require an increase
  from measured current but does not block unrelated power-tree work.

- 2026-08-26 codex/terra-t012: power tree pruned to four rails and finished.
  `power_supply.kicad_sch` rewritten: 5V bus (mux output, PWR_FLAG, TP80, bulk
  22u/10u/100n), AP63301WU-7 3V3_D buck (L4 2.2uH, Cin 10u+100n, Cout 2x22u,
  BST 100n, FB 31.6k/10k -> 3.33 V, EN 100k to Vin), 3V3_MIC branch (FB2, fit 0R
  0603 initially, 120R@100MHz ferrite option per T-008; 10uF+1uF bulk; >=100 mA
  allocation), +12V from the existing TPS55340 boost subsheet (TP81, 22u bulk).
  Sequencing: boost EN pulled to +3.3V (R164) so 12V rises after 3V3_D; buck EN
  pulled to Vin (R160). Boost sheet finished: COMP network added (R163 10k +
  C261 4.7nF, datasheet starting point - verify stability at bring-up), SYNC
  already to GND, PGND got PWR_FLAG (#FLG406). ideal_diode re-homed to
  sonar_lib:DZDH0401DW-7 + footprint Package_TO_SOT_SMD:SOT-363_SC-70-6 (kills
  GS_PMIC/GS_SO lib warnings). Deleted sheets: 5_to_10_boost,
  inverting_buck_boost(+_OLD), -10v_negative_ldo, 2.75V_ldo, 12v_to_10v_ldo,
  5V_in_adjustable_buck. Top sheet: power_supply sheet-symbol pins pruned to
  Vin only, global label "5V" added on the VMUX wire (matches pinmap SJ2
  option), XT60 "-" pin and USB-C CC pins made passive (kills power-output
  conflicts). sonar_lib: added R_0603_31.6k (LCSC TBD -> T-014), fixed
  TPS55340PWPR stacked hidden SW pin (output -> passive), DZDH footprint.
  Rails table: orchestration/rails.md. digital.kicad_sch and
  orchestration/pinmap.md untouched.
  DoD note: "every rail consumed somewhere" holds for 5V (buck+boost inputs,
  SJ2 option) and +3.3V (digital sheet +3.3V, 15 uses) today; +12V consumer is
  T-013 (DRV8876 VM) and 3V3_MIC consumer is T-010 (mic array) - both wired and
  flagged ready, documented in rails.md. CP-C reviews.
  KiCad-10.0.1 gotchas for the next agent (also in journal): instance pins need
  (pin "N" (uuid ...)) maps or the netlister drops the sheet; `(at x y)` without
  rotation angle fails to load; a wire endpoint on a pin endpoint is unreliable
  unless the other wire end terminates cleanly - avoid dangling wire ends and
  pass-through crossings without junctions; hierarchical sheet-block uuids are
  embedded in child instance paths - reusing the old sheet uuid (3221bd23...)
  kept the boost sheet's annotation valid.
  VERIFICATION (kicad-cli 10.0.1, `./scripts/check.sh` + direct ERC):
    ERC gate (kicad-cli sch erc --severity-all, sonar.kicad_sch):
      baseline (HEAD): " ** ERC messages: 456  Errors 339  Warnings 117"
      now:             " ** ERC messages: 377  Errors 298  Warnings 79"
      per-sheet: /power_supply/ 0, /power_supply/Vin to 12V Boost/ 0,
      /power_mux/ 0, /power_mux/ideal_diode0/ 0, /power_mux/ideal_diode1/ 0
      (baseline: 10, 7, 0, 4, 4). No message-type count increased vs baseline;
      remaining 298 errors are T-010 array / T-013 TX-Drive / GS_* lib-table
      scope. pin_to_pin 12->0, multiple_net_names 3->0, similar_label_and_power
      5->0, hier_label_mismatch 125->116, power_pin_not_driven 118->108.
    Netlist spot-check (export is nondeterministic under the pre-existing C6
      duplicate-ref annotation error, so ERC is the gate): 5V = {U61/3, U35/3,
      U37/4, U38/4, J45/2, TP5/1, TP80/1, L2/1, R160/1, C174/1, C161/1, C162/1},
      +3.3V = {digital consumers..., FB2/1, R164/1, TP82/1},
      3V3_MIC = {FB2/2, C171/1, C181/1, TP86/1}, +12V = {D1/1, C180/1, TP81/1},
      Net-(U35-EN)={U35/4,R164/2}, Net-(U35-COMP)={U35/8,R163/1},
      Net-(U35-FREQ)={U35/10,R139/1} - all rails and regulator pins land right.
    ./scripts/check.sh: sonar ERC exit 5 (violations, soft-accepted as before),
      netlist/pdf/svg/bom exports exit 0; rx_amp_sim + txrx_dev unchanged
      (ERC exit 5 baselines). `kicad-cli pcb drc` SIGABRTs in this sandbox
      (exit 134, known environmental issue per STATUS/T-016) - DRC NOT run;
      re-run unsandboxed. ERC is the gate.
    Visual: build/sonar-svg/ pages rendered and inspected (power_supply, boost,
      mux, top power section all correct). Note: build/sonar-svg/ holds STALE
      pages of the deleted sheets from earlier runs (gitignored build dir is
      not cleaned by check.sh).
  Left for others: sonar.kicad_pcb still holds deleted sheets' footprints
  (resync at P3); T-014 sources R_0603_31.6k + FB2-as-0R; T-013 hooks +12V to
  DRV8876 VM; T-010 consumes 3V3_MIC.
