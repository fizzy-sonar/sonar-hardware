`timescale 1ns/1ps
`default_nettype none

// Exercise the actual hardware top, including its clock/reset/startup path,
// sampler, stalled stream FIFO, SRAM and UART. Only human-scale delays and the
// snapshot/UART length are compressed; the 16,384-frame USB FIFO and PDM/SRAM
// clock rates retain their production values. No internal signal is forced.
module tb_top_snapshot #(
    parameter integer PDM_CLOCK_HZ = 3072000,
    parameter integer FT_PRESENT = 0
);
    localparam integer FRAMES = 64;
    localparam integer BYTES = 48 + 3*FRAMES;
    localparam integer UART_DIV = 4;
    localparam real UART_BIT_NS = 20.833333 * UART_DIV;
    reg sysclk = 0;
    reg [1:0] btn = 0;
    reg ft_clock_running = FT_PRESENT;
    reg ft_clock = 0;
    reg ft_txe_n = 1;
    wire pdm_src, pdm_en, pdm_fb;
    reg [11:0] pdm_data = 0;
    wire [1:0] led;
    wire overflow_led, stopped_led;
    wire tx_en, tx_ph, tx_nsleep;
    wire [18:0] addr;
    wire [7:0] data;
    wire ce_n, oe_n, we_n, uart;
    reg [15:0] stimulus_index = 0;
    reg [23:0] stimulus_frame = 24'ha50000;
    reg [7:0] received [0:3*BYTES-1];
    integer received_count = 0;
    integer line;

    always #41.666667 sysclk = ~sysclk;
    always #8.333333 ft_clock = ft_clock_running ? ~ft_clock : 1'b0;
    // A simple external clock-buffer loopback, not an analog mic model.
    assign #2 pdm_fb = pdm_src;

    sonar_top #(.PDM_CLOCK_HZ(PDM_CLOCK_HZ)) dut (
        .sysclk(sysclk), .btn(btn), .led(led), .led0_b(overflow_led),
        .led0_g(stopped_led), .led0_r(), .pdm_clk_src(pdm_src),
        .pdm_clk_en(pdm_en), .pdm_clk_fb(pdm_fb), .pdm_d(pdm_data),
        .ft_clkout(ft_clock), .ft_rxf_n(1'b1), .ft_txe_n(ft_txe_n),
        .ft_d(), .ft_wr_n(), .ft_rd_n(), .ft_oe_n(),
        .tx_en(tx_en), .tx_ph(tx_ph), .tx_nsleep(tx_nsleep),
        .tx_nfault(1'b1), .tx_pmode(), .MemAdr(addr), .MemDB(data),
        .RamCEn(ce_n), .RamOEn(oe_n), .RamWEn(we_n), .uart_rxd_out(uart)
    );
    defparam dut.startup_i.CTRL_CLOCK_HZ = 12000;
    defparam dut.btn0_i.DEBOUNCE_CYCLES = 8;
    defparam dut.snapshot_i.SNAPSHOT_FRAMES = FRAMES;
    defparam dut.snapshot_i.CLKS_PER_BIT = UART_DIV;
    defparam dut.snapshot_i.FRAME_TIMEOUT_CLKS = 20000;

    is61wv5128bll_model memory_i (
        .addr(addr), .data(data), .ce_n(ce_n), .oe_n(oe_n), .we_n(we_n)
    );

    // Each complete edge pair carries a new 24-bit tagged counter. Check the
    // serial output independently for tag, ordering, gaps and both CRCs.
    always @(negedge pdm_fb) begin
        #20;
        stimulus_index = stimulus_index + 1;
        stimulus_frame = {8'ha5, stimulus_index};
        for (line = 0; line < 12; line = line + 1)
            pdm_data[line] = stimulus_frame[2*line];
    end
    always @(posedge pdm_fb) begin
        #20;
        for (line = 0; line < 12; line = line + 1)
            pdm_data[line] = stimulus_frame[2*line+1];
    end

    function automatic [31:0] crc_byte(input [31:0] c, input [7:0] b);
        reg [31:0] v;
        integer j;
        begin
            v = c ^ b;
            for (j = 0; j < 8; j = j + 1)
                v = v[0] ? (v >> 1) ^ 32'hedb88320 : v >> 1;
            crc_byte = v;
        end
    endfunction
    function automatic [31:0] word_at(input integer base);
        word_at = {received[base+3], received[base+2],
                   received[base+1], received[base]};
    endfunction

    initial begin : uart_receiver
        reg [7:0] byte_value;
        integer bit_index;
        forever begin
            @(negedge uart);
            #(UART_BIT_NS/2);
            if (uart !== 0) $fatal(1, "UART start bit");
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1) begin
                #(UART_BIT_NS);
                byte_value[bit_index] = uart;
            end
            #(UART_BIT_NS);
            if (uart !== 1) $fatal(1, "UART stop bit");
            if (received_count >= 3*BYTES) $fatal(1, "unexpected UART bytes");
            received[received_count] = byte_value;
            received_count = received_count + 1;
        end
    end

    task automatic capture(input integer capture_number, input integer id);
        integer base, j;
        reg [15:0] first_index, actual_index;
        reg [31:0] crc;
        begin
            base = capture_number * BYTES;
            @(negedge sysclk); btn[0] = 1;
            wait (led[0] === 1);
            repeat (20) @(negedge sysclk);
            btn[0] = 0;
            wait (led[0] === 0);
            if (led[1] !== 0) $fatal(1, "snapshot reported an error");
            if (received_count != base + BYTES)
                $fatal(1, "snapshot length %0d, want %0d", received_count-base, BYTES);
            if (word_at(base) !== 32'h31504e53 ||
                received[base+4] != 1 || received[base+5] != 48)
                $fatal(1, "SNP1 header");
            if (word_at(base+8) != id || word_at(base+20) != PDM_CLOCK_HZ ||
                word_at(base+28) != FRAMES || word_at(base+32) != 3*FRAMES)
                $fatal(1, "capture id/clock/count");
            if (received[base+24] != 24 || received[base+26] != 12)
                $fatal(1, "channel geometry");
            first_index = {received[base+49], received[base+48]};
            crc = 32'hffffffff;
            for (j = 0; j < 3*FRAMES; j = j + 1)
                crc = crc_byte(crc, received[base+48+j]);
            if (word_at(base+36) !== ~crc) $fatal(1, "payload CRC");
            for (j = 0; j < FRAMES; j = j + 1) begin
                actual_index = {received[base+49+3*j], received[base+48+3*j]};
                if (received[base+50+3*j] !== 8'ha5 ||
                    actual_index !== ((first_index+j) & 16'hffff))
                    $fatal(1, "sample tag/order/gap at frame %0d", j);
            end
            crc = 32'hffffffff;
            for (j = 0; j < 40; j = j + 1)
                crc = crc_byte(crc, received[base+j]);
            if (word_at(base+40) !== ~crc) $fatal(1, "header CRC");
            repeat (30) @(negedge sysclk);
        end
    endtask

    // Default TX must remain asleep through startup, capture, USB and reset.
    always @(negedge sysclk)
        if (dut.reset_sysclk === 0 &&
            {tx_en, tx_ph, tx_nsleep} !== 3'b000)
            $fatal(1, "uncommanded TX activity");

    initial begin
        wait (overflow_led === 1 && stopped_led === 1);
        // User arrives long after the USB FIFO is full. No internal trigger.
        repeat (100) @(posedge pdm_fb);
        capture(0, 0);
        capture(1, 1);
        ft_clock_running = 1;
        ft_txe_n = 0;
        repeat (1000) @(posedge ft_clock);
        if (overflow_led !== 1 || stopped_led !== 1)
            $fatal(1, "USB reconnect silently cleared incomplete stream");
        @(negedge sysclk); btn[1] = 1;
        repeat (20) @(negedge sysclk);
        btn[1] = 0;
        wait (dut.capture_enable === 1);
        repeat (100) @(posedge pdm_fb);
        if (overflow_led !== 0 || stopped_led !== 0)
            $fatal(1, "manual reset failed to recover streaming state");
        capture(2, 0);
        $display("PASS top snapshot %0d Hz FT_PRESENT=%0d: delayed/two captures, SRAM/UART counter+CRC, reconnect/reset, TX idle", PDM_CLOCK_HZ, FT_PRESENT);
        $finish;
    end
    initial begin
        #15000000;
        $display("debug lock=%b enable=%b fb=%b pdmrst=%b ftrst=%b accept=%b full=%b overflow=%b busy=%b bytes=%0d",
                 dut.clocks_locked, dut.capture_enable, pdm_fb, dut.reset_pdm,
                 dut.reset_ft, dut.stream_i.accepting, dut.stream_i.fifo_full,
                 overflow_led, led[0], received_count);
        $fatal(1, "top snapshot timeout (USB-dependent capture or missing clocks)");
    end
endmodule
`default_nettype wire
