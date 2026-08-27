`timescale 1ns/1ps
`default_nettype none

// REVIEW-2026-08-26 S6: async-assert / synchronous-release reset
// synchronizer, one instance per RECEIVING clock domain. Assertion is
// immediate (async preset); release is aligned to the destination clock
// after two flops, so no domain sees a metastable or non-simultaneous
// release. This is exactly the pattern the async_fifo's paired
// wr_reset/rd_reset are sensitive to. A domain whose clock is not running
// yet (pdm_clk_fb before the mic clock starts, sram_clk before the MMCM
// locks) simply holds reset until its clock runs - the intended behavior.
module reset_sync (
    input  wire clk,
    input  wire reset_async,
    output wire reset_synced
);
    (* ASYNC_REG = "TRUE" *) reg meta = 1'b1;
    reg sync = 1'b1;
    always @(posedge clk or posedge reset_async) begin
        if (reset_async) begin
            meta <= 1'b1;
            sync <= 1'b1;
        end else begin
            meta <= 1'b0;
            sync <= meta;
        end
    end
    assign reset_synced = sync;
endmodule

`default_nettype wire
