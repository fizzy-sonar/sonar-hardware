`timescale 1ns/1ps
`default_nettype none

// Raw capture path: IDDR -> 24-bit frame -> 64 KiB dual-clock FIFO -> bytes.
// No CIC, FIR, calibration, or other DSP exists on this primary path.
module pdm_stream_core #(
    parameter integer PDM_CLOCK_HZ = 3072000,
    parameter integer FIFO_DEPTH = 16384,
    parameter [31:0] INITIAL_CAPTURE_ID = 32'd0,
    parameter [63:0] FIRST_LOGICAL_FRAME = 64'd0
) (
    input  wire        pdm_clk_fb,
    input  wire        pdm_reset,
    input  wire [11:0] pdm_data,
    input  wire        capture_enable,
    output reg         overflow_sticky,
    output reg         capture_stopped,

    input  wire        ft_clk,
    input  wire        ft_reset,
    input  wire        ft_txe_n,
    output wire [7:0]  ft_data_out,
    output wire        ft_data_oe,
    output wire        ft_wr_n,
    output wire        ft_rd_n,
    output wire        ft_oe_n,
    output wire        ft_siwu_n
);
    wire [23:0] sampled_frame;
    wire        sampled_valid;
    wire        fifo_full;
    wire        fifo_empty;
    wire [31:0] fifo_rd_data;
    wire        fifo_rd_valid;
    wire        fifo_rd_en;

    (* ASYNC_REG = "TRUE" *) reg pdm_capture_meta;
    (* ASYNC_REG = "TRUE" *) reg pdm_capture_sync;
    reg pdm_capture_sync_d;
    (* ASYNC_REG = "TRUE" *) reg ft_capture_meta;
    (* ASYNC_REG = "TRUE" *) reg ft_capture_sync;
    reg ft_capture_sync_d;
    reg accepting;
    reg [31:0] next_capture_id;

    wire pdm_capture_active = pdm_capture_sync;
    wire pdm_capture_start = pdm_capture_sync && !pdm_capture_sync_d;
    wire ft_capture_active = ft_capture_sync;
    wire ft_capture_start = ft_capture_sync && !ft_capture_sync_d;
    wire pdm_path_reset = pdm_reset || !pdm_capture_active;
    wire ft_path_reset = ft_reset || !ft_capture_active;

    pdm_ddr_sampler sampler_i (
        .pdm_clk_fb(pdm_clk_fb),
        .reset(pdm_path_reset),
        .pdm_data(pdm_data),
        .frame_data(sampled_frame),
        .frame_valid(sampled_valid)
    );

    always @(posedge pdm_clk_fb) begin
        if (pdm_reset) begin
            pdm_capture_meta   <= 1'b0;
            pdm_capture_sync   <= 1'b0;
            pdm_capture_sync_d <= 1'b0;
            accepting       <= 1'b0;
            overflow_sticky <= 1'b0;
            capture_stopped <= 1'b0;
        end else begin
            pdm_capture_meta   <= capture_enable;
            pdm_capture_sync   <= pdm_capture_meta;
            pdm_capture_sync_d <= pdm_capture_sync;

            if (pdm_capture_start) begin
                // Overflow is sticky for the completed capture and clears only
                // when this explicit new capture begins (or on global reset).
                overflow_sticky <= 1'b0;
                capture_stopped <= 1'b0;
                accepting       <= 1'b1;
            end else if (!pdm_capture_active) begin
                accepting <= 1'b0;
            end else if (!capture_stopped) begin
                accepting <= 1'b1;
            end

            if (accepting && sampled_valid && fifo_full) begin
                overflow_sticky <= 1'b1;
                capture_stopped <= 1'b1;
                accepting       <= 1'b0;
            end
        end
    end

    // capture_enable crosses independently into the FT232H clock domain. Its
    // low interval is the explicit stream boundary and holds both local FIFO
    // ports reset; a new header therefore cannot splice into stale payload.
    always @(posedge ft_clk) begin
        if (ft_reset) begin
            ft_capture_meta   <= 1'b0;
            ft_capture_sync   <= 1'b0;
            ft_capture_sync_d <= 1'b0;
            next_capture_id   <= INITIAL_CAPTURE_ID;
        end else begin
            ft_capture_meta   <= capture_enable;
            ft_capture_sync   <= ft_capture_meta;
            ft_capture_sync_d <= ft_capture_sync;
            if (ft_capture_start)
                next_capture_id <= next_capture_id + 1'b1;
        end
    end

    async_fifo #(
        .WIDTH(32),
        .DEPTH(FIFO_DEPTH)
    ) frame_fifo_i (
        .wr_clk(pdm_clk_fb),
        .wr_reset(pdm_path_reset),
        .wr_en(accepting && sampled_valid && !fifo_full),
        .wr_data({8'h00, sampled_frame}),
        .wr_full(fifo_full),
        .rd_clk(ft_clk),
        .rd_reset(ft_path_reset),
        .rd_en(fifo_rd_en),
        .rd_data(fifo_rd_data),
        .rd_valid(fifo_rd_valid),
        .rd_empty(fifo_empty)
    );

    wire [7:0] payload_data;
    wire       payload_valid;
    wire       payload_ready;
    wire [7:0] header_data;
    wire       header_valid;
    wire       header_done;
    wire       sink_ready;
    wire [7:0] sink_data = header_done ? payload_data : header_data;
    wire       sink_valid = ft_capture_active &&
                            (header_done ? payload_valid : header_valid);

    frame_byte_packer packer_i (
        .clk(ft_clk),
        .reset(ft_path_reset),
        // Do not hide an extra prefetched frame behind a blocked header. The
        // documented elastic capacity stays exactly FIFO_DEPTH full frames.
        .fifo_empty(fifo_empty || !header_done),
        .fifo_rd_en(fifo_rd_en),
        .fifo_rd_data(fifo_rd_data),
        .fifo_rd_valid(fifo_rd_valid),
        .byte_data(payload_data),
        .byte_valid(payload_valid),
        .byte_ready(payload_ready)
    );

    stream_header #(
        .PDM_CLOCK_HZ(PDM_CLOCK_HZ)
    ) header_i (
        .clk(ft_clk),
        .reset(ft_path_reset),
        .start(ft_capture_start),
        .capture_id(next_capture_id),
        .first_logical_frame(FIRST_LOGICAL_FRAME),
        .byte_data(header_data),
        .byte_valid(header_valid),
        .byte_ready(sink_ready && !header_done),
        .done(header_done)
    );

    assign payload_ready = sink_ready && header_done;

    ft245_sync_tx ft245_i (
        .clk(ft_clk),
        .reset(ft_path_reset),
        .ft_txe_n(ft_txe_n),
        .byte_data(sink_data),
        .byte_valid(sink_valid),
        .byte_ready(sink_ready),
        .ft_data_out(ft_data_out),
        .ft_data_oe(ft_data_oe),
        .ft_wr_n(ft_wr_n),
        .ft_rd_n(ft_rd_n),
        .ft_oe_n(ft_oe_n),
        .ft_siwu_n(ft_siwu_n)
    );
endmodule

`default_nettype wire
