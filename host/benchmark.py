from __future__ import annotations

from time import perf_counter

from sonar_host.dsp import generate_point_target_fixture
from sonar_host.packet import SNR1_FLAGS, SNR1_HEADER, SNR1_MAGIC, SNR1_VERSION
from sonar_host.transport import BufferedTransportReader, MockTransport

TARGET_MB_S = 9.216


def build_stream_bytes(payload: bytes, *, capture_id: int, clock_hz: int) -> bytes:
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


def run_benchmark(iterations: int = 24) -> tuple[float, float]:
    fixture = generate_point_target_fixture(output_samples=8192, chirp_samples=640)
    stream_bytes = build_stream_bytes(
        fixture.payload,
        capture_id=fixture.capture_frames,
        clock_hz=fixture.raw_clock_hz,
    )
    payload_bytes = 0
    started = perf_counter()
    for _ in range(iterations):
        chunks = [
            stream_bytes[index : index + 11_000]
            for index in range(0, len(stream_bytes), 11_000)
        ]
        reader = BufferedTransportReader(MockTransport(chunks), chunk_size=11_000)
        capture = reader.open_stream().capture_exact_frames(fixture.capture_frames)
        payload_bytes += capture.store.size_bytes
        reader.close_stream()
    elapsed = perf_counter() - started
    throughput = payload_bytes / elapsed / 1_000_000.0
    return throughput, throughput / TARGET_MB_S


def main() -> None:
    throughput, ratio = run_benchmark()
    verdict = "PASS" if throughput >= TARGET_MB_S else "FAIL"
    print(
        f"T-021 synthetic ingest benchmark: {throughput:.3f} MB/s "
        f"vs target {TARGET_MB_S:.3f} MB/s ({ratio:.2f}x) => {verdict}"
    )


if __name__ == "__main__":
    main()
