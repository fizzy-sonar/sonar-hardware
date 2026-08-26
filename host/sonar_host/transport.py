from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

import numpy as np

from .capture import RawCaptureStore
from .errors import StreamIncompleteError, StreamOverflowError, TruncatedPacketError
from .packet import SNR1_HEADER_LEN, StreamHeader, parse_snr1_header, unpack_logical_frames


class MockTransport:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = iter(chunks)

    def read(self, size: int) -> bytes:
        del size
        return next(self._chunks, b"")


class FT232HTransport:
    def __init__(self, url: str) -> None:
        from pyftdi.ftdi import Ftdi

        self._device = Ftdi()
        self._device.open_from_url(url)
        self._device.set_bitmode(0, 0x40)

    def read(self, size: int) -> bytes:
        return self._device.read_data_bytes(size, 4)


@dataclass
class StreamCapture:
    header: StreamHeader
    store: RawCaptureStore

    @property
    def frame_count(self) -> int:
        return self.store.frame_count

    def unpack_frames(self) -> np.ndarray:
        return unpack_logical_frames(self.store.payload())


class BufferedTransportReader:
    def __init__(
        self,
        transport,
        *,
        chunk_size: int = 16_384,
        sticky_overflow_check: Callable[[], bool] | None = None,
    ) -> None:
        self._transport = transport
        self._chunk_size = chunk_size
        self._sticky_overflow_check = sticky_overflow_check
        self._buffer = bytearray()
        self._saw_eof = False

    def read_exact(self, size: int) -> bytes:
        while len(self._buffer) < size and not self._saw_eof:
            self._fill()
        if len(self._buffer) < size:
            raise TruncatedPacketError(f"expected {size} bytes, got {len(self._buffer)} before EOF")
        data = bytes(self._buffer[:size])
        del self._buffer[:size]
        return data

    def open_stream(self) -> "SNR1StreamParser":
        header = parse_snr1_header(self.read_exact(SNR1_HEADER_LEN))
        return SNR1StreamParser(self, header)

    def _fill(self) -> None:
        chunk = self._transport.read(self._chunk_size)
        if self._sticky_overflow_check and self._sticky_overflow_check():
            raise StreamOverflowError("transport reported sticky overflow; capture is incomplete")
        if not chunk:
            self._saw_eof = True
            return
        self._buffer.extend(chunk)

    def pop_frame_bytes(self, max_frames: int) -> bytes | None:
        target_bytes = max_frames * 3
        while len(self._buffer) < target_bytes and not self._saw_eof:
            self._fill()
        whole_frames = len(self._buffer) // 3
        if whole_frames == 0:
            if self._saw_eof:
                return None
            self._fill()
            whole_frames = len(self._buffer) // 3
            if whole_frames == 0 and self._saw_eof:
                return None
        count = min(max_frames, whole_frames)
        size = count * 3
        data = bytes(self._buffer[:size])
        del self._buffer[:size]
        return data

    def close_stream(self) -> None:
        while not self._saw_eof:
            self._fill()
        if self._buffer:
            raise StreamIncompleteError(
                f"stream ended with {len(self._buffer)} trailing bytes; no silent resync is allowed"
            )


class SNR1StreamParser:
    def __init__(self, reader: BufferedTransportReader, header: StreamHeader) -> None:
        self.header = header
        self._reader = reader

    def iter_frame_blocks(self, max_frames: int = 4096) -> Iterator[np.ndarray]:
        while True:
            frame_bytes = self._reader.pop_frame_bytes(max_frames)
            if frame_bytes is None:
                break
            yield unpack_logical_frames(frame_bytes)
        self._reader.close_stream()

    def capture_exact_frames(
        self,
        requested_frames: int,
        store: RawCaptureStore | None = None,
    ) -> StreamCapture:
        capture_store = store or RawCaptureStore()
        frames_read = 0
        while frames_read < requested_frames:
            remaining = requested_frames - frames_read
            frame_bytes = self._reader.pop_frame_bytes(min(remaining, 4096))
            if frame_bytes is None:
                raise StreamIncompleteError(
                    f"stream ended after {frames_read} frames; requested {requested_frames}"
                )
            capture_store.append(frame_bytes)
            frames_read += len(frame_bytes) // 3
        return StreamCapture(header=self.header, store=capture_store)
