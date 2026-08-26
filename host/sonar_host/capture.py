from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


class RawCaptureStore:
    def __init__(self) -> None:
        self._chunks: list[bytes] = []
        self._size = 0

    def append(self, chunk: bytes) -> None:
        if not chunk:
            return
        self._chunks.append(bytes(chunk))
        self._size += len(chunk)

    @property
    def size_bytes(self) -> int:
        return self._size

    @property
    def frame_count(self) -> int:
        return self._size // 3

    def payload(self) -> bytes:
        return b"".join(self._chunks)

    def save_npy(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(output_path, np.frombuffer(self.payload(), dtype=np.uint8))
        return output_path


class ChannelRingBuffer:
    def __init__(self, channels: int, capacity: int) -> None:
        self._capacity = capacity
        self._channels = channels
        self._data = np.zeros((capacity, channels), dtype=np.float32)
        self._start = 0
        self._length = 0

    def append(self, block: np.ndarray) -> None:
        samples = np.asarray(block, dtype=np.float32)
        if samples.ndim != 2 or samples.shape[1] != self._channels:
            raise ValueError(
                f"expected samples with shape (n, {self._channels}), got {samples.shape}"
            )
        if samples.shape[0] >= self._capacity:
            self._data[:] = samples[-self._capacity :]
            self._start = 0
            self._length = self._capacity
            return
        end = (self._start + self._length) % self._capacity
        first = min(samples.shape[0], self._capacity - end)
        self._data[end : end + first] = samples[:first]
        remaining = samples.shape[0] - first
        if remaining:
            self._data[:remaining] = samples[first:]
        if self._length + samples.shape[0] <= self._capacity:
            self._length += samples.shape[0]
        else:
            overflow = self._length + samples.shape[0] - self._capacity
            self._start = (self._start + overflow) % self._capacity
            self._length = self._capacity

    def snapshot(self) -> np.ndarray:
        if self._length == 0:
            return np.zeros((0, self._channels), dtype=np.float32)
        if self._start + self._length <= self._capacity:
            return self._data[self._start : self._start + self._length].copy()
        first = self._capacity - self._start
        return np.vstack((self._data[self._start :], self._data[: self._length - first])).copy()


@dataclass(frozen=True)
class CaptureSummary:
    capture_id: int
    frame_count: int
    payload_path: Path
