# 2026-08-26 — codex/terra-t009 — T-009 close-out / independent re-verification

## What this session was

Resume of `agent/T-009-pico-snapshot-fw` after the previous session
(`codex/t009-final-repair`) was killed at its token budget post-repair. The
worktree was clean at tip 49afac0; ticket frontmatter already read
`status: done` and STATUS.md already reflected the repair. I assessed the
existing work against the ticket DoD/Verification, found it complete, made **no
code changes**, and re-ran the entire host verification suite myself rather than
trusting the prior log entries.

## Verification I ran (all from `firmware/pico-snapshot/`, actual output in the
## T-009 ticket Log entry dated 2026-08-26 codex/terra-t009)

- Python source-contract test and sim test: both exit 0.
- Both C test binaries compiled `-Wall -Wextra -Werror` warning-clean, exit 0
  (divider math, all 24 DDR channel positions, SNP1 schema/CRC, CDC
  backpressure/partial-write/disconnect).
- `host/simulate.py`: 49,152 frames / 147,456 payload bytes synthetic 28 kHz PDM;
  tone/off-tone ratio 287.3 dB; wrote `build/synthetic_spectrogram.pgm`.
- `host/receiver.py`: `valid SNP1 capture=7 frames=49152 clock=3072000 Hz`;
  `cmp` of synthetic vs validated output: byte-identical.
- `ruff check` all passed; `git diff --check` clean.

## State of the ticket

DoD met: firmware + receiver in `firmware/pico-snapshot/`; synthetic-Pattern
loopback is bit-exact; capture → decimation → spectrogram of a known tone
demonstrated in sim. Throughput math (5.333 ms/48 KiB window, 224 KiB SRAM of
520 KiB, ≥40.4 ms Full-Speed drain) is logged in README and the ticket Log.
Remaining work is physical only: `PICO_SDK_PATH` build, PIO/DMA/USB/mic
validation — gated on T-007 purchases; board pins are T-011's release.

## Boundaries

No main-branch merge, no push, no KiCad edits, no purchases. Joshua's dirty
`sonar-v1-pcb/sonar.kicad_pro` untouched. CMake correctly stops with the repo's
explicit missing-SDK error in this environment.

## Next step for the orchestrator

Integrate `agent/T-009-pico-snapshot-fw` (tip: this session's close-out commit)
into main. Nothing blocks that merge; T-021 may now adopt or amend the proposed
SNP1 framing (`firmware/pico-snapshot/README.md`).
