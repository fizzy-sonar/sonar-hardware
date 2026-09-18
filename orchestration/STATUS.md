# STATUS — Sonar v1

_Last updated: 2026-09-14 by codex/T-023 — USB-independent snapshots repaired
and top-level tested. T-023 remains in progress for commanded TX/status/timing
metadata; T-024/T-025 ready. Joshua prefers Vivado; D012 retained. Next host is
a proposed x86 Linux VM. No purchases; main-project edit preserved._

## Now
- **Migration preservation, 2026-09-18 (T-028):** existing KiCad project setting edit committed; required harness passed baseline rules. Public GitHub push blocked by automatic approval review pending explicit permission to publish full pending history. See T-028 and migration journal. Engineering gates remain unchanged.
- **Execution plan, 2026-09-14:** Joshua confirmed **home desk only**, **US$250**
  for cloud/development modules/cables/adapters (excluding coupons/equipment),
  and **2–4 hands-on hours/week**. `docs/next-steps.md` defines the staged calendar:
  first Vivado reports this week, target checked digital capture by early October,
  conditional first echo Oct 12–25 after assembled coupons and measurement access.
  Next user inputs: usable x86 SSH host, AMD installer/license access and shipping
  country/postal code. openFPGALoader officially lists Cmod A7-35T plus macOS
  installation; actual local programming remains untested. No lab access assumed.
- **Cloud cost follow-up, 2026-09-14:** `docs/cloud-compute-pricing.md` compares
  4 vCPU/8 GiB, 100 GiB disk and 20 compute hours over 3 days versus one month.
  Linode is about $5.18 for that sprint; Modal's published monthly credit covers
  the modeled usage, subject to actual tool compatibility. Dedalus student email
  is drafted only; its free disk cap, access, architecture and storage billing
  need resolution. No outreach, provisioning, provider selection or spend.
- **Vivado retained, 2026-09-14:** Joshua owns a school DE10-Lite and Raspberry
  Pi, but prefers Vivado and can arrange a VM. D012/Cmod remains binding; D014
  is not adopted and T-027 must not start. Recommended first host: x86-64 Ubuntu
  22.04.5, 8 GB/4 vCPU/160 GB Linode, Vivado 2026.1 BASIC. This Mac/Pi are ARM;
  an ordinary ARM VM does not solve tool support. See `docs/vivado-validation.md`
  for exact handoff/build commands, source provenance and remaining signoff gates.
  No VM, license enrollment, external upload or Vivado run has occurred.
- **T-023 progress, 2026-09-13:** acquisition tap now precedes USB flow control;
  FIFO pointers reset without a running FT clock. Four new actual-top behavioral
  tests pass at 3.072/4.8 MHz with absent/blocked USB, delayed/consecutive
  snapshots, SRAM/UART counters+CRCs and reconnect/reset; all 21 gateware checks
  pass. Mutation restoring the USB-gated tap fails with header-only capture.
  **R3 starvation is repaired in simulation; R4 commanded TX is still open.**
  No Vivado synthesis/timing/CDC or physical proof. T-023 is not done.
- **Purchase/bring-up answer:** `docs/pre-hardware-readiness.md` recommends
  development capability first, rev B coupons after assembly/bench/quote gates,
  and HOLD the legacy main PCB. Cmod is $104 on the current distributor listing
  and still Micro-B; prior USB-C preference is not silently waived. FT232H's
  required EEPROM FIFO setup and a source-audited adapter map are in
  `docs/ft232h-bench-preflight.md`. Current UART needs >=45.55 s/full snapshot;
  the proposed 1 Hz demo is not supported by that default. T-024/T-025 updated.
- Host suite remains 5/5 but idle-EOF and chunk-state defects still reproduce.
  Required KiCad harness passes its existing-baseline rules, not clean-main-board
  rules. Coupon release source/export hashes match 66/66; no KiCad file changed.
  Earlier fast-review evidence predates the RTL repair; its hash guard should
  mark it stale. Use the new readiness brief for current next actions.
- **T-026 done: fast, read-only review.** `./scripts/open_review.sh` now opens
  `build/review/fast.html` immediately without regenerating EDA artifacts. One
  immediate question: what Cmod/FT232H/Vivado access is available? Answers stay
  in chat; Joshua explicitly rejected copying/exporting answers. `--full` keeps
  the visual appendix; `--live` regenerates it and runs gateware. The short brief
  and two diagrams are under `orchestration/review/`. Fresh gateware 17/17 and
  pinned host 5/5 pass while independent starvation/host probes still reproduce
  bugs. No bitstream/physical capture proof. Private Site was registered but
  **not published**: external upload was denied by permission review; do not
  retry unless Joshua explicitly authorizes the payload/destination. Local
  review is complete; optional remote publication is not an engineering gate.
- **T-022 done: R1/R2 repaired, coupon rev B back at CP-BM review.** Full filled-board
  DRC is 0 violations / 0 unconnected / 0 footprint errors on both variants.
  Independent complete TI pin map, 94-pad schematic/PCB parity, negative tests,
  actual Gerber/drill/CSV inspection and deterministic regeneration pass. Read
  `coupons/mic-bakeoff/docs/T-022-release-verification.md` and the updated order
  package. Stock/price refresh, assembly DFM, purchase approval and physical tests
  remain Joshua's gates. Do not order historical rev A artifacts.
- **Product review remains open.** REVIEW-2026-09-05 R3 is repaired in simulation
  on 2026-09-13; R4: no commanded/timestamped TX;
  R5: idle reads become EOF; R6: finite-record DSP is not a live pipeline.
  Gateware 21/21 and host 5/5 PASS. Host probes still reproduce R5/R6.
- **Next work:** T-023 (top, priority 1)
  completes integrated capture; T-024 (mid) completes live host processing;
  T-025 (mid) prepares a concrete first-echo/bench proposal. Coupon design sources
  changed under T-022; no architecture decision was changed or ratified.
- **KiCad safety, 2026-09-06:** no KiCad editor process was running before regeneration.
  Both coupon projects, symbols and footprints changed on disk: reload before
  opening. `sonar-v1-pcb/sonar.kicad_pro` user edit left untouched.
- **MA40S4S:** live Murata section 5.3 specifies a 20 Vpp maximum input; treat it
  as a terminal limit and keep this transducer disabled at 12 V. D013 ratification
  remains Joshua's. A human interpretation is not a substitute for this rating.
- Older milestone details below are retained as history. Claims that the agent
  queue is exhausted or coupons are ready for purchase are superseded above.
- **T-018 historical appendix:** run `./scripts/open_review.sh --full` for the guided CP-B/CP-BM review
  surface. It freshly generates current schematic/PDF renders, main-board and both
  coupon top/bottom 2D + 3D views, analysis/DSP/gateware evidence, persistent review
  notes, and a paste-ready response. `./scripts/open_review.sh --live` also re-runs
  all 17 gateware checks before opening. Generator/checker PASS; main PCB is loudly
  marked legacy and NOT FOR APPROVAL because P3 has not started.
- **Historical 2026-08-26 milestone snapshot (engineering reopened above).** P1/P2/P5
  agent work is landed: T-009/T-021/T-012/T-013 done, T-011 done (live-gate defect found +
  repaired + re-verified), T-016 (now back at review after T-022), T-020 simulator milestone
  done (bitstream waits on Vivado host). Remaining: Joshua's CP-B/CP-BM reviews,
  T-007 purchases/host choice, then T-010 (unblocked by CP-BM) → T-014 → T-015
  (cross-family review) → CP-C. T-005 EDA spike: **done, NO-GO for v1** (host `pcb build` confirmed the boundary) — see `spikes/eda-zener/REPORT.md`. **T-017 deep port done 2026-08-27 (codex/terra-t017):** with network+host, Zener builds — 3 blocks (power_supply, rx_preamp_tile, tx_drive) + 3 ICs (AP63301/OPA4171/DRV8876), `pcb build` ✓ 67 components, netlist node-for-node parity vs KiCad, live BOM; importer still emits empty stubs. **Session 2 (authenticated, same day):** diode account live — BOM coverage survey 28/29 lines hit, 23/29 with symbol+footprint assets, all 10 key ICs fully covered; all 3 ICs swapped from hand-written to registry (LCSC) assets via the search→download→vendor flow (component API is search/download only; CSE quota exhausted, LCSC works); rebuild ✓ 67 components with ZERO net/node netlist deltas; BOM match improved to 79.2%. Verdict **GO-WITH-CONDITIONS for v2, strengthened** (account condition drops, multi-unit softens; toolchain-pin/importer/JLC-table remain); D008 stands. Integrated on `main` through merge `1e2a012` and journal close-out `d33867a`.
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
- **T-016 historical pre-repair package description (superseded by rev B above):** separate SPH and ICS coupon
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
  section zero violations. The orchestrator re-verified the gate and closed
  T-011 (`status: done`).
  **2026-08-26 review repair (codex/sol-t011-fix, REVIEW-2026-08-26 B1/S1/S9):**
  the Cmod VU feed's orphan `+5V` net + stale masking PWR_FLAG are gone -
  J40.24 now reaches the power tree's `5V` net through new R420 (0R 0603,
  populated by default; DNP to isolate for module-USB backfeed). write_xdc()
  preserves the MANUAL APPEND section (regen-twice byte-identical). R411 10k
  pull-up added on FT_SIWU. Netlist: 5V=15 nodes incl. U35.3 buck VIN + U61.3
  boost VIN + R420.2; 5V_CMOD={J40.24,R420.1}; `+5V` absent; ERC /digital/
  zero; pinmap gate PASS 44/44.
- **T-011/T-013 integration landed:** the committed repair includes the
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
  sheets deleted. **2026-08-26 review repair (codex/sol-t011-fix, REVIEW S2):**
  rails.md now records the real v1 strategy (carrier 5V powers the Cmod via VU
  through R420, populated by default; module-USB backfeed bring-up procedure;
  Cmod ~200-400 mA typ allocation added to the 5V budget as an unmeasured
  assumption); the stale self-powered/SJ1-SJ2 text is deleted. `pcb drc` still SIGABRTs in the sandbox (exit 134) — ERC is
  the gate; DRC re-run unsandboxed remains open.
- **KiCad open?** Unknown. **2026-08-26 codex/sol-t020: `20kHz-h-bridge.kicad_sch` text box edited on disk (pio44->pio48 TX_NSLEEP text only) — reload KiCad.** **KiCad files changed on disk 2026-08-26 (sonar.kicad_sch,
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
| T-026 fast human review | **top** coordinator + **cheap** artifacts | **done**; read-only local review, one immediate question, no copy workflow; optional remote upload not authorized |
| T-022 coupon release repair | **mid** | **done**; rev B full DRC 0/0/0 both variants, pin/geometry/export checks pass; T-016 back at human review |
| T-027 DE10-Lite bench port | **top** | **blocked; not selected**; D014 not adopted, Joshua prefers Vivado |
| T-023 commanded echo capture | **top** | **in-progress**, priority 1; snapshot independence repaired/tested, commanded TX/control/timestamp still open; coordinate with T-020 |
| T-024 live host pipeline | **mid** | **ready**; idle/EOF semantics, stateful DSP, bounded capture/replay |
| T-025 first-echo bench plan | **mid** | **ready**; measurable demo, executable acquisition, equipment/access/cost proposal |
| T-002 parts & lifecycle audit | **cheap** | **done**; matrix committed; unlocks T-008 |
| T-007 buy list + Vivado-host options | **cheap** | **review**; Joshua purchase/host choices remain |
| T-006 kicad-cli check harness | **cheap** | **done**; baseline recorded |
| T-009 Pico 2 snapshot firmware | **mid** | **done (host-verified)**; physical integration waits on pins/SDK/board |
| T-021 host software | mid | **done**; physical FT232H/libusb still untested |
| T-020 Vivado gateware | **top** | **in-progress**; `make test` PASS (17/17, Icarus 13.0) incl. review S6/S7/S8 hardening (per-domain reset syncs, functional UNISIM-style models, no-clipped-edge clock TB); bitstream + hardware demo wait on the Vivado host |
| T-008 PDM RX design | **top** | **done**; provisional electrical baseline, not physical MPN release |
| T-016 mic coupon bake-off | mid | **review (CP-BM)**; repaired rev B verified under T-022; human DFM/sourcing/purchase/bench gates remain |
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
- **T-016 human gate:** T-022 resolved the 2026-09-05 electrical hold. Use only
  verified rev B exports; confirm DFM, current sourcing/quotes and purchase
  approval before ordering. Physical bake-off and final MPN release remain open.
- ~~REVIEW-2026-08-26 follow-up (schematic, pre-CP-C): TX_NSLEEP J40.44 vs
  pio48~~ **RESOLVED 2026-08-26 (codex/sol-t020, session 6):** the audit was
  stale. Evidence: `digital.kicad_sch` regenerates content-identical (UUIDs
  only) from current `scripts/gen_digital_sheet.py`, whose PINS maps DIP
  position 48 -> TX_NSLEEP and whose sheet code attaches each net label by
  `pm[str(position)]` - so the sheet's TX_NSLEEP label is on J40.48; the
  ETH_RXD1 label sits 4 rows (10.16 mm) below it at J40.44; pinmap.md:111
  and the XDC agree (pio48/V8). No generator fix needed. The one genuinely
  stale artifact was the TX Drive sheet text box ("pio1/2/44/8 out") on
  `20kHz-h-bridge.kicad_sch` - corrected to "pio1/2/48/8 out".
- **D013 proposed (needs Joshua, CP-B/CP-C):** v1 default TX = piezo horn
  tweeter 20-32 kHz chirps; MA40S4S 40 kHz use gated on Joshua's datasheet
  reading of whether 20 Vpp is a terminal or fundamental limit (terminal =>
  reduced VM setpoint or series element). See decisions/D013, REVIEW S5.
- Vivado synthesis (part of T-020) waits on the Vivado host purchase/decision (T-007
  item 7). The T-020 testbench layer is DONE (17/17, freshly re-run 2026-08-27)
  and also gates the
  `sonar_top` <-> XDC port bijection (`gateware/sim/check_ports.py`, exact 28
  ports/73 bits, TX_EN/TX_PH mapped per `orchestration/tx-limits.md`); the SRAM
  timing constants question is closed by the documented per-phase margin analysis
  in `gateware/sim/README.md` (>=2.1x worst case). Remaining T-020 DoD: batch build
  + utilization/timing/CDC + UNISIM/BRAM proofs + SRAM set_output_delay budgeting
  on the host; hardware FT232H/UART demo; CP-C confirm vs the ISSI PDF.
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
- 2026-09-13 — codex/T-023: USB-independent snapshot and clockless FIFO reset
  repair; 21 gateware checks, 5 host checks, starvation negative control and
  existing-baseline KiCad harness verified. Current purchase/bring-up brief and
  FT232H adapter/EEPROM preflight delivered. No hardware/Vivado or TX-command
  proof. Journal: `2026-09-13-codex-t023-readout-readiness.md`.
- 2026-09-05 — codex/T-019: independent review complete, seven findings and a
  first-echo execution path. Confirmed TI pin mismatch, ran full filled-coupon
  DRC outside sandbox (82/92 violations, zero unconnected, five shorts each),
  reproduced fallback starvation and host faults. Gateware 17/17, host 5/5,
  Pico host/C tests, bake-off selftest and repository harness completed.
  No design fixes or purchases; T-022–T-025 ready. Journal:
  `2026-09-05-codex-t019-independent-review.md`.
- 2026-08-27 — codex/sol-t018: guided visual review done. Added eight-step,
  locally persistent review workflow, 71 actual images, current main/coupon
  schematic and PCB exports, full PDF, review-summary builder, strict page/asset
  checker, and `./scripts/open_review.sh`. Visual QA passed; no design file changed.
  Journal: 2026-08-27-codex-sol-t018-guided-review.md.
- 2026-08-27 — codex/sol-t020 resume audit: confirmed T-017 and T-020 are
  integrated on `main`; re-ran `gateware` `make clean && make test` (17/17 PASS,
  full 512 KiB snapshot bit-exact, RTL/XDC 28 ports/73 bits exact); confirmed the
  T-016 lock with `uv lock --check --offline`. Local host remains ARM64 with no
  Vivado executable or attached Cmod/FTDI/Pico. No design file changed; Joshua's
  pre-existing `sonar-v1-pcb/sonar.kicad_pro` edit remains untouched.
- 2026-08-27 — codex/terra-t017: T-017 done — Zener deep port builds on host
  (67 comps, netlist parity exact, BOM live-priced, voltage checks
  negative-tested); authenticated registry coverage and assets strengthened the
  verdict to GO-WITH-CONDITIONS for v2; importer still broken. Later integrated
  on `main` through `d33867a`. Journal: 2026-08-27-codex-terra-t017.md.
- 2026-08-26 — codex/sol-t020 (session 5): REVIEW-2026-08-26 TX fixes —
  B2 blocker (tx_nco_pwm free-running 46.875 kHz carrier replaced by
  phase-derived duty gating; per-half-cycle duty hard-bounded by
  amplitude/256 +/-1 clock; new tb_tx_duty_bound runs the reviewer's exact
  config + amplitude sweep + chirp endpoints + ramp, 0 violations, old RTL
  fails with 594; envelope re-derived in tx-limits.md), S3 (TX_NSLEEP
  pio44->pio48 doc fix + schematic follow-up flagged), S4 (DRV8876 00=coast,
  11=brake; CP-C truth-table item), S5 (terminal-excursion statement +
  D013 proposed), NIT5 (ft_d driven continuously). `make test` 13/13 PASS.
  Uncommitted on agent/T-020-gateware. Journal addendum 5.
- 2026-08-26 — codex/sol-t011-fix: repaired REVIEW-2026-08-26 B1/S1/S2/S9 in
  scripts/gen_digital_sheet.py + rails.md (regenerated outputs; R420 0R VU feed,
  PWR_FLAG deleted, XDC read-modify-write, FT_SIWU pull-up, Cmod 5V allocation).
  Verification in the T-011/T-012 Logs + journal
  2026-08-26-codex-sol-t011-fix.md. Uncommitted; orchestrator integrates.
- 2026-08-26 — codex/sol-t020 (session 4): finished the agent-doable T-020
  remainder — sonar_top/XDC port reconciliation (bijection gated by new
  gateware/sim/check_ports.py as make-test check 12; TX per tx-limits.md;
  unpinnable scaffolding tied off: POR + btn[1] reset, TX idle/asleep) and the
  SRAM timing-margin analysis (gateware/sim/README.md, worst 2.1x; CP-C
  confirm-vs-ISSI-PDF line in ticket Log). `make test` 12/12 PASS. All
  uncommitted on agent/T-020-gateware. Ticket stays in-progress (Vivado host +
  hardware demo gates). Journal: 2026-08-26-codex-sol-t020-gateware.md addendum 4.
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
- 2026-08-26 — codex/terra-t016-fix: REVIEW-2026-08-26 findings S10/S11/NIT4
  fixed — order quantities reconciled (24 mics/MPN, 12 clock buffers, one
  cross-checked table), C1..C8 changed to 100 nF X7R 0603 (C0G 0603 unbuyable),
  ruff pinned to 0.14.0 + format drift repaired; check_coupons.sh exit 0
  re-verified. Host lock refresh later landed in `7b29747`; fresh
  `uv lock --check --offline` PASS 2026-08-27. See
  journal 2026-08-26-codex-terra-t016-fix.md and the T-016 Log.
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
