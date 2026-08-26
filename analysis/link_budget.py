#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8,<4", "numpy>=1.26,<3"]
# ///
"""Parametric in-air sonar link-budget model for Sonar v1.

The model deliberately separates published quantities from engineering assumptions.
It is a design/sensitivity tool, not a substitute for calibrated measurements of the
chosen transmitter, microphone, target, and room.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable

# Matplotlib otherwise tries to create a cache in ~/.matplotlib, which is not always
# writable in agent/CI environments.
if "MPLCONFIGDIR" not in os.environ:
    _mpl_cache = Path(tempfile.gettempdir()) / "sonar-link-budget-matplotlib"
    _mpl_cache.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(_mpl_cache)
if "XDG_CACHE_HOME" not in os.environ:
    _xdg_cache = Path(tempfile.gettempdir()) / "sonar-link-budget-cache"
    _xdg_cache.mkdir(parents=True, exist_ok=True)
    os.environ["XDG_CACHE_HOME"] = str(_xdg_cache)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


REFERENCE_PRESSURE_KPA = 101.325
REFERENCE_TEMPERATURE_K = 293.15
TRIPLE_POINT_K = 273.16
MIC_COUNT = 24
DEFAULT_CENTER_FREQUENCY_HZ = 25_000.0
DEFAULT_BANDWIDTH_HZ = 12_000.0
DEFAULT_CHIRP_DURATION_S = 6.6e-3
# The PLAN hand calculation states 30 dB SPL in an 8 kHz band. CLI ambient
# levels keep that reference and are rescaled when the modeled noise bandwidth
# changes.
AMBIENT_REFERENCE_BANDWIDTH_HZ = 8_000.0
DEFAULT_AMBIENT_NOISE_DB_SPL = 30.0
DEFAULT_DETECTION_THRESHOLD_DB = 13.0
DEFAULT_DRIVE_V_RMS = 10.8


@dataclass(frozen=True)
class AcousticNoiseCurve:
    """Equivalent input acoustic noise over a stated reference bandwidth."""

    name: str
    frequencies_hz: tuple[float, ...]
    levels_db_spl: tuple[float, ...]
    reference_bandwidth_hz: float
    uncertainty_db: float
    basis: str

    def self_noise_db_spl(
        self,
        frequency_hz: float | np.ndarray,
        noise_bandwidth_hz: float | None = None,
    ) -> float | np.ndarray:
        if noise_bandwidth_hz is None:
            noise_bandwidth_hz = self.reference_bandwidth_hz
        if noise_bandwidth_hz <= 0.0:
            raise ValueError("noise_bandwidth_hz must be positive")
        frequency = np.asarray(frequency_hz, dtype=float)
        # Acoustic noise powers, not decibel values, add and interpolate.
        reference_power = 10.0 ** (np.asarray(self.levels_db_spl) / 10.0)
        interpolated_power = np.interp(frequency, self.frequencies_hz, reference_power)
        result = 10.0 * np.log10(interpolated_power)
        # Local-white-noise approximation. This is exact only when the spectral
        # density is flat across the analysis band; the center-frequency sweep
        # captures the much slower PDM noise-shaping trend.
        result += 10.0 * np.log10(noise_bandwidth_hz / self.reference_bandwidth_hz)
        return _return_scalar_if_scalar(frequency_hz, result)


@dataclass(frozen=True)
class Transmitter:
    """Free-field on-axis source level at a stated reference drive."""

    name: str
    frequencies_hz: tuple[float, ...]
    source_levels_db_spl_at_1m: tuple[float, ...]
    reference_drive_v_rms: float
    basis: str
    valid_frequency_range_hz: tuple[float, float] | None = None

    def source_level_db_spl(
        self, frequency_hz: float | np.ndarray, drive_v_rms: float
    ) -> float | np.ndarray:
        if not math.isfinite(drive_v_rms) or drive_v_rms <= 0:
            raise ValueError("drive_v_rms must be finite and positive")
        frequency = np.asarray(frequency_hz, dtype=float)
        reference_level = np.interp(
            frequency,
            self.frequencies_hz,
            self.source_levels_db_spl_at_1m,
        )
        # Small-signal pressure is assumed proportional to voltage. Compression and
        # device voltage limits must be applied after the actual part is selected.
        result = reference_level + 20.0 * np.log10(
            drive_v_rms / self.reference_drive_v_rms
        )
        if self.valid_frequency_range_hz is not None:
            valid_minimum, valid_maximum = self.valid_frequency_range_hz
            result = np.where(
                (frequency >= valid_minimum) & (frequency <= valid_maximum),
                result,
                np.nan,
            )
        return _return_scalar_if_scalar(frequency_hz, result)


# Manufacturer ultrasonic SNR curves are stated over 5 kHz analysis bands. The
# analog fallback is an engineering envelope derived from the IM73A135 noise-density
# and response plots; its ultrasonic uncertainty is wider (about +/-5 dB).
OPTION_B_ANALOG = AcousticNoiseCurve(
    name="IM73A135 analog estimate",
    frequencies_hz=(20_000.0, 25_000.0, 32_000.0, 40_000.0),
    levels_db_spl=(15.0, 15.0, 15.0, 15.0),
    reference_bandwidth_hz=5_000.0,
    uncertainty_db=5.0,
    basis="IM73A135 noise density and response; provisional +/-5 dB envelope",
)
OPTION_B_SPV0142 = AcousticNoiseCurve(
    name="SPV0142 analog fallback",
    frequencies_hz=(20_000.0, 25_000.0, 32_000.0, 40_000.0),
    levels_db_spl=(24.2, 24.2, 24.2, 24.2),
    reference_bandwidth_hz=5_000.0,
    uncertainty_db=5.0,
    basis="19 kHz near-ultrasonic SNR extrapolated; provisional +/-5 dB",
)
OPTION_C_ICS_41352 = AcousticNoiseCurve(
    name="ICS-41352 PDM",
    frequencies_hz=(22_500.0, 27_500.0, 32_500.0, 37_500.0),
    levels_db_spl=(16.0, 17.0, 20.0, 24.0),
    reference_bandwidth_hz=5_000.0,
    uncertainty_db=3.0,
    basis="manufacturer ultrasonic SNR Figure 9; visible shaped-noise rise",
)
OPTION_C_T5838 = AcousticNoiseCurve(
    name="T5838 PDM",
    frequencies_hz=(22_500.0, 27_500.0, 32_500.0, 37_500.0),
    levels_db_spl=(13.0, 11.0, 12.0, 14.0),
    reference_bandwidth_hz=5_000.0,
    uncertainty_db=3.0,
    basis="manufacturer ultrasonic SNR Figure 10; values digitized approximately",
)
OPTION_C_ICS_41350_PROXY = replace(
    OPTION_C_ICS_41352,
    name="ICS-41350 via ICS-41352 proxy",
    uncertainty_db=5.0,
    basis="no part-specific ultrasonic noise curve; ICS-41352 nominal +/-5 dB",
)
OPTION_C_SPH0641_PROXY = replace(
    OPTION_C_ICS_41352,
    name="SPH0641LU4H via ICS-41352 proxy",
    uncertainty_db=5.0,
    basis="no part-specific ultrasonic noise curve; ICS-41352 nominal +/-5 dB",
)
# Until T-002/T-008 selects a microphone, use the noisier of the two candidates
# with direct ultrasonic-noise data as the provisional primary curve. This does not
# prove that it upper-bounds the ICS-41350 or SPH0641LU4H proxies.
OPTION_C_PDM = OPTION_C_ICS_41352


# MA40S4S's 40 kHz datum normalizes to about 109.5 dB SPL at 1 m when its
# 120 dB-at-0.3 m test is geometrically spread to 1 m. Its published response only
# reaches 30 kHz, so the primary 20-29 kHz band is intentionally returned as NaN.
MA40S4S = Transmitter(
    name="Murata MA40S4S narrowband",
    frequencies_hz=(30_000.0, 35_000.0, 40_000.0),
    source_levels_db_spl_at_1m=(69.5, 87.5, 109.5),
    reference_drive_v_rms=10.0,
    basis="Murata datasheet response digitized and normalized from 0.3 m to 1 m",
    valid_frequency_range_hz=(30_000.0, 40_000.0),
)
WIDEBAND_PIEZO_TARGET = Transmitter(
    name="Representative wideband piezo placeholder",
    frequencies_hz=(20_000.0, 25_000.0, 32_000.0, 40_000.0),
    source_levels_db_spl_at_1m=(104.0, 104.0, 104.0, 104.0),
    reference_drive_v_rms=10.8,
    basis="CTS KSN1197A class scaled from 2.83 Vrms; provisional +/-10 dB",
    valid_frequency_range_hz=(20_000.0, 40_000.0),
)

TARGET_STRENGTH_DB = {
    "wall": 20.0,
    "person": -10.0,
    "small object": -30.0,
}


def _return_scalar_if_scalar(
    original: float | np.ndarray, result: np.ndarray
) -> float | np.ndarray:
    if np.ndim(original) == 0:
        return float(np.asarray(result))
    return result


def atmospheric_absorption_db_per_m(
    frequency_hz: float | np.ndarray,
    temperature_c: float = 20.0,
    relative_humidity_percent: float = 50.0,
    pressure_kpa: float = REFERENCE_PRESSURE_KPA,
) -> float | np.ndarray:
    """Return atmospheric attenuation in dB/m using ISO 9613-1 equations.

    The implementation follows the standard relaxation-frequency formulation. The
    relative humidity argument is a percentage in [0, 100], and frequency is in Hz.
    """

    if temperature_c <= -273.15:
        raise ValueError("temperature_c must be above absolute zero")
    if not 0.0 <= relative_humidity_percent <= 100.0:
        raise ValueError("relative_humidity_percent must be in [0, 100]")
    if pressure_kpa <= 0.0:
        raise ValueError("pressure_kpa must be positive")

    frequency = np.asarray(frequency_hz, dtype=float)
    if np.any(frequency <= 0.0):
        raise ValueError("frequency_hz must be positive")

    temperature_k = temperature_c + 273.15
    temperature_ratio = temperature_k / REFERENCE_TEMPERATURE_K
    pressure_ratio = pressure_kpa / REFERENCE_PRESSURE_KPA

    saturation_pressure_ratio = 10.0 ** (
        -6.8346 * (TRIPLE_POINT_K / temperature_k) ** 1.261 + 4.6151
    )
    molar_water_vapor_percent = (
        relative_humidity_percent * saturation_pressure_ratio / pressure_ratio
    )

    oxygen_relaxation_hz = pressure_ratio * (
        24.0
        + 4.04e4
        * molar_water_vapor_percent
        * (0.02 + molar_water_vapor_percent)
        / (0.391 + molar_water_vapor_percent)
    )
    nitrogen_relaxation_hz = (
        pressure_ratio
        * temperature_ratio**-0.5
        * (
            9.0
            + 280.0
            * molar_water_vapor_percent
            * np.exp(-4.17 * (temperature_ratio ** (-1.0 / 3.0) - 1.0))
        )
    )

    classical = 1.84e-11 * pressure_ratio**-1.0 * temperature_ratio**0.5
    molecular = temperature_ratio**-2.5 * (
        0.01275
        * np.exp(-2239.1 / temperature_k)
        / (oxygen_relaxation_hz + frequency**2 / oxygen_relaxation_hz)
        + 0.1068
        * np.exp(-3352.0 / temperature_k)
        / (nitrogen_relaxation_hz + frequency**2 / nitrogen_relaxation_hz)
    )
    result = 8.686 * frequency**2 * (classical + molecular)
    return _return_scalar_if_scalar(frequency_hz, result)


def speed_of_sound_m_per_s(
    temperature_c: float = 20.0, relative_humidity_percent: float = 50.0
) -> float:
    """Engineering approximation for room-pressure humid air."""

    if not 0.0 <= relative_humidity_percent <= 100.0:
        raise ValueError("relative_humidity_percent must be in [0, 100]")
    return 331.3 + 0.606 * temperature_c + 0.0124 * relative_humidity_percent


def incoherent_db_sum(*levels_db: float | np.ndarray) -> float | np.ndarray:
    """Power-sum independent noise levels expressed in dB."""

    if not levels_db:
        raise ValueError("at least one level is required")
    arrays = np.broadcast_arrays(
        *[np.asarray(level, dtype=float) for level in levels_db]
    )
    result = 10.0 * np.log10(sum(10.0 ** (level / 10.0) for level in arrays))
    if all(np.ndim(level) == 0 for level in levels_db):
        return float(np.asarray(result))
    return result


def total_noise_db_spl(
    frequency_hz: float | np.ndarray,
    microphone: AcousticNoiseCurve,
    ambient_noise_db_spl: float = DEFAULT_AMBIENT_NOISE_DB_SPL,
    noise_bandwidth_hz: float = AMBIENT_REFERENCE_BANDWIDTH_HZ,
) -> float | np.ndarray:
    if noise_bandwidth_hz <= 0.0:
        raise ValueError("noise_bandwidth_hz must be positive")
    ambient_in_band_db_spl = ambient_noise_db_spl + 10.0 * math.log10(
        noise_bandwidth_hz / AMBIENT_REFERENCE_BANDWIDTH_HZ
    )
    return incoherent_db_sum(
        microphone.self_noise_db_spl(frequency_hz, noise_bandwidth_hz),
        ambient_in_band_db_spl,
    )


def integrated_microphone_noise_db_spl(
    microphone: AcousticNoiseCurve,
    minimum_frequency_hz: float,
    maximum_frequency_hz: float,
    sample_count: int = 2_001,
) -> float:
    """Integrate a center-frequency noise envelope across a contiguous band."""

    if minimum_frequency_hz <= 0.0 or maximum_frequency_hz <= minimum_frequency_hz:
        raise ValueError("frequency band must be positive and increasing")
    if sample_count < 2:
        raise ValueError("sample_count must be at least 2")
    frequencies_hz = np.linspace(
        minimum_frequency_hz, maximum_frequency_hz, sample_count
    )
    reference_levels_db = np.asarray(
        microphone.self_noise_db_spl(frequencies_hz, microphone.reference_bandwidth_hz)
    )
    noise_power_density = (
        10.0 ** (reference_levels_db / 10.0) / microphone.reference_bandwidth_hz
    )
    integrated_power = float(
        np.sum(
            0.5
            * (noise_power_density[:-1] + noise_power_density[1:])
            * np.diff(frequencies_hz)
        )
    )
    return 10.0 * math.log10(integrated_power)


def integrated_total_noise_db_spl(
    microphone: AcousticNoiseCurve,
    minimum_frequency_hz: float,
    maximum_frequency_hz: float,
    ambient_noise_db_spl: float = DEFAULT_AMBIENT_NOISE_DB_SPL,
) -> float:
    bandwidth_hz = maximum_frequency_hz - minimum_frequency_hz
    microphone_noise = integrated_microphone_noise_db_spl(
        microphone, minimum_frequency_hz, maximum_frequency_hz
    )
    ambient_noise = ambient_noise_db_spl + 10.0 * math.log10(
        bandwidth_hz / AMBIENT_REFERENCE_BANDWIDTH_HZ
    )
    return float(incoherent_db_sum(microphone_noise, ambient_noise))


def array_gain_db(microphone_count: int = MIC_COUNT) -> float:
    if microphone_count <= 0:
        raise ValueError("microphone_count must be positive")
    return 10.0 * math.log10(microphone_count)


def pulse_compression_gain_db(
    bandwidth_hz: float = DEFAULT_BANDWIDTH_HZ,
    chirp_duration_s: float = DEFAULT_CHIRP_DURATION_S,
    implementation_loss_db: float = 0.0,
) -> float:
    if bandwidth_hz <= 0.0 or chirp_duration_s <= 0.0:
        raise ValueError("bandwidth_hz and chirp_duration_s must be positive")
    return (
        10.0 * math.log10(max(1.0, bandwidth_hz * chirp_duration_s))
        - implementation_loss_db
    )


def blind_zone_m(
    chirp_duration_s: float,
    ringdown_s: float = 0.0,
    temperature_c: float = 20.0,
    relative_humidity_percent: float = 50.0,
) -> float:
    """Conservative blanked-receiver range c*(TX + recovery)/2.

    Sonar v1 has separate TX and RX elements, so this is not a fundamental geometric
    blind zone. It applies when direct leakage or recovery forces RX to be blanked.
    """

    if chirp_duration_s < 0.0 or ringdown_s < 0.0:
        raise ValueError("chirp_duration_s and ringdown_s must be non-negative")
    speed = speed_of_sound_m_per_s(temperature_c, relative_humidity_percent)
    return speed * (chirp_duration_s + ringdown_s) / 2.0


def range_resolution_m(
    bandwidth_hz: float,
    temperature_c: float = 20.0,
    relative_humidity_percent: float = 50.0,
) -> float:
    if bandwidth_hz <= 0.0:
        raise ValueError("bandwidth_hz must be positive")
    return speed_of_sound_m_per_s(temperature_c, relative_humidity_percent) / (
        2.0 * bandwidth_hz
    )


def sonar_margin_db(
    range_m: float | np.ndarray,
    source_level_db_spl_at_1m: float | np.ndarray,
    target_strength_db: float,
    absorption_db_per_m: float | np.ndarray,
    noise_level_db_spl: float | np.ndarray,
    processing_gain_db: float,
    detection_threshold_db: float = DEFAULT_DETECTION_THRESHOLD_DB,
) -> float | np.ndarray:
    """Monostatic active-sonar margin with two-way spherical spreading."""

    distance = np.asarray(range_m, dtype=float)
    if np.any(distance <= 0.0):
        raise ValueError("range_m must be positive")
    result = (
        np.asarray(source_level_db_spl_at_1m, dtype=float)
        + target_strength_db
        - 40.0 * np.log10(distance)
        - 2.0 * np.asarray(absorption_db_per_m, dtype=float) * distance
        - np.asarray(noise_level_db_spl, dtype=float)
        + processing_gain_db
        - detection_threshold_db
    )
    return _return_scalar_if_scalar(range_m, result)


def max_detectable_range_m(
    source_level_db_spl_at_1m: float,
    target_strength_db: float,
    absorption_db_per_m: float,
    noise_level_db_spl: float,
    processing_gain_db: float,
    detection_threshold_db: float = DEFAULT_DETECTION_THRESHOLD_DB,
    minimum_range_m: float = 0.05,
    search_limit_m: float = 200.0,
) -> float:
    """Solve the monotonic margin=0 crossing by bisection."""

    parameters = (
        source_level_db_spl_at_1m,
        target_strength_db,
        absorption_db_per_m,
        noise_level_db_spl,
        processing_gain_db,
        detection_threshold_db,
        minimum_range_m,
        search_limit_m,
    )
    if not all(math.isfinite(value) for value in parameters):
        raise ValueError("max-range inputs must all be finite")
    if minimum_range_m <= 0.0 or search_limit_m <= minimum_range_m:
        raise ValueError("range search bounds must be positive and increasing")
    if absorption_db_per_m < 0.0:
        raise ValueError("absorption_db_per_m must be non-negative")

    def margin(distance_m: float) -> float:
        return float(
            sonar_margin_db(
                distance_m,
                source_level_db_spl_at_1m,
                target_strength_db,
                absorption_db_per_m,
                noise_level_db_spl,
                processing_gain_db,
                detection_threshold_db,
            )
        )

    if margin(minimum_range_m) < 0.0:
        return 0.0
    if margin(search_limit_m) >= 0.0:
        return search_limit_m

    low = minimum_range_m
    high = search_limit_m
    for _ in range(80):
        midpoint = (low + high) / 2.0
        if margin(midpoint) >= 0.0:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


def _processing_gain_db(bandwidth_hz: float, chirp_duration_s: float) -> float:
    return array_gain_db() + pulse_compression_gain_db(bandwidth_hz, chirp_duration_s)


def _plot_absorption(
    output_dir: Path, temperature_c: float, pressure_kpa: float
) -> None:
    frequencies_hz = np.linspace(20_000.0, 40_000.0, 241)
    fig, ax = plt.subplots(figsize=(8.0, 4.8), constrained_layout=True)
    for humidity in (20.0, 50.0, 80.0):
        attenuation = atmospheric_absorption_db_per_m(
            frequencies_hz, temperature_c, humidity, pressure_kpa
        )
        ax.plot(frequencies_hz / 1_000.0, attenuation, label=f"{humidity:.0f}% RH")
    ax.set(
        title=f"ISO 9613-1 atmospheric absorption at {temperature_c:.0f} °C",
        xlabel="Frequency (kHz)",
        ylabel="One-way absorption (dB/m)",
        xlim=(20.0, 40.0),
    )
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.savefig(output_dir / "absorption-vs-frequency.png", dpi=160)
    plt.close(fig)


def _plot_microphone_noise(output_dir: Path) -> None:
    frequencies_hz = np.linspace(20_000.0, 40_000.0, 241)
    plot_bandwidth_hz = AMBIENT_REFERENCE_BANDWIDTH_HZ
    option_b = np.asarray(
        OPTION_B_ANALOG.self_noise_db_spl(frequencies_hz, plot_bandwidth_hz)
    )
    option_c = np.asarray(
        OPTION_C_PDM.self_noise_db_spl(frequencies_hz, plot_bandwidth_hz)
    )
    t5838 = np.asarray(
        OPTION_C_T5838.self_noise_db_spl(frequencies_hz, plot_bandwidth_hz)
    )

    fig, (ax_noise, ax_delta) = plt.subplots(
        2,
        1,
        figsize=(8.0, 7.2),
        sharex=True,
        constrained_layout=True,
        height_ratios=(1.35, 1.0),
    )
    for microphone in (
        OPTION_B_ANALOG,
        OPTION_B_SPV0142,
        OPTION_C_ICS_41352,
        OPTION_C_T5838,
    ):
        ax_noise.plot(
            frequencies_hz / 1_000.0,
            microphone.self_noise_db_spl(frequencies_hz, plot_bandwidth_hz),
            label=microphone.name,
        )
    ax_noise.set(
        title="Manufacturer-derived 8 kHz-equivalent microphone noise",
        ylabel="Equivalent input noise (dB SPL)",
    )
    ax_noise.grid(True, alpha=0.3)
    ax_noise.legend()

    ax_delta.plot(
        frequencies_hz / 1_000.0,
        option_c - option_b,
        color="black",
        linestyle="--",
        label="ICS-41352 minus IM73A135, mic only",
    )
    ax_delta.plot(
        frequencies_hz / 1_000.0,
        t5838 - option_b,
        color="grey",
        linestyle=":",
        label="T5838 minus IM73A135, mic only",
    )
    for ambient_noise in (20.0, 30.0, 40.0):
        total_b = np.asarray(
            total_noise_db_spl(
                frequencies_hz,
                OPTION_B_ANALOG,
                ambient_noise,
                plot_bandwidth_hz,
            ),
            dtype=float,
        )
        total_c = np.asarray(
            total_noise_db_spl(
                frequencies_hz,
                OPTION_C_PDM,
                ambient_noise,
                plot_bandwidth_hz,
            ),
            dtype=float,
        )
        ax_delta.plot(
            frequencies_hz / 1_000.0,
            total_c - total_b,
            label=f"With {ambient_noise:.0f} dB SPL ambient",
        )
    ax_delta.set(
        xlabel="Frequency (kHz)",
        ylabel="PDM minus IM73A135 noise (dB)",
        xlim=(20.0, 40.0),
    )
    ax_delta.grid(True, alpha=0.3)
    ax_delta.legend(fontsize=8)
    fig.savefig(output_dir / "option-b-vs-c-noise.png", dpi=160)
    plt.close(fig)


def _plot_anchor_margin(
    output_dir: Path,
    temperature_c: float,
    humidity_percent: float,
    pressure_kpa: float,
    ambient_noise_db_spl: float,
    drive_v_rms: float,
    bandwidth_hz: float,
    chirp_duration_s: float,
) -> None:
    distances_m = np.geomspace(0.25, 80.0, 500)
    processing_gain = _processing_gain_db(bandwidth_hz, chirp_duration_s)
    source_level = WIDEBAND_PIEZO_TARGET.source_level_db_spl(
        DEFAULT_CENTER_FREQUENCY_HZ, drive_v_rms
    )
    iso_absorption = atmospheric_absorption_db_per_m(
        DEFAULT_CENTER_FREQUENCY_HZ,
        temperature_c,
        humidity_percent,
        pressure_kpa,
    )

    anchor_margin = sonar_margin_db(
        distances_m,
        110.0,
        TARGET_STRENGTH_DB["person"],
        0.5,
        30.0,
        13.8 + 19.0,
        DEFAULT_DETECTION_THRESHOLD_DB,
    )
    analog_margin = sonar_margin_db(
        distances_m,
        source_level,
        TARGET_STRENGTH_DB["person"],
        iso_absorption,
        total_noise_db_spl(
            DEFAULT_CENTER_FREQUENCY_HZ,
            OPTION_B_ANALOG,
            ambient_noise_db_spl,
            bandwidth_hz,
        ),
        processing_gain,
    )
    pdm_margin = sonar_margin_db(
        distances_m,
        source_level,
        TARGET_STRENGTH_DB["person"],
        iso_absorption,
        total_noise_db_spl(
            DEFAULT_CENTER_FREQUENCY_HZ,
            OPTION_C_PDM,
            ambient_noise_db_spl,
            bandwidth_hz,
        ),
        processing_gain,
    )

    fig, ax = plt.subplots(figsize=(8.0, 5.0), constrained_layout=True)
    ax.fill_between(
        distances_m,
        pdm_margin - 10.0,
        pdm_margin + 10.0,
        alpha=0.12,
        color="tab:green",
        label="Wideband source-level uncertainty (+/-10 dB)",
        zorder=0,
    )
    ax.semilogx(distances_m, anchor_margin, label="PLAN hand-calc anchor")
    ax.semilogx(distances_m, pdm_margin, label="Option C PDM + ISO atmosphere")
    ax.semilogx(
        distances_m,
        analog_margin,
        linestyle="--",
        label="Option B + ISO atmosphere",
    )
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.axvline(10.0, color="grey", linestyle=":", linewidth=1.0)
    ax.set(
        title="Person-target margin at 25 kHz",
        xlabel="Range (m)",
        ylabel="Detection margin (dB)",
        xlim=(0.25, 80.0),
        ylim=(-50.0, 100.0),
    )
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.savefig(output_dir / "person-margin-vs-range.png", dpi=160)
    plt.close(fig)


def _plot_max_range(
    output_dir: Path,
    temperature_c: float,
    humidity_percent: float,
    pressure_kpa: float,
    ambient_noise_db_spl: float,
    drive_v_rms: float,
    bandwidth_hz: float,
    chirp_duration_s: float,
) -> None:
    frequencies_hz = np.linspace(20_000.0, 40_000.0, 161)
    absorption = np.asarray(
        atmospheric_absorption_db_per_m(
            frequencies_hz,
            temperature_c,
            humidity_percent,
            pressure_kpa,
        )
    )
    noise = np.asarray(
        total_noise_db_spl(
            frequencies_hz,
            OPTION_C_PDM,
            ambient_noise_db_spl,
            bandwidth_hz,
        )
    )
    processing_gain = _processing_gain_db(bandwidth_hz, chirp_duration_s)

    fig, axes = plt.subplots(
        1, 2, figsize=(12.0, 4.8), sharey=True, constrained_layout=True
    )
    for ax, transmitter in zip(axes, (WIDEBAND_PIEZO_TARGET, MA40S4S), strict=True):
        source_levels = np.asarray(
            transmitter.source_level_db_spl(frequencies_hz, drive_v_rms)
        )
        for target_name, target_strength in TARGET_STRENGTH_DB.items():
            ranges = []
            for source_level, alpha, noise_level in zip(
                source_levels, absorption, noise, strict=True
            ):
                if np.isfinite(source_level):
                    ranges.append(
                        max_detectable_range_m(
                            float(source_level),
                            target_strength,
                            float(alpha),
                            float(noise_level),
                            processing_gain,
                        )
                    )
                else:
                    ranges.append(np.nan)
            ax.plot(
                frequencies_hz / 1_000.0,
                ranges,
                label=f"{target_name} ({target_strength:+.0f} dB TS)",
            )
        ax.set(
            title=transmitter.name,
            xlabel="Frequency (kHz)",
            xlim=(20.0, 40.0),
            ylim=(0.0, 60.0),
        )
        if transmitter is MA40S4S:
            ax.axvspan(20.0, 30.0, color="grey", alpha=0.1)
            ax.text(
                25.0,
                48.0,
                "No published SPL data",
                color="dimgray",
                ha="center",
                va="center",
                fontsize=9,
            )
        ax.grid(True, alpha=0.3)
    axes[0].set_ylabel("Zero-margin range (m)")
    axes[1].legend(fontsize=8)
    fig.suptitle("Provisional ICS-41352 PDM maximum range by target and transmitter")
    fig.savefig(output_dir / "max-range-vs-frequency.png", dpi=160)
    plt.close(fig)


def _plot_blind_zone(
    output_dir: Path,
    temperature_c: float,
    humidity_percent: float,
    bandwidth_hz: float,
) -> None:
    durations_ms = np.linspace(0.1, 12.0, 240)
    fig, ax_range = plt.subplots(figsize=(8.0, 4.8), constrained_layout=True)
    for ringdown_ms in (0.0, 0.25, 1.0):
        zones = [
            blind_zone_m(
                duration_ms / 1_000.0,
                ringdown_ms / 1_000.0,
                temperature_c,
                humidity_percent,
            )
            for duration_ms in durations_ms
        ]
        ax_range.plot(
            durations_ms,
            zones,
            label=f"{ringdown_ms:g} ms recovery/guard",
        )
    ax_range.set(
        title="Chirp processing gain versus conservative blind zone",
        xlabel="Chirp duration (ms)",
        ylabel="Blind zone (m)",
        xlim=(0.0, 12.0),
    )
    ax_range.grid(True, alpha=0.3)
    ax_range.legend(loc="upper left", fontsize=8)

    ax_gain = ax_range.twinx()
    gains_db = [
        pulse_compression_gain_db(bandwidth_hz, duration_ms / 1_000.0)
        for duration_ms in durations_ms
    ]
    ax_gain.plot(durations_ms, gains_db, color="black", linestyle="--")
    ax_gain.set_ylabel("Pulse-compression gain (dB)")
    fig.savefig(output_dir / "blind-zone-vs-chirp.png", dpi=160)
    plt.close(fig)


def _write_blind_zone_csv(
    output_dir: Path,
    temperature_c: float,
    humidity_percent: float,
    bandwidth_hz: float,
    ringdown_s: float,
) -> None:
    durations_ms = (0.5, 1.0, 2.0, 4.0, 6.67, 8.0)
    with (output_dir / "blind-zone-schedule.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            (
                "chirp_duration_ms",
                "time_bandwidth_product",
                "pulse_compression_gain_db",
                "blind_zone_tx_only_m",
                "blind_zone_wideband_0p25ms_guard_m",
                "blind_zone_narrowband_1ms_guard_m",
                "configured_guard_ms",
                "blind_zone_configured_guard_m",
            )
        )
        for duration_ms in durations_ms:
            duration_s = duration_ms / 1_000.0
            writer.writerow(
                (
                    f"{duration_ms:.2f}",
                    f"{bandwidth_hz * duration_s:.2f}",
                    f"{pulse_compression_gain_db(bandwidth_hz, duration_s):.2f}",
                    f"{blind_zone_m(duration_s, 0.0, temperature_c, humidity_percent):.3f}",
                    f"{blind_zone_m(duration_s, 0.00025, temperature_c, humidity_percent):.3f}",
                    f"{blind_zone_m(duration_s, 0.001, temperature_c, humidity_percent):.3f}",
                    f"{ringdown_s * 1_000.0:.3f}",
                    f"{blind_zone_m(duration_s, ringdown_s, temperature_c, humidity_percent):.3f}",
                )
            )


def _write_microphone_summary_csv(
    output_dir: Path, ambient_noise_db_spl: float
) -> None:
    microphones = (
        ("B", OPTION_B_ANALOG),
        ("B", OPTION_B_SPV0142),
        ("C", OPTION_C_ICS_41352),
        ("C proxy", OPTION_C_ICS_41350_PROXY),
        ("C proxy", OPTION_C_SPH0641_PROXY),
        ("C", OPTION_C_T5838),
    )
    bands = (("20-32", 20_000.0, 32_000.0), ("20-40", 20_000.0, 40_000.0))
    with (output_dir / "microphone-band-summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            (
                "band_khz",
                "option",
                "microphone_curve",
                "mic_only_noise_db_spl",
                "mic_only_delta_vs_im73a135_db",
                "total_with_ambient_db_spl",
                "total_delta_vs_im73a135_db",
                "curve_uncertainty_db",
            )
        )
        for band_name, minimum_hz, maximum_hz in bands:
            baseline_mic = integrated_microphone_noise_db_spl(
                OPTION_B_ANALOG, minimum_hz, maximum_hz
            )
            baseline_total = integrated_total_noise_db_spl(
                OPTION_B_ANALOG,
                minimum_hz,
                maximum_hz,
                ambient_noise_db_spl,
            )
            for option, microphone in microphones:
                mic_noise = integrated_microphone_noise_db_spl(
                    microphone, minimum_hz, maximum_hz
                )
                total_noise = integrated_total_noise_db_spl(
                    microphone,
                    minimum_hz,
                    maximum_hz,
                    ambient_noise_db_spl,
                )
                writer.writerow(
                    (
                        band_name,
                        option,
                        microphone.name,
                        f"{mic_noise:.2f}",
                        f"{mic_noise - baseline_mic:+.2f}",
                        f"{total_noise:.2f}",
                        f"{total_noise - baseline_total:+.2f}",
                        f"{microphone.uncertainty_db:.1f}",
                    )
                )


def _write_max_range_csv(
    output_dir: Path,
    temperature_c: float,
    humidity_percent: float,
    pressure_kpa: float,
    ambient_noise_db_spl: float,
    drive_v_rms: float,
    bandwidth_hz: float,
    chirp_duration_s: float,
) -> None:
    processing_gain = _processing_gain_db(bandwidth_hz, chirp_duration_s)
    with (output_dir / "max-range-summary.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            (
                "transmitter",
                "frequency_khz",
                "target",
                "target_strength_db",
                "source_level_db_spl_at_1m",
                "absorption_db_per_m",
                "total_noise_db_spl",
                "max_range_m",
            )
        )
        for transmitter in (WIDEBAND_PIEZO_TARGET, MA40S4S):
            for frequency_hz in (20_000.0, 25_000.0, 32_000.0, 40_000.0):
                source_level = float(
                    transmitter.source_level_db_spl(frequency_hz, drive_v_rms)
                )
                absorption = float(
                    atmospheric_absorption_db_per_m(
                        frequency_hz,
                        temperature_c,
                        humidity_percent,
                        pressure_kpa,
                    )
                )
                noise = float(
                    total_noise_db_spl(
                        frequency_hz,
                        OPTION_C_PDM,
                        ambient_noise_db_spl,
                        bandwidth_hz,
                    )
                )
                for target_name, target_strength in TARGET_STRENGTH_DB.items():
                    maximum_range = (
                        max_detectable_range_m(
                            source_level,
                            target_strength,
                            absorption,
                            noise,
                            processing_gain,
                        )
                        if math.isfinite(source_level)
                        else math.nan
                    )
                    writer.writerow(
                        (
                            transmitter.name,
                            f"{frequency_hz / 1_000.0:.0f}",
                            target_name,
                            f"{target_strength:.1f}",
                            f"{source_level:.2f}"
                            if math.isfinite(source_level)
                            else "",
                            f"{absorption:.4f}",
                            f"{noise:.2f}",
                            f"{maximum_range:.2f}"
                            if math.isfinite(maximum_range)
                            else "",
                        )
                    )


def _assert_sanity() -> dict[str, float]:
    anchor_margin_10m = float(
        sonar_margin_db(
            10.0,
            110.0,
            -10.0,
            0.5,
            30.0,
            13.8 + 19.0,
            13.0,
        )
    )
    expected_anchor_margin_10m = 90.0 - 40.0 * math.log10(10.0) - 10.0
    assert abs(anchor_margin_10m - expected_anchor_margin_10m) <= 0.3

    standard_alpha_25khz = float(atmospheric_absorption_db_per_m(25_000.0, 20.0, 50.0))
    assert 0.6 < standard_alpha_25khz < 0.9
    # ISO 9613-1 Table 1 gives 25.8 dB/km for this condition.
    iso_table_alpha_10khz = float(
        atmospheric_absorption_db_per_m(10_000.0, -20.0, 50.0)
    )
    assert abs(iso_table_alpha_10khz * 1_000.0 - 25.8) < 0.1
    assert abs(array_gain_db() - 13.802) < 0.01
    assert abs(pulse_compression_gain_db() - 18.99) < 0.05
    assert 0.013 < range_resolution_m(DEFAULT_BANDWIDTH_HZ) < 0.015
    pdm_penalty_20_32khz = integrated_microphone_noise_db_spl(
        OPTION_C_ICS_41352, 20_000.0, 32_000.0
    ) - integrated_microphone_noise_db_spl(OPTION_B_ANALOG, 20_000.0, 32_000.0)
    assert 2.2 < pdm_penalty_20_32khz < 2.5
    assert math.isnan(float(MA40S4S.source_level_db_spl(25_000.0, 10.0)))
    return {
        "anchor_margin_10m_db": anchor_margin_10m,
        "iso_alpha_25khz_db_per_m": standard_alpha_25khz,
        "array_gain_db": array_gain_db(),
        "pulse_compression_gain_db": pulse_compression_gain_db(),
    }


def generate_outputs(args: argparse.Namespace) -> dict[str, float]:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    sanity = _assert_sanity()
    _plot_absorption(output_dir, args.temperature_c, args.pressure_kpa)
    _plot_microphone_noise(output_dir)
    _plot_anchor_margin(
        output_dir,
        args.temperature_c,
        args.humidity_percent,
        args.pressure_kpa,
        args.ambient_noise_db_spl,
        args.drive_v_rms,
        args.bandwidth_khz * 1_000.0,
        args.chirp_duration_ms / 1_000.0,
    )
    _plot_max_range(
        output_dir,
        args.temperature_c,
        args.humidity_percent,
        args.pressure_kpa,
        args.ambient_noise_db_spl,
        args.drive_v_rms,
        args.bandwidth_khz * 1_000.0,
        args.chirp_duration_ms / 1_000.0,
    )
    _plot_blind_zone(
        output_dir,
        args.temperature_c,
        args.humidity_percent,
        args.bandwidth_khz * 1_000.0,
    )
    _write_blind_zone_csv(
        output_dir,
        args.temperature_c,
        args.humidity_percent,
        args.bandwidth_khz * 1_000.0,
        args.ringdown_ms / 1_000.0,
    )
    _write_microphone_summary_csv(output_dir, args.ambient_noise_db_spl)
    _write_max_range_csv(
        output_dir,
        args.temperature_c,
        args.humidity_percent,
        args.pressure_kpa,
        args.ambient_noise_db_spl,
        args.drive_v_rms,
        args.bandwidth_khz * 1_000.0,
        args.chirp_duration_ms / 1_000.0,
    )

    frequency_hz = DEFAULT_CENTER_FREQUENCY_HZ
    absorption = float(
        atmospheric_absorption_db_per_m(
            frequency_hz,
            args.temperature_c,
            args.humidity_percent,
            args.pressure_kpa,
        )
    )
    noise = float(
        total_noise_db_spl(
            frequency_hz,
            OPTION_C_PDM,
            args.ambient_noise_db_spl,
            args.bandwidth_khz * 1_000.0,
        )
    )
    processing_gain = _processing_gain_db(
        args.bandwidth_khz * 1_000.0, args.chirp_duration_ms / 1_000.0
    )
    source_level = float(
        WIDEBAND_PIEZO_TARGET.source_level_db_spl(frequency_hz, args.drive_v_rms)
    )
    primary_margin_10m = float(
        sonar_margin_db(
            10.0,
            source_level,
            TARGET_STRENGTH_DB["person"],
            absorption,
            noise,
            processing_gain,
        )
    )
    primary_max_range = max_detectable_range_m(
        source_level,
        TARGET_STRENGTH_DB["person"],
        absorption,
        noise,
        processing_gain,
    )
    im73_mic_band_noise = integrated_microphone_noise_db_spl(
        OPTION_B_ANALOG, 20_000.0, 32_000.0
    )
    ics_mic_band_noise = integrated_microphone_noise_db_spl(
        OPTION_C_ICS_41352, 20_000.0, 32_000.0
    )
    im73_total_band_noise = integrated_total_noise_db_spl(
        OPTION_B_ANALOG,
        20_000.0,
        32_000.0,
        args.ambient_noise_db_spl,
    )
    ics_total_band_noise = integrated_total_noise_db_spl(
        OPTION_C_ICS_41352,
        20_000.0,
        32_000.0,
        args.ambient_noise_db_spl,
    )
    sanity.update(
        {
            "primary_margin_10m_db": primary_margin_10m,
            "primary_person_max_range_m": primary_max_range,
            "primary_total_noise_25khz_db_spl": noise,
            "primary_absorption_25khz_db_per_m": absorption,
            "scenario_processing_gain_db": processing_gain,
            "scenario_temperature_c": args.temperature_c,
            "scenario_humidity_percent": args.humidity_percent,
            "pdm_mic_only_penalty_20_32khz_db": (
                ics_mic_band_noise - im73_mic_band_noise
            ),
            "pdm_total_penalty_20_32khz_db": (
                ics_total_band_noise - im73_total_band_noise
            ),
            "chirp_duration_ms": args.chirp_duration_ms,
            "ringdown_ms": args.ringdown_ms,
            "bandwidth_khz": args.bandwidth_khz,
            "range_resolution_m": range_resolution_m(
                args.bandwidth_khz * 1_000.0,
                args.temperature_c,
                args.humidity_percent,
            ),
            "blind_zone_with_guard_m": blind_zone_m(
                args.chirp_duration_ms / 1_000.0,
                args.ringdown_ms / 1_000.0,
                args.temperature_c,
                args.humidity_percent,
            ),
        }
    )
    return sanity


def _finite_float(value: str) -> float:
    try:
        result = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a number") from error
    if not math.isfinite(result):
        raise argparse.ArgumentTypeError("must be finite")
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "generated",
        help="directory for plots and CSV tables",
    )
    parser.add_argument("--temperature-c", type=_finite_float, default=20.0)
    parser.add_argument("--humidity-percent", type=_finite_float, default=50.0)
    parser.add_argument(
        "--pressure-kpa", type=_finite_float, default=REFERENCE_PRESSURE_KPA
    )
    parser.add_argument(
        "--ambient-noise-db-spl",
        type=_finite_float,
        default=DEFAULT_AMBIENT_NOISE_DB_SPL,
        help="ambient acoustic noise referenced to an 8 kHz band",
    )
    parser.add_argument(
        "--drive-v-rms",
        type=_finite_float,
        default=DEFAULT_DRIVE_V_RMS,
        help="sine or fundamental-equivalent transmitter drive",
    )
    parser.add_argument(
        "--bandwidth-khz",
        type=_finite_float,
        default=12.0,
        help="chirp and receiver noise bandwidth",
    )
    parser.add_argument("--chirp-duration-ms", type=_finite_float, default=6.6)
    parser.add_argument("--ringdown-ms", type=_finite_float, default=1.0)
    return parser


def _format_summary(summary: dict[str, float]) -> Iterable[str]:
    yield "Sonar v1 link-budget outputs generated"
    yield f"  Anchor margin at 10 m: {summary['anchor_margin_10m_db']:.2f} dB"
    yield f"  24-channel array gain: {summary['array_gain_db']:.2f} dB"
    yield (
        "  Scenario pulse-compression gain: "
        f"{summary['scenario_processing_gain_db'] - summary['array_gain_db']:.2f} dB"
    )
    yield (
        f"  Scenario absorption at 25 kHz ({summary['scenario_temperature_c']:g} C, "
        f"{summary['scenario_humidity_percent']:g}% RH): "
        f"{summary['primary_absorption_25khz_db_per_m']:.3f} dB/m"
    )
    yield (
        "  Primary Option C person margin at 10 m: "
        f"{summary['primary_margin_10m_db']:.2f} dB"
    )
    yield (
        "  Primary Option C person zero-margin range: "
        f"{summary['primary_person_max_range_m']:.2f} m"
    )
    yield (
        "  ICS-41352 mic-only / ambient-context penalty over 20-32 kHz: "
        f"{summary['pdm_mic_only_penalty_20_32khz_db']:.2f} / "
        f"{summary['pdm_total_penalty_20_32khz_db']:.2f} dB"
    )
    yield (
        f"  {summary['bandwidth_khz']:.1f} kHz range resolution: "
        f"{summary['range_resolution_m']:.4f} m"
    )
    yield (
        f"  {summary['chirp_duration_ms']:g} ms chirp + "
        f"{summary['ringdown_ms']:g} ms guard blind zone: "
        f"{summary['blind_zone_with_guard_m']:.3f} m"
    )


def main() -> None:
    args = _build_parser().parse_args()
    summary = generate_outputs(args)
    for line in _format_summary(summary):
        print(line)
    print(f"  Output directory: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
