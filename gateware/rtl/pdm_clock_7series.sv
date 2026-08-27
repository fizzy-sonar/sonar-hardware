`timescale 1ns/1ps
`default_nettype none

// Artix-7 implementation scaffold for exact build-time PDM rates from Cmod A7's
// 12 MHz oscillator. Vivado-only primitives are isolated in this one file;
// gateware/sim/xilinx_7series_stubs.sv provides FUNCTIONAL models so Icarus
// executes this logic too (REVIEW-2026-08-26 S7). Placed clock-routing/timing
// proof and the UNISIM/xsim equivalence run are still gated on the Vivado host.
//
// Reset/CDC hardening (REVIEW-2026-08-26 S6 + S8):
//  - every fabric domain gets an async-assert/sync-release reset
//    synchronizer (reset_sync);
//  - buffer_oe (sysclk domain, from pdm_clock_startup) is synchronized into
//    the selected_clock domain before the ODDR D1, so an enable transition
//    can never be captured metastable onto the mic array clock. ODDR D2 is
//    constant 0, so Q falls only on a falling edge and rises only on a
//    sampling rising edge: every emitted high pulse is a full half-period
//    (tb_pdm_clock asserts no mic-clock edge is ever clipped);
//  - BUFGCTRL S0/S1 are registered in their OWN I0/I1 clock domains per
//    UG472, with a one-hot interlock (each select is gated by the other's
//    synchronized deassertion) so the mux switch is glitch-free by
//    construction. pdm_clock_startup changes select_ultrasonic only while
//    buffer_oe is low, and SWITCH_OFF_CYCLES exceeds the 2-flop OE-sync
//    latency at the slowest selected clock, so the output is verifiably
//    off before any select transition reaches the mux.
module pdm_clock_7series #(
    parameter integer PDM_CLOCK_HZ = 3072000
) (
    input  wire clk_12mhz,
    input  wire reset,
    input  wire buffer_oe,
    input  wire select_ultrasonic,
    output wire pdm_clk_src,
    output wire locked,
    // 48 MHz (768 MHz VCO / 16) for the SRAM snapshot controller and its UART;
    // one byte per three clocks = 16 MB/s, above the 14.4 MB/s ICS worst case.
    output wire sram_clk
);
    localparam integer ULTRA_DIVIDE =
        PDM_CLOCK_HZ == 3072000 ? 125 :
        PDM_CLOCK_HZ == 4800000 ? 80 : 0;
    wire mmcm_feedback;
    wire mmcm_feedback_buf;
    wire standard_2x_unbuf;
    wire ultrasonic_2x_unbuf;
    wire sram_clk_unbuf;
    wire standard_2x;
    wire ultrasonic_2x;
    reg [1:0] standard_divider;
    reg ultrasonic_divider;
    wire standard_clock_unbuf = standard_divider[1]; // 6.144 / 4 = 1.536 MHz
    wire ultrasonic_clock_unbuf = ultrasonic_divider; // selected 2x / 2
    wire standard_clock;
    wire ultrasonic_clock;
    wire selected_clock;
    wire reset_std2x;
    wire reset_ultra2x;
    wire reset_stdclk;
    wire reset_ultraclk;
    wire reset_selclk;

    initial begin
        if (ULTRA_DIVIDE == 0)
            $error("pdm_clock_7series supports only 3.072 and 4.8 MHz");
    end

    MMCME2_BASE #(
        .BANDWIDTH("OPTIMIZED"),
        .CLKIN1_PERIOD(83.333),
        .DIVCLK_DIVIDE(1),
        .CLKFBOUT_MULT_F(64.0),       // 12 MHz * 64 = 768 MHz VCO
        .CLKOUT0_DIVIDE_F(125.0),     // 6.144 MHz, then /4 standard
        .CLKOUT1_DIVIDE(ULTRA_DIVIDE), // 6.144 or 9.6 MHz, then /2
        .CLKOUT2_DIVIDE(16)            // 48 MHz SRAM snapshot/UART clock
    ) mmcm_i (
        .CLKIN1(clk_12mhz),
        .CLKFBIN(mmcm_feedback_buf),
        .RST(reset),                  // MMCM RST is a true async input
        .PWRDWN(1'b0),
        .CLKFBOUT(mmcm_feedback),
        .CLKOUT0(standard_2x_unbuf),
        .CLKOUT1(ultrasonic_2x_unbuf),
        .CLKOUT2(sram_clk_unbuf),
        .LOCKED(locked)
    );

    BUFG feedback_buf_i (.I(mmcm_feedback), .O(mmcm_feedback_buf));
    BUFG standard_2x_buf_i (.I(standard_2x_unbuf), .O(standard_2x));
    BUFG ultrasonic_2x_buf_i (.I(ultrasonic_2x_unbuf), .O(ultrasonic_2x));
    BUFG sram_buf_i (.I(sram_clk_unbuf), .O(sram_clk));

    // S6: per-domain async-assert/sync-release for every fabric clock here.
    reset_sync reset_std2x_i (
        .clk(standard_2x), .reset_async(reset || !locked),
        .reset_synced(reset_std2x));
    reset_sync reset_ultra2x_i (
        .clk(ultrasonic_2x), .reset_async(reset || !locked),
        .reset_synced(reset_ultra2x));
    reset_sync reset_stdclk_i (
        .clk(standard_clock), .reset_async(reset || !locked),
        .reset_synced(reset_stdclk));
    reset_sync reset_ultraclk_i (
        .clk(ultrasonic_clock), .reset_async(reset || !locked),
        .reset_synced(reset_ultraclk));
    reset_sync reset_selclk_i (
        .clk(selected_clock), .reset_async(reset || !locked),
        .reset_synced(reset_selclk));

    always @(posedge standard_2x) begin
        if (reset_std2x) standard_divider <= 2'd0;
        else             standard_divider <= standard_divider + 1'b1;
    end
    always @(posedge ultrasonic_2x) begin
        if (reset_ultra2x) ultrasonic_divider <= 1'b0;
        else               ultrasonic_divider <= ~ultrasonic_divider;
    end

    BUFG standard_buf_i (.I(standard_clock_unbuf), .O(standard_clock));
    BUFG ultrasonic_buf_i (.I(ultrasonic_clock_unbuf), .O(ultrasonic_clock));

    // S8: BUFGCTRL selects registered in their own input-clock domains with
    // a one-hot interlock (see the module header). Transient both-asserted
    // is impossible: S1 cannot rise until S0's fall has propagated into the
    // ultrasonic domain, and vice versa.
    (* ASYNC_REG = "TRUE" *) reg s0_meta = 1'b0;
    reg s0_sync = 1'b0;
    (* ASYNC_REG = "TRUE" *) reg s1_in_std_meta = 1'b0;
    reg s1_in_std = 1'b0;
    reg s0_sel = 1'b0;
    (* ASYNC_REG = "TRUE" *) reg s1_meta = 1'b0;
    reg s1_sync = 1'b0;
    (* ASYNC_REG = "TRUE" *) reg s0_in_ult_meta = 1'b0;
    reg s0_in_ult = 1'b0;
    reg s1_sel = 1'b0;
    always @(posedge standard_clock) begin
        if (reset_stdclk) begin
            s0_meta       <= 1'b0;
            s0_sync       <= 1'b0;
            s1_in_std_meta <= 1'b0;
            s1_in_std     <= 1'b0;
            s0_sel        <= 1'b0;
        end else begin
            s0_meta       <= !select_ultrasonic;
            s0_sync       <= s0_meta;
            s1_in_std_meta <= s1_sel;
            s1_in_std     <= s1_in_std_meta;
            s0_sel        <= s0_sync && !s1_in_std;
        end
    end
    always @(posedge ultrasonic_clock) begin
        if (reset_ultraclk) begin
            s1_meta       <= 1'b0;
            s1_sync       <= 1'b0;
            s0_in_ult_meta <= 1'b0;
            s0_in_ult     <= 1'b0;
            s1_sel        <= 1'b0;
        end else begin
            s1_meta       <= select_ultrasonic;
            s1_sync       <= s1_meta;
            s0_in_ult_meta <= s0_sel;
            s0_in_ult     <= s0_in_ult_meta;
            s1_sel        <= s1_sync && !s0_in_ult;
        end
    end

    BUFGCTRL clock_mux_i (
        .I0(standard_clock), .I1(ultrasonic_clock),
        .S0(s0_sel), .S1(s1_sel),
        .CE0(1'b1), .CE1(1'b1), .IGNORE0(1'b0), .IGNORE1(1'b0),
        .O(selected_clock)
    );

    // S8: buffer_oe synchronized into selected_clock before the ODDR D1.
    (* ASYNC_REG = "TRUE" *) reg oe_meta = 1'b0;
    reg oe_sync = 1'b0;
    always @(posedge selected_clock) begin
        if (reset_selclk) begin
            oe_meta <= 1'b0;
            oe_sync <= 1'b0;
        end else begin
            oe_meta <= buffer_oe;
            oe_sync <= oe_meta;
        end
    end

    ODDR #(.DDR_CLK_EDGE("SAME_EDGE"), .INIT(1'b0), .SRTYPE("SYNC")) output_i (
        .C(selected_clock), .CE(1'b1),
        .D1(oe_sync), .D2(1'b0), .R(reset), .S(1'b0), .Q(pdm_clk_src)
    );
endmodule

`default_nettype wire
