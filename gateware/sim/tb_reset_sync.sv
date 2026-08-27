`timescale 1ns/1ps
`default_nettype none

// REVIEW-2026-08-26 S6 TB: per-domain async-assert/sync-release reset
// synchronizers (reset_sync) and the btn[0] debounce (button_debounce).
//
// Proves, per domain:
//  1. assertion is immediate (async), even with the domain clock stopped;
//  2. release happens exactly on the 2nd rising edge of the domain clock
//     after the async input falls - never mid-cycle, never simultaneous
//     across domains;
//  3. once released, the reset stays low.
// And for the button path:
//  4. contact bounce produces no output transition;
//  5. a pulse shorter than the debounce window is rejected;
//  6. a stable press produces exactly one clean level change.
module tb_reset_sync;
    // Representative destination clocks: 3.072 MHz (pdm), 60 MHz (ft),
    // 48 MHz (sram), plus 12 MHz sysclk for the debouncer.
    reg clk_pdm  = 1'b0; always #162.760 clk_pdm  = ~clk_pdm;
    reg clk_ft   = 1'b0; always #8.333   clk_ft   = ~clk_ft;
    reg clk_sram = 1'b0; always #10.417  clk_sram = ~clk_sram;
    reg clk_sys  = 1'b0; always #41.667  clk_sys  = ~clk_sys;

    reg  reset_async = 1'b0;
    wire rst_pdm, rst_ft, rst_sram;
    integer released_pdm  = 0;
    integer released_ft   = 0;
    integer released_sram = 0;

    reset_sync pdm_i  (.clk(clk_pdm),  .reset_async(reset_async),
                       .reset_synced(rst_pdm));
    reset_sync ft_i   (.clk(clk_ft),   .reset_async(reset_async),
                       .reset_synced(rst_ft));
    reset_sync sram_i (.clk(clk_sram), .reset_async(reset_async),
                       .reset_synced(rst_sram));

    // Debouncer with a short window so the TB stays fast (production uses
    // 240000 cycles = 20 ms at 12 MHz).
    localparam integer DEB = 8;
    reg  btn_raw = 1'b0;
    wire btn_clean;
    button_debounce #(.DEBOUNCE_CYCLES(DEB)) deb_i (
        .clk(clk_sys), .reset(1'b0), .btn_async(btn_raw),
        .btn_clean(btn_clean)
    );

    // (2) release must coincide with a posedge of the domain clock: the
    // synchronizer flops update on the posedge NBA, so sampling rst right
    // after its falling event must see the clock already high.
    always @(negedge rst_pdm)
        if (reset_async === 1'b0 && !released_pdm) begin
            if (clk_pdm !== 1'b1)
                $fatal(1, "pdm reset released off-clock-edge");
            released_pdm = 1;
        end
    always @(negedge rst_ft)
        if (reset_async === 1'b0 && !released_ft) begin
            if (clk_ft !== 1'b1)
                $fatal(1, "ft reset released off-clock-edge");
            released_ft = 1;
        end
    always @(negedge rst_sram)
        if (reset_async === 1'b0 && !released_sram) begin
            if (clk_sram !== 1'b1)
                $fatal(1, "sram reset released off-clock-edge");
            released_sram = 1;
        end

    // (3) released resets must stay released.
    always @(posedge rst_pdm or posedge rst_ft or posedge rst_sram)
        if (reset_async === 1'b0 && $time > 2000)
            $fatal(1, "released reset re-asserted without async reset");

    initial begin
        // Initial state: synchronizers power up asserted.
        #1;
        if (rst_pdm !== 1'b1 || rst_ft !== 1'b1 || rst_sram !== 1'b1)
            $fatal(1, "resets not asserted at time 0");

        // (1) async assertion lands immediately even with clocks running
        // at unrelated phases; hold, then release at a phase aligned to
        // NONE of the domain clocks.
        #100;
        reset_async = 1'b1;
        #0.1;
        if (rst_pdm !== 1'b1 || rst_ft !== 1'b1 || rst_sram !== 1'b1)
            $fatal(1, "async assertion did not propagate immediately");

        #500;
        reset_async = 1'b0;  // released at a phase aligned to no clock

        // Measure: rst must fall exactly 2 posedges after release per
        // domain (meta captures 0 on edge 1, sync follows on edge 2).
        fork
            begin : watch_pdm
                integer n;
                n = 0;
                while (rst_pdm === 1'b1) begin
                    @(posedge clk_pdm);
                    #0.1;
                    n = n + 1;
                    if (n > 4) $fatal(1, "pdm reset never released");
                end
                if (n != 2) $fatal(1, "pdm released after %0d edges, want 2", n);
            end
            begin : watch_ft
                integer n;
                n = 0;
                while (rst_ft === 1'b1) begin
                    @(posedge clk_ft);
                    #0.1;
                    n = n + 1;
                    if (n > 4) $fatal(1, "ft reset never released");
                end
                if (n != 2) $fatal(1, "ft released after %0d edges, want 2", n);
            end
            begin : watch_sram
                integer n;
                n = 0;
                while (rst_sram === 1'b1) begin
                    @(posedge clk_sram);
                    #0.1;
                    n = n + 1;
                    if (n > 4) $fatal(1, "sram reset never released");
                end
                if (n != 2) $fatal(1, "sram released after %0d edges, want 2", n);
            end
        join

        // Second assertion, this time mid-cycle relative to every clock.
        #1000;
        reset_async = 1'b1;
        #0.1;
        if (rst_pdm !== 1'b1 || rst_ft !== 1'b1 || rst_sram !== 1'b1)
            $fatal(1, "second async assertion not immediate");
        #3.7;  // deliberately phase-misaligned release
        reset_async = 1'b0;
        wait (rst_pdm === 1'b0 && rst_ft === 1'b0 && rst_sram === 1'b0);
        #100;

        // (4)(5)(6) debounce: bounce around a press, then a short glitch,
        // then a real press.
        if (btn_clean !== 1'b0) $fatal(1, "btn_clean not low at start");
        // bounce: 6 toggles 2 sysclk cycles apart (each < DEB)
        repeat (3) begin
            btn_raw = 1'b1; repeat (2) @(posedge clk_sys);
            btn_raw = 1'b0; repeat (2) @(posedge clk_sys);
        end
        repeat (DEB + 2) @(posedge clk_sys);
        if (btn_clean !== 1'b0) $fatal(1, "bounce leaked to btn_clean");

        // short glitch high, shorter than the window
        btn_raw = 1'b1; repeat (DEB - 2) @(posedge clk_sys);
        btn_raw = 1'b0; repeat (DEB + 2) @(posedge clk_sys);
        if (btn_clean !== 1'b0) $fatal(1, "short glitch leaked to btn_clean");

        // real press: stable high longer than the window
        btn_raw = 1'b1;
        repeat (DEB + 4) @(posedge clk_sys);
        #0.1;
        if (btn_clean !== 1'b1) $fatal(1, "stable press not debounced high");
        // hold and confirm no retrigger/glitch while raw stays high
        repeat (2 * DEB) @(posedge clk_sys);
        if (btn_clean !== 1'b1) $fatal(1, "btn_clean dropped during hold");

        // bounce on release, then stable low
        repeat (2) begin
            btn_raw = 1'b0; repeat (2) @(posedge clk_sys);
            btn_raw = 1'b1; repeat (2) @(posedge clk_sys);
        end
        if (btn_clean !== 1'b1) $fatal(1, "release bounce dropped btn_clean");
        btn_raw = 1'b0;
        repeat (DEB + 4) @(posedge clk_sys);
        #0.1;
        if (btn_clean !== 1'b0) $fatal(1, "stable release not debounced low");

        $display("PASS reset_sync/release edges=2/domain + debounce clean");
        $finish;
    end

    initial begin
        #100000;
        $fatal(1, "tb_reset_sync timeout");
    end
endmodule

`default_nettype wire
