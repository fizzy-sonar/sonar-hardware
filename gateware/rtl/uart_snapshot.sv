`timescale 1ns/1ps
`default_nettype none

// Bounded simulator/bring-up snapshot. This small inferred RAM proves the wire
// format and UART fallback; a controller for the Cmod's 512 KiB external SRAM is
// still required before claiming the full hardware window.
module uart_snapshot #(
    parameter integer PDM_CLOCK_HZ = 3072000,
    parameter integer FRAME_COUNT = 16,
    parameter integer CLKS_PER_BIT = 104,
    parameter [31:0] CAPTURE_ID = 32'd0
) (
    input  wire        clk,
    input  wire        reset,
    input  wire        start,
    input  wire [23:0] frame_data,
    input  wire        frame_valid,
    output wire        frame_ready,
    output wire        uart_tx_o,
    output reg         busy,
    output reg         done
);
    localparam integer FRAME_INDEX_WIDTH =
        FRAME_COUNT <= 2 ? 1 : $clog2(FRAME_COUNT);
    localparam [2:0] IDLE = 3'd0, CAPTURE = 3'd1, HEADER = 3'd2,
                     PAYLOAD = 3'd3, WAIT_LAST = 3'd4;

    reg [2:0] state;
    reg [23:0] memory [0:FRAME_COUNT-1];
    reg [FRAME_INDEX_WIDTH-1:0] capture_index;
    reg [FRAME_INDEX_WIDTH-1:0] send_frame_index;
    reg [1:0] send_byte_index;
    reg [5:0] header_index;
    reg [31:0] payload_crc_state;
    reg [31:0] payload_crc_final;
    reg [31:0] header_crc_final;

    wire uart_ready;
    wire uart_valid = (state == HEADER) || (state == PAYLOAD);
    reg [7:0] uart_data;
    integer crc_index;
    reg [31:0] crc_work;
    reg [31:0] completed_payload_crc;

    function automatic [31:0] crc32_byte(
        input [31:0] crc_in,
        input [7:0] data_in
    );
        integer bit_number;
        reg [31:0] crc;
        begin
            crc = crc_in ^ data_in;
            for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1)
                crc = crc[0] ? (crc >> 1) ^ 32'hedb88320 : crc >> 1;
            crc32_byte = crc;
        end
    endfunction

    function automatic [7:0] snapshot_header_byte(
        input [5:0] byte_index,
        input [31:0] payload_crc
    );
        begin
            case (byte_index)
                0: snapshot_header_byte = "S";
                1: snapshot_header_byte = "N";
                2: snapshot_header_byte = "P";
                3: snapshot_header_byte = "1";
                4: snapshot_header_byte = 8'd1;
                5: snapshot_header_byte = 8'd48;
                6, 7: snapshot_header_byte = 8'd0;
                8: snapshot_header_byte = CAPTURE_ID[7:0];
                9: snapshot_header_byte = CAPTURE_ID[15:8];
                10: snapshot_header_byte = CAPTURE_ID[23:16];
                11: snapshot_header_byte = CAPTURE_ID[31:24];
                // first_logical_frame = 0
                12, 13, 14, 15, 16, 17, 18, 19: snapshot_header_byte = 8'd0;
                20: snapshot_header_byte = PDM_CLOCK_HZ[7:0];
                21: snapshot_header_byte = PDM_CLOCK_HZ[15:8];
                22: snapshot_header_byte = PDM_CLOCK_HZ[23:16];
                23: snapshot_header_byte = PDM_CLOCK_HZ[31:24];
                24: snapshot_header_byte = 8'd24;
                25: snapshot_header_byte = 8'd0;
                26: snapshot_header_byte = 8'd12;
                27: snapshot_header_byte = 8'd0;
                28: snapshot_header_byte = FRAME_COUNT[7:0];
                29: snapshot_header_byte = FRAME_COUNT[15:8];
                30: snapshot_header_byte = FRAME_COUNT[23:16];
                31: snapshot_header_byte = FRAME_COUNT[31:24];
                32: snapshot_header_byte = (3*FRAME_COUNT) & 8'hff;
                33: snapshot_header_byte = ((3*FRAME_COUNT) >> 8) & 8'hff;
                34: snapshot_header_byte = ((3*FRAME_COUNT) >> 16) & 8'hff;
                35: snapshot_header_byte = ((3*FRAME_COUNT) >> 24) & 8'hff;
                36: snapshot_header_byte = payload_crc[7:0];
                37: snapshot_header_byte = payload_crc[15:8];
                38: snapshot_header_byte = payload_crc[23:16];
                39: snapshot_header_byte = payload_crc[31:24];
                40: snapshot_header_byte = header_crc_final[7:0];
                41: snapshot_header_byte = header_crc_final[15:8];
                42: snapshot_header_byte = header_crc_final[23:16];
                43: snapshot_header_byte = header_crc_final[31:24];
                default: snapshot_header_byte = 8'd0;
            endcase
        end
    endfunction

    assign frame_ready = state == CAPTURE;

    always @* begin
        if (state == HEADER) begin
            uart_data = snapshot_header_byte(header_index, payload_crc_final);
        end else if (state == PAYLOAD) begin
            case (send_byte_index)
                0: uart_data = memory[send_frame_index][7:0];
                1: uart_data = memory[send_frame_index][15:8];
                default: uart_data = memory[send_frame_index][23:16];
            endcase
        end else begin
            uart_data = 8'd0;
        end
    end

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) uart_i (
        .clk(clk),
        .reset(reset),
        .data(uart_data),
        .valid(uart_valid),
        .ready(uart_ready),
        .tx(uart_tx_o)
    );

    initial begin
        if (FRAME_COUNT < 1) $error("uart_snapshot FRAME_COUNT must be positive");
    end

    always @(posedge clk) begin
        if (reset) begin
            state              <= IDLE;
            capture_index      <= {FRAME_INDEX_WIDTH{1'b0}};
            send_frame_index   <= {FRAME_INDEX_WIDTH{1'b0}};
            send_byte_index    <= 2'd0;
            header_index       <= 6'd0;
            payload_crc_state  <= 32'hffffffff;
            payload_crc_final  <= 32'd0;
            header_crc_final   <= 32'd0;
            busy               <= 1'b0;
            done               <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: begin
                    busy <= 1'b0;
                    if (start) begin
                        state             <= CAPTURE;
                        busy              <= 1'b1;
                        capture_index     <= {FRAME_INDEX_WIDTH{1'b0}};
                        payload_crc_state <= 32'hffffffff;
                    end
                end

                CAPTURE: if (frame_valid) begin
                    memory[capture_index] <= frame_data;
                    crc_work = crc32_byte(payload_crc_state, frame_data[7:0]);
                    crc_work = crc32_byte(crc_work, frame_data[15:8]);
                    crc_work = crc32_byte(crc_work, frame_data[23:16]);
                    payload_crc_state <= crc_work;
                    if (capture_index == FRAME_COUNT - 1) begin
                        completed_payload_crc = ~crc_work;
                        payload_crc_final <= completed_payload_crc;
                        // Use the just-completed payload CRC directly so the
                        // header checksum has no nonblocking-assignment race.
                        crc_work = 32'hffffffff;
                        for (crc_index = 0; crc_index < 40; crc_index = crc_index + 1)
                            crc_work = crc32_byte(
                                crc_work,
                                snapshot_header_byte(crc_index[5:0], completed_payload_crc)
                            );
                        header_crc_final <= ~crc_work;
                        header_index     <= 6'd0;
                        state            <= HEADER;
                    end else begin
                        capture_index <= capture_index + 1'b1;
                    end
                end

                HEADER: if (uart_ready) begin
                    if (header_index == 6'd47) begin
                        send_frame_index <= {FRAME_INDEX_WIDTH{1'b0}};
                        send_byte_index  <= 2'd0;
                        state            <= PAYLOAD;
                    end else begin
                        header_index <= header_index + 1'b1;
                    end
                end

                PAYLOAD: if (uart_ready) begin
                    if (send_byte_index == 2'd2) begin
                        send_byte_index <= 2'd0;
                        if (send_frame_index == FRAME_COUNT - 1) begin
                            state <= WAIT_LAST;
                        end else begin
                            send_frame_index <= send_frame_index + 1'b1;
                        end
                    end else begin
                        send_byte_index <= send_byte_index + 1'b1;
                    end
                end

                WAIT_LAST: if (uart_ready) begin
                    state <= IDLE;
                    busy  <= 1'b0;
                    done  <= 1'b1;
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule

`default_nettype wire
