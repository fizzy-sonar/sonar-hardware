# 2026-08-26 — codex/terra-t016-fix: T-016 coupon-package review fixes (S10/S11/NIT4)

Scope: the three T-016 findings in `orchestration/review/REVIEW-2026-08-26.md`.
No commits/merges/pushes per instructions; no orders placed (CP-BM stays Joshua's).

## S10 — order quantities were not self-consistent

Review was right: 16 mics/MPN and 8 buffers could not fully populate 5+5 boards
(needs 20/MPN and 10). Reconciled in `coupons/mic-bakeoff/docs/order-package.md`:

- Purchase: **24 mics per MPN** (SPH0641LU4H-1, ICS-41352), **12 CDCLVC1112PWR**.
- Basis: JLC 5-board min/variant fully assembled = 20 mics/MPN + 10 buffers;
  +20% assembly-loss/rework spares. Estimator floor (12 valid units/MPN = 3
  coupons x 4 sites) is met by any 3 of 5 coupons; 2 spare boards absorb
  whole-coupon failures.
- Added one reconciliation table in order-package.md cross-checking every
  number; updated the header margin note and pre-order checklist step 5.

## S11 — 100 nF C0G/NP0 0603 is not a buyable part

Chose **100 nF X7R 0603** (lower DFM risk than C0G 1206: zero layout change,
footprint `C_0603_T016` unchanged). Rationale: digital PDM mic supply bypass on
a 3.3 V rail; X7R DC-bias droop acceptable; mic PSRR + 10 uF/1 uF bulk cover it.
Updated `generate_coupon.py` (values + PCB fab text), regenerated both coupons
(sch/pcb now say `100nF X7R 0603`, BOM export confirms), plus README.md,
order-package.md (BOM line + new pre-order checklist step 4 flagging the
change), and runbook.md §0 note. No residual "C0G" anywhere in the package.

## NIT4 — check_coupons.sh exit 1 under ruff 0.14.0

Root cause: ruff was never pinned; T-016's recorded "exit 0" came from an older
unpinned system ruff (exact version unrecoverable). Fix: pinned `ruff==0.14.0`
in `pyproject.toml` `[project.optional-dependencies] dev`, reformatted the 4
drifted files with exactly that version, and made `check_coupons.sh` fail loudly
on ruff version mismatch (with a pointer to the pin) instead of emitting a
misleading format diff. **Documented choice: pin (not version-tolerant check).**

Sandbox limitation: offline — `uv lock` could not refresh `uv.lock` for the new
dev extra. **Host must run `uv lock` once, then `uv sync --extra dev`.** Until
then the pyproject pin is the source of truth and check_coupons.sh asserts it.

## Verification

`./coupons/mic-bakeoff/check_coupons.sh` **exit 0** (full real log:
`build/t016/check-run-2026-08-26.log`). Tail:

```
== lint
All checks passed!
4 files already formatted
SUMMARY: coupon package checks passed
```

ERC 4/4 waivers per variant, geometric verify all PASS (0 unconnected; gaps
0.145–0.150 mm; 4x 0.50 mm NPTH; J1 map; pad-1 quadrants), fab export clean,
analysis selftest all branches, normative estimator sha256 unchanged.
"regen produced a diff" in this run is the S11 change itself; quiet after commit.

## Next

Joshua: CP-BM pre-order checklist in `docs/order-package.md` (now 6 steps —
incl. X7R BOM-pick confirmation and reconciled quantities); run `uv lock` on
the host; then approve/place/pay. T-016 stays `review`.
