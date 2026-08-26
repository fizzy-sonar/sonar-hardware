#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
    void *context;
    void (*task)(void *context);
    bool (*connected)(void *context);
    uint32_t (*write_available)(void *context);
    uint32_t (*write)(void *context, const uint8_t *data, uint32_t size);
    void (*flush)(void *context);
} sonar_cdc_io_t;

/* Services USB during backpressure and accepts partial writes. */
bool sonar_cdc_write_all(const sonar_cdc_io_t *io, const uint8_t *data,
                         size_t size);
