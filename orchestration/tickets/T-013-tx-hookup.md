---
id: T-013
title: Connect the h-bridge; TX connector
status: done
phase: P2
tier: mid        # KiCad edits, small scope
priority: 3
assignee: codex/terra-t013
depends_on: [T-002]
needs_human: false
created: 2026-08-25
updated: 2026-08-26
---
## Goal
Give 20kHz-h-bridge.kicad_sch real hierarchical ports (defect #4), wire control lines to the digital sheet, add the off-board TX connector + optional series-L/snubber footprints (DNP-able).

## Context
Decisions D007, D001 (center cell hosts connector/hole).

## Definition of Done
ERC-clean; drive path traceable top-sheet → DRV8876 → connector.

## Verification
check.sh ERC.

## Log
- 2026-08-25 claude (fable): ticket created from architecture review.
- 2026-08-25 codex/sol-t008: marked ready after T-002 completion; mic coupon/MPN
  release in T-016 does not affect the TX hookup.
- 2026-08-26 codex/terra-t013: done. Rewrote 20kHz-h-bridge.kicad_sch (defect #4):
  five real hierarchical ports (TX_EN/TX_PH/TX_NSLEEP/TX_PMODE in, TX_NFAULT out)
  matched by sheet pins on the top-sheet TX Drive block, each bridged there to the
  digital sheet's global labels. Full DRV8876 (U62) hookup: VM=+12V (C286 100nF +
  C287 10uF), VCP bypass C285 1uF (+PWR_FLAG #FLG407, TI types VCP power_in),
  CPH-CPL C284 47nF, VREF=+3.3V, IPROPI R171 1.69k (trip ~1.95A), IMODE strap
  R172 10R to GND, nFAULT pull-up R170 10k to +3.3V (per pinmap), GND/PGND/EP to
  GND. Off-board transducer connector J50 (MKDS 5.08mm screw terminal) via 0R
  series R173/R174 (0603-L EMI option) with DNP RC snubber R175+C288 across the
  load. Re-homed DRV8876PWPR + C_0603_22nF->47nF and new R_0603_0R into
  sonar_lib (kills GS_H_Bridges/GS_Capacitor_0603/GS_SO missing-lib warnings;
  DRV8876 footprint now stock Package_SO). Old U34/C6 refs retired (fixes the
  pre-existing C6 duplicate-ref - netlist is now deterministic). TX waveform
  limits for T-020 documented in orchestration/tx-limits.md (MA40S4S: 40kHz only,
  20Vpp continuous square -> amplitude cap 187/256; verified against local
  datasheet PDF Table 1).
  CP-C verify items (offline here, flagged on-sheet): PMODE polarity
  (high = IN1/IN2 PWM), IMODE=GND strap mode, CPH-CPL 47nF vs George's 22nF.

  Verification (kicad-cli 10.0.1, this worktree):
    $ scripts/check.sh -> sonar_erc exit=5 (soft-accepted baseline violations),
      netlist/pdf/svg/bom exit=0 all three projects; pcb drc SIGABRTs (exit 134)
      in this sandbox - environmental (T-006/T-012 saw the same), ERC is the gate.
    ERC message totals: 377 (298 err/79 warn) at branch HEAD -> 347 (276/71).
      Per-category: pin_not_connected 32->24, power_pin_not_driven 108->105,
      pin_not_driven 12->6, isolated_pin_label 22->18 (TX_* labels now land on
      U62), lib_symbol_issues 26->24, footprint_link_issues 26->24.
      NO category increased; no new message types.
      Section "***** Sheet /TX Drive/" is EMPTY (zero messages) - was 22 errors.
      TX Drive hier_label_mismatch: none (5 pins match 5 labels).
    Netlist node audit (build/sonar.net, kicad-cli sch export netlist):
      U62.1=TX_EN(J40.1,TP404) U62.2=TX_PH(J40.2) U62.3=TX_NSLEEP(J40.44)
      U62.16=TX_PMODE(J40.8) U62.4=TX_NFAULT(J40.5,R170) U62.5=+3.3V
      U62.11=+12V U62.12/13/14=charge-pump caps U62.9/15/17=GND
      Drive path: U62.8 OUT1 ->TX_DRV1-> R173 -> J50.1 ; U62.10 OUT2 ->TX_DRV2->
      R174 -> J50.2 ; snubber R175+C288 bridges J50.1/J50.2 (DNP).
      Old refs: U34 ABSENT; C6 only in legacy eight_transducer_array.
    Netlist determinism: two consecutive exports differ only in the (date) line -
      T-012's nondeterminism was the C6 dup, now fixed. Remaining "annotation
      errors" warning = legacy cross-sheet ref collisions (C167/R41/TP87... in
      eight_transducer_array/rx_amp/quad_rx_pre_amp/mems_rx) - T-010 scope, not T-013.
    BOM: J50/U62/R170-175/C284-288 present with footprints; R175/C288 marked DNP.
    Visual: SVG renders of TX Drive + top sheet inspected (ports, labels, notes
      box, no symbol/wire collisions).
  Not done / next: pcb drc re-run unsandboxed (environmental); CP-C datasheet
  strap checks above; CP-E bench Vpp measurement at J50.
