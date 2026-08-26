`timescale 1ps/1ps
`default_nettype none

module tb_sampler_packer #(
    parameter integer PDM_CLOCK_HZ = 3072000
);
    localparam integer HALF_PERIOD_PS = 500000000000 / PDM_CLOCK_HZ;
    localparam integer TEST_FRAMES = 80;

    reg pdm_clk = 1'b0;
    reg reset = 1'b1;
    reg [11:0] pdm_data = 12'd0;
    wire [23:0] frame_data;
    wire frame_valid;
    reg [23:0] expected [0:TEST_FRAMES-1];
    integer expected_written = 0;
    integer expected_read = 0;
    integer sigma_accumulator [0:23];
    integer channel;
    integer n;
    reg [23:0] next_frame;

    pdm_ddr_sampler dut (
        .pdm_clk_fb(pdm_clk),
        .reset(reset),
        .pdm_data(pdm_data),
        .frame_data(frame_data),
        .frame_valid(frame_valid)
    );

    always #(HALF_PERIOD_PS) pdm_clk = ~pdm_clk;

    function automatic integer sine16(input integer phase);
        begin
            case (phase & 15)
                0: sine16 = 0;    1: sine16 = 49;
                2: sine16 = 90;   3: sine16 = 117;
                4: sine16 = 127;  5: sine16 = 117;
                6: sine16 = 90;   7: sine16 = 49;
                8: sine16 = 0;    9: sine16 = -49;
                10: sine16 = -90; 11: sine16 = -117;
                12: sine16 = -127; 13: sine16 = -117;
                14: sine16 = -90; 15: sine16 = -49;
            endcase
        end
    endfunction

    task automatic drive_frame(input [23:0] logical_frame);
        integer line;
        begin
            expected[expected_written] = logical_frame;
            expected_written = expected_written + 1;
            for (line = 0; line < 12; line = line + 1)
                pdm_data[line] = logical_frame[2*line];
            @(posedge pdm_clk);
            #1;
            for (line = 0; line < 12; line = line + 1)
                pdm_data[line] = logical_frame[2*line+1];
            @(negedge pdm_clk);
            #1;
        end
    endtask

    always @(posedge pdm_clk) begin
        #2;
        if (!reset && frame_valid) begin
            if (expected_read >= expected_written) begin
                $fatal(1, "sampler emitted unexpected frame %06x", frame_data);
            end
            if (frame_data !== expected[expected_read]) begin
                $fatal(1, "frame %0d mismatch: got %06x expected %06x",
                       expected_read, frame_data, expected[expected_read]);
            end
            expected_read = expected_read + 1;
        end
    end

    initial begin
        if (PDM_CLOCK_HZ != 3072000 && PDM_CLOCK_HZ != 4800000)
            $fatal(1, "test rate must be 3.072 or 4.8 MHz");
        if (PDM_CLOCK_HZ * 24 !=
            (PDM_CLOCK_HZ == 3072000 ? 73728000 : 115200000))
            $fatal(1, "raw payload-rate calculation failed");

        for (channel = 0; channel < 24; channel = channel + 1)
            sigma_accumulator[channel] = 0;

        repeat (3) @(posedge pdm_clk);
        @(negedge pdm_clk);
        #1;
        reset = 1'b0;

        // Counter-pattern frames make every byte and channel position obvious.
        for (n = 0; n < 16; n = n + 1)
            drive_frame((24'h13579b * n) ^ 24'ha55a3c);

        // Deterministic first-order sigma-delta streams for phase-offset 16-step
        // sine tones. This is stimulus, not a microphone fidelity model.
        for (n = 0; n < 64; n = n + 1) begin
            next_frame = 24'd0;
            for (channel = 0; channel < 24; channel = channel + 1) begin
                sigma_accumulator[channel] = sigma_accumulator[channel] +
                                             sine16(n + channel);
                if (sigma_accumulator[channel] >= 0) begin
                    next_frame[channel] = 1'b1;
                    sigma_accumulator[channel] = sigma_accumulator[channel] - 127;
                end else begin
                    next_frame[channel] = 1'b0;
                    sigma_accumulator[channel] = sigma_accumulator[channel] + 127;
                end
            end
            drive_frame(next_frame);
        end

        // One more edge pair lets the sampler publish the final logical frame.
        @(negedge pdm_clk);
        pdm_data = 12'd0;
        @(posedge pdm_clk);
        wait (expected_read == TEST_FRAMES);
        $display("PASS sampler/tone rate=%0dHz frames=%0d payload=%0db/s",
                 PDM_CLOCK_HZ, expected_read, PDM_CLOCK_HZ * 24);
        $finish;
    end

    initial begin
        #(HALF_PERIOD_PS * 400);
        $fatal(1, "sampler test timeout (%0d/%0d)", expected_read, TEST_FRAMES);
    end
endmodule

`default_nettype wire
