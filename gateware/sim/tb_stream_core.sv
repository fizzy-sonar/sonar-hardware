`timescale 1ns/1ps
`default_nettype none

// End-to-end proof of the continuous path. The clocks are asynchronous, TXE#
// includes a long initial stall plus pseudo-random stalls, and every emitted
// payload frame is checked against the frame actually accepted by the FIFO.
module tb_stream_core;
    localparam integer FIFO_DEPTH = 128;
    localparam integer FRAMES_TO_CHECK = 100;

    reg pdm_clk = 1'b0;
    reg ft_clk = 1'b0;
    reg pdm_reset = 1'b1;
    reg ft_reset = 1'b1;
    reg capture_enable = 1'b0;
    reg [11:0] pdm_data = 12'd0;
    reg ft_txe_n = 1'b1;
    wire overflow_sticky;
    wire capture_stopped;
    wire [7:0] ft_data;
    wire ft_data_oe, ft_wr_n, ft_rd_n, ft_oe_n, ft_siwu_n;

    reg [23:0] stimulus_frame = 24'h13579b;
    reg [23:0] accepted_frames [0:511];
    reg [7:0] received_header [0:31];
    reg [23:0] assembled_frame = 24'd0;
    reg [7:0] held_data = 8'd0;
    reg holding_stalled_byte = 1'b0;
    reg [15:0] lfsr = 16'h1ace;
    integer accepted_count = 0;
    integer output_count = 0;
    integer payload_byte = 0;
    integer emitted_frames = 0;
    integer initial_stall_cycles = 90;
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

    // Present the even bits before each rising edge and the matching odd bits
    // before its following falling edge. The standalone sampler test checks the
    // external edge mapping exhaustively; this test follows it through USB.
    always @(negedge pdm_clk) begin
        #1;
        stimulus_frame = {stimulus_frame[22:0],
                          stimulus_frame[23] ^ stimulus_frame[22] ^
                          stimulus_frame[21] ^ stimulus_frame[16]};
        for (line = 0; line < 12; line = line + 1)
            pdm_data[line] = stimulus_frame[2*line];
    end

    always @(posedge pdm_clk) begin
        if (dut.frame_fifo_i.wr_take) begin
            accepted_frames[accepted_count] = dut.frame_fifo_i.wr_data[23:0];
            accepted_count = accepted_count + 1;
        end
        #1;
        for (line = 0; line < 12; line = line + 1)
            pdm_data[line] = stimulus_frame[2*line+1];
    end

    // Roughly 75% ready after a deliberately long opening stall. This is still
    // faster on average than the scaled producer, so a lossless run must not
    // overflow even though individual stalls cross many FT clock cycles.
    always @(negedge ft_clk) begin
        if (ft_reset || !capture_enable) begin
            ft_txe_n <= 1'b1;
        end else if (initial_stall_cycles != 0) begin
            initial_stall_cycles = initial_stall_cycles - 1;
            ft_txe_n <= 1'b1;
        end else begin
            lfsr <= {lfsr[14:0], lfsr[15] ^ lfsr[13] ^ lfsr[12] ^ lfsr[10]};
            ft_txe_n <= (lfsr[1:0] == 2'b00);
        end
    end

    always @(posedge ft_clk) begin
        if (!ft_reset) begin
            if (!ft_rd_n || !ft_oe_n || !ft_siwu_n)
                $fatal(1, "write-only FT245 controls left inactive-safe state");
            if ((!ft_wr_n) !== ft_data_oe)
                $fatal(1, "FT245 WR# and data-output-enable disagree");

            if (dut.sink_valid && !dut.sink_ready) begin
                if (holding_stalled_byte && dut.sink_data !== held_data)
                    $fatal(1, "stream byte changed while downstream not ready");
                held_data = dut.sink_data;
                holding_stalled_byte = 1'b1;
            end else begin
                holding_stalled_byte = 1'b0;
            end

            if (!ft_txe_n && !ft_wr_n) begin
                if (output_count < 32) begin
                    received_header[output_count] = ft_data;
                end else begin
                    case (payload_byte)
                        0: assembled_frame[7:0] = ft_data;
                        1: assembled_frame[15:8] = ft_data;
                        2: begin
                            assembled_frame[23:16] = ft_data;
                            if (emitted_frames >= accepted_count)
                                $fatal(1, "emitted a frame the producer never accepted");
                            if (assembled_frame !== accepted_frames[emitted_frames])
                                $fatal(1, "payload frame %0d got %06x expected %06x",
                                       emitted_frames, assembled_frame,
                                       accepted_frames[emitted_frames]);
                            emitted_frames = emitted_frames + 1;
                        end
                    endcase
                    payload_byte = payload_byte == 2 ? 0 : payload_byte + 1;
                end
                output_count = output_count + 1;
            end
        end
    end

    initial begin
        repeat (4) @(posedge pdm_clk);
        @(negedge ft_clk);
        pdm_reset = 1'b0;
        ft_reset = 1'b0;
        repeat (8) @(posedge ft_clk);
        if (!ft_wr_n || ft_data_oe || output_count != 0)
            $fatal(1, "stream emitted before capture_enable");

        @(negedge ft_clk);
        capture_enable = 1'b1;
        wait (emitted_frames == FRAMES_TO_CHECK);

        if (overflow_sticky || capture_stopped)
            $fatal(1, "lossless backpressure case overflowed");
        if (accepted_count < FRAMES_TO_CHECK)
            $fatal(1, "consumer outran accepted-frame scoreboard");
        if ({received_header[0], received_header[1], received_header[2],
             received_header[3]} !== "SNR1" ||
            received_header[4] != 1 || received_header[5] != 32 ||
            {received_header[7], received_header[6]} != 16'h0007 ||
            {received_header[11], received_header[10], received_header[9],
             received_header[8]} != 32'd0 ||
            {received_header[19], received_header[18], received_header[17],
             received_header[16], received_header[15], received_header[14],
             received_header[13], received_header[12]} != 64'd0 ||
            {received_header[23], received_header[22], received_header[21],
             received_header[20]} != 3072000 ||
            {received_header[25], received_header[24]} != 16'd24 ||
            {received_header[27], received_header[26]} != 16'd12 ||
            {received_header[31], received_header[30], received_header[29],
             received_header[28]} != 32'd0)
            $fatal(1, "end-to-end SNR1 header mismatch");

        $display("PASS core SNR1 + %0d exact frames survive long/random TXE# stalls",
                 emitted_frames);
        $finish;
    end

    initial begin
        #200000;
        $fatal(1, "stream-core timeout accepted=%0d emitted=%0d bytes=%0d",
               accepted_count, emitted_frames, output_count);
    end
endmodule

`default_nettype wire
