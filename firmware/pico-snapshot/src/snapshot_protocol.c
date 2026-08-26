#include "snapshot_protocol.h"

#include <string.h>

static void put16(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
}

static void put32(uint8_t *p, uint32_t v) {
    for (unsigned i = 0; i < 4; ++i) {
        p[i] = (uint8_t)(v >> (8 * i));
    }
}

static void put64(uint8_t *p, uint64_t v) {
    for (unsigned i = 0; i < 8; ++i) {
        p[i] = (uint8_t)(v >> (8 * i));
    }
}

static uint16_t get16(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static uint32_t get32(const uint8_t *p) {
    uint32_t value = 0;
    for (unsigned i = 0; i < 4; ++i) {
        value |= (uint32_t)p[i] << (8 * i);
    }
    return value;
}

static uint64_t get64(const uint8_t *p) {
    uint64_t value = 0;
    for (unsigned i = 0; i < 8; ++i) {
        value |= (uint64_t)p[i] << (8 * i);
    }
    return value;
}

uint32_t sonar_crc32(const uint8_t *bytes, size_t size) {
    uint32_t crc = 0xffffffffu;
    for (size_t i = 0; i < size; ++i) {
        crc ^= bytes[i];
        for (unsigned bit = 0; bit < 8; ++bit) {
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
        }
    }
    return ~crc;
}

bool sonar_snapshot_encode_header(uint8_t out[SONAR_SNAPSHOT_HEADER_BYTES],
                                  const sonar_snapshot_header_t *header) {
    if (out == NULL || header == NULL ||
        header->frame_count > UINT32_MAX / SONAR_BYTES_PER_FRAME ||
        header->channels != SONAR_CHANNELS ||
        header->data_lines != SONAR_DATA_LINES ||
        header->payload_bytes !=
            header->frame_count * SONAR_BYTES_PER_FRAME) {
        return false;
    }
    memset(out, 0, SONAR_SNAPSHOT_HEADER_BYTES);
    memcpy(out, SONAR_SNAPSHOT_MAGIC, 4);
    out[4] = SONAR_SNAPSHOT_VERSION;
    out[5] = SONAR_SNAPSHOT_HEADER_BYTES;
    put32(out + 8, header->sequence);
    put64(out + 12, header->first_frame);
    put32(out + 20, header->clock_hz);
    put16(out + 24, header->channels);
    put16(out + 26, header->data_lines);
    put32(out + 28, header->frame_count);
    put32(out + 32, header->payload_bytes);
    put32(out + 36, header->payload_crc32);
    put32(out + 40, sonar_crc32(out, 40));
    return true;
}

bool sonar_snapshot_decode_header(
    sonar_snapshot_header_t *out,
    const uint8_t in[SONAR_SNAPSHOT_HEADER_BYTES]) {
    if (out == NULL || in == NULL || memcmp(in, SONAR_SNAPSHOT_MAGIC, 4) ||
        in[4] != SONAR_SNAPSHOT_VERSION ||
        in[5] != SONAR_SNAPSHOT_HEADER_BYTES || get16(in + 6) != 0 ||
        get32(in + 44) != 0 ||
        get32(in + 40) != sonar_crc32(in, 40)) {
        return false;
    }
    out->sequence = get32(in + 8);
    out->first_frame = get64(in + 12);
    out->clock_hz = get32(in + 20);
    out->channels = get16(in + 24);
    out->data_lines = get16(in + 26);
    out->frame_count = get32(in + 28);
    out->payload_bytes = get32(in + 32);
    out->payload_crc32 = get32(in + 36);
    return out->frame_count <= UINT32_MAX / SONAR_BYTES_PER_FRAME &&
           out->channels == SONAR_CHANNELS &&
           out->data_lines == SONAR_DATA_LINES &&
           out->payload_bytes ==
               out->frame_count * SONAR_BYTES_PER_FRAME;
}

void sonar_pack_frame(uint8_t out[SONAR_BYTES_PER_FRAME], uint32_t channels24) {
    out[0] = (uint8_t)channels24;
    out[1] = (uint8_t)(channels24 >> 8);
    out[2] = (uint8_t)(channels24 >> 16);
}

uint32_t sonar_unpack_frame(const uint8_t in[SONAR_BYTES_PER_FRAME]) {
    return (uint32_t)in[0] | ((uint32_t)in[1] << 8) |
           ((uint32_t)in[2] << 16);
}
