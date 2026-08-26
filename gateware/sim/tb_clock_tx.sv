`timescale 1ns/1ps
`default_nettype none

module tb_clock_tx;
    reg clk = 1'b0;
    reg reset = 1'b1;
    reg power_good = 1'b0;
    reg wake = 1'b0;
    wire buffer_oe, select_ultrasonic, discard_samples, capture_enable;
    reg tx_start = 1'b0;
    reg [7:0] phase_increment = 8'd0;
    reg signed [11:0] phase_increment_delta = 12'sd0;
    reg [7:0] amplitude = 8'd0;
    reg [31:0] burst_cycles = 32'd0;
    wire tx_a, tx_b, tx_active, limit_fault;
    integer active_cycles = 0;
    integer standard_cycles = 0;
    integer switch_off_cycles = 0;
    integer settle_cycles = 0;
    integer chirp_step_count = 0;
    reg [7:0] chirp_steps [0:7];

    always #5 clk = ~clk;

    pdm_clock_startup #(
        .CTRL_CLOCK_HZ(1000),
        .START_STANDARD_MS(50),
        .ULTRASONIC_SETTLE_MS(10),
        .SWITCH_OFF_CYCLES(2)
    ) startup_i (
        .clk(clk), .reset(reset), .power_good(power_good),
        .wake_request(wake), .buffer_oe(buffer_oe),
        .select_ultrasonic(select_ultrasonic),
        .discard_samples(discard_samples), .capture_enable(capture_enable)
    );

    tx_nco_pwm #(
        .PHASE_BITS(8), .PWM_BITS(8), .RAMP_FRAC_BITS(4),
        .MAX_PHASE_INCREMENT(8'd64), .MAX_AMPLITUDE(8'd128),
        .MAX_BURST_CYCLES(16)
    ) tx_i (
        .clk(clk), .reset(reset), .start(tx_start),
        .phase_increment(phase_increment),
        .phase_increment_delta(phase_increment_delta),
        .amplitude(amplitude),
        .burst_cycles(burst_cycles), .tx_a(tx_a), .tx_b(tx_b),
        .active(tx_active), .limit_fault(limit_fault)
    );

    always @(posedge clk) begin
        if (tx_a && tx_b) $fatal(1, "TX bridge commands overlap");
        if (!tx_active && (tx_a || tx_b)) $fatal(1, "TX not low while inactive");
        if (tx_active) begin
            active_cycles = active_cycles + 1;
            if (chirp_step_count < 8) begin
                chirp_steps[chirp_step_count] =
                    tx_i.phase_step_accum[11:4];
                chirp_step_count = chirp_step_count + 1;
            end
        end
        #1;
        if (!reset && power_good && wake && !capture_enable) begin
            if (buffer_oe && !select_ultrasonic && discard_samples)
                standard_cycles = standard_cycles + 1;
            else if (!buffer_oe && !select_ultrasonic && discard_samples)
                switch_off_cycles = switch_off_cycles + 1;
            else if (buffer_oe && select_ultrasonic && discard_samples)
                settle_cycles = settle_cycles + 1;
            else
                $fatal(1, "illegal PDM startup output combination");
        end
    end

    task automatic pulse_tx_start;
        begin
            @(negedge clk); tx_start = 1'b1;
            @(negedge clk); tx_start = 1'b0;
        end
    endtask

    initial begin
        // Exact MMCM/divider arithmetic used by pdm_clock_7series: 768 MHz VCO,
        // 6.144 MHz /4 for startup and /2 after the selected ultrasonic output.
        if (((12000000 * 64 / 125) / 4) != 1536000 ||
            ((12000000 * 64 / 125) / 2) != 3072000 ||
            ((12000000 * 64 / 80) / 2) != 4800000)
            $fatal(1, "PDM clock-plan arithmetic mismatch");
        if (3072000 * 24 != 73728000 || 4800000 * 24 != 115200000)
            $fatal(1, "PDM raw-rate arithmetic mismatch");

        repeat (3) @(posedge clk);
        reset = 1'b0;
        power_good = 1'b1;
        wake = 1'b1;
        wait (buffer_oe);
        if (select_ultrasonic || capture_enable || !discard_samples)
            $fatal(1, "bad standard-start state");
        wait (!buffer_oe);
        if (select_ultrasonic) $fatal(1, "clock selected before quiet interval");
        wait (select_ultrasonic && buffer_oe);
        if (capture_enable || !discard_samples) $fatal(1, "settle not discarded");
        wait (capture_enable);
        if (!select_ultrasonic || !buffer_oe || discard_samples)
            $fatal(1, "bad ultrasonic run state");
        if (standard_cycles != 50 || switch_off_cycles != 2 ||
            settle_cycles != 10)
            $fatal(1, "startup durations std=%0d off=%0d settle=%0d",
                   standard_cycles, switch_off_cycles, settle_cycles);

        // Reject an over-limit request and remain electrically safe.
        phase_increment = 8'd20;
        phase_increment_delta = 12'sd0;
        amplitude = 8'd200;
        burst_cycles = 8;
        pulse_tx_start();
        @(posedge clk); #1;
        if (!limit_fault || tx_active || tx_a || tx_b)
            $fatal(1, "unsafe over-limit TX handling");

        // A valid upward chirp clears the fault, advances its phase step by
        // exactly +0.5/cycle in Q4, and stops by itself.
        amplitude = 8'd96;
        burst_cycles = 8;
        phase_increment_delta = 12'sd8;
        pulse_tx_start();
        wait (tx_active);
        wait (!tx_active);
        @(posedge clk); #1;
        if (limit_fault || tx_a || tx_b) $fatal(1, "TX did not return safe low");
        if (active_cycles != 8)
            $fatal(1, "TX duration mismatch: active %0d cycles", active_cycles);
        if (chirp_step_count != 8 ||
            chirp_steps[0] != 20 || chirp_steps[1] != 20 ||
            chirp_steps[2] != 21 || chirp_steps[3] != 21 ||
            chirp_steps[4] != 22 || chirp_steps[5] != 22 ||
            chirp_steps[6] != 23 || chirp_steps[7] != 23)
            $fatal(1, "TX chirp phase-step ramp mismatch");

        // A ramp that would cross the configured frequency ceiling must stop
        // rather than emit an out-of-envelope phase step.
        phase_increment = 8'd63;
        phase_increment_delta = 12'sd32; // +2.0/cycle in Q4
        burst_cycles = 4;
        pulse_tx_start();
        wait (tx_active);
        wait (!tx_active);
        @(posedge clk); #1;
        if (!limit_fault || tx_a || tx_b)
            $fatal(1, "TX ramp-limit crossing was not stopped safely");

        wake = 1'b0;
        @(posedge clk); #1;
        if (buffer_oe || capture_enable) $fatal(1, "sleep did not disable PDM");
        $display("PASS exact 1.536/3.072/4.8MHz plan, 50ms+10ms startup, and bounded TX chirp safety");
        $finish;
    end
endmodule

`default_nettype wire
