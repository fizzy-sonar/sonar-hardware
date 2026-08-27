`timescale 1ns/1ps
`default_nettype none

// Round-trip proof for sram_snapshot against the timing-enforcing
// IS61WV5128BLL model. Two parameter variants (see Makefile):
//   small: two back-to-back 16-frame captures plus a stream-stopped timeout
//          capture, each byte- and CRC-exact;
//   full:  one capture filling the complete 512 KiB window (174,762 frames =
//          524,286 payload bytes), drained and checked bit-exact.
module tb_sram_snapshot #(
    parameter integer SNAPSHOT_FRAMES = 16,
    parameter integer CLKS_PER_BIT = 8,
    parameter integer FRAME_TIMEOUT_CLKS = 2000,
    parameter integer FULL_WINDOW = 0
);
    localparam real CLK_HALF_NS = 10.4165;      // 48 MHz SRAM/UART clock
    localparam integer STREAM_HALF_NS = 50;     // 10 MHz stand-in stream clock
    localparam integer MAX_BYTES = 48 + 3*SNAPSHOT_FRAMES;
    localparam [31:0] INITIAL_ID = 32'd5;

    reg clk = 1'b0;
    reg stream_clk = 1'b0;
    reg reset = 1'b1;
    reg start = 1'b0;
    reg [23:0] stream_frame_data = 24'd0;
    reg stream_frame_valid = 1'b0;
    wire [18:0] sram_addr;
    wire [7:0] sram_data;
    wire sram_ce_n, sram_oe_n, sram_we_n;
    wire uart_line, busy, done, capture_error;
    wire [31:0] captured_frames;

    reg [7:0] received [0:3*MAX_BYTES-1];
    integer received_count = 0;
    integer i;

    always #(CLK_HALF_NS) clk = ~clk;
    always #(STREAM_HALF_NS) stream_clk = ~stream_clk;

    sram_snapshot #(
        .PDM_CLOCK_HZ(3072000),
        .SNAPSHOT_FRAMES(SNAPSHOT_FRAMES),
        .CLKS_PER_BIT(CLKS_PER_BIT),
        .INITIAL_CAPTURE_ID(INITIAL_ID),
        .FRAME_TIMEOUT_CLKS(FRAME_TIMEOUT_CLKS)
    ) dut (
        .clk(clk), .reset(reset), .start(start),
        .stream_clk(stream_clk), .stream_reset(reset),
        .stream_frame_data(stream_frame_data),
        .stream_frame_valid(stream_frame_valid),
        .sram_addr(sram_addr), .sram_data(sram_data),
        .sram_ce_n(sram_ce_n), .sram_oe_n(sram_oe_n), .sram_we_n(sram_we_n),
        .uart_tx_o(uart_line), .busy(busy), .done(done),
        .capture_error(capture_error), .captured_frames(captured_frames)
    );

    is61wv5128bll_model sram_i (
        .addr(sram_addr), .data(sram_data),
        .ce_n(sram_ce_n), .oe_n(sram_oe_n), .we_n(sram_we_n)
    );

    function automatic [7:0] expected_byte(input integer j);
        expected_byte = (j + (j >> 8) + 8'h3c) & 8'hff;
    endfunction

    function automatic [31:0] crc32_byte(
        input [31:0] crc_in,
        input [7:0] data_in
    );
        integer bit_number;
        reg [31:0] value;
        begin
            value = crc_in ^ data_in;
            for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1)
                value = value[0] ? (value >> 1) ^ 32'hedb88320 : value >> 1;
            crc32_byte = value;
        end
    endfunction

    task automatic receive_uart_byte(output [7:0] value);
        integer bit_number;
        begin
            @(negedge uart_line);
            #(CLK_HALF_NS * 2 * CLKS_PER_BIT / 2);
            if (uart_line !== 1'b0) $fatal(1, "bad UART start bit");
            for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1) begin
                #(CLK_HALF_NS * 2 * CLKS_PER_BIT);
                value[bit_number] = uart_line;
            end
            #(CLK_HALF_NS * 2 * CLKS_PER_BIT);
            if (uart_line !== 1'b1) $fatal(1, "bad UART stop bit");
        end
    endtask

    // One frame per three stream clocks: 3.33 Mframes/s into the CDC FIFO,
    // slower than the 5.33 Mframes/s SRAM service rate (like the real
    // 3.072/4.8 MHz stream), so steady-state capture never overruns.
    task automatic send_frames(input integer count, input integer gbase);
        integer k;
        begin
            for (k = 0; k < count; k = k + 1) begin
                @(negedge stream_clk);
                stream_frame_data = {expected_byte(gbase + 3*k + 2),
                                     expected_byte(gbase + 3*k + 1),
                                     expected_byte(gbase + 3*k)};
                stream_frame_valid = 1'b1;
                @(negedge stream_clk);
                stream_frame_valid = 1'b0;
                @(negedge stream_clk);
            end
        end
    endtask

    task automatic verify_capture(
        input integer base,
        input integer frames,
        input [31:0] cap_id,
        input integer gbase
    );
        integer total;
        integer j;
        reg [31:0] crc;
        begin
            total = 48 + 3*frames;
            if (received_count < base + total)
                $fatal(1, "capture ended at %0d bytes, expected %0d",
                       received_count, base + total);
            if ({received[base], received[base+1], received[base+2],
                 received[base+3]} !== "SNP1") $fatal(1, "bad SNP1 magic");
            if (received[base+4] != 1 || received[base+5] != 48)
                $fatal(1, "bad SNP1 version/header size");
            if ({received[base+11], received[base+10], received[base+9],
                 received[base+8]} !== cap_id)
                $fatal(1, "bad capture id (want %0d)", cap_id);
            if ({received[base+23], received[base+22], received[base+21],
                 received[base+20]} != 3072000)
                $fatal(1, "bad PDM clock field");
            if (received[base+24] != 24 || received[base+26] != 12)
                $fatal(1, "bad geometry fields");
            if ({received[base+31], received[base+30], received[base+29],
                 received[base+28]} != frames)
                $fatal(1, "bad frame count (want %0d)", frames);
            if ({received[base+35], received[base+34], received[base+33],
                 received[base+32]} != 3*frames)
                $fatal(1, "bad payload byte count");
            for (j = 0; j < 3*frames; j = j + 1)
                if (received[base+48+j] !== expected_byte(gbase + j))
                    $fatal(1, "payload byte %0d mismatch: got %02x want %02x",
                           j, received[base+48+j], expected_byte(gbase + j));
            crc = 32'hffffffff;
            for (j = 0; j < 3*frames; j = j + 1)
                crc = crc32_byte(crc, received[base+48+j]);
            crc = ~crc;
            if ({received[base+39], received[base+38], received[base+37],
                 received[base+36]} !== crc)
                $fatal(1, "payload CRC mismatch");
            crc = 32'hffffffff;
            for (j = 0; j < 40; j = j + 1)
                crc = crc32_byte(crc, received[base+j]);
            crc = ~crc;
            if ({received[base+43], received[base+42], received[base+41],
                 received[base+40]} !== crc)
                $fatal(1, "header CRC mismatch");
        end
    endtask

    integer received_goal = 0;
    initial begin : receive_loop
        forever begin
            receive_uart_byte(received[received_count % (3*MAX_BYTES)]);
            received_count = received_count + 1;
        end
    end

    task automatic run_capture(
        input integer frames,
        input [31:0] cap_id,
        input integer gbase
    );
        integer base;
        begin
            base = received_count;
            @(negedge clk); start = 1'b1;
            @(negedge clk); start = 1'b0;
            wait (busy);
            if (frames > 0) begin
                // Let the capturing flag cross into the stream domain first.
                #1000;
                send_frames(frames, gbase);
            end
            wait (done);
            @(posedge clk);
            verify_capture(base, frames, cap_id, gbase);
            if (captured_frames != frames)
                $fatal(1, "captured_frames %0d != %0d", captured_frames, frames);
        end
    endtask

    initial begin
        repeat (8) @(posedge clk);
        reset = 1'b0;
        repeat (8) @(posedge clk);
        if (FULL_WINDOW) begin
            run_capture(SNAPSHOT_FRAMES, INITIAL_ID, 0);
            if (capture_error) $fatal(1, "unexpected stream overrun");
            $display("PASS SRAM snapshot full 512 KiB window bytes=%0d bit-exact",
                     received_count);
        end else begin
            run_capture(SNAPSHOT_FRAMES, INITIAL_ID, 0);
            if (capture_error) $fatal(1, "unexpected stream overrun");
            // Back-to-back second capture, stream pattern continues.
            run_capture(SNAPSHOT_FRAMES, INITIAL_ID + 1, 3*SNAPSHOT_FRAMES);
            if (capture_error) $fatal(1, "unexpected stream overrun");
            // Stream stopped: timeout ends the capture with zero frames.
            run_capture(0, INITIAL_ID + 2, 0);
            if (capture_error) $fatal(1, "unexpected stream overrun");
            $display("PASS SRAM snapshot SNP1 round-trip: two back-to-back %0d-frame captures + timeout-empty header, CRCs verified",
                     SNAPSHOT_FRAMES);
        end
        $finish;
    end

    initial begin
        if (FULL_WINDOW) #2000000000;
        else             #200000000;
        $fatal(1, "SRAM snapshot timeout (%0d bytes)", received_count);
    end
endmodule

`default_nettype wire
