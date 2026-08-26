#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "capture_config.h"
#include "snapshot_protocol.h"

void sonar_repack_pio_words(uint8_t *, const uint32_t *, uint32_t);

static uint32_t interleave_edges(uint32_t rising, uint32_t falling) {
    uint32_t packed = 0;
    for (unsigned line = 0; line < 12; ++line) {
        packed |= ((rising >> line) & 1u) << (2u * line);
        packed |= ((falling >> line) & 1u) << (2u * line + 1u);
    }
    return packed;
}

static void put32_little_endian(uint8_t *out, uint32_t value) {
    for (unsigned byte = 0; byte < 4; ++byte) {
        out[byte] = (uint8_t)(value >> (8u * byte));
    }
}

int main(void) {
    assert(PDM_STANDARD_FRAMES == 76800u);
    assert(PDM_SETTLE_FRAMES == 30720u);

    sonar_pio_clock_config_t standard_clock;
    sonar_pio_clock_config_t ultrasonic_clock;
    assert(sonar_pio_clock_config(150000000u, PDM_STANDARD_HZ,
                                  &standard_clock));
    assert(standard_clock.divider_integer == 9u);
    assert(standard_clock.divider_fraction == 196u);
    assert(standard_clock.actual_hz == PDM_STANDARD_HZ);
    assert(standard_clock.error_ppm == 0);
    assert(sonar_pio_clock_config(150000000u, PDM_ULTRASONIC_HZ,
                                  &ultrasonic_clock));
    assert(ultrasonic_clock.divider_integer == 4u);
    assert(ultrasonic_clock.divider_fraction == 226u);
    assert(ultrasonic_clock.actual_hz == PDM_ULTRASONIC_HZ);
    assert(ultrasonic_clock.error_ppm == 0);

    sonar_pio_clock_config_t quantized_clock;
    assert(sonar_pio_clock_config(125000000u, PDM_ULTRASONIC_HZ,
                                  &quantized_clock));
    assert(quantized_clock.divider_integer == 4u);
    assert(quantized_clock.divider_fraction == 18u);
    assert(quantized_clock.actual_hz == 3071017u);
    assert(quantized_clock.error_ppm == -320);
    assert(!sonar_pio_clock_config(80000000u, PDM_ULTRASONIC_HZ,
                                   &quantized_clock));
    assert(quantized_clock.error_ppm == -500);
    assert(!sonar_pio_clock_config(1000000u, PDM_ULTRASONIC_HZ,
                                   &ultrasonic_clock));
    assert(!sonar_pio_clock_config(150000000u, 0, &ultrasonic_clock));

    assert(sonar_crc32((const uint8_t *)"123456789", 9) == 0xcbf43926u);

    const uint32_t rising = 0xa53u;
    const uint32_t falling = 0x5acu;
    const uint32_t pio_word = (rising << 12u) | falling;
    const uint32_t expected_channels = interleave_edges(rising, falling);
    uint8_t repacked[SONAR_BYTES_PER_FRAME];
    sonar_repack_pio_words(repacked, &pio_word, 1);
    assert(sonar_unpack_frame(repacked) == expected_channels);
    for (unsigned line = 0; line < 12; ++line) {
        assert(((sonar_unpack_frame(repacked) >> (2u * line)) & 1u) ==
               ((rising >> line) & 1u));
        assert(((sonar_unpack_frame(repacked) >> (2u * line + 1u)) & 1u) ==
               ((falling >> line) & 1u));
    }

    const uint8_t payload[] = {0x01, 0x00, 0x80, 0xfe, 0xff, 0x7f};
    sonar_snapshot_header_t header = {
        .sequence = 42,
        .first_frame = 30720,
        .clock_hz = ultrasonic_clock.actual_hz,
        .channels = 24,
        .data_lines = 12,
        .frame_count = 2,
        .payload_bytes = 6,
        .payload_crc32 = sonar_crc32(payload, sizeof(payload)),
    };
    uint8_t wire[SONAR_SNAPSHOT_HEADER_BYTES];
    assert(sonar_snapshot_encode_header(wire, &header));
    assert(memcmp(wire, "SNP1\x01\x30\0\0", 8) == 0);
    sonar_snapshot_header_t decoded;
    assert(sonar_snapshot_decode_header(&decoded, wire));
    assert(decoded.sequence == 42 && decoded.first_frame == 30720);
    assert(decoded.clock_hz == PDM_ULTRASONIC_HZ);
    assert(decoded.payload_crc32 == header.payload_crc32);

    wire[6] = 1;
    put32_little_endian(wire + 40, sonar_crc32(wire, 40));
    assert(!sonar_snapshot_decode_header(&decoded, wire));
    assert(sonar_snapshot_encode_header(wire, &header));
    wire[10] ^= 1;
    assert(!sonar_snapshot_decode_header(&decoded, wire));

    header.frame_count = UINT32_MAX;
    header.payload_bytes = 0;
    assert(!sonar_snapshot_encode_header(wire, &header));
    return 0;
}
