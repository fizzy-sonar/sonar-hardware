`timescale 1ns/1ps
`default_nettype none

// Force the elastic FIFO to fill behind TXE# and prove the failure contract:
// latch status, stop accepting forever for that capture, then drain exactly the
// already accepted prefix. A low/high capture boundary must retain old status
// until the next capture and then emit exactly one new header with sequence +1.
module tb_overflow_stop;
    localparam integer FIFO_DEPTH = 8;
    localparam integer FIRST_STREAM_BYTES = 32 + 3 * FIFO_DEPTH;

    reg pdm_clk = 1'b0;
    reg ft_clk = 1'b0;
    reg pdm_reset = 1'b1;
    reg ft_reset = 1'b1;
    reg capture_enable = 1'b0;
    reg [11:0] pdm_data = 12'd0;
    reg ft_txe_n = 1'b1;
    wire overflow_sticky, capture_stopped;
    wire [7:0] ft_data;
    wire ft_data_oe, ft_wr_n, ft_rd_n, ft_oe_n, ft_siwu_n;

    reg [23:0] stimulus_frame = 24'h2468ac;
    reg [23:0] accepted_frames [0:FIFO_DEPTH-1];
    reg [7:0] received [0:255];
    reg [23:0] assembled = 24'd0;
    integer accepted_count = 0;
    integer received_count = 0;
    integer accepted_after_stop;
    integer second_header_offset;
    integer frame_number;
    integer line;

    always #50 pdm_clk = ~pdm_clk;
    always #5 ft_clk = ~ft_clk;

    pdm_stream_core #(
        .PDM_CLOCK_HZ(3072000),
        .FIFO_DEPTH(FIFO_DEPTH)
    ) dut (
        .pdm_clk_fb(pdm_clk), .pdm_reset(pdm_reset), .pdm_data(pdm_data),
        .capture_enable(capture_enable), .overflow_sticky(overflow_sticky),
        .capture_stopped(capture_stopped), .ft_clk(ft_clk), .ft_reset(ft_reset),
        .ft_txe_n(ft_txe_n), .ft_data_out(ft_data),
        .ft_data_oe(ft_data_oe), .ft_wr_n(ft_wr_n), .ft_rd_n(ft_rd_n),
        .ft_oe_n(ft_oe_n), .ft_siwu_n(ft_siwu_n)
    );

    always @(negedge pdm_clk) begin
        #1;
        stimulus_frame = {stimulus_frame[22:0],
                          stimulus_frame[23] ^ stimulus_frame[22] ^
                          stimulus_frame[21] ^ stimulus_frame[16]};
        for (line = 0; line < 12; line = line + 1)
            pdm_data[line] = stimulus_frame[2*line];
    end

    always @(posedge pdm_clk) begin
        if (dut.frame_fifo_i.wr_take && accepted_count < FIFO_DEPTH) begin
            accepted_frames[accepted_count] = dut.frame_fifo_i.wr_data[23:0];
            accepted_count = accepted_count + 1;
        end
        #1;
        for (line = 0; line < 12; line = line + 1)
            pdm_data[line] = stimulus_frame[2*line+1];
    end

    always @(posedge ft_clk) begin
        if (!ft_reset) begin
            if (!ft_rd_n || !ft_oe_n || !ft_siwu_n)
                $fatal(1, "write-only FT245 controls left inactive-safe state");
            if (!ft_txe_n && !ft_wr_n) begin
                if (!ft_data_oe) $fatal(1, "FT data not driven with WR# low");
                received[received_count] = ft_data;
                received_count = received_count + 1;
            end
        end
    end

    task automatic check_header(input integer base, input [31:0] capture_id);
        begin
            if ({received[base], received[base+1], received[base+2],
                 received[base+3]} !== "SNR1" ||
                received[base+4] != 1 || received[base+5] != 32 ||
                {received[base+7], received[base+6]} != 16'h0007 ||
                {received[base+11], received[base+10], received[base+9],
                 received[base+8]} != capture_id ||
                {received[base+19], received[base+18], received[base+17],
                 received[base+16], received[base+15], received[base+14],
                 received[base+13], received[base+12]} != 64'd0 ||
                {received[base+23], received[base+22], received[base+21],
                 received[base+20]} != 3072000 ||
                {received[base+25], received[base+24]} != 16'd24 ||
                {received[base+27], received[base+26]} != 16'd12 ||
                {received[base+31], received[base+30], received[base+29],
                 received[base+28]} != 32'd0)
                $fatal(1, "bad SNR1 header at offset %0d", base);
        end
    endtask

    initial begin
        repeat (4) @(posedge pdm_clk);
        @(negedge ft_clk);
        pdm_reset = 1'b0;
        ft_reset = 1'b0;
        capture_enable = 1'b1;

        wait (capture_stopped);
        if (!overflow_sticky)
            $fatal(1, "overflow stop lacked sticky status");
        if (accepted_count != FIFO_DEPTH)
            $fatal(1, "overflow accepted %0d frames, expected exact capacity %0d",
                   accepted_count, FIFO_DEPTH);
        accepted_after_stop = accepted_count;
        repeat (8) @(posedge pdm_clk);
        if (!capture_stopped || !overflow_sticky ||
            accepted_count != accepted_after_stop)
            $fatal(1, "capture accepted data or cleared status after overflow");
        if (received_count != 0)
            $fatal(1, "bytes escaped while TXE# was continuously high");

        // Resume the host: only the canonical header and accepted prefix may
        // drain. No later sampled frame is allowed to appear.
        @(negedge ft_clk); ft_txe_n = 1'b0;
        wait (received_count == FIRST_STREAM_BYTES);
        repeat (20) @(posedge ft_clk);
        if (received_count != FIRST_STREAM_BYTES)
            $fatal(1, "overflowed capture emitted data beyond accepted prefix");
        check_header(0, 32'd0);
        for (frame_number = 0; frame_number < FIFO_DEPTH;
             frame_number = frame_number + 1) begin
            assembled = {received[32 + 3*frame_number + 2],
                         received[32 + 3*frame_number + 1],
                         received[32 + 3*frame_number]};
            if (assembled !== accepted_frames[frame_number])
                $fatal(1, "drained frame %0d got %06x expected %06x",
                       frame_number, assembled, accepted_frames[frame_number]);
        end

        // Low is an explicit abort/fresh-stream boundary. Old overflow remains
        // observable throughout the low interval, then clears at the next PDM
        // capture start. FT emits one new header with incremented capture ID.
        @(negedge ft_clk); capture_enable = 1'b0;
        repeat (8) @(posedge pdm_clk);
        if (!overflow_sticky || !capture_stopped)
            $fatal(1, "sticky overflow cleared before a new capture began");
        second_header_offset = received_count;
        repeat (8) @(posedge ft_clk);
        if (received_count != second_header_offset)
            $fatal(1, "stream wrote while capture_enable was low");

        @(negedge ft_clk); capture_enable = 1'b1;
        wait (received_count >= second_header_offset + 32);
        check_header(second_header_offset, 32'd1);
        wait (!overflow_sticky && !capture_stopped);

        $display("PASS overflow stops and drains exact %0d-frame prefix; capture restart increments SNR1 ID",
                 accepted_after_stop);
        $finish;
    end

    initial begin
        #50000;
        $fatal(1, "overflow-stop timeout accepted=%0d received=%0d",
               accepted_count, received_count);
    end
endmodule

`default_nettype wire
