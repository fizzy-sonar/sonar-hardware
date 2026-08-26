`timescale 1ns/1ps
`default_nettype none

module tb_uart_snapshot;
    localparam integer CLOCK_PERIOD_NS = 10;
    localparam integer CLKS_PER_BIT = 8;
    localparam integer FRAMES = 4;
    localparam integer TOTAL_BYTES = 48 + 3*FRAMES;
    reg clk = 1'b0;
    reg reset = 1'b1;
    reg start = 1'b0;
    reg [23:0] frame_data = 24'd0;
    reg frame_valid = 1'b0;
    wire frame_ready;
    wire uart_line;
    wire busy;
    wire done;
    reg [7:0] received [0:TOTAL_BYTES-1];
    integer received_count = 0;
    integer i;
    reg [31:0] crc;

    always #(CLOCK_PERIOD_NS/2) clk = ~clk;

    uart_snapshot #(
        .PDM_CLOCK_HZ(3072000),
        .FRAME_COUNT(FRAMES),
        .CLKS_PER_BIT(CLKS_PER_BIT),
        .CAPTURE_ID(32'h12345678)
    ) dut (
        .clk(clk), .reset(reset), .start(start),
        .frame_data(frame_data), .frame_valid(frame_valid),
        .frame_ready(frame_ready), .uart_tx_o(uart_line),
        .busy(busy), .done(done)
    );

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
            #(CLOCK_PERIOD_NS * CLKS_PER_BIT / 2);
            if (uart_line !== 1'b0) $fatal(1, "bad UART start bit");
            for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1) begin
                #(CLOCK_PERIOD_NS * CLKS_PER_BIT);
                value[bit_number] = uart_line;
            end
            #(CLOCK_PERIOD_NS * CLKS_PER_BIT);
            if (uart_line !== 1'b1) $fatal(1, "bad UART stop bit");
        end
    endtask

    task automatic send_frame(input [23:0] value);
        begin
            wait (frame_ready);
            @(negedge clk);
            frame_data = value;
            frame_valid = 1'b1;
            @(negedge clk);
            frame_valid = 1'b0;
        end
    endtask

    initial begin : receive_loop
        while (received_count < TOTAL_BYTES) begin
            receive_uart_byte(received[received_count]);
            received_count = received_count + 1;
        end
    end

    initial begin
        repeat (4) @(posedge clk);
        reset = 1'b0;
        @(negedge clk); start = 1'b1;
        @(negedge clk); start = 1'b0;
        send_frame(24'h030201);
        send_frame(24'h131211);
        send_frame(24'h232221);
        send_frame(24'h333231);

        wait (done);
        if (received_count != TOTAL_BYTES)
            $fatal(1, "snapshot ended after %0d/%0d bytes", received_count, TOTAL_BYTES);
        if ({received[0], received[1], received[2], received[3]} !== "SNP1")
            $fatal(1, "bad SNP1 magic");
        if (received[4] != 1 || received[5] != 48)
            $fatal(1, "bad SNP1 version/header size");
        if ({received[11],received[10],received[9],received[8]} != 32'h12345678)
            $fatal(1, "bad capture id");
        if ({received[23],received[22],received[21],received[20]} != 3072000)
            $fatal(1, "bad PDM clock");
        if (received[24] != 24 || received[26] != 12 || received[28] != FRAMES)
            $fatal(1, "bad geometry/count fields");
        for (i = 0; i < 3*FRAMES; i = i + 1)
            if (received[48+i] !== ((i/3)*16 + (i%3) + 1))
                $fatal(1, "payload byte %0d mismatch: %02x", i, received[48+i]);

        crc = 32'hffffffff;
        for (i = 48; i < TOTAL_BYTES; i = i + 1) crc = crc32_byte(crc, received[i]);
        crc = ~crc;
        if ({received[39],received[38],received[37],received[36]} !== crc)
            $fatal(1, "payload CRC mismatch");
        crc = 32'hffffffff;
        for (i = 0; i < 40; i = i + 1) crc = crc32_byte(crc, received[i]);
        crc = ~crc;
        if ({received[43],received[42],received[41],received[40]} !== crc)
            $fatal(1, "header CRC mismatch");
        $display("PASS UART SNP1 snapshot bytes=%0d CRCs verified", received_count);
        $finish;
    end

    initial begin
        #200000;
        $fatal(1, "UART snapshot timeout (%0d bytes)", received_count);
    end
endmodule

`default_nettype wire
