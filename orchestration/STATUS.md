# STATUS — Sonar v1

_Last updated: 2026-08-26 by claude/orchestrator — T-011 live-gate repair verified and done; T-005 spike done (NO-GO); every non-human-gated ticket is now complete._

## Now
- **Agent queue exhausted 2026-08-26; the project is human-gated.** P1/P2/P5
  agent work is landed: T-009/T-021/T-012/T-013 done, T-011 done (live-gate defect found +
  repaired + re-verified), T-016 at review (CP-BM), T-020 simulator milestone
  done (bitstream waits on Vivado host). Remaining: Joshua's CP-B/CP-BM reviews,
  T-007 purchases/host choice, then T-010 (unblocked by CP-BM) → T-014 → T-015
  (cross-family review) → CP-C. T-005 EDA spike: **done, NO-GO for v1** (host `pcb build` confirmed the boundary) — see `spikes/eda-zener/REPORT.md`.
- Architecture locked (see PLAN.md v2): 24 PDM ultrasonic mics → Cmod A7-35T +
  FT232H USB streaming → Python DSP; Pico 2 snapshot v0; TX via DRV8876 + connector.
- **T-021 done:** host reference pipeline now has strict SNP1/SNR1 parsers, buffered
  ingest, `.npy`/ring storage, 24-channel CIC+FIR decimation, per-channel
  calibration, chirp/matched filter/beamforming, deterministic synthetic recovery
  tests, demo artifact generation, and a synthetic in-memory ingest benchmark at
  4042.582 MB/s versus the 9.216 MB/s contract (re-run 2026-08-26:
  3888.015 MB/s, PASS). Physical FT232H/libusb capture is still untested; `pytest`
  is uninstallable in the offline sandbox, so the ticket-sanctioned `unittest`
  fallback (5/5 OK) is the verification of record.
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
- **T-009 done (host-verified, hardware pending):** one finite PIO SM generates
  clock and samples both DDR edges; one-shot DMA capture buffers alternate between
  commands after standard/ultrasonic drains. Direct TinyUSB CDC, quantized clock
  reporting, ultrasonic-only frame counters, GPIO guards, packet/CRC checks, and
  partial-write/backpressure tests pass. No Pico SDK or hardware is present, so no
  PIO assembly/ARM build, enumeration, waveform, mic, or physical throughput is
  claimed. T-011 owns board pins; T-021 owns canonical packet-format adoption.
- **T-008 done (electrical baseline only):** provisional SPH0641LU4H-1 at
  3.072 MHz, 24 mics paired onto 12 DATA lines, 3.3 V CDCLVC1112 clock tree, and
  9.216 MB/s raw contract v1. D011's final MPN/footprint is **not released**.
- **T-016 at `review` / human gate at CP-BM:** separate SPH and ICS coupon
  designs, sourcing/order package, runbook, fixture drawing, raw-data schema,
  and the deterministic analyzer are delivered and verified
  (`coupons/mic-bakeoff/check_coupons.sh` exit 0). Caveats called out in the
  ticket Log: CDCLVC1112PWR pin map UNVERIFIED (offline); `kicad-cli pcb drc`
  must be re-run unsandboxed (it SIGABRTs in the agent sandbox even on
  known-good boards); distributor stock/prices need re-checking at order time.
  Joshua alone runs the pre-order checklist, authorizes/places coupon orders,
  operates/provides bench data, ratifies the MPN, and closes the ticket. SPH
  3.3 V max current, clock-input capacitance/load, and allowable PCB-port
  misregistration remain nonblocking evidence gaps to characterize, not invent.
- **T-011 live-source gate FAILED, then repaired (2026-08-26, codex/sol-t011):**
  the orchestrator's live fetch of the Digilent master XDC + reference manual
  showed the offline pin table was WRONG on DIP positions — truth is
  pio[01]..pio[48] skipping pio15/16 (XADC analog-only) and pio24/25 (VU/GND; no
  3V3 pin exists). All net↔package-pin pairings were already valid; the fix was
  a pure position re-map (N→N 1-14, N→N+2 15-21, N→N+4 22-44), position 24=VU←
  carrier +5V (new power strategy; SJ1/SJ2 and the fictional CMOD_3V3 pin
  removed), 25=GND, 15/16 NC. The prior offline audit's "T-008 CC list corrupt"
  resolution was a correlated-recall error — REVERTED; true CC set =
  {3,5,8,18,19,36,37,38,40,43,46,47,48} (T-008 was right; contract doc restored).
  All outputs regenerated; reproducible gate committed:
  `scripts/check_pinmap_vs_xdc.py` → PASS 44/44 vs the live XDC; ERC /digital/
  section zero violations. **T-011 stays in-progress until orchestrator
  re-verifies.**
- **UNCOMMITTED WORK WARNING:** T-011 repair changes are in the working tree,
  (TX_EN/TX_PH/TX_NSLEEP/TX_PMODE/TX_NFAULT) bridged on the top sheet to the
  digital sheet's global labels; DRV8876 fully wired (VM=+12V, charge pump,
  VREF=3.3V, ~1.95A trip, nFAULT pull-up); off-board transducer on J50 screw
  terminal via 0R series elements + DNP RC snubber. Project ERC 377->347, TX
  Drive section at zero messages; drive path netlist-verified (OUT1/2 -> R173/174
  -> J50). MA40S4S 20Vpp/40kHz limit enforced via documented gateware envelope
  (orchestration/tx-limits.md, amplitude cap 187/256). CP-C verify items: PMODE/
  IMODE straps, CPH-CPL 47nF. `pcb drc` still SIGABRTs in the sandbox (exit 134).
- **T-012 done:** power tree pruned to four rails (5V mux output, +3.3V buck,
  3V3_MIC filtered branch at >=100 mA per T-008, +12V TX boost) and fully
  ERC-clean (project ERC 456/339/117 -> 377/298/79; power sheets at zero
  messages). Sequencing (12V after 3V3_D), bulk caps, rail test points, and the
  bring-up rails table are in `orchestration/rails.md`. Seven legacy converter
  sheets deleted. `pcb drc` still SIGABRTs in the sandbox (exit 134) — ERC is
  the gate; DRC re-run unsandboxed remains open.
- **KiCad open?** Unknown. **KiCad files changed on disk 2026-08-26 (sonar.kicad_sch,
  new digital.kicad_sch) — Joshua: reload KiCad before opening the project.**
  2026-08-26 terra-t012: power-tree files rewritten/deleted on branch
  agent/T-012-power-tree (power_supply, 5v_to_12v_boost, ideal_diode,
  sonar.kicad_sch, sonar_lib.kicad_sym; 7 legacy sheets deleted). Reload KiCad.
  2026-08-26 terra-t016: new KiCad files added under `coupons/mic-bakeoff/` on
  branch agent/T-016-mic-bakeoff (no existing project files touched); reload
  before opening if KiCad had the repo open.
  2026-08-26 terra-t013: 20kHz-h-bridge.kicad_sch rewritten, sonar.kicad_sch
  (TX Drive sheet pins + labels) and sonar_lib.kicad_sym (DRV8876PWPR,
  C_0603_22nF, R_0603_0R added) changed on branch agent/T-013-tx-hookup.
  Reload KiCad.

## Work queue — launch ready tickets on the tier shown (routing table in README.md)

| Ticket | Tier | Notes |
|---|---|---|
| T-002 parts & lifecycle audit | **cheap** | **done**; matrix committed; unlocks T-008 |
| T-007 buy list + Vivado-host options | **cheap** | **review**; Joshua purchase/host choices remain |
| T-006 kicad-cli check harness | **cheap** | **done**; baseline recorded |
| T-009 Pico 2 snapshot firmware | **mid** | **done (host-verified)**; physical integration waits on pins/SDK/board |
| T-021 host software | mid | **done**; physical FT232H/libusb still untested |
| T-020 Vivado gateware | **top** | **in-progress**; `make test` PASS (11/11, Icarus 13.0) incl. the 512 KiB SRAM snapshot fallback (full-window bit-exact); real XDC landed + SRAM pins appended; bitstream waits on the Vivado host + a `sonar_top` port-name reconciliation pass |
| T-008 PDM RX design | **top** | **done**; provisional electrical baseline, not physical MPN release |
| T-016 mic coupon bake-off | mid | **review**; agent package delivered + verified; Joshua's CP-BM checklist in `coupons/mic-bakeoff/docs/order-package.md` |
| T-010 array sheet | mid | **blocked on T-016**; no provisional footprint/BOM freeze |
| T-011 digital sheet | **top** | **done**; live-gate repair verified 44/44 vs live master XDC; `scripts/check_pinmap_vs_xdc.py` is the reproducible gate |
| T-012 power tree | mid | **done**; rails table in `orchestration/rails.md`; CP-C reviews |
| T-013 TX hookup | mid | **done**; TX Drive sheet ERC-clean, J50 connector, limits doc |

T-007 is **in review** (buy list repaired; Joshua choices remain).

T-005 EDA spike (mid): **done** — NO-GO for v1 (D008 stands); importer fails on all 3 real inputs; host-side `pcb build` run by orchestrator confirmed the hand-written-IC boundary. T-001 done 2026-08-25.
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
  item 7). The T-020 testbench layer is DONE and now includes the 512 KiB
  external-SRAM snapshot fallback (D012) with a timing-enforcing IS61WV5128BLL model:
  dual-rate sampler/packer/FIFO/FT245/UART-snapshot/SRAM-snapshot/TX-chirp sims all
  pass (11/11). Remaining T-020 DoD: batch build + utilization/timing/CDC +
  UNISIM/BRAM proofs + SRAM set_output_delay budgeting on the host; a deliberate
  `sonar_top` port-name reconciliation vs the T-011 XDC (pre-existing mismatch,
  incl. TX_EN/TX_PH mapping); live ISSI datasheet re-check of the model's timing
  constants; hardware FT232H/UART demo.
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
- 2026-08-26 — codex/terra-t005: T-005 EDA spike (diodeinc/pcb Zener) → NO-GO for v1;
  report `spikes/eda-zener/REPORT.md`, hand port + raw importer outputs under
  `spikes/eda-zener/`; ticket at review; sandbox blocked git — ALL changes
  uncommitted on branch agent/T-005-eda-spike, orchestrator commits. Journal:
  2026-08-26-codex-terra-t005-eda-spike.md.
- 2026-08-26 — codex/sol-t011 (repair): live-source gate FAILED the pin table;
  re-mapped DIP positions (15/16 analog NC, 24=VU←+5V, 25=GND), reverted the
  wrong audit CC "resolution" (T-008's list was right), added
  scripts/check_pinmap_vs_xdc.py (PASS 44/44 vs live XDC), ERC /digital/ clean.
  See ticket log + journal addendum 2.
- 2026-08-26 — codex/sol-t011-audit: offline pin audit — SUPERSEDED: its
  "confirmation" and CC-list resolution were correlated-recall errors (caught by
  the live gate). Real fixes it made that stand: U50→U60 refdes collision.
- 2026-08-26 — codex/terra-t013: T-013 done — TX hookup, hier ports, J50
  connector, tx-limits.md; verification + gotchas in the ticket Log and journal
  2026-08-26-codex-terra-t013-tx.md.
- 2026-08-26 — codex/terra-t012: T-012 done — four-rail power tree,
  ERC-clean power subtree, rails.md; gotchas + verification in journal
  2026-08-26-codex-terra-t012-power.md and the ticket Log.
- 2026-08-26 — codex/sol-t011: T-011 digital sheet/pinmap/XDC delivered; ERC-clean
  digital sheet; DF40/adc_bus removed; git sandbox-blocked (orchestrator must commit);
  pin audit pending. See journal + ticket log.
- 2026-08-26 — codex/terra-t016: T-016 coupon bake-off package (designs,
  analysis, runbook, order package) delivered and verified; ticket → review;
  CP-BM gate is Joshua's.
- 2026-08-26 — codex/sol-t020 (session 3): SRAM snapshot fallback done —
  `sram_snapshot.sv` + ISSI timing-checking model + TBs (back-to-back, timeout,
  full 512 KiB bit-exact), 48 MHz MMCM clock, sonar_top btn0/uart_rxd_out
  integration, 30 SRAM + UART pins appended verbatim to the real XDC;
  `make test` 11/11 PASS. All uncommitted (orchestrator commits). Ticket stays
  in-progress: Vivado host + port-name reconciliation + hardware demo remain.
- 2026-08-26 — codex/sol-t020: recovered the killed session's uncommitted
  `gateware/` work, committed it in four logical commits, re-ran `make test`
  (all PASS). Ticket stays in-progress on the Vivado-host/T-011 gates. Sandbox
  blocked worktree git writes, so commits are staged as
  `t020-gateware-commits.bundle` in the worktree — orchestrator fetches it per
  the ticket Log / journal before integrating.
- 2026-08-26 — codex/terra-t021: resumed the killed T-021 session; audited the
  pipeline against the DoD/D012 scope (all present), re-ran verification fresh
  (unittest 5/5 OK, demo recovers target, benchmark 421x contract), confirmed pytest
  is uninstallable offline; no code changes needed.
- 2026-08-26 — codex/sol-t021: replaced the stale host stub with strict packet and
  stream parsing, buffered ingest, real multichannel DSP/calibration/beamforming,
  deterministic synthetic recovery tests, demo artifact generation, and a synthetic
  in-memory benchmark above the 9.216 MB/s contract; `pytest` unavailable locally,
  `unittest` verification passed.
- 2026-08-26 — codex/terra-t009: T-009 close-out. No code changes; re-ran full
  host verification (C/Python tests, 49,152-frame synthetic capture byte-identical,
  287.3 dB tone recovery, ruff/diff clean); verification output pasted in ticket
  Log; ticket stays `done`; branch ready for orchestrator merge.
- 2026-08-26 — codex/t009-final-repair: repaired T-009's single-SM PIO timing,
  DMA/IRQ sequencing, direct TinyUSB CDC, clock quantization/counters, GPIO guards,
  backpressure tests, and stale architecture claims; hardware remains unvalidated.

- 2026-08-25 — codex/sol-t008: repaired independent-review findings by making SPH
  provisional, defining quantitative D011/T-001 thresholds, adding T-016/CP-BM,
  and blocking only T-010's physical MPN/footprint freeze; no KiCad file edited.
- 2026-08-25 — codex/sol-t008: completed PDM mic selection/electrical design,
  paired-edge timing and current budgets, physical bake-off/calibration plan, and
  capture contract v1; no KiCad file edited.
- 2026-08-25 — codex: completed T-001 ISO/manufacturer-backed link-budget model,
  plots, microphone comparison, and blind-zone schedule; see journal and ticket log.
- 2026-08-25 — codex/terra-t009: completed T-009's sim-allowed Pico snapshot
  firmware/host proof; no hardware validation claimed. See journal and ticket log.
- 2026-08-25 — claude (fable): architecture review → decisions → orchestration →
  platform finalization + GO. See journal (one file, three addenda).
