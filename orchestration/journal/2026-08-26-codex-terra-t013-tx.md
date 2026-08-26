# 2026-08-26 — codex/terra-t013 — T-013 TX hookup

## What happened
T-013 (tier mid, Terra — match) done. The TX Drive sheet (20kHz-h-bridge.kicad_sch)
was a draft: U34 + one 22nF cap, 15 unconnected pins, no ports (defect #4). Full
rewrite, sheet uuid and instance path kept stable.

Final design: DRV8876 (U62) on VM=+12V (100nF+10uF), VCP→VM 1uF + PWR_FLAG,
CPH–CPL 47nF, VREF=+3.3V, IPROPI 1.69k→GND (trip ≈1.95A, regulation never
engages), IMODE 10R→GND, nFAULT 10k pull-up→+3.3V, GND/PGND/EP→GND. Five
hierarchical ports (TX_EN/TX_PH/TX_NSLEEP/TX_PMODE in, TX_NFAULT out) ↔ sheet pins
on the top-sheet TX Drive block ↔ global labels to the digital sheet (T-011 had
already placed TX_* global labels; the netlist shows them joined to J40 pins
1/2/44/8/5). Off-board transducer on J50 (MKDS 5.08mm screw terminal) through 0R
series R173/R174 (swap-for-0603-L EMI option), DNP RC snubber R175+C288 across the
load. Drive path verified in the netlist: OUT1→R173→J50.1, OUT2→R174→J50.2.

Re-homed DRV8876PWPR + 47nF cap into sonar_lib and added R_0603_0R there
(MPN/LCSC blank = sourcing gap for T-014, same convention as T-012's R161).
DRV8876 footprint GS_SO:→stock Package_SO: (identical geometry name). Symbols
edited in the re-home: PGND pin unspecified→power_in, EP unhidden (kills the
multiple_net_names GND/EP warning). Retired refs U34/C6 → U62/C284: the C6 dup
was the source of T-012's nondeterministic netlist; two consecutive exports now
differ only in the date line.

Gateware contract: `orchestration/tx-limits.md` — MA40S4S (datasheet PDF is local:
sonar-v1-pcb/data_sheets/ultrasonics.pdf, Table 1: 20 Vpp continuous square,
40 kHz) gets fixed-tone 40 kHz, amplitude ≤187/256 (fundamental-equivalent 20 Vpp;
full-scale 12V bridge = 24 Vpp would violate it), burst ≤10 ms; tweeter chirp
20–32 kHz provisional. tx_a→EN/IN1, tx_b→PH/IN2, TX_PMODE high = PWM mode.

## Verification
ERC gate: project 377(298e/79w) → 347(276e/71w); TX Drive section ZERO messages;
no category increased. Netlist node audit (full table in ticket Log) PASS. BOM
picks up all new parts, DNP flags on snubber. SVG renders inspected. `pcb drc`
SIGABRTs (exit 134) in this sandbox — environmental, same as T-006/T-012/T-016;
re-run unsandboxed.

## Gotchas for the next agent (beyond T-012's list)
- Literal newlines inside KiCad text strings break the whole-project load with a
  bare "Failed to load schematic" (no file/line). Use `\n` escapes. A paren
  balance check won't catch this.
- kicad-cli ERC on a top sheet that fails to load still exits 0-ish and leaves the
  STALE report on disk — check the report's timestamp before trusting counts.
- Hidden power pins (DRV8876 EP) create an implicit global net named after the
  pin; overlapping it with a visible GND pin + power:GND symbol triggers
  multiple_net_names. Unhiding the EP pin in the project lib fixes it cleanly.
- Power symbol typed `power_in` on an internally-driven node (VCP charge pump):
  PWR_FLAG on the net is the accepted ERC idiom.
- "Annotation errors" warning on netlist export persists: legacy cross-sheet ref
  collisions (C167/R41/TP87… across eight_transducer_array/rx_amp/quad_rx_pre_amp/
  mems_rx). Not T-013 scope — T-010 replaces those sheets.

## State / next
All changes uncommitted in worktree agent/T-013-tx-hookup (sandbox can't write
.git — orchestrator commits/merges). Files touched: 20kHz-h-bridge.kicad_sch,
sonar.kicad_sch (TX Drive pins + labels + note), sonar_lib.kicad_sym
(DRV8876PWPR, C_0603_22nF, R_0603_0R added), orchestration/tx-limits.md (new),
ticket, STATUS.md, CLAUDE.md, rails.md one-liner. Open items: CP-C datasheet strap
checks (PMODE/IMODE/47nF), unsandboxed pcb drc, CP-E Vpp measurement at J50.
**KiCad files changed on disk again — Joshua: reload KiCad before opening.**
