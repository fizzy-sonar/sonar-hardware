# STATUS — Sonar v1

_Last updated: 2026-08-25 by codex — T-001 complete; link budget is not nominally PDM-SNR-gated._

## Now
- **Phases open for agent work: P1 and P5.** P2 unlocks when T-002 + T-008 are done.
- Architecture locked (see PLAN.md v2): 24 PDM ultrasonic mics → Cmod A7-35T +
  FT232H USB streaming → Python DSP; Pico 2 snapshot v0; TX via DRV8876 + connector.
- **T-001 done:** reference case gives +27.1 dB person margin at 10 m and 20.2 m
  zero-margin range. ICS-41352 adds only 0.15 dB total noise in the stated ambient
  context; keep D011 through the T-002/T-008 bake-off. Wideband TX calibration and
  small-target margin are the remaining CP-B acoustic risks.
- **KiCad open?** Unknown — check before hand-editing `.kicad_sch` (README rules).

## Ready tickets — launch each on the tier shown (routing table in README.md)

| Ticket | Tier | Notes |
|---|---|---|
| T-002 parts & lifecycle audit | **cheap** | in-progress (codex); unlocks T-008 |
| T-007 buy list + Vivado-host options | **cheap** | ends at `review` for Joshua to purchase |
| T-006 kicad-cli check harness | **cheap** | shell scripting |
| T-009 Pico 2 snapshot firmware | mid | PIO/DMA; the first-echoes path |
| T-021 host software | mid | benchmark pyftdi ingest early |
| T-020 Vivado gateware | **top** | TB layer needs no Vivado host — start there |
| T-008 PDM RX design | **top** | unlocks after T-002 |

Optional/non-gating: T-005 EDA spike (mid). T-001 done 2026-08-25.
**The three `cheap` tickets do not need a reasoning model — launch them small.**

## Cost note (2026-08-25)
Joshua burned ~25% of a weekly Codex budget in the architecture-exploration session
(the most token-hungry phase). P1/P5 tickets are bounded by comparison. See the
**Model / tier routing** table in `orchestration/README.md` — running T-002/T-006/
T-007 on a top reasoning tier is the main avoidable waste. Decision rule: if the
*weekly* cap is hit before the week ends under the new ticket workflow, escalate
(credits first, then the 5× tier); the 5-hour cap alone is pacing, not a blocker.

## Blockers
- Vivado synthesis (part of T-020) waits on the Vivado host purchase/decision (T-007
  item 7). The T-020 testbench layer is NOT blocked — start there.

## Notes for Joshua
- When T-007's buy list lands (status: review): purchase, and pick mini-PC vs cloud
  VM for Vivado. Everything else is agent-executable to CP-B/CP-C.
- MA40S4S is 40 kHz-only; a 12 V full bridge also exceeds its published
  continuous-square Vpp limit. T-013 must enforce the selected transducer's limit.
- The orchestration baseline and T-001 are committed. Joshua's pre-existing
  `sonar-v1-pcb/sonar.kicad_pro` change remains untouched and uncommitted.

## Recent sessions
- 2026-08-25 — codex: completed T-001 ISO/manufacturer-backed link-budget model,
  plots, microphone comparison, and blind-zone schedule; see journal and ticket log.
- 2026-08-25 — claude (fable): architecture review → decisions → orchestration →
  platform finalization + GO. See journal (one file, three addenda).
