`timescale 1ns/1ps
`default_nettype none

// Artix-7 implementation scaffold for exact build-time PDM rates from Cmod A7's
// 12 MHz oscillator. Vivado-only primitives are isolated in this one file.
// Placed clock-routing/timing proof is intentionally still gated on the host.
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
        .RST(reset),
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

    always @(posedge standard_2x) begin
        if (reset || !locked) standard_divider <= 2'd0;
        else                  standard_divider <= standard_divider + 1'b1;
    end
    always @(posedge ultrasonic_2x) begin
        if (reset || !locked) ultrasonic_divider <= 1'b0;
        else                  ultrasonic_divider <= ~ultrasonic_divider;
    end

    BUFG standard_buf_i (.I(standard_clock_unbuf), .O(standard_clock));
    BUFG ultrasonic_buf_i (.I(ultrasonic_clock_unbuf), .O(ultrasonic_clock));

    // The control state machine changes S0/S1 only while the external clock
    // buffer is disabled. Vivado must still verify the generated clocks/CDC.
    BUFGCTRL clock_mux_i (
        .I0(standard_clock), .I1(ultrasonic_clock),
        .S0(!select_ultrasonic), .S1(select_ultrasonic),
        .CE0(1'b1), .CE1(1'b1), .IGNORE0(1'b0), .IGNORE1(1'b0),
        .O(selected_clock)
    );

    ODDR #(.DDR_CLK_EDGE("SAME_EDGE"), .INIT(1'b0), .SRTYPE("SYNC")) output_i (
        .C(selected_clock), .CE(1'b1),
        .D1(buffer_oe), .D2(1'b0), .R(reset), .S(1'b0), .Q(pdm_clk_src)
    );
endmodule

`default_nettype wire
