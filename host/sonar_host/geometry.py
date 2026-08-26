from __future__ import annotations

import numpy as np

CHANNEL_TO_GRID = (
    (0, 0),
    (1, 0),
    (2, 0),
    (3, 0),
    (0, 1),
    (1, 1),
    (3, 1),
    (4, 1),
    (0, 2),
    (1, 2),
    (3, 2),
    (4, 2),
    (0, 3),
    (1, 3),
    (2, 3),
    (3, 3),
    (0, 4),
    (1, 4),
    (2, 4),
    (3, 4),
    (4, 0),
    (4, 1),
    (4, 3),
    (4, 4),
)


def array_positions(pitch_m: float = 0.0075) -> np.ndarray:
    positions = np.zeros((len(CHANNEL_TO_GRID), 3), dtype=np.float64)
    for channel, (grid_x, grid_y) in enumerate(CHANNEL_TO_GRID):
        positions[channel, 0] = (grid_x - 2.0) * pitch_m
        positions[channel, 1] = (grid_y - 2.0) * pitch_m
    return positions


def steering_delays(
    positions_m: np.ndarray,
    azimuth_deg: float,
    elevation_deg: float = 0.0,
    sound_speed_m_s: float = 343.0,
) -> np.ndarray:
    azimuth = np.deg2rad(azimuth_deg)
    elevation = np.deg2rad(elevation_deg)
    direction = np.array(
        [
            np.sin(azimuth) * np.cos(elevation),
            np.sin(elevation),
            np.cos(azimuth) * np.cos(elevation),
        ],
        dtype=np.float64,
    )
    return -(positions_m @ direction) / sound_speed_m_s
