# STATUS — Sonar v1

_Last updated: 2026-08-26 by codex/terra-t016 — T-016 coupon/order/test package delivered, ticket at `review` (CP-BM human gate)._

## Now
- **Phases open for agent work: P1, P2, and P5.** T-002/T-008 are done and CP-B
  still reviews the analysis/bake-off thresholds. T-016 is ready for an agent to
  prepare the coupon/order/test package. Only T-010 is blocked on its physical
  result; T-011/T-012/T-013 and P5 may proceed.
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
- **KiCad open?** Unknown — check before hand-editing `.kicad_sch` (README rules).
  2026-08-26 terra-t016: new KiCad files added under `coupons/mic-bakeoff/` on
  branch agent/T-016-mic-bakeoff (no existing project files touched); reload
  before opening if KiCad had the repo open.

## Work queue — launch ready tickets on the tier shown (routing table in README.md)

| Ticket | Tier | Notes |
|---|---|---|
| T-002 parts & lifecycle audit | **cheap** | **done**; matrix committed; unlocks T-008 |
| T-007 buy list + Vivado-host options | **cheap** | **review**; Joshua purchase/host choices remain |
| T-006 kicad-cli check harness | **cheap** | **done**; baseline recorded |
| T-009 Pico 2 snapshot firmware | **mid** | **done (host-verified)**; physical integration waits on pins/SDK/board |
| T-021 host software | mid | **done**; physical FT232H/libusb still untested |
| T-020 Vivado gateware | **top** | **in-progress**; `gateware/` simulator milestone done, `make test` PASS (9/9, Icarus 13.0); bitstream waits on Vivado host + T-011 XDC |
| T-008 PDM RX design | **top** | **done**; provisional electrical baseline, not physical MPN release |
| T-016 mic coupon bake-off | mid | **review**; agent package delivered + verified; Joshua's CP-BM checklist in `coupons/mic-bakeoff/docs/order-package.md` |
| T-010 array sheet | mid | **blocked on T-016**; no provisional footprint/BOM freeze |
| T-011 digital sheet | **top** | **ready**; common pin map/returned clock can proceed |
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
  item 7). The T-020 testbench layer is DONE (2026-08-26): dual-rate sampler/packer/
  FIFO/FT245/UART-snapshot/TX-chirp sims all pass; `build_bitstream.tcl` refuses an
  unpinned bitstream until T-011 publishes `constraints/sonar_cmod_a7.xdc`. Remaining
  T-020 DoD: batch build + utilization/timing/CDC + UNISIM/BRAM proofs on the host,
  real XDC from T-011, hardware FT232H/UART demo.
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
- 2026-08-26 — codex/terra-t016: T-016 coupon bake-off package (designs,
  analysis, runbook, order package) delivered and verified; ticket → review;
  CP-BM gate is Joshua's.
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
