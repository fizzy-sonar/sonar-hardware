# STATUS — Sonar v1

_Last updated: 2026-08-25 by claude (fable) — GO given; CP-A complete; D012 ratified._

## Now
- **Phases open for agent work: P1 and P5.** P2 unlocks when T-002 + T-008 are done.
- Architecture locked (see PLAN.md v2): 24 PDM ultrasonic mics → Cmod A7-35T +
  FT232H USB streaming → Python DSP; Pico 2 snapshot v0; TX via DRV8876 + connector.
- **KiCad open?** Unknown — check before hand-editing `.kicad_sch` (README rules).

## Ready tickets (pick lowest priority number first)
- T-001 link-budget model (P1, prio 1)
- T-002 parts & lifecycle audit (P1, prio 1)
- T-007 buy list incl. Vivado-host options (P1, prio 1, needs_human at the end)
- T-009 Pico 2 snapshot firmware (P5, prio 1)
- T-006 kicad-cli check harness (P1, prio 2)
- T-020 Vivado gateware — TB layer needs no Vivado host (P5, prio 2)
- T-021 host software — benchmark pyftdi ingest early (P5, prio 2)
- T-008 PDM RX design — unlocks after T-002
- (optional, non-gating: T-005 EDA spike)

## Blockers
- Vivado synthesis (part of T-020) waits on the Vivado host purchase/decision (T-007
  item 7). The T-020 testbench layer is NOT blocked — start there.

## Notes for Joshua
- When T-007's buy list lands (status: review): purchase, and pick mini-PC vs cloud
  VM for Vivado. Everything else is agent-executable to CP-B/CP-C.
- Nothing from this session is committed to git yet; your pre-existing
  sonar.kicad_pro change is also uncommitted.

## Recent sessions
- 2026-08-25 — claude (fable): architecture review → decisions → orchestration →
  platform finalization + GO. See journal (one file, three addenda).
