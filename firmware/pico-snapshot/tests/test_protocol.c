#include <assert.h>
#include <string.h>
#include "snapshot_protocol.h"
void sonar_repack_pio_words(uint8_t *, const uint32_t *, uint32_t);

int main(void) {
    const uint8_t expected[] = {0x55, 0x55, 0x55}; /* odd channels only */
    uint8_t frame[3]; sonar_pack_frame(frame, 0x555555); assert(!memcmp(frame, expected, 3));
    assert(sonar_unpack_frame(frame) == 0x555555);
    const uint32_t pio_words[] = {0x000001, 0x800000}; uint8_t repacked[6];
    sonar_repack_pio_words(repacked, pio_words, 2);
    assert(!memcmp(repacked, (uint8_t[]){1, 0, 0, 0, 0, 0x80}, 6));
    const uint8_t payload[] = {0x01, 0x00, 0x80, 0xfe, 0xff, 0x7f};
    sonar_snapshot_header_t h = {.sequence = 42, .first_frame = 1234, .clock_hz = 3072000,
        .channels = 24, .data_lines = 12, .frame_count = 2, .payload_bytes = 6,
        .payload_crc32 = sonar_crc32(payload, sizeof payload)};
    uint8_t wire[48]; assert(sonar_snapshot_encode_header(wire, &h));
    sonar_snapshot_header_t decoded; assert(sonar_snapshot_decode_header(&decoded, wire));
    assert(decoded.sequence == 42 && decoded.first_frame == 1234 && decoded.payload_crc32 == h.payload_crc32);
    wire[10] ^= 1; assert(!sonar_snapshot_decode_header(&decoded, wire));
    return 0;
}
