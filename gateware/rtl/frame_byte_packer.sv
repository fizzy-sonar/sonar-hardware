`timescale 1ns/1ps
`default_nettype none

// Read 32-bit FIFO words and emit only the low 24 bits as three bytes. Byte 0
// contains CH00..CH07, byte 1 CH08..CH15, and byte 2 CH16..CH23.
module frame_byte_packer (
    input  wire        clk,
    input  wire        reset,
    input  wire        fifo_empty,
    output reg         fifo_rd_en,
    input  wire [31:0] fifo_rd_data,
    input  wire        fifo_rd_valid,
    output wire [7:0]  byte_data,
    output wire        byte_valid,
    input  wire        byte_ready
);
    reg [23:0] frame;
    reg [1:0]  byte_index;
    reg        have_frame;
    reg        request_pending;

    assign byte_valid = have_frame;
    assign byte_data = byte_index == 2'd0 ? frame[7:0] :
                       byte_index == 2'd1 ? frame[15:8] : frame[23:16];

    always @(posedge clk) begin
        if (reset) begin
            frame           <= 24'd0;
            byte_index      <= 2'd0;
            have_frame      <= 1'b0;
            request_pending <= 1'b0;
            fifo_rd_en      <= 1'b0;
        end else begin
            fifo_rd_en <= 1'b0;

            if (!have_frame && !request_pending && !fifo_empty) begin
                fifo_rd_en      <= 1'b1;
                request_pending <= 1'b1;
            end

            if (fifo_rd_valid) begin
                frame           <= fifo_rd_data[23:0];
                byte_index      <= 2'd0;
                have_frame      <= 1'b1;
                request_pending <= 1'b0;
            end

            if (have_frame && byte_ready) begin
                if (byte_index == 2'd2) begin
                    have_frame <= 1'b0;
                    byte_index <= 2'd0;
                end else begin
                    byte_index <= byte_index + 1'b1;
                end
            end
        end
    end
endmodule

`default_nettype wire
