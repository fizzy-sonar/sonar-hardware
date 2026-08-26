# T-020 PLACEHOLDER ONLY -- NOT SAFE FOR BITSTREAM GENERATION.
# T-011 must generate constraints/sonar_cmod_a7.xdc from
# orchestration/pinmap.md. No PACKAGE_PIN assignment is guessed here.

# Timing intent for the documented on-module 12 MHz oscillator. The real XDC must
# bind this port and every PDM/FT245/TX signal to audited Cmod/header pins.
create_clock -name sys_clk_12mhz -period 83.333 [get_ports sys_clk_12mhz]
