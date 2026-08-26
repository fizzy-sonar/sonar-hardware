# 2026-08-26 — codex/terra-t016: T-016 mic coupon bake-off package (→ review)

## Session

- Branch `agent/T-016-mic-bakeoff`, worktree quirk: the sandbox could not write
  the main checkout's `.git/worktrees` dir, so work happened in a `git clone
  --shared` at `/private/tmp/sonar-t016-git` (objects shared with the main repo;
  branch commits are fetchable from there).
- No network in sandbox (DNS fails). Land patterns were instead derived from
  **local primary datasheet PDFs** left in `/private/tmp` by earlier sessions
  (SPH0641LU4H-1.pdf Knowles Rev B; ICS-41352.pdf DS-000048 Rev 1.0), rendered
  with pdftoppm and read dimensionally. Distributor re-check was impossible:
  dated 2026-08-25 evidence carried forward with an explicit flag.

## Delivered (all on the branch)

- `analysis/pdm_bakeoff.py` — exact normative hierarchical estimator
  (byte-identity of the ticket/docs block asserted, sha256 7408e0ae…),
  every quantitative gate, the five-branch selection rule, T-001 link gate
  wired through `link_budget.py` (reproduces 27.09 dB / 20.18 m reference), and
  a synthetic selftest exercising every threshold and branch.
- `coupons/mic-bakeoff/` — two separate coupon designs (no shared/dual
  footprint): 4 mics on one CDCLVC1112PWR output (worst four-load branch),
  SELECT-paired data with 0R isolation, returned clock, current-break jumper,
  0.50 mm NPTH ports, 4-layer 1.6 mm production-intent stack-up. Everything is
  emitted by `generate_coupon.py` (deterministic uuids; regen is a no-op diff).
- Docs: runbook, fixture drawing + uncertainty template, raw-data schema,
  capture config, order package, sourcing evidence. `check_coupons.sh` is the
  one-command verifier.

## Findings / evidence boundaries

- SPH land: pads 0.725×0.522, columns ±0.8375, rows +1.513/+2.335 from port,
  ring Ø1.625/Ø1.025, port Ø0.325±0.05 (sheet 9/10). ICS land: pads
  0.522×0.725 at (1.252/2.074, ±0.8375), ring Ø1.625/Ø1.025, port Ø0.375
  (Fig. 3 orientation + Fig. 16/18 dims). The patterns are genuinely different.
- **CDCLVC1112PWR pin map is UNVERIFIED** (TI datasheet offline). It lives in
  one table in the generator; pre-order checklist item 1.
- **`kicad-cli pcb drc` SIGABRTs in this sandbox on ANY board** (verified on
  known-good repo boards; T-006's harness needed approved unsandboxed runs).
  Substitution: pcbnew zone-fill + connectivity (0 unconnected both variants)
  plus a static copper-clearance audit (min observed 0.145 mm ≥ 0.127 target).
  Joshua: re-run DRC unsandboxed before ordering.
- KiCad 10 gotchas hit (for future generators): symbol-lib y axis is inverted
  vs schematic y; embedded `lib_symbols` need the `lib:` nickname prefix;
  `(fill yes …)` zone syntax is stale (v10: `(fill (thermal_gap …) …)`);
  kicad-cli pcb commands need a sibling `.kicad_pro` and a writable HOME.
- ERC residue is 4 reviewed waivers per variant (2× pin_to_pin on the intended
  SELECT-paired DATA merge, 2× power_pin_not_driven).

## Verification

`./coupons/mic-bakeoff/check_coupons.sh` exit 0 — deterministic regen, ERC
waivers-only, verify_coupon.py all-pass, fab export (gerbers/drill/pos with
zones filled), analysis selftest (all branches + T-001 wiring), ruff, and
`git diff --check`. Full output in `build/t016/check-final.log` and the T-016
ticket Log.

## Next steps

1. Joshua: CP-BM — pre-order checklist (`coupons/mic-bakeoff/docs/order-package.md`),
   then approve/place/pay, bench per runbook, ratify the MPN release record.
2. Agents after T-016 closes: T-010 instantiates only the released MPN/footprint.
3. No KiCad-main-project files were edited; new files live under coupons/ only.
   STATUS.md notes files changed on disk.
