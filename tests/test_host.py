import struct
import unittest

import numpy as np

from sonar_host.dsp import generate_point_target_fixture, process_payload
from sonar_host.errors import (
    HeaderCRCError,
    PacketFormatError,
    StreamIncompleteError,
    StreamOverflowError,
    TruncatedPacketError,
)
from sonar_host.packet import (
    SNR1_FLAGS,
    SNR1_HEADER,
    SNR1_MAGIC,
    SNR1_VERSION,
    encode_snp1,
    pack_logical_frames,
    parse_snp1,
    unpack_logical_frames,
)
from sonar_host.transport import BufferedTransportReader, MockTransport


def build_snr1_stream(payload: bytes, *, capture_id: int = 7, clock_hz: int = 3_072_000) -> bytes:
    header = SNR1_HEADER.pack(
        SNR1_MAGIC,
        SNR1_VERSION,
        32,
        SNR1_FLAGS,
        capture_id,
        0,
        clock_hz,
        24,
        12,
        0,
    )
    return header + payload


class HostPipelineTests(unittest.TestCase):
    def test_snp1_round_trip_and_bit_order(self) -> None:
        frames = np.zeros((4, 24), dtype=np.uint8)
        frames[0, 0] = 1
        frames[0, 23] = 1
        frames[1, 4] = 1
        payload = pack_logical_frames(frames)
        capture = parse_snp1(encode_snp1(payload, capture_id=3, first_frame=11))
        unpacked = unpack_logical_frames(capture.payload)
        self.assertEqual(capture.capture_id, 3)
        self.assertEqual(capture.first_frame, 11)
        self.assertEqual(capture.frame_count, 4)
        self.assertEqual(unpacked.shape, (4, 24))
        self.assertEqual(int(unpacked[0, 0]), 1)
        self.assertEqual(int(unpacked[0, 23]), 1)
        self.assertEqual(int(unpacked[1, 4]), 1)

    def test_snp1_validates_crc_and_header_contract(self) -> None:
        payload = bytes([0xAA, 0x55, 0x01]) * 8
        packet = bytearray(encode_snp1(payload))
        packet[10] ^= 0x01
        with self.assertRaises(HeaderCRCError):
            parse_snp1(bytes(packet))

        broken = bytearray(encode_snp1(payload))
        broken[32:36] = struct.pack("<I", 99)
        broken[40:44] = struct.pack("<I", 0)
        with self.assertRaises(PacketFormatError):
            parse_snp1(bytes(broken))

        with self.assertRaises(TruncatedPacketError):
            parse_snp1(packet[:12])

    def test_snr1_stream_parser_handles_chunking_and_rejects_partial_tail(self) -> None:
        frames = np.zeros((25, 24), dtype=np.uint8)
        frames[:, ::2] = 1
        payload = pack_logical_frames(frames)
        stream = build_snr1_stream(payload)
        chunks = [stream[:19], stream[19:68], stream[68:101], stream[101:]]
        reader = BufferedTransportReader(MockTransport(chunks), chunk_size=17)
        parser = reader.open_stream()
        recovered = np.vstack(list(parser.iter_frame_blocks(max_frames=7)))
        self.assertTrue(np.array_equal(recovered, frames))

        truncated = build_snr1_stream(payload)[:-2]
        reader = BufferedTransportReader(MockTransport([truncated]), chunk_size=4096)
        parser = reader.open_stream()
        with self.assertRaises(StreamIncompleteError):
            list(parser.iter_frame_blocks(max_frames=64))

    def test_snr1_surfaces_sticky_overflow(self) -> None:
        payload = pack_logical_frames(np.zeros((32, 24), dtype=np.uint8))
        stream = build_snr1_stream(payload)
        state = {"reads": 0}

        def sticky_overflow() -> bool:
            state["reads"] += 1
            return state["reads"] >= 3

        reader = BufferedTransportReader(
            MockTransport([stream[:32], stream[32:70], stream[70:]]),
            chunk_size=24,
            sticky_overflow_check=sticky_overflow,
        )
        parser = reader.open_stream()
        with self.assertRaises(StreamOverflowError):
            list(parser.iter_frame_blocks(max_frames=4))

    def test_end_to_end_point_target_recovers_range_and_bearing(self) -> None:
        fixture = generate_point_target_fixture(range_m=4.4, bearing_deg=10.0, seed=17)
        _, _, scan = process_payload(
            fixture.payload,
            raw_clock_hz=fixture.raw_clock_hz,
            calibration=fixture.calibration,
            reference_chirp=fixture.chirp,
            positions_m=fixture.positions_m,
        )
        self.assertLess(abs(scan.range_m - fixture.truth_range_m), 0.18)
        self.assertLess(abs(scan.bearing_deg - fixture.truth_bearing_deg), 2.0)


if __name__ == "__main__":
    unittest.main()
