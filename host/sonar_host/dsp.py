from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .errors import CalibrationError
from .geometry import array_positions, steering_delays
from .packet import pack_logical_frames, unpack_logical_frames

SOUND_SPEED_M_S = 343.0


@dataclass(frozen=True)
class ChannelCalibration:
    gains: np.ndarray
    sample_delays: np.ndarray


@dataclass(frozen=True)
class BeamScanResult:
    range_m: float
    bearing_deg: float
    elevation_deg: float
    peak_index: int
    peak_value: float
    azimuth_grid_deg: np.ndarray
    beam_peaks: np.ndarray
    beamformed: np.ndarray


@dataclass(frozen=True)
class SyntheticFixture:
    payload: bytes
    capture_frames: int
    raw_clock_hz: int
    sample_rate_hz: float
    chirp: np.ndarray
    truth_range_m: float
    truth_bearing_deg: float
    gain_errors: np.ndarray
    calibration: ChannelCalibration
    positions_m: np.ndarray


def chirp(
    sample_rate_hz: float,
    samples: int,
    *,
    start_hz: float = 20_000.0,
    end_hz: float = 32_000.0,
) -> np.ndarray:
    t = np.arange(samples, dtype=np.float64) / sample_rate_hz
    duration = max(samples - 1, 1) / sample_rate_hz
    phase = 2.0 * np.pi * (
        start_hz * t + 0.5 * (end_hz - start_hz) * t * t / duration
    )
    envelope = np.hanning(samples)
    return np.sin(phase) * envelope


def matched_filter(samples: np.ndarray, reference: np.ndarray) -> np.ndarray:
    x = _as_channel_matrix(samples)
    ref = np.asarray(reference, dtype=np.float64)
    kernel = ref[::-1]
    return np.column_stack(
        [np.convolve(x[:, channel], kernel, mode="same") for channel in range(x.shape[1])]
    )


def decimate_pdm_cic_fir(
    logical_frames: np.ndarray,
    *,
    decimation: int = 24,
    stages: int = 3,
    fir_taps: int = 63,
    fir_cutoff_hz: float = 40_000.0,
    sample_rate_hz: float = 128_000.0,
) -> np.ndarray:
    bits = _as_channel_matrix(logical_frames).astype(np.float64)
    signed = bits * 2.0 - 1.0
    integrated = signed
    for _ in range(stages):
        integrated = np.cumsum(integrated, axis=0)
    decimated = integrated[decimation - 1 :: decimation]
    comb = decimated
    for _ in range(stages):
        comb = np.diff(comb, axis=0, prepend=comb[:1])
    comb /= float(decimation**stages)
    taps = design_lowpass_fir(fir_taps, fir_cutoff_hz, sample_rate_hz)
    return np.column_stack(
        [np.convolve(comb[:, channel], taps, mode="same") for channel in range(comb.shape[1])]
    )


def design_lowpass_fir(taps: int, cutoff_hz: float, sample_rate_hz: float) -> np.ndarray:
    half = (taps - 1) / 2.0
    n = np.arange(taps, dtype=np.float64) - half
    normalized = cutoff_hz / sample_rate_hz
    sinc = 2.0 * normalized * np.sinc(2.0 * normalized * n)
    window = np.hamming(taps)
    kernel = sinc * window
    return kernel / np.sum(kernel)


def default_pair_calibration(
    *,
    sample_rate_hz: float,
    raw_clock_hz: int,
    gains: np.ndarray | None = None,
) -> ChannelCalibration:
    channel_count = 24
    actual_gains = (
        np.ones(channel_count, dtype=np.float64)
        if gains is None
        else np.asarray(gains, dtype=np.float64)
    )
    if actual_gains.shape != (channel_count,):
        raise CalibrationError(f"expected {channel_count} gains, got {actual_gains.shape}")
    delays = np.zeros(channel_count, dtype=np.float64)
    delays[1::2] = -0.5 * sample_rate_hz / raw_clock_hz
    return ChannelCalibration(gains=1.0 / actual_gains, sample_delays=delays)


def apply_calibration(samples: np.ndarray, calibration: ChannelCalibration) -> np.ndarray:
    matrix = _as_channel_matrix(samples).astype(np.float64)
    if calibration.gains.shape != (matrix.shape[1],):
        raise CalibrationError(
            f"gain vector shape {calibration.gains.shape} does not match channel count {matrix.shape[1]}"
        )
    if calibration.sample_delays.shape != (matrix.shape[1],):
        raise CalibrationError(
            f"delay vector shape {calibration.sample_delays.shape} does not match channel count {matrix.shape[1]}"
        )
    calibrated = np.zeros_like(matrix)
    sample_axis = np.arange(matrix.shape[0], dtype=np.float64)
    for channel in range(matrix.shape[1]):
        delayed_axis = sample_axis - calibration.sample_delays[channel]
        shifted = np.interp(
            delayed_axis, sample_axis, matrix[:, channel], left=0.0, right=0.0
        )
        calibrated[:, channel] = shifted * calibration.gains[channel]
    return calibrated


def beamform_delay_and_sum(
    samples: np.ndarray,
    *,
    sample_rate_hz: float,
    delays_s: np.ndarray,
) -> np.ndarray:
    matrix = _as_channel_matrix(samples).astype(np.float64)
    axis = np.arange(matrix.shape[0], dtype=np.float64)
    shifted = np.zeros_like(matrix)
    for channel in range(matrix.shape[1]):
        sample_delay = delays_s[channel] * sample_rate_hz
        shifted[:, channel] = np.interp(
            axis - sample_delay, axis, matrix[:, channel], left=0.0, right=0.0
        )
    return np.mean(shifted, axis=1)


def estimate_range_and_bearing(
    matched: np.ndarray,
    *,
    sample_rate_hz: float,
    reference_length: int,
    positions_m: np.ndarray | None = None,
    azimuth_grid_deg: np.ndarray | None = None,
    elevation_deg: float = 0.0,
) -> BeamScanResult:
    matrix = _as_channel_matrix(matched)
    scan_positions = (
        array_positions() if positions_m is None else np.asarray(positions_m, dtype=np.float64)
    )
    azimuths = (
        np.linspace(-35.0, 35.0, 71, dtype=np.float64)
        if azimuth_grid_deg is None
        else np.asarray(azimuth_grid_deg, dtype=np.float64)
    )
    beamformed_series = []
    peaks = np.zeros_like(azimuths)
    peak_indices = np.zeros_like(azimuths, dtype=np.int64)
    for index, azimuth in enumerate(azimuths):
        delays = -steering_delays(scan_positions, azimuth, elevation_deg)
        beam = beamform_delay_and_sum(matrix, sample_rate_hz=sample_rate_hz, delays_s=delays)
        beamformed_series.append(beam)
        abs_beam = np.abs(beam)
        peak_indices[index] = int(np.argmax(abs_beam))
        peaks[index] = float(abs_beam[peak_indices[index]])
    best = int(np.argmax(peaks))
    peak_index = int(peak_indices[best])
    travel_samples = peak_index - (reference_length // 2)
    travel_time_s = max(travel_samples, 0) / sample_rate_hz
    range_m = travel_time_s * SOUND_SPEED_M_S / 2.0
    return BeamScanResult(
        range_m=range_m,
        bearing_deg=float(azimuths[best]),
        elevation_deg=float(elevation_deg),
        peak_index=peak_index,
        peak_value=float(peaks[best]),
        azimuth_grid_deg=azimuths,
        beam_peaks=peaks,
        beamformed=beamformed_series[best],
    )


def generate_point_target_fixture(
    *,
    range_m: float = 4.2,
    bearing_deg: float = 12.0,
    raw_clock_hz: int = 3_072_000,
    decimation: int = 24,
    output_samples: int = 4096,
    chirp_samples: int = 512,
    pitch_m: float = 0.0075,
    amplitude: float = 0.28,
    noise_std: float = 0.035,
    seed: int = 20260826,
) -> SyntheticFixture:
    sample_rate_hz = raw_clock_hz / decimation
    positions = array_positions(pitch_m)
    gain_errors = np.linspace(0.94, 1.06, positions.shape[0], dtype=np.float64)
    calibration = default_pair_calibration(
        sample_rate_hz=sample_rate_hz,
        raw_clock_hz=raw_clock_hz,
        gains=gain_errors,
    )
    reference = chirp(sample_rate_hz, chirp_samples)
    delays = steering_delays(positions, bearing_deg)
    base_delay_samples = int(round((2.0 * range_m / SOUND_SPEED_M_S) * sample_rate_hz))
    analog = np.zeros((output_samples, positions.shape[0]), dtype=np.float64)
    noise_rng = np.random.default_rng(seed)
    signal_start = base_delay_samples
    for channel in range(positions.shape[0]):
        shifted = _fractional_shift(reference, delays[channel] * sample_rate_hz)
        end = min(output_samples, signal_start + shifted.shape[0])
        analog[signal_start:end, channel] += (
            amplitude * shifted[: end - signal_start] * gain_errors[channel]
        )
    analog += noise_rng.normal(scale=noise_std, size=analog.shape)
    payload, frame_count = _encode_analog_to_pdm_payload(analog, decimation)
    return SyntheticFixture(
        payload=payload,
        capture_frames=frame_count,
        raw_clock_hz=raw_clock_hz,
        sample_rate_hz=sample_rate_hz,
        chirp=reference,
        truth_range_m=range_m,
        truth_bearing_deg=bearing_deg,
        gain_errors=gain_errors,
        calibration=calibration,
        positions_m=positions,
    )


def process_payload(
    payload: bytes,
    *,
    raw_clock_hz: int,
    calibration: ChannelCalibration,
    reference_chirp: np.ndarray,
    positions_m: np.ndarray,
    azimuth_grid_deg: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, BeamScanResult]:
    logical_frames = unpack_logical_frames(payload)
    sample_rate_hz = raw_clock_hz / 24.0
    decimated = decimate_pdm_cic_fir(
        logical_frames,
        sample_rate_hz=sample_rate_hz,
    )
    calibrated = apply_calibration(decimated, calibration)
    matched = matched_filter(calibrated, reference_chirp)
    scan = estimate_range_and_bearing(
        matched,
        sample_rate_hz=sample_rate_hz,
        reference_length=len(reference_chirp),
        positions_m=positions_m,
        azimuth_grid_deg=azimuth_grid_deg,
    )
    return decimated, matched, scan


def _encode_analog_to_pdm_payload(samples: np.ndarray, decimation: int) -> tuple[bytes, int]:
    upsampled = np.repeat(samples, decimation * 2, axis=0)
    pdm_bits = _sigma_delta_modulate(np.clip(upsampled, -0.95, 0.95))
    logical_frames = np.empty((samples.shape[0] * decimation, samples.shape[1]), dtype=np.uint8)
    logical_frames[:, 0::2] = pdm_bits[0::2, 0::2]
    logical_frames[:, 1::2] = pdm_bits[1::2, 1::2]
    payload = pack_logical_frames(logical_frames)
    return payload, logical_frames.shape[0]


def _sigma_delta_modulate(signal: np.ndarray) -> np.ndarray:
    accumulator = np.zeros(signal.shape[1], dtype=np.float64)
    output = np.zeros(signal.shape, dtype=np.uint8)
    for index in range(signal.shape[0]):
        accumulator += signal[index]
        bit = accumulator >= 0.0
        output[index] = bit
        accumulator -= np.where(bit, 1.0, -1.0)
    return output


def _fractional_shift(signal: np.ndarray, delay_samples: float) -> np.ndarray:
    axis = np.arange(signal.shape[0], dtype=np.float64)
    return np.interp(axis - delay_samples, axis, signal, left=0.0, right=0.0)


def _as_channel_matrix(samples: np.ndarray) -> np.ndarray:
    matrix = np.asarray(samples)
    if matrix.ndim == 1:
        return matrix[:, None]
    if matrix.ndim != 2:
        raise ValueError(f"expected a 1D or 2D array, got shape {matrix.shape}")
    return matrix
