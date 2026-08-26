`timescale 1ns/1ps
`default_nettype none

module tb_fifo_ft245;
    reg wr_clk = 1'b0;
    reg ft_clk = 1'b0;
    reg wr_reset = 1'b1;
    reg ft_reset = 1'b1;
    reg wr_en = 1'b0;
    reg [31:0] wr_data = 32'd0;
    wire wr_full;
    wire rd_empty;
    wire [31:0] rd_data;
    wire rd_valid;
    wire rd_en;
    wire [7:0] packed_data;
    wire packed_valid;
    wire packed_ready;
    reg ft_txe_n = 1'b1;
    wire [7:0] ft_data;
    wire ft_data_oe, ft_wr_n, ft_rd_n, ft_oe_n, ft_siwu_n;
    reg [7:0] received [0:63];
    integer received_count = 0;
    integer expected_byte;
    integer frame_number;

    always #15 wr_clk = ~wr_clk;
    always #5 ft_clk = ~ft_clk;

    async_fifo #(.WIDTH(32), .DEPTH(8)) fifo_i (
        .wr_clk(wr_clk), .wr_reset(wr_reset), .wr_en(wr_en),
        .wr_data(wr_data), .wr_full(wr_full),
        .rd_clk(ft_clk), .rd_reset(ft_reset), .rd_en(rd_en),
        .rd_data(rd_data), .rd_valid(rd_valid), .rd_empty(rd_empty)
    );

    frame_byte_packer packer_i (
        .clk(ft_clk), .reset(ft_reset), .fifo_empty(rd_empty),
        .fifo_rd_en(rd_en), .fifo_rd_data(rd_data),
        .fifo_rd_valid(rd_valid), .byte_data(packed_data),
        .byte_valid(packed_valid), .byte_ready(packed_ready)
    );

    ft245_sync_tx ft_i (
        .clk(ft_clk), .reset(ft_reset),
        .ft_txe_n(ft_txe_n), .byte_data(packed_data),
        .byte_valid(packed_valid), .byte_ready(packed_ready),
        .ft_data_out(ft_data), .ft_data_oe(ft_data_oe),
        .ft_wr_n(ft_wr_n), .ft_rd_n(ft_rd_n), .ft_oe_n(ft_oe_n),
        .ft_siwu_n(ft_siwu_n)
    );

    // FT245 BFM: accept on CLKOUT rising edge only when TXE# and WR# are low.
    always @(posedge ft_clk) begin
        if (!ft_reset && !ft_txe_n && !ft_wr_n) begin
            if (!ft_data_oe) $fatal(1, "data bus not driven during write");
            received[received_count] = ft_data;
            received_count = received_count + 1;
        end
        if (!ft_rd_n || !ft_oe_n || !ft_siwu_n)
            $fatal(1, "write-only FT245 controls left safe inactive state");
    end

    task automatic push_frame(input [23:0] frame);
        begin
            while (wr_full) @(posedge wr_clk);
            @(negedge wr_clk);
            wr_data = {8'h00, frame};
            wr_en = 1'b1;
            @(negedge wr_clk);
            wr_en = 1'b0;
        end
    endtask

    initial begin
        repeat (3) @(posedge ft_clk);
        wr_reset = 1'b0;
        ft_reset = 1'b0;

        // Alternate ready and backpressured intervals while asynchronous writes
        // continue. Every accepted byte must remain ordered and unique.
        fork
            begin
                repeat (5) @(negedge ft_clk);
                ft_txe_n = 1'b0;
                repeat (7) @(negedge ft_clk);
                ft_txe_n = 1'b1;
                repeat (11) @(negedge ft_clk);
                ft_txe_n = 1'b0;
                repeat (9) @(negedge ft_clk);
                ft_txe_n = 1'b1;
                repeat (4) @(negedge ft_clk);
                ft_txe_n = 1'b0;
            end
            begin
                for (frame_number = 0; frame_number < 8; frame_number = frame_number + 1)
                    push_frame({8'hc0 + frame_number[7:0],
                                8'h80 + frame_number[7:0],
                                8'h40 + frame_number[7:0]});
            end
        join

        wait (received_count == 24);
        for (frame_number = 0; frame_number < 8; frame_number = frame_number + 1) begin
            for (expected_byte = 0; expected_byte < 3; expected_byte = expected_byte + 1) begin
                case (expected_byte)
                    0: if (received[3*frame_number] !== 8'h40 + frame_number)
                           $fatal(1, "byte0 mismatch frame %0d", frame_number);
                    1: if (received[3*frame_number+1] !== 8'h80 + frame_number)
                           $fatal(1, "byte1 mismatch frame %0d", frame_number);
                    2: if (received[3*frame_number+2] !== 8'hc0 + frame_number)
                           $fatal(1, "byte2 mismatch frame %0d", frame_number);
                endcase
            end
        end
        $display("PASS async FIFO/packer/FT245 backpressure bytes=%0d", received_count);
        $finish;
    end

    initial begin
        #10000;
        $fatal(1, "FIFO/FT245 test timeout, received %0d bytes", received_count);
    end
endmodule

`default_nettype wire
