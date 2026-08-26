import struct
import zlib

import numpy as np

H = struct.Struct("<4sBBHIQIHHIIIII")


def encode_snp1(payload, capture_id=0, first_frame=0, clock_hz=3072000):
    n = len(payload) // 3
    h = H.pack(
        b"SNP1",
        1,
        48,
        0,
        capture_id,
        first_frame,
        clock_hz,
        24,
        12,
        n,
        len(payload),
        zlib.crc32(payload) & 0xFFFFFFFF,
        0,
        0,
    )
    return h[:40] + struct.pack("<I", zlib.crc32(h[:40]) & 0xFFFFFFFF) + b"\0" * 4 + payload


def decode_snp1(blob):
    x = H.unpack(blob[:48])
    assert (
        x[:4] == (b"SNP1", 1, 48, 0)
        and x[7:9] == (24, 12)
        and zlib.crc32(blob[:40]) & 0xFFFFFFFF == x[12]
    )
    p = blob[48:]
    assert len(p) == x[10] and zlib.crc32(p) & 0xFFFFFFFF == x[11]
    return {"capture_id": x[4], "clock_hz": x[6], "frames": x[9], "payload": p}


def unpack_payload(p):
    a = np.frombuffer(p, dtype=np.uint8).reshape(-1, 3)
    w = (
        a[:, 0].astype(np.uint32)
        | (a[:, 1].astype(np.uint32) << 8)
        | (a[:, 2].astype(np.uint32) << 16)
    )
    return ((w[:, None] >> np.arange(24)) & 1).astype(np.int8)
