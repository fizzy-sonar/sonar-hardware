from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

import numpy as np

from .errors import (
    HeaderCRCError,
    PacketFormatError,
    PayloadCRCError,
    StreamFormatError,
    TruncatedPacketError,
)

SNP1_HEADER = struct.Struct("<4sBBHIQIHHIIIII")
SNR1_HEADER = struct.Struct("<4sBBHIQIHHI")

SNP1_MAGIC = b"SNP1"
SNR1_MAGIC = b"SNR1"
SNP1_VERSION = 1
SNR1_VERSION = 1
SNP1_HEADER_LEN = 48
SNR1_HEADER_LEN = 32
SNP1_FLAGS = 0x0000
SNR1_FLAGS = 0x0007
CHANNELS = 24
DATA_LINES = 12
BYTES_PER_FRAME = 3


@dataclass(frozen=True)
class SnapshotCapture:
    capture_id: int
    first_frame: int
    clock_hz: int
    frame_count: int
    payload: bytes

    @property
    def sample_rate_hz(self) -> float:
        return self.clock_hz / 24.0


@dataclass(frozen=True)
class StreamHeader:
    capture_id: int
    first_frame: int
    clock_hz: int
    flags: int

    @property
    def sample_rate_hz(self) -> float:
        return self.clock_hz / 24.0


def encode_snp1(
    payload: bytes,
    *,
    capture_id: int = 0,
    first_frame: int = 0,
    clock_hz: int = 3_072_000,
) -> bytes:
    frame_count = len(payload) // BYTES_PER_FRAME
    payload_crc = zlib.crc32(payload) & 0xFFFFFFFF
    header = SNP1_HEADER.pack(
        SNP1_MAGIC,
        SNP1_VERSION,
        SNP1_HEADER_LEN,
        SNP1_FLAGS,
        capture_id,
        first_frame,
        clock_hz,
        CHANNELS,
        DATA_LINES,
        frame_count,
        len(payload),
        payload_crc,
        0,
        0,
    )
    header_crc = zlib.crc32(header[:40]) & 0xFFFFFFFF
    return header[:40] + struct.pack("<I", header_crc) + b"\0" * 4 + payload


def parse_snp1(blob: bytes) -> SnapshotCapture:
    if len(blob) < SNP1_HEADER_LEN:
        raise TruncatedPacketError(
            f"SNP1 packet truncated: expected at least {SNP1_HEADER_LEN} bytes, got {len(blob)}"
        )
    (
        magic,
        version,
        header_len,
        flags,
        capture_id,
        first_frame,
        clock_hz,
        channels,
        data_lines,
        frame_count,
        payload_bytes,
        payload_crc,
        header_crc,
        reserved,
    ) = SNP1_HEADER.unpack(blob[:SNP1_HEADER_LEN])
    _validate_snp1_header(
        magic=magic,
        version=version,
        header_len=header_len,
        flags=flags,
        channels=channels,
        data_lines=data_lines,
        frame_count=frame_count,
        payload_bytes=payload_bytes,
        header_crc=header_crc,
        reserved=reserved,
        header_bytes=blob[:SNP1_HEADER_LEN],
    )
    payload = blob[SNP1_HEADER_LEN:]
    if len(payload) != payload_bytes:
        raise TruncatedPacketError(
            f"SNP1 payload truncated: header advertises {payload_bytes} bytes, got {len(payload)}"
        )
    actual_payload_crc = zlib.crc32(payload) & 0xFFFFFFFF
    if actual_payload_crc != payload_crc:
        raise PayloadCRCError(
            f"SNP1 payload CRC mismatch: expected 0x{payload_crc:08x}, got 0x{actual_payload_crc:08x}"
        )
    return SnapshotCapture(
        capture_id=capture_id,
        first_frame=first_frame,
        clock_hz=clock_hz,
        frame_count=frame_count,
        payload=payload,
    )


def parse_snr1_header(blob: bytes) -> StreamHeader:
    if len(blob) < SNR1_HEADER_LEN:
        raise TruncatedPacketError(
            f"SNR1 header truncated: expected {SNR1_HEADER_LEN} bytes, got {len(blob)}"
        )
    (
        magic,
        version,
        header_len,
        flags,
        capture_id,
        first_frame,
        clock_hz,
        channels,
        data_lines,
        reserved,
    ) = SNR1_HEADER.unpack(blob[:SNR1_HEADER_LEN])
    if magic != SNR1_MAGIC:
        raise StreamFormatError(f"SNR1 magic mismatch: expected {SNR1_MAGIC!r}, got {magic!r}")
    if version != SNR1_VERSION:
        raise StreamFormatError(
            f"SNR1 version mismatch: expected {SNR1_VERSION}, got {version}"
        )
    if header_len != SNR1_HEADER_LEN:
        raise StreamFormatError(
            f"SNR1 header_len mismatch: expected {SNR1_HEADER_LEN}, got {header_len}"
        )
    if flags != SNR1_FLAGS:
        raise StreamFormatError(
            f"SNR1 flags mismatch: expected 0x{SNR1_FLAGS:04x}, got 0x{flags:04x}"
        )
    if channels != CHANNELS or data_lines != DATA_LINES:
        raise StreamFormatError(
            f"SNR1 channel map mismatch: expected {CHANNELS}/{DATA_LINES}, got {channels}/{data_lines}"
        )
    if reserved != 0:
        raise StreamFormatError(f"SNR1 reserved field must be zero, got {reserved}")
    return StreamHeader(
        capture_id=capture_id,
        first_frame=first_frame,
        clock_hz=clock_hz,
        flags=flags,
    )


def unpack_logical_frames(payload: bytes) -> np.ndarray:
    if len(payload) % BYTES_PER_FRAME != 0:
        raise PacketFormatError(
            f"payload length must be a multiple of {BYTES_PER_FRAME}, got {len(payload)}"
        )
    triplets = np.frombuffer(payload, dtype=np.uint8).reshape(-1, BYTES_PER_FRAME)
    words = (
        triplets[:, 0].astype(np.uint32)
        | (triplets[:, 1].astype(np.uint32) << 8)
        | (triplets[:, 2].astype(np.uint32) << 16)
    )
    return ((words[:, None] >> np.arange(CHANNELS, dtype=np.uint32)) & 1).astype(np.uint8)


def pack_logical_frames(bits: np.ndarray) -> bytes:
    frame_bits = np.asarray(bits, dtype=np.uint8)
    if frame_bits.ndim != 2 or frame_bits.shape[1] != CHANNELS:
        raise PacketFormatError(
            f"expected logical frames with shape (n, {CHANNELS}), got {frame_bits.shape}"
        )
    words = np.zeros(frame_bits.shape[0], dtype=np.uint32)
    for channel in range(CHANNELS):
        words |= (frame_bits[:, channel] & 1).astype(np.uint32) << channel
    packed = np.empty((frame_bits.shape[0], BYTES_PER_FRAME), dtype=np.uint8)
    packed[:, 0] = words & 0xFF
    packed[:, 1] = (words >> 8) & 0xFF
    packed[:, 2] = (words >> 16) & 0xFF
    return packed.tobytes()


def _validate_snp1_header(
    *,
    magic: bytes,
    version: int,
    header_len: int,
    flags: int,
    channels: int,
    data_lines: int,
    frame_count: int,
    payload_bytes: int,
    header_crc: int,
    reserved: int,
    header_bytes: bytes,
) -> None:
    if magic != SNP1_MAGIC:
        raise PacketFormatError(f"SNP1 magic mismatch: expected {SNP1_MAGIC!r}, got {magic!r}")
    if version != SNP1_VERSION:
        raise PacketFormatError(
            f"SNP1 version mismatch: expected {SNP1_VERSION}, got {version}"
        )
    if header_len != SNP1_HEADER_LEN:
        raise PacketFormatError(
            f"SNP1 header_len mismatch: expected {SNP1_HEADER_LEN}, got {header_len}"
        )
    if flags != SNP1_FLAGS:
        raise PacketFormatError(
            f"SNP1 flags mismatch: expected 0x{SNP1_FLAGS:04x}, got 0x{flags:04x}"
        )
    if channels != CHANNELS or data_lines != DATA_LINES:
        raise PacketFormatError(
            f"SNP1 channel map mismatch: expected {CHANNELS}/{DATA_LINES}, got {channels}/{data_lines}"
        )
    expected_payload_bytes = frame_count * BYTES_PER_FRAME
    if payload_bytes != expected_payload_bytes:
        raise PacketFormatError(
            f"SNP1 payload size mismatch: frame_count={frame_count} implies {expected_payload_bytes} bytes, "
            f"header advertises {payload_bytes}"
        )
    if reserved != 0:
        raise PacketFormatError(f"SNP1 reserved field must be zero, got {reserved}")
    actual_header_crc = zlib.crc32(header_bytes[:40]) & 0xFFFFFFFF
    if actual_header_crc != header_crc:
        raise HeaderCRCError(
            f"SNP1 header CRC mismatch: expected 0x{header_crc:08x}, got 0x{actual_header_crc:08x}"
        )
