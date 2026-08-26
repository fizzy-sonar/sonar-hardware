#ifndef SONAR_SNAPSHOT_PROTOCOL_H
#define SONAR_SNAPSHOT_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Wire format is little endian and deliberately independent of RP2350 ABI. */
#define SONAR_SNAPSHOT_MAGIC "SNP1"
#define SONAR_SNAPSHOT_VERSION 1u
#define SONAR_SNAPSHOT_HEADER_BYTES 48u
#define SONAR_CHANNELS 24u
#define SONAR_DATA_LINES 12u
#define SONAR_BYTES_PER_FRAME 3u

typedef struct {
    uint32_t sequence;
    /* Ultrasonic frame periods only; stopped clocks and standard mode do not count. */
    uint64_t first_frame;
    /* Actual quantized clock, rounded to the nearest hertz. */
    uint32_t clock_hz;
    uint16_t channels;
    uint16_t data_lines;
    uint32_t frame_count;
    uint32_t payload_bytes;
    uint32_t payload_crc32;
} sonar_snapshot_header_t;

uint32_t sonar_crc32(const uint8_t *bytes, size_t size);
bool sonar_snapshot_encode_header(uint8_t out[SONAR_SNAPSHOT_HEADER_BYTES],
                                  const sonar_snapshot_header_t *header);
bool sonar_snapshot_decode_header(sonar_snapshot_header_t *out,
                                  const uint8_t in[SONAR_SNAPSHOT_HEADER_BYTES]);
/* Packs CH00..CH23 into bits 0..23, therefore preserving rising/falling order. */
void sonar_pack_frame(uint8_t out[SONAR_BYTES_PER_FRAME], uint32_t channels24);
uint32_t sonar_unpack_frame(const uint8_t in[SONAR_BYTES_PER_FRAME]);

#endif
