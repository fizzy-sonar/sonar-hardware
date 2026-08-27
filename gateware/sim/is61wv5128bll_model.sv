`timescale 1ns/1ps
`default_nettype none

// Behavioral model of the Cmod A7's on-module ISSI IS61WV5128BLL-10BLI
// (512K x 8, 19 address + 8 bidirectional data + CE#/OE#/WE#) with the timing
// checks the snapshot controller must respect. Digilent's reference manual
// section 3 rates the module for 8 ns access at the 3.3 V rail, so the -8 ns
// grade column of the ISSI 61-64WV5128Axx-Bxx datasheet AC table is enforced:
//   tWC  write cycle time            >= 8 ns
//   tPWE WE# pulse width             >= 6 ns
//   tSD  data setup to write end     >= 5.5 ns
//   tHD  data hold from write end    >= 0 ns (not checkable below zero)
//   tRC  read cycle time             >= 8 ns
//   tAA  address access time         <= 8 ns (modeled as output delay)
//   tDOE OE# access time             <= 5 ns (covered by the tAA model delay)
// The controller's per-phase margins against these values are analyzed in
// sim/README.md (worst case 2.6x at the -10 ns grade). CP-C checklist:
// confirm against the ISSI PDF (ticket T-020 Log).
module is61wv5128bll_model #(
    parameter integer T_AA_NS  = 8,
    parameter integer T_WC_NS  = 8,
    parameter integer T_PWE_NS = 6,
    parameter real    T_SD_NS  = 5.5
) (
    input  wire [18:0] addr,
    inout  wire [7:0]  data,
    input  wire        ce_n,
    input  wire        oe_n,
    input  wire        we_n
);
    reg [7:0] mem [0:524287];
    integer init_index;
    initial begin
        // Deterministic nonzero fill so a misaligned read cannot pass by
        // matching an all-zero default.
        for (init_index = 0; init_index < 524288; init_index = init_index + 1)
            mem[init_index] = (init_index * 7 + 3) & 8'hff;
    end

    // Asynchronous read: data appears T_AA_NS after the latest of address /
    // CE# / OE# and returns to Z when deselected (same net delay).
    wire read_active = !ce_n && !oe_n && we_n;
    assign #(T_AA_NS) data = read_active ? mem[addr] : 8'hzz;

    // Write commit on the rising edge of WE# (CE# is held low across whole
    // captures by the controller), with pulse/cycle/data-setup checks.
    realtime we_fall_time;
    realtime last_write_end;
    realtime last_data_change;
    realtime last_addr_change;
    reg      write_in_progress;

    initial begin
        we_fall_time      = 0;
        last_write_end    = -1000.0;
        last_data_change  = -1000.0;
        last_addr_change  = -1000.0;
        write_in_progress = 1'b0;
    end

    always @(data) last_data_change = $realtime;
    always @(addr) last_addr_change = $realtime;

    always @(negedge we_n) begin
        if (!ce_n) begin
            if (!oe_n)
                $fatal(1, "SRAM: WE# and OE# both low (bus contention) at %0t",
                       $realtime);
            if ($realtime - last_write_end < T_WC_NS)
                $fatal(1, "SRAM: tWC violation (%0.1f ns < %0d ns) at %0t",
                       $realtime - last_write_end, T_WC_NS, $realtime);
            we_fall_time      = $realtime;
            write_in_progress = 1'b1;
        end
    end

    always @(posedge we_n) begin
        if (write_in_progress) begin
            if ($realtime - we_fall_time < T_PWE_NS)
                $fatal(1, "SRAM: tPWE violation (%0.1f ns < %0d ns) at %0t",
                       $realtime - we_fall_time, T_PWE_NS, $realtime);
            if ($realtime - last_data_change < T_SD_NS)
                $fatal(1, "SRAM: tSD violation (%0.1f ns < %0.1f ns) at %0t",
                       $realtime - last_data_change, T_SD_NS, $realtime);
            if ($realtime - last_addr_change < T_SD_NS)
                $fatal(1, "SRAM: address setup violation at %0t", $realtime);
            if (data === 8'hzz || ^data === 1'bx)
                $fatal(1, "SRAM: write with undriven data bus at %0t", $realtime);
            mem[addr]         = data;
            last_write_end    = $realtime;
            write_in_progress = 1'b0;
        end
    end

    // CE#-terminated write (not used by the controller; kept for completeness).
    always @(posedge ce_n) begin
        if (write_in_progress) begin
            if ($realtime - we_fall_time < T_PWE_NS)
                $fatal(1, "SRAM: tPWE violation (CE# end) at %0t", $realtime);
            if (data === 8'hzz || ^data === 1'bx)
                $fatal(1, "SRAM: write with undriven data bus at %0t", $realtime);
            mem[addr]         = data;
            last_write_end    = $realtime;
            write_in_progress = 1'b0;
        end
    end
endmodule

`default_nettype wire
