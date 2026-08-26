#!/usr/bin/env python3
"""Deterministic electrical checks for the Sonar v1 PDM receive design."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MicTiming:
    name: str
    clock_hz: float
    assert_max_ns: float
    high_z_min_ns: float


SPH0641 = MicTiming("SPH0641LU4H-1", 3_072_000, 40.0, 3.0)
ICS41352 = MicTiming("ICS-41352 alternate", 4_800_000, 50.0, 5.0)

# Board-level allocation, not a manufacturer specification. It includes clock-buffer
# output skew, unequal loading, and PCB clock/data route mismatch and must be checked
# in layout and at bring-up.
BOARD_SKEW_BUDGET_NS = 0.500

# AMD DS181 v1.27.1, XC7A35T-1: direct ILOGIC D-to-CLK setup/hold and CPG236
# package skew. These are device numbers; Vivado must still time the placed design.
FPGA_SETUP_NS = 0.010
FPGA_HOLD_NS = 0.330
FPGA_PACKAGE_SKEW_NS = 0.048


def timing_margin(mic: MicTiming) -> tuple[float, float, float]:
    half_period_ns = 0.5e9 / mic.clock_hz
    setup_margin_ns = (
        half_period_ns
        - mic.assert_max_ns
        - BOARD_SKEW_BUDGET_NS
        - FPGA_PACKAGE_SKEW_NS
        - FPGA_SETUP_NS
    )
    hold_margin_ns = (
        mic.high_z_min_ns - BOARD_SKEW_BUDGET_NS - FPGA_PACKAGE_SKEW_NS - FPGA_HOLD_NS
    )
    return half_period_ns, setup_margin_ns, hold_margin_ns


def main() -> None:
    print("Sonar v1 PDM RX electrical checks")
    for mic in (SPH0641, ICS41352):
        half_period_ns, setup_margin_ns, hold_margin_ns = timing_margin(mic)
        assert setup_margin_ns > 0
        assert hold_margin_ns > 0
        print(
            f"  {mic.name}: half-period={half_period_ns:.3f} ns, "
            f"setup margin={setup_margin_ns:.3f} ns, "
            f"hold margin={hold_margin_ns:.3f} ns"
        )

    mic_typ_ma = 24 * 0.845
    mic_max_ma_at_1v8 = 24 * 1.000
    period_s = 1 / SPH0641.clock_hz
    buffer_internal_dynamic_ma = 12 * 6e-12 * 3.3 * SPH0641.clock_hz * 1e3
    buffer_known_max_ma = 10.0 + buffer_internal_dynamic_ma
    buffer_pulse_skew_ns = 0.180
    duty_delta_percent = buffer_pulse_skew_ns / (period_s * 1e9) * 100
    print(f"  24 microphones at 1.8 V datasheet condition: {mic_typ_ma:.2f} mA typ")
    print(
        f"  24 microphones at 1.8 V datasheet condition: {mic_max_ma_at_1v8:.2f} mA max"
    )
    print(
        "  CDCLVC1112 known internal current at 3.3 V: "
        f"<= {buffer_known_max_ma:.2f} mA "
        "(10 mA static max + calculated CPD term; load current excluded)"
    )
    print(
        "  Known reference subtotal: "
        f"{mic_max_ma_at_1v8 + buffer_known_max_ma:.2f} mA "
        "(not a 3.3 V rail maximum)"
    )
    print(
        "  Clock-buffer duty range from 180 ps pulse-skew limit: "
        f"{50 - duty_delta_percent:.3f}% to {50 + duty_delta_percent:.3f}%"
    )

    raw_mbps = 24 * SPH0641.clock_hz / 1e6
    raw_mb_s = raw_mbps / 8
    pcm_rate_hz = SPH0641.clock_hz / 24
    half_sample_um = 343.0 * period_s / 2 * 1e6
    phase_32k_deg = 360 * 32_000 * period_s / 2
    print(
        f"  Stream: {raw_mbps:.3f} Mb/s = {raw_mb_s:.3f} MB/s; "
        f"decimate-by-24 => {pcm_rate_hz:.0f} samples/s/channel"
    )
    print(
        f"  Paired-edge offset: {period_s * 0.5e9:.3f} ns = "
        f"{half_sample_um:.2f} um at 343 m/s = {phase_32k_deg:.3f} deg at 32 kHz"
    )

    # Interface-level sanity checks at the worst stated rail points.
    sph_data_high_min_v = 3.135 - 0.45
    sph_data_low_max_v = 0.45
    fpga_vih_v = 2.0
    fpga_vil_v = 0.8
    assert sph_data_high_min_v > fpga_vih_v
    assert sph_data_low_max_v < fpga_vil_v
    print(
        "  SPH data -> Cmod LVCMOS33 DC margins: "
        f"HIGH={sph_data_high_min_v - fpga_vih_v:.3f} V, "
        f"LOW={fpga_vil_v - sph_data_low_max_v:.3f} V"
    )


if __name__ == "__main__":
    main()
