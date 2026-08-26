# 2026-08-25 — codex/luna-t006 — T-006

Implemented `scripts/check.sh` and `scripts/README.md`. Outputs are deterministic
and ignored under `build/`; no design files were changed. The harness distinguishes
missing kicad-cli (exit 2) from ERC/DRC baseline violations (reports plus exit 0).
The sandbox lacks the host KiCad binary, so both verification runs recorded the
same missing-tool failure rather than inventing design error counts.
