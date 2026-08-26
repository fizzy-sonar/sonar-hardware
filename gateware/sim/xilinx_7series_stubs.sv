`timescale 1ns/1ps
`default_nettype none

// Port-compatible compile stubs only. They let portable Icarus elaboration cover
// the XILINX IDDR/MMCM/ODDR branches and the complete top-level wiring. They do
// not model primitive timing or substitute for UNISIM/xsim and placed Vivado.
module IDDR #(
    parameter DDR_CLK_EDGE = "OPPOSITE_EDGE",
    parameter INIT_Q1 = 1'b0,
    parameter INIT_Q2 = 1'b0,
    parameter SRTYPE = "SYNC"
) (
    output wire Q1,
    output wire Q2,
    input  wire C,
    input  wire CE,
    input  wire D,
    input  wire R,
    input  wire S
);
    assign Q1 = INIT_Q1;
    assign Q2 = INIT_Q2;
endmodule

module MMCME2_BASE #(
    parameter BANDWIDTH = "OPTIMIZED",
    parameter real CLKIN1_PERIOD = 0.0,
    parameter integer DIVCLK_DIVIDE = 1,
    parameter real CLKFBOUT_MULT_F = 5.0,
    parameter real CLKOUT0_DIVIDE_F = 1.0,
    parameter integer CLKOUT1_DIVIDE = 1
) (
    input  wire CLKIN1,
    input  wire CLKFBIN,
    input  wire RST,
    input  wire PWRDWN,
    output wire CLKFBOUT,
    output wire CLKOUT0,
    output wire CLKOUT1,
    output wire LOCKED
);
    assign CLKFBOUT = 1'b0;
    assign CLKOUT0 = 1'b0;
    assign CLKOUT1 = 1'b0;
    assign LOCKED = 1'b0;
endmodule

module BUFG (
    input  wire I,
    output wire O
);
    assign O = I;
endmodule

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
    assign O = S1 ? I1 : (S0 ? I0 : 1'b0);
endmodule

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
    assign Q = INIT;
endmodule

`default_nettype wire
