---
id: T-017
title: Zener deep port — registry/datasheet modules, real pcb build
status: done
phase: P1
tier: mid        # tool spike with network; scripting + datasheet transcription
priority: 4
assignee: codex/terra-t017
depends_on: [T-005]
needs_human: false
created: 2026-08-27
updated: 2026-08-27  # closed by codex/terra-t017
---
## Goal
T-005's NO-GO was driven by an offline sandbox (registry unreachable, ICs
unwritable). Joshua has now explicitly authorized pulling from the pcb package
registry AND hand-defining modules from datasheets. Give diodeinc/pcb (Zener) a
fair, full evaluation: port real Sonar v1 circuit blocks to `.zen` and make
`pcb build` actually succeed.

## Context
- T-005 spike artifacts: `spikes/eda-zener/` (REPORT.md, hand-port/, imports).
- Port targets (pick 2, in this order): (a) the RX preamp channel hand-port —
  complete it by defining `quad_opamp.zen` from the datasheet; (b) the T-012
  power supply sheet (`sonar-v1-pcb/power_supply.kicad_sch`, AP63301 buck +
  mic-rail filter). Optional stretch: TX h-bridge (DRV8876).
- Datasheets: `sonar-v1-pcb/data_sheets/`, manufacturer sites (network OK).
- `pcb` CLI is installed at ~/.local/bin/pcb on this host. Registry access is
  authorized by Joshua (2026-08-27). Network use is limited to package/datasheet
  fetches — no accounts, no purchases.
- D008 (KiCad remains the v1 EDA) is NOT being overturned; this spike informs v2.

## Definition of Done
`spikes/eda-zener/deep-port/` contains the ported `.zen` blocks; `pcb build`
succeeds and produces netlist + BOM; a comparison notes parity/gaps vs the KiCad
originals (pin counts, net spot-check); REPORT.md gains a "Deep port (T-017)"
verdict section with GO / NO-GO / GO-WITH-CONDITIONS and the evidence.

## Verification
Real `pcb build` output pasted in the ticket Log; BOM/netlist artifacts exist.

## Log
- 2026-08-27 claude/orchestrator: created at Joshua's direction ("push it
  further, port it, ok to pull from registry or define from datasheet").
- 2026-08-27 codex/terra-t017: DONE. Deep port built and verified on host
  (pcbc 0.4.38, network on). Verdict: GO-WITH-CONDITIONS for v2 authoring;
  D008 untouched. Full evidence in spikes/eda-zener/REPORT.md "Deep port
  (T-017)". Deliverables: spikes/eda-zener/deep-port/sonar_v1_deep_port/
  (components/{AP63301,OPA4171,DRV8876}.zen hand-written from live-fetched
  datasheets; modules/{power_supply,rx_preamp_tile,tx_drive}.zen;
  symbols/ + footprints/ vendored) + artifacts deep-port/{bom.txt,bom.json,
  netlist.net} and layout/{default.net,layout.kicad_pcb} (67 footprints).
  Registry finding: code.diode.computer registry + `pcb component` API are
  ACCOUNT-gated (401/403; no account allowed per rules) - all ICs
  hand-written (~10-20 min each). BOM stock/price API works anonymously.
  Importer re-test on host: still empty stub on power_supply.kicad_sch.
  Parity vs KiCad netlist: node-for-node exact on all checked nets (power
  sheet 5V/+3.3V/3V3_MIC/FB/SW/BST/EN; preamp ch0; TX block 17/17 DRV8876
  pins). ERC-equivalent voltage_within checks verified live via negative
  test (build fails on injected rail mismatch).

  Real verification output (host, 2026-08-27):

  $ pcb build .
  ✓ AP63301.zen (1 components)
  ✓ DRV8876.zen (1 components)
  ✓ OPA4171.zen (1 components)
  ✓ power_supply.zen (17 components)
  ✓ rx_preamp_tile.zen (37 components)
  ✓ tx_drive.zen (13 components)
  ✓ sonar_v1_deep_port.zen (67 components)

  $ pcb layout --no-open sonar_v1_deep_port.zen
  ✓ sonar_v1_deep_port.zen layout updated (.../layout/layout.kicad_pcb)

  $ pcb bom sonar_v1_deep_port.zen   (rows of interest; full table in
    deep-port/bom.txt)
  U1 OPA4171IDR  Texas Instruments    Quad 36V RRIO op-amp, SOIC-14
  U2 AP63301WU-7 Diodes Incorporated  C2158003  $0.96 ($4.80)
  U3 DRV8876PWPR Texas Instruments    C575551   $1.95 ($9.75)
  Total: US $8.68 | Global $3.82
  Matched / planner-ranked: 18 (75.0%) unique, 49 (87.5%) qty

  # Netlist spot-check (layout/default.net) vs KiCad (kicad-cli export):
  +5V:   C14.1 C15.1 C16.1 R17.1 TP11.1 U2.3      == KiCad 5V (6/6)
  +3V3:  C19.1 C20.1 FB1.1 L1.2 R19.1 TP9.1 (+TX) == KiCad +3.3V (6/6)
  3V3_MIC: C17.1 C18.1 FB1.2 TP10.1               == KiCad 3V3_MIC (4/4)
  PSU.Net-(U61-SW): C13.2 L1.1 U2.5  == Net-(U61-SW) (3/3)
  PSU.Net-(U61-FB): R18.1 R19.2 U2.1 == Net-(U61-FB) (3/3)
  # Negative ERC test: voltage_within("5V 10%")(v33) ->
  Error: Voltage range 3.3V 2% of +3V3 is not within 5V 10% (build FAILS,
  as designed; reverted)

  No git commits made (rule); ALL changes uncommitted in the worktree.
- 2026-08-27 codex/terra-t017 (session 2, AUTHENTICATED — Joshua's
  diode.computer account live): registry swap + BOM coverage survey done.
  (1) Coverage: 29 real v1 BOM lines probed via `pcb component search` —
  28/29 hit (only PSPHAQ127-270M boost inductor missed), 23/29 with
  symbol+footprint assets; ALL 10 key ICs/mics (AP63301, TPS55340,
  CDCLVC1112, LAN8720A, ICS-41352/41350, DRV8876, FT232HL, OPA4171AIDR,
  SPH0641LU4H-1) have full assets. Table in REPORT.md session-2 section;
  raw JSON in deep-port/coverage/results.json. (2) Swap: component API is
  search+download only (no in-language Part(mpn=) auto-resolution — verified
  in diodeinc/pcb source); flow = download signed S3 asset URLs (LCSC
  backend; CSE quota exhausted server-side) -> vendor files -> Component(
  symbol=Symbol(library=...), footprint=File(...)). All 3 hand-written
  components swapped to registry assets. `pcb build` ✓ 67 components;
  netlist parity: git diff of layout/default.net vs session-1 (KiCad-verified)
  netlist shows ZERO net/node line changes — only value/footprint/libsource
  strings + pin-name labels (GND-vs-PGND pin 4 AP63301; INA--style OPA4171;
  DRV8876 identical). pcb bom improved to 79.2% unique matched
  (OPA4171AIDR/C46269). Footprint geometry deltas (LCSC easyeda2kicad vs
  KiCad libs) are layout-only and documented per-component. (3) REPORT.md
  session-2 section added; verdict: GO-WITH-CONDITIONS strengthened —
  condition (a) account decision DROPS, (c) multi-unit softens (registry
  symbols have unique per-unit pin names); standing: toolchain pin, no
  importer, JLC house table. No commits (rule); all changes uncommitted.
