from __future__ import annotations

from pathlib import Path

import numpy as np

from sonar_host.capture import RawCaptureStore
from sonar_host.dsp import generate_point_target_fixture, process_payload


def write_svg(
    path: Path,
    title: str,
    x_values: np.ndarray,
    y_values: np.ndarray,
    scan_x: np.ndarray,
    scan_y: np.ndarray,
) -> None:
    width = 900
    height = 520
    margin = 60

    def scale(series: np.ndarray, lower: float, upper: float, span: float) -> np.ndarray:
        if upper == lower:
            return np.full(series.shape, span / 2.0)
        return (series - lower) / (upper - lower) * span

    plot_width = width - 2 * margin
    plot_height = height - 2 * margin

    x_scaled = margin + scale(
        x_values, float(x_values.min()), float(x_values.max()), plot_width
    )
    y_scaled = height - margin - scale(
        y_values, float(y_values.min()), float(y_values.max()), plot_height
    )
    scan_scaled_x = margin + scale(
        scan_x, float(scan_x.min()), float(scan_x.max()), plot_width
    )
    scan_scaled_y = height - margin - scale(
        scan_y, float(scan_y.min()), float(scan_y.max()), plot_height
    )

    path_one = " ".join(
        f"{'M' if index == 0 else 'L'} {x_scaled[index]:.2f} {y_scaled[index]:.2f}"
        for index in range(len(x_scaled))
    )
    path_two = " ".join(
        f"{'M' if index == 0 else 'L'} {scan_scaled_x[index]:.2f} {scan_scaled_y[index]:.2f}"
        for index in range(len(scan_scaled_x))
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <rect width="100%" height="100%" fill="#f7f7f2"/>
  <text x="{margin}" y="34" font-family="Menlo, monospace" font-size="22" fill="#1f2d3d">{title}</text>
  <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#4b5563" stroke-width="1.5"/>
  <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#4b5563" stroke-width="1.5"/>
  <path d="{path_one}" fill="none" stroke="#0f766e" stroke-width="2.2"/>
  <path d="{path_two}" fill="none" stroke="#b91c1c" stroke-width="2.2"/>
  <text x="{margin}" y="{height - 18}" font-family="Menlo, monospace" font-size="12" fill="#374151">Range profile</text>
  <text x="{width - 190}" y="{height - 18}" font-family="Menlo, monospace" font-size="12" fill="#374151">Bearing scan</text>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)


def main() -> None:
    fixture = generate_point_target_fixture()
    _, matched, scan = process_payload(
        fixture.payload,
        raw_clock_hz=fixture.raw_clock_hz,
        calibration=fixture.calibration,
        reference_chirp=fixture.chirp,
        positions_m=fixture.positions_m,
    )
    artifact_dir = Path("host/artifacts")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    capture_store = RawCaptureStore()
    capture_store.append(fixture.payload)
    npy_path = capture_store.save_npy(artifact_dir / "t021-demo-capture.npy")
    matched_axis = (
        np.arange(matched.shape[0], dtype=np.float64) / fixture.sample_rate_hz * 343.0 / 2.0
    )
    svg_path = artifact_dir / "t021-demo.svg"
    write_svg(
        svg_path,
        title="Sonar T-021 synthetic point-target demo",
        x_values=matched_axis,
        y_values=np.abs(scan.beamformed),
        scan_x=scan.azimuth_grid_deg,
        scan_y=scan.beam_peaks,
    )
    summary_path = artifact_dir / "t021-demo-summary.txt"
    summary = (
        f"truth_range_m={fixture.truth_range_m:.3f}\n"
        f"estimated_range_m={scan.range_m:.3f}\n"
        f"truth_bearing_deg={fixture.truth_bearing_deg:.2f}\n"
        f"estimated_bearing_deg={scan.bearing_deg:.2f}\n"
        f"plot_artifact={svg_path}\n"
        f"capture_npy={npy_path}\n"
    )
    summary_path.write_text(summary)
    print(summary.strip())


if __name__ == "__main__":
    main()
