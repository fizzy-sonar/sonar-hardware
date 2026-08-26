---
id: T-012
title: Prune power tree to four rails
status: ready
phase: P2
tier: mid        # KiCad power-tree edits
priority: 2
assignee:
depends_on: [T-002]
needs_human: false
created: 2026-08-25
updated: 2026-08-25
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
