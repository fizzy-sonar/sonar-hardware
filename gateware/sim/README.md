# Gateware testbench notes (T-020)

## Port bijection gate

`check_ports.py` (wired into `make test`, 12th check) asserts an exact
bijection between the `sonar_top` port list and the active `get_ports` names
of `constraints/sonar_cmod_a7.xdc` (commented DNP RMII block excluded),
including per-bit bus coverage. Port names are the authoritative net names of
`orchestration/pinmap.md`. Current status: 28 ports / 73 bits exact.

## SRAM timing-margin analysis (IS61WV5128BLL-10BLI, snapshot fallback)

The on-module 512K x 8 async SRAM is driven by `rtl/sram_snapshot.sv` on the
MMCM-derived 48 MHz clock (tCLK = 20.833 ns). The ISSI PDF is unreachable from
the offline sandboxes (ISSI serves HTML only; no archived copy), so the model
constants use the standard industry -8/-10 async-SRAM grade values that the
IS61/64WV5128Axx/Bxx family shares. The analysis below shows the controller is
not marginal against *any* plausible grade, which is why this is a documented
margin argument plus a CP-C confirm item rather than a blocker.

### What the controller actually generates

Write byte (S_WRITE, one byte per 3 clocks = 62.5 ns, 16 MB/s):

| Phase  | Clocks | ns      | Pin activity |
|--------|--------|---------|--------------|
| SETUP  | 1      | 20.833  | address + data driven, CE# low, WE# high |
| PULSE  | 1      | 20.833  | WE# low (the write pulse) |
| HOLD   | 1      | 20.833  | WE# high, address + data still driven |
| **cycle** | **3** | **62.5** | back-to-back bytes repeat SETUP/PULSE/HOLD |

Read byte (S_PREAD, address/control applied at one clock edge, data latched at
the next):

| Phase    | Clocks | ns     | Pin activity |
|----------|--------|--------|--------------|
| APPLY    | 1      | 20.833 | address driven, CE#/OE# low, WE# high |
| LATCH    | 1      | 20.833 | data sampled at the edge ending this phase |
| **cycle** | **>=3** | **>=62.5** | S_PSEND between reads; UART-bound to ~8.7 us/byte in practice |

### Margin vs standard -8/-10 grade values

| Parameter | Datasheet (-8 / -10 grade) | Controller provides | Margin (-8) | Margin (-10) |
|-----------|---------------------------|---------------------|-------------|--------------|
| tWC write cycle | >= 8 / 10 ns | 62.5 ns | 7.8x | 6.3x |
| tWP (tPWE) WE# pulse | >= 6 / 8 ns | 20.833 ns | 3.5x | **2.6x** |
| tSD data setup to write end | >= 5.5 ns | 41.667 ns (SETUP+PULSE) | 7.6x | 7.6x |
| tHD data hold from write end | >= 0 ns | 20.833 ns (HOLD) | n/a | n/a |
| tRC read cycle | >= 8 / 10 ns | >= 62.5 ns | 7.8x | 6.3x |
| tAA address access | <= 8 / 10 ns | 20.833 ns budgeted | **2.6x** | **2.1x** |
| tOE (tDOE) OE# access | <= 4 / 5 ns | 20.833 ns budgeted | 5.2x | 4.2x |

Worst case anywhere in the table: **2.1x** (tAA against a hypothetical -10 ns
grade); against the actual on-module -10BLI part and the Digilent-rated 8 ns
access at 3.3 V, >= 2.6x everywhere. This meets the >= 2x margin target before
any board-level budgeting. FPGA output-delay/input-delay skew, trace
mismatch, and I/O-standard slew are NOT included here; they are the
`set_output_delay`/board-skew budgeting step on the Vivado host (ticket Log
item), which has ~12.8 ns of slack to absorb at the binding tAA corner.

`sim/is61wv5128bll_model.sv` enforces tWC/tPWE/tSD (and CE#-ended writes) in
simulation and models tAA = 8 ns as an output delay, so the TB suite would
fail if the controller ever shrank these phases. CP-C checklist: **confirm
these constants against the ISSI IS61WV5128BLL datasheet PDF** (one line in
the T-020 ticket Log).
