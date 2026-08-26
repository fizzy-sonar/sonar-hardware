`timescale 1ns/1ps
`default_nettype none

// Hardware integration scaffold. Exact PACKAGE_PIN assignments intentionally do
// not exist until T-011 publishes orchestration/pinmap.md.
module sonar_top #(
    parameter integer PDM_CLOCK_HZ = 3072000
) (
    input  wire        sys_clk_12mhz,
    input  wire        reset,
    input  wire        mic_power_good,
    input  wire        wake_request,
    output wire        pdm_clk_src,
    output wire        pdm_clk_buffer_oe,
    input  wire        pdm_clk_fb,
    input  wire [11:0] pdm_data,

    input  wire        ft_clk,
    input  wire        ft_txe_n,
    inout  wire [7:0]  ft_data,
    output wire        ft_wr_n,
    output wire        ft_rd_n,
    output wire        ft_oe_n,
    output wire        ft_siwu_n,

    input  wire        tx_start,
    input  wire [23:0] tx_phase_increment,
    input  wire signed [31:0] tx_phase_increment_delta_q8,
    input  wire [7:0]  tx_amplitude,
    input  wire [31:0] tx_burst_cycles,
    output wire        tx_a,
    output wire        tx_b,
    output wire        capture_overflow,
    output wire        capture_stopped,
    output wire        tx_limit_fault
);
    wire select_ultrasonic;
    wire discard_samples;
    wire capture_enable;
    wire clocks_locked;
    wire [7:0] ft_data_out;
    wire ft_data_oe;
    wire tx_active;

    pdm_clock_startup startup_i (
        .clk(sys_clk_12mhz), .reset(reset),
        .power_good(mic_power_good && clocks_locked),
        .wake_request(wake_request), .buffer_oe(pdm_clk_buffer_oe),
        .select_ultrasonic(select_ultrasonic),
        .discard_samples(discard_samples), .capture_enable(capture_enable)
    );

    pdm_clock_7series #(.PDM_CLOCK_HZ(PDM_CLOCK_HZ)) clocks_i (
        .clk_12mhz(sys_clk_12mhz), .reset(reset),
        .buffer_oe(pdm_clk_buffer_oe),
        .select_ultrasonic(select_ultrasonic),
        .pdm_clk_src(pdm_clk_src), .locked(clocks_locked)
    );

    pdm_stream_core #(.PDM_CLOCK_HZ(PDM_CLOCK_HZ)) stream_i (
        // capture_enable is the coordinated per-capture reset/boundary. Keep
        // pdm_reset global so overflow survives sleep until reset/new capture.
        .pdm_clk_fb(pdm_clk_fb), .pdm_reset(reset),
        .pdm_data(pdm_data), .capture_enable(capture_enable),
        .overflow_sticky(capture_overflow), .capture_stopped(capture_stopped),
        .ft_clk(ft_clk), .ft_reset(reset), .ft_txe_n(ft_txe_n),
        .ft_data_out(ft_data_out), .ft_data_oe(ft_data_oe),
        .ft_wr_n(ft_wr_n), .ft_rd_n(ft_rd_n), .ft_oe_n(ft_oe_n),
        .ft_siwu_n(ft_siwu_n)
    );
    assign ft_data = ft_data_oe ? ft_data_out : 8'hzz;

    // Conservative generic bounds; T-013 must narrow these to the chosen driver,
    // transducer, supply, and waveform before hardware TX is enabled.
    tx_nco_pwm #(
        .PHASE_BITS(24),
        .MAX_PHASE_INCREMENT(24'd55924), // <=40 kHz at 12 MHz
        .MAX_AMPLITUDE(8'd128),
        .MAX_BURST_CYCLES(32'd120000)    // <=10 ms at 12 MHz
    ) tx_i (
        .clk(sys_clk_12mhz), .reset(reset), .start(tx_start),
        .phase_increment(tx_phase_increment),
        .phase_increment_delta(tx_phase_increment_delta_q8),
        .amplitude(tx_amplitude),
        .burst_cycles(tx_burst_cycles), .tx_a(tx_a), .tx_b(tx_b),
        .active(tx_active), .limit_fault(tx_limit_fault)
    );
endmodule

`default_nettype wire
