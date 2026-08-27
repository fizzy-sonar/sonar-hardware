`timescale 1ns/1ps
`default_nettype none

// Control-plane sequencing for the provisional SPH microphone. The clock-maker
// itself is separate: this block selects its exact 1.536 MHz standard clock, then
// disables output before selecting the parameterized ultrasonic clock.
module pdm_clock_startup #(
    parameter integer CTRL_CLOCK_HZ = 12000000,
    parameter integer START_STANDARD_MS = 50,
    parameter integer ULTRASONIC_SETTLE_MS = 10,
    // REVIEW-2026-08-26 S8: the clock-off window must exceed the 2-flop
    // buffer_oe synchronizer latency in the slowest selected_clock domain
    // (2 x 651 ns at 1.536 MHz = 1.302 us) so the mic clock is verifiably
    // OFF before select_ultrasonic changes; 20 cycles at 12 MHz = 1.67 us.
    parameter integer SWITCH_OFF_CYCLES = 20
) (
    input  wire clk,
    input  wire reset,
    input  wire power_good,
    input  wire wake_request,
    output reg  buffer_oe,
    output reg  select_ultrasonic,
    output reg  discard_samples,
    output reg  capture_enable
);
    localparam integer CYCLES_PER_MS = CTRL_CLOCK_HZ / 1000;
    localparam integer STANDARD_CYCLES = CYCLES_PER_MS * START_STANDARD_MS;
    localparam integer SETTLE_CYCLES = CYCLES_PER_MS * ULTRASONIC_SETTLE_MS;
    localparam [2:0] OFF = 3'd0, STANDARD = 3'd1, SWITCH_OFF = 3'd2,
                     SETTLE = 3'd3, RUN = 3'd4;
    localparam integer MAX_TIMED_COUNT =
        STANDARD_CYCLES > SETTLE_CYCLES ? STANDARD_CYCLES : SETTLE_CYCLES;
    localparam integer MAX_COUNT = MAX_TIMED_COUNT > SWITCH_OFF_CYCLES ?
                                   MAX_TIMED_COUNT : SWITCH_OFF_CYCLES;
    localparam integer COUNT_WIDTH = MAX_COUNT <= 2 ? 1 : $clog2(MAX_COUNT + 1);
    reg [2:0] state;
    reg [COUNT_WIDTH-1:0] count;

    initial begin
        if (CTRL_CLOCK_HZ % 1000 != 0)
            $error("CTRL_CLOCK_HZ must be divisible by 1000");
        if (START_STANDARD_MS < 1 || ULTRASONIC_SETTLE_MS < 1 ||
            SWITCH_OFF_CYCLES < 1)
            $error("PDM startup durations must all be positive");
    end

    always @(posedge clk) begin
        if (reset || !wake_request || !power_good) begin
            state               <= OFF;
            count               <= {COUNT_WIDTH{1'b0}};
            buffer_oe           <= 1'b0;
            select_ultrasonic   <= 1'b0;
            discard_samples     <= 1'b1;
            capture_enable      <= 1'b0;
        end else begin
            case (state)
                OFF: begin
                    state             <= STANDARD;
                    count             <= {COUNT_WIDTH{1'b0}};
                    buffer_oe         <= 1'b1;
                    select_ultrasonic <= 1'b0;
                    discard_samples   <= 1'b1;
                    capture_enable    <= 1'b0;
                end
                STANDARD: if (count == STANDARD_CYCLES - 1) begin
                    state     <= SWITCH_OFF;
                    count     <= {COUNT_WIDTH{1'b0}};
                    buffer_oe <= 1'b0;
                end else count <= count + 1'b1;
                SWITCH_OFF: if (count == SWITCH_OFF_CYCLES - 1) begin
                    state             <= SETTLE;
                    count             <= {COUNT_WIDTH{1'b0}};
                    select_ultrasonic <= 1'b1;
                    buffer_oe         <= 1'b1;
                end else count <= count + 1'b1;
                SETTLE: if (count == SETTLE_CYCLES - 1) begin
                    state           <= RUN;
                    discard_samples <= 1'b0;
                    capture_enable  <= 1'b1;
                end else count <= count + 1'b1;
                RUN: begin
                    buffer_oe       <= 1'b1;
                    capture_enable  <= 1'b1;
                    discard_samples <= 1'b0;
                end
                default: state <= OFF;
            endcase
        end
    end
endmodule

`default_nettype wire
