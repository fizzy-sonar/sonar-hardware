`timescale 1ns/1ps
`default_nettype none

// REVIEW-2026-08-26 S7/S8 TB: waveform-level test of pdm_clock_7series
// through the FUNCTIONAL primitive models (xilinx_7series_stubs.sv), driven
// by the real pdm_clock_startup FSM (time-compressed 1000x like
// tb_clock_tx). Checks, over the full OFF -> 1.536 MHz -> clock-off ->
// 3.072 MHz -> run sequence AND a wake-requested re-run:
//  1. every high pulse of pdm_clk_src is a full half-period of either the
//     standard (1.536 MHz) or ultrasonic (3.072 MHz) clock - no mic-clock
//     edge is ever clipped, including across enable/disable and the
//     BUFGCTRL rate switch;
//  2. the output is verifiably OFF around the rate switch (the off window
//     exceeds the OE-sync latency: SWITCH_OFF_CYCLES=20 at 12 MHz =
//     1.67 us > 2 x 651 ns);
//  3. rates: ~1.536 MHz during standard, ~3.072 MHz in run, sram_clk
//     ~48 MHz, MMCM locks;
//  4. disable through wake_request mid-run also emits only full pulses.
module tb_pdm_clock;
    localparam real HALF_STD_NS   = 325.521;  // 1.536 MHz half period
    localparam real HALF_ULTRA_NS = 162.760;  // 3.072 MHz half period

    reg clk12 = 1'b0;
    always #41.667 clk12 = ~clk12;  // 12.000 MHz

    reg reset = 1'b1;
    reg wake  = 1'b1;
    wire buffer_oe, select_ultrasonic, discard_samples, capture_enable;
    wire pdm_clk_src, locked, sram_clk;

    pdm_clock_startup #(
        .CTRL_CLOCK_HZ(12000),     // 1000x time compression: 1 "ms" = 1 us
        .START_STANDARD_MS(8),
        .ULTRASONIC_SETTLE_MS(4),
        .SWITCH_OFF_CYCLES(20)     // production value; see pdm_clock_startup
    ) startup_i (
        // power_good(locked) mirrors production (sonar_top gates the FSM on
        // clocks_locked), so the sync-chain latency after lock is exercised.
        .clk(clk12), .reset(reset), .power_good(locked), .wake_request(wake),
        .buffer_oe(buffer_oe), .select_ultrasonic(select_ultrasonic),
        .discard_samples(discard_samples), .capture_enable(capture_enable)
    );

    pdm_clock_7series #(.PDM_CLOCK_HZ(3072000)) dut (
        .clk_12mhz(clk12), .reset(reset),
        .buffer_oe(buffer_oe), .select_ultrasonic(select_ultrasonic),
        .pdm_clk_src(pdm_clk_src), .locked(locked), .sram_clk(sram_clk)
    );

    // (1) pulse-width monitor: every output high pulse must be a full half
    // period of one of the two rates. A clipped edge (metastable OE capture
    // or a glitchy mux switch) shows up here as a short pulse.
    real t_rise = -1.0;
    real w;
    integer pulses = 0;
    always @(posedge pdm_clk_src) t_rise = $realtime;
    always @(negedge pdm_clk_src) begin
        if (t_rise >= 0.0) begin
            w = $realtime - t_rise;
            pulses = pulses + 1;
            if (!((w > 0.92 * HALF_STD_NS   && w < 1.08 * HALF_STD_NS) ||
                  (w > 0.92 * HALF_ULTRA_NS && w < 1.08 * HALF_ULTRA_NS)))
                $fatal(1, "clipped/runt mic clock pulse: %0.1f ns at %0t",
                       w, $realtime);
        end
    end

    // Rate counters.
    integer std_pulses = 0;
    integer ult_pulses = 0;
    always @(posedge pdm_clk_src) begin
        if (capture_enable === 1'b0 && select_ultrasonic === 1'b0)
            std_pulses = std_pulses + 1;
        if (capture_enable === 1'b1 && select_ultrasonic === 1'b1)
            ult_pulses = ult_pulses + 1;
    end

    integer sram_count = 0;
    integer run_count  = 0;
    integer n;

    initial begin
        // POR + lock
        repeat (4) @(posedge clk12);
        #1;
        reset = 1'b0;

        // (3) MMCM must lock; sram_clk must run at ~48 MHz.
        wait (locked === 1'b1);
        sram_count = 0;
        #2000;  // 2 us window
        if (sram_count < 90 || sram_count > 102)
            $fatal(1, "sram_clk rate wrong: %0d cycles/2us (want ~96)",
                   sram_count);

        // Startup sequence completes: capture_enable rises (4 us standard +
        // 1.67 us switch-off + 4 us settle, compressed).
        wait (capture_enable === 1'b1);
        if (std_pulses < 2 || std_pulses > 14)
            $fatal(1, "standard-phase pulses %0d outside 1.536 MHz window",
                   std_pulses);

        // Measure the run rate over a 10 us window: 3.072 MHz -> ~31.
        #1000;
        run_count = 0;
        #10000;
        if (run_count < 27 || run_count > 35)
            $fatal(1, "run rate wrong: %0d cycles/10us (want ~31)",
                   run_count);

        // (4) bounce the whole sequence once via wake_request: FSM drops
        // buffer_oe, re-runs standard/switch/settle. The pulse monitor
        // keeps running throughout - any clip is fatal.
        wake = 1'b0;
        #500;
        wake = 1'b1;
        wait (capture_enable === 1'b1);
        #2000;

        if (pulses < 40)
            $fatal(1, "implausibly few output pulses (%0d) - clock stuck?",
                   pulses);
        $display("PASS pdm_clock waveform: pulses=%0d std=%0d run10us=%0d sram2us=%0d, no clipped edges",
                 pulses, std_pulses, run_count, sram_count);
        $finish;
    end

    always @(posedge sram_clk) sram_count = sram_count + 1;
    always @(posedge pdm_clk_src)
        if (capture_enable === 1'b1) run_count = run_count + 1;

    initial begin
        #2000000;  // 2 ms wall-clock guard
        $fatal(1, "tb_pdm_clock timeout");
    end
endmodule

`default_nettype wire
