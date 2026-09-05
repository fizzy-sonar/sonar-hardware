`timescale 1ns/1ps
// T-019: reproduce the integrated fallback's dead tap after a USB stall.
// Small FIFO accelerates the same default-depth failure, without modifying RTL.
module tb_fallback_starvation;
    reg pdm_clk = 0, ft_clk = 0, reset = 1, capture = 0;
    wire stopped, overflow, tap_valid;
    wire [23:0] tap_data;
    integer taps = 0;
    integer taps_at_stop;
    always #50 pdm_clk = ~pdm_clk;
    always #5 ft_clk = ~ft_clk;
    pdm_stream_core #(.FIFO_DEPTH(8)) dut (
        .pdm_clk_fb(pdm_clk), .pdm_reset(reset), .pdm_data(12'b0),
        .capture_enable(capture), .overflow_sticky(overflow),
        .capture_stopped(stopped), .tap_frame_data(tap_data),
        .tap_frame_valid(tap_valid), .ft_clk(ft_clk), .ft_reset(reset),
        .ft_txe_n(1'b1)
    );
    always @(posedge pdm_clk) if (tap_valid) taps = taps + 1;
    initial begin
        repeat (4) @(negedge pdm_clk);
        reset = 0; capture = 1;
        wait (stopped);
        @(negedge pdm_clk);
        taps_at_stop = taps;
        // A later user snapshot button can only open the snapshot's local
        // FIFO; it cannot restart this upstream tap in sonar_top.
        repeat (100) @(negedge pdm_clk);
        if (!overflow || taps != taps_at_stop)
            $fatal(1, "reviewed starvation behavior changed");
        $display("REPRODUCED: stalled USB stops snapshot tap; taps before=%0d after=%0d", taps_at_stop, taps);
        $finish;
    end
    initial begin #100000; $fatal(1, "probe timeout"); end
endmodule
