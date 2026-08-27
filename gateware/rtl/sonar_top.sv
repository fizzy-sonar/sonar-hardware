`timescale 1ns/1ps
`default_nettype none

// Hardware top for the Cmod A7-35T. The port list is an exact bijection with
// the ACTIVE get_ports of constraints/sonar_cmod_a7.xdc (the commented DNP
// RMII block excluded); sim/check_ports.py enforces this in `make test`.
// Port names are the pinmap net names of orchestration/pinmap.md (authoritative;
// XDC generated from it by T-011, SRAM/UART section appended from the Digilent
// master XDC). Do not add ports here without a pinmap/XDC pin.
//
// Control-plane note: the pinmap has no spare DIP pins, so the simulator-only
// scaffolding knobs (mic_power_good, wake_request, TX start/increments/
// amplitude/burst, capture status pins) are tied off internally until a real
// control plane exists (ticket Log, remaining item). TX is permanently idle:
// tx_nco_pwm never starts, tx_en/tx_ph stay low, and tx_nsleep holds the
// DRV8876 asleep (its nSLEEP has an internal pull-down; driving it low is the
// safe default).
//
// TX mapping (authoritative: orchestration/tx-limits.md, T-013):
//   tx_en  = DRV8876 EN/IN1 = tx_a (positive half-cycle PWM pulse)
//   tx_ph  = DRV8876 PH/IN2 = tx_b (negative half-cycle PWM pulse)
//   tx_pmode = 1 -> PMODE high selects the IN1/IN2 (PWM) interface mode that
//                 matches the complementary tx_a/tx_b drive (CP-C datasheet
//                 verify item, does not affect the safety envelope)
//   tx_nsleep = tx_active (bridge sleeps unless a burst is running)
//   tx_nfault = open-drain fault input (10k pull-up R170 on the TX sheet),
//               mirrored on led0_r for bring-up.
//
// Debug LED mapping (on-module, active-high):
//   led[0] = SRAM snapshot busy      led[1] = SRAM snapshot error
//   led0_b = capture_overflow        led0_g = capture_stopped
//   led0_r = tx_limit_fault | ~tx_nfault
// Buttons (on-module, active-high): btn[0] = snapshot trigger, btn[1] = manual
// reset (async assert, synchronous use inside the clocked always blocks).
module sonar_top #(
    parameter integer PDM_CLOCK_HZ = 3072000
) (
    input  wire        sysclk,

    input  wire [1:0]  btn,
    output wire [1:0]  led,
    output wire        led0_b,
    output wire        led0_g,
    output wire        led0_r,

    output wire        pdm_clk_src,
    output wire        pdm_clk_en,
    input  wire        pdm_clk_fb,
    input  wire [11:0] pdm_d,

    input  wire        ft_clkout,
    input  wire        ft_rxf_n,       // reserved: RX path/control plane (unused)
    input  wire        ft_txe_n,
    inout  wire [7:0]  ft_d,
    output wire        ft_wr_n,
    output wire        ft_rd_n,
    output wire        ft_oe_n,

    output wire        tx_en,
    output wire        tx_ph,
    output wire        tx_nsleep,
    input  wire        tx_nfault,
    output wire        tx_pmode,

    // On-module IS61WV5128BLL-10BLI 512 KiB SRAM (dedicated bank-14 pins).
    output wire [18:0] MemAdr,
    inout  wire [7:0]  MemDB,
    output wire        RamCEn,
    output wire        RamOEn,
    output wire        RamWEn,

    // D012 snapshot drain over the Cmod's own USB-UART bridge (FT2232HQ RXD).
    output wire        uart_rxd_out
);
    // No dedicated reset pin exists in the pinmap: power-on reset holds for
    // 16 sysclk cycles after configuration (FF INIT, works in Icarus and on
    // 7-series), and btn[1] is the manual reset.
    reg [15:0] por_shift = 16'hFFFF;
    always @(posedge sysclk) por_shift <= {por_shift[14:0], 1'b0};
    wire reset = por_shift[15] | btn[1];

    wire select_ultrasonic;
    wire discard_samples;
    wire capture_enable;
    wire clocks_locked;
    wire [7:0] ft_d_out;
    wire ft_d_oe;
    wire tx_a;
    wire tx_b;
    wire tx_active;
    wire tx_limit_fault;
    wire capture_overflow;
    wire capture_stopped;
    wire sram_clk;
    wire [23:0] tap_frame_data;
    wire        tap_frame_valid;
    wire        snapshot_busy;
    wire        snapshot_done;
    wire        snapshot_error;

    // Control plane TODO: no external power-good/wake pins exist yet, so the
    // startup controller assumes the array is powered and runs its
    // 50 ms standard-mode / clock-off / 10 ms ultrasonic sequence once.
    pdm_clock_startup startup_i (
        .clk(sysclk), .reset(reset),
        .power_good(1'b1 && clocks_locked),
        .wake_request(1'b1), .buffer_oe(pdm_clk_en),
        .select_ultrasonic(select_ultrasonic),
        .discard_samples(discard_samples), .capture_enable(capture_enable)
    );

    pdm_clock_7series #(.PDM_CLOCK_HZ(PDM_CLOCK_HZ)) clocks_i (
        .clk_12mhz(sysclk), .reset(reset),
        .buffer_oe(pdm_clk_en),
        .select_ultrasonic(select_ultrasonic),
        .pdm_clk_src(pdm_clk_src), .locked(clocks_locked),
        .sram_clk(sram_clk)
    );

    pdm_stream_core #(.PDM_CLOCK_HZ(PDM_CLOCK_HZ)) stream_i (
        // capture_enable is the coordinated per-capture reset/boundary. Keep
        // pdm_reset global so overflow survives sleep until reset/new capture.
        .pdm_clk_fb(pdm_clk_fb), .pdm_reset(reset),
        .pdm_data(pdm_d), .capture_enable(capture_enable),
        .overflow_sticky(capture_overflow), .capture_stopped(capture_stopped),
        .ft_clk(ft_clkout), .ft_reset(reset), .ft_txe_n(ft_txe_n),
        .ft_data_out(ft_d_out), .ft_data_oe(ft_d_oe),
        .ft_wr_n(ft_wr_n), .ft_rd_n(ft_rd_n), .ft_oe_n(ft_oe_n),
        .ft_siwu_n(),                 // SIWU# not pinned out in the pinmap
        .tap_frame_data(tap_frame_data), .tap_frame_valid(tap_frame_valid)
    );
    assign ft_d = ft_d_oe ? ft_d_out : 8'hzz;

    // 512 KiB SRAM snapshot fallback (D012). The SRAM/UART clock domain is
    // held in reset until the MMCM locks; capture frames tap the accepted
    // stream so a snapshot can never observe frames the primary path dropped.
    sram_snapshot #(
        .PDM_CLOCK_HZ(PDM_CLOCK_HZ)
    ) snapshot_i (
        .clk(sram_clk), .reset(reset || !clocks_locked), .start(btn[0]),
        .stream_clk(pdm_clk_fb), .stream_reset(reset),
        .stream_frame_data(tap_frame_data),
        .stream_frame_valid(tap_frame_valid),
        .sram_addr(MemAdr), .sram_data(MemDB),
        .sram_ce_n(RamCEn), .sram_oe_n(RamOEn), .sram_we_n(RamWEn),
        .uart_tx_o(uart_rxd_out),
        .busy(snapshot_busy), .done(snapshot_done),
        .capture_error(snapshot_error), .captured_frames()
    );
    assign led[0] = snapshot_busy;
    assign led[1] = snapshot_error;
    assign led0_b = capture_overflow;
    assign led0_g = capture_stopped;
    assign led0_r = tx_limit_fault | ~tx_nfault;

    // T-013-released envelope for the MA40S4S default (orchestration/
    // tx-limits.md): 40 kHz ceiling, amplitude 187/256 (<=20 Vpp), 10 ms
    // bursts. Idle until a control plane drives start; both bridge inputs stay
    // low and nSLEEP holds the driver asleep.
    tx_nco_pwm #(
        .PHASE_BITS(24),
        .MAX_PHASE_INCREMENT(24'd55924), // <=40 kHz at 12 MHz
        .MAX_AMPLITUDE(8'd187),          // tx-limits.md MA40S4S derivation
        .MAX_BURST_CYCLES(32'd120000)    // <=10 ms at 12 MHz
    ) tx_i (
        .clk(sysclk), .reset(reset), .start(1'b0),
        .phase_increment(24'd0),
        .phase_increment_delta(32'sd0),
        .amplitude(8'd0),
        .burst_cycles(32'd0), .tx_a(tx_a), .tx_b(tx_b),
        .active(tx_active), .limit_fault(tx_limit_fault)
    );
    assign tx_en     = tx_a;
    assign tx_ph     = tx_b;
    assign tx_nsleep = tx_active;
    assign tx_pmode  = 1'b1; // IN1/IN2 (PWM) interface mode (tx-limits.md)
endmodule

`default_nettype wire
