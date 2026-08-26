`timescale 1ns/1ps
`default_nettype none

// Dual-clock FIFO with Gray-coded pointer synchronization. DEPTH must be a
// power of two. The production default is 16,384 x 32 bits = exactly 64 KiB.
module async_fifo #(
    parameter integer WIDTH = 32,
    parameter integer DEPTH = 16384
) (
    input  wire             wr_clk,
    input  wire             wr_reset,
    input  wire             wr_en,
    input  wire [WIDTH-1:0] wr_data,
    output reg              wr_full,

    input  wire             rd_clk,
    input  wire             rd_reset,
    input  wire             rd_en,
    output reg  [WIDTH-1:0] rd_data,
    output reg              rd_valid,
    output reg              rd_empty
);
    localparam integer ADDR_WIDTH = $clog2(DEPTH);
    localparam integer PTR_WIDTH  = ADDR_WIDTH + 1;

    reg [WIDTH-1:0] memory [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] wr_binary, wr_gray;
    reg [PTR_WIDTH-1:0] rd_binary, rd_gray;
    (* ASYNC_REG = "TRUE" *) reg [PTR_WIDTH-1:0] rd_gray_sync1, rd_gray_sync2;
    (* ASYNC_REG = "TRUE" *) reg [PTR_WIDTH-1:0] wr_gray_sync1, wr_gray_sync2;

    wire wr_take = wr_en && !wr_full;
    wire rd_take = rd_en && !rd_empty;
    wire [PTR_WIDTH-1:0] wr_binary_next = wr_binary + wr_take;
    wire [PTR_WIDTH-1:0] rd_binary_next = rd_binary + rd_take;
    wire [PTR_WIDTH-1:0] wr_gray_next = (wr_binary_next >> 1) ^ wr_binary_next;
    wire [PTR_WIDTH-1:0] rd_gray_next = (rd_binary_next >> 1) ^ rd_binary_next;

    // Full when the next write pointer is one complete ring ahead of the read
    // pointer. In Gray code that inverts the two most-significant bits.
    wire wr_full_next =
        wr_gray_next == {~rd_gray_sync2[PTR_WIDTH-1:PTR_WIDTH-2],
                         rd_gray_sync2[PTR_WIDTH-3:0]};
    wire rd_empty_next = (rd_gray_next == wr_gray_sync2);

    initial begin
        if (DEPTH < 4 || (DEPTH & (DEPTH - 1)) != 0) begin
            $error("async_fifo DEPTH must be a power of two >= 4");
        end
    end

    always @(posedge wr_clk) begin
        if (wr_reset) begin
            wr_binary     <= {PTR_WIDTH{1'b0}};
            wr_gray       <= {PTR_WIDTH{1'b0}};
            rd_gray_sync1 <= {PTR_WIDTH{1'b0}};
            rd_gray_sync2 <= {PTR_WIDTH{1'b0}};
            wr_full       <= 1'b0;
        end else begin
            rd_gray_sync1 <= rd_gray;
            rd_gray_sync2 <= rd_gray_sync1;
            if (wr_take) begin
                memory[wr_binary[ADDR_WIDTH-1:0]] <= wr_data;
            end
            wr_binary <= wr_binary_next;
            wr_gray   <= wr_gray_next;
            wr_full   <= wr_full_next;
        end
    end

    always @(posedge rd_clk) begin
        if (rd_reset) begin
            rd_binary     <= {PTR_WIDTH{1'b0}};
            rd_gray       <= {PTR_WIDTH{1'b0}};
            wr_gray_sync1 <= {PTR_WIDTH{1'b0}};
            wr_gray_sync2 <= {PTR_WIDTH{1'b0}};
            rd_data       <= {WIDTH{1'b0}};
            rd_valid      <= 1'b0;
            rd_empty      <= 1'b1;
        end else begin
            wr_gray_sync1 <= wr_gray;
            wr_gray_sync2 <= wr_gray_sync1;
            rd_valid      <= rd_take;
            if (rd_take) begin
                rd_data <= memory[rd_binary[ADDR_WIDTH-1:0]];
            end
            rd_binary <= rd_binary_next;
            rd_gray   <= rd_gray_next;
            rd_empty  <= rd_empty_next;
        end
    end
endmodule

`default_nettype wire
