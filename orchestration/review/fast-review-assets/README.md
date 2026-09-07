# Fast-review diagrams

These standalone SVGs summarize the current FPGA readout boundary. The topology and the coupled snapshot tap are grounded in `gateware/rtl/pdm_stream_core.sv` and `gateware/rtl/sonar_top.sv`; the simulator/evidence boundary is described in `gateware/README.md` and `orchestration/review/REVIEW-2026-09-05.md`. Rates are calculated from 24 channels × the stated PDM clock: 9.216 MB/s at 3.072 MHz and 14.4 MB/s at 4.8 MHz. FIFO slack is 49,152 bytes divided by each rate: 5.33 ms and 3.41 ms. These are explanatory assets, not hardware validation or a progress claim.
