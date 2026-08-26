"""Validate and store SNP1 USB CDC frames; standard-library only."""

from __future__ import annotations

import argparse
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

HEADER_BYTES = 48
HEADER = struct.Struct("<4sBBHIQIHHIIIII")


@dataclass(frozen=True)
class Snapshot:
    capture_id: int
    first_frame: int
    clock_hz: int
    frames: int
    payload: bytes


def decode(blob: bytes) -> Snapshot:
    if len(blob) < HEADER_BYTES:
        raise ValueError("truncated SNP1 header")
    (
        magic,
        version,
        header_len,
        flags,
        capture_id,
        first,
        clock,
        channels,
        lines,
        frames,
        payload_len,
        payload_crc,
        header_crc,
        reserved,
    ) = HEADER.unpack(blob[:HEADER_BYTES])
    if (magic, version, header_len, flags, channels, lines, reserved) != (
        b"SNP1",
        1,
        48,
        0,
        24,
        12,
        0,
    ):
        raise ValueError("unsupported SNP1 header")
    if zlib.crc32(blob[:40]) & 0xFFFFFFFF != header_crc:
        raise ValueError("header CRC mismatch")
    if payload_len != frames * 3 or len(blob) != HEADER_BYTES + payload_len:
        raise ValueError("invalid payload length")
    payload = blob[HEADER_BYTES:]
    if zlib.crc32(payload) & 0xFFFFFFFF != payload_crc:
        raise ValueError("payload CRC mismatch")
    return Snapshot(capture_id, first, clock, frames, payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input", type=Path, help="CDC capture bytes (one complete SNP1 frame)"
    )
    parser.add_argument("output", type=Path, help="validated raw SNP1 output")
    args = parser.parse_args()
    blob = args.input.read_bytes()
    snapshot = decode(blob)
    args.output.write_bytes(blob)
    print(
        f"valid SNP1 capture={snapshot.capture_id} frames={snapshot.frames} clock={snapshot.clock_hz} Hz"
    )


if __name__ == "__main__":
    main()
