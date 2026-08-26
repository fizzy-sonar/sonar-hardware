`timescale 1ns/1ps
`default_nettype none

// Minimal 8-N-1 UART transmitter. CLKS_PER_BIT must be >= 2.
module uart_tx #(
    parameter integer CLKS_PER_BIT = 104
) (
    input  wire       clk,
    input  wire       reset,
    input  wire [7:0] data,
    input  wire       valid,
    output wire       ready,
    output reg        tx
);
    localparam integer COUNT_WIDTH = $clog2(CLKS_PER_BIT);
    reg [COUNT_WIDTH-1:0] clock_count;
    reg [3:0] bit_index;
    reg [9:0] shift;
    reg busy;

    assign ready = !busy;

    initial begin
        if (CLKS_PER_BIT < 2) $error("uart_tx CLKS_PER_BIT must be >= 2");
    end

    always @(posedge clk) begin
        if (reset) begin
            clock_count <= {COUNT_WIDTH{1'b0}};
            bit_index   <= 4'd0;
            shift       <= 10'h3ff;
            busy        <= 1'b0;
            tx          <= 1'b1;
        end else if (!busy) begin
            tx <= 1'b1;
            if (valid) begin
                // LSB first: start, eight data bits, stop.
                shift       <= {1'b1, data, 1'b0};
                clock_count <= {COUNT_WIDTH{1'b0}};
                bit_index   <= 4'd0;
                busy        <= 1'b1;
                tx          <= 1'b0;
            end
        end else if (clock_count == CLKS_PER_BIT - 1) begin
            clock_count <= {COUNT_WIDTH{1'b0}};
            if (bit_index == 4'd9) begin
                busy <= 1'b0;
                tx   <= 1'b1;
            end else begin
                bit_index <= bit_index + 1'b1;
                shift     <= {1'b1, shift[9:1]};
                tx        <= shift[1];
            end
        end else begin
            clock_count <= clock_count + 1'b1;
        end
    end
endmodule

`default_nettype wire
