`timescale 1ns/1ps
`default_nettype none

module tb_stream_header;
    reg clk = 1'b0;
    reg reset = 1'b1;
    reg start = 1'b0;
    reg ready = 1'b0;
    reg [31:0] capture_id = 32'h78563412;
    reg [63:0] first_frame = 64'h0123456789abcdef;
    wire [7:0] data;
    wire valid, done;
    reg [7:0] received [0:31];
    integer count = 0;
    integer held_count;

    always #5 clk = ~clk;

    stream_header #(.PDM_CLOCK_HZ(4800000)) dut (
        .clk(clk), .reset(reset), .start(start),
        .capture_id(capture_id), .first_logical_frame(first_frame),
        .byte_data(data), .byte_valid(valid),
        .byte_ready(ready), .done(done)
    );

    always @(posedge clk)
        if (!reset && valid && ready) begin
            received[count] = data;
            count = count + 1;
        end

    initial begin
        repeat (3) @(posedge clk);
        @(negedge clk); reset = 1'b0; ready = 1'b1;
        repeat (3) @(posedge clk);
        if (valid || done || count != 0)
            $fatal(1, "SNR1 emitted before explicit capture start");
        @(negedge clk); start = 1'b1;
        @(negedge clk); start = 1'b0;
        repeat (9) @(negedge clk);
        ready = 1'b0;
        held_count = count;
        repeat (7) @(negedge clk);
        if (count != held_count) $fatal(1, "SNR1 advanced under backpressure");
        ready = 1'b1;
        wait (done);
        if (count != 32) $fatal(1, "SNR1 length %0d", count);
        if ({received[0],received[1],received[2],received[3]} !== "SNR1")
            $fatal(1, "bad SNR1 magic");
        if (received[4] != 1 || received[5] != 32 ||
            {received[7],received[6]} != 16'h0007)
            $fatal(1, "bad SNR1 version/flags");
        if ({received[11],received[10],received[9],received[8]} != 32'h78563412)
            $fatal(1, "bad capture id");
        if ({received[19],received[18],received[17],received[16],
             received[15],received[14],received[13],received[12]} !=
            64'h0123456789abcdef)
            $fatal(1, "bad first logical frame");
        if ({received[23],received[22],received[21],received[20]} != 4800000)
            $fatal(1, "bad stream PDM rate");
        if (received[24] != 24 || received[25] != 0 ||
            received[26] != 12 || received[27] != 0)
            $fatal(1, "bad stream geometry");
        if ({received[31],received[30],received[29],received[28]} != 32'd0)
            $fatal(1, "non-zero SNR1 reserved field");

        // A later capture gets exactly one independently latched header.
        count = 0;
        capture_id = 32'h01020304;
        first_frame = 64'hf0e0d0c0b0a09080;
        @(negedge clk); start = 1'b1;
        @(negedge clk); start = 1'b0;
        wait (done);
        if (count != 32 ||
            {received[11],received[10],received[9],received[8]} != 32'h01020304 ||
            {received[19],received[18],received[17],received[16],
             received[15],received[14],received[13],received[12]} !=
            64'hf0e0d0c0b0a09080)
            $fatal(1, "second capture header was not independently latched");
        $display("PASS SNR1 exact 32-byte headers start once per capture and hold under backpressure");
        $finish;
    end
endmodule

`default_nettype wire
