`timescale 1ns/1ps
`default_nettype none

// Write-only FT245 synchronous-FIFO interface. Data and WR# are registered from
// FT_CLK so they get a full clock period of setup before FT232H samples them.
// The one-byte output register can be replaced on the same edge its prior byte
// is accepted, preserving one byte/clock burst throughput. TXE# may change after
// a clock edge; a byte retires only when registered WR# and TXE# are both low.
module ft245_sync_tx (
    input  wire       clk,
    input  wire       reset,
    input  wire       ft_txe_n,
    input  wire [7:0] byte_data,
    input  wire       byte_valid,
    output wire       byte_ready,
    output wire [7:0] ft_data_out,
    output wire       ft_data_oe,
    output wire       ft_wr_n,
    output wire       ft_rd_n,
    output wire       ft_oe_n,
    output wire       ft_siwu_n
);
    reg [7:0] output_data;
    reg       output_valid;
    reg       write_armed;

    wire output_accepted = output_valid && write_armed && !ft_txe_n;
    wire input_accepted = byte_valid && byte_ready;

    // Empty space or a simultaneous FT232H acceptance makes room for one input.
    assign byte_ready = !reset && (!output_valid || output_accepted);
    assign ft_data_out = output_data;
    assign ft_data_oe = !reset && output_valid && write_armed;
    assign ft_wr_n = !ft_data_oe;

    // The v1 core is transmit-only. Never enable the FT232H read direction.
    assign ft_rd_n = 1'b1;
    assign ft_oe_n = 1'b1;
    assign ft_siwu_n = 1'b1;

    always @(posedge clk) begin
        if (reset) begin
            output_data  <= 8'd0;
            output_valid <= 1'b0;
            write_armed  <= 1'b0;
        end else begin
            if (input_accepted) begin
                output_data  <= byte_data;
                output_valid <= 1'b1;
            end else if (output_accepted) begin
                output_valid <= 1'b0;
            end

            // Arm only from a sampled-low TXE#. If TXE# rises after this edge,
            // both-low qualification prevents retirement and the byte is held.
            if (input_accepted) begin
                write_armed <= !ft_txe_n;
            end else if (output_accepted) begin
                write_armed <= 1'b0;
            end else if (output_valid) begin
                write_armed <= !ft_txe_n;
            end else begin
                write_armed <= 1'b0;
            end
        end
    end
endmodule

`default_nettype wire
