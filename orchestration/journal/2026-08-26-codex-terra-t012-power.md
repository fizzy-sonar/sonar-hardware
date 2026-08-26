# 2026-08-26 — codex/terra-t012 — T-012 power-tree prune

## What happened
Claimed T-012 (tier mid, Terra — match). Pruned the Sonar v1 power tree to the
D011 four-rail set and made the whole power subtree ERC-clean.

Design now: USB-C VBUS / XT60 → FB1 → power_mux (2× DZDH0401DW-7 + AO3415
ideal-diode OR) → global **5V** (VMUX) → AP63301WU-7 buck → **+3.3V** (3V3_D)
→ FB2 (fit 0R; ferrite option) → **3V3_MIC** (≥100 mA, T-008); 5V → TPS55340
boost → **+12V** for TX (T-013 hooks it to DRV8876 VM). Sequencing: buck EN to
Vin; boost EN to +3.3V via R164 (12 V after 3V3_D). Test points TP80/81/82/86
(+5V/+12V/+3.3V/3V3_MIC). Details + bring-up checks: `orchestration/rails.md`.

Deleted files: 5_to_10_boost, inverting_buck_boost(+_OLD), -10v_negative_ldo,
2.75V_ldo, 12v_to_10v_ldo, 5V_in_adjustable_buck. power_supply.kicad_sch
rewritten; 5v_to_12v_boost.kicad_sch finished (COMP RC, PGND PWR_FLAG, EN
sequencing); ideal_diode re-homed to sonar_lib (kills GS_PMIC/GS_SO warnings);
top sheet: dead power_supply sheet pins removed, global `5V` label on VMUX,
XT60/USB-C connector pin types fixed. digital.kicad_sch + pinmap.md untouched.

## Verification (kicad-cli 10.0.1)
- ERC (the gate): 456/339/117 (msgs/err/warn at HEAD) → **377/298/79**;
  power_supply, boost, power_mux, ideal_diode0/1 sections: **0 messages**.
  No message-type count increased vs baseline; the rest is T-010/T-013/GS-lib
  scope. Full real output pasted in the T-012 ticket Log.
- check.sh: ERC exit 5 (soft-accepted violations, as baseline), netlist/PDF/
  SVG/BOM exit 0 on all three projects; **`pcb drc` SIGABRTs (exit 134) in this
  sandbox — environmental, DRC not run, must be re-run unsandboxed.**
- Netlist spot-check OK but export is NONDETERMINISTIC under the pre-existing
  C6 duplicate-ref annotation error (baseline shows the same flakiness) — do
  not use the netlist as a connectivity gate until C6 is fixed (T-013/T-010).
- Visual: build/sonar-svg renders of power_supply/boost/mux/top inspected.

## KiCad 10.0.1 hand-editing gotchas (cost me an hour; save the next agent)
1. Symbol instances need `(pin "N" (uuid ...))` entries for every pin or the
   netlist silently drops the whole subsheet ("Failed to load schematic" when
   loaded standalone; ERC still parses it — misleading).
2. `(at x y)` without a rotation field fails to load. Always write `(at x y 0)`.
3. Keep hierarchical sheet-block UUIDs stable: child components' instance paths
   embed them. A fresh sheet uuid orphaned the boost sheet's annotation and
   wires "dangled" until I restored the old uuid (3221bd23-…).
4. Zero-length-pin symbols (power symbols, PWR_FLAG, TestPoint_Probe) landing
   mid-wire need an explicit `(junction …)` at that point to connect.
5. Don't leave wire ends in space — a dangling-ended wire poisons connectivity
   of the items along it.
6. Symbol-def coordinates are y-up relative to the sheet (def y is negated on
   placement). I "repaired" the TPS55340 FREQ wire onto a non-pin and had to
   revert — trust ERC-reported pin coordinates, not my mental math.
7. New refs must be checked against the **netlist comp list**, not just
   per-file Reference properties — multi-instance subsheets (mems_rx etc.)
   reuse refs like C163/C166 per instance path.

## State / next
T-012 → done. Uncommitted in worktree `agent/T-012-power-tree` (sandbox can't
write .git — orchestrator commits). Remaining queue unchanged: T-013 (TX, +12V
consumer), T-010 (blocked on T-016 CP-BM), T-011 needs Joshua's 60-s master-XDC
fetch. KiCad files changed on disk again — Joshua: reload KiCad before opening.
