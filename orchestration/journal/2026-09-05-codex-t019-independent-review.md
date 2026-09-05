# 2026-09-05 — codex/T-019 independent current-gate review

Joshua asked for an independent repository/product-readiness review. Oriented via
protocol, STATUS, PLAN, CLAUDE, ROADMAP, recent journals and the earlier review.
Claimed new top-tier T-019; claim commit 7bf4b77. Baseline main was 7d2f59d.

## Result

HOLD coupon orders; engineering work is not exhausted. Review and exact evidence:
`orchestration/review/REVIEW-2026-09-05.md`. TI's primary datasheet disproves the
coupon U1 pin map. Both actual boards wire device GND pin 11 to +3V3_MIC.
Full DRC with in-memory plane fill found 82/92 violations, zero unconnected, and
five shorting-item findings per variant (C1–C4 and R1). Custom verifier passes
because it skips same-footprint copper comparisons and no-net pads.

RTL probe proves USB-stall-induced snapshot starvation. TX is permanently tied
off at the hardware top and lacks a TX-to-capture time reference. Host probe
proves temporary empty reads become EOF; decimation is finite-record and cannot
be called on successive live chunks with unchanged behavior. Existing tests pass
despite these integration gaps.

## Verification

Gateware 17/17; host 5/5 with pinned NumPy 2.3.2; Pico host contract/sim and two C
executables exit 0; bake-off analyzer selftest PASS with matplotlib supplied via
uv; Cmod map 44/44 against committed manufacturer snapshot. Full repository
KiCad harness completed outside sandbox (exit 0, violations intentionally
accepted); main ERC 346. Coupon DRC reports in build/t019-*-filled-drc.rpt.
No physical acquisition, Pico SDK build, Vivado synthesis or measured acoustics.

## Changes and next action

Only review evidence, ticket/status/journal and order/review hold documentation
changed. T-016 moved to blocked on new T-022. T-022–T-025 are ready with concrete
definitions of done. Start T-022 (mid): complete U1 manufacturer-pin audit, repair
physical shorts and all release checks. T-023 (top) owns commanded/timestamped TX
and independent fallback, coordinated with T-020; T-024 (mid) owns live host; T-025
(mid) prepares the executable first-echo bench and equipment/access proposal.
Keep D013 proposed and MA40S4S disabled at 12 V. Joshua retains purchases,
requirements/decision ratification and physical-bench operation. Do not reopen EDA
or architecture exploration as a substitute for one end-to-end measured echo.

The existing guided review HTML is historical and was not regenerated; its source
review plan and order package now warn of the hold. No KiCad source was saved;
Joshua's original sonar.kicad_pro edit remains untouched. No remote was pushed.
