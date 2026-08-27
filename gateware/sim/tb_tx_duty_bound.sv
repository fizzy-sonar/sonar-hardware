`timescale 1ns/1ps
`default_nettype none

// REVIEW-2026-08-26 finding B2 regression. The pre-fix tx_nco_pwm chopped each
// half-cycle with a free-running 256-clock PWM carrier (46.875 kHz, 21.33 us)
// LONGER than a 40 kHz half-cycle (12.5 us): the reviewer's run at
// PHASE_BITS=24, phase_increment=55924, amplitude=187, 12 MHz showed 15.7% of
// half-cycles at ~100% duty while the mean sat exactly on target.
//
// The phase-gated rewrite must HARD-BOUND every half-cycle. Bound enforced
// here (derived in orchestration/tx-limits.md): on-clocks per half-cycle
//   <= floor(amplitude * half_len / 256) + 2        (+/-1 clock phase
//   quantization at each pulse edge). This TB asserts ZERO half-cycles over
// the bound for: (a) the reviewer's exact config, >=200k clocks; (b) an
// amplitude sweep 0..255 at 40 kHz (0 must be rejected, not run); (c) both
// chirp endpoints 20/32 kHz (phase_increment 27962/44739) at amplitude 187
// and 255; (d) a full 20->32 kHz ramp at amplitude 187.
module tb_tx_duty_bound;
    localparam integer PHASE_BITS = 24;
    localparam integer PWM_BITS = 8;
    localparam [PHASE_BITS-1:0] F40K = 24'd55924; // 40.0 kHz @ 12 MHz
    localparam [PHASE_BITS-1:0] F20K = 24'd27962; // chirp low endpoint
    localparam [PHASE_BITS-1:0] F32K = 24'd44739; // chirp high endpoint

    reg clk = 1'b0;
    reg reset = 1'b1;
    reg start = 1'b0;
    reg [PHASE_BITS-1:0] phase_increment = {PHASE_BITS{1'b0}};
    reg signed [PHASE_BITS+7:0] phase_increment_delta = 32'sd0;
    reg [PWM_BITS-1:0] amplitude = {PWM_BITS{1'b0}};
    reg [31:0] burst_cycles = 32'd0;
    wire tx_a, tx_b, active, limit_fault;

    always #41.667 clk = ~clk; // 12 MHz

    tx_nco_pwm #(
        .PHASE_BITS(PHASE_BITS), .PWM_BITS(PWM_BITS), .RAMP_FRAC_BITS(8),
        .MAX_PHASE_INCREMENT(F40K), .MAX_AMPLITUDE(8'd255),
        .MAX_BURST_CYCLES(32'd1000000)
    ) tx_i (
        .clk(clk), .reset(reset), .start(start),
        .phase_increment(phase_increment),
        .phase_increment_delta(phase_increment_delta),
        .amplitude(amplitude),
        .burst_cycles(burst_cycles), .tx_a(tx_a), .tx_b(tx_b),
        .active(active), .limit_fault(limit_fault)
    );

    // Per-half-cycle monitor (white-box: boundary = NCO polarity MSB toggle).
    integer half_cnt = 0, on_cnt = 0;
    integer half_cycles = 0, violations = 0;
    integer amp_now = 0;
    integer worst_on = 0, worst_half = 1; // worst duty ratio seen
    reg pol = 1'b0;

    always @(posedge clk) begin
        if (tx_a && tx_b) $fatal(1, "bridge outputs overlap");
        if (!active && (tx_a || tx_b))
            $fatal(1, "TX outputs hot while inactive");
        if (active) begin
            if (tx_i.phase[PHASE_BITS-1] !== pol) begin
                // Close the completed half-cycle (the samples gathered so far
                // all belong to it; partial first/last halves of a burst are
                // never closed and therefore never checked).
                if (half_cnt > 0) begin
                    half_cycles = half_cycles + 1;
                    if (on_cnt * 256 > amp_now * half_cnt + 512) begin
                        violations = violations + 1;
                        if (violations <= 5)
                            $display("VIOLATION: amp=%0d on=%0d half=%0d duty=%0d/256",
                                     amp_now, on_cnt, half_cnt,
                                     on_cnt * 256 / half_cnt);
                    end
                    if (on_cnt * worst_half > worst_on * half_cnt) begin
                        worst_on   = on_cnt;
                        worst_half = half_cnt;
                    end
                end
                half_cnt = 0;
                on_cnt   = 0;
                pol      = tx_i.phase[PHASE_BITS-1];
            end
            half_cnt = half_cnt + 1;
            if (tx_a || tx_b) on_cnt = on_cnt + 1;
        end
    end

    task automatic run_case(input [PHASE_BITS-1:0] pi,
                            input signed [31:0] delta,
                            input [PWM_BITS-1:0] amp,
                            input [31:0] bursts);
        begin
            @(negedge clk);
            // Reset the monitor so a trailing partial half-cycle of the
            // previous burst is never closed under this run's amplitude.
            half_cnt = 0; on_cnt = 0; pol = 1'b0;
            phase_increment       = pi;
            phase_increment_delta = delta;
            amplitude             = amp;
            burst_cycles          = bursts;
            amp_now               = amp;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
            if (amp == 0) begin
                @(posedge clk); #1;
                if (!limit_fault || active)
                    $fatal(1, "amplitude=0 must be rejected, not run");
                @(negedge clk);
            end else begin
                wait (active);
                wait (!active);
                @(posedge clk); #1;
                if (limit_fault)
                    $fatal(1, "unexpected limit_fault pi=%0d amp=%0d", pi, amp);
            end
        end
    endtask

    integer a;
    integer hc0, v0;
    initial begin
        repeat (4) @(posedge clk);
        @(negedge clk); reset = 1'b0;

        // (a) Reviewer's exact config: 40 kHz, amplitude 187, 200k clocks.
        hc0 = half_cycles; v0 = violations;
        run_case(F40K, 32'sd0, 8'd187, 32'd200000);
        if (half_cycles - hc0 < 1200)
            $fatal(1, "reviewer run too short: %0d half-cycles",
                   half_cycles - hc0);
        if (violations != v0)
            $fatal(1, "B2 regression: %0d half-cycles over the bound in the reviewer config",
                   violations - v0);
        $display("reviewer config: %0d half-cycles, 0 over bound", half_cycles - hc0);

        // (b) Amplitude sweep 0..255 at 40 kHz (~10 half-cycles each).
        run_case(F40K, 32'sd0, 8'd0, 32'd1024); // must be rejected
        for (a = 1; a < 256; a = a + 1)
            run_case(F40K, 32'sd0, a[7:0], 32'd3072);
        $display("amplitude sweep 0..255 done");

        // (c) Both chirp endpoints at the MA40S4S cap and at full scale.
        run_case(F20K, 32'sd0, 8'd187, 32'd4096);
        run_case(F20K, 32'sd0, 8'd255, 32'd4096);
        run_case(F32K, 32'sd0, 8'd187, 32'd4096);
        run_case(F32K, 32'sd0, 8'd255, 32'd4096);
        $display("chirp endpoints done");

        // (d) Full 20->32 kHz ramp: +524/cycle in Q8 climbs 27962 -> ~44730
        // over 8192 clocks, staying under the 55924 ceiling.
        run_case(F20K, 32'sd524, 8'd187, 32'd8192);
        $display("20->32kHz ramp done");

        if (violations != 0)
            $fatal(1, "B2 regression: %0d half-cycles exceeded the duty bound",
                   violations);
        $display("PASS B2 duty hard-bound: %0d half-cycles checked, 0 over bound; worst duty %0d/%0d = %0d/256",
                 half_cycles, worst_on, worst_half,
                 worst_on * 256 / worst_half);
        $finish;
    end
endmodule

`default_nettype wire
