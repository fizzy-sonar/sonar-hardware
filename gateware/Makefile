IVERILOG ?= iverilog
PYTHON ?= python3
VVP ?= vvp
BUILD_DIR := build
RTL := rtl/pdm_ddr_sampler.sv \
	rtl/async_fifo.sv \
	rtl/frame_byte_packer.sv \
	rtl/stream_header.sv \
	rtl/ft245_sync_tx.sv \
	rtl/pdm_stream_core.sv \
	rtl/uart_tx.sv \
	rtl/uart_snapshot.sv \
	rtl/pdm_clock_startup.sv \
	rtl/tx_nco_pwm.sv \
	rtl/sram_snapshot.sv

.PHONY: test clean

test: $(BUILD_DIR)
	$(IVERILOG) -g2012 -Wall -s tb_sampler_packer \
		-Ptb_sampler_packer.PDM_CLOCK_HZ=3072000 \
		-o $(BUILD_DIR)/tb_sampler_3072 $(RTL) sim/tb_sampler_packer.sv
	$(VVP) $(BUILD_DIR)/tb_sampler_3072
	$(IVERILOG) -g2012 -Wall -s tb_sampler_packer \
		-Ptb_sampler_packer.PDM_CLOCK_HZ=4800000 \
		-o $(BUILD_DIR)/tb_sampler_4800 $(RTL) sim/tb_sampler_packer.sv
	$(VVP) $(BUILD_DIR)/tb_sampler_4800
	$(IVERILOG) -g2012 -Wall -s tb_fifo_ft245 \
		-o $(BUILD_DIR)/tb_fifo_ft245 $(RTL) sim/tb_fifo_ft245.sv
	$(VVP) $(BUILD_DIR)/tb_fifo_ft245
	$(IVERILOG) -g2012 -Wall -s tb_stream_core \
		-o $(BUILD_DIR)/tb_stream_core $(RTL) sim/tb_stream_core.sv
	$(VVP) $(BUILD_DIR)/tb_stream_core
	$(IVERILOG) -g2012 -Wall -s tb_overflow_stop \
		-o $(BUILD_DIR)/tb_overflow_stop $(RTL) sim/tb_overflow_stop.sv
	$(VVP) $(BUILD_DIR)/tb_overflow_stop
	$(IVERILOG) -g2012 -Wall -s tb_stream_header \
		-o $(BUILD_DIR)/tb_stream_header $(RTL) sim/tb_stream_header.sv
	$(VVP) $(BUILD_DIR)/tb_stream_header
	$(IVERILOG) -g2012 -Wall -s tb_uart_snapshot \
		-o $(BUILD_DIR)/tb_uart_snapshot $(RTL) sim/tb_uart_snapshot.sv
	$(VVP) $(BUILD_DIR)/tb_uart_snapshot
	$(IVERILOG) -g2012 -Wall -s tb_clock_tx \
		-o $(BUILD_DIR)/tb_clock_tx $(RTL) sim/tb_clock_tx.sv
	$(VVP) $(BUILD_DIR)/tb_clock_tx
	$(IVERILOG) -g2012 -Wall -s tb_tx_duty_bound \
		-o $(BUILD_DIR)/tb_tx_duty_bound $(RTL) sim/tb_tx_duty_bound.sv
	$(VVP) $(BUILD_DIR)/tb_tx_duty_bound
	$(IVERILOG) -g2012 -Wall -s tb_sram_snapshot \
		-Ptb_sram_snapshot.SNAPSHOT_FRAMES=16 \
		-Ptb_sram_snapshot.CLKS_PER_BIT=8 \
		-Ptb_sram_snapshot.FRAME_TIMEOUT_CLKS=2000 \
		-o $(BUILD_DIR)/tb_sram_snapshot_small $(RTL) \
		sim/is61wv5128bll_model.sv sim/tb_sram_snapshot.sv
	$(VVP) $(BUILD_DIR)/tb_sram_snapshot_small
	$(IVERILOG) -g2012 -Wall -s tb_sram_snapshot \
		-Ptb_sram_snapshot.SNAPSHOT_FRAMES=174762 \
		-Ptb_sram_snapshot.CLKS_PER_BIT=2 \
		-Ptb_sram_snapshot.FRAME_TIMEOUT_CLKS=4194304 \
		-Ptb_sram_snapshot.FULL_WINDOW=1 \
		-o $(BUILD_DIR)/tb_sram_snapshot_full $(RTL) \
		sim/is61wv5128bll_model.sv sim/tb_sram_snapshot.sv
	$(VVP) $(BUILD_DIR)/tb_sram_snapshot_full
	$(IVERILOG) -g2012 -Wall -DXILINX -s sonar_top -t null \
		$(RTL) rtl/pdm_clock_7series.sv rtl/sonar_top.sv \
		sim/xilinx_7series_stubs.sv
	@echo "PASS XILINX primitive branches and sonar_top elaborate with compile-only stubs"
	$(PYTHON) sim/check_ports.py

$(BUILD_DIR):
	mkdir -p $@

clean:
	rm -rf $(BUILD_DIR)
