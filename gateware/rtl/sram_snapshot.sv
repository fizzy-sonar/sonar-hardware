`timescale 1ns/1ps
`default_nettype none

// 512 KiB on-module SRAM snapshot controller -- the D012 day-one fallback
// capture path ("UART snapshot via the Cmod's own USB"). On `start`, packed
// 3-byte PDM frames (the exact shared SNP1/SNR1 payload of STREAM_FORMAT.md)
// are streamed into the Cmod A7's ISSI IS61WV5128BLL-10BLI (512K x 8), then the
// bounded window is drained over the on-module USB-UART bridge with the exact
// 48-byte SNP1 v1 header, payload CRC-32, and header CRC-32.
//
// Clocking: `clk` is the MMCM-derived 48 MHz SRAM/UART clock. The PDM frame
// stream crosses in through a small Gray-pointer async FIFO (the same verified
// primitive as the primary FT245 path). Service rate is one byte per three
// `clk` cycles = 16 MB/s, above the 14.4 MB/s ICS worst case and the 9.216 MB/s
// SPH baseline, so the 16-entry CDC FIFO never fills in steady state.
//
// External SRAM timing. The on-module part is the 10 ns-class
// IS61WV5128BLL-10BLI; Digilent's reference manual section 3 rates the module
// for 8 ns access at the 3.3 V rail. Cited ISSI 61-64WV5128Axx-Bxx datasheet AC
// parameters (-8 ns grade): tWC (write cycle) >= 8 ns, tPWE (WE# pulse) >= 6 ns,
// tSD (data setup to write end) >= 5.5 ns, tHD (data hold) >= 0 ns,
// tRC (read cycle) >= 8 ns, tAA (address access) <= 8 ns, tDOE (OE# access)
// <= 5 ns. The three-phase write below (SETUP/PULSE/HOLD, 20.833 ns each at
// 48 MHz) gives >= 2.6x margin on every write minimum plus a full-clock
// address/data hold after WE# rises; reads allow 41.7 ns against the 8 ns
// access. sim/is61wv5128bll_model.sv enforces these minimums in simulation.
// TODO(host): re-verify the cited numbers against the live ISSI PDF on the
// Vivado host (the offline sandbox cannot refetch it) and let Vivado check
// board-level setup/hold with set_output_delay before hardware bring-up.
module sram_snapshot #(
    parameter integer PDM_CLOCK_HZ = 3072000,
    // floor(512 KiB / 3-byte frames): uses bytes 0..524285 of the window.
    parameter integer SNAPSHOT_FRAMES = 174762,
    parameter integer CLKS_PER_BIT = 417, // 48 MHz / 115200 baud
    parameter [31:0] INITIAL_CAPTURE_ID = 32'd0,
    // No frame for this many `clk` cycles ends the capture early (stream
    // stopped/slept mid-snapshot). Default ~87 ms at 48 MHz.
    parameter integer FRAME_TIMEOUT_CLKS = 4194304
) (
    input  wire        clk,
    input  wire        reset,
    input  wire        start,          // asynchronous OK; synchronized here

    // PDM-domain accepted-frame tap from pdm_stream_core.
    input  wire        stream_clk,
    input  wire        stream_reset,
    input  wire [23:0] stream_frame_data,
    input  wire        stream_frame_valid,

    // IS61WV5128BLL-10BLI interface (Cmod A7 bank-14 dedicated pins).
    output reg  [18:0] sram_addr,
    inout  wire [7:0]  sram_data,
    output reg         sram_ce_n,
    output reg         sram_oe_n,
    output reg         sram_we_n,

    output wire        uart_tx_o,
    output reg         busy,
    output reg         done,
    output reg         capture_error,  // CDC FIFO overrun; count still exact
    output wire [31:0] captured_frames
);
    localparam [2:0] S_IDLE = 3'd0, S_POP = 3'd1, S_WRITE = 3'd2,
                     S_HCRC = 3'd3, S_HEADER = 3'd4, S_PREAD = 3'd5,
                     S_PSEND = 3'd6, S_FINISH = 3'd7;

    reg [2:0]  state;
    reg        capturing;              // clk domain
    reg [31:0] frames_written;
    reg [31:0] byte_addr;              // SRAM write cursor (bytes)
    reg [31:0] read_addr;              // SRAM read cursor (bytes)
    reg [31:0] payload_total;          // 3 * frames_written, latched at finish
    reg [23:0] frame_word;
    reg [1:0]  byte_phase;             // which payload byte of the frame
    reg [1:0]  wphase;                 // 0=SETUP 1=PULSE 2=HOLD
    reg        rphase;                 // read microcycle phase
    reg        request_pending;
    reg        next_pending;
    reg        next_valid;
    reg [23:0] next_word;
    reg [31:0] timeout_count;
    reg [5:0]  header_index;
    reg [31:0] capture_id;
    reg [31:0] cap_id_run;
    reg [31:0] payload_crc;
    reg [31:0] payload_crc_final;
    reg [31:0] header_crc_work;
    reg [31:0] header_crc_final;
    reg [7:0]  read_latch;
    reg        data_drive;
    reg [7:0]  data_out;

    assign captured_frames = frames_written;
    assign sram_data = data_drive ? data_out : 8'hzz;

    initial begin
        if (SNAPSHOT_FRAMES < 1) $error("sram_snapshot SNAPSHOT_FRAMES < 1");
        if (SNAPSHOT_FRAMES * 3 > 524288)
            $error("sram_snapshot window exceeds the 512 KiB SRAM");
    end

    function automatic [31:0] crc32_byte(
        input [31:0] crc_in,
        input [7:0] data_in
    );
        integer bit_number;
        reg [31:0] crc;
        begin
            crc = crc_in ^ data_in;
            for (bit_number = 0; bit_number < 8; bit_number = bit_number + 1)
                crc = crc[0] ? (crc >> 1) ^ 32'hedb88320 : crc >> 1;
            crc32_byte = crc;
        end
    endfunction

    // Exact SNP1 v1 header (see STREAM_FORMAT.md). Counts come from the
    // completed capture, so an early-terminated window is still described
    // accurately.
    function automatic [7:0] header_byte(
        input [5:0]  byte_index,
        input [31:0] cap_id,
        input [31:0] frame_count,
        input [31:0] payload_crc_value,
        input [31:0] header_crc_value
    );
        begin
            case (byte_index)
                0: header_byte = "S";
                1: header_byte = "N";
                2: header_byte = "P";
                3: header_byte = "1";
                4: header_byte = 8'd1;
                5: header_byte = 8'd48;
                6, 7: header_byte = 8'd0;
                8: header_byte = cap_id[7:0];
                9: header_byte = cap_id[15:8];
                10: header_byte = cap_id[23:16];
                11: header_byte = cap_id[31:24];
                // first_logical_frame = 0
                12, 13, 14, 15, 16, 17, 18, 19: header_byte = 8'd0;
                20: header_byte = PDM_CLOCK_HZ[7:0];
                21: header_byte = PDM_CLOCK_HZ[15:8];
                22: header_byte = PDM_CLOCK_HZ[23:16];
                23: header_byte = PDM_CLOCK_HZ[31:24];
                24: header_byte = 8'd24;
                25: header_byte = 8'd0;
                26: header_byte = 8'd12;
                27: header_byte = 8'd0;
                28: header_byte = frame_count[7:0];
                29: header_byte = frame_count[15:8];
                30: header_byte = frame_count[23:16];
                31: header_byte = frame_count[31:24];
                32: header_byte = (3 * frame_count) & 8'hff;
                33: header_byte = ((3 * frame_count) >> 8) & 8'hff;
                34: header_byte = ((3 * frame_count) >> 16) & 8'hff;
                35: header_byte = ((3 * frame_count) >> 24) & 8'hff;
                36: header_byte = payload_crc_value[7:0];
                37: header_byte = payload_crc_value[15:8];
                38: header_byte = payload_crc_value[23:16];
                39: header_byte = payload_crc_value[31:24];
                40: header_byte = header_crc_value[7:0];
                41: header_byte = header_crc_value[15:8];
                42: header_byte = header_crc_value[23:16];
                43: header_byte = header_crc_value[31:24];
                default: header_byte = 8'd0;
            endcase
        end
    endfunction

    // ------------------------------------------------------------------
    // Frame CDC: PDM domain -> 48 MHz domain, 16 x 32 Gray-pointer FIFO.
    // The write side only accepts frames while a capture is active; both
    // ports are held in reset between captures so no stale frame survives.
    // ------------------------------------------------------------------
    (* ASYNC_REG = "TRUE" *) reg cap_stream_meta;
    (* ASYNC_REG = "TRUE" *) reg cap_stream_sync;
    reg stream_overrun;
    wire fifo_wr_full;
    wire [31:0] fifo_rd_data;
    wire fifo_rd_valid;
    wire fifo_rd_empty;
    reg  fifo_rd_en;

    wire stream_wr_en = stream_frame_valid && cap_stream_sync && !fifo_wr_full;

    always @(posedge stream_clk) begin
        if (stream_reset) begin
            cap_stream_meta <= 1'b0;
            cap_stream_sync <= 1'b0;
            stream_overrun  <= 1'b0;
        end else begin
            cap_stream_meta <= capturing;
            cap_stream_sync <= cap_stream_meta;
            if (!cap_stream_sync) begin
                stream_overrun <= 1'b0;
            end else if (stream_frame_valid && fifo_wr_full) begin
                stream_overrun <= 1'b1;
            end
        end
    end

    (* ASYNC_REG = "TRUE" *) reg overrun_meta;
    (* ASYNC_REG = "TRUE" *) reg overrun_sync;
    always @(posedge clk) begin
        if (reset) begin
            overrun_meta <= 1'b0;
            overrun_sync <= 1'b0;
        end else begin
            overrun_meta <= stream_overrun;
            overrun_sync <= overrun_meta;
        end
    end

    async_fifo #(
        .WIDTH(32),
        .DEPTH(16)
    ) frame_cdc_i (
        .wr_clk(stream_clk),
        .wr_reset(stream_reset || !cap_stream_sync),
        .wr_en(stream_wr_en),
        .wr_data({8'h00, stream_frame_data}),
        .wr_full(fifo_wr_full),
        .rd_clk(clk),
        .rd_reset(reset || !capturing),
        .rd_en(fifo_rd_en),
        .rd_data(fifo_rd_data),
        .rd_valid(fifo_rd_valid),
        .rd_empty(fifo_rd_empty)
    );

    // Start synchronizer and edge detect.
    (* ASYNC_REG = "TRUE" *) reg start_meta;
    reg start_sync;
    reg start_sync_d;
    wire start_edge = start_sync && !start_sync_d;
    always @(posedge clk) begin
        if (reset) begin
            start_meta   <= 1'b0;
            start_sync   <= 1'b0;
            start_sync_d <= 1'b0;
        end else begin
            start_meta   <= start;
            start_sync   <= start_meta;
            start_sync_d <= start_sync;
        end
    end

    wire [7:0] selected_byte = byte_phase == 2'd0 ? frame_word[7:0] :
                               byte_phase == 2'd1 ? frame_word[15:8] :
                                                    frame_word[23:16];

    wire uart_ready;

    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) uart_i (
        .clk(clk),
        .reset(reset),
        .data(state == S_HEADER ?
              header_byte(header_index, cap_id_run, frames_written,
                          payload_crc_final, header_crc_final) :
              read_latch),
        .valid(state == S_HEADER || state == S_PSEND),
        .ready(uart_ready),
        .tx(uart_tx_o)
    );

    reg [31:0] crc_next;

    always @(posedge clk) begin
        if (reset) begin
            state             <= S_IDLE;
            capturing         <= 1'b0;
            frames_written    <= 32'd0;
            byte_addr         <= 32'd0;
            read_addr         <= 32'd0;
            payload_total     <= 32'd0;
            frame_word        <= 24'd0;
            byte_phase        <= 2'd0;
            wphase            <= 2'd0;
            rphase            <= 1'b0;
            fifo_rd_en        <= 1'b0;
            request_pending   <= 1'b0;
            next_pending      <= 1'b0;
            next_valid        <= 1'b0;
            next_word         <= 24'd0;
            timeout_count     <= 32'd0;
            header_index      <= 6'd0;
            capture_id        <= INITIAL_CAPTURE_ID;
            cap_id_run        <= 32'd0;
            payload_crc       <= 32'hffffffff;
            payload_crc_final <= 32'd0;
            header_crc_work   <= 32'hffffffff;
            header_crc_final  <= 32'd0;
            read_latch        <= 8'd0;
            data_drive        <= 1'b0;
            data_out          <= 8'd0;
            sram_addr         <= 19'd0;
            sram_ce_n         <= 1'b1;
            sram_oe_n         <= 1'b1;
            sram_we_n         <= 1'b1;
            busy              <= 1'b0;
            done              <= 1'b0;
            capture_error     <= 1'b0;
        end else begin
            done       <= 1'b0;
            fifo_rd_en <= 1'b0;

            if (fifo_rd_valid) begin
                if (request_pending) begin
                    frame_word      <= fifo_rd_data[23:0];
                    request_pending <= 1'b0;
                end else begin
                    next_word    <= fifo_rd_data[23:0];
                    next_valid   <= 1'b1;
                    next_pending <= 1'b0;
                end
            end

            case (state)
                S_IDLE: begin
                    sram_ce_n <= 1'b1;
                    sram_oe_n <= 1'b1;
                    sram_we_n <= 1'b1;
                    data_drive <= 1'b0;
                    if (start_edge) begin
                        state           <= S_POP;
                        capturing       <= 1'b1;
                        busy            <= 1'b1;
                        capture_error   <= 1'b0;
                        frames_written  <= 32'd0;
                        byte_addr       <= 32'd0;
                        byte_phase      <= 2'd0;
                        wphase          <= 2'd0;
                        request_pending <= 1'b0;
                        next_pending    <= 1'b0;
                        next_valid      <= 1'b0;
                        timeout_count   <= 32'd0;
                        payload_crc     <= 32'hffffffff;
                        cap_id_run      <= capture_id;
                        capture_id      <= capture_id + 1'b1;
                    end
                end

                S_POP: begin
                    // SRAM deselected while waiting for a frame.
                    sram_ce_n <= 1'b1;
                    sram_oe_n <= 1'b1;
                    sram_we_n <= 1'b1;
                    data_drive <= 1'b0;
                    if (overrun_sync || timeout_count == FRAME_TIMEOUT_CLKS) begin
                        // Stream stopped (or overran) mid-capture: the header
                        // honestly reports the frames already written.
                        if (overrun_sync) capture_error <= 1'b1;
                        capturing         <= 1'b0;
                        request_pending   <= 1'b0;
                        next_pending      <= 1'b0;
                        next_valid        <= 1'b0;
                        payload_crc_final <= ~payload_crc;
                        payload_total     <= 3 * frames_written;
                        header_crc_work   <= 32'hffffffff;
                        header_index      <= 6'd0;
                        state             <= S_HCRC;
                    end else if (next_valid) begin
                        frame_word    <= next_word;
                        next_valid    <= 1'b0;
                        timeout_count <= 32'd0;
                        byte_phase    <= 2'd0;
                        wphase        <= 2'd0;
                        state         <= S_WRITE;
                    end else if (request_pending && fifo_rd_valid) begin
                        // frame_word latched by the common handler above.
                        timeout_count <= 32'd0;
                        byte_phase    <= 2'd0;
                        wphase        <= 2'd0;
                        state         <= S_WRITE;
                    end else begin
                        timeout_count <= timeout_count + 1'b1;
                        if (!request_pending && !fifo_rd_empty) begin
                            fifo_rd_en      <= 1'b1;
                            request_pending <= 1'b1;
                        end
                    end
                end

                S_WRITE: begin
                    case (wphase)
                        2'd0: begin // SETUP: address/data/CE# stable, WE# high
                            sram_addr  <= byte_addr[18:0];
                            data_out   <= selected_byte;
                            data_drive <= 1'b1;
                            sram_ce_n  <= 1'b0;
                            sram_oe_n  <= 1'b1;
                            sram_we_n  <= 1'b1;
                            wphase     <= 2'd1;
                            // Prefetch the next frame so service stays at nine
                            // clocks per frame (16 MB/s > 14.4 MB/s worst case).
                            if (!next_valid && !next_pending && !fifo_rd_empty) begin
                                fifo_rd_en   <= 1'b1;
                                next_pending <= 1'b1;
                            end
                        end
                        2'd1: begin // PULSE: WE# low for a full 20.833 ns
                            sram_we_n <= 1'b0;
                            wphase    <= 2'd2;
                        end
                        default: begin // HOLD: WE# high, bus held one more clock
                            sram_we_n <= 1'b1;
                            wphase    <= 2'd0;
                            crc_next = crc32_byte(payload_crc, selected_byte);
                            payload_crc <= crc_next;
                            byte_addr   <= byte_addr + 1'b1;
                            if (byte_phase == 2'd2) begin
                                byte_phase     <= 2'd0;
                                frames_written <= frames_written + 1'b1;
                                timeout_count  <= 32'd0;
                                if (frames_written + 1 == SNAPSHOT_FRAMES) begin
                                    capturing         <= 1'b0;
                                    request_pending   <= 1'b0;
                                    next_pending      <= 1'b0;
                                    next_valid        <= 1'b0;
                                    payload_crc_final <= ~crc_next;
                                    payload_total     <= 3 * (frames_written + 1);
                                    header_crc_work   <= 32'hffffffff;
                                    header_index      <= 6'd0;
                                    data_drive        <= 1'b0;
                                    sram_ce_n         <= 1'b1;
                                    state             <= S_HCRC;
                                end else if (next_valid) begin
                                    frame_word <= next_word;
                                    next_valid <= 1'b0;
                                end else begin
                                    data_drive <= 1'b0;
                                    sram_ce_n  <= 1'b1;
                                    state      <= S_POP;
                                end
                            end else begin
                                byte_phase <= byte_phase + 1'b1;
                            end
                        end
                    endcase
                end

                // Header CRC is computed one byte per clock (40 clocks) rather
                // than as a 40-deep combinational CRC chain.
                S_HCRC: begin
                    if (header_index == 6'd39) begin
                        header_crc_final <= ~crc32_byte(
                            header_crc_work,
                            header_byte(6'd39, cap_id_run, frames_written,
                                        payload_crc_final, 32'd0));
                        header_index <= 6'd0;
                        state        <= S_HEADER;
                    end else begin
                        header_crc_work <= crc32_byte(
                            header_crc_work,
                            header_byte(header_index, cap_id_run, frames_written,
                                        payload_crc_final, 32'd0));
                        header_index <= header_index + 1'b1;
                    end
                end

                S_HEADER: begin
                    if (uart_ready) begin
                        if (header_index == 6'd47) begin
                            read_addr <= 32'd0;
                            rphase    <= 1'b0;
                            if (payload_total == 0) begin
                                state <= S_FINISH;
                            end else begin
                                state <= S_PREAD;
                            end
                        end else begin
                            header_index <= header_index + 1'b1;
                        end
                    end
                end

                S_PREAD: begin
                    if (rphase == 1'b0) begin
                        // Address + CE#/OE# applied; WE# stays high.
                        sram_addr  <= read_addr[18:0];
                        sram_ce_n  <= 1'b0;
                        sram_oe_n  <= 1'b0;
                        sram_we_n  <= 1'b1;
                        data_drive <= 1'b0;
                        rphase     <= 1'b1;
                    end else begin
                        // 41.7 ns of address/OE# access against the 8 ns tAA.
                        read_latch <= sram_data;
                        sram_ce_n  <= 1'b1;
                        sram_oe_n  <= 1'b1;
                        rphase     <= 1'b0;
                        state      <= S_PSEND;
                    end
                end

                S_PSEND: begin
                    if (uart_ready) begin
                        if (read_addr + 1 == payload_total) begin
                            state <= S_FINISH;
                        end else begin
                            read_addr <= read_addr + 1'b1;
                            state     <= S_PREAD;
                        end
                    end
                end

                S_FINISH: begin
                    if (uart_ready) begin
                        state <= S_IDLE;
                        busy  <= 1'b0;
                        done  <= 1'b1;
                    end
                end

                default: state <= S_IDLE;
            endcase
        end
    end
endmodule

`default_nettype wire
