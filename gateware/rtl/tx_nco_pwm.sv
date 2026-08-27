`timescale 1ns/1ps
`default_nettype none

// Bounded chirp NCO + amplitude PWM for two DRV8876 control lines. The signed
// fixed-point delta is added to the phase increment once per system clock; zero
// selects a fixed tone. A request outside any configured limit is rejected, and
// a ramp that later crosses a limit stops immediately with limit_fault asserted.
// Reset, idle, and rejected states drive both outputs low. T-013 owns the final
// transducer voltage/duty/duration envelope (orchestration/tx-limits.md).
//
// REVIEW-2026-08-26 finding B2 (duty gating rework): the pre-fix design chopped
// each half-cycle with a free-running 8-bit PWM carrier (12 MHz/256 = 46.875
// kHz, 21.33 us) that is LONGER than a 40 kHz half-cycle (12.5 us). Carrier and
// half-cycle boundaries drifted past each other, so 15.7% of half-cycles landed
// entirely inside the carrier on-window and ran at ~100% duty at amplitude=187
// while the long-term mean stayed exactly on target - every averaged check
// passed and the per-half-cycle bound failed. The carrier is now gone: the
// output is gated by the NCO phase itself, on only for the first
// amplitude/256 of each half-cycle's phase range, so per-half-cycle duty is
// HARD-BOUNDED by amplitude/256 (+/-1 clock of phase quantization) at any
// frequency or chirp rate. Requires PHASE_BITS > PWM_BITS.
module tx_nco_pwm #(
    parameter integer PHASE_BITS = 24,
    parameter integer PWM_BITS = 8,
    parameter integer RAMP_FRAC_BITS = 8,
    parameter [PHASE_BITS-1:0] MAX_PHASE_INCREMENT = {PHASE_BITS{1'b1}},
    parameter [PWM_BITS-1:0] MAX_AMPLITUDE = {PWM_BITS{1'b1}},
    parameter [31:0] MAX_BURST_CYCLES = 32'd120000
) (
    input  wire                      clk,
    input  wire                      reset,
    input  wire                      start,
    input  wire [PHASE_BITS-1:0]     phase_increment,
    input  wire signed [PHASE_BITS+RAMP_FRAC_BITS-1:0]
                                      phase_increment_delta,
    input  wire [PWM_BITS-1:0]       amplitude,
    input  wire [31:0]               burst_cycles,
    output reg                       tx_a,
    output reg                       tx_b,
    output reg                       active,
    output reg                       limit_fault
);
    localparam integer STEP_ACC_BITS = PHASE_BITS + RAMP_FRAC_BITS;
    reg [PHASE_BITS-1:0] phase;
    reg signed [STEP_ACC_BITS:0] phase_step_accum;
    reg signed [STEP_ACC_BITS:0] phase_delta_latched;
    reg [PWM_BITS-1:0] amplitude_latched;
    reg [31:0] cycles_left;
    // Phase-derived duty gate: top PWM_BITS of the sub-half-cycle phase.
    // phase[PHASE_BITS-1] is the polarity, so phase[PHASE_BITS-2 -: PWM_BITS]
    // sweeps 0..2^PWM_BITS-1 exactly once per half-cycle.
    wire [PWM_BITS-1:0] phase_pwm = phase[PHASE_BITS-2 -: PWM_BITS];
    wire pwm_on = phase_pwm < amplitude_latched;
    wire signed [STEP_ACC_BITS:0] phase_step_next =
        phase_step_accum + phase_delta_latched;
    wire signed [STEP_ACC_BITS:0] max_phase_step_q =
        $signed({1'b0, MAX_PHASE_INCREMENT, {RAMP_FRAC_BITS{1'b0}}});

    always @(posedge clk) begin
        if (reset) begin
            phase             <= {PHASE_BITS{1'b0}};
            phase_step_accum  <= {(STEP_ACC_BITS+1){1'b0}};
            phase_delta_latched <= {(STEP_ACC_BITS+1){1'b0}};
            amplitude_latched <= {PWM_BITS{1'b0}};
            cycles_left       <= 32'd0;
            tx_a              <= 1'b0;
            tx_b              <= 1'b0;
            active            <= 1'b0;
            limit_fault       <= 1'b0;
        end else begin
            tx_a <= 1'b0;
            tx_b <= 1'b0;

            if (start && !active) begin
                if (phase_increment == 0 ||
                    phase_increment > MAX_PHASE_INCREMENT ||
                    amplitude == 0 || amplitude > MAX_AMPLITUDE ||
                    burst_cycles == 0 || burst_cycles > MAX_BURST_CYCLES) begin
                    limit_fault <= 1'b1;
                    active      <= 1'b0;
                end else begin
                    phase             <= {PHASE_BITS{1'b0}};
                    phase_step_accum  <= $signed(
                        {1'b0, phase_increment, {RAMP_FRAC_BITS{1'b0}}}
                    );
                    phase_delta_latched <= $signed(
                        {phase_increment_delta[STEP_ACC_BITS-1],
                         phase_increment_delta}
                    );
                    amplitude_latched <= amplitude;
                    cycles_left       <= burst_cycles;
                    active            <= 1'b1;
                    limit_fault       <= 1'b0;
                end
            end else if (active) begin
                phase     <= phase +
                             phase_step_accum[STEP_ACC_BITS-1:RAMP_FRAC_BITS];
                if (pwm_on) begin
                    if (phase[PHASE_BITS-1]) tx_b <= 1'b1;
                    else                     tx_a <= 1'b1;
                end
                if (cycles_left == 1) begin
                    cycles_left <= 32'd0;
                    active      <= 1'b0;
                    tx_a        <= 1'b0;
                    tx_b        <= 1'b0;
                end else if (phase_step_next <= 0 ||
                             phase_step_next > max_phase_step_q) begin
                    cycles_left <= 32'd0;
                    active      <= 1'b0;
                    limit_fault <= 1'b1;
                    tx_a        <= 1'b0;
                    tx_b        <= 1'b0;
                end else begin
                    cycles_left      <= cycles_left - 1'b1;
                    phase_step_accum <= phase_step_next;
                end
            end
        end
    end
endmodule

`default_nettype wire
