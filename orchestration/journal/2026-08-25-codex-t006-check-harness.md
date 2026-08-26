# 2026-08-25 — codex/luna-t006 — T-006

Implemented `scripts/check.sh` and `scripts/README.md`. Outputs are deterministic
and ignored under `build/`; no design files were changed. The harness distinguishes
missing kicad-cli (exit 2) from ERC/DRC baseline violations (reports plus exit 0).
KiCad 10 was found at the standard macOS app path. ERC baselines were measured;
headless DRC crashed with exit 134, and the repaired harness now returns exit 1
for those tool failures. The harness now sets writable repo-local
`build/xdg-cache`; the no-writable-cache error is gone, but DRC still aborts 134
with Fontconfig configuration warnings. Joshua’s two approved unsandboxed runs
returned exit 0 with identical summaries: ERC and DRC returned baseline code 5,
exports returned 0. DRC reports measured sonar 175 violations, 499 unconnected
pads, 0 footprint errors; rx_amp_sim 1/0/0; txrx_dev 1/0/0.
