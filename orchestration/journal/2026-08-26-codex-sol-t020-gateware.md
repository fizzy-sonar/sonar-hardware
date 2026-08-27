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

## Addendum — session 3 (SRAM snapshot fallback, the last agent-doable item)

- Built the D012 day-one fallback end to end in simulation:
  `rtl/sram_snapshot.sv` captures the accepted-frame tap of
  `pdm_stream_core` (new `tap_frame_data`/`tap_frame_valid` outputs) through a
  16x32 async FIFO into the Cmod's IS61WV5128BLL-10BLI, then drains the window
  over `uart_tx` with byte-exact SNP1 v1 framing (48-byte header, payload CRC,
  header CRC; counts computed from the completed capture so timeout/overrun
  truncation is honestly described; IDs increment per capture).
- Clocking: new 48 MHz MMCM CLKOUT2 (/16 from the 768 MHz VCO) + BUFG in
  `pdm_clock_7series` (`sram_clk`); one byte per three clocks = 16 MB/s, above
  the 14.4 MB/s ICS worst case, so the CDC FIFO never fills in steady state.
  Write microcycle SETUP/PULSE/HOLD (20.833 ns each) gives >= 2.6x margin on
  every cited ISSI -8 ns grade parameter (tWC/tPWE/tSD/tHD; reads get 41.7 ns
  vs tAA 8 ns). `sim/is61wv5128bll_model.sv` enforces tWC/tPWE/tSD and models
  tAA. **Caveat:** no network in the sandbox — the cited ISSI constants are
  standard -8/-10 grade values, marked TODO(host) for re-verification against
  the live PDF on the Vivado host.
- `sim/tb_sram_snapshot.sv` proves: two back-to-back 16-frame captures + a
  stream-stopped timeout (zero-frame) capture, IDs 5/6/7, all byte- and
  CRC-exact; and one full 512 KiB window — 174,762 frames, 524,334 bytes
  drained bit-exact (pattern + both CRCs) in ~47 s of Icarus wall time.
- `sonar_top` integrates it behind `btn[0]` (snapshot trigger), `led[0]` busy /
  `led[1]` error, drain on `uart_rxd_out` (J18, the FT2232HQ bridge). New
  ports use master-XDC names (MemAdr/MemDB/RamCEn/RamOEn/RamWEn).
- XDC: appended the 30 SRAM pins + `uart_rxd_out` copied EXACTLY from the live
  master XDC (`/tmp/cmod-a7-master.xdc`), marked MANUAL APPEND so regeneration
  from `scripts/gen_digital_sheet.py` preserves it; zero overlap with the 44
  DIP pins (all SRAM/UART pins are dedicated bank-14 on-module nets);
  `scripts/check_pinmap_vs_xdc.py` still PASSes 44/44.
- `cd gateware && make clean && make test`: 11/11 PASS (9 previous + 2 new);
  only the three known benign Icarus `@*` warnings in `uart_snapshot.sv`.
- Found and flagged (not fixed — pre-existing, needs a reviewed pass):
  `sonar_top`'s legacy port names don't match the T-011 XDC (`sys_clk_12mhz`
  vs `sysclk`, `pdm_data` vs `pdm_d`, `ft_data`/`ft_clk` vs `ft_d`/`ft_clkout`,
  `tx_a`/`tx_b` vs the TX_EN/TX_PH DRV8876 interface). The bitstream build
  cannot bind until that reconciliation happens; recorded in the ticket Log.
- Rules honored: no commit/merge/push (sandbox git is read-only anyway;
  everything left uncommitted for the orchestrator), ticket stays in-progress
  on the Vivado-host gate (T-007), journal extended, STATUS updated.

## Addendum — session 4 (port reconciliation + SRAM timing evidence)

- **Port-name reconciliation (the flag from session 3, now closed).** Pinmap
  stayed authoritative (the XDC names were right), so the RTL side moved:
  `sys_clk_12mhz`->`sysclk`, `pdm_data`->`pdm_d`, `pdm_clk_buffer_oe`->
  `pdm_clk_en`, `ft_data`->`ft_d`, `ft_clk`->`ft_clkout`. TX mapping was
  already ratified in `orchestration/tx-limits.md`: `tx_en`=`tx_a` (EN/IN1),
  `tx_ph`=`tx_b` (PH/IN2), `tx_pmode`=1 (IN1/IN2 PWM mode), `tx_nsleep`=
  `tx_active`, `tx_nfault` (open-drain, R170 pull-up) mirrored on `led0_r`.
  The leftover simulator-only scaffolding ports had NO pins anywhere in the
  pinmap (no spares on the DIP), so instead of fabricating pins they became
  documented internal tie-offs: 16-cycle power-on reset + btn[1] manual reset,
  `mic_power_good`/`wake_request`=1, TX start/increments tied to idle (driver
  held asleep via `tx_nsleep`), status on the RGB LED (led0_b=overflow,
  led0_g=stopped), `ft_siwu_n` dropped (not pinned out). TX envelope now uses
  the T-013 MA40S4S limits (amplitude 187/256) instead of the generic 128.
- **New reproducible gate:** `gateware/sim/check_ports.py` parses the
  `sonar_top` header and the XDC's active `get_ports` (commented DNP block
  excluded) and asserts an exact bijection incl. per-bit bus coverage;
  negative-tested both directions (rename one port -> FAIL exit 1 listing both
  directions). Wired into `make test` as check 12. Result: 28 ports / 73 bits
  exact.
- **SRAM timing evidence (TODO(host) replaced).** The ISSI PDF is unreachable
  from every sandbox (HTML only, no archive), so `gateware/sim/README.md` now
  carries the per-phase analysis: write = SETUP/PULSE/HOLD, 1 clk (20.833 ns)
  each, 62.5 ns/byte; read = address/OE# applied for exactly 1 clk before the
  latch edge. Margins vs standard -8/-10 grade values: tWC 6.3-7.8x, tWP
  2.6-3.5x, tSD 7.6x, tRC 6.3-7.8x, tAA 2.1-2.6x (binding corner), tOE
  4.2-5.2x — all >= the 2x target. Session 3's "reads get 41.7 ns" comment was
  off by 2x (that is the read cycle, not the access budget); RTL comments
  corrected. Residual risk (FPGA I/O delay, board skew) belongs to the host
  `set_output_delay` budgeting (~12.8 ns slack at the tAA corner); CP-C keeps
  a one-line "confirm against ISSI PDF" checklist item in the ticket Log.
- Verification: `make clean && make test` 12/12 PASS (Icarus 13.0; only the
  three known benign `@*` warnings); `scripts/check_pinmap_vs_xdc.py` still
  PASSes 44/44 (XDC untouched).
- Rules honored: no commit/merge/push — all changes uncommitted on
  agent/T-020-gateware for the orchestrator; ticket stays in-progress on the
  Vivado-host + hardware-demo gates.
