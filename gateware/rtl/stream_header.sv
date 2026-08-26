`timescale 1ns/1ps
`default_nettype none

// SNR1 continuous-stream header. It intentionally mirrors the common prefix of
// SNP1 while omitting finite-length and CRC fields that cannot be known up front.
module stream_header #(
    parameter integer PDM_CLOCK_HZ = 3072000
) (
    input  wire       clk,
    input  wire       reset,
    input  wire       start,
    input  wire [31:0] capture_id,
    input  wire [63:0] first_logical_frame,
    output wire [7:0] byte_data,
    output wire       byte_valid,
    input  wire       byte_ready,
    output wire       done
);
    reg [5:0] index;
    reg       active;
    reg       complete;
    reg [31:0] capture_id_latched;
    reg [63:0] first_frame_latched;

    function automatic [7:0] header_byte(input [5:0] byte_index);
        begin
            case (byte_index)
                0: header_byte = "S";
                1: header_byte = "N";
                2: header_byte = "R";
                3: header_byte = "1";
                4: header_byte = 8'd1;   // version
                5: header_byte = 8'd32;  // header bytes
                6: header_byte = 8'h07;  // raw, LE frames, fixed edge map
                7: header_byte = 8'h00;
                8: header_byte = capture_id_latched[7:0];
                9: header_byte = capture_id_latched[15:8];
                10: header_byte = capture_id_latched[23:16];
                11: header_byte = capture_id_latched[31:24];
                12: header_byte = first_frame_latched[7:0];
                13: header_byte = first_frame_latched[15:8];
                14: header_byte = first_frame_latched[23:16];
                15: header_byte = first_frame_latched[31:24];
                16: header_byte = first_frame_latched[39:32];
                17: header_byte = first_frame_latched[47:40];
                18: header_byte = first_frame_latched[55:48];
                19: header_byte = first_frame_latched[63:56];
                20: header_byte = PDM_CLOCK_HZ[7:0];
                21: header_byte = PDM_CLOCK_HZ[15:8];
                22: header_byte = PDM_CLOCK_HZ[23:16];
                23: header_byte = PDM_CLOCK_HZ[31:24];
                24: header_byte = 8'd24;
                25: header_byte = 8'd0;
                26: header_byte = 8'd12;
                27: header_byte = 8'd0;
                default: header_byte = 8'h00;
            endcase
        end
    endfunction

    assign byte_data  = header_byte(index);
    assign byte_valid = active;
    assign done       = complete;

    always @(posedge clk) begin
        if (reset) begin
            index               <= 6'd0;
            active              <= 1'b0;
            complete            <= 1'b0;
            capture_id_latched  <= 32'd0;
            first_frame_latched <= 64'd0;
        end else if (start) begin
            index               <= 6'd0;
            active              <= 1'b1;
            complete            <= 1'b0;
            capture_id_latched  <= capture_id;
            first_frame_latched <= first_logical_frame;
        end else if (active && byte_ready) begin
            if (index == 6'd31) begin
                active   <= 1'b0;
                complete <= 1'b1;
            end else begin
                index <= index + 1'b1;
            end
        end
    end
endmodule

`default_nettype wire
