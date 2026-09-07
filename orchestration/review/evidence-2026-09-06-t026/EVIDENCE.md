# T-026 artifact subtask A — 2026-09-06

This is a read-only evidence rerun. It does not claim Vivado, board, USB,
acoustic, or timing sign-off. Generated logs in this directory are the raw
outputs of the commands below.

## Commands and results

### Gateware simulation/elaboration

Command:

```text
make -C gateware test
```

Result: exit 0; 17 `PASS` lines. The suite covered sampler/packer at 3.072 and
4.8 MHz (including Xilinx primitive stubs), async FIFO/FT245 backpressure,
stream core under TXE# stalls, overflow-stop/restart, SNR1 header, UART
snapshot, startup/clock/TX duty bounds, reset/debounce, PDM clock stubs,
small and full 512 KiB SRAM snapshot, top-level Xilinx-stub elaboration, and
the 28-port/73-bit top/XDC bijection. See `gateware-make-test.log` and
`gateware-make-test-exit.txt`.

This proves the checked-in RTL behavior under Icarus simulations and top-level
stub elaboration only. It does not prove Vivado synthesis/implementation,
placed-and-routed timing, Cmod pins, FT232H signaling, SRAM electrical timing,
or a physical capture.

### Host unit tests

The first offline `uv run --offline` invocation using the default user cache
was blocked by sandbox permissions (exit 2; see `host-unittest.log`). A
repo-local cache was then used with the project's pinned environment:

```text
PYTHONPATH=host python3 -m unittest discover -s tests -q
```

The reproducible command was:

```text
PYTHONPATH=host UV_CACHE_DIR=build/uv-cache uv run --offline python -m unittest discover -s tests -q
```

Result: exit 0, `Ran 5 tests ... OK`, using Python 3.14.2 and NumPy 2.3.2.
See `host-unittest-pinned.log`, `host-unittest-pinned-exit.txt`, and
`uv-pinned-version.log`.

### Existing host diagnostic probe

```text
PYTHONPATH=host UV_CACHE_DIR=build/uv-cache uv run --offline python orchestration/review/evidence-2026-09-05/probe_host.py
```

Result: exit 0. It reproduced (a) a transient empty read being treated as EOF
(`stream ended after 0 frames; requested 1`) and (b) whole-buffer versus
independently-decimated chunks differing by max `0.233102`. This is diagnostic
evidence of the reviewed host semantics, not a proposed fix or live USB test.
See `host-probe-pinned.log` and `host-probe-pinned-exit.txt`.

### Existing RTL starvation probe

The first literal compile recipe omitted `pdm_ddr_sampler.sv` and failed with
an unknown-module error; that raw attempt is in `rtl-probe-compile.log` and
`rtl-probe-exit.txt`. The corrected compile included that transitive RTL
dependency:

```text
iverilog -g2012 -Wall -s tb_fallback_starvation -o \
  build/review-probes/tb_fallback_starvation \
  orchestration/review/evidence-2026-09-05/tb_fallback_starvation.sv \
  gateware/rtl/reset_sync.sv gateware/rtl/pdm_ddr_sampler.sv \
  gateware/rtl/async_fifo.sv gateware/rtl/frame_byte_packer.sv \
  gateware/rtl/stream_header.sv gateware/rtl/ft245_sync_tx.sv \
  gateware/rtl/pdm_stream_core.sv
vvp build/review-probes/tb_fallback_starvation
```

Result: compile and run exit 0; `REPRODUCED: stalled USB stops snapshot tap;
taps before=9 after=9`. This is a small FIFO behavioral reproduction of the
starvation path; it is not a proof of the production FIFO's exact time-to-stop
or a hardware USB measurement. See `rtl-probe-compile-fixed.log`,
`rtl-probe-run-fixed.log`, and `rtl-probe-exit-fixed.txt`.

The generated executable is kept outside the evidence directory at
`build/review-probes/tb_fallback_starvation`; it is not a source artifact.

## Direct source inventory and review anchors

- `gateware/rtl/sonar_top.sv:11-17` documents the control-plane scaffolding
  as tied off; `:216-232` instantiates TX with `.start(1'b0)`, zero phase,
  zero amplitude, and zero burst cycles, then maps the resulting idle outputs
  to `tx_en`, `tx_ph`, and `tx_nsleep`. This is direct source evidence that a
  commanded TX/echo path is not present at the hardware top; it is not a claim
  about a physical board.
- `gateware/rtl/sonar_top.sv:190-205` couples the SRAM snapshot to the
  accepted `pdm_stream_core` tap (`tap_frame_data`/`tap_frame_valid`) through
  `stream_clk=pdm_clk_fb` and `stream_reset=reset_pdm`. The comment at
  `:190-192` explicitly says the snapshot sees only accepted primary-stream
  frames; this coupling is also exercised by the starvation probe.
- `gateware/rtl/sonar_top.sv:104-120` and `:172-182` show separate reset
  synchronizers for PDM, FT, and SRAM domains. `reset_sync.sv:19-26` asserts
  asynchronously but releases only on destination-clock edges. Therefore, if
  `ft_clkout` is absent, `reset_ft` cannot synchronously release; this is a
  directly observable clock-availability dependency, not a timing sign-off.
- `gateware/constraints/sonar_cmod_a7.xdc:42-62` constrains the returned PDM
  clock and FT `CLKOUT` as primary clocks. At `:85-87`, the file says PDM
  `set_input_delay` constraints belong in a timing XDC but none are present in
  this file. At `:97-99`, SRAM board-level `set_output_delay`/setup-hold
  budgeting is explicitly host-gated; no Vivado timing report was produced in
  this run. These are open proof items, not failed hardware.

`SHA256SUMS` records SHA-256 hashes for the RTL, constraints, host modules,
probe sources, and `pyproject.toml` used by this evidence run, so a later
review can detect stale evidence after source changes.

## Scope boundary

No Vivado executable, implementation report, placed-and-routed timing, Cmod,
FT232H, SRAM, Pico, microphone, or acoustic measurement was available or
performed. The pre-existing user edit remains preserved: `git status` still
reports `M sonar-v1-pcb/sonar.kicad_pro`; no design source was edited.
