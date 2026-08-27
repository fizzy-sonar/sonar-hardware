`timescale 1ns/1ps
`default_nettype none

// FUNCTIONAL behavioral models of the Xilinx 7-series primitives used by
// pdm_ddr_sampler (IDDR) and pdm_clock_7series (MMCME2_BASE/BUFG/BUFGCTRL/
// ODDR). REVIEW-2026-08-26 S7: the previous stubs drove constant outputs,
// so no TB ever executed the synthesis branches. These models reproduce the
// primitives' FUNCTION (edge semantics, output frequencies, lock behavior)
// so Icarus runs the same logic the synthesized hardware runs. They do not
// model propagation timing or replace the UNISIM/xsim equivalence run and
// placed-timing proof that remain gated on the Vivado host (T-020 Log).

// ---------------------------------------------------------------------------
// IDDR, DDR_CLK_EDGE="SAME_EDGE_PIPELINED" (the only mode the design uses).
// Q1 = D sampled on rising edge k, Q2 = D sampled on the FOLLOWING falling
// edge k.5, both presented together after rising edge k+1 (UG471). That is
// exactly the pairing the portable `else` branch of pdm_ddr_sampler models,
// so the XILINX and portable branches emit identical frame sequences -
// tb_sampler_packer runs both and checks the same capture checksum.
// SRTYPE="SYNC" reset/set semantics (sampled at the clock edges).
// ---------------------------------------------------------------------------
module IDDR #(
    parameter DDR_CLK_EDGE = "OPPOSITE_EDGE",
    parameter INIT_Q1 = 1'b0,
    parameter INIT_Q2 = 1'b0,
    parameter SRTYPE = "SYNC"
) (
    output reg  Q1,
    output reg  Q2,
    input  wire C,
    input  wire CE,
    input  wire D,
    input  wire R,
    input  wire S
);
    reg d_rise = INIT_Q1;
    reg d_fall = INIT_Q2;

    initial begin
        Q1 = INIT_Q1;
        Q2 = INIT_Q2;
    end

    always @(posedge C) begin
        if (S)           d_rise <= 1'b1;
        else if (R)      d_rise <= INIT_Q1;
        else if (CE)     d_rise <= D;
    end
    always @(negedge C) begin
        if (S)           d_fall <= 1'b1;
        else if (R)      d_fall <= INIT_Q2;
        else if (CE)     d_fall <= D;
    end
    // Pipeline stage that aligns the falling-edge sample with the rising
    // sample on a single rising edge (the "PIPELINED" half of the mode).
    always @(posedge C) begin
        if (S)           begin Q1 <= 1'b1;    Q2 <= 1'b1;    end
        else if (R)      begin Q1 <= INIT_Q1; Q2 <= INIT_Q2; end
        else if (CE)     begin Q1 <= d_rise;  Q2 <= d_fall;  end
    end
endmodule

// ---------------------------------------------------------------------------
// MMCME2_BASE: functional clock generator. VCO frequency =
// CLKIN1 * CLKFBOUT_MULT_F / DIVCLK_DIVIDE; each CLKOUTn is the VCO divided
// (50% duty toggle generators, 1 ps resolution via the file timescale).
// LOCKED asserts 20 CLKIN1 cycles after RST release. CLKFBIN is ignored
// (no phase/det-skew modeling).
// ---------------------------------------------------------------------------
module MMCME2_BASE #(
    parameter BANDWIDTH = "OPTIMIZED",
    parameter real CLKIN1_PERIOD = 0.0,
    parameter integer DIVCLK_DIVIDE = 1,
    parameter real CLKFBOUT_MULT_F = 5.0,
    parameter real CLKOUT0_DIVIDE_F = 1.0,
    parameter integer CLKOUT1_DIVIDE = 1,
    parameter integer CLKOUT2_DIVIDE = 1
) (
    input  wire CLKIN1,
    input  wire CLKFBIN,
    input  wire RST,
    input  wire PWRDWN,
    output wire CLKFBOUT,
    output wire CLKOUT0,
    output wire CLKOUT1,
    output wire CLKOUT2,
    output reg  LOCKED
);
    localparam real HALF_VCO =
        CLKIN1_PERIOD * DIVCLK_DIVIDE / CLKFBOUT_MULT_F / 2.0;
    localparam real HALF0 = HALF_VCO * CLKOUT0_DIVIDE_F;
    localparam real HALF1 = HALF_VCO * CLKOUT1_DIVIDE;
    localparam real HALF2 = HALF_VCO * CLKOUT2_DIVIDE;

    reg vco  = 1'b0;
    reg out0 = 1'b0;
    reg out1 = 1'b0;
    reg out2 = 1'b0;
    integer lock_count = 0;

    initial LOCKED = 1'b0;

    wire run = !RST && !PWRDWN;
    always begin #(HALF_VCO); vco  = run ? ~vco  : 1'b0; end
    always begin #(HALF0);    out0 = run ? ~out0 : 1'b0; end
    always begin #(HALF1);    out1 = run ? ~out1 : 1'b0; end
    always begin #(HALF2);    out2 = run ? ~out2 : 1'b0; end

    always @(posedge CLKIN1) begin
        if (!run) begin
            LOCKED     <= 1'b0;
            lock_count <= 0;
        end else if (!LOCKED) begin
            if (lock_count == 19) LOCKED <= 1'b1;
            lock_count <= lock_count + 1;
        end
    end

    assign CLKFBOUT = vco;
    assign CLKOUT0  = out0;
    assign CLKOUT1  = out1;
    assign CLKOUT2  = out2;
endmodule

// ---------------------------------------------------------------------------
module BUFG (
    input  wire I,
    output wire O
);
    assign O = I;
endmodule

// ---------------------------------------------------------------------------
// BUFGCTRL: functional model of the glitch-free clock mux. The output is
// cut only while the current clock is low and joins the newly selected
// clock only while it is low, so the model never emits a runt pulse -
// matching the real macro's behavior when S0/S1 are registered in their
// own I0/I1 domains with a one-hot interlock (UG472; see
// pdm_clock_7series, REVIEW-2026-08-26 S8). Both selects low => output low.
// ---------------------------------------------------------------------------
module BUFGCTRL (
    input  wire I0,
    input  wire I1,
    input  wire S0,
    input  wire S1,
    input  wire CE0,
    input  wire CE1,
    input  wire IGNORE0,
    input  wire IGNORE1,
    output wire O
);
    reg sel  = 1'b0;   // 0 = I0 selected, 1 = I1
    reg gate = 1'b0;
    wire req     = (S1 && CE1) ? 1'b1 : (S0 && CE0) ? 1'b0 : sel;
    wire cur_clk = sel ? I1 : I0;
    wire req_clk = req ? I1 : I0;

    always @(negedge cur_clk or negedge req_clk) begin
        if (!(S0 || S1))
            gate <= 1'b0;
        else if (req != sel) begin
            if (!cur_clk) gate <= 1'b0;             // cut while current low
            if (!req_clk) begin                     // join while new low
                sel  <= req;
                gate <= 1'b1;
            end
        end else
            gate <= 1'b1;
    end

    assign O = gate ? req_clk : 1'b0;
endmodule

// ---------------------------------------------------------------------------
// ODDR, DDR_CLK_EDGE="SAME_EDGE" (the only mode the design uses): Q takes
// D1 on the rising edge of C and D2 on the following falling edge. With
// D2 tied to 0 and D1 a synchronized output-enable, every high pulse Q
// emits is a full half-period of C - tb_pdm_clock asserts no mic-clock
// edge is ever clipped. SRTYPE="SYNC" reset/set.
// ---------------------------------------------------------------------------
module ODDR #(
    parameter DDR_CLK_EDGE = "OPPOSITE_EDGE",
    parameter INIT = 1'b0,
    parameter SRTYPE = "SYNC"
) (
    input  wire C,
    input  wire CE,
    input  wire D1,
    input  wire D2,
    input  wire R,
    input  wire S,
    output wire Q
);
    // Single output reg driven at both edges (simulation model only): Q
    // takes the value of D1 AT the rising edge and D2 AT the falling edge,
    // which is what the silicon mux+FF pair does. (A combinational
    // "C ? qr : qf" form glitches zero-width when qr updates on the same
    // edge C rises.)
    reg q = INIT;

    always @(posedge C) begin
        if (S)       q <= 1'b1;
        else if (R)  q <= INIT;
        else if (CE) q <= D1;
    end
    always @(negedge C) begin
        if (S)       q <= 1'b1;
        else if (R)  q <= INIT;
        else if (CE) q <= D2;
    end

    assign Q = q;
endmodule

`default_nettype wire
