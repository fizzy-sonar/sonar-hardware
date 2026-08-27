`timescale 1ns/1ps
`default_nettype none

// Turn twelve edge-shared PDM wires into the contract's 24-bit logical frame.
// frame_data[2*i] is the SELECT-low microphone sampled on a rising edge.
// frame_data[2*i+1] is SELECT-high sampled on the following falling edge.
// A complete frame is presented on the next rising edge.
module pdm_ddr_sampler #(
    parameter integer DATA_LINES = 12
) (
    input  wire                    pdm_clk_fb,
    input  wire                    reset,
    input  wire [DATA_LINES-1:0]   pdm_data,
    output reg  [2*DATA_LINES-1:0] frame_data,
    output reg                     frame_valid
);
    integer i;

`ifdef XILINX
    // SAME_EDGE_PIPELINED makes the two samples from one external clock
    // period available together - one full clock AFTER the sampled edge
    // pair (Q1 = rising k, Q2 = falling k.5, both after rising k+1). The
    // functional IDDR model in sim/xilinx_7series_stubs.sv implements
    // exactly that latency (REVIEW-2026-08-26 S7), and pipeline_valid is
    // two stages deep to match, so the first frame_valid marks a REAL
    // sampled pair. tb_sampler_packer runs this branch under -DXILINX and
    // the portable branch without it; both must emit identical frames.
    wire [DATA_LINES-1:0] rising_samples;
    wire [DATA_LINES-1:0] falling_samples;
    reg [1:0]             pipeline_valid;

    genvar bit_index;
    generate
        for (bit_index = 0; bit_index < DATA_LINES; bit_index = bit_index + 1) begin : gen_iddr
            IDDR #(
                .DDR_CLK_EDGE("SAME_EDGE_PIPELINED"),
                .INIT_Q1(1'b0),
                .INIT_Q2(1'b0),
                .SRTYPE("SYNC")
            ) iddr_i (
                .Q1(rising_samples[bit_index]),
                .Q2(falling_samples[bit_index]),
                .C(pdm_clk_fb),
                .CE(1'b1),
                .D(pdm_data[bit_index]),
                .R(reset),
                .S(1'b0)
            );
        end
    endgenerate

    always @(posedge pdm_clk_fb) begin
        if (reset) begin
            frame_data     <= {2*DATA_LINES{1'b0}};
            frame_valid    <= 1'b0;
            pipeline_valid <= 2'b00;
        end else begin
            for (i = 0; i < DATA_LINES; i = i + 1) begin
                frame_data[2*i]   <= rising_samples[i];
                frame_data[2*i+1] <= falling_samples[i];
            end
            frame_valid    <= pipeline_valid[1];
            pipeline_valid <= {pipeline_valid[0], 1'b1};
        end
    end
`else
    // Simulator-first behavioral IDDR. Keeping this model explicit makes the
    // edge contract reviewable without a Xilinx UNISIM installation.
    reg [DATA_LINES-1:0] rising_latch;
    reg [DATA_LINES-1:0] falling_latch;
    reg                  have_rising;
    reg                  have_falling;

    always @(negedge pdm_clk_fb) begin
        if (reset) begin
            falling_latch <= {DATA_LINES{1'b0}};
            have_falling  <= 1'b0;
        end else begin
            falling_latch <= pdm_data;
            have_falling  <= 1'b1;
        end
    end

    always @(posedge pdm_clk_fb) begin
        if (reset) begin
            rising_latch <= {DATA_LINES{1'b0}};
            have_rising  <= 1'b0;
            frame_data   <= {2*DATA_LINES{1'b0}};
            frame_valid  <= 1'b0;
        end else begin
            frame_valid <= have_rising && have_falling;
            if (have_rising && have_falling) begin
                for (i = 0; i < DATA_LINES; i = i + 1) begin
                    frame_data[2*i]   <= rising_latch[i];
                    frame_data[2*i+1] <= falling_latch[i];
                end
            end
            rising_latch <= pdm_data;
            have_rising  <= 1'b1;
        end
    end
`endif
endmodule

`default_nettype wire
