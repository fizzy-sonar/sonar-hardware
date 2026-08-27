`timescale 1ns/1ps
`default_nettype none

// REVIEW-2026-08-26 S6: 2-flop input synchronizer + debounce for the
// mechanical btn[0] snapshot trigger. A level change must hold for
// DEBOUNCE_CYCLES consecutive clk edges before btn_clean follows, so
// contact bounce cannot produce multiple sram_snapshot.start triggers.
// The debounced level still crosses into the sram_clk domain through
// sram_snapshot's internal 2-flop start synchronizer - that CDC was
// already correct; this module removes the mechanical multi-trigger.
module button_debounce #(
    parameter integer DEBOUNCE_CYCLES = 240000  // 20 ms at 12 MHz sysclk
) (
    input  wire clk,
    input  wire reset,
    input  wire btn_async,
    output reg  btn_clean
);
    localparam integer COUNT_WIDTH = DEBOUNCE_CYCLES <= 1 ? 1 :
                                     $clog2(DEBOUNCE_CYCLES);
    (* ASYNC_REG = "TRUE" *) reg meta = 1'b0;
    reg sync = 1'b0;
    reg [COUNT_WIDTH-1:0] count = {COUNT_WIDTH{1'b0}};

    initial btn_clean = 1'b0;

    always @(posedge clk) begin
        if (reset) begin
            meta      <= 1'b0;
            sync      <= 1'b0;
            count     <= {COUNT_WIDTH{1'b0}};
            btn_clean <= 1'b0;
        end else begin
            meta <= btn_async;
            sync <= meta;
            if (sync == btn_clean) begin
                count <= {COUNT_WIDTH{1'b0}};
            end else if (count == DEBOUNCE_CYCLES - 1) begin
                btn_clean <= sync;
                count     <= {COUNT_WIDTH{1'b0}};
            end else begin
                count <= count + 1'b1;
            end
        end
    end
endmodule

`default_nettype wire
