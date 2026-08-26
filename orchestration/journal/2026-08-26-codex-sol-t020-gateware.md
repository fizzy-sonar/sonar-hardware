# 2026-08-26 — codex/sol-t020: simulator-first Artix-7 gateware

## What happened

- Recovered the previously uncommitted `gateware/` draft on
  `agent/T-020-gateware` and audited every RTL, testbench, Tcl, format, and
  constraint file against D006, D012, and `docs/pdm-capture-contract.md`.
- Repaired the capture lifecycle. Reset release is now quiet; synchronized
  `capture_enable` starts exactly one independently latched 32-byte `SNR1` header,
  followed by raw frames. A sufficiently long low interval resets both FIFO
  domains/packer/header before the next incrementing capture ID.
- Made overflow a tested transaction contract: FIFO full accepts no later frame,
  latches visible `capture_overflow`/`capture_stopped`, and drains exactly the
  accepted prefix without an in-band gap or fake resynchronization. Status remains
  sticky through capture-low and clears only at global reset/new capture.
- Registered the FT232H write data and `WR#` path from `FT_CLK`. The output skid
  byte keeps one-byte-per-clock burst capability while retirement still requires
  sampled `TXE#` and registered `WR#` both low. This leaves a full FT clock of
  setup instead of relying on an unsafe combinational TXE-to-WR path.
- Kept the canonical 24-channel map: data line `i` rising -> CH`2*i`, following
  falling -> CH`2*i+1`; payload is three little-endian bytes per frame.
- Tightened exact 50 ms standard-clock, clock-off, 10 ms mode-settle checks and
  added a bounded signed fixed-point NCO increment ramp so the TX simulator block
  is chirp-capable and stops safely on an envelope crossing.
- Added compile-only 7-series primitive stubs so portable CI elaborates the
  vendor IDDR/MMCM/ODDR branches and complete top wiring without pretending those
  stubs prove Xilinx primitive behavior.

## Verification

`cd gateware && make test` passes with Icarus Verilog 13.0:

- both 3.072 and 4.8 MHz sampler variants, 80 frames each, correct
  73.728/115.2 Mb/s raw rates;
- FIFO/packer/FT245 order and end-to-end `SNR1` plus 100 exact frames through long
  and pseudo-random backpressure;
- forced overflow drains exactly eight accepted frames, never resumes that
  capture, retains sticky status, and restarts with capture ID 1;
- complete two-capture header fields/hold behavior, UART snapshot CRCs, exact
  startup durations/clock arithmetic, bounded chirp safety, and Xilinx/top
  compile-only elaboration.

`git diff --check` passes. The user's KiCad file was untouched.

## Open gates / exact next step

T-020 is not done. T-011 must first publish the audited Cmod/FT232H pin map and
`gateware/constraints/sonar_cmod_a7.xdc`. On an x86 host with Vivado, run the two
documented batch Tcl commands, inspect UNISIM edge polarity, BRAM inference,
generated clocks, FT_CLK/PDM input-output delays, CDC, utilization, and timing,
then append the real reports to the ticket. Hardware must separately demonstrate
FT232H and UART operation. The full 512 KiB external-SRAM snapshot controller and
real control-plane integration remain; T-013 must release TX waveform limits.

## Addendum — session 2 (recovery, commit, re-verify)

- Prior session was killed before committing; this session found all work
  uncommitted, audited it against the ticket/journal, and committed it in four
  logical commits: `feat` RTL, `test` benches+Makefile, `docs` README/stream
  format, `build` Tcl/placeholder XDC/`.gitignore`.
- Re-ran verification from clean: `cd gateware && make clean && make test` —
  all nine steps PASS under Icarus Verilog 13.0 (real PASS lines pasted into
  the T-020 Log). `git diff --check` clean. `scripts/check.sh` not run: it is
  KiCad-only and no KiCad file changed on this branch.
- **Environment problem:** the sandbox grants write only to the worktree; the
  shared git dir (`/Users/joshuahimmens/code/sonar-hardware/.git`) is
  read-only and escalation is disabled, so `git commit` in the worktree fails
  with "Operation not permitted". Workaround: commits were authored in a
  scratch git dir (`GIT_DIR=.git-scratch`, object alternates into the real
  store) and exported as a bundle at the worktree root,
  `t020-gateware-commits.bundle`. The orchestrator lands them with:

      cd /Users/joshuahimmens/code/sonar-hardware
      git fetch /private/tmp/sonar-t020/t020-gateware-commits.bundle \
        agent/T-020-gateware:agent/T-020-gateware

  (`git bundle verify` first if desired; prerequisite efa7802 is on main.)
  `.git-scratch/` in the worktree is scratch and should be deleted after the
  fetch; the worktree files themselves match the committed trees exactly.
- T-020 stays `in-progress`: Vivado host (T-007 item 7) and T-011's pin map /
  real XDC remain the gates, plus UNISIM/BRAM proofs and hardware demos. See
  the ticket Log for the exact remaining DoD items.
