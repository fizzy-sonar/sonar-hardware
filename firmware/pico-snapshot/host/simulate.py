"""GPIO-independent synthetic PDM capture and deterministic decimation/spectrogram."""

from __future__ import annotations

import math
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from receiver import HEADER, decode  # noqa: E402

CLOCK_HZ = 3_072_000
DECIMATION = 24
TONE_HZ = 28_000


def pdm_bit(value: float, accumulator: float) -> tuple[int, float]:
    accumulator += value
    bit = int(accumulator >= 0.0)
    accumulator -= 1.0 if bit else -1.0
    return bit, accumulator


def make_payload(frames: int) -> bytes:
    """Models PIO's two 12-pin reads: even/rising then odd/falling, packed CH bit."""
    accumulators = [0.0] * 24
    payload = bytearray(3 * frames)
    for n in range(frames):
        packed = 0
        for line in range(12):
            for edge in range(2):
                channel = 2 * line + edge
                sample_time = (n + 0.5 * edge) / CLOCK_HZ
                value = 0.5 + 0.43 * math.sin(
                    2.0 * math.pi * TONE_HZ * sample_time + channel * 0.07
                )
                bit, accumulators[channel] = pdm_bit(value, accumulators[channel])
                packed |= bit << channel
        payload[3 * n : 3 * n + 3] = packed.to_bytes(3, "little")
    return bytes(payload)


def make_snapshot(payload: bytes, capture_id: int = 7) -> bytes:
    frames = len(payload) // 3
    prefix = HEADER.pack(
        b"SNP1",
        1,
        48,
        0,
        capture_id,
        0,
        CLOCK_HZ,
        24,
        12,
        frames,
        len(payload),
        zlib.crc32(payload) & 0xFFFFFFFF,
        0,
        0,
    )
    header_crc = zlib.crc32(prefix[:40]) & 0xFFFFFFFF
    return prefix[:40] + struct.pack("<I", header_crc) + b"\0\0\0\0" + payload


def decimate_channel(payload: bytes, channel: int) -> list[float]:
    # Boxcar CIC stage; phase is retained by channel bit extraction.
    out: list[float] = []
    for start in range(0, len(payload) // 3, DECIMATION):
        bits = 0
        for n in range(start, start + DECIMATION):
            if n >= len(payload) // 3:
                break
            bits += (payload[3 * n + channel // 8] >> (channel % 8)) & 1
        if start + DECIMATION <= len(payload) // 3:
            out.append((bits / DECIMATION - 0.5) / 0.43)
    return out


def power_at_tone(samples: list[float], frequency: float, sample_rate: float) -> float:
    re = sum(
        x * math.cos(2 * math.pi * frequency * n / sample_rate)
        for n, x in enumerate(samples)
    )
    im = sum(
        x * math.sin(2 * math.pi * frequency * n / sample_rate)
        for n, x in enumerate(samples)
    )
    return re * re + im * im


def write_spectrogram_pgm(samples: list[float], output: Path) -> None:
    # Small portable image: 64 time blocks x 64 0..64 kHz bins (no third-party deps).
    columns, rows, block = 64, 64, 256
    pixels = bytearray()
    for bin_index in range(rows):
        f = bin_index * (CLOCK_HZ / DECIMATION / 2) / (rows - 1)
        for col in range(columns):
            chunk = samples[col * block : (col + 1) * block]
            if len(chunk) < block:
                chunk = chunk + [0.0] * (block - len(chunk))
            p = power_at_tone(chunk, f, CLOCK_HZ / DECIMATION) / (block * block)
            pixels.append(min(255, int(255 * min(1.0, p * 12))))
    output.write_bytes(f"P5\n{columns} {rows}\n255\n".encode() + pixels)


def main() -> None:
    out = ROOT.parent / "build"
    out.mkdir(exist_ok=True)
    blob = make_snapshot(make_payload(49_152))  # 16 ms, three 48 KiB firmware windows.
    snapshot_path = out / "synthetic.snp1"
    snapshot_path.write_bytes(blob)
    snap = decode(blob)
    samples = decimate_channel(snap.payload, 0)
    tone = power_at_tone(samples, TONE_HZ, CLOCK_HZ / DECIMATION)
    off_tone = power_at_tone(samples, 45_000, CLOCK_HZ / DECIMATION)
    write_spectrogram_pgm(samples, out / "synthetic_spectrogram.pgm")
    print(f"synthetic capture: {snap.frames} frames, {len(snap.payload)} payload bytes")
    print(
        f"channel 0 {TONE_HZ} Hz tone/off-tone power ratio: {10 * math.log10(tone / off_tone):.1f} dB"
    )
    if tone <= off_tone * 100:
        raise SystemExit("known tone was not recovered")


if __name__ == "__main__":
    main()
