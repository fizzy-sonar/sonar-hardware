# STATUS — Sonar v1

_Last updated: 2026-08-26 by codex/sol-t011-audit — T-011 pin audit done offline; discrepancies resolved; U50→U60 collision fixed; one live master-XDC fetch (human, ~60 s) gates T-011 done._

## Now
- **Phases open for agent work: P1, P2, and P5.** T-002/T-008 are done and CP-B
  still reviews the analysis/bake-off thresholds. T-016 is ready for an agent to
  prepare the coupon/order/test package. Only T-010 is blocked on its physical
  result; T-011/T-012/T-013 and P5 may proceed.
- Architecture locked (see PLAN.md v2): 24 PDM ultrasonic mics → Cmod A7-35T +
  FT232H USB streaming → Python DSP; Pico 2 snapshot v0; TX via DRV8876 + connector.
- **T-001 done:** reference case gives +27.1 dB person margin at 10 m and 20.2 m
  zero-margin range. ICS-41352 adds only 0.15 dB total noise in the stated ambient
  context; keep D011 through the quantitative T-016 bake-off. Wideband TX
  calibration and small-target margin remain CP-B acoustic risks.
- **T-002 done:** parts/lifecycle matrix delivered. ICS-41352 is NRND; missing
  candidate/JLC evidence remains explicit rather than being treated as stock.
- **T-006 done:** KiCad CLI harness added with repo-local cache and hard-failure
  semantics. Approved unsandboxed runs pass end-to-end; baseline DRC is sonar
  175/499/0, rx_amp_sim 1/0/0, txrx_dev 1/0/0 (violations/unconnected/footprints).
- **T-007 review:** click-ready dev-hardware list and Vivado host comparison
  delivered; Joshua must choose reseller, host, and purchase timing.
- **T-008 done (electrical baseline only):** provisional SPH0641LU4H-1 at
  3.072 MHz, 24 mics paired onto 12 DATA lines, 3.3 V CDCLVC1112 clock tree, and
  9.216 MB/s raw contract v1. D011's final MPN/footprint is **not released**.
- **T-016 ready / human gate at CP-BM:** agent prepares separate 12-unit-per-MPN
  coupon designs, sourcing/order package, calibrated runbook, and analysis. Joshua
  alone authorizes/places coupon orders, operates/provides bench data, ratifies the
  MPN, and closes the ticket. No coupon source or spend is currently authorized.
  SPH 3.3 V max current, clock-input capacitance/load, and allowable PCB-port
  misregistration remain nonblocking evidence gaps to characterize, not invent.
- **T-011 audited offline (2026-08-26, codex/sol-t011-audit):** both flagged
  discrepancies RESOLVED (T-008 CC list corrupt — pio46/47/48 are DIP power pins;
  pio16/17 are the real MRCC_35 pair; pio18/19/37/38/40 not CC; no net assignments
  changed); LAN8720A ref collision U50→U60 found and fixed in the generator, all
  outputs regenerated, ERC re-run clean on /digital/; netlist cross-check
  J40 48/48, J41 20/20, J42 26/26, U60 25/25 PASS; capture-contract CC list
  corrected. **The audit sandbox also had no network**: one live fetch of the
  Digilent master XDC + reference manual (instructions at top of pinmap.md, ~60 s
  for Joshua in a browser) is the only remaining gate before T-011 → done.
- **UNCOMMITTED WORK WARNING:** the T-011 sandbox blocked all git writes (approval
  policy Never) — branch agent/T-011-digital-sheet has a complete working tree that
  the ORCHESTRATOR MUST COMMIT (`git add -A` in that worktree). Nothing was pushed.
- **KiCad open?** Unknown. **KiCad files changed on disk 2026-08-26 (sonar.kicad_sch,
  new digital.kicad_sch) — Joshua: reload KiCad before opening the project.**

## Work queue — launch ready tickets on the tier shown (routing table in README.md)

| Ticket | Tier | Notes |
|---|---|---|
| T-002 parts & lifecycle audit | **cheap** | **done**; matrix committed; unlocks T-008 |
| T-007 buy list + Vivado-host options | **cheap** | **review**; Joshua purchase/host choices remain |
| T-006 kicad-cli check harness | **cheap** | **done**; baseline recorded |
| T-009 Pico 2 snapshot firmware | mid | PIO/DMA; the first-echoes path |
| T-021 host software | mid | benchmark pyftdi ingest early |
| T-020 Vivado gateware | **top** | TB layer can parameterize 3.072/4.8 MHz now; synthesis waits on host |
| T-008 PDM RX design | **top** | **done**; provisional electrical baseline, not physical MPN release |
| T-016 mic coupon bake-off | mid | **ready**; agent package ends at human CP-BM purchase/bench/release gate |
| T-010 array sheet | mid | **blocked on T-016**; no provisional footprint/BOM freeze |
| T-011 digital sheet | **top** | audited offline, fixes applied; **needs 60-s human live master-XDC diff** then done |
| T-012 power tree | mid | **ready**; carry >=100 mA provisional mic rail |
| T-013 TX hookup | mid | **ready**; independent of mic release |

T-007 is **in review** (buy list repaired; Joshua choices remain).

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
- T-010, T-014's microphone line, and CP-C are blocked on T-016. After its agent
  package reaches `review`, the exact remaining human gate is: Joshua approves and
  places/pays for coupons, provides/operates the calibrated bench capture, and
  ratifies the resulting exact MPN/footprint release. Agents do not perform those
  actions and no order is authorized yet.

## Notes for Joshua
- When T-007's buy list lands (status: review): purchase, and pick mini-PC vs cloud
  VM for Vivado. Separately, do nothing on microphone coupons until T-016 reaches
  `review` with a checked order/runbook package; CP-BM will ask explicitly then.
- MA40S4S is 40 kHz-only; a 12 V full bridge also exceeds its published
  continuous-square Vpp limit. T-013 must enforce the selected transducer's limit.
- The orchestration baseline and T-001 are committed. Joshua's pre-existing
  `sonar-v1-pcb/sonar.kicad_pro` change remains untouched and uncommitted.

## Recent sessions
- 2026-08-26 — codex/sol-t011-audit: offline pin audit complete; discrepancies
  resolved; U50→U60 fixed; contract doc corrected; live master-XDC fetch is the
  last gate. See ticket log + journal addendum.
- 2026-08-26 — codex/sol-t011: T-011 digital sheet/pinmap/XDC delivered; ERC-clean
  digital sheet; DF40/adc_bus removed; git sandbox-blocked (orchestrator must commit);
  pin audit pending. See journal + ticket log.
- 2026-08-25 — codex/sol-t008: repaired independent-review findings by making SPH
  provisional, defining quantitative D011/T-001 thresholds, adding T-016/CP-BM,
  and blocking only T-010's physical MPN/footprint freeze; no KiCad file edited.
- 2026-08-25 — codex/sol-t008: completed PDM mic selection/electrical design,
  paired-edge timing and current budgets, physical bake-off/calibration plan, and
  capture contract v1; no KiCad file edited.
- 2026-08-25 — codex: completed T-001 ISO/manufacturer-backed link-budget model,
  plots, microphone comparison, and blind-zone schedule; see journal and ticket log.
- 2026-08-25 — claude (fable): architecture review → decisions → orchestration →
  platform finalization + GO. See journal (one file, three addenda).
