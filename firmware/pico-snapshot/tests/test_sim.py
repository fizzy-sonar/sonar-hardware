from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
from receiver import decode
from simulate import (
    decimate_channel,
    make_payload,
    make_snapshot,
    power_at_tone,
    CLOCK_HZ,
    TONE_HZ,
)


def main() -> None:
    payload = make_payload(2400)
    snap = decode(make_snapshot(payload))
    assert snap.frames == 2400 and len(snap.payload) == 7200
    samples = decimate_channel(payload, 0)
    assert (
        power_at_tone(samples, TONE_HZ, CLOCK_HZ / 24)
        > power_at_tone(samples, 45_000, CLOCK_HZ / 24) * 10
    )
    bad = bytearray(make_snapshot(payload))
    bad[-1] ^= 1
    try:
        decode(bytes(bad))
    except ValueError as error:
        assert "payload CRC" in str(error)
    else:
        raise AssertionError("CRC failure was accepted")


if __name__ == "__main__":
    main()
